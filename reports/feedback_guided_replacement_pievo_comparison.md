# PiEvo Replacement Ledger Feedback Comparison

本文档比较原始 replacement observation ledger 与 feedback-guided strict replacement ledger 进入 PiEvo-faithful 后的差异。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM-GPR，不涉及暂缓的商品级组分或聚合物超图表示。

## Inputs

- Original PiEvo output: `artifacts/pievo_faithful_replacement_195_smoke`
- Feedback-guided PiEvo output: `artifacts/pievo_faithful_feedback_replacement_195_smoke`

## Summary

| metric | original replacement ledger | feedback-guided replacement ledger |
| --- | ---: | ---: |
| external rows | 10 | 11 |
| external mean reward | 0.7148 | 0.7185 |
| external best distance C | 0.3732 | 0.3732 |
| history rows | 14 | 15 |
| total authority weight | 14.0000 | 15.0000 |
| posterior entropy | 2.4869 | 1.4358 |
| MAP principle | long_aliphatic_penalty | long_aliphatic_penalty |
| MAP principle posterior | 0.4749 | 0.7454 |
| best selected distance C | 0.0055 | 0.0055 |
| selected rows | 4 | 4 |
| all selected pass | True | True |

## IDS Selection Overlap

| selected overlap | selected union | Jaccard | same selected set |
| ---: | ---: | ---: | --- |
| 4 | 4 | 1.000 | True |

## Posterior Delta

| principle | original posterior | feedback-guided posterior | delta |
| --- | ---: | ---: | ---: |
| long_aliphatic_penalty | 0.474851 | 0.745435 | +0.270584 |
| reaction_a5dd26ae10ad | 0.044640 | 0.021692 | -0.022948 |
| stereochemical_complexity_penalty | 0.028724 | 0.012725 | -0.015999 |
| druglike_hetero_complexity_penalty | 0.028892 | 0.014120 | -0.014772 |
| too_flexible_penalty | 0.025928 | 0.012691 | -0.013237 |
| reaction_536dfe22d324 | 0.025341 | 0.012447 | -0.012893 |
| cyanate_ester_triazine | 0.025340 | 0.012447 | -0.012893 |
| nitrile_rich_rigidity | 0.025340 | 0.012447 | -0.012893 |
| reaction_839cd29ef5d7 | 0.020334 | 0.011760 | -0.008574 |
| peptide_like_out_of_domain | 0.014697 | 0.007076 | -0.007620 |
| formal_charge_practical_penalty | 0.014697 | 0.007076 | -0.007620 |
| aromatic_backbones_raise_tg | 0.014697 | 0.007076 | -0.007620 |

## Interpretation

- Strict replacement ledger 接收 11 条外部 surrogate observation，原始 replacement ledger 接收 10 条。
- 在相同随机种子、目标 Tg、target guard 和 PiEvo 参数下，4 轮 IDS 选择集合没有变化；这说明当前短 smoke 中选择路径主要受候选池和 target-feasible IDS 控制。
- 但 feedback-guided ledger 让 posterior entropy 明显下降，并把 MAP principle 的后验推得更集中。这表示失败回流虽然没有马上改变所选配方，但已经改变了 principle posterior 的置信分布。
- 这里的后验收缩仍然来自 surrogate/Harness observation，不是物理真理。后续若加入真实 DSC 或高保真模拟，应该用更高 authority weight 重新比较 posterior delta。
