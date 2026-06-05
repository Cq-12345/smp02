from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pandas as pd

from scripts.import_proposal_eval_generation_records import run_import


def test_import_proposal_eval_generation_records_preserves_harness_gates(tmp_path: Path) -> None:
    scored = tmp_path / "replacement_proposals_scored.csv"
    pd.DataFrame(
        [
            {
                "proposal_index": 10,
                "formula_id": "f_ok",
                "replace_side": "a",
                "original_smiles": "CCO",
                "replacement_smiles": "NCC",
                "smiles": "CCO|NCC",
                "ratios": "0.50000:0.50000",
                "compatibility_reasons": "amine-alcohol smoke compatibility",
                "predicted_tg_mean_c": 196.0,
                "predicted_tg_sigma_c": 8.0,
                "ood_penalty": 0.1,
                "target_ok": True,
                "chemistry_ok": True,
                "harness_pass": True,
            },
            {
                "proposal_index": 11,
                "formula_id": "f_fail",
                "replace_side": "b",
                "original_smiles": "CCC",
                "replacement_smiles": "CCCC",
                "smiles": "CCC|CCCC",
                "ratios": "0.50000:0.50000",
                "compatibility_reasons": "",
                "predicted_tg_mean_c": 260.0,
                "predicted_tg_sigma_c": 12.0,
                "ood_penalty": 0.2,
                "target_ok": False,
                "chemistry_ok": False,
                "harness_pass": False,
            },
        ]
    ).to_csv(scored, index=False)

    ledger, summary = run_import(
        Namespace(
            scored=str(scored),
            strategy="vae_latent_local_search",
            source_context="unit_test_eval",
            generator_id="unit_test_generator",
            target_tg_c=195.0,
            target_window_c=5.0,
            generation_time="2026-06-06",
            reward_temperature_c=5.0,
            schema="trail/generation/generation_record_schema.yaml",
            limit=None,
            out_dir=str(tmp_path / "records"),
            report=str(tmp_path / "report.md"),
        )
    )

    assert summary["input_rows"] == 2
    assert summary["harness_pass_rows"] == 1
    assert summary["record_pass_rows"] == 2
    assert int(ledger["harness_pass"].sum()) == 1
    failed = ledger.loc[~ledger["harness_pass"]].iloc[0]
    assert "target_out_of_window" in failed["harness_failure_reason"]
    assert "chemistry_evidence_missing" in failed["harness_failure_reason"]
    payload = json.loads(ledger.loc[ledger["harness_pass"]].iloc[0]["candidate_json"])
    assert payload["proposal_index"] == 10
    assert payload["source_row_index"] == 0
    assert (tmp_path / "records" / "generation_record_ledger.csv").exists()
    assert (tmp_path / "records" / "generation_record_summary.json").exists()
    assert (tmp_path / "report.md").exists()
