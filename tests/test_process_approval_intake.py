from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.import_process_approval_intake import import_process_approval_intake


SMILES = "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|NCCN"


def test_process_approval_requires_human_fields_and_unblocks_observation_request(tmp_path: Path) -> None:
    suggestions = pd.DataFrame(
        [
            {
                "request_id": "validation_001_process_completion",
                "process_record_id": "review_queue_0001",
                "linked_observation_id": "candidate_001",
                "target_tg_c": 195.0,
                "surrogate_tg_c": 195.2,
                "candidate_origin": "pytest",
                "reaction_principle": "epoxy_primary_amine",
                "process_template": "epoxy_amine_thermal_cure",
                "suggested_inputs": "mix_temperature_c=60.0;cure_temperature_c=120.0;cure_time_h=2.0;post_cure_temperature_c=180.0;post_cure_time_h=2.0",
                "risk_flags": "standard_human_review",
                "evidence_level": "knowledge_template_suggestion_not_observation",
                "smiles": SMILES,
                "ratios": "0.5:0.5",
            }
        ]
    )
    suggestions_path = tmp_path / "suggestions.csv"
    suggestions.to_csv(suggestions_path, index=False)
    suggested_records = pd.DataFrame(
        [
            {
                "process_record_id": "review_queue_0001",
                "linked_observation_id": "candidate_001",
                "source_type": "surrogate_review",
                "target_tg_c": 195.0,
                "observed_tg_c": 195.2,
                "smiles": SMILES,
                "ratios": "0.5:0.5",
                "reaction_principle": "epoxy_primary_amine",
                "process_template": "epoxy_amine_thermal_cure",
                "review_status": "needs_human_review",
                "literature_source": "pytest",
                "operator": "pytest",
                "cure_temperature_c": 120.0,
                "cure_time_h": 2.0,
                "post_cure_temperature_c": 180.0,
                "post_cure_time_h": 2.0,
                "mix_temperature_c": 60.0,
                "notes": "suggested",
            }
        ]
    )
    suggested_records_path = tmp_path / "suggested_records.csv"
    suggested_records.to_csv(suggested_records_path, index=False)
    approvals = pd.DataFrame(
        [
            {
                "approval_id": "approval_validation_001_process_completion",
                "request_id": "validation_001_process_completion",
                "process_record_id": "review_queue_0001",
                "linked_observation_id": "candidate_001",
                "approval_decision": "approved",
                "process_ready": True,
                "reviewer_approved": True,
                "reviewer_id": "pytest_reviewer",
                "review_date": "2026-06-06",
                "review_notes": "approved for high-fidelity validation",
            }
        ]
    )
    approvals_path = tmp_path / "approvals.csv"
    approvals.to_csv(approvals_path, index=False)
    requests = pd.DataFrame(
        [
            {
                "request_id": "validation_001_process_completion",
                "linked_observation_id": "candidate_001",
                "task_type": "process_completion",
                "target_tg_c": 195.0,
                "eligible_observation_source_type": "",
                "blocked_by_process_completion": False,
            },
            {
                "request_id": "validation_001_high_fidelity_validation",
                "linked_observation_id": "candidate_001",
                "task_type": "high_fidelity_validation",
                "target_tg_c": 195.0,
                "eligible_observation_source_type": "high_fidelity_simulation",
                "blocked_by_process_completion": True,
            },
        ]
    )
    requests_path = tmp_path / "requests.csv"
    requests.to_csv(requests_path, index=False)

    template, review, process_rows, ledger, unblocked, summary = import_process_approval_intake(
        suggestions_path,
        suggested_records_path,
        approvals_path,
        requests_path,
        Path("trail/experiments/process_record_schema.yaml"),
        Path("trail/knowledge/smp_prior_knowledge.yaml"),
    )

    assert len(template) == 1
    assert len(review) == 1
    assert len(process_rows) == 1
    assert len(ledger) == 1
    assert bool(review.iloc[0]["accepted_process_approval"]) is True
    assert bool(ledger.iloc[0]["ready_for_active_ledger"]) is True
    assert list(unblocked["request_id"]) == ["validation_001_high_fidelity_validation"]
    assert summary["accepted_process_approval_rows"] == 1
    assert summary["unblocked_observation_request_rows"] == 1
    assert summary["approval_gate_status"] == "process_approval_unblocked_requests"


def test_process_approval_rejects_missing_reviewer_approval(tmp_path: Path) -> None:
    suggestions = pd.DataFrame(
        [
            {
                "request_id": "validation_001_process_completion",
                "process_record_id": "review_queue_0001",
                "linked_observation_id": "candidate_001",
                "target_tg_c": 195.0,
                "surrogate_tg_c": 195.2,
                "candidate_origin": "pytest",
                "reaction_principle": "epoxy_primary_amine",
                "process_template": "epoxy_amine_thermal_cure",
                "suggested_inputs": "",
                "risk_flags": "",
                "evidence_level": "knowledge_template_suggestion_not_observation",
                "smiles": SMILES,
                "ratios": "0.5:0.5",
            }
        ]
    )
    suggestions_path = tmp_path / "suggestions.csv"
    suggestions.to_csv(suggestions_path, index=False)
    suggested_records_path = tmp_path / "suggested_records.csv"
    pd.DataFrame(
        [
            {
                "process_record_id": "review_queue_0001",
                "linked_observation_id": "candidate_001",
                "source_type": "surrogate_review",
                "target_tg_c": 195.0,
                "observed_tg_c": 195.2,
                "smiles": SMILES,
                "ratios": "0.5:0.5",
                "reaction_principle": "epoxy_primary_amine",
                "process_template": "epoxy_amine_thermal_cure",
                "review_status": "needs_human_review",
            }
        ]
    ).to_csv(suggested_records_path, index=False)
    approvals_path = tmp_path / "approvals.csv"
    pd.DataFrame(
        [
            {
                "approval_id": "approval_validation_001_process_completion",
                "request_id": "validation_001_process_completion",
                "process_record_id": "review_queue_0001",
                "linked_observation_id": "candidate_001",
                "approval_decision": "approved",
                "process_ready": True,
                "reviewer_approved": False,
                "reviewer_id": "pytest_reviewer",
            }
        ]
    ).to_csv(approvals_path, index=False)
    requests_path = tmp_path / "requests.csv"
    pd.DataFrame(
        [
            {
                "request_id": "validation_001_high_fidelity_validation",
                "linked_observation_id": "candidate_001",
                "target_tg_c": 195.0,
                "eligible_observation_source_type": "high_fidelity_simulation",
                "blocked_by_process_completion": True,
            }
        ]
    ).to_csv(requests_path, index=False)

    _, review, _, _, unblocked, summary = import_process_approval_intake(
        suggestions_path,
        suggested_records_path,
        approvals_path,
        requests_path,
        Path("trail/experiments/process_record_schema.yaml"),
        Path("trail/knowledge/smp_prior_knowledge.yaml"),
    )

    assert bool(review.iloc[0]["accepted_process_approval"]) is False
    assert "reviewer_approved_not_true" in review.iloc[0]["final_rejection_reasons"]
    assert unblocked.empty
    assert summary["accepted_process_approval_rows"] == 0
