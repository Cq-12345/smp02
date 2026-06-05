# Generation Failure Feedback Analysis

本文档回应 TODO 中“生成 -> 预测/评估 -> 优化（改进假设）”和“人工闭环/失败回流”的要求。当前仍使用单一小分子 SMILES / MoleCode，不涉及商品级组分或聚合物超图表示。

## Outputs

- Strategy feedback: `artifacts/trail/generation_feedback_strict/strategy_feedback.csv`
- Failure reasons: `artifacts/trail/generation_feedback_strict/failure_reason_counts.csv`
- Replacement failure groups: `artifacts/trail/generation_feedback_strict/replacement_failure_groups.csv`
- Summary: `artifacts/trail/generation_feedback_strict/generation_feedback_summary.json`

## Summary

| item | value |
| --- | ---: |
| generation_records | 4 |
| generation_harness_pass | 3 |
| generation_harness_fail | 1 |
| replacement_rejections | 0 |
| failure_reason_types | 3 |
| strategies_analyzed | 3 |
| top_failure_reason | prediction_missing |
| lowest_policy_strategy | llm_smiles_generation |

## Strategy Feedback

| strategy | records | pass rate | policy delta | top failure | next constraint |
| --- | ---: | ---: | ---: | --- | --- |
| functional_group_replacement | 1 | 1.000 | 0.10 |  | retain: keep strategy in candidate generator pool. |
| llm_rag_principle_generation | 2 | 1.000 | 0.10 |  | retain: keep strategy in candidate generator pool. |
| llm_smiles_generation | 1 | 0.000 | -0.25 | prediction_missing | predictor_feedback: run VAE-WVCM/GNN predictor before recommendation. |

## Failure Reasons

| reason | count | action |
| --- | ---: | --- |
| prediction_missing | 1 | predictor_feedback: run VAE-WVCM/GNN predictor before recommendation. |
| chemistry_evidence_missing | 1 | chemistry_feedback: require compatibility_reasons from functional-group rules. |
| replacement_formula_failed_reaction_or_ratio_constraints | 1 | replacement_feedback: preserve complementary reactive pair, not only shared groups. |

## Replacement Group Feedback

| shared groups | failures | mean tanimoto | feedback |
| --- | ---: | ---: | --- |
| none | 0 | 0.000 | no replacement failure groups |

## Interpretation

- 失败回流现在是一个可运行的审计步骤，而不是只在报告里口头说明。
- `policy_weight_delta` 不是物理真理或最终 RL policy；它是下一轮生成器排序/人工审核优先级的建议权重。
- 当前 replacement rejection 输入为 0；若 replacement strategy pass rate 上升，说明前一轮互补反应对约束已经修复了主要失败路径。
- `llm_smiles_generation` 草案必须先补预测和化学兼容证据，再允许进入 PiEvo IDS 或实验推荐。
