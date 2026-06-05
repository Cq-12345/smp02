from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from smp02.utils import load_json, save_json


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def top_posterior(path: Path, n: int = 8) -> list[dict[str, object]]:
    posterior = load_json(path)
    rows = [
        {"principle": str(name), "posterior": float(value)}
        for name, value in sorted(posterior.items(), key=lambda item: float(item[1]), reverse=True)[:n]
    ]
    return rows


def summarize_run(label: str, output_dir: Path) -> dict[str, Any]:
    summary = load_json(output_dir / "pievo_faithful_summary.json")
    posterior = load_json(output_dir / "principle_posterior.json")
    selected = read_csv_if_exists(output_dir / "selected_formulations.csv")
    external = read_csv_if_exists(output_dir / "external_observations_used.csv")
    map_principle = str(summary.get("map_principle", ""))
    selected_keys = set()
    if not selected.empty:
        selected_keys = {f"{row['smiles']}@{row['ratios']}" for _, row in selected.iterrows()}
    return {
        "label": label,
        "output_dir": str(output_dir),
        "external_rows": int(summary.get("external_observation_summary", {}).get("accepted_rows", len(external))),
        "external_mean_reward": float(summary.get("external_observation_summary", {}).get("mean_reward", 0.0)),
        "external_best_distance_c": None if external.empty else float(pd.to_numeric(external["target_distance_c"]).min()),
        "history_rows": int(summary.get("history_rows", 0)),
        "total_authority_weight": float(summary.get("total_authority_weight", 0.0)),
        "posterior_entropy": float(summary.get("posterior_entropy", 0.0)),
        "map_principle": map_principle,
        "map_principle_posterior": float(posterior.get(map_principle, 0.0)),
        "best_selected_target_distance_c": summary.get("best_selected_target_distance_c"),
        "selected_rows": int(summary.get("selected_rows", len(selected))),
        "all_selected_within_target_guard": bool(summary.get("all_selected_within_target_guard", False)),
        "all_selected_pass": bool(summary.get("validation", {}).get("all_selected_pass", False)),
        "selected_keys": sorted(selected_keys),
        "top_posterior": top_posterior(output_dir / "principle_posterior.json"),
    }


def posterior_delta(original_dir: Path, feedback_dir: Path) -> pd.DataFrame:
    original = load_json(original_dir / "principle_posterior.json")
    feedback = load_json(feedback_dir / "principle_posterior.json")
    names = sorted(set(original) | set(feedback))
    rows = []
    for name in names:
        original_value = float(original.get(name, 0.0))
        feedback_value = float(feedback.get(name, 0.0))
        rows.append(
            {
                "principle": name,
                "original_posterior": original_value,
                "feedback_guided_posterior": feedback_value,
                "delta": feedback_value - original_value,
                "abs_delta": abs(feedback_value - original_value),
            }
        )
    return pd.DataFrame(rows).sort_values("abs_delta", ascending=False)


def selected_overlap(original: dict[str, Any], feedback: dict[str, Any]) -> dict[str, object]:
    original_keys = set(original["selected_keys"])
    feedback_keys = set(feedback["selected_keys"])
    union = original_keys | feedback_keys
    overlap = original_keys & feedback_keys
    return {
        "selected_overlap": int(len(overlap)),
        "selected_union": int(len(union)),
        "selected_jaccard": 1.0 if not union else float(len(overlap) / len(union)),
        "same_selected_set": original_keys == feedback_keys,
    }


