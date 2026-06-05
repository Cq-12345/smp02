# SMP 生成模型与 Harness 约束策略

本文档对应 TODO 中“生成模型：探索空间界定、生成策略、VAE 替换策略、LLM/SFT/prompt/RAG/Harness、扩散生成、流匹配等”。当前阶段仍使用小分子 SMILES / MoleCode，不做真实商品组分和聚合物超图表示。

## 1. 生成不是直接决策

在本项目中，生成模型只负责提出候选假设：

```text
h = (m_1..m_n, r_1..r_n)
```

候选必须经过：

- Harness 硬约束过滤。
- VAE-WVCM / GNN / ensemble predictor 评估。
- Predictor ensemble disagreement 标记 epistemic/OOD 风险。
- PiEvo-faithful IDS 选择。
- 真实或高保真实验结果回写。

因此生成模型不应直接决定“最好配方”，它只扩大可检验搜索空间。

## 2. 探索空间界定

当前搜索空间：

- 组分：小分子 SMILES / MoleCode 兼容候选。
- 来源：library、generated、literature_template、chembl。
- 组分数：1 到 4。
- 比例：simplex，满足最小比例阈值。
- 化学网络：必须存在官能团兼容边。
- 目标：`target_tg_c` 可变，不写死 250 C 或 195 C。

暂缓搜索空间：

- 商品级复杂组分。
- 聚合物重复单元超图。
- 工艺参数图谱。

## 3. 生成策略分层

### 3.1 规则/模板生成

用途：

- 快速注入热固性合理结构，如二胺、二酸酐、二环氧、氰酸酯、双马来酰亚胺、异氰酸酯等。

优点：

- 可控、可解释、容易通过 Harness。

缺点：

- 新颖性有限。

当前 record 化结果：

- `scripts/build_rule_template_generation_records.py` 会把 `artifacts/reproduce/discovery/selected_candidates.csv` 中的近目标规则/模板候选写成 `rule_template` generation records。
- 本轮 195±5 C 生成 50 条 records，50 条通过 importer/Harness；最佳 target distance 为 0.003 C，mean generation reward 为 0.9888。
- 这些 records 是当前小分子搜索空间的规则基线种子，不是真实 DSC 或新物理实验；它们进入 SFT/diffusion/flow 训练语料前仍保留 source/context/audit 字段。
- 输出见 `artifacts/trail/generation/rule_template_records/*` 和 `reports/rule_template_generation_records.md`。

### 3.2 替换生成

已有脚本：

- `trail/generation/vae_replacement_strategy.py`

逻辑：

- 从高分候选出发。
- 按共享官能团找可替换小分子。
- 用 Morgan fingerprint Tanimoto 排序。
- 可选 feedback-guided strict 模式：替换分子必须继续和未替换的另一侧单体形成 `compatibility_reason` 可映射反应对。

用途：

- 在保持反应兼容性的前提下做局部探索。

当前评估闭环：

- `scripts/evaluate_replacement_proposals.py`
- `artifacts/trail/generation/replacement_eval/replacement_proposals_scored.csv`
- `artifacts/trail/generation/replacement_eval/replacement_proposals_harness.csv`
- `artifacts/trail/generation/replacement_eval/replacement_observation_ledger.csv`
- `reports/replacement_proposal_evaluation.md`
- `reports/replacement_pievo_feedback_smoke.md`
- `artifacts/trail/generation/feedback_guided_replacement_proposals.csv`
- `artifacts/trail/generation/feedback_guided_replacement_eval/replacement_observation_ledger.csv`
- `reports/feedback_guided_replacement_evaluation.md`
- `reports/feedback_guided_replacement_comparison.md`
- `configs/pievo_faithful_feedback_replacement_195_smoke.yaml`
- `artifacts/pievo_faithful_feedback_replacement_195_smoke/*`
- `reports/feedback_guided_replacement_pievo_comparison.md`
- `scripts/run_feedback_replacement_target_sweep.py`
- `artifacts/trail/generation/feedback_guided_replacement_target_sweep/*`
- `artifacts/pievo_faithful_feedback_replacement_target_sweep/*`
- `reports/feedback_guided_replacement_target_sweep.md`
- `artifacts/trail/generation/expanded_inventory_replacement_proposals.csv`
- `artifacts/trail/generation/expanded_inventory_replacement_eval/replacement_proposals_scored.csv`
- `artifacts/trail/generation/expanded_inventory_replacement_records/generation_record_ledger.csv`
- `reports/expanded_inventory_replacement_evaluation.md`
- `reports/expanded_inventory_replacement_generation_records.md`

