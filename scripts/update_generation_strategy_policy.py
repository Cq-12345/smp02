from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


STRATEGY_ORDER = [
    "vae_latent_local_search",
    "functional_group_replacement",
    "llm_rag_principle_generation",
    "llm_smiles_generation",
    "sft_candidate_generator",
    "diffusion_or_flow_matching",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def exp_reward_from_distance(best_distance_c: float | None, reward_temperature_c: float = 5.0) -> float | None:
    if best_distance_c is None or pd.isna(best_distance_c):
        return None
    return float(math.exp(-abs(float(best_distance_c)) / reward_temperature_c))


def bounded(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def feedback_lookup(strategy_feedback: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if strategy_feedback.empty or "strategy" not in strategy_feedback.columns:
        return {}
    return {str(row["strategy"]): row.to_dict() for _, row in strategy_feedback.iterrows()}


def arm_from_eval_summary(strategy: str, summary: dict[str, Any], feedback: dict[str, dict[str, Any]]) -> dict[str, Any]:
    attempts = int(summary.get("input_proposals", summary.get("input_rows", 0)) or 0)
    successes = int(summary.get("harness_pass", summary.get("harness_pass_rows", 0)) or 0)
    best_distance = summary.get("best_distance_c")
    reward = exp_reward_from_distance(best_distance)
    fb = feedback.get(strategy, {})
    return {
        "strategy": strategy,
        "status": "active",
        "evidence_source": "proposal_eval_summary",
        "attempts": attempts,
        "successes": successes,
        "failures": max(0, attempts - successes),
        "raw_pass_rate": successes / max(attempts, 1),
        "mean_reward": reward,
        "best_distance_c": best_distance,
        "observations": int(summary.get("replacement_observations", successes) or 0),
        "feedback_delta": float(fb.get("policy_weight_delta", 0.0) or 0.0),
        "readiness_gate": True,
        "readiness_reason": "proposal generator is executable; every output still requires predictor/Harness/PiEvo.",
        "next_constraint": fb.get("next_constraint", "retain: keep strategy in candidate generator pool."),
    }


def arm_from_generation_summary(strategy: str, summary: dict[str, Any], feedback: dict[str, dict[str, Any]]) -> dict[str, Any]:
    attempts = int(summary.get("input_rows", 0) or 0)
    successes = int(summary.get("harness_pass_rows", 0) or 0)
    best_distance = summary.get("best_distance_c")
    reward = summary.get("mean_generation_reward")
    if reward is None:
        reward = exp_reward_from_distance(best_distance)
    fb = feedback.get(strategy, {})
    return {
        "strategy": strategy,
        "status": "active",
        "evidence_source": "generation_record_summary",
        "attempts": attempts,
        "successes": successes,
        "failures": max(0, attempts - successes),
        "raw_pass_rate": successes / max(attempts, 1),
        "mean_reward": None if reward is None else float(reward),
        "best_distance_c": best_distance,
        "observations": successes,
        "feedback_delta": float(fb.get("policy_weight_delta", 0.0) or 0.0),
        "readiness_gate": True,
        "readiness_reason": "generation records can be emitted, but must stay behind ledger/Harness/PiEvo gates.",
        "next_constraint": fb.get("next_constraint", "retain: keep strategy in candidate generator pool."),
    }


def arm_from_feedback_only(strategy: str, feedback: dict[str, dict[str, Any]]) -> dict[str, Any]:
    fb = feedback.get(strategy, {})
    attempts = int(fb.get("records", 0) or 0)
    successes = int(fb.get("harness_pass", 0) or 0)
    return {
        "strategy": strategy,
        "status": "suppressed" if attempts and successes == 0 else "active",
        "evidence_source": "strategy_feedback",
        "attempts": attempts,
        "successes": successes,
        "failures": max(0, attempts - successes),
        "raw_pass_rate": successes / max(attempts, 1),
        "mean_reward": None if pd.isna(fb.get("mean_generation_reward", np.nan)) else float(fb.get("mean_generation_reward")),
        "best_distance_c": None,
        "observations": successes,
        "feedback_delta": float(fb.get("policy_weight_delta", 0.0) or 0.0),
        "readiness_gate": successes > 0,
        "readiness_reason": "strategy has no validated successful records yet." if successes == 0 else "strategy has at least one successful record.",
        "next_constraint": fb.get("next_constraint", "manual_review: add typed feedback before expanding this strategy."),
    }


def arm_from_training_readiness(strategy: str, summary: dict[str, Any]) -> dict[str, Any]:
    if strategy == "sft_candidate_generator":
        examples = int(summary.get("sft_examples", 0) or 0)
        ready = bool(summary.get("sft_ready", False))
        needed = int(summary.get("next_data_needed_for_sft", 0) or 0)
        minimum = int(summary.get("sft_min_examples", 0) or 0)
    else:
        examples = int(summary.get("diffusion_flow_seed_rows", 0) or 0)
        ready = bool(summary.get("diffusion_flow_ready", False))
        needed = int(summary.get("next_data_needed_for_diffusion_flow", 0) or 0)
        minimum = int(summary.get("diffusion_flow_min_examples", 0) or 0)
    return {
        "strategy": strategy,
        "status": "active" if ready else "data_collection_only",
        "evidence_source": "generative_training_readiness",
        "attempts": examples,
        "successes": examples if ready else 0,
        "failures": needed,
        "raw_pass_rate": bounded(examples / max(minimum, 1)) if minimum else 0.0,
        "mean_reward": None,
        "best_distance_c": None,
        "observations": examples,
        "feedback_delta": 0.0,
        "readiness_gate": ready,
        "readiness_reason": "ready for training" if ready else f"not ready; need {needed} more validated records before training.",
        "next_constraint": (
            "run SFT dry-run or training job with generation_record JSONL, then evaluate behind predictor/Harness/PiEvo gates."
            if ready
            else "collect more Harness-passing, prediction-backed generation records before training."
        ),
    }


def arm_from_sft_generation_or_training(
    sft_generation_summary: dict[str, Any],
    training_summary: dict[str, Any],
    feedback: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if int(sft_generation_summary.get("input_rows", 0) or 0) <= 0:
        return arm_from_training_readiness("sft_candidate_generator", training_summary)
    arm = arm_from_generation_summary("sft_candidate_generator", sft_generation_summary, feedback)
    arm["evidence_source"] = "sft_dry_run_generation_record_summary"
    if not bool(training_summary.get("sft_ready", False)):
        arm["status"] = "data_collection_only"
        arm["readiness_gate"] = False
        arm["readiness_reason"] = "SFT dry-run exists, but SFT corpus readiness gate is not currently satisfied."
        arm["next_constraint"] = "collect more Harness-passing, prediction-backed generation records before training."
        return arm
    arm["readiness_gate"] = True
    arm["readiness_reason"] = "SFT dry-run generated auditable records; replace dry-run with trained SFT only behind the same gates."
    arm["next_constraint"] = "replace prototype dry-run with neural SFT or keep collecting validated records; always evaluate behind predictor/Harness/PiEvo gates."
    return arm


def collect_arms(
    strategy_feedback: pd.DataFrame,
    expanded_replacement: dict[str, Any],
    latent_local_search_eval: dict[str, Any],
    expanded_generation: dict[str, Any],
    training_summary: dict[str, Any],
    sft_generation_summary: dict[str, Any] | None = None,
) -> pd.DataFrame:
    feedback = feedback_lookup(strategy_feedback)
    sft_generation_summary = sft_generation_summary or {}
    arms = [
        arm_from_eval_summary("vae_latent_local_search", latent_local_search_eval, feedback),
        arm_from_eval_summary("functional_group_replacement", expanded_replacement, feedback),
        arm_from_generation_summary("llm_rag_principle_generation", expanded_generation, feedback),
        arm_from_feedback_only("llm_smiles_generation", feedback),
        arm_from_sft_generation_or_training(sft_generation_summary, training_summary, feedback),
        arm_from_training_readiness("diffusion_or_flow_matching", training_summary),
    ]
    return pd.DataFrame(arms)


def score_policy(arms: pd.DataFrame, exploration_c: float, softmax_temperature: float, total_budget: int) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = arms.copy()
    total_attempts = int(frame["attempts"].clip(lower=0).sum())
    log_term = math.log(max(total_attempts, 1) + 1.0)
    scores = []
    for _, row in frame.iterrows():
        attempts = max(int(row["attempts"]), 0)
        successes = max(int(row["successes"]), 0)
        failures = max(int(row["failures"]), 0)
        beta_pass_mean = (successes + 1.0) / (successes + failures + 2.0)
        reward = row["mean_reward"]
        reward = beta_pass_mean if reward is None or pd.isna(reward) else float(reward)
        utility_mean = 0.55 * beta_pass_mean + 0.45 * bounded(reward)
        exploration_bonus = exploration_c * math.sqrt(log_term / (attempts + 1.0))
        readiness_penalty = 0.0 if bool(row["readiness_gate"]) else 0.55
        suppression_penalty = 0.35 if str(row["status"]) == "suppressed" else 0.0
        score = utility_mean + exploration_bonus + float(row["feedback_delta"]) - readiness_penalty - suppression_penalty
        scores.append(
            {
                "beta_pass_mean": beta_pass_mean,
                "utility_mean": utility_mean,
                "exploration_bonus": exploration_bonus,
                "readiness_penalty": readiness_penalty,
                "bandit_score": score,
            }
        )
    scored = pd.concat([frame, pd.DataFrame(scores)], axis=1)
    eligible = scored["status"].isin(["active"]) & scored["readiness_gate"].astype(bool)
    raw = np.full(len(scored), -np.inf, dtype=float)
    if eligible.any():
        raw[eligible.to_numpy()] = scored.loc[eligible, "bandit_score"].to_numpy(dtype=float) / max(softmax_temperature, 1e-6)
        raw_max = float(np.max(raw[eligible.to_numpy()]))
        weights = np.zeros(len(scored), dtype=float)
        weights[eligible.to_numpy()] = np.exp(raw[eligible.to_numpy()] - raw_max)
        weights = weights / weights.sum()
    else:
        weights = np.zeros(len(scored), dtype=float)
    scored["allocation_fraction"] = weights
    scored["allocation_per_100"] = np.rint(weights * int(total_budget)).astype(int)
    diff = int(total_budget) - int(scored["allocation_per_100"].sum())
    if diff and eligible.any():
        best_index = scored.loc[eligible, "allocation_fraction"].idxmax()
        scored.loc[best_index, "allocation_per_100"] += diff
    scored["human_review_priority"] = [
        human_review_priority(row)
        for _, row in scored.iterrows()
    ]
    scored["recommended_next_action"] = [
        recommended_next_action(row)
        for _, row in scored.iterrows()
    ]
    scored = scored.sort_values(["allocation_fraction", "bandit_score"], ascending=[False, False]).reset_index(drop=True)
    summary = {
        "strategies": int(len(scored)),
        "eligible_active_strategies": int(eligible.sum()),
        "total_attempts": total_attempts,
        "total_budget": int(total_budget),
        "top_strategy": scored.iloc[0]["strategy"] if not scored.empty else "",
        "suppressed_strategies": int((scored["status"] == "suppressed").sum()),
        "data_collection_only_strategies": int((scored["status"] == "data_collection_only").sum()),
    }
    return scored, summary


def human_review_priority(row: pd.Series) -> str:
    if str(row["status"]) in {"suppressed", "data_collection_only"}:
        return "gate_review"
    if row.get("best_distance_c") is not None and not pd.isna(row.get("best_distance_c")) and float(row["best_distance_c"]) <= 1.0:
        return "high"
    if float(row.get("allocation_fraction", 0.0)) >= 0.25:
        return "medium"
    return "normal"


def recommended_next_action(row: pd.Series) -> str:
    if str(row["status"]) == "data_collection_only":
        return str(row["next_constraint"])
    if str(row["status"]) == "suppressed":
        return str(row["next_constraint"])
    allocation = int(row.get("allocation_per_100", 0))
    return f"allocate {allocation}/100 next-round proposal budget; keep predictor/Harness/PiEvo gates active."


def write_report(policy: pd.DataFrame, summary: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    lines = [
        "# Generation Strategy Bandit Policy",
        "",
        "本文档把 TODO 中“RL、人工闭环、搜索空间优化”的部分落成一个可审计的 strategy-level contextual bandit。这里的 arm 是生成策略，reward 来自 Harness pass、target reward 和 observation throughput；它不是物理真理，也不替代 PiEvo IDS。",
        "",
        "## 输出文件",
        "",
        f"- Policy table: `{out_dir / 'generation_strategy_bandit_policy.csv'}`",
        f"- Summary: `{out_dir / 'generation_strategy_bandit_summary.json'}`",
        f"- Report: `{report_path}`",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "| strategy | status | attempts | successes | beta pass mean | utility | UCB bonus | score | allocation/100 | review | action |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for _, row in policy.iterrows():
        lines.append(
            f"| {row['strategy']} | {row['status']} | {int(row['attempts'])} | {int(row['successes'])} | "
            f"{float(row['beta_pass_mean']):.3f} | {float(row['utility_mean']):.3f} | "
            f"{float(row['exploration_bonus']):.3f} | {float(row['bandit_score']):.3f} | "
            f"{int(row['allocation_per_100'])} | {row['human_review_priority']} | {row['recommended_next_action']} |"
        )
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- `allocation_per_100` 是下一轮生成预算建议，不是最终推荐配方。",
            "- `sft_candidate_generator` 只有在 SFT JSONL 达到最小样本和 eval split 后才会成为 active arm；否则只保留数据收集建议。",
            "- `diffusion_or_flow_matching` 在 seed table 未达到最小样本前不获得训练/生成预算，只获得数据收集建议。",
            "- `llm_smiles_generation` 若仍缺 predictor 或 chemistry evidence，会被压到 gate review，而不是进入 PiEvo 或实验推荐。",
            "- 高 allocation 的策略仍必须把候选写入 generation/proposal ledger，再经过 predictor、Harness、PiEvo 和人工审核。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_policy(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    arms = collect_arms(
        read_csv(Path(args.strategy_feedback)),
        read_json(Path(args.expanded_replacement_summary)),
        read_json(Path(args.vae_latent_local_search_eval_summary)),
        read_json(Path(args.expanded_generation_summary)),
        read_json(Path(args.generative_training_summary)),
        read_json(Path(getattr(args, "sft_generation_summary", "artifacts/trail/generation/sft_candidate_dry_run/generation_record_summary.json"))),
    )
    policy, summary = score_policy(
        arms,
        exploration_c=float(args.exploration_c),
        softmax_temperature=float(args.softmax_temperature),
        total_budget=int(args.total_budget),
    )
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    policy.to_csv(out_dir / "generation_strategy_bandit_policy.csv", index=False)
    (out_dir / "generation_strategy_bandit_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(policy, summary, out_dir, Path(args.report))
    return policy, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Update generation strategy allocation with a small contextual-bandit policy.")
    parser.add_argument("--strategy-feedback", default="artifacts/trail/generation_feedback_strict/strategy_feedback.csv")
    parser.add_argument("--expanded-replacement-summary", default="artifacts/trail/generation/expanded_inventory_replacement_eval/replacement_eval_summary.json")
    parser.add_argument("--vae-latent-local-search-eval-summary", default="artifacts/trail/generation/vae_latent_local_search_eval/replacement_eval_summary.json")
    parser.add_argument("--expanded-generation-summary", default="artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag/generation_record_summary.json")
    parser.add_argument("--generative-training-summary", default="artifacts/trail/generation/generative_training_sets/generative_training_summary.json")
    parser.add_argument("--sft-generation-summary", default="artifacts/trail/generation/sft_candidate_dry_run/generation_record_summary.json")
    parser.add_argument("--exploration-c", type=float, default=0.25)
    parser.add_argument("--softmax-temperature", type=float, default=0.25)
    parser.add_argument("--total-budget", type=int, default=100)
    parser.add_argument("--out-dir", default="artifacts/trail/generation_strategy_policy")
    parser.add_argument("--report", default="reports/generation_strategy_bandit_policy.md")
    args = parser.parse_args()
    run_policy(args)


if __name__ == "__main__":
    main()
