# 20260606_01 TODO 执行状态

本文档是对 `TODO.md` 的执行化记录。每次继续该 goal 时都应重新读取 `TODO.md`，再更新本状态。

## 本轮读取到的 TODO 要点

- 真实 Tg 温度不固定。
- 表示层：真实商品级组分、聚合物、复杂材料的超图建模。当前明确暂缓，不做。
- 知识库：官能团匹配、化学反应原理、知识图谱、本体。
- 候选组分数据集：SMP 论文、数据库、按官能团分类。
- 预测模型：GNN、CNN/SVR/RF 论文对比，以及更多模型。
- 生成模型：VAE 替换策略、LLM、SFT、prompt、RAG、Harness、扩散/流匹配。
- 闭环：搜索空间 -> 生成假设 -> 预测/评估 -> 优化假设；多智能体、RL、人工闭环、真实实验迭代；充分尊重 PiEvo 数学公式。

## 当前边界

暂缓：

- 真实商品级组分和聚合物超图/异构图表示。

继续：

- 小分子 SMILES / MoleCode / VAE-WVCM 表示。
- 可变目标 Tg。
- PiEvo-faithful 闭环。
- 知识库、候选集、模型、生成策略和 workflow 文档化与代码化。

## 本轮新增交付物

### 第一轮

- `src/smp02/pievo_faithful.py`：PiEvo-faithful 闭环骨架。
- `configs/pievo_faithful_250.yaml`：250 C 目标配置。
- `configs/pievo_faithful_smoke.yaml`：快速验证配置。
- `tests/test_pievo_faithful_math.py`：核心数学函数测试。
- `docs/pievo_faithful_smp.md`：PiEvo-faithful 数学设计说明。
- `docs/smp_research_system_plan.md`：TODO 总体研究系统路线图。
- `artifacts/pievo_faithful_smoke/*`：PiEvo-faithful smoke 运行产物，4 轮观测，硬约束验证通过。
- `trail/candidates/build_component_inventory.py`：候选小分子组分 inventory 构建脚本。
- `artifacts/trail/candidates_smoke/*`：候选组分 smoke inventory，694 个候选，18 类官能团。

### 第二轮

- `trail/knowledge/smp_prior_knowledge.yaml`：扩展为结构先验、适用域先验、硬约束、20 条反应原则和候选来源。
- `trail/knowledge/ontology.yaml`：扩展本体类与关系。
- `trail/knowledge/build_kg.py`：适配新 schema，输出 graphml/json/summary。
- `artifacts/trail/kg_enriched/*`：扩展知识图谱，109 个节点、95 条边。
- `docs/smp_knowledge_base_and_ontology.md`：知识库与本体中文说明。
- `scripts/summarize_model_zoo.py`：预测模型 zoo 自动汇总脚本。
- `reports/model_selection_analysis.md`：预测模型中文对比报告。
- `docs/generation_strategy_and_harness.md`：生成模型与 Harness 策略文档。
- `trail/generation/generation_strategy_registry.yaml`：生成策略 registry 和记录 schema。
- `trail/harness/constraints.py`：支持可变目标 `target-center/window` 和多组分 `smiles|ratios` 格式。
- `artifacts/trail/harness/pievo_smoke_validation.csv`：PiEvo smoke 的 harness 验证，250±20 C 下 3/4 通过。
- `artifacts/trail/generation/replacement_proposals.csv`：替换生成 proposals，120 条。

### 第三轮

- `scripts/analyze_variable_targets.py`：对同一候选池按多个目标 Tg 重新排序、重新计算距离和 reward。
- `artifacts/trail/target_sweep/*`：190、195、200、250 C 四个目标的候选汇总和 top-k 明细。
- `reports/variable_target_tg_analysis.md`：可变目标 Tg 中文分析报告。
- `trail/gnn/train_gnn.py`：GNN 训练脚本补齐 85/15 split、MAPEK、MAE、RMSE、PCP、R2 和 prediction/metrics 输出。
- `artifacts/trail/gnn_aligned_smoke/*`：GNN 指标对齐 smoke 输出。
- `reports/gnn_metric_alignment_smoke.md`：GNN 与 model zoo 指标对齐说明。
- `trail/experiments/observation_schema.yaml`：真实实验、文献、高保真模拟、surrogate observation ledger schema。
- `trail/experiments/import_observations.py`：实验观测导入、校验、加权 reward 计算脚本。
- `trail/experiments/example_observations.csv`：schema 演示数据；其中真实 DSC 行是占位示例，不代表真实实验已经完成。
- `artifacts/trail/experiments/*`：observation ledger 导入 smoke 输出。
- `docs/real_experiment_feedback_loop.md`：真实实验、人工审核和 PiEvo posterior 更新的接入说明。

### 第四轮

- `src/smp02/pievo_faithful.py`：外部 observation ledger 接入 PiEvo full-history posterior。
- `configs/pievo_faithful_ledger_smoke.yaml`：带 ledger 的 PiEvo-faithful smoke 配置。
- `tests/test_pievo_faithful_math.py`：新增外部观测加载和 authority weight posterior 测试。
- `artifacts/pievo_faithful_ledger_smoke/*`：ledger smoke 输出，包含 `observation_history.csv`、`external_observations_used.csv`、`external_observation_summary.json`。
- `reports/pievo_faithful_ledger_feedback_smoke.md`：外部观测进入 posterior 的中文 smoke 报告。
- `docs/pievo_faithful_smp.md`：补充加权 full-history posterior 公式。
- `docs/real_experiment_feedback_loop.md`：从“后续应接入”更新为“当前已接入”。