结果：

- 120 条 replacement proposals 输入。
- 107 条可重建为完整双组分配方并完成 VAE-WVCM-GPR 预测。
- 10 条通过 Harness。
- `scripts/evaluate_replacement_proposals.py` 默认使用 CPU deterministic VAE encoding，避免 CUDA 数值路径导致 surrogate ledger 漂移。
- 最佳 replacement 预测 Tg 为 194.63 C，距 195 C 目标 0.37 C；4 条在 1 C 内，10 条在 5 C 内。
- 通过项已写入 observation ledger，并进入 `configs/pievo_faithful_replacement_195_smoke.yaml` 的 PiEvo-faithful external history。
- 失败回流后的 strict replacement 仍生成 120 条 proposal，但每条都带非空 `counterpart_compatibility_reason`。
- Strict replacement 的重建失败从 13 条降到 0 条，Harness 通过从 10 条增至 11 条；最佳距离仍为 0.37 C，说明互补反应对约束没有牺牲当前最佳近目标候选。
- Strict replacement observation ledger 已进入 PiEvo-faithful：外部 observation 从 10 条变为 11 条，posterior entropy 从 2.4869 降为 1.4358，MAP principle 仍为 `long_aliphatic_penalty`，其 posterior 从 0.4749 升至 0.7454。
- 在相同 seed、目标 Tg 和 target guard 下，4 轮 IDS 选择集合没有变化，最佳新选择仍为 194.99 C、距 195 C 目标 0.01 C；这说明本轮 feedback 主要改变 posterior 置信分布，而不是短 smoke 的选择路径。
- 多目标 strict replacement + PiEvo sweep 已覆盖 190/195/200/250 C，且每个目标都重新计算 replacement target window、external ledger reward 和 PiEvo posterior。
- 6 轮 smoke 中最佳新选择分别为 190.06、194.99、199.80、249.90 C；对应目标距离为 0.057、0.006、0.204、0.099 C，所有 selected 都通过 Harness。
- 目标不同会改变 MAP principle：190 C 为 `reaction_a5dd26ae10ad`，195 C 为 `long_aliphatic_penalty`，200 C 为 `too_flexible_penalty`，250 C 为 `heavy_halogen_practical_risk`。这说明可变目标 Tg 已进入 posterior 层，而不是只做同一候选表重排序。
- Expanded inventory 已进入 strict replacement 生成器：`--component-inventory artifacts/trail/candidates_expanded/component_inventory.csv` 会保留 `replacement_source/label/template_family/template_intended_group`。
- Expanded replacement smoke 生成 200 条 strict proposals、200 条可重建并评分、18 条通过 Harness；其中 `literature_template` 被评分 29 条，3 条通过 Harness，最佳 template 候选距 195 C 目标 0.52 C。
- 这 200 条 scored proposals 已通过 `scripts/import_proposal_eval_generation_records.py` 写回 generation record ledger：200 条 record 全部基础字段通过，18 条 Harness pass，失败项保留 target/chemistry failure reason 用于策略回流。
- 原始 replacement、feedback-guided replacement 以及 190/195/200/250 C 多目标 strict replacement scored proposals 也已写回 generation record ledgers；这些账本为 SFT 和 diffusion/flow 提供更多目标条件、更多失败原因和更多 Harness-passing 小分子种子。

### 3.3 VAE latent 生成

当前已落地一个保守版本：

- `trail/generation/vae_latent_local_search.py`
- 在 expanded inventory 内对高 reward 配方的单体做 VAE latent-neighborhood retrieval。
- 使用当前 VAE encoder 的 `mu` 向量计算单体级 latent Euclidean distance。
- 默认仍要求共享至少一个源侧官能团，并在 `--require-counterpart-compatibility` 下保持与未替换 co-monomer 的可映射反应对。
- 输出保留 `latent_distance / latent_cosine_similarity / latent_rank / tanimoto / matched_groups`，方便比较 VAE 表示相近与 Morgan fingerprint 相近是否导向不同候选。

运行入口：

```bash
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
```

当前 smoke 结果：

