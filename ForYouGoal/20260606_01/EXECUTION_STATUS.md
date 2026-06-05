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

### 第十三轮

- `trail/experiments/process_record_schema.yaml`：新增 process record ledger schema，结构化记录文献/真实/高保真/人工审核工艺条件。
- `trail/experiments/example_process_records.csv`：新增 Paper Table 6 A/B 和 replacement surrogate 107 的 process review 示例。
- `trail/experiments/import_process_records.py`：新增 process record 导入与完整性校验脚本。
- `artifacts/trail/experiments/process_record_ledger.csv`、`process_record_summary.json`：process record smoke 输出。
- `reports/process_record_schema_smoke.md`：新增 process record 中文 smoke 报告。
- `docs/real_experiment_feedback_loop.md`：补充 observation ledger 与 process record ledger 的关系。
- `tests/test_process_records.py`：新增 process template 必填字段和 active ledger readiness 测试。

### 第十四轮

- `trail/generation/vae_replacement_strategy.py`：新增 feedback-guided strict replacement 模式，要求替换分子必须和未替换的另一侧单体保留可映射互补反应对。
- `scripts/evaluate_replacement_proposals.py`：把 `counterpart_groups`、`counterpart_compatibility_reason`、`feedback_constraint` 透传到 scored CSV，并让空 rejection CSV 保持稳定表头。
- `artifacts/trail/generation/feedback_guided_replacement_proposals.csv`：strict replacement proposals，120 条，每条都有非空 counterpart compatibility reason。
- `artifacts/trail/generation/feedback_guided_replacement_eval/*`：strict replacement 的 predictor、Harness、observation ledger 和 summary 输出。
- `reports/feedback_guided_replacement_evaluation.md`：strict replacement 预测与 Harness 中文报告。
- `reports/feedback_guided_replacement_comparison.md`：原始 replacement 与 feedback-guided replacement 对比报告。
- `tests/test_replacement_strategy_feedback.py`：新增互补反应对过滤测试。

### 第十五轮

- `configs/pievo_faithful_feedback_replacement_195_smoke.yaml`：新增 strict replacement observation ledger 的 195 C PiEvo-faithful smoke 配置。
- `artifacts/pievo_faithful_feedback_replacement_195_smoke/*`：feedback-guided replacement observations 进入 PiEvo posterior 的完整输出。
- `scripts/compare_pievo_feedback_ledgers.py`：新增原始 replacement ledger 与 feedback-guided replacement ledger 的 PiEvo posterior 对比脚本。
- `artifacts/trail/generation/feedback_guided_replacement_pievo_compare/*`：posterior delta、summary CSV/JSON 输出。
- `reports/feedback_guided_replacement_pievo_comparison.md`：feedback-guided replacement ledger 进入 PiEvo 后的中文对比报告。
- `docs/closed_loop_workflow.md`、`docs/generation_strategy_and_harness.md`：更新 replacement feedback -> PiEvo posterior 的闭环状态。
- `tests/test_pievo_feedback_comparison.py`：新增 PiEvo feedback ledger 对比脚本测试。

### 第十六轮

- `scripts/run_feedback_replacement_target_sweep.py`：新增 feedback-guided strict replacement 多目标 runner，对每个目标重新执行 replacement eval、observation ledger 和 PiEvo-faithful。
- `artifacts/trail/generation/feedback_guided_replacement_target_sweep/*`：190/195/200/250 C 的 replacement evaluation、ledger、动态 PiEvo config 和 sweep summary。
- `artifacts/pievo_faithful_feedback_replacement_target_sweep/*`：190/195/200/250 C 的 6 轮 PiEvo-faithful 输出。
- `reports/feedback_guided_replacement_target_sweep.md`：feedback-guided replacement 多目标闭环中文报告。
- `tests/test_feedback_replacement_target_sweep.py`：新增 target slug、动态配置和 sweep summary 测试。
- `scripts/evaluate_replacement_proposals.py`：让空 replacement observation input 也保持 observation ledger schema 表头，支持目标无通过项时的稳定 pipeline。
- `docs/closed_loop_workflow.md`、`docs/generation_strategy_and_harness.md`、`trail/generation/generation_strategy_registry.yaml`：补充多目标 replacement feedback 闭环。

### 第十七轮

- `artifacts/trail/generation_feedback_strict/*`：基于 strict replacement 空 rejection 表重新生成 strategy feedback；`functional_group_replacement` 从旧负策略变为保留策略。
- `reports/generation_failure_feedback_strict.md`：strict feedback 中文报告。
- `scripts/run_feedback_aware_llm_rag_agent.py`：新增 feedback-aware LLM/RAG agent，读取 RAG 上下文和 strict strategy feedback，输出 generation records。
- `trail/rag/simple_retriever.py`：过滤单字符和纯数字 query token，避免 `C`、`0` 这类噪声压过 strict feedback RAG 上下文。
- `artifacts/trail/generation/feedback_aware_llm_rag/*`：agent packet、policy、input records、generation ledger 和 summary。
- `reports/feedback_aware_llm_rag_agent.md`：feedback-aware LLM/RAG agent 中文报告。
- `tests/test_feedback_aware_llm_rag_agent.py`：新增 policy 抑制和 offline agent ledger 导入测试。
- `tests/test_simple_retriever.py`：新增 RAG 检索噪声 token 过滤测试。
- `docs/closed_loop_workflow.md`、`docs/generation_strategy_and_harness.md`、`trail/generation/generation_strategy_registry.yaml`：补充 feedback-aware LLM/RAG agent 状态和命令入口。

### 第十八轮

- `scripts/import_generation_ledger_observations.py`：新增 generation ledger -> surrogate observation ledger 桥接脚本，只提升 Harness/record/pass 且有预测的 records。
- `artifacts/trail/generation/feedback_aware_llm_rag_observations/*`：feedback-aware LLM/RAG generation records 转 observation input、observation ledger 和 summary。
- `configs/pievo_faithful_feedback_aware_llm_rag_195_smoke.yaml`：新增读取 LLM/RAG surrogate observation ledger 的 195 C PiEvo-faithful 6 轮 smoke 配置。
- `artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke/*`：LLM/RAG observations 进入 PiEvo posterior 后的 selected、history、posterior 和 summary。
- `reports/feedback_aware_llm_rag_pievo_feedback.md`：feedback-aware LLM/RAG -> observation ledger -> PiEvo 中文报告。
- `tests/test_generation_observation_bridge.py`：新增桥接门禁测试，防止 draft/缺预测 records 被提升为 observations。
- `trail/workflow/multi_agent_workflow.py`、`artifacts/trail/workflow/multi_agent_summary.json`：workflow summary 增加 feedback-aware observation ledger 和 PiEvo summary 字段。
- `docs/closed_loop_workflow.md`、`docs/generation_strategy_and_harness.md`、`trail/generation/generation_strategy_registry.yaml`：补充 LLM/RAG records 进入 PiEvo 的完整链路。

### 第十九轮

- `trail/candidates/sparse_functional_group_templates.yaml`：新增稀疏高价值官能团候选模板库，覆盖 cyanate ester、maleimide、isocyanate、anhydride、thiol。
- `scripts/expand_sparse_candidate_templates.py`：新增 sparse functional-group candidate expansion 脚本，执行 RDKit/允许元素/单片段/官能团检测/去重。
- `artifacts/trail/candidates_expanded/*`：扩展 inventory、functional group index、summary、added/rejected 模板明细。
- `artifacts/trail/candidates_expanded_source_audit/*`：对 expanded inventory 重新做 source audit 和 functional-group coverage。
- `reports/sparse_candidate_template_expansion.md`：新增候选稀疏官能团扩展中文报告。
- `reports/candidate_source_audit_expanded.md`：新增 expanded inventory source audit 中文报告。
- `trail/candidates/source_registry.yaml`：新增 `literature_template` 来源及其 authority/trust boundary。
- `trail/candidates/build_component_inventory.py`：修复空/NaN groups 被写成伪官能团 `nan` 的 summary 问题。
- `trail/candidates/README.md`：补充 expanded inventory 构建和复审命令。
- `tests/test_sparse_candidate_template_expansion.py`：新增模板扩展和空 group 过滤测试。

### 第二十轮

- `scripts/run_predictor_ensemble_disagreement.py`：新增 predictor ensemble disagreement 审计脚本，从当前 model zoo 中选取同一 latent size 的强模型，计算候选层面的模型间分歧。
- `artifacts/trail/predictors/ensemble_disagreement/*`：输出候选集 ensemble mean/std/range、低分歧近目标候选、高分歧近目标候选、成员模型表和 summary。
- `reports/predictor_ensemble_disagreement.md`：新增模型集成分歧/OOD 风险中文报告。
- `trail/workflow/multi_agent_workflow.py`：workflow summary 接入 predictor ensemble disagreement summary。
- `artifacts/trail/workflow/multi_agent_summary.json`：重生成后包含 predictor ensemble 模型数、近目标数、低/高分歧数和平均分歧。
- `tests/test_predictor_ensemble_disagreement.py`：新增 candidate schema、model selection 和 disagreement bucket 测试。
- `tests/test_workflow_summary.py`：新增 workflow summary 读取 predictor ensemble disagreement 的测试。
- `docs/closed_loop_workflow.md`、`docs/smp_research_system_plan.md`、`docs/generation_strategy_and_harness.md`、`reports/model_selection_analysis.md`、`reports/gnn_metric_alignment_smoke.md`：补充 predictor ensemble disagreement 当前状态。

