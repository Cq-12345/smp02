from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pandas as pd

from scripts.update_target_conditioned_generation_policy import build_target_policy, merge_replacement_evidence, run_target_conditioned_policy


def replacement_row(target: float, harness_pass: int, mean_reward: float, best_reward: float, selected_distance: float) -> dict:
    return {
        "target_tg_c": target,
        "replacement_input_proposals": 120,
        "replacement_harness_pass": harness_pass,
        "replacement_best_distance_c": selected_distance,
        "replacement_observations": harness_pass,
        "pievo_external_mean_reward": mean_reward,
        "best_selected_target_distance_c": selected_distance,
        "best_selected_reward": best_reward,
        "pievo_map_principle": "replacement_principle",
        "pievo_map_principle_posterior": 0.25,
        "pievo_all_selected_pass": True,
    }


def latent_row(target: float, harness_pass: int, mean_reward: float, best_reward: float, selected_distance: float) -> dict:
    return {
        "target_tg_c": target,
        "latent_input_proposals": 200,
        "latent_harness_pass": harness_pass,
        "latent_best_distance_c": selected_distance,
        "latent_observations": harness_pass,
        "pievo_external_mean_reward": mean_reward,
        "best_selected_target_distance_c": selected_distance,
        "best_selected_reward": best_reward,
        "pievo_map_principle": "latent_principle",
        "pievo_map_principle_posterior": 0.10,
        "pievo_all_selected_pass": True,
    }


def global_policy_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "strategy": "llm_rag_principle_generation",
                "status": "active",
                "readiness_gate": True,
                "evidence_source": "generation_record_summary",
                "attempts": 2,
                "successes": 2,
                "failures": 0,
                "raw_pass_rate": 1.0,
                "beta_pass_mean": 0.75,
                "utility_mean": 0.84,
                "exploration_bonus": 0.35,
                "bandit_score": 1.29,
                "allocation_fraction": 0.52,
                "observations": 2,
                "mean_reward": 0.95,
                "best_distance_c": 0.01,
            },
            {
                "strategy": "sft_candidate_generator",
                "status": "active",
                "readiness_gate": True,
                "evidence_source": "sft_trained_projection_generation_record_summary",
                "attempts": 23,
                "successes": 23,
                "failures": 0,
                "raw_pass_rate": 1.0,
                "beta_pass_mean": 0.96,
                "utility_mean": 0.97,
                "exploration_bonus": 0.13,
                "bandit_score": 1.09,
                "allocation_fraction": 0.23,
                "observations": 23,
                "mean_reward": 0.98,
                "best_distance_c": 0.01,
            },
            {
                "strategy": "diffusion_or_flow_matching",
                "status": "active",
                "readiness_gate": True,
                "evidence_source": "diffusion_flow_trained_projection_generation_record_summary",
                "attempts": 23,
                "successes": 23,
                "failures": 0,
                "raw_pass_rate": 1.0,
                "beta_pass_mean": 0.96,
                "utility_mean": 0.91,
                "exploration_bonus": 0.13,
                "bandit_score": 1.04,
                "allocation_fraction": 0.19,
                "observations": 23,
                "mean_reward": 0.86,
                "best_distance_c": 0.01,
            },
            {
                "strategy": "llm_smiles_generation",
                "status": "suppressed",
                "readiness_gate": False,
                "evidence_source": "strategy_feedback",
                "attempts": 1,
                "successes": 0,
                "failures": 1,
                "raw_pass_rate": 0.0,
                "beta_pass_mean": 0.33,
                "utility_mean": 0.33,
                "exploration_bonus": 0.44,
                "bandit_score": -0.38,
                "allocation_fraction": 0.0,
                "observations": 0,
                "mean_reward": None,
                "best_distance_c": None,
            },
        ]
    )


