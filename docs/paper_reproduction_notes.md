# Paper Reproduction Notes

## 本地材料

- 主论文：`paper/Journal of Polymer Science - 2024 - Teimouri - Machine Learning‐Driven Discovery of Thermoset Shape Memory Polymers With.pdf`
- 补充材料：`paper/pol20241095-sup-0001-supinfo.docx`
- 扩充数据集：`data/SMP_Dataset.xlsx`
- ChEMBL：`data/chembl_36_chemreps.txt`

## 论文流程

论文框架分为三段：

1. TL-VAE：
   - 使用 550,000 个 ChEMBL drug-like molecules 预训练。
   - 使用 SMP 单体随机 SMILES 增强数据 fine-tune。
   - latent size 比较：16, 32, 64, 128, 256, 512, 1024。
   - 输入 SMILES one-hot 矩阵尺寸：204 x 55。
2. Tg predictor：
   - 对每个单体用 fine-tuned VAE 编码成 latent vector。
   - 用 WVCM 按摩尔比加权求和，得到 SMP vector。
   - 训练 CNN、SVR、RF，训练/测试划分 85%/15%。
3. Forward design：
   - 按官能团类别生成化学上合理的单体组合。
   - 摩尔比从 5% 到 95%，步长 5%。
   - 用最佳模型预测 Tg，筛选 190-200°C 候选。

## 论文/补充材料超参数

VAE：

- batch size: 512
- learning rate: 0.0001
- optimizer: Adam
- encoder: 2D convolution layers `1-32-16-8`，fully connected `1456`
- decoder: fully connected `1456`，2D convolution layers `8-16-2-1`
- activation: ReLU
- kernel size: 3 x 3
- pretrain epochs: 20
- fine-tune epochs: 20
- reconstruction weight: 1.0
- validity weight: 0.1

CNN Tg predictor：

- batch size: 16
- learning rate: 0.00001
- optimizer: Adam
- conv layers: `1->256`, `256->128`, `128->64`, kernel 3
- FC layers: `64->256->64->64->64->32->32->32->1`
- activation: ReLU
- weight decay: 1e-3

SVR：

- C: 1000
- kernel: RBF
- epsilon: 1.0

RF：

- trees: 100

## 论文指标

论文报告 SVR 组合中 latent size 64 的 test MAPE 最低：

- VAE(64)+SVR: test MAPE 6.43%, test R2 0.87
- VAE(512)+SVR: test R2 0.88, 但 test MAPE 7.41%

因此本仓库默认 discovery 使用 `latent_size=64` 和 SVR。

## 复现决策

补充材料没有公开原始代码，也没有给出具体官能团映射表和所有训练随机种子。本实现做了以下可审计补全：

- one-hot charset 从本地 ChEMBL + SMP 单体自动构建，并保证不少于 55 个 token。
- VAE encoder/decoder 层数与通道数对齐论文表格，使用 adaptive pooling 固定到 1456 维。
- validity penalty 被记录进 loss 标量；由于 RDKit validity 是离散检查，它主要作为训练日志和不可微惩罚项。
- 官能团规则由 `src/smp02/functional_groups.py` 的 SMARTS 和兼容性映射定义，并在 `docs/functional_group_classification_and_matching.md` 解释。

