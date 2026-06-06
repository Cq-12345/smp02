from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.build_predictor_model_registry import build_model_registry


def metric_row(
    method: str,
    latent: int,
    path: Path,
    mapek: float,
    mae: float,
    rmse: float,
    r2: float,
    predictor_kind: str = "joblib",
) -> dict[str, object]:
    return {
        "ML method": method,
        "latent_size": latent,
        "model_family": "model_zoo",
        "predictor_kind": predictor_kind,
        "model_path": str(path),
        "MAPEK test dataset (%)": mapek,
        "MAE test dataset (C)": mae,
        "RMSE test dataset (C)": rmse,
        "R2 test": r2,
    }


def test_predictor_model_registry_selects_primary_backups_and_ensemble(tmp_path: Path) -> None:
    gpr = tmp_path / "gpr.joblib"
    nusvr = tmp_path / "nusvr.joblib"
    xgb = tmp_path / "xgb.joblib"
    better_r2 = tmp_path / "r2.joblib"
    missing = tmp_path / "missing.joblib"
    for path in [gpr, nusvr, xgb, better_r2]:
        path.write_text("placeholder", encoding="utf-8")
    metrics = pd.DataFrame(
        [
            metric_row("VAE (512) + GaussianProcess_RBF", 512, gpr, 3.9, 18.0, 40.0, 0.82),
            metric_row("VAE (512) + NuSVR_RBF", 512, nusvr, 4.1, 17.0, 30.0, 0.89),
            metric_row("VAE (512) + XGBoost_hist_depth3", 512, xgb, 4.3, 20.0, 35.0, 0.85),
            metric_row("VAE (256) + Ridge", 256, better_r2, 5.0, 21.0, 33.0, 0.91),
            metric_row("VAE (512) + Missing", 512, missing, 1.0, 1.0, 1.0, 0.99),
        ]
    )
    metrics_path = tmp_path / "metrics.csv"
    best_path = tmp_path / "best.json"
    metrics.to_csv(metrics_path, index=False)
    best_path.write_text(json.dumps(metrics.iloc[0].to_dict()), encoding="utf-8")

    registry, summary = build_model_registry(metrics_path, best_path, top_k_ensemble=3)

    assert summary["primary_method"] == "VAE (512) + GaussianProcess_RBF"
    assert summary["mae_backup_method"] == "VAE (512) + NuSVR_RBF"
    assert summary["rmse_backup_method"] == "VAE (512) + NuSVR_RBF"
    assert summary["r2_backup_method"] == "VAE (256) + Ridge"
    assert summary["uncertainty_provider_method"] == "VAE (512) + GaussianProcess_RBF"
    assert summary["ensemble_member_rows"] == 3
    assert "VAE (512) + Missing" not in summary["ensemble_member_methods"]
    assert set(registry["role"]) >= {
        "primary_closed_loop_predictor",
        "point_error_backup_mae",
        "point_error_backup_rmse",
        "point_error_backup_r2",
        "uncertainty_provider",
        "ensemble_guard_member",
    }
