from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pandas as pd

from scripts.build_generative_training_sets import build_training_sets


def test_build_generative_training_sets_filters_to_harness_pass_records(tmp_path: Path) -> None:
    ledger = tmp_path / "generation_record_ledger.csv"
    pd.DataFrame(
        [
            {
                "generation_id": "ok",
                "strategy": "llm_rag_principle_generation",
                "stage": "harnessed",
                "target_tg_c": 195,
                "target_window_c": 5,
                "candidate_smiles": "CCO|NCC",
                "candidate_ratios": "0.50000:0.50000",
                "source_context": "rag",
                "compatibility_reasons": "amine-alcohol test",
                "predicted_tg_mean_c": 196,
                "predicted_tg_sigma_c": 10,
                "ood_penalty": 0.1,
                "target_distance_c": 1,
                "generation_reward": 0.8,
                "harness_pass": True,
                "record_pass": True,
                "candidate_json": '{"candidate":"ok"}',
            },
            {
                "generation_id": "draft",
                "strategy": "llm_smiles_generation",
                "stage": "draft",
                "target_tg_c": 195,
                "target_window_c": 5,
                "candidate_smiles": "CCO|NCC",
                "candidate_ratios": "0.60000:0.60000",
                "source_context": "rag",
                "compatibility_reasons": "",
                "predicted_tg_mean_c": "",
                "target_distance_c": "",
                "generation_reward": "",
                "harness_pass": False,
                "record_pass": True,
            },
        ]
    ).to_csv(ledger, index=False)
    args = Namespace(
        ledgers=[ledger],
        min_reward=0.0,
        min_sft_examples=1,
        min_diffusion_flow_examples=1,
        out_dir=str(tmp_path / "out"),
        report=str(tmp_path / "report.md"),
    )

    summary = build_training_sets(args)

    assert summary["input_rows"] == 2
    assert summary["harness_pass_rows"] == 1
    assert summary["sft_examples"] == 1
    assert summary["diffusion_flow_seed_rows"] == 1
    sft_lines = (tmp_path / "out" / "sft_generation_records.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(sft_lines) == 1
    example = json.loads(sft_lines[0])
    assert example["metadata"]["generation_id"] == "ok"
    assert "Harness" in example["messages"][0]["content"]
    seed_table = pd.read_csv(tmp_path / "out" / "diffusion_flow_seed_table.csv")
    assert list(seed_table["generation_id"]) == ["ok"]
