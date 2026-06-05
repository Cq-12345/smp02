# SMP 的 PiEvo-faithful 闭环设计

本文档说明 `pievo_faithful` 模式如何把 PiEvo 的数学结构迁移到当前 SMP 配方发现任务中。这里仍然使用单一小分子 SMILES / MoleCode / VAE-WVCM 表示；真实商品级组分、聚合物超图表示暂时不进入本阶段。

## 1. 任务定义：真实 Tg 目标不固定

历史的 agent 配置以 `target_tg_c = 250.0` 为例，但系统不能写死 250 C。PiEvo-faithful 模式把目标温度作为任务参数：

```text
T_target = config.agent_discovery.target_tg_c
```

环境反馈不直接使用 `Tg_hat`，而使用“接近目标”的 reward。对 surrogate 观测，`T_observed = Tg_hat`；对真实 DSC、文献或高保真模拟，`T_observed` 使用 ledger 中记录的观测 Tg：

```text
y(h) = exp(-abs(T_observed(h) - T_target) / tau)
```

其中 `tau = pievo_faithful.reward_temperature_c`。这样无论目标是 190 C、200 C、250 C 还是其他温度，闭环都在优化“接近目标”而不是盲目追求更高 Tg。

## 2. PiEvo 数学对应

### 2.1 Hypothesis

SMP 配方假设为：

```text
h = (n, m_1..m_n, r_1..r_n)
```

其中 `m_i` 是小分子 SMILES，`r_i` 是摩尔比例，满足硬约束：

```text
valid_rdkit(m_i)
and encodable_by_vae_charset(m_i)
and sum_i r_i = 1
and min_ratio <= r_i
and reactive_network_ok(h)
```

### 2.2 Principle

Principle 不再只是排序 bonus，而是有后验概率的解释假说：

```text
P_j = (name_j, feature_j, effect_j, prior_mass_j)
```

例子：

- 芳香/多芳香刚性骨架提高 Tg。
- 酰亚胺、酸酐、氰酸酯、马来酰亚胺网络更容易形成高 Tg。
- 长脂肪链、PEG-like 片段、过多可旋转键降低 Tg。
- 特定官能团反应兼容关系可以形成合理热固性网络。

### 2.3 Principle-conditioned GP Expert

每个 principle 都有一个独立 GP expert：

```text
M_P: phi(h, P) -> y
```

当前实现中的 `phi(h, P)` 是确定性特征向量，包含：

- 配方是否触发该 principle 的结构/反应特征；
- principle effect 与触发状态的乘积；
- 当前配方 prior score；
- OOD penalty；
- surrogate sigma；
- 组分数量；
- out-of-library 组分数量；
- 目标距离归一化；
- target reward。

这不是论文中语义 embedding 的逐字复制，但保留了 PiEvo 的关键结构：likelihood 必须由 `h` 和 `P` 的联合特征决定，而不是由一个全局模型直接决定。

### 2.4 Full-history Posterior

每轮用完整历史重新计算 principle 后验。若 observation ledger 提供了不同来源权重，真实 DSC、文献、高保真模拟和 surrogate 观测会以不同 authority weight 进入同一个后验：

```text
log p_t(P) = log p0(P) + sum_s w_s log p(y_s | h_s, P)
```

实现位置：

- `src/smp02/pievo_faithful.py::update_posterior_full_history`
- `src/smp02/pievo_faithful.py::sequential_predictive_log_likelihood`
- `src/smp02/pievo_faithful.py::load_external_observations`
- `src/smp02/pievo_faithful.py::gaussian_likelihood`
- `src/smp02/pievo_faithful.py::normalize_log_weights`

这一步是“抛弃没用规律”的数学基础：不能解释历史观测的 principle 会得到低 likelihood，后验自然下降。

工程上采用 sequential predictive likelihood：第 `s` 个历史观测只用 `1..s-1` 的历史训练对应 GP，再计算 `p(y_s | h_s, P)`。这样仍然使用完整历史证据，但避免 GP 在同一个训练点上自我解释导致所有 principle likelihood 接近相同。

