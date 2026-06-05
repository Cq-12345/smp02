from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pandas as pd

from scripts.update_generation_strategy_policy import collect_arms, high_authority_feedback_context, run_policy, score_policy


def test_bandit_policy_gates_unready_generators() -> None:
    feedback = pd.DataFrame(
        [
            {
                "strategy": "llm_smiles_generation",
                "records": 1,
                "harness_pass": 0,
                "pass_rate": 0.0,
                "policy_weight_delta": -0.25,
                "next_constraint": "predictor_feedback: run predictor first.",
            }
        ]
    )
    arms = collect_arms(
        feedback,
        expanded_replacement={"input_proposals": 200, "harness_pass": 18, "best_distance_c": 0.2, "replacement_observations": 18},
        latent_local_search_eval={"input_proposals": 200, "harness_pass": 42, "best_distance_c": 0.2, "replacement_observations": 42},
        expanded_generation={"input_rows": 2, "harness_pass_rows": 2, "best_distance_c": 0.003, "mean_generation_reward": 0.95},
        training_summary={
            "sft_examples": 5,
            "sft_ready": False,
            "next_data_needed_for_sft": 15,
            "sft_min_examples": 20,
            "diffusion_flow_seed_rows": 5,
            "diffusion_flow_ready": False,
            "next_data_needed_for_diffusion_flow": 95,
            "diffusion_flow_min_examples": 100,
        },
    )

    policy, summary = score_policy(arms, exploration_c=0.25, softmax_temperature=0.25, total_budget=100)

    assert summary["eligible_active_strategies"] == 3
    assert int(policy["allocation_per_100"].sum()) == 100
    by_strategy = {row["strategy"]: row for _, row in policy.iterrows()}
    assert by_strategy["llm_smiles_generation"]["status"] == "suppressed"
    assert by_strategy["llm_smiles_generation"]["allocation_per_100"] == 0
    assert by_strategy["sft_candidate_generator"]["status"] == "data_collection_only"
    assert by_strategy["sft_candidate_generator"]["allocation_per_100"] == 0
    assert by_strategy["diffusion_or_flow_matching"]["status"] == "data_collection_only"
    assert by_strategy["diffusion_or_flow_matching"]["allocation_per_100"] == 0
    assert by_strategy["vae_latent_local_search"]["bandit_score"] > by_strategy["functional_group_replacement"]["bandit_score"]


def test_high_authority_feedback_context_tracks_active_evidence_state() -> None:
    waiting = high_authority_feedback_context(
        {"active_rows": 0, "authority_weight_sum": 0.0},
        {"bridge_status": "no_active_evidence_noop", "external_accepted_rows": 0, "active_evidence_updates_posterior": False},
    )
    assert waiting["high_authority_evidence_status"] == "awaiting_high_authority_evidence"
    assert waiting["high_authority_budget_mode"] == "surrogate_backed_allocation"
    assert waiting["active_evidence_updates_pievo_posterior"] is False

    active = high_authority_feedback_context(
        {"active_rows": 2, "authority_weight_sum": 8.0},
        {"bridge_status": "active_evidence_updates_posterior", "external_accepted_rows": 2, "active_evidence_updates_posterior": True},
    )
    assert active["high_authority_evidence_status"] == "high_authority_posterior_active"
    assert active["high_authority_budget_mode"] == "high_authority_informed_allocation_ready"
    assert active["active_observation_authority_weight_sum"] == 8.0


def test_bandit_policy_activates_ready_sft_without_unbounded_rate() -> None:
    arms = collect_arms(
        pd.DataFrame(),
        expanded_replacement={"input_proposals": 200, "harness_pass": 18, "best_distance_c": 0.2, "replacement_observations": 18},
        latent_local_search_eval={"input_proposals": 200, "harness_pass": 42, "best_distance_c": 0.2, "replacement_observations": 42},
        expanded_generation={"input_rows": 2, "harness_pass_rows": 2, "best_distance_c": 0.01, "mean_generation_reward": 0.95},
        training_summary={
            "sft_examples": 64,
            "sft_ready": True,
            "next_data_needed_for_sft": 0,
            "sft_min_examples": 20,
            "diffusion_flow_seed_rows": 64,
            "diffusion_flow_ready": False,
            "next_data_needed_for_diffusion_flow": 36,
            "diffusion_flow_min_examples": 100,
        },
    )

    policy, summary = score_policy(arms, exploration_c=0.25, softmax_temperature=0.25, total_budget=100)

    by_strategy = {row["strategy"]: row for _, row in policy.iterrows()}
    assert summary["eligible_active_strategies"] == 4
    assert by_strategy["sft_candidate_generator"]["status"] == "active"
    assert by_strategy["sft_candidate_generator"]["readiness_gate"]
    assert by_strategy["sft_candidate_generator"]["raw_pass_rate"] == 1.0
    assert by_strategy["sft_candidate_generator"]["allocation_per_100"] > 0
    assert by_strategy["diffusion_or_flow_matching"]["status"] == "data_collection_only"


