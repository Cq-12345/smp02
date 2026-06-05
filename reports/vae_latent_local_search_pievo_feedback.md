# VAE Latent Local Search -> PiEvo Feedback

本文档记录 `VAE latent local search -> predictor/Harness -> observation ledger -> PiEvo-faithful posterior` 的闭环 smoke。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM-GPR，不涉及暂缓的商品级组分或聚合物超图表示。

## 输入链路

- Latent proposals: `artifacts/trail/generation/vae_latent_local_search/latent_local_search_proposals.csv`
- Proposal summary: `artifacts/trail/generation/vae_latent_local_search/latent_local_search_summary.json`
- Evaluated proposals: `artifacts/trail/generation/vae_latent_local_search_eval/replacement_proposals_scored.csv`
- Observation ledger: `artifacts/trail/generation/vae_latent_local_search_eval/replacement_observation_ledger.csv`
- PiEvo config: `configs/pievo_faithful_vae_latent_local_search_195_smoke.yaml`
- PiEvo output: `artifacts/pievo_faithful_vae_latent_local_search_195_smoke`

## 生成与评估结果

| item | value |
| --- | ---: |
| latent proposals | 200 |
| rebuilt formulas | 200 |
| scored formulas | 200 |
| Harness pass | 42 |
| rejected proposals | 0 |
| best target distance (C) | 0.20046 |
| within 1 C | 10 |
| within 5 C | 42 |
| literature_template proposals | 39 |
| literature_template Harness pass | 7 |

本轮 local search 使用当前 VAE encoder 的 monomer latent 坐标做近邻检索，同时要求替换单体和未替换 co-monomer 保持可映射反应对。它不是 decoder 直接生成新 SMILES；它是在 expanded inventory 内做 VAE 表示空间的局部搜索。

## PiEvo 反馈结果

| item | value |
| --- | ---: |
| external observations accepted | 42 |
| external observations rejected | 0 |
| total posterior history rows | 46 |
| posterior entropy | 3.353029 |
| MAP principle | reaction_839cd29ef5d7 |
| selected rows | 4 |
| best selected distance (C) | 0.059032 |
| all selected within target guard | true |

PiEvo 接收 42 条外部 surrogate observations 后，4 轮 IDS 选择全部通过 195±5 C target guard。最佳新选择预测 Tg 为 195.06 C，距目标 0.059 C。

## 解释

- 这条链路补齐了 TODO 中“VAE：替换策略；生成策略”的 VAE latent 版本，而不仅是 Morgan/Tanimoto replacement。
- `latent_distance` 和 `tanimoto` 同时保留，后续可以比较 VAE 表示相近与传统指纹相似是否对应不同的可用配方区域。
- 42 条通过 Harness 的 surrogate observations 是 posterior evidence，但不是物理真值；真实 DSC、高保真模拟或文献复现实验进入 ledger 后应给更高 authority weight。
- 当前 MAP principle 转为 `reaction_839cd29ef5d7`，说明 latent local search 的外部 evidence 对 reaction principle posterior 有影响；这属于后验候选规律，不应直接当作不可推翻的化学真理。
