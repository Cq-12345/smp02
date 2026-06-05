from __future__ import annotations

import argparse
import copy
from pathlib import Path

import pandas as pd

from smp02.pievo_faithful import run_pievo_faithful
from smp02.utils import load_config, load_json, resolve_device, save_json, set_seed


def target_slug(target_tg_c: float) -> str:
    text = f"{float(target_tg_c):.1f}".rstrip("0").rstrip(".")
    return text.replace("-", "minus_").replace(".", "p")


def closest_candidate_summary(output_dir: Path) -> dict[str, object]:
    diagnostics_path = output_dir / "candidate_diagnostics.csv"
    if not diagnostics_path.exists():
        return {
            "closest_candidate_predicted_tg_mean_c": None,
            "closest_candidate_target_distance_c": None,
            "closest_candidate_reward": None,
        }
    diagnostics = pd.read_csv(diagnostics_path, low_memory=False)
    if diagnostics.empty:
        return {
            "closest_candidate_predicted_tg_mean_c": None,
            "closest_candidate_target_distance_c": None,
            "closest_candidate_reward": None,
        }
    row = diagnostics.sort_values("target_distance_c").iloc[0]
    return {
        "closest_candidate_predicted_tg_mean_c": float(row["predicted_tg_mean_c"]),
        "closest_candidate_target_distance_c": float(row["target_distance_c"]),
        "closest_candidate_reward": float(row["environment_reward"]),
    }


def run_one_target(base_cfg: dict, target_tg_c: float, output_root: Path, reuse_existing: bool) -> dict[str, object]:
    cfg = copy.deepcopy(base_cfg)
    cfg.setdefault("agent_discovery", {})
    cfg.setdefault("pievo_faithful", {})
    cfg["agent_discovery"]["target_tg_c"] = float(target_tg_c)
    cfg["pievo_faithful"]["output_dir"] = str(output_root / f"target_{target_slug(target_tg_c)}")
    output_dir = Path(cfg["pievo_faithful"]["output_dir"])
    summary_path = output_dir / "pievo_faithful_summary.json"
    selected_path = output_dir / "selected_formulations.csv"
    if not reuse_existing or not summary_path.exists() or not selected_path.exists():
        set_seed(int(cfg.get("seed", 42)))
        device = resolve_device(cfg.get("device", "cuda"))
        selected = run_pievo_faithful(cfg, device)
    else:
        selected = pd.read_csv(selected_path, low_memory=False)
    summary = load_json(summary_path)
    if selected.empty:
        best = {
            "best_selected_predicted_tg_mean_c": None,
            "best_selected_target_distance_c": None,
            "best_selected_reward": None,
        }
    else:
        row = selected.sort_values("target_distance_c").iloc[0]
        best = {
            "best_selected_predicted_tg_mean_c": float(row["predicted_tg_mean_c"]),
            "best_selected_target_distance_c": float(row["target_distance_c"]),
            "best_selected_reward": float(row["environment_reward"]),
        }
    closest = closest_candidate_summary(output_dir)
    return {
        "target_tg_c": float(target_tg_c),
        "output_dir": cfg["pievo_faithful"]["output_dir"],
        "rounds": int(summary.get("rounds", 0)),
        "selected_rows": int(summary.get("selected_rows", 0)),
        "history_rows": int(summary.get("history_rows", summary.get("selected_rows", 0))),
        "map_principle": summary.get("map_principle"),
        "posterior_entropy": float(summary.get("posterior_entropy", 0.0)),
        "all_selected_pass": bool(summary.get("validation", {}).get("all_selected_pass", False)),
        **best,
        **closest,
    }


def write_report(rows: list[dict[str, object]], report_path: Path, base_config: Path) -> None:
    lines = [
        "# PiEvo-Faithful 多目标 Tg Smoke",
        "",
        "本文档回应 TODO 中“真实 Tg 温度不固定”的要求：这里不是对同一个候选池重排序，而是把不同目标 Tg 分别放入 PiEvo-faithful 闭环运行。",
        "",
        f"- Base config: `{base_config}`",
        "",
        "## Summary",
        "",
        "| target Tg (C) | best selected Tg (C) | selected distance (C) | closest candidate Tg (C) | closest distance (C) | MAP principle | pass |",
        "| ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        best_tg = row["best_selected_predicted_tg_mean_c"]
        distance = row["best_selected_target_distance_c"]
        closest_tg = row["closest_candidate_predicted_tg_mean_c"]
        closest_distance = row["closest_candidate_target_distance_c"]
        lines.append(
            f"| {float(row['target_tg_c']):.1f} | "
            f"{'-' if best_tg is None else f'{float(best_tg):.2f}'} | "
            f"{'-' if distance is None else f'{float(distance):.2f}'} | "
            f"{'-' if closest_tg is None else f'{float(closest_tg):.2f}'} | "
            f"{'-' if closest_distance is None else f'{float(closest_distance):.2f}'} | "
            f"{row['map_principle']} | {bool(row['all_selected_pass'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `target_tg_c` 已经是闭环任务参数，不再只是后处理筛选参数。",
            "- 每个目标都拥有独立 output directory、round history、posterior 和 selected formulations。",
            "- `best selected` 表示 IDS/暖启动实际选择并写入 observation history 的最好样本；`closest candidate` 表示该目标运行过程中候选诊断表里最接近目标的样本。",
            "- 如果 `best selected` 明显差于 `closest candidate`，说明短 smoke 的探索策略还没有充分利用近目标候选；正式运行应提高 rounds、降低 warmup 或加入目标命中约束。",
            "- 该 smoke 使用小规模候选批次，适合验证链路；正式运行应提高 `candidate_batch_size` 和 `rounds`。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PiEvo-faithful smoke over multiple target Tg values.")
    parser.add_argument("--config", default="configs/pievo_faithful_smoke.yaml")
    parser.add_argument("--targets", nargs="+", type=float, default=[190.0, 200.0, 250.0])
    parser.add_argument("--output-root", default="artifacts/pievo_faithful_target_sweep_smoke")
    parser.add_argument("--report", default="reports/pievo_target_sweep_smoke.md")
    parser.add_argument("--reuse-existing", action="store_true", help="Reuse existing target output directories when summaries already exist.")
    args = parser.parse_args()
    base_config = Path(args.config)
    base_cfg = load_config(base_config)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    rows = [run_one_target(base_cfg, target, output_root, args.reuse_existing) for target in args.targets]
    df = pd.DataFrame(rows)
    df.to_csv(output_root / "target_sweep_summary.csv", index=False)
    save_json(rows, output_root / "target_sweep_summary.json")
    write_report(rows, Path(args.report), base_config)


if __name__ == "__main__":
    main()