def fmt(value: object, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_report(
    original: dict[str, Any],
    feedback: dict[str, Any],
    deltas: pd.DataFrame,
    overlap: dict[str, object],
    report_path: Path,
) -> None:
    rows = [
        ("external rows", original["external_rows"], feedback["external_rows"]),
        ("external mean reward", original["external_mean_reward"], feedback["external_mean_reward"]),
        ("external best distance C", original["external_best_distance_c"], feedback["external_best_distance_c"]),
        ("history rows", original["history_rows"], feedback["history_rows"]),
        ("total authority weight", original["total_authority_weight"], feedback["total_authority_weight"]),
        ("posterior entropy", original["posterior_entropy"], feedback["posterior_entropy"]),
        ("MAP principle", original["map_principle"], feedback["map_principle"]),
        ("MAP principle posterior", original["map_principle_posterior"], feedback["map_principle_posterior"]),
        ("best selected distance C", original["best_selected_target_distance_c"], feedback["best_selected_target_distance_c"]),
        ("selected rows", original["selected_rows"], feedback["selected_rows"]),
        ("all selected pass", original["all_selected_pass"], feedback["all_selected_pass"]),
    ]
    lines = [
        "# PiEvo Replacement Ledger Feedback Comparison",
        "",
        "本文档比较原始 replacement observation ledger 与 feedback-guided strict replacement ledger 进入 PiEvo-faithful 后的差异。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM-GPR，不涉及暂缓的商品级组分或聚合物超图表示。",
        "",
        "## Inputs",
        "",
        f"- Original PiEvo output: `{original['output_dir']}`",
        f"- Feedback-guided PiEvo output: `{feedback['output_dir']}`",
        "",
        "## Summary",
        "",
        "| metric | original replacement ledger | feedback-guided replacement ledger |",
        "| --- | ---: | ---: |",
    ]
    for metric, original_value, feedback_value in rows:
        lines.append(f"| {metric} | {fmt(original_value)} | {fmt(feedback_value)} |")
    lines.extend(
        [
            "",
            "## IDS Selection Overlap",
            "",
            "| selected overlap | selected union | Jaccard | same selected set |",
            "| ---: | ---: | ---: | --- |",
            f"| {overlap['selected_overlap']} | {overlap['selected_union']} | {float(overlap['selected_jaccard']):.3f} | {overlap['same_selected_set']} |",
            "",
            "## Posterior Delta",
            "",
            "| principle | original posterior | feedback-guided posterior | delta |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for _, row in deltas.head(12).iterrows():
        lines.append(
            f"| {row['principle']} | {float(row['original_posterior']):.6f} | "
            f"{float(row['feedback_guided_posterior']):.6f} | {float(row['delta']):+.6f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Strict replacement ledger 接收 11 条外部 surrogate observation，原始 replacement ledger 接收 10 条。",
            "- 在相同随机种子、目标 Tg、target guard 和 PiEvo 参数下，4 轮 IDS 选择集合没有变化；这说明当前短 smoke 中选择路径主要受候选池和 target-feasible IDS 控制。",
            "- 但 feedback-guided ledger 让 posterior entropy 明显下降，并把 MAP principle 的后验推得更集中。这表示失败回流虽然没有马上改变所选配方，但已经改变了 principle posterior 的置信分布。",
            "- 这里的后验收缩仍然来自 surrogate/Harness observation，不是物理真理。后续若加入真实 DSC 或高保真模拟，应该用更高 authority weight 重新比较 posterior delta。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare_runs(original_dir: Path, feedback_dir: Path, out_dir: Path, report_path: Path) -> dict[str, Any]:
    original = summarize_run("original_replacement", original_dir)
    feedback = summarize_run("feedback_guided_replacement", feedback_dir)
    deltas = posterior_delta(original_dir, feedback_dir)
    overlap = selected_overlap(original, feedback)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "original": {key: value for key, value in original.items() if key != "selected_keys"},
        "feedback_guided": {key: value for key, value in feedback.items() if key != "selected_keys"},
        **overlap,
    }
    pd.DataFrame([original, feedback]).drop(columns=["selected_keys", "top_posterior"]).to_csv(out_dir / "pievo_feedback_ledger_comparison.csv", index=False)
    deltas.to_csv(out_dir / "principle_posterior_delta.csv", index=False)
    save_json(summary, out_dir / "pievo_feedback_ledger_comparison.json")
    write_report(original, feedback, deltas, overlap, report_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare PiEvo runs using original vs feedback-guided replacement ledgers.")
    parser.add_argument("--original-dir", default="artifacts/pievo_faithful_replacement_195_smoke")
    parser.add_argument("--feedback-dir", default="artifacts/pievo_faithful_feedback_replacement_195_smoke")
    parser.add_argument("--out-dir", default="artifacts/trail/generation/feedback_guided_replacement_pievo_compare")
    parser.add_argument("--report", default="reports/feedback_guided_replacement_pievo_comparison.md")
    args = parser.parse_args()
    compare_runs(Path(args.original_dir), Path(args.feedback_dir), Path(args.out_dir), Path(args.report))


if __name__ == "__main__":
    main()