### 第二十一轮

- `src/smp02/pievo_faithful.py`：新增 live predictor ensemble disagreement，PiEvo 每轮对实际候选批次运行 top-k model zoo，并写入 ensemble mean/std/range、bucket 和 human review priority。
- `src/smp02/pievo_faithful.py`：新增 ensemble disagreement guard，在 target guard 后用 `predictor_ensemble_std_tg_c <= tau` 收缩 IDS selection pool；若低分歧候选不足则回退，避免过度保守。
- `configs/pievo_faithful_ensemble_guard_195_smoke.yaml`：新增 195 C live ensemble guard smoke 配置。
- `artifacts/pievo_faithful_ensemble_guard_195_smoke/*`：新增 6 轮 PiEvo live ensemble guard 输出，包括 `candidate_diagnostics.csv`、`selected_formulations.csv`、`round_history.json`、`predictor_ensemble_members.csv` 和 summary/report。
- `reports/pievo_ensemble_disagreement_guard_smoke.md`：新增 PiEvo live ensemble guard 中文 smoke 报告。
- `docs/pievo_faithful_smp.md`：新增 Ensemble-Guard IDS 数学说明，明确 disagreement 是选择域/人工审核信号，不进入 principle likelihood。
- `trail/workflow/multi_agent_workflow.py`、`artifacts/trail/workflow/multi_agent_summary.json`：workflow summary 新增 PiEvo ensemble guard 结果字段。
- `tests/test_pievo_faithful_math.py`：新增 ensemble disagreement guard 选择池测试。
- `tests/test_workflow_summary.py`：新增 workflow summary 读取 PiEvo ensemble guard summary 的测试。
- `docs/closed_loop_workflow.md`、`docs/smp_research_system_plan.md`、`docs/generation_strategy_and_harness.md`、`reports/model_selection_analysis.md`：补充 live ensemble guard 当前状态。

### 第二十二轮

- `trail/generation/vae_replacement_strategy.py`：新增 `--component-inventory` replacement pool 入口，可直接使用 `artifacts/trail/candidates_expanded/component_inventory.csv`，并保留 `replacement_source/label/template_family/template_intended_group` provenance。
- `scripts/evaluate_replacement_proposals.py`：将 replacement provenance 透传到 scored CSV、observation notes 和报告，并统计 `literature_template_scored`、`literature_template_harness_pass`。
- `artifacts/trail/generation/expanded_inventory_replacement_proposals.csv`：expanded inventory strict replacement proposals，200 条。
- `artifacts/trail/generation/expanded_inventory_replacement_eval/*`：expanded replacement 的 predictor、Harness、observation ledger、summary 输出；200 条可重建并评分，18 条通过 Harness，29 条 `literature_template` 被评分，3 条通过 Harness。
- `reports/expanded_inventory_replacement_evaluation.md`：expanded inventory replacement 中文评估报告；最佳 `literature_template` 候选预测 Tg 为 194.48 C，距 195 C 目标 0.52 C。
- `scripts/run_feedback_aware_llm_rag_agent.py`：新增 `--preferred-replacement-source`，expanded inventory 场景下优先把 `replacement_source=literature_template` 的成功 replacement record 纳入 LLM/RAG 上下文；报告路径也改为实际 out-dir 路径。
- `artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag/*`：expanded feedback-aware LLM/RAG records、ledger、policy、packet 和 summary；2 条 records 都通过 Harness，`literature_template_context_rows=1`。
- `reports/expanded_inventory_feedback_aware_llm_rag_agent.md`：expanded inventory LLM/RAG agent 中文报告。
- `trail/workflow/multi_agent_workflow.py`、`artifacts/trail/workflow/multi_agent_summary.json`：workflow summary 新增 expanded replacement 与 expanded LLM/RAG 字段。
- `tests/test_replacement_strategy_feedback.py`：新增 expanded component inventory replacement provenance 测试。
- `tests/test_workflow_summary.py`：新增 workflow summary 读取 expanded inventory 链路字段测试。
- `docs/closed_loop_workflow.md`、`docs/smp_research_system_plan.md`、`docs/generation_strategy_and_harness.md`、`trail/generation/generation_strategy_registry.yaml`：补充 expanded inventory 接入 replacement/LLM/RAG/workflow 的命令、状态和 registry。

### 第二十三轮

- `trail/gnn/train_gnn.py`：新增 `--global-features`，在 graph pooling 后拼接 31 维 formulation-level global vector；特征包括组分数/比例熵、RDKit 加权结构描述符、18 类官能团权重、互补反应对覆盖和 reactive group weight。
- `trail/gnn/train_gnn.py`：`GNNRegressor` 新增 `global_channels`，支持 GCN/GIN/GAT/MPNN 在不改变小分子图表示的情况下读取配方级特征。
- `scripts/run_gnn_architecture_smoke.py`：支持 `--global-features`，可对多架构统一打开 global formulation features。
- `scripts/run_gnn_global_feature_smoke.py`：新增 baseline vs global-feature GNN smoke runner。
- `artifacts/trail/gnn_global_feature_smoke/*`：新增 MPNN baseline/global 两组 metrics、predictions、模型权重、comparison CSV 和 summary JSON。
- `reports/gnn_global_feature_smoke.md`：新增 GNN global feature 中文 smoke 报告。
- `trail/workflow/multi_agent_workflow.py`、`artifacts/trail/workflow/multi_agent_summary.json`：workflow summary 新增 GNN global-feature 字段。
- `tests/test_gnn_architectures.py`：新增 global feature vector、batching 和 MPNN forward 测试。
- `tests/test_workflow_summary.py`：新增 workflow summary 读取 GNN global-feature summary 的测试。
- `reports/model_selection_analysis.md`、`reports/gnn_metric_alignment_smoke.md`、`docs/smp_research_system_plan.md`、`docs/closed_loop_workflow.md`：补充 GNN global-feature 当前状态和审计边界。

### 第二十四轮

- `scripts/build_generative_training_sets.py`：新增 SFT / diffusion / flow 训练数据构建脚本，从 generation record ledgers 中筛选 `record_pass + harness_pass + prediction_available` 的候选。
- `artifacts/trail/generation/generative_training_sets/sft_generation_records.jsonl`：新增 SFT JSONL，assistant 输出为 auditable generation record JSON，不是自由文本推荐。
- `artifacts/trail/generation/generative_training_sets/diffusion_flow_seed_table.csv`：新增 diffusion/flow seed table，记录 target Tg、SMILES、比例、surrogate Tg、reward、compatibility evidence 和 source ledger。
- `artifacts/trail/generation/generative_training_sets/generative_training_summary.json`：新增 readiness summary；当前 8 条 generation ledger 输入、7 条 Harness pass、去重后 5 条训练候选。
- `reports/generative_training_set_readiness.md`：新增 SFT / diffusion / flow readiness 中文报告；SFT 为 4 train/1 eval，`sft_ready=false`，还缺 15 条；diffusion/flow 为 4 train/1 eval，`diffusion_flow_ready=false`，还缺 95 条。
- `trail/workflow/multi_agent_workflow.py`、`artifacts/trail/workflow/multi_agent_summary.json`：workflow summary 新增 generative training readiness 字段。
- `tests/test_generative_training_sets.py`：新增训练语料构建过滤测试，防止 draft/失败 records 进入 SFT 或 diffusion/flow seed。
- `tests/test_workflow_summary.py`：新增 workflow summary 读取 generative training readiness 的测试。
- `trail/generation/generation_strategy_registry.yaml`、`docs/generation_strategy_and_harness.md`、`docs/smp_research_system_plan.md`、`docs/closed_loop_workflow.md`：将 SFT/扩散/流匹配从“纯 future/deferred”更新为“训练数据契约已实现，readiness 未通过”。

### 第二十八轮

- `scripts/import_proposal_eval_generation_records.py`：新增 scored proposal eval -> generation record ledger 桥接脚本，把已完成 predictor/Harness 的 proposals 写回统一 generation ledger。
- `artifacts/trail/generation/vae_latent_local_search_records/*`：导入 200 条 VAE latent local search scored proposals，200 条 record 基础字段通过，42 条 Harness pass。
- `artifacts/trail/generation/expanded_inventory_replacement_records/*`：导入 200 条 expanded replacement scored proposals，200 条 record 基础字段通过，18 条 Harness pass。
- `scripts/build_generative_training_sets.py`：默认输入新增上述两个 proposal generation ledgers。
- `artifacts/trail/generation/generative_training_sets/*`、`reports/generative_training_set_readiness.md`：重生成 SFT/diffusion/flow 训练语料；当前 408 条 ledger 输入、67 条 Harness pass、64 条训练候选；SFT 为 52 train/12 eval，`sft_ready=true`；diffusion/flow 为 52 train/12 eval，`diffusion_flow_ready=false`，还缺 36 条。
- `artifacts/trail/generation_strategy_policy/*`、`reports/generation_strategy_bandit_policy.md`：重算 strategy bandit；6 个策略中 4 个 eligible active、1 个 suppressed、1 个 data_collection_only；SFT candidate generator 成为 active arm。
- `artifacts/trail/workflow/multi_agent_summary.json`：重生成 workflow summary，接入新的 SFT readiness 和 strategy policy 数字。
- `tests/test_proposal_eval_generation_records.py`：新增 proposal eval 桥接门禁测试，防止失败 proposals 绕过 Harness 进入训练标签。
- `trail/generation/generation_strategy_registry.yaml`、`docs/generation_strategy_and_harness.md`、`docs/closed_loop_workflow.md`、`docs/smp_research_system_plan.md`：同步 proposal ledger bridge、SFT ready 和 diffusion/flow 仍未 ready 的当前状态。

