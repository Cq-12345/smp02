from __future__ import annotations

import argparse
import math
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.exceptions import ConvergenceWarning

from smp02.agent_discovery import (
    AgentConfig,
    FormulaCandidate,
    Principle,
    build_monomer_pool,
    encode_pool,
    evaluate_formulas,
    fingerprint_diversity,
    formula_key,
    initial_principles,
    load_charset_meta,
    monomer_pool_frame,
    ood_reference_scale,
    parse_agent_config,
    random_formulas,
    safe_slug,
    systematic_pair_formulas,
    validate_formula_frame,
)
from smp02.predictors import load_predictor
from smp02.utils import ensure_dir, load_config, resolve_device, save_json, set_seed


@dataclass
class PiEvoFaithfulConfig:
    output_dir: Path
    rounds: int
    candidate_batch_size: int
    warmup_rounds: int
    observation_noise: float
    anomaly_threshold: float
    anomaly_min_count: int
    ids_mc_samples: int
    ids_epsilon: float
    reward_temperature_c: float
    max_added_principles: int
    random_seed: int


@dataclass
class Observation:
    round_index: int
    hypothesis_key: str
    row: dict[str, object]
    reward: float
    predicted_tg_mean_c: float
    predicted_tg_sigma_c: float


@dataclass
class Anomaly:
    hypothesis_key: str
    principle: str
    expected_reward: float
    observed_reward: float
    surprisal: float
    predicted_tg_mean_c: float
    target_distance_c: float


class PrincipleGPExpert:
    def __init__(self, principle_id: str, seed: int) -> None:
        self.principle_id = principle_id
        self.seed = seed
        self.model: GaussianProcessRegressor | None = None
        self.y_mean = 0.5
        self.y_var = 1.0
        self.n_observations = 0

    def fit(self, x: np.ndarray, y: np.ndarray) -> None:
        self.n_observations = int(len(y))
        if len(y) == 0:
            self.model = None
            self.y_mean = 0.5
            self.y_var = 1.0
            return
        self.y_mean = float(np.mean(y))
        self.y_var = float(max(np.var(y), 1e-4))
        if len(y) < 2:
            self.model = None
            return
        kernel = ConstantKernel(1.0, (1e-3, 1e3)) * RBF(length_scale=np.ones(x.shape[1]), length_scale_bounds=(1e-3, 1e3))
        kernel += WhiteKernel(noise_level=1e-3, noise_level_bounds=(1e-6, 1e-1))
        self.model = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            normalize_y=True,
            random_state=self.seed,
            n_restarts_optimizer=0,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            self.model.fit(x, y)

    def predict(self, x: np.ndarray) -> tuple[float, float]:
        if x.ndim == 1:
            x = x.reshape(1, -1)
        if self.model is None:
            return self.y_mean, self.y_var + 0.25
        mean, std = self.model.predict(x, return_std=True)
        return float(mean[0]), float(max(std[0] ** 2, 1e-8))


def parse_pievo_faithful_config(cfg: dict, agent_cfg: AgentConfig) -> PiEvoFaithfulConfig:
    raw = cfg.get("pievo_faithful", {})
    default_out = agent_cfg.output_dir.parent / f"{agent_cfg.output_dir.name}_pievo_faithful"
    return PiEvoFaithfulConfig(
        output_dir=Path(raw.get("output_dir", default_out)),
        rounds=int(raw.get("rounds", 12)),
        candidate_batch_size=int(raw.get("candidate_batch_size", min(agent_cfg.samples_per_iteration, 3000))),
        warmup_rounds=int(raw.get("warmup_rounds", 3)),
        observation_noise=float(raw.get("observation_noise", 0.08)),
        anomaly_threshold=float(raw.get("anomaly_threshold", 0.75)),
        anomaly_min_count=int(raw.get("anomaly_min_count", 2)),
        ids_mc_samples=int(raw.get("ids_mc_samples", 48)),
        ids_epsilon=float(raw.get("ids_epsilon", 1e-6)),
        reward_temperature_c=float(raw.get("reward_temperature_c", max(agent_cfg.target_window_c, 1.0))),
        max_added_principles=int(raw.get("max_added_principles", 6)),
        random_seed=int(raw.get("random_seed", cfg.get("seed", 42))),
    )


