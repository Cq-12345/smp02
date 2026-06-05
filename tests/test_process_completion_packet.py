from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_process_completion_packet import build_process_completion_packet


def test_process_completion_packet_expands_immediate_batch_into_fillable_process_records(tmp_path: Path) -> None:
    schedule = pd.DataFrame(
        [
            {
                "execution_rank": 1,
                "request_id": "validation_001_process_completion",
                "validation_rank": 1,
                "linked_observation_id": "candidate_001",
                "task_type": "process_completion",
                "target_tg_c": 195.0,
                "surrogate_tg_c": 195.2,
                "target_distance_c": 0.2,
                "predicted_tg_sigma_c": 25.0,
                "candidate_origin": "vae_latent_local_search",
                "process_template": "epoxy_amine_thermal_cure",
                "smiles": "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|NCCN",
                "ratios": "0.5:0.5",
                "request_priority_score": 0.9,
                "required_inputs": "mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h",
                "execution_status": "planned_not_completed",
                "immediate_batch_selected": True,
                "unlocks_observation_request": True,
            },
            {
                "execution_rank": 2,
                "request_id": "validation_001_high_fidelity_validation",
                "validation_rank": 1,
                "linked_observation_id": "candidate_001",
                "task_type": "high_fidelity_validation",
                "target_tg_c": 195.0,
                "surrogate_tg_c": 195.2,
                "target_distance_c": 0.2,
                "predicted_tg_sigma_c": 25.0,
                "candidate_origin": "vae_latent_local_search",
                "process_template": "epoxy_amine_thermal_cure",
                "smiles": "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|NCCN",
                "ratios": "0.5:0.5",
                "request_priority_score": 0.8,
                "required_inputs": "model_ensemble_recheck",
                "execution_status": "planned_not_completed",
                "immediate_batch_selected": False,
                "unlocks_observation_request": False,
            },
        ]
    )
    schedule_path = tmp_path / "schedule.csv"
    schedule.to_csv(schedule_path, index=False)
    draft = pd.DataFrame(
        [
            {
                "process_record_id": "review_queue_0001",
                "linked_observation_id": "candidate_001",
                "source_type": "surrogate_review",
                "target_tg_c": 195.0,
                "observed_tg_c": 195.2,
                "smiles": "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|NCCN",
                "ratios": "0.5:0.5",
                "reaction_principle": "epoxy_primary_amine",
                "process_template": "epoxy_amine_thermal_cure",
                "review_status": "needs_human_review",
                "literature_source": "pytest",
                "operator": "pytest",
                "notes": "draft",
            }
        ]
    )
    draft_path = tmp_path / "draft.csv"
    draft.to_csv(draft_path, index=False)

    packet, process_template, ledger, summary = build_process_completion_packet(
        schedule_path,
        draft_path,
        Path("trail/experiments/process_record_schema.yaml"),
        Path("trail/knowledge/smp_prior_knowledge.yaml"),
    )

    assert len(packet) == 1
    assert len(process_template) == 1
    assert len(ledger) == 1
    assert packet.iloc[0]["process_record_id"] == "review_queue_0001"
    assert packet.iloc[0]["process_completion_status"] == "pending_human_input"
    assert packet.iloc[0]["mix_temperature_c"] == ""
    assert bool(packet.iloc[0]["unlocks_observation_request"]) is True
    assert process_template.iloc[0]["review_status"] == "needs_process_details"
    assert summary["selected_process_completion_rows"] == 1
    assert summary["draft_record_matches"] == 1
    assert summary["unlocks_observation_rows"] == 1
    assert summary["process_record_pass_rows"] == 1
    assert summary["ready_for_active_ledger_rows"] == 0
    assert summary["process_incomplete_rows"] == 1
    assert summary["required_field_frequency"]["cure_temperature_c"] == 1
