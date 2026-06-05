from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_LEDGER_PATHS = [
    "artifacts/trail/human_review/validation_result_observation_ledger.csv",
]

ACTIVE_SOURCE_TYPES = ["high_fidelity_simulation", "real_dsc", "literature"]

BASE_LEDGER_COLUMNS = [
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
    "valid_smiles",
    "ratio_ok",
    "target_distance_c",
    "target_reward",
    "authority_weight",
    "weighted_reward",
    "ledger_pass",
]

ACTIVE_LEDGER_COLUMNS = BASE_LEDGER_COLUMNS + [
    "source_ledger",
    "active_evidence",
    "active_evidence_scope",
]


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed"}


def numeric_mean(df: pd.DataFrame, column: str) -> float | None:
    if df.empty or column not in df.columns:
        return None
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    return float(values.mean()) if len(values) else None


def numeric_sum(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[column], errors="coerce").fillna(0.0).sum())


def numeric_max(df: pd.DataFrame, column: str) -> float | None:
    if df.empty or column not in df.columns:
        return None
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    return float(values.max()) if len(values) else None


def read_ledgers(paths: list[Path]) -> tuple[pd.DataFrame, list[str]]:
    frames = []
    missing = []
    for path in paths:
        if not path.exists():
            missing.append(str(path))
            continue
        frame = pd.read_csv(path)
        for column in BASE_LEDGER_COLUMNS:
            if column not in frame.columns:
                frame[column] = ""
        frame["source_ledger"] = str(path)
        frames.append(frame[BASE_LEDGER_COLUMNS + ["source_ledger"]])
    if not frames:
        return pd.DataFrame(columns=BASE_LEDGER_COLUMNS + ["source_ledger"]), missing
    return pd.concat(frames, ignore_index=True), missing


def filter_active_observations(
    ledger: pd.DataFrame,
    allowed_sources: list[str] | tuple[str, ...] = tuple(ACTIVE_SOURCE_TYPES),
    require_ledger_pass: bool = True,
) -> pd.DataFrame:
    out = ledger.copy()
    for column in BASE_LEDGER_COLUMNS + ["source_ledger"]:
        if column not in out.columns:
            out[column] = ""
    source_allowed = out["source_type"].fillna("").astype(str).isin(set(allowed_sources))
    if require_ledger_pass:
        ledger_pass = out["ledger_pass"].map(bool_value)
    else:
        ledger_pass = pd.Series([True] * len(out), index=out.index)
    active = out[source_allowed & ledger_pass].copy()
    active["active_evidence"] = True
    active["active_evidence_scope"] = "approved_high_authority_observation"
    return active[ACTIVE_LEDGER_COLUMNS]


def summarize_active_ledger(
    input_ledger: pd.DataFrame,
    active_ledger: pd.DataFrame,
    input_paths: list[Path],
    missing_paths: list[str],
    allowed_sources: list[str] | tuple[str, ...] = tuple(ACTIVE_SOURCE_TYPES),
) -> dict[str, Any]:
    ledger_pass_rows = int(input_ledger["ledger_pass"].map(bool_value).sum()) if "ledger_pass" in input_ledger else 0
    source_counts = input_ledger["source_type"].value_counts().to_dict() if "source_type" in input_ledger else {}
    active_source_counts = active_ledger["source_type"].value_counts().to_dict() if not active_ledger.empty else {}
    validation_result_active_rows = 0
    if "source_ledger" in active_ledger:
        validation_result_active_rows = int(active_ledger["source_ledger"].fillna("").str.contains("validation_result").sum())
    return {
        "input_ledgers": [str(path) for path in input_paths],
        "missing_input_ledgers": missing_paths,
        "allowed_active_source_types": list(allowed_sources),
        "input_rows": int(len(input_ledger)),
        "source_counts": source_counts,
        "ledger_pass_rows": ledger_pass_rows,
        "allowed_source_rows": int(input_ledger["source_type"].fillna("").astype(str).isin(set(allowed_sources)).sum())
        if "source_type" in input_ledger
        else 0,
        "active_rows": int(len(active_ledger)),
        "active_source_counts": active_source_counts,
        "validation_result_active_rows": validation_result_active_rows,
        "authority_weight_sum": numeric_sum(active_ledger, "authority_weight"),
        "max_authority_weight": numeric_max(active_ledger, "authority_weight"),
        "mean_target_distance_c": numeric_mean(active_ledger, "target_distance_c"),
        "mean_weighted_reward": numeric_mean(active_ledger, "weighted_reward"),
    }