### 第二十九轮

- `scripts/run_sft_candidate_generator_dry_run.py`：新增内部 SFT candidate generator dry-run，用 SFT train split validated prototypes 生成 `sft_candidate_generator` generation records。
- `artifacts/trail/generation/sft_candidate_dry_run/*`：生成 25 条 SFT dry-run records，25 条全部通过 generation record/Harness；最佳 target distance 为 0.003 C，mean generation reward 为 0.7778；heldout eval 12 条，其中 3 条 exact candidate match。
- `reports/sft_candidate_generator_dry_run.md`：新增 SFT dry-run 中文报告，明确当前 mode 是 `prototype_replay_not_weight_update`，不冒充神经权重微调完成。
- `scripts/update_generation_strategy_policy.py`：SFT arm 优先读取 SFT dry-run generation summary；若 dry-run 不存在则回退到 SFT readiness。
- `artifacts/trail/generation_strategy_policy/*`、`reports/generation_strategy_bandit_policy.md`：重算策略预算；`sft_candidate_generator` 以 25/25 dry-run pass 的实际 generation evidence 成为 active arm，获得 21/100 proposal budget 建议。
- `trail/workflow/multi_agent_workflow.py`、`artifacts/trail/workflow/multi_agent_summary.json`：workflow summary 新增 SFT dry-run rows、Harness pass、best distance、heldout eval 和 exact match 字段。
- `tests/test_sft_candidate_generator_dry_run.py`、`tests/test_generation_strategy_policy.py`、`tests/test_workflow_summary.py`：新增 SFT dry-run、policy dry-run evidence 和 workflow 字段测试。
- `trail/generation/generation_strategy_registry.yaml`、`docs/generation_strategy_and_harness.md`、`docs/closed_loop_workflow.md`、`docs/smp_research_system_plan.md`：同步 SFT dry-run 当前状态和下一步边界。

### 第三十轮

- `scripts/build_rule_template_generation_records.py`：新增 rule-template generation record 构建脚本，把当前 selected candidate space 的近目标规则/模板候选写入统一 generation ledger。
- `artifacts/trail/generation/rule_template_records/*`、`reports/rule_template_generation_records.md`：生成 50 条 `rule_template` records，50 条全部通过 importer/Harness；最佳 target distance 为 0.003 C，mean generation reward 为 0.9888。
- `artifacts/trail/generation/original_replacement_records/*`、`reports/original_replacement_generation_records.md`：把原始 replacement scored proposals 写回 generation record ledger，107 条输入、10 条 Harness pass，最佳 target distance 为 0.373 C。
- `artifacts/trail/generation/feedback_guided_replacement_records/*`、`reports/feedback_guided_replacement_generation_records.md`：把 feedback-guided strict replacement scored proposals 写回 generation record ledger，120 条输入、11 条 Harness pass，最佳 target distance 为 0.373 C。
- `artifacts/trail/generation/feedback_guided_replacement_target_records/target_190/*`、`target_195/*`、`target_200/*`、`target_250/*`：把多目标 strict replacement scored proposals 写回 generation record ledgers；对应 Harness pass 为 13、11、11、4。
- `reports/feedback_guided_replacement_target_190_generation_records.md`、`reports/feedback_guided_replacement_target_195_generation_records.md`、`reports/feedback_guided_replacement_target_200_generation_records.md`、`reports/feedback_guided_replacement_target_250_generation_records.md`：新增多目标 proposal eval -> generation ledger 桥接报告。
- `scripts/build_generative_training_sets.py`：默认输入扩展到 12 个 generation ledgers，包含 rule-template、prompt/RAG、原始/strict replacement、VAE latent local search、expanded replacement 和多目标 strict replacement 账本。
- `artifacts/trail/generation/generative_training_sets/*`、`reports/generative_training_set_readiness.md`：重建训练语料；当前 1165 条 ledger 输入、177 条 Harness pass、143 条训练候选。SFT 为 124 train/19 eval，`sft_ready=true`；diffusion/flow seed table 为 124 train/19 eval，`diffusion_flow_ready=true`。
- `artifacts/trail/generation/sft_candidate_dry_run/*`、`reports/sft_candidate_generator_dry_run.md`：基于扩展后 SFT JSONL 重跑 dry-run，25 条 records 全部通过 Harness；mean generation reward 为 0.9922，heldout eval 19 条，exact candidate match 为 0。
- `scripts/update_generation_strategy_policy.py`、`artifacts/trail/generation_strategy_policy/*`、`reports/generation_strategy_bandit_policy.md`：重算 strategy bandit；6 个策略中 5 个 eligible active、1 个 suppressed、0 个 data_collection_only。SFT 获得 23/100，diffusion/flow 因 seed gate 已通过获得 19/100。
- `artifacts/trail/workflow/multi_agent_summary.json`：workflow summary 已读取新的训练语料、SFT dry-run 和 strategy policy 字段，记录 `generative_training_diffusion_flow_ready=true`、`generation_strategy_policy_data_collection_only_strategies=0`。
- `tests/test_rule_template_generation_records.py`、`tests/test_generation_strategy_policy.py`：新增 rule-template ledger 构建测试和 ready diffusion/flow active arm 测试。
- `trail/generation/generation_strategy_registry.yaml`、`docs/generation_strategy_and_harness.md`、`docs/closed_loop_workflow.md`、`docs/smp_research_system_plan.md`：同步 rule-template baseline、143 条训练候选、diffusion/flow readiness 和下一步训练边界。

### 第三十一轮

- `scripts/run_diffusion_flow_candidate_generator_dry_run.py`：新增 diffusion/flow candidate generator dry-run，用 diffusion/flow seed table 的 train split validated seed prototypes 生成 `diffusion_or_flow_matching` generation records。
- `artifacts/trail/generation/diffusion_flow_candidate_dry_run/*`：生成 19 条 diffusion/flow dry-run records，19 条全部通过 generation record/Harness；最佳 target distance 为 0.003 C，mean generation reward 为 0.9934；heldout eval 19 条，exact candidate match 为 0。
- `reports/diffusion_flow_candidate_generator_dry_run.md`：新增 diffusion/flow dry-run 中文报告，明确当前 mode 是 `conditional_seed_replay_not_weight_update`，不冒充神经扩散或 flow-matching 权重训练完成。
- `scripts/update_generation_strategy_policy.py`：diffusion/flow arm 优先读取 diffusion/flow dry-run generation summary；若 dry-run 不存在则回退到 seed-table readiness。
- `artifacts/trail/generation_strategy_policy/*`、`reports/generation_strategy_bandit_policy.md`：重算策略预算；`diffusion_or_flow_matching` 以 19/19 dry-run pass 的实际 generation evidence 成为 active arm，获得 23/100 proposal budget 建议；SFT 为 22/100。
- `trail/workflow/multi_agent_workflow.py`、`artifacts/trail/workflow/multi_agent_summary.json`：workflow summary 新增 diffusion/flow dry-run rows、Harness pass、best distance、heldout eval 和 exact match 字段。
- `tests/test_diffusion_flow_candidate_generator_dry_run.py`、`tests/test_generation_strategy_policy.py`、`tests/test_workflow_summary.py`：新增 diffusion/flow dry-run、policy dry-run evidence 和 workflow 字段测试。
- `trail/generation/generation_strategy_registry.yaml`、`docs/generation_strategy_and_harness.md`、`docs/closed_loop_workflow.md`、`docs/smp_research_system_plan.md`：同步 diffusion/flow dry-run 当前状态和下一步边界。

### 第三十二轮

- `scripts/train_conditional_flow_matching_generator.py`：新增轻量条件 flow-matching 训练脚本，在 31 维 formulation global feature 空间训练 MLP velocity field，并用目标 Tg 作为条件。
- `artifacts/trail/generation/diffusion_flow_trained_generator/*`：训练 120 epoch 后生成模型 checkpoint、scaler、training summary、nearest seed projection、generation input records 和 generation ledger。
- `reports/diffusion_flow_trained_generator.md`：新增训练型 flow projection 中文报告，明确当前是 `conditional_flow_matching_trained_projection`，不是直接 SMILES diffusion 生成。
- 本轮 trained projection 从 184 个连续样本中投影得到 23 条 `diffusion_or_flow_matching` records，23 条全部通过 generation record/Harness；最佳 target distance 为 0.005 C，mean generation reward 为 0.8340。
- 训练指标：train loss 从 1.888 降到 1.313，eval loss 为 1.802，projection distance mean 为 5.025。
- `scripts/update_generation_strategy_policy.py`：diffusion/flow arm 现在优先读取 trained projection summary，其次读取 dry-run summary，再回退到 seed-table readiness。
- `artifacts/trail/generation_strategy_policy/*`、`reports/generation_strategy_bandit_policy.md`：重算策略预算；`diffusion_or_flow_matching` 使用 23/23 trained projection evidence，获得 18/100 proposal budget 建议；SFT 为 23/100。
- `trail/workflow/multi_agent_workflow.py`、`artifacts/trail/workflow/multi_agent_summary.json`：workflow summary 新增 trained flow rows、Harness pass、best distance、train/eval loss 和 projection distance 字段。
- `tests/test_conditional_flow_matching_generator.py`、`tests/test_generation_strategy_policy.py`、`tests/test_workflow_summary.py`：新增 flow training/projection、policy trained evidence 和 workflow 字段测试。
- `trail/generation/generation_strategy_registry.yaml`、`docs/generation_strategy_and_harness.md`、`docs/closed_loop_workflow.md`、`docs/smp_research_system_plan.md`：同步 trained flow projection 当前状态和下一步边界。

