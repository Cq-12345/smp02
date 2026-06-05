# Closed-loop Workflow

本仓库把 README 中的闭环要求实现为 in-silico workflow：

1. 界定搜索空间：
   - 从扩充 XLSX 提取唯一单体。
   - 用 SMARTS 分类官能团。
   - 用兼容性矩阵过滤化学上合理的单体对。
2. 生成假设：
   - 对每个合理单体对枚举摩尔比。
   - 默认 5%-95%，步长 5%。
3. 预测/评估：
   - VAE 编码单体。
   - WVCM 生成配方向量。
   - SVR 预测 Tg。
   - 按目标区间 190-200°C 和 target distance 排序。
4. 优化/改进假设：
   - 闭环脚本读取候选空间。
   - 每轮选择 top-k 候选。
   - 被选候选的 compatibility principle 权重提高。
   - 下一轮排序加入 principle prior，逐步偏向更有效的官能团组合。

脚本入口：

```bash
PYTHONPATH=src conda run --no-capture-output -n mhc_pyg314 python -m smp02.cli closed-loop --config configs/reproduce.yaml
```

输出：

- `closed_loop_selected.csv`
- `closed_loop_history.json`
- `evolved_principles.json`

这个闭环目前使用模型预测作为反馈源。若后续有真实合成/DSC 实验结果，可以把实验 Tg 作为新 observation 加入数据集，再重训 predictor 或更新 principle weights。

