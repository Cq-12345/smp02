from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_active_observation_ledger import build_active_ledger, filter_active_observations


def test_active_observation_ledger_keeps_only_passed_high_authority_rows(tmp_path: Path) -> None:
    ledger = pd.DataFrame(
        [
            {
                "observation_id": "hf_ok",
                "source_type": "high_fidelity_simulation",
                "target_tg_c": 250.0,
                "observed_tg_c": 251.0,
                "smiles": "CCO|NCC",
                "ratios": "0.5:0.5",
                "target_distance_c": 1.0,
                "authority_weight": 3.0,
                "weighted_reward": 2.4,
                "ledger_pass": True,
                "source_ledger": "validation_result_observation_ledger.csv",
            },
            {
                "observation_id": "dsc_ok",
                "source_type": "real_dsc",
                "target_tg_c": 195.0,
                "observed_tg_c": 194.0,
                "smiles": "CCO|NCC",
                "ratios": "0.5:0.5",
                "target_distance_c": 1.0,
                "authority_weight": 5.0,
                "weighted_reward": 4.0,
                "ledger_pass": "true",
                "source_ledger": "manual_dsc_ledger.csv",
            },
            {
                "observation_id": "lit_ok",
                "source_type": "literature",
                "target_tg_c": 195.0,
                "observed_tg_c": 196.0,
                "smiles": "CCO|NCC",
                "ratios": "0.5:0.5",
                "target_distance_c": 1.0,
                "authority_weight": 2.0,
                "weighted_reward": 1.6,
                "ledger_pass": "passed",
                "source_ledger": "literature_ledger.csv",
            },
            {
                "observation_id": "surrogate_ok_but_not_active",
                "source_type": "surrogate",
                "target_tg_c": 195.0,
                "observed_tg_c": 195.2,
                "smiles": "CCO|NCC",
                "ratios": "0.5:0.5",
                "target_distance_c": 0.2,
                "authority_weight": 1.0,
                "weighted_reward": 0.96,
                "ledger_pass": True,
                "source_ledger": "surrogate_ledger.csv",
            },
            {
                "observation_id": "hf_failed_ledger_gate",
                "source_type": "high_fidelity_simulation",
                "target_tg_c": 250.0,
                "observed_tg_c": 260.0,
                "smiles": "bad",
                "ratios": "0.9:0.9",
                "target_distance_c": 10.0,
                "authority_weight": 3.0,
                "weighted_reward": 0.1,
                "ledger_pass": False,
                "source_ledger": "validation_result_observation_ledger.csv",
            },
        ]
    )

    active = filter_active_observations(ledger)

    assert active["observation_id"].tolist() == ["hf_ok", "dsc_ok", "lit_ok"]
    assert set(active["source_type"]) == {"high_fidelity_simulation", "real_dsc", "literature"}
    assert active["active_evidence"].all()


def test_build_active_ledger_writes_empty_output_when_no_accepted_results(tmp_path: Path) -> None:
    input_path = tmp_path / "validation_result_observation_ledger.csv"
    pd.DataFrame(
        columns=[
            "observation_id",
            "source_type",
            "target_tg_c",
            "observed_tg_c",
            "smiles",
            "ratios",
            "ledger_pass",
        ]
    ).to_csv(input_path, index=False)

    out_path = tmp_path / "active.csv"
    summary_path = tmp_path / "summary.json"
    report_path = tmp_path / "report.md"
    active, summary = build_active_ledger([input_path], out_path, summary_path, report_path)

    assert active.empty
    assert out_path.exists()
    assert summary["input_rows"] == 0
    assert summary["active_rows"] == 0
    assert summary["validation_result_active_rows"] == 0
    assert "active_rows=0" in report_path.read_text(encoding="utf-8")