def target_reward(predicted_tg_c: float, target_tg_c: float, reward_temperature_c: float) -> float:
    scale = max(float(reward_temperature_c), 1e-6)
    return float(math.exp(-abs(float(predicted_tg_c) - float(target_tg_c)) / scale))


def gaussian_likelihood(y: float, mean: float, variance: float) -> float:
    var = max(float(variance), 1e-10)
    exponent = -0.5 * ((float(y) - float(mean)) ** 2) / var
    return float(max((1.0 / math.sqrt(2.0 * math.pi * var)) * math.exp(exponent), 1e-300))


def normalize_log_weights(log_weights: dict[str, float]) -> dict[str, float]:
    if not log_weights:
        return {}
    max_log = max(log_weights.values())
    weights = {key: math.exp(value - max_log) for key, value in log_weights.items()}
    total = sum(weights.values())
    if total <= 0.0 or not math.isfinite(total):
        uniform = 1.0 / len(weights)
        return {key: uniform for key in weights}
    return {key: value / total for key, value in weights.items()}


def entropy(probs: dict[str, float]) -> float:
    return float(-sum(p * math.log(max(p, 1e-12)) for p in probs.values() if p > 0.0))


def surprisal_score(y: float, mean: float, model_variance: float, observation_noise: float) -> float:
    total_variance = max(float(model_variance) + float(observation_noise) ** 2, 1e-10)
    normalized_error = ((float(y) - float(mean)) ** 2) / total_variance
    return float(1.0 - math.exp(-math.sqrt(normalized_error)))


def row_bool(row: dict[str, object], name: str) -> bool:
    value = row.get(f"feature_{name}", False)
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes"}
    return bool(value)


def principle_feature_vector(row: dict[str, object], principle: Principle, agent_cfg: AgentConfig, pievo_cfg: PiEvoFaithfulConfig) -> np.ndarray:
    aligned = 1.0 if row_bool(row, principle.feature) else 0.0
    target_distance = float(row.get("target_distance_c", agent_cfg.target_window_c * 10.0))
    target_proximity = target_reward(
        float(row.get("predicted_tg_mean_c", agent_cfg.target_tg_c)),
        agent_cfg.target_tg_c,
        pievo_cfg.reward_temperature_c,
    )
    return np.asarray(
        [
            aligned,
            principle.effect * aligned,
            float(row.get("prior_score", 0.0)),
            float(row.get("ood_penalty", 0.0)),
            float(row.get("predicted_tg_sigma_c", 0.0)) / 100.0,
            float(row.get("n_components", 1.0)) / max(agent_cfg.max_components, 1),
            float(row.get("new_component_count", 0.0)) / max(agent_cfg.max_components, 1),
            target_distance / max(pievo_cfg.reward_temperature_c, 1e-6),
            target_proximity,
        ],
        dtype=float,
    )


def initial_priors(principles: list[Principle]) -> dict[str, float]:
    if not principles:
        return {}
    mass = 1.0 / len(principles)
    return {p.name: mass for p in principles}


def train_principle_experts(
    principles: list[Principle],
    history: list[Observation],
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
) -> dict[str, PrincipleGPExpert]:
    experts: dict[str, PrincipleGPExpert] = {}
    y = np.asarray([obs.reward for obs in history], dtype=float)
    for principle in principles:
        expert = PrincipleGPExpert(principle.name, pievo_cfg.random_seed)
        if history:
            x = np.vstack([principle_feature_vector(obs.row, principle, agent_cfg, pievo_cfg) for obs in history])
        else:
            x = np.empty((0, 9), dtype=float)
        expert.fit(x, y)
        experts[principle.name] = expert
    return experts


