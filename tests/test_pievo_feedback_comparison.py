from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.compare_pievo_feedback_ledgers import compare_runs


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def make_run(path: Path, entropy: float, map_prob: float, selected_suffix: str) -> None:
    path.mkdir(parents=True)
    write_json(
        path / "pievo_faithful_summary.json",
        {
            "external_observation_summary": {"accepted_rows": 1, "mean_reward": 0.9},
            "history_rows": 2,
            "total_authority_weight": 2.0,
            "posterior_entropy": entropy,
            "map_principle": "p1",
            "best_selected_target_distance_c": 0.2,
            "selected_rows": 1,
            "all_selected_within_target_guard": True,
            "validation": {"all_selected_pass": True},
        },
    )
    write_json(path / "principle_posterior.json", {"p1": map_prob, "p2": 1.0 - map_prob})
    pd.DataFrame(
        [
            {
                "observation_id": "external_1",
                "smiles": "CCO|NCC",
                "ratios": "0.5:0.5",
                "target_distance_c": 0.3,
            }
        ]
    ).to_csv(path / "external_observations_used.csv", index=False)
    pd.DataFrame(
        [
            {
                "observation_id": "selected_1",
                "smiles": f"CCO|NCC{selected_suffix}",
                "ratios": "0.5:0.5",
                "target_distance_c": 0.2,
            }
        ]
    ).to_csv(path / "selected_formulations.csv", index=False)


def test_compare_pievo_feedback_ledgers_writes_delta(tmp_path: Path) -> None:
    original = tmp_path / "original"
    feedback = tmp_path / "feedback"
    make_run(original, entropy=2.0, map_prob=0.6, selected_suffix="")
    make_run(feedback, entropy=1.0, map_prob=0.8, selected_suffix="")

    out_dir = tmp_path / "out"
    report = tmp_path / "report.md"
    summary = compare_runs(original, feedback, out_dir, report)

    assert summary["same_selected_set"] is True
    assert summary["feedback_guided"]["posterior_entropy"] == 1.0
    delta = pd.read_csv(out_dir / "principle_posterior_delta.csv")
    assert delta.iloc[0]["principle"] == "p1"
    assert round(float(delta.iloc[0]["delta"]), 6) == 0.2
    assert "IDS Selection Overlap" in report.read_text(encoding="utf-8")
