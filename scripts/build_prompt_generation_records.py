from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

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
    digest = " || ".join(text.replace("\n", " ")[:180] for _, text, _ in retrieved)
    return refs, digest


def selected_record(row: pd.Series, generation_id: str, query: str, refs: str, digest: str, target_tg_c: float, target_window_c: float) -> dict[str, object]:
    smiles = f"{row['smiles_a']}|{row['smiles_b']}"
    ratios = f"{float(row['ratio_a']):.5f}:{float(row['ratio_b']):.5f}"
    prompt = (
        f"Target Tg {target_tg_c:.1f} C within {target_window_c:.1f} C. "
        "Use retrieved SMP principles to propose a small-molecule formulation with explicit functional-group compatibility."
    )
    return {
        "generation_id": generation_id,
        "strategy": "llm_rag_principle_generation",
        "stage": "harnessed",
        "target_tg_c": target_tg_c,
        "target_window_c": target_window_c,
        "candidate_smiles": smiles,
        "candidate_ratios": ratios,
        "source_context": "rag_prompt_smoke_from_selected_candidates",
        "generator_id": "prompt_contract_smoke_v1",
        "generation_time": "2026-06-06",
        "prompt_id": "smp_rag_formula_contract_v1",
        "prompt_text": prompt,
        "prompt_hash": prompt_hash(prompt),
        "rag_query": query,
        "rag_context_refs": refs,
        "rag_context_digest": digest,
        "principle_hypothesis": "Rigid aromatic compatible functional groups should keep the target window reachable.",
        "functional_group_plan": f"{row['groups_a']} + {row['groups_b']}",
        "candidate_json": json.dumps({"smiles": smiles.split("|"), "ratios": ratios.split(":")}, ensure_ascii=False),
        "compatibility_reasons": row["compatibility_reason"],
        "predicted_tg_mean_c": float(row["predicted_tg"]),
        "predicted_tg_sigma_c": "",
        "ood_penalty": "",
        "pievo_round": 0,
        "selected_by_ids": False,
        "harness_failure_reason": "",
        "review_status": "needs_review",
        "notes": "Smoke record that emulates an LLM/RAG proposal but uses an already scored candidate for reproducibility.",
    }


def replacement_record(row: pd.Series, generation_id: str, query: str, refs: str, digest: str, target_tg_c: float, target_window_c: float) -> dict[str, object]:
    prompt = (
        f"Target Tg {target_tg_c:.1f} C. Replace one component while preserving a compatible reaction pair; "
        "report the original side, replacement SMILES, and expected reaction evidence."
    )
    return {
        "generation_id": generation_id,
        "strategy": "functional_group_replacement",
        "stage": "harnessed",
        "target_tg_c": target_tg_c,
        "target_window_c": target_window_c,
        "candidate_smiles": row["smiles"],
        "candidate_ratios": row["ratios"],
        "source_context": "vae_replacement_with_prompt_audit",
        "generator_id": "trail/generation/vae_replacement_strategy.py",
        "generation_time": "2026-06-06",
        "prompt_id": "replacement_audit_contract_v1",
        "prompt_text": prompt,
        "prompt_hash": prompt_hash(prompt),
        "rag_query": query,
        "rag_context_refs": refs,
        "rag_context_digest": digest,
        "principle_hypothesis": "Functional-group-preserving local replacement can preserve reactivity while moving Tg.",
        "functional_group_plan": str(row["groups"]),
        "candidate_json": json.dumps({"smiles": str(row["smiles"]).split("|"), "ratios": str(row["ratios"]).split(":")}, ensure_ascii=False),
        "compatibility_reasons": row["compatibility_reasons"],
        "predicted_tg_mean_c": float(row["predicted_tg_mean_c"]),
        "predicted_tg_sigma_c": float(row["predicted_tg_sigma_c"]),
        "ood_penalty": float(row["ood_penalty"]),
        "pievo_round": 0,
        "selected_by_ids": False,
        "harness_failure_reason": "",
        "review_status": "needs_review",
        "notes": f"Replacement proposal index {int(row['proposal_index'])}; side={row['replace_side']}.",
    }


def failed_draft_record(row: pd.Series, generation_id: str, query: str, refs: str, digest: str, target_tg_c: float, target_window_c: float) -> dict[str, object]:
    prompt = (
        f"Target Tg {target_tg_c:.1f} C. Draft a new SMILES-level replacement from RAG context. "
        "Do not assume chemistry is valid until Harness checks it."
    )
    return {
        "generation_id": generation_id,
        "strategy": "llm_smiles_generation",
        "stage": "draft",
        "target_tg_c": target_tg_c,
        "target_window_c": target_window_c,
        "candidate_smiles": f"{row['original_smiles']}|{row['replacement_smiles']}",
        "candidate_ratios": "0.50000:0.50000",
        "source_context": "rag_prompt_smoke_failure_case",
        "generator_id": "prompt_contract_smoke_v1",
        "generation_time": "2026-06-06",
        "prompt_id": "smp_rag_smiles_draft_contract_v1",
        "prompt_text": prompt,
        "prompt_hash": prompt_hash(prompt),
        "rag_query": query,
        "rag_context_refs": refs,
        "rag_context_digest": digest,
        "principle_hypothesis": "Shared groups alone are insufficient; reaction pair and ratio constraints must still be checked.",
        "functional_group_plan": str(row["shared_groups"]),
        "candidate_json": json.dumps({"smiles": [row["original_smiles"], row["replacement_smiles"]], "ratios": [0.5, 0.5]}, ensure_ascii=False),
        "compatibility_reasons": "",
        "predicted_tg_mean_c": "",
        "predicted_tg_sigma_c": "",
        "ood_penalty": "",
        "pievo_round": 0,
        "selected_by_ids": False,
        "harness_failure_reason": row["reason"],
        "review_status": "rejected_by_harness",
        "notes": "Intentional failed draft to prove that prompt/RAG records preserve Harness rejection feedback.",
    }


