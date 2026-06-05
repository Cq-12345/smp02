# Sparse Target Replacement Expansion

本文档把 target-conditioned policy 标出的 sparse Tg 目标转成可执行搜索空间扩展。当前仍使用单一小分子 SMILES / MoleCode：先从 `all_ratio_candidates.csv` 中按目标 Tg 重新选择 source candidates，再做 strict functional-group replacement，随后进入 predictor、Harness、PiEvo 和 generation record ledger。

## Artifacts

- Expansion root: `artifacts/trail/generation/sparse_target_replacement_expansion`
- PiEvo output root: `artifacts/pievo_faithful_sparse_target_replacement_expansion`
- Generation record root: `artifacts/trail/generation/sparse_target_replacement_records`

## Summary

| target Tg (C) | source rows | proposals | harness pass | best eval dist (C) | external rows | best selected dist (C) | generation pass | MAP principle |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 250.0 | 40 | 320 | 42 | 0.034 | 42 | 0.099 | 42 | reaction_cc7f1a60f1af |

## Interpretation

- 这一步不是扩大到商品级组分或聚合物超图；它只是在现有两单体小分子配方表中，为 sparse target 重新选择更贴近目标 Tg 的 source pool。
- 与上一轮 target sweep 相比，关键差别是 source candidates 不再来自 195 C selected candidates，而来自全量 ratio candidate 表中目标 Tg 附近的候选。
- 通过项已写回 generation record ledger，可进入后续 SFT / diffusion-flow seed table；未通过项仍保留在 scored/eval 文件中用于失败回流。
- 这些结果仍是 VAE-WVCM-GPR surrogate + Harness + PiEvo posterior 证据，不是 DSC 真值。
