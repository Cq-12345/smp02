from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ENTRIES = [
    {
        "task_id": "variable_tg_targets",
        "todo_area": "真实 Tg 温度不固定",
        "status": "implemented",
        "evidence_paths": [
            "reports/variable_target_tg_analysis.md",
            "reports/pievo_target_sweep_smoke.md",
            "reports/feedback_guided_replacement_target_sweep.md",
        ],
        "next_action": "用真实/高保真 observation 做正式多目标 posterior sweep",
    },
    {
        "task_id": "commodity_polymer_hypergraph_representation",
        "todo_area": "真实商品级组分/聚合物/超图表示",
        "status": "deferred_by_user",
        "evidence_paths": ["ForYouGoal/20260606_01/TODO.md"],
        "next_action": "等待用户恢复该方向；当前继续使用单一小分子 SMILES/MoleCode",
    },
    {
        "task_id": "knowledge_prior_ontology",
        "todo_area": "知识库/先验库/本体",
        "status": "implemented_needs_more_literature_extraction",
        "evidence_paths": [
            "trail/knowledge/smp_prior_knowledge.yaml",
            "trail/knowledge/ontology.yaml",
            "docs/smp_knowledge_base_and_ontology.md",
            "reports/knowledge_provenance_process_update.md",
        ],
        "next_action": "从更多 SMP 文献抽取固化程序和 process fields",
    },
    {
        "task_id": "candidate_component_dataset",
        "todo_area": "候选组分数据集/来源/官能团分类",
        "status": "implemented",
        "evidence_paths": [
            "trail/candidates/source_registry.yaml",
            "artifacts/trail/candidates_expanded/component_inventory.csv",
            "reports/candidate_source_audit_expanded.md",
            "reports/sparse_candidate_template_expansion.md",
        ],
        "next_action": "用真实/高保真 evidence 调整 source authority",
    },
    {
        "task_id": "predictor_model_zoo",
        "todo_area": "预测模型/CNN-SVR-RF/GNN/model zoo",
        "status": "implemented",
        "evidence_paths": [
            "reports/model_selection_analysis.md",
            "reports/predictor_model_selection_registry.md",
            "reports/predictor_ensemble_disagreement.md",
            "reports/gnn_architecture_smoke_leaderboard.md",
            "reports/gnn_global_feature_smoke.md",
        ],
        "next_action": "更长 GNN 训练，并评估是否纳入 ensemble/OOD 审计",
    },
    {
        "task_id": "generation_models",
        "todo_area": "生成模型/VAE/LLM/RAG/SFT/diffusion/flow/Harness",
        "status": "implemented_smoke_needs_real_generator_outputs",
        "evidence_paths": [
            "reports/vae_latent_local_search_evaluation.md",
            "reports/feedback_aware_llm_rag_agent.md",
            "reports/sft_candidate_generator_dry_run.md",
            "reports/diffusion_flow_candidate_generator_dry_run.md",
            "reports/diffusion_flow_trained_generator.md",
            "docs/generation_strategy_and_harness.md",
        ],
        "next_action": "接入真实外部 LLM/SFT 或有效 SMILES decoder；输出仍走 ledger/Harness/PiEvo",
    },
    {
        "task_id": "pievo_faithful_closed_loop",
        "todo_area": "PiEvo-faithful/原则 posterior/IDS/full-history",
        "status": "implemented",
        "evidence_paths": [
            "src/smp02/pievo_faithful.py",
            "docs/pievo_faithful_smp.md",
            "artifacts/pievo_faithful_ensemble_guard_195_smoke/pievo_faithful_summary.json",
            "reports/pievo_ensemble_disagreement_guard_smoke.md",
        ],
        "next_action": "用高权重真实/高保真 evidence 检验 posterior shift",
    },
    {
        "task_id": "human_real_experiment_loop",
        "todo_area": "人工闭环/真实实验结果迭代优化",
        "status": "implemented_blocked_by_human_or_high_fidelity_evidence",
        "evidence_paths": [
            "reports/human_experiment_review_queue.md",
            "reports/process_approval_intake.md",
            "reports/high_fidelity_protocol_packet.md",
            "reports/validation_dependency_graph.md",
            "reports/active_high_authority_observation_ledger.md",
        ],
        "next_action": "先审核 12 行 process approval，再执行高保真/真实结果 intake",
    },
    {
        "task_id": "workflow_agent_summary",
        "todo_area": "多智能体 workflow/服务化总览",
        "status": "implemented",
        "evidence_paths": [
            "trail/workflow/multi_agent_workflow.py",
            "artifacts/trail/workflow/multi_agent_summary.json",
            "docs/closed_loop_workflow.md",
        ],
        "next_action": "后续把真实 provider/真实实验结果接入同一 summary",
    },
    {
        "task_id": "rl_strategy_policy",
        "todo_area": "RL/策略层预算分配",
        "status": "implemented_surrogate_backed",
        "evidence_paths": [
            "reports/generation_strategy_bandit_policy.md",
            "reports/target_conditioned_generation_strategy_policy.md",
            "artifacts/trail/generation_strategy_policy/generation_strategy_bandit_summary.json",
        ],
        "next_action": "高权重 evidence 进入后，比较 posterior shift 再调预算",
    },
]