def write_report(ledger: pd.DataFrame, summary: dict[str, object], report_path: Path, packet_path: Path) -> None:
    lines = [
        "# Generation Record Schema Smoke",
        "",
        "本文档记录 TODO 中“LLM / prompt / RAG / Harness 约束控制”的落地状态。当前没有调用外部 LLM；本 smoke 用可复现的候选模拟 LLM/RAG 输出，目的是固定输入输出契约和失败回流字段。",
        "",
        "## Outputs",
        "",
        f"- Prompt/RAG packet: `{packet_path}`",
        "- Input records: `artifacts/trail/generation/prompt_records/prompt_generation_records_input.csv`",
        "- Ledger: `artifacts/trail/generation/prompt_records/generation_record_ledger.csv`",
        "- Summary: `artifacts/trail/generation/prompt_records/generation_record_summary.json`",
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
            "## Strategy Counts",
            "",
            "| strategy | rows |",
            "| --- | ---: |",
        ]
    )
    for strategy, count in summary.get("strategy_counts", {}).items():
        lines.append(f"| {strategy} | {count} |")
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
            "- `generation_record_schema.yaml` 现在把 prompt、RAG refs、候选 JSON、预测值、Harness 判定和 PiEvo 选择状态放在同一个 ledger 契约里。",
            "- `llm_smiles_generation` 的失败样例说明：LLM/RAG 草案即使 SMILES 有效，也可能因为缺预测、缺化学兼容证据或反应/比例约束失败而不能进入推荐。",
            "- 后续真正接入 LLM、SFT、扩散或流匹配时，应先写 generation record，再进入 predictor/Harness/PiEvo。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_packet(records: list[dict[str, object]], packet_path: Path) -> None:
    lines = [
        "# Prompt/RAG Generation Packet",
        "",
        "This packet is a reproducible stand-in for a future LLM call. It records the prompts, retrieved context refs, and candidate payloads that must be preserved when a real model is connected.",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"## {record['generation_id']}",
                "",
                f"- strategy: `{record['strategy']}`",
                f"- prompt_id: `{record['prompt_id']}`",
                f"- prompt_hash: `{record['prompt_hash']}`",
                f"- rag_query: `{record['rag_query']}`",
                f"- rag_context_refs: `{record['rag_context_refs']}`",
                "",
                "Prompt:",
                "",
                "```text",
                str(record["prompt_text"]),
                "```",
                "",
                "Candidate JSON:",
                "",
                "```json",
                str(record["candidate_json"]),
                "```",
                "",
            ]
        )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build reproducible prompt/RAG generation records and import them into a ledger.")
    parser.add_argument("--selected", default="artifacts/reproduce/discovery/selected_candidates.csv")
    parser.add_argument("--replacement-scored", default="artifacts/trail/generation/replacement_eval/replacement_proposals_scored.csv")
    parser.add_argument("--replacement-rejections", default="artifacts/trail/generation/replacement_eval/replacement_proposal_rejections.csv")
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--out-dir", default="artifacts/trail/generation/prompt_records")
    parser.add_argument("--report", default="reports/generation_record_schema_smoke.md")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    query = f"SMP target Tg {args.target_tg_c:.0f} C functional group compatibility rigid aromatic epoxy amine cyanate ester Harness"
    docs = [
        Path("docs/generation_strategy_and_harness.md"),
        Path("docs/smp_knowledge_base_and_ontology.md"),
        Path("docs/pievo_faithful_smp.md"),
        Path("trail/knowledge/smp_prior_knowledge.yaml"),
    ]
    refs, digest = context_bundle(query, docs, top_k=4)

    selected = pd.read_csv(args.selected).head(2)
    replacement = pd.read_csv(args.replacement_scored)
    replacement_pass = replacement[replacement["harness_pass"]].sort_values(["target_distance_c", "ood_penalty"]).head(1)
    rejections = pd.read_csv(args.replacement_rejections).head(1)

    records: list[dict[str, object]] = []
    for idx, (_, row) in enumerate(selected.iterrows(), start=1):
        records.append(selected_record(row, f"prompt_rag_selected_{idx:03d}", query, refs, digest, args.target_tg_c, args.target_window_c))
    if not replacement_pass.empty:
        records.append(replacement_record(replacement_pass.iloc[0], "prompt_rag_replacement_001", query, refs, digest, args.target_tg_c, args.target_window_c))
    if not rejections.empty:
        records.append(failed_draft_record(rejections.iloc[0], "prompt_rag_failed_001", query, refs, digest, args.target_tg_c, args.target_window_c))

    input_path = out_dir / "prompt_generation_records_input.csv"
    ledger_path = out_dir / "generation_record_ledger.csv"
    summary_path = out_dir / "generation_record_summary.json"
    packet_path = out_dir / "prompt_rag_packet.md"
    pd.DataFrame(records).to_csv(input_path, index=False)
    ledger, summary = import_generation_records(input_path, Path("trail/generation/generation_record_schema.yaml"), args.target_window_c)
    ledger.to_csv(ledger_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_packet(records, packet_path)
    write_report(ledger, summary, Path(args.report), packet_path)


if __name__ == "__main__":
    main()
