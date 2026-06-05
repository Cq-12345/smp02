from __future__ import annotations

import argparse
import copy
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from smp02.utils import load_config, load_json, save_json


def target_slug(target_tg_c: float) -> str:
    text = f"{float(target_tg_c):.1f}".rstrip("0").rstrip(".")
    return text.replace("-", "minus_").replace(".", "p")


def python_env() -> dict[str, str]:
    env = os.environ.copy()
    src_path = str(Path("src").resolve())
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else src_path + os.pathsep + env["PYTHONPATH"]
    return env


def run_command(cmd: list[str], reuse_existing: bool, sentinel: Path) -> None:
    if reuse_existing and sentinel.exists():
        return
    subprocess.run(cmd, check=True, cwd=Path.cwd(), env=python_env())


def write_target_config(
    base_cfg: dict[str, Any],
    target_tg_c: float,
    target_window_c: float,
    ledger_path: Path,
    pievo_output_dir: Path,
    config_path: Path,
    rounds: int,
    candidate_batch_size: int,
    external_limit: int | None,
) -> None:
    cfg = copy.deepcopy(base_cfg)
    cfg.setdefault("agent_discovery", {})
    cfg.setdefault("pievo_faithful", {})
    slug = target_slug(target_tg_c)
    cfg["agent_discovery"]["target_tg_c"] = float(target_tg_c)
    cfg["agent_discovery"]["target_window_c"] = float(target_window_c)
    cfg["agent_discovery"]["output_dir"] = f"artifacts/agent_discovery_feedback_replacement_target_{slug}"
    cfg["pievo_faithful"]["output_dir"] = str(pievo_output_dir)
    cfg["pievo_faithful"]["rounds"] = int(rounds)
    cfg["pievo_faithful"]["candidate_batch_size"] = int(candidate_batch_size)
    cfg["pievo_faithful"]["target_guard_enabled"] = True
    cfg["pievo_faithful"]["target_guard_max_distance_c"] = float(target_window_c)
    cfg["pievo_faithful"]["external_observation_ledger"] = str(ledger_path)
    cfg["pievo_faithful"]["external_observation_limit"] = external_limit
    cfg["pievo_faithful"]["external_observation_require_pass"] = True
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")