## 任务映射

| TODO 项 | 当前状态 | 证据 | 下一步 |
| --- | --- | --- | --- |
| 真实 Tg 温度不固定 | 第三轮已批量验证 | `scripts/analyze_variable_targets.py`，`reports/variable_target_tg_analysis.md` | 按目标温度分别运行 PiEvo-faithful，而不只重排已有候选 |
| 表示层超图 | 暂缓 | 本文档明确 deferred | 等用户恢复该方向 |
| 知识库/先验库 | 第二版完成 | `trail/knowledge/*.yaml`，`artifacts/trail/kg_enriched/`，`docs/smp_knowledge_base_and_ontology.md` | 加文献来源和工艺条件字段 |
| 候选组分数据集 | 初版已有 | `trail/candidates/build_component_inventory.py`，`artifacts/trail/candidates_smoke/` | 扩展论文来源 registry |
| 预测模型 | model zoo 和 GNN 指标已对齐 | `reports/model_selection_analysis.md`，`reports/gnn_metric_alignment_smoke.md` | 将 GNN 加入正式 leaderboard，并尝试 GIN/GAT/MPNN |
| 生成模型 | 第二版策略完成 | `docs/generation_strategy_and_harness.md`，`trail/generation/generation_strategy_registry.yaml`，`artifacts/trail/generation/replacement_proposals.csv` | 将 replacement proposals 送入 predictor/PiEvo |
| 闭环 workflow | PiEvo-faithful 已接收 ledger 加权历史 | `src/smp02/pievo_faithful.py`，`artifacts/pievo_faithful_ledger_smoke/` | 对多个目标温度运行带 ledger 的 PiEvo，并比较 posterior |
| RL/人工闭环/真实实验 | schema 与 posterior 接入已完成 smoke | `trail/experiments/observation_schema.yaml`，`reports/pievo_faithful_ledger_feedback_smoke.md` | 用真实实验替换示例占位行，建立审核流程 |
| GitHub 同步 | 待本轮验证后执行 | git status/commit/push | 测试通过后提交 |

## 对“发现新规律、抛弃没用规律”的当前理解

PiEvo-faithful 模式中，principle 不再是固定加分项，而是带后验的解释假说。若某条 principle 无法解释历史观测，其 full-history likelihood 低，posterior 会下降；若 anomaly-derived principle 能解释 MAP principle 解释失败的观测，其 posterior 会上升。

需要注意：当前观测仍主要来自 VAE-WVCM surrogate，因此这些规律是 surrogate-consistent candidate principles，不是最终物理真理。真实 DSC/合成结果应作为更高权重观测进入闭环。

本轮 smoke 只有 4 个观测，posterior 只出现轻微非均匀化，这是正常现象。后续应增加 rounds、candidate_batch_size 和真实/高保真观测，才有足够 evidence 明显提升或压低 principle。

## 第二轮模型结论

- 当前按 MAPEK 选择的最佳模型仍是 `VAE(512)+GaussianProcess_RBF`，MAPEK test 为 3.9778%，适合 PiEvo-faithful 使用其不确定性。
- `VAE(512)+NuSVR_RBF` 的 MAE/RMSE/R2 更强，适合作为点预测强基线或 ensemble 成员。
- 论文 RF/CNN/SVR 基线已纳入报告；RF 明显优于当前 CNN/SVR，model zoo 又优于 RF。
- 普通摄氏度 MAPE 不适合作为主指标，继续以 MAPEK/MAE/RMSE/R2 共同判断。

## 第三轮结论

- 真实目标 Tg 不应写死为 250 C。同一候选池在 190、195、200、250 C 下都有大量 within-5C 候选，但这只是重排序；真正的下一步是让 PiEvo-faithful 对每个目标分别更新 posterior 和选择策略。
- 当前 GNN smoke 只是指标对齐验证，不是强模型。10 epoch 简单 GCN 的 test MAPEK 为 16.3492%，MAE 为 65.8156 C，明显弱于 VAE-WVCM model zoo。它的价值是后续可以作为结构视角模型或 ensemble disagreement/OOD 信号。
- 真实实验闭环已经有最小可执行 ledger。后续任何 DSC、文献复现实验或高保真模拟都应先进入 ledger，再以更高 authority weight 参与 posterior 更新。
- PiEvo 规律发现目前仍是 surrogate-consistent。要真正“发现新规律、抛弃没用规律”，必须把高权重真实观测加入 full-history likelihood。

## 第四轮结论

- PiEvo-faithful 现在已经真正接收外部 observation ledger，而不是只在文档中描述。外部观测以 round 0 history 进入 posterior。
- 后验公式已经变为 `log p_t(P) = log p0(P) + sum_s w_s log p(y_s | h_s, P)`，其中 `w_s` 来自 `authority_weight`。
- Ledger smoke 接收 2 条外部观测、0 条拒绝；外部权重为 6，总 posterior history 为 6 条、总权重为 10。
- 本轮 smoke 最佳新 surrogate 选择为预测 Tg 249.63 C，距离 250 C 目标 0.37 C。
- 示例 ledger 中 `real_dsc` 仍是占位示例，不是实际 DSC 物理结果；真实实验数据替换后，posterior 才能开始更可靠地压低弱 principle。
