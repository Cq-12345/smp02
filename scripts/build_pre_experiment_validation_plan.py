from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def read_knowledge_templates(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("process_condition_templates", {}) or {}


def number(value: Any, default: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def semicolon_list(value: Any) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def target_reward(distance_c: float, reward_temperature_c: float) -> float:
    return float(math.exp(-abs(distance_c) / reward_temperature_c))


def validation_risk_flags(row: pd.Series, high_sigma_c: float, ood_threshold: float) -> list[str]:
    flags = []
    sigma = number(row.get("predicted_tg_sigma_c"))
    ood = number(row.get("ood_penalty"))
    target = number(row.get("target_tg_c"))
    missing_fields = semicolon_list(row.get("missing_process_fields"))
    origin = str(row.get("candidate_origin", ""))
    new_component_count = number(row.get("new_component_count"))
    if missing_fields:
        flags.append("process_incomplete")
    if sigma >= high_sigma_c:
        flags.append("high_predictor_sigma")
    if ood >= ood_threshold:
        flags.append("high_ood_penalty")
    if new_component_count > 0:
        flags.append("new_component")
    if target >= 240:
        flags.append("high_tg_target")
    if "sparse_target" in origin:
        flags.append("sparse_target_origin")
    return flags


def validation_lane(flags: list[str]) -> str:
    process_needed = "process_incomplete" in flags
    high_fidelity_needed = any(flag in flags for flag in ["high_predictor_sigma", "high_ood_penalty", "high_tg_target", "sparse_target_origin"])
    if process_needed and high_fidelity_needed:
        return "process_plus_high_fidelity"
    if process_needed:
        return "process_completion_before_dsc"
    if high_fidelity_needed:
        return "high_fidelity_before_dsc"
    return "dsc_candidate_after_review"


def validation_methods(flags: list[str], process_template: str) -> list[str]:
    methods = ["process_feasibility_review", "model_ensemble_recheck"]
    if "high_predictor_sigma" in flags or "high_ood_penalty" in flags:
        methods.append("high_fidelity_simulation_or_expanded_model_ensemble")
    if "high_tg_target" in flags:
        methods.append("thermal_stability_pre_screen")
    if "sparse_target_origin" in flags:
        methods.append("target_specific_literature_check")
    if process_template == "isocyanate_urethane_urea":
        methods.append("moisture_control_review")
    if process_template == "anhydride_amine_imidization":
        methods.append("imidization_protocol_review")
    if process_template == "cyanate_ester_triazine_cure":
        methods.append("trimerization_catalyst_review")
    return methods


def next_action(lane: str) -> str:
    if lane == "process_plus_high_fidelity":
        return "complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC."
    if lane == "process_completion_before_dsc":
        return "complete process fields and feasibility review before scheduling DSC."
    if lane == "high_fidelity_before_dsc":
        return "run high-fidelity/model-ensemble validation before any DSC scheduling."
    return "eligible for DSC planning after human review."


def validation_score(row: pd.Series, flags: list[str], reward_temperature_c: float) -> float:
    distance = number(row.get("target_distance_c"), default=999.0)
    reward = target_reward(distance, reward_temperature_c)
    sigma = number(row.get("predicted_tg_sigma_c"))
    missing_count = len(semicolon_list(row.get("missing_process_fields")))
    priority_bonus = 0.12 if str(row.get("review_priority", "")) == "process_design_for_dsc" else 0.06
    target_bonus = 0.10 if "high_tg_target" in flags else 0.0
    sparse_bonus = 0.07 if "sparse_target_origin" in flags else 0.0
    uncertainty_penalty = min(sigma / 350.0, 0.25)
    burden_penalty = min(missing_count * 0.035, 0.2)
    return float(reward + priority_bonus + target_bonus + sparse_bonus - uncertainty_penalty - burden_penalty)


def build_validation_plan(
    queue_path: Path,
    knowledge_path: Path,
    top_k: int = 30,
    high_sigma_c: float = 50.0,
    ood_threshold: float = 2.0,
    reward_temperature_c: float = 5.0,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    queue = pd.read_csv(queue_path) if queue_path.exists() else pd.DataFrame()
    if queue.empty:
        empty_summary = {
            "input_review_rows": 0,
            "plan_rows": 0,
            "process_completion_required_rows": 0,
            "high_fidelity_required_rows": 0,
            "dsc_ready_without_process_completion_rows": 0,
            "target_counts": {},
            "validation_lane_counts": {},
            "candidate_origin_counts": {},
            "best_target_distance_c": None,
            "best_validation_score": None,
        }
        return pd.DataFrame(), empty_summary

    templates = read_knowledge_templates(knowledge_path)
    records = []
    for _, row in queue.iterrows():
        process_template = str(row.get("process_template", ""))
        flags = validation_risk_flags(row, high_sigma_c=high_sigma_c, ood_threshold=ood_threshold)
        lane = validation_lane(flags)
        missing_fields = semicolon_list(row.get("missing_process_fields"))
        template = templates.get(process_template, {})
        methods = validation_methods(flags, process_template)
        records.append(
            {
                "review_rank": int(number(row.get("review_rank"), default=0)),
                "linked_observation_id": row.get("linked_observation_id", ""),
                "target_tg_c": number(row.get("target_tg_c")),
                "observed_tg_c": number(row.get("observed_tg_c")),
                "target_distance_c": number(row.get("target_distance_c")),
                "predicted_tg_sigma_c": number(row.get("predicted_tg_sigma_c")),
                "candidate_origin": row.get("candidate_origin", ""),
                "reaction_principle": row.get("reaction_principle", ""),
                "process_template": process_template,
                "template_trigger": template.get("trigger", ""),
                "template_catalyst": template.get("catalyst", ""),
                "template_notes": template.get("notes", ""),
                "missing_process_fields": ";".join(missing_fields),
                "missing_process_field_count": len(missing_fields),
                "risk_flags": ";".join(flags),
                "validation_lane": lane,
                "validation_methods": ";".join(methods),
                "process_completion_required": bool(missing_fields),
                "high_fidelity_required": lane in {"process_plus_high_fidelity", "high_fidelity_before_dsc"},
                "dsc_ready_without_process_completion": lane == "dsc_candidate_after_review",
                "recommended_next_action": next_action(lane),
                "validation_score": validation_score(row, flags, reward_temperature_c=reward_temperature_c),
                "smiles": row.get("smiles", ""),
                "ratios": row.get("ratios", ""),
            }
        )
    plan = pd.DataFrame(records)
    plan = plan.sort_values(["validation_score", "target_distance_c"], ascending=[False, True]).head(top_k).copy()
    plan.insert(0, "validation_rank", range(1, len(plan) + 1))
    summary = {
        "input_review_rows": int(len(queue)),
        "plan_rows": int(len(plan)),
        "process_completion_required_rows": int(plan["process_completion_required"].sum()),
        "high_fidelity_required_rows": int(plan["high_fidelity_required"].sum()),
        "dsc_ready_without_process_completion_rows": int(plan["dsc_ready_without_process_completion"].sum()),
        "target_counts": {f"{float(key):.1f}": int(value) for key, value in plan["target_tg_c"].value_counts().sort_index().items()},
        "validation_lane_counts": plan["validation_lane"].value_counts().to_dict(),
        "candidate_origin_counts": plan["candidate_origin"].value_counts().to_dict(),
        "best_target_distance_c": float(plan["target_distance_c"].min()) if len(plan) else None,
        "best_validation_score": float(plan["validation_score"].max()) if len(plan) else None,
    }
    return plan, summary


def write_report(plan: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pre-experiment Validation Plan",
        "",
        "本文档把人工复核队列推进为高保真/真实实验前的验证计划。它不会把 surrogate 候选升级为真实 observation，只给出人工补工艺和高保真复核顺序。",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, dict):
            continue
        lines.append(f"| {key} | {value} |")
    for title, counts in [
        ("Target Tg Distribution", summary.get("target_counts", {})),
        ("Validation Lane Distribution", summary.get("validation_lane_counts", {})),
        ("Candidate Origin Distribution", summary.get("candidate_origin_counts", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| item | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Top Validation Items",
            "",
            "| rank | target Tg (C) | Tg (C) | distance (C) | sigma (C) | lane | origin | template | flags | action |",
            "| ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for _, row in plan.head(15).iterrows():
        lines.append(
            f"| {int(row['validation_rank'])} | {float(row['target_tg_c']):.1f} | {float(row['observed_tg_c']):.2f} | "
            f"{float(row['target_distance_c']):.3f} | {float(row['predicted_tg_sigma_c']):.2f} | "
            f"{row['validation_lane']} | {row['candidate_origin']} | {row['process_template']} | "
            f"{row['risk_flags']} | {row['recommended_next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Gate Rules",
            "",
            "- `process_completion_required=true` 表示仍需人工补齐工艺字段，不能进入 active high-authority ledger。",
            "- `high_fidelity_required=true` 表示预测不确定性、高 Tg 稀疏目标或 OOD 风险较高，应先做高保真/集成模型复核。",
            "- 只有人工补齐工艺、真实或高保真观测完成并显式批准后，才允许写入高权重 observation ledger。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default="artifacts/trail/human_review/human_experiment_review_queue.csv")
    parser.add_argument("--knowledge", default="trail/knowledge/smp_prior_knowledge.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/pre_experiment_validation_plan.md")
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--high-sigma-c", type=float, default=50.0)
    parser.add_argument("--ood-threshold", type=float, default=2.0)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plan, summary = build_validation_plan(
        Path(args.queue),
        Path(args.knowledge),
        top_k=args.top_k,
        high_sigma_c=args.high_sigma_c,
        ood_threshold=args.ood_threshold,
    )
    plan_path = out_dir / "pre_experiment_validation_plan.csv"
    summary_path = out_dir / "pre_experiment_validation_plan_summary.json"
    plan.to_csv(plan_path, index=False)
    summary = {
        **summary,
        "plan_path": str(plan_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(plan, summary, Path(args.report))


if __name__ == "__main__":
    main()
