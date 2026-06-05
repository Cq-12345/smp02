from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pandas as pd

from scripts.build_rule_template_generation_records import run_import


def test_build_rule_template_generation_records_from_selected_candidates(tmp_path: Path) -> None:
    selected = tmp_path / "selected_candidates.csv"
    pd.DataFrame(
        [
            {
                "smiles_a": "CCO",
                "smiles_b": "NCC",
                "groups_a": "hydroxyl",
                "groups_b": "primary_amine",
                "compatibility_reason": "amine-alcohol smoke compatibility",
                "ratio_a": 0.5,
                "ratio_b": 0.5,
                "predicted_tg": 195.5,
                "target_distance": 0.5,
                "in_target_range": True,
            },
            {
                "smiles_a": "CCC",
                "smiles_b": "CCCC",
                "groups_a": "alkyl",
                "groups_b": "alkyl",
                "compatibility_reason": "",
                "ratio_a": 0.5,
                "ratio_b": 0.5,
                "predicted_tg": 220.0,
                "target_distance": 25.0,
                "in_target_range": False,
            },
        ]
    ).to_csv(selected, index=False)

    ledger, summary = run_import(
        Namespace(
            selected=str(selected),
            target_tg_c=195.0,
            target_window_c=5.0,
            max_records=10,
            generation_time="2026-06-06",
            reward_temperature_c=5.0,
            schema="trail/generation/generation_record_schema.yaml",
            out_dir=str(tmp_path / "out"),
            report=str(tmp_path / "report.md"),
        )
    )

    assert summary["input_rows"] == 1
    assert summary["harness_pass_rows"] == 1
    assert set(ledger["strategy"]) == {"rule_template"}
    payload = json.loads(ledger.iloc[0]["candidate_json"])
    assert payload["groups_a"] == "hydroxyl"
    assert payload["source_row_index"] == 0
    assert (tmp_path / "out" / "generation_record_ledger.csv").exists()
    assert (tmp_path / "report.md").exists()
