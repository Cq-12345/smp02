# Closed-loop Workflow

本仓库把 README / TODO 中的闭环要求实现为 in-silico workflow。当前仍使用单一小分子 SMILES / MoleCode，不做商品级复杂组分或聚合物超图表示。

1. 界定搜索空间：
   - 从扩充 XLSX 提取唯一单体。
   - 用 SMARTS 分类官能团。
   - 用兼容性矩阵过滤化学上合理的单体对。
2. 生成假设：
   - 对每个合理单体对枚举摩尔比。
   - 默认 5%-95%，步长 5%。
3. 预测/评估：
   - VAE 编码单体。
   - WVCM 生成配方向量。
   - model zoo / GNN / uncertainty / OOD 评估 Tg。
   - predictor ensemble disagreement 标记单一模型和强模型集体判断的偏差。
   - 按可变 `target_tg_c` 和 target distance 排序。
   - Harness 检查 RDKit、比例、目标窗口和反应兼容性。
4. 优化/改进假设：
   - PiEvo-faithful 使用 full-history posterior、MAP residual anomaly 和 IDS 选择。
   - Generation feedback analyzer 统计 Harness 失败原因和 generation strategy pass rate。
   - VAE replacement 生成器读取失败回流后，可用 `--require-counterpart-compatibility` 保留互补反应对。
   - feedback-guided replacement ledger 已进入 PiEvo posterior 对比；失败回流现在不只是报告建议，而会改变 posterior 置信分布。
   - Feedback-aware LLM/RAG agent 读取 strict strategy feedback，保留已修复的 replacement/RAG 策略，并抑制缺 predictor/chemistry evidence 的 SMILES 草案。
   - 人工审核优先查看高 reward、低 OOD、通过 Harness 的候选，以及失败原因集中的规则。

脚本入口：

```bash
PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli closed-loop --config configs/reproduce.yaml
```

输出：

- `closed_loop_selected.csv`
- `closed_loop_history.json`
- `evolved_principles.json`

