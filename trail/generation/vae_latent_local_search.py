from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from rdkit import Chem

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from smp02.functional_groups import compatibility_reason
from smp02.utils import load_config, load_json, resolve_device
from smp02.vae import encode_smiles, load_vae_checkpoint
from trail.generation.vae_replacement_strategy import PROPOSAL_COLUMNS, load_replacement_pool, parse_group_set, tanimoto


LATENT_PROPOSAL_COLUMNS = [
    *PROPOSAL_COLUMNS,
    "latent_distance",
    "latent_cosine_similarity",
    "latent_rank",
    "latent_search_space_rows",
    "latent_compatible_rows",
    "matched_groups",
    "latent_size",
    "vae_checkpoint",
]


def canonical_smiles(value: object) -> str | None:
    mol = Chem.MolFromSmiles(str(value))
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, canonical=True)


def is_vae_encodable(smiles: str, charset: list[str], max_length: int) -> bool:
    allowed = set(charset)
    return len(smiles) <= max_length and all(ch in allowed for ch in smiles)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def prepare_replacement_pool(frame: pd.DataFrame, charset: list[str] | None = None, max_length: int | None = None) -> pd.DataFrame:
    pool = frame.copy()
    pool["canonical_smiles"] = pool["smiles"].map(canonical_smiles)
    pool = pool[pool["canonical_smiles"].notna()].copy()
    if charset is not None and max_length is not None:
        pool = pool[pool["canonical_smiles"].map(lambda smiles: is_vae_encodable(str(smiles), charset, int(max_length)))].copy()
    pool["group_set"] = pool["groups"].map(parse_group_set)
    pool = pool[pool["group_set"].map(bool)].copy()
    return pool.drop_duplicates(subset=["canonical_smiles", "source", "label"]).reset_index(drop=True)


def candidate_source_tg(row: pd.Series) -> float:
    if "predicted_tg" in row and pd.notna(row["predicted_tg"]):
        return float(row["predicted_tg"])
    if "predicted_tg_mean_c" in row and pd.notna(row["predicted_tg_mean_c"]):
        return float(row["predicted_tg_mean_c"])
    raise ValueError("Candidate rows must contain predicted_tg or predicted_tg_mean_c.")


def propose_latent_replacements_from_vectors(
    candidates: pd.DataFrame,
    pool: pd.DataFrame,
    vectors: dict[str, np.ndarray],
    top_k: int,
    per_side: int,
    latent_size: int,
    vae_checkpoint: str,
    require_counterpart_compatibility: bool = False,
    require_shared_groups: bool = True,
) -> pd.DataFrame:
    if candidates.empty or pool.empty:
        return pd.DataFrame(columns=LATENT_PROPOSAL_COLUMNS)

    rows: list[dict[str, Any]] = []
    for _, row in candidates.head(top_k).iterrows():
        source_tg = candidate_source_tg(row)
        for side in ["a", "b"]:
            raw_smiles = str(row[f"smiles_{side}"])
            base_smiles = canonical_smiles(raw_smiles)
            if base_smiles is None or base_smiles not in vectors:
                continue
            base_groups = parse_group_set(row[f"groups_{side}"])
            other_side = "b" if side == "a" else "a"
            counterpart_groups = parse_group_set(row[f"groups_{other_side}"])
            base_vector = vectors[base_smiles]
            scored: list[dict[str, Any]] = []
            search_space_rows = 0
            compatible_rows = 0
            seen_replacements: set[str] = set()

            for _, alt in pool.iterrows():
                alt_smiles = str(alt["canonical_smiles"])
                if alt_smiles == base_smiles or alt_smiles in seen_replacements or alt_smiles not in vectors:
                    continue
                alt_groups = alt["group_set"]
                matched_groups = base_groups & alt_groups
                if require_shared_groups and not matched_groups:
                    continue
                search_space_rows += 1
                reason = compatibility_reason(counterpart_groups, alt_groups)
                if require_counterpart_compatibility and reason is None:
                    continue
                compatible_rows += 1
                seen_replacements.add(alt_smiles)
                alt_vector = vectors[alt_smiles]
                scored.append(
                    {
                        "source_candidate_tg": source_tg,
                        "replace_side": side,
                        "original_smiles": raw_smiles,
                        "replacement_smiles": alt_smiles,
                        "replacement_source": alt.get("source", "unknown"),
                        "replacement_label": alt.get("label", ""),
                        "replacement_template_family": alt.get("template_family", ""),
                        "replacement_template_intended_group": alt.get("template_intended_group", ""),
                        "shared_groups": ";".join(sorted(base_groups)),
                        "counterpart_groups": ";".join(sorted(counterpart_groups)),
                        "counterpart_compatibility_reason": "" if reason is None else reason,
                        "feedback_constraint": (
                            "vae_latent_neighborhood_preserve_complementary_reactive_pair"
                            if require_counterpart_compatibility
                            else "vae_latent_neighborhood_shared_functional_group"
                        ),
                        "tanimoto": tanimoto(raw_smiles, alt_smiles),
                        "latent_distance": float(np.linalg.norm(base_vector - alt_vector)),
                        "latent_cosine_similarity": cosine_similarity(base_vector, alt_vector),
                        "latent_search_space_rows": search_space_rows,
                        "latent_compatible_rows": compatible_rows,
                        "matched_groups": ";".join(sorted(matched_groups)),
                        "latent_size": int(latent_size),
                        "vae_checkpoint": vae_checkpoint,
                    }
                )

            for rank, proposal in enumerate(sorted(scored, key=lambda item: item["latent_distance"])[:per_side], start=1):
                proposal["latent_rank"] = rank
                proposal["latent_search_space_rows"] = search_space_rows
                proposal["latent_compatible_rows"] = compatible_rows
                rows.append(proposal)

    return pd.DataFrame(rows, columns=LATENT_PROPOSAL_COLUMNS)


