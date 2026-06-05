from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_human_experiment_review_queue import build_review_queue, infer_reaction_principle, process_template_for_principle, read_knowledge
from trail.experiments.import_process_records import import_process_records


def test_reaction_text_maps_to_process_template() -> None:
    knowledge = read_knowledge(Path("trail/knowledge/smp_prior_knowledge.yaml"))

    principle = infer_reaction_principle("氰酸酯-胺共反应。")

    assert principle == "cyanate_ester_amine"
    assert process_template_for_principle(principle, knowledge) == "cyanate_ester_triazine_cure"


def test_human_review_queue_keeps_surrogate_drafts_out_of_active_ledger(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates.csv"
    pd.DataFrame(
        [
            {
                "harness_pass": True,
                "formula_id": 1,
                "smiles": "N#COc1ccc(CC2CCCC(Cc3ccc(OC#N)cc3)C2)cc1|Nc1ccc(Oc2ccc(N)cc2)cc1",
                "ratios": "0.90000:0.10000",
                "predicted_tg_mean_c": 194.63,
                "predicted_tg_sigma_c": 37.5,
                "target_tg_c": 195.0,
                "target_distance_c": 0.37,
                "compatibility_reasons": "氰酸酯-胺共反应。",
            }
        ]
    ).to_csv(candidates, index=False)

    queue, process_records, summary = build_review_queue(
        [(candidates, "unit_test_candidate")],
        Path("trail/knowledge/smp_prior_knowledge.yaml"),
        per_table_limit=10,
        top_k=5,
    )
    draft_path = tmp_path / "draft_process_records.csv"
    process_records.to_csv(draft_path, index=False)
    ledger, process_summary = import_process_records(
        draft_path,
        Path("trail/experiments/process_record_schema.yaml"),
        Path("trail/knowledge/smp_prior_knowledge.yaml"),
    )

    assert summary["queue_rows"] == 1
    assert queue.iloc[0]["reaction_principle"] == "cyanate_ester_amine"
    assert queue.iloc[0]["process_template"] == "cyanate_ester_triazine_cure"
    assert "trimerization_temperature_c" in queue.iloc[0]["missing_process_fields"]
    assert queue.iloc[0]["review_priority"] == "process_design_for_dsc"
    assert process_summary["process_record_pass_rows"] == 1
    assert process_summary["ready_for_active_ledger_rows"] == 0
    assert bool(ledger.iloc[0]["ready_for_active_ledger"]) is False
