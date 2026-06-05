# SMP02: thermoset SMP discovery reproduction

本仓库复现论文 `Machine Learning-Driven Discovery of Thermoset Shape Memory Polymers With High Glass Transition Temperature Using Variational Autoencoders` 的可执行流程，并使用本地扩充数据集 `data/SMP_Dataset.xlsx`。

## 已实现闭环

1. 读取扩充 XLSX 数据集，解析每个 SMP 的单体 SMILES、摩尔比和 Tg。
2. 用 ChEMBL SMILES 预训练 VAE，并用 SMP 单体随机 SMILES 增强数据 fine-tune decoder。
3. 对 7 个 latent size `[16, 32, 64, 128, 256, 512, 1024]` 训练 VAE。
4. 用 WVCM 将单体 latent vector 按摩尔比加权求和，训练 CNN、SVR、RF 预测 Tg。
5. 对单体做官能团 SMARTS 分类，按热固性反应兼容规则生成合理候选配方。
6. 枚举 5%-95% 摩尔比，用最佳 SVR 预测 Tg，筛选 190-200°C 候选。
7. 运行“界定搜索空间 -> 生成假设 -> 预测评估 -> 优化原则/假设”的 in-silico 闭环迭代。

## 环境

目标环境：`conda activate mhc_pyg314`

必要依赖已经写入 `requirements.txt` 和 `pyproject.toml`。如果缺包：

```bash
conda run -n mhc_pyg314 python -m pip install -r requirements.txt
```

## 快速验证

Smoke 配置只训练极小样本和少量 epoch，用于检查整条链路：

```bash
./scripts/run_smoke.sh
```

输出在 `artifacts/smoke/`。

## 完整复现

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

