from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from smp02.utils import load_config, load_json, save_json  # noqa: E402
from trail.generation.vae_replacement_strategy import propose_replacements  # noqa: E402


def target_slug(target_tg_c: float) -> str:
    text = f"{float(target_tg_c):.1f}".rstrip("0").rstrip(".")
    return text.replace("-", "minus_").replace(".", "p")


def python_env() -> dict[str, str]:
    env = os.environ.copy()
    src_path = str((REPO_ROOT / "src").resolve())
    root_path = str(REPO_ROOT.resolve())
    existing = env.get("PYTHONPATH", "")
    parts = [src_path, root_path]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def run_command(cmd: list[str], reuse_existing: bool, sentinel: Path) -> None:
    if reuse_existing and sentinel.exists():
        return
    subprocess.run(cmd, check=True, cwd=REPO_ROOT, env=python_env())


def sparse_targets_from_policy(policy_summary: Path, explicit_targets: list[float] | None) -> list[float]:
    if explicit_targets:
        return [float(target) for target in explicit_targets]
    summary = load_json(policy_summary) if policy_summary.exists() else {}
    return [float(target) for target in summary.get("sparse_targets", [])]


def select_target_source_candidates(
    candidates: pd.DataFrame,
    target_tg_c: float,
    target_window_c: float,
    source_top_k: int,
    source_window_c: float,
    high_tg_bias_c: float,
) -> pd.DataFrame:
    required = {
        "smiles_a",
        "smiles_b",
        "groups_a",
        "groups_b",
        "compatibility_reason",
        "ratio_a",
        "ratio_b",
        "predicted_tg",
    }
    missing = sorted(required - set(candidates.columns))
    if missing:
        raise ValueError(f"Candidate table missing required columns: {missing}")
    frame = candidates.copy()
    frame["target_distance"] = (frame["predicted_tg"].astype(float) - float(target_tg_c)).abs()
    frame["in_target_range"] = frame["target_distance"] <= float(target_window_c)
    frame["high_tg_bias_distance"] = (frame["predicted_tg"].astype(float) - (float(target_tg_c) + float(high_tg_bias_c))).abs()
    window = frame[frame["target_distance"] <= float(source_window_c)].copy()
    source = window if len(window) >= int(source_top_k) else frame
    source = source.sort_values(
        ["target_distance", "high_tg_bias_distance", "predicted_tg"],
        ascending=[True, True, False],
    )
    source = source.drop_duplicates(subset=["smiles_a", "smiles_b", "ratio_a", "ratio_b"], keep="first")
    return source.head(int(source_top_k)).drop(columns=["high_tg_bias_distance"]).reset_index(drop=True)


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
    cfg["agent_discovery"]["output_dir"] = f"artifacts/agent_discovery_sparse_target_replacement_{slug}"
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


def summarize_target(target_tg_c: float, source_rows: int, proposal_rows: int, eval_dir: Path, pievo_dir: Path, record_dir: Path) -> dict[str, object]:
    eval_summary = load_json(eval_dir / "replacement_eval_summary.json")
    pievo_summary = load_json(pievo_dir / "pievo_faithful_summary.json")
    record_summary = load_json(record_dir / "generation_record_summary.json")
    external = pievo_summary.get("external_observation_summary", {})
    map_principle = pievo_summary.get("map_principle")
    return {
        "target_tg_c": float(target_tg_c),
        "source_candidate_rows": int(source_rows),
        "replacement_input_proposals": int(proposal_rows),
        "replacement_rebuilt_formulas": int(eval_summary.get("rebuilt_formulas", 0)),
        "replacement_harness_pass": int(eval_summary.get("harness_pass", 0)),
        "replacement_best_distance_c": eval_summary.get("best_distance_c"),
        "replacement_within_1c": int(eval_summary.get("within_1c", 0)),
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
        "generation_record_rows": int(record_summary.get("input_rows", 0)),
        "generation_record_harness_pass": int(record_summary.get("harness_pass_rows", 0)),
        **best_selected_summary(pievo_dir),
    }


