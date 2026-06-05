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

### 第五轮

- `scripts/run_pievo_target_sweep.py`：多目标 PiEvo-faithful smoke runner。
- `artifacts/pievo_faithful_target_sweep_smoke/*`：190、200、250 C 三个目标分别运行的 PiEvo-faithful 输出。
- `reports/pievo_target_sweep_smoke.md`：多目标闭环中文对比报告。

### 第六轮

- `src/smp02/pievo_faithful.py`：新增 target-feasible IDS，先在目标可行域内执行 warmup/IDS；可行域不足时才回退全候选。
- `configs/pievo_faithful_smoke.yaml`、`configs/pievo_faithful_ledger_smoke.yaml`、`configs/pievo_faithful_250.yaml`：开启 `target_guard_enabled`，5 C guard。
- `tests/test_pievo_faithful_math.py`：新增 target guard warmup 选择测试，防止高方差远目标候选抢占实验轮次。
- `artifacts/pievo_faithful_smoke/*`、`artifacts/pievo_faithful_ledger_smoke/*`、`artifacts/pievo_faithful_target_sweep_smoke/*`：按 target-feasible IDS 重跑 smoke。
- `docs/pievo_faithful_smp.md`：新增 Target-Feasible IDS 数学说明。
- `reports/pievo_target_sweep_smoke.md`：更新多目标闭环结果。

### 第七轮

- `scripts/evaluate_replacement_proposals.py`：把 VAE replacement proposals 重建为完整配方，送入 VAE-WVCM-GPR predictor 和 Harness；现默认 CPU deterministic encoding，避免 CUDA 非确定数值路径导致 ledger 漂移。
- `artifacts/trail/generation/replacement_eval/*`：replacement 预测、Harness、rejection、observation ledger 输出。
- `configs/pievo_faithful_replacement_195_smoke.yaml`：读取 replacement observation ledger 的 195 C PiEvo-faithful smoke 配置。
- `artifacts/pievo_faithful_replacement_195_smoke/*`：replacement observations 进入 PiEvo posterior 的 smoke 输出。
- `reports/replacement_proposal_evaluation.md`：replacement proposal 预测与 Harness 中文报告。
- `reports/replacement_pievo_feedback_smoke.md`：replacement observation 进入 PiEvo-faithful 的中文报告。
- `docs/generation_strategy_and_harness.md`：更新 replacement 生成闭环状态。

### 第八轮

- `trail/generation/generation_record_schema.yaml`：新增 generation record ledger schema，覆盖 LLM/RAG/prompt/SFT/扩散/流匹配等生成器的共同记录契约。
- `trail/generation/import_generation_records.py`：新增 generation record 导入和校验脚本，自动计算 SMILES/ratio/prediction/target/chemistry/Harness 状态和失败原因。
- `scripts/build_prompt_generation_records.py`：新增可复现 prompt/RAG smoke runner，不调用外部 LLM，但记录 prompt、RAG refs、候选 JSON 和 Harness 回流。
- `artifacts/trail/generation/prompt_records/*`：prompt/RAG generation packet、input records、ledger 和 summary。
- `reports/generation_record_schema_smoke.md`：generation record schema smoke 中文报告。
- `tests/test_generation_records.py`：新增 generation ledger 失败回流测试。
- `trail/generation/generation_strategy_registry.yaml`：从“计划中的 record schema”升级为 schema/importer/smoke 输出可追踪。
- `docs/generation_strategy_and_harness.md`：补充 LLM/RAG/prompt record schema 当前状态和下一步。

### 第九轮

- `trail/candidates/source_registry.yaml`：新增候选组分来源 registry，记录 `library/generated/chembl/generation_record` 的来源类型、权威等级、证据文件、用途和信任边界。
- `scripts/audit_candidate_sources.py`：新增候选来源和官能团覆盖审计脚本。
- `artifacts/trail/candidates_source_audit/*`：候选来源 summary、官能团来源覆盖表和 JSON 摘要。
- `reports/candidate_source_audit.md`：候选来源与官能团覆盖中文报告。
- `trail/candidates/README.md`：补充 source registry 和 audit 命令。
- `tests/test_candidate_source_audit.py`：新增稀疏高价值官能团检测测试。

### 第十轮

