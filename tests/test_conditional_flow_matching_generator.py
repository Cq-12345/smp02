from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pandas as pd

from scripts.train_conditional_flow_matching_generator import run_training


def test_conditional_flow_matching_generator_trains_and_writes_records(tmp_path: Path) -> None:
    seed_table = tmp_path / "diffusion_flow_seed_table.csv"
    pd.DataFrame(
        [
            {
                "split": "train",
                "generation_id": "seed-1",
                "strategy": "rule_template",
                "target_tg_c": 195.0,
                "target_window_c": 5.0,
                "candidate_smiles": "CCO|NCC",
                "candidate_ratios": "0.50000:0.50000",
                "predicted_tg_mean_c": 195.5,
                "predicted_tg_sigma_c": 1.0,
                "target_distance_c": 0.5,
                "generation_reward": 0.9,
                "compatibility_reasons": "amine-alcohol smoke compatibility",
                "source_ledger": "unit.csv",
            },
            {
                "split": "train",
                "generation_id": "seed-2",
                "strategy": "vae_latent_local_search",
                "target_tg_c": 195.0,
                "target_window_c": 5.0,
                "candidate_smiles": "CCN|OCC",
                "candidate_ratios": "0.40000:0.60000",
                "predicted_tg_mean_c": 196.0,
                "predicted_tg_sigma_c": 1.2,
                "target_distance_c": 1.0,
                "generation_reward": 0.8,
                "compatibility_reasons": "amine-alcohol smoke compatibility",
                "source_ledger": "unit.csv",
            },
            {
                "split": "train",
                "generation_id": "seed-3",
                "strategy": "functional_group_replacement",
                "target_tg_c": 200.0,
                "target_window_c": 5.0,
                "candidate_smiles": "CCCO|NCCC",
                "candidate_ratios": "0.55000:0.45000",
                "predicted_tg_mean_c": 199.0,
                "predicted_tg_sigma_c": 1.5,
                "target_distance_c": 1.0,
                "generation_reward": 0.8,
                "compatibility_reasons": "amine-alcohol smoke compatibility",
                "source_ledger": "unit.csv",
            },
            {
                "split": "eval",
                "generation_id": "seed-eval",
                "strategy": "rule_template",
                "target_tg_c": 195.0,
                "target_window_c": 5.0,
                "candidate_smiles": "CCO|NCC",
                "candidate_ratios": "0.50000:0.50000",
                "predicted_tg_mean_c": 195.2,
                "predicted_tg_sigma_c": 1.0,
                "target_distance_c": 0.2,
                "generation_reward": 0.95,
                "compatibility_reasons": "amine-alcohol smoke compatibility",
                "source_ledger": "unit.csv",
            },
        ]
    ).to_csv(seed_table, index=False)

    ledger, summary = run_training(
        Namespace(
            seed_table=str(seed_table),
            target_tg_c=195.0,
            target_window_c=5.0,
            max_records=2,
            sample_multiplier=4,
            epochs=2,
            batch_size=2,
            hidden_dim=16,
            learning_rate=1e-3,
            integration_steps=2,
            seed=7,
            device="cpu",
            generation_time="2026-06-06",
            reward_temperature_c=5.0,
            schema="trail/generation/generation_record_schema.yaml",
            out_dir=str(tmp_path / "out"),
            report=str(tmp_path / "report.md"),
        )
    )

    assert summary["generator_mode"] == "conditional_flow_matching_trained_projection"
    assert summary["epochs"] == 2
    assert summary["train_seed_rows"] == 3
    assert summary["eval_seed_rows"] == 1
    assert summary["projected_records"] > 0
    assert summary["harness_pass_rows"] == summary["input_rows"]
    assert summary["train_loss_final"] is not None
    assert summary["model_path"]
    assert set(ledger["strategy"]) == {"diffusion_or_flow_matching"}
    assert int(ledger["harness_pass"].sum()) == summary["input_rows"]
    assert (tmp_path / "out" / "conditional_flow_matching_model.pt").exists()
    assert (tmp_path / "out" / "nearest_seed_projection.csv").exists()
    assert (tmp_path / "out" / "generation_record_ledger.csv").exists()
    assert (tmp_path / "report.md").exists()
