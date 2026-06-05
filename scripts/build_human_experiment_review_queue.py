from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from trail.experiments.import_process_records import (  # noqa: E402
    import_process_records,
    process_templates,
    ratios_sum_ok,
    required_process_fields,
    smiles_valid,
)


REACTION_TEXT_TO_PRINCIPLE = [
    ("环氧-伯胺", "epoxy_primary_amine"),
    ("环氧-仲胺", "epoxy_secondary_amine"),
    ("环氧-酸酐", "epoxy_anhydride"),
    ("环氧-羧酸", "epoxy_carboxylic_acid"),
    ("环氧-羟基", "epoxy_hydroxyl"),
    ("酸酐-胺", "anhydride_primary_amine"),
    ("酸酐-羟基", "anhydride_hydroxyl"),
    ("异氰酸酯-伯胺", "isocyanate_primary_amine"),
    ("异氰酸酯-仲胺", "isocyanate_secondary_amine"),
    ("异氰酸酯-羟基", "isocyanate_hydroxyl"),
    ("氰酸酯-胺", "cyanate_ester_amine"),
    ("氰酸酯-酚", "cyanate_ester_phenol"),
    ("氰酸酯三聚", "cyanate_ester_self"),
    ("马来酰亚胺与烯基", "maleimide_vinyl"),
    ("马来酰亚胺-胺", "maleimide_amine"),
    ("马来酰亚胺-硫醇", "maleimide_thiol"),
    ("硫醇-烯", "thiol_ene"),
    ("自由基", "acrylate_vinyl_radical"),
]


PROCESS_RECORD_COLUMNS = [
    "process_record_id",
    "linked_observation_id",
    "source_type",
    "target_tg_c",
    "observed_tg_c",
    "smiles",
    "ratios",
    "reaction_principle",
    "process_template",
    "review_status",
    "literature_source",
    "operator",
    "catalyst",
    "catalyst_loading",
    "cure_temperature_c",
    "cure_time_h",
    "post_cure_temperature_c",
    "post_cure_time_h",
    "imidization_temperature_c",
    "imidization_time_h",
    "trimerization_temperature_c",
    "initiator_type",
    "initiator_loading",
    "moisture_control",
    "nco_index",
    "notes",
]


def split_reactions(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).replace("|", ";").split(";") if part.strip()]


def infer_reaction_principle(reaction_text: object) -> str:
    text = ";".join(split_reactions(reaction_text))
    for marker, principle in REACTION_TEXT_TO_PRINCIPLE:
        if marker in text:
            return principle
    return "manual_reaction_assignment_required"


def process_template_for_principle(principle: str, knowledge: dict[str, Any]) -> str:
    reaction_map = knowledge.get("reaction_evidence_map", {})
    item = reaction_map.get(principle, {})
    return str(item.get("process_template", "manual_process_template_required"))


def read_knowledge(path: Path) -> dict[str, Any]:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def numeric(row: pd.Series, columns: list[str], default: float | None = None) -> float | None:
    for column in columns:
        if column in row and pd.notna(row[column]):
            try:
                return float(row[column])
            except ValueError:
                continue
    return default


def text_value(row: pd.Series, columns: list[str], default: str = "") -> str:
    for column in columns:
        if column in row and pd.notna(row[column]) and str(row[column]).strip():
            return str(row[column]).strip()
    return default


def target_reward(distance_c: float | None, reward_temperature_c: float) -> float:
    if distance_c is None:
        return 0.0
    return float(math.exp(-abs(distance_c) / reward_temperature_c))


