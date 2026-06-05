from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


AGENTS = {
    "space_agent": "界定搜索空间：官能团、反应兼容性、摩尔比网格。",
    "generator_agent": "生成候选假设：模板、VAE replacement、prompt/RAG、未来 SFT/扩散/流匹配。",
    "rag_generator_agent": "读取 RAG 上下文和 strict strategy feedback，生成 auditable generation records。",
    "predictor_agent": "评估假设：VAE-WVCM model zoo、GNN、uncertainty、OOD。",
    "harness_agent": "硬约束过滤：RDKit、比例、目标窗口、官能团反应兼容性。",
    "feedback_agent": "失败回流：统计 generation ledger 和 Harness rejection，给下一轮生成器约束。",
    "principle_agent": "更新原则：PiEvo full-history posterior、MAP residual anomaly、IDS 选择。",
    "human_review_agent": "人工闭环：审核候选、补工艺条件、决定是否进入真实/高保真 observation ledger。",
}


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def summarize(
    candidate_space: Path,
    closed_loop_history: Path,
    generation_feedback: Path,
    generation_ledger: Path,
    feedback_aware_ledger: Path,
    feedback_aware_observation_ledger: Path,
    feedback_aware_pievo_summary: Path,
) -> dict:
    candidates = pd.read_csv(candidate_space) if candidate_space.exists() else pd.DataFrame()
    history = read_json(closed_loop_history, [])
    feedback = read_json(generation_feedback, {})
    ledger = pd.read_csv(generation_ledger) if generation_ledger.exists() else pd.DataFrame()
    feedback_aware = pd.read_csv(feedback_aware_ledger) if feedback_aware_ledger.exists() else pd.DataFrame()
    feedback_aware_observations = pd.read_csv(feedback_aware_observation_ledger) if feedback_aware_observation_ledger.exists() else pd.DataFrame()
    feedback_aware_pievo = read_json(feedback_aware_pievo_summary, {})
    return {
        "agents": AGENTS,
        "candidate_rows": int(len(candidates)),
        "best_candidates": candidates.head(10).to_dict(orient="records") if not candidates.empty else [],
        "closed_loop_history": history,
        "generation_ledger_rows": int(len(ledger)),
        "generation_harness_pass": int(ledger["harness_pass"].fillna(False).astype(bool).sum()) if not ledger.empty and "harness_pass" in ledger else 0,
        "feedback_aware_llm_rag_rows": int(len(feedback_aware)),
        "feedback_aware_llm_rag_harness_pass": (
            int(feedback_aware["harness_pass"].fillna(False).astype(bool).sum())
            if not feedback_aware.empty and "harness_pass" in feedback_aware
            else 0
        ),
        "feedback_aware_llm_rag_observation_rows": int(len(feedback_aware_observations)),
        "feedback_aware_llm_rag_observation_pass": (
            int(feedback_aware_observations["ledger_pass"].fillna(False).astype(bool).sum())
            if not feedback_aware_observations.empty and "ledger_pass" in feedback_aware_observations
            else 0
        ),
        "feedback_aware_llm_rag_pievo_best_distance_c": feedback_aware_pievo.get("best_selected_target_distance_c"),
        "feedback_aware_llm_rag_pievo_external_rows": feedback_aware_pievo.get("external_observation_summary", {}).get("accepted_rows", 0),
        "generation_feedback": feedback,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-space", default="artifacts/reproduce/discovery/candidate_space_top_scored.csv")
    parser.add_argument("--history", default="artifacts/reproduce/closed_loop/closed_loop_history.json")
    parser.add_argument("--generation-feedback", default="artifacts/trail/generation_feedback_strict/generation_feedback_summary.json")
    parser.add_argument("--generation-ledger", default="artifacts/trail/generation/prompt_records/generation_record_ledger.csv")
    parser.add_argument("--feedback-aware-ledger", default="artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv")
    parser.add_argument("--feedback-aware-observation-ledger", default="artifacts/trail/generation/feedback_aware_llm_rag_observations/generation_observation_ledger.csv")
    parser.add_argument("--feedback-aware-pievo-summary", default="artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke/pievo_faithful_summary.json")
    parser.add_argument("--out", default="artifacts/trail/workflow/multi_agent_summary.json")
    args = parser.parse_args()
    result = summarize(
        Path(args.candidate_space),
        Path(args.history),
        Path(args.generation_feedback),
        Path(args.generation_ledger),
        Path(args.feedback_aware_ledger),
        Path(args.feedback_aware_observation_ledger),
        Path(args.feedback_aware_pievo_summary),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
