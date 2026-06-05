from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


AGENTS = {
    "space_agent": "界定搜索空间：官能团、反应兼容性、摩尔比网格。",
    "generator_agent": "生成候选假设：模板、VAE replacement、prompt/RAG、SFT dry-run、trained SFT projection、diffusion/flow dry-run、trained flow projection，以及未来直接神经生成模型。",
    "rag_generator_agent": "读取 RAG 上下文和 strict strategy feedback，生成 auditable generation records。",
    "predictor_agent": "评估假设：VAE-WVCM model zoo、GNN、ensemble disagreement、uncertainty/OOD。",
    "harness_agent": "硬约束过滤：RDKit、比例、目标窗口、官能团反应兼容性。",
    "feedback_agent": "失败回流：统计 generation ledger 和 Harness rejection，给下一轮生成器约束。",
    "principle_agent": "更新原则：PiEvo full-history posterior、MAP residual anomaly、IDS 选择。",
    "human_review_agent": "人工闭环：审核候选、补工艺条件、决定是否进入真实/高保真 observation ledger。",
}


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def summarize(
    candidate_space: Path,
    closed_loop_history: Path,
    generation_feedback: Path,
    generation_ledger: Path,
    feedback_aware_ledger: Path,
    feedback_aware_observation_ledger: Path,
    feedback_aware_pievo_summary: Path,
    ensemble_disagreement_summary: Path,
    ensemble_guard_pievo_summary: Path,
    expanded_replacement_summary: Path,
    expanded_generation_summary: Path,
    vae_latent_local_search_summary: Path,
    vae_latent_local_search_eval_summary: Path,
    vae_latent_local_search_pievo_summary: Path,
    vae_latent_local_search_target_sweep_summary: Path,
    generation_strategy_policy_summary: Path,
    human_review_queue_summary: Path,
    gnn_global_feature_summary: Path,
    generative_training_summary: Path,
    sft_candidate_generation_summary: Path,
    diffusion_flow_candidate_generation_summary: Path = Path("artifacts/trail/generation/diffusion_flow_candidate_dry_run/generation_record_summary.json"),
    diffusion_flow_trained_generation_summary: Path = Path("artifacts/trail/generation/diffusion_flow_trained_generator/generation_record_summary.json"),
    sft_trained_candidate_generation_summary: Path = Path("artifacts/trail/generation/sft_trained_projection_generator/generation_record_summary.json"),
) -> dict:
    candidates = pd.read_csv(candidate_space) if candidate_space.exists() else pd.DataFrame()
    history = read_json(closed_loop_history, [])
    feedback = read_json(generation_feedback, {})
    ledger = pd.read_csv(generation_ledger) if generation_ledger.exists() else pd.DataFrame()
    feedback_aware = pd.read_csv(feedback_aware_ledger) if feedback_aware_ledger.exists() else pd.DataFrame()
    feedback_aware_observations = pd.read_csv(feedback_aware_observation_ledger) if feedback_aware_observation_ledger.exists() else pd.DataFrame()
    feedback_aware_pievo = read_json(feedback_aware_pievo_summary, {})
    ensemble_disagreement = read_json(ensemble_disagreement_summary, {})
    ensemble_guard_pievo = read_json(ensemble_guard_pievo_summary, {})
    expanded_replacement = read_json(expanded_replacement_summary, {})
    expanded_generation = read_json(expanded_generation_summary, {})
    latent_local_search = read_json(vae_latent_local_search_summary, {})
    latent_local_search_eval = read_json(vae_latent_local_search_eval_summary, {})
    latent_local_search_pievo = read_json(vae_latent_local_search_pievo_summary, {})
    latent_local_search_target_sweep = read_json(vae_latent_local_search_target_sweep_summary, {})
    strategy_policy = read_json(generation_strategy_policy_summary, {})
    human_review = read_json(human_review_queue_summary, {})
    gnn_global = read_json(gnn_global_feature_summary, {})
    generative_training = read_json(generative_training_summary, {})
    sft_candidate_generation = read_json(sft_candidate_generation_summary, {})
    diffusion_flow_candidate_generation = read_json(diffusion_flow_candidate_generation_summary, {})
    diffusion_flow_trained_generation = read_json(diffusion_flow_trained_generation_summary, {})
    sft_trained_candidate_generation = read_json(sft_trained_candidate_generation_summary, {})
    return {
        "agents": AGENTS,
        "candidate_rows": int(len(candidates)),
        "best_candidates": candidates.head(10).to_dict(orient="records") if not candidates.empty else [],
        "closed_loop_history": history,
        "generation_ledger_rows": int(len(ledger)),
        "generation_harness_pass": int(ledger["harness_pass"].fillna(False).astype(bool).sum()) if not ledger.empty and "harness_pass" in ledger else 0,
        "feedback_aware_llm_rag_rows": int(len(feedback_aware)),
        "feedback_aware_llm_rag_harness_pass": (
            int(feedback_aware["harness_pass"].fillna(False).astype(bool).sum())
            if not feedback_aware.empty and "harness_pass" in feedback_aware
            else 0
        ),
        "feedback_aware_llm_rag_observation_rows": int(len(feedback_aware_observations)),
        "feedback_aware_llm_rag_observation_pass": (
            int(feedback_aware_observations["ledger_pass"].fillna(False).astype(bool).sum())
            if not feedback_aware_observations.empty and "ledger_pass" in feedback_aware_observations
            else 0
        ),
        "feedback_aware_llm_rag_pievo_best_distance_c": feedback_aware_pievo.get("best_selected_target_distance_c"),
        "feedback_aware_llm_rag_pievo_external_rows": feedback_aware_pievo.get("external_observation_summary", {}).get("accepted_rows", 0),
        "predictor_ensemble_models": ensemble_disagreement.get("ensemble_models", 0),
        "predictor_ensemble_near_target_rows": ensemble_disagreement.get("near_target_rows", 0),
        "predictor_ensemble_low_disagreement_rows": ensemble_disagreement.get("near_target_low_disagreement_rows", 0),
        "predictor_ensemble_high_disagreement_rows": ensemble_disagreement.get("near_target_high_disagreement_rows", 0),
        "predictor_ensemble_mean_std_c": ensemble_disagreement.get("mean_ensemble_std_c"),
        "predictor_ensemble_mean_abs_best_model_delta_c": ensemble_disagreement.get("mean_abs_best_model_delta_c"),
        "pievo_ensemble_guard_selected_rows": ensemble_guard_pievo.get("selected_rows", 0),
        "pievo_ensemble_guard_best_distance_c": ensemble_guard_pievo.get("best_selected_target_distance_c"),
        "pievo_ensemble_guard_all_selected_within_guard": ensemble_guard_pievo.get("all_selected_within_ensemble_disagreement_guard"),
        "pievo_ensemble_guard_mean_selected_std_c": ensemble_guard_pievo.get("mean_selected_predictor_ensemble_std_tg_c"),
        "expanded_inventory_replacement_scored": expanded_replacement.get("scored_formulas", 0),
        "expanded_inventory_replacement_harness_pass": expanded_replacement.get("harness_pass", 0),
        "expanded_inventory_replacement_literature_template_scored": expanded_replacement.get("literature_template_scored", 0),
        "expanded_inventory_replacement_literature_template_harness_pass": expanded_replacement.get("literature_template_harness_pass", 0),
        "expanded_inventory_llm_rag_rows": expanded_generation.get("input_rows", 0),
        "expanded_inventory_llm_rag_harness_pass": expanded_generation.get("harness_pass_rows", 0),
        "expanded_inventory_llm_rag_literature_template_context_rows": expanded_generation.get("literature_template_context_rows", 0),
        "vae_latent_local_search_proposals": latent_local_search.get("proposals", 0),
        "vae_latent_local_search_literature_template_proposals": latent_local_search.get("literature_template_proposals", 0),
        "vae_latent_local_search_harness_pass": latent_local_search_eval.get("harness_pass", 0),
        "vae_latent_local_search_best_distance_c": latent_local_search_eval.get("best_distance_c"),
        "vae_latent_local_search_literature_template_harness_pass": latent_local_search_eval.get("literature_template_harness_pass", 0),
        "vae_latent_local_search_observations": latent_local_search_eval.get("replacement_observations", 0),
        "vae_latent_local_search_pievo_external_rows": latent_local_search_pievo.get("external_observation_summary", {}).get("accepted_rows", 0),
        "vae_latent_local_search_pievo_best_distance_c": latent_local_search_pievo.get("best_selected_target_distance_c"),
        "vae_latent_local_search_target_sweep_targets": latent_local_search_target_sweep.get("targets", 0),
        "vae_latent_local_search_target_sweep_total_harness_pass": latent_local_search_target_sweep.get("total_latent_harness_pass", 0),
        "vae_latent_local_search_target_sweep_total_observations": latent_local_search_target_sweep.get("total_latent_observations", 0),
        "vae_latent_local_search_target_sweep_all_selected_pass": latent_local_search_target_sweep.get("all_pievo_selected_pass"),
        "vae_latent_local_search_target_sweep_all_selected_within_guard": latent_local_search_target_sweep.get("all_pievo_selected_within_guard"),
        "vae_latent_local_search_target_sweep_best_target_tg_c": latent_local_search_target_sweep.get("best_target_tg_c"),
        "vae_latent_local_search_target_sweep_best_selected_distance_c": latent_local_search_target_sweep.get("best_selected_target_distance_c"),
        "vae_latent_local_search_target_sweep_best_target_map_principle": latent_local_search_target_sweep.get("best_target_map_principle"),
        "generation_strategy_policy_top_strategy": strategy_policy.get("top_strategy"),
        "generation_strategy_policy_eligible_active_strategies": strategy_policy.get("eligible_active_strategies", 0),
        "generation_strategy_policy_suppressed_strategies": strategy_policy.get("suppressed_strategies", 0),
        "generation_strategy_policy_data_collection_only_strategies": strategy_policy.get("data_collection_only_strategies", 0),
        "generation_strategy_policy_total_budget": strategy_policy.get("total_budget", 0),
        "human_review_queue_rows": human_review.get("queue_rows", 0),
        "human_review_ready_for_active_ledger_rows": human_review.get("ready_for_active_ledger_rows", 0),
        "human_review_draft_ready_for_active_ledger_rows": human_review.get("draft_ready_for_active_ledger_rows", 0),
        "human_review_best_target_distance_c": human_review.get("best_target_distance_c"),
        "human_review_process_design_for_dsc_rows": human_review.get("review_priorities", {}).get("process_design_for_dsc", 0),
        "human_review_high_fidelity_before_dsc_rows": human_review.get("review_priorities", {}).get("high_fidelity_before_dsc", 0),
        "gnn_global_feature_architecture": gnn_global.get("architecture"),
        "gnn_global_feature_best_case": gnn_global.get("best_case"),
        "gnn_global_feature_baseline_mapek_test_pct": gnn_global.get("baseline_mapek_test_pct"),
        "gnn_global_feature_global_mapek_test_pct": gnn_global.get("global_mapek_test_pct"),
        "gnn_global_feature_mapek_delta_pct": gnn_global.get("global_minus_baseline_mapek_test_pct"),
        "gnn_global_feature_mae_delta_c": gnn_global.get("global_minus_baseline_mae_test_c"),
        "generative_training_sft_examples": generative_training.get("sft_examples", 0),
        "generative_training_sft_ready": generative_training.get("sft_ready", False),
        "generative_training_diffusion_flow_seed_rows": generative_training.get("diffusion_flow_seed_rows", 0),
        "generative_training_diffusion_flow_ready": generative_training.get("diffusion_flow_ready", False),
        "generative_training_next_sft_needed": generative_training.get("next_data_needed_for_sft", 0),
        "generative_training_next_diffusion_flow_needed": generative_training.get("next_data_needed_for_diffusion_flow", 0),
        "sft_candidate_generator_rows": sft_candidate_generation.get("input_rows", 0),
        "sft_candidate_generator_harness_pass": sft_candidate_generation.get("harness_pass_rows", 0),
        "sft_candidate_generator_best_distance_c": sft_candidate_generation.get("best_distance_c"),
        "sft_candidate_generator_mode": sft_candidate_generation.get("generator_mode", ""),
        "sft_candidate_generator_heldout_eval_rows": sft_candidate_generation.get("heldout_eval_rows", 0),
        "sft_candidate_generator_heldout_exact_candidate_matches": sft_candidate_generation.get("heldout_exact_candidate_matches", 0),
        "sft_trained_generator_rows": sft_trained_candidate_generation.get("input_rows", 0),
        "sft_trained_generator_harness_pass": sft_trained_candidate_generation.get("harness_pass_rows", 0),
        "sft_trained_generator_best_distance_c": sft_trained_candidate_generation.get("best_distance_c"),
        "sft_trained_generator_mode": sft_trained_candidate_generation.get("generator_mode", ""),
        "sft_trained_generator_train_loss_final": sft_trained_candidate_generation.get("train_loss_final"),
        "sft_trained_generator_eval_loss_final": sft_trained_candidate_generation.get("eval_loss_final"),
        "sft_trained_generator_projection_distance_mean": sft_trained_candidate_generation.get("projection_distance_mean"),
        "sft_trained_generator_heldout_eval_rows": sft_trained_candidate_generation.get("heldout_eval_rows", 0),
        "sft_trained_generator_heldout_exact_candidate_matches": sft_trained_candidate_generation.get("heldout_exact_candidate_matches", 0),
        "diffusion_flow_candidate_generator_rows": diffusion_flow_candidate_generation.get("input_rows", 0),
        "diffusion_flow_candidate_generator_harness_pass": diffusion_flow_candidate_generation.get("harness_pass_rows", 0),
        "diffusion_flow_candidate_generator_best_distance_c": diffusion_flow_candidate_generation.get("best_distance_c"),
        "diffusion_flow_candidate_generator_mode": diffusion_flow_candidate_generation.get("generator_mode", ""),
        "diffusion_flow_candidate_generator_heldout_eval_rows": diffusion_flow_candidate_generation.get("heldout_eval_rows", 0),
        "diffusion_flow_candidate_generator_heldout_exact_candidate_matches": diffusion_flow_candidate_generation.get("heldout_exact_candidate_matches", 0),
        "diffusion_flow_trained_generator_rows": diffusion_flow_trained_generation.get("input_rows", 0),
        "diffusion_flow_trained_generator_harness_pass": diffusion_flow_trained_generation.get("harness_pass_rows", 0),
        "diffusion_flow_trained_generator_best_distance_c": diffusion_flow_trained_generation.get("best_distance_c"),
        "diffusion_flow_trained_generator_mode": diffusion_flow_trained_generation.get("generator_mode", ""),
        "diffusion_flow_trained_generator_train_loss_final": diffusion_flow_trained_generation.get("train_loss_final"),
        "diffusion_flow_trained_generator_eval_loss_final": diffusion_flow_trained_generation.get("eval_loss_final"),
        "diffusion_flow_trained_generator_projection_distance_mean": diffusion_flow_trained_generation.get("projection_distance_mean"),
        "generation_feedback": feedback,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-space", default="artifacts/reproduce/discovery/candidate_space_top_scored.csv")
    parser.add_argument("--history", default="artifacts/reproduce/closed_loop/closed_loop_history.json")
    parser.add_argument("--generation-feedback", default="artifacts/trail/generation_feedback_strict/generation_feedback_summary.json")
    parser.add_argument("--generation-ledger", default="artifacts/trail/generation/prompt_records/generation_record_ledger.csv")
    parser.add_argument("--feedback-aware-ledger", default="artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv")
    parser.add_argument("--feedback-aware-observation-ledger", default="artifacts/trail/generation/feedback_aware_llm_rag_observations/generation_observation_ledger.csv")
    parser.add_argument("--feedback-aware-pievo-summary", default="artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke/pievo_faithful_summary.json")
    parser.add_argument("--ensemble-disagreement-summary", default="artifacts/trail/predictors/ensemble_disagreement/ensemble_disagreement_summary.json")
    parser.add_argument("--ensemble-guard-pievo-summary", default="artifacts/pievo_faithful_ensemble_guard_195_smoke/pievo_faithful_summary.json")
    parser.add_argument("--expanded-replacement-summary", default="artifacts/trail/generation/expanded_inventory_replacement_eval/replacement_eval_summary.json")
    parser.add_argument("--expanded-generation-summary", default="artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag/generation_record_summary.json")
    parser.add_argument("--vae-latent-local-search-summary", default="artifacts/trail/generation/vae_latent_local_search/latent_local_search_summary.json")
    parser.add_argument("--vae-latent-local-search-eval-summary", default="artifacts/trail/generation/vae_latent_local_search_eval/replacement_eval_summary.json")
    parser.add_argument("--vae-latent-local-search-pievo-summary", default="artifacts/pievo_faithful_vae_latent_local_search_195_smoke/pievo_faithful_summary.json")
    parser.add_argument("--vae-latent-local-search-target-sweep-summary", default="artifacts/trail/generation/vae_latent_local_search_target_sweep/vae_latent_local_search_target_sweep_aggregate.json")
    parser.add_argument("--generation-strategy-policy-summary", default="artifacts/trail/generation_strategy_policy/generation_strategy_bandit_summary.json")
    parser.add_argument("--human-review-queue-summary", default="artifacts/trail/human_review/human_experiment_review_queue_summary.json")
    parser.add_argument("--gnn-global-feature-summary", default="artifacts/trail/gnn_global_feature_smoke/gnn_global_feature_summary.json")
    parser.add_argument("--generative-training-summary", default="artifacts/trail/generation/generative_training_sets/generative_training_summary.json")
    parser.add_argument("--sft-candidate-generation-summary", default="artifacts/trail/generation/sft_candidate_dry_run/generation_record_summary.json")
    parser.add_argument("--diffusion-flow-candidate-generation-summary", default="artifacts/trail/generation/diffusion_flow_candidate_dry_run/generation_record_summary.json")
    parser.add_argument("--diffusion-flow-trained-generation-summary", default="artifacts/trail/generation/diffusion_flow_trained_generator/generation_record_summary.json")
    parser.add_argument("--sft-trained-candidate-generation-summary", default="artifacts/trail/generation/sft_trained_projection_generator/generation_record_summary.json")
    parser.add_argument("--out", default="artifacts/trail/workflow/multi_agent_summary.json")
    args = parser.parse_args()
    result = summarize(
        Path(args.candidate_space),
        Path(args.history),
        Path(args.generation_feedback),
        Path(args.generation_ledger),
        Path(args.feedback_aware_ledger),
        Path(args.feedback_aware_observation_ledger),
        Path(args.feedback_aware_pievo_summary),
        Path(args.ensemble_disagreement_summary),
        Path(args.ensemble_guard_pievo_summary),
        Path(args.expanded_replacement_summary),
        Path(args.expanded_generation_summary),
        Path(args.vae_latent_local_search_summary),
        Path(args.vae_latent_local_search_eval_summary),
        Path(args.vae_latent_local_search_pievo_summary),
        Path(args.vae_latent_local_search_target_sweep_summary),
        Path(args.generation_strategy_policy_summary),
        Path(args.human_review_queue_summary),
        Path(args.gnn_global_feature_summary),
        Path(args.generative_training_summary),
        Path(args.sft_candidate_generation_summary),
        Path(args.diffusion_flow_candidate_generation_summary),
        Path(args.diffusion_flow_trained_generation_summary),
        Path(args.sft_trained_candidate_generation_summary),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
