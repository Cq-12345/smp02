from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


def run_architecture(architecture: str, args: argparse.Namespace) -> dict[str, object]:
    out = Path(args.out_dir) / architecture
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
        architecture,
        "--hidden",
        str(args.hidden),
        "--seed",
        str(args.seed),
        "--out",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    metrics = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    metrics["output_dir"] = str(out)
    return metrics


def write_report(leaderboard: pd.DataFrame, report_path: Path, args: argparse.Namespace) -> None:
    best = leaderboard.sort_values(["MAPEK test dataset (%)", "MAE test dataset (C)"]).iloc[0]
    lines = [
        "# GNN Architecture Smoke Leaderboard",
        "",
        "本文档回应 TODO 中“预测模型：GNN”和“尝试 GIN/GAT/MPNN”的要求。当前仍使用单一小分子 SMILES 图，不涉及商品级组分、聚合物或超图表示。",
        "",
        "## Run",
        "",
        "```bash",
        f"PYTHONPATH=src {sys.executable} scripts/run_gnn_architecture_smoke.py --epochs {args.epochs} --batch-size {args.batch_size} --out-dir {args.out_dir}",
        "```",
        "",
        "## Leaderboard",
        "",
        "| rank | architecture | MAPEK test (%) | MAE test (C) | RMSE test (C) | R2 test |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    ranked = leaderboard.sort_values(["MAPEK test dataset (%)", "MAE test dataset (C)"]).reset_index(drop=True)
    for idx, row in ranked.iterrows():
        lines.append(
            f"| {idx + 1} | {row['architecture']} | {float(row['MAPEK test dataset (%)']):.4f} | "
            f"{float(row['MAE test dataset (C)']):.4f} | {float(row['RMSE test dataset (C)']):.4f} | {float(row['R2 test']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- 本 smoke 最优 GNN 架构为 `{best['architecture']}`，MAPEK test 为 {float(best['MAPEK test dataset (%)']):.4f}%。",
            "- 这些 GNN 仍是短训 smoke，不应替代当前最佳 VAE-WVCM-GPR/NuSVR 模型。",
            "- GNN 的价值更适合作为结构视角 ensemble 成员、disagreement/OOD 信号，以及未来加入 bond/process/global formulation features 后再正式比较。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small GCN/GIN/GAT/MPNN Tg prediction smoke leaderboard.")
    parser.add_argument("--data", default="data/SMP_Dataset.xlsx")
    parser.add_argument("--architectures", default="gcn,gin,gat,mpnn")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default="artifacts/trail/gnn_architecture_smoke")
    parser.add_argument("--report", default="reports/gnn_architecture_smoke_leaderboard.md")
    args = parser.parse_args()
    architectures = [part.strip() for part in args.architectures.split(",") if part.strip()]
    rows = [run_architecture(architecture, args) for architecture in architectures]
    leaderboard = pd.DataFrame(rows)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    leaderboard.sort_values(["MAPEK test dataset (%)", "MAE test dataset (C)"]).to_csv(out_dir / "gnn_architecture_leaderboard.csv", index=False)
    (out_dir / "gnn_architecture_summary.json").write_text(
        json.dumps(
            {
                "architectures": architectures,
                "epochs": int(args.epochs),
                "batch_size": int(args.batch_size),
                "best_architecture": str(leaderboard.sort_values(["MAPEK test dataset (%)", "MAE test dataset (C)"]).iloc[0]["architecture"]),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_report(leaderboard, Path(args.report), args)


if __name__ == "__main__":
    main()
