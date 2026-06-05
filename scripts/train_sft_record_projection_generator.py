from __future__ import annotations

import argparse
import hashlib
import json
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


class SFTRecordProjectionRegressor(nn.Module):
    def __init__(self, condition_dim: int, output_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(condition_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, condition: torch.Tensor) -> torch.Tensor:
        return self.net(condition)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def stable_id(*parts: object) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"sft_trained_{digest}"


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


def split_smiles(value: object) -> list[str]:
    smiles = [part.strip() for part in str(value).split("|") if part.strip()]
    if not smiles:
        raise ValueError(f"Invalid SMILES string: {value}")
    return smiles


def candidate_feature(smiles_value: object, ratio_value: object) -> np.ndarray:
    smiles = split_smiles(smiles_value)
    ratios = parse_ratios(ratio_value)
    if len(smiles) != len(ratios):
        raise ValueError(f"SMILES count {len(smiles)} != ratio count {len(ratios)}")
    return np.asarray(formulation_global_features(smiles, ratios), dtype=np.float32)


def extract_line(prompt: str, prefix: str) -> str:
    for line in prompt.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def count_refs(refs: str) -> int:
    return len([part for part in refs.split("|") if part.strip()])


def load_sft_examples(path: Path) -> list[dict[str, Any]]:
    examples = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        messages = item.get("messages", [])
        assistant = next((message for message in messages if message.get("role") == "assistant"), None)
        user = next((message for message in messages if message.get("role") == "user"), None)
        if assistant is None:
            raise ValueError(f"SFT example line {line_number} has no assistant message")
        payload = json.loads(str(assistant["content"]))
        metadata = dict(item.get("metadata", {}))
        metadata["line_number"] = line_number
        examples.append(
            {
                "payload": payload,
                "metadata": metadata,
                "user_prompt": "" if user is None else str(user.get("content", "")),
            }
        )
    return examples


def build_training_table(examples: list[dict[str, Any]]) -> tuple[pd.DataFrame, np.ndarray]:
    rows = []
    formulation_features = []
    for example in examples:
        payload = dict(example["payload"])
        metadata = dict(example["metadata"])
        user_prompt = str(example.get("user_prompt", ""))
        smiles = str(payload.get("candidate_smiles", ""))
        ratios = str(payload.get("candidate_ratios", ""))
        features = candidate_feature(smiles, ratios)
        rag_refs = extract_line(user_prompt, "RAG refs:")
        rag_digest = extract_line(user_prompt, "RAG digest:")
        rows.append(
            {
                "split": str(metadata.get("split", "")),
                "line_number": int(metadata.get("line_number", 0) or 0),
                "generation_id": str(metadata.get("generation_id", "")),
                "source_strategy": str(metadata.get("strategy", payload.get("strategy", ""))),
                "source_ledger": str(metadata.get("source_ledger", "")),
                "target_tg_c": as_float(payload.get("target_tg_c")),
                "target_window_c": as_float(payload.get("target_window_c")),
                "predicted_tg_mean_c": as_float(payload.get("predicted_tg_mean_c")),
                "predicted_tg_sigma_c": as_float(payload.get("predicted_tg_sigma_c")),
                "ood_penalty": as_float(payload.get("ood_penalty")),
                "target_distance_c": as_float(metadata.get("target_distance_c")),
                "generation_reward": as_float(metadata.get("generation_reward")),
                "candidate_smiles": smiles,
                "candidate_ratios": ratios,
                "principle_hypothesis": str(payload.get("principle_hypothesis", "")),
                "functional_group_plan": str(payload.get("functional_group_plan", "")),
                "compatibility_reasons": str(payload.get("compatibility_reasons", "")),
                "source_candidate_json": payload.get("candidate_json", ""),
                "user_prompt": user_prompt,
                "rag_context_refs": rag_refs,
                "rag_context_digest": rag_digest,
                "prompt_length": len(user_prompt),
                "rag_ref_count": count_refs(rag_refs),
                "rag_digest_length": len(rag_digest),
            }
        )
        formulation_features.append(features)
    table = pd.DataFrame(rows)
    if table.empty:
        raise ValueError("SFT JSONL has no usable examples")
    table["feature_index"] = range(len(table))
    return table, np.vstack(formulation_features).astype(np.float32)


def one_hot(value: str, vocab: list[str]) -> list[float]:
    return [1.0 if value == item else 0.0 for item in vocab]


def condition_matrix(table: pd.DataFrame, strategy_vocab: list[str]) -> np.ndarray:
    rows = []
    for _, row in table.iterrows():
        rows.append(
            [
                as_float(row["target_tg_c"]),
                as_float(row["target_window_c"]),
                as_float(row["target_distance_c"]),
                as_float(row["generation_reward"]),
                min(as_float(row["prompt_length"]) / 2000.0, 2.0),
                min(as_float(row["rag_ref_count"]) / 10.0, 2.0),
                min(as_float(row["rag_digest_length"]) / 2000.0, 2.0),
            ]
            + one_hot(str(row["source_strategy"]), strategy_vocab)
        )
    return np.asarray(rows, dtype=np.float32)


def output_matrix(table: pd.DataFrame, formulation_features: np.ndarray, strategy_vocab: list[str]) -> np.ndarray:
    rows = []
    for _, row in table.iterrows():
        feature = formulation_features[int(row["feature_index"])]
        rows.append(
            np.concatenate(
                [
                    feature,
                    np.asarray(
                        [
                            as_float(row["predicted_tg_mean_c"]),
                            as_float(row["predicted_tg_sigma_c"]),
                            as_float(row["ood_penalty"]),
                            as_float(row["target_distance_c"]),
                            as_float(row["generation_reward"]),
                        ],
                        dtype=np.float32,
                    ),
                    np.asarray(one_hot(str(row["source_strategy"]), strategy_vocab), dtype=np.float32),
                ]
            )
        )
    return np.vstack(rows).astype(np.float32)


def standardize(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = values.mean(axis=0)
    std = values.std(axis=0)
    std = np.where(std < 1e-6, 1.0, std)
    return (values - mean) / std, mean, std


def apply_standardize(values: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return (values - mean) / std


def train_model(
    condition_std: np.ndarray,
    output_std: np.ndarray,
    epochs: int,
    batch_size: int,
    hidden_dim: int,
    learning_rate: float,
    device: torch.device,
) -> tuple[SFTRecordProjectionRegressor, list[float]]:
    x = torch.tensor(condition_std, dtype=torch.float32, device=device)
    y = torch.tensor(output_std, dtype=torch.float32, device=device)
    model = SFTRecordProjectionRegressor(condition_dim=x.shape[1], output_dim=y.shape[1], hidden_dim=hidden_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    losses: list[float] = []
    for _ in range(int(epochs)):
        order = torch.randperm(x.shape[0], device=device)
        epoch_losses = []
        for start in range(0, x.shape[0], int(batch_size)):
            index = order[start : start + int(batch_size)]
            pred = model(x[index])
            loss = torch.mean((pred - y[index]) ** 2)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_losses.append(float(loss.detach().cpu()))
        losses.append(float(np.mean(epoch_losses)))
    return model, losses


def eval_loss(model: SFTRecordProjectionRegressor, condition_std: np.ndarray, output_std: np.ndarray, device: torch.device) -> float | None:
    if len(condition_std) == 0:
        return None
    model.eval()
    with torch.no_grad():
        x = torch.tensor(condition_std, dtype=torch.float32, device=device)
        y = torch.tensor(output_std, dtype=torch.float32, device=device)
        pred = model(x)
        return float(torch.mean((pred - y) ** 2).cpu())


def target_projection_pool(table: pd.DataFrame, target_tg_c: float, target_window_c: float) -> pd.DataFrame:
    pool = table[table["split"].astype(str) == "train"].copy()
    target_ok = (pool["predicted_tg_mean_c"].astype(float) - float(target_tg_c)).abs() <= float(target_window_c)
    return pool[target_ok].copy() if target_ok.any() else pool


def generated_condition_matrix(
    train_rows: pd.DataFrame,
    strategy_vocab: list[str],
    target_tg_c: float,
    target_window_c: float,
    samples: int,
) -> tuple[np.ndarray, list[int]]:
    ranked = train_rows.sort_values(["target_distance_c", "generation_reward", "generation_id"], ascending=[True, False, True]).reset_index(drop=True)
    rows = []
    source_indices = []
    for sample_index in range(int(samples)):
        source = ranked.iloc[sample_index % len(ranked)].copy()
        source["target_tg_c"] = float(target_tg_c)
        source["target_window_c"] = float(target_window_c)
        rows.append(source)
        source_indices.append(int(source["feature_index"]))
    return condition_matrix(pd.DataFrame(rows), strategy_vocab), source_indices


def predict_outputs(
    model: SFTRecordProjectionRegressor,
    condition_raw: np.ndarray,
    condition_mean: np.ndarray,
    condition_std: np.ndarray,
    condition_noise_std: float,
    device: torch.device,
    seed: int,
) -> np.ndarray:
    generator = torch.Generator(device=device)
    generator.manual_seed(int(seed))
    x = torch.tensor(apply_standardize(condition_raw, condition_mean, condition_std), dtype=torch.float32, device=device)
    if float(condition_noise_std) > 0:
        x = x + torch.randn(x.shape, generator=generator, device=device) * float(condition_noise_std)
    model.eval()
    with torch.no_grad():
        return model(x).cpu().numpy().astype(np.float32)


def project_predictions(
    predicted_output_std: np.ndarray,
    pool: pd.DataFrame,
    all_output_std: np.ndarray,
    source_condition_indices: list[int],
    max_records: int,
) -> pd.DataFrame:
    rows = []
    seen: set[tuple[str, str]] = set()
    pool_indices = pool["feature_index"].astype(int).to_numpy()
    pool_features = all_output_std[pool_indices]
    for sample_index, sample in enumerate(predicted_output_std):
        distances = np.linalg.norm(pool_features - sample.reshape(1, -1), axis=1)
        for order_index in np.argsort(distances):
            row = pool.iloc[int(order_index)].copy()
            key = (str(row["candidate_smiles"]), str(row["candidate_ratios"]))
            if key in seen:
                continue
            seen.add(key)
            row["generated_condition_index"] = int(sample_index)
            row["source_condition_feature_index"] = int(source_condition_indices[sample_index])
            row["projection_distance"] = float(distances[int(order_index)])
            rows.append(row)
            break
        if len(rows) >= int(max_records):
            break
    return pd.DataFrame(rows)


def record_from_projection(row: pd.Series, args: argparse.Namespace, metrics: dict[str, Any]) -> dict[str, Any]:
    prompt = "\n".join(
        [
            "Supervised SFT-style candidate generation.",
            f"Target Tg condition: {float(args.target_tg_c):.1f} C",
            f"Target window: +/-{float(args.target_window_c):.1f} C",
            "Train a neural regressor from SFT prompt/source features to structured generation-record features, then project to a validated train-split record.",
            f"Source SFT generation id: {row['generation_id']}",
            f"Source strategy: {row['source_strategy']}",
        ]
    )
    source_candidate_json = row.get("source_candidate_json", "")
    if not isinstance(source_candidate_json, str):
        source_candidate_json = json.dumps(source_candidate_json, ensure_ascii=False, sort_keys=True)
    candidate_audit = {
        "generator_mode": "supervised_neural_sft_projection",
        "not_llm_weight_update": True,
        "training_target": "structured_generation_record_feature_projection",
        "source_sft_generation_id": str(row["generation_id"]),
        "source_sft_strategy": str(row["source_strategy"]),
        "source_sft_split": str(row["split"]),
        "source_ledger": str(row.get("source_ledger", "")),
        "source_line_number": int(row.get("line_number", 0) or 0),
        "generated_condition_index": int(row.get("generated_condition_index", -1)),
        "source_condition_feature_index": int(row.get("source_condition_feature_index", -1)),
        "projection_distance": as_float(row.get("projection_distance")),
        "source_target_distance_c": as_float(row.get("target_distance_c")),
        "source_generation_reward": as_float(row.get("generation_reward")),
        "source_candidate_json": source_candidate_json,
        "model_path": str(metrics.get("model_path", "")),
        "train_loss_final": metrics.get("train_loss_final"),
        "eval_loss_final": metrics.get("eval_loss_final"),
    }
    return {
        "generation_id": stable_id(row["generation_id"], row["candidate_smiles"], row["candidate_ratios"], row.get("generated_condition_index", "")),
        "strategy": "sft_candidate_generator",
        "stage": "harnessed",
        "target_tg_c": float(args.target_tg_c),
        "target_window_c": float(args.target_window_c),
        "candidate_smiles": str(row["candidate_smiles"]),
        "candidate_ratios": str(row["candidate_ratios"]),
        "source_context": "supervised_neural_sft_projection",
        "generator_id": "sft_candidate_generator:structured_projection_mlp_v1",
        "generation_time": str(args.generation_time),
        "prompt_id": "supervised_neural_sft_projection_v1",
        "prompt_text": prompt,
        "prompt_hash": prompt_hash(prompt),
        "rag_query": "",
        "rag_context_refs": str(row.get("rag_context_refs", "")),
        "rag_context_digest": "Trained supervised projection over SFT generation-record features, then projected to a validated train-split record.",
        "principle_hypothesis": str(row.get("principle_hypothesis", "")),
        "functional_group_plan": str(row.get("functional_group_plan", "")),
        "candidate_json": json.dumps(candidate_audit, ensure_ascii=False, sort_keys=True),
        "compatibility_reasons": str(row.get("compatibility_reasons", "")),
        "predicted_tg_mean_c": as_float(row.get("predicted_tg_mean_c")),
        "predicted_tg_sigma_c": as_float(row.get("predicted_tg_sigma_c")),
        "ood_penalty": as_float(row.get("projection_distance")),
        "pievo_round": "",
        "selected_by_ids": False,
        "harness_failure_reason": "",
        "review_status": "needs_review",
        "notes": "Neural SFT-style projection trained on structured generation records, then projected to a validated train row; not real DSC and not external LLM fine-tuning.",
    }


def heldout_eval_table(table: pd.DataFrame, prototypes: pd.DataFrame) -> pd.DataFrame:
    eval_rows = table[table["split"].astype(str) == "eval"].copy()
    if eval_rows.empty:
        return pd.DataFrame(
            columns=[
                "eval_generation_id",
                "eval_candidate_smiles",
                "eval_candidate_ratios",
                "nearest_generated_id",
                "nearest_generated_distance_c",
                "exact_candidate_match",
            ]
        )
    generated = prototypes.copy()
    generated["target_distance_c"] = (generated["predicted_tg_mean_c"].astype(float) - generated["target_tg_c"].astype(float)).abs()
    rows = []
    for _, row in eval_rows.iterrows():
        exact = generated[(generated["candidate_smiles"] == row["candidate_smiles"]) & (generated["candidate_ratios"] == row["candidate_ratios"])]
        if exact.empty:
            nearest = generated.sort_values("target_distance_c").iloc[0] if not generated.empty else pd.Series()
        else:
            nearest = exact.iloc[0]
        rows.append(
            {
                "eval_generation_id": row["generation_id"],
                "eval_candidate_smiles": row["candidate_smiles"],
                "eval_candidate_ratios": row["candidate_ratios"],
                "nearest_generated_id": "" if nearest.empty else nearest["generation_id"],
                "nearest_generated_distance_c": None if nearest.empty else float(nearest["target_distance_c"]),
                "exact_candidate_match": bool(not exact.empty),
            }
        )
    return pd.DataFrame(rows)


def write_report(summary: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    lines = [
        "# Supervised SFT Projection Generator Smoke",
        "",
        "本文档把 SFT 从 prototype replay dry-run 推进一步：在 SFT generation record 的结构化特征空间训练一个轻量监督 MLP，再把模型输出投影回最近的 validated train-split record，并写入 `sft_candidate_generator` generation ledger。",
        "",
        "这不是外部 LLM 微调，也不是自由 SMILES 生成；它验证的是 SFT 语料、神经权重训练、结构化投影、Harness 和策略回流链路。",
        "",
        "## 输出文件",
        "",
        f"- Input records: `{out_dir / 'sft_projection_generation_records_input.csv'}`",
        f"- Ledger: `{out_dir / 'generation_record_ledger.csv'}`",
        f"- Projection table: `{out_dir / 'nearest_sft_record_projection.csv'}`",
        f"- Training metrics: `{out_dir / 'sft_projection_training_summary.json'}`",
        f"- Model: `{out_dir / 'sft_record_projection_model.pt'}`",
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
            "- 训练输入是 SFT prompt/source 条件特征；训练输出是候选配方的 formulation global features、预测 Tg、reward 和来源策略特征。",
            "- 连续模型输出不会直接被当成配方；必须投影到最近 validated train-split record，随后重新经过 generation record importer 和 Harness。",
            "- 该 smoke 验证的是有权重更新的 SFT-style 训练链路，不证明 LLM 已完成微调，也不证明模型能分布外创造新 SMILES。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_training(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    set_seed(int(args.seed))
    device = torch.device(args.device)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    examples = load_sft_examples(Path(args.sft_jsonl))
    table, formulation_features = build_training_table(examples)
    train_rows = table[table["split"].astype(str) == "train"].copy()
    eval_rows = table[table["split"].astype(str) == "eval"].copy()
    if train_rows.empty:
        raise ValueError("SFT JSONL has no train split examples")
    strategy_vocab = sorted({str(value) for value in table["source_strategy"].dropna().unique()})

    all_condition = condition_matrix(table, strategy_vocab)
    all_output = output_matrix(table, formulation_features, strategy_vocab)
    train_indices = train_rows["feature_index"].astype(int).to_numpy()
    eval_indices = eval_rows["feature_index"].astype(int).to_numpy()
    train_condition = all_condition[train_indices]
    train_output = all_output[train_indices]
    train_condition_std, condition_mean, condition_std = standardize(train_condition)
    train_output_std, output_mean, output_std = standardize(train_output)
    all_output_std = apply_standardize(all_output, output_mean, output_std)
    eval_condition_std = apply_standardize(all_condition[eval_indices], condition_mean, condition_std) if len(eval_indices) else np.zeros((0, train_condition.shape[1]), dtype=np.float32)
    eval_output_std = apply_standardize(all_output[eval_indices], output_mean, output_std) if len(eval_indices) else np.zeros((0, train_output.shape[1]), dtype=np.float32)

    model, train_losses = train_model(
        train_condition_std,
        train_output_std,
        epochs=args.epochs,
        batch_size=args.batch_size,
        hidden_dim=args.hidden_dim,
        learning_rate=args.learning_rate,
        device=device,
    )
    final_eval_loss = eval_loss(model, eval_condition_std, eval_output_std, device)

    generated_conditions, source_condition_indices = generated_condition_matrix(
        train_rows,
        strategy_vocab,
        target_tg_c=float(args.target_tg_c),
        target_window_c=float(args.target_window_c),
        samples=int(args.max_records) * int(args.sample_multiplier),
    )
    predicted_outputs = predict_outputs(
        model,
        generated_conditions,
        condition_mean,
        condition_std,
        condition_noise_std=float(args.condition_noise_std),
        device=device,
        seed=int(args.seed) + 1,
    )
    pool = target_projection_pool(table, float(args.target_tg_c), float(args.target_window_c))
    projected = project_predictions(
        predicted_outputs,
        pool,
        all_output_std,
        source_condition_indices=source_condition_indices,
        max_records=int(args.max_records),
    )
    projection_path = out_dir / "nearest_sft_record_projection.csv"
    projected.to_csv(projection_path, index=False)

    model_path = out_dir / "sft_record_projection_model.pt"
    scaler_path = out_dir / "sft_projection_scaler.json"
    torch.save(
        {
            "state_dict": model.state_dict(),
            "condition_dim": int(train_condition.shape[1]),
            "output_dim": int(train_output.shape[1]),
            "hidden_dim": int(args.hidden_dim),
            "strategy_vocab": strategy_vocab,
            "condition_mean": condition_mean.tolist(),
            "condition_std": condition_std.tolist(),
            "output_mean": output_mean.tolist(),
            "output_std": output_std.tolist(),
        },
        model_path,
    )
    scaler_path.write_text(
        json.dumps(
            {
                "strategy_vocab": strategy_vocab,
                "condition_mean": condition_mean.tolist(),
                "condition_std": condition_std.tolist(),
                "output_mean": output_mean.tolist(),
                "output_std": output_std.tolist(),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    metrics: dict[str, Any] = {
        "generator_mode": "supervised_neural_sft_projection",
        "sft_jsonl": str(args.sft_jsonl),
        "train_examples": int(len(train_rows)),
        "eval_examples": int(len(eval_rows)),
        "condition_dim": int(train_condition.shape[1]),
        "output_dim": int(train_output.shape[1]),
        "hidden_dim": int(args.hidden_dim),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "learning_rate": float(args.learning_rate),
        "condition_noise_std": float(args.condition_noise_std),
        "generated_continuous_outputs": int(len(predicted_outputs)),
        "projected_records": int(len(projected)),
        "projection_pool_rows": int(len(pool)),
        "projection_distance_mean": None if projected.empty else float(projected["projection_distance"].mean()),
        "projection_distance_min": None if projected.empty else float(projected["projection_distance"].min()),
        "projection_distance_max": None if projected.empty else float(projected["projection_distance"].max()),
        "train_loss_initial": float(train_losses[0]) if train_losses else None,
        "train_loss_final": float(train_losses[-1]) if train_losses else None,
        "eval_loss_final": final_eval_loss,
        "model_path": str(model_path),
        "scaler_path": str(scaler_path),
        "projection_path": str(projection_path),
    }
    records = pd.DataFrame(
        [record_from_projection(row, args, metrics) for _, row in projected.iterrows()],
        columns=GENERATION_RECORD_COLUMNS,
    )
    input_path = out_dir / "sft_projection_generation_records_input.csv"
    ledger_path = out_dir / "generation_record_ledger.csv"
    summary_path = out_dir / "generation_record_summary.json"
    training_summary_path = out_dir / "sft_projection_training_summary.json"
    heldout_path = out_dir / "heldout_eval_retrieval.csv"
    records.to_csv(input_path, index=False)
    ledger, summary = import_generation_records(input_path, Path(args.schema), args.reward_temperature_c)
    ledger.to_csv(ledger_path, index=False)
    heldout = heldout_eval_table(table, records)
    heldout.to_csv(heldout_path, index=False)
    summary = summary | metrics | {
        "generated_records": int(len(records)),
        "heldout_exact_candidate_matches": int(heldout["exact_candidate_match"].sum()) if not heldout.empty else 0,
        "heldout_eval_rows": int(len(heldout)),
        "input_records_path": str(input_path),
        "generation_record_ledger_path": str(ledger_path),
        "heldout_eval_retrieval_path": str(heldout_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    training_summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(summary, out_dir, Path(args.report))
    return ledger, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a lightweight supervised SFT-style projection generator over generation-record features.")
    parser.add_argument("--sft-jsonl", default="artifacts/trail/generation/generative_training_sets/sft_generation_records.jsonl")
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--max-records", type=int, default=23)
    parser.add_argument("--sample-multiplier", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--condition-noise-std", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--generation-time", default="2026-06-06")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--schema", default="trail/generation/generation_record_schema.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/generation/sft_trained_projection_generator")
    parser.add_argument("--report", default="reports/sft_trained_projection_generator.md")
    args = parser.parse_args()
    run_training(args)


if __name__ == "__main__":
    main()