def test_target_conditioned_policy_allocates_per_target_and_preserves_target_evidence() -> None:
    replacement = [
        replacement_row(190.0, harness_pass=13, mean_reward=0.54, best_reward=0.99, selected_distance=0.06),
        replacement_row(250.0, harness_pass=4, mean_reward=0.71, best_reward=0.98, selected_distance=0.10),
    ]
    latent = [
        latent_row(190.0, harness_pass=38, mean_reward=0.66, best_reward=1.00, selected_distance=0.002),
        latent_row(250.0, harness_pass=5, mean_reward=0.58, best_reward=0.90, selected_distance=0.51),
    ]

    policy, target_summary, summary = build_target_policy(
        replacement,
        latent,
        global_policy_frame(),
        total_budget=100,
        base_transfer_budget=25,
        min_transfer_budget=8,
        reference_target_tg_c=195.0,
        transfer_decay_c=80.0,
    )

    assert summary["targets"] == 2
    assert summary["all_targets_allocation_sum_100"] is True
    assert set(policy["evidence_scope"]) == {"target_sweep", "global_transfer"}
    assert target_summary.set_index("target_tg_c").loc[250.0, "transfer_budget"] < target_summary.set_index("target_tg_c").loc[190.0, "transfer_budget"]
    assert summary["top_target_specific_strategy_by_target"]["190.0"] == "vae_latent_local_search"
    assert summary["top_target_specific_strategy_by_target"]["250.0"] == "functional_group_replacement"
    for _, group in policy.groupby("target_tg_c"):
        assert int(group["allocation_per_100"].sum()) == 100
        assert group[group["strategy"] == "llm_smiles_generation"].iloc[0]["allocation_per_100"] == 0


def test_run_target_conditioned_policy_writes_outputs(tmp_path: Path) -> None:
    replacement = tmp_path / "replacement.json"
    replacement.write_text(
        json.dumps([replacement_row(250.0, harness_pass=4, mean_reward=0.71, best_reward=0.98, selected_distance=0.10)]),
        encoding="utf-8",
    )
    latent = tmp_path / "latent.json"
    latent.write_text(
        json.dumps([latent_row(250.0, harness_pass=5, mean_reward=0.58, best_reward=0.90, selected_distance=0.51)]),
        encoding="utf-8",
    )
    global_policy = tmp_path / "global_policy.csv"
    global_policy_frame().to_csv(global_policy, index=False)
    sparse = tmp_path / "sparse.json"
    sparse.write_text("[]", encoding="utf-8")
    out_dir = tmp_path / "out"
    report = tmp_path / "report.md"

    policy, target_summary, summary = run_target_conditioned_policy(
        Namespace(
            replacement_target_sweep_summary=str(replacement),
            vae_latent_target_sweep_summary=str(latent),
            sparse_target_replacement_expansion_summary=str(sparse),
            global_policy=str(global_policy),
            total_budget=100,
            transferable_exploration_budget=25,
            min_transferable_budget=8,
            reference_transfer_target_tg_c=195.0,
            transfer_decay_c=80.0,
            softmax_temperature=0.18,
            exploration_c=0.15,
            out_dir=str(out_dir),
            report=str(report),
        )
    )

    assert not policy.empty
    assert not target_summary.empty
    assert summary["top_target_specific_strategy_by_target"]["250.0"] == "functional_group_replacement"
    assert (out_dir / "target_conditioned_generation_strategy_policy.csv").exists()
    assert (out_dir / "target_conditioned_generation_strategy_target_summary.csv").exists()
    assert (out_dir / "target_conditioned_generation_strategy_summary.json").exists()
    assert report.exists()


def test_merge_replacement_evidence_prefers_sparse_expansion_for_same_target() -> None:
    base = [replacement_row(250.0, harness_pass=4, mean_reward=0.71, best_reward=0.98, selected_distance=0.10)]
    sparse = [
        {
            **replacement_row(250.0, harness_pass=42, mean_reward=0.63, best_reward=0.98, selected_distance=0.099),
            "replacement_best_distance_c": 0.034,
        }
    ]

    merged = merge_replacement_evidence(base, sparse)

    assert len(merged) == 1
    assert merged[0]["replacement_harness_pass"] == 42
    assert merged[0]["target_evidence_source"] == "sparse_target_replacement_expansion"
