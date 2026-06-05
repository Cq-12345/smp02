from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from smp02.agent_discovery import initial_principles, parse_agent_config  # noqa: E402
from smp02.pievo_faithful import (  # noqa: E402
    entropy,
    initial_priors,
    load_external_observations,
    parse_pievo_faithful_config,
    train_principle_experts,
    update_posterior_full_history,
)
from smp02.utils import load_config  # noqa: E402


OBSERVATION_OUTPUT_COLUMNS = [
    "formula_id",
    "n_components",
    "smiles",
    "ratios",
    "sources",
    "labels",
    "groups",
    "compatibility_reasons",
    "predicted_tg_mean_c",
    "predicted_tg_sigma_c",
    "observed_tg_c",
    "target_tg_c",
    "target_distance_c",
    "prior_score",
    "observation_id",
    "observation_source_type",
    "authority_weight",
    "evidence_role",
]


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Active Evidence PiEvo Bridge",
        "",
        "本文档验证 active high-authority observation ledger 是否已经能进入 PiEvo 的外部观测加载和 full-history posterior 更新路径。",
        "它不生成新候选，也不把 surrogate 候选升级成真实证据。",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    scalar_keys = [
        "external_input_rows",
        "external_candidate_rows_after_ledger_pass",
        "external_candidate_rows_after_source_filter",
        "external_candidate_rows_after_active_filter",
        "external_accepted_rows",
        "external_rejected_rows",
        "posterior_history_rows",
        "total_authority_weight",
        "posterior_entropy",
    ]
    for key in scalar_keys:
        lines.append(f"| {key} | {summary.get(key)} |")
    lines.extend(
        [
            "",
            "## Gate",
            "",
            f"- external ledger: `{summary.get('external_ledger_path')}`",
            f"- allowed source types: `{summary.get('allowed_source_types')}`",
            f"- require active evidence: `{summary.get('require_active_evidence')}`",
            f"- bridge status: `{summary.get('bridge_status')}`",
            "",
            "## Interpretation",
            "",
            "- `active_evidence_updates_posterior` 表示已有高权重观测进入 full-history posterior；当前为 false 时，本 bridge 的 posterior 输入仅为先验，主闭环仍依赖 surrogate smoke 证据。",
            "- `no_active_evidence_noop` 表示 active ledger 为空或没有可接收行，这是正确的质量门行为。",
            "- 如果未来填入真实 DSC、高保真模拟或文献复现实验，本脚本会在同一路径中记录 accepted rows、authority weight 和 posterior MAP principle。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_bridge(config_path: Path, out_dir: Path, report_path: Path) -> dict[str, Any]:
    cfg = load_config(config_path)
    agent_cfg = parse_agent_config(cfg)
    pievo_cfg = parse_pievo_faithful_config(cfg, agent_cfg)
    principles = initial_principles()
    observations, external_summary = load_external_observations(pievo_cfg, principles, agent_cfg)
    priors = initial_priors(principles)
    experts = train_principle_experts(principles, observations, agent_cfg, pievo_cfg)
    posterior = update_posterior_full_history(principles, priors, experts, observations, agent_cfg, pievo_cfg)
    map_principle = max(posterior, key=posterior.get) if posterior else ""
    total_authority_weight = float(sum(obs.authority_weight for obs in observations))
    out_dir.mkdir(parents=True, exist_ok=True)

    observations_path = out_dir / "active_evidence_pievo_external_observations_used.csv"
    posterior_path = out_dir / "active_evidence_principle_posterior.json"
    summary_path = out_dir / "active_evidence_pievo_bridge_summary.json"
    observation_rows = [obs.row for obs in observations]
    observation_frame = pd.DataFrame(observation_rows)
    for column in OBSERVATION_OUTPUT_COLUMNS:
        if column not in observation_frame.columns:
            observation_frame[column] = ""
    observation_frame.to_csv(observations_path, index=False)
    posterior_path.write_text(json.dumps({key: float(value) for key, value in posterior.items()}, indent=2, ensure_ascii=False), encoding="utf-8")

    accepted_rows = int(external_summary.get("accepted_rows", 0))
    summary = {
        "config_path": str(config_path),
        "external_ledger_path": external_summary.get("ledger_path", ""),
        "target_tg_c": float(agent_cfg.target_tg_c),
        "reward_temperature_c": float(pievo_cfg.reward_temperature_c),
        "allowed_source_types": external_summary.get("allowed_source_types"),
        "require_active_evidence": external_summary.get("require_active_evidence", False),
        "external_input_rows": external_summary.get("input_rows", 0),
        "external_candidate_rows_after_ledger_pass": external_summary.get("candidate_rows_after_ledger_pass", 0),
        "external_candidate_rows_after_source_filter": external_summary.get("candidate_rows_after_source_filter", 0),
        "external_candidate_rows_after_active_filter": external_summary.get("candidate_rows_after_active_filter", 0),
        "external_accepted_rows": accepted_rows,
        "external_rejected_rows": external_summary.get("rejected_rows", 0),
        "external_source_counts": external_summary.get("source_counts", {}),
        "posterior_history_rows": int(len(observations)),
        "total_authority_weight": total_authority_weight,
        "posterior_entropy": float(entropy(posterior)) if posterior else None,
        "map_principle": map_principle,
        "active_evidence_updates_posterior": accepted_rows > 0,
        "bridge_status": "active_evidence_updates_posterior" if accepted_rows > 0 else "no_active_evidence_noop",
        "observations_path": str(observations_path),
        "posterior_path": str(posterior_path),
        "summary_path": str(summary_path),
        "report_path": str(report_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(summary, report_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate active high-authority evidence as a PiEvo posterior input.")
    parser.add_argument("--config", default="configs/pievo_faithful_active_evidence_bridge_smoke.yaml")
    parser.add_argument("--out-dir", default="artifacts/pievo_faithful_active_evidence_bridge_smoke")
    parser.add_argument("--report", default="reports/active_evidence_pievo_bridge.md")
    args = parser.parse_args()
    run_bridge(Path(args.config), Path(args.out_dir), Path(args.report))


if __name__ == "__main__":
    main()
