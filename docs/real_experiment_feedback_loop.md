# 真实实验与人工闭环接入方案

本文档回应 TODO 中“RL，人工闭环，真实实验结果迭代优化”的部分。当前仍然只处理小分子 SMILES / MoleCode 配方，不处理商品级组分和聚合物超图。

## 1. 为什么需要 observation ledger

当前 PiEvo-faithful 的 observation 主要来自 VAE-WVCM surrogate，因此发现的是 surrogate-consistent candidate principles。要把候选规律升级为更可靠的物理规律，必须接入更高权重的观测：

- 真实 DSC / DMA。
- 高保真模拟。
- 文献复现实验。
- 人工审核后的实验记录。

这些观测应进入统一 observation ledger，而不是散落在 notebook 或聊天记录里。

## 2. Schema

Schema 文件：

- `trail/experiments/observation_schema.yaml`
- `trail/experiments/process_record_schema.yaml`

核心字段：

- `observation_id`
- `source_type`: `surrogate`、`real_dsc`、`high_fidelity_simulation`、`literature`
- `target_tg_c`
- `observed_tg_c`
- `smiles`
- `ratios`

权重：

```text
surrogate: 1
literature: 2
high_fidelity_simulation: 3
real_dsc: 5
```

这个权重不是最终科学结论，只是告诉 PiEvo posterior：真实实验比 surrogate 更有解释权。

Process record 不直接改变 authority weight。它判断一个 Tg observation 是否有足够工艺细节可以被复现或升级为 active high-authority ledger。

## 3. Reward

目标 Tg 不固定，因此每条 observation 单独保存 `target_tg_c`：

```text
reward = exp(-abs(observed_tg_c - target_tg_c) / tau)
weighted_reward = reward * authority_weight
```

## 4. 导入脚本

```bash
PYTHONPATH=src python trail/experiments/import_observations.py \
  --input trail/experiments/example_observations.csv \
  --out artifacts/trail/experiments/observation_ledger.csv \
  --summary artifacts/trail/experiments/observation_ledger_summary.json
```

输出：

- `observation_ledger.csv`
- `observation_ledger_summary.json`

工艺/人工审核记录：

```bash
PYTHONPATH=src python trail/experiments/import_process_records.py \
  --input trail/experiments/example_process_records.csv \
  --out artifacts/trail/experiments/process_record_ledger.csv \
  --summary artifacts/trail/experiments/process_record_summary.json
```

输出：

- `process_record_ledger.csv`
- `process_record_summary.json`

候选复核队列：

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_human_experiment_review_queue.py \
  --out-dir artifacts/trail/human_review \
  --report reports/human_experiment_review_queue.md
```

输出：

- `human_experiment_review_queue.csv`
- `draft_process_records.csv`
- `draft_process_record_ledger.csv`
- `human_experiment_review_queue_summary.json`

高权重 active evidence ledger：

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/build_active_observation_ledger.py \
  --out-dir artifacts/trail/human_review \
  --report reports/active_high_authority_observation_ledger.md
```

输出：

- `active_high_authority_observation_ledger.csv`
- `active_high_authority_observation_summary.json`
- `reports/active_high_authority_observation_ledger.md`

Active evidence 到 PiEvo posterior 的 bridge：

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_active_evidence_pievo_bridge.py \
  --config configs/pievo_faithful_active_evidence_bridge_smoke.yaml \
  --out-dir artifacts/pievo_faithful_active_evidence_bridge_smoke \
  --report reports/active_evidence_pievo_bridge.md
```

输出：

- `active_evidence_pievo_external_observations_used.csv`
- `active_evidence_principle_posterior.json`
- `active_evidence_pievo_bridge_summary.json`
- `reports/active_evidence_pievo_bridge.md`

## 5. 与 PiEvo 的连接

当前 `pievo_faithful` 已经可以把 ledger 中通过审核的 observation 加入 history：

```text
H_t = H_surrogate + H_real + H_literature
```

并在 likelihood 中考虑权重：

```text
log p_t(P) = log p0(P) + sum_s w_s * log p(y_s | h_s, P)
```

这样真实实验可以更快压低无法解释真实 Tg 的 principle，也可以提升能解释真实 anomaly 的 principle。

对应配置：

```yaml
pievo_faithful:
  external_observation_ledger: artifacts/trail/experiments/observation_ledger.csv
  external_observation_require_pass: true
  external_observation_limit: 2
