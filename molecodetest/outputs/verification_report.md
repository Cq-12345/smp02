# MoleCode 本地验证报告

验证目录：`molecodetest/`

## 结论

- 本地验证通过：pass=12，fail=0，info=2。
- MoleCode 0.1.0 可以在本项目 conda 环境中安装并运行。
- 小分子 SMILES/MoleCode 往返、聚合物 PSMILES/MoleCode 往返、Markush 缩写节点解析与图同构比较均有可执行证据。
- 对我们的 SMP 项目，BPAB/BPADA 经过 MoleCode 往返后，官能团分类和兼容性约束保持一致。
- 这支持把 MoleCode 放在“结构表示、生成、编辑、约束审计”层；不支持把它当作 Tg 预测模型替代品。

## 逐项结果

| Domain | Case | Status | Claim | Detail | Evidence |
| --- | --- | --- | --- | --- | --- |
| environment | package | info | MoleCode package is installed in the active environment | molecode==0.1.0; rdkit canonicalization used for structural equality |  |
| scope | property_prediction | info | MoleCode is tested here as a structural representation, not as a Tg predictor | No MoleCode API was used for Tg/property prediction; the existing SMP predictor remains the property model. |  |
| small_molecule | official_aspirin | pass | SMILES -> MoleCode -> SMILES is canonical-equivalent | canonical=CC(=O)Oc1ccccc1C(=O)O; nodes=13; edges=13 | `molecodetest/outputs/graphs/official_aspirin.mmd` |
| small_molecule | official_aspirin | pass | MoleCode exposes typed nodes and edges in Mermaid graph text | graph_header=True; atom_nodes=13; edges=13 | `molecodetest/outputs/graphs/official_aspirin.mmd` |
| small_molecule | project_bpab | pass | SMILES -> MoleCode -> SMILES is canonical-equivalent | canonical=Nc1ccc(Oc2ccc(-c3ccc(Oc4ccc(N)cc4)cc3)cc2)cc1; nodes=28; edges=31 | `molecodetest/outputs/graphs/project_bpab.mmd` |
| small_molecule | project_bpab | pass | MoleCode exposes typed nodes and edges in Mermaid graph text | graph_header=True; atom_nodes=28; edges=31 | `molecodetest/outputs/graphs/project_bpab.mmd` |
| small_molecule | project_bpada | pass | SMILES -> MoleCode -> SMILES is canonical-equivalent | canonical=CC(C)(c1ccc(Oc2ccc3c(c2)C(=O)OC3=O)cc1)c1ccc(Oc2ccc3c(c2)C(=O)OC3=O)cc1; nodes=39; edges=44 | `molecodetest/outputs/graphs/project_bpada.mmd` |
| small_molecule | project_bpada | pass | MoleCode exposes typed nodes and edges in Mermaid graph text | graph_header=True; atom_nodes=39; edges=44 | `molecodetest/outputs/graphs/project_bpada.mmd` |
| project_smp | BPAB/BPADA | pass | MoleCode round-trip preserves SMP functional-group classification and pair compatibility | BPAB groups=aromatic;ether;primary_amine; BPADA groups=anhydride;aromatic;ester;ether; compatibility=酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 |  |
| project_smp | BPAB/BPADA | pass | Paper BPAB/BPADA ratios are present in the local full candidate table | ratio_a/b=0.50/0.50: row=17565, Tg=226.28 C; ratio_a/b=0.55/0.45: row=17566, Tg=202.01 C | `artifacts/reproduce/discovery/all_ratio_candidates.csv` |
| polymer | nylon6 | pass | PSMILES repeat unit -> MoleCode -> PSMILES is canonical-equivalent | canonical=*NCCCCCC(*)=O; repeat_marker=×8; termini=TL/TR | `molecodetest/outputs/graphs/polymer_nylon6.mmd` |
| polymer | polyethylene | pass | PSMILES repeat unit -> MoleCode -> PSMILES is canonical-equivalent | canonical=*CC*; repeat_marker=×100; termini=TL/TR | `molecodetest/outputs/graphs/polymer_polyethylene.mmd` |
| markush | abbrev_nodes | pass | Markush-style abbreviation nodes are parsed as graph nodes | abbrev_labels=['Boc', 'R1']; edges=2 | `molecodetest/outputs/graphs/markush_abbrev_nodes.mmd` |
| markush | graph_isomorphism | pass | Markush graph comparison detects same and changed topology | self-isomorphic=True; missing-edge-isomorphic=False | `molecodetest/outputs/graphs/markush_abbrev_nodes.mmd` |

## 来源对应

- 论文 `/home/user4/smp02/paper/2605.16480v1.pdf`：核心主张包括 training-free、graph-explicit、Subgraph-Node-Edge、标准格式确定性双向转换、聚合物/Markush 扩展，以及 MoleCode 不创造模型缺失化学知识的限制。
- GitHub `https://github.com/AtomFlow-AI/MoleCode`：公开 README 给出的 `pip install molecode`、小分子 round-trip、polymer/Markush API 与本地验证接口一致。

复跑命令：

```bash
conda run -n mhc_pyg314 python molecodetest/verify_molecode.py
```
