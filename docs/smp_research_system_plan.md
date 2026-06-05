# SMP 配方发现研究系统路线图

本文档把 `ForYouGoal/20260606_01/TODO.md` 中除“真实组分超图表示层”之外的任务拆成可执行系统。当前阶段仍使用小分子 SMILES / MoleCode / VAE latent 表示。

## 0. 当前边界

暂不执行：

- 商品级复杂组分、聚合物、超图/异构图统一表示。

继续执行：

- 知识库与先验库。
- 候选组分数据集。
- 预测模型体系。
- 生成模型策略。
- 闭环 autonomous workflow。
- PiEvo-faithful principle evolution。
- 真实 Tg 目标可变。

## 1. 知识库和先验库

现有资产：

- `trail/knowledge/smp_prior_knowledge.yaml`
- `trail/knowledge/ontology.yaml`
- `trail/knowledge/build_kg.py`
- `docs/functional_group_classification_and_matching.md`

需要持续扩展的知识类型：

- 官能团检测：epoxy、amine、anhydride、isocyanate、hydroxyl、phenol、acrylate、vinyl、thiol、cyanate ester、maleimide 等。
- 反应原则：epoxy-amine、anhydride-amine、isocyanate-hydroxyl、cyanate ester 自聚、acrylate/vinyl 自由基固化、thiol-ene 等。
- Tg 结构先验：刚性芳香骨架、酰亚胺/氰酸酯网络、高交联密度通常提高 Tg；长脂肪链、PEG-like、过高可旋转键通常降低 Tg。
- 适用域先验：OOD、VAE charset、RDKit validity、单片段分子、允许元素集合。

系统要求：

- 硬约束只用于过滤，不随意学习或弱化。
- 软先验进入 PiEvo principle space，可以被 evidence 提升或降低 posterior。

## 2. 候选组分数据集

候选来源分为三层：

- `library`：`data/SMP_Dataset.xlsx` 中出现过的单体。
- `generated`：人工模板/规则生成的小分子 monomer seeds。
- `literature_template`：面向 cyanate ester、maleimide、isocyanate、anhydride、thiol 等稀疏高价值官能团的可审计小分子模板。
- `chembl`：`data/chembl_36_chemreps.txt` 中经 RDKit、charset、元素和官能团规则筛选后的候选。

组织方式：

- 按官能团分类。
- 按反应兼容关系建立 candidate pair / formula space。
- 按 source 标注是否 out-of-library。
- 按 OOD 与 VAE 可编码性标注模型适用域风险。

当前落地：

- `agent_discovery` 会输出 `monomer_pool.csv`。
- `discovery` 会输出 `monomer_functional_groups.csv`、`compatible_monomer_pairs.csv`。
- `pievo_faithful` 会复用同一候选池，但把候选选择交给 IDS。
- `trail/candidates/build_component_inventory.py` 会输出 `component_inventory.csv` 和 `functional_group_index.csv`。
- `scripts/expand_sparse_candidate_templates.py` 已生成 `artifacts/trail/candidates_expanded/component_inventory.csv`，候选数从 694 增至 743。
- expanded source audit 显示 `cyanate_ester/maleimide/isocyanate/anhydride/thiol` 都已达到当前 sparse coverage 阈值。

## 3. 预测模型

现有体系：

- 论文复现模型：CNN、SVR、RF。
- 扩展 model zoo：MLP、GBR、KRR、LightGBM、XGBoost、CatBoost、NGBoost、ExtraTrees、GPR、KNN、PLS、ElasticNet 等。
- GNN 草案：`trail/gnn/train_gnn.py`。
- 集成分歧审计：`scripts/run_predictor_ensemble_disagreement.py` 会从同一 latent size 的强模型中计算候选级 ensemble mean/std/range，把 epistemic/OOD 风险写入 `artifacts/trail/predictors/ensemble_disagreement/`。

关键指标：

- MAE。
- RMSE。
- MAPE：保留，但摄氏度接近 0 或负数时不可靠。
- MAPEK：Kelvin 分母，更适合 Tg 温度。
- R2。
- PCP。

训练/评估要求：

- 默认遵循论文 85/15 train/test split。
- 模型选择应优先看 `MAPEK test`、`MAE test`、`RMSE test` 和 R2 的综合表现。
- 任何用于 agent 的 predictor 都必须保存模型路径、latent size、训练特征路径和指标。
- 单一最佳模型不能单独决定推荐顺序；当前 workflow 同时记录 target distance、Harness、PiEvo posterior 和 predictor ensemble disagreement。

## 4. 生成模型策略

当前生成层先不做复杂扩散/流匹配训练，先形成多策略候选生成：

- 规则模板生成：保留已知热固性结构 motif。
- 替换生成：按官能团和 Morgan fingerprint 相似度替换单体。
- VAE latent 邻域搜索：未来可在 latent space 中扰动，再 decode。
- LLM/RAG 生成：未来可用知识库检索约束 prompt，生成 SMILES 或候选规则。
- Harness 控制：所有生成结果必须通过 RDKit、charset、元素、官能团、反应兼容、ratio simplex 等约束。

生成不是最终决策；生成只产生候选 `h`，评估和选择由 predictor、PiEvo posterior、IDS 共同完成。

## 5. 闭环 autonomous workflow

闭环结构：

```text
界定搜索空间 -> 生成假设 -> 预测/评估 -> 选择实验 -> 更新 principle posterior -> anomaly augmentation -> 下一轮
```

Agent 分工：

- Space Agent：确定目标 Tg、组分数量、ratio 范围、硬约束、候选来源。
- Generator Agent：产生候选配方。
- Predictor Agent：调用 VAE-WVCM predictor、GNN 和 model zoo ensemble，给出 Tg mean/sigma、模型间分歧和 OOD 风险。
- Principle Agent：维护 principle space，处理 anomaly，提出新 principle。
- Experiment Agent：执行 surrogate 或真实实验观测。
- Optimizer Agent：用 IDS 选择下一步最值得观测的候选。

当前落地：

- `trail/workflow/multi_agent_workflow.py` 是摘要级 workflow。
- `src/smp02/pievo_faithful.py` 是更接近 PiEvo 数学的闭环实现。

## 6. PiEvo-faithful 要求

必须具备：

- `p_t(P)` principle posterior。
- 每个 principle 一个 GP expert。
- full-history posterior update。
- MAP residual anomaly。
- coherent augmentation。
- IDS selection。

不能把 PiEvo 简化为：

- 多生成几个候选再排序。
- 给规则加一个固定 bonus。
- 只看接近目标或 OOD 就叫 anomaly。

## 7. 后续迭代优先级

第一优先级：

- 跑通 `configs/pievo_faithful_smoke.yaml`。
- 检查 `principle_posterior.json` 是否能随 history 改变。
- 检查 `candidate_diagnostics.csv` 是否包含 regret、information gain、IDS ratio。
- 将 agent_discovery 的候选池与 PiEvo-faithful 的选择结果对比。

第二优先级：

- 建立候选组分 registry 文档和 CSV 自动构建脚本。
- 将知识库 YAML 扩展为更完整的 reaction/prior ontology。
- 加入真实实验结果导入接口，让真实 Tg 以更高权重更新 posterior。

第三优先级：

- 用 LLM/RAG 生成 anomaly-derived principles。
- 对 dormant principle 做剪枝策略。
- 对不同目标 Tg 批量运行，观察 posterior 是否随目标变化。