PiEvo-faithful / generation feedback 相关入口：

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.cli \
  pievo-faithful \
  --config configs/pievo_faithful_replacement_195_smoke.yaml

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/analyze_generation_feedback.py \
  --generation-ledger artifacts/trail/generation/prompt_records/generation_record_ledger.csv \
  --replacement-rejections artifacts/trail/generation/replacement_eval/replacement_proposal_rejections.csv \
  --out-dir artifacts/trail/generation_feedback \
  --report reports/generation_failure_feedback.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.pievo_faithful \
  --config configs/pievo_faithful_feedback_replacement_195_smoke.yaml

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/compare_pievo_feedback_ledgers.py \
  --original-dir artifacts/pievo_faithful_replacement_195_smoke \
  --feedback-dir artifacts/pievo_faithful_feedback_replacement_195_smoke \
  --out-dir artifacts/trail/generation/feedback_guided_replacement_pievo_compare \
  --report reports/feedback_guided_replacement_pievo_comparison.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_feedback_replacement_target_sweep.py \
  --targets 190 195 200 250 \
  --rounds 6 \
  --candidate-batch-size 260

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python trail/generation/vae_replacement_strategy.py \
  --candidates artifacts/reproduce/discovery/selected_candidates.csv \
  --component-inventory artifacts/trail/candidates_expanded/component_inventory.csv \
  --top-k 20 \
  --per-side 5 \
  --require-counterpart-compatibility \
  --out artifacts/trail/generation/expanded_inventory_replacement_proposals.csv

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/evaluate_replacement_proposals.py \
  --proposals artifacts/trail/generation/expanded_inventory_replacement_proposals.csv \
  --out-dir artifacts/trail/generation/expanded_inventory_replacement_eval \
  --report reports/expanded_inventory_replacement_evaluation.md \
  --target-tg-c 195 \
  --target-window-c 5 \
  --device cpu

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/import_proposal_eval_generation_records.py \
  --scored artifacts/trail/generation/expanded_inventory_replacement_eval/replacement_proposals_scored.csv \
  --strategy functional_group_replacement \
  --source-context expanded_inventory_replacement_eval \
  --generator-id trail/generation/vae_replacement_strategy.py \
  --out-dir artifacts/trail/generation/expanded_inventory_replacement_records \
  --report reports/expanded_inventory_replacement_generation_records.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python trail/generation/vae_latent_local_search.py \
  --candidates artifacts/reproduce/discovery/selected_candidates.csv \
  --component-inventory artifacts/trail/candidates_expanded/component_inventory.csv \
  --top-k 20 \
  --per-side 5 \
  --require-counterpart-compatibility \
  --out artifacts/trail/generation/vae_latent_local_search/latent_local_search_proposals.csv \
  --report reports/vae_latent_local_search.md \
  --device cpu

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/evaluate_replacement_proposals.py \
  --proposals artifacts/trail/generation/vae_latent_local_search/latent_local_search_proposals.csv \
  --out-dir artifacts/trail/generation/vae_latent_local_search_eval \
  --report reports/vae_latent_local_search_evaluation.md \
  --target-tg-c 195 \
  --target-window-c 5 \
  --device cpu

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/import_proposal_eval_generation_records.py \
  --scored artifacts/trail/generation/vae_latent_local_search_eval/replacement_proposals_scored.csv \
  --strategy vae_latent_local_search \
  --source-context vae_latent_local_search_eval \
  --generator-id trail/generation/vae_latent_local_search.py \
  --out-dir artifacts/trail/generation/vae_latent_local_search_records \
  --report reports/vae_latent_local_search_generation_records.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.pievo_faithful \
  --config configs/pievo_faithful_vae_latent_local_search_195_smoke.yaml

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_vae_latent_local_search_target_sweep.py \
  --targets 190 195 200 250 \
  --rounds 4 \
  --candidate-batch-size 220 \
  --output-root artifacts/trail/generation/vae_latent_local_search_target_sweep \
  --pievo-output-root artifacts/pievo_faithful_vae_latent_local_search_target_sweep \
  --report reports/vae_latent_local_search_target_sweep.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/analyze_generation_feedback.py \
  --generation-ledger artifacts/trail/generation/prompt_records/generation_record_ledger.csv \
  --replacement-rejections artifacts/trail/generation/feedback_guided_replacement_eval/replacement_proposal_rejections.csv \
  --out-dir artifacts/trail/generation_feedback_strict \
  --report reports/generation_failure_feedback_strict.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_feedback_aware_llm_rag_agent.py \
  --provider offline_policy

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_feedback_aware_llm_rag_agent.py \
  --provider offline_policy \
  --replacement-scored artifacts/trail/generation/expanded_inventory_replacement_eval/replacement_proposals_scored.csv \
  --preferred-replacement-source literature_template \
  --out-dir artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag \
  --report reports/expanded_inventory_feedback_aware_llm_rag_agent.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/import_generation_ledger_observations.py \
  --generation-ledger artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv \
  --out-dir artifacts/trail/generation/feedback_aware_llm_rag_observations \
  --report reports/feedback_aware_llm_rag_pievo_feedback.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.pievo_faithful \
  --config configs/pievo_faithful_feedback_aware_llm_rag_195_smoke.yaml

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/import_generation_ledger_observations.py \
  --generation-ledger artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv \
  --out-dir artifacts/trail/generation/feedback_aware_llm_rag_observations \
  --pievo-output-dir artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke \
  --report reports/feedback_aware_llm_rag_pievo_feedback.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_predictor_ensemble_disagreement.py \
  --candidates artifacts/reproduce/discovery/candidate_space_top_scored.csv \
  --out-dir artifacts/trail/predictors/ensemble_disagreement \
  --report reports/predictor_ensemble_disagreement.md \
  --top-k 6 \
  --target-tg-c 195 \
  --target-window-c 5 \
  --device cpu

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_predictor_model_registry.py \
  --out-dir artifacts/trail/predictors/model_selection_registry \
  --report reports/predictor_model_selection_registry.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.pievo_faithful \
  --config configs/pievo_faithful_ensemble_guard_195_smoke.yaml

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_gnn_global_feature_smoke.py \
  --architecture mpnn \
  --epochs 5 \
  --batch-size 32 \
  --out-dir artifacts/trail/gnn_global_feature_smoke \
  --report reports/gnn_global_feature_smoke.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_rule_template_generation_records.py \
  --selected artifacts/reproduce/discovery/selected_candidates.csv \
  --target-tg-c 195 \
  --target-window-c 5 \
  --max-records 50 \
  --out-dir artifacts/trail/generation/rule_template_records \
  --report reports/rule_template_generation_records.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_generative_training_sets.py \
  --out-dir artifacts/trail/generation/generative_training_sets \
  --report reports/generative_training_set_readiness.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_sft_candidate_generator_dry_run.py \
  --max-records 25 \
  --out-dir artifacts/trail/generation/sft_candidate_dry_run \
  --report reports/sft_candidate_generator_dry_run.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/train_sft_record_projection_generator.py \
  --epochs 120 \
  --batch-size 64 \
  --max-records 23 \
  --sample-multiplier 8 \
  --out-dir artifacts/trail/generation/sft_trained_projection_generator \
  --report reports/sft_trained_projection_generator.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_diffusion_flow_candidate_generator_dry_run.py \
  --max-records 19 \
  --out-dir artifacts/trail/generation/diffusion_flow_candidate_dry_run \
  --report reports/diffusion_flow_candidate_generator_dry_run.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/train_conditional_flow_matching_generator.py \
  --epochs 120 \
  --batch-size 64 \
  --max-records 23 \
  --sample-multiplier 8 \
  --integration-steps 24 \
  --out-dir artifacts/trail/generation/diffusion_flow_trained_generator \
  --report reports/diffusion_flow_trained_generator.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_external_generator_output_checklist.py \
  --out-dir artifacts/trail/generation/external_generator_output_checklist \
  --report reports/external_generator_output_checklist.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/update_generation_strategy_policy.py \
  --out-dir artifacts/trail/generation_strategy_policy \
  --report reports/generation_strategy_bandit_policy.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_human_experiment_review_queue.py \
  --out-dir artifacts/trail/human_review \
  --report reports/human_experiment_review_queue.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_pre_experiment_validation_plan.py \
  --out-dir artifacts/trail/human_review \
  --report reports/pre_experiment_validation_plan.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_validation_request_packet.py \
  --out-dir artifacts/trail/human_review \
  --report reports/validation_request_packet.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_validation_execution_schedule.py \
  --out-dir artifacts/trail/human_review \
  --report reports/validation_execution_schedule.md \
  --immediate-batch-size 12

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_process_completion_packet.py \
  --out-dir artifacts/trail/human_review \
  --report reports/process_completion_packet.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_process_design_suggestion_packet.py \
  --out-dir artifacts/trail/human_review \
  --report reports/process_design_suggestion_packet.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/import_process_approval_intake.py \
  --out-dir artifacts/trail/human_review \
  --report reports/process_approval_intake.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_process_approval_reviewer_checklist.py \
  --out-dir artifacts/trail/human_review \
  --report reports/process_approval_reviewer_checklist.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_high_fidelity_protocol_packet.py \
  --out-dir artifacts/trail/human_review \
  --report reports/high_fidelity_protocol_packet.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_validation_dependency_graph.py \
  --out-dir artifacts/trail/human_review \
  --report reports/validation_dependency_graph.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/import_validation_request_results.py \
  --out-dir artifacts/trail/human_review \
  --report reports/validation_result_intake.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_active_observation_ledger.py \
  --out-dir artifacts/trail/human_review \
  --report reports/active_high_authority_observation_ledger.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_active_evidence_pievo_bridge.py \
  --config configs/pievo_faithful_active_evidence_bridge_smoke.yaml \
  --out-dir artifacts/pievo_faithful_active_evidence_bridge_smoke \
  --report reports/active_evidence_pievo_bridge.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_todo_completion_audit.py \
  --out-dir artifacts/trail/workflow \
  --report reports/todo_completion_audit.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python trail/workflow/multi_agent_workflow.py \
  --generation-feedback artifacts/trail/generation_feedback_strict/generation_feedback_summary.json \
  --generation-ledger artifacts/trail/generation/prompt_records/generation_record_ledger.csv \
  --feedback-aware-ledger artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv \
  --feedback-aware-observation-ledger artifacts/trail/generation/feedback_aware_llm_rag_observations/generation_observation_ledger.csv \
  --feedback-aware-pievo-summary artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke/pievo_faithful_summary.json \
  --ensemble-disagreement-summary artifacts/trail/predictors/ensemble_disagreement/ensemble_disagreement_summary.json \
  --predictor-model-registry-summary artifacts/trail/predictors/model_selection_registry/predictor_model_selection_summary.json \
  --ensemble-guard-pievo-summary artifacts/pievo_faithful_ensemble_guard_195_smoke/pievo_faithful_summary.json \
  --expanded-replacement-summary artifacts/trail/generation/expanded_inventory_replacement_eval/replacement_eval_summary.json \
  --expanded-generation-summary artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag/generation_record_summary.json \
  --vae-latent-local-search-summary artifacts/trail/generation/vae_latent_local_search/latent_local_search_summary.json \
  --vae-latent-local-search-eval-summary artifacts/trail/generation/vae_latent_local_search_eval/replacement_eval_summary.json \
  --vae-latent-local-search-pievo-summary artifacts/pievo_faithful_vae_latent_local_search_195_smoke/pievo_faithful_summary.json \
  --vae-latent-local-search-target-sweep-summary artifacts/trail/generation/vae_latent_local_search_target_sweep/vae_latent_local_search_target_sweep_aggregate.json \
  --generation-strategy-policy-summary artifacts/trail/generation_strategy_policy/generation_strategy_bandit_summary.json \
  --human-review-queue-summary artifacts/trail/human_review/human_experiment_review_queue_summary.json \
  --human-review-validation-summary artifacts/trail/human_review/pre_experiment_validation_plan_summary.json \
  --validation-request-summary artifacts/trail/human_review/validation_request_summary.json \
  --validation-execution-schedule-summary artifacts/trail/human_review/validation_execution_schedule_summary.json \
  --process-completion-packet-summary artifacts/trail/human_review/process_completion_packet_summary.json \
  --process-design-suggestion-summary artifacts/trail/human_review/process_design_suggestion_summary.json \
  --process-approval-summary artifacts/trail/human_review/process_completion_approval_summary.json \
  --process-approval-reviewer-checklist-summary artifacts/trail/human_review/process_approval_reviewer_checklist_summary.json \
  --high-fidelity-protocol-summary artifacts/trail/human_review/high_fidelity_protocol_summary.json \
  --validation-dependency-summary artifacts/trail/human_review/validation_dependency_summary.json \
  --validation-result-intake-summary artifacts/trail/human_review/validation_result_intake_summary.json \
  --active-observation-summary artifacts/trail/human_review/active_high_authority_observation_summary.json \
  --active-evidence-pievo-bridge-summary artifacts/pievo_faithful_active_evidence_bridge_smoke/active_evidence_pievo_bridge_summary.json \
  --todo-completion-audit-summary artifacts/trail/workflow/todo_completion_audit_summary.json \
  --external-generator-output-checklist-summary artifacts/trail/generation/external_generator_output_checklist/external_generator_output_checklist_summary.json \
  --gnn-global-feature-summary artifacts/trail/gnn_global_feature_smoke/gnn_global_feature_summary.json \
  --generative-training-summary artifacts/trail/generation/generative_training_sets/generative_training_summary.json \
  --sft-candidate-generation-summary artifacts/trail/generation/sft_candidate_dry_run/generation_record_summary.json \
  --diffusion-flow-candidate-generation-summary artifacts/trail/generation/diffusion_flow_candidate_dry_run/generation_record_summary.json \
  --diffusion-flow-trained-generation-summary artifacts/trail/generation/diffusion_flow_trained_generator/generation_record_summary.json \
  --sft-trained-candidate-generation-summary artifacts/trail/generation/sft_trained_projection_generator/generation_record_summary.json \
  --target-conditioned-strategy-policy-summary artifacts/trail/generation_strategy_policy_target_conditioned/target_conditioned_generation_strategy_summary.json \
  --sparse-target-replacement-expansion-summary artifacts/trail/generation/sparse_target_replacement_expansion/sparse_target_replacement_expansion_summary.json \
  --out artifacts/trail/workflow/multi_agent_summary.json