def write_report(proposals: pd.DataFrame, summary: dict[str, Any], report_path: Path, out_path: Path) -> None:
    lines = [
        "# VAE Latent Local Search",
        "",
        "本文档把 TODO 中“VAE：替换策略；生成策略”推进为可运行的 VAE latent-neighborhood local search。它不声称 VAE decoder 已经生成全新有效 SMILES，而是在当前可审计候选 inventory 中，用 VAE latent 距离检索高 reward 候选附近的替换单体，再交给同一 predictor/Harness 评估链。",
        "",
        "## 输出文件",
        "",
        f"- Proposals: `{out_path}`",
        f"- Summary: `{out_path.with_name('latent_local_search_summary.json')}`",
        f"- Report: `{report_path}`",
        "",
        "## 汇总",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 最近邻替换示例",
            "",
            "| rank | source Tg (C) | side | latent distance | latent cosine | tanimoto | source | matched groups | compatibility |",
            "| ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    ordered = proposals.sort_values(["latent_distance", "source_candidate_tg"]).head(20) if not proposals.empty else proposals
    for rank, (_, row) in enumerate(ordered.iterrows(), start=1):
        lines.append(
            f"| {rank} | {float(row['source_candidate_tg']):.3f} | {row['replace_side']} | "
            f"{float(row['latent_distance']):.4f} | {float(row['latent_cosine_similarity']):.4f} | "
            f"{float(row['tanimoto']):.3f} | {row['replacement_source']} | "
            f"{str(row['matched_groups']).replace('|', '; ')} | "
            f"{str(row['counterpart_compatibility_reason']).replace('|', '; ')} |"
        )
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- 旧 replacement 使用 Morgan/Tanimoto 排序；本策略使用当前 VAE encoder 学到的 latent 几何排序。",
            "- `--require-counterpart-compatibility` 打开时，替换单体必须继续和未替换的另一侧单体形成可映射反应对。",
            "- 输出仍保留 `tanimoto`，便于后续比较“指纹相似”和“VAE 表示相近”是否给出不同候选。",
            "- 下一步必须运行 `scripts/evaluate_replacement_proposals.py`；未通过 predictor/Harness/PiEvo 的 latent 邻居不能被当成推荐配方。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_latent_local_search(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    cfg = load_config(args.config)
    seed = int(cfg.get("seed", 42))
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)

    best_model = load_json(args.best_model)
    latent_size = int(args.latent_size or best_model["latent_size"])
    checkpoint_path = Path(cfg["output_dir"]) / "vae" / f"finetuned_latent_{latent_size}.pt"
    device = resolve_device(args.device)
    vae, checkpoint = load_vae_checkpoint(checkpoint_path, map_location=device)
    vae.to(device)

    candidates = pd.read_csv(args.candidates)
    raw_pool = load_replacement_pool(Path(args.groups), None if not args.component_inventory else Path(args.component_inventory))
    pool = prepare_replacement_pool(raw_pool, checkpoint["charset"], int(checkpoint["max_length"]))
    selected = candidates.head(args.top_k)
    selected_smiles = []
    for _, row in selected.iterrows():
        for side in ["a", "b"]:
            smi = canonical_smiles(row[f"smiles_{side}"])
            if smi is not None and is_vae_encodable(smi, checkpoint["charset"], int(checkpoint["max_length"])):
                selected_smiles.append(smi)
    unique_smiles = sorted(set(selected_smiles) | set(pool["canonical_smiles"].astype(str)))
    latent = encode_smiles(
        vae,
        unique_smiles,
        checkpoint["charset"],
        int(checkpoint["max_length"]),
        device,
        batch_size=args.encode_batch_size,
    )
    vectors = {smiles: latent[idx] for idx, smiles in enumerate(unique_smiles)}
    proposals = propose_latent_replacements_from_vectors(
        candidates,
        pool,
        vectors,
        top_k=args.top_k,
        per_side=args.per_side,
        latent_size=latent_size,
        vae_checkpoint=str(checkpoint_path),
        require_counterpart_compatibility=args.require_counterpart_compatibility,
        require_shared_groups=not args.allow_no_shared_groups,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proposals.to_csv(out_path, index=False)
    summary = {
        "input_candidate_rows": int(len(candidates)),
        "source_candidate_rows": int(len(selected)),
        "replacement_pool_rows": int(len(pool)),
        "encoded_unique_smiles": int(len(unique_smiles)),
        "proposals": int(len(proposals)),
        "latent_size": int(latent_size),
        "per_side": int(args.per_side),
        "require_counterpart_compatibility": bool(args.require_counterpart_compatibility),
        "require_shared_groups": not bool(args.allow_no_shared_groups),
        "literature_template_proposals": 0
        if proposals.empty or "replacement_source" not in proposals
        else int((proposals["replacement_source"].astype(str) == "literature_template").sum()),
        "mean_latent_distance": None if proposals.empty else round(float(proposals["latent_distance"].mean()), 6),
        "min_latent_distance": None if proposals.empty else round(float(proposals["latent_distance"].min()), 6),
        "mean_tanimoto": None if proposals.empty else round(float(proposals["tanimoto"].mean()), 6),
    }
    summary_path = out_path.with_name("latent_local_search_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(proposals, summary, Path(args.report), out_path)
    return proposals, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate replacement proposals by VAE latent-neighborhood retrieval.")
    parser.add_argument("--config", default="configs/reproduce.yaml")
    parser.add_argument("--best-model", default="artifacts/reproduce/predictors/best_model.json")
    parser.add_argument("--candidates", default="artifacts/reproduce/discovery/selected_candidates.csv")
    parser.add_argument("--groups", default="artifacts/reproduce/discovery/monomer_functional_groups.csv")
    parser.add_argument("--component-inventory", default="artifacts/trail/candidates_expanded/component_inventory.csv")
    parser.add_argument("--latent-size", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--per-side", type=int, default=5)
    parser.add_argument("--require-counterpart-compatibility", action="store_true")
    parser.add_argument("--allow-no-shared-groups", action="store_true")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--encode-batch-size", type=int, default=512)
    parser.add_argument("--out", default="artifacts/trail/generation/vae_latent_local_search/latent_local_search_proposals.csv")
    parser.add_argument("--report", default="reports/vae_latent_local_search.md")
    args = parser.parse_args()
    run_latent_local_search(args)


if __name__ == "__main__":
    main()
