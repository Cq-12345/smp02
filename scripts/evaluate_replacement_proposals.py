from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

from smp02.agent_discovery import (
    AgentConfig,
    MonomerCandidate,
    build_formula,
    classify_mol,
    compute_prior_score,
    evaluate_formulas,
    functionality_estimate,
    initial_principles,
    monomer_features,
    ood_reference_scale,
)
from smp02.data import load_smp_records, unique_monomers
from smp02.predictors import load_predictor
from smp02.utils import load_config, load_json, resolve_device, save_json
from smp02.vae import encode_smiles, load_vae_checkpoint

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trail.experiments.import_observations import import_observations
from trail.harness.constraints import validate_candidates


def canonical(value: object) -> str | None:
    mol = Chem.MolFromSmiles(str(value))
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, canonical=True)


def monomer_candidate(smiles: str, source: str, label: str, known_monomers: set[str], principles) -> MonomerCandidate:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    smiles = Chem.MolToSmiles(mol, canonical=True)
    groups, counts = classify_mol(mol)
    features = monomer_features(mol, groups, counts)
    return MonomerCandidate(
        smiles=smiles,
        source=source,
        label=label,
        groups=groups,
        monomer_prior_score=compute_prior_score(features, principles),
        molecular_weight=float(Descriptors.MolWt(mol)),
        heavy_atoms=int(mol.GetNumHeavyAtoms()),
        aromatic_rings=int(rdMolDescriptors.CalcNumAromaticRings(mol)),
        rotatable_bonds=int(rdMolDescriptors.CalcNumRotatableBonds(mol)),
        functionality=int(functionality_estimate(counts)),
        in_library=smiles in known_monomers,
        features=features,
    )


def make_agent_cfg(
    base_cfg: dict,
    best_model: dict,
    predictor_path: Path,
    checkpoint_path: Path,
    features_path: Path,
    target_tg_c: float,
    target_window_c: float,
) -> AgentConfig:
    discovery_cfg = base_cfg.get("discovery", {})
    return AgentConfig(
        target_tg_c=float(target_tg_c),
        target_window_c=float(target_window_c),
        output_dir=Path("artifacts/trail/generation/replacement_eval"),
        latent_size=int(best_model["latent_size"]),
        vae_checkpoint=checkpoint_path,
        predictor_path=predictor_path,
        training_features_path=features_path,
        max_components=2,
        min_components=2,
        min_ratio=float(discovery_cfg.get("ratio_start", 0.05)),
        require_out_of_library=False,
        generated_pool_limit=0,
        chembl_limit=0,
        chembl_pool_limit=0,
        library_pool_limit=0,
        pair_pool_limit=0,
        iterations=1,
        samples_per_iteration=0,
        elite_k=20,
        selected_top_k=20,
        prediction_batch_size=2048,
        encode_batch_size=512,
        prior_learning_rate=0.1,
        uncertainty_weight=0.06,
        ood_weight=0.35,
        prior_weight=1.6,
        novelty_weight=0.15,
        component_count_weight=0.05,
    )


def source_lookup(selected: pd.DataFrame) -> dict[tuple[str, str, str], pd.Series]:
    lookup: dict[tuple[str, str, str], pd.Series] = {}
    for _, row in selected.iterrows():
        tg_key = f"{float(row['predicted_tg']):.6f}"
        for side in ["a", "b"]:
            key = (tg_key, side, str(row[f"smiles_{side}"]))
            lookup.setdefault(key, row)
    return lookup