## 任务映射

| TODO 项 | 当前状态 | 证据 | 下一步 |
| --- | --- | --- | --- |
| 真实 Tg 温度不固定 | 已完成候选重排、闭环目标 sweep、target-feasible IDS，以及 feedback-guided replacement 的多目标 PiEvo sweep | `reports/variable_target_tg_analysis.md`，`reports/pievo_target_sweep_smoke.md`，`reports/feedback_guided_replacement_target_sweep.md` | 扩大候选池并接入真实/高保真 observation 做正式目标 sweep |
| 表示层超图 | 暂缓 | 本文档明确 deferred | 等用户恢复该方向 |
| 知识库/先验库 | 已有官能团/反应/本体/文献来源/工艺条件模板，并有 process record 校验 | `trail/knowledge/*.yaml`，`artifacts/trail/kg_enriched/`，`docs/smp_knowledge_base_and_ontology.md`，`reports/knowledge_provenance_process_update.md`，`reports/process_record_schema_smoke.md` | 从更多 SMP 文献抽取具体固化程序，补全 process fields |
| 候选组分数据集 | inventory、来源 registry、官能团覆盖审计、稀疏高价值官能团模板扩展、expanded inventory 复审，以及 expanded inventory -> replacement/LLM/RAG 上下文接入已完成 | `trail/candidates/build_component_inventory.py`，`trail/candidates/source_registry.yaml`，`trail/candidates/sparse_functional_group_templates.yaml`，`reports/candidate_source_audit.md`，`reports/sparse_candidate_template_expansion.md`，`reports/candidate_source_audit_expanded.md`，`reports/expanded_inventory_replacement_evaluation.md`，`reports/expanded_inventory_feedback_aware_llm_rag_agent.md` | 持续用真实/高保真 observation 调整 source authority，并检查 expanded source 在不同目标 Tg 下是否稳定贡献候选 |
| 预测模型 | model zoo、GNN 指标对齐、GCN/GIN/GAT/MPNN smoke leaderboard、GNN global formulation feature smoke、predictor ensemble disagreement 审计和 PiEvo live ensemble guard 已完成 | `reports/model_selection_analysis.md`，`reports/gnn_metric_alignment_smoke.md`，`reports/gnn_architecture_smoke_leaderboard.md`，`reports/gnn_global_feature_smoke.md`，`reports/predictor_ensemble_disagreement.md`，`reports/pievo_ensemble_disagreement_guard_smoke.md` | 做更长 GNN 训练，谨慎加入 process condition template 特征，并把 GNN 结构视角纳入同一 disagreement/OOD 审计 |
| 生成模型 | replacement proposals 已进入 predictor、Harness、ledger 和 PiEvo；generation record schema、失败回流、feedback-guided replacement strict 约束、PiEvo posterior 对比、多目标 sweep、feedback-aware LLM/RAG agent、LLM/RAG records -> observation ledger -> PiEvo bridge、expanded inventory replacement/LLM-RAG 上下文，以及 SFT/diffusion/flow 训练数据契约已落地；rule-template baseline records 已加入统一 ledger；SFT readiness 与 diffusion/flow seed-table readiness 均已通过；SFT dry-run、diffusion/flow dry-run 和轻量条件 flow-matching trained projection 均已生成并通过 Harness | `reports/replacement_proposal_evaluation.md`，`reports/replacement_pievo_feedback_smoke.md`，`reports/generation_record_schema_smoke.md`，`reports/generation_failure_feedback.md`，`reports/generation_failure_feedback_strict.md`，`reports/feedback_guided_replacement_comparison.md`，`reports/feedback_guided_replacement_pievo_comparison.md`，`reports/feedback_guided_replacement_target_sweep.md`，`reports/feedback_aware_llm_rag_agent.md`，`reports/feedback_aware_llm_rag_pievo_feedback.md`，`reports/expanded_inventory_replacement_evaluation.md`，`reports/expanded_inventory_feedback_aware_llm_rag_agent.md`，`reports/vae_latent_local_search_generation_records.md`，`reports/expanded_inventory_replacement_generation_records.md`，`reports/rule_template_generation_records.md`，`reports/generative_training_set_readiness.md`，`reports/sft_candidate_generator_dry_run.md`，`reports/diffusion_flow_candidate_generator_dry_run.md`，`reports/diffusion_flow_trained_generator.md` | 可以用真实神经 SFT/LLM 权重训练替换 prototype replay，也可以改进 flow training/projection 或加入有效 SMILES decoder。所有生成输出仍必须写入 ledger，并经过 predictor、Harness、PiEvo 和人工审核 |
| 闭环 workflow | PiEvo-faithful 已接收 ledger 加权历史，target-feasible IDS、generation failure feedback、LLM/RAG observation bridge、predictor ensemble disagreement、live ensemble guard、expanded inventory generation summary、GNN global-feature summary、proposal generation ledger bridge、rule-template generation records、SFT/diffusion readiness、SFT dry-run、diffusion/flow dry-run、trained flow projection 和 strategy bandit policy 已接入 workflow summary；replacement 侧已能用 failure feedback 改变下一轮生成分布、改变 principle posterior，并在多目标 Tg 下运行 | `src/smp02/pievo_faithful.py`，`artifacts/pievo_faithful_ledger_smoke/`，`artifacts/trail/workflow/multi_agent_summary.json`，`artifacts/trail/generation/feedback_guided_replacement_target_sweep/`，`artifacts/trail/generation/feedback_aware_llm_rag/`，`artifacts/trail/generation/feedback_aware_llm_rag_observations/`，`artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke/`，`artifacts/trail/predictors/ensemble_disagreement/`，`artifacts/pievo_faithful_ensemble_guard_195_smoke/`，`artifacts/trail/generation/expanded_inventory_replacement_eval/`，`artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag/`，`artifacts/trail/gnn_global_feature_smoke/`，`artifacts/trail/generation/rule_template_records/`，`artifacts/trail/generation/generative_training_sets/`，`artifacts/trail/generation/sft_candidate_dry_run/`，`artifacts/trail/generation/diffusion_flow_candidate_dry_run/`，`artifacts/trail/generation/diffusion_flow_trained_generator/`，`artifacts/trail/generation_strategy_policy/` | 用真实/高保真 observation 验证 surrogate posterior 规律，并把外部 LLM provider、GNN disagreement、expanded source provenance、真实 SFT 输出复评、diffusion/flow 训练输出和真实实验风险复核接入同一审计链 |
| RL/人工闭环/真实实验 | observation schema、process record schema、posterior 接入、human review agent 和 generation feedback smoke 已完成 | `trail/experiments/observation_schema.yaml`，`trail/experiments/process_record_schema.yaml`，`reports/pievo_faithful_ledger_feedback_smoke.md`，`reports/generation_failure_feedback.md`，`reports/process_record_schema_smoke.md` | 用真实实验替换示例占位行，并补齐 process fields 后批准进入 active ledger |
| GitHub 同步 | 持续执行，每轮验证后提交推送 | git status/commit/push | 后续继续按轮次同步 |

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

## 第十三轮结论

- 真实/文献 Tg 现在不再只是 observation ledger 的一个数字；process record ledger 会检查固化程序、催化剂、后固化等模板字段是否完整。
- Paper Table 6 的 A/B 配方已进入 process review 示例：A 距 195 C 目标 16.86 C，B 距 195 C 目标 27.07 C；二者都缺 `solvent;imidization_temperature_c;imidization_time_h`，因此不能标记为 `ready_for_active_ledger`。
- Replacement surrogate 107 距 195 C 目标 0.37 C，但缺 `trimerization_temperature_c;catalyst_loading;post_cure_temperature_c`，因此仍是 `needs_human_review`。
- 当前 3 条 process records 基础格式全部通过，但 0 条 ready for active ledger。这是刻意的质量门禁：缺工艺条件的文献/候选不能直接作为高权重物理证据进入 PiEvo posterior。

## 第十四轮结论

