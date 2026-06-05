from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pandas as pd

from scripts.run_diffusion_flow_candidate_generator_dry_run import run_dry_run


def test_diffusion_flow_candidate_generator_dry_run_writes_harnessed_records(tmp_path: Path) -> None:
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

    ledger, summary = run_dry_run(
        Namespace(
            seed_table=str(seed_table),
            max_records=2,
            target_tg_c=195.0,
            target_window_c=5.0,
            target_condition_tolerance_c=5.0,
            generation_time="2026-06-06",
            reward_temperature_c=5.0,
            schema="trail/generation/generation_record_schema.yaml",
            out_dir=str(tmp_path / "out"),
            report=str(tmp_path / "report.md"),
        )
    )

    assert summary["generator_mode"] == "conditional_seed_replay_not_weight_update"
    assert summary["generated_records"] == 2
    assert summary["harness_pass_rows"] == 2
    assert summary["train_seed_rows"] == 2
    assert summary["eval_seed_rows"] == 1
    assert summary["heldout_eval_rows"] == 1
    assert summary["heldout_exact_candidate_matches"] == 1
    assert set(ledger["strategy"]) == {"diffusion_or_flow_matching"}
    assert int(ledger["harness_pass"].sum()) == 2
    assert (tmp_path / "out" / "generation_record_ledger.csv").exists()
    assert (tmp_path / "out" / "heldout_eval_retrieval.csv").exists()
    assert (tmp_path / "report.md").exists()
