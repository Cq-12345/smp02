# Feedback-Guided Replacement Comparison

本文档比较原始 VAE replacement 生成器和第十二轮失败回流后的 strict replacement 生成器。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM-GPR，不涉及商品级组分或聚合物超图表示。

## Feedback Constraint

第十二轮失败回流显示，`functional_group_replacement` 的主要失败原因是 `replacement_formula_failed_reaction_or_ratio_constraints`。这说明只按“原单体和替代单体共享官能团 + Tanimoto 相似”筛选不够，因为替代后还必须和未替换的另一侧单体形成可映射反应对。

本轮新增 strict 约束：

```text
old: replacement_groups intersect original_groups is non-empty
new: old constraint + compatibility_reason(counterpart_groups, replacement_groups) is non-empty
```

生成器会把以下审计字段写入 proposal 和 scored CSV：

- `counterpart_groups`
- `counterpart_compatibility_reason`
- `feedback_constraint`

## Artifacts

- `artifacts/trail/generation/feedback_guided_replacement_proposals.csv`
- `artifacts/trail/generation/feedback_guided_replacement_eval/replacement_proposals_scored.csv`
- `artifacts/trail/generation/feedback_guided_replacement_eval/replacement_proposals_harness.csv`
- `artifacts/trail/generation/feedback_guided_replacement_eval/replacement_proposal_rejections.csv`
- `artifacts/trail/generation/feedback_guided_replacement_eval/replacement_observation_ledger.csv`
- `reports/feedback_guided_replacement_evaluation.md`

## Comparison

| metric | original replacement | feedback-guided replacement |
| --- | ---: | ---: |
| input proposals | 120 | 120 |
| rebuilt formulas | 107 | 120 |
| scored formulas | 107 | 120 |
| rejected proposals | 13 | 0 |
| harness pass | 10 | 11 |
| within 1 C | 4 | 4 |
| within 5 C | 10 | 11 |
| best distance to 195 C | 0.373243 C | 0.373243 C |
| replacement observations | 10 | 11 |

## Top Passing Examples

| rank | predicted Tg (C) | distance (C) | side | replacement tanimoto | counterpart compatibility |
| ---: | ---: | ---: | --- | ---: | --- |
| 1 | 194.63 | 0.37 | b | 0.471 | 氰酸酯-胺共反应。 |
| 2 | 194.55 | 0.45 | a | 0.560 | 氰酸酯-胺共反应。 |
| 3 | 195.57 | 0.57 | b | 0.375 | 环氧-伯胺开环固化。 |
| 4 | 194.08 | 0.92 | b | 0.375 | 异氰酸酯-伯胺形成聚脲。 |

## Interpretation

- 失败回流已经真正改变了下一轮 replacement 生成器，而不是只停留在报告建议中。
- Strict 约束把重建阶段的反应/比例失败从 13 条降到 0 条，同时没有牺牲最佳近目标候选。
- Harness 通过数从 10 增至 11，说明“先保留互补反应对，再做 Tanimoto 局部替换”比单纯共享官能团更适合当前双组分配方生成。
- 这仍然是 surrogate-consistent 结论，不是物理真理。真实 DSC 或高保真实验进入 observation ledger 后，才可以把这些 replacement observation 升级为更高权重证据。

## Command

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python trail/generation/vae_replacement_strategy.py \
  --top-k 20 \
  --per-side 3 \
  --require-counterpart-compatibility \
  --out artifacts/trail/generation/feedback_guided_replacement_proposals.csv

PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/evaluate_replacement_proposals.py \
  --target-tg-c 195 \
  --target-window-c 5 \
  --proposals artifacts/trail/generation/feedback_guided_replacement_proposals.csv \
  --out-dir artifacts/trail/generation/feedback_guided_replacement_eval \
  --report reports/feedback_guided_replacement_evaluation.md
```