- 200 条 latent local search proposals。
- 200 条全部可重建并评分，0 条重建拒绝。
- 42 条通过 Harness，最佳 target distance 为 0.200 C。
- `literature_template` proposals 为 39 条，其中 7 条通过 Harness。
- 42 条通过项进入 surrogate observation ledger 后，PiEvo-faithful 接收 42 条外部 observations、拒绝 0 条。
- 4 轮 PiEvo selected 全部通过 target guard，最佳 selected distance 为 0.059 C，MAP principle 为 `reaction_839cd29ef5d7`。
- 这 200 条 scored proposals 已通过 `scripts/import_proposal_eval_generation_records.py` 写回 generation record ledger：200 条 record 全部基础字段通过，42 条 Harness pass。该账本现在是 SFT/diffusion/flow 训练语料的主要来源之一。

后续可做：

- 再考虑从高 reward 候选的 latent 附近采样并 decode。
- 加入 decoder validity/harness pass rate 作为训练或筛选指标。
- 对不同目标 Tg 学习条件化 latent proposal。

边界：

- 当前不是 VAE decoder 直接生成新 SMILES；它是 decoder-free inventory local search。
- latent 邻居必须继续经过 predictor/Harness/PiEvo，不能直接当成推荐配方。

### 3.4 LLM/RAG 生成

推荐方式：

- RAG 检索知识库、反应原则、候选 inventory 和已观测失败/成功案例。
- LLM 只生成候选原则、候选官能团组合或 SMILES 草案。
- Harness 必须作为外部硬约束，不能依赖 LLM 自我声明合法。

当前可用基础：

- `trail/rag/simple_retriever.py`：RAG smoke 检索器，已过滤单字符和纯数字 query token，避免 `C`、`0` 这类噪声压过 strict feedback 上下文。
- `trail/knowledge/smp_prior_knowledge.yaml`
- `artifacts/trail/candidates_smoke/component_inventory.csv`
- `artifacts/trail/candidates_expanded/component_inventory.csv`
- `reports/sparse_candidate_template_expansion.md`
- `reports/candidate_source_audit_expanded.md`
- `trail/generation/generation_record_schema.yaml`
- `trail/generation/import_generation_records.py`
- `scripts/build_prompt_generation_records.py`
- `artifacts/trail/generation/prompt_records/generation_record_ledger.csv`
- `reports/generation_record_schema_smoke.md`
- `scripts/run_feedback_aware_llm_rag_agent.py`
- `scripts/import_generation_ledger_observations.py`
- `artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv`
- `artifacts/trail/generation/feedback_aware_llm_rag_observations/generation_observation_ledger.csv`
- `artifacts/trail/generation_feedback_strict/strategy_feedback.csv`
- `reports/feedback_aware_llm_rag_agent.md`
- `artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag/generation_record_ledger.csv`
- `reports/expanded_inventory_feedback_aware_llm_rag_agent.md`
- `reports/feedback_aware_llm_rag_pievo_feedback.md`
- `reports/generation_failure_feedback_strict.md`
- `configs/pievo_faithful_feedback_aware_llm_rag_195_smoke.yaml`
- `artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke/pievo_faithful_summary.json`

当前 record schema 已覆盖：

- `generation_id / strategy / stage / target_tg_c / target_window_c`
- `candidate_smiles / candidate_ratios`
- `prompt_id / prompt_text / prompt_hash`
- `rag_query / rag_context_refs / rag_context_digest`
- `principle_hypothesis / functional_group_plan / candidate_json`
- `predicted_tg_mean_c / predicted_tg_sigma_c / ood_penalty`
- `harness_pass / harness_failure_reason`
- `pievo_round / selected_by_ids / review_status`

Prompt/RAG smoke 结果：

- 4 条输入 generation records。
- 2 条 `llm_rag_principle_generation`、1 条 `functional_group_replacement`、1 条 `llm_smiles_generation`。
- 3 条通过 Harness，1 条 draft 失败并记录 `prediction_missing;chemistry_evidence_missing;replacement_formula_failed_reaction_or_ratio_constraints`。
- 最佳 generation record 预测 Tg 为 195.00 C，距 195 C 目标 0.003 C。
- 这一步没有调用外部 LLM；它固定的是未来 LLM/SFT/扩散/流匹配生成器必须遵守的记录契约。

Feedback-aware LLM/RAG agent 状态：

