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
    MonomerCandidate,
    Principle,
    build_monomer_pool,
    classify_mol,
    compatibility_edges,
    compute_prior_score,
    encode_pool,
    evaluate_formulas,
    fingerprint_diversity,
    formulas_to_features,
    formula_features,
    formula_key,
    functionality_estimate,
    initial_principles,
    load_charset_meta,
    monomer_features,
    monomer_pool_frame,
    ood_reference_scale,
    parse_agent_config,
    predict_with_uncertainty,
    random_formulas,
    safe_slug,
    systematic_pair_formulas,
    validate_formula_frame,
)
from smp02.predictors import load_predictor
from smp02.utils import ensure_dir, load_config, resolve_device, save_json, set_seed

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors


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
    external_observation_ledger: Path | None = None
    external_observation_limit: int | None = None
    external_observation_require_pass: bool = True
    external_observation_allowed_source_types: tuple[str, ...] | None = None
    external_observation_require_active_evidence: bool = False
    target_guard_enabled: bool = False
    target_guard_max_distance_c: float = 5.0
    target_guard_min_candidates: int = 1
    ensemble_disagreement_enabled: bool = False
    ensemble_metrics_path: Path | None = None
    ensemble_top_k: int = 6
    ensemble_selection_metric: str = "MAPEK test dataset (%)"
    ensemble_selection_higher_is_better: bool = False
    ensemble_consensus_std_c: float = 10.0
    ensemble_high_disagreement_std_c: float = 25.0
    ensemble_disagreement_guard_enabled: bool = False
    ensemble_disagreement_guard_max_std_c: float = 25.0
    ensemble_disagreement_guard_min_candidates: int = 1


@dataclass
class Observation:
    round_index: int
    hypothesis_key: str
    row: dict[str, object]
    reward: float
    predicted_tg_mean_c: float
    predicted_tg_sigma_c: float
    authority_weight: float = 1.0
    source_type: str = "surrogate"
    observation_id: str = ""
    evidence_role: str = "surrogate_selected"


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
    external_ledger = raw.get("external_observation_ledger")
    external_limit = raw.get("external_observation_limit")
    allowed_sources_raw = raw.get("external_observation_allowed_source_types")
    if allowed_sources_raw is None or allowed_sources_raw == "":
        allowed_source_types = None
    elif isinstance(allowed_sources_raw, str):
        allowed_source_types = tuple(part.strip() for part in allowed_sources_raw.split(",") if part.strip())
    else:
        allowed_source_types = tuple(str(part).strip() for part in allowed_sources_raw if str(part).strip())
    ensemble_metrics = raw.get("ensemble_metrics_path", "artifacts/reproduce/predictors/all_predictor_metrics.csv")
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
        external_observation_ledger=None if external_ledger in {None, ""} else Path(external_ledger),
        external_observation_limit=None if external_limit in {None, ""} else int(external_limit),
        external_observation_require_pass=bool(raw.get("external_observation_require_pass", True)),
        external_observation_allowed_source_types=allowed_source_types,
        external_observation_require_active_evidence=bool(raw.get("external_observation_require_active_evidence", False)),
        target_guard_enabled=bool(raw.get("target_guard_enabled", False)),
        target_guard_max_distance_c=float(raw.get("target_guard_max_distance_c", agent_cfg.target_window_c)),
        target_guard_min_candidates=int(raw.get("target_guard_min_candidates", 1)),
        ensemble_disagreement_enabled=bool(raw.get("ensemble_disagreement_enabled", False)),
        ensemble_metrics_path=None if ensemble_metrics in {None, ""} else Path(ensemble_metrics),
        ensemble_top_k=int(raw.get("ensemble_top_k", 6)),
        ensemble_selection_metric=str(raw.get("ensemble_selection_metric", "MAPEK test dataset (%)")),
        ensemble_selection_higher_is_better=bool(raw.get("ensemble_selection_higher_is_better", False)),
        ensemble_consensus_std_c=float(raw.get("ensemble_consensus_std_c", 10.0)),
        ensemble_high_disagreement_std_c=float(raw.get("ensemble_high_disagreement_std_c", 25.0)),
        ensemble_disagreement_guard_enabled=bool(raw.get("ensemble_disagreement_guard_enabled", False)),
        ensemble_disagreement_guard_max_std_c=float(raw.get("ensemble_disagreement_guard_max_std_c", raw.get("ensemble_high_disagreement_std_c", 25.0))),
        ensemble_disagreement_guard_min_candidates=int(raw.get("ensemble_disagreement_guard_min_candidates", 1)),
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


def truthy(value: object) -> bool:
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def finite_or_default(value: object, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default)
    return number if math.isfinite(number) else float(default)


def disagreement_bucket(std_c: float, consensus_std_c: float, high_std_c: float) -> str:
    if not math.isfinite(float(std_c)):
        return "unavailable"
    if float(std_c) <= float(consensus_std_c):
        return "low_disagreement"
    if float(std_c) >= float(high_std_c):
        return "high_disagreement"
    return "moderate_disagreement"