def fmt(value: object, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_report(rows: list[dict[str, object]], report_path: Path, output_root: Path, pievo_root: Path, record_root: Path) -> None:
    lines = [
        "# Sparse Target Replacement Expansion",
        "",
        "本文档把 target-conditioned policy 标出的 sparse Tg 目标转成可执行搜索空间扩展。当前仍使用单一小分子 SMILES / MoleCode：先从 `all_ratio_candidates.csv` 中按目标 Tg 重新选择 source candidates，再做 strict functional-group replacement，随后进入 predictor、Harness、PiEvo 和 generation record ledger。",
        "",
        "## Artifacts",
        "",
        f"- Expansion root: `{output_root}`",
        f"- PiEvo output root: `{pievo_root}`",
        f"- Generation record root: `{record_root}`",
        "",
        "## Summary",
        "",
        "| target Tg (C) | source rows | proposals | harness pass | best eval dist (C) | external rows | best selected dist (C) | generation pass | MAP principle |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {float(row['target_tg_c']):.1f} | "
            f"{int(row['source_candidate_rows'])} | "
            f"{int(row['replacement_input_proposals'])} | "
            f"{int(row['replacement_harness_pass'])} | "
            f"{fmt(row['replacement_best_distance_c'])} | "
            f"{int(row['pievo_external_rows'])} | "
            f"{fmt(row['best_selected_target_distance_c'])} | "
            f"{int(row['generation_record_harness_pass'])} | "
            f"{row['pievo_map_principle']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- 这一步不是扩大到商品级组分或聚合物超图；它只是在现有两单体小分子配方表中，为 sparse target 重新选择更贴近目标 Tg 的 source pool。",
            "- 与上一轮 target sweep 相比，关键差别是 source candidates 不再来自 195 C selected candidates，而来自全量 ratio candidate 表中目标 Tg 附近的候选。",
            "- 通过项已写回 generation record ledger，可进入后续 SFT / diffusion-flow seed table；未通过项仍保留在 scored/eval 文件中用于失败回流。",
            "- 这些结果仍是 VAE-WVCM-GPR surrogate + Harness + PiEvo posterior 证据，不是 DSC 真值。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_sparse_expansion(args: argparse.Namespace) -> list[dict[str, object]]:
    targets = sparse_targets_from_policy(Path(args.target_policy_summary), args.targets)
    output_root = Path(args.output_root)
    pievo_root = Path(args.pievo_output_root)
    record_root = Path(args.record_root)
    config_root = output_root / "configs"
    output_root.mkdir(parents=True, exist_ok=True)
    pievo_root.mkdir(parents=True, exist_ok=True)
    record_root.mkdir(parents=True, exist_ok=True)
    if not targets:
        existing_summary = output_root / "sparse_target_replacement_expansion_summary.json"
        if existing_summary.exists() and not args.overwrite_empty:
            rows = load_json(existing_summary)
            return rows if isinstance(rows, list) else []
        save_json([], output_root / "sparse_target_replacement_expansion_summary.json")
        write_report([], Path(args.report), output_root, pievo_root, record_root)
        return []

    all_candidates = pd.read_csv(args.candidates, low_memory=False)
    base_cfg = load_config(args.config)
    rows: list[dict[str, object]] = []
    for target in targets:
        slug = target_slug(float(target))
        target_root = output_root / f"target_{slug}"
        selected_path = target_root / "source_candidates.csv"
        proposals_path = target_root / "sparse_target_replacement_proposals.csv"
        target_root.mkdir(parents=True, exist_ok=True)
        source_candidates = select_target_source_candidates(
            all_candidates,
            float(target),
            float(args.target_window_c),
            int(args.source_top_k),
            float(args.source_window_c),
            float(args.high_tg_bias_c),
        )
        source_candidates.to_csv(selected_path, index=False)
        proposals = propose_replacements(
            selected_path,
            Path(args.groups),
            top_k=int(args.source_top_k),
            per_side=int(args.per_side),
            require_counterpart_compatibility=bool(args.require_counterpart_compatibility),
            component_inventory=None if not args.component_inventory else Path(args.component_inventory),
        )
        proposals.to_csv(proposals_path, index=False)
        eval_dir = target_root / "replacement_eval"
        run_command(
            [
                sys.executable,
                "scripts/evaluate_replacement_proposals.py",
                "--target-tg-c",
                str(float(target)),
                "--target-window-c",
                str(float(args.target_window_c)),
                "--proposals",
                str(proposals_path),
                "--selected",
                str(selected_path),
                "--out-dir",
                str(eval_dir),
                "--report",
                str(target_root / "replacement_evaluation.md"),
            ],
            args.reuse_existing,
            eval_dir / "replacement_eval_summary.json",
        )
        pievo_dir = pievo_root / f"target_{slug}"
        target_config = config_root / f"pievo_sparse_target_replacement_{slug}.yaml"
        write_target_config(
            base_cfg,
            float(target),
            float(args.target_window_c),
            eval_dir / "replacement_observation_ledger.csv",
            pievo_dir,
            target_config,
            int(args.rounds),
            int(args.candidate_batch_size),
            None if int(args.external_limit) < 0 else int(args.external_limit),
        )
        run_command(
            [sys.executable, "-m", "smp02.pievo_faithful", "--config", str(target_config)],
            args.reuse_existing,
            pievo_dir / "pievo_faithful_summary.json",
        )
        record_dir = record_root / f"target_{slug}"
        run_command(
            [
                sys.executable,
                "scripts/import_proposal_eval_generation_records.py",
                "--scored",
                str(eval_dir / "replacement_proposals_scored.csv"),
                "--strategy",
                "functional_group_replacement",
                "--source-context",
                f"sparse_target_replacement_expansion_target_{slug}",
                "--generator-id",
                "sparse_target_replacement_expansion",
                "--target-tg-c",
                str(float(target)),
                "--target-window-c",
                str(float(args.target_window_c)),
                "--out-dir",
                str(record_dir),
                "--report",
                str(Path("reports") / f"sparse_target_replacement_target_{slug}_generation_records.md"),
            ],
            args.reuse_existing,
            record_dir / "generation_record_summary.json",
        )
        rows.append(summarize_target(float(target), len(source_candidates), len(proposals), eval_dir, pievo_dir, record_dir))

    pd.DataFrame(rows).to_csv(output_root / "sparse_target_replacement_expansion_summary.csv", index=False)
    save_json(rows, output_root / "sparse_target_replacement_expansion_summary.json")
    write_report(rows, Path(args.report), output_root, pievo_root, record_root)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand replacement source pools for target-conditioned sparse Tg regions.")
    parser.add_argument("--config", default="configs/pievo_faithful_feedback_replacement_195_smoke.yaml")
    parser.add_argument("--target-policy-summary", default="artifacts/trail/generation_strategy_policy_target_conditioned/target_conditioned_generation_strategy_summary.json")
    parser.add_argument("--targets", nargs="*", type=float, default=None)
    parser.add_argument("--candidates", default="artifacts/reproduce/discovery/all_ratio_candidates.csv")
    parser.add_argument("--groups", default="artifacts/reproduce/discovery/monomer_functional_groups.csv")
    parser.add_argument("--component-inventory", default="artifacts/trail/candidates_expanded/component_inventory.csv")
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--source-window-c", type=float, default=10.0)
    parser.add_argument("--source-top-k", type=int, default=40)
    parser.add_argument("--per-side", type=int, default=4)
    parser.add_argument("--high-tg-bias-c", type=float, default=5.0)
    parser.add_argument("--require-counterpart-compatibility", action="store_true", default=True)
    parser.add_argument("--rounds", type=int, default=6)
    parser.add_argument("--candidate-batch-size", type=int, default=320)
    parser.add_argument("--external-limit", type=int, default=-1)
    parser.add_argument("--output-root", default="artifacts/trail/generation/sparse_target_replacement_expansion")
    parser.add_argument("--pievo-output-root", default="artifacts/pievo_faithful_sparse_target_replacement_expansion")
    parser.add_argument("--record-root", default="artifacts/trail/generation/sparse_target_replacement_records")
    parser.add_argument("--report", default="reports/sparse_target_replacement_expansion.md")
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument(
        "--overwrite-empty",
        action="store_true",
        help="When no sparse target is present, overwrite the summary with an empty result instead of preserving existing expansion evidence.",
    )
    args = parser.parse_args()
    run_sparse_expansion(args)


if __name__ == "__main__":
    main()
