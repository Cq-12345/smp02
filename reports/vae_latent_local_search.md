# VAE Latent Local Search

本文档把 TODO 中“VAE：替换策略；生成策略”推进为可运行的 VAE latent-neighborhood local search。它不声称 VAE decoder 已经生成全新有效 SMILES，而是在当前可审计候选 inventory 中，用 VAE latent 距离检索高 reward 候选附近的替换单体，再交给同一 predictor/Harness 评估链。

## 输出文件

- Proposals: `artifacts/trail/generation/vae_latent_local_search/latent_local_search_proposals.csv`
- Summary: `artifacts/trail/generation/vae_latent_local_search/latent_local_search_summary.json`
- Report: `reports/vae_latent_local_search.md`

## 汇总

| item | value |
| --- | ---: |
| input_candidate_rows | 500 |
| source_candidate_rows | 20 |
| replacement_pool_rows | 710 |
| encoded_unique_smiles | 710 |
| proposals | 200 |
| latent_size | 512 |
| per_side | 5 |
| require_counterpart_compatibility | True |
| require_shared_groups | True |
| literature_template_proposals | 39 |
| mean_latent_distance | 0.062434 |
| min_latent_distance | 0.005643 |
| mean_tanimoto | 0.244208 |

## 最近邻替换示例

| rank | source Tg (C) | side | latent distance | latent cosine | tanimoto | source | matched groups | compatibility |
| ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| 1 | 194.966 | b | 0.0056 | 1.0000 | 0.375 | library | primary_amine | 异氰酸酯-伯胺形成聚脲。 |
| 2 | 195.007 | b | 0.0056 | 1.0000 | 0.375 | library | primary_amine | 环氧-伯胺开环固化。 |
| 3 | 194.968 | b | 0.0064 | 1.0000 | 0.897 | library | aromatic;epoxy;ester;ether | 环氧-伯胺开环固化。 |
| 4 | 194.948 | b | 0.0090 | 1.0000 | 0.429 | library | aromatic;primary_amine | 环氧-伯胺开环固化。 |
| 5 | 194.966 | a | 0.0092 | 1.0000 | 0.538 | literature_template | aromatic;isocyanate | 异氰酸酯-伯胺形成聚脲。 |
| 6 | 194.968 | a | 0.0110 | 1.0000 | 0.120 | library | aromatic | 环氧-羟基醚化，常需催化剂。 |
| 7 | 195.020 | b | 0.0119 | 1.0000 | 0.308 | library | hydroxyl | 环氧-羟基醚化，常需催化剂。 |
| 8 | 194.966 | b | 0.0125 | 1.0000 | 0.323 | library | primary_amine | 异氰酸酯-伯胺形成聚脲。 |
| 9 | 195.007 | b | 0.0125 | 1.0000 | 0.323 | library | primary_amine | 环氧-伯胺开环固化。 |
| 10 | 195.020 | b | 0.0125 | 0.9999 | 0.286 | library | hydroxyl | 环氧-羟基醚化，常需催化剂。 |
| 11 | 195.020 | b | 0.0125 | 1.0000 | 0.222 | library | hydroxyl | 环氧-羟基醚化，常需催化剂。 |
| 12 | 194.968 | a | 0.0138 | 0.9999 | 0.400 | library | aromatic;primary_amine | 环氧-伯胺开环固化。 |
| 13 | 195.020 | b | 0.0160 | 0.9999 | 0.176 | library | hydroxyl | 环氧-羟基醚化，常需催化剂。 |
| 14 | 195.020 | b | 0.0175 | 0.9999 | 0.111 | literature_template | hydroxyl | 环氧-羧酸开环酯化。 |
| 15 | 194.972 | a | 0.0182 | 0.9999 | 0.105 | library | hydroxyl | 酸酐-羟基酯化。 |
| 16 | 194.972 | a | 0.0208 | 0.9999 | 0.375 | library | hydroxyl | 酸酐-羟基酯化。 |
| 17 | 194.949 | b | 0.0224 | 0.9998 | 0.471 | library | aromatic;primary_amine | 氰酸酯-胺共反应。 |
| 18 | 194.972 | b | 0.0224 | 0.9998 | 0.471 | library | aromatic;primary_amine | 氰酸酯-胺共反应。 |
| 19 | 195.052 | b | 0.0224 | 0.9998 | 0.471 | library | aromatic;primary_amine | 环氧-伯胺开环固化。 |
| 20 | 194.968 | a | 0.0226 | 0.9999 | 0.400 | library | aromatic;primary_amine | 环氧-伯胺开环固化。 |

## 解释

- 旧 replacement 使用 Morgan/Tanimoto 排序；本策略使用当前 VAE encoder 学到的 latent 几何排序。
- `--require-counterpart-compatibility` 打开时，替换单体必须继续和未替换的另一侧单体形成可映射反应对。
- 输出仍保留 `tanimoto`，便于后续比较“指纹相似”和“VAE 表示相近”是否给出不同候选。
- 下一步必须运行 `scripts/evaluate_replacement_proposals.py`；未通过 predictor/Harness/PiEvo 的 latent 邻居不能被当成推荐配方。