def test_bandit_policy_prefers_sft_dry_run_summary_when_available() -> None:
    arms = collect_arms(
        pd.DataFrame(),
        expanded_replacement={"input_proposals": 200, "harness_pass": 18, "best_distance_c": 0.2, "replacement_observations": 18},
        latent_local_search_eval={"input_proposals": 200, "harness_pass": 42, "best_distance_c": 0.2, "replacement_observations": 42},
        expanded_generation={"input_rows": 2, "harness_pass_rows": 2, "best_distance_c": 0.01, "mean_generation_reward": 0.95},
        training_summary={
            "sft_examples": 64,
            "sft_ready": True,
            "next_data_needed_for_sft": 0,
            "sft_min_examples": 20,
            "diffusion_flow_seed_rows": 64,
            "diffusion_flow_ready": False,
            "next_data_needed_for_diffusion_flow": 36,
            "diffusion_flow_min_examples": 100,
        },
        sft_generation_summary={
            "input_rows": 25,
            "harness_pass_rows": 25,
            "best_distance_c": 0.003,
            "mean_generation_reward": 0.78,
        },
    )

    by_strategy = {row["strategy"]: row for _, row in arms.iterrows()}
    assert by_strategy["sft_candidate_generator"]["evidence_source"] == "sft_dry_run_generation_record_summary"
    assert by_strategy["sft_candidate_generator"]["attempts"] == 25
    assert by_strategy["sft_candidate_generator"]["successes"] == 25
    assert by_strategy["sft_candidate_generator"]["status"] == "active"


def test_bandit_policy_prefers_trained_sft_summary_over_dry_run() -> None:
    arms = collect_arms(
        pd.DataFrame(),
        expanded_replacement={"input_proposals": 200, "harness_pass": 18, "best_distance_c": 0.2, "replacement_observations": 18},
        latent_local_search_eval={"input_proposals": 200, "harness_pass": 42, "best_distance_c": 0.2, "replacement_observations": 42},
        expanded_generation={"input_rows": 2, "harness_pass_rows": 2, "best_distance_c": 0.01, "mean_generation_reward": 0.95},
        training_summary={
            "sft_examples": 143,
            "sft_ready": True,
            "next_data_needed_for_sft": 0,
            "sft_min_examples": 20,
            "diffusion_flow_seed_rows": 143,
            "diffusion_flow_ready": True,
            "next_data_needed_for_diffusion_flow": 0,
            "diffusion_flow_min_examples": 100,
        },
        sft_generation_summary={
            "input_rows": 25,
            "harness_pass_rows": 25,
            "best_distance_c": 0.003,
            "mean_generation_reward": 0.99,
        },
        sft_trained_summary={
            "input_rows": 23,
            "harness_pass_rows": 23,
            "best_distance_c": 0.006,
            "mean_generation_reward": 0.84,
        },
    )

    by_strategy = {row["strategy"]: row for _, row in arms.iterrows()}
    assert by_strategy["sft_candidate_generator"]["evidence_source"] == "sft_trained_projection_generation_record_summary"
    assert by_strategy["sft_candidate_generator"]["attempts"] == 23
    assert by_strategy["sft_candidate_generator"]["successes"] == 23
    assert by_strategy["sft_candidate_generator"]["status"] == "active"