def select_ensemble_predictors(metrics: pd.DataFrame, agent_cfg: AgentConfig, pievo_cfg: PiEvoFaithfulConfig) -> pd.DataFrame:
    metric = pievo_cfg.ensemble_selection_metric
    if metric not in metrics.columns:
        raise ValueError(f"Missing ensemble selection metric column: {metric}")
    frame = metrics.copy()
    frame = frame[(frame["latent_size"].astype(int) == int(agent_cfg.latent_size)) & (frame["predictor_kind"].astype(str) == "joblib")]
    frame = frame[frame["model_path"].astype(str).map(lambda path: Path(path).exists())]
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=[metric])
    if frame.empty:
        raise ValueError(f"No usable ensemble predictors for latent_size={agent_cfg.latent_size}, metric={metric}.")
    return frame.sort_values(metric, ascending=not pievo_cfg.ensemble_selection_higher_is_better).head(pievo_cfg.ensemble_top_k).reset_index(drop=True)


def load_predictor_ensemble(agent_cfg: AgentConfig, pievo_cfg: PiEvoFaithfulConfig) -> tuple[list[dict[str, object]], pd.DataFrame]:
    if not pievo_cfg.ensemble_disagreement_enabled:
        return [], pd.DataFrame()
    if pievo_cfg.ensemble_metrics_path is None:
        raise ValueError("ensemble_disagreement_enabled requires ensemble_metrics_path.")
    if not pievo_cfg.ensemble_metrics_path.exists():
        raise FileNotFoundError(f"Missing ensemble metrics file: {pievo_cfg.ensemble_metrics_path}")
    predictors = select_ensemble_predictors(pd.read_csv(pievo_cfg.ensemble_metrics_path), agent_cfg, pievo_cfg)
    members: list[dict[str, object]] = []
    for _, row in predictors.iterrows():
        members.append(
            {
                "name": str(row["ML method"]),
                "slug": safe_slug(str(row["ML method"]).replace(f"VAE ({agent_cfg.latent_size}) + ", "")),
                "path": str(row["model_path"]),
                "bundle": load_predictor(row["model_path"]),
            }
        )
    return members, predictors


def attach_live_ensemble_disagreement(
    scored: pd.DataFrame,
    formulas: list[FormulaCandidate],
    vectors: dict[str, np.ndarray],
    ensemble_members: list[dict[str, object]],
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
) -> pd.DataFrame:
    if not ensemble_members or scored.empty:
        return scored
    result = scored.copy()
    x = formulas_to_features(formulas, vectors, agent_cfg.latent_size)
    prediction_values: list[np.ndarray] = []
    for member in ensemble_members:
        pred, sigma = predict_with_uncertainty(member["bundle"], x)
        slug = str(member["slug"])
        result[f"predictor_ensemble_pred_{slug}_tg_c"] = pred
        if np.isfinite(sigma).any():
            result[f"predictor_ensemble_sigma_{slug}_tg_c"] = sigma
        prediction_values.append(np.asarray(pred, dtype=float))
    values = np.vstack(prediction_values).T
    result["predictor_ensemble_model_count"] = int(values.shape[1])
    result["predictor_ensemble_mean_tg_c"] = np.mean(values, axis=1)
    result["predictor_ensemble_std_tg_c"] = np.std(values, axis=1, ddof=0)
    result["predictor_ensemble_min_tg_c"] = np.min(values, axis=1)
    result["predictor_ensemble_max_tg_c"] = np.max(values, axis=1)
    result["predictor_ensemble_range_tg_c"] = result["predictor_ensemble_max_tg_c"] - result["predictor_ensemble_min_tg_c"]
    result["predictor_ensemble_target_distance_c"] = (result["predictor_ensemble_mean_tg_c"] - float(agent_cfg.target_tg_c)).abs()
    result["predictor_ensemble_best_model_delta_c"] = result["predictor_ensemble_mean_tg_c"] - pd.to_numeric(
        result["predicted_tg_mean_c"],
        errors="coerce",
    )
    result["predictor_ensemble_disagreement_bucket"] = [
        disagreement_bucket(value, pievo_cfg.ensemble_consensus_std_c, pievo_cfg.ensemble_high_disagreement_std_c)
        for value in result["predictor_ensemble_std_tg_c"].astype(float)
    ]
    result["predictor_ensemble_near_target"] = result["predictor_ensemble_target_distance_c"] <= float(agent_cfg.target_window_c)
    result["predictor_ensemble_near_target_low_disagreement"] = (
        result["predictor_ensemble_near_target"]
        & (result["predictor_ensemble_std_tg_c"] <= float(pievo_cfg.ensemble_consensus_std_c))
    )
    result["predictor_ensemble_near_target_high_disagreement"] = (
        result["predictor_ensemble_near_target"]
        & (result["predictor_ensemble_std_tg_c"] >= float(pievo_cfg.ensemble_high_disagreement_std_c))
    )
    result["human_review_priority"] = "standard_surrogate_review"
    result.loc[result["predictor_ensemble_near_target_low_disagreement"], "human_review_priority"] = "priority_low_disagreement_near_target"
    result.loc[result["predictor_ensemble_near_target_high_disagreement"], "human_review_priority"] = "review_high_disagreement_near_target"
    result.loc[
        (~result["predictor_ensemble_near_target"]) & (result["predictor_ensemble_std_tg_c"] >= float(pievo_cfg.ensemble_high_disagreement_std_c)),
        "human_review_priority",
    ] = "review_high_disagreement"
    return result


