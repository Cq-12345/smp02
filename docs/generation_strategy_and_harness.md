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

- `trail/rag/simple_retriever.py`
- `trail/knowledge/smp_prior_knowledge.yaml`
- `artifacts/trail/candidates_smoke/component_inventory.csv`
- `trail/generation/generation_record_schema.yaml`
- `trail/generation/import_generation_records.py`
- `scripts/build_prompt_generation_records.py`
- `artifacts/trail/generation/prompt_records/generation_record_ledger.csv`
- `reports/generation_record_schema_smoke.md`

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

当前结果：

- 4 条 prompt/RAG generation records 中 3 条通过 Harness。
- replacement rejections 为 13 条。
- 主失败原因为 `replacement_formula_failed_reaction_or_ratio_constraints`，共 14 次。
- `llm_smiles_generation` 当前 policy delta 为 -0.25，必须先补 prediction 和 chemistry evidence。
- `functional_group_replacement` 当前 policy delta 为 -0.10，下一轮应加入“替换后必须保留互补反应对”的约束。
- 该约束已在 `trail/generation/vae_replacement_strategy.py --require-counterpart-compatibility` 中落地；strict evaluation 中 replacement 重建拒绝数为 0。

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

1. 将真实 LLM/RAG agent 接到 `generation_record_schema.yaml`，要求先输出 generation record，再进入 predictor/Harness/PiEvo。
2. 将 LLM 生成限制在“提出 principle/官能团组合/候选模板”，SMILES 草案必须由 RDKit、预测模型和 Harness 再验证。
3. 对 feedback-guided replacement 做更多目标温度和更长 rounds 的 PiEvo sweep，确认 posterior 收缩是否会在更大候选池中改变 IDS 选择路径。
4. 将 `generation_feedback/strategy_feedback.csv` 继续接入 prompt/RAG 生成器，用失败案例压低弱生成规则；replacement 侧已完成互补反应对约束和 PiEvo posterior 对比。
5. 在真实或高保真 observation 足够前，不优先训练 SFT/扩散/流匹配。
