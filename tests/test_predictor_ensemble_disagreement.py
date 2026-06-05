from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.run_predictor_ensemble_disagreement import (
    candidate_components,
    disagreement_bucket,
    ensemble_statistics,
    select_top_predictors,
)


def test_candidate_components_supports_two_candidate_schemas() -> None:
    row_pair = pd.Series({"smiles_a": "CCO", "smiles_b": "NCC", "ratio_a": 0.25, "ratio_b": 0.75})
    row_joined = pd.Series({"smiles": "CCO|NCC", "ratios": "0.25000:0.75000"})

    assert candidate_components(row_pair) == (["CCO", "NCC"], [0.25, 0.75])
    assert candidate_components(row_joined) == (["CCO", "NCC"], [0.25, 0.75])


def test_select_top_predictors_filters_by_latent_and_existing_path(tmp_path: Path) -> None:
    existing = tmp_path / "model.joblib"
    existing.write_text("placeholder", encoding="utf-8")
    metrics = pd.DataFrame(
        [
            {"ML method": "bad latent", "latent_size": 16, "predictor_kind": "joblib", "model_path": str(existing), "MAPEK test dataset (%)": 1.0},
            {"ML method": "missing", "latent_size": 512, "predictor_kind": "joblib", "model_path": str(tmp_path / "missing.joblib"), "MAPEK test dataset (%)": 0.5},
            {"ML method": "ok", "latent_size": 512, "predictor_kind": "joblib", "model_path": str(existing), "MAPEK test dataset (%)": 2.0},
        ]
    )

    selected = select_top_predictors(metrics, latent_size=512, top_k=3, metric="MAPEK test dataset (%)")

    assert list(selected["ML method"]) == ["ok"]


def test_ensemble_statistics_and_buckets() -> None:
    predictions = pd.DataFrame({"m1": [190.0, 200.0], "m2": [194.0, 210.0], "m3": [196.0, 220.0]})
    stats = ensemble_statistics(predictions)

    assert list(stats["ensemble_model_count"]) == [3, 3]
    assert round(float(stats.loc[0, "ensemble_mean_tg_c"]), 3) == 193.333
    assert round(float(stats.loc[1, "ensemble_range_tg_c"]), 3) == 20.0
    assert disagreement_bucket(5.0, 10.0, 25.0) == "low_disagreement"
    assert disagreement_bucket(15.0, 10.0, 25.0) == "moderate_disagreement"
    assert disagreement_bucket(30.0, 10.0, 25.0) == "high_disagreement"