当前权重默认值：

```text
surrogate: 1
literature: 2
high_fidelity_simulation: 3
real_dsc: 5
```

这些权重不是物理真理，只是 posterior 更新时的证据强度。真实实验记录必须先经过人工/脚本审核，标记为 `ledger_pass` 后再进入 active history。

### 2.5 MAP Residual Anomaly

异常不再定义为“低先验但接近目标”，而是 MAP principle 对历史观测解释失败：

```text
P_MAP = argmax_P p_t(P)

S_s = 1 - exp(-sqrt((y_s - mu_MAP(h_s))^2 / (sigma_MAP^2(h_s) + sigma_obs^2)))
```

若 `S_s > theta`，该历史观测进入 anomaly set。实现位置：

- `src/smp02/pievo_faithful.py::surprisal_score`
- `src/smp02/pievo_faithful.py::detect_map_residual_anomalies`

### 2.6 Coherent Augmentation

当 anomaly 数量超过阈值时，系统尝试加入新的 candidate principle。当前版本先用确定性规则从 anomaly 共享特征中提出新 principle：

```text
P_new = common_feature(U_t)
P_t+1 = P_t union {P_new}
```

加入后必须重新训练所有 GP experts，并用 full history 重新计算所有后验。这一点避免了“新规律只解释局部异常，但破坏整体历史一致性”的问题。

### 2.7 IDS Selection

候选选择不再按 `agent_score` 排序，而使用 PiEvo 的 information-directed selection：

```text
h_t = argmin_h Delta_t(h)^2 / (I_t(h) + eps)
```

其中：

```text
Delta_t(h) = E_p[V*(P)] - E_p[r(h, P)]
I_t(h) = H[p_t(P)] - E_y[H[p_t(P | h, y)]]
```

当前实现用 Monte Carlo/BALD 估计 `I_t(h)`。实现位置：

- `src/smp02/pievo_faithful.py::information_gain`
- `src/smp02/pievo_faithful.py::select_by_ids`

### 2.8 Target-Feasible IDS

多目标 smoke 暴露过一个问题：候选池中存在很接近目标 Tg 的配方，但短程 warmup/IDS 可能因为探索方差而选择远离目标的样本。为避免闭环浪费实验轮次，当前实现加入 target guard：

```text
H_feasible = {h in H : |T_observed_or_predicted(h) - T_target| <= delta}
h_t = argmin_{h in H_feasible} Delta_t(h)^2 / (I_t(h) + eps)
```

若 `H_feasible` 为空或候选数低于阈值，系统回退到全集 `H`，避免在低资源目标上完全停滞。这样仍然保留 PiEvo 的 IDS 数学结构，只是把可实验/可推荐的假设空间收缩到目标可行域。

配置：

```yaml
pievo_faithful:
  target_guard_enabled: true
  target_guard_max_distance_c: 5.0
  target_guard_min_candidates: 1
```

实现位置：

- `src/smp02/pievo_faithful.py::target_guard_selection_pool`
- `src/smp02/pievo_faithful.py::select_by_ids`

### 2.9 Ensemble-Guard IDS

上一轮 predictor ensemble disagreement 审计只覆盖了一个固定 discovery candidate CSV。为了让该信号真正进入 PiEvo，每轮 PiEvo 现在会对自己实际生成的候选批次运行同一组 top-k VAE-WVCM model-zoo predictors，并计算：

```text
mu_ens(h) = mean_m f_m(h)
sigma_ens(h) = std_m f_m(h)
```

其中 `f_m` 是 GPR、NuSVR、XGBoost、ExtraTrees、GradientBoosting 等已训练 surrogate。`sigma_ens(h)` 是模型间分歧，不是物理真实不确定性。它不进入 principle likelihood，也不会被当成真实 observation；它只用于收缩选择域和标记人工审核优先级：

