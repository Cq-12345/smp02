from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_high_fidelity_protocol_packet import build_protocol_packet


def test_high_fidelity_protocol_packet_stays_blocked_when_process_approval_missing(tmp_path: Path) -> None:
    requests = pd.DataFrame(
        [
            {
                "request_id": "validation_001_high_fidelity_validation",
                "validation_rank": 1,
                "linked_observation_id": "candidate_001",
                "task_type": "high_fidelity_validation",
                "target_tg_c": 250.0,
                "surrogate_tg_c": 249.8,
                "target_distance_c": 0.2,
                "predicted_tg_sigma_c": 80.0,
                "candidate_origin": "sparse_target_replacement_250",
                "process_template": "epoxy_anhydride_catalyzed_cure",
                "risk_flags": "process_incomplete;high_tg_target;sparse_target_origin",
                "eligible_observation_source_type": "high_fidelity_simulation",
                "authority_weight_if_completed": 3.0,
                "request_priority_score": 0.9,
                "required_inputs": "process_feasibility_review;model_ensemble_recheck;thermal_stability_pre_screen",
                "blocked_by_process_completion": True,
                "smiles": "CCO|NCCN",
                "ratios": "0.5:0.5",
            }
        ]
    )
    requests_path = tmp_path / "requests.csv"
    requests.to_csv(requests_path, index=False)
    unblocked_path = tmp_path / "unblocked.csv"
    unblocked_path.write_text("", encoding="utf-8")
    approval_summary = tmp_path / "approval.json"
    approval_summary.write_text('{"approval_gate_status": "awaiting_human_process_approval"}', encoding="utf-8")

    protocols, summary = build_protocol_packet(requests_path, unblocked_path, approval_summary)

    assert len(protocols) == 1
    assert protocols.iloc[0]["protocol_status"] == "blocked_pending_process_approval"
    assert bool(protocols.iloc[0]["can_start_high_fidelity_protocol"]) is False
    assert bool(protocols.iloc[0]["creates_observation"]) is False
    assert summary["high_fidelity_protocol_rows"] == 1
    assert summary["blocked_protocol_rows"] == 1
    assert summary["ready_protocol_rows"] == 0
    assert summary["method_frequency"]["thermal_stability_pre_screen"] == 1
    assert summary["evidence_level"] == "high_fidelity_protocol_template_not_observation"


def test_high_fidelity_protocol_packet_marks_unblocked_request_ready(tmp_path: Path) -> None:
    requests = pd.DataFrame(
        [
            {
                "request_id": "validation_001_high_fidelity_validation",
                "validation_rank": 1,
                "linked_observation_id": "candidate_001",
                "task_type": "high_fidelity_validation",
                "target_tg_c": 195.0,
                "surrogate_tg_c": 195.1,
                "target_distance_c": 0.1,
                "predicted_tg_sigma_c": 55.0,
                "candidate_origin": "vae_latent_local_search",
                "process_template": "epoxy_amine_thermal_cure",
                "risk_flags": "process_incomplete;high_predictor_sigma",
                "eligible_observation_source_type": "high_fidelity_simulation",
                "authority_weight_if_completed": 3.0,
                "request_priority_score": 0.8,
                "required_inputs": "process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble",
                "blocked_by_process_completion": True,
                "smiles": "CCO|NCCN",
                "ratios": "0.5:0.5",
            }
        ]
    )
    requests_path = tmp_path / "requests.csv"
    requests.to_csv(requests_path, index=False)
    unblocked_path = tmp_path / "unblocked.csv"
    pd.DataFrame([{"request_id": "validation_001_high_fidelity_validation"}]).to_csv(unblocked_path, index=False)
    approval_summary = tmp_path / "approval.json"
    approval_summary.write_text('{"approval_gate_status": "process_approval_unblocked_requests"}', encoding="utf-8")

    protocols, summary = build_protocol_packet(requests_path, unblocked_path, approval_summary)

    assert protocols.iloc[0]["protocol_status"] == "ready_for_high_fidelity_execution"
    assert bool(protocols.iloc[0]["process_approval_unblocked"]) is True
    assert bool(protocols.iloc[0]["can_start_high_fidelity_protocol"]) is True
    assert bool(protocols.iloc[0]["creates_observation"]) is False
    assert protocols.iloc[0]["evidence_level"] == "high_fidelity_protocol_template_not_observation"
    assert summary["ready_protocol_rows"] == 1
    assert summary["process_approval_unblocked_rows"] == 1
    assert summary["target_counts"]["195.0"] == 1
    assert summary["method_frequency"]["high_fidelity_simulation_or_expanded_model_ensemble"] == 1
    assert summary["approval_gate_status"] == "process_approval_unblocked_requests"
    assert summary["evidence_level"] == "high_fidelity_protocol_template_not_observation"