def test_bandit_policy_activates_ready_diffusion_flow() -> None:
    arms = collect_arms(
        pd.DataFrame(),
        expanded_replacement={"input_proposals": 200, "harness_pass": 18, "best_distance_c": 0.2, "replacement_observations": 18},
        latent_local_search_eval={"input_proposals": 200, "harness_pass": 42, "best_distance_c": 0.2, "replacement_observations": 42},
        expanded_generation={"input_rows": 2, "harness_pass_rows": 2, "best_distance_c": 0.01, "mean_generation_reward": 0.95},
        training_summary={
            "sft_examples": 143,
            "sft_ready": True,
            "next_data_needed_for_sft": 0,
            "sft_min_examples": 20,
            "diffusion_flow_seed_rows": 143,
            "diffusion_flow_ready": True,
            "next_data_needed_for_diffusion_flow": 0,
            "diffusion_flow_min_examples": 100,
        },
    )

    policy, summary = score_policy(arms, exploration_c=0.25, softmax_temperature=0.25, total_budget=100)

    by_strategy = {row["strategy"]: row for _, row in policy.iterrows()}
    assert summary["eligible_active_strategies"] == 5
    assert summary["data_collection_only_strategies"] == 0
    assert by_strategy["diffusion_or_flow_matching"]["status"] == "active"
    assert by_strategy["diffusion_or_flow_matching"]["readiness_gate"]
    assert by_strategy["diffusion_or_flow_matching"]["attempts"] == 143
    assert by_strategy["diffusion_or_flow_matching"]["successes"] == 143
    assert by_strategy["diffusion_or_flow_matching"]["allocation_per_100"] > 0
    assert "diffusion/flow dry-run" in by_strategy["diffusion_or_flow_matching"]["next_constraint"]


def test_bandit_policy_prefers_diffusion_flow_dry_run_summary_when_available() -> None:
    arms = collect_arms(
        pd.DataFrame(),
        expanded_replacement={"input_proposals": 200, "harness_pass": 18, "best_distance_c": 0.2, "replacement_observations": 18},
        latent_local_search_eval={"input_proposals": 200, "harness_pass": 42, "best_distance_c": 0.2, "replacement_observations": 42},
        expanded_generation={"input_rows": 2, "harness_pass_rows": 2, "best_distance_c": 0.01, "mean_generation_reward": 0.95},
        training_summary={
            "sft_examples": 143,
            "sft_ready": True,
            "next_data_needed_for_sft": 0,
            "sft_min_examples": 20,
            "diffusion_flow_seed_rows": 143,
            "diffusion_flow_ready": True,
            "next_data_needed_for_diffusion_flow": 0,
            "diffusion_flow_min_examples": 100,
        },
        diffusion_flow_generation_summary={
            "input_rows": 19,
            "harness_pass_rows": 19,
            "best_distance_c": 0.003,
            "mean_generation_reward": 0.99,
        },
    )

    by_strategy = {row["strategy"]: row for _, row in arms.iterrows()}
    assert by_strategy["diffusion_or_flow_matching"]["evidence_source"] == "diffusion_flow_dry_run_generation_record_summary"
    assert by_strategy["diffusion_or_flow_matching"]["attempts"] == 19
    assert by_strategy["diffusion_or_flow_matching"]["successes"] == 19
    assert by_strategy["diffusion_or_flow_matching"]["status"] == "active"


def test_bandit_policy_prefers_trained_diffusion_flow_summary_over_dry_run() -> None:
    arms = collect_arms(
        pd.DataFrame(),
        expanded_replacement={"input_proposals": 200, "harness_pass": 18, "best_distance_c": 0.2, "replacement_observations": 18},
        latent_local_search_eval={"input_proposals": 200, "harness_pass": 42, "best_distance_c": 0.2, "replacement_observations": 42},
        expanded_generation={"input_rows": 2, "harness_pass_rows": 2, "best_distance_c": 0.01, "mean_generation_reward": 0.95},
        training_summary={
            "sft_examples": 143,
            "sft_ready": True,
            "next_data_needed_for_sft": 0,
            "sft_min_examples": 20,
            "diffusion_flow_seed_rows": 143,
            "diffusion_flow_ready": True,
            "next_data_needed_for_diffusion_flow": 0,
            "diffusion_flow_min_examples": 100,
        },
        diffusion_flow_generation_summary={
            "input_rows": 19,
            "harness_pass_rows": 19,
            "best_distance_c": 0.003,
            "mean_generation_reward": 0.99,
        },
        diffusion_flow_trained_summary={
            "input_rows": 23,
            "harness_pass_rows": 23,
            "best_distance_c": 0.005,
            "mean_generation_reward": 0.84,
        },
    )

    by_strategy = {row["strategy"]: row for _, row in arms.iterrows()}
    assert by_strategy["diffusion_or_flow_matching"]["evidence_source"] == "diffusion_flow_trained_projection_generation_record_summary"
    assert by_strategy["diffusion_or_flow_matching"]["attempts"] == 23
    assert by_strategy["diffusion_or_flow_matching"]["successes"] == 23
    assert by_strategy["diffusion_or_flow_matching"]["status"] == "active"