- 第十二轮失败回流现在已经真正改变了 replacement 生成器：`--require-counterpart-compatibility` 要求替换后仍存在 `compatibility_reason(counterpart_groups, replacement_groups)`。
- Feedback-guided replacement 仍生成 120 条 proposals，但每条都带有非空 `counterpart_compatibility_reason`，可以审计它保留的是哪类反应对。
- 原始 replacement 的重建失败为 13 条，strict replacement 的重建失败为 0 条；Harness 通过数从 10 增至 11。
- Strict replacement 的最佳预测 Tg 仍为 194.63 C，距 195 C 目标 0.37 C；within-1C 仍为 4 条，within-5C 从 10 条增至 11 条。
- 这说明“共享官能团 + Tanimoto”应被视为局部相似性启发式，而“替换后保留互补反应对”应作为 replacement 生成的硬约束。该结论仍然只是 surrogate/Harness 层面的，不等价于真实物理实验结论。

## 第十五轮结论

- Strict replacement observation ledger 已进入 PiEvo-faithful，不再只停留在生成和 Harness 评估层。
- 原始 replacement ledger 给 PiEvo 10 条外部 surrogate observations；feedback-guided strict ledger 给 PiEvo 11 条，外部 mean reward 从 0.7148 提升到 0.7185。
- 在相同随机种子、195 C 目标、target guard 和 PiEvo 参数下，4 轮 IDS 选择集合完全相同，最佳新选择仍为 194.99 C，距目标 0.01 C。
- 但 principle posterior 明显变化：posterior entropy 从 2.4869 降到 1.4358，MAP principle `long_aliphatic_penalty` 后验从 0.4749 升到 0.7454。
- 这说明 feedback-guided replacement 本轮主要让 posterior 更集中，而不是马上改变短程 IDS 选择路径。后续应扩大目标温度 sweep、rounds 和候选批次，验证这种 posterior 收缩在更长闭环里是否会改变推荐配方。

## 第十六轮结论

- Feedback-guided strict replacement 已从单一 195 C 扩展为 190/195/200/250 C 多目标闭环；每个目标都重新计算 replacement target window、external observation ledger reward 和 PiEvo full-history posterior。
- 6 轮 smoke 的最佳新 PiEvo 选择分别为 190.06、194.99、199.80、249.90 C，距对应目标分别为 0.057、0.006、0.204、0.099 C，所有 selected 都通过 Harness。
- Strict replacement 在四个目标下的 Harness 通过数分别为 13、11、11、4；250 C 也仍有 4 条 replacement observations 可作为外部 history。
- MAP principle 会随目标变化：190 C 为 `reaction_a5dd26ae10ad`，195 C 为 `long_aliphatic_penalty`，200 C 为 `too_flexible_penalty`，250 C 为 `heavy_halogen_practical_risk`。
- 这一步证明“真实 Tg 不固定”已经进入 replacement evaluation、ledger reward 和 PiEvo posterior 三层，而不是只在候选 CSV 上做后处理排序。当前仍是 surrogate smoke，真实 DSC/高保真数据进入后才可确认这些 posterior 规律是否可靠。

## 第十七轮结论

- Strict feedback 版本已经把 replacement 最新状态反馈给生成策略：`functional_group_replacement` pass rate 为 1.0、policy delta 为 +0.10；`llm_rag_principle_generation` 也为 +0.10；`llm_smiles_generation` 仍为 -0.25。
- Feedback-aware LLM/RAG agent 已经读取 RAG 上下文和 strict strategy feedback，默认 `offline_policy` provider 保持可复现；若设置 `OPENAI_API_KEY`，可切换 `openai_compatible` provider。
- Agent 默认 RAG 上下文已聚焦 strategy registry、strict feedback、PiEvo 数学说明和 target sweep，且检索器会过滤单字符/纯数字噪声 token，避免旧 replacement rejection 历史压过最新 strict policy。
- Agent smoke 生成 2 条 `llm_rag_principle_generation` records，2 条都通过 generation ledger/Harness；最佳 target distance 为 0.003 C，mean generation reward 为 0.9637。
- 当前 agent 明确抑制 `llm_smiles_generation` 自由草案，因为它缺 predictor 和 chemistry evidence；成功 strict replacement 被作为 RAG evidence，而不是继续沿用旧失败策略状态。
- 这一步不是直接相信 LLM 输出，而是把 LLM/RAG 变成“候选 JSON 生成器”：所有候选必须先进入 generation record ledger，再经过 RDKit、ratio、prediction、target、chemistry gate，后续才允许进入 PiEvo 或人工审核。

## 第十八轮结论

- Feedback-aware LLM/RAG 现在不再停在 generation ledger：2 条通过 Harness 的 records 已转成 surrogate observation ledger，2 条都通过 observation ledger 校验。
- observation ledger 的平均 target distance 为 0.188 C，mean weighted reward 为 0.9637；source_type 保持为 `surrogate`，没有冒充真实 DSC 或文献观测。
- `configs/pievo_faithful_feedback_aware_llm_rag_195_smoke.yaml` 读取这 2 条外部 observations 后运行 6 轮 PiEvo-faithful；外部 observation 接收 2 条、拒绝 0 条，总外部 authority weight 为 2.0。
- 6 轮 selected 全部通过 target guard 和 validation，最佳 selected distance 为 0.0055 C；MAP principle 为 `reaction_a5dd26ae10ad`，posterior entropy 为 3.5038。
- 这一步把 LLM/RAG 闭环补齐为 `strict feedback -> RAG agent -> generation record -> observation ledger -> PiEvo full-history posterior -> workflow summary`。失败 draft 仍留在 generation feedback 中，不会被提升为 observation。

## 第十九轮结论

- 候选组分数据集不再只是发现稀疏问题：本轮新增 49 个 `literature_template` 小分子候选，expanded inventory 从 694 增至 743。
- 五个稀疏高价值官能团全部跨过 source registry 中的 15 个覆盖阈值：cyanate_ester 3 -> 15、maleimide 5 -> 16、isocyanate 7 -> 16、anhydride 10 -> 16、thiol 13 -> 24。
- expanded source audit 中未注册来源为 0，`sparse_high_value_groups_needing_expansion` 为空；说明候选空间覆盖问题已从“待扩展”变成“已有可审计扩展池”。
- `literature_template` 的 authority level 仍为 2：它只是候选来源，不是 Tg 标签来源。后续这些分子必须继续通过 predictor/Harness/PiEvo，真实实验或高保真 observation 才能提高证据权重。
- 同时修复了 inventory group index 对空 groups 的处理，避免 `nan` 被写成伪官能团污染 functional group summary。

## 第二十轮结论

- Predictor ensemble disagreement 已从“下一步建议”变成可运行审计：当前选用 6 个 VAE(512)-WVCM 强模型，包括 GPR、NuSVR、XGBoost、ExtraTrees 和 sklearn GradientBoosting。
- 在 `candidate_space_top_scored.csv` 的 10000 条候选中，按 ensemble mean 计算 195±5 C 近目标候选共有 1045 条。
- 近目标候选里，低分歧候选有 84 条，适合优先进入 PiEvo/人工审核；高分歧候选有 526 条，虽然 ensemble mean 接近目标，但应标记为 epistemic/OOD 风险，需要更多模型或高权重 observation 复核。
- 全候选平均 ensemble std 为 32.16 C，中位数为 30.92 C，最大为 83.51 C；best GPR 与 ensemble mean 的平均绝对偏差为 30.37 C。
- 这说明单一 GPR 仍可作为 PiEvo 的默认代理，但不能把它的点预测当成唯一排序标准。后续推荐应同时看 target distance、Harness、principle posterior 和 ensemble disagreement。
- 当前 disagreement 是模型间分歧，不是物理真实不确定性。真实 DSC/高保真 observation 进入后，才能判断哪些高分歧区域代表真实新规律，哪些只是 surrogate 外推噪声。

## 第二十一轮结论

- 固定候选表的 ensemble disagreement 不能直接代表 PiEvo 每轮实际生成候选。检查显示 `candidate_space_top_scored.csv` 与现有 PiEvo smoke 的 1560 条候选没有交集，因此本轮改为 live ensemble prediction。
- PiEvo-faithful 现在每轮对自己的候选批次运行 6 个 VAE(512)-WVCM top predictors，并把 `predictor_ensemble_std_tg_c`、bucket 和 `human_review_priority` 写入 diagnostics/selected/history。
- Ensemble disagreement guard 已接入 IDS selection pool：选择域变为 `target_distance_c <= 5 C` 且 `predictor_ensemble_std_tg_c <= 25 C`；若低分歧候选不足再回退，避免过度保守。
- 195 C、6 轮 smoke 中，两层 guard 每轮都实际启用；6 个 selected 全部在 target guard 和 ensemble guard 内，最佳 selected Tg 为 195.06 C，距离 0.059 C。
- 本轮 selected 的平均 ensemble std 为 16.40 C，0 条低分歧（std <= 10 C），0 条高分歧（std >= 25 C），说明当前推荐主要处于中等模型分歧区。
- 这个 guard 不改变 PiEvo posterior 公式，也不把 disagreement 当成真实观测。它只是把高 epistemic/OOD 风险候选推迟到更多模型或真实/高保真 observation 复核之后。

## 第二十二轮结论

