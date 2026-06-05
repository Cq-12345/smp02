请复现该文章【/home/user4/smp02/paper/Journal of Polymer Science - 2024 - Teimouri - Machine Learning‐Driven Discovery of Thermoset Shape Memory Polymers With.pdf】和补充材料【/home/user4/smp02/paper/pol20241095-sup-0001-supinfo.docx】，包括文章的每个特殊的训练模型、各种尝试、对比试验等。要求：使用我这个扩充版本的数据集XLSX。要求训练模型、寻找新配方，都要做。

充分利用我们当前计算机CPU、GPU、内存、显存的良好性能，适度地并行加快计算。

conda 环境 (mhc_pyg314)

本仓库复现论文 `Machine Learning-Driven Discovery of Thermoset Shape Memory Polymers With High Glass Transition Temperature Using Variational Autoencoders` 的可执行流程，并使用本地扩充数据集 `data/SMP_Dataset.xlsx`。

你需要创建git仓库，并同步至【https://github.com/Cq-12345/smp02.git】。记得定期提交到github啊！

论文见PAPER文件夹

目标环境：`conda activate mhc_pyg314`

2. Categorize SMILES strings based on functional groups.
3. Define reasonable combinations of functional groups for SMP generation.


这两个步骤到底是怎么做的？你可能需要分析论文，并形成你的思考，把这部分官能团分类与匹配单独形成一个新的介绍文档。


在没有做到完美复刻实现论文的所有模型训练与实验的前提下，不允许退出运行。

在完美复刻实现论文后，做如下尝试，需要代码统一放在trail里面，内部结构自行组织。尝试这种内容，来源于会议速记。


【

## 完整复现

1. smp的合理知识库，先验知识库
2. 官能团匹配等？
3. 化学反应原理
4. 知识图谱（LLM+agent，整理）
5. 本体
6. 候选组分数据集
7. 来源：smp相关论文；数据库
8. 数据集组织：按官能团分类；
9. 数据库：…
10. 预测模型
11. GNN
12. 其他，Learning parameters for ML models (CNN, SVR, and RF)【paper】…比对
13. 生成模型：【paper】
14. 探索空间的界定
15. 生成策略
16. VAE：替换策略；
17. LLM：
18. 微调sft；（内部）
19. prompt
20. rag上下文；
21. Harness约束控制（外部改进）
22. 其他生成模型，扩散生成，流匹配等。。。
23. 界定搜索空间——生成（假设）——预测/评估——优化（改进假设）：workflow闭环自主迭代
24. 多智能体服务workflow
25. 实现环境
26. 参考rag，harness，
27. RL，人工闭环，真实实验结果迭代优化
28. 搜索空间优化，根据先验知识+当前上下文等（见文献PIEVO）】

完整配置对齐论文参数：ChEMBL 550,000 条、VAE 20 epoch pretrain + 20 epoch fine-tune、7 个 latent size、CNN/SVR/RF 对比。

```bash

./scripts/run_reproduce.sh

```

或分步运行：

```bash

PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli inspect-data --config configs/reproduce.yaml

PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli train-vae --config configs/reproduce.yaml

PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli train-predictors --config configs/reproduce.yaml

PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli discover --config configs/reproduce.yaml

PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli closed-loop --config configs/reproduce.yaml

```

## 关键文档

- `docs/paper_reproduction_notes.md`: 论文和补充材料中的模型、超参数、评价指标和复现决策。
- `docs/functional_group_classification_and_matching.md`: 官能团分类与合理匹配规则，回答 README 原任务中特别指出的问题。
- `docs/closed_loop_workflow.md`: 自主迭代闭环的实现方式。
- `trail/`: 会议速记中的扩展尝试，包括知识库、知识图谱、本体、GNN、RAG、harness 和多智能体 workflow 原型。

## 原任务摘要

原始要求：复现论文和补充材料中的特殊训练模型、尝试和对比实验；使用扩充版 XLSX；训练模型并寻找新配方；实现“界定搜索空间 -> 生成假设 -> 预测/评估 -> 优化”的闭环；补充官能团分类与匹配文档；扩展尝试代码放在 `trail/`。
