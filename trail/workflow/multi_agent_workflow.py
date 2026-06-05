from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


AGENTS = {
    "space_agent": "界定搜索空间：官能团、反应兼容性、摩尔比网格。",
    "generator_agent": "生成候选假设：单体对和替换策略。",
    "predictor_agent": "评估假设：VAE-WVCM-SVR/RF/CNN Tg 预测。",
    "principle_agent": "更新原则：统计高分候选的反应规则并调整下一轮优先级。",
}


def summarize(candidate_space: Path, closed_loop_history: Path) -> dict:
    candidates = pd.read_csv(candidate_space) if candidate_space.exists() else pd.DataFrame()
    history = json.loads(closed_loop_history.read_text(encoding="utf-8")) if closed_loop_history.exists() else []
    return {
        "agents": AGENTS,
        "candidate_rows": int(len(candidates)),
        "best_candidates": candidates.head(10).to_dict(orient="records") if not candidates.empty else [],
        "closed_loop_history": history,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-space", default="artifacts/reproduce/discovery/candidate_space_top_scored.csv")
    parser.add_argument("--history", default="artifacts/reproduce/closed_loop/closed_loop_history.json")
    parser.add_argument("--out", default="artifacts/trail/workflow/multi_agent_summary.json")
    args = parser.parse_args()
    result = summarize(Path(args.candidate_space), Path(args.history))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()

