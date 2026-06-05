from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from trail.workflow.multi_agent_workflow import summarize


def test_workflow_summary_includes_predictor_ensemble_disagreement(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates.csv"
    candidates.write_text("smiles,ratios\nCCO|NCC,0.5:0.5\n", encoding="utf-8")
    history = tmp_path / "history.json"
    history.write_text("[]", encoding="utf-8")
    feedback = tmp_path / "feedback.json"
    feedback.write_text("{}", encoding="utf-8")
    ledger = tmp_path / "ledger.csv"
    pd.DataFrame({"harness_pass": [True, False]}).to_csv(ledger, index=False)
    feedback_aware_ledger = tmp_path / "feedback_aware_ledger.csv"
    pd.DataFrame({"harness_pass": [True]}).to_csv(feedback_aware_ledger, index=False)
    observations = tmp_path / "observations.csv"
    pd.DataFrame({"ledger_pass": [True]}).to_csv(observations, index=False)
    pievo_summary = tmp_path / "pievo_summary.json"
    pievo_summary.write_text(
        json.dumps({"best_selected_target_distance_c": 0.5, "external_observation_summary": {"accepted_rows": 1}}),
        encoding="utf-8",
    )
    ensemble_summary = tmp_path / "ensemble_summary.json"
    ensemble_summary.write_text(
        json.dumps(
            {
                "ensemble_models": 6,
                "near_target_rows": 1045,
                "near_target_low_disagreement_rows": 84,
                "near_target_high_disagreement_rows": 526,
                "mean_ensemble_std_c": 32.16,
                "mean_abs_best_model_delta_c": 30.37,
            }
        ),
        encoding="utf-8",
    )

    result = summarize(
        candidates,
        history,
        feedback,
        ledger,
        feedback_aware_ledger,
        observations,
        pievo_summary,
        ensemble_summary,
    )

    assert result["predictor_ensemble_models"] == 6
    assert result["predictor_ensemble_near_target_rows"] == 1045
    assert result["predictor_ensemble_low_disagreement_rows"] == 84
    assert result["predictor_ensemble_high_disagreement_rows"] == 526
    assert result["predictor_ensemble_mean_std_c"] == 32.16
    assert result["predictor_ensemble_mean_abs_best_model_delta_c"] == 30.37
