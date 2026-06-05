from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from rdkit import Chem


def validate_candidates(path: Path, target_min: float, target_max: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.empty:
        return df
    checks = []
    for _, row in df.iterrows():
        valid_a = Chem.MolFromSmiles(str(row["smiles_a"])) is not None
        valid_b = Chem.MolFromSmiles(str(row["smiles_b"])) is not None
        ratio_ok = abs(float(row["ratio_a"]) + float(row["ratio_b"]) - 1.0) < 1e-6
        target_ok = target_min <= float(row["predicted_tg"]) <= target_max
        chemistry_ok = bool(str(row.get("compatibility_reason", "")).strip())
        checks.append(valid_a and valid_b and ratio_ok and target_ok and chemistry_ok)
    out = df.copy()
    out["harness_pass"] = checks
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="artifacts/reproduce/discovery/selected_candidates.csv")
    parser.add_argument("--target-min", type=float, default=190.0)
    parser.add_argument("--target-max", type=float, default=200.0)
    parser.add_argument("--out", default="artifacts/trail/harness/candidate_validation.csv")
    args = parser.parse_args()
    result = validate_candidates(Path(args.candidates), args.target_min, args.target_max)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(target, index=False)


if __name__ == "__main__":
    main()

