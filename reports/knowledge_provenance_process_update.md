# Knowledge Provenance And Process Conditions Update

本文档记录 TODO 中“smp 合理知识库、先验知识库、知识图谱、本体”的本轮增强。当前仍只覆盖单一小分子 SMILES / MoleCode，不做商品级复杂组分或聚合物超图表示。

## What Changed

- `trail/knowledge/smp_prior_knowledge.yaml` 新增 `literature_sources`、`process_condition_templates`、`reaction_evidence_map` 和 `structural_evidence_map`。
- `trail/knowledge/ontology.yaml` 新增 `LiteratureSource` 和 `ProcessConditionTemplate` 类，以及 `supported_by_source`、`conditioned_by_process` 关系。
- `trail/knowledge/build_kg.py` 现在会把文献来源和工艺条件模板写入知识图谱。
- `artifacts/trail/kg_enriched/*` 已重建。

## KG Summary

| item | value |
| --- | ---: |
| nodes | 126 |
| edges | 151 |
| literature sources | 5 |
| process condition templates | 8 |
| reaction principles | 20 |
| supported_by_source edges | 36 |
| conditioned_by_process edges | 20 |

## Interpretation

- 反应原则不再只是“官能团 A 与 B 兼容”，还会指向需要记录的工艺条件模板。
- 结构先验和反应原则现在有来源节点，但这些来源仍是本地文件/规则级证据，不等于真实物理真理。
- 后续真实实验或文献复现数据进入 observation ledger 时，应把催化剂、固化温度、后固化、光/热/自由基触发方式结构化记录。
- PiEvo posterior 仍应把这些 principle 当作可被证据削弱或增强的假说，而不是硬编码真理。