def normalize_candidate_table(path: Path, origin: str, limit: int | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty:
        return pd.DataFrame()
    if "harness_pass" in df.columns:
        df = df[df["harness_pass"].fillna(False).astype(bool)].copy()
    if "ledger_pass" in df.columns:
        df = df[df["ledger_pass"].fillna(False).astype(bool)].copy()
    if "target_distance_c" in df.columns:
        df = df.sort_values("target_distance_c", ascending=True)
    if limit is not None:
        df = df.head(limit).copy()
    rows = []
    for idx, row in df.iterrows():
        smiles = text_value(row, ["smiles", "candidate_smiles"])
        ratios = text_value(row, ["ratios", "candidate_ratios"])
        if not smiles or not ratios:
            continue
        observed = numeric(row, ["observed_tg_c", "predicted_tg_mean_c", "predicted_tg"], default=None)
        target = numeric(row, ["target_tg_c"], default=195.0)
        distance = numeric(row, ["target_distance_c"], default=None)
        if distance is None and observed is not None and target is not None:
            distance = abs(observed - target)
        rows.append(
            {
                "candidate_origin": origin,
                "source_path": str(path),
                "source_row_index": int(idx),
                "linked_observation_id": text_value(row, ["observation_id"], default=f"{origin}_{int(idx):04d}"),
                "target_tg_c": target,
                "observed_tg_c": observed,
                "predicted_tg_mean_c": numeric(row, ["predicted_tg_mean_c", "predicted_tg", "observed_tg_c"], default=None),
                "predicted_tg_sigma_c": numeric(row, ["predicted_tg_sigma_c"], default=None),
                "target_distance_c": distance,
                "smiles": smiles,
                "ratios": ratios,
                "sources": text_value(row, ["sources"], default=text_value(row, ["source_type"], default="surrogate")),
                "labels": text_value(row, ["labels"], default=""),
                "groups": text_value(row, ["groups"], default=""),
                "compatibility_reasons": text_value(row, ["compatibility_reasons"], default=text_value(row, ["compatibility_reason"], default="")),
                "ood_penalty": numeric(row, ["ood_penalty"], default=0.0),
                "new_component_count": numeric(row, ["new_component_count"], default=0.0),
                "notes": text_value(row, ["notes"], default=""),
            }
        )
    return pd.DataFrame(rows)


def review_priority(row: pd.Series) -> str:
    if not bool(row["valid_smiles"]) or not bool(row["ratio_ok"]) or str(row["process_template"]) == "manual_process_template_required":
        return "template_or_validity_review"
    sigma = row.get("predicted_tg_sigma_c")
    distance = row.get("target_distance_c")
    if pd.notna(sigma) and float(sigma) >= 90.0:
        return "high_fidelity_before_dsc"
    if pd.notna(distance) and float(distance) <= 1.0:
        return "process_design_for_dsc"
    return "standard_process_review"


def recommended_action(row: pd.Series) -> str:
    if str(row["review_priority"]) == "template_or_validity_review":
        return "assign process template or fix invalid formulation before experiment."
    if str(row["review_priority"]) == "high_fidelity_before_dsc":
        return "run high-fidelity or ensemble review before committing DSC resources."
    return "complete missing process fields, then decide whether to schedule synthesis/DSC."


def review_tier(priority: str) -> int:
    order = {
        "process_design_for_dsc": 1,
        "high_fidelity_before_dsc": 2,
        "standard_process_review": 3,
        "template_or_validity_review": 4,
    }
    return order.get(str(priority), 5)


def build_review_queue(
    candidate_tables: list[tuple[Path, str]],
    knowledge_path: Path,
    per_table_limit: int | None = 20,
    top_k: int = 30,
    reward_temperature_c: float = 5.0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    knowledge = read_knowledge(knowledge_path)
    templates = process_templates(knowledge_path)
    frames = [normalize_candidate_table(path, origin, per_table_limit) for path, origin in candidate_tables]
    candidates = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True) if any(not f.empty for f in frames) else pd.DataFrame()
    if candidates.empty:
        empty = pd.DataFrame()
        return empty, pd.DataFrame(columns=PROCESS_RECORD_COLUMNS), {"input_candidates": 0, "queue_rows": 0}
    candidates = candidates.drop_duplicates(subset=["smiles", "ratios"]).copy()
    candidates["reaction_principle"] = candidates["compatibility_reasons"].map(infer_reaction_principle)
    candidates["process_template"] = [
        process_template_for_principle(principle, knowledge)
        for principle in candidates["reaction_principle"].astype(str)
    ]
    candidates["required_process_fields"] = [
        ";".join(required_process_fields(template, templates))
        for template in candidates["process_template"].astype(str)
    ]
    candidates["missing_process_fields"] = candidates["required_process_fields"]
    candidates["missing_process_field_count"] = [
        len([field for field in str(value).split(";") if field])
        for value in candidates["missing_process_fields"]
    ]
    candidates["valid_smiles"] = candidates["smiles"].map(smiles_valid)
    candidates["ratio_ok"] = candidates["ratios"].map(ratios_sum_ok)
    candidates["target_reward"] = candidates["target_distance_c"].map(lambda value: target_reward(value, reward_temperature_c))
    candidates["surrogate_risk_penalty"] = (
        candidates["predicted_tg_sigma_c"].fillna(80.0).astype(float) / 200.0
        + candidates["ood_penalty"].fillna(0.0).astype(float) * 0.03
        + candidates["new_component_count"].fillna(0.0).astype(float) * 0.03
    )
    candidates["process_burden_penalty"] = candidates["missing_process_field_count"].astype(float) * 0.04
    candidates["review_score"] = candidates["target_reward"] - candidates["surrogate_risk_penalty"] - candidates["process_burden_penalty"]
    candidates["review_priority"] = [review_priority(row) for _, row in candidates.iterrows()]
    candidates["review_tier"] = candidates["review_priority"].map(review_tier)
    candidates["recommended_action"] = [recommended_action(row) for _, row in candidates.iterrows()]
    candidates["ready_for_active_ledger"] = False
    candidates["review_status"] = "needs_human_review"
    queue = candidates.sort_values(
        ["review_tier", "review_score", "target_distance_c"],
        ascending=[True, False, True],
    ).head(top_k).reset_index(drop=True)
    queue["review_rank"] = range(1, len(queue) + 1)

    process_rows = []
    for _, row in queue.iterrows():
        process_rows.append(
            {
                "process_record_id": f"review_queue_{int(row['review_rank']):04d}",
                "linked_observation_id": row["linked_observation_id"],
                "source_type": "surrogate_review",
                "target_tg_c": row["target_tg_c"],
                "observed_tg_c": row["observed_tg_c"],
                "smiles": row["smiles"],
                "ratios": row["ratios"],
                "reaction_principle": row["reaction_principle"],
                "process_template": row["process_template"],
                "review_status": "needs_human_review",
                "literature_source": row["candidate_origin"],
                "operator": "smp02_human_review_queue",
                "catalyst": "",
                "catalyst_loading": "",
                "cure_temperature_c": "",
                "cure_time_h": "",
                "post_cure_temperature_c": "",
                "post_cure_time_h": "",
                "imidization_temperature_c": "",
                "imidization_time_h": "",
                "trimerization_temperature_c": "",
                "initiator_type": "",
                "initiator_loading": "",
                "moisture_control": "",
                "nco_index": "",
                "notes": (
                    f"Human review queue draft; missing_process_fields={row['missing_process_fields']}; "
                    f"review_priority={row['review_priority']}; not active ledger evidence."
                ),
            }
        )
    process_records = pd.DataFrame(process_rows, columns=PROCESS_RECORD_COLUMNS)
    summary = {
        "input_candidates": int(sum(len(frame) for frame in frames if not frame.empty)),
        "deduplicated_candidates": int(len(candidates)),
        "queue_rows": int(len(queue)),
        "ready_for_active_ledger_rows": int(queue["ready_for_active_ledger"].sum()),
        "process_templates": queue["process_template"].value_counts().to_dict(),
        "review_priorities": queue["review_priority"].value_counts().to_dict(),
        "mean_target_distance_c": float(queue["target_distance_c"].mean()) if len(queue) else None,
        "best_target_distance_c": float(queue["target_distance_c"].min()) if len(queue) else None,
    }
    return queue, process_records, summary


def write_report(queue: pd.DataFrame, process_summary: dict[str, Any], summary: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    lines = [
        "# Human Experiment Review Queue",
        "",
        "本文档把 TODO 中“人工闭环、真实实验结果迭代优化”推进为可运行的候选复核队列。当前所有输入仍是 surrogate / Harness / PiEvo evidence，不会自动升级为真实 DSC 或 active high-authority ledger。",
        "",
        "## 输出文件",
        "",
        f"- Review queue: `{out_dir / 'human_experiment_review_queue.csv'}`",
        f"- Draft process records: `{out_dir / 'draft_process_records.csv'}`",
        f"- Draft process ledger: `{out_dir / 'draft_process_record_ledger.csv'}`",
        f"- Summary: `{out_dir / 'human_experiment_review_queue_summary.json'}`",
        f"- Report: `{report_path}`",
        "",
        "## Queue Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, dict):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Draft Process Ledger Gate",
            "",
            "| item | value |",
            "| --- | ---: |",
        ]
    )
    for key, value in process_summary.items():
        if isinstance(value, dict):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Top Review Items",
            "",
            "| rank | Tg (C) | distance (C) | sigma (C) | template | missing process fields | priority | action |",
            "| ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
        ]
    )
    for _, row in queue.head(15).iterrows():
        sigma = "" if pd.isna(row["predicted_tg_sigma_c"]) else f"{float(row['predicted_tg_sigma_c']):.2f}"
        lines.append(
            f"| {int(row['review_rank'])} | {float(row['observed_tg_c']):.2f} | {float(row['target_distance_c']):.3f} | "
            f"{sigma} | {row['process_template']} | {row['missing_process_fields']} | "
            f"{row['review_priority']} | {row['recommended_action']} |"
        )
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- 这个队列只决定哪些 surrogate 候选值得人工补工艺条件、做高保真复核或排实验优先级。",
            "- `draft_process_record_ledger.csv` 应保持 `ready_for_active_ledger=false`，直到人类补齐工艺字段并显式批准。",
            "- 真实 DSC 或文献复现实验完成后，应写入 observation ledger，并用更高 authority weight 更新 PiEvo posterior。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_candidate_table_specs(values: list[str]) -> list[tuple[Path, str]]:
    specs = []
    for value in values:
        if "::" in value:
            path, origin = value.split("::", 1)
        else:
            path = value
            origin = Path(value).stem
        specs.append((Path(path), origin))
    return specs


