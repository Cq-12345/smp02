from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from smp02.closed_loop import run_closed_loop
from smp02.data import augment_smiles, filter_smiles_by_charset, iter_chembl_smiles, load_smp_records, records_to_frame, unique_monomers
from smp02.discovery import discover_candidates
from smp02.functional_groups import classify_many
from smp02.predictors import train_predictor_suite
from smp02.training import fine_tune_vae_decoder, train_vae_model
from smp02.utils import ensure_dir, load_config, resolve_device, save_json, set_seed
from smp02.vae import build_charset


def _paths(cfg: dict) -> dict[str, Path]:
    root = ensure_dir(cfg["output_dir"])
    return {
        "root": root,
        "vae": ensure_dir(root / "vae"),
        "predictors": ensure_dir(root / "predictors"),
        "discovery": ensure_dir(root / "discovery"),
        "closed_loop": ensure_dir(root / "closed_loop"),
    }


def inspect_data(cfg: dict) -> None:
    paths = _paths(cfg)
    records = load_smp_records(cfg["data_path"])
    monomers = unique_monomers(records)
    records_to_frame(records).to_csv(paths["root"] / "parsed_smp_dataset.csv", index=False)
    pd.DataFrame(classify_many(monomers)).to_csv(paths["root"] / "unique_monomer_functional_groups.csv", index=False)
    save_json(
        {
            "records": len(records),
            "unique_monomers": len(monomers),
            "min_tg": min(r.tg for r in records),
            "max_tg": max(r.tg for r in records),
            "mean_tg": sum(r.tg for r in records) / len(records),
        },
        paths["root"] / "data_summary.json",
    )


def prepare_smiles(cfg: dict) -> tuple[list[str], list[str], list[str]]:
    records = load_smp_records(cfg["data_path"])
    monomers = unique_monomers(records)
    smiles_cfg = cfg["smiles"]
    vae_cfg = cfg["vae"]
    chembl = list(iter_chembl_smiles(cfg["chembl_path"], limit=int(vae_cfg["chembl_limit"]), max_length=int(smiles_cfg["max_length"])))
    augmented = augment_smiles(
        monomers,
        per_monomer=int(smiles_cfg["augment_per_monomer"]),
        limit=int(smiles_cfg["augmented_limit"]),
    )
    charset = build_charset(chembl + augmented + monomers, min_size=int(smiles_cfg["min_charset_size"]))
    chembl = filter_smiles_by_charset(chembl, charset, int(smiles_cfg["max_length"]))
    augmented = filter_smiles_by_charset(augmented, charset, int(smiles_cfg["max_length"]))
    return chembl, augmented, charset


def train_vae(cfg: dict, force: bool = False) -> None:
    paths = _paths(cfg)
    device = resolve_device(cfg.get("device", "cuda"))
    chembl, augmented, charset = prepare_smiles(cfg)
    save_json({"charset": charset, "size": len(charset)}, paths["vae"] / "charset.json")
    vae_cfg = cfg["vae"]
    for latent_size in vae_cfg["latent_sizes"]:
        pre_path = paths["vae"] / f"pretrained_latent_{latent_size}.pt"
        fine_path = paths["vae"] / f"finetuned_latent_{latent_size}.pt"
        if force or not pre_path.exists():
            train_vae_model(
                chembl,
                charset,
                int(cfg["smiles"]["max_length"]),
                int(latent_size),
                pre_path,
                epochs=int(vae_cfg["pretrain_epochs"]),
                batch_size=int(vae_cfg["batch_size"]),
                learning_rate=float(vae_cfg["learning_rate"]),
                device=device,
                num_workers=int(vae_cfg["num_workers"]),
                reconstruction_weight=float(vae_cfg["reconstruction_weight"]),
                kl_weight=float(vae_cfg["kl_weight"]),
                validity_weight=float(vae_cfg["validity_weight"]),
            )
        if force or not fine_path.exists():
            fine_tune_vae_decoder(
                pre_path,
                augmented,
                fine_path,
                epochs=int(vae_cfg["finetune_epochs"]),
                batch_size=int(vae_cfg["batch_size"]),
                learning_rate=float(vae_cfg["learning_rate"]),
                device=device,
                num_workers=int(vae_cfg["num_workers"]),
                reconstruction_weight=float(vae_cfg["reconstruction_weight"]),
                kl_weight=float(vae_cfg["kl_weight"]),
                validity_weight=float(vae_cfg["validity_weight"]),
            )


