# Closed-loop Workflow

本仓库把 README / TODO 中的闭环要求实现为 in-silico workflow。当前仍使用单一小分子 SMILES / MoleCode，不做商品级复杂组分或聚合物超图表示。

1. 界定搜索空间：
   - 从扩充 XLSX 提取唯一单体。
   - 用 SMARTS 分类官能团。
   - 用兼容性矩阵过滤化学上合理的单体对。
2. 生成假设：
   - 对每个合理单体对枚举摩尔比。
   - 默认 5%-95%，步长 5%。
3. 预测/评估：
   - VAE 编码单体。
   - WVCM 生成配方向量。
   - model zoo / GNN / uncertainty / OOD 评估 Tg。
   - 按可变 `target_tg_c` 和 target distance 排序。
   - Harness 检查 RDKit、比例、目标窗口和反应兼容性。
4. 优化/改进假设：
   - PiEvo-faithful 使用 full-history posterior、MAP residual anomaly 和 IDS 选择。
   - Generation feedback analyzer 统计 Harness 失败原因和 generation strategy pass rate。
   - VAE replacement 生成器读取失败回流后，可用 `--require-counterpart-compatibility` 保留互补反应对。
   - feedback-guided replacement ledger 已进入 PiEvo posterior 对比；失败回流现在不只是报告建议，而会改变 posterior 置信分布。
   - Feedback-aware LLM/RAG agent 读取 strict strategy feedback，保留已修复的 replacement/RAG 策略，并抑制缺 predictor/chemistry evidence 的 SMILES 草案。
   - 人工审核优先查看高 reward、低 OOD、通过 Harness 的候选，以及失败原因集中的规则。

脚本入口：

```bash
PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli closed-loop --config configs/reproduce.yaml
```

输出：

- `closed_loop_selected.csv`
- `closed_loop_history.json`
- `evolved_principles.json`

PiEvo-faithful / generation feedback 相关入口：

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.cli \
  pievo-faithful \
  --config configs/pievo_faithful_replacement_195_smoke.yaml

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/analyze_generation_feedback.py \
  --generation-ledger artifacts/trail/generation/prompt_records/generation_record_ledger.csv \
  --replacement-rejections artifacts/trail/generation/replacement_eval/replacement_proposal_rejections.csv \
  --out-dir artifacts/trail/generation_feedback \
  --report reports/generation_failure_feedback.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.pievo_faithful \
  --config configs/pievo_faithful_feedback_replacement_195_smoke.yaml

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/compare_pievo_feedback_ledgers.py \
  --original-dir artifacts/pievo_faithful_replacement_195_smoke \
  --feedback-dir artifacts/pievo_faithful_feedback_replacement_195_smoke \
  --out-dir artifacts/trail/generation/feedback_guided_replacement_pievo_compare \
  --report reports/feedback_guided_replacement_pievo_comparison.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_feedback_replacement_target_sweep.py \
  --targets 190 195 200 250 \
  --rounds 6 \
  --candidate-batch-size 260

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/analyze_generation_feedback.py \
  --generation-ledger artifacts/trail/generation/prompt_records/generation_record_ledger.csv \
  --replacement-rejections artifacts/trail/generation/feedback_guided_replacement_eval/replacement_proposal_rejections.csv \
  --out-dir artifacts/trail/generation_feedback_strict \
  --report reports/generation_failure_feedback_strict.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_feedback_aware_llm_rag_agent.py \
  --provider offline_policy

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/import_generation_ledger_observations.py \
  --generation-ledger artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv \
  --out-dir artifacts/trail/generation/feedback_aware_llm_rag_observations \
  --report reports/feedback_aware_llm_rag_pievo_feedback.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.pievo_faithful \
  --config configs/pievo_faithful_feedback_aware_llm_rag_195_smoke.yaml

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/import_generation_ledger_observations.py \
  --generation-ledger artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv \
  --out-dir artifacts/trail/generation/feedback_aware_llm_rag_observations \
  --pievo-output-dir artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke \
  --report reports/feedback_aware_llm_rag_pievo_feedback.md

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python trail/workflow/multi_agent_workflow.py \
  --generation-feedback artifacts/trail/generation_feedback_strict/generation_feedback_summary.json \
  --generation-ledger artifacts/trail/generation/prompt_records/generation_record_ledger.csv \
  --feedback-aware-ledger artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv \
  --feedback-aware-observation-ledger artifacts/trail/generation/feedback_aware_llm_rag_observations/generation_observation_ledger.csv \
  --feedback-aware-pievo-summary artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke/pievo_faithful_summary.json \
  --out artifacts/trail/workflow/multi_agent_summary.json
```

新增 agent 角色：

- `harness_agent`：硬约束过滤，不被 posterior 学习弱化。
- `feedback_agent`：把 generation ledger 和 Harness rejection 转成下一轮生成器约束。
- `rag_generator_agent`：读取 RAG refs 和 strict strategy feedback，产出 generation records，而不是直接推荐。
- `human_review_agent`：补工艺条件、决定是否进入真实/高保真 observation ledger。

当前 replacement 反馈闭环的观测结果：

- 原始 replacement ledger：10 条外部 surrogate observations，posterior entropy 为 2.4869。
- Feedback-guided strict replacement ledger：11 条外部 surrogate observations，posterior entropy 为 1.4358。
- 两者 MAP principle 均为 `long_aliphatic_penalty`，但 strict ledger 把其 posterior 从 0.4749 推至 0.7454。
- 4 轮 smoke 的 IDS 选择集合相同，说明这个短程实验中 feedback 主要改变 posterior 置信分布；更长 rounds 和更多目标 Tg 才能验证它是否改变最终选择路径。

多目标 replacement 反馈闭环已经补充：

- 190/195/200/250 C 每个目标都重新计算 replacement Harness、external observation ledger、PiEvo reward 和 posterior。
- 6 轮 smoke 的最佳新选择分别距目标 0.057、0.006、0.204、0.099 C。
- MAP principle 随目标变化，说明目标 Tg 已经影响 full-history posterior，而不是只影响候选表排序。

LLM/RAG 反馈闭环已经补充：

- strict feedback 中 `functional_group_replacement` 和 `llm_rag_principle_generation` 均为保留策略，`llm_smiles_generation` 继续被抑制。
- feedback-aware LLM/RAG agent 生成 2 条 `llm_rag_principle_generation` records，2 条都通过 Harness。
- 这 2 条 records 已通过 `scripts/import_generation_ledger_observations.py` 转成 surrogate observation ledger，并进入 195 C PiEvo-faithful 6 轮 smoke。
- PiEvo 接收 2 条外部 observations、0 条拒绝；6 轮 selected 全部通过 target guard，最佳 selected distance 为 0.0055 C，MAP principle 为 `reaction_a5dd26ae10ad`。
- 当前运行使用 `offline_policy` provider 保持可复现；外部 LLM 只替换候选 JSON 生成步骤，不改变 ledger/Harness/PiEvo 审计链。

这个闭环目前主要使用 surrogate 和 smoke ledger 作为反馈源。若后续有真实合成/DSC 实验结果，应把实验 Tg 和工艺条件作为高权重 observation 加入 ledger，再更新 PiEvo posterior、重训 predictor 或修正 generation policy。
