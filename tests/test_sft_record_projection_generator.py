from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from scripts.train_sft_record_projection_generator import run_training


def sft_line(
    generation_id: str,
    split: str,
    smiles: str,
    ratios: str,
    predicted_tg_c: float,
    strategy: str = "rule_template",
) -> str:
    payload = {
        "candidate_json": {"smiles": smiles.split("|"), "ratios": ratios.split(":")},
        "candidate_ratios": ratios,
        "candidate_smiles": smiles,
        "compatibility_reasons": "test compatibility evidence",
        "functional_group_plan": "test functional-group plan",
        "ood_penalty": 0.0,
        "predicted_tg_mean_c": predicted_tg_c,
        "predicted_tg_sigma_c": 0.0,
        "principle_hypothesis": "test principle",
        "review_status": "needs_review",
        "stage": "harnessed",
        "strategy": strategy,
        "target_tg_c": 195.0,
        "target_window_c": 5.0,
    }
    item = {
        "messages": [
            {"role": "system", "content": "Generate auditable records."},
            {
                "role": "user",
                "content": (
                    "Target Tg: 195.0 C\n"
                    "Target window: +/-5.0 C\n"
                    "RAG refs: test_ref_a|test_ref_b\n"
                    "RAG digest: test digest\n"
                ),
            },
            {"role": "assistant", "content": json.dumps(payload)},
        ],
        "metadata": {
            "generation_id": generation_id,
            "strategy": strategy,
            "source_ledger": "test_generation_record_ledger.csv",
            "target_distance_c": abs(predicted_tg_c - 195.0),
            "generation_reward": 0.95,
            "split": split,
        },
    }
    return json.dumps(item)


def test_sft_record_projection_training_writes_auditable_outputs(tmp_path: Path) -> None:
    sft_jsonl = tmp_path / "sft.jsonl"
    sft_jsonl.write_text(
        "\n".join(
            [
                sft_line("g1", "train", "NCCN|O=C=NCCN=C=O", "0.50000:0.50000", 194.8),
                sft_line("g2", "train", "C1CO1|NCCN", "0.40000:0.60000", 195.4, "functional_group_replacement"),
                sft_line("g3", "train", "C=CC(=O)OCC|NCCN", "0.30000:0.70000", 196.2),
                sft_line("g4", "train", "O=C1OC(=O)CC1|NCCN", "0.60000:0.40000", 193.9),
                sft_line("g5", "eval", "CCO|NCCN", "0.50000:0.50000", 195.2),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    report = tmp_path / "report.md"

    ledger, summary = run_training(
        Namespace(
            sft_jsonl=str(sft_jsonl),
            target_tg_c=195.0,
            target_window_c=5.0,
            max_records=3,
            sample_multiplier=3,
            epochs=2,
            batch_size=2,
            hidden_dim=16,
            learning_rate=1e-3,
            condition_noise_std=0.0,
            seed=3,
            device="cpu",
            generation_time="2026-06-06",
            reward_temperature_c=5.0,
            schema="trail/generation/generation_record_schema.yaml",
            out_dir=str(out_dir),
            report=str(report),
        )
    )

    assert summary["generator_mode"] == "supervised_neural_sft_projection"
    assert summary["train_examples"] == 4
    assert summary["eval_examples"] == 1
    assert summary["input_rows"] == 3
    assert summary["harness_pass_rows"] == 3
    assert summary["train_loss_final"] is not None
    assert summary["projection_distance_mean"] is not None
    assert not ledger.empty
    assert ledger["harness_pass"].all()
    assert (out_dir / "sft_record_projection_model.pt").exists()
    assert (out_dir / "sft_projection_scaler.json").exists()
    assert (out_dir / "nearest_sft_record_projection.csv").exists()
    assert report.exists()
