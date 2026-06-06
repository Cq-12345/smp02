# TODO Completion Audit

本文档把 TODO 的非暂缓任务、证据文件和剩余边界结构化。它不产生 Tg observation，也不代表真实实验已经完成。

## Summary

| item | value |
| --- | ---: |
| audit_rows | 10 |
| implemented_rows | 9 |
| deferred_rows | 1 |
| needs_real_or_high_fidelity_evidence_rows | 2 |
| all_evidence_present_rows | 10 |
| missing_evidence_rows | 0 |
| non_deferred_all_evidence_present | True |
| primary_open_blocker | human_process_approval_and_real_or_high_fidelity_observation |
| evidence_level | todo_completion_audit_not_observation |
| audit_path | artifacts/trail/workflow/todo_completion_audit.csv |
| summary_path | artifacts/trail/workflow/todo_completion_audit_summary.json |
| report_path | reports/todo_completion_audit.md |

## Task Matrix

| task | status | evidence | next action |
| --- | --- | ---: | --- |
| 真实 Tg 温度不固定 | implemented | 3/3 | 用真实/高保真 observation 做正式多目标 posterior sweep |
| 真实商品级组分/聚合物/超图表示 | deferred_by_user | 1/1 | 等待用户恢复该方向；当前继续使用单一小分子 SMILES/MoleCode |
| 知识库/先验库/本体 | implemented_needs_more_literature_extraction | 4/4 | 从更多 SMP 文献抽取固化程序和 process fields |
| 候选组分数据集/来源/官能团分类 | implemented | 4/4 | 用真实/高保真 evidence 调整 source authority |
| 预测模型/CNN-SVR-RF/GNN/model zoo | implemented | 5/5 | 更长 GNN 训练，并评估是否纳入 ensemble/OOD 审计 |
| 生成模型/VAE/LLM/RAG/SFT/diffusion/flow/Harness | implemented_smoke_needs_real_generator_outputs | 6/6 | 接入真实外部 LLM/SFT 或有效 SMILES decoder；输出仍走 ledger/Harness/PiEvo |
| PiEvo-faithful/原则 posterior/IDS/full-history | implemented | 4/4 | 用高权重真实/高保真 evidence 检验 posterior shift |
| 人工闭环/真实实验结果迭代优化 | implemented_blocked_by_human_or_high_fidelity_evidence | 5/5 | 先审核 12 行 process approval，再执行高保真/真实结果 intake |
| 多智能体 workflow/服务化总览 | implemented | 3/3 | 后续把真实 provider/真实实验结果接入同一 summary |
| RL/策略层预算分配 | implemented_surrogate_backed | 3/3 | 高权重 evidence 进入后，比较 posterior shift 再调预算 |

## Interpretation

- `deferred_by_user` 只对应商品级/聚合物/超图表示；当前按用户要求不做。
- `implemented_*` 表示已有代码、artifact 或文档证据；其中 `needs_real_or_high_fidelity_evidence` 说明下一步需要人工审批、真实实验或高保真结果，而不能由脚本伪造。
- 当前主阻塞不是 surrogate 生成失败，而是高权重证据链等待 process approval 和真实/高保真 result intake。
