from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch

from smp02.data import SMPRecord, unique_monomers
from smp02.functional_groups import classify_smiles, compatibility_reason
from smp02.predictors import load_predictor, predict_sklearn_bundle
from smp02.utils import ensure_dir, save_json
from smp02.vae import encode_smiles, load_vae_checkpoint


def ratio_grid(start: float, stop: float, step: float) -> list[float]:
    values = []
    value = start
    while value <= stop + 1e-9:
        values.append(round(value, 10))
        value += step
    return values


def compatible_pairs(monomers: list[str]) -> list[dict[str, object]]:
    groups = {smi: classify_smiles(smi).groups for smi in monomers}
    rows: list[dict[str, object]] = []
    for i, smi_a in enumerate(monomers):
        start_j = i
        for smi_b in monomers[start_j:]:
            if smi_a == smi_b and compatibility_reason(groups[smi_a], groups[smi_b]) is None:
                continue
            reason = compatibility_reason(groups[smi_a], groups[smi_b])
            if reason is None:
                continue
            rows.append(
                {
                    "smiles_a": smi_a,
                    "smiles_b": smi_b,
                    "groups_a": ";".join(groups[smi_a]),
                    "groups_b": ";".join(groups[smi_b]),
                    "compatibility_reason": reason,
                }
            )
    return rows


def discover_candidates(
    records: list[SMPRecord],
    vae_checkpoint: str | Path,
    predictor_path: str | Path,
    out_dir: str | Path,
    cfg: dict,
    device: torch.device,
) -> pd.DataFrame:
    out = ensure_dir(out_dir)
    disc_cfg = cfg["discovery"]
    latent_size = int(disc_cfg["latent_size"])
    vae, checkpoint = load_vae_checkpoint(vae_checkpoint, map_location=device)
    vae.to(device)
    if int(checkpoint["latent_size"]) != latent_size:
        raise ValueError(f"VAE checkpoint latent size {checkpoint['latent_size']} != discovery latent size {latent_size}")
    monomers = unique_monomers(records)
    latent = encode_smiles(vae, monomers, checkpoint["charset"], int(checkpoint["max_length"]), device, batch_size=cfg["vae"]["batch_size"])
    vectors = {smi: latent[i] for i, smi in enumerate(monomers)}
    group_rows = []
    for smi in monomers:
        cls = classify_smiles(smi)
        group_rows.append({"smiles": smi, "groups": ";".join(cls.groups), "invalid": cls.invalid})
    pd.DataFrame(group_rows).to_csv(out / "monomer_functional_groups.csv", index=False)

    pairs = compatible_pairs(monomers)
    pd.DataFrame(pairs).to_csv(out / "compatible_monomer_pairs.csv", index=False)
    predictor = load_predictor(predictor_path)
    ratios = ratio_grid(float(disc_cfg["ratio_start"]), float(disc_cfg["ratio_stop"]), float(disc_cfg["ratio_step"]))
    rows: list[dict[str, object]] = []
    x_rows = []
    meta_rows = []
    for pair in pairs:
        va = vectors[str(pair["smiles_a"])]
        vb = vectors[str(pair["smiles_b"])]
        for ratio_a in ratios:
            ratio_b = 1.0 - ratio_a
            x_rows.append(ratio_a * va + ratio_b * vb)
            meta_rows.append({**pair, "ratio_a": ratio_a, "ratio_b": ratio_b})
            if len(x_rows) >= 8192:
                x = np.vstack(x_rows).astype(np.float32)
                pred = predict_sklearn_bundle(predictor, x)
                for meta, tg in zip(meta_rows, pred, strict=False):
                    rows.append({**meta, "predicted_tg": float(tg)})
                x_rows.clear()
                meta_rows.clear()
    if x_rows:
        x = np.vstack(x_rows).astype(np.float32)
        pred = predict_sklearn_bundle(predictor, x)
        for meta, tg in zip(meta_rows, pred, strict=False):
            rows.append({**meta, "predicted_tg": float(tg)})

    all_df = pd.DataFrame(rows)
    if all_df.empty:
        all_df.to_csv(out / "all_ratio_candidates.csv", index=False)
        all_df.to_csv(out / "candidate_space_top_scored.csv", index=False)
        all_df.to_csv(out / "selected_candidates.csv", index=False)
        return all_df
    center = (float(disc_cfg["target_tg_min"]) + float(disc_cfg["target_tg_max"])) / 2.0
    all_df["target_distance"] = (all_df["predicted_tg"] - center).abs()
    all_df["in_target_range"] = (
        (all_df["predicted_tg"] >= float(disc_cfg["target_tg_min"]))
        & (all_df["predicted_tg"] <= float(disc_cfg["target_tg_max"]))
    )
    all_df.to_csv(out / "all_ratio_candidates.csv", index=False)
    top_space = all_df.sort_values("target_distance").head(max(int(disc_cfg["max_candidates"]) * 20, 1000))
    top_space.to_csv(out / "candidate_space_top_scored.csv", index=False)
    selected = all_df[all_df["in_target_range"]].sort_values("target_distance").head(int(disc_cfg["max_candidates"]))
    selected.to_csv(out / "selected_candidates.csv", index=False)
    save_json(
        {
            "n_monomers": len(monomers),
            "n_compatible_pairs": len(pairs),
            "n_ratio_candidates": int(len(all_df)),
            "n_selected": int(len(selected)),
            "target_range": [float(disc_cfg["target_tg_min"]), float(disc_cfg["target_tg_max"])],
        },
        out / "discovery_summary.json",
    )
    return selected