```text
H_target = {h in H : |T_primary(h) - T_target| <= delta}
H_risk = {h in H_target : sigma_ens(h) <= tau_ens}
h_t = argmin_{h in H_risk} Delta_t(h)^2 / (I_t(h) + eps)
```

如果 `H_risk` 数量不足，系统回退到 `H_target`，避免因为 ensemble 过保守而完全停止探索。这样保留 PiEvo 的 IDS 数学结构：posterior 仍由 full-history likelihood 更新，ensemble disagreement 只是候选选择/人工复核层面的 epistemic risk gate。

配置：

```yaml
pievo_faithful:
  ensemble_disagreement_enabled: true
  ensemble_metrics_path: artifacts/reproduce/predictors/all_predictor_metrics.csv
  ensemble_top_k: 6
  ensemble_consensus_std_c: 10.0
  ensemble_high_disagreement_std_c: 25.0
  ensemble_disagreement_guard_enabled: true
  ensemble_disagreement_guard_max_std_c: 25.0
  ensemble_disagreement_guard_min_candidates: 1
```

实现位置：

- `src/smp02/pievo_faithful.py::load_predictor_ensemble`
- `src/smp02/pievo_faithful.py::attach_live_ensemble_disagreement`
- `src/smp02/pievo_faithful.py::target_guard_selection_pool`
- `src/smp02/pievo_faithful.py::select_by_ids`

## 3. 当前输出

运行：

```bash
smp02 pievo-faithful --config configs/pievo_faithful_smoke.yaml
```

会输出：

- `selected_formulations.csv`：每轮被 PiEvo-faithful 选中并观测的配方。
- `observation_history.csv`：进入 full-history posterior 的全部观测，包括外部 ledger 和本轮 surrogate 选择。
- `external_observations_used.csv`：本轮实际接收的外部 ledger 观测。
- `external_observation_summary.json`：外部观测接收、拒绝、来源计数和权重汇总。
- `candidate_diagnostics.csv`：候选的 expected reward、IDS regret、information gain、IDS ratio。
- `predictor_ensemble_members.csv`：当启用 live ensemble disagreement 时，本轮使用的 top-k predictor 成员。
- `principle_posterior.json`：最终 principle 后验。
- `principles.json`：初始和 anomaly-derived principles。
- `round_history.json`：每轮 anomaly、posterior entropy、MAP principle、选择方式。
- `pievo_faithful_report.md`：中文/英文混合报告。

如果要验证真实/人工 ledger 接入，可以运行：

```bash
smp02 pievo-faithful --config configs/pievo_faithful_ledger_smoke.yaml
```

该 smoke 会读取 `artifacts/trail/experiments/observation_ledger.csv`，并把通过审核的外部观测作为 round 0 history。注意：当前示例 ledger 中的 `real_dsc` 行是 schema 占位行，不代表真实 DSC 已经完成。

## 4. 如何理解“发现新规律、抛弃没用规律”

PiEvo-faithful 可以做的是“后验意义上的候选规律发现”：

- 如果某个 principle 对历史观测的 likelihood 低，它的 posterior 会下降。
- 如果 anomaly-derived principle 能更好解释历史，它会获得更高 posterior。
- 低 posterior principle 应先进入 dormant/pruned 状态，而不应立刻永久删除。
- 如果所有观测都来自 VAE-WVCM surrogate，那么发现的是 surrogate-consistent 规律，不是物理真理。

要把候选规律升级为可靠物理规律，需要引入真实合成/DSC 或高保真计算，并把真实观测作为更高权重的数据源。

## 5. 与旧 agent_discovery 的关系

旧 `agent_discovery` 适合大规模候选筛选，目标是快速找到满足硬约束、接近目标 Tg、OOD 可控的 out-of-library 配方。

新 `pievo_faithful` 适合研究闭环，目标是维护 principle 后验、解释 anomaly、用 IDS 选择最有信息量的实验。

两者不互相替代：

- `agent_discovery` 可以给 PiEvo-faithful 提供较好的候选池。
- `pievo_faithful` 可以给 agent_discovery 反哺 principle posterior 和需要扩展的搜索区域。