def sequential_predictive_log_likelihood(
    principle: Principle,
    history: list[Observation],
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
) -> float:
    logp = 0.0
    prior_x: list[np.ndarray] = []
    prior_y: list[float] = []
    for obs in history:
        expert = PrincipleGPExpert(principle.name, pievo_cfg.random_seed)
        if prior_y:
            expert.fit(np.vstack(prior_x), np.asarray(prior_y, dtype=float))
        else:
            expert.fit(np.empty((0, 9), dtype=float), np.empty(0, dtype=float))
        x_obs = principle_feature_vector(obs.row, principle, agent_cfg, pievo_cfg)
        mean, variance = expert.predict(x_obs)
        logp += math.log(gaussian_likelihood(obs.reward, mean, variance + pievo_cfg.observation_noise**2))
        prior_x.append(x_obs)
        prior_y.append(obs.reward)
    return logp


def update_posterior_full_history(
    principles: list[Principle],
    priors: dict[str, float],
    experts: dict[str, PrincipleGPExpert],
    history: list[Observation],
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
) -> dict[str, float]:
    if not principles:
        return {}
    if not history:
        return normalize_log_weights({p.name: math.log(max(priors.get(p.name, 1e-12), 1e-12)) for p in principles})
    log_weights: dict[str, float] = {}
    for principle in principles:
        logp = math.log(max(priors.get(principle.name, 1e-12), 1e-12))
        if len(history) <= 1:
            expert = experts[principle.name]
            for obs in history:
                mean, variance = expert.predict(principle_feature_vector(obs.row, principle, agent_cfg, pievo_cfg))
                logp += math.log(gaussian_likelihood(obs.reward, mean, variance + pievo_cfg.observation_noise**2))
        else:
            logp += sequential_predictive_log_likelihood(principle, history, agent_cfg, pievo_cfg)
        log_weights[principle.name] = logp
    return normalize_log_weights(log_weights)


def detect_map_residual_anomalies(
    principles: list[Principle],
    beliefs: dict[str, float],
    experts: dict[str, PrincipleGPExpert],
    history: list[Observation],
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
) -> list[Anomaly]:
    if not beliefs or not history:
        return []
    by_name = {p.name: p for p in principles}
    map_name = max(beliefs, key=beliefs.get)
    map_principle = by_name[map_name]
    expert = experts[map_name]
    anomalies: list[Anomaly] = []
    for obs in history:
        mean, variance = expert.predict(principle_feature_vector(obs.row, map_principle, agent_cfg, pievo_cfg))
        score = surprisal_score(obs.reward, mean, variance, pievo_cfg.observation_noise)
        if score > pievo_cfg.anomaly_threshold:
            anomalies.append(
                Anomaly(
                    hypothesis_key=obs.hypothesis_key,
                    principle=map_name,
                    expected_reward=mean,
                    observed_reward=obs.reward,
                    surprisal=score,
                    predicted_tg_mean_c=obs.predicted_tg_mean_c,
                    target_distance_c=float(obs.row.get("target_distance_c", math.nan)),
                )
            )
    return sorted(anomalies, key=lambda item: item.surprisal, reverse=True)


def augment_principles_from_anomalies(
    principles: list[Principle],
    priors: dict[str, float],
    anomalies: list[Anomaly],
    history: list[Observation],
    pievo_cfg: PiEvoFaithfulConfig,
) -> list[str]:
    if len(anomalies) < pievo_cfg.anomaly_min_count:
        return []
    existing_features = {p.feature for p in principles}
    existing_names = {p.name for p in principles}
    anomalous_keys = {item.hypothesis_key for item in anomalies}
    anomalous_rows = [obs.row for obs in history if obs.hypothesis_key in anomalous_keys]
    feature_counts: dict[str, int] = {}
    for row in anomalous_rows:
        for key, value in row.items():
            if not key.startswith("feature_"):
                continue
            feature = key.removeprefix("feature_")
            if feature in existing_features:
                continue
            if bool(value):
                feature_counts[feature] = feature_counts.get(feature, 0) + 1
    added: list[str] = []
    for feature, count in sorted(feature_counts.items(), key=lambda item: item[1], reverse=True):
        if count < pievo_cfg.anomaly_min_count or len(added) >= pievo_cfg.max_added_principles:
            continue
        name = "pievo_discovered_" + safe_slug(feature)
        if name in existing_names:
            continue
        principles.append(
            Principle(
                name=name,
                kind="soft",
                description=f"PiEvo anomaly-derived principle for feature {feature}; added because MAP residual anomalies repeatedly shared it.",
                feature=feature,
                effect=1.0,
                weight=0.35,
                confidence=0.35,
            )
        )
        priors[name] = min(0.02, 1.0 / max(100.0, len(priors) * 20.0))
        added.append(name)
        existing_names.add(name)
        existing_features.add(feature)
    if added:
        normalized = normalize_log_weights({key: math.log(max(value, 1e-12)) for key, value in priors.items()})
        priors.clear()
        priors.update(normalized)
    return added


