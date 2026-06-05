from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from rdkit import Chem

from smp02.agent_discovery import (
    ALLOWED_ATOMS,
    GENERATED_MONOMER_SEEDS,
    allowed_atom_set,
    classify_mol,
    functionality_estimate,
    monomer_features,
    one_fragment,
)
from smp02.data import canonicalize_smiles, iter_chembl_smiles, load_smp_records, unique_monomers


def candidate_row(smiles: str, source: str, label: str) -> dict[str, object] | None:
    canonical = canonicalize_smiles(smiles)
    if canonical is None:
        return None
    mol = Chem.MolFromSmiles(canonical)
    if mol is None or not one_fragment(mol) or not allowed_atom_set(mol):
        return None
    groups, counts = classify_mol(mol)
    features = monomer_features(mol, groups, counts)
    return {
        "smiles": canonical,
        "source": source,
        "label": label,
        "groups": ";".join(groups),
        "functionality": functionality_estimate(counts),
        "allowed_atoms": ";".join(sorted(ALLOWED_ATOMS)),
        **{f"feature_{name}": value for name, value in features.items()},
    }


def build_inventory(data_path: Path, chembl_path: Path, chembl_limit: int, include_generated: bool = True) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()

    records = load_smp_records(data_path)
    for idx, smiles in enumerate(unique_monomers(records), start=1):
        row = candidate_row(smiles, "library", f"library_{idx}")
        if row and str(row["smiles"]) not in seen:
            seen.add(str(row["smiles"]))
            rows.append(row)

    if include_generated:
        for label, smiles in GENERATED_MONOMER_SEEDS:
            row = candidate_row(smiles, "generated", label)
            if row and str(row["smiles"]) not in seen:
                seen.add(str(row["smiles"]))
                rows.append(row)

    for idx, smiles in enumerate(iter_chembl_smiles(chembl_path, limit=chembl_limit, max_length=220, validate=True), start=1):
        row = candidate_row(smiles, "chembl", f"chembl_scan_{idx}")
        if row and str(row["smiles"]) not in seen:
            seen.add(str(row["smiles"]))
            rows.append(row)

    return pd.DataFrame(rows)


def functional_group_index(inventory: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in inventory.iterrows():
        raw_groups = "" if pd.isna(row.get("groups", "")) else str(row.get("groups", ""))
        groups = set(raw_groups.split(";")) - {"", "nan", "None"}
        for group in sorted(groups):
            rows.append({"group": group, "smiles": row["smiles"], "source": row["source"], "label": row["label"]})
    return pd.DataFrame(rows)


def write_outputs(inventory: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(out_dir / "component_inventory.csv", index=False)
    group_index = functional_group_index(inventory)
    group_index.to_csv(out_dir / "functional_group_index.csv", index=False)
    source_counts = Counter(inventory["source"]) if not inventory.empty else Counter()
    group_counts = Counter(group_index["group"]) if not group_index.empty else Counter()
    summary = {
        "n_components": int(len(inventory)),
        "source_counts": dict(source_counts),
        "n_functional_groups": int(len(group_counts)),
        "top_functional_groups": dict(group_counts.most_common(30)),
    }
    (out_dir / "component_inventory_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a small-molecule SMP component inventory grouped by functional groups.")
    parser.add_argument("--data", default="data/SMP_Dataset.xlsx")
    parser.add_argument("--chembl", default="data/chembl_36_chemreps.txt")
    parser.add_argument("--chembl-limit", type=int, default=5000)
    parser.add_argument("--no-generated", action="store_true")
    parser.add_argument("--out", default="artifacts/trail/candidates")
    args = parser.parse_args()
    inventory = build_inventory(Path(args.data), Path(args.chembl), args.chembl_limit, include_generated=not args.no_generated)
    write_outputs(inventory, Path(args.out))


if __name__ == "__main__":
    main()
