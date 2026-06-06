from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_process_approval_reviewer_checklist import build_reviewer_checklist


def test_process_approval_reviewer_checklist_maps_downstream_protocol(tmp_path: Path) -> None:
    approval = pd.DataFrame(
        [
            {
                "approval_id": "approval_validation_001_process_completion",
                "request_id": "validation_001_process_completion",
                "process_record_id": "record_001",
                "linked_observation_id": "candidate_001",
                "approval_decision": "",
                "process_ready": False,
                "reviewer_approved": False,
                "target_tg_c": 250.0,
                "surrogate_tg_c": 249.9,
                "candidate_origin": "sparse_target_replacement_250",
                "reaction_principle": "epoxy_hydroxyl",
                "process_template": "epoxy_anhydride_catalyzed_cure",
                "suggested_inputs": "catalyst_loading=1 wt%;cure_temperature_c=170.0;post_cure_temperature_c=230.0",
                "risk_flags": "high_tg_process_window;high_predictor_sigma",
                "smiles": "CCO|NCC",
                "ratios": "0.5:0.5",
            }
        ]
    )
    suggestions = pd.DataFrame(
        [
            {
                "request_id": "validation_001_process_completion",
                "target_distance_c": 0.1,
                "predicted_tg_sigma_c": 80.0,
            }
        ]
    )
    protocols = pd.DataFrame(
        [
            {
                "protocol_id": "protocol_validation_001_high_fidelity_validation",
                "linked_observation_id": "candidate_001",
                "required_methods": "process_feasibility_review;model_ensemble_recheck;target_specific_literature_check",
                "authority_weight_if_completed": 3.0,
            }
        ]
    )
    approval_path = tmp_path / "approval.csv"
    suggestions_path = tmp_path / "suggestions.csv"
    protocol_path = tmp_path / "protocols.csv"
    approval.to_csv(approval_path, index=False)
    suggestions.to_csv(suggestions_path, index=False)
    protocols.to_csv(protocol_path, index=False)

    checklist, summary = build_reviewer_checklist(approval_path, suggestions_path, protocol_path)

    assert len(checklist) == 1
    row = checklist.iloc[0]
    assert row["approval_status"] == "awaiting_human_review"
    assert bool(row["ready_for_human_review"]) is True
    assert bool(row["creates_observation"]) is False
    assert row["downstream_protocol_count"] == 1
    assert row["downstream_protocol_ids"] == "protocol_validation_001_high_fidelity_validation"
    assert "target_specific_literature_check" in row["downstream_required_methods"]
    assert "review high-Tg thermal stability" in row["reviewer_required_checks"]
    assert summary["ready_for_human_review_rows"] == 1
    assert summary["already_submitted_rows"] == 0
    assert summary["can_unlock_high_fidelity_protocol_rows"] == 1
    assert summary["downstream_protocol_rows"] == 1
    assert summary["suggested_field_frequency"]["cure_temperature_c"] == 1
    assert summary["creates_observation"] is False
    assert summary["evidence_level"] == "process_approval_reviewer_checklist_not_observation"


def test_process_approval_reviewer_checklist_counts_accepted_rows(tmp_path: Path) -> None:
    approval = pd.DataFrame(
        [
            {
                "approval_id": "approval_validation_001_process_completion",
                "request_id": "validation_001_process_completion",
                "process_record_id": "record_001",
                "linked_observation_id": "candidate_001",
                "approval_decision": "approved",
                "process_ready": True,
                "reviewer_approved": True,
                "target_tg_c": 195.0,
                "surrogate_tg_c": 195.0,
                "candidate_origin": "vae_latent_local_search",
                "reaction_principle": "epoxy_amine",
                "process_template": "epoxy_amine_thermal_cure",
                "suggested_inputs": "cure_temperature_c=120.0",
                "risk_flags": "",
                "smiles": "CCO|NCC",
                "ratios": "0.5:0.5",
            }
        ]
    )
    approval_path = tmp_path / "approval.csv"
    suggestions_path = tmp_path / "suggestions.csv"
    protocol_path = tmp_path / "protocols.csv"
    approval.to_csv(approval_path, index=False)
    pd.DataFrame().to_csv(suggestions_path, index=False)
    pd.DataFrame().to_csv(protocol_path, index=False)

    checklist, summary = build_reviewer_checklist(approval_path, suggestions_path, protocol_path)

    assert checklist.iloc[0]["approval_status"] == "accepted_process_approval"
    assert bool(checklist.iloc[0]["ready_for_human_review"]) is False
    assert summary["accepted_process_approval_rows"] == 1
    assert summary["ready_for_human_review_rows"] == 0
