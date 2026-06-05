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
- `trail/generation/vae_replacement_strategy.py --component-inventory artifacts/trail/candidates_expanded/component_inventory.csv` 已把 expanded inventory 接入 strict replacement，并保留 `literature_template` provenance。
- `scripts/run_feedback_aware_llm_rag_agent.py --preferred-replacement-source literature_template` 已把 expanded replacement 的成功记录接入 LLM/RAG 上下文。

## 3. 预测模型

现有体系：

- 论文复现模型：CNN、SVR、RF。
- 扩展 model zoo：MLP、GBR、KRR、LightGBM、XGBoost、CatBoost、NGBoost、ExtraTrees、GPR、KNN、PLS、ElasticNet 等。
- GNN：`trail/gnn/train_gnn.py`，支持 GCN/GIN/GAT/MPNN、bond edge features，以及可选 global formulation features。
- 集成分歧审计：`scripts/run_predictor_ensemble_disagreement.py` 会从同一 latent size 的强模型中计算候选级 ensemble mean/std/range，把 epistemic/OOD 风险写入 `artifacts/trail/predictors/ensemble_disagreement/`。
- PiEvo live ensemble guard：`configs/pievo_faithful_ensemble_guard_195_smoke.yaml` 会对 PiEvo 每轮实际候选批次运行 top-k model zoo，并用 `predictor_ensemble_std_tg_c` 收缩 IDS selection pool。
- GNN global feature smoke：`scripts/run_gnn_global_feature_smoke.py` 对比 baseline MPNN 与 global-feature MPNN，确认组分数/比例熵、官能团权重和 reaction compatibility 特征可以进入 GNN head；当前 5 epoch 下未改善 MAPEK/MAE。

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
- 单一最佳模型不能单独决定推荐顺序；当前 workflow 同时记录 target distance、Harness、PiEvo posterior 和 predictor ensemble disagreement，并已能在 PiEvo selection pool 中过滤高分歧候选。

## 4. 生成模型策略

当前生成层先不做复杂扩散/流匹配训练，先形成多策略候选生成：

- 规则模板生成：保留已知热固性结构 motif。
- 替换生成：按官能团和 Morgan fingerprint 相似度替换单体。
- Expanded replacement：从 expanded inventory 选择替换分子，保留 source/template provenance，并用 strict counterpart compatibility 过滤。
- VAE latent 邻域搜索：`trail/generation/vae_latent_local_search.py` 已在 expanded inventory 内按 VAE latent 距离检索局部替换单体；当前是 decoder-free inventory search，不声称直接 decoder 生成新 SMILES。
- LLM/RAG 生成：未来可用知识库检索约束 prompt，生成 SMILES 或候选规则。
- SFT / diffusion / flow 数据契约：`scripts/import_proposal_eval_generation_records.py` 先把已评分 proposals 写回 generation record ledger，`scripts/build_generative_training_sets.py` 再把通过 Harness 的 records 转成 SFT JSONL 和 diffusion/flow seed table；当前 SFT readiness 已通过，SFT dry-run generator 已产生 records，diffusion/flow 仍受 seed-table gate 约束。
- Strategy-level bandit policy：`scripts/update_generation_strategy_policy.py` 会把各生成策略的 Harness pass、target reward、失败回流和 readiness gate 汇总成下一轮 proposal 预算建议。
- Harness 控制：所有生成结果必须通过 RDKit、charset、元素、官能团、反应兼容、ratio simplex 等约束。

生成不是最终决策；生成只产生候选 `h`，评估和选择由 predictor、PiEvo posterior、IDS 共同完成。

VAE latent local search 当前 195 C smoke：

- 200 条 latent proposals，200 条可重建并评分。
- 42 条通过 Harness，最佳 target distance 为 0.200 C。
- `literature_template` 有 39 条 proposals、7 条通过 Harness。
- 42 条通过项进入 PiEvo-faithful external observation ledger 后，4 轮 selected 全部通过 target guard，最佳 selected distance 为 0.059 C。
- scored latent proposals 已写回 generation record ledger，并和 expanded replacement records 一起把 SFT 训练候选扩展到 64 条。
- `scripts/run_sft_candidate_generator_dry_run.py` 已用 SFT train split validated prototypes 生成 25 条 `sft_candidate_generator` records，25 条全部通过 Harness；这是链路验证，不是神经权重微调完成。

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
- workflow summary 已读取 expanded replacement、VAE latent local search、expanded LLM/RAG summary 和 generation strategy bandit policy，用来确认 expanded inventory 与策略优化是否真正进入生成链路，而不只是停留在 source audit。

当前 bandit policy 状态：

- 6 个策略被纳入 arm：VAE latent local search、functional-group replacement、LLM/RAG principle generation、LLM SMILES draft、SFT candidate generator、diffusion/flow matching。
- 4 个策略 eligible active；1 个 suppressed；1 个 data_collection_only。
- top strategy 为 `llm_rag_principle_generation`。
- `sft_candidate_generator` 已因 64 条 SFT 样本和 25 条 dry-run records 进入 active arm；`diffusion_or_flow_matching` 仍因 seed rows 不足只进入数据收集目标；`llm_smiles_generation` 在缺 predictor/chemistry evidence 时不进入下一轮预算。

当前 human review queue 状态：

- `scripts/build_human_experiment_review_queue.py` 已把 surrogate/PiEvo/Harness 候选转成人工实验复核队列。
- 输入 58 条候选，去重 43 条，输出 30 条 review items。
- 30 条 draft process records 基础格式通过，但 `ready_for_active_ledger=0`，说明仍需人工补固化/催化/后固化/酰亚胺化等工艺字段。
- 这一步把“真实实验结果迭代优化”前的人工质量门禁落成 artifact，而不是直接把 surrogate 结果冒充真实实验。

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
- 对 GNN global features 做更长训练，并评估是否作为结构视角加入 predictor ensemble disagreement。
- SFT dry-run 已跑通；下一步可做真实神经 SFT/LLM 权重训练或用外部 provider 替换 prototype replay。继续扩大通过 Harness 且进入 observation ledger 的 generation records，把 diffusion/flow seed rows 从 64 条补到 100 条以上。
