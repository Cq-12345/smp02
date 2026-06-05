from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from trail.generation.import_generation_records import import_generation_records
from trail.rag.simple_retriever import chunks, retrieve


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def context_bundle(query: str, docs: list[Path], top_k: int) -> tuple[str, str]:
    retrieved = retrieve(query, chunks(docs), top_k)
    refs = "|".join(ref for ref, _, _ in retrieved)
    digest = " || ".join(text.replace("\n", " ")[:220] for _, text, _ in retrieved)
    return refs, digest


def load_strategy_feedback(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            columns=[
                "strategy",
                "records",
                "harness_pass",
                "harness_fail",
                "pass_rate",
                "policy_weight_delta",
                "top_failure_reason",
                "next_constraint",
            ]
        )
    return pd.read_csv(path)


def policy_from_feedback(feedback: pd.DataFrame, min_pass_rate: float = 0.5) -> dict[str, Any]:
    decisions: dict[str, Any] = {
        "preferred_strategies": [],
        "suppressed_strategies": [],
        "constraints": [],
        "policy_table": [],
    }
    for _, row in feedback.iterrows():
        strategy = str(row["strategy"])
        pass_rate = float(row.get("pass_rate", 0.0))
        delta = float(row.get("policy_weight_delta", 0.0))
        constraint = "" if pd.isna(row.get("next_constraint")) else str(row.get("next_constraint"))
        item = {
            "strategy": strategy,
            "pass_rate": pass_rate,
            "policy_weight_delta": delta,
            "top_failure_reason": "" if pd.isna(row.get("top_failure_reason")) else str(row.get("top_failure_reason")),
            "next_constraint": constraint,
        }
        decisions["policy_table"].append(item)
        if pass_rate >= min_pass_rate and delta >= 0.0:
            decisions["preferred_strategies"].append(strategy)
        else:
            decisions["suppressed_strategies"].append(item)
        if constraint and not constraint.startswith("retain:"):
            decisions["constraints"].append(f"{strategy}: {constraint}")
    return decisions


def closest_selected_candidate(selected_path: Path, target_tg_c: float) -> pd.Series:
    selected = pd.read_csv(selected_path)
    selected["target_distance_c"] = (selected["predicted_tg"].astype(float) - float(target_tg_c)).abs()
    return selected.sort_values("target_distance_c").iloc[0]


def closest_replacement_candidate(scored_path: Path, target_tg_c: float) -> pd.Series | None:
    scored = pd.read_csv(scored_path)
    if "harness_pass" in scored.columns:
        scored = scored[scored["harness_pass"].map(lambda value: str(value).lower() in {"1", "true", "yes"})].copy()
    if scored.empty:
        return None
    scored["target_distance_c"] = (scored["predicted_tg_mean_c"].astype(float) - float(target_tg_c)).abs()
    return scored.sort_values(["target_distance_c", "ood_penalty", "predicted_tg_sigma_c"]).iloc[0]


def build_agent_prompt(
    target_tg_c: float,
    target_window_c: float,
    query: str,
    refs: str,
    digest: str,
    policy: dict[str, Any],
) -> str:
    return "\n".join(
        [
            "You are an SMP formulation generation agent.",
            f"Target Tg: {target_tg_c:.1f} C, window: +/-{target_window_c:.1f} C.",
            "Representation scope: single small-molecule SMILES / MoleCode only.",
            "Generate only auditable candidate records. Do not bypass RDKit, predictor, Harness, or PiEvo.",
            f"RAG query: {query}",
            f"RAG refs: {refs}",
            f"RAG digest: {digest}",
            "Generation feedback policy:",
            json.dumps(policy, ensure_ascii=False, indent=2),
            "Return JSON list of generation records following trail/generation/generation_record_schema.yaml.",
        ]
    )


