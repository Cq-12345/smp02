from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_process_design_suggestion_packet import build_suggestions


def test_process_design_suggestions_use_template_union_without_unlocking_active_ledger(tmp_path: Path) -> None:
    packet = pd.DataFrame(
        [
            {
                "request_id": "validation_001_process_completion",
                "process_record_id": "review_queue_0001",
                "linked_observation_id": "candidate_001",
                "target_tg_c": 250.0,
                "surrogate_tg_c": 249.8,
                "target_distance_c": 0.2,
                "predicted_tg_sigma_c": 80.0,
                "candidate_origin": "sparse_target_replacement_250",
                "reaction_principle": "epoxy_anhydride",
                "process_template": "epoxy_anhydride_catalyzed_cure",
                "required_inputs": "cure_temperature_c;post_cure_temperature_c",
                "unlocks_observation_request": True,
                "smiles": "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|O=C1OC(=O)c2ccccc21",
                "ratios": "0.5:0.5",
            }
        ]
    )
    packet_path = tmp_path / "packet.csv"
    packet.to_csv(packet_path, index=False)
    process_template = pd.DataFrame(
        [
            {
                "process_record_id": "review_queue_0001",
                "linked_observation_id": "candidate_001",
                "source_type": "surrogate_review",
                "target_tg_c": 250.0,
                "observed_tg_c": 249.8,
                "smiles": "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|O=C1OC(=O)c2ccccc21",
                "ratios": "0.5:0.5",
                "reaction_principle": "epoxy_anhydride",
                "process_template": "epoxy_anhydride_catalyzed_cure",
                "review_status": "needs_process_details",
                "literature_source": "pytest",
                "operator": "pytest",
                "notes": "draft",
            }
        ]
    )
    process_template_path = tmp_path / "process_template.csv"
    process_template.to_csv(process_template_path, index=False)

    suggestions, suggested_process, ledger, summary = build_suggestions(
        packet_path,
        process_template_path,
        Path("trail/experiments/process_record_schema.yaml"),
        Path("trail/knowledge/smp_prior_knowledge.yaml"),
    )

    assert len(suggestions) == 1
    assert len(suggested_process) == 1
    assert len(ledger) == 1
    assert "catalyst_loading=" in suggestions.iloc[0]["suggested_inputs"]
    assert suggestions.iloc[0]["suggestion_status"] == "draft_process_design_requires_human_review"
    assert suggestions.iloc[0]["evidence_level"] == "knowledge_template_suggestion_not_observation"
    assert "high_tg_process_window" in suggestions.iloc[0]["risk_flags"]
    assert bool(ledger.iloc[0]["process_fields_complete"]) is True
    assert bool(ledger.iloc[0]["ready_for_active_ledger"]) is False
    assert summary["suggestion_rows"] == 1
    assert summary["suggested_process_record_pass_rows"] == 1
    assert summary["suggested_process_fields_complete_rows"] == 1
    assert summary["suggested_ready_for_active_ledger_rows"] == 0
    assert summary["can_unlock_observation_after_human_approval_rows"] == 1