```

输出文件：

- `observation_history.csv`：全部 posterior history。
- `external_observations_used.csv`：本轮接收的外部观测。
- `external_observation_summary.json`：接收/拒绝行数、来源计数和外部总权重。
- `selected_formulations.csv`：只保存本轮 PiEvo 新选择的 surrogate 配方，不混入外部历史观测。

Smoke 结果：

- 配置：`configs/pievo_faithful_ledger_smoke.yaml`
- 外部 ledger：2 行接收、0 行拒绝。
- 外部权重：surrogate 1 + real_dsc 5 = 6。
- posterior history：2 条外部观测 + 4 条本轮 surrogate 观测 = 6。
- 最佳本轮新选择：预测 Tg 249.63 C，距 250 C 目标 0.37 C。

注意：示例 ledger 中的 `real_dsc` 行仍是占位演示数据，不应当作为真实物理实验结论引用。

## 6. 人工闭环

建议人工审核字段：

- 是否真实合成成功。
- DSC 曲线是否可靠。
- 是否有多峰 Tg 或相分离。
- 固化程序是否完整。
- 样品是否降解。
- 是否应进入 active ledger。

当前 process record smoke：

- 3 条记录全部通过基础格式检查。
- 0 条 `ready_for_active_ledger`。
- Paper Table 6 A/B 缺少 `solvent;imidization_temperature_c;imidization_time_h`。
- Replacement surrogate 107 缺少 `trimerization_temperature_c;catalyst_loading;post_cure_temperature_c`。

这意味着：即使已有文献 Tg 或 surrogate Tg，也不能绕过工艺完整性审核直接作为高权重真实证据进入 PiEvo posterior。

人工审核不是替代模型，而是控制数据质量，避免错误实验记录污染 posterior。

当前 human experiment review queue：

- 输入 88 条 surrogate/Harness/PiEvo 候选，去重后 73 条，输出 30 条人工复核候选。
- 队列目标分布为 195 C 17 条、250 C 13 条；250 C 的候选全部来自 `sparse_target_replacement_250`，不会被混入 195 C 目标。
- 队列最佳 target distance 为 0.034 C，来自 250 C sparse target replacement expansion。
- 20 条为 `process_design_for_dsc`，适合先补工艺字段再决定是否排真实实验。
- 10 条为 `high_fidelity_before_dsc`，通常是预测 sigma 较高或 surrogate 风险较高，建议先做高保真/集成复核。
- 30 条 draft process records 基础格式全部通过，但 `ready_for_active_ledger_rows=0`；这正是预期门禁，防止 surrogate 候选未经人工和工艺细节直接升级为高权重证据。

当前 pre-experiment validation plan：

- `scripts/build_pre_experiment_validation_plan.py` 会读取人工复核队列、知识库 process templates 和候选风险信号，输出 `pre_experiment_validation_plan.csv` 与 `reports/pre_experiment_validation_plan.md`。
- 当前 30 条候选全部 `process_completion_required=true`，说明都必须补齐工艺字段后才能考虑真实 DSC。
- 25 条 `high_fidelity_required=true`，主要来自高 Tg 稀疏目标、较高 predictor sigma、OOD 或新组分风险，应先做高保真/扩展模型集成复核。
- 0 条 `dsc_ready_without_process_completion`，因此当前没有任何 surrogate 候选可以绕过人工工艺补全直接进入真实实验或 active ledger。

当前 validation request packet：

- `scripts/build_validation_request_packet.py` 把 validation plan 转成 `validation_request_queue.csv` 和 `reports/validation_request_packet.md`。
- 当前共有 55 个 request：30 个 `process_completion` 只用于补齐工艺记录，25 个 `high_fidelity_validation` 完成后才可能以 `source_type=high_fidelity_simulation` 写入 observation ledger。
- 25 个 high-fidelity request 全部 `blocked_by_process_completion=true`，说明高保真复核也必须等工艺字段补齐和人工批准后才能成为高权重证据。
- 当前 `real_dsc_request_rows=0`；这不是没有候选，而是说明还没有候选通过工艺完整性和人工质量门，不能直接排真实 DSC。

当前 validation result intake：

- `scripts/import_validation_request_results.py` 会把 request 完成结果回收为 observation input；准入条件是 request 可产生 observation、`source_type` 匹配、`observed_tg_c` 非空、`process_ready=true` 且 `reviewer_approved=true`。
- 当前生成 25 条 high-fidelity result intake template，等待真实高保真结果填写。
- 当前没有完成结果，因此 `accepted_result_rows=0`、`observation_ledger_pass_rows=0`；PiEvo posterior 仍没有新增高权重真实/高保真 evidence。
- 这一步保证即使有人填写了高保真或 DSC 数值，也不能绕过工艺完整性和人工批准直接污染 observation ledger。

当前 active high-authority observation ledger：

- `scripts/build_active_observation_ledger.py` 只读取已经通过上一层 observation ledger 的结果，不读取 request template 或原始 result 草稿。
- 默认只允许 `high_fidelity_simulation`、`real_dsc`、`literature` 三类来源成为 active evidence；`surrogate` 即使通过 Harness，也不能进入这一层。
- 当前输入 ledger 为 `validation_result_observation_ledger.csv`，其中 0 条完成观测；因此 `active_rows=0`、`authority_weight_sum=0.0`。
- 这层 ledger 才是后续 PiEvo posterior、strategy update 或真实实验总结应读取的高权重 evidence source。当前为空表示质量门没有被绕过，而不是说明候选生成链路失败。

当前 active evidence -> PiEvo bridge：

- `scripts/run_active_evidence_pievo_bridge.py` 使用 PiEvo 自身的 `load_external_observations` 和 `update_posterior_full_history`，验证 active ledger 是否会改变 principle posterior。
- `configs/pievo_faithful_active_evidence_bridge_smoke.yaml` 显式要求 `external_observation_allowed_source_types=[high_fidelity_simulation, real_dsc, literature]` 且 `external_observation_require_active_evidence=true`。
- 当前 `external_accepted_rows=0`、`posterior_history_rows=0`、`active_evidence_updates_posterior=false`、`bridge_status=no_active_evidence_noop`。
- 这意味着当前 PiEvo posterior 没有新增高权重 evidence；未来一旦高保真/真实/文献结果通过 gate，同一脚本会记录 accepted rows、authority weight、MAP principle 和 posterior entropy。
