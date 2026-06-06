from __future__ import annotations

import json
from pathlib import Path

from scripts.build_external_generator_output_checklist import build_external_generator_checklist


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_external_generator_output_checklist_marks_ready_and_suppressed_rows(tmp_path: Path) -> None:
    training = tmp_path / "training.json"
    policy = tmp_path / "policy.json"
    llm = tmp_path / "llm.json"
    sft = tmp_path / "sft.json"
    flow = tmp_path / "flow.json"
    write_json(
        training,
        {
            "sft_ready": True,
            "sft_examples": 25,
            "sft_train_examples": 20,
            "sft_eval_examples": 5,
            "diffusion_flow_ready": True,
            "diffusion_flow_seed_rows": 120,
            "diffusion_flow_train_rows": 100,
            "diffusion_flow_eval_rows": 20,
        },
    )
    write_json(
        policy,
        {
            "top_strategy": "llm_rag_principle_generation",
            "suppressed_strategies": 1,
            "high_authority_evidence_status": "awaiting_high_authority_evidence",
        },
    )
    write_json(llm, {"input_rows": 2, "harness_pass_rows": 2})
    write_json(sft, {"input_rows": 23, "harness_pass_rows": 23})
    write_json(flow, {"input_rows": 19, "harness_pass_rows": 19})

    checklist, summary = build_external_generator_checklist(training, policy, llm, sft, flow)

    assert len(checklist) == 4
    assert summary["ready_external_provider_rows"] == 3
    assert summary["suppressed_or_blocked_rows"] == 1
    assert summary["sft_ready"] is True
    assert summary["diffusion_flow_ready"] is True
    assert summary["ready_strategy_counts"]["sft_candidate_generator"] == 1
    assert summary["blocked_strategy_counts"]["llm_smiles_generation"] == 1
    assert bool(checklist[checklist["strategy"] == "llm_smiles_generation"].iloc[0]["can_submit_external_outputs"]) is False
    assert checklist["creates_observation"].eq(False).all()
    assert summary["evidence_level"] == "external_generator_output_checklist_not_observation"


def test_external_generator_output_checklist_blocks_sft_and_flow_when_training_not_ready(tmp_path: Path) -> None:
    training = tmp_path / "training.json"
    policy = tmp_path / "policy.json"
    empty = tmp_path / "empty.json"
    write_json(training, {"sft_ready": False, "diffusion_flow_ready": False})
    write_json(policy, {"suppressed_strategies": 1})
    write_json(empty, {})

    checklist, summary = build_external_generator_checklist(training, policy, empty, empty, empty)

    assert summary["ready_external_provider_rows"] == 1
    assert summary["suppressed_or_blocked_rows"] == 3
    assert checklist[checklist["strategy"] == "sft_candidate_generator"].iloc[0]["readiness_status"] == "blocked_by_sft_training_data_gate"
    assert checklist[checklist["strategy"] == "diffusion_or_flow_matching"].iloc[0]["readiness_status"] == "blocked_by_diffusion_flow_seed_gate"
