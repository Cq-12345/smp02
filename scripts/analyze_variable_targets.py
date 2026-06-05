from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd


def prediction_column(df: pd.DataFrame) -> str:
    for col in ["predicted_tg_mean_c", "predicted_tg", "Tg", "tg"]:
        if col in df.columns:
            return col
    raise ValueError("No Tg prediction column found. Expected one of predicted_tg_mean_c, predicted_tg, Tg, tg.")


def target_reward(predicted_tg_c: float, target_tg_c: float, reward_temperature_c: float) -> float:
    return float(math.exp(-abs(float(predicted_tg_c) - float(target_tg_c)) / max(float(reward_temperature_c), 1e-9)))


def target_sweep(df: pd.DataFrame, targets: list[float], top_k: int, reward_temperature_c: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    pred_col = prediction_column(df)
    all_top = []
    summary_rows = []
    for target in targets:
        work = df.copy()
        work["target_tg_c"] = float(target)
        work["target_distance_c"] = (work[pred_col].astype(float) - float(target)).abs()
        work["target_reward"] = work[pred_col].map(lambda value: target_reward(float(value), float(target), reward_temperature_c))
        sort_cols = ["target_distance_c"]
        if "predicted_tg_sigma_c" in work.columns:
            sort_cols.append("predicted_tg_sigma_c")
        if "ood_penalty" in work.columns:
            sort_cols.append("ood_penalty")
        top = work.sort_values(sort_cols).head(top_k).copy()
        top["target_rank"] = range(1, len(top) + 1)
        all_top.append(top)
        summary_rows.append(
            {
                "target_tg_c": float(target),
                "best_predicted_tg_c": None if top.empty else float(top.iloc[0][pred_col]),
                "best_target_distance_c": None if top.empty else float(top.iloc[0]["target_distance_c"]),
                "best_reward": None if top.empty else float(top.iloc[0]["target_reward"]),
                "top_k": int(len(top)),
                "within_1c": int((work["target_distance_c"] <= 1.0).sum()),
                "within_5c": int((work["target_distance_c"] <= 5.0).sum()),
                "within_10c": int((work["target_distance_c"] <= 10.0).sum()),
            }
        )
    top_df = pd.concat(all_top, ignore_index=True) if all_top else pd.DataFrame()
    return pd.DataFrame(summary_rows), top_df


def markdown_cell(value: object, max_len: int = 180) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    text = str(value).replace("\n", " ")[:max_len]
    return text.replace("|", "\\|")


def write_report(summary: pd.DataFrame, top: pd.DataFrame, out: Path, source: Path, reward_temperature_c: float) -> None:
    lines = [
        "# 可变目标 Tg 批量分析",
        "",
        "本文档用于回应 TODO 中“真实 Tg 温度不固定”的要求。这里不重新训练模型，而是读取已有候选池，对多个目标 Tg 重新计算目标距离和 reward。",
        "",
        f"- 候选来源：`{source}`",
        f"- Reward：`exp(-abs(predicted_Tg - target_Tg) / {reward_temperature_c:g})`",
        "",
        "## 目标汇总",
        "",
        "| target Tg (C) | best predicted Tg (C) | best distance (C) | best reward | within 1C | within 5C | within 10C |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['target_tg_c']:.1f} | {row['best_predicted_tg_c']:.3f} | "
            f"{row['best_target_distance_c']:.3f} | {row['best_reward']:.4f} | "
            f"{int(row['within_1c'])} | {int(row['within_5c'])} | {int(row['within_10c'])} |"
        )
    lines.extend(["", "## 每个目标的 Top 5", ""])
    keep_cols = [col for col in ["target_tg_c", "target_rank", "predicted_tg_mean_c", "predicted_tg", "target_distance_c", "target_reward", "smiles", "ratios", "sources", "compatibility_reasons"] if col in top.columns]
    for target, group in top.groupby("target_tg_c"):
        lines.extend([f"### Target {float(target):.1f} C", ""])
        lines.append("| " + " | ".join(keep_cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(keep_cols)) + " |")
        for _, row in group.head(5).iterrows():
            cells = [markdown_cell(row[col]) for col in keep_cols]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines.extend(
        [
            "## 结论",
            "",
            "- 同一个候选池可以服务多个 Tg 目标，目标温度不应写死在算法里。",
            "- 对每个目标都应分别计算 `target_distance` 和 `target_reward`，再进入 Harness、PiEvo IDS 或人工筛选。",
            "- 若某个目标的 within-5C 候选很少，应扩展该目标附近的生成策略，而不是只沿用 250 C 候选。",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze candidate pools under multiple target Tg values.")
    parser.add_argument("--candidates", default="artifacts/agent_discovery_250/candidate_formulations.csv")
    parser.add_argument("--targets", nargs="+", type=float, default=[190.0, 195.0, 200.0, 250.0])
    parser.add_argument("--top-k", type=int, default=25)
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--out-dir", default="artifacts/trail/target_sweep")
    parser.add_argument("--report", default="reports/variable_target_tg_analysis.md")
    args = parser.parse_args()
    source = Path(args.candidates)
    df = pd.read_csv(source, low_memory=False)
    summary, top = target_sweep(df, args.targets, args.top_k, args.reward_temperature_c)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "target_sweep_summary.csv", index=False)
    top.to_csv(out_dir / "target_sweep_top_candidates.csv", index=False)
    write_report(summary, top, Path(args.report), source, args.reward_temperature_c)


if __name__ == "__main__":
    main()