def build_replacement_formulas(
    proposals: pd.DataFrame,
    selected: pd.DataFrame,
    known_monomers: set[str],
    principles,
    charset: list[str],
    max_length: int,
    target_tg_c: float,
) -> tuple[list, list[dict[str, object]], pd.DataFrame]:
    lookup = source_lookup(selected)
    allowed_chars = set(charset)
    formulas = []
    metadata = []
    rejections = []
    seen = set()
    for proposal_index, proposal in proposals.iterrows():
        side = str(proposal["replace_side"])
        source_tg = float(proposal["source_candidate_tg"])
        tg_key = f"{source_tg:.6f}"
        original = str(proposal["original_smiles"])
        source = lookup.get((tg_key, side, original))
        if source is None:
            rejections.append({"proposal_index": int(proposal_index), "reason": "source_candidate_not_found", **proposal.to_dict()})
            continue
        replacement = canonical(proposal["replacement_smiles"])
        if replacement is None:
            rejections.append({"proposal_index": int(proposal_index), "reason": "invalid_replacement_smiles", **proposal.to_dict()})
            continue
        if len(replacement) > max_length or any(ch not in allowed_chars for ch in replacement):
            rejections.append({"proposal_index": int(proposal_index), "reason": "replacement_not_encodable_by_vae_charset", **proposal.to_dict()})
            continue
        other_side = "b" if side == "a" else "a"
        other = canonical(source[f"smiles_{other_side}"])
        if other is None:
            rejections.append({"proposal_index": int(proposal_index), "reason": "invalid_other_side_smiles", **proposal.to_dict()})
            continue
        smiles_a = replacement if side == "a" else other
        smiles_b = other if side == "a" else replacement
        ratios = (float(source["ratio_a"]), float(source["ratio_b"]))
        try:
            monomers = [
                monomer_candidate(smiles_a, "replacement_pool" if side == "a" else "source_candidate", "replacement_a" if side == "a" else "source_a", known_monomers, principles),
                monomer_candidate(smiles_b, "replacement_pool" if side == "b" else "source_candidate", "replacement_b" if side == "b" else "source_b", known_monomers, principles),
            ]
        except ValueError as exc:
            rejections.append({"proposal_index": int(proposal_index), "reason": str(exc), **proposal.to_dict()})
            continue
        formula = build_formula(monomers, ratios, principles, min_ratio=0.05)
        if formula is None:
            rejections.append({"proposal_index": int(proposal_index), "reason": "replacement_formula_failed_reaction_or_ratio_constraints", **proposal.to_dict()})
            continue
        key = ("|".join(formula.smiles), ":".join(f"{ratio:.5f}" for ratio in formula.ratios))
        if key in seen:
            rejections.append({"proposal_index": int(proposal_index), "reason": "duplicate_replacement_formula", **proposal.to_dict()})
            continue
        seen.add(key)
        formulas.append(formula)
        metadata.append(
            {
                "proposal_index": int(proposal_index),
                "source_candidate_tg_c": source_tg,
                "source_target_distance_c": abs(source_tg - float(target_tg_c)),
                "replace_side": side,
                "original_smiles": original,
                "replacement_smiles": replacement,
                "replacement_tanimoto": float(proposal["tanimoto"]),
                "shared_groups": proposal["shared_groups"],
                "counterpart_groups": proposal.get("counterpart_groups", ""),
                "counterpart_compatibility_reason": proposal.get("counterpart_compatibility_reason", ""),
                "feedback_constraint": proposal.get("feedback_constraint", ""),
                "source_smiles_a": source["smiles_a"],
                "source_smiles_b": source["smiles_b"],
                "source_ratio_a": float(source["ratio_a"]),
                "source_ratio_b": float(source["ratio_b"]),
                "source_compatibility_reason": source["compatibility_reason"],
            }
        )
    rejection_df = pd.DataFrame(rejections)
    if rejection_df.empty:
        rejection_df = pd.DataFrame(
            columns=[
                "proposal_index",
                "reason",
                *[column for column in proposals.columns if column not in {"proposal_index", "reason"}],
            ]
        )
    return formulas, metadata, rejection_df


