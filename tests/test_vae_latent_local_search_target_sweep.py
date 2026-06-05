from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.run_vae_latent_local_search_target_sweep import aggregate_rows, summarize_target, target_slug, write_target_config
from smp02.utils import load_config


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_target_slug_handles_decimal_values() -> None:
    assert target_slug(195.0) == "195"
    assert target_slug(192.5) == "192p5"
    assert target_slug(-7.5) == "minus_7p5"


def test_write_target_config_sets_latent_ledger(tmp_path: Path) -> None:
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
    assert cfg["agent_discovery"]["output_dir"].endswith("target_200")
    assert cfg["pievo_faithful"]["rounds"] == 6
    assert cfg["pievo_faithful"]["candidate_batch_size"] == 260
    assert cfg["pievo_faithful"]["external_observation_ledger"].endswith("ledger.csv")
    assert cfg["pievo_faithful"]["external_observation_limit"] is None


def test_summarize_target_reads_latent_and_pievo_outputs(tmp_path: Path) -> None:
    eval_dir = tmp_path / "eval"
    pievo_dir = tmp_path / "pievo"
    write_json(
        eval_dir / "replacement_eval_summary.json",
        {
            "input_proposals": 200,
            "harness_pass": 22,
            "best_distance_c": 0.4,
            "within_1c": 3,
            "within_5c": 22,
            "replacement_observations": 22,
            "literature_template_scored": 39,
            "literature_template_harness_pass": 4,
        },
    )
    write_json(
        pievo_dir / "pievo_faithful_summary.json",
        {
            "rounds": 4,
            "history_rows": 26,
            "external_observation_summary": {"accepted_rows": 22, "mean_reward": 0.7},
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

    summary = summarize_target(
        200.0,
        {"mean_latent_distance": 0.1, "mean_tanimoto": 0.2},
        eval_dir,
        pievo_dir,
    )

    assert summary["target_tg_c"] == 200.0
    assert summary["latent_harness_pass"] == 22
    assert summary["latent_literature_template_harness_pass"] == 4
    assert summary["pievo_external_rows"] == 22
    assert summary["pievo_map_principle_posterior"] == 0.8
    assert summary["best_selected_target_distance_c"] == 0.2


def test_aggregate_rows_tracks_best_target_and_totals(tmp_path: Path) -> None:
    rows = [
        {
            "target_tg_c": 190.0,
            "latent_input_proposals": 200,
            "latent_harness_pass": 12,
            "latent_observations": 12,
            "pievo_external_rows": 12,
            "pievo_all_selected_pass": True,
            "pievo_all_selected_within_guard": True,
            "best_selected_predicted_tg_mean_c": 190.5,
            "best_selected_target_distance_c": 0.5,
            "pievo_map_principle": "p190",
        },
        {
            "target_tg_c": 200.0,
            "latent_input_proposals": 200,
            "latent_harness_pass": 22,
            "latent_observations": 22,
            "pievo_external_rows": 22,
            "pievo_all_selected_pass": True,
            "pievo_all_selected_within_guard": True,
            "best_selected_predicted_tg_mean_c": 200.1,
            "best_selected_target_distance_c": 0.1,
            "pievo_map_principle": "p200",
        },
    ]

    aggregate = aggregate_rows(rows, tmp_path / "out", tmp_path / "pievo")

    assert aggregate["targets"] == 2
    assert aggregate["total_latent_harness_pass"] == 34
    assert aggregate["total_pievo_external_rows"] == 34
    assert aggregate["all_pievo_selected_pass"] is True
    assert aggregate["best_target_tg_c"] == 200.0
    assert aggregate["best_selected_target_distance_c"] == 0.1
