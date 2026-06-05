from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.import_generation_ledger_observations import generation_ledger_to_observation_input
from trail.experiments.import_observations import import_observations


def test_generation_ledger_bridge_only_promotes_harnessed_predicted_records(tmp_path: Path) -> None:
    ledger = pd.DataFrame(
        [
            {
                "generation_id": "ok",
                "strategy": "llm_rag_principle_generation",
                "stage": "harnessed",
                "target_tg_c": 195.0,
                "candidate_smiles": "C1CO1|NCCN",
                "candidate_ratios": "0.50000:0.50000",
                "predicted_tg_mean_c": 195.2,
                "predicted_tg_sigma_c": 1.5,
                "harness_pass": True,
                "record_pass": True,
                "target_distance_c": 0.2,
            },
            {
                "generation_id": "draft",
                "strategy": "llm_smiles_generation",
                "stage": "draft",
                "target_tg_c": 195.0,
                "candidate_smiles": "C1CO1|NCCN",
                "candidate_ratios": "0.50000:0.50000",
                "predicted_tg_mean_c": "",
                "harness_pass": False,
                "record_pass": True,
            },
        ]
    )

    observation_input = generation_ledger_to_observation_input(
        ledger,
        source_type="surrogate",
        observation_prefix="test",
        operator="pytest",
        method="generation_record_surrogate_bridge",
        experiment_date="2026-06-06",
        require_harness_pass=True,
        require_record_pass=True,
    )
    input_path = tmp_path / "observations.csv"
    observation_input.to_csv(input_path, index=False)
    observation_ledger, summary = import_observations(input_path, Path("trail/experiments/observation_schema.yaml"), 5.0)

    assert list(observation_input["observation_id"]) == ["test_llm_rag_principle_generation_ok"]
    assert summary["ledger_pass_rows"] == 1
    assert float(observation_ledger.iloc[0]["observed_tg_c"]) == 195.2
    assert observation_ledger.iloc[0]["source_type"] == "surrogate"
