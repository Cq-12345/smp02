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
    predictor_model_registry_summary: Path,
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
    target_conditioned_strategy_policy_summary: Path = Path(
        "artifacts/trail/generation_strategy_policy_target_conditioned/target_conditioned_generation_strategy_summary.json"
    ),
    sparse_target_replacement_expansion_summary: Path = Path(
        "artifacts/trail/generation/sparse_target_replacement_expansion/sparse_target_replacement_expansion_summary.json"
    ),
    human_review_validation_summary: Path = Path("artifacts/trail/human_review/pre_experiment_validation_plan_summary.json"),
    validation_request_summary: Path = Path("artifacts/trail/human_review/validation_request_summary.json"),
    validation_execution_schedule_summary: Path = Path("artifacts/trail/human_review/validation_execution_schedule_summary.json"),
    process_completion_packet_summary: Path = Path("artifacts/trail/human_review/process_completion_packet_summary.json"),
    process_design_suggestion_summary: Path = Path("artifacts/trail/human_review/process_design_suggestion_summary.json"),
    process_approval_summary: Path = Path("artifacts/trail/human_review/process_completion_approval_summary.json"),
    high_fidelity_protocol_summary: Path = Path("artifacts/trail/human_review/high_fidelity_protocol_summary.json"),
    validation_dependency_summary: Path = Path("artifacts/trail/human_review/validation_dependency_summary.json"),
    validation_result_intake_summary: Path = Path("artifacts/trail/human_review/validation_result_intake_summary.json"),
    active_observation_summary: Path = Path("artifacts/trail/human_review/active_high_authority_observation_summary.json"),
    active_evidence_pievo_bridge_summary: Path = Path(
        "artifacts/pievo_faithful_active_evidence_bridge_smoke/active_evidence_pievo_bridge_summary.json"
    ),
    todo_completion_audit_summary: Path = Path("artifacts/trail/workflow/todo_completion_audit_summary.json"),
) -> dict:
    candidates = pd.read_csv(candidate_space) if candidate_space.exists() else pd.DataFrame()
    history = read_json(closed_loop_history, [])
    feedback = read_json(generation_feedback, {})
    ledger = pd.read_csv(generation_ledger) if generation_ledger.exists() else pd.DataFrame()
    feedback_aware = pd.read_csv(feedback_aware_ledger) if feedback_aware_ledger.exists() else pd.DataFrame()
    feedback_aware_observations = pd.read_csv(feedback_aware_observation_ledger) if feedback_aware_observation_ledger.exists() else pd.DataFrame()
    feedback_aware_pievo = read_json(feedback_aware_pievo_summary, {})
    ensemble_disagreement = read_json(ensemble_disagreement_summary, {})
    predictor_model_registry = read_json(predictor_model_registry_summary, {})
    ensemble_guard_pievo = read_json(ensemble_guard_pievo_summary, {})
    expanded_replacement = read_json(expanded_replacement_summary, {})
    expanded_generation = read_json(expanded_generation_summary, {})
    latent_local_search = read_json(vae_latent_local_search_summary, {})
    latent_local_search_eval = read_json(vae_latent_local_search_eval_summary, {})
    latent_local_search_pievo = read_json(vae_latent_local_search_pievo_summary, {})
    latent_local_search_target_sweep = read_json(vae_latent_local_search_target_sweep_summary, {})
    strategy_policy = read_json(generation_strategy_policy_summary, {})
    human_review = read_json(human_review_queue_summary, {})
    human_validation = read_json(human_review_validation_summary, {})
    validation_requests = read_json(validation_request_summary, {})
    validation_execution = read_json(validation_execution_schedule_summary, {})
    process_completion_packet = read_json(process_completion_packet_summary, {})
    process_design_suggestion = read_json(process_design_suggestion_summary, {})
    process_approval = read_json(process_approval_summary, {})
    high_fidelity_protocol = read_json(high_fidelity_protocol_summary, {})
    validation_dependency = read_json(validation_dependency_summary, {})
    validation_result_intake = read_json(validation_result_intake_summary, {})
    active_observations = read_json(active_observation_summary, {})
    active_evidence_pievo_bridge = read_json(active_evidence_pievo_bridge_summary, {})
    todo_completion_audit = read_json(todo_completion_audit_summary, {})
    gnn_global = read_json(gnn_global_feature_summary, {})
    generative_training = read_json(generative_training_summary, {})
    sft_candidate_generation = read_json(sft_candidate_generation_summary, {})
    diffusion_flow_candidate_generation = read_json(diffusion_flow_candidate_generation_summary, {})
    diffusion_flow_trained_generation = read_json(diffusion_flow_trained_generation_summary, {})
    sft_trained_candidate_generation = read_json(sft_trained_candidate_generation_summary, {})
    target_conditioned_strategy_policy = read_json(target_conditioned_strategy_policy_summary, {})
    sparse_target_replacement_expansion = read_json(sparse_target_replacement_expansion_summary, [])
    sparse_rows = sparse_target_replacement_expansion if isinstance(sparse_target_replacement_expansion, list) else []
    sparse_best_eval = min(
        [row.get("replacement_best_distance_c") for row in sparse_rows if row.get("replacement_best_distance_c") is not None],
        default=None,
    )
    sparse_best_selected = min(
        [row.get("best_selected_target_distance_c") for row in sparse_rows if row.get("best_selected_target_distance_c") is not None],
        default=None,
    )
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
        "predictor_model_registry_primary_method": predictor_model_registry.get("primary_method", ""),
        "predictor_model_registry_primary_latent_size": predictor_model_registry.get("primary_latent_size"),
        "predictor_model_registry_primary_mapek_test_pct": predictor_model_registry.get("primary_mapek_test_pct"),
        "predictor_model_registry_primary_mae_test_c": predictor_model_registry.get("primary_mae_test_c"),
        "predictor_model_registry_primary_rmse_test_c": predictor_model_registry.get("primary_rmse_test_c"),
        "predictor_model_registry_primary_r2_test": predictor_model_registry.get("primary_r2_test"),
        "predictor_model_registry_mae_backup_method": predictor_model_registry.get("mae_backup_method", ""),
        "predictor_model_registry_rmse_backup_method": predictor_model_registry.get("rmse_backup_method", ""),
        "predictor_model_registry_r2_backup_method": predictor_model_registry.get("r2_backup_method", ""),
        "predictor_model_registry_uncertainty_provider_method": predictor_model_registry.get("uncertainty_provider_method", ""),
        "predictor_model_registry_ensemble_member_rows": predictor_model_registry.get("ensemble_member_rows", 0),
        "predictor_model_registry_evidence_level": predictor_model_registry.get("evidence_level", ""),
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
        "generation_strategy_policy_high_authority_evidence_status": strategy_policy.get("high_authority_evidence_status", ""),
        "generation_strategy_policy_high_authority_budget_mode": strategy_policy.get("high_authority_budget_mode", ""),
        "generation_strategy_policy_active_evidence_bridge_status": strategy_policy.get("active_evidence_bridge_status", ""),
        "generation_strategy_policy_active_evidence_updates_pievo_posterior": strategy_policy.get(
            "active_evidence_updates_pievo_posterior",
            False,
        ),
        "target_conditioned_strategy_policy_targets": target_conditioned_strategy_policy.get("targets", 0),
        "target_conditioned_strategy_policy_all_targets_allocation_sum_100": target_conditioned_strategy_policy.get(
            "all_targets_allocation_sum_100"
        ),
        "target_conditioned_strategy_policy_top_strategy_by_target": target_conditioned_strategy_policy.get("top_strategy_by_target", {}),
        "target_conditioned_strategy_policy_top_target_specific_strategy_by_target": target_conditioned_strategy_policy.get(
            "top_target_specific_strategy_by_target", {}
        ),
        "target_conditioned_strategy_policy_transfer_budget_by_target": target_conditioned_strategy_policy.get(
            "transfer_budget_by_target", {}
        ),
        "target_conditioned_strategy_policy_sparse_targets": target_conditioned_strategy_policy.get("sparse_targets", []),
        "target_conditioned_strategy_policy_sparse_target_count": target_conditioned_strategy_policy.get("sparse_target_count", 0),
        "target_conditioned_strategy_policy_high_authority_evidence_status": target_conditioned_strategy_policy.get(
            "target_high_authority_evidence_status",
            "",
        ),
        "target_conditioned_strategy_policy_high_authority_budget_mode": target_conditioned_strategy_policy.get(
            "target_high_authority_budget_mode",
            "",
        ),
        "target_conditioned_strategy_policy_high_authority_rows_by_target": target_conditioned_strategy_policy.get(
            "target_high_authority_rows_by_target",
            {},
        ),
        "target_conditioned_strategy_policy_active_evidence_updates_pievo_posterior": target_conditioned_strategy_policy.get(
            "active_evidence_updates_pievo_posterior",
            False,
        ),
        "sparse_target_replacement_expansion_targets": int(len(sparse_rows)),
        "sparse_target_replacement_expansion_target_values": [row.get("target_tg_c") for row in sparse_rows],
        "sparse_target_replacement_expansion_source_candidate_rows": int(sum(row.get("source_candidate_rows", 0) for row in sparse_rows)),
        "sparse_target_replacement_expansion_proposals": int(sum(row.get("replacement_input_proposals", 0) for row in sparse_rows)),
        "sparse_target_replacement_expansion_harness_pass": int(sum(row.get("replacement_harness_pass", 0) for row in sparse_rows)),
        "sparse_target_replacement_expansion_generation_record_harness_pass": int(
            sum(row.get("generation_record_harness_pass", 0) for row in sparse_rows)
        ),
        "sparse_target_replacement_expansion_best_eval_distance_c": sparse_best_eval,
        "sparse_target_replacement_expansion_best_selected_distance_c": sparse_best_selected,
        "sparse_target_replacement_expansion_all_selected_pass": bool(sparse_rows)
        and all(bool(row.get("pievo_all_selected_pass", False)) for row in sparse_rows),
        "sparse_target_replacement_expansion_all_selected_within_guard": bool(sparse_rows)
        and all(bool(row.get("pievo_all_selected_within_guard", False)) for row in sparse_rows),
        "human_review_queue_rows": human_review.get("queue_rows", 0),
        "human_review_ready_for_active_ledger_rows": human_review.get("ready_for_active_ledger_rows", 0),
        "human_review_draft_ready_for_active_ledger_rows": human_review.get("draft_ready_for_active_ledger_rows", 0),
        "human_review_best_target_distance_c": human_review.get("best_target_distance_c"),
        "human_review_process_design_for_dsc_rows": human_review.get("review_priorities", {}).get("process_design_for_dsc", 0),
        "human_review_high_fidelity_before_dsc_rows": human_review.get("review_priorities", {}).get("high_fidelity_before_dsc", 0),
        "human_review_target_counts": human_review.get("target_counts", {}),
        "human_review_candidate_origin_counts": human_review.get("candidate_origin_counts", {}),
        "human_validation_plan_rows": human_validation.get("plan_rows", 0),
        "human_validation_process_completion_required_rows": human_validation.get("process_completion_required_rows", 0),
        "human_validation_high_fidelity_required_rows": human_validation.get("high_fidelity_required_rows", 0),
        "human_validation_dsc_ready_without_process_completion_rows": human_validation.get(
            "dsc_ready_without_process_completion_rows", 0
        ),
        "human_validation_target_counts": human_validation.get("target_counts", {}),
        "human_validation_lane_counts": human_validation.get("validation_lane_counts", {}),
        "human_validation_candidate_origin_counts": human_validation.get("candidate_origin_counts", {}),
        "human_validation_best_target_distance_c": human_validation.get("best_target_distance_c"),
        "human_validation_best_score": human_validation.get("best_validation_score"),
        "validation_request_rows": validation_requests.get("request_rows", 0),
        "validation_request_process_completion_rows": validation_requests.get("process_completion_request_rows", 0),
        "validation_request_high_fidelity_rows": validation_requests.get("high_fidelity_request_rows", 0),
        "validation_request_real_dsc_rows": validation_requests.get("real_dsc_request_rows", 0),
        "validation_request_blocked_by_process_completion_rows": validation_requests.get("blocked_by_process_completion_rows", 0),
        "validation_request_task_type_counts": validation_requests.get("task_type_counts", {}),
        "validation_request_expected_observation_source_counts": validation_requests.get("expected_observation_source_counts", {}),
        "validation_request_target_counts": validation_requests.get("target_counts", {}),
        "validation_request_max_authority_weight_if_completed": validation_requests.get("max_authority_weight_if_completed", 0),
        "validation_execution_schedule_rows": validation_execution.get("schedule_rows", 0),
        "validation_execution_immediate_rows": validation_execution.get("immediate_executable_rows", 0),
        "validation_execution_immediate_batch_rows": validation_execution.get("immediate_batch_rows", 0),
        "validation_execution_blocked_rows": validation_execution.get("blocked_rows", 0),
        "validation_execution_process_completion_unlock_rows": validation_execution.get("process_completion_unlock_rows", 0),
        "validation_execution_blocked_observation_rows": validation_execution.get("blocked_observation_rows", 0),
        "validation_execution_immediate_batch_target_counts": validation_execution.get("immediate_batch_target_counts", {}),
        "validation_execution_phase_counts": validation_execution.get("phase_counts", {}),
        "process_completion_packet_rows": process_completion_packet.get("selected_process_completion_rows", 0),
        "process_completion_packet_draft_matches": process_completion_packet.get("draft_record_matches", 0),
        "process_completion_packet_unlocks_observation_rows": process_completion_packet.get("unlocks_observation_rows", 0),
        "process_completion_packet_record_pass_rows": process_completion_packet.get("process_record_pass_rows", 0),
        "process_completion_packet_ready_for_active_ledger_rows": process_completion_packet.get("ready_for_active_ledger_rows", 0),
        "process_completion_packet_incomplete_rows": process_completion_packet.get("process_incomplete_rows", 0),
        "process_completion_packet_target_counts": process_completion_packet.get("target_counts", {}),
        "process_completion_packet_required_field_frequency": process_completion_packet.get("required_field_frequency", {}),
        "process_design_suggestion_rows": process_design_suggestion.get("suggestion_rows", 0),
        "process_design_suggestion_high_tg_rows": process_design_suggestion.get("high_tg_rows", 0),
        "process_design_suggestion_high_sigma_rows": process_design_suggestion.get("high_sigma_rows", 0),
        "process_design_suggestion_can_unlock_after_human_approval_rows": process_design_suggestion.get(
            "can_unlock_observation_after_human_approval_rows",
            0,
        ),
        "process_design_suggestion_record_pass_rows": process_design_suggestion.get(
            "suggested_process_record_pass_rows",
            0,
        ),
        "process_design_suggestion_fields_complete_rows": process_design_suggestion.get(
            "suggested_process_fields_complete_rows",
            0,
        ),
        "process_design_suggestion_ready_for_active_ledger_rows": process_design_suggestion.get(
            "suggested_ready_for_active_ledger_rows",
            0,
        ),
        "process_design_suggestion_template_counts": process_design_suggestion.get("process_template_counts", {}),
        "process_design_suggestion_suggested_field_frequency": process_design_suggestion.get("suggested_field_frequency", {}),
        "process_design_suggestion_evidence_level": process_design_suggestion.get("evidence_level", ""),
        "process_approval_template_rows": process_approval.get("approval_template_rows", 0),
        "process_approval_submitted_rows": process_approval.get("submitted_approval_rows", 0),
        "process_approval_accepted_rows": process_approval.get("accepted_process_approval_rows", 0),
        "process_approval_rejected_rows": process_approval.get("rejected_process_approval_rows", 0),
        "process_approval_ready_process_record_rows": process_approval.get("ready_process_record_rows", 0),
        "process_approval_unblocked_observation_request_rows": process_approval.get("unblocked_observation_request_rows", 0),
        "process_approval_unblocked_target_counts": process_approval.get("unblocked_target_counts", {}),
        "process_approval_unblocked_source_counts": process_approval.get("unblocked_source_counts", {}),
        "process_approval_gate_status": process_approval.get("approval_gate_status", ""),
        "high_fidelity_protocol_rows": high_fidelity_protocol.get("high_fidelity_protocol_rows", 0),
        "high_fidelity_protocol_ready_rows": high_fidelity_protocol.get("ready_protocol_rows", 0),
        "high_fidelity_protocol_blocked_rows": high_fidelity_protocol.get("blocked_protocol_rows", 0),
        "high_fidelity_protocol_process_approval_unblocked_rows": high_fidelity_protocol.get(
            "process_approval_unblocked_rows",
            0,
        ),
        "high_fidelity_protocol_target_counts": high_fidelity_protocol.get("target_counts", {}),
        "high_fidelity_protocol_method_frequency": high_fidelity_protocol.get("method_frequency", {}),
        "high_fidelity_protocol_approval_gate_status": high_fidelity_protocol.get("approval_gate_status", ""),
        "high_fidelity_protocol_evidence_level": high_fidelity_protocol.get("evidence_level", ""),
        "validation_dependency_node_rows": validation_dependency.get("node_rows", 0),
        "validation_dependency_edge_rows": validation_dependency.get("edge_rows", 0),
        "validation_dependency_blocked_or_pending_edge_rows": validation_dependency.get("blocked_or_pending_edge_rows", 0),
        "validation_dependency_pending_process_approval_rows": validation_dependency.get("pending_process_approval_rows", 0),
        "validation_dependency_ready_high_fidelity_protocol_rows": validation_dependency.get(
            "ready_high_fidelity_protocol_rows",
            0,
        ),
        "validation_dependency_blocked_high_fidelity_protocol_rows": validation_dependency.get(
            "blocked_high_fidelity_protocol_rows",
            0,
        ),
        "validation_dependency_active_evidence_rows": validation_dependency.get("active_evidence_rows", 0),
        "validation_dependency_ready_next_action": validation_dependency.get("ready_next_action", ""),
        "validation_dependency_ready_next_action_rows": validation_dependency.get("ready_next_action_rows", 0),
        "validation_dependency_blocker_reason_counts": validation_dependency.get("blocker_reason_counts", {}),
        "validation_dependency_evidence_level": validation_dependency.get("evidence_level", ""),
        "validation_result_template_rows": validation_result_intake.get("template_rows", 0),
        "validation_result_rows": validation_result_intake.get("result_rows", 0),
        "validation_result_accepted_rows": validation_result_intake.get("accepted_result_rows", 0),
        "validation_result_rejected_rows": validation_result_intake.get("rejected_result_rows", 0),
        "validation_result_observation_ledger_pass_rows": validation_result_intake.get("observation_ledger_pass_rows", 0),
        "validation_result_rejection_reason_counts": validation_result_intake.get("rejection_reason_counts", {}),
        "validation_result_accepted_source_counts": validation_result_intake.get("accepted_source_counts", {}),
        "active_observation_input_rows": active_observations.get("input_rows", 0),
        "active_observation_rows": active_observations.get("active_rows", 0),
        "active_observation_validation_result_rows": active_observations.get("validation_result_active_rows", 0),
        "active_observation_source_counts": active_observations.get("active_source_counts", {}),
        "active_observation_authority_weight_sum": active_observations.get("authority_weight_sum", 0),
        "active_observation_max_authority_weight": active_observations.get("max_authority_weight"),
        "active_observation_mean_target_distance_c": active_observations.get("mean_target_distance_c"),
        "active_observation_mean_weighted_reward": active_observations.get("mean_weighted_reward"),
        "active_evidence_pievo_bridge_status": active_evidence_pievo_bridge.get("bridge_status", ""),
        "active_evidence_pievo_bridge_accepted_rows": active_evidence_pievo_bridge.get("external_accepted_rows", 0),
        "active_evidence_pievo_bridge_rejected_rows": active_evidence_pievo_bridge.get("external_rejected_rows", 0),
        "active_evidence_pievo_bridge_posterior_history_rows": active_evidence_pievo_bridge.get("posterior_history_rows", 0),
        "active_evidence_pievo_bridge_total_authority_weight": active_evidence_pievo_bridge.get("total_authority_weight", 0),
        "active_evidence_pievo_bridge_posterior_entropy": active_evidence_pievo_bridge.get("posterior_entropy"),
        "active_evidence_pievo_bridge_map_principle": active_evidence_pievo_bridge.get("map_principle", ""),
        "active_evidence_updates_pievo_posterior": active_evidence_pievo_bridge.get("active_evidence_updates_posterior", False),
        "todo_completion_audit_rows": todo_completion_audit.get("audit_rows", 0),
        "todo_completion_implemented_rows": todo_completion_audit.get("implemented_rows", 0),
        "todo_completion_deferred_rows": todo_completion_audit.get("deferred_rows", 0),
        "todo_completion_needs_real_or_high_fidelity_evidence_rows": todo_completion_audit.get(
            "needs_real_or_high_fidelity_evidence_rows",
            0,
        ),
        "todo_completion_missing_evidence_rows": todo_completion_audit.get("missing_evidence_rows", 0),
        "todo_completion_non_deferred_all_evidence_present": todo_completion_audit.get(
            "non_deferred_all_evidence_present",
            False,
        ),
        "todo_completion_primary_open_blocker": todo_completion_audit.get("primary_open_blocker", ""),
        "todo_completion_evidence_level": todo_completion_audit.get("evidence_level", ""),
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
    parser.add_argument(
        "--predictor-model-registry-summary",
        default="artifacts/trail/predictors/model_selection_registry/predictor_model_selection_summary.json",
    )
    parser.add_argument("--ensemble-guard-pievo-summary", default="artifacts/pievo_faithful_ensemble_guard_195_smoke/pievo_faithful_summary.json")
    parser.add_argument("--expanded-replacement-summary", default="artifacts/trail/generation/expanded_inventory_replacement_eval/replacement_eval_summary.json")
    parser.add_argument("--expanded-generation-summary", default="artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag/generation_record_summary.json")
    parser.add_argument("--vae-latent-local-search-summary", default="artifacts/trail/generation/vae_latent_local_search/latent_local_search_summary.json")
    parser.add_argument("--vae-latent-local-search-eval-summary", default="artifacts/trail/generation/vae_latent_local_search_eval/replacement_eval_summary.json")
    parser.add_argument("--vae-latent-local-search-pievo-summary", default="artifacts/pievo_faithful_vae_latent_local_search_195_smoke/pievo_faithful_summary.json")
    parser.add_argument("--vae-latent-local-search-target-sweep-summary", default="artifacts/trail/generation/vae_latent_local_search_target_sweep/vae_latent_local_search_target_sweep_aggregate.json")
    parser.add_argument("--generation-strategy-policy-summary", default="artifacts/trail/generation_strategy_policy/generation_strategy_bandit_summary.json")
    parser.add_argument("--human-review-queue-summary", default="artifacts/trail/human_review/human_experiment_review_queue_summary.json")
    parser.add_argument(
        "--human-review-validation-summary",
        default="artifacts/trail/human_review/pre_experiment_validation_plan_summary.json",
    )
    parser.add_argument(
        "--validation-request-summary",
        default="artifacts/trail/human_review/validation_request_summary.json",
    )
    parser.add_argument(
        "--validation-execution-schedule-summary",
        default="artifacts/trail/human_review/validation_execution_schedule_summary.json",
    )
    parser.add_argument(
        "--process-completion-packet-summary",
        default="artifacts/trail/human_review/process_completion_packet_summary.json",
    )
    parser.add_argument(
        "--process-design-suggestion-summary",
        default="artifacts/trail/human_review/process_design_suggestion_summary.json",
    )
    parser.add_argument(
        "--process-approval-summary",
        default="artifacts/trail/human_review/process_completion_approval_summary.json",
    )
    parser.add_argument(
        "--high-fidelity-protocol-summary",
        default="artifacts/trail/human_review/high_fidelity_protocol_summary.json",
    )
    parser.add_argument(
        "--validation-dependency-summary",
        default="artifacts/trail/human_review/validation_dependency_summary.json",
    )
    parser.add_argument(
        "--validation-result-intake-summary",
        default="artifacts/trail/human_review/validation_result_intake_summary.json",
    )
    parser.add_argument(
        "--active-observation-summary",
        default="artifacts/trail/human_review/active_high_authority_observation_summary.json",
    )
    parser.add_argument(
        "--active-evidence-pievo-bridge-summary",
        default="artifacts/pievo_faithful_active_evidence_bridge_smoke/active_evidence_pievo_bridge_summary.json",
    )
    parser.add_argument(
        "--todo-completion-audit-summary",
        default="artifacts/trail/workflow/todo_completion_audit_summary.json",
    )
    parser.add_argument("--gnn-global-feature-summary", default="artifacts/trail/gnn_global_feature_smoke/gnn_global_feature_summary.json")
    parser.add_argument("--generative-training-summary", default="artifacts/trail/generation/generative_training_sets/generative_training_summary.json")
    parser.add_argument("--sft-candidate-generation-summary", default="artifacts/trail/generation/sft_candidate_dry_run/generation_record_summary.json")
    parser.add_argument("--diffusion-flow-candidate-generation-summary", default="artifacts/trail/generation/diffusion_flow_candidate_dry_run/generation_record_summary.json")
    parser.add_argument("--diffusion-flow-trained-generation-summary", default="artifacts/trail/generation/diffusion_flow_trained_generator/generation_record_summary.json")
    parser.add_argument("--sft-trained-candidate-generation-summary", default="artifacts/trail/generation/sft_trained_projection_generator/generation_record_summary.json")
    parser.add_argument(
        "--target-conditioned-strategy-policy-summary",
        default="artifacts/trail/generation_strategy_policy_target_conditioned/target_conditioned_generation_strategy_summary.json",
    )
    parser.add_argument(
        "--sparse-target-replacement-expansion-summary",
        default="artifacts/trail/generation/sparse_target_replacement_expansion/sparse_target_replacement_expansion_summary.json",
    )
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
        Path(args.predictor_model_registry_summary),
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
        Path(args.target_conditioned_strategy_policy_summary),
        Path(args.sparse_target_replacement_expansion_summary),
        Path(args.human_review_validation_summary),
        Path(args.validation_request_summary),
        Path(args.validation_execution_schedule_summary),
        Path(args.process_completion_packet_summary),
        Path(args.process_design_suggestion_summary),
        Path(args.process_approval_summary),
        Path(args.high_fidelity_protocol_summary),
        Path(args.validation_dependency_summary),
        Path(args.validation_result_intake_summary),
        Path(args.active_observation_summary),
        Path(args.active_evidence_pievo_bridge_summary),
        Path(args.todo_completion_audit_summary),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
