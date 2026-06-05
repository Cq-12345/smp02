from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from trail.workflow.multi_agent_workflow import summarize


def test_workflow_summary_includes_predictor_ensemble_disagreement(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates.csv"
    candidates.write_text("smiles,ratios\nCCO|NCC,0.5:0.5\n", encoding="utf-8")
    history = tmp_path / "history.json"
    history.write_text("[]", encoding="utf-8")
    feedback = tmp_path / "feedback.json"
    feedback.write_text("{}", encoding="utf-8")
    ledger = tmp_path / "ledger.csv"
    pd.DataFrame({"harness_pass": [True, False]}).to_csv(ledger, index=False)
    feedback_aware_ledger = tmp_path / "feedback_aware_ledger.csv"
    pd.DataFrame({"harness_pass": [True]}).to_csv(feedback_aware_ledger, index=False)
    observations = tmp_path / "observations.csv"
    pd.DataFrame({"ledger_pass": [True]}).to_csv(observations, index=False)
    pievo_summary = tmp_path / "pievo_summary.json"
    pievo_summary.write_text(
        json.dumps({"best_selected_target_distance_c": 0.5, "external_observation_summary": {"accepted_rows": 1}}),
        encoding="utf-8",
    )
    ensemble_summary = tmp_path / "ensemble_summary.json"
    ensemble_summary.write_text(
        json.dumps(
            {
                "ensemble_models": 6,
                "near_target_rows": 1045,
                "near_target_low_disagreement_rows": 84,
                "near_target_high_disagreement_rows": 526,
                "mean_ensemble_std_c": 32.16,
                "mean_abs_best_model_delta_c": 30.37,
            }
        ),
        encoding="utf-8",
    )
    ensemble_guard_pievo = tmp_path / "ensemble_guard_pievo.json"
    ensemble_guard_pievo.write_text(
        json.dumps(
            {
                "selected_rows": 6,
                "best_selected_target_distance_c": 0.059,
                "all_selected_within_ensemble_disagreement_guard": True,
                "mean_selected_predictor_ensemble_std_tg_c": 16.4,
            }
        ),
        encoding="utf-8",
    )
    expanded_replacement = tmp_path / "expanded_replacement.json"
    expanded_replacement.write_text(
        json.dumps(
            {
                "scored_formulas": 200,
                "harness_pass": 18,
                "literature_template_scored": 29,
                "literature_template_harness_pass": 3,
            }
        ),
        encoding="utf-8",
    )
    expanded_generation = tmp_path / "expanded_generation.json"
    expanded_generation.write_text(
        json.dumps({"input_rows": 2, "harness_pass_rows": 2, "literature_template_context_rows": 1}),
        encoding="utf-8",
    )
    latent_local_search = tmp_path / "latent_local_search.json"
    latent_local_search.write_text(
        json.dumps({"proposals": 200, "literature_template_proposals": 39}),
        encoding="utf-8",
    )
    latent_local_search_eval = tmp_path / "latent_local_search_eval.json"
    latent_local_search_eval.write_text(
        json.dumps(
            {
                "harness_pass": 42,
                "best_distance_c": 0.20046,
                "literature_template_harness_pass": 7,
                "replacement_observations": 42,
            }
        ),
        encoding="utf-8",
    )
    latent_local_search_pievo = tmp_path / "latent_local_search_pievo.json"
    latent_local_search_pievo.write_text(
        json.dumps({"best_selected_target_distance_c": 0.059, "external_observation_summary": {"accepted_rows": 42}}),
        encoding="utf-8",
    )
    strategy_policy = tmp_path / "strategy_policy.json"
    strategy_policy.write_text(
        json.dumps(
            {
                "top_strategy": "llm_rag_principle_generation",
                "eligible_active_strategies": 3,
                "suppressed_strategies": 1,
                "data_collection_only_strategies": 2,
                "total_budget": 100,
            }
        ),
        encoding="utf-8",
    )
    human_review = tmp_path / "human_review.json"
    human_review.write_text(
        json.dumps(
            {
                "queue_rows": 30,
                "ready_for_active_ledger_rows": 0,
                "draft_ready_for_active_ledger_rows": 0,
                "best_target_distance_c": 0.059,
                "review_priorities": {
                    "process_design_for_dsc": 13,
                    "high_fidelity_before_dsc": 11,
                },
            }
        ),
        encoding="utf-8",
    )
    gnn_global = tmp_path / "gnn_global.json"
    gnn_global.write_text(
        json.dumps(
            {
                "architecture": "mpnn",
                "best_case": "mpnn_global",
                "baseline_mapek_test_pct": 11.0,
                "global_mapek_test_pct": 10.5,
                "global_minus_baseline_mapek_test_pct": -0.5,
                "global_minus_baseline_mae_test_c": -2.0,
            }
        ),
        encoding="utf-8",
    )
    generative_training = tmp_path / "generative_training.json"
    generative_training.write_text(
        json.dumps(
            {
                "sft_examples": 7,
                "sft_ready": False,
                "diffusion_flow_seed_rows": 7,
                "diffusion_flow_ready": False,
                "next_data_needed_for_sft": 13,
                "next_data_needed_for_diffusion_flow": 93,
            }
        ),
        encoding="utf-8",
    )
    sft_candidate_generation = tmp_path / "sft_candidate_generation.json"
    sft_candidate_generation.write_text(
        json.dumps(
            {
                "input_rows": 25,
                "harness_pass_rows": 25,
                "best_distance_c": 0.003,
                "generator_mode": "prototype_replay_not_weight_update",
                "heldout_eval_rows": 12,
                "heldout_exact_candidate_matches": 3,
            }
        ),
        encoding="utf-8",
    )
    sft_trained_generation = tmp_path / "sft_trained_generation.json"
    sft_trained_generation.write_text(
        json.dumps(
            {
                "input_rows": 23,
                "harness_pass_rows": 23,
                "best_distance_c": 0.006,
                "generator_mode": "supervised_neural_sft_projection",
                "train_loss_final": 0.8,
                "eval_loss_final": 1.4,
                "projection_distance_mean": 3.2,
                "heldout_eval_rows": 19,
                "heldout_exact_candidate_matches": 0,
            }
        ),
        encoding="utf-8",
    )
    diffusion_flow_candidate_generation = tmp_path / "diffusion_flow_candidate_generation.json"
    diffusion_flow_candidate_generation.write_text(
        json.dumps(
            {
                "input_rows": 19,
                "harness_pass_rows": 19,
                "best_distance_c": 0.004,
                "generator_mode": "conditional_seed_replay_not_weight_update",
                "heldout_eval_rows": 19,
                "heldout_exact_candidate_matches": 0,
            }
        ),
        encoding="utf-8",
    )
    diffusion_flow_trained_generation = tmp_path / "diffusion_flow_trained_generation.json"
    diffusion_flow_trained_generation.write_text(
        json.dumps(
            {
                "input_rows": 23,
                "harness_pass_rows": 23,
                "best_distance_c": 0.005,
                "generator_mode": "conditional_flow_matching_trained_projection",
                "train_loss_final": 1.2,
                "eval_loss_final": 1.8,
                "projection_distance_mean": 5.0,
            }
        ),
        encoding="utf-8",
    )

    result = summarize(
        candidates,
        history,
        feedback,
        ledger,
        feedback_aware_ledger,
        observations,
        pievo_summary,
        ensemble_summary,
        ensemble_guard_pievo,
        expanded_replacement,
        expanded_generation,
        latent_local_search,
        latent_local_search_eval,
        latent_local_search_pievo,
        strategy_policy,
        human_review,
        gnn_global,
        generative_training,
        sft_candidate_generation,
        diffusion_flow_candidate_generation,
        diffusion_flow_trained_generation,
        sft_trained_generation,
    )

    assert result["predictor_ensemble_models"] == 6
    assert result["predictor_ensemble_near_target_rows"] == 1045
    assert result["predictor_ensemble_low_disagreement_rows"] == 84
    assert result["predictor_ensemble_high_disagreement_rows"] == 526
    assert result["predictor_ensemble_mean_std_c"] == 32.16
    assert result["predictor_ensemble_mean_abs_best_model_delta_c"] == 30.37
    assert result["pievo_ensemble_guard_selected_rows"] == 6
    assert result["pievo_ensemble_guard_best_distance_c"] == 0.059
    assert result["pievo_ensemble_guard_all_selected_within_guard"] is True
    assert result["pievo_ensemble_guard_mean_selected_std_c"] == 16.4
    assert result["expanded_inventory_replacement_scored"] == 200
    assert result["expanded_inventory_replacement_harness_pass"] == 18
    assert result["expanded_inventory_replacement_literature_template_scored"] == 29
    assert result["expanded_inventory_replacement_literature_template_harness_pass"] == 3
    assert result["expanded_inventory_llm_rag_rows"] == 2
    assert result["expanded_inventory_llm_rag_harness_pass"] == 2
    assert result["expanded_inventory_llm_rag_literature_template_context_rows"] == 1
    assert result["vae_latent_local_search_proposals"] == 200
    assert result["vae_latent_local_search_literature_template_proposals"] == 39
    assert result["vae_latent_local_search_harness_pass"] == 42
    assert result["vae_latent_local_search_best_distance_c"] == 0.20046
    assert result["vae_latent_local_search_literature_template_harness_pass"] == 7
    assert result["vae_latent_local_search_observations"] == 42
    assert result["vae_latent_local_search_pievo_external_rows"] == 42
    assert result["vae_latent_local_search_pievo_best_distance_c"] == 0.059
    assert result["generation_strategy_policy_top_strategy"] == "llm_rag_principle_generation"
    assert result["generation_strategy_policy_eligible_active_strategies"] == 3
    assert result["generation_strategy_policy_suppressed_strategies"] == 1
    assert result["generation_strategy_policy_data_collection_only_strategies"] == 2
    assert result["generation_strategy_policy_total_budget"] == 100
    assert result["human_review_queue_rows"] == 30
    assert result["human_review_ready_for_active_ledger_rows"] == 0
    assert result["human_review_draft_ready_for_active_ledger_rows"] == 0
    assert result["human_review_best_target_distance_c"] == 0.059
    assert result["human_review_process_design_for_dsc_rows"] == 13
    assert result["human_review_high_fidelity_before_dsc_rows"] == 11
    assert result["gnn_global_feature_architecture"] == "mpnn"
    assert result["gnn_global_feature_best_case"] == "mpnn_global"
    assert result["gnn_global_feature_mapek_delta_pct"] == -0.5
    assert result["gnn_global_feature_mae_delta_c"] == -2.0
    assert result["generative_training_sft_examples"] == 7
    assert result["generative_training_sft_ready"] is False
    assert result["generative_training_diffusion_flow_seed_rows"] == 7
    assert result["generative_training_diffusion_flow_ready"] is False
    assert result["generative_training_next_sft_needed"] == 13
    assert result["generative_training_next_diffusion_flow_needed"] == 93
    assert result["sft_candidate_generator_rows"] == 25
    assert result["sft_candidate_generator_harness_pass"] == 25
    assert result["sft_candidate_generator_best_distance_c"] == 0.003
    assert result["sft_candidate_generator_mode"] == "prototype_replay_not_weight_update"
    assert result["sft_candidate_generator_heldout_eval_rows"] == 12
    assert result["sft_candidate_generator_heldout_exact_candidate_matches"] == 3
    assert result["sft_trained_generator_rows"] == 23
    assert result["sft_trained_generator_harness_pass"] == 23
    assert result["sft_trained_generator_best_distance_c"] == 0.006
    assert result["sft_trained_generator_mode"] == "supervised_neural_sft_projection"
    assert result["sft_trained_generator_train_loss_final"] == 0.8
    assert result["sft_trained_generator_eval_loss_final"] == 1.4
    assert result["sft_trained_generator_projection_distance_mean"] == 3.2
    assert result["sft_trained_generator_heldout_eval_rows"] == 19
    assert result["sft_trained_generator_heldout_exact_candidate_matches"] == 0
    assert result["diffusion_flow_candidate_generator_rows"] == 19
    assert result["diffusion_flow_candidate_generator_harness_pass"] == 19
    assert result["diffusion_flow_candidate_generator_best_distance_c"] == 0.004
    assert result["diffusion_flow_candidate_generator_mode"] == "conditional_seed_replay_not_weight_update"
    assert result["diffusion_flow_candidate_generator_heldout_eval_rows"] == 19
    assert result["diffusion_flow_candidate_generator_heldout_exact_candidate_matches"] == 0
    assert result["diffusion_flow_trained_generator_rows"] == 23
    assert result["diffusion_flow_trained_generator_harness_pass"] == 23
    assert result["diffusion_flow_trained_generator_best_distance_c"] == 0.005
    assert result["diffusion_flow_trained_generator_mode"] == "conditional_flow_matching_trained_projection"
    assert result["diffusion_flow_trained_generator_train_loss_final"] == 1.2
    assert result["diffusion_flow_trained_generator_eval_loss_final"] == 1.8
    assert result["diffusion_flow_trained_generator_projection_distance_mean"] == 5.0