- `trail/knowledge/smp_prior_knowledge.yaml`：新增 `literature_sources`、`process_condition_templates`、`reaction_evidence_map`、`structural_evidence_map`。
- `trail/knowledge/ontology.yaml`：新增 `LiteratureSource`、`ProcessConditionTemplate` 以及 `supported_by_source`、`conditioned_by_process` 关系。
- `trail/knowledge/build_kg.py`：构图时写入文献来源节点、工艺条件模板节点和证据/工艺边。
- `artifacts/trail/kg_enriched/*`：重建知识图谱，规模更新为 126 个节点、151 条边。
- `docs/smp_knowledge_base_and_ontology.md`：更新知识图谱规模、工艺条件模板和后续结构化 observation 要求。
- `reports/knowledge_provenance_process_update.md`：新增知识来源和工艺条件中文报告。
- `tests/test_knowledge_graph_provenance.py`：新增 KG provenance/process 边测试。

### 第十一轮

- `trail/gnn/train_gnn.py`：GNN 从单一 GCN 扩展为 `gcn/gin/gat/mpnn` 可选架构，并加入 bond edge features。
- `scripts/run_gnn_architecture_smoke.py`：新增 GNN 多架构 smoke runner，汇总同一 85/15 split 下的 leaderboard。
- `artifacts/trail/gnn_architecture_smoke/*`：GCN、GIN、GAT、MPNN 5 epoch smoke metrics、predictions、模型权重和总 leaderboard。
- `reports/gnn_architecture_smoke_leaderboard.md`：新增 GNN 多架构中文 leaderboard。
- `reports/gnn_metric_alignment_smoke.md`：更新下一步，说明 GIN/GAT/MPNN 已完成 smoke。
- `tests/test_gnn_architectures.py`：新增四种 GNN 架构 forward 测试。

### 第十二轮

- `scripts/analyze_generation_feedback.py`：新增 generation failure feedback analyzer，把 generation ledger 和 replacement rejection 转成策略级 pass rate、失败原因、policy delta 和下一轮约束。
- `artifacts/trail/generation_feedback/*`：生成 `strategy_feedback.csv`、`failure_reason_counts.csv`、`replacement_failure_groups.csv` 和 `generation_feedback_summary.json`。
- `reports/generation_failure_feedback.md`：新增失败回流中文报告。
- `trail/workflow/multi_agent_workflow.py`：多智能体 workflow 增加 `harness_agent`、`feedback_agent`、`human_review_agent`，并读取 generation feedback summary。
- `artifacts/trail/workflow/multi_agent_summary.json`：重生成 workflow summary，包含 generation ledger 和 feedback 摘要。
- `docs/closed_loop_workflow.md`：更新闭环说明，把 PiEvo-faithful、generation feedback 和 human review agent 纳入 workflow。
- `docs/generation_strategy_and_harness.md`：新增“失败回流”小节。
- `tests/test_generation_feedback.py`：新增失败原因和策略 policy delta 测试。

## 任务映射

