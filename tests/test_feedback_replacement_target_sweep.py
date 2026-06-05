from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.run_feedback_replacement_target_sweep import summarize_target, target_slug, write_target_config
from smp02.utils import load_config


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_target_slug_handles_decimal_and_negative_values() -> None:
    assert target_slug(195.0) == "195"
    assert target_slug(192.5) == "192p5"
    assert target_slug(-5.0) == "minus_5"


def test_write_target_config_sets_feedback_ledger(tmp_path: Path) -> None:
    base_cfg = {
        "seed": 42,
        "device": "cpu",
        "agent_discovery": {"target_tg_c": 195.0, "target_window_c": 5.0},
        "pievo_faithful": {"rounds": 4, "candidate_batch_size": 220},
    }
    config_path = tmp_path / "target.yaml"
    write_target_config(
        base_cfg,
        200.0,
        5.0,
        tmp_path / "ledger.csv",
        tmp_path / "pievo",
        config_path,
        rounds=6,
        candidate_batch_size=260,
        external_limit=None,
    )

    cfg = load_config(config_path)
    assert cfg["agent_discovery"]["target_tg_c"] == 200.0
    assert cfg["pievo_faithful"]["rounds"] == 6
    assert cfg["pievo_faithful"]["candidate_batch_size"] == 260
    assert cfg["pievo_faithful"]["external_observation_ledger"].endswith("ledger.csv")
    assert cfg["pievo_faithful"]["external_observation_limit"] is None


def test_summarize_target_reads_replacement_and_pievo_outputs(tmp_path: Path) -> None:
    eval_dir = tmp_path / "eval"
    pievo_dir = tmp_path / "pievo"
    write_json(
        eval_dir / "replacement_eval_summary.json",
        {
            "input_proposals": 120,
            "harness_pass": 7,
            "best_distance_c": 0.4,
            "within_5c": 7,
            "replacement_observations": 7,
        },
    )
    write_json(
        pievo_dir / "pievo_faithful_summary.json",
        {
            "rounds": 6,
            "history_rows": 13,
            "external_observation_summary": {"accepted_rows": 7, "mean_reward": 0.7},
            "posterior_entropy": 1.2,
            "map_principle": "p1",
            "all_selected_within_target_guard": True,
            "validation": {"all_selected_pass": True},
        },
    )
    write_json(pievo_dir / "principle_posterior.json", {"p1": 0.8})
    pd.DataFrame(
        [
            {
                "predicted_tg_mean_c": 199.8,
                "target_distance_c": 0.2,
                "environment_reward": 0.96,
            }
        ]
    ).to_csv(pievo_dir / "selected_formulations.csv", index=False)

    summary = summarize_target(200.0, eval_dir, pievo_dir)

    assert summary["target_tg_c"] == 200.0
    assert summary["replacement_harness_pass"] == 7
    assert summary["pievo_external_rows"] == 7
    assert summary["pievo_map_principle_posterior"] == 0.8
    assert summary["best_selected_target_distance_c"] == 0.2
