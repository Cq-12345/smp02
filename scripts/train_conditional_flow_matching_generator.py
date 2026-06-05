from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from trail.generation.import_generation_records import import_generation_records  # noqa: E402
from trail.gnn.train_gnn import formulation_global_features  # noqa: E402


GENERATION_RECORD_COLUMNS = [
    "generation_id",
    "strategy",
    "stage",
    "target_tg_c",
    "target_window_c",
    "candidate_smiles",
    "candidate_ratios",
    "source_context",
    "generator_id",
    "generation_time",
    "prompt_id",
    "prompt_text",
    "prompt_hash",
    "rag_query",
    "rag_context_refs",
    "rag_context_digest",
    "principle_hypothesis",
    "functional_group_plan",
    "candidate_json",
    "compatibility_reasons",
    "predicted_tg_mean_c",
    "predicted_tg_sigma_c",
    "ood_penalty",
    "pievo_round",
    "selected_by_ids",
    "harness_failure_reason",
    "review_status",
    "notes",
]


class ConditionalFlowMatcher(nn.Module):
    def __init__(self, feature_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(feature_dim + 2, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, feature_dim),
        )

    def forward(self, x_t: torch.Tensor, target_condition: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([x_t, target_condition, t], dim=1))


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def stable_id(*parts: object) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"flow_trained_{digest}"


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def as_float(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def parse_ratios(value: object) -> list[float]:
    ratios = [float(part) for part in str(value).split(":") if str(part).strip()]
    total = sum(ratios)
    if not ratios or total <= 0:
        raise ValueError(f"Invalid ratio string: {value}")
    return [ratio / total for ratio in ratios]


def candidate_feature(row: pd.Series) -> np.ndarray:
    smiles = [part.strip() for part in str(row["candidate_smiles"]).split("|") if part.strip()]
    ratios = parse_ratios(row["candidate_ratios"])
    if len(smiles) != len(ratios):
        raise ValueError(f"SMILES count {len(smiles)} != ratio count {len(ratios)}")
    return np.asarray(formulation_global_features(smiles, ratios), dtype=np.float32)


def load_seed_table(path: Path) -> pd.DataFrame:
    table = pd.read_csv(path)
    required = {
        "split",
        "generation_id",
        "strategy",
        "target_tg_c",
        "target_window_c",
        "candidate_smiles",
        "candidate_ratios",
        "predicted_tg_mean_c",
        "target_distance_c",
        "generation_reward",
        "compatibility_reasons",
        "source_ledger",
    }
    missing = sorted(required - set(table.columns))
    if missing:
        raise ValueError(f"Diffusion/flow seed table {path} missing required columns: {missing}")
    table = table.copy()
    for column in [
        "target_tg_c",
        "target_window_c",
        "predicted_tg_mean_c",
        "predicted_tg_sigma_c",
        "target_distance_c",
        "generation_reward",
    ]:
        if column not in table.columns:
            table[column] = 0.0
        table[column] = table[column].map(as_float)
    features = [candidate_feature(row) for _, row in table.iterrows()]
    table["feature_index"] = range(len(table))
    table.attrs["features"] = np.vstack(features).astype(np.float32)
    return table


def standardize(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = values.mean(axis=0)
    std = values.std(axis=0)
    std = np.where(std < 1e-6, 1.0, std)
    return (values - mean) / std, mean, std


def target_stats(targets: np.ndarray) -> tuple[float, float]:
    mean = float(targets.mean())
    std = float(targets.std())
    return mean, max(std, 1.0)


def train_model(
    features_std: np.ndarray,
    target_tg_c: np.ndarray,
    target_mean: float,
    target_std: float,
    epochs: int,
    batch_size: int,
    hidden_dim: int,
    learning_rate: float,
    device: torch.device,
) -> tuple[ConditionalFlowMatcher, list[float]]:
    x1 = torch.tensor(features_std, dtype=torch.float32, device=device)
    cond = torch.tensor(((target_tg_c - target_mean) / target_std).reshape(-1, 1), dtype=torch.float32, device=device)
    model = ConditionalFlowMatcher(feature_dim=x1.shape[1], hidden_dim=hidden_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    losses: list[float] = []
    for _ in range(int(epochs)):
        order = torch.randperm(x1.shape[0], device=device)
        epoch_losses = []
        for start in range(0, x1.shape[0], int(batch_size)):
            index = order[start : start + int(batch_size)]
            target_batch = x1[index]
            cond_batch = cond[index]
            noise = torch.randn_like(target_batch)
            t = torch.rand((target_batch.shape[0], 1), device=device)
            x_t = (1.0 - t) * noise + t * target_batch
            velocity = target_batch - noise
            pred = model(x_t, cond_batch, t)
            loss = torch.mean((pred - velocity) ** 2)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_losses.append(float(loss.detach().cpu()))
        losses.append(float(np.mean(epoch_losses)))
    return model, losses


def flow_matching_eval_loss(
    model: ConditionalFlowMatcher,
    features_std: np.ndarray,
    target_tg_c: np.ndarray,
    target_mean: float,
    target_std: float,
    device: torch.device,
    seed: int,
) -> float | None:
    if len(features_std) == 0:
        return None
    generator = torch.Generator(device=device)
    generator.manual_seed(int(seed))
    model.eval()
    with torch.no_grad():
        x1 = torch.tensor(features_std, dtype=torch.float32, device=device)
        cond = torch.tensor(((target_tg_c - target_mean) / target_std).reshape(-1, 1), dtype=torch.float32, device=device)
        noise = torch.randn(x1.shape, generator=generator, device=device)
        t = torch.rand((x1.shape[0], 1), generator=generator, device=device)
        x_t = (1.0 - t) * noise + t * x1
        velocity = x1 - noise
        pred = model(x_t, cond, t)
        return float(torch.mean((pred - velocity) ** 2).cpu())


def sample_flow(
    model: ConditionalFlowMatcher,
    samples: int,
    feature_dim: int,
    target_tg_c: float,
    target_mean: float,
    target_std: float,
    integration_steps: int,
    device: torch.device,
    seed: int,
) -> np.ndarray:
    generator = torch.Generator(device=device)
    generator.manual_seed(int(seed))
    x = torch.randn((int(samples), int(feature_dim)), generator=generator, device=device)
    cond_value = (float(target_tg_c) - target_mean) / target_std
    cond = torch.full((int(samples), 1), float(cond_value), dtype=torch.float32, device=device)
    model.eval()
    with torch.no_grad():
        for step in range(int(integration_steps)):
            t_value = (step + 0.5) / max(int(integration_steps), 1)
            t = torch.full((int(samples), 1), float(t_value), dtype=torch.float32, device=device)
            x = x + model(x, cond, t) / max(int(integration_steps), 1)
    return x.cpu().numpy().astype(np.float32)


def projection_pool(seed_table: pd.DataFrame, target_tg_c: float, target_window_c: float) -> pd.DataFrame:
    pool = seed_table[seed_table["split"].astype(str) == "train"].copy()
    target_ok = (pool["predicted_tg_mean_c"].astype(float) - float(target_tg_c)).abs() <= float(target_window_c)
    return pool[target_ok].copy() if target_ok.any() else pool


def project_samples(
    generated_std: np.ndarray,
    pool: pd.DataFrame,
    all_features_std: np.ndarray,
    max_records: int,
) -> pd.DataFrame:
    rows = []
    seen: set[tuple[str, str]] = set()
    pool_indices = pool["feature_index"].astype(int).to_numpy()
    pool_features = all_features_std[pool_indices]
    for sample_index, sample in enumerate(generated_std):
        distances = np.linalg.norm(pool_features - sample.reshape(1, -1), axis=1)
        for order_index in np.argsort(distances):
            row = pool.iloc[int(order_index)].copy()
            key = (str(row["candidate_smiles"]), str(row["candidate_ratios"]))
            if key in seen:
                continue
            seen.add(key)
            row["generated_sample_index"] = int(sample_index)
            row["projection_distance"] = float(distances[int(order_index)])
            rows.append(row)
            break
        if len(rows) >= int(max_records):
            break
    return pd.DataFrame(rows)


def record_from_projection(row: pd.Series, args: argparse.Namespace, metrics: dict[str, Any]) -> dict[str, Any]:
    prompt = "\n".join(
        [
            "Conditional flow-matching candidate generation.",
            f"Target Tg condition: {float(args.target_tg_c):.1f} C",
            f"Target window: +/-{float(args.target_window_c):.1f} C",
            "Train a continuous vector field over formulation global features, then project generated features to nearest validated seed record.",
            f"Source seed generation id: {row['generation_id']}",
            f"Source seed strategy: {row['strategy']}",
        ]
    )
    candidate_audit = {
        "generator_mode": "conditional_flow_matching_trained_projection",
        "source_seed_generation_id": str(row["generation_id"]),
        "source_seed_strategy": str(row["strategy"]),
        "source_seed_split": str(row["split"]),
        "source_ledger": str(row.get("source_ledger", "")),
        "generated_sample_index": int(row.get("generated_sample_index", -1)),
        "projection_distance": as_float(row.get("projection_distance")),
        "source_target_distance_c": as_float(row.get("target_distance_c")),
        "source_generation_reward": as_float(row.get("generation_reward")),
        "model_path": str(metrics.get("model_path", "")),
        "train_loss_final": metrics.get("train_loss_final"),
        "eval_loss_final": metrics.get("eval_loss_final"),
    }
    return {
        "generation_id": stable_id(row["generation_id"], row["candidate_smiles"], row["candidate_ratios"], row.get("generated_sample_index", "")),
        "strategy": "diffusion_or_flow_matching",
        "stage": "harnessed",
        "target_tg_c": float(args.target_tg_c),
        "target_window_c": float(args.target_window_c),
        "candidate_smiles": str(row["candidate_smiles"]),
        "candidate_ratios": str(row["candidate_ratios"]),
        "source_context": "conditional_flow_matching_trained_projection",
        "generator_id": "diffusion_or_flow_matching:conditional_flow_matching_mlp_v1",
        "generation_time": str(args.generation_time),
        "prompt_id": "conditional_flow_matching_trained_projection_v1",
        "prompt_text": prompt,
        "prompt_hash": prompt_hash(prompt),
        "rag_query": "",
        "rag_context_refs": str(row.get("source_ledger", "")),
        "rag_context_digest": "Trained conditional flow-matching feature generator projected to a validated seed-table row.",
        "principle_hypothesis": "A conditional flow over formulation descriptors can propose target-window regions, but discrete candidates remain validated by nearest-seed projection and Harness.",
        "functional_group_plan": "",
        "candidate_json": json.dumps(candidate_audit, ensure_ascii=False, sort_keys=True),
        "compatibility_reasons": str(row.get("compatibility_reasons", "")),
        "predicted_tg_mean_c": as_float(row.get("predicted_tg_mean_c")),
        "predicted_tg_sigma_c": as_float(row.get("predicted_tg_sigma_c")),
        "ood_penalty": as_float(row.get("projection_distance")),
        "pievo_round": "",
        "selected_by_ids": False,
        "harness_failure_reason": "",
        "review_status": "needs_review",
        "notes": "Conditional flow-matching MLP trained on seed-table formulation features, then projected to a validated seed row; not real DSC and not direct SMILES generation.",
    }


def write_report(summary: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    lines = [
        "# Conditional Flow-Matching Generator Smoke",
        "",
        "本文档把 diffusion/flow 从 seed replay dry-run 推进一步：在 formulation global feature 空间训练一个轻量条件 flow-matching MLP，然后把连续生成点投影回最近的 validated seed row 并写入 `diffusion_or_flow_matching` generation ledger。",
        "",
        "这仍不是直接 SMILES 扩散生成；它是小分子 SMILES/MoleCode 范围内的训练型原型，用来验证权重训练、采样、离散投影、Harness 和策略回流链路。",
        "",
        "## 输出文件",
        "",
        f"- Input records: `{out_dir / 'flow_matching_generation_records_input.csv'}`",
        f"- Ledger: `{out_dir / 'generation_record_ledger.csv'}`",
        f"- Projection table: `{out_dir / 'nearest_seed_projection.csv'}`",
        f"- Training metrics: `{out_dir / 'flow_matching_training_summary.json'}`",
        f"- Model: `{out_dir / 'conditional_flow_matching_model.pt'}`",
        f"- Report: `{report_path}`",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, dict) or isinstance(value, list):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- flow-matching 训练目标是预测从 Gaussian noise 到 formulation global feature 的 velocity，并以目标 Tg 作为条件。",
            "- 连续生成点不会直接被当成配方；必须投影到最近 validated seed row，随后重新经过 generation record importer 和 Harness。",
            "- 该 smoke 验证的是训练与审计链路，不证明神经 flow 已能产生分布外新 SMILES。后续若要取消 nearest-seed projection，必须新增 SMILES decoder、predictor 和 Harness 复评。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_training(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    set_seed(int(args.seed))
    device = torch.device(args.device)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    seed_table = load_seed_table(Path(args.seed_table))
    all_features = seed_table.attrs["features"]
    train_rows = seed_table[seed_table["split"].astype(str) == "train"].copy()
    eval_rows = seed_table[seed_table["split"].astype(str) == "eval"].copy()
    if train_rows.empty:
        raise ValueError("Diffusion/flow seed table has no train split rows")
    train_features = all_features[train_rows["feature_index"].astype(int).to_numpy()]
    train_features_std, feature_mean, feature_std = standardize(train_features)
    all_features_std = (all_features - feature_mean) / feature_std
    eval_features_std = all_features_std[eval_rows["feature_index"].astype(int).to_numpy()] if not eval_rows.empty else np.zeros((0, train_features.shape[1]), dtype=np.float32)
    target_mean, target_std = target_stats(train_rows["target_tg_c"].astype(float).to_numpy())

    model, train_losses = train_model(
        train_features_std,
        train_rows["target_tg_c"].astype(float).to_numpy(),
        target_mean,
        target_std,
        epochs=args.epochs,
        batch_size=args.batch_size,
        hidden_dim=args.hidden_dim,
        learning_rate=args.learning_rate,
        device=device,
    )
    eval_loss = flow_matching_eval_loss(
        model,
        eval_features_std,
        eval_rows["target_tg_c"].astype(float).to_numpy() if not eval_rows.empty else np.asarray([], dtype=float),
        target_mean,
        target_std,
        device,
        seed=int(args.seed) + 1,
    )

    generated_std = sample_flow(
        model,
        samples=int(args.max_records) * int(args.sample_multiplier),
        feature_dim=train_features.shape[1],
        target_tg_c=float(args.target_tg_c),
        target_mean=target_mean,
        target_std=target_std,
        integration_steps=int(args.integration_steps),
        device=device,
        seed=int(args.seed) + 2,
    )
    pool = projection_pool(seed_table, float(args.target_tg_c), float(args.target_window_c))
    projected = project_samples(generated_std, pool, all_features_std, max_records=int(args.max_records))
    projection_path = out_dir / "nearest_seed_projection.csv"
    projected.to_csv(projection_path, index=False)

    model_path = out_dir / "conditional_flow_matching_model.pt"
    scaler_path = out_dir / "flow_matching_scaler.json"
    torch.save(
        {
            "state_dict": model.state_dict(),
            "feature_dim": int(train_features.shape[1]),
            "hidden_dim": int(args.hidden_dim),
            "target_mean": target_mean,
            "target_std": target_std,
            "feature_mean": feature_mean.tolist(),
            "feature_std": feature_std.tolist(),
        },
        model_path,
    )
    scaler_path.write_text(
        json.dumps(
            {
                "feature_mean": feature_mean.tolist(),
                "feature_std": feature_std.tolist(),
                "target_mean": target_mean,
                "target_std": target_std,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    metrics: dict[str, Any] = {
        "generator_mode": "conditional_flow_matching_trained_projection",
        "seed_table": str(args.seed_table),
        "train_seed_rows": int(len(train_rows)),
        "eval_seed_rows": int(len(eval_rows)),
        "feature_dim": int(train_features.shape[1]),
        "hidden_dim": int(args.hidden_dim),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "learning_rate": float(args.learning_rate),
        "integration_steps": int(args.integration_steps),
        "generated_continuous_samples": int(len(generated_std)),
        "projected_records": int(len(projected)),
        "projection_pool_rows": int(len(pool)),
        "projection_distance_mean": None if projected.empty else float(projected["projection_distance"].mean()),
        "projection_distance_min": None if projected.empty else float(projected["projection_distance"].min()),
        "projection_distance_max": None if projected.empty else float(projected["projection_distance"].max()),
        "train_loss_initial": float(train_losses[0]) if train_losses else None,
        "train_loss_final": float(train_losses[-1]) if train_losses else None,
        "eval_loss_final": eval_loss,
        "model_path": str(model_path),
        "scaler_path": str(scaler_path),
        "projection_path": str(projection_path),
    }
    records = pd.DataFrame(
        [record_from_projection(row, args, metrics) for _, row in projected.iterrows()],
        columns=GENERATION_RECORD_COLUMNS,
    )
    input_path = out_dir / "flow_matching_generation_records_input.csv"
    ledger_path = out_dir / "generation_record_ledger.csv"
    summary_path = out_dir / "generation_record_summary.json"
    training_summary_path = out_dir / "flow_matching_training_summary.json"
    records.to_csv(input_path, index=False)
    ledger, summary = import_generation_records(input_path, Path(args.schema), args.reward_temperature_c)
    ledger.to_csv(ledger_path, index=False)
    summary = summary | metrics | {
        "input_records_path": str(input_path),
        "generation_record_ledger_path": str(ledger_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    training_summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(summary, out_dir, Path(args.report))
    return ledger, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a lightweight conditional flow-matching generator over formulation features.")
    parser.add_argument("--seed-table", default="artifacts/trail/generation/generative_training_sets/diffusion_flow_seed_table.csv")
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--max-records", type=int, default=23)
    parser.add_argument("--sample-multiplier", type=int, default=6)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--integration-steps", type=int, default=24)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--generation-time", default="2026-06-06")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--schema", default="trail/generation/generation_record_schema.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/generation/diffusion_flow_trained_generator")
    parser.add_argument("--report", default="reports/diffusion_flow_trained_generator.md")
    args = parser.parse_args()
    run_training(args)


if __name__ == "__main__":
    main()