def hypothetical_entropy(
    row: dict[str, object],
    sampled_y: float,
    principles: list[Principle],
    beliefs: dict[str, float],
    experts: dict[str, PrincipleGPExpert],
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
) -> float:
    log_weights: dict[str, float] = {}
    for principle in principles:
        prior = max(beliefs.get(principle.name, 1e-12), 1e-12)
        mean, variance = experts[principle.name].predict(principle_feature_vector(row, principle, agent_cfg, pievo_cfg))
        log_weights[principle.name] = math.log(prior) + math.log(gaussian_likelihood(sampled_y, mean, variance + pievo_cfg.observation_noise**2))
    return entropy(normalize_log_weights(log_weights))


def information_gain(
    row: dict[str, object],
    principles: list[Principle],
    beliefs: dict[str, float],
    experts: dict[str, PrincipleGPExpert],
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
    rng: np.random.Generator,
) -> float:
    current_entropy = entropy(beliefs)
    if current_entropy <= 1e-12:
        return 0.0
    pids = [p.name for p in principles]
    probs = np.asarray([beliefs.get(pid, 0.0) for pid in pids], dtype=float)
    probs = probs / max(probs.sum(), 1e-12)
    posterior_entropies = []
    by_name = {p.name: p for p in principles}
    for _ in range(max(1, pievo_cfg.ids_mc_samples)):
        pid = str(rng.choice(pids, p=probs))
        principle = by_name[pid]
        mean, variance = experts[pid].predict(principle_feature_vector(row, principle, agent_cfg, pievo_cfg))
        sampled_y = float(rng.normal(mean, math.sqrt(max(variance + pievo_cfg.observation_noise**2, 1e-10))))
        posterior_entropies.append(hypothetical_entropy(row, sampled_y, principles, beliefs, experts, agent_cfg, pievo_cfg))
    return float(max(0.0, current_entropy - float(np.mean(posterior_entropies))))


