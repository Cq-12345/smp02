from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd
import yaml
from rdkit import Chem


def target_reward(observed_tg_c: float, target_tg_c: float, reward_temperature_c: float) -> float:
    return float(math.exp(-abs(float(observed_tg_c) - float(target_tg_c)) / max(float(reward_temperature_c), 1e-9)))


def ratios_sum_ok(value: str) -> bool:
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


def load_authority_weights(schema_path: Path) -> dict[str, float]:
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    return {str(k): float(v) for k, v in schema.get("authority_weights", {}).items()}


def import_observations(input_path: Path, schema_path: Path, reward_temperature_c: float) -> tuple[pd.DataFrame, dict[str, object]]:
    df = pd.read_csv(input_path)
    required = ["observation_id", "source_type", "target_tg_c", "observed_tg_c", "smiles", "ratios"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required observation columns: {missing}")
    weights = load_authority_weights(schema_path)
    out = df.copy()
    out["valid_smiles"] = out["smiles"].map(smiles_valid)
    out["ratio_ok"] = out["ratios"].map(ratios_sum_ok)
    out["target_distance_c"] = (out["observed_tg_c"].astype(float) - out["target_tg_c"].astype(float)).abs()
    out["target_reward"] = [
        target_reward(obs, target, reward_temperature_c)
        for obs, target in zip(out["observed_tg_c"], out["target_tg_c"], strict=False)
    ]
    out["authority_weight"] = out["source_type"].map(lambda source: weights.get(str(source), 1.0))
    out["weighted_reward"] = out["target_reward"] * out["authority_weight"]
    out["ledger_pass"] = out["valid_smiles"] & out["ratio_ok"] & out["observed_tg_c"].notna() & out["target_tg_c"].notna()
    summary = {
        "input_rows": int(len(out)),
        "ledger_pass_rows": int(out["ledger_pass"].sum()),
        "source_counts": out["source_type"].value_counts().to_dict(),
        "mean_target_distance_c": float(out["target_distance_c"].mean()) if len(out) else None,
        "mean_weighted_reward": float(out["weighted_reward"].mean()) if len(out) else None,
        "reward_temperature_c": float(reward_temperature_c),
    }
    return out, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import surrogate/real Tg observations into a weighted SMP observation ledger.")
    parser.add_argument("--input", default="trail/experiments/example_observations.csv")
    parser.add_argument("--schema", default="trail/experiments/observation_schema.yaml")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--out", default="artifacts/trail/experiments/observation_ledger.csv")
    parser.add_argument("--summary", default="artifacts/trail/experiments/observation_ledger_summary.json")
    args = parser.parse_args()
    ledger, summary = import_observations(Path(args.input), Path(args.schema), args.reward_temperature_c)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(out, index=False)
    Path(args.summary).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
