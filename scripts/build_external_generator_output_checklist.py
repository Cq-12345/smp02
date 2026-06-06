from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


CHECKLIST_COLUMNS = [
    "checklist_rank",
    "provider_task_id",
    "strategy",
    "provider_mode",
    "readiness_status",
    "can_submit_external_outputs",
    "readiness_reason",
    "required_input_artifacts",
    "required_output_contract",
    "required_generation_record_fields",
    "post_submit_gate_sequence",
    "current_surrogate_rows",
    "current_harness_pass_rows",
    "creates_observation",
    "evidence_level",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def policy_status(policy: dict[str, Any], strategy: str) -> str:
    if strategy == "llm_smiles_generation" and int(policy.get("suppressed_strategies", 0)) > 0:
        return "suppressed_pending_predictor_and_chemistry_evidence"
    return "eligible_or_not_suppressed_by_policy"


def build_external_generator_checklist(
    generative_training_summary_path: Path,
    strategy_policy_summary_path: Path,
    feedback_aware_llm_rag_summary_path: Path,
    sft_trained_summary_path: Path,
    diffusion_flow_trained_summary_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    training = read_json(generative_training_summary_path)
    policy = read_json(strategy_policy_summary_path)
    llm_rag = read_json(feedback_aware_llm_rag_summary_path)
    sft_trained = read_json(sft_trained_summary_path)
    flow_trained = read_json(diffusion_flow_trained_summary_path)
    required_fields = (
        "generation_id;strategy;stage;target_tg_c;target_window_c;candidate_smiles;"
        "candidate_ratios;source_context;generator_id;candidate_json;functional_group_plan;notes"
    )
    gate_sequence = "generation_record_import;predictor_scoring;Harness;PiEvo_IDS;human_review;observation_gate_if_completed"
    rows = [
        {
            "provider_task_id": "external_llm_rag_principle_generation",
            "strategy": "llm_rag_principle_generation",
            "provider_mode": "openai_compatible_or_other_external_llm",
            "readiness_status": "ready_for_external_provider_output",
            "can_submit_external_outputs": True,
            "readiness_reason": "feedback-aware offline/RAG chain exists; external provider output must use same generation record contract",
            "required_input_artifacts": "trail/generation/generation_strategy_registry.yaml;artifacts/trail/generation_feedback_strict/strategy_feedback.csv;trail/knowledge/smp_prior_knowledge.yaml",
            "required_output_contract": "generation_record_ledger.csv rows with auditable prompt/RAG context and candidate JSON",
            "required_generation_record_fields": required_fields + ";prompt_id;prompt_hash;rag_context_refs;principle_hypothesis",
            "post_submit_gate_sequence": gate_sequence,
            "current_surrogate_rows": int(llm_rag.get("input_rows", 0)),
            "current_harness_pass_rows": int(llm_rag.get("harness_pass_rows", 0)),
            "creates_observation": False,
            "evidence_level": "external_generator_output_checklist_not_observation",
        },
        {
            "provider_task_id": "external_sft_finetune_generation",
            "strategy": "sft_candidate_generator",
            "provider_mode": "real_sft_or_finetuned_llm_output",
            "readiness_status": "ready_for_external_provider_output" if bool(training.get("sft_ready")) else "blocked_by_sft_training_data_gate",
            "can_submit_external_outputs": bool(training.get("sft_ready")),
            "readiness_reason": f"sft_ready={bool(training.get('sft_ready'))}; train/eval rows={training.get('sft_train_examples', 0)}/{training.get('sft_eval_examples', 0)}",
            "required_input_artifacts": "artifacts/trail/generation/generative_training_sets/sft_generation_records.jsonl",
            "required_output_contract": "generation_record_ledger.csv rows from real SFT/fine-tuned output, not prototype replay",
            "required_generation_record_fields": required_fields + ";prompt_id;candidate_json",
            "post_submit_gate_sequence": gate_sequence,
            "current_surrogate_rows": int(sft_trained.get("input_rows", 0)),
            "current_harness_pass_rows": int(sft_trained.get("harness_pass_rows", 0)),
            "creates_observation": False,
            "evidence_level": "external_generator_output_checklist_not_observation",
        },
        {
            "provider_task_id": "external_diffusion_flow_decoder_generation",
            "strategy": "diffusion_or_flow_matching",
            "provider_mode": "valid_smiles_decoder_or_external_diffusion_flow_output",
            "readiness_status": "ready_for_external_provider_output"
            if bool(training.get("diffusion_flow_ready"))
            else "blocked_by_diffusion_flow_seed_gate",
            "can_submit_external_outputs": bool(training.get("diffusion_flow_ready")),
            "readiness_reason": f"diffusion_flow_ready={bool(training.get('diffusion_flow_ready'))}; seed train/eval rows={training.get('diffusion_flow_train_rows', 0)}/{training.get('diffusion_flow_eval_rows', 0)}; current trained projection is not a free SMILES decoder",
            "required_input_artifacts": "artifacts/trail/generation/generative_training_sets/diffusion_flow_seed_table.csv",
            "required_output_contract": "generation_record_ledger.csv rows with valid SMILES decoded/proposed by external flow or decoder",
            "required_generation_record_fields": required_fields + ";candidate_json;compatibility_reasons",
            "post_submit_gate_sequence": gate_sequence,
            "current_surrogate_rows": int(flow_trained.get("input_rows", 0)),
            "current_harness_pass_rows": int(flow_trained.get("harness_pass_rows", 0)),
            "creates_observation": False,
            "evidence_level": "external_generator_output_checklist_not_observation",
        },
        {
            "provider_task_id": "external_llm_free_smiles_generation",
            "strategy": "llm_smiles_generation",
            "provider_mode": "free_form_llm_smiles_draft",
            "readiness_status": policy_status(policy, "llm_smiles_generation"),
            "can_submit_external_outputs": False,
            "readiness_reason": "free SMILES drafts remain suppressed until predictor and chemistry evidence are attached; use LLM/RAG principle records first",
            "required_input_artifacts": "trail/generation/generation_record_schema.yaml;trail/harness/constraints.py",
            "required_output_contract": "draft generation records only; cannot enter recommendation path without RDKit, predictor, Harness, and chemistry evidence",
            "required_generation_record_fields": required_fields + ";harness_failure_reason",
            "post_submit_gate_sequence": "draft_record_import;RDKit_validation;predictor_scoring;Harness;manual_review",
            "current_surrogate_rows": 0,
            "current_harness_pass_rows": 0,
            "creates_observation": False,
            "evidence_level": "external_generator_output_checklist_not_observation",
        },
    ]
    checklist = pd.DataFrame(rows)
    checklist.insert(0, "checklist_rank", range(1, len(checklist) + 1))
    checklist = checklist[CHECKLIST_COLUMNS]
    summary = {
        "checklist_rows": int(len(checklist)),
        "ready_external_provider_rows": int(checklist["can_submit_external_outputs"].sum()),
        "suppressed_or_blocked_rows": int((~checklist["can_submit_external_outputs"]).sum()),
        "sft_ready": bool(training.get("sft_ready", False)),
        "diffusion_flow_ready": bool(training.get("diffusion_flow_ready", False)),
        "sft_examples": int(training.get("sft_examples", 0)),
        "diffusion_flow_seed_rows": int(training.get("diffusion_flow_seed_rows", 0)),
        "strategy_policy_top_strategy": policy.get("top_strategy", ""),
        "strategy_policy_high_authority_evidence_status": policy.get("high_authority_evidence_status", ""),
        "ready_strategy_counts": checklist.loc[checklist["can_submit_external_outputs"], "strategy"].value_counts().to_dict(),
        "blocked_strategy_counts": checklist.loc[~checklist["can_submit_external_outputs"], "strategy"].value_counts().to_dict(),
        "creates_observation": False,
        "evidence_level": "external_generator_output_checklist_not_observation",
    }
    return checklist, summary


def write_report(checklist: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# External Generator Output Checklist",
        "",
        "本文档把真实外部 LLM/SFT/decoder/flow 输出接入前的门禁结构化。它不调用外部模型，也不把 draft 输出当作 observation。",
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
    lines.extend(
        [
            "",
            "## Provider Rows",
            "",
            "| rank | provider task | strategy | status | can submit | current pass rows |",
            "| ---: | --- | --- | --- | --- | ---: |",
        ]
    )
    for _, row in checklist.iterrows():
        lines.append(
            f"| {int(row['checklist_rank'])} | {row['provider_task_id']} | {row['strategy']} | "
            f"{row['readiness_status']} | {bool(row['can_submit_external_outputs'])} | {int(row['current_harness_pass_rows'])} |"
        )
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "- 外部生成器只能提交 generation record rows，不能直接推荐配方。",
            "- 所有输出必须继续经过 predictor、Harness、PiEvo IDS 和人工审核。",
            "- `creates_observation=false` 表示这一步不是实验结果，也不会进入 active high-authority evidence ledger。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an intake checklist for real external generator outputs.")
    parser.add_argument("--generative-training-summary", default="artifacts/trail/generation/generative_training_sets/generative_training_summary.json")
    parser.add_argument("--strategy-policy-summary", default="artifacts/trail/generation_strategy_policy/generation_strategy_bandit_summary.json")
    parser.add_argument("--feedback-aware-llm-rag-summary", default="artifacts/trail/generation/feedback_aware_llm_rag/generation_record_summary.json")
    parser.add_argument("--sft-trained-summary", default="artifacts/trail/generation/sft_trained_projection_generator/generation_record_summary.json")
    parser.add_argument("--diffusion-flow-trained-summary", default="artifacts/trail/generation/diffusion_flow_trained_generator/generation_record_summary.json")
    parser.add_argument("--out-dir", default="artifacts/trail/generation/external_generator_output_checklist")
    parser.add_argument("--report", default="reports/external_generator_output_checklist.md")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    checklist, summary = build_external_generator_checklist(
        Path(args.generative_training_summary),
        Path(args.strategy_policy_summary),
        Path(args.feedback_aware_llm_rag_summary),
        Path(args.sft_trained_summary),
        Path(args.diffusion_flow_trained_summary),
    )
    checklist_path = out_dir / "external_generator_output_checklist.csv"
    summary_path = out_dir / "external_generator_output_checklist_summary.json"
    checklist.to_csv(checklist_path, index=False)
    summary = {
        **summary,
        "checklist_path": str(checklist_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(checklist, summary, Path(args.report))


if __name__ == "__main__":
    main()