def run_queue(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    queue, process_records, summary = build_review_queue(
        parse_candidate_table_specs(args.candidate_table),
        Path(args.knowledge),
        per_table_limit=args.per_table_limit,
        top_k=args.top_k,
        reward_temperature_c=args.reward_temperature_c,
    )
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = out_dir / "human_experiment_review_queue.csv"
    draft_records_path = out_dir / "draft_process_records.csv"
    process_ledger_path = out_dir / "draft_process_record_ledger.csv"
    process_summary_path = out_dir / "draft_process_record_summary.json"
    queue.to_csv(queue_path, index=False)
    process_records.to_csv(draft_records_path, index=False)
    if process_records.empty:
        process_ledger = pd.DataFrame()
        process_summary = {"input_rows": 0, "ready_for_active_ledger_rows": 0}
    else:
        process_ledger, process_summary = import_process_records(
            draft_records_path,
            Path(args.process_schema),
            Path(args.knowledge),
        )
    process_ledger.to_csv(process_ledger_path, index=False)
    process_summary_path.write_text(json.dumps(process_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = summary | {
        "draft_process_record_pass_rows": int(process_summary.get("process_record_pass_rows", 0)),
        "draft_ready_for_active_ledger_rows": int(process_summary.get("ready_for_active_ledger_rows", 0)),
        "queue_path": str(queue_path),
        "draft_process_records_path": str(draft_records_path),
        "draft_process_record_ledger_path": str(process_ledger_path),
    }
    (out_dir / "human_experiment_review_queue_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(queue, process_summary, summary, out_dir, Path(args.report))
    return queue, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a human experiment/process review queue from surrogate candidates.")
    parser.add_argument(
        "--candidate-table",
        action="append",
        default=[
            "artifacts/trail/generation/vae_latent_local_search_eval/replacement_proposals_scored.csv::vae_latent_local_search",
            "artifacts/pievo_faithful_vae_latent_local_search_195_smoke/selected_formulations.csv::pievo_latent_local_search_selected",
            "artifacts/pievo_faithful_ensemble_guard_195_smoke/selected_formulations.csv::pievo_ensemble_guard_selected",
            "artifacts/trail/generation/expanded_inventory_replacement_eval/replacement_proposals_scored.csv::expanded_inventory_replacement",
        ],
        help="Candidate CSV path, optionally suffixed with ::origin. Can be provided multiple times.",
    )
    parser.add_argument("--knowledge", default="trail/knowledge/smp_prior_knowledge.yaml")
    parser.add_argument("--process-schema", default="trail/experiments/process_record_schema.yaml")
    parser.add_argument("--per-table-limit", type=int, default=30)
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/human_experiment_review_queue.md")
    args = parser.parse_args()
    run_queue(args)


if __name__ == "__main__":
    main()
