from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from smp02.utils import load_config, resolve_device
from smp02.vae import encode_smiles, load_vae_checkpoint


def safe_column_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_").lower()


def candidate_components(row: pd.Series) -> tuple[list[str], list[float]]:
    if "smiles" in row and "ratios" in row and pd.notna(row["smiles"]) and pd.notna(row["ratios"]):
        smiles = [part.strip() for part in str(row["smiles"]).split("|") if part.strip()]
        ratios = [float(part) for part in str(row["ratios"]).split(":") if str(part).strip()]
    elif {"smiles_a", "smiles_b", "ratio_a", "ratio_b"}.issubset(row.index):
        smiles = [str(row["smiles_a"]).strip(), str(row["smiles_b"]).strip()]
        ratios = [float(row["ratio_a"]), float(row["ratio_b"])]
    else:
        raise ValueError("Candidate row must contain either smiles/ratios or smiles_a/smiles_b/ratio_a/ratio_b.")
    if len(smiles) != len(ratios):
        raise ValueError(f"SMILES count {len(smiles)} != ratio count {len(ratios)}")
    total = sum(ratios)
    if total <= 0:
        raise ValueError("Ratios must have positive sum.")
    return smiles, [ratio / total for ratio in ratios]


def candidate_feature_matrix(candidates: pd.DataFrame, vectors: dict[str, np.ndarray], latent_size: int) -> tuple[np.ndarray, list[dict[str, Any]]]:
    features = np.zeros((len(candidates), latent_size), dtype=np.float32)
    parse_rows: list[dict[str, Any]] = []
    for idx, row in candidates.iterrows():
        smiles, ratios = candidate_components(row)
        missing = [smiles_value for smiles_value in smiles if smiles_value not in vectors]
        if missing:
            raise ValueError(f"Missing VAE vectors for candidate row {idx}: {missing}")
        for smiles_value, ratio in zip(smiles, ratios, strict=False):
            features[int(idx)] += float(ratio) * vectors[smiles_value].astype(np.float32)
        parse_rows.append(
            {
                "candidate_smiles": "|".join(smiles),
                "candidate_ratios": ":".join(f"{ratio:.5f}" for ratio in ratios),
                "candidate_components": len(smiles),
            }
        )
    return features, parse_rows


def select_top_predictors(metrics: pd.DataFrame, latent_size: int, top_k: int, metric: str) -> pd.DataFrame:
    frame = metrics.copy()
    frame = frame[(frame["latent_size"].astype(int) == int(latent_size)) & (frame["predictor_kind"].astype(str) == "joblib")]
    frame = frame[frame["model_path"].astype(str).map(lambda path: Path(path).exists())]
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[metric])
    if frame.empty:
        raise ValueError(f"No usable joblib predictors for latent_size={latent_size}, metric={metric}.")
    return frame.sort_values(metric, ascending=True).head(top_k).reset_index(drop=True)


def predict_bundle(bundle: dict[str, Any], x: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    x_scaled = bundle["x_scaler"].transform(x)
    model = bundle["model"]
    try:
        y_scaled, std_scaled = model.predict(x_scaled, return_std=True)
        y = bundle["y_scaler"].inverse_transform(np.asarray(y_scaled).reshape(-1, 1)).ravel()
        data_range = float(getattr(bundle["y_scaler"], "data_range_", np.asarray([1.0]))[0])
        return y, np.asarray(std_scaled, dtype=float).reshape(-1) * data_range
    except TypeError:
        y_scaled = model.predict(x_scaled)
    y = bundle["y_scaler"].inverse_transform(np.asarray(y_scaled).reshape(-1, 1)).ravel()
    return y, None


def ensemble_statistics(predictions: pd.DataFrame) -> pd.DataFrame:
    values = predictions.to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "ensemble_mean_tg_c": np.mean(values, axis=1),
            "ensemble_std_tg_c": np.std(values, axis=1, ddof=0),
            "ensemble_min_tg_c": np.min(values, axis=1),
            "ensemble_max_tg_c": np.max(values, axis=1),
            "ensemble_range_tg_c": np.max(values, axis=1) - np.min(values, axis=1),
            "ensemble_model_count": values.shape[1],
        }
    )


def disagreement_bucket(std: float, consensus_threshold: float, high_threshold: float) -> str:
    if std <= consensus_threshold:
        return "low_disagreement"
    if std >= high_threshold:
        return "high_disagreement"
    return "moderate_disagreement"


