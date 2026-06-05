# SMP 小分子知识库与本体说明

本文档对应 TODO 中“smp 的合理知识库、先验知识库：官能团匹配、化学反应原理、知识图谱、本体”。当前阶段只覆盖单一小分子 SMILES / MoleCode 兼容候选，不处理商品级复杂组分和聚合物超图表示。

## 1. 知识库边界

当前知识库文件：

- `trail/knowledge/smp_prior_knowledge.yaml`
- `trail/knowledge/ontology.yaml`
- `trail/knowledge/build_kg.py`

当前图谱产物：

- `artifacts/trail/kg_enriched/smp_knowledge_graph.json`
- `artifacts/trail/kg_enriched/smp_knowledge_graph.graphml`
- `artifacts/trail/kg_enriched/smp_knowledge_graph_summary.json`

本轮扩展后的图谱规模：

- 109 个节点。
- 95 条边。
- 20 条反应原则。
- 10 条结构先验。
- 3 条适用域/可转移性先验。
- 6 条硬约束。

## 2. 硬约束

硬约束不是 principle posterior 的一部分，不应被 PiEvo 学习或弱化。它们用于过滤非法候选：

- RDKit 可解析。
- 当前阶段只接受单片段小分子。
- 元素集合受 VAE/MoleCode 覆盖范围限制。
- SMILES 必须可被 VAE charset 编码。
- 摩尔比例满足 simplex。
- 多组分配方必须存在可解释的官能团反应网络。

## 3. 结构先验

结构先验是可被 PiEvo 后验证据调整的候选规律：

- 芳香骨架提高 Tg。
- 多芳香结构提高刚性。
- 酰亚胺/酸酐路线通常提高高温性能。
- 氰酸酯三嗪网络可提高 Tg。
- 马来酰亚胺参与刚性共聚或 Michael 加成。
- 高反应官能度提高交联密度。
- 柔性醚、PEG-like、长脂肪链和高可旋转键数降低 Tg 风险。

这些不是绝对真理。它们在 `pievo_faithful` 中应体现为 `P_j`，通过完整历史似然改变 posterior。

## 4. 反应原则

知识库目前覆盖 20 类小分子热固性相关反应：

- 环氧-伯胺、环氧-仲胺、环氧-酸酐、环氧-羧酸、环氧-羟基。
- 酸酐-伯胺、酸酐-仲胺、酸酐-羟基。
- 异氰酸酯-羟基、异氰酸酯-伯胺、异氰酸酯-仲胺。
- 丙烯酸酯/甲基丙烯酸酯-乙烯基自由基共聚。
- thiol-ene、thiol-acrylate。
- 氰酸酯自聚、氰酸酯-酚、氰酸酯-胺。
- 马来酰亚胺-乙烯基、马来酰亚胺-硫醇、马来酰亚胺-胺。

每条反应原则记录：

- compatible functional groups。
- expected network。
- mechanism。
- confidence。
- notes。

## 5. 候选来源本体

候选来源分为：

- `library`：SMP 数据集中已出现的小分子单体，可信度最高。
- `generated`：由热固性结构模板产生的小分子，可信度中等。
- `chembl`：数据库小分子经规则筛选后进入候选池，可信度低到中等。

这个来源信息不应直接等价于物理规律，但可以作为适用域和转移风险的条件变量。

## 6. 与 PiEvo 的连接

在 PiEvo-faithful 中：

```text
P_t = structural_principles + applicability_principles + reaction_principles + anomaly_derived_principles
```

硬约束只决定候选是否进入搜索空间，不进入 posterior。软先验进入 posterior：

```text
p_t(P) proportional p0(P) * product_s p(y_s | h_s, P)
```

若某个先验不能解释历史观测，它会降低 posterior；若 anomaly-derived principle 能解释原有 MAP principle 的残差，它会获得更高 posterior。

## 7. 后续扩展

下一步应继续补：

- 论文来源字段：每条先验和反应规则对应的文献或实验依据。
- 工艺条件字段：催化剂、固化温度、后固化、光/热/自由基条件。
- 风险字段：毒性、挥发性、商业可得性、合成复杂度。
- 与真实 DSC 结果连接的 observation schema。
