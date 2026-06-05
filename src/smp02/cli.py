from __future__ import annotations

import argparse
import copy
from pathlib import Path

import pandas as pd

from smp02.closed_loop import run_closed_loop
from smp02.agent_discovery import run_agent_discovery
from smp02.data import augment_smiles, filter_smiles_by_charset, iter_chembl_smiles, load_smp_records, records_to_frame, unique_monomers
from smp02.discovery import discover_candidates
from smp02.functional_groups import classify_many
from smp02.predictors import select_best_model, train_predictor_suite
from smp02.training import fine_tune_vae_decoder, train_vae_model
from smp02.utils import ensure_dir, load_config, load_json, resolve_device, save_json, set_seed
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
    chembl = list(
        iter_chembl_smiles(
            cfg["chembl_path"],
            limit=int(vae_cfg["chembl_limit"]),
            max_length=int(smiles_cfg["max_length"]),
            validate=False,
        )
    )
    augmented = augment_smiles(
        monomers,
        per_monomer=int(smiles_cfg["augment_per_monomer"]),
        limit=int(smiles_cfg["augmented_limit"]),
    )
    charset = build_charset(chembl + augmented + monomers, min_size=int(smiles_cfg["min_charset_size"]))
    chembl = filter_smiles_by_charset(chembl, charset, int(smiles_cfg["max_length"]))
    augmented = filter_smiles_by_charset(augmented, charset, int(smiles_cfg["max_length"]))
    print(
        f"Prepared SMILES: chembl={len(chembl)}, augmented_smp={len(augmented)}, "
        f"charset={len(charset)}, max_length={smiles_cfg['max_length']}",
        flush=True,
    )
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
        metrics_df = pd.concat(all_metrics, ignore_index=True)
        metrics_df.to_csv(paths["predictors"] / "all_predictor_metrics.csv", index=False)
        best = select_best_model(metrics_df, paths["predictors"] / "best_model.json", cfg)
        if best:
            print(f"Best predictor: {best['ML method']} by {best['selection_metric']}={best[best['selection_metric']]}", flush=True)


def discover(cfg: dict) -> None:
    paths = _paths(cfg)
    device = resolve_device(cfg.get("device", "cuda"))
    records = load_smp_records(cfg["data_path"])
    run_cfg = copy.deepcopy(cfg)
    predictor_setting = str(cfg["discovery"].get("predictor", "svr"))
    latent_size = int(cfg["discovery"]["latent_size"])
    if predictor_setting == "best":
        best_path = paths["predictors"] / "best_model.json"
        if not best_path.exists():
            raise FileNotFoundError(f"Missing global best model file: {best_path}")
        best = load_json(best_path)
        latent_size = int(best["latent_size"])
        predictor = Path(best["model_path"])
        run_cfg["discovery"]["latent_size"] = latent_size
    else:
        predictor = paths["predictors"] / f"latent_{latent_size}" / f"svr_latent_{latent_size}.joblib"
    checkpoint = paths["vae"] / f"finetuned_latent_{latent_size}.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing VAE checkpoint: {checkpoint}")
    if not predictor.exists():
        raise FileNotFoundError(f"Missing predictor: {predictor}")
    discover_candidates(records, checkpoint, predictor, paths["discovery"], run_cfg, device)


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


def agent_discover(cfg: dict) -> None:
    device = resolve_device(cfg.get("device", "cuda"))
    selected = run_agent_discovery(cfg, device)
    if not selected.empty:
        best = selected.iloc[0]
        print(
            f"Best agent recommendation: Tg={float(best['predicted_tg_mean_c']):.2f} C, "
            f"distance={float(best['target_distance_c']):.2f} C, "
            f"score={float(best['agent_score']):.2f}, n={int(best['n_components'])}, sources={best['sources']}",
            flush=True,
        )


def run_all(cfg: dict, force: bool = False) -> None:
    inspect_data(cfg)
    train_vae(cfg, force=force)
    train_predictors(cfg)
    discover(cfg)
    closed_loop(cfg)


def main() -> None:
    parser = argparse.ArgumentParser(description="SMP02 paper reproduction workflow")
    parser.add_argument("command", choices=["inspect-data", "train-vae", "train-predictors", "discover", "closed-loop", "agent-discover", "run-all"])
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
    elif args.command == "agent-discover":
        agent_discover(cfg)
    elif args.command == "run-all":
        run_all(cfg, force=args.force)


if __name__ == "__main__":
    main()
