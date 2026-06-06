from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


LOWER_IS_BETTER = {
    "MAPEK test dataset (%)": True,
    "MAE test dataset (C)": True,
    "RMSE test dataset (C)": True,
    "MAPE test dataset (%)": True,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def bool_model_exists(path: Any) -> bool:
    return Path(str(path)).exists()


def sort_by_metric(frame: pd.DataFrame, metric: str, lower_is_better: bool = True) -> pd.DataFrame:
    work = frame.replace([float("inf"), float("-inf")], pd.NA).dropna(subset=[metric]).copy()
    secondary = [col for col in ["MAPEK test dataset (%)", "MAE test dataset (C)", "RMSE test dataset (C)"] if col in work.columns and col != metric]
    return work.sort_values([metric, *secondary], ascending=[lower_is_better, *([True] * len(secondary))]).reset_index(drop=True)


def usable_joblib_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    work = metrics.copy()
    if "predictor_kind" in work.columns:
        work = work[work["predictor_kind"].astype(str) == "joblib"]
    if "model_path" in work.columns:
        work = work[work["model_path"].map(bool_model_exists)]
    return work.reset_index(drop=True)


def row_payload(row: pd.Series, role: str, role_rank: int, rationale: str) -> dict[str, Any]:
    return {
        "role": role,
        "role_rank": int(role_rank),
        "ML method": row.get("ML method", ""),
        "latent_size": int(row.get("latent_size", 0)),
        "model_family": row.get("model_family", ""),
        "predictor_kind": row.get("predictor_kind", ""),
        "model_path": row.get("model_path", ""),
        "MAPEK test dataset (%)": float(row.get("MAPEK test dataset (%)", 0.0)),
        "MAE test dataset (C)": float(row.get("MAE test dataset (C)", 0.0)),
        "RMSE test dataset (C)": float(row.get("RMSE test dataset (C)", 0.0)),
        "R2 test": float(row.get("R2 test", 0.0)),
        "selection_rationale": rationale,
        "model_path_exists": bool_model_exists(row.get("model_path", "")),
    }


def best_metric_row(metrics: pd.DataFrame, metric: str, lower_is_better: bool = True) -> pd.Series:
    ranked = sort_by_metric(metrics, metric, lower_is_better)
    if ranked.empty:
        raise ValueError(f"No usable model rows for metric {metric}")
    return ranked.iloc[0]


def build_model_registry(
    metrics_path: Path,
    best_model_path: Path,
    top_k_ensemble: int = 6,
    selection_metric: str = "MAPEK test dataset (%)",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    metrics = pd.read_csv(metrics_path)
    usable = usable_joblib_metrics(metrics)
    if usable.empty:
        raise ValueError("No usable joblib predictor rows with existing model_path.")
    best_json = read_json(best_model_path)
    if best_json:
        primary = pd.Series(best_json)
        if not bool_model_exists(primary.get("model_path", "")):
            primary = best_metric_row(usable, selection_metric, lower_is_better=LOWER_IS_BETTER.get(selection_metric, True))
    else:
        primary = best_metric_row(usable, selection_metric, lower_is_better=LOWER_IS_BETTER.get(selection_metric, True))
    primary_latent = int(primary.get("latent_size"))
    same_latent = usable[usable["latent_size"].astype(int) == primary_latent].copy()
    rows = [
        row_payload(
            primary,
            "primary_closed_loop_predictor",
            1,
            "lowest MAPEK test model; retained as default because it also provides GPR uncertainty when GaussianProcess is selected",
        )
    ]
    mae = best_metric_row(usable, "MAE test dataset (C)", lower_is_better=True)
    rows.append(row_payload(mae, "point_error_backup_mae", 1, "lowest MAE test model across usable model zoo"))
    rmse = best_metric_row(usable, "RMSE test dataset (C)", lower_is_better=True)
    rows.append(row_payload(rmse, "point_error_backup_rmse", 1, "lowest RMSE test model across usable model zoo"))
    r2 = best_metric_row(usable, "R2 test", lower_is_better=False)
    rows.append(row_payload(r2, "point_error_backup_r2", 1, "highest R2 test model across usable model zoo"))
    gpr_candidates = usable[usable["ML method"].astype(str).str.contains("GaussianProcess", case=False, na=False)]
    uncertainty = best_metric_row(gpr_candidates, selection_metric, lower_is_better=True) if not gpr_candidates.empty else primary
    rows.append(row_payload(uncertainty, "uncertainty_provider", 1, "best usable GaussianProcess model for predictive standard deviation"))
    ensemble = sort_by_metric(same_latent, selection_metric, lower_is_better=True).head(top_k_ensemble)
    for rank, (_, row) in enumerate(ensemble.iterrows(), start=1):
        rows.append(
            row_payload(
                row,
                "ensemble_guard_member",
                rank,
                f"top-{top_k_ensemble} same-latent joblib model for ensemble disagreement guard",
            )
        )
    registry = pd.DataFrame(rows)
    summary = {
        "metrics_rows": int(len(metrics)),
        "usable_joblib_rows": int(len(usable)),
        "latent_sizes": [int(value) for value in sorted(usable["latent_size"].astype(int).unique())],
        "selection_metric": selection_metric,
        "primary_method": str(primary.get("ML method")),
        "primary_latent_size": primary_latent,
        "primary_model_path": str(primary.get("model_path")),
        "primary_model_exists": bool_model_exists(primary.get("model_path")),
        "primary_mapek_test_pct": float(primary.get("MAPEK test dataset (%)")),
        "primary_mae_test_c": float(primary.get("MAE test dataset (C)")),
        "primary_rmse_test_c": float(primary.get("RMSE test dataset (C)")),
        "primary_r2_test": float(primary.get("R2 test")),
        "mae_backup_method": str(mae.get("ML method")),
        "mae_backup_mae_test_c": float(mae.get("MAE test dataset (C)")),
        "rmse_backup_method": str(rmse.get("ML method")),
        "rmse_backup_rmse_test_c": float(rmse.get("RMSE test dataset (C)")),
        "r2_backup_method": str(r2.get("ML method")),
        "r2_backup_r2_test": float(r2.get("R2 test")),
        "uncertainty_provider_method": str(uncertainty.get("ML method")),
        "uncertainty_provider_latent_size": int(uncertainty.get("latent_size")),
        "ensemble_member_rows": int(len(ensemble)),
        "ensemble_member_methods": [str(value) for value in ensemble["ML method"].tolist()],
        "recommended_default_predictor": "primary_closed_loop_predictor",
        "recommended_guard": "ensemble_guard_member",
        "evidence_level": "predictor_selection_registry_not_new_training",
    }
    return registry, summary


def write_report(registry: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Predictor Model Selection Registry",
        "",
        "本文档把当前 model zoo 的选择结果固化为可被 workflow 读取的注册表。它不重新训练模型，只把已有 85/15 split 指标转成后续闭环的模型契约。",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, list):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Registry Rows",
            "",
            "| role | rank | model | latent | MAPEK test (%) | MAE test (C) | RMSE test (C) | R2 test |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in registry.iterrows():
        lines.append(
            f"| {row['role']} | {int(row['role_rank'])} | {row['ML method']} | {int(row['latent_size'])} | "
            f"{float(row['MAPEK test dataset (%)']):.4f} | {float(row['MAE test dataset (C)']):.4f} | "
            f"{float(row['RMSE test dataset (C)']):.4f} | {float(row['R2 test']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Usage",
            "",
            "- `primary_closed_loop_predictor` 是默认闭环代理模型；当前应继续使用 `VAE(512)+GaussianProcess_RBF`。",
            "- `point_error_backup_*` 是点预测误差视角的备选，不替代 uncertainty provider。",
            "- `ensemble_guard_member` 是 PiEvo live ensemble guard 和候选 OOD/disagreement 审计使用的模型集合。",
            "- 该 registry 的 `evidence_level` 表明这里只是选择契约，不是新训练结果，也不是物理实验观测。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a predictor model selection registry from the trained model zoo.")
    parser.add_argument("--metrics", default="artifacts/reproduce/predictors/all_predictor_metrics.csv")
    parser.add_argument("--best-model", default="artifacts/reproduce/predictors/best_model.json")
    parser.add_argument("--out-dir", default="artifacts/trail/predictors/model_selection_registry")
    parser.add_argument("--report", default="reports/predictor_model_selection_registry.md")
    parser.add_argument("--top-k-ensemble", type=int, default=6)
    parser.add_argument("--selection-metric", default="MAPEK test dataset (%)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    registry, summary = build_model_registry(Path(args.metrics), Path(args.best_model), args.top_k_ensemble, args.selection_metric)
    registry_path = out_dir / "predictor_model_selection_registry.csv"
    summary_path = out_dir / "predictor_model_selection_summary.json"
    registry.to_csv(registry_path, index=False)
    summary = {
        **summary,
        "registry_path": str(registry_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(registry, summary, Path(args.report))


if __name__ == "__main__":
    main()