def test_run_policy_writes_outputs(tmp_path: Path) -> None:
    feedback = tmp_path / "strategy_feedback.csv"
    pd.DataFrame(
        [
            {
                "strategy": "llm_smiles_generation",
                "records": 1,
                "harness_pass": 0,
                "pass_rate": 0.0,
                "policy_weight_delta": -0.25,
                "next_constraint": "predictor_feedback: run predictor first.",
            }
        ]
    ).to_csv(feedback, index=False)
    expanded = tmp_path / "expanded.json"
    expanded.write_text(json.dumps({"input_proposals": 10, "harness_pass": 2, "best_distance_c": 0.5, "replacement_observations": 2}), encoding="utf-8")
    latent = tmp_path / "latent.json"
    latent.write_text(json.dumps({"input_proposals": 10, "harness_pass": 4, "best_distance_c": 0.2, "replacement_observations": 4}), encoding="utf-8")
    generation = tmp_path / "generation.json"
    generation.write_text(json.dumps({"input_rows": 2, "harness_pass_rows": 2, "best_distance_c": 0.01, "mean_generation_reward": 0.99}), encoding="utf-8")
    training = tmp_path / "training.json"
    training.write_text(
        json.dumps(
            {
                "sft_examples": 5,
                "sft_ready": False,
                "next_data_needed_for_sft": 15,
                "sft_min_examples": 20,
                "diffusion_flow_seed_rows": 5,
                "diffusion_flow_ready": False,
                "next_data_needed_for_diffusion_flow": 95,
                "diffusion_flow_min_examples": 100,
            }
        ),
        encoding="utf-8",
    )
    sft_generation = tmp_path / "sft_generation.json"
    sft_generation.write_text(json.dumps({"input_rows": 0}), encoding="utf-8")
    diffusion_flow_generation = tmp_path / "diffusion_flow_generation.json"
    diffusion_flow_generation.write_text(json.dumps({"input_rows": 0}), encoding="utf-8")
    diffusion_flow_trained = tmp_path / "diffusion_flow_trained.json"
    diffusion_flow_trained.write_text(json.dumps({"input_rows": 0}), encoding="utf-8")
    active_observation = tmp_path / "active_observation.json"
    active_observation.write_text(json.dumps({"active_rows": 0, "authority_weight_sum": 0.0}), encoding="utf-8")
    active_bridge = tmp_path / "active_bridge.json"
    active_bridge.write_text(
        json.dumps(
            {
                "bridge_status": "no_active_evidence_noop",
                "external_accepted_rows": 0,
                "external_rejected_rows": 0,
                "active_evidence_updates_posterior": False,
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    report = tmp_path / "report.md"

    policy, summary = run_policy(
        Namespace(
            strategy_feedback=str(feedback),
            expanded_replacement_summary=str(expanded),
            vae_latent_local_search_eval_summary=str(latent),
            expanded_generation_summary=str(generation),
            generative_training_summary=str(training),
            sft_generation_summary=str(sft_generation),
            diffusion_flow_generation_summary=str(diffusion_flow_generation),
            diffusion_flow_trained_generation_summary=str(diffusion_flow_trained),
            active_observation_summary=str(active_observation),
            active_evidence_pievo_bridge_summary=str(active_bridge),
            exploration_c=0.25,
            softmax_temperature=0.25,
            total_budget=100,
            out_dir=str(out_dir),
            report=str(report),
        )
    )

    assert not policy.empty
    assert summary["strategies"] == 6
    assert summary["high_authority_evidence_status"] == "awaiting_high_authority_evidence"
    assert summary["high_authority_budget_mode"] == "surrogate_backed_allocation"
    assert summary["active_evidence_bridge_status"] == "no_active_evidence_noop"
    assert (out_dir / "generation_strategy_bandit_policy.csv").exists()
    assert (out_dir / "generation_strategy_bandit_summary.json").exists()
    assert report.exists()