| TODO 项 | 当前状态 | 证据 | 下一步 |
| --- | --- | --- | --- |
| 真实 Tg 温度不固定 | 已完成候选重排、闭环目标 sweep 和 target-feasible IDS | `reports/variable_target_tg_analysis.md`，`reports/pievo_target_sweep_smoke.md` | 扩大 rounds/candidate_batch_size 做正式目标 sweep |
| 表示层超图 | 暂缓 | 本文档明确 deferred | 等用户恢复该方向 |
| 知识库/先验库 | 已有官能团/反应/本体/文献来源/工艺条件模板 | `trail/knowledge/*.yaml`，`artifacts/trail/kg_enriched/`，`docs/smp_knowledge_base_and_ontology.md`，`reports/knowledge_provenance_process_update.md` | 把真实文献配方和固化程序转成结构化 observation/process records |
| 候选组分数据集 | inventory、来源 registry、官能团覆盖审计已完成 | `trail/candidates/build_component_inventory.py`，`trail/candidates/source_registry.yaml`，`reports/candidate_source_audit.md` | 针对 cyanate/maleimide/isocyanate/anhydride/thiol 从 SMP 文献扩展候选 |
| 预测模型 | model zoo、GNN 指标对齐和 GCN/GIN/GAT/MPNN smoke leaderboard 已完成 | `reports/model_selection_analysis.md`，`reports/gnn_metric_alignment_smoke.md`，`reports/gnn_architecture_smoke_leaderboard.md` | 做更长 GNN 训练，并加入官能团/reaction/process 全局特征和 ensemble disagreement |
| 生成模型 | replacement proposals 已进入 predictor、Harness、ledger 和 PiEvo；generation record schema 和失败回流已覆盖 LLM/RAG/prompt smoke | `reports/replacement_proposal_evaluation.md`，`reports/replacement_pievo_feedback_smoke.md`，`reports/generation_record_schema_smoke.md`，`reports/generation_failure_feedback.md` | 接入真实 LLM/RAG agent，按 feedback policy delta 约束下一轮生成 |
| 闭环 workflow | PiEvo-faithful 已接收 ledger 加权历史，target-feasible IDS 和 generation failure feedback 已接入 workflow summary | `src/smp02/pievo_faithful.py`，`artifacts/pievo_faithful_ledger_smoke/`，`artifacts/trail/workflow/multi_agent_summary.json` | 对多个目标温度运行带 feedback 的 PiEvo，并比较 posterior/strategy feedback |
| RL/人工闭环/真实实验 | observation schema、posterior 接入、human review agent 和 generation feedback smoke 已完成 | `trail/experiments/observation_schema.yaml`，`reports/pievo_faithful_ledger_feedback_smoke.md`，`reports/generation_failure_feedback.md` | 用真实实验替换示例占位行，建立结构化工艺审核记录 |
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

## 第五轮结论

- 190、200、250 C 三个目标已经分别进入 PiEvo-faithful 闭环运行，不再只是对同一候选表做后处理排序。
- 每个目标都生成独立的 output directory、candidate diagnostics、selected formulations、round history 和 posterior。
- 候选诊断表中三个目标都有近目标候选：190 C 最近 0.13 C，200 C 最近 0.23 C，250 C 最近 0.37 C。
- 但 4 轮小 smoke 的 IDS/暖启动实际选择并没有总是选中近目标候选：190 C best selected 距离 30.32 C，200 C best selected 距离 39.72 C，250 C best selected 距离 16.89 C。
- 这说明当前 PiEvo-faithful 的短程探索策略已能发现近目标候选，但“选择进入 observation history”的策略还需要加入目标命中约束或调低 warmup 探索，否则正式闭环会浪费实验轮次。

## 第六轮结论

- Target-feasible IDS 已经修复第五轮暴露的问题：保留 PiEvo 的 IDS 公式，但把可选域限制为 `target_distance_c <= 5 C` 的候选；若没有足够可行候选再回退全集。
- 普通 250 C smoke 的 4 个 selected 全部在 5 C 内，最佳距离 0.53 C。
- Ledger 250 C smoke 的 4 个 selected 全部在 5 C 内，最佳距离 0.37 C；外部 ledger 仍有 2 条观测、总权重 6。
- 多目标 190/200/250 C smoke 的全部 selected 都在 5 C 内，best selected 分别为 189.87 C、199.89 C、249.47 C，距离分别为 0.13 C、0.11 C、0.53 C。
- 这一步不是放弃探索，而是把 IDS 放进“可实验/可推荐”的目标可行域内，避免短程闭环把实验轮次浪费在明显偏离目标的配方上。

## 第七轮结论

- VAE replacement proposals 已经从孤立 CSV 进入完整闭环：`proposal -> rebuild formulation -> predictor -> Harness -> observation ledger -> PiEvo posterior`。
- 120 条 replacement proposals 中，107 条可重建并预测，10 条通过 Harness，13 条因反应/比例约束失败被拒绝。
- 评估脚本现默认 CPU deterministic VAE encoding；稳定审计路径下，通过项中最佳 replacement 预测 Tg 为 194.63 C，距 195 C 目标 0.37 C；4 条在 1 C 内，10 条在 5 C 内。
- 10 条通过项已写入 replacement observation ledger，并作为外部 surrogate history 进入 195 C PiEvo-faithful。
- Replacement-PiEvo smoke 接收 10 条外部 replacement observations，posterior history 共 14 条；本轮 PiEvo 新选择最佳预测 Tg 为 194.99 C，距 195 C 目标 0.01 C。

## 第八轮结论

