from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pandas as pd

from scripts.run_sparse_target_replacement_expansion import (
    run_sparse_expansion,
    select_target_source_candidates,
    sparse_targets_from_policy,
    target_slug,
)


def candidate(predicted_tg: float, suffix: str) -> dict[str, object]:
    return {
        "smiles_a": f"NC{suffix}",
        "smiles_b": f"O=C=NC{suffix}",
        "groups_a": "primary_amine",
        "groups_b": "isocyanate",
        "compatibility_reason": "异氰酸酯-伯胺形成聚脲。",
        "ratio_a": 0.5,
        "ratio_b": 0.5,
        "predicted_tg": predicted_tg,
        "target_distance": abs(predicted_tg - 195.0),
        "in_target_range": False,
    }


def test_sparse_targets_from_policy_uses_explicit_targets_first(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"sparse_targets": [250.0]}), encoding="utf-8")

    assert sparse_targets_from_policy(policy, [240.0, 260.0]) == [240.0, 260.0]
    assert sparse_targets_from_policy(policy, None) == [250.0]


def test_target_slug_handles_sparse_target_values() -> None:
    assert target_slug(250.0) == "250"
    assert target_slug(247.5) == "247p5"
    assert target_slug(-10.0) == "minus_10"


def test_select_target_source_candidates_recomputes_distance_for_sparse_target() -> None:
    frame = pd.DataFrame(
        [
            candidate(195.0, "a"),
            candidate(247.0, "b"),
            candidate(250.1, "c"),
            candidate(252.0, "d"),
            candidate(310.0, "e"),
        ]
    )

    selected = select_target_source_candidates(
        frame,
        target_tg_c=250.0,
        target_window_c=5.0,
        source_top_k=3,
        source_window_c=10.0,
        high_tg_bias_c=5.0,
    )

    assert len(selected) == 3
    assert selected.iloc[0]["predicted_tg"] == 250.1
    assert selected["in_target_range"].all()
    assert selected["target_distance"].max() <= 5.0
    assert 195.0 not in set(selected["predicted_tg"])


def test_run_sparse_expansion_preserves_existing_summary_when_no_sparse_targets(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"sparse_targets": []}), encoding="utf-8")
    output_root = tmp_path / "out"
    output_root.mkdir()
    existing = [{"target_tg_c": 250.0, "replacement_harness_pass": 42}]
    (output_root / "sparse_target_replacement_expansion_summary.json").write_text(json.dumps(existing), encoding="utf-8")

    rows = run_sparse_expansion(
        Namespace(
            target_policy_summary=str(policy),
            targets=None,
            output_root=str(output_root),
            pievo_output_root=str(tmp_path / "pievo"),
            record_root=str(tmp_path / "records"),
            overwrite_empty=False,
            candidates=str(tmp_path / "missing.csv"),
            config=str(tmp_path / "missing.yaml"),
            target_window_c=5.0,
            source_top_k=40,
            source_window_c=10.0,
            high_tg_bias_c=5.0,
            groups=str(tmp_path / "groups.csv"),
            component_inventory="",
            per_side=4,
            require_counterpart_compatibility=True,
            rounds=6,
            candidate_batch_size=320,
            external_limit=-1,
            report=str(tmp_path / "report.md"),
            reuse_existing=False,
        )
    )

    assert rows == existing
    assert json.loads((output_root / "sparse_target_replacement_expansion_summary.json").read_text(encoding="utf-8")) == existing
