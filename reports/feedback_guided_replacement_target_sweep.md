# Feedback-Guided Replacement Target Sweep

本文档把 feedback-guided strict replacement 从单一 195 C 扩展到多个目标 Tg。每个目标都会重新计算 replacement Harness/observation ledger，再把该 ledger 作为 PiEvo-faithful external history 运行。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM-GPR，不涉及暂缓的商品级组分或聚合物超图表示。

## Artifacts

- Replacement/evaluation root: `artifacts/trail/generation/feedback_guided_replacement_target_sweep`
- PiEvo output root: `artifacts/pievo_faithful_feedback_replacement_target_sweep`

## Summary

| target Tg (C) | replacement pass | replacement best dist (C) | external rows | PiEvo rounds | best selected Tg (C) | best selected dist (C) | posterior entropy | MAP principle | MAP posterior | pass |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 190.0 | 13 | 0.994 | 13 | 6 | 190.06 | 0.057 | 3.284 | reaction_a5dd26ae10ad | 0.093 | True |
| 195.0 | 11 | 0.373 | 11 | 6 | 194.99 | 0.006 | 1.305 | long_aliphatic_penalty | 0.770 | True |
| 200.0 | 11 | 0.445 | 11 | 6 | 199.80 | 0.204 | 2.878 | too_flexible_penalty | 0.257 | True |
| 250.0 | 4 | 0.489 | 4 | 6 | 249.90 | 0.099 | 3.552 | heavy_halogen_practical_risk | 0.037 | True |

## Interpretation

- 这一步检验“真实 Tg 不固定”：replacement 不是只为 195 C 服务，而是对每个目标重新计算 target window、reward 和 PiEvo posterior。
- strict replacement 的互补反应对约束保留在所有目标中；差异来自目标窗口和后续 PiEvo full-history posterior。
- 若某个目标的 replacement pass 很少或为 0，PiEvo 仍可运行，但 posterior 主要来自本轮 surrogate 选择而不是 external replacement history。
- 当前仍是 smoke 规模。若要判断 posterior 收缩是否真正改变 IDS 推荐路径，应继续提高 `rounds`、`candidate_batch_size`，并加入真实 DSC 或高保真 observation。
