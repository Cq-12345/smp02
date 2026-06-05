from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPLACEMENT_FAILURE_GROUP_COLUMNS = [
    "shared_groups",
    "failures",
    "mean_tanimoto",
    "top_reason",
    "feedback",
]


def split_reasons(value: object) -> list[str]:
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.replace("|", ";").split(";") if part.strip()]


def recommended_action(reason: str) -> str:
    if reason.startswith("missing_required_fields"):
        return "block_before_harness: require complete generation record fields."
    if reason == "unknown_strategy":
        return "block_before_harness: register the generator strategy first."
    if reason == "invalid_smiles":
        return "rdkit_feedback: regenerate or canonicalize SMILES before prediction."
    if reason == "ratio_sum_not_one":
        return "ratio_feedback: renormalize candidate_ratios to simplex before scoring."
    if reason == "prediction_missing":
        return "predictor_feedback: run VAE-WVCM/GNN predictor before recommendation."
    if reason == "target_out_of_window":
        return "target_feedback: condition generation on target_tg_c and target_window_c."
    if reason == "chemistry_evidence_missing":
        return "chemistry_feedback: require compatibility_reasons from functional-group rules."
    if reason == "replacement_formula_failed_reaction_or_ratio_constraints":
        return "replacement_feedback: preserve complementary reactive pair, not only shared groups."
    if reason == "duplicate_replacement_formula":
        return "diversity_feedback: deduplicate by canonical formulation key before prediction."
    return "manual_review: inspect failure and add a typed feedback rule."


def strategy_policy_delta(pass_rate: float, fail_rows: int) -> float:
    if fail_rows <= 0 and pass_rate >= 0.75:
        return 0.10
    if pass_rate >= 0.75:
        return 0.05
    if pass_rate >= 0.50:
        return 0.0
    if pass_rate > 0.0:
        return -0.10
    return -0.25