```

新增 agent 角色：

- `harness_agent`：硬约束过滤，不被 posterior 学习弱化。
- `feedback_agent`：把 generation ledger 和 Harness rejection 转成下一轮生成器约束。
- `rag_generator_agent`：读取 RAG refs 和 strict strategy feedback，产出 generation records，而不是直接推荐。
- `human_review_agent`：补工艺条件、决定是否进入真实/高保真 observation ledger。
- `active_evidence_agent`：只把通过 validation result intake 和 observation ledger gate 的高权重观测暴露给 PiEvo posterior/策略更新，并在无证据时显式 no-op。

当前 replacement 反馈闭环的观测结果：

- 原始 replacement ledger：10 条外部 surrogate observations，posterior entropy 为 2.4869。
- Feedback-guided strict replacement ledger：11 条外部 surrogate observations，posterior entropy 为 1.4358。
- 两者 MAP principle 均为 `long_aliphatic_penalty`，但 strict ledger 把其 posterior 从 0.4749 推至 0.7454。
- 4 轮 smoke 的 IDS 选择集合相同，说明这个短程实验中 feedback 主要改变 posterior 置信分布；更长 rounds 和更多目标 Tg 才能验证它是否改变最终选择路径。

多目标 replacement 反馈闭环已经补充：

- 190/195/200/250 C 每个目标都重新计算 replacement Harness、external observation ledger、PiEvo reward 和 posterior。
- 6 轮 smoke 的最佳新选择分别距目标 0.057、0.006、0.204、0.099 C。
- MAP principle 随目标变化，说明目标 Tg 已经影响 full-history posterior，而不是只影响候选表排序。

LLM/RAG 反馈闭环已经补充：

- strict feedback 中 `functional_group_replacement` 和 `llm_rag_principle_generation` 均为保留策略，`llm_smiles_generation` 继续被抑制。
- feedback-aware LLM/RAG agent 生成 2 条 `llm_rag_principle_generation` records，2 条都通过 Harness。
- expanded inventory 版本会从 `expanded_inventory_replacement_eval/replacement_proposals_scored.csv` 中优先取 `replacement_source=literature_template` 的成功 record 作为 RAG 证据。
- expanded LLM/RAG smoke 同样生成 2 条通过 Harness 的 records，其中 1 条明确使用 `literature_template` 上下文。
- 这 2 条 records 已通过 `scripts/import_generation_ledger_observations.py` 转成 surrogate observation ledger，并进入 195 C PiEvo-faithful 6 轮 smoke。
- PiEvo 接收 2 条外部 observations、0 条拒绝；6 轮 selected 全部通过 target guard，最佳 selected distance 为 0.0055 C，MAP principle 为 `reaction_a5dd26ae10ad`。
- 当前运行使用 `offline_policy` provider 保持可复现；外部 LLM 只替换候选 JSON 生成步骤，不改变 ledger/Harness/PiEvo 审计链。

Expanded inventory replacement 已补充：

- strict replacement 现在可用 `--component-inventory artifacts/trail/candidates_expanded/component_inventory.csv` 替代旧 `monomer_functional_groups.csv`，并保留 `replacement_source/label/template_family/template_intended_group`。
- 本轮 expanded replacement 生成 200 条 strict proposals，200 条全部可重建并评分，18 条通过 Harness。
- `literature_template` 候选被评分 29 条，其中 3 条通过 Harness；最佳 template 候选预测 Tg 为 194.48 C，距 195 C 目标 0.52 C。
- Workflow summary 已读取 expanded replacement 和 expanded LLM/RAG summary，因此 expanded inventory 不再只是候选池审计结果，而是进入了生成与总览链路。

VAE latent local search 已补充：

- `trail/generation/vae_latent_local_search.py` 使用当前 VAE(512) encoder 的 latent 距离，在 expanded inventory 内检索高 reward 配方的局部替换单体。
- 当前是 decoder-free inventory search，不声称 VAE decoder 已经直接生成新 SMILES；每条 proposal 仍必须经过 predictor、Harness 和 PiEvo。
- 195 C smoke 生成 200 条 proposals，200 条可重建并评分，42 条通过 Harness，最佳 target distance 为 0.200 C。
- `literature_template` proposals 为 39 条，其中 7 条通过 Harness。
- 42 条通过项进入 PiEvo external observation ledger 后，4 轮 selected 全部通过 target guard，最佳 selected distance 为 0.059 C，MAP principle 为 `reaction_839cd29ef5d7`。
- Workflow summary 已读取 latent local search summary、evaluation summary 和 PiEvo summary。
- `scripts/run_vae_latent_local_search_target_sweep.py` 已把同一批 latent proposals 扩展到 190/195/200/250 C 四个目标：800 条 target-wise evaluations 中 126 条通过 Harness，126 条进入 surrogate observation ledger。
- 四个目标的 latent Harness pass 分别为 38、42、41、5；250 C 目标覆盖明显较弱，提示下一轮应按目标重新选择 source candidate pool 或做条件化 latent retrieval。
- 四个目标 PiEvo selected 全部通过 target guard 和 validation；最佳 selected distance 分别为 0.002、0.059、0.043、0.511 C。
- Workflow summary 已读取 `vae_latent_local_search_target_sweep_aggregate.json`，记录 targets、total Harness pass、total observations、best target 和 all selected pass。

Predictor ensemble disagreement 已补充：

- `scripts/build_predictor_model_registry.py` 已把 model zoo 选择结果固化为 registry：默认闭环代理为 `VAE(512)+GaussianProcess_RBF`，MAPEK test 为 3.9778%，MAE/RMSE/R2 备选为 `VAE(512)+NuSVR_RBF`。
- registry 的 `uncertainty_provider` 仍是 GaussianProcess_RBF；它解释了为什么 PiEvo 默认使用 GPR sigma，而不是只按 MAE/RMSE 选 NuSVR。
- Workflow summary 已读取 `predictor_model_registry_*` 字段，让“后续就用哪个模型”成为 artifact 契约，而不是只写在报告里。
- 当前使用 6 个 VAE(512)-WVCM 强模型作为 ensemble 成员，覆盖 GPR、NuSVR、XGBoost、ExtraTrees 和 sklearn GradientBoosting。
- 10000 条候选中，按 ensemble mean 计算 195±5 C 近目标候选共有 1045 条；其中低分歧 84 条，高分歧 526 条。
- `ensemble_std_tg_c` 不是物理不确定性，而是模型间分歧；低分歧近目标候选适合优先进入人工审核，高分歧近目标候选应作为 OOD/epistemic 风险标记。
- Workflow summary 已读取 `ensemble_disagreement_summary.json`，让 predictor agent 的 OOD 信号进入总览，而不是停留在单独报告。
- PiEvo 现在不再只读取固定候选表的 disagreement 审计；`configs/pievo_faithful_ensemble_guard_195_smoke.yaml` 会对每轮实际生成的候选批次做 live ensemble prediction，并把 `predictor_ensemble_std_tg_c <= 25 C` 作为 IDS selection pool guard。
- 6 轮 smoke 中 target guard 和 ensemble guard 每轮都启用，6 个 selected 全部在 5 C target guard 内，也全部在 ensemble disagreement guard 内；最佳 selected distance 为 0.059 C，mean selected ensemble std 为 16.40 C。

GNN global feature smoke 已补充：

- `trail/gnn/train_gnn.py --global-features` 会在 graph pooling 后拼接 31 维配方级特征，包括比例熵、RDKit 加权结构描述符、官能团权重、互补反应对覆盖和 reactive group weight。
- `scripts/run_gnn_global_feature_smoke.py` 对比 `mpnn_baseline` 与 `mpnn_global`，并输出 `artifacts/trail/gnn_global_feature_smoke/*` 和 `reports/gnn_global_feature_smoke.md`。
- 5 epoch smoke 下 global-feature MPNN 的 MAPEK test 为 11.6125%，baseline 为 11.0512%；短训下没有改善 MAPEK/MAE，但 RMSE/R2 略好。
- Workflow summary 已读取 `gnn_global_feature_summary.json`；该 GNN 当前是结构视角和 OOD/ensemble 候选信号，不替代 VAE-WVCM-GPR/NuSVR。

SFT / diffusion / flow readiness 已补充：

- `scripts/build_generative_training_sets.py` 从 generation record ledgers 中筛选 `record_pass + harness_pass + prediction_available` 的记录，生成 SFT JSONL 和 diffusion/flow seed table。
- `scripts/import_proposal_eval_generation_records.py` 会把已经完成 predictor/Harness 的 scored proposals 写回 generation record ledger，让 SFT/扩散/流匹配使用同一审计链。
- `scripts/build_rule_template_generation_records.py` 会把当前 selected candidate space 的近目标规则/模板候选写成 `rule_template` generation records，作为 SFT/diffusion/flow 的规则基线种子。
- 当前 16 个 generation ledgers 共 1965 条输入，其中 303 条通过 Harness，去重后得到 227 条训练候选。
- SFT JSONL 为 192 条 train、35 条 eval，`sft_ready=true`；当前门槛 20 条已通过，SFT dry-run 和轻量监督 trained projection smoke 均已完成。
- diffusion/flow seed table 为 192 条 train、35 条 eval，`diffusion_flow_ready=true`；当前门槛 100 条已通过，且 diffusion/flow dry-run 与轻量 flow-matching 训练 smoke 已完成。
- `scripts/build_external_generator_output_checklist.py` 已把真实外部 LLM/SFT/decoder/flow 输出接入前的门禁结构化：4 类 provider task 中 3 类 ready，`llm_smiles_generation` 仍 suppressed；所有外部输出只能先提交 generation records。
- 这一步仍不直接推荐 SFT/flow 输出；训练后生成的候选必须重新写入 ledger，并经过 predictor、Harness、PiEvo 和人工审核。

SFT candidate generator dry-run 已补充：

- `scripts/run_sft_candidate_generator_dry_run.py` 用 SFT train split 中的 validated prototypes 生成 `sft_candidate_generator` records。
- 当前 dry-run 生成 25 条 records，25 条全部通过 generation record/Harness；最佳 target distance 为 0.003 C。
- mean generation reward 为 0.9922；heldout eval 有 35 条，其中 0 条和 dry-run prototypes 完全同候选。
- dry-run mode 是 `prototype_replay_not_weight_update`，即链路验证和策略激活，不冒充神经权重微调完成。
- Workflow summary 已读取 SFT dry-run summary，记录 rows、Harness pass、best distance、heldout eval rows 和 exact candidate matches。

SFT trained projection generator smoke 已补充：

- `scripts/train_sft_record_projection_generator.py` 在 SFT generation record 的结构化特征空间训练轻量监督 MLP；输入是 target/prompt/source 条件特征，输出是 formulation global features、预测 Tg、reward 和来源策略特征。
- 当前 120 epoch smoke 中，train loss 从 0.880 降至 0.621，eval loss 为 0.725。
- 连续模型输出投影到最近 validated train-split record 后，得到 23 条 `sft_candidate_generator` records，23 条全部通过 Harness。
- 最佳 target distance 为 0.003 C，mean generation reward 为 0.9798，projection distance mean 为 3.643。
- 这是有权重更新的 SFT-style projection，不是外部 LLM 微调，也不是自由 SMILES 生成；后续若接入真实 LLM/SFT 输出，仍必须走同一 ledger/Harness/PiEvo 门禁。
- Workflow summary 已读取 trained SFT summary，记录 rows、Harness pass、best distance、训练损失、projection distance 和 heldout eval。

Diffusion/flow candidate generator dry-run 已补充：

- `scripts/run_diffusion_flow_candidate_generator_dry_run.py` 用 diffusion/flow seed table train split 中的 validated seed prototypes 生成 `diffusion_or_flow_matching` records。
- 当前 dry-run 生成 19 条 records，19 条全部通过 generation record/Harness；最佳 target distance 为 0.003 C，mean generation reward 为 0.9934。
- heldout eval 有 35 条，其中 0 条和 dry-run prototypes 完全同候选。
- dry-run mode 是 `conditional_seed_replay_not_weight_update`，即链路验证和策略激活，不冒充神经扩散或 flow-matching 权重训练完成。
- Workflow summary 已读取 diffusion/flow dry-run summary，记录 rows、Harness pass、best distance、heldout eval rows 和 exact candidate matches。

Conditional flow-matching trained generator smoke 已补充：

- `scripts/train_conditional_flow_matching_generator.py` 在 31 维 formulation global feature 空间训练条件 flow-matching MLP，并以目标 Tg 作为条件。
- 当前 120 epoch smoke 中，train loss 从 1.839 降至 1.177，eval loss 为 1.412。
- 连续生成 184 个特征样本后投影到最近 validated seed row，得到 23 条 `diffusion_or_flow_matching` records，23 条全部通过 Harness。
- 最佳 target distance 为 0.005 C，mean generation reward 为 0.8918，projection distance mean 为 4.422。
- 这是训练型 projection，不是直接 SMILES diffusion；后续若取消 nearest-seed projection，必须新增有效 decoder、predictor 和 Harness 复评。
- Workflow summary 已读取 trained flow summary，记录 rows、Harness pass、best distance、训练损失和 projection distance。

Generation strategy bandit policy 已补充：

- `scripts/update_generation_strategy_policy.py` 把 strategy feedback、replacement/latent eval、LLM/RAG summary 和生成模型 readiness 汇总为 strategy-level contextual bandit。
- 当前 arm 包括 `vae_latent_local_search`、`functional_group_replacement`、`llm_rag_principle_generation`、`llm_smiles_generation`、`sft_candidate_generator`、`diffusion_or_flow_matching`。
- 输出的 `allocation_per_100` 是下一轮 proposal 预算建议，不是最终配方推荐；所有候选仍必须经过 predictor、Harness、PiEvo 和人工审核。
- 当前 6 个策略中 5 个 eligible active，1 个 suppressed，0 个 data_collection_only；top strategy 为 `llm_rag_principle_generation`。
- `sft_candidate_generator` 已因 23 条 trained projection records 全部通过 Harness 成为 active arm；当前 policy 优先读取 trained SFT summary，SFT 获得 23/100 proposal budget 建议。
- `diffusion_or_flow_matching` 已因 23 条 trained projection records 全部通过 Harness 成为 active arm，获得 19/100 proposal budget 建议；当前仍只是训练型 projection 链路已开放，不代表已有直接 SMILES 扩散/流模型推荐。
- `llm_smiles_generation` 因缺 predictor/chemistry evidence 继续 suppressed。
- policy summary 已读取 active evidence/PiEvo bridge 状态；当前 `high_authority_evidence_status=awaiting_high_authority_evidence`，`high_authority_budget_mode=surrogate_backed_allocation`，因此 allocation 仍按 surrogate/generation evidence 计算。
- Workflow summary 已读取 `generation_strategy_bandit_summary.json` 的 high-authority 字段，让“RL/策略优化”能区分 surrogate-backed budget 和未来 high-authority-informed budget。

Target-conditioned generation strategy policy 已补充：

- `scripts/update_target_conditioned_generation_policy.py` 读取 replacement target sweep、VAE latent target sweep 和全局 strategy bandit，把下一轮预算从单一 195 C 全局配置改成每个目标 Tg 单独分配。
- 当前 190/195/200/250 C 每个目标预算和都为 100；190/195/200 C 的 target-specific top strategy 为 `vae_latent_local_search`，250 C 切换为 `functional_group_replacement`。
- 全局 LLM/RAG、SFT projection、flow projection 只拿可迁移 exploration budget；该 budget 以 195 C 为参考衰减，250 C 只保留 13/100，避免把 195 C evidence 硬外推到高 Tg 区间。
- 250 C 曾被标记为 sparse target；`scripts/run_sparse_target_replacement_expansion.py` 已从全量 ratio candidates 中重新选择 40 条 250 C source candidates，生成 320 条 strict replacement proposals，其中 42 条通过 Harness，best eval distance 为 0.034 C。
- 这 42 条 surrogate observations 进入 PiEvo 后，6 轮 selected 全部通过 target guard；best selected distance 为 0.099 C，MAP principle 为 `reaction_cc7f1a60f1af`。
- sparse expansion 通过项已写回 `artifacts/trail/generation/sparse_target_replacement_records/target_250/generation_record_ledger.csv`，并纳入 SFT/diffusion-flow 训练语料；目标条件化 policy 重算后 `sparse_targets=[]`。
- target-conditioned policy 也已读取 active high-authority evidence；当前 `target_high_authority_evidence_status=awaiting_target_high_authority_evidence`，每个目标 Tg 的 active high-authority rows 都是 0，因此 budget mode 仍为 `target_surrogate_backed_allocation`。
- Workflow summary 已读取 `target_conditioned_generation_strategy_summary.json` 和 `sparse_target_replacement_expansion_summary.json`，记录每个目标的 top strategy、transfer budget、sparse target、high-authority rows 和 250 C expansion 结果。

Human experiment review queue 已补充：

- `scripts/build_human_experiment_review_queue.py` 会读取当前通过 Harness/PiEvo 的 surrogate 候选，推断 reaction principle、process template 和缺失工艺字段。
- 默认 candidate table spec 支持 `path::origin::target_tg_c`，让没有 `target_tg_c` 列的目标专属 scored table 也能保留真实目标温度。
- 当前队列输入 88 条候选，去重后 73 条，输出 30 条人工复核候选。
- 目标分布为 195 C 17 条、250 C 13 条；250 C 候选全部来自 `sparse_target_replacement_250`，最佳 target distance 为 0.034 C。
- draft process records 30 条基础格式都通过，但 `ready_for_active_ledger=0`，因为仍缺固化温度、后固化、催化剂、NCO 指数、酰亚胺化条件等字段。
- 队列中 20 条是 `process_design_for_dsc`，10 条建议先做 `high_fidelity_before_dsc`。
- 最佳队列候选距 250 C 目标 0.034 C，但仍只是 surrogate evidence；必须由人工补齐工艺并显式批准，才能进入真实/高权重 observation ledger。
- `scripts/build_pre_experiment_validation_plan.py` 已把队列转成实验前验证计划：30 条都需要补工艺字段，25 条还需要高保真/扩展集成模型复核，0 条可不补工艺直接进入 DSC。
- `scripts/build_validation_request_packet.py` 已把验证计划转成 55 个可分派 request：30 个只补工艺记录，25 个完成后可作为 `high_fidelity_simulation` 候选 observation，但都被工艺补全 gate 阻塞；当前 0 个 real DSC request。
- `scripts/build_validation_execution_schedule.py` 已把 55 个 request 排成执行顺序：30 个 process completion 可立即执行，25 个 high-fidelity observation request 仍 blocked；当前 immediate batch 12 个任务全部是 process completion，其中 8 个来自 250 C sparse target 候选。
- `scripts/build_process_completion_packet.py` 已把 immediate batch 展开成 12 行可填写工艺补全模板；12 行都能通过基础 process record 格式，但因字段未填和未批准，`ready_for_active_ledger=0`。
- `scripts/build_process_design_suggestion_packet.py` 已把 12 行工艺补全模板转成知识模板驱动的工艺建议：12 行基础 process record 通过，12 行字段可由模板建议补全，8 行是 250 C 高 Tg 工艺窗口，5 行有高 predictor sigma；但所有行仍保持 `review_status=needs_human_review`，`ready_for_active_ledger=0`。
- `scripts/import_process_approval_intake.py` 已生成 12 行人工审批模板；当前没有人工提交的审批记录，因此 `accepted_process_approval_rows=0`、`unblocked_observation_request_rows=0`。即使未来审批通过，也只是解锁对应 high-fidelity/real request，仍不会直接写入 observation ledger。
- `scripts/build_process_approval_reviewer_checklist.py` 已把 12 行审批模板转成 reviewer checklist：12 行都 ready for human review，当前 0 行 submitted/accepted；这 12 行若通过，可解锁 13 条 downstream high-fidelity protocol。字段频次最高的是 `cure_temperature_c` 和 `post_cure_temperature_c`，各 10 次。
- `scripts/build_high_fidelity_protocol_packet.py` 已把 25 条 high-fidelity request 展开成方法协议包：195 C 12 条、250 C 13 条；当前 0 条 ready、25 条仍被 process approval 阻塞。协议包只列出 `process_feasibility_review`、`model_ensemble_recheck`、`high_fidelity_simulation_or_expanded_model_ensemble` 等必需方法，不产生 observation。
- `scripts/build_validation_dependency_graph.py` 已把 request、process approval、high-fidelity protocol、result intake 和 active evidence gate 形式化成 DAG：118 个节点、125 条边，当前 125 条边全部 blocked/pending。critical path 的下一步是审核 12 行 `process_completion_approval_template`。
- `scripts/import_validation_request_results.py` 已生成 25 条 high-fidelity result intake template；当前没有完成结果，因此 0 条 accepted observation、0 条 observation ledger pass。
- `scripts/build_active_observation_ledger.py` 已把 result intake 后的 observation ledger 再过滤成 active high-authority evidence ledger；当前 0 条 active rows，因为尚无完成且获批的高保真/真实/文献观测。
- PiEvo 外部观测加载器现在支持 `external_observation_allowed_source_types` 和 `external_observation_require_active_evidence`；active-evidence bridge 用这些二级过滤保护 posterior。
- `scripts/run_active_evidence_pievo_bridge.py` 已验证 active ledger 可进入 PiEvo full-history posterior 路径；当前 `bridge_status=no_active_evidence_noop`，`external_accepted_rows=0`，`active_evidence_updates_posterior=false`。
- `scripts/build_todo_completion_audit.py` 已把 TODO 覆盖情况转成 10 行审计表：9 行 implemented、1 行按用户要求 deferred、0 行 evidence missing；主阻塞是人工 process approval 和真实/高保真 observation。
- Workflow summary 已读取 `human_experiment_review_queue_summary.json`、`pre_experiment_validation_plan_summary.json`、`validation_request_summary.json`、`process_completion_packet_summary.json`、`process_design_suggestion_summary.json`、`process_completion_approval_summary.json`、`process_approval_reviewer_checklist_summary.json`、`high_fidelity_protocol_summary.json`、`validation_dependency_summary.json`、`validation_result_intake_summary.json`、`active_high_authority_observation_summary.json`、`active_evidence_pievo_bridge_summary.json` 和 `todo_completion_audit_summary.json`，并记录 `human_review_*`、`human_validation_*`、`validation_request_*`、`process_completion_packet_*`、`process_design_suggestion_*`、`process_approval_*`、`process_approval_reviewer_*`、`high_fidelity_protocol_*`、`validation_dependency_*`、`validation_result_*`、`active_observation_*`、`active_evidence_pievo_bridge_*` 与 `todo_completion_*` 字段，让人工闭环不再只是 schema 和说明文档。

这个闭环目前主要使用 surrogate 和 smoke ledger 作为反馈源。若后续有真实合成/DSC 实验结果，应把实验 Tg 和工艺条件作为高权重 observation 加入 ledger，再更新 PiEvo posterior、重训 predictor 或修正 generation policy。
