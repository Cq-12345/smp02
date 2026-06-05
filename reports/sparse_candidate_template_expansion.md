# Sparse Functional Group Candidate Expansion

本文档回应 TODO 中“候选组分数据集：来源、按官能团分类、数据库”的补强要求。本轮仍只使用单一小分子 SMILES / MoleCode，不进入商品级组分、聚合物或超图表示。

## Outputs

- Template library: `trail/candidates/sparse_functional_group_templates.yaml`
- Expanded inventory: `artifacts/trail/candidates_expanded/component_inventory.csv`
- Added templates: `artifacts/trail/candidates_expanded/template_expansion_added.csv`
- Rejected templates: `artifacts/trail/candidates_expanded/template_expansion_rejected.csv`
- Summary: `artifacts/trail/candidates_expanded/template_expansion_summary.json`

## Summary

| item | value |
| --- | ---: |
| base inventory rows | 694 |
| expanded inventory rows | 743 |
| added templates | 49 |
| rejected templates | 1 |

## Sparse High-Value Coverage

| group | before | after | before note | after note |
| --- | ---: | ---: | --- | --- |
| anhydride | 10 | 16 | needs_literature_expansion | covered |
| cyanate_ester | 3 | 15 | needs_literature_expansion | covered |
| isocyanate | 7 | 16 | needs_literature_expansion | covered |
| maleimide | 5 | 16 | needs_literature_expansion | covered |
| thiol | 13 | 24 | needs_literature_expansion | covered |

## Added Template Families

| intended group | added rows |
| --- | ---: |
| anhydride | 6 |
| cyanate_ester | 12 |
| isocyanate | 9 |
| maleimide | 11 |
| thiol | 11 |

## Interpretation

- `literature_template` 是低/中权威候选来源：它只表示热固性/SMP 常见小分子单体家族模板，不提供 Tg 标签。
- 新增模板必须先通过 RDKit、允许元素、单片段、官能团检测和去重，随后仍需进入 predictor/Harness/PiEvo。
- 本轮目标是修复候选空间的稀疏官能团覆盖，让后续 replacement、LLM/RAG 和 PiEvo 有更多可反应方向可探索。