- `scripts/run_feedback_aware_llm_rag_agent.py` 会读取 RAG 上下文、`strategy_feedback.csv`，再输出 generation records。
- 默认 RAG 上下文聚焦 `generation_strategy_registry.yaml`、strict failure feedback、PiEvo 数学说明和 target sweep 结果，避免旧 replacement rejection 历史压过最新 strict policy。
- 默认 provider 为 `offline_policy`，用于可复现 smoke；若设置 `OPENAI_API_KEY`，可切换到 `openai_compatible` provider，但输出仍必须写入同一 generation ledger。
- 当前 strict feedback 中，`functional_group_replacement` 和 `llm_rag_principle_generation` 均被保留，`llm_smiles_generation` 因缺 predictor/chemistry evidence 被抑制。
- Agent smoke 生成 2 条 `llm_rag_principle_generation` records，2 条都通过 Harness；最佳距离为 0.003 C，mean generation reward 为 0.9637。
- `scripts/import_generation_ledger_observations.py` 已把这 2 条成功 records 转成 surrogate observation ledger；失败/缺预测 records 不会被提升为 observation。
- `configs/pievo_faithful_feedback_aware_llm_rag_195_smoke.yaml` 已把该 ledger 接入 PiEvo-faithful：6 轮 smoke 接收 2 条外部 observations、0 条拒绝，6 条 selected 全部通过 target guard，最佳 selected distance 为 0.0055 C。
- Expanded inventory 版本的 feedback-aware LLM/RAG agent 已读取 expanded replacement scored，并优先使用 `replacement_source=literature_template` 的 cyanate ester record 作为 RAG 证据；2 条 records 都通过 Harness，`literature_template_context_rows=1`。

### 3.5 失败回流

已有脚本：

- `scripts/analyze_generation_feedback.py`

输入：

- `artifacts/trail/generation/prompt_records/generation_record_ledger.csv`
- `artifacts/trail/generation/replacement_eval/replacement_proposal_rejections.csv`

输出：

- `artifacts/trail/generation_feedback/strategy_feedback.csv`
- `artifacts/trail/generation_feedback/failure_reason_counts.csv`
- `artifacts/trail/generation_feedback/replacement_failure_groups.csv`
- `reports/generation_failure_feedback.md`
- `artifacts/trail/generation_feedback_strict/strategy_feedback.csv`
- `reports/generation_failure_feedback_strict.md`

当前结果：

- 4 条 prompt/RAG generation records 中 3 条通过 Harness。
- replacement rejections 为 13 条。
- 主失败原因为 `replacement_formula_failed_reaction_or_ratio_constraints`，共 14 次。
- `llm_smiles_generation` 当前 policy delta 为 -0.25，必须先补 prediction 和 chemistry evidence。
- `functional_group_replacement` 当前 policy delta 为 -0.10，下一轮应加入“替换后必须保留互补反应对”的约束。
- 该约束已在 `trail/generation/vae_replacement_strategy.py --require-counterpart-compatibility` 中落地；strict evaluation 中 replacement 重建拒绝数为 0。
- strict feedback 版本中，replacement rejection 输入为 0，`functional_group_replacement` pass rate 回升到 1.0，policy delta 为 +0.10；`llm_smiles_generation` 仍为 -0.25。

### 3.6 SFT / 内部微调

当前已落地训练语料契约，且 SFT readiness gate 已通过：

- `scripts/build_generative_training_sets.py`
- `scripts/import_proposal_eval_generation_records.py`
- `scripts/run_sft_candidate_generator_dry_run.py`
- `artifacts/trail/generation/generative_training_sets/sft_generation_records.jsonl`
- `artifacts/trail/generation/generative_training_sets/generative_training_summary.json`
- `artifacts/trail/generation/sft_candidate_dry_run/generation_record_ledger.csv`
- `reports/sft_candidate_generator_dry_run.md`
- `reports/generative_training_set_readiness.md`

语料构建规则：

- 输入：已导入的 generation record ledgers。
- 训练标签：必须 `record_pass=true`、`harness_pass=true`、有 predictor 输出和 generation reward。
- 输出：OpenAI-style `messages` JSONL，其中 assistant 消息是 auditable generation record JSON，不是自由文本推荐。

当前 readiness：

- 12 个 generation ledgers 共 1165 条输入，其中 177 条通过 Harness；去重和 reward 过滤后得到 143 条训练候选。
- SFT JSONL 为 124 条 train、19 条 eval。
- `sft_ready=true`，当前最小门槛为 20 条样本，已超过；下一步可以做 SFT dry-run 或训练作业。
- SFT 生成器即使训练完成，也只能生成 auditable generation record JSON；候选仍必须重新经过 predictor、Harness、PiEvo 和人工审核，不能直接推荐。

