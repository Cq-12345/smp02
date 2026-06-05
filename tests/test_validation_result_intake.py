from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.import_validation_request_results import evaluate_results, result_template_from_requests
from trail.experiments.import_observations import import_observations


def test_validation_result_intake_accepts_only_gated_observation_results(tmp_path: Path) -> None:
    requests = pd.DataFrame(
        [
            {
                "request_id": "validation_001_high_fidelity_validation",
                "task_type": "high_fidelity_validation",
                "target_tg_c": 250.0,
                "surrogate_tg_c": 249.9,
                "predicted_tg_sigma_c": 75.0,
                "candidate_origin": "sparse_target_replacement_250",
                "eligible_observation_source_type": "high_fidelity_simulation",
                "smiles": "CC1CO1|O=C1OC(=O)c2ccccc21",
                "ratios": "0.60000:0.40000",
                "blocked_by_process_completion": True,
                "required_inputs": "process_feasibility_review",
            },
            {
                "request_id": "validation_001_process_completion",
                "task_type": "process_completion",
                "target_tg_c": 250.0,
                "surrogate_tg_c": 249.9,
                "predicted_tg_sigma_c": 75.0,
                "candidate_origin": "sparse_target_replacement_250",
                "eligible_observation_source_type": "",
                "smiles": "CC1CO1|O=C1OC(=O)c2ccccc21",
                "ratios": "0.60000:0.40000",
                "blocked_by_process_completion": False,
                "required_inputs": "cure_temperature_c",
            },
        ]
    )
    template = result_template_from_requests(requests)
    assert len(template) == 1
    assert template.iloc[0]["source_type"] == "high_fidelity_simulation"

    results = pd.DataFrame(
        [
            {
                "result_id": "hf_ok",
                "request_id": "validation_001_high_fidelity_validation",
                "source_type": "high_fidelity_simulation",
                "observed_tg_c": 251.0,
                "method": "md_simulation",
                "experiment_date": "2026-06-06",
                "operator": "pytest",
                "process_record_id": "p_ready",
                "process_ready": True,
                "reviewer_approved": True,
                "result_notes": "accepted test result",
            },
            {
                "result_id": "bad_process_task",
                "request_id": "validation_001_process_completion",
                "source_type": "high_fidelity_simulation",
                "observed_tg_c": 250.0,
                "method": "md_simulation",
                "experiment_date": "2026-06-06",
                "operator": "pytest",
                "process_record_id": "p_ready",
                "process_ready": True,
                "reviewer_approved": True,
                "result_notes": "wrong request type",
            },
            {
                "result_id": "not_approved",
                "request_id": "validation_001_high_fidelity_validation",
                "source_type": "high_fidelity_simulation",
                "observed_tg_c": 252.0,
                "method": "md_simulation",
                "experiment_date": "2026-06-06",
                "operator": "pytest",
                "process_record_id": "p_ready",
                "process_ready": True,
                "reviewer_approved": False,
                "result_notes": "not approved",
            },
        ]
    )

    review, observation_input, summary = evaluate_results(requests, results)
    assert summary["accepted_result_rows"] == 1
    assert summary["rejected_result_rows"] == 2
    assert summary["rejection_reason_counts"]["request_not_observation_capable"] == 1
    assert summary["rejection_reason_counts"]["reviewer_not_approved"] == 1
    assert observation_input.iloc[0]["source_type"] == "high_fidelity_simulation"
    assert observation_input.iloc[0]["observation_id"] == "validation_result_hf_ok"
    assert bool(review[review["result_result_id"] == "hf_ok"].iloc[0]["accepted_for_observation_ledger"]) is True

    observation_path = tmp_path / "observation_input.csv"
    observation_input.to_csv(observation_path, index=False)
    ledger, ledger_summary = import_observations(observation_path, Path("trail/experiments/observation_schema.yaml"), 5.0)
    assert ledger_summary["ledger_pass_rows"] == 1
    assert ledger.iloc[0]["source_type"] == "high_fidelity_simulation"
    assert float(ledger.iloc[0]["authority_weight"]) == 3.0
