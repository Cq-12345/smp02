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
- PiEvo-faithful IDS 选择。
- 真实或高保真实验结果回写。

因此生成模型不应直接决定“最好配方”，它只扩大可检验搜索空间。

## 2. 探索空间界定

当前搜索空间：

- 组分：小分子 SMILES / MoleCode 兼容候选。
- 来源：library、generated、chembl。
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

### 3.3 VAE latent 生成

当前策略：

- 先不盲目 decode 大量 latent。
- 优先使用 VAE latent 做相似性、OOD、局部扰动和候选排序。

后续可做：

- 从高 reward 候选的 latent 附近采样。
- 加入 decoder validity/harness pass rate 作为训练或筛选指标。
- 对不同目标 Tg 学习条件化 latent proposal。

### 3.4 LLM/RAG 生成

推荐方式：

- RAG 检索知识库、反应原则、候选 inventory 和已观测失败/成功案例。
- LLM 只生成候选原则、候选官能团组合或 SMILES 草案。
- Harness 必须作为外部硬约束，不能依赖 LLM 自我声明合法。

当前可用基础：

- `trail/rag/simple_retriever.py`：RAG smoke 检索器，已过滤单字符和纯数字 query token，避免 `C`、`0` 这类噪声压过 strict feedback 上下文。
- `trail/knowledge/smp_prior_knowledge.yaml`
- `artifacts/trail/candidates_smoke/component_inventory.csv`
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

只有当积累足够高质量样本后才值得做：

- 输入：目标 Tg、约束、active principles、历史 observation。
- 输出：候选配方 JSON。
- 训练标签：通过 Harness 且经 surrogate/真实实验验证的候选。

短期内不建议优先 SFT，因为数据规模和真实标签不足。

### 3.7 扩散/流匹配

当前阶段只作为研究路线，不立即训练：

- 分子扩散/流匹配需要更大的有效单体数据集。
- 还需要约束生成反应官能团和可合成性。
- 若未来引入 polymer/超图表示，再考虑图扩散或 flow matching。

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
知识库/RAG -> 生成候选 -> Harness -> predictor/uncertainty/OOD -> PiEvo IDS -> observation -> posterior/anomaly -> 新一轮生成
```

生成模型的价值应通过两个指标衡量：

- `validity`: 通过 Harness 的比例。
- `utility`: 被 PiEvo IDS 选中并获得高 reward 的比例。

## 6. 近期优先级

1. 若接入外部 LLM，使用 `scripts/run_feedback_aware_llm_rag_agent.py --provider openai_compatible`，并保持 generation record -> predictor/Harness -> observation ledger -> PiEvo 的审计链。
2. 将 LLM 生成继续限制在“提出 principle/官能团组合/候选模板”，SMILES 草案必须由 RDKit、预测模型和 Harness 再验证。
3. 对 feedback-guided replacement 做更大候选池和真实/高保真 observation 版本的 PiEvo sweep，确认 surrogate posterior 规律是否能被物理证据保留。
4. 将 `generation_feedback/strategy_feedback.csv` 继续接入 prompt/RAG 生成器，用失败案例压低弱生成规则；replacement 和 feedback-aware LLM/RAG 侧都已完成 observation ledger -> PiEvo posterior 的 smoke 闭环。
5. 在真实或高保真 observation 足够前，不优先训练 SFT/扩散/流匹配。