def evidence_exists(root: Path, evidence_paths: list[str]) -> tuple[int, list[str]]:
    missing = [path for path in evidence_paths if not (root / path).exists()]
    return len(evidence_paths) - len(missing), missing


def build_audit(root: Path, entries: list[dict[str, Any]] | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = []
    for entry in entries or DEFAULT_ENTRIES:
        paths = list(entry["evidence_paths"])
        present_count, missing = evidence_exists(root, paths)
        status = str(entry["status"])
        rows.append(
            {
                "task_id": entry["task_id"],
                "todo_area": entry["todo_area"],
                "status": status,
                "deferred": status == "deferred_by_user",
                "needs_real_or_high_fidelity_evidence": "real" in status or "high_fidelity" in status or "human" in status,
                "evidence_paths": ";".join(paths),
                "evidence_present_count": present_count,
                "evidence_expected_count": len(paths),
                "all_evidence_present": present_count == len(paths),
                "missing_evidence_paths": ";".join(missing),
                "next_action": entry["next_action"],
            }
        )
    frame = pd.DataFrame(rows)
    non_deferred = frame[~frame["deferred"].astype(bool)] if not frame.empty else pd.DataFrame()
    missing = frame[~frame["all_evidence_present"].astype(bool)] if not frame.empty else pd.DataFrame()
    needs_evidence = frame[frame["needs_real_or_high_fidelity_evidence"].astype(bool)] if not frame.empty else pd.DataFrame()
    summary = {
        "audit_rows": int(len(frame)),
        "implemented_rows": int(frame["status"].astype(str).str.startswith("implemented").sum()) if not frame.empty else 0,
        "deferred_rows": int(frame["deferred"].sum()) if not frame.empty else 0,
        "needs_real_or_high_fidelity_evidence_rows": int(len(needs_evidence)),
        "all_evidence_present_rows": int(frame["all_evidence_present"].sum()) if not frame.empty else 0,
        "missing_evidence_rows": int(len(missing)),
        "non_deferred_all_evidence_present": bool(non_deferred["all_evidence_present"].all()) if not non_deferred.empty else True,
        "primary_open_blocker": "human_process_approval_and_real_or_high_fidelity_observation",
        "deferred_task_ids": frame.loc[frame["deferred"], "task_id"].tolist() if not frame.empty else [],
        "needs_evidence_task_ids": needs_evidence["task_id"].tolist() if not needs_evidence.empty else [],
        "missing_evidence_task_ids": missing["task_id"].tolist() if not missing.empty else [],
        "evidence_level": "todo_completion_audit_not_observation",
    }
    return frame, summary


def write_report(frame: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TODO Completion Audit",
        "",
        "本文档把 TODO 的非暂缓任务、证据文件和剩余边界结构化。它不产生 Tg observation，也不代表真实实验已经完成。",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, list):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Task Matrix",
            "",
            "| task | status | evidence | next action |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for _, row in frame.iterrows():
        lines.append(
            f"| {row['todo_area']} | {row['status']} | "
            f"{int(row['evidence_present_count'])}/{int(row['evidence_expected_count'])} | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `deferred_by_user` 只对应商品级/聚合物/超图表示；当前按用户要求不做。",
            "- `implemented_*` 表示已有代码、artifact 或文档证据；其中 `needs_real_or_high_fidelity_evidence` 说明下一步需要人工审批、真实实验或高保真结果，而不能由脚本伪造。",
            "- 当前主阻塞不是 surrogate 生成失败，而是高权重证据链等待 process approval 和真实/高保真 result intake。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit TODO completion evidence without changing model state.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-dir", default="artifacts/trail/workflow")
    parser.add_argument("--report", default="reports/todo_completion_audit.md")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame, summary = build_audit(root)
    audit_path = out_dir / "todo_completion_audit.csv"
    summary_path = out_dir / "todo_completion_audit_summary.json"
    frame.to_csv(audit_path, index=False)
    summary = {
        **summary,
        "audit_path": str(audit_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(frame, summary, Path(args.report))


if __name__ == "__main__":
    main()