def principle_feature_vector(row: dict[str, object], principle: Principle, agent_cfg: AgentConfig, pievo_cfg: PiEvoFaithfulConfig) -> np.ndarray:
    aligned = 1.0 if row_bool(row, principle.feature) else 0.0
    target_tg_c = finite_or_default(row.get("target_tg_c"), agent_cfg.target_tg_c)
    target_distance = finite_or_default(row.get("target_distance_c"), agent_cfg.target_window_c * 10.0)
    observed_or_predicted_tg_c = finite_or_default(row.get("observed_tg_c"), row.get("predicted_tg_mean_c", agent_cfg.target_tg_c))
    target_proximity = target_reward(
        observed_or_predicted_tg_c,
        target_tg_c,
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


AUTHORITY_WEIGHTS = {
    "surrogate": 1.0,
    "literature": 2.0,
    "high_fidelity_simulation": 3.0,
    "real_dsc": 5.0,
}


def parse_ratio_string(value: object, n_components: int) -> tuple[float, ...]:
    try:
        ratios = tuple(float(part) for part in str(value).split(":") if str(part).strip())
    except ValueError as exc:
        raise ValueError(f"Invalid ratio string: {value}") from exc
    if len(ratios) != n_components:
        raise ValueError(f"Ratio count {len(ratios)} does not match component count {n_components}.")
    total = sum(ratios)
    if total <= 0.0 or abs(total - 1.0) > 1e-3:
        raise ValueError(f"Ratios must sum to 1.0, got {total:.6f}.")
    return ratios


def external_monomer_candidate(smiles: str, observation_id: str, idx: int) -> MonomerCandidate:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES in external observation {observation_id}: {smiles}")
    canonical = Chem.MolToSmiles(mol, canonical=True)
    groups, counts = classify_mol(mol)
    features = monomer_features(mol, groups, counts)
    return MonomerCandidate(
        smiles=canonical,
        source="external",
        label=f"{observation_id}_{idx}",
        groups=groups,
        monomer_prior_score=0.0,
        molecular_weight=float(Descriptors.MolWt(mol)),
        heavy_atoms=int(mol.GetNumHeavyAtoms()),
        aromatic_rings=int(rdMolDescriptors.CalcNumAromaticRings(mol)),
        rotatable_bonds=int(rdMolDescriptors.CalcNumRotatableBonds(mol)),
        functionality=int(functionality_estimate(counts)),
        in_library=True,
        features=features,
    )


def external_observation_from_row(
    row: pd.Series,
    principles: list[Principle],
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
    row_index: int,
) -> Observation:
    observation_id = str(row.get("observation_id", f"external_{row_index}"))
    source_type = str(row.get("source_type", "surrogate"))
    smiles_values = [part.strip() for part in str(row["smiles"]).split("|") if part.strip()]
    if not smiles_values:
        raise ValueError(f"External observation {observation_id} has no SMILES.")
    ratios = parse_ratio_string(row["ratios"], len(smiles_values))
    monomers = [external_monomer_candidate(smiles, observation_id, idx) for idx, smiles in enumerate(smiles_values)]
    if len(monomers) == 1:
        reasons: tuple[str, ...] = ()
    else:
        reasons, _ = compatibility_edges(monomers)
        reasons = tuple(reasons)
    features = formula_features(monomers, reasons, new_component_count=0)
    for col, value in row.items():
        if str(col).startswith("feature_"):
            features[str(col).removeprefix("feature_")] = truthy(value)

    target_tg_c = finite_or_default(row.get("target_tg_c"), agent_cfg.target_tg_c)
    observed_tg_c = finite_or_default(row.get("observed_tg_c"), target_tg_c)
    predicted_tg_c = finite_or_default(row.get("predicted_tg_mean_c"), observed_tg_c)
    predicted_sigma_c = finite_or_default(row.get("predicted_tg_sigma_c"), 0.0)
    reward = target_reward(observed_tg_c, target_tg_c, pievo_cfg.reward_temperature_c)
    authority_weight = finite_or_default(row.get("authority_weight"), AUTHORITY_WEIGHTS.get(source_type, 1.0))
    canonical_smiles = tuple(m.smiles for m in monomers)
    ratio_text = ":".join(f"{ratio:.5f}" for ratio in ratios)
    row_dict: dict[str, object] = {
        "formula_id": observation_id,
        "n_components": len(monomers),
        "smiles": "|".join(canonical_smiles),
        "ratios": ratio_text,
        "sources": source_type,
        "labels": "|".join(m.label for m in monomers),
        "groups": "|".join(";".join(m.groups) for m in monomers),
        "new_component_count": 0,
        "compatibility_reasons": "|".join(reasons),
        "predicted_tg_mean_c": predicted_tg_c,
        "predicted_tg_sigma_c": predicted_sigma_c,
        "observed_tg_c": observed_tg_c,
        "target_tg_c": target_tg_c,
        "target_distance_c": abs(observed_tg_c - target_tg_c),
        "prior_score": compute_prior_score(features, principles),
        "ood_distance": math.nan,
        "ood_penalty": 0.0,
        "agent_score": math.nan,
        "observation_id": observation_id,
        "observation_source_type": source_type,
        "authority_weight": authority_weight,
        "evidence_role": "external_observation",
    }
    row_dict.update({f"feature_{name}": value for name, value in features.items()})
    return Observation(
        round_index=0,
        hypothesis_key=f"external:{observation_id}",
        row=row_dict,
        reward=reward,
        predicted_tg_mean_c=predicted_tg_c,
        predicted_tg_sigma_c=predicted_sigma_c,
        authority_weight=authority_weight,
        source_type=source_type,
        observation_id=observation_id,
        evidence_role="external_observation",
    )


def load_external_observations(
    pievo_cfg: PiEvoFaithfulConfig,
    principles: list[Principle],
    agent_cfg: AgentConfig,
) -> tuple[list[Observation], dict[str, object]]:
    path = pievo_cfg.external_observation_ledger
    if path is None:
        return [], {"enabled": False, "accepted_rows": 0, "rejected_rows": 0}
    if not path.exists():
        raise FileNotFoundError(f"Missing external observation ledger: {path}")
    df = pd.read_csv(path, low_memory=False)
    input_rows = int(len(df))
    candidate_rows_after_ledger_pass = input_rows
    if pievo_cfg.external_observation_require_pass and "ledger_pass" in df.columns:
        df = df[df["ledger_pass"].map(truthy)].copy()
    candidate_rows_after_ledger_pass = int(len(df))
    candidate_rows_after_source_filter = int(len(df))
    if pievo_cfg.external_observation_allowed_source_types is not None:
        allowed_sources = set(pievo_cfg.external_observation_allowed_source_types)
        if "source_type" in df.columns:
            df = df[df["source_type"].fillna("").astype(str).isin(allowed_sources)].copy()
        else:
            df = df.iloc[0:0].copy()
        candidate_rows_after_source_filter = int(len(df))
    candidate_rows_after_active_filter = int(len(df))
    if pievo_cfg.external_observation_require_active_evidence:
        if "active_evidence" in df.columns:
            df = df[df["active_evidence"].map(truthy)].copy()
        else:
            df = df.iloc[0:0].copy()
        candidate_rows_after_active_filter = int(len(df))
    candidate_rows_before_limit = int(len(df))
    if pievo_cfg.external_observation_limit is not None:
        df = df.head(pievo_cfg.external_observation_limit).copy()
    observations: list[Observation] = []
    rejected: list[dict[str, object]] = []
    for idx, row in df.iterrows():
        try:
            observations.append(external_observation_from_row(row, principles, agent_cfg, pievo_cfg, int(idx)))
        except Exception as exc:
            rejected.append(
                {
                    "row_index": int(idx),
                    "observation_id": str(row.get("observation_id", f"external_{idx}")),
                    "reason": str(exc),
                }
            )
    summary = {
        "enabled": True,
        "ledger_path": str(path),
        "input_rows": input_rows,
        "candidate_rows_after_ledger_pass": candidate_rows_after_ledger_pass,
        "allowed_source_types": None
        if pievo_cfg.external_observation_allowed_source_types is None
        else list(pievo_cfg.external_observation_allowed_source_types),
        "candidate_rows_after_source_filter": candidate_rows_after_source_filter,
        "require_active_evidence": bool(pievo_cfg.external_observation_require_active_evidence),
        "candidate_rows_after_active_filter": candidate_rows_after_active_filter,
        "candidate_rows_before_limit": candidate_rows_before_limit,
        "external_observation_limit": pievo_cfg.external_observation_limit,
        "candidate_rows_after_filter": int(len(df)),
        "accepted_rows": int(len(observations)),
        "rejected_rows": int(len(rejected)),
        "rejected": rejected,
        "source_counts": pd.Series([obs.source_type for obs in observations]).value_counts().to_dict(),
        "total_authority_weight": float(sum(obs.authority_weight for obs in observations)),
        "mean_reward": None if not observations else float(np.mean([obs.reward for obs in observations])),
    }
    return observations, summary


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
        log_likelihood = math.log(gaussian_likelihood(obs.reward, mean, variance + pievo_cfg.observation_noise**2))
        logp += max(float(obs.authority_weight), 0.0) * log_likelihood
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
                log_likelihood = math.log(gaussian_likelihood(obs.reward, mean, variance + pievo_cfg.observation_noise**2))
                logp += max(float(obs.authority_weight), 0.0) * log_likelihood
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


def target_guard_selection_pool(
    candidates: pd.DataFrame,
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
) -> tuple[pd.DataFrame, dict[str, object]]:
    max_distance = float(pievo_cfg.target_guard_max_distance_c)
    distances = pd.to_numeric(candidates["target_distance_c"], errors="coerce")
    feasible = distances <= max_distance
    feasible_count = int(feasible.sum())
    if not pievo_cfg.target_guard_enabled:
        pool = candidates
        guard = {
            "enabled": False,
            "active": False,
            "max_distance_c": max_distance,
            "candidate_count": feasible_count,
            "pool_size": int(len(candidates)),
            "reason": "disabled",
        }
    elif feasible_count >= max(1, int(pievo_cfg.target_guard_min_candidates)):
        pool = candidates.loc[feasible].copy()
        guard = {
            "enabled": True,
            "active": True,
            "max_distance_c": max_distance,
            "candidate_count": feasible_count,
            "pool_size": int(len(pool)),
            "reason": f"target_distance_c <= {max_distance:g}",
        }
    else:
        pool = candidates
        guard = {
            "enabled": True,
            "active": False,
            "max_distance_c": max_distance,
            "candidate_count": feasible_count,
            "pool_size": int(len(candidates)),
            "reason": f"insufficient feasible candidates for target_window={agent_cfg.target_window_c:g}",
        }
    max_std = float(pievo_cfg.ensemble_disagreement_guard_max_std_c)
    guard.update(
        {
            "disagreement_enabled": bool(pievo_cfg.ensemble_disagreement_guard_enabled),
            "disagreement_active": False,
            "disagreement_max_std_c": max_std,
            "disagreement_candidate_count": 0,
            "disagreement_missing_count": int(len(pool)),
            "disagreement_pool_size": int(len(pool)),
            "disagreement_reason": "disabled",
        }
    )
    if not pievo_cfg.ensemble_disagreement_guard_enabled:
        return pool, guard
    if "predictor_ensemble_std_tg_c" not in pool.columns:
        guard["disagreement_reason"] = "missing predictor_ensemble_std_tg_c"
        return pool, guard
    std_values = pd.to_numeric(pool["predictor_ensemble_std_tg_c"], errors="coerce")
    disagreement_feasible = std_values <= max_std
    disagreement_count = int(disagreement_feasible.sum())
    missing_count = int(std_values.isna().sum())
    guard["disagreement_candidate_count"] = disagreement_count
    guard["disagreement_missing_count"] = missing_count
    min_candidates = max(1, int(pievo_cfg.ensemble_disagreement_guard_min_candidates))
    if disagreement_count >= min_candidates:
        guarded_pool = pool.loc[disagreement_feasible].copy()
        guard["disagreement_active"] = True
        guard["disagreement_pool_size"] = int(len(guarded_pool))
        guard["disagreement_reason"] = f"predictor_ensemble_std_tg_c <= {max_std:g}"
        guard["pool_size"] = int(len(guarded_pool))
        return guarded_pool, guard
    guard["disagreement_reason"] = f"insufficient low-disagreement candidates for max_std={max_std:g}"
    guard["disagreement_pool_size"] = int(len(pool))
    return pool, guard


def attach_selection_pool_diagnostics(
    diagnostics: pd.DataFrame,
    selection_pool: pd.DataFrame,
    guard: dict[str, object],
) -> None:
    diagnostics["pievo_target_guard_enabled"] = bool(guard["enabled"])
    diagnostics["pievo_target_guard_active"] = bool(guard["active"])
    diagnostics["pievo_target_guard_max_distance_c"] = float(guard["max_distance_c"])
    diagnostics["pievo_target_guard_candidate_count"] = int(guard["candidate_count"])
    diagnostics["pievo_selection_pool_size"] = int(guard["pool_size"])
    diagnostics["pievo_selection_pool_reason"] = str(guard["reason"])
    diagnostics["pievo_ensemble_disagreement_guard_enabled"] = bool(guard.get("disagreement_enabled", False))
    diagnostics["pievo_ensemble_disagreement_guard_active"] = bool(guard.get("disagreement_active", False))
    diagnostics["pievo_ensemble_disagreement_guard_max_std_c"] = float(guard.get("disagreement_max_std_c", math.nan))
    diagnostics["pievo_ensemble_disagreement_guard_candidate_count"] = int(guard.get("disagreement_candidate_count", 0))
    diagnostics["pievo_ensemble_disagreement_guard_missing_count"] = int(guard.get("disagreement_missing_count", 0))
    diagnostics["pievo_ensemble_disagreement_guard_reason"] = str(guard.get("disagreement_reason", "disabled"))
    diagnostics["pievo_selection_pool_member"] = diagnostics.index.isin(selection_pool.index)


def selection_method_name(base: str, guard: dict[str, object]) -> str:
    target_active = bool(guard.get("active", False))
    disagreement_active = bool(guard.get("disagreement_active", False))
    if target_active and disagreement_active:
        return f"target_and_ensemble_guard_{base}"
    if target_active:
        return f"target_guard_{base}"
    if disagreement_active:
        return f"ensemble_disagreement_guard_{base}"
    return base


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
    selection_pool, guard = target_guard_selection_pool(candidates, agent_cfg, pievo_cfg)
    rows = [row.to_dict() for _, row in selection_pool.iterrows()]
    diagnostics = candidates.copy()
    attach_selection_pool_diagnostics(diagnostics, selection_pool, guard)
    if len(history) < pievo_cfg.warmup_rounds:
        warmup_scores = []
        for row in rows:
            variance_sum = 0.0
            for principle in principles:
                _, variance = experts[principle.name].predict(principle_feature_vector(row, principle, agent_cfg, pievo_cfg))
                variance_sum += beliefs.get(principle.name, 0.0) * variance
            warmup_scores.append(variance_sum)
        idx = int(np.argmax(warmup_scores))
        selected_index = selection_pool.index[idx]
        method = selection_method_name("warmup_max_variance", guard)
        diagnostics["pievo_selection_method"] = method
        diagnostics["pievo_warmup_variance"] = np.nan
        diagnostics.loc[selection_pool.index, "pievo_warmup_variance"] = warmup_scores
        diagnostics["pievo_selected"] = False
        diagnostics.loc[selected_index, "pievo_selected"] = True
        return candidates.loc[selected_index], diagnostics

    prediction_by_principle: dict[str, list[float]] = {}
    for principle in principles:
        prediction_by_principle[principle.name] = [
            experts[principle.name].predict(principle_feature_vector(row, principle, agent_cfg, pievo_cfg))[0] for row in rows
        ]
    expected_optimal = 0.0
    for principle in principles:
        values = prediction_by_principle[principle.name]
        expected_optimal += beliefs.get(principle.name, 0.0) * max(values)

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
    diagnostics["pievo_selection_method"] = selection_method_name("ids_min_regret2_over_information", guard)
    diagnostics["pievo_expected_reward"] = np.nan
    diagnostics["pievo_regret"] = np.nan
    diagnostics["pievo_information_gain"] = np.nan
    diagnostics["pievo_ids_ratio"] = np.nan
    diagnostics.loc[selection_pool.index, "pievo_expected_reward"] = expected_rewards
    diagnostics.loc[selection_pool.index, "pievo_regret"] = ids_regrets
    diagnostics.loc[selection_pool.index, "pievo_information_gain"] = ids_information
    diagnostics.loc[selection_pool.index, "pievo_ids_ratio"] = ids_ratios
    selected_idx = int(np.argmin(ids_ratios))
    selected_index = selection_pool.index[selected_idx]
    diagnostics["pievo_selected"] = False
    diagnostics.loc[selected_index, "pievo_selected"] = True
    return candidates.loc[selected_index], diagnostics


def write_pievo_report(
    out: Path,
    agent_cfg: AgentConfig,
    pievo_cfg: PiEvoFaithfulConfig,
    selected: pd.DataFrame,
    principles: list[Principle],
    beliefs: dict[str, float],
    round_history: list[dict[str, object]],
    external_summary: dict[str, object],
    total_history_rows: int,
    total_authority_weight: float,
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
        f"- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / {pievo_cfg.reward_temperature_c:.2f})",
        f"- Rounds: {pievo_cfg.rounds}",
        "",
        "## PiEvo State",
        "",
        f"- Active principles: {len(principles)}",
        f"- Total observations in posterior history: {total_history_rows}",
        f"- Total authority weight: {total_authority_weight:.3f}",
        f"- Posterior entropy: {entropy(beliefs):.6f}",
        f"- MAP principle: {max(beliefs, key=beliefs.get) if beliefs else '-'}",
        f"- Target guard: {pievo_cfg.target_guard_enabled} within {pievo_cfg.target_guard_max_distance_c:.2f} C",
        f"- Predictor ensemble disagreement: {pievo_cfg.ensemble_disagreement_enabled}",
        f"- Ensemble disagreement guard: {pievo_cfg.ensemble_disagreement_guard_enabled} within std <= {pievo_cfg.ensemble_disagreement_guard_max_std_c:.2f} C",
        "",
        "## External Evidence",
        "",
        f"- External ledger enabled: {bool(external_summary.get('enabled', False))}",
        f"- Accepted external rows: {int(external_summary.get('accepted_rows', 0))}",
        f"- Rejected external rows: {int(external_summary.get('rejected_rows', 0))}",
        f"- External source counts: {external_summary.get('source_counts', {})}",
        "",
        "## Selected Observations",
        "",
        "| Round | Tg mean (C) | target distance (C) | reward | selected by | target guard | ensemble guard | risk-feasible candidates | ensemble std (C) | review | anomalies | added principles |",
        "| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- | ---: | --- |",
    ]
    for item in round_history:
        ensemble_std = item.get("selected_predictor_ensemble_std_tg_c", math.nan)
        ensemble_std_text = "-" if not math.isfinite(float(ensemble_std)) else f"{float(ensemble_std):.2f}"
        lines.append(
            f"| {item['round']} | {item['selected_predicted_tg_mean_c']:.2f} | "
            f"{item['selected_target_distance_c']:.2f} | {item['selected_reward']:.4f} | "
            f"{item['selection_method']} | {item.get('target_guard_active', False)} | "
            f"{item.get('ensemble_disagreement_guard_active', False)} | "
            f"{int(item.get('ensemble_disagreement_guard_candidate_count', 0))} | {ensemble_std_text} | "
            f"{item.get('selected_human_review_priority', '-') or '-'} | {item['anomaly_count']} | "
            f"{', '.join(item['added_principles']) or '-'} |"
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
            "- External ledger observations enter `observation_history.csv`; only rows marked `surrogate_selected` are written as new PiEvo recommendations in `selected_formulations.csv`.",
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
    ensemble_members, ensemble_predictors = load_predictor_ensemble(agent_cfg, pievo_cfg)
    if not ensemble_predictors.empty:
        ensemble_predictors.to_csv(out / "predictor_ensemble_members.csv", index=False)
    train_features = np.asarray(np.load(agent_cfg.training_features_path)["x"], dtype=np.float32)
    ood_scale = ood_reference_scale(train_features)
    principles = initial_principles()
    priors = initial_priors(principles)
    beliefs = priors.copy()
    rng = np.random.default_rng(pievo_cfg.random_seed)
    external_history, external_summary = load_external_observations(pievo_cfg, principles, agent_cfg)
    history: list[Observation] = list(external_history)
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
        scored = attach_live_ensemble_disagreement(scored, formulas, vectors, ensemble_members, agent_cfg, pievo_cfg)
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
                    "ensemble_disagreement_enabled": bool(ensemble_members),
                    "ensemble_disagreement_guard_active": False,
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
        selected_diag = diagnostics.loc[diagnostics["pievo_selected"]].iloc[0]
        key = str(selected_row["smiles"]) + "@" + str(selected_row["ratios"])
        reward = target_reward(float(selected_row["predicted_tg_mean_c"]), agent_cfg.target_tg_c, pievo_cfg.reward_temperature_c)
        selected_dict = selected_row.to_dict()
        selected_dict.update(
            {
                "observed_tg_c": float(selected_row["predicted_tg_mean_c"]),
                "target_tg_c": agent_cfg.target_tg_c,
                "observation_id": f"surrogate_round_{round_index}",
                "observation_source_type": "surrogate",
                "authority_weight": 1.0,
                "evidence_role": "surrogate_selected",
            }
        )
        for field in [
            "pievo_selection_method",
            "pievo_target_guard_enabled",
            "pievo_target_guard_active",
            "pievo_target_guard_max_distance_c",
            "pievo_target_guard_candidate_count",
            "pievo_selection_pool_size",
            "pievo_selection_pool_reason",
            "pievo_ensemble_disagreement_guard_enabled",
            "pievo_ensemble_disagreement_guard_active",
            "pievo_ensemble_disagreement_guard_max_std_c",
            "pievo_ensemble_disagreement_guard_candidate_count",
            "pievo_ensemble_disagreement_guard_missing_count",
            "pievo_ensemble_disagreement_guard_reason",
        ]:
            selected_dict[field] = selected_diag.get(field)
        history.append(
            Observation(
                round_index=round_index,
                hypothesis_key=key,
                row=selected_dict,
                reward=reward,
                predicted_tg_mean_c=float(selected_row["predicted_tg_mean_c"]),
                predicted_tg_sigma_c=float(selected_row["predicted_tg_sigma_c"]),
                authority_weight=1.0,
                source_type="surrogate",
                observation_id=f"surrogate_round_{round_index}",
                evidence_role="surrogate_selected",
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
                "target_guard_enabled": bool(selected_diag.get("pievo_target_guard_enabled", False)),
                "target_guard_active": bool(selected_diag.get("pievo_target_guard_active", False)),
                "target_guard_max_distance_c": float(selected_diag.get("pievo_target_guard_max_distance_c", math.nan)),
                "target_guard_candidate_count": int(selected_diag.get("pievo_target_guard_candidate_count", 0)),
                "selection_pool_size": int(selected_diag.get("pievo_selection_pool_size", len(scored))),
                "ensemble_disagreement_enabled": bool(ensemble_members),
                "ensemble_disagreement_guard_enabled": bool(selected_diag.get("pievo_ensemble_disagreement_guard_enabled", False)),
                "ensemble_disagreement_guard_active": bool(selected_diag.get("pievo_ensemble_disagreement_guard_active", False)),
                "ensemble_disagreement_guard_max_std_c": float(selected_diag.get("pievo_ensemble_disagreement_guard_max_std_c", math.nan)),
                "ensemble_disagreement_guard_candidate_count": int(selected_diag.get("pievo_ensemble_disagreement_guard_candidate_count", 0)),
                "ensemble_disagreement_guard_missing_count": int(selected_diag.get("pievo_ensemble_disagreement_guard_missing_count", 0)),
                "selected_predictor_ensemble_std_tg_c": finite_or_default(selected_row.get("predictor_ensemble_std_tg_c"), math.nan),
                "selected_predictor_ensemble_bucket": str(selected_row.get("predictor_ensemble_disagreement_bucket", "")),
                "selected_human_review_priority": str(selected_row.get("human_review_priority", "")),
                "anomaly_count": len(anomalies),
                "added_principles": added,
                "posterior_entropy": entropy(beliefs),
                "map_principle": max(beliefs, key=beliefs.get) if beliefs else None,
            }
        )

    experts = train_principle_experts(principles, history, agent_cfg, pievo_cfg)
    beliefs = update_posterior_full_history(principles, priors, experts, history, agent_cfg, pievo_cfg)
    observation_history = pd.DataFrame(
        [
            obs.row
            | {
                "environment_reward": obs.reward,
                "pievo_round": obs.round_index,
                "authority_weight": obs.authority_weight,
                "observation_source_type": obs.source_type,
                "evidence_role": obs.evidence_role,
            }
            for obs in history
        ]
    )
    observation_history.to_csv(out / "observation_history.csv", index=False)
    if external_history:
        pd.DataFrame(
            [
                obs.row
                | {
                    "environment_reward": obs.reward,
                    "pievo_round": obs.round_index,
                    "authority_weight": obs.authority_weight,
                    "observation_source_type": obs.source_type,
                    "evidence_role": obs.evidence_role,
                }
                for obs in external_history
            ]
        ).to_csv(out / "external_observations_used.csv", index=False)
    selected = pd.DataFrame(
        [
            obs.row | {"environment_reward": obs.reward, "pievo_round": obs.round_index}
            for obs in history
            if obs.evidence_role == "surrogate_selected"
        ]
    )
    selected.to_csv(out / "selected_formulations.csv", index=False)
    if all_diagnostics:
        pd.concat(all_diagnostics, ignore_index=True).to_csv(out / "candidate_diagnostics.csv", index=False)
    save_json(round_history, out / "round_history.json")
    save_json(external_summary, out / "external_observation_summary.json")
    save_json({name: float(prob) for name, prob in beliefs.items()}, out / "principle_posterior.json")
    save_json([asdict(p) for p in principles], out / "principles.json")
    validation = validate_formula_frame(selected, agent_cfg) if not selected.empty else {"selected_rows": 0, "all_selected_pass": False}
    selected_has_ensemble = not selected.empty and "predictor_ensemble_std_tg_c" in selected.columns
    selected_ensemble_std = pd.to_numeric(selected["predictor_ensemble_std_tg_c"], errors="coerce") if selected_has_ensemble else pd.Series(dtype=float)
    save_json(validation, out / "validation_summary.json")
    save_json(
        {
            "target_tg_c": agent_cfg.target_tg_c,
            "target_window_c": agent_cfg.target_window_c,
            "reward_temperature_c": pievo_cfg.reward_temperature_c,
            "target_guard_enabled": pievo_cfg.target_guard_enabled,
            "target_guard_max_distance_c": pievo_cfg.target_guard_max_distance_c,
            "target_guard_min_candidates": pievo_cfg.target_guard_min_candidates,
            "ensemble_disagreement_enabled": pievo_cfg.ensemble_disagreement_enabled,
            "ensemble_metrics_path": None if pievo_cfg.ensemble_metrics_path is None else str(pievo_cfg.ensemble_metrics_path),
            "ensemble_top_k": pievo_cfg.ensemble_top_k,
            "ensemble_selection_metric": pievo_cfg.ensemble_selection_metric,
            "ensemble_disagreement_guard_enabled": pievo_cfg.ensemble_disagreement_guard_enabled,
            "ensemble_disagreement_guard_max_std_c": pievo_cfg.ensemble_disagreement_guard_max_std_c,
            "ensemble_disagreement_guard_min_candidates": pievo_cfg.ensemble_disagreement_guard_min_candidates,
            "pool_stats": pool_stats,
            "rounds": pievo_cfg.rounds,
            "selected_rows": int(len(selected)),
            "history_rows": int(len(history)),
            "external_observation_summary": external_summary,
            "total_authority_weight": float(sum(obs.authority_weight for obs in history)),
            "posterior_entropy": entropy(beliefs),
            "map_principle": max(beliefs, key=beliefs.get) if beliefs else None,
            "best_selected_target_distance_c": None if selected.empty else float(selected["target_distance_c"].min()),
            "selected_within_target_guard": None
            if selected.empty
            else int((selected["target_distance_c"] <= pievo_cfg.target_guard_max_distance_c).sum()),
            "all_selected_within_target_guard": False
            if selected.empty
            else bool((selected["target_distance_c"] <= pievo_cfg.target_guard_max_distance_c).all()),
            "selected_with_ensemble_disagreement_rows": 0 if not selected_has_ensemble else int(selected_ensemble_std.notna().sum()),
            "selected_low_disagreement_rows": 0
            if not selected_has_ensemble
            else int((selected_ensemble_std <= pievo_cfg.ensemble_consensus_std_c).sum()),
            "selected_high_disagreement_rows": 0
            if not selected_has_ensemble
            else int((selected_ensemble_std >= pievo_cfg.ensemble_high_disagreement_std_c).sum()),
            "all_selected_within_ensemble_disagreement_guard": None
            if not selected_has_ensemble
            else bool((selected_ensemble_std <= pievo_cfg.ensemble_disagreement_guard_max_std_c).all()),
            "mean_selected_predictor_ensemble_std_tg_c": None if not selected_has_ensemble else float(selected_ensemble_std.mean()),
            "top25_diversity": None if selected.empty else fingerprint_diversity(selected.head(25)["smiles"].map(lambda value: str(value).split("|")[0])),
            "validation": validation,
        },
        out / "pievo_faithful_summary.json",
    )
    write_pievo_report(
        out,
        agent_cfg,
        pievo_cfg,
        selected,
        principles,
        beliefs,
        round_history,
        external_summary,
        len(history),
        float(sum(obs.authority_weight for obs in history)),
        validation,
    )
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
