from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_validation_request_packet import build_requests


def test_validation_request_packet_preserves_observation_authority_gates(tmp_path: Path) -> None:
    plan = tmp_path / "plan.csv"
    pd.DataFrame(
        [
            {
                "validation_rank": 1,
                "linked_observation_id": "sparse_250",
                "target_tg_c": 250.0,
                "observed_tg_c": 249.97,
                "target_distance_c": 0.03,
                "predicted_tg_sigma_c": 78.0,
                "candidate_origin": "sparse_target_replacement_250",
                "process_template": "epoxy_anhydride_catalyzed_cure",
                "risk_flags": "process_incomplete;high_tg_target;sparse_target_origin",
                "validation_lane": "process_plus_high_fidelity",
                "validation_methods": "process_feasibility_review;high_fidelity_simulation_or_expanded_model_ensemble",
                "process_completion_required": True,
                "high_fidelity_required": True,
                "dsc_ready_without_process_completion": False,
                "missing_process_fields": "catalyst_loading;cure_temperature_c;post_cure_temperature_c",
                "validation_score": 0.95,
                "smiles": "CC1CO1|O=C1OC(=O)c2ccccc21",
                "ratios": "0.60000:0.40000",
            },
            {
                "validation_rank": 2,
                "linked_observation_id": "ready_195",
                "target_tg_c": 195.0,
                "observed_tg_c": 195.2,
                "target_distance_c": 0.2,
                "predicted_tg_sigma_c": 10.0,
                "candidate_origin": "literature_review",
                "process_template": "epoxy_amine_thermal_cure",
                "risk_flags": "",
                "validation_lane": "dsc_candidate_after_review",
                "validation_methods": "process_feasibility_review",
                "process_completion_required": False,
                "high_fidelity_required": False,
                "dsc_ready_without_process_completion": True,
                "missing_process_fields": "",
                "validation_score": 0.8,
                "smiles": "CCO|NCC",
                "ratios": "0.50000:0.50000",
            },
        ]
    ).to_csv(plan, index=False)

    requests, summary = build_requests(plan, Path("trail/experiments/observation_schema.yaml"))

    assert summary["request_rows"] == 3
    assert summary["process_completion_request_rows"] == 1
    assert summary["high_fidelity_request_rows"] == 1
    assert summary["real_dsc_request_rows"] == 1
    assert summary["blocked_by_process_completion_rows"] == 1
    assert summary["expected_observation_source_counts"]["high_fidelity_simulation"] == 1
    assert summary["expected_observation_source_counts"]["real_dsc"] == 1
    process = requests[requests["task_type"] == "process_completion"].iloc[0]
    high_fidelity = requests[requests["task_type"] == "high_fidelity_validation"].iloc[0]
    real_dsc = requests[requests["task_type"] == "real_dsc_planning"].iloc[0]
    assert process["eligible_observation_source_type"] == ""
    assert high_fidelity["eligible_observation_source_type"] == "high_fidelity_simulation"
    assert high_fidelity["authority_weight_if_completed"] == 3.0
    assert bool(high_fidelity["blocked_by_process_completion"]) is True
    assert real_dsc["eligible_observation_source_type"] == "real_dsc"
    assert real_dsc["authority_weight_if_completed"] == 5.0