def select_by_ids(
    candidates: pd.DataFrame,
    principles: list[Principle],
    beliefs: dict[str, float],
    experts: dict[str, PrincipleGPExpert],
    history: list[Observation],
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
    rng: np.random.Generator,
) -> tuple[pd.Series, pd.DataFrame]:
    rows = [row.to_dict() for _, row in candidates.iterrows()]
    if len(history) < pievo_cfg.warmup_rounds:
        warmup_scores = []
        for row in rows:
            variance_sum = 0.0
            for principle in principles:
                _, variance = experts[principle.name].predict(principle_feature_vector(row, principle, agent_cfg, pievo_cfg))
                variance_sum += beliefs.get(principle.name, 0.0) * variance
            warmup_scores.append(variance_sum)
        idx = int(np.argmax(warmup_scores))
        diagnostics = candidates.copy()
        diagnostics["pievo_selection_method"] = "warmup_max_variance"
        diagnostics["pievo_warmup_variance"] = warmup_scores
        diagnostics["pievo_selected"] = False
        diagnostics.iloc[idx, diagnostics.columns.get_loc("pievo_selected")] = True
        return candidates.iloc[idx], diagnostics

    prediction_by_principle: dict[str, list[float]] = {}
    for principle in principles:
        prediction_by_principle[principle.name] = [
            experts[principle.name].predict(principle_feature_vector(row, principle, agent_cfg, pievo_cfg))[0] for row in rows
        ]
    expected_optimal = 0.0
    for principle in principles:
        values = prediction_by_principle[principle.name]
        expected_optimal += beliefs.get(principle.name, 0.0) * max(values)

    diagnostics = candidates.copy()
    ids_regrets = []
    ids_information = []
    ids_ratios = []
    expected_rewards = []
    for idx, row in enumerate(rows):
        expected_reward = sum(beliefs.get(p.name, 0.0) * prediction_by_principle[p.name][idx] for p in principles)
        regret = max(0.0, expected_optimal - expected_reward)
        info = information_gain(row, principles, beliefs, experts, agent_cfg, pievo_cfg, rng)
        ratio = (regret**2) / (info + pievo_cfg.ids_epsilon)
        expected_rewards.append(expected_reward)
        ids_regrets.append(regret)
        ids_information.append(info)
        ids_ratios.append(ratio)
    diagnostics["pievo_selection_method"] = "ids_min_regret2_over_information"
    diagnostics["pievo_expected_reward"] = expected_rewards
    diagnostics["pievo_regret"] = ids_regrets
    diagnostics["pievo_information_gain"] = ids_information
    diagnostics["pievo_ids_ratio"] = ids_ratios
    selected_idx = int(np.argmin(ids_ratios))
    diagnostics["pievo_selected"] = False
    diagnostics.iloc[selected_idx, diagnostics.columns.get_loc("pievo_selected")] = True
    return candidates.iloc[selected_idx], diagnostics