def load_generation_ledger(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_replacement_rejections(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty:
        return df
    df = df.copy()
    df["strategy"] = "functional_group_replacement"
    df["harness_pass"] = False
    df["harness_failure_reason"] = df["reason"]
    return df


def failure_reason_counts(*frames: pd.DataFrame) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    by_strategy: Counter[tuple[str, str]] = Counter()
    for frame in frames:
        if frame.empty or "harness_failure_reason" not in frame.columns:
            continue
        for _, row in frame.iterrows():
            strategy = str(row.get("strategy", "unknown"))
            for reason in split_reasons(row.get("harness_failure_reason", "")):
                counter[reason] += 1
                by_strategy[(strategy, reason)] += 1
    rows = []
    for reason, count in counter.most_common():
        strategies = {
            strategy: value
            for (strategy, reason_key), value in by_strategy.items()
            if reason_key == reason
        }
        rows.append(
            {
                "failure_reason": reason,
                "count": int(count),
                "strategy_counts": json.dumps(strategies, ensure_ascii=False, sort_keys=True),
                "recommended_action": recommended_action(reason),
            }
        )
    return pd.DataFrame(rows)


def strategy_feedback(generation: pd.DataFrame, replacement_rejections: pd.DataFrame) -> pd.DataFrame:
    frames = []
    if not generation.empty:
        frames.append(generation[["strategy", "harness_pass", "generation_reward", "harness_failure_reason"]].copy())
    if not replacement_rejections.empty:
        tmp = replacement_rejections[["strategy", "harness_pass", "harness_failure_reason"]].copy()
        tmp["generation_reward"] = np.nan
        frames.append(tmp)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    rows = []
    for strategy, frame in combined.groupby("strategy"):
        total = int(len(frame))
        passes = int(frame["harness_pass"].fillna(False).astype(bool).sum())
        fails = total - passes
        pass_rate = passes / max(total, 1)
        reasons = Counter(reason for value in frame["harness_failure_reason"] for reason in split_reasons(value))
        top_reason = reasons.most_common(1)[0][0] if reasons else ""
        rows.append(
            {
                "strategy": strategy,
                "records": total,
                "harness_pass": passes,
                "harness_fail": fails,
                "pass_rate": pass_rate,
                "mean_generation_reward": (
                    float(pd.to_numeric(frame["generation_reward"], errors="coerce").dropna().mean())
                    if pd.to_numeric(frame["generation_reward"], errors="coerce").dropna().size
                    else None
                ),
                "top_failure_reason": top_reason,
                "policy_weight_delta": strategy_policy_delta(pass_rate, fails),
                "next_constraint": recommended_action(top_reason) if top_reason else "retain: keep strategy in candidate generator pool.",
            }
        )
    return pd.DataFrame(rows).sort_values(["policy_weight_delta", "pass_rate"], ascending=[False, False])


def replacement_failure_groups(rejections: pd.DataFrame) -> pd.DataFrame:
    if rejections.empty or "shared_groups" not in rejections.columns:
        return pd.DataFrame(columns=REPLACEMENT_FAILURE_GROUP_COLUMNS)
    rows = []
    for groups, frame in rejections.groupby("shared_groups"):
        rows.append(
            {
                "shared_groups": groups,
                "failures": int(len(frame)),
                "mean_tanimoto": float(pd.to_numeric(frame["tanimoto"], errors="coerce").mean()),
                "top_reason": frame["reason"].value_counts().idxmax(),
                "feedback": "Require a complementary co-reactant check after replacement; shared groups alone are insufficient.",
            }
        )
    return pd.DataFrame(rows, columns=REPLACEMENT_FAILURE_GROUP_COLUMNS).sort_values("failures", ascending=False)


def write_report(
    summary: dict[str, Any],
    strategy_df: pd.DataFrame,
    reason_df: pd.DataFrame,
    group_df: pd.DataFrame,
    report_path: Path,
    out_dir: Path,
) -> None:
    lines = [
        "# Generation Failure Feedback Analysis",
        "",
        "本文档回应 TODO 中“生成 -> 预测/评估 -> 优化（改进假设）”和“人工闭环/失败回流”的要求。当前仍使用单一小分子 SMILES / MoleCode，不涉及商品级组分或聚合物超图表示。",
        "",
        "## Outputs",
        "",
        f"- Strategy feedback: `{out_dir / 'strategy_feedback.csv'}`",
        f"- Failure reasons: `{out_dir / 'failure_reason_counts.csv'}`",
        f"- Replacement failure groups: `{out_dir / 'replacement_failure_groups.csv'}`",
        f"- Summary: `{out_dir / 'generation_feedback_summary.json'}`",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, (dict, list)):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Strategy Feedback",
            "",
            "| strategy | records | pass rate | policy delta | top failure | next constraint |",
            "| --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for _, row in strategy_df.iterrows():
        lines.append(
            f"| {row['strategy']} | {int(row['records'])} | {float(row['pass_rate']):.3f} | "
            f"{float(row['policy_weight_delta']):.2f} | {row['top_failure_reason']} | {row['next_constraint']} |"
        )
    lines.extend(
        [
            "",
            "## Failure Reasons",
            "",
            "| reason | count | action |",
            "| --- | ---: | --- |",
        ]
    )
    for _, row in reason_df.iterrows():
        lines.append(f"| {row['failure_reason']} | {int(row['count'])} | {row['recommended_action']} |")
    lines.extend(
        [
            "",
            "## Replacement Group Feedback",
            "",
            "| shared groups | failures | mean tanimoto | feedback |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    if group_df.empty:
        lines.append("| none | 0 | 0.000 | no replacement failure groups |")
    else:
        for _, row in group_df.head(12).iterrows():
            lines.append(f"| {row['shared_groups']} | {int(row['failures'])} | {float(row['mean_tanimoto']):.3f} | {row['feedback']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- 失败回流现在是一个可运行的审计步骤，而不是只在报告里口头说明。",
            "- `policy_weight_delta` 不是物理真理或最终 RL policy；它是下一轮生成器排序/人工审核优先级的建议权重。",
        ]
    )
    if int(summary.get("replacement_rejections", 0)) > 0:
        lines.append(
            "- 当前 replacement 失败集中在 `replacement_formula_failed_reaction_or_ratio_constraints`，说明“共享官能团相似”不足以保证完整配方可反应。"
        )
    else:
        lines.append(
            "- 当前 replacement rejection 输入为 0；若 replacement strategy pass rate 上升，说明前一轮互补反应对约束已经修复了主要失败路径。"
        )
    lines.append("- `llm_smiles_generation` 草案必须先补预测和化学兼容证据，再允许进入 PiEvo IDS 或实验推荐。")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze_feedback(generation_path: Path, replacement_rejections_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    generation = load_generation_ledger(generation_path)
    replacement_rejections = load_replacement_rejections(replacement_rejections_path)
    strategy_df = strategy_feedback(generation, replacement_rejections)
    reason_df = failure_reason_counts(generation, replacement_rejections)
    group_df = replacement_failure_groups(replacement_rejections)
    summary = {
        "generation_records": int(len(generation)),
        "generation_harness_pass": int(generation["harness_pass"].fillna(False).astype(bool).sum()) if not generation.empty else 0,
        "generation_harness_fail": int((~generation["harness_pass"].fillna(False).astype(bool)).sum()) if not generation.empty else 0,
        "replacement_rejections": int(len(replacement_rejections)),
        "failure_reason_types": int(len(reason_df)),
        "strategies_analyzed": int(len(strategy_df)),
        "top_failure_reason": reason_df.iloc[0]["failure_reason"] if not reason_df.empty else "",
        "lowest_policy_strategy": strategy_df.sort_values("policy_weight_delta").iloc[0]["strategy"] if not strategy_df.empty else "",
    }
    return strategy_df, reason_df, group_df, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze generated SMP hypotheses and produce failure-feedback policy hints.")
    parser.add_argument("--generation-ledger", default="artifacts/trail/generation/prompt_records/generation_record_ledger.csv")
    parser.add_argument("--replacement-rejections", default="artifacts/trail/generation/replacement_eval/replacement_proposal_rejections.csv")
    parser.add_argument("--out-dir", default="artifacts/trail/generation_feedback")
    parser.add_argument("--report", default="reports/generation_failure_feedback.md")
    args = parser.parse_args()
    strategy_df, reason_df, group_df, summary = analyze_feedback(Path(args.generation_ledger), Path(args.replacement_rejections))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    strategy_df.to_csv(out_dir / "strategy_feedback.csv", index=False)
    reason_df.to_csv(out_dir / "failure_reason_counts.csv", index=False)
    group_df.to_csv(out_dir / "replacement_failure_groups.csv", index=False)
    (out_dir / "generation_feedback_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(summary, strategy_df, reason_df, group_df, Path(args.report), out_dir)


if __name__ == "__main__":
    main()