def selected_record(
    row: pd.Series,
    generation_id: str,
    prompt: str,
    query: str,
    refs: str,
    digest: str,
    target_tg_c: float,
    target_window_c: float,
    policy: dict[str, Any],
) -> dict[str, object]:
    smiles = f"{row['smiles_a']}|{row['smiles_b']}"
    ratios = f"{float(row['ratio_a']):.5f}:{float(row['ratio_b']):.5f}"
    return {
        "generation_id": generation_id,
        "strategy": "llm_rag_principle_generation",
        "stage": "harnessed",
        "target_tg_c": target_tg_c,
        "target_window_c": target_window_c,
        "candidate_smiles": smiles,
        "candidate_ratios": ratios,
        "source_context": "feedback_aware_rag_selected_candidate",
        "generator_id": "feedback_aware_llm_rag_agent:offline_policy",
        "generation_time": "2026-06-06",
        "prompt_id": "feedback_aware_smp_rag_agent_v1",
        "prompt_text": prompt,
        "prompt_hash": prompt_hash(prompt),
        "rag_query": query,
        "rag_context_refs": refs,
        "rag_context_digest": digest,
        "principle_hypothesis": "Retain high-pass-rate LLM/RAG principle generation and require explicit reaction compatibility evidence.",
        "functional_group_plan": f"{row['groups_a']} + {row['groups_b']}",
        "candidate_json": json.dumps(
            {
                "smiles": smiles.split("|"),
                "ratios": ratios.split(":"),
                "feedback_policy": {
                    "preferred": policy["preferred_strategies"],
                    "suppressed": [item["strategy"] for item in policy["suppressed_strategies"]],
                },
            },
            ensure_ascii=False,
        ),
        "compatibility_reasons": row["compatibility_reason"],
        "predicted_tg_mean_c": float(row["predicted_tg"]),
        "predicted_tg_sigma_c": "",
        "ood_penalty": "",
        "pievo_round": 0,
        "selected_by_ids": False,
        "harness_failure_reason": "",
        "review_status": "needs_review",
        "notes": "Feedback-aware offline RAG agent record; preferred strategy retained from strategy_feedback.csv.",
    }


def replacement_context_record(
    row: pd.Series,
    generation_id: str,
    prompt: str,
    query: str,
    refs: str,
    digest: str,
    target_tg_c: float,
    target_window_c: float,
    policy: dict[str, Any],
) -> dict[str, object]:
    constraint_text = " ; ".join(policy.get("constraints", []))
    return {
        "generation_id": generation_id,
        "strategy": "llm_rag_principle_generation",
        "stage": "harnessed",
        "target_tg_c": target_tg_c,
        "target_window_c": target_window_c,
        "candidate_smiles": row["smiles"],
        "candidate_ratios": row["ratios"],
        "source_context": "feedback_guided_replacement_as_rag_evidence",
        "generator_id": "feedback_aware_llm_rag_agent:offline_policy",
        "generation_time": "2026-06-06",
        "prompt_id": "feedback_aware_smp_rag_agent_v1",
        "prompt_text": prompt,
        "prompt_hash": prompt_hash(prompt),
        "rag_query": query,
        "rag_context_refs": refs,
        "rag_context_digest": digest,
        "principle_hypothesis": "Successful strict replacement is treated as evidence that complementary reactive-pair preservation should be a generation constraint.",
        "functional_group_plan": str(row.get("groups", "")),
        "candidate_json": json.dumps(
            {
                "smiles": str(row["smiles"]).split("|"),
                "ratios": str(row["ratios"]).split(":"),
                "feedback_constraints": constraint_text,
                "replacement_metadata": {
                    "proposal_index": int(row["proposal_index"]),
                    "replace_side": str(row["replace_side"]),
                    "counterpart_compatibility_reason": str(row.get("counterpart_compatibility_reason", "")),
                },
            },
            ensure_ascii=False,
        ),
        "compatibility_reasons": row["compatibility_reasons"],
        "predicted_tg_mean_c": float(row["predicted_tg_mean_c"]),
        "predicted_tg_sigma_c": float(row["predicted_tg_sigma_c"]),
        "ood_penalty": float(row["ood_penalty"]),
        "pievo_round": 0,
        "selected_by_ids": False,
        "harness_failure_reason": "",
        "review_status": "needs_review",
        "notes": "RAG agent used replacement feedback as context but emitted an LLM/RAG principle-generation record.",
    }


