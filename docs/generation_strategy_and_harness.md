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

用途：

- 在保持反应兼容性的前提下做局部探索。

当前评估闭环：

- `scripts/evaluate_replacement_proposals.py`
- `artifacts/trail/generation/replacement_eval/replacement_proposals_scored.csv`
- `artifacts/trail/generation/replacement_eval/replacement_proposals_harness.csv`
- `artifacts/trail/generation/replacement_eval/replacement_observation_ledger.csv`
- `reports/replacement_proposal_evaluation.md`
- `reports/replacement_pievo_feedback_smoke.md`

结果：

- 120 条 replacement proposals 输入。
- 107 条可重建为完整双组分配方并完成 VAE-WVCM-GPR 预测。
- 10 条通过 Harness。
- 最佳 replacement 预测 Tg 为 194.93 C，距 195 C 目标 0.07 C。
- 通过项已写入 observation ledger，并进入 `configs/pievo_faithful_replacement_195_smoke.yaml` 的 PiEvo-faithful external history。

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

### 3.5 SFT / 内部微调

只有当积累足够高质量样本后才值得做：

- 输入：目标 Tg、约束、active principles、历史 observation。
- 输出：候选配方 JSON。
- 训练标签：通过 Harness 且经 surrogate/真实实验验证的候选。

短期内不建议优先 SFT，因为数据规模和真实标签不足。

### 3.6 扩散/流匹配

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

1. 建立 generation record schema，记录来源、prompt、RAG context、harness 失败原因。
2. 将 LLM 生成限制在“提出 principle/官能团组合/候选模板”，先不直接相信其 SMILES。
3. 对 replacement 的失败原因做回流：13 条失败均为反应/比例约束失败，应改进官能团匹配或比例搜索。
4. 在真实或高保真 observation 足够前，不优先训练 SFT/扩散/流匹配。
