# Candidate Source Registry And Functional Group Audit

本文档回应 TODO 中“候选组分数据集：来源、按官能团分类、数据库组织”的要求。当前仍只处理单一小分子 SMILES / MoleCode，不做商品级复杂组分或聚合物超图表示。

## Outputs

- Source registry: `trail/candidates/source_registry.yaml`
- Source summary: `artifacts/trail/candidates_expanded_source_audit/candidate_source_summary.csv`
- Functional group coverage: `artifacts/trail/candidates_expanded_source_audit/functional_group_source_coverage.csv`
- JSON summary: `artifacts/trail/candidates_expanded_source_audit/candidate_source_audit_summary.json`

## Inventory Summary

- Candidate components: 743
- Functional groups: 18
- Registered sources: 5

## Source Summary

| source | type | authority | components | groups | top groups |
| --- | --- | ---: | ---: | ---: | --- |
| library | literature_dataset | 4 | 225 | 17 | ether:155;aromatic:110;ester:73;primary_amine:62;vinyl:58;epoxy:39;hydroxyl:38;secondary_amine:8 |
| literature_template | curated_literature_template | 2 | 49 | 15 | aromatic:35;ether:22;vinyl:13;nitrile:12;cyanate_ester:12;maleimide:11;imide:11;thiol:11 |
| generated | rule_template_seed | 2 | 10 | 15 | aromatic:10;ether:4;primary_amine:2;hydroxyl:2;phenol:2;anhydride:1;ester:1;cyanate_ester:1 |
| chembl | database_screen | 1 | 459 | 16 | aromatic:365;ether:261;hydroxyl:248;secondary_amine:224;vinyl:142;ester:139;primary_amine:103;carboxylic_acid:85 |

## Sparse High-Value Groups

| group | total | sources present | note |
| --- | ---: | ---: | --- |
| none | 0 | 0 | all sparse high-value groups above threshold |

## Interpretation

- `library` 是当前最高权重来源，因为它直接来自本地 SMP 数据集和论文复现材料。
- `generated` 用来补足热固性常见但数据稀疏的结构；它不是实验标签来源，必须继续通过 predictor/Harness/PiEvo。
- `literature_template` 用手工整理的小分子模板补足稀疏热固性官能团；它仍是候选来源，不是 Tg 标签来源。
- `chembl` 提供新颖性和 OOD 探索，但 authority 较低，尤其需要过滤 drug-like 复杂结构。
- 稀疏高价值官能团应优先从 SMP 论文或人工规则模板扩展，而不是盲目扩大 ChEMBL 数量。
- 后续真实 LLM/RAG 生成出的候选应通过 generation record ledger 进入 `generation_record` 来源，而不是直接混入 library。