当前 SFT dry-run：

- `scripts/run_sft_candidate_generator_dry_run.py` 已用 train split 中的 validated prototypes 生成 25 条 `sft_candidate_generator` records。
- 25 条 records 全部通过 generation record/Harness，最佳 target distance 为 0.003 C，mean generation reward 为 0.9922。
- heldout eval 有 19 条，其中 0 条和 dry-run prototypes 完全同候选；这说明 dry-run 主要验证链路，不证明神经 SFT 已学会分布外生成。
- dry-run mode 明确为 `prototype_replay_not_weight_update`。后续真正训练 LLM/SFT 权重时，应把模型输出写入同一 ledger，并和该 dry-run 的 pass rate、target distance、重复率对比。

### 3.7 扩散/流匹配

当前已落地 diffusion/flow seed table 契约，完成一个保守 seed replay dry-run，并进一步完成一个轻量条件 flow-matching 训练 smoke；仍未直接生成新 SMILES：

- `artifacts/trail/generation/generative_training_sets/diffusion_flow_seed_table.csv`
- `scripts/run_diffusion_flow_candidate_generator_dry_run.py`
- `artifacts/trail/generation/diffusion_flow_candidate_dry_run/generation_record_ledger.csv`
- `scripts/train_conditional_flow_matching_generator.py`
- `artifacts/trail/generation/diffusion_flow_trained_generator/generation_record_ledger.csv`
- `reports/generative_training_set_readiness.md`
- `reports/diffusion_flow_candidate_generator_dry_run.md`
- `reports/diffusion_flow_trained_generator.md`

Seed table 记录：

- 目标 Tg、窗口、候选 SMILES、比例。
- surrogate predicted Tg、sigma、target distance、generation reward。
- compatibility evidence 和 source ledger。

当前 readiness：

- diffusion/flow seed rows 为 143，124 条 train、19 条 eval。
- `diffusion_flow_ready=true`，当前最小门槛 100 条 seed rows 已通过。
- dry-run 使用 train split 中的 validated seed prototypes 做 `conditional_seed_replay_not_weight_update`，生成 19 条 `diffusion_or_flow_matching` records。
- 19 条 records 全部通过 generation record/Harness，最佳 target distance 为 0.003 C，mean generation reward 为 0.9934。
- heldout eval 有 19 条，其中 0 条和 dry-run prototypes 完全同候选；这说明 dry-run 主要验证链路，不证明神经 diffusion/flow 已学会连续配方流形或分布外生成。
- 训练型 smoke 使用 31 维 formulation global features 训练条件 flow-matching MLP：从 Gaussian noise 到配方特征的 velocity，以目标 Tg 为条件。
- 训练 120 epoch 后，train loss 从 1.888 降到 1.313，eval loss 为 1.802；连续生成点投影到最近 validated seed row 后得到 23 条 records，23 条全部通过 Harness。
- 训练型 projection 的最佳 target distance 为 0.005 C，mean generation reward 为 0.8340，projection distance mean 为 5.025；这说明链路已能训练和采样，但投影质量仍需优化。
- 这一步把扩散/流匹配从“空泛未来项”推进为可训练数据契约、可审计 dry-run 和轻量训练型 projection；训练后输出仍必须重新写入 generation ledger，并经过 predictor、Harness、PiEvo 和人工审核。

## 4. Harness 约束

Harness 是生成层和评估层之间的硬门禁。

当前脚本：

- `trail/harness/constraints.py`

支持：

- 旧两组分候选：`smiles_a/smiles_b/ratio_a/ratio_b/predicted_tg`。
- 新多组分候选：`smiles` 使用 `|` 分隔，`ratios` 使用 `:` 分隔，`predicted_tg_mean_c`。
- 可变目标：`--target-center` + `--target-window`。

示例：

```bash
PYTHONPATH=src python trail/harness/constraints.py \
  --candidates artifacts/pievo_faithful_smoke/selected_formulations.csv \
  --target-center 250 \
  --target-window 20 \
  --out artifacts/trail/harness/pievo_smoke_validation.csv
```

## 5. 推荐闭环

```text
知识库/RAG -> 生成候选 -> Harness -> predictor/ensemble disagreement/OOD -> PiEvo IDS -> observation -> posterior/anomaly -> 新一轮生成
```

