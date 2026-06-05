from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from scripts.run_sft_candidate_generator_dry_run import run_dry_run


def sft_line(generation_id: str, split: str, smiles: str, ratios: str, predicted: float) -> str:
    payload = {
        "strategy": "llm_rag_principle_generation",
        "stage": "harnessed",
        "target_tg_c": 195.0,
        "target_window_c": 5.0,
        "candidate_smiles": smiles,
        "candidate_ratios": ratios,
        "compatibility_reasons": "amine-alcohol smoke compatibility",
        "principle_hypothesis": "unit-test principle",
        "functional_group_plan": "unit-test groups",
        "predicted_tg_mean_c": predicted,
        "predicted_tg_sigma_c": 1.0,
        "ood_penalty": 0.1,
        "review_status": "needs_review",
    }
    return json.dumps(
        {
            "messages": [
                {"role": "system", "content": "Generate auditable records."},
                {
                    "role": "user",
                    "content": "Target Tg: 195.0 C\nRAG refs: unit-ref\nRAG digest: unit digest\nSource context: unit",
                },
                {"role": "assistant", "content": json.dumps(payload, sort_keys=True)},
            ],
            "metadata": {
                "generation_id": generation_id,
                "strategy": "llm_rag_principle_generation",
                "source_ledger": "unit.csv",
                "target_distance_c": abs(predicted - 195.0),
                "generation_reward": 1.0,
                "split": split,
            },
        }
    )


def test_sft_candidate_generator_dry_run_writes_harnessed_records(tmp_path: Path) -> None:
    sft_jsonl = tmp_path / "sft.jsonl"
    sft_jsonl.write_text(
        "\n".join(
            [
                sft_line("train-1", "train", "CCO|NCC", "0.50000:0.50000", 195.5),
                sft_line("train-2", "train", "CCN|OCC", "0.40000:0.60000", 196.0),
                sft_line("eval-1", "eval", "CCO|NCC", "0.50000:0.50000", 195.2),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    ledger, summary = run_dry_run(
        Namespace(
            sft_jsonl=str(sft_jsonl),
            max_records=2,
            target_tg_c=195.0,
            target_window_c=5.0,
            generation_time="2026-06-06",
            reward_temperature_c=5.0,
            schema="trail/generation/generation_record_schema.yaml",
            out_dir=str(tmp_path / "out"),
            report=str(tmp_path / "report.md"),
        )
    )

    assert summary["generator_mode"] == "prototype_replay_not_weight_update"
    assert summary["generated_records"] == 2
    assert summary["harness_pass_rows"] == 2
    assert summary["heldout_eval_rows"] == 1
    assert summary["heldout_exact_candidate_matches"] == 1
    assert set(ledger["strategy"]) == {"sft_candidate_generator"}
    assert int(ledger["harness_pass"].sum()) == 2
    assert (tmp_path / "out" / "generation_record_ledger.csv").exists()
    assert (tmp_path / "out" / "heldout_eval_retrieval.csv").exists()
    assert (tmp_path / "report.md").exists()
