from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from rdkit import Chem


REQUIRED_COLUMNS = [
    "generation_id",
    "strategy",
    "stage",
    "target_tg_c",
    "target_window_c",
    "candidate_smiles",
    "candidate_ratios",
    "source_context",
]


def load_schema(schema_path: Path) -> dict[str, Any]:
    return yaml.safe_load(schema_path.read_text(encoding="utf-8"))


def allowed_strategies(schema: dict[str, Any]) -> set[str]:
    strategy = schema.get("required_fields", {}).get("strategy", {})
    return {str(value) for value in strategy.get("values", [])}


def ratios_sum_ok(value: object) -> bool:
    try:
        ratios = [float(part) for part in str(value).split(":")]
        return bool(ratios) and abs(sum(ratios) - 1.0) < 1e-4
    except Exception:
        return False


def smiles_valid(value: object) -> bool:
    try:
        parts = [part for part in str(value).split("|") if part]
        return bool(parts) and all(Chem.MolFromSmiles(part) is not None for part in parts)
    except Exception:
        return False


def as_float(value: object) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "selected"}


def target_reward(predicted_tg_c: float | None, target_tg_c: float | None, reward_temperature_c: float) -> float | None:
    if predicted_tg_c is None or target_tg_c is None:
        return None
    return float(math.exp(-abs(predicted_tg_c - target_tg_c) / max(float(reward_temperature_c), 1e-9)))


def missing_required(row: pd.Series) -> list[str]:
    missing = []
    for column in REQUIRED_COLUMNS:
        value = row.get(column)
        if pd.isna(value) or str(value).strip() == "":
            missing.append(column)
    return missing


def build_failure_reason(row: pd.Series, explicit: object, missing: list[str]) -> str:
    reasons = []
    if missing:
        reasons.append("missing_required_fields:" + "|".join(missing))
    if not bool(row["strategy_allowed"]):
        reasons.append("unknown_strategy")
    if not bool(row["valid_smiles"]):
        reasons.append("invalid_smiles")
    if not bool(row["ratio_ok"]):
        reasons.append("ratio_sum_not_one")
    if not bool(row["prediction_available"]):
        reasons.append("prediction_missing")
    elif not bool(row["target_ok"]):
        reasons.append("target_out_of_window")
    if not bool(row["chemistry_ok"]):
        reasons.append("chemistry_evidence_missing")
    explicit_text = "" if pd.isna(explicit) else str(explicit).strip()
    if explicit_text and explicit_text not in reasons:
        reasons.append(explicit_text)
    return ";".join(reasons)


def import_generation_records(
    input_path: Path,
    schema_path: Path,
    reward_temperature_c: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = pd.read_csv(input_path)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required generation record columns: {missing_columns}")

    schema = load_schema(schema_path)
    allowed = allowed_strategies(schema)
    out = df.copy()
    for optional in [
        "compatibility_reasons",
        "predicted_tg_mean_c",
        "harness_failure_reason",
        "selected_by_ids",
        "review_status",
    ]:
        if optional not in out.columns:
            out[optional] = ""

    row_missing = [missing_required(row) for _, row in out.iterrows()]
    out["required_fields_present"] = [not missing for missing in row_missing]
    out["strategy_allowed"] = out["strategy"].map(lambda value: str(value) in allowed)
    out["valid_smiles"] = out["candidate_smiles"].map(smiles_valid)
    out["ratio_ok"] = out["candidate_ratios"].map(ratios_sum_ok)
    out["predicted_tg_mean_c"] = out["predicted_tg_mean_c"].map(as_float)
    out["target_tg_c"] = out["target_tg_c"].astype(float)
    out["target_window_c"] = out["target_window_c"].astype(float)
    out["prediction_available"] = out["predicted_tg_mean_c"].notna()
    out["target_distance_c"] = [
        None if predicted is None else abs(float(predicted) - float(target))
        for predicted, target in zip(out["predicted_tg_mean_c"], out["target_tg_c"], strict=False)
    ]
    out["target_ok"] = [
        bool(distance is not None and distance <= float(window))
        for distance, window in zip(out["target_distance_c"], out["target_window_c"], strict=False)
    ]
    out["chemistry_ok"] = out["compatibility_reasons"].fillna("").astype(str).str.strip().str.len().gt(0)
    out["harness_pass"] = out[["valid_smiles", "ratio_ok", "prediction_available", "target_ok", "chemistry_ok"]].all(axis=1)
    out["generation_reward"] = [
        target_reward(predicted, target, reward_temperature_c)
        for predicted, target in zip(out["predicted_tg_mean_c"], out["target_tg_c"], strict=False)
    ]
    out["selected_by_ids"] = out["selected_by_ids"].map(parse_bool)
    out["record_pass"] = out[["required_fields_present", "strategy_allowed", "valid_smiles", "ratio_ok"]].all(axis=1)
    out["harness_failure_reason"] = [
        "" if harness_pass else build_failure_reason(row, explicit, missing)
        for (_, row), explicit, missing, harness_pass in zip(
            out.iterrows(),
            df.get("harness_failure_reason", pd.Series([""] * len(out))),
            row_missing,
            out["harness_pass"],
            strict=False,
        )
    ]
    out["review_status"] = [
        status if str(status).strip() else ("needs_review" if record_pass else "rejected_by_harness")
        for status, record_pass in zip(out["review_status"], out["record_pass"], strict=False)
    ]
    summary = {
        "input_rows": int(len(out)),
        "record_pass_rows": int(out["record_pass"].sum()),
        "ready_for_prediction_rows": int((out["record_pass"] & ~out["prediction_available"]).sum()),
        "harness_pass_rows": int(out["harness_pass"].sum()),
        "harness_fail_rows": int((~out["harness_pass"]).sum()),
        "strategy_counts": out["strategy"].value_counts().to_dict(),
        "stage_counts": out["stage"].value_counts().to_dict(),
        "best_distance_c": None if out["target_distance_c"].dropna().empty else float(out["target_distance_c"].dropna().min()),
        "mean_generation_reward": None if out["generation_reward"].dropna().empty else float(out["generation_reward"].dropna().mean()),
        "reward_temperature_c": float(reward_temperature_c),
    }
    return out, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import generated SMP hypotheses into an auditable generation record ledger.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--schema", default="trail/generation/generation_record_schema.yaml")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--out", default="artifacts/trail/generation/records/generation_record_ledger.csv")
    parser.add_argument("--summary", default="artifacts/trail/generation/records/generation_record_summary.json")
    args = parser.parse_args()
    ledger, summary = import_generation_records(Path(args.input), Path(args.schema), args.reward_temperature_c)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(out, index=False)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
