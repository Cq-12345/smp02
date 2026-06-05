from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


def run_case(name: str, global_features: bool, args: argparse.Namespace) -> dict[str, object]:
    out = Path(args.out_dir) / name
    cmd = [
        sys.executable,
        "trail/gnn/train_gnn.py",
        "--data",
        args.data,
        "--epochs",
        str(args.epochs),
        "--batch-size",
        str(args.batch_size),
        "--architecture",
        args.architecture,
        "--hidden",
        str(args.hidden),
        "--seed",
        str(args.seed),
        "--out",
        str(out),
    ]
    if global_features:
        cmd.append("--global-features")
    subprocess.run(cmd, check=True)
    metrics = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    metrics["case"] = name
    metrics["output_dir"] = str(out)
    return metrics


def write_report(comparison: pd.DataFrame, summary: dict[str, object], report_path: Path, args: argparse.Namespace) -> None:
    ranked = comparison.sort_values(["MAPEK test dataset (%)", "MAE test dataset (C)"]).reset_index(drop=True)
    best = ranked.iloc[0]
    lines = [
        "# GNN Global Feature Smoke",
        "",
        "本文档回应 TODO 中“预测模型：GNN”和“知识/反应/global formulation 上下文进入模型”的后续推进。当前仍只使用单一小分子 SMILES 图，不涉及暂缓的商品级组分或聚合物超图表示。",
        "",
        "## Run",
        "",
        "```bash",
        f"PYTHONPATH=src {sys.executable} scripts/run_gnn_global_feature_smoke.py --architecture {args.architecture} --epochs {args.epochs} --batch-size {args.batch_size}",
        "```",
        "",
        "## Compared Cases",
        "",
        "| rank | case | global features | MAPEK test (%) | MAE test (C) | RMSE test (C) | R2 test |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for idx, row in ranked.iterrows():
        lines.append(
            f"| {idx + 1} | {row['case']} | {bool(row['global_features'])} | "
            f"{float(row['MAPEK test dataset (%)']):.4f} | {float(row['MAE test dataset (C)']):.4f} | "
            f"{float(row['RMSE test dataset (C)']):.4f} | {float(row['R2 test']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Global Feature Contract",
            "",
            "- 特征在 graph pooling 后拼接进入 GNN head，不改变小分子图表示。",
            "- 向量包含组分数/比例熵、加权重原子数、芳香/杂原子/环/可旋转键信息、18 类官能团权重、互补反应对覆盖和 reactive group weight。",
            "- 这些特征来自 RDKit、SMARTS 官能团分类和现有 reaction compatibility rule；它们是模型输入和 OOD 审计信号，不是物理真理。",
            "",
            "## Interpretation",
            "",
            f"- 本 smoke 最优 case 为 `{best['case']}`，MAPEK test 为 {float(best['MAPEK test dataset (%)']):.4f}%。",
            f"- global-feature case 相对 baseline 的 MAPEK delta 为 {float(summary['global_minus_baseline_mapek_test_pct']):.4f}%，MAE delta 为 {float(summary['global_minus_baseline_mae_test_c']):.4f} C。",
            "- 单次短训 smoke 只能验证链路和特征契约，不能证明 GNN 已超过 VAE-WVCM model zoo；后续若扩大 epochs，应把该 GNN 作为结构视角加入 ensemble disagreement/OOD 审计。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare one GNN architecture with and without formulation-level global features.")
    parser.add_argument("--data", default="data/SMP_Dataset.xlsx")
    parser.add_argument("--architecture", choices=["gcn", "gin", "gat", "mpnn"], default="mpnn")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default="artifacts/trail/gnn_global_feature_smoke")
    parser.add_argument("--report", default="reports/gnn_global_feature_smoke.md")
    args = parser.parse_args()

    rows = [
        run_case(f"{args.architecture}_baseline", False, args),
        run_case(f"{args.architecture}_global", True, args),
    ]
    comparison = pd.DataFrame(rows)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(out_dir / "gnn_global_feature_comparison.csv", index=False)
    baseline = comparison.loc[comparison["case"] == f"{args.architecture}_baseline"].iloc[0]
    global_row = comparison.loc[comparison["case"] == f"{args.architecture}_global"].iloc[0]
    summary = {
        "architecture": args.architecture,
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "baseline_mapek_test_pct": float(baseline["MAPEK test dataset (%)"]),
        "global_mapek_test_pct": float(global_row["MAPEK test dataset (%)"]),
        "global_minus_baseline_mapek_test_pct": float(global_row["MAPEK test dataset (%)"] - baseline["MAPEK test dataset (%)"]),
        "baseline_mae_test_c": float(baseline["MAE test dataset (C)"]),
        "global_mae_test_c": float(global_row["MAE test dataset (C)"]),
        "global_minus_baseline_mae_test_c": float(global_row["MAE test dataset (C)"] - baseline["MAE test dataset (C)"]),
        "best_case": str(comparison.sort_values(["MAPEK test dataset (%)", "MAE test dataset (C)"]).iloc[0]["case"]),
    }
    (out_dir / "gnn_global_feature_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(comparison, summary, Path(args.report), args)


if __name__ == "__main__":
    main()