def write_report(scored: pd.DataFrame, rejections: pd.DataFrame, summary: dict[str, object], report_path: Path, target_tg_c: float) -> None:
    lines = [
        "# VAE Replacement Proposals: Prediction And Harness Evaluation",
        "",
        "本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            f"目标 Tg: {target_tg_c:.1f} C",
            "",
            "## Top Harness-Passing Replacements",
            "",
            "| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | tanimoto | chemistry |",
            "| ---: | ---: | ---: | ---: | --- | ---: | --- |",
        ]
    )
    passed = scored[scored["harness_pass"]].sort_values(["target_distance_c", "ood_penalty", "predicted_tg_sigma_c"]).head(20)
    for rank, (_, row) in enumerate(passed.iterrows(), start=1):
        lines.append(
            f"| {rank} | {float(row['predicted_tg_mean_c']):.2f} | {float(row['target_distance_c']):.2f} | "
            f"{float(row['predicted_tg_sigma_c']):.2f} | {row['replace_side']} | {float(row['replacement_tanimoto']):.3f} | "
            f"{str(row['compatibility_reasons']).replace('|', '; ')} |"
        )
    lines.extend(
        [
            "",
            "## Rejection Reasons",
            "",
        ]
    )
    if rejections.empty:
        lines.append("- No rejected proposals.")
    else:
        counts = rejections["reason"].value_counts()
        for reason, count in counts.items():
            lines.append(f"- {reason}: {int(count)}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。",
            "- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。",
            "- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_replacement_observation_ledger(scored: pd.DataFrame, out_dir: Path, target_tg_c: float, reward_temperature_c: float) -> tuple[Path, Path, Path]:
    passed = scored[scored["harness_pass"]].copy() if "harness_pass" in scored else pd.DataFrame()
    observation_input = out_dir / "replacement_observations_input.csv"
    ledger_path = out_dir / "replacement_observation_ledger.csv"
    summary_path = out_dir / "replacement_observation_ledger_summary.json"
    columns = [
        "observation_id",
        "source_type",
        "target_tg_c",
        "observed_tg_c",
        "smiles",
        "ratios",
        "predicted_tg_mean_c",
        "predicted_tg_sigma_c",
        "experiment_date",
        "operator",
        "method",
        "notes",
    ]
    rows = []
    for _, row in passed.sort_values(["target_distance_c", "ood_penalty", "predicted_tg_sigma_c"]).iterrows():
        rows.append(
            {
                "observation_id": f"replacement_surrogate_{int(row['formula_id']):04d}",
                "source_type": "surrogate",
                "target_tg_c": float(target_tg_c),
                "observed_tg_c": float(row["predicted_tg_mean_c"]),
                "smiles": row["smiles"],
                "ratios": row["ratios"],
                "predicted_tg_mean_c": float(row["predicted_tg_mean_c"]),
                "predicted_tg_sigma_c": float(row["predicted_tg_sigma_c"]),
                "experiment_date": "2026-06-06",
                "operator": "smp02_replacement_eval",
                "method": "vae_wvcm_gpr_surrogate",
                "notes": f"VAE replacement proposal {int(row['proposal_index'])}; replace_side={row['replace_side']}; tanimoto={float(row['replacement_tanimoto']):.3f}",
            }
        )
    pd.DataFrame(rows, columns=columns).to_csv(observation_input, index=False)
    ledger, ledger_summary = import_observations(observation_input, Path("trail/experiments/observation_schema.yaml"), reward_temperature_c)
    ledger.to_csv(ledger_path, index=False)
    save_json(ledger_summary, summary_path)
    return observation_input, ledger_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict and harness-check VAE replacement proposals as complete formulations.")
    parser.add_argument("--config", default="configs/reproduce.yaml")
    parser.add_argument("--proposals", default="artifacts/trail/generation/replacement_proposals.csv")
    parser.add_argument("--selected", default="artifacts/reproduce/discovery/selected_candidates.csv")
    parser.add_argument("--best-model", default="artifacts/reproduce/predictors/best_model.json")
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--device", default="cpu", help="Device for deterministic VAE encoding; use cuda only when speed is required.")
    parser.add_argument("--out-dir", default="artifacts/trail/generation/replacement_eval")
    parser.add_argument("--report", default="reports/replacement_proposal_evaluation.md")
    args = parser.parse_args()

    cfg = load_config(args.config)
    seed = int(cfg.get("seed", 42))
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    best_model = load_json(args.best_model)
    latent_size = int(best_model["latent_size"])
    predictor_path = Path(best_model["model_path"])
    checkpoint_path = Path(cfg["output_dir"]) / "vae" / f"finetuned_latent_{latent_size}.pt"
    features_path = Path(cfg["output_dir"]) / "predictors" / f"latent_{latent_size}" / f"wvcm_features_latent_{latent_size}.npz"
    device = resolve_device(args.device)
    vae, checkpoint = load_vae_checkpoint(checkpoint_path, map_location=device)
    vae.to(device)
    proposals = pd.read_csv(args.proposals)
    selected = pd.read_csv(args.selected)
    known_monomers = set(unique_monomers(load_smp_records(cfg["data_path"])))
    principles = initial_principles()
    formulas, metadata, rejections = build_replacement_formulas(
        proposals,
        selected,
        known_monomers,
        principles,
        checkpoint["charset"],
        int(checkpoint["max_length"]),
        args.target_tg_c,
    )
    unique_smiles = sorted({smiles for formula in formulas for smiles in formula.smiles})
    latent = encode_smiles(vae, unique_smiles, checkpoint["charset"], int(checkpoint["max_length"]), device, batch_size=512)
    vectors = {smiles: latent[idx] for idx, smiles in enumerate(unique_smiles)}
    predictor = load_predictor(predictor_path)
    train_features = np.asarray(np.load(features_path)["x"], dtype=np.float32)
    agent_cfg = make_agent_cfg(
        cfg,
        best_model,
        predictor_path,
        checkpoint_path,
        features_path,
        args.target_tg_c,
        args.target_window_c,
    )
    scored = evaluate_formulas(formulas, vectors, predictor, train_features, ood_reference_scale(train_features), agent_cfg)
    if not scored.empty:
        scored = pd.concat([pd.DataFrame(metadata), scored], axis=1)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scored_path = out_dir / "replacement_proposals_scored.csv"
    scored_raw_path = out_dir / "replacement_proposals_scored_raw.csv"
    harness_path = out_dir / "replacement_proposals_harness.csv"
    rejection_path = out_dir / "replacement_proposal_rejections.csv"
    scored.to_csv(scored_raw_path, index=False)
    rejections.to_csv(rejection_path, index=False)
    harness = validate_candidates(scored_raw_path, args.target_tg_c - args.target_window_c, args.target_tg_c + args.target_window_c)
    harness.to_csv(harness_path, index=False)
    if not scored.empty:
        scored = scored.merge(harness[["formula_id", "harness_pass", "target_ok", "chemistry_ok"]], on="formula_id", how="left")
    scored.to_csv(scored_path, index=False)
    observation_input_path, observation_ledger_path, observation_ledger_summary_path = write_replacement_observation_ledger(
        scored,
        out_dir,
        args.target_tg_c,
        args.target_window_c,
    )
    summary = {
        "input_proposals": int(len(proposals)),
        "rebuilt_formulas": int(len(formulas)),
        "scored_formulas": int(len(scored)),
        "harness_pass": int(scored["harness_pass"].sum()) if "harness_pass" in scored else 0,
        "rejected_proposals": int(len(rejections)),
        "best_distance_c": None if scored.empty else round(float(scored["target_distance_c"].min()), 6),
        "within_1c": 0 if scored.empty else int((scored["target_distance_c"] <= 1.0).sum()),
        "within_5c": 0 if scored.empty else int((scored["target_distance_c"] <= args.target_window_c).sum()),
        "predictor": best_model["ML method"],
        "latent_size": latent_size,
        "replacement_observations": 0 if scored.empty else int(scored["harness_pass"].sum()),
    }
    save_json(
        summary
        | {
            "best_model": best_model,
            "scored_path": str(scored_path),
            "harness_path": str(harness_path),
            "rejection_path": str(rejection_path),
            "replacement_observations_input_path": str(observation_input_path),
            "replacement_observation_ledger_path": str(observation_ledger_path),
            "replacement_observation_ledger_summary_path": str(observation_ledger_summary_path),
        },
        out_dir / "replacement_eval_summary.json",
    )
    write_report(scored, rejections, summary, Path(args.report), args.target_tg_c)


if __name__ == "__main__":
    main()