- Generation record schema 已经落地，不再只是 registry 里的字段清单。它把 `strategy/stage/target/candidate/prompt/RAG/prediction/Harness/PiEvo/review` 放在同一条可审计记录中。
- Prompt/RAG smoke 生成 4 条 records：2 条 `llm_rag_principle_generation`、1 条 `functional_group_replacement`、1 条 `llm_smiles_generation` draft。
- 4 条 records 都满足 schema 基本字段；其中 3 条通过 Harness，1 条 draft 失败并保留 `prediction_missing;chemistry_evidence_missing;replacement_formula_failed_reaction_or_ratio_constraints`。
- 最佳 prompt/RAG generation record 预测 Tg 为 195.00 C，距 195 C 目标 0.003 C。
- 当前 smoke 没有调用外部 LLM；它的作用是定义未来 LLM/RAG/SFT/扩散/流匹配生成器必须遵守的记录契约，防止生成结果绕过 Harness 或丢失失败原因。

## 第九轮结论

- 候选组分数据集现在不只是 `component_inventory.csv`，还拥有来源 registry，可区分 `library`、`generated`、`chembl` 和未来 `generation_record` 的信任边界。
- 当前 smoke inventory 有 694 个小分子候选：`library=225`、`generated=10`、`chembl=459`；所有 inventory source 都已在 registry 中注册。
- 官能团覆盖为 18 类。稀疏高价值官能团仍明显不足：`cyanate_ester=3`、`maleimide=5`、`isocyanate=7`、`anhydride=10`、`thiol=13`。
- 下一步候选扩展不应盲目扩大 ChEMBL，而应优先从 SMP 文献和人工规则模板补足这些稀疏但对热固性交联很关键的官能团。

## 第十轮结论

- 知识图谱现在把“规则/先验是什么”和“证据/工艺条件来自哪里”分开建模，避免把官能团兼容规则误当成无条件物理真理。
- KG 规模从 109 节点/95 边扩展到 126 节点/151 边；其中包括 5 个文献/证据来源节点、8 个工艺条件模板节点、36 条 `supported_by_source` 边和 20 条 `conditioned_by_process` 边。
- 每条反应原则都连接到一个工艺条件模板，例如 `epoxy_primary_amine -> epoxy_amine_thermal_cure`、`cyanate_ester_self -> cyanate_ester_triazine_cure`。
- 这些工艺模板只是要求字段和审计框架，不代表真实实验已经完成；真实 DSC 或文献复现仍需进入 observation ledger，并结构化记录催化剂、固化温度、后固化、引发方式等。

## 第十一轮结论

- GNN 预测模型不再只有一个简单 GCN smoke；现在同一脚本支持 `gcn/gin/gat/mpnn`，并且 MPNN 使用 bond edge features。
- 5 epoch smoke leaderboard 中，MPNN 最好：MAPEK test 11.0512%，MAE test 47.1922 C，R2 test 0.5651。
- GIN 次之：MAPEK test 15.2202%，MAE test 60.4392 C。5 epoch 下 GCN/GAT 明显欠拟合。
- 这些结果仍显著弱于当前最佳 VAE-WVCM-GPR：MAPEK test 3.9778%，MAE test 18.7641 C。因此 GNN 当前适合作为结构视角和 OOD/ensemble disagreement 信号，不应替代主代理模型。

## 第十二轮结论

- 失败回流已经从文档建议变成可运行分析：`generation_ledger + replacement_rejections -> strategy feedback / failure reasons / replacement group feedback`。
- 当前分析覆盖 4 条 generation records 和 13 条 replacement rejections；主失败原因为 `replacement_formula_failed_reaction_or_ratio_constraints`，共 14 次。
- `llm_rag_principle_generation` pass rate 为 1.0，policy delta 为 +0.10；`functional_group_replacement` pass rate 为 0.071，policy delta 为 -0.10；`llm_smiles_generation` pass rate 为 0，policy delta 为 -0.25。
- 这说明下一轮不能只按共享官能团/Tanimoto 做 replacement，必须在替换后立即验证互补反应对；LLM SMILES 草案也必须先补 predictor 和 chemistry evidence。
- 这些 policy delta 不是最终 RL policy，也不是物理真理；它们是给下一轮生成器排序和人工审核的可审计建议。