def write_report(
    scored: pd.DataFrame,
    predictors: pd.DataFrame,
    summary: dict[str, Any],
    out_dir: Path,
    report_path: Path,
    target_tg_c: float,
    target_window_c: float,
) -> None:
    lines = [
        "# 预测模型集成分歧审计",
        "",
        "本文档回应 TODO 中“预测模型：GNN、CNN/SVR/RF 论文对比，以及更多模型”的后续补强：不只选单个最佳模型，而是用当前 model zoo 的强模型集成来标记候选的 epistemic disagreement / OOD 风险。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM 表示，不涉及暂缓的超图表示。",
        "",
        "## 输出文件",
        "",
        f"- Scored candidates: `{out_dir / 'candidate_ensemble_disagreement.csv'}`",
        f"- Predictor table: `{out_dir / 'ensemble_predictors.csv'}`",
        f"- Summary: `{out_dir / 'ensemble_disagreement_summary.json'}`",
        f"- Low-disagreement near-target candidates: `{out_dir / 'low_disagreement_near_target.csv'}`",
        f"- High-disagreement near-target candidates: `{out_dir / 'high_disagreement_near_target.csv'}`",
        "",
        "## 集成成员",
        "",
        "| rank | model | MAPEK test (%) | MAE test (C) | R2 test |",
        "| ---: | --- | ---: | ---: | ---: |",
    ]
    for rank, (_, row) in enumerate(predictors.iterrows(), start=1):
        lines.append(
            f"| {rank} | {row['ML method']} | {float(row['MAPEK test dataset (%)']):.4f} | "
            f"{float(row['MAE test dataset (C)']):.4f} | {float(row['R2 test']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## 汇总",
            "",
            "| item | value |",
            "| --- | ---: |",
        ]
    )
    for key, value in summary.items():
        if isinstance(value, dict):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 低分歧近目标候选示例",
            "",
            "| rank | ensemble Tg (C) | std (C) | GPR delta (C) | chemistry | ratios |",
            "| ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    low = scored[scored["ensemble_near_target_low_disagreement"]].sort_values(["ensemble_target_distance_c", "ensemble_std_tg_c"]).head(10)
    for rank, (_, row) in enumerate(low.iterrows(), start=1):
        lines.append(
            f"| {rank} | {float(row['ensemble_mean_tg_c']):.3f} | {float(row['ensemble_std_tg_c']):.3f} | "
            f"{float(row['best_model_delta_c']):.3f} | {str(row.get('compatibility_reason', row.get('compatibility_reasons', ''))).replace('|', '; ')} | "
            f"{row['candidate_ratios']} |"
        )
    lines.extend(
        [
            "",
            "## 高分歧近目标候选示例",
            "",
            "| rank | ensemble Tg (C) | std (C) | range (C) | GPR delta (C) | chemistry |",
            "| ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    high = scored[scored["ensemble_near_target_high_disagreement"]].sort_values(["ensemble_std_tg_c", "ensemble_target_distance_c"], ascending=[False, True]).head(10)
    for rank, (_, row) in enumerate(high.iterrows(), start=1):
        lines.append(
            f"| {rank} | {float(row['ensemble_mean_tg_c']):.3f} | {float(row['ensemble_std_tg_c']):.3f} | "
            f"{float(row['ensemble_range_tg_c']):.3f} | {float(row['best_model_delta_c']):.3f} | "
            f"{str(row.get('compatibility_reason', row.get('compatibility_reasons', ''))).replace('|', '; ')} |"
        )
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- `ensemble_std_tg_c` 是模型间分歧，不等价于物理不确定性；它适合作为候选推荐和人工审核的 epistemic/OOD 信号。",
            "- 低分歧且接近目标的候选适合优先进入 PiEvo/人工审核；高分歧但接近目标的候选适合标记为需要更多模型或实验验证。",
            "- 当前 best model 仍可作为主代理，但 `best_model_delta_c` 能暴露 GPR 与强点预测模型集体判断的偏差。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_audit(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = load_config(args.config)
    device = resolve_device(args.device)
    metrics = pd.read_csv(args.metrics)
    best = json.loads(Path(args.best_model).read_text(encoding="utf-8"))
    latent_size = int(args.latent_size or best["latent_size"])
    predictors = select_top_predictors(metrics, latent_size, args.top_k, args.selection_metric)
    candidates = pd.read_csv(args.candidates).head(args.limit) if args.limit else pd.read_csv(args.candidates)

    checkpoint_path = Path(cfg["output_dir"]) / "vae" / f"finetuned_latent_{latent_size}.pt"
    vae, checkpoint = load_vae_checkpoint(checkpoint_path, map_location=device)
    vae.to(device)
    unique_smiles = sorted({smiles for _, row in candidates.iterrows() for smiles in candidate_components(row)[0]})
    latent = encode_smiles(vae, unique_smiles, checkpoint["charset"], int(checkpoint["max_length"]), device, batch_size=args.encode_batch_size)
    vectors = {smiles: latent[idx] for idx, smiles in enumerate(unique_smiles)}
    x, parse_rows = candidate_feature_matrix(candidates.reset_index(drop=True), vectors, latent_size)

    prediction_columns = {}
    gpr_sigma = None
    for _, predictor_row in predictors.iterrows():
        bundle = joblib.load(predictor_row["model_path"])
        pred, sigma = predict_bundle(bundle, x)
        name = safe_column_name(str(predictor_row["ML method"]).replace(f"VAE ({latent_size}) + ", ""))
        prediction_columns[f"pred_{name}_tg_c"] = pred
        if sigma is not None:
            prediction_columns[f"sigma_{name}_tg_c"] = sigma
            if "gaussianprocess" in name:
                gpr_sigma = sigma

    prediction_frame = pd.DataFrame(prediction_columns)
    pred_only = prediction_frame[[column for column in prediction_frame.columns if column.startswith("pred_")]]
    stats = ensemble_statistics(pred_only)
    scored = pd.concat([candidates.reset_index(drop=True), pd.DataFrame(parse_rows), prediction_frame, stats], axis=1)
    base_col = "predicted_tg" if "predicted_tg" in scored.columns else "predicted_tg_mean_c" if "predicted_tg_mean_c" in scored.columns else None
    if base_col:
        scored["best_model_predicted_tg_c"] = pd.to_numeric(scored[base_col], errors="coerce")
        scored["best_model_delta_c"] = scored["ensemble_mean_tg_c"] - scored["best_model_predicted_tg_c"]
    else:
        scored["best_model_predicted_tg_c"] = np.nan
        scored["best_model_delta_c"] = np.nan
    scored["gpr_sigma_tg_c"] = gpr_sigma if gpr_sigma is not None else np.nan
    scored["ensemble_target_distance_c"] = (scored["ensemble_mean_tg_c"] - float(args.target_tg_c)).abs()
    scored["disagreement_bucket"] = [
        disagreement_bucket(value, args.consensus_std_c, args.high_disagreement_std_c)
        for value in scored["ensemble_std_tg_c"].astype(float)
    ]
    scored["ensemble_near_target"] = scored["ensemble_target_distance_c"] <= float(args.target_window_c)
    scored["ensemble_near_target_low_disagreement"] = scored["ensemble_near_target"] & (scored["ensemble_std_tg_c"] <= float(args.consensus_std_c))
    scored["ensemble_near_target_high_disagreement"] = scored["ensemble_near_target"] & (scored["ensemble_std_tg_c"] >= float(args.high_disagreement_std_c))

    predictors.to_csv(out_dir / "ensemble_predictors.csv", index=False)
    scored.to_csv(out_dir / "candidate_ensemble_disagreement.csv", index=False)
    scored[scored["ensemble_near_target_low_disagreement"]].sort_values(["ensemble_target_distance_c", "ensemble_std_tg_c"]).to_csv(
        out_dir / "low_disagreement_near_target.csv",
        index=False,
    )
    scored[scored["ensemble_near_target_high_disagreement"]].sort_values(["ensemble_std_tg_c", "ensemble_target_distance_c"], ascending=[False, True]).to_csv(
        out_dir / "high_disagreement_near_target.csv",
        index=False,
    )
    summary = {
        "candidate_rows": int(len(scored)),
        "ensemble_models": int(len(predictors)),
        "target_tg_c": float(args.target_tg_c),
        "target_window_c": float(args.target_window_c),
        "mean_ensemble_std_c": float(scored["ensemble_std_tg_c"].mean()),
        "median_ensemble_std_c": float(scored["ensemble_std_tg_c"].median()),
        "max_ensemble_std_c": float(scored["ensemble_std_tg_c"].max()),
        "near_target_rows": int(scored["ensemble_near_target"].sum()),
        "near_target_low_disagreement_rows": int(scored["ensemble_near_target_low_disagreement"].sum()),
        "near_target_high_disagreement_rows": int(scored["ensemble_near_target_high_disagreement"].sum()),
        "mean_abs_best_model_delta_c": float(scored["best_model_delta_c"].abs().mean()) if base_col else None,
        "consensus_std_c": float(args.consensus_std_c),
        "high_disagreement_std_c": float(args.high_disagreement_std_c),
    }
    (out_dir / "ensemble_disagreement_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(scored, predictors, summary, out_dir, Path(args.report), args.target_tg_c, args.target_window_c)
    return scored, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Score candidates with top model-zoo predictors and compute ensemble disagreement.")
    parser.add_argument("--config", default="configs/reproduce.yaml")
    parser.add_argument("--metrics", default="artifacts/reproduce/predictors/all_predictor_metrics.csv")
    parser.add_argument("--best-model", default="artifacts/reproduce/predictors/best_model.json")
    parser.add_argument("--candidates", default="artifacts/reproduce/discovery/candidate_space_top_scored.csv")
    parser.add_argument("--out-dir", default="artifacts/trail/predictors/ensemble_disagreement")
    parser.add_argument("--report", default="reports/predictor_ensemble_disagreement.md")
    parser.add_argument("--latent-size", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--selection-metric", default="MAPEK test dataset (%)")
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--consensus-std-c", type=float, default=10.0)
    parser.add_argument("--high-disagreement-std-c", type=float, default=25.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--encode-batch-size", type=int, default=512)
    args = parser.parse_args()
    run_audit(args)


if __name__ == "__main__":
    main()