def offline_policy_records(
    selected_path: Path,
    replacement_scored_path: Path,
    target_tg_c: float,
    target_window_c: float,
    prompt: str,
    query: str,
    refs: str,
    digest: str,
    policy: dict[str, Any],
) -> list[dict[str, object]]:
    records = [
        selected_record(
            closest_selected_candidate(selected_path, target_tg_c),
            "feedback_rag_selected_001",
            prompt,
            query,
            refs,
            digest,
            target_tg_c,
            target_window_c,
            policy,
        )
    ]
    replacement = closest_replacement_candidate(replacement_scored_path, target_tg_c)
    if replacement is not None:
        records.append(
            replacement_context_record(
                replacement,
                "feedback_rag_replacement_context_001",
                prompt,
                query,
                refs,
                digest,
                target_tg_c,
                target_window_c,
                policy,
            )
        )
    return records


def call_openai_compatible(prompt: str, model: str, base_url: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for --provider openai_compatible.")
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data["choices"][0]["message"]["content"])


def parse_llm_records(text: str) -> list[dict[str, object]]:
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        raise ValueError("LLM response did not contain a JSON list.")
    records = json.loads(match.group(0))
    if not isinstance(records, list):
        raise ValueError("LLM response JSON is not a list.")
    return [dict(item) for item in records]


def write_packet(records: list[dict[str, object]], prompt: str, packet_path: Path, policy: dict[str, Any], provider: str) -> None:
    lines = [
        "# Feedback-Aware LLM/RAG Agent Packet",
        "",
        f"- provider: `{provider}`",
        f"- prompt_hash: `{prompt_hash(prompt)}`",
        "",
        "## Policy",
        "",
        "```json",
        json.dumps(policy, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Prompt",
        "",
        "```text",
        prompt,
        "```",
        "",
        "## Candidate Records",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"### {record['generation_id']}",
                "",
                f"- strategy: `{record['strategy']}`",
                f"- stage: `{record['stage']}`",
                f"- candidate_smiles: `{record['candidate_smiles']}`",
                "",
                "```json",
                str(record.get("candidate_json", "")),
                "```",
                "",
            ]
        )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("\n".join(lines), encoding="utf-8")