- Expanded inventory 现在不再只是候选来源审计结果：`literature_template` 已进入 strict replacement 生成池，并通过 predictor/Harness/observation ledger 评估。
- Expanded replacement 生成 200 条 strict proposals，200 条全部可重建并评分，18 条通过 Harness；其中 `literature_template` 被评分 29 条，3 条通过 Harness。
- 最佳 `literature_template` 候选预测 Tg 为 194.48 C，距 195 C 目标 0.52 C；最佳 overall expanded replacement 距离为 0.200 C。
- Expanded feedback-aware LLM/RAG agent 使用 `--preferred-replacement-source literature_template` 后，2 条 records 都通过 Harness，其中 1 条明确使用 curated sparse functional-group template 作为上下文证据。
- Workflow summary 已新增 expanded inventory replacement/LLM-RAG 字段，证明 expanded source 已进入总览链路，而不是停留在单独报告。
- 这些结果仍是 VAE-WVCM-GPR surrogate 和 Harness 层面的证据，不是物理实验真值。`literature_template` 的价值在于扩展可检验搜索空间；是否成为高权重规律，还需要真实 DSC、高保真模拟或文献复现实验进入 observation ledger。

## 第二十三轮结论

- GNN 现在不只看节点原子特征和 bond edge features：`--global-features` 已把配方级比例、官能团、RDKit 结构摘要和 reaction compatibility 信息拼接到 graph pooling 后的 head。
- MPNN baseline/global 对比已在同一 85/15 split、同一 5 epoch 条件下运行：baseline MAPEK test 为 11.0512%，global-feature MAPEK test 为 11.6125%。
- global-feature case 的 MAE test 也略差，47.90 C vs 47.19 C；但 RMSE/R2 略好，61.44 C / 0.5922 vs 63.45 C / 0.5651。
- 因此本轮不能宣称 global features 提升了 GNN；它证明的是“知识/反应/global formulation 特征可以稳定进入 GNN 训练和 workflow summary”，而不是证明该模型已经优于 baseline。
- 当前最佳预测代理仍应是 VAE-WVCM model zoo；GNN global features 更适合作为后续结构视角、OOD/disagreement 或更长训练实验的候选输入。

## 第二十四轮结论

- SFT、扩散、流匹配现在不再只是文档里的 future 名词：已有脚本把通过 generation record/Harness 的候选转成 SFT JSONL 和 diffusion/flow seed table。
- 当前 8 条 generation ledger 输入中，7 条通过 Harness；去重后得到 5 条训练候选，其中 `llm_rag_principle_generation=4`、`functional_group_replacement=1`。
- SFT JSONL 为 4 条 train、1 条 eval；因为最小门槛是 20 条，`sft_ready=false`，还缺 15 条。
- diffusion/flow seed table 也是 4 条 train、1 条 eval；因为最小门槛是 100 条，`diffusion_flow_ready=false`，还缺 95 条。
- 这一步的价值是建立数据合同和红线：draft、缺 predictor、缺 chemistry evidence 或 Harness 失败的记录不会成为训练标签；样本不足时不训练生成模型，避免把 195 C smoke 的窄分布学成“规律”。

## 第二十五轮结论

- `vae_latent_local_search` 已从 registry 中的 planned future 变成可运行、可审计的 decoder-free inventory search。
- 新增 `trail/generation/vae_latent_local_search.py`：读取 expanded inventory 和当前 VAE(512) checkpoint，对高 reward 配方的单体做 latent-neighborhood replacement retrieval，并保留 `latent_distance/latent_cosine_similarity/latent_rank/tanimoto/matched_groups`。
- 新增 `tests/test_vae_latent_local_search.py`：验证 strict counterpart compatibility 会过滤“latent 很近但反应不兼容”的替换，兼容且 latent 最近的替换排第一。
- `scripts/evaluate_replacement_proposals.py` 已能透传 latent local search metadata 到 scored CSV、报告和 observation notes。
- 新增 `configs/pievo_faithful_vae_latent_local_search_195_smoke.yaml`，读取 latent local search 的 surrogate observation ledger 运行 PiEvo-faithful。
- 本轮真实 smoke：200 条 latent proposals，200 条可重建并评分，42 条通过 Harness，0 条重建拒绝；最佳 target distance 为 0.200 C。
- `literature_template` 在 latent local search 中产生 39 条 proposals，其中 7 条通过 Harness，比 expanded strict replacement 的 3 条 template 通过项更多。
- 42 条 Harness 通过项进入 PiEvo external observation ledger 后全部被接收，4 轮 selected 全部通过 target guard，最佳 selected distance 为 0.059 C，MAP principle 为 `reaction_839cd29ef5d7`。
- 这一步仍不声称 VAE decoder 已生成新分子；它证明的是当前 VAE latent 表示可作为局部搜索排序信号，并已经接入 predictor/Harness/PiEvo/workflow summary。

## 第二十六轮结论

- TODO 中“RL、人工闭环、搜索空间优化”现在有了一个可运行的 strategy-level contextual bandit policy，而不只是口头描述。
- 新增 `scripts/update_generation_strategy_policy.py`：读取 strict strategy feedback、expanded replacement eval、VAE latent local search eval、expanded LLM/RAG summary 和 SFT/diffusion readiness，输出下一轮 proposal 预算建议。
- 新增 `tests/test_generation_strategy_policy.py`：验证预算归一到 100、`llm_smiles_generation` 缺 predictor/chemistry evidence 时被 suppressed、SFT 和 diffusion/flow readiness 未通过时进入 data_collection_only。
- 当前 policy 纳入 6 个策略，其中 3 个 eligible active、1 个 suppressed、2 个 data_collection_only；top strategy 为 `llm_rag_principle_generation`。
- 当前 `allocation_per_100` 是 proposal 预算建议，不是推荐配方；所有候选仍必须写入 ledger，并经过 predictor、Harness、PiEvo 和人工审核。
- `sft_candidate_generator` 和 `diffusion_or_flow_matching` 在 readiness gate 未通过前不拿训练/生成预算，只获得“继续收集 validated generation records”的数据目标。
- Workflow summary、registry、closed-loop 文档和生成策略文档已接入 `artifacts/trail/generation_strategy_policy/generation_strategy_bandit_summary.json`。

## 第二十七轮结论

- TODO 中“人工闭环、真实实验结果迭代优化”现在不只停留在 observation/process schema；新增了真实可运行的候选复核队列。
- 新增 `scripts/build_human_experiment_review_queue.py`：读取 VAE latent local search、PiEvo selected、ensemble guard selected、expanded replacement 等通过 Harness/PiEvo 的 surrogate 候选，推断 reaction principle、process template、缺失工艺字段、复核优先级和建议动作。
- 新增 `tests/test_human_experiment_review_queue.py`：验证氰酸酯-胺反应映射到 `cyanate_ester_triazine_cure`，并验证 draft process records 不会自动变成 active ledger。
- 初版 review queue 输入 58 条候选，去重 43 条，输出 30 条人工复核候选；最佳 target distance 为 0.059 C。当前队列已在第三十七轮加入 250 C sparse target 候选并重建。
- 30 条 draft process records 基础格式全部通过，但 `ready_for_active_ledger_rows=0`，因为仍缺固化温度、后固化、催化剂、NCO 指数、酰亚胺化条件等工艺字段。
- 队列中 13 条是 `process_design_for_dsc`，11 条是 `high_fidelity_before_dsc`；这让人工闭环能先补工艺、做高保真复核，再决定是否排真实合成/DSC。
- Workflow summary、closed-loop 文档、真实实验文档和路线图已接入 `artifacts/trail/human_review/human_experiment_review_queue_summary.json`。

## 第二十八轮结论

- scored proposals 现在不再只停留在 replacement/latent eval 目录；它们已经通过 `scripts/import_proposal_eval_generation_records.py` 写回统一 generation record ledger。
- VAE latent local search 的 200 条 scored proposals 中，200 条 record 基础字段通过，42 条 Harness pass；expanded replacement 的 200 条 scored proposals 中，200 条 record 基础字段通过，18 条 Harness pass。
- SFT/diffusion/flow 训练语料因此从 8 条 ledger 输入扩展到 408 条输入；Harness pass 为 67 条，去重后训练候选为 64 条。
- SFT JSONL 现在是 52 条 train、12 条 eval，`sft_ready=true`；这意味着可以进入 SFT dry-run 或训练作业，但训练后的候选仍必须重新写入 ledger，并经过 predictor、Harness、PiEvo 和人工审核。
- diffusion/flow seed table 也是 52 条 train、12 条 eval，但 `diffusion_flow_ready=false`；100 条 seed 门槛还差 36 条，因此扩散/流匹配仍不应训练。
- Strategy bandit policy 已重算：eligible active strategies 从 3 增至 4，`sft_candidate_generator` 成为 active arm 并获得 25/100 proposal budget 建议；`diffusion_or_flow_matching` 仍是 data_collection_only。
- 这一步的本质是把“已被 predictor/Harness 评分的生成结果”纳入统一审计和训练数据链路，避免 SFT/flow 数据只依赖少量 prompt/RAG smoke records，也避免失败 proposals 绕过 Harness 成为训练标签。

## 第二十九轮结论

