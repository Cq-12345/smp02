from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from rdkit import Chem


def ratio_sum_ok(value: str) -> bool:
    try:
        ratios = [float(part) for part in str(value).split(":")]
        return abs(sum(ratios) - 1.0) < 1e-4
    except Exception:
        return False


def smiles_valid(value: str) -> bool:
    try:
        return all(Chem.MolFromSmiles(part) is not None for part in str(value).split("|"))
    except Exception:
        return False


def target_bounds(target_min: float | None, target_max: float | None, target_center: float | None, target_window: float | None) -> tuple[float, float]:
    if target_center is not None:
        window = 5.0 if target_window is None else float(target_window)
        return float(target_center) - window, float(target_center) + window
    if target_min is None or target_max is None:
        raise ValueError("Either --target-center or both --target-min/--target-max must be supplied.")
    return float(target_min), float(target_max)


def validate_candidates(path: Path, target_min: float, target_max: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.empty:
        return df
    if {"smiles", "ratios", "predicted_tg_mean_c", "compatibility_reasons"}.issubset(df.columns):
        out = df.copy()
        out["valid_smiles"] = out["smiles"].map(smiles_valid)
        out["ratio_ok"] = out["ratios"].map(ratio_sum_ok)
        out["target_ok"] = out["predicted_tg_mean_c"].map(lambda value: target_min <= float(value) <= target_max)
        out["chemistry_ok"] = out["compatibility_reasons"].fillna("").astype(str).str.len().gt(0)
        out["harness_pass"] = out[["valid_smiles", "ratio_ok", "target_ok", "chemistry_ok"]].all(axis=1)
        return out
    checks = []
    detail_rows = []
    for _, row in df.iterrows():
        valid_a = Chem.MolFromSmiles(str(row["smiles_a"])) is not None
        valid_b = Chem.MolFromSmiles(str(row["smiles_b"])) is not None
        ratio_ok = abs(float(row["ratio_a"]) + float(row["ratio_b"]) - 1.0) < 1e-6
        target_ok = target_min <= float(row["predicted_tg"]) <= target_max
        chemistry_ok = bool(str(row.get("compatibility_reason", "")).strip())
        checks.append(valid_a and valid_b and ratio_ok and target_ok and chemistry_ok)
        detail_rows.append((valid_a and valid_b, ratio_ok, target_ok, chemistry_ok))
    out = df.copy()
    out[["valid_smiles", "ratio_ok", "target_ok", "chemistry_ok"]] = detail_rows
    out["harness_pass"] = checks
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="artifacts/reproduce/discovery/selected_candidates.csv")
    parser.add_argument("--target-min", type=float, default=None)
    parser.add_argument("--target-max", type=float, default=None)
    parser.add_argument("--target-center", type=float, default=195.0)
    parser.add_argument("--target-window", type=float, default=5.0)
    parser.add_argument("--out", default="artifacts/trail/harness/candidate_validation.csv")
    args = parser.parse_args()
    low, high = target_bounds(args.target_min, args.target_max, args.target_center, args.target_window)
    result = validate_candidates(Path(args.candidates), low, high)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(target, index=False)


if __name__ == "__main__":
    main()