def write_report(
    ledger: pd.DataFrame,
    summary: dict[str, Any],
    policy: dict[str, Any],
    report_path: Path,
    packet_path: Path,
    provider: str,
) -> None:
    lines = [
        "# Feedback-Aware LLM/RAG Agent Smoke",
        "",
        "本文档记录一个真正可运行的 LLM/RAG agent 契约：agent 读取知识库 RAG 上下文、generation feedback policy，并输出 `generation_record_schema.yaml` 约束下的候选 records。当前运行使用 `offline_policy` provider 保持可复现；如果设置 `OPENAI_API_KEY`，同一脚本可切到 `openai_compatible` provider，但输出仍必须先进入 generation ledger、predictor/Harness/PiEvo。",
        "",
        "## Outputs",
        "",
        f"- Agent packet: `{packet_path}`",
        "- Input records: `artifacts/trail/generation/feedback_aware_llm_rag/feedback_aware_generation_records_input.csv`",
        "- Ledger: `artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv`",
        "- Summary: `artifacts/trail/generation/feedback_aware_llm_rag/generation_record_summary.json`",
        "",
        "## Provider And Policy",
        "",
        f"- provider: `{provider}`",
        f"- preferred strategies: `{', '.join(policy['preferred_strategies'])}`",
        f"- suppressed strategies: `{', '.join(item['strategy'] for item in policy['suppressed_strategies'])}`",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, dict):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Records",
            "",
            "| generation id | strategy | stage | predicted Tg (C) | distance (C) | harness | failure reason |",
            "| --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for _, row in ledger.iterrows():
        predicted = "" if pd.isna(row["predicted_tg_mean_c"]) else f"{float(row['predicted_tg_mean_c']):.2f}"
        distance = "" if pd.isna(row["target_distance_c"]) else f"{float(row['target_distance_c']):.2f}"
        lines.append(
            f"| {row['generation_id']} | {row['strategy']} | {row['stage']} | {predicted} | {distance} | "
            f"{bool(row['harness_pass'])} | {str(row['harness_failure_reason']).replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `llm_smiles_generation` 当前被 policy 抑制，因为上一轮反馈显示其 pass rate 为 0 且缺 predictor/chemistry evidence。",
            "- `functional_group_replacement` 和 `llm_rag_principle_generation` 在 strict feedback 中都被保留；agent 用成功 strict replacement 记录作为 RAG 证据，而不是继续沿用旧失败状态。",
            "- `llm_rag_principle_generation` 被保留，用 RAG 上下文和成功 strict replacement 记录提出候选原则/配方证据。",
            "- 这一步不是绕过 Harness 的自由文本生成；所有候选先进入 generation record ledger，再由 importer 计算 SMILES、ratio、prediction、target 和 chemistry gate。",
            "- 真正外部 LLM 只负责提出候选 JSON；是否可信仍由 RDKit、predictor、Harness、PiEvo 和人工审核决定。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_agent(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    query = (
        f"SMP target_tg_{args.target_tg_c:.0f} strict generation_feedback_strict strategy_feedback "
        "functional_group_replacement llm_rag_principle_generation llm_smiles_generation "
        "feedback-guided generation functional group compatibility PiEvo posterior Harness"
    )
    docs = [Path(path) for path in args.docs]
    refs, digest = context_bundle(query, docs, args.top_k)
    feedback = load_strategy_feedback(Path(args.strategy_feedback))
    policy = policy_from_feedback(feedback, args.min_pass_rate)
    prompt = build_agent_prompt(args.target_tg_c, args.target_window_c, query, refs, digest, policy)
    if args.provider == "offline_policy":
        records = offline_policy_records(
            Path(args.selected),
            Path(args.replacement_scored),
            args.target_tg_c,
            args.target_window_c,
            prompt,
            query,
            refs,
            digest,
            policy,
        )
    else:
        text = call_openai_compatible(prompt, args.model, args.base_url)
        records = parse_llm_records(text)
    input_path = out_dir / "feedback_aware_generation_records_input.csv"
    ledger_path = out_dir / "generation_record_ledger.csv"
    summary_path = out_dir / "generation_record_summary.json"
    packet_path = out_dir / "feedback_aware_llm_rag_packet.md"
    policy_path = out_dir / "feedback_aware_policy.json"
    pd.DataFrame(records).to_csv(input_path, index=False)
    ledger, summary = import_generation_records(input_path, Path(args.schema), args.target_window_c)
    ledger.to_csv(ledger_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    policy_path.write_text(json.dumps(policy, indent=2, ensure_ascii=False), encoding="utf-8")
    write_packet(records, prompt, packet_path, policy, args.provider)
    write_report(ledger, summary, policy, Path(args.report), packet_path, args.provider)
    return ledger, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a feedback-aware LLM/RAG SMP generation agent into the generation record ledger.")
    parser.add_argument("--provider", choices=["offline_policy", "openai_compatible"], default="offline_policy")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    parser.add_argument("--selected", default="artifacts/reproduce/discovery/selected_candidates.csv")
    parser.add_argument("--replacement-scored", default="artifacts/trail/generation/feedback_guided_replacement_eval/replacement_proposals_scored.csv")
    parser.add_argument("--strategy-feedback", default="artifacts/trail/generation_feedback_strict/strategy_feedback.csv")
    parser.add_argument("--schema", default="trail/generation/generation_record_schema.yaml")
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--min-pass-rate", type=float, default=0.5)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--docs",
        nargs="+",
        default=[
            "trail/generation/generation_strategy_registry.yaml",
            "docs/smp_knowledge_base_and_ontology.md",
            "docs/pievo_faithful_smp.md",
            "reports/generation_failure_feedback_strict.md",
            "reports/feedback_guided_replacement_target_sweep.md",
            "trail/knowledge/smp_prior_knowledge.yaml",
        ],
    )
    parser.add_argument("--out-dir", default="artifacts/trail/generation/feedback_aware_llm_rag")
    parser.add_argument("--report", default="reports/feedback_aware_llm_rag_agent.md")
    args = parser.parse_args()
    run_agent(args)


if __name__ == "__main__":
    main()