- SFT 现在不只是 `sft_ready=true`：已有一个可运行的 `sft_candidate_generator` dry-run 链路，能把 SFT JSONL 的 train split validated prototypes 转成新的 generation records。
- 本轮按上一轮 policy 的 SFT proposal budget 生成 25 条 dry-run records，25 条全部通过 importer/Harness；最佳 target distance 为 0.003 C，mean generation reward 为 0.7778。
- Heldout eval 有 12 条，其中 3 条与 dry-run prototypes 完全同候选；这个数字提醒我们当前 dry-run 是链路验证和 prototype replay，不是证明模型已经学会分布外生成。
- Strategy bandit 已改为优先使用 SFT dry-run generation summary：`sft_candidate_generator` 的 attempts/successes 变为 25/25，而不是仅引用 readiness 里的 64 条训练候选。
- 重算后 SFT 获得 21/100 下一轮 proposal budget 建议；`llm_rag_principle_generation` 仍为 top strategy，`diffusion_or_flow_matching` 仍因 seed rows 不足保持 data_collection_only。
- 当前仍不能声称“真实神经 SFT 权重已训练完成”。下一步若要完成更严格的 SFT，应把 prototype replay 替换为真实 LLM/SFT 训练或外部 provider 微调输出，并用同一 ledger/Harness/PiEvo 链路复评。

## 第三十轮结论

- 本轮把原始 replacement、feedback-guided replacement、多目标 replacement target sweep 和 rule-template baseline 全部写回统一 generation record ledger，训练语料不再只依赖 prompt/RAG、expanded replacement 和 VAE latent local search。
- 当前 12 个 generation ledgers 共 1165 条输入，177 条通过 Harness，去重后得到 143 条训练候选；这使 SFT 和 diffusion/flow seed-table readiness 同时通过。
- SFT JSONL 现在为 124 条 train、19 条 eval；diffusion/flow seed table 也是 124 条 train、19 条 eval。`next_data_needed_for_sft=0`，`next_data_needed_for_diffusion_flow=0`。
- 基于扩展语料重跑 SFT dry-run 后，25 条 `sft_candidate_generator` records 全部通过 Harness，mean generation reward 从 0.7778 升到 0.9922；heldout eval 增至 19 条，exact candidate match 为 0。
- Strategy bandit 现在有 5 个 eligible active、0 个 data_collection_only；`diffusion_or_flow_matching` 因 seed gate 通过获得 19/100 proposal budget 建议。
- 这不等于 diffusion/flow 模型已经训练完成，也不等于 SFT 已完成神经权重更新。它表示数据合同和 readiness gate 已经满足，下一步可以启动真实 SFT 或 diffusion/flow dry-run/训练，但所有生成输出仍必须重新进入 ledger，并经过 predictor、Harness、PiEvo 和人工审核。

## 第三十一轮结论

- Diffusion/flow 现在不只停在 `diffusion_flow_ready=true`：已有一个可运行的 `diffusion_or_flow_matching` dry-run 链路，能把 diffusion/flow seed table 的 train split validated prototypes 转成新的 generation records。
- 本轮按上一轮 diffusion/flow proposal budget 生成 19 条 dry-run records，19 条全部通过 importer/Harness；最佳 target distance 为 0.003 C，mean generation reward 为 0.9934。
- Heldout eval 有 19 条，其中 0 条与 dry-run prototypes 完全同候选；这个数字提醒我们当前 dry-run 是链路验证和 conditional seed replay，不是证明模型已经学会连续配方流形或分布外生成。
- Strategy bandit 已改为优先使用 diffusion/flow dry-run generation summary：`diffusion_or_flow_matching` 的 attempts/successes 变为 19/19，而不是仅引用 readiness 里的 143 条 seed rows。
- 重算后 diffusion/flow 获得 23/100 下一轮 proposal budget 建议，SFT 获得 22/100；`llm_rag_principle_generation` 仍为 top strategy。
- 当前仍不能声称“真实神经 diffusion/flow 权重已训练完成”。下一步若要完成更严格的扩散/流匹配，应把 seed replay 替换为真实条件生成模型训练输出，并用同一 ledger/Harness/PiEvo 链路复评。

## 第三十二轮结论

- Diffusion/flow 已从 seed replay dry-run 推进到真实训练步骤：`ConditionalFlowMatcher` 在 formulation global feature 空间学习从 Gaussian noise 到配方特征的 velocity，并以目标 Tg 作为条件。
- 本轮不是直接 SMILES diffusion。连续生成的 31 维特征必须投影回最近的 validated seed row，再写入 generation ledger 并重新通过 Harness。
- 120 epoch smoke 中，train loss 从 1.888 降到 1.313，说明训练链路有效；eval loss 为 1.802，说明泛化仍有限，后续不能夸大。
- 投影后 23 条 `diffusion_or_flow_matching` records 全部通过 Harness，最佳 target distance 为 0.005 C；但 mean generation reward 为 0.8340，低于 seed replay dry-run 的 0.9934，说明训练型 projection 当前没有超过“直接近邻 seed replay”。
- Strategy bandit 因此把 diffusion/flow 的下一轮预算从 dry-run evidence 的 23/100 调整为 trained projection evidence 的 18/100；这是合理的降权，而不是失败。
- 下一步若继续做 diffusion/flow，应优先改进 representation/decoder：要么提升 feature-space flow 的投影质量，要么引入有效 SMILES decoder，再用 predictor/Harness/PiEvo 复评，不能把连续特征样本直接当作配方推荐。

## 第三十三轮结论

- SFT 也已从 prototype replay dry-run 推进到真实训练步骤：`scripts/train_sft_record_projection_generator.py` 在 SFT generation record 的结构化特征空间训练轻量监督 MLP。
- 该模型输入 target/prompt/source 条件特征，输出 formulation global features、预测 Tg、reward 和来源策略特征；连续输出必须投影回最近的 validated train-split record 后，才写入 generation ledger。
- 120 epoch smoke 中，train loss 从 0.880 降到 0.618，eval loss 为 0.810；这说明训练链路有效，但仍是结构化投影，不是外部 LLM 微调或自由 SMILES 生成。
- 投影后得到 23 条 `sft_candidate_generator` records，23 条全部通过 Harness；最佳 target distance 为 0.003 C，mean generation reward 为 0.9565，projection distance mean 为 3.585。
- Heldout eval 有 19 条，其中 1 条和 projection 输出完全同候选；这个数字提示当前 projection 仍大量依赖 validated 训练原型，不能夸大为分布外生成能力。
- Strategy bandit 已改为优先读取 trained SFT projection summary：`sft_candidate_generator` 的 evidence source 从 dry-run 切换为 `sft_trained_projection_generation_record_summary`，下一轮预算保持 23/100；`diffusion_or_flow_matching` 仍为 18/100，top strategy 仍是 `llm_rag_principle_generation`。
- Workflow summary 已新增 trained SFT 字段，记录 rows、Harness pass、best distance、训练损失、projection distance 和 heldout eval。后续若做真正 LLM/SFT fine-tune 输出，也必须写入同一 generation ledger，并经过 predictor、Harness、PiEvo 和人工审核。

## 第三十四轮结论

- VAE latent local search 已从单一 195 C smoke 扩展到 190/195/200/250 C 多目标闭环：`scripts/run_vae_latent_local_search_target_sweep.py` 对同一批 latent-neighborhood proposals 分别重新计算 target window、observation ledger reward 和 PiEvo posterior。
- 四个目标共 800 条 target-wise evaluations，126 条通过 Harness 并进入 surrogate observation ledger；各目标通过数分别为 38、42、41、5。250 C 通过数明显偏少，说明同一批 latent proposals 对高温目标覆盖不足，后续应做目标条件化 source pool 或 latent retrieval。
- 四个目标 PiEvo selected 全部通过 target guard 和 validation；最佳 selected distance 分别为 0.002、0.059、0.043、0.511 C。MAP principle 分别为 `maleimide_rigid_network`、`reaction_839cd29ef5d7`、`sulfone_diamine_rigidity`、`reaction_a5dd26ae10ad`。
- 这些 target-wise latent scored proposals 已通过 `scripts/import_proposal_eval_generation_records.py` 写回 4 个 generation record ledgers，并加入 `scripts/build_generative_training_sets.py` 默认输入。
- 训练语料从 12 个 ledgers / 1165 rows / 177 Harness pass / 143 training candidates，扩展到 16 个 ledgers / 1965 rows / 303 Harness pass / 227 training candidates；SFT 和 diffusion/flow train/eval 变成 192/35。
- 基于扩展语料重跑后，SFT trained projection 的 eval loss 从 0.810 降到 0.725，mean generation reward 从 0.9565 升到 0.9798；flow trained projection 的 eval loss 从 1.802 降到 1.502，mean generation reward 从 0.8340 升到 0.8645。
- Strategy bandit 重算后仍以 `llm_rag_principle_generation` 为 top strategy；SFT trained projection 保持 23/100，diffusion/flow trained projection 从 18/100 升到 19/100。所有这些仍是 surrogate/Harness 证据，不是物理实验真值。

## 第三十五轮结论

