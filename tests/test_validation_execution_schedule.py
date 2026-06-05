from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_validation_execution_schedule import build_execution_schedule


def test_validation_execution_schedule_prioritizes_process_completion_before_blocked_observations(tmp_path: Path) -> None:
    requests = pd.DataFrame(
        [
            {
                "request_id": "validation_001_process_completion",
                "validation_rank": 1,
                "task_type": "process_completion",
                "target_tg_c": 250.0,
                "target_distance_c": 0.04,
                "candidate_origin": "sparse_target_replacement_250",
                "eligible_observation_source_type": "",
                "authority_weight_if_completed": 0.0,
                "request_priority_score": 0.95,
                "required_inputs": "cure_temperature_c;catalyst_loading",
                "blocked_by_process_completion": False,
            },
            {
                "request_id": "validation_001_high_fidelity_validation",
                "validation_rank": 1,
                "task_type": "high_fidelity_validation",
                "target_tg_c": 250.0,
                "target_distance_c": 0.04,
                "candidate_origin": "sparse_target_replacement_250",
                "eligible_observation_source_type": "high_fidelity_simulation",
                "authority_weight_if_completed": 3.0,
                "request_priority_score": 0.90,
                "required_inputs": "model_ensemble_recheck",
                "blocked_by_process_completion": True,
            },
            {
                "request_id": "validation_002_process_completion",
                "validation_rank": 2,
                "task_type": "process_completion",
                "target_tg_c": 195.0,
                "target_distance_c": 0.50,
                "candidate_origin": "vae_latent_local_search",
                "eligible_observation_source_type": "",
                "authority_weight_if_completed": 0.0,
                "request_priority_score": 0.70,
                "required_inputs": "post_cure_temperature_c",
                "blocked_by_process_completion": False,
            },
        ]
    )
    request_path = tmp_path / "requests.csv"
    requests.to_csv(request_path, index=False)

    schedule, summary = build_execution_schedule(request_path, immediate_batch_size=2)

    by_request = {row["request_id"]: row for _, row in schedule.iterrows()}
    assert summary["input_request_rows"] == 3
    assert summary["immediate_executable_rows"] == 2
    assert summary["blocked_rows"] == 1
    assert summary["process_completion_unlock_rows"] == 1
    assert summary["immediate_batch_rows"] == 2
    assert summary["immediate_batch_target_counts"] == {"195.0": 1, "250.0": 1}
    assert by_request["validation_001_process_completion"]["execution_phase"] == "process_completion_now"
    assert bool(by_request["validation_001_process_completion"]["unlocks_observation_request"]) is True
    assert bool(by_request["validation_001_process_completion"]["immediate_batch_selected"]) is True
    assert by_request["validation_001_high_fidelity_validation"]["execution_phase"] == "blocked_until_process_completion"
    assert by_request["validation_001_high_fidelity_validation"]["dependency_request_id"] == "validation_001_process_completion"
    assert bool(by_request["validation_001_high_fidelity_validation"]["immediate_executable"]) is False
    assert by_request["validation_001_high_fidelity_validation"]["execution_status"] == "planned_not_completed"
