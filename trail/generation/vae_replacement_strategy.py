from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

from smp02.functional_groups import compatibility_reason


PROPOSAL_COLUMNS = [
    "source_candidate_tg",
    "replace_side",
    "original_smiles",
    "replacement_smiles",
    "replacement_source",
    "replacement_label",
    "replacement_template_family",
    "replacement_template_intended_group",
    "shared_groups",
    "counterpart_groups",
    "counterpart_compatibility_reason",
    "feedback_constraint",
    "tanimoto",
]


def parse_group_set(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    return {
        item.strip()
        for item in str(value).split(";")
        if item.strip() and item.strip().lower() not in {"nan", "none"}
    }


def tanimoto(a: str, b: str) -> float:
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    ma = Chem.MolFromSmiles(a)
    mb = Chem.MolFromSmiles(b)
    if ma is None or mb is None:
        return 0.0
    return float(DataStructs.TanimotoSimilarity(gen.GetFingerprint(ma), gen.GetFingerprint(mb)))


def load_replacement_pool(groups: Path, component_inventory: Path | None = None) -> pd.DataFrame:
    path = component_inventory if component_inventory is not None else groups
    frame = pd.read_csv(path)
    if "invalid" in frame.columns:
        invalid = frame["invalid"].map(lambda value: str(value).strip().lower() in {"1", "true", "yes"})
        frame = frame[~invalid].copy()
    required = {"smiles", "groups"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Replacement pool {path} missing required columns: {missing}")
    defaults = {
        "source": "unknown",
        "label": "",
        "template_family": "",
        "template_intended_group": "",
    }
    for column, value in defaults.items():
        if column not in frame.columns:
            frame[column] = value
        else:
            frame[column] = frame[column].fillna(value)
    return frame


def propose_replacements(
    candidates: Path,
    groups: Path,
    top_k: int,
    per_side: int = 3,
    require_counterpart_compatibility: bool = False,
    component_inventory: Path | None = None,
) -> pd.DataFrame:
    cand = pd.read_csv(candidates)
    group_df = load_replacement_pool(groups, component_inventory)
    if cand.empty or group_df.empty:
        return pd.DataFrame(columns=PROPOSAL_COLUMNS)
    group_df["group_set"] = group_df["groups"].map(parse_group_set)
    rows = []
    for _, row in cand.head(top_k).iterrows():
        for side in ["a", "b"]:
            smi = str(row[f"smiles_{side}"])
            base_groups = parse_group_set(row[f"groups_{side}"])
            other_side = "b" if side == "a" else "a"
            counterpart_groups = parse_group_set(row[f"groups_{other_side}"])
            pool = group_df[group_df["group_set"].map(lambda g: bool(base_groups & g))]
            scored = []
            for _, alt in pool.iterrows():
                alt_smi = str(alt["smiles"])
                if alt_smi == smi:
                    continue
                reason = compatibility_reason(counterpart_groups, alt["group_set"])
                if require_counterpart_compatibility and reason is None:
                    continue
                scored.append((alt_smi, tanimoto(smi, alt_smi), reason, alt.to_dict()))
            for alt_smi, score, reason, alt_meta in sorted(scored, key=lambda x: x[1], reverse=True)[:per_side]:
                rows.append(
                    {
                        "source_candidate_tg": row["predicted_tg"],
                        "replace_side": side,
                        "original_smiles": smi,
                        "replacement_smiles": alt_smi,
                        "replacement_source": alt_meta.get("source", "unknown"),
                        "replacement_label": alt_meta.get("label", ""),
                        "replacement_template_family": alt_meta.get("template_family", ""),
                        "replacement_template_intended_group": alt_meta.get("template_intended_group", ""),
                        "shared_groups": ";".join(sorted(base_groups)),
                        "counterpart_groups": ";".join(sorted(counterpart_groups)),
                        "counterpart_compatibility_reason": "" if reason is None else reason,
                        "feedback_constraint": (
                            "preserve_complementary_reactive_pair"
                            if require_counterpart_compatibility
                            else "shared_functional_group_similarity"
                        ),
                        "tanimoto": score,
                    }
                )
    return pd.DataFrame(rows, columns=PROPOSAL_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="artifacts/reproduce/discovery/selected_candidates.csv")
    parser.add_argument("--groups", default="artifacts/reproduce/discovery/monomer_functional_groups.csv")
    parser.add_argument(
        "--component-inventory",
        default="",
        help="Optional component_inventory.csv replacement pool; when set, overrides --groups and preserves source/template provenance.",
    )
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--per-side", type=int, default=3)
    parser.add_argument(
        "--require-counterpart-compatibility",
        action="store_true",
        help="Filter replacements to those that preserve a mapped reactive pair with the unchanged co-monomer.",
    )
    parser.add_argument("--out", default="artifacts/trail/generation/replacement_proposals.csv")
    args = parser.parse_args()
    result = propose_replacements(
        Path(args.candidates),
        Path(args.groups),
        args.top_k,
        per_side=args.per_side,
        require_counterpart_compatibility=args.require_counterpart_compatibility,
        component_inventory=None if not args.component_inventory else Path(args.component_inventory),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)


if __name__ == "__main__":
    main()