def train_predictors(cfg: dict) -> None:
    paths = _paths(cfg)
    device = resolve_device(cfg.get("device", "cuda"))
    records = load_smp_records(cfg["data_path"])
    all_metrics = []
    for latent_size in cfg["vae"]["latent_sizes"]:
        checkpoint = paths["vae"] / f"finetuned_latent_{latent_size}.pt"
        if not checkpoint.exists():
            raise FileNotFoundError(f"Missing VAE checkpoint: {checkpoint}")
        metrics = train_predictor_suite(records, checkpoint, paths["predictors"] / f"latent_{latent_size}", cfg, device)
        all_metrics.append(metrics)
    if all_metrics:
        pd.concat(all_metrics, ignore_index=True).to_csv(paths["predictors"] / "all_predictor_metrics.csv", index=False)


def discover(cfg: dict) -> None:
    paths = _paths(cfg)
    device = resolve_device(cfg.get("device", "cuda"))
    records = load_smp_records(cfg["data_path"])
    latent_size = int(cfg["discovery"]["latent_size"])
    checkpoint = paths["vae"] / f"finetuned_latent_{latent_size}.pt"
    predictor = paths["predictors"] / f"latent_{latent_size}" / f"svr_latent_{latent_size}.joblib"
    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing VAE checkpoint: {checkpoint}")
    if not predictor.exists():
        raise FileNotFoundError(f"Missing SVR predictor: {predictor}")
    discover_candidates(records, checkpoint, predictor, paths["discovery"], cfg, device)


def closed_loop(cfg: dict) -> None:
    paths = _paths(cfg)
    cl_cfg = cfg["closed_loop"]
    candidate_space = paths["discovery"] / "candidate_space_top_scored.csv"
    if not candidate_space.exists():
        raise FileNotFoundError(f"Missing candidate space: {candidate_space}")
    run_closed_loop(
        candidate_space,
        paths["closed_loop"],
        iterations=int(cl_cfg["iterations"]),
        top_k=int(cl_cfg["top_k"]),
        target_center=float(cl_cfg["target_center"]),
        uncertainty_weight=float(cl_cfg["uncertainty_weight"]),
    )


def run_all(cfg: dict, force: bool = False) -> None:
    inspect_data(cfg)
    train_vae(cfg, force=force)
    train_predictors(cfg)
    discover(cfg)
    closed_loop(cfg)


def main() -> None:
    parser = argparse.ArgumentParser(description="SMP02 paper reproduction workflow")
    parser.add_argument("command", choices=["inspect-data", "train-vae", "train-predictors", "discover", "closed-loop", "run-all"])
    parser.add_argument("--config", default="configs/reproduce.yaml")
    parser.add_argument("--force", action="store_true", help="overwrite existing VAE checkpoints")
    args = parser.parse_args()
    cfg = load_config(args.config)
    set_seed(int(cfg["seed"]))
    if args.command == "inspect-data":
        inspect_data(cfg)
    elif args.command == "train-vae":
        train_vae(cfg, force=args.force)
    elif args.command == "train-predictors":
        train_predictors(cfg)
    elif args.command == "discover":
        discover(cfg)
    elif args.command == "closed-loop":
        closed_loop(cfg)
    elif args.command == "run-all":
        run_all(cfg, force=args.force)


if __name__ == "__main__":
    main()

