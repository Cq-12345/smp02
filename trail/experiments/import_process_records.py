from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from rdkit import Chem


REQUIRED_COLUMNS = [
    "process_record_id",
    "linked_observation_id",
    "source_type",
    "target_tg_c",
    "observed_tg_c",
    "smiles",
    "ratios",
    "reaction_principle",
    "process_template",
    "review_status",
]


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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


def present(value: object) -> bool:
    return not pd.isna(value) and str(value).strip() != ""


def process_templates(knowledge_path: Path) -> dict[str, dict[str, Any]]:
    knowledge = load_yaml(knowledge_path)
    return knowledge.get("process_condition_templates", {})


def required_process_fields(template_name: str, templates: dict[str, dict[str, Any]]) -> list[str]:
    template = templates.get(str(template_name), {})
    return [str(field) for field in template.get("cure_schedule_fields", [])]


def missing_process_fields(row: pd.Series, required_fields: list[str]) -> list[str]:
    missing = []
    for field in required_fields:
        if field not in row or not present(row[field]):
            missing.append(field)
    return missing


def import_process_records(
    input_path: Path,
    schema_path: Path,
    knowledge_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = pd.read_csv(input_path)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required process record columns: {missing_columns}")
    schema = load_yaml(schema_path)
    templates = process_templates(knowledge_path)
    allowed_source_types = set(schema["required_fields"]["source_type"]["values"])
    allowed_review = set(schema["required_fields"]["review_status"]["values"])
    out = df.copy()
    out["source_type_allowed"] = out["source_type"].map(lambda value: str(value) in allowed_source_types)
    out["review_status_allowed"] = out["review_status"].map(lambda value: str(value) in allowed_review)
    out["valid_smiles"] = out["smiles"].map(smiles_valid)
    out["ratio_ok"] = out["ratios"].map(ratios_sum_ok)
    out["process_template_known"] = out["process_template"].map(lambda value: str(value) in templates)
    required_lists = [required_process_fields(str(value), templates) for value in out["process_template"]]
    missing_lists = [missing_process_fields(row, fields) for (_, row), fields in zip(out.iterrows(), required_lists, strict=False)]
    out["required_process_fields"] = [";".join(fields) for fields in required_lists]
    out["missing_process_fields"] = [";".join(fields) for fields in missing_lists]
    out["process_fields_complete"] = [len(fields) == 0 for fields in missing_lists]
    out["target_distance_c"] = (out["observed_tg_c"].astype(float) - out["target_tg_c"].astype(float)).abs()
    out["process_record_pass"] = out[
        [
            "source_type_allowed",
            "review_status_allowed",
            "valid_smiles",
            "ratio_ok",
            "process_template_known",
        ]
    ].all(axis=1)
    out["ready_for_active_ledger"] = out["process_record_pass"] & out["process_fields_complete"] & (
        out["review_status"] == "approved_for_active_ledger"
    )
    summary = {
        "input_rows": int(len(out)),
        "process_record_pass_rows": int(out["process_record_pass"].sum()),
        "ready_for_active_ledger_rows": int(out["ready_for_active_ledger"].sum()),
        "process_incomplete_rows": int((~out["process_fields_complete"]).sum()),
        "source_counts": out["source_type"].value_counts().to_dict(),
        "review_status_counts": out["review_status"].value_counts().to_dict(),
        "process_template_counts": out["process_template"].value_counts().to_dict(),
        "mean_target_distance_c": float(out["target_distance_c"].mean()) if len(out) else None,
    }
    return out, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import SMP process/review records and validate process-condition completeness.")
    parser.add_argument("--input", default="trail/experiments/example_process_records.csv")
    parser.add_argument("--schema", default="trail/experiments/process_record_schema.yaml")
    parser.add_argument("--knowledge", default="trail/knowledge/smp_prior_knowledge.yaml")
    parser.add_argument("--out", default="artifacts/trail/experiments/process_record_ledger.csv")
    parser.add_argument("--summary", default="artifacts/trail/experiments/process_record_summary.json")
    args = parser.parse_args()
    ledger, summary = import_process_records(Path(args.input), Path(args.schema), Path(args.knowledge))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(out, index=False)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