def write_pievo_report(
    out: Path,
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
    selected: pd.DataFrame,
    principles: list[Principle],
    beliefs: dict[str, float],
    round_history: list[dict[str, object]],
    validation: dict[str, object],
) -> None:
    lines = [
        "# PiEvo-Faithful SMP Discovery Report",
        "",
        "This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.",
        "",
        "## Objective",
        "",
        f"- Target Tg: {agent_cfg.target_tg_c:.2f} C",
        f"- Reward: exp(-abs(predicted_Tg - target_Tg) / {pievo_cfg.reward_temperature_c:.2f})",
        f"- Rounds: {pievo_cfg.rounds}",
        "",
        "## PiEvo State",
        "",
        f"- Active principles: {len(principles)}",
        f"- Posterior entropy: {entropy(beliefs):.6f}",
        f"- MAP principle: {max(beliefs, key=beliefs.get) if beliefs else '-'}",
        "",
        "## Selected Observations",
        "",
        "| Round | Tg mean (C) | target distance (C) | reward | selected by | anomalies | added principles |",
        "| --- | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for item in round_history:
        lines.append(
            f"| {item['round']} | {item['selected_predicted_tg_mean_c']:.2f} | "
            f"{item['selected_target_distance_c']:.2f} | {item['selected_reward']:.4f} | "
            f"{item['selection_method']} | {item['anomaly_count']} | {', '.join(item['added_principles']) or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Top Posterior Principles",
            "",
            "| Principle | posterior | feature | effect | description |",
            "| --- | ---: | --- | ---: | --- |",
        ]
    )
    by_name = {p.name: p for p in principles}
    for name, prob in sorted(beliefs.items(), key=lambda item: item[1], reverse=True)[:25]:
        principle = by_name[name]
        lines.append(f"| {name} | {prob:.6f} | {principle.feature} | {principle.effect:.1f} | {principle.description} |")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            "```json",
            pd.Series(validation).to_json(force_ascii=False, indent=2),
            "```",
            "",
            "## Interpretation",
            "",
            "- Posterior belief is evidence-weighted model belief, not physical truth.",
            "- A principle with low posterior is not deleted immediately; it should be dormant/pruned only after enough independent observations.",
            "- Real synthesis/DSC observations should be appended as higher-authority evidence and can override surrogate-only beliefs.",
        ]
    )
    (out / "pievo_faithful_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pievo_faithful(cfg: dict, device: torch.device) -> pd.DataFrame:
    agent_cfg = parse_agent_config(cfg)
    pievo_cfg = parse_pievo_faithful_config(cfg, agent_cfg)
    out = ensure_dir(pievo_cfg.output_dir)
    if not agent_cfg.vae_checkpoint.exists():
        raise FileNotFoundError(f"Missing VAE checkpoint: {agent_cfg.vae_checkpoint}")
    if not agent_cfg.predictor_path.exists():
        raise FileNotFoundError(f"Missing predictor: {agent_cfg.predictor_path}")
    if not agent_cfg.training_features_path.exists():
        raise FileNotFoundError(f"Missing training features: {agent_cfg.training_features_path}")

    charset, max_length = load_charset_meta(agent_cfg.vae_checkpoint, device)
    pool, pool_stats = build_monomer_pool(cfg, agent_cfg, charset, max_length)
    monomer_pool_frame(pool).to_csv(out / "monomer_pool.csv", index=False)
    vectors, _, _ = encode_pool(pool, agent_cfg.vae_checkpoint, device, agent_cfg.encode_batch_size)
    predictor = load_predictor(agent_cfg.predictor_path)
    train_features = np.asarray(np.load(agent_cfg.training_features_path)["x"], dtype=np.float32)
    ood_scale = ood_reference_scale(train_features)
    principles = initial_principles()
    priors = initial_priors(principles)
    beliefs = priors.copy()
    rng = np.random.default_rng(pievo_cfg.random_seed)
    history: list[Observation] = []
    round_history: list[dict[str, object]] = []
    all_diagnostics: list[pd.DataFrame] = []
    global_seen: set[str] = set()

    systematic = systematic_pair_formulas(pool, principles, agent_cfg.min_ratio, agent_cfg.require_out_of_library, agent_cfg.pair_pool_limit)
    for formula in systematic:
        global_seen.add(formula_key(formula.smiles, formula.ratios))

    for round_index in range(1, pievo_cfg.rounds + 1):
        experts = train_principle_experts(principles, history, agent_cfg, pievo_cfg)
        beliefs = update_posterior_full_history(principles, priors, experts, history, agent_cfg, pievo_cfg)
        anomalies = detect_map_residual_anomalies(principles, beliefs, experts, history, agent_cfg, pievo_cfg)
        added = augment_principles_from_anomalies(principles, priors, anomalies, history, pievo_cfg)
        if added:
            experts = train_principle_experts(principles, history, agent_cfg, pievo_cfg)
            beliefs = update_posterior_full_history(principles, priors, experts, history, agent_cfg, pievo_cfg)

        formulas: list[FormulaCandidate] = []
        if round_index == 1:
            formulas.extend(systematic[: pievo_cfg.candidate_batch_size])
        formulas.extend(
            random_formulas(
                pool,
                principles,
                rng,
                max(0, pievo_cfg.candidate_batch_size - len(formulas)),
                agent_cfg.min_components,
                agent_cfg.max_components,
                agent_cfg.min_ratio,
                agent_cfg.require_out_of_library,
                global_seen,
            )
        )
        scored = evaluate_formulas(formulas, vectors, predictor, train_features, ood_scale, agent_cfg)
        if scored.empty:
            round_history.append(
                {
                    "round": round_index,
                    "generated_candidates": 0,
                    "selection_method": "no_candidates",
                    "selected_predicted_tg_mean_c": math.nan,
                    "selected_target_distance_c": math.nan,
                    "selected_reward": math.nan,
                    "anomaly_count": len(anomalies),
                    "added_principles": added,
                    "posterior_entropy": entropy(beliefs),
                }
            )
            continue
        scored["round"] = round_index
        scored["environment_reward"] = scored["predicted_tg_mean_c"].map(
            lambda value: target_reward(float(value), agent_cfg.target_tg_c, pievo_cfg.reward_temperature_c)
        )
        selected_row, diagnostics = select_by_ids(scored, principles, beliefs, experts, history, agent_cfg, pievo_cfg, rng)
        diagnostics["round"] = round_index
        all_diagnostics.append(diagnostics)
        key = str(selected_row["smiles"]) + "@" + str(selected_row["ratios"])
        reward = target_reward(float(selected_row["predicted_tg_mean_c"]), agent_cfg.target_tg_c, pievo_cfg.reward_temperature_c)
        history.append(
            Observation(
                round_index=round_index,
                hypothesis_key=key,
                row=selected_row.to_dict(),
                reward=reward,
                predicted_tg_mean_c=float(selected_row["predicted_tg_mean_c"]),
                predicted_tg_sigma_c=float(selected_row["predicted_tg_sigma_c"]),
            )
        )
        round_history.append(
            {
                "round": round_index,
                "generated_candidates": int(len(scored)),
                "selection_method": str(diagnostics.loc[diagnostics["pievo_selected"], "pievo_selection_method"].iloc[0]),
                "selected_predicted_tg_mean_c": float(selected_row["predicted_tg_mean_c"]),
                "selected_target_distance_c": float(selected_row["target_distance_c"]),
                "selected_reward": reward,
                "anomaly_count": len(anomalies),
                "added_principles": added,
                "posterior_entropy": entropy(beliefs),
                "map_principle": max(beliefs, key=beliefs.get) if beliefs else None,
            }
        )

    experts = train_principle_experts(principles, history, agent_cfg, pievo_cfg)
    beliefs = update_posterior_full_history(principles, priors, experts, history, agent_cfg, pievo_cfg)
    selected = pd.DataFrame([obs.row | {"environment_reward": obs.reward, "pievo_round": obs.round_index} for obs in history])
    selected.to_csv(out / "selected_formulations.csv", index=False)
    if all_diagnostics:
        pd.concat(all_diagnostics, ignore_index=True).to_csv(out / "candidate_diagnostics.csv", index=False)
    save_json(round_history, out / "round_history.json")
    save_json({name: float(prob) for name, prob in beliefs.items()}, out / "principle_posterior.json")
    save_json([asdict(p) for p in principles], out / "principles.json")
    validation = validate_formula_frame(selected, agent_cfg) if not selected.empty else {"selected_rows": 0, "all_selected_pass": False}
    save_json(validation, out / "validation_summary.json")
    save_json(
        {
            "target_tg_c": agent_cfg.target_tg_c,
            "target_window_c": agent_cfg.target_window_c,
            "reward_temperature_c": pievo_cfg.reward_temperature_c,
            "pool_stats": pool_stats,
            "rounds": pievo_cfg.rounds,
            "selected_rows": int(len(selected)),
            "posterior_entropy": entropy(beliefs),
            "map_principle": max(beliefs, key=beliefs.get) if beliefs else None,
            "best_selected_target_distance_c": None if selected.empty else float(selected["target_distance_c"].min()),
            "top25_diversity": None if selected.empty else fingerprint_diversity(selected.head(25)["smiles"].map(lambda value: str(value).split("|")[0])),
            "validation": validation,
        },
        out / "pievo_faithful_summary.json",
    )
    write_pievo_report(out, agent_cfg, pievo_cfg, selected, principles, beliefs, round_history, validation)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="PiEvo-faithful SMP formulation discovery")
    parser.add_argument("--config", default="configs/pievo_faithful_250.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)
    set_seed(int(cfg.get("seed", 42)))
    device = resolve_device(cfg.get("device", "cuda"))
    selected = run_pievo_faithful(cfg, device)
    if selected.empty:
        print("No candidates selected.")
    else:
        best = selected.sort_values("target_distance_c").iloc[0]
        print(
            f"Best PiEvo-faithful observation: Tg={float(best['predicted_tg_mean_c']):.2f} C, "
            f"distance={float(best['target_distance_c']):.2f} C, reward={float(best['environment_reward']):.4f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
