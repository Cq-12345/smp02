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

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.pievo_faithful \
  --config configs/pievo_faithful_vae_latent_local_search_195_smoke.yaml

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

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.pievo_faithful \
  --config configs/pievo_faithful_ensemble_guard_195_smoke.yaml

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_gnn_global_feature_smoke.py \
  --architecture mpnn \
  --epochs 5 \
  --batch-size 32 \
  --out-dir artifacts/trail/gnn_global_feature_smoke \
  --report reports/gnn_global_feature_smoke.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_generative_training_sets.py \
  --out-dir artifacts/trail/generation/generative_training_sets \
  --report reports/generative_training_set_readiness.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python trail/workflow/multi_agent_workflow.py \
  --generation-feedback artifacts/trail/generation_feedback_strict/generation_feedback_summary.json \
  --generation-ledger artifacts/trail/generation/prompt_records/generation_record_ledger.csv \
  --feedback-aware-ledger artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv \
  --feedback-aware-observation-ledger artifacts/trail/generation/feedback_aware_llm_rag_observations/generation_observation_ledger.csv \
  --feedback-aware-pievo-summary artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke/pievo_faithful_summary.json \
  --ensemble-disagreement-summary artifacts/trail/predictors/ensemble_disagreement/ensemble_disagreement_summary.json \
  --ensemble-guard-pievo-summary artifacts/pievo_faithful_ensemble_guard_195_smoke/pievo_faithful_summary.json \
  --expanded-replacement-summary artifacts/trail/generation/expanded_inventory_replacement_eval/replacement_eval_summary.json \
  --expanded-generation-summary artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag/generation_record_summary.json \
  --vae-latent-local-search-summary artifacts/trail/generation/vae_latent_local_search/latent_local_search_summary.json \
  --vae-latent-local-search-eval-summary artifacts/trail/generation/vae_latent_local_search_eval/replacement_eval_summary.json \
  --vae-latent-local-search-pievo-summary artifacts/pievo_faithful_vae_latent_local_search_195_smoke/pievo_faithful_summary.json \
  --gnn-global-feature-summary artifacts/trail/gnn_global_feature_smoke/gnn_global_feature_summary.json \
  --generative-training-summary artifacts/trail/generation/generative_training_sets/generative_training_summary.json \
  --out artifacts/trail/workflow/multi_agent_summary.json
```

新增 agent 角色：

- `harness_agent`：硬约束过滤，不被 posterior 学习弱化。
- `feedback_agent`：把 generation ledger 和 Harness rejection 转成下一轮生成器约束。
- `rag_generator_agent`：读取 RAG refs 和 strict strategy feedback，产出 generation records，而不是直接推荐。
- `human_review_agent`：补工艺条件、决定是否进入真实/高保真 observation ledger。

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

Predictor ensemble disagreement 已补充：

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
- 当前 8 条 generation ledger 输入中有 7 条通过 Harness，去重后得到 5 条训练候选。
- SFT JSONL 为 4 条 train、1 条 eval，`sft_ready=false`；当前门槛 20 条，还缺 15 条。
- diffusion/flow seed table 为 4 条 train、1 条 eval，`diffusion_flow_ready=false`；当前门槛 100 条，还缺 95 条。
- 这一步不是训练生成模型，而是建立训练数据合同和 readiness gate，防止用过小的 smoke 数据训练出不可泛化生成器。

这个闭环目前主要使用 surrogate 和 smoke ledger 作为反馈源。若后续有真实合成/DSC 实验结果，应把实验 Tg 和工艺条件作为高权重 observation 加入 ledger，再更新 PiEvo posterior、重训 predictor 或修正 generation policy。