def write_report(summary: dict[str, Any], report_path: Path, out_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Active High-authority Observation Ledger",
        "",
        "本文档记录哪些 observation ledger 行可以作为 active evidence 进入后续 PiEvo posterior、策略更新或人工闭环统计。",
        "当前规则只接受已经通过 `ledger_pass` 的 `high_fidelity_simulation`、`real_dsc`、`literature`；`surrogate` 不进入这一层。",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    scalar_keys = [
        "input_rows",
        "ledger_pass_rows",
        "allowed_source_rows",
        "active_rows",
        "validation_result_active_rows",
        "authority_weight_sum",
        "max_authority_weight",
        "mean_target_distance_c",
        "mean_weighted_reward",
    ]
    for key in scalar_keys:
        lines.append(f"| {key} | {summary.get(key)} |")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- active ledger: `{out_path}`",
            "",
            "## Gate Rules",
            "",
            "- 必须已经通过前一层 observation ledger 的 `ledger_pass`。",
            "- `source_type` 必须属于 `high_fidelity_simulation`、`real_dsc` 或 `literature`。",
            "- validation request result 仍必须先经过 request/source/process/reviewer gate；本脚本不接收原始 result template。",
            "- 当前若 `active_rows=0`，表示还没有完成并获批的高权重观测，不表示候选生成链路失败。",
        ]
    )
    for title, counts in [
        ("Input Source Counts", summary.get("source_counts", {})),
        ("Active Source Counts", summary.get("active_source_counts", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| source_type | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_active_ledger(
    ledger_paths: list[Path],
    out_path: Path,
    summary_path: Path,
    report_path: Path,
    allowed_sources: list[str] | tuple[str, ...] = tuple(ACTIVE_SOURCE_TYPES),
    require_ledger_pass: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    input_ledger, missing_paths = read_ledgers(ledger_paths)
    active_ledger = filter_active_observations(input_ledger, allowed_sources, require_ledger_pass)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    active_ledger.to_csv(out_path, index=False)
    summary = summarize_active_ledger(input_ledger, active_ledger, ledger_paths, missing_paths, allowed_sources)
    summary["out_path"] = str(out_path)
    summary["summary_path"] = str(summary_path)
    summary["report_path"] = str(report_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(summary, report_path, out_path)
    return active_ledger, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the active high-authority observation ledger.")
    parser.add_argument("--ledger", action="append", dest="ledgers", help="Observation ledger path. Can be passed multiple times.")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--out", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--report", default="reports/active_high_authority_observation_ledger.md")
    parser.add_argument("--allow-source", action="append", dest="allowed_sources")
    parser.add_argument("--no-require-ledger-pass", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_path = Path(args.out) if args.out else out_dir / "active_high_authority_observation_ledger.csv"
    summary_path = Path(args.summary) if args.summary else out_dir / "active_high_authority_observation_summary.json"
    ledger_paths = [Path(path) for path in (args.ledgers or DEFAULT_LEDGER_PATHS)]
    allowed_sources = args.allowed_sources or ACTIVE_SOURCE_TYPES
    build_active_ledger(
        ledger_paths=ledger_paths,
        out_path=out_path,
        summary_path=summary_path,
        report_path=Path(args.report),
        allowed_sources=allowed_sources,
        require_ledger_pass=not args.no_require_ledger_pass,
    )


if __name__ == "__main__":
    main()