def read_frame(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def best_selected_summary(pievo_dir: Path) -> dict[str, object]:
    selected = read_frame(pievo_dir / "selected_formulations.csv")
    if selected.empty:
        return {
            "best_selected_predicted_tg_mean_c": None,
            "best_selected_target_distance_c": None,
            "best_selected_reward": None,
        }
    row = selected.sort_values("target_distance_c").iloc[0]
    return {
        "best_selected_predicted_tg_mean_c": float(row["predicted_tg_mean_c"]),
        "best_selected_target_distance_c": float(row["target_distance_c"]),
        "best_selected_reward": float(row["environment_reward"]),
    }


def map_principle_posterior(pievo_dir: Path, map_principle: str | None) -> float | None:
    if not map_principle:
        return None
    posterior_path = pievo_dir / "principle_posterior.json"
    if not posterior_path.exists():
        return None
    posterior = load_json(posterior_path)
    return None if map_principle not in posterior else float(posterior[map_principle])


def summarize_target(target_tg_c: float, eval_dir: Path, pievo_dir: Path) -> dict[str, object]:
    eval_summary = load_json(eval_dir / "replacement_eval_summary.json")
    pievo_summary = load_json(pievo_dir / "pievo_faithful_summary.json")
    external = pievo_summary.get("external_observation_summary", {})
    map_principle = pievo_summary.get("map_principle")
    return {
        "target_tg_c": float(target_tg_c),
        "replacement_input_proposals": int(eval_summary.get("input_proposals", 0)),
        "replacement_harness_pass": int(eval_summary.get("harness_pass", 0)),
        "replacement_best_distance_c": eval_summary.get("best_distance_c"),
        "replacement_within_5c": int(eval_summary.get("within_5c", 0)),
        "replacement_observations": int(eval_summary.get("replacement_observations", 0)),
        "pievo_output_dir": str(pievo_dir),
        "pievo_rounds": int(pievo_summary.get("rounds", 0)),
        "pievo_history_rows": int(pievo_summary.get("history_rows", 0)),
        "pievo_external_rows": int(external.get("accepted_rows", 0)),
        "pievo_external_mean_reward": external.get("mean_reward"),
        "pievo_posterior_entropy": float(pievo_summary.get("posterior_entropy", 0.0)),
        "pievo_map_principle": map_principle,
        "pievo_map_principle_posterior": map_principle_posterior(pievo_dir, None if map_principle is None else str(map_principle)),
        "pievo_all_selected_within_guard": bool(pievo_summary.get("all_selected_within_target_guard", False)),
        "pievo_all_selected_pass": bool(pievo_summary.get("validation", {}).get("all_selected_pass", False)),
        **best_selected_summary(pievo_dir),
    }


def fmt(value: object, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_report(rows: list[dict[str, object]], report_path: Path, output_root: Path, pievo_root: Path) -> None:
    lines = [
        "# Feedback-Guided Replacement Target Sweep",
        "",
        "本文档把 feedback-guided strict replacement 从单一 195 C 扩展到多个目标 Tg。每个目标都会重新计算 replacement Harness/observation ledger，再把该 ledger 作为 PiEvo-faithful external history 运行。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM-GPR，不涉及暂缓的商品级组分或聚合物超图表示。",
        "",
        "## Artifacts",
        "",
        f"- Replacement/evaluation root: `{output_root}`",
        f"- PiEvo output root: `{pievo_root}`",
        "",
        "## Summary",
        "",
        "| target Tg (C) | replacement pass | replacement best dist (C) | external rows | PiEvo rounds | best selected Tg (C) | best selected dist (C) | posterior entropy | MAP principle | MAP posterior | pass |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {float(row['target_tg_c']):.1f} | "
            f"{int(row['replacement_harness_pass'])} | "
            f"{fmt(row['replacement_best_distance_c'])} | "
            f"{int(row['pievo_external_rows'])} | "
            f"{int(row['pievo_rounds'])} | "
            f"{fmt(row['best_selected_predicted_tg_mean_c'], 2)} | "
            f"{fmt(row['best_selected_target_distance_c'], 3)} | "
            f"{fmt(row['pievo_posterior_entropy'], 3)} | "
            f"{row['pievo_map_principle']} | "
            f"{fmt(row['pievo_map_principle_posterior'], 3)} | "
            f"{bool(row['pievo_all_selected_pass'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- 这一步检验“真实 Tg 不固定”：replacement 不是只为 195 C 服务，而是对每个目标重新计算 target window、reward 和 PiEvo posterior。",
            "- strict replacement 的互补反应对约束保留在所有目标中；差异来自目标窗口和后续 PiEvo full-history posterior。",
            "- 若某个目标的 replacement pass 很少或为 0，PiEvo 仍可运行，但 posterior 主要来自本轮 surrogate 选择而不是 external replacement history。",
            "- 当前仍是 smoke 规模。若要判断 posterior 收缩是否真正改变 IDS 推荐路径，应继续提高 `rounds`、`candidate_batch_size`，并加入真实 DSC 或高保真 observation。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_sweep(args: argparse.Namespace) -> list[dict[str, object]]:
    output_root = Path(args.output_root)
    pievo_root = Path(args.pievo_output_root)
    config_root = output_root / "configs"
    output_root.mkdir(parents=True, exist_ok=True)
    pievo_root.mkdir(parents=True, exist_ok=True)
    base_cfg = load_config(args.config)
    rows: list[dict[str, object]] = []
    for target in args.targets:
        slug = target_slug(target)
        eval_dir = output_root / f"target_{slug}" / "replacement_eval"
        eval_report = eval_dir / "replacement_evaluation.md"
        eval_summary = eval_dir / "replacement_eval_summary.json"
        run_command(
            [
                sys.executable,
                "scripts/evaluate_replacement_proposals.py",
                "--target-tg-c",
                str(float(target)),
                "--target-window-c",
                str(float(args.target_window_c)),
                "--proposals",
                str(args.proposals),
                "--out-dir",
                str(eval_dir),
                "--report",
                str(eval_report),
            ],
            args.reuse_existing,
            eval_summary,
        )
        pievo_dir = pievo_root / f"target_{slug}"
        target_config = config_root / f"pievo_feedback_replacement_target_{slug}.yaml"
        ledger_path = eval_dir / "replacement_observation_ledger.csv"
        write_target_config(
            base_cfg,
            float(target),
            float(args.target_window_c),
            ledger_path,
            pievo_dir,
            target_config,
            int(args.rounds),
            int(args.candidate_batch_size),
            None if args.external_limit < 0 else int(args.external_limit),
        )
        run_command(
            [sys.executable, "-m", "smp02.pievo_faithful", "--config", str(target_config)],
            args.reuse_existing,
            pievo_dir / "pievo_faithful_summary.json",
        )
        rows.append(summarize_target(float(target), eval_dir, pievo_dir))
    pd.DataFrame(rows).to_csv(output_root / "feedback_replacement_target_sweep_summary.csv", index=False)
    save_json(rows, output_root / "feedback_replacement_target_sweep_summary.json")
    write_report(rows, Path(args.report), output_root, pievo_root)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run feedback-guided replacement evaluation and PiEvo over multiple target Tg values.")
    parser.add_argument("--config", default="configs/pievo_faithful_feedback_replacement_195_smoke.yaml")
    parser.add_argument("--proposals", default="artifacts/trail/generation/feedback_guided_replacement_proposals.csv")
    parser.add_argument("--targets", nargs="+", type=float, default=[190.0, 195.0, 200.0, 250.0])
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--rounds", type=int, default=6)
    parser.add_argument("--candidate-batch-size", type=int, default=260)
    parser.add_argument("--external-limit", type=int, default=-1, help="Negative means no explicit external observation limit.")
    parser.add_argument("--output-root", default="artifacts/trail/generation/feedback_guided_replacement_target_sweep")
    parser.add_argument("--pievo-output-root", default="artifacts/pievo_faithful_feedback_replacement_target_sweep")
    parser.add_argument("--report", default="reports/feedback_guided_replacement_target_sweep.md")
    parser.add_argument("--reuse-existing", action="store_true")
    args = parser.parse_args()
    run_sweep(args)


if __name__ == "__main__":
    main()
