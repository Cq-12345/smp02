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
    cfg["agent_discovery"]["output_dir"] = f"artifacts/agent_discovery_vae_latent_local_search_target_{slug}"
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


def summarize_target(target_tg_c: float, latent_summary: dict[str, Any], eval_dir: Path, pievo_dir: Path) -> dict[str, object]:
    eval_summary = load_json(eval_dir / "replacement_eval_summary.json")
    pievo_summary = load_json(pievo_dir / "pievo_faithful_summary.json")
    external = pievo_summary.get("external_observation_summary", {})
    map_principle = pievo_summary.get("map_principle")
    return {
        "target_tg_c": float(target_tg_c),
        "latent_input_proposals": int(eval_summary.get("input_proposals", 0)),
        "latent_harness_pass": int(eval_summary.get("harness_pass", 0)),
        "latent_best_distance_c": eval_summary.get("best_distance_c"),
        "latent_within_1c": int(eval_summary.get("within_1c", 0)),
        "latent_within_5c": int(eval_summary.get("within_5c", 0)),
        "latent_observations": int(eval_summary.get("replacement_observations", 0)),
        "latent_literature_template_scored": int(eval_summary.get("literature_template_scored", 0)),
        "latent_literature_template_harness_pass": int(eval_summary.get("literature_template_harness_pass", 0)),
        "latent_mean_distance": latent_summary.get("mean_latent_distance"),
        "latent_mean_tanimoto": latent_summary.get("mean_tanimoto"),
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


def aggregate_rows(rows: list[dict[str, object]], output_root: Path, pievo_root: Path) -> dict[str, object]:
    if not rows:
        return {
            "targets": 0,
            "output_root": str(output_root),
            "pievo_output_root": str(pievo_root),
        }
    best = min(
        rows,
        key=lambda row: float("inf") if row.get("best_selected_target_distance_c") is None else float(row["best_selected_target_distance_c"]),
    )
    return {
        "targets": int(len(rows)),
        "target_values": [float(row["target_tg_c"]) for row in rows],
        "output_root": str(output_root),
        "pievo_output_root": str(pievo_root),
        "total_latent_input_proposals": int(sum(int(row["latent_input_proposals"]) for row in rows)),
        "total_latent_harness_pass": int(sum(int(row["latent_harness_pass"]) for row in rows)),
        "total_latent_observations": int(sum(int(row["latent_observations"]) for row in rows)),
        "total_pievo_external_rows": int(sum(int(row["pievo_external_rows"]) for row in rows)),
        "all_pievo_selected_pass": bool(all(bool(row["pievo_all_selected_pass"]) for row in rows)),
        "all_pievo_selected_within_guard": bool(all(bool(row["pievo_all_selected_within_guard"]) for row in rows)),
        "best_target_tg_c": float(best["target_tg_c"]),
        "best_selected_predicted_tg_mean_c": best.get("best_selected_predicted_tg_mean_c"),
        "best_selected_target_distance_c": best.get("best_selected_target_distance_c"),
        "best_target_map_principle": best.get("pievo_map_principle"),
    }


def write_report(rows: list[dict[str, object]], aggregate: dict[str, object], report_path: Path, output_root: Path, pievo_root: Path) -> None:
    lines = [
        "# VAE Latent Local Search Target Sweep",
        "",
        "本文档把 VAE latent local search 从单一 195 C 扩展到多个目标 Tg。latent proposals 保持同一批 VAE-neighborhood 候选；每个目标都会重新计算 predictor/Harness target window、observation ledger reward，并作为 PiEvo-faithful external history 运行。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM-GPR，不涉及暂缓的商品级组分或聚合物超图表示。",
        "",
        "## Artifacts",
        "",
        f"- Latent/evaluation root: `{output_root}`",
        f"- PiEvo output root: `{pievo_root}`",
        "",
        "## Aggregate",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in aggregate.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Target Summary",
            "",
            "| target Tg (C) | latent pass | latent best dist (C) | literature template pass | external rows | PiEvo rounds | best selected Tg (C) | best selected dist (C) | posterior entropy | MAP principle | MAP posterior | pass |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {float(row['target_tg_c']):.1f} | "
            f"{int(row['latent_harness_pass'])} | "
            f"{fmt(row['latent_best_distance_c'])} | "
            f"{int(row['latent_literature_template_harness_pass'])} | "
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
            "- 这一步检验“真实 Tg 不固定”：VAE latent local search 不是只服务 195 C，而是对每个目标重新计算 target window、reward 和 PiEvo posterior。",
            "- latent-neighborhood 排序本身不等于物理规律；它只是给 replacement proposal 提供一个 VAE 表示空间邻域信号，所有结果仍要经过 predictor、Harness、PiEvo 和人工审核。",
            "- 若某个目标的 latent pass 很少，说明同一批 latent proposals 对该目标覆盖不足，下一轮应改变 source candidate pool 或按目标重新运行 latent retrieval。",
            "- 当前是 smoke 规模；后续可以把该 sweep 的失败原因回流给 strategy bandit，或与 Tanimoto replacement、rule-template 和 trained SFT/flow projection 做目标级预算对比。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_sweep(args: argparse.Namespace) -> tuple[list[dict[str, object]], dict[str, object]]:
    output_root = Path(args.output_root)
    pievo_root = Path(args.pievo_output_root)
    config_root = output_root / "configs"
    latent_dir = output_root / "latent_local_search"
    output_root.mkdir(parents=True, exist_ok=True)
    pievo_root.mkdir(parents=True, exist_ok=True)
    latent_dir.mkdir(parents=True, exist_ok=True)
    base_cfg = load_config(args.config)

    latent_proposals = latent_dir / "latent_local_search_proposals.csv"
    latent_summary_path = latent_dir / "latent_local_search_summary.json"
    run_command(
        [
            sys.executable,
            "trail/generation/vae_latent_local_search.py",
            "--top-k",
            str(int(args.latent_top_k)),
            "--per-side",
            str(int(args.latent_per_side)),
            "--out",
            str(latent_proposals),
            "--report",
            str(latent_dir / "vae_latent_local_search.md"),
            *("--require-counterpart-compatibility".split() if args.require_counterpart_compatibility else []),
        ],
        args.reuse_existing,
        latent_summary_path,
    )
    latent_summary = load_json(latent_summary_path)

    rows: list[dict[str, object]] = []
    for target in args.targets:
        slug = target_slug(target)
        eval_dir = output_root / f"target_{slug}" / "latent_eval"
        eval_report = eval_dir / "latent_replacement_evaluation.md"
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
                str(latent_proposals),
                "--out-dir",
                str(eval_dir),
                "--report",
                str(eval_report),
            ],
            args.reuse_existing,
            eval_summary,
        )
        pievo_dir = pievo_root / f"target_{slug}"
        target_config = config_root / f"pievo_vae_latent_local_search_target_{slug}.yaml"
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
        rows.append(summarize_target(float(target), latent_summary, eval_dir, pievo_dir))

    summary_path = output_root / "vae_latent_local_search_target_sweep_summary.csv"
    pd.DataFrame(rows).to_csv(summary_path, index=False)
    save_json(rows, output_root / "vae_latent_local_search_target_sweep_summary.json")
    aggregate = aggregate_rows(rows, output_root, pievo_root)
    save_json(aggregate, output_root / "vae_latent_local_search_target_sweep_aggregate.json")
    write_report(rows, aggregate, Path(args.report), output_root, pievo_root)
    return rows, aggregate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VAE latent local-search evaluation and PiEvo over multiple target Tg values.")
    parser.add_argument("--config", default="configs/pievo_faithful_vae_latent_local_search_195_smoke.yaml")
    parser.add_argument("--targets", nargs="+", type=float, default=[190.0, 195.0, 200.0, 250.0])
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--candidate-batch-size", type=int, default=220)
    parser.add_argument("--external-limit", type=int, default=-1, help="Negative means no explicit external observation limit.")
    parser.add_argument("--latent-top-k", type=int, default=20)
    parser.add_argument("--latent-per-side", type=int, default=5)
    parser.add_argument("--require-counterpart-compatibility", action="store_true", default=True)
    parser.add_argument("--output-root", default="artifacts/trail/generation/vae_latent_local_search_target_sweep")
    parser.add_argument("--pievo-output-root", default="artifacts/pievo_faithful_vae_latent_local_search_target_sweep")
    parser.add_argument("--report", default="reports/vae_latent_local_search_target_sweep.md")
    parser.add_argument("--reuse-existing", action="store_true")
    args = parser.parse_args()
    run_sweep(args)


if __name__ == "__main__":
    main()
