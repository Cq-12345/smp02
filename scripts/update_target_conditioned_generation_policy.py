from __future__ import annotations

import argparse
import json
import math
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


TARGET_SWEEP_STRATEGIES = {
    "functional_group_replacement": {
        "prefix": "replacement",
        "source": "feedback_guided_replacement_target_sweep",
    },
    "vae_latent_local_search": {
        "prefix": "latent",
        "source": "vae_latent_local_search_target_sweep",
    },
}

TRANSFER_STRATEGIES = [
    "llm_rag_principle_generation",
    "sft_candidate_generator",
    "diffusion_or_flow_matching",
    "llm_smiles_generation",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def bounded(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


def exp_reward_from_distance(best_distance_c: float | None, reward_temperature_c: float = 5.0) -> float | None:
    if best_distance_c is None or pd.isna(best_distance_c):
        return None
    return float(math.exp(-abs(float(best_distance_c)) / reward_temperature_c))


def rows_by_target(rows: Any) -> dict[float, dict[str, Any]]:
    if isinstance(rows, dict) and "target_values" in rows:
        return {}
    if isinstance(rows, dict) and "rows" in rows:
        rows = rows["rows"]
    if not isinstance(rows, list):
        return {}
    by_target: dict[float, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("target_tg_c") is None:
            continue
        by_target[float(row["target_tg_c"])] = row
    return by_target


def beta_pass_mean(successes: int, attempts: int) -> float:
    failures = max(0, attempts - successes)
    return float((successes + 1.0) / (successes + failures + 2.0))


def coalesce_float(*values: Any) -> float | None:
    for value in values:
        if value is None:
            continue
        if isinstance(value, float) and math.isnan(value):
            continue
        return float(value)
    return None


def target_sweep_arm(strategy: str, target_tg_c: float, row: dict[str, Any]) -> dict[str, Any]:
    config = TARGET_SWEEP_STRATEGIES[strategy]
    prefix = config["prefix"]
    attempts = int(row.get(f"{prefix}_input_proposals", 0) or 0)
    successes = int(row.get(f"{prefix}_harness_pass", 0) or 0)
    observations = int(row.get(f"{prefix}_observations", successes) or 0)
    proposal_best_distance = coalesce_float(row.get(f"{prefix}_best_distance_c"))
    selected_distance = coalesce_float(row.get("best_selected_target_distance_c"), proposal_best_distance)
    mean_reward = coalesce_float(
        row.get("pievo_external_mean_reward"),
        exp_reward_from_distance(selected_distance),
        exp_reward_from_distance(proposal_best_distance),
    )
    best_reward = coalesce_float(
        row.get("best_selected_reward"),
        exp_reward_from_distance(selected_distance),
        exp_reward_from_distance(proposal_best_distance),
    )
    pass_mean = beta_pass_mean(successes, attempts)
    utility = 0.25 * pass_mean + 0.30 * bounded(mean_reward or pass_mean) + 0.45 * bounded(best_reward or pass_mean)
    map_posterior = coalesce_float(row.get("pievo_map_principle_posterior"), 0.0) or 0.0
    posterior_uncertainty_bonus = 0.04 * (1.0 - bounded(map_posterior))
    status = "active" if successes > 0 and bool(row.get("pievo_all_selected_pass", True)) else "target_data_collection_only"
    return {
        "target_tg_c": float(target_tg_c),
        "strategy": strategy,
        "status": status,
        "evidence_scope": "target_sweep",
        "evidence_source": row.get("target_evidence_source", config["source"]),
        "attempts": attempts,
        "successes": successes,
        "failures": max(0, attempts - successes),
        "raw_pass_rate": successes / max(attempts, 1),
        "beta_pass_mean": pass_mean,
        "mean_reward": mean_reward,
        "best_selected_reward": best_reward,
        "proposal_best_distance_c": proposal_best_distance,
        "best_selected_target_distance_c": selected_distance,
        "observations": observations,
        "target_utility": utility,
        "principle_uncertainty_bonus": posterior_uncertainty_bonus,
        "target_score": utility + posterior_uncertainty_bonus,
        "readiness_gate": status == "active",
        "target_specific": True,
        "map_principle": row.get("pievo_map_principle", ""),
        "map_principle_posterior": map_posterior,
        "pievo_posterior_entropy": row.get("pievo_posterior_entropy"),
        "transfer_reference_target_tg_c": None,
        "transfer_decay_weight": 1.0,
        "allocation_pool": "target_specific",
        "allocation_fraction": 0.0,
        "allocation_per_100": 0,
        "recommended_next_action": "",
    }


def target_arms_for_target(
    target_tg_c: float,
    replacement_by_target: dict[float, dict[str, Any]],
    latent_by_target: dict[float, dict[str, Any]],
    exploration_c: float,
) -> pd.DataFrame:
    rows = []
    if target_tg_c in replacement_by_target:
        rows.append(target_sweep_arm("functional_group_replacement", target_tg_c, replacement_by_target[target_tg_c]))
    if target_tg_c in latent_by_target:
        rows.append(target_sweep_arm("vae_latent_local_search", target_tg_c, latent_by_target[target_tg_c]))
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    log_term = math.log(float(frame["attempts"].clip(lower=0).sum()) + 1.0)
    bonuses = []
    for _, row in frame.iterrows():
        attempts = max(int(row["attempts"]), 0)
        bonuses.append(float(exploration_c) * math.sqrt(log_term / (attempts + 1.0)))
    frame["target_exploration_bonus"] = bonuses
    frame["target_score"] = frame["target_score"] + frame["target_exploration_bonus"]
    return frame


def replacement_evidence_score(row: dict[str, Any]) -> tuple[int, float, float]:
    harness_pass = int(row.get("replacement_harness_pass", 0) or 0)
    selected_distance = coalesce_float(row.get("best_selected_target_distance_c"), row.get("replacement_best_distance_c"))
    eval_distance = coalesce_float(row.get("replacement_best_distance_c"))
    return (
        harness_pass,
        -(float("inf") if selected_distance is None else selected_distance),
        -(float("inf") if eval_distance is None else eval_distance),
    )


def merge_replacement_evidence(base_rows: Any, sparse_rows: Any) -> list[dict[str, Any]]:
    merged: dict[float, dict[str, Any]] = {}
    for target, row in rows_by_target(base_rows).items():
        item = dict(row)
        item["target_evidence_source"] = "feedback_guided_replacement_target_sweep"
        merged[target] = item
    for target, row in rows_by_target(sparse_rows).items():
        item = dict(row)
        item["target_evidence_source"] = "sparse_target_replacement_expansion"
        current = merged.get(target)
        if current is None or replacement_evidence_score(item) > replacement_evidence_score(current):
            merged[target] = item
    return [merged[target] for target in sorted(merged)]


def transfer_arms_for_target(
    target_tg_c: float,
    global_policy: pd.DataFrame,
    reference_target_tg_c: float,
    transfer_decay_c: float,
) -> pd.DataFrame:
    if global_policy.empty or "strategy" not in global_policy.columns:
        return pd.DataFrame()
    rows = []
    decay_weight = math.exp(-abs(float(target_tg_c) - float(reference_target_tg_c)) / max(float(transfer_decay_c), 1e-6))
    for _, row in global_policy.iterrows():
        strategy = str(row["strategy"])
        if strategy not in TRANSFER_STRATEGIES:
            continue
        status = str(row.get("status", "active"))
        readiness = bool(row.get("readiness_gate", False))
        global_fraction = float(row.get("allocation_fraction", 0.0) or 0.0)
        rows.append(
            {
                "target_tg_c": float(target_tg_c),
                "strategy": strategy,
                "status": status,
                "evidence_scope": "global_transfer",
                "evidence_source": row.get("evidence_source", "generation_strategy_bandit_policy"),
                "attempts": int(row.get("attempts", 0) or 0),
                "successes": int(row.get("successes", 0) or 0),
                "failures": int(row.get("failures", 0) or 0),
                "raw_pass_rate": float(row.get("raw_pass_rate", 0.0) or 0.0),
                "beta_pass_mean": float(row.get("beta_pass_mean", 0.0) or 0.0),
                "mean_reward": coalesce_float(row.get("mean_reward")),
                "best_selected_reward": coalesce_float(exp_reward_from_distance(row.get("best_distance_c"))),
                "proposal_best_distance_c": coalesce_float(row.get("best_distance_c")),
                "best_selected_target_distance_c": coalesce_float(row.get("best_distance_c")),
                "observations": int(row.get("observations", 0) or 0),
                "target_utility": float(row.get("utility_mean", 0.0) or 0.0),
                "principle_uncertainty_bonus": 0.0,
                "target_exploration_bonus": float(row.get("exploration_bonus", 0.0) or 0.0),
                "target_score": float(row.get("bandit_score", 0.0) or 0.0) * decay_weight,
                "readiness_gate": readiness,
                "target_specific": False,
                "map_principle": "",
                "map_principle_posterior": None,
                "pievo_posterior_entropy": None,
                "transfer_reference_target_tg_c": float(reference_target_tg_c),
                "transfer_decay_weight": decay_weight,
                "global_allocation_fraction": global_fraction,
                "allocation_pool": "global_transfer",
                "allocation_fraction": 0.0,
                "allocation_per_100": 0,
                "recommended_next_action": "",
            }
        )
    return pd.DataFrame(rows)


def allocate_softmax(frame: pd.DataFrame, budget: int, score_col: str, temperature: float) -> pd.DataFrame:
    out = frame.copy()
    out["allocation_fraction"] = 0.0
    out["allocation_per_100"] = 0
    if out.empty or budget <= 0:
        return out
    eligible = out["status"].eq("active") & out["readiness_gate"].astype(bool)
    if not eligible.any():
        return out
    scores = out.loc[eligible, score_col].to_numpy(dtype=float)
    scores = scores / max(float(temperature), 1e-6)
    scores = scores - float(np.max(scores))
    weights = np.exp(scores)
    weights = weights / weights.sum()
    out.loc[eligible, "allocation_fraction"] = weights
    out.loc[eligible, "allocation_per_100"] = np.rint(weights * int(budget)).astype(int)
    diff = int(budget) - int(out["allocation_per_100"].sum())
    if diff:
        best_index = out.loc[eligible, "allocation_fraction"].idxmax()
        out.loc[best_index, "allocation_per_100"] += diff
    return out


def allocate_by_global_fraction(frame: pd.DataFrame, budget: int) -> pd.DataFrame:
    out = frame.copy()
    out["allocation_fraction"] = 0.0
    out["allocation_per_100"] = 0
    if out.empty or budget <= 0:
        return out
    eligible = out["status"].eq("active") & out["readiness_gate"].astype(bool)
    if not eligible.any():
        return out
    weights = out.loc[eligible, "global_allocation_fraction"].to_numpy(dtype=float)
    if float(weights.sum()) <= 0.0:
        weights = np.ones(len(weights), dtype=float)
    weights = weights / weights.sum()
    out.loc[eligible, "allocation_fraction"] = weights
    out.loc[eligible, "allocation_per_100"] = np.rint(weights * int(budget)).astype(int)
    diff = int(budget) - int(out["allocation_per_100"].sum())
    if diff:
        best_index = out.loc[eligible, "allocation_fraction"].idxmax()
        out.loc[best_index, "allocation_per_100"] += diff
    return out


def add_recommended_actions(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    actions = []
    for _, row in out.iterrows():
        allocation = int(row.get("allocation_per_100", 0) or 0)
        target = float(row["target_tg_c"])
        if str(row["status"]) != "active":
            actions.append("hold: wait for predictor/chemistry/Harness evidence before allocating target budget.")
        elif bool(row.get("target_specific", False)):
            actions.append(
                f"allocate {allocation}/100 for {target:.1f} C target-conditioned proposals; rerun ledger, predictor, Harness and PiEvo."
            )
        else:
            actions.append(
                f"allocate {allocation}/100 transferable exploration budget from {float(row['transfer_reference_target_tg_c']):.1f} C evidence; validate at {target:.1f} C before use."
            )
    out["recommended_next_action"] = actions
    return out


def target_transfer_budget(
    target_tg_c: float,
    base_transfer_budget: int,
    min_transfer_budget: int,
    total_budget: int,
    reference_target_tg_c: float,
    transfer_decay_c: float,
    has_active_transfer: bool,
    has_active_target_specific: bool,
) -> int:
    if not has_active_transfer:
        return 0
    if not has_active_target_specific:
        return int(total_budget)
    decay_weight = math.exp(-abs(float(target_tg_c) - float(reference_target_tg_c)) / max(float(transfer_decay_c), 1e-6))
    budget = int(round(float(base_transfer_budget) * decay_weight))
    budget = max(int(min_transfer_budget), budget)
    return max(0, min(int(total_budget), budget))


def build_target_policy(
    replacement_rows: Any,
    latent_rows: Any,
    global_policy: pd.DataFrame,
    total_budget: int = 100,
    base_transfer_budget: int = 25,
    min_transfer_budget: int = 8,
    reference_target_tg_c: float = 195.0,
    transfer_decay_c: float = 80.0,
    softmax_temperature: float = 0.18,
    exploration_c: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    replacement_by_target = rows_by_target(replacement_rows)
    latent_by_target = rows_by_target(latent_rows)
    targets = sorted(set(replacement_by_target) | set(latent_by_target))
    all_rows = []
    target_summary_rows = []
    for target in targets:
        target_specific = target_arms_for_target(target, replacement_by_target, latent_by_target, exploration_c)
        transfer = transfer_arms_for_target(target, global_policy, reference_target_tg_c, transfer_decay_c)
        active_transfer = bool((transfer["status"].eq("active") & transfer["readiness_gate"].astype(bool)).any()) if not transfer.empty else False
        active_target_specific = (
            bool((target_specific["status"].eq("active") & target_specific["readiness_gate"].astype(bool)).any())
            if not target_specific.empty
            else False
        )
        transfer_budget = target_transfer_budget(
            target,
            base_transfer_budget,
            min_transfer_budget,
            total_budget,
            reference_target_tg_c,
            transfer_decay_c,
            active_transfer,
            active_target_specific,
        )
        target_budget = int(total_budget) - transfer_budget
        target_specific = allocate_softmax(target_specific, target_budget, "target_score", softmax_temperature)
        transfer = allocate_by_global_fraction(transfer, transfer_budget)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning, message="The behavior of DataFrame concatenation")
            combined = pd.concat([target_specific, transfer], ignore_index=True)
        if not combined.empty:
            diff = int(total_budget) - int(combined["allocation_per_100"].sum())
            eligible = combined["status"].eq("active") & combined["readiness_gate"].astype(bool)
            if diff and eligible.any():
                best_index = combined.loc[eligible, "allocation_per_100"].idxmax()
                combined.loc[best_index, "allocation_per_100"] += diff
            combined = add_recommended_actions(combined)
            combined = combined.sort_values(
                ["target_tg_c", "allocation_per_100", "target_score"],
                ascending=[True, False, False],
            ).reset_index(drop=True)
            all_rows.append(combined)
            target_specific_only = combined[combined["target_specific"].astype(bool)]
            active_combined = combined[combined["allocation_per_100"] > 0]
            top = active_combined.iloc[0]["strategy"] if not active_combined.empty else ""
            top_target_specific = (
                target_specific_only.sort_values(["allocation_per_100", "target_score"], ascending=[False, False]).iloc[0]["strategy"]
                if not target_specific_only.empty
                else ""
            )
            target_summary_rows.append(
                {
                    "target_tg_c": target,
                    "total_budget": int(total_budget),
                    "target_specific_budget": int(target_budget),
                    "transfer_budget": int(transfer_budget),
                    "allocation_sum": int(combined["allocation_per_100"].sum()),
                    "target_specific_successes": int(target_specific_only["successes"].sum()) if not target_specific_only.empty else 0,
                    "target_specific_observations": int(target_specific_only["observations"].sum()) if not target_specific_only.empty else 0,
                    "top_strategy": top,
                    "top_target_specific_strategy": top_target_specific,
                    "top_target_specific_map_principle": (
                        target_specific_only.sort_values(["allocation_per_100", "target_score"], ascending=[False, False]).iloc[0][
                            "map_principle"
                        ]
                        if not target_specific_only.empty
                        else ""
                    ),
                    "transfer_decay_weight": math.exp(
                        -abs(float(target) - float(reference_target_tg_c)) / max(float(transfer_decay_c), 1e-6)
                    ),
                    "is_sparse_target": bool((int(target_specific_only["successes"].sum()) if not target_specific_only.empty else 0) < 15),
                }
            )
    policy = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    target_summary = pd.DataFrame(target_summary_rows)
    summary = {
        "targets": int(len(targets)),
        "target_values": targets,
        "strategies_per_target": int(policy.groupby("target_tg_c")["strategy"].nunique().max()) if not policy.empty else 0,
        "total_budget_per_target": int(total_budget),
        "base_transfer_budget": int(base_transfer_budget),
        "min_transfer_budget": int(min_transfer_budget),
        "reference_transfer_target_tg_c": float(reference_target_tg_c),
        "transfer_decay_c": float(transfer_decay_c),
        "target_specific_strategies": sorted(TARGET_SWEEP_STRATEGIES),
        "transfer_strategies": TRANSFER_STRATEGIES,
        "all_targets_allocation_sum_100": bool(not target_summary.empty and (target_summary["allocation_sum"] == int(total_budget)).all()),
        "top_strategy_by_target": {
            f"{float(row['target_tg_c']):.1f}": row["top_strategy"] for _, row in target_summary.iterrows()
        },
        "top_target_specific_strategy_by_target": {
            f"{float(row['target_tg_c']):.1f}": row["top_target_specific_strategy"] for _, row in target_summary.iterrows()
        },
        "transfer_budget_by_target": {
            f"{float(row['target_tg_c']):.1f}": int(row["transfer_budget"]) for _, row in target_summary.iterrows()
        },
        "sparse_targets": [
            float(row["target_tg_c"]) for _, row in target_summary.iterrows() if bool(row["is_sparse_target"])
        ],
        "sparse_target_count": int(target_summary["is_sparse_target"].sum()) if not target_summary.empty else 0,
    }
    return policy, target_summary, summary


def write_report(policy: pd.DataFrame, target_summary: pd.DataFrame, summary: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    lines = [
        "# Target-conditioned Generation Strategy Policy",
        "",
        "本文档把“真实 Tg 不固定”的要求落成目标条件化的下一轮生成预算。它保留当前全局 strategy bandit，但不再把 195 C 附近的全局证据直接外推到所有目标。",
        "",
        "## 输出文件",
        "",
        f"- Policy table: `{out_dir / 'target_conditioned_generation_strategy_policy.csv'}`",
        f"- Target summary: `{out_dir / 'target_conditioned_generation_strategy_target_summary.csv'}`",
        f"- Summary: `{out_dir / 'target_conditioned_generation_strategy_summary.json'}`",
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
            "## Target Summary",
            "",
            "| target Tg C | target-specific budget | transferable budget | target successes | top strategy | top target-specific strategy | sparse |",
            "| ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for _, row in target_summary.iterrows():
        lines.append(
            f"| {float(row['target_tg_c']):.1f} | {int(row['target_specific_budget'])} | {int(row['transfer_budget'])} | "
            f"{int(row['target_specific_successes'])} | {row['top_strategy']} | {row['top_target_specific_strategy']} | {bool(row['is_sparse_target'])} |"
        )
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "| target Tg C | strategy | scope | status | attempts | successes | best selected distance C | score | allocation/100 | action |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for _, row in policy.iterrows():
        distance = row.get("best_selected_target_distance_c")
        distance_text = "" if distance is None or pd.isna(distance) else f"{float(distance):.3f}"
        lines.append(
            f"| {float(row['target_tg_c']):.1f} | {row['strategy']} | {row['evidence_scope']} | {row['status']} | "
            f"{int(row['attempts'])} | {int(row['successes'])} | {distance_text} | {float(row['target_score']):.3f} | "
            f"{int(row['allocation_per_100'])} | {row['recommended_next_action']} |"
        )
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- `target_sweep` 证据来自该目标 Tg 下实际跑过的 replacement/VAE latent sweep、sparse-target expansion 和 PiEvo selected reward；同一目标下会优先采用更强的 replacement evidence。",
            "- `global_transfer` 证据来自全局 strategy bandit；它只拿可迁移 exploration budget，且离 195 C 参考目标越远预算越小。",
            "- `allocation_per_100` 是下一轮 proposal 预算，不是最终配方推荐；所有候选仍必须写入 ledger，并重新经过 predictor、Harness、PiEvo 和人工审核。",
            "- `sparse_targets` 非空时，含义是目标条件化成功样本少，应优先扩大对应温区候选池或引入新 principle，而不是把 195 C 规律硬外推；当前若为空，只表示 sample-count gate 暂时通过，不表示物理真值已验证。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_target_conditioned_policy(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    replacement_rows = merge_replacement_evidence(
        read_json(Path(args.replacement_target_sweep_summary)),
        read_json(Path(args.sparse_target_replacement_expansion_summary)),
    )
    policy, target_summary, summary = build_target_policy(
        replacement_rows,
        read_json(Path(args.vae_latent_target_sweep_summary)),
        read_csv(Path(args.global_policy)),
        total_budget=int(args.total_budget),
        base_transfer_budget=int(args.transferable_exploration_budget),
        min_transfer_budget=int(args.min_transferable_budget),
        reference_target_tg_c=float(args.reference_transfer_target_tg_c),
        transfer_decay_c=float(args.transfer_decay_c),
        softmax_temperature=float(args.softmax_temperature),
        exploration_c=float(args.exploration_c),
    )
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    policy.to_csv(out_dir / "target_conditioned_generation_strategy_policy.csv", index=False)
    target_summary.to_csv(out_dir / "target_conditioned_generation_strategy_target_summary.csv", index=False)
    (out_dir / "target_conditioned_generation_strategy_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_report(policy, target_summary, summary, out_dir, Path(args.report))
    return policy, target_summary, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Update target-conditioned proposal-budget policy across generator strategies.")
    parser.add_argument(
        "--replacement-target-sweep-summary",
        default="artifacts/trail/generation/feedback_guided_replacement_target_sweep/feedback_replacement_target_sweep_summary.json",
    )
    parser.add_argument(
        "--vae-latent-target-sweep-summary",
        default="artifacts/trail/generation/vae_latent_local_search_target_sweep/vae_latent_local_search_target_sweep_summary.json",
    )
    parser.add_argument(
        "--sparse-target-replacement-expansion-summary",
        default="artifacts/trail/generation/sparse_target_replacement_expansion/sparse_target_replacement_expansion_summary.json",
    )
    parser.add_argument(
        "--global-policy",
        default="artifacts/trail/generation_strategy_policy/generation_strategy_bandit_policy.csv",
    )
    parser.add_argument("--total-budget", type=int, default=100)
    parser.add_argument("--transferable-exploration-budget", type=int, default=25)
    parser.add_argument("--min-transferable-budget", type=int, default=8)
    parser.add_argument("--reference-transfer-target-tg-c", type=float, default=195.0)
    parser.add_argument("--transfer-decay-c", type=float, default=80.0)
    parser.add_argument("--softmax-temperature", type=float, default=0.18)
    parser.add_argument("--exploration-c", type=float, default=0.15)
    parser.add_argument("--out-dir", default="artifacts/trail/generation_strategy_policy_target_conditioned")
    parser.add_argument("--report", default="reports/target_conditioned_generation_strategy_policy.md")
    args = parser.parse_args()
    run_target_conditioned_policy(args)


if __name__ == "__main__":
    main()