- 新增 `scripts/update_target_conditioned_generation_policy.py`：把下一轮生成预算从单一全局 195 C bandit，扩展为 190/195/200/250 C 每个目标 Tg 单独分配。
- 新 policy 把 evidence 分成两类：replacement/VAE latent 使用 target sweep 的目标条件化证据；LLM/RAG、SFT projection、diffusion/flow projection 只作为 global-transfer exploration，并按 `exp(-abs(T-195)/80)` 衰减 transfer budget。
- 输出已生成：`artifacts/trail/generation_strategy_policy_target_conditioned/target_conditioned_generation_strategy_policy.csv`、`target_conditioned_generation_strategy_target_summary.csv`、`target_conditioned_generation_strategy_summary.json` 和 `reports/target_conditioned_generation_strategy_policy.md`。
- 当前每个目标 Tg 的 proposal budget 和都为 100。190/195/200 C 的 target-specific top strategy 为 `vae_latent_local_search`；250 C 切换为 `functional_group_replacement`。
- 250 C 的 transfer budget 从 25/100 收缩到 13/100，并被标为 sparse target；原因是目标条件化成功样本只有 9 条，且 VAE latent 在 250 C 的 best selected distance 为 0.511 C，replacement 为 0.099 C。
- `trail/workflow/multi_agent_workflow.py` 和 `artifacts/trail/workflow/multi_agent_summary.json` 已接入目标条件化 policy，记录每个目标的 top strategy、transfer budget 和 sparse target。
- `tests/test_target_conditioned_generation_policy.py` 和 `tests/test_workflow_summary.py` 已覆盖每目标预算归一、global-transfer 衰减、250 C strategy 切换和 workflow summary 字段。

## 第三十六轮结论

- 新增 `scripts/run_sparse_target_replacement_expansion.py`：读取 target-conditioned policy 的 `sparse_targets`，对 250 C 从 `all_ratio_candidates.csv` 重新选择 source pool，再运行 strict replacement、predictor/Harness、PiEvo 和 generation record import。
- 250 C sparse expansion 本轮选择 40 条 source candidates，生成 320 条 replacement proposals；318 条可重建并评分，42 条通过 Harness，best eval distance 为 0.034 C。
- 42 条 surrogate observations 进入 `artifacts/pievo_faithful_sparse_target_replacement_expansion/target_250/`，6 轮 PiEvo selected 全部通过 target guard；best selected distance 为 0.099 C，MAP principle 为 `reaction_cc7f1a60f1af`。
- 通过项已写入 `artifacts/trail/generation/sparse_target_replacement_records/target_250/generation_record_ledger.csv`；去重后为生成训练语料新增 41 条 250 C functional-group replacement examples。
- `scripts/build_generative_training_sets.py` 默认 ledger 已加入 sparse target record；训练语料从 227 条候选增至 268 条，SFT/diffusion-flow train/eval 为 226/42。
- 已重跑 SFT dry-run、SFT trained projection、diffusion/flow dry-run 和 conditional flow trained projection。SFT trained eval loss 为 0.750、mean generation reward 为 0.9800；flow trained eval loss 为 1.412、mean generation reward 为 0.8918。
- `scripts/update_target_conditioned_generation_policy.py` 现在会合并原 replacement target sweep 与 sparse expansion evidence；重算后 `sparse_targets=[]`，250 C 仍由 `functional_group_replacement` 作为 target-specific top strategy，allocation 为 51/100。
- `trail/workflow/multi_agent_workflow.py` 和 `artifacts/trail/workflow/multi_agent_summary.json` 已接入 sparse expansion summary，记录 250 C expansion 的 proposals、Harness pass、generation record pass、best distance 和 PiEvo guard 状态。
- 新增 `tests/test_sparse_target_replacement_expansion.py`，并扩展 `tests/test_target_conditioned_generation_policy.py`、`tests/test_workflow_summary.py`，覆盖 source-pool 选择、sparse evidence 合并和 workflow summary 字段。

## 第三十七轮结论

- 人工复核队列现在支持目标温度覆盖写法：`path::origin::target_tg_c`。这修复了一个关键风险：250 C sparse expansion 的 scored table 没有 `target_tg_c` 列时，不能默认落回 195 C。
- 默认输入已加入 `artifacts/trail/generation/sparse_target_replacement_expansion/target_250/replacement_eval/replacement_proposals_scored.csv::sparse_target_replacement_250::250`。
- 重建后的 review queue 输入 88 条候选、去重 73 条、输出 30 条人工复核候选；目标分布为 195 C 17 条、250 C 13 条。
- 250 C 的 13 条复核候选全部来自 `sparse_target_replacement_250`，最佳 target distance 为 0.034 C；这说明高 Tg 稀疏目标已经进入人工闭环，而不是只停留在生成/策略 policy 里。
- 30 条 draft process records 基础格式全部通过，但 `ready_for_active_ledger_rows=0`；这仍是正确门禁，因为所有候选都还缺人工确认的工艺字段和真实/高保真观测。
- `trail/workflow/multi_agent_workflow.py` 已记录 `human_review_target_counts` 和 `human_review_candidate_origin_counts`，workflow summary 可以看到人工复核队列中 195/250 C 和各候选来源的组成。
- 新增测试覆盖 250 C target override 和 workflow summary 字段，避免后续新目标候选被错误归入默认 195 C。

## 第三十八轮结论

- 新增 `scripts/build_pre_experiment_validation_plan.py`：把人工复核队列推进为实验前验证计划，读取 process templates、目标温度、prediction sigma、OOD、新组分和候选来源，输出验证通道与下一步动作。
- 生成产物包括 `artifacts/trail/human_review/pre_experiment_validation_plan.csv`、`pre_experiment_validation_plan_summary.json` 和 `reports/pre_experiment_validation_plan.md`。
- 当前 30 条 review items 全部进入 validation plan；其中 30 条都需要补工艺字段，25 条还需要高保真/扩展集成模型复核，0 条可在不补工艺的情况下直接进入 DSC。
- 目标分布仍为 195 C 17 条、250 C 13 条；250 C sparse target 候选在 plan 中全部被标记为高 Tg 稀疏目标，建议 `thermal_stability_pre_screen`、`target_specific_literature_check` 和高保真/集成模型复核。
- 这一步没有创建真实 DSC，也没有把任何 surrogate 候选升级为 high-authority observation；它只是把“人工闭环/真实实验前质量门”从队列推进成可执行的验证计划。
- `trail/workflow/multi_agent_workflow.py` 已接入 `human_validation_*` 字段，workflow summary 现在能看到 validation plan rows、process completion rows、high fidelity rows、lane counts 和 target/origin counts。
- 新增 `tests/test_pre_experiment_validation_plan.py`，并扩展 `tests/test_workflow_summary.py`，覆盖 250 C sparse/high-sigma 候选进入 `process_plus_high_fidelity` 通道以及 workflow summary 读取验证计划。

## 第三十九轮结论

- 新增 `scripts/build_validation_request_packet.py`：把 pre-experiment validation plan 转成可分派 request queue，明确哪些任务只是工艺补全，哪些完成后才可能作为高权重 observation。
- 生成产物包括 `artifacts/trail/human_review/validation_request_queue.csv`、`validation_request_summary.json` 和 `reports/validation_request_packet.md`。
- 当前 30 条 validation plan items 生成 55 个 request：30 个 `process_completion`、25 个 `high_fidelity_validation`、0 个 `real_dsc_planning`。
- 25 个 high-fidelity request 的 `eligible_observation_source_type=high_fidelity_simulation`、authority weight 为 3.0，但全部 `blocked_by_process_completion=true`；也就是说工艺字段补齐和人工批准之前，它们不能写入 observation ledger。
- 250 C sparse target 候选产生 26 个 request：13 个工艺补全、13 个高保真验证。当前没有任何 250 C 候选可以直接进入真实 DSC。
- `trail/workflow/multi_agent_workflow.py` 已接入 `validation_request_*` 字段，workflow summary 现在记录 request rows、process completion rows、high fidelity rows、real DSC rows、blocked rows 和 expected observation source counts。
- 新增 `tests/test_validation_request_packet.py`，并扩展 `tests/test_workflow_summary.py`，覆盖 high-fidelity/real-DSC authority gate 和 request summary 读取。

## 第四十轮结论

- 新增 `scripts/import_validation_request_results.py`：把 validation request 完成结果回收为 observation input，并在写入 observation ledger 前执行 request/source/process/reviewer 四重 gate。
- 生成产物包括 `validation_result_intake_template.csv`、`validation_result_review.csv`、`validation_result_observation_input.csv`、`validation_result_observation_ledger.csv`、`validation_result_observation_summary.json`、`validation_result_intake_summary.json` 和 `reports/validation_result_intake.md`。
- 当前 25 条 high-fidelity request 生成了 25 条 result intake template；由于尚无真实/高保真完成结果，`result_rows=0`、`accepted_result_rows=0`、`observation_ledger_pass_rows=0`。
- 准入规则是：request 必须 observation-capable，结果 `source_type` 必须匹配 request 的 `eligible_observation_source_type`，`observed_tg_c` 必须存在，`process_ready=true`，并且 `reviewer_approved=true`。
- 这一步没有新增真实 DSC 或高保真 evidence；它只是把未来结果如何安全进入 observation ledger 的回收门落成 artifact，防止未批准结果污染 PiEvo posterior。
- `trail/workflow/multi_agent_workflow.py` 已接入 `validation_result_*` 字段，workflow summary 可以看到 template rows、result rows、accepted rows、rejected rows 和 observation ledger pass rows。
- 新增 `tests/test_validation_result_intake.py`，并扩展 `tests/test_workflow_summary.py`，覆盖 high-fidelity result 被接受、process-completion request 不能直接产生 observation、未批准结果被拒绝，以及 workflow summary 读取 result intake。
