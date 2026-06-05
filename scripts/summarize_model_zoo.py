from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


METRICS = [
    "MAPEK test dataset (%)",
    "MAE test dataset (C)",
    "RMSE test dataset (C)",
    "R2 test",
    "PCP test dataset (%)",
    "MAPE test dataset (%)",
]


def fmt(value: float, digits: int = 4) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):.{digits}f}"


def markdown_table(df: pd.DataFrame, cols: list[str], max_rows: int | None = None) -> list[str]:
    work = df.copy()
    if max_rows is not None:
        work = work.head(max_rows)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in work.iterrows():
        cells = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                cells.append(fmt(value))
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def family_name(method: str) -> str:
    tail = method.split("+", 1)[-1].strip()
    if tail in {"SVR", "RF", "CNN"}:
        return "paper_" + tail
    return tail.split("_", 1)[0].replace(" ", "")


def write_report(metrics_path: Path, best_path: Path, out_path: Path, top_n: int) -> None:
    df = pd.read_csv(metrics_path)
    df = df.sort_values(["MAPEK test dataset (%)", "MAE test dataset (C)", "RMSE test dataset (C)"], ascending=[True, True, True])
    best = json.loads(best_path.read_text(encoding="utf-8")) if best_path.exists() else df.iloc[0].to_dict()
    df["family_summary"] = df["ML method"].map(family_name)
    top_by_latent = df.sort_values(["latent_size", "MAPEK test dataset (%)"]).groupby("latent_size", as_index=False).head(1)
    paper = df[df["model_family"].eq("paper")].copy()
    family = (
        df.groupby("family_summary")
        .agg(
            count=("ML method", "count"),
            best_mapek=("MAPEK test dataset (%)", "min"),
            best_mae=("MAE test dataset (C)", "min"),
            best_rmse=("RMSE test dataset (C)", "min"),
            best_r2=("R2 test", "max"),
        )
        .reset_index()
        .sort_values(["best_mapek", "best_mae"])
    )

    lines = [
        "# SMP Tg 预测模型对比分析",
        "",
        "本文档自动汇总 `artifacts/reproduce/predictors/all_predictor_metrics.csv`，用于回应 TODO 中“预测模型：GNN、CNN/SVR/RF 论文对比，以及更多模型”的任务。当前比较仍基于小分子 SMILES -> VAE latent -> WVCM 的表示；超图表示暂缓。",
        "",
        "## 1. 选择原则",
        "",
        "- 优先指标：`MAPEK test dataset (%)`，因为 Tg 摄氏度可能为负或接近 0，普通 MAPE 的分母不稳定。",
        "- 辅助指标：MAE、RMSE、R2、PCP。",
        "- 不能只看训练集；当前按 test 指标排序。",
        "- 对 agent/闭环任务，GPR 这类带不确定性的模型有额外价值，但如果 MAE/RMSE 明显更差，应与 NuSVR/ensemble 模型共同作为候选。",
        "",
        "## 2. 当前最佳模型",
        "",
        f"- 最佳模型：`{best['ML method']}`",
        f"- latent size：`{best['latent_size']}`",
        f"- MAPEK test：`{fmt(best['MAPEK test dataset (%)'])}%`",
        f"- MAE test：`{fmt(best['MAE test dataset (C)'])} C`",
        f"- RMSE test：`{fmt(best['RMSE test dataset (C)'])} C`",
        f"- R2 test：`{fmt(best['R2 test'])}`",
        f"- model path：`{best['model_path']}`",
        "",
        "解释：当前全局选择按 MAPEK 选中 GaussianProcess_RBF。它适合 PiEvo-faithful，因为能提供预测不确定性；但 NuSVR_RBF 的 MAE/RMSE/R2 更好，实际闭环推荐应保留二者作为 ensemble/对照。",
        "",
        f"## 3. Top {top_n} 模型",
        "",
    ]
    lines.extend(markdown_table(df, ["latent_size", "ML method", *METRICS], max_rows=top_n))
    lines.extend(["", "## 4. 每个 latent size 的最佳模型", ""])
    lines.extend(markdown_table(top_by_latent, ["latent_size", "ML method", "MAPEK test dataset (%)", "MAE test dataset (C)", "RMSE test dataset (C)", "R2 test"]))
    lines.extend(["", "## 5. 论文基线 CNN/SVR/RF", ""])
    if paper.empty:
        lines.append("当前 metrics 中没有 `predictor_kind=paper` 的记录。")
    else:
        lines.extend(markdown_table(paper.sort_values(["MAPEK test dataset (%)", "MAE test dataset (C)"]), ["latent_size", "ML method", *METRICS], max_rows=30))
    lines.extend(["", "## 6. 模型家族概览", ""])
    lines.extend(markdown_table(family, ["family_summary", "count", "best_mapek", "best_mae", "best_rmse", "best_r2"], max_rows=40))
    lines.extend(
        [
            "",
            "## 7. 结论与后续",
            "",
            "- 当前最佳用于闭环的默认选择仍可保持 `VAE(512)+GaussianProcess_RBF`，因为它兼顾 MAPEK 和不确定性。",
            "- 若只追求点预测误差，`VAE(512)+NuSVR_RBF` 是强候选，MAE/RMSE/R2 优于 GPR。",
            "- RF/CNN/SVR 论文基线应保留为可复现实验对照，但当前 model zoo 已明显扩展。",
            "- 下一步应加入模型集成：GPR 提供不确定性，NuSVR/GBDT/ExtraTrees 提供稳健点预测，PiEvo 使用 disagreement 作为 OOD 或 epistemic signal。",
            "- GNN 已有草案，但还需要和同一 85/15 split、同一指标体系统一比较。",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize SMP predictor model zoo in Chinese markdown.")
    parser.add_argument("--metrics", default="artifacts/reproduce/predictors/all_predictor_metrics.csv")
    parser.add_argument("--best", default="artifacts/reproduce/predictors/best_model.json")
    parser.add_argument("--out", default="reports/model_selection_analysis.md")
    parser.add_argument("--top-n", type=int, default=30)
    args = parser.parse_args()
    write_report(Path(args.metrics), Path(args.best), Path(args.out), args.top_n)


if __name__ == "__main__":
    main()