生成模型的价值应通过两个指标衡量：

- `validity`: 通过 Harness 的比例。
- `utility`: 被 PiEvo IDS 选中并获得高 reward 的比例。

### 5.1 Strategy-level RL / Bandit Policy

当前已经新增一个轻量 strategy-level contextual bandit，用于回应 TODO 中“RL、人工闭环、搜索空间优化”的部分：

- `scripts/update_generation_strategy_policy.py`
- `artifacts/trail/generation_strategy_policy/generation_strategy_bandit_policy.csv`
- `artifacts/trail/generation_strategy_policy/generation_strategy_bandit_summary.json`
- `reports/generation_strategy_bandit_policy.md`

数学含义：

```text
arm = generation strategy
score = utility_mean + UCB_exploration_bonus + feedback_delta - readiness_penalty - suppression_penalty
allocation = softmax(score / temperature)
```

其中 `utility_mean` 由 Beta-smoothed Harness pass mean 和 target reward 混合得到；UCB bonus 用于继续探索样本少但当前表现好的策略。这个 policy 只分配下一轮 proposal 预算，不替代 PiEvo IDS，也不允许绕过 predictor/Harness。

当前结果：

- 6 个策略进入 policy：VAE latent local search、functional-group replacement、LLM/RAG principle generation、LLM SMILES draft、SFT candidate generator、diffusion/flow matching。
- 5 个策略为 eligible active。
- `llm_smiles_generation` 仍 suppressed，因为它缺 predictor/chemistry evidence。
- `sft_candidate_generator` 已因 143 条 SFT 样本和 25 条 dry-run generation records 成为 active arm，获得 23/100 下一轮 proposal budget 建议。
- `diffusion_or_flow_matching` 已因 23 条 trained projection generation records 成为 active arm，获得 18/100 下一轮 proposal budget 建议；这只表示训练型投影链路已可用，不表示已有可信直接 SMILES diffusion/flow 模型输出。
- 当前 top strategy 为 `llm_rag_principle_generation`，原因是 2/2 generation records 通过 Harness 且 UCB 鼓励继续探索低样本高回报策略。

## 6. 近期优先级

1. 若接入外部 LLM，使用 `scripts/run_feedback_aware_llm_rag_agent.py --provider openai_compatible`，并保持 generation record -> predictor/Harness -> observation ledger -> PiEvo 的审计链。
2. 将 LLM 生成继续限制在“提出 principle/官能团组合/候选模板”，SMILES 草案必须由 RDKit、预测模型和 Harness 再验证。
3. 对 feedback-guided replacement 做更大候选池和真实/高保真 observation 版本的 PiEvo sweep，确认 surrogate posterior 规律是否能被物理证据保留。
4. 将 `generation_feedback/strategy_feedback.csv` 继续接入 prompt/RAG 生成器，用失败案例压低弱生成规则；replacement 和 feedback-aware LLM/RAG 侧都已完成 observation ledger -> PiEvo posterior 的 smoke 闭环。
5. 生成候选排序时同步读取 `reports/predictor_ensemble_disagreement.md` 和 `artifacts/trail/predictors/ensemble_disagreement/low_disagreement_near_target.csv`；高分歧近目标候选应优先被标记为复核对象，而不是直接推荐。
6. 对进入 PiEvo 的新候选批次，使用 `configs/pievo_faithful_ensemble_guard_195_smoke.yaml` 的 live ensemble guard 重新计算本批次 `predictor_ensemble_std_tg_c`，不要假设固定候选表的 disagreement 结果覆盖所有生成候选。
7. SFT dry-run、diffusion/flow dry-run 和轻量条件 flow-matching 训练 smoke 都已跑通；下一步应改进 flow 训练/投影质量，或加入有效 SMILES decoder。任何训练输出仍必须写入 ledger 并经过 predictor/Harness/PiEvo。
8. 对 VAE latent local search 做多目标 sweep，并比较 latent-distance ranking、Tanimoto ranking 和 PiEvo posterior 的差异；当前 195 C smoke 已证明链路可运行，但还不能说明 latent metric 已是最优生成策略。
9. 下一轮生成预算可以读取 `generation_strategy_bandit_policy.csv`，但每个被分配预算的策略仍必须写入 ledger，并走 predictor/Harness/PiEvo/人工审核链路。
