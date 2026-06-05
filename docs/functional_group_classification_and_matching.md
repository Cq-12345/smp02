# 官能团分类与合理匹配规则

## 结论

论文和补充材料只写了两步：

1. `Categorize SMILES strings based on functional groups.`
2. `Define reasonable combinations of functional groups for SMP generation.`

但没有公开具体 SMARTS、类别表或兼容性矩阵。因此本仓库把这两步实现为可审计规则：

- 用 RDKit SMARTS 对 SMILES 做官能团检测。
- 用热固性 SMP 常见固化/交联反应定义兼容性。
- 只允许至少存在一个兼容反应对的单体组合进入候选搜索空间。

规则文件：`src/smp02/functional_groups.py`

## 官能团分类

当前分类覆盖以下类别：

- `epoxy`: 环氧基。
- `primary_amine`, `secondary_amine`: 伯胺/仲胺。
- `anhydride`: 酸酐。
- `isocyanate`: 异氰酸酯。
- `hydroxyl`, `phenol`: 醇羟基/酚羟基。
- `carboxylic_acid`: 羧酸。
- `acrylate_or_methacrylate`, `vinyl`: 可自由基聚合或 thiol-ene 的不饱和基团。
- `thiol`: 硫醇。
- `cyanate_ester`: 氰酸酯。
- `maleimide`: 马来酰亚胺。
- `imide`, `ester`, `ether`, `nitrile`, `aromatic`: 结构/性能相关基团。

这些类别不是互斥的。一个单体可以同时有芳香环、醚键、酸酐、酰亚胺等多个标签。

## 合理匹配

合理组合不是简单地按相似官能团配对，而是按反应可行性过滤：

- 环氧 + 伯胺/仲胺：环氧开环固化。
- 环氧 + 酸酐：环氧-酸酐固化。
- 环氧 + 羧酸/羟基：开环酯化或醚化，通常需要催化剂。
- 酸酐 + 胺：形成聚酰胺酸/聚酰亚胺前体。
- 酸酐 + 羟基/酚羟基：酯化。
- 异氰酸酯 + 羟基/酚羟基：聚氨酯。
- 异氰酸酯 + 胺：聚脲。
- 丙烯酸酯/甲基丙烯酸酯 + 乙烯基：自由基共聚。
- 丙烯酸酯/甲基丙烯酸酯 + 硫醇：thiol-ene/Michael 加成。
- 氰酸酯 + 氰酸酯：三聚形成三嗪网络。
- 氰酸酯 + 酚羟基/胺：共固化或催化三聚。
- 马来酰亚胺 + 胺/硫醇/乙烯基：Michael 加成或共聚。

## 为什么这样做

SMP discovery 的候选空间不能只由模型预测值决定。若任意两个 SMILES 都可组合，搜索空间会产生大量化学上不可合成或无法形成交联网络的假设。论文第 3 节明确要求“systematically paired based on their functional groups, ensuring only chemically compatible combinations”，所以这里用反应兼容性作为 hard constraint。

## 限制

- 规则不判断反应动力学、催化剂、溶解性、商业可得性或实际加工窗口。
- SMARTS 检测是子结构级别，不能完全判断官能度、空间位阻或是否能形成有效网络。
- 当前实现偏向常见热固性体系，后续可把真实实验失败/成功结果写回规则权重。

## 输出文件

运行 discovery 后会生成：

- `monomer_functional_groups.csv`: 每个单体的官能团标签。
- `compatible_monomer_pairs.csv`: 通过兼容性过滤的单体对和理由。
- `selected_candidates.csv`: 预测 Tg 在目标区间的候选配方。

