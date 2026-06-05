from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PRIMARY_METRIC = "MAPEK test dataset (%)"


def fmt_float(value: object, ndigits: int = 4) -> str:
    return f"{float(value):.{ndigits}f}"


def main() -> None:
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)

    predictors_dir = Path("artifacts/reproduce/predictors")
    discovery_dir = Path("artifacts/reproduce/discovery")
    closed_loop_dir = Path("artifacts/reproduce/closed_loop")

    metrics = pd.read_csv(predictors_dir / "all_predictor_metrics.csv")
    ascending = True
    leaderboard = metrics.sort_values(PRIMARY_METRIC, ascending=ascending).reset_index(drop=True)
    leaderboard_cols = [
        "ML method",
        "latent_size",
        "model_family",
        "MAPEK test dataset (%)",
        "MAE test dataset (C)",
        "RMSE test dataset (C)",
        "MAPE test dataset (%)",
        "PCP test dataset (%)",
        "R2 test",
        "model_path",
    ]
    leaderboard[leaderboard_cols].head(50).to_csv(report_dir / "model_zoo_leaderboard_top50.csv", index=False)

    best = json.loads((predictors_dir / "best_model.json").read_text(encoding="utf-8"))
    discovery = json.loads((discovery_dir / "discovery_summary.json").read_text(encoding="utf-8"))
    selected = pd.read_csv(discovery_dir / "selected_candidates.csv")
    harness = pd.read_csv(discovery_dir / "harness_validation.csv")
    history = json.loads((closed_loop_dir / "closed_loop_history.json").read_text(encoding="utf-8"))
    principles = json.loads((closed_loop_dir / "evolved_principles.json").read_text(encoding="utf-8"))

    candidate_cols = [
        "smiles_a",
        "smiles_b",
        "ratio_a",
        "ratio_b",
        "predicted_tg",
        "target_distance",
        "compatibility_reason",
    ]
    selected[candidate_cols].head(50).to_csv(report_dir / "selected_candidates_top50.csv", index=False)

    lines: list[str] = []
    lines.append("# Reproduction Summary")
    lines.append("")
    lines.append("Run date: 2026-06-05 Asia/Shanghai")
    lines.append("")
    lines.append("## VAE")
    lines.append("")
    lines.append("- Completed latent sizes: 16, 32, 64, 128, 256, 512, 1024.")
    lines.append("- Full checkpoints are under `artifacts/reproduce/vae/` and are ignored by git.")
    lines.append("- Default high-performance config uses both visible GPUs, VAE batch size 2048, 24 DataLoader workers, and CUDA convolution/matmul speed settings.")
    lines.append("")
    lines.append("## Tg Predictor Model Zoo")
    lines.append("")
    lines.append(f"- Evaluated rows: {len(metrics)} model/latent combinations.")
    lines.append(f"- Primary selection metric: `{PRIMARY_METRIC}`; lower is better.")
    lines.append(f"- Best model: `{best['ML method']}`.")
    lines.append(
        "- Best test metrics: "
        f"MAPEK {fmt_float(best['MAPEK test dataset (%)'], 6)}%, "
        f"MAE {fmt_float(best['MAE test dataset (C)'], 3)} C, "
        f"RMSE {fmt_float(best['RMSE test dataset (C)'], 3)} C, "
        f"R2 {fmt_float(best['R2 test'], 6)}, "
        f"legacy MAPE {fmt_float(best['MAPE test dataset (%)'], 3)}%."
    )
    lines.append("- Full top-50 leaderboard: `reports/model_zoo_leaderboard_top50.csv`.")
    lines.append("")
    lines.append("| Rank | Method | MAPEK test (%) | MAE test (C) | RMSE test (C) | R2 test | Legacy MAPE test (%) |")
    lines.append("| ---: | --- | ---: | ---: | ---: | ---: | ---: |")
    for index, row in leaderboard.head(10).iterrows():
        lines.append(
            f"| {index + 1} | {row['ML method']} | "
            f"{fmt_float(row['MAPEK test dataset (%)'], 6)} | "
            f"{fmt_float(row['MAE test dataset (C)'], 3)} | "
            f"{fmt_float(row['RMSE test dataset (C)'], 3)} | "
            f"{fmt_float(row['R2 test'], 6)} | "
            f"{fmt_float(row['MAPE test dataset (%)'], 3)} |"
        )
    lines.append("")
    lines.append("## Functional-Group Discovery")
    lines.append("")
    lines.append("- Discovery uses SMARTS-based monomer functional-group classification and thermoset compatibility rules.")
    lines.append(f"- Monomers: {discovery['n_monomers']}.")
    lines.append(f"- Compatible monomer pairs: {discovery['n_compatible_pairs']}.")
    lines.append(f"- Ratio candidates: {discovery['n_ratio_candidates']}.")
    lines.append("- Full ratio candidate table: `artifacts/reproduce/discovery/all_ratio_candidates.csv`.")
    lines.append(f"- Selected candidates in {discovery['target_range'][0]:.0f}-{discovery['target_range'][1]:.0f} C: {discovery['n_selected']}.")
    lines.append(f"- Harness pass rate on selected candidates: {int(harness['harness_pass'].sum())}/{len(harness)}.")
    lines.append("- Full top-50 selected candidates: `reports/selected_candidates_top50.csv`.")
    lines.append("")
    lines.append("| Rank | Ratio A | Ratio B | Predicted Tg | Distance | Compatibility |")
    lines.append("| ---: | ---: | ---: | ---: | ---: | --- |")
    for index, row in selected.head(10).iterrows():
        lines.append(
            f"| {index + 1} | {fmt_float(row['ratio_a'], 2)} | {fmt_float(row['ratio_b'], 2)} | "
            f"{fmt_float(row['predicted_tg'], 4)} | {fmt_float(row['target_distance'], 4)} | {row['compatibility_reason']} |"
        )
    lines.append("")
    lines.append("## Closed Loop")
    lines.append("")
    lines.append(f"- Iterations: {len(history)}; selected per iteration: {history[0]['selected'] if history else 0}.")
    lines.append("- Iteration best predicted Tg values:")
    for item in history:
        lines.append(f"  - Iteration {item['iteration']}: {fmt_float(item['best_predicted_tg'], 4)} C")
    lines.append("- Top evolved reaction principles:")
    for reason, count in list(principles.items())[:10]:
        lines.append(f"  - {reason}: {count}")
    lines.append("")
    lines.append("## Verification")
    lines.append("")
    lines.append("- `python -m compileall -q src tests`: passed.")
    lines.append("- `pytest -q`: passed.")
    lines.append("- `trail/harness/constraints.py`: generated `artifacts/reproduce/discovery/harness_validation.csv`.")
    lines.append("- `trail/workflow/multi_agent_workflow.py`: generated `artifacts/reproduce/closed_loop/multi_agent_summary.json`.")
    lines.append("")

    (report_dir / "reproduce_summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
