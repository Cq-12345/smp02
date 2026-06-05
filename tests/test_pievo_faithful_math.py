from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from smp02.agent_discovery import AgentConfig, Principle
from smp02.pievo_faithful import (
    Observation,
    PiEvoFaithfulConfig,
    load_external_observations,
    normalize_log_weights,
    select_by_ids,
    surprisal_score,
    target_reward,
    update_posterior_full_history,
)


class DummyExpert:
    def __init__(self, mean: float, variance: float = 0.01) -> None:
        self.mean = mean
        self.variance = variance

    def predict(self, _x):
        return self.mean, self.variance


class DistanceVarianceExpert:
    def predict(self, x):
        target_distance_scaled = float(x.reshape(1, -1)[0, 7])
        return 0.5, 10.0 if target_distance_scaled > 5.0 else 0.01


def fake_agent_cfg() -> AgentConfig:
    return AgentConfig(
        target_tg_c=250.0,
        target_window_c=5.0,
        output_dir=Path("artifacts/test"),
        latent_size=8,
        vae_checkpoint=Path("vae.pt"),
        predictor_path=Path("predictor.joblib"),
        training_features_path=Path("features.npz"),
        max_components=4,
        min_components=1,
        min_ratio=0.05,
        require_out_of_library=True,
        generated_pool_limit=1,
        chembl_limit=1,
        chembl_pool_limit=1,
        library_pool_limit=1,
        pair_pool_limit=1,
        iterations=1,
        samples_per_iteration=1,
        elite_k=1,
        selected_top_k=1,
        prediction_batch_size=1,
        encode_batch_size=1,
        prior_learning_rate=0.1,
        uncertainty_weight=0.1,
        ood_weight=0.1,
        prior_weight=0.1,
        novelty_weight=0.1,
        component_count_weight=0.1,
    )


def fake_pievo_cfg() -> PiEvoFaithfulConfig:
    return PiEvoFaithfulConfig(
        output_dir=Path("artifacts/test"),
        rounds=2,
        candidate_batch_size=2,
        warmup_rounds=1,
        observation_noise=0.05,
        anomaly_threshold=0.7,
        anomaly_min_count=2,
        ids_mc_samples=4,
        ids_epsilon=1e-6,
        reward_temperature_c=5.0,
        max_added_principles=2,
        random_seed=42,
    )


def test_target_reward_supports_nonfixed_target() -> None:
    assert target_reward(250.0, 250.0, 5.0) == 1.0
    assert target_reward(190.0, 190.0, 5.0) == 1.0
    assert target_reward(260.0, 250.0, 5.0) < target_reward(252.0, 250.0, 5.0)


def test_normalize_log_weights_returns_distribution() -> None:
    probs = normalize_log_weights({"a": -1000.0, "b": -999.0})
    assert set(probs) == {"a", "b"}
    assert abs(sum(probs.values()) - 1.0) < 1e-12
    assert probs["b"] > probs["a"]


def test_full_history_posterior_prefers_better_likelihood() -> None:
    principles = [
        Principle("good", "soft", "good principle", "feature_a", 1.0, 1.0, 0.5),
        Principle("bad", "soft", "bad principle", "feature_b", 1.0, 1.0, 0.5),
    ]
    priors = {"good": 0.5, "bad": 0.5}
    experts = {"good": DummyExpert(0.9), "bad": DummyExpert(0.1)}
    row = {
        "feature_feature_a": True,
        "feature_feature_b": False,
        "target_distance_c": 1.0,
        "predicted_tg_mean_c": 249.0,
        "predicted_tg_sigma_c": 1.0,
        "prior_score": 0.0,
        "ood_penalty": 0.0,
        "n_components": 2,
        "new_component_count": 1,
    }
    history = [Observation(1, "h1", row, 0.9, 249.0, 1.0)]
    posterior = update_posterior_full_history(principles, priors, experts, history, fake_agent_cfg(), fake_pievo_cfg())
    assert posterior["good"] > 0.99
    assert posterior["bad"] < 0.01


def test_authority_weight_changes_posterior_strength() -> None:
    principles = [
        Principle("good", "soft", "good principle", "feature_a", 1.0, 1.0, 0.5),
        Principle("bad", "soft", "bad principle", "feature_b", 1.0, 1.0, 0.5),
    ]
    priors = {"good": 0.1, "bad": 0.9}
    experts = {"good": DummyExpert(0.60), "bad": DummyExpert(0.40)}
    row = {
        "feature_feature_a": True,
        "feature_feature_b": False,
        "target_tg_c": 250.0,
        "target_distance_c": 2.0,
        "predicted_tg_mean_c": 248.0,
        "predicted_tg_sigma_c": 1.0,
        "prior_score": 0.0,
        "ood_penalty": 0.0,
        "n_components": 2,
        "new_component_count": 1,
    }
    low_weight = [Observation(1, "h1", row, 0.55, 248.0, 1.0, authority_weight=1.0)]
    high_weight = [Observation(1, "h1", row, 0.55, 248.0, 1.0, authority_weight=5.0)]
    low_posterior = update_posterior_full_history(principles, priors, experts, low_weight, fake_agent_cfg(), fake_pievo_cfg())
    high_posterior = update_posterior_full_history(principles, priors, experts, high_weight, fake_agent_cfg(), fake_pievo_cfg())
    assert low_posterior["bad"] > low_posterior["good"]
    assert high_posterior["good"] > high_posterior["bad"]


def test_load_external_observations_adds_weighted_history(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.csv"
    ledger.write_text(
        "\n".join(
            [
                "observation_id,source_type,target_tg_c,observed_tg_c,smiles,ratios,ledger_pass",
                "real_001,real_dsc,200,198,CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|Nc1ccc(N)cc1,0.5:0.5,True",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cfg = fake_pievo_cfg()
    cfg.external_observation_ledger = ledger
    observations, summary = load_external_observations(cfg, [], fake_agent_cfg())
    assert summary["accepted_rows"] == 1
    assert summary["rejected_rows"] == 0
    assert observations[0].evidence_role == "external_observation"
    assert observations[0].authority_weight == 5.0
    assert observations[0].row["target_tg_c"] == 200.0
    assert observations[0].row["target_distance_c"] == 2.0
    assert observations[0].row["feature_aromatic_backbone"] is True


def test_load_external_observations_can_require_active_high_authority_evidence(tmp_path: Path) -> None:
    ledger = tmp_path / "active_ledger.csv"
    ledger.write_text(
        "\n".join(
            [
                "observation_id,source_type,target_tg_c,observed_tg_c,smiles,ratios,ledger_pass,active_evidence",
                "hf_001,high_fidelity_simulation,250,249,CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|Nc1ccc(N)cc1,0.5:0.5,True,True",
                "dsc_not_active,real_dsc,250,248,CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|Nc1ccc(N)cc1,0.5:0.5,True,False",
                "surrogate_not_allowed,surrogate,250,250,CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1|Nc1ccc(N)cc1,0.5:0.5,True,True",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cfg = fake_pievo_cfg()
    cfg.external_observation_ledger = ledger
    cfg.external_observation_allowed_source_types = ("high_fidelity_simulation", "real_dsc", "literature")
    cfg.external_observation_require_active_evidence = True

    observations, summary = load_external_observations(cfg, [], fake_agent_cfg())

    assert summary["input_rows"] == 3
    assert summary["candidate_rows_after_ledger_pass"] == 3
    assert summary["candidate_rows_after_source_filter"] == 2
    assert summary["candidate_rows_after_active_filter"] == 1
    assert summary["accepted_rows"] == 1
    assert summary["allowed_source_types"] == ["high_fidelity_simulation", "real_dsc", "literature"]
    assert summary["require_active_evidence"] is True
    assert observations[0].observation_id == "hf_001"
    assert observations[0].source_type == "high_fidelity_simulation"
    assert observations[0].authority_weight == 3.0


def test_target_guard_limits_warmup_selection_to_near_target_candidates() -> None:
    principles = [Principle("target_guard_test", "soft", "test principle", "feature_a", 1.0, 1.0, 1.0)]
    candidates = pd.DataFrame(
        [
            {
                "formula_id": "near",
                "target_distance_c": 1.0,
                "predicted_tg_mean_c": 249.0,
                "predicted_tg_sigma_c": 1.0,
                "prior_score": 0.0,
                "ood_penalty": 0.0,
                "n_components": 2,
                "new_component_count": 1,
                "feature_feature_a": True,
            },
            {
                "formula_id": "far_high_variance",
                "target_distance_c": 100.0,
                "predicted_tg_mean_c": 150.0,
                "predicted_tg_sigma_c": 1.0,
                "prior_score": 0.0,
                "ood_penalty": 0.0,
                "n_components": 2,
                "new_component_count": 1,
                "feature_feature_a": True,
            },
        ]
    )
    cfg = fake_pievo_cfg()
    cfg.target_guard_enabled = True
    cfg.target_guard_max_distance_c = 5.0
    selected, diagnostics = select_by_ids(
        candidates,
        principles,
        {"target_guard_test": 1.0},
        {"target_guard_test": DistanceVarianceExpert()},
        [],
        fake_agent_cfg(),
        cfg,
        np.random.default_rng(42),
    )
    assert selected["formula_id"] == "near"
    assert bool(diagnostics.loc[0, "pievo_selection_pool_member"]) is True
    assert bool(diagnostics.loc[1, "pievo_selection_pool_member"]) is False
    assert diagnostics.loc[0, "pievo_selection_method"] == "target_guard_warmup_max_variance"


def test_ensemble_disagreement_guard_limits_warmup_selection_to_low_risk_candidates() -> None:
    principles = [Principle("ensemble_guard_test", "soft", "test principle", "feature_a", 1.0, 1.0, 1.0)]
    candidates = pd.DataFrame(
        [
            {
                "formula_id": "low_disagreement",
                "target_distance_c": 1.0,
                "predicted_tg_mean_c": 249.0,
                "predicted_tg_sigma_c": 1.0,
                "predictor_ensemble_std_tg_c": 8.0,
                "prior_score": 0.0,
                "ood_penalty": 0.0,
                "n_components": 2,
                "new_component_count": 1,
                "feature_feature_a": True,
            },
            {
                "formula_id": "high_disagreement_high_variance",
                "target_distance_c": 100.0,
                "predicted_tg_mean_c": 150.0,
                "predicted_tg_sigma_c": 1.0,
                "predictor_ensemble_std_tg_c": 80.0,
                "prior_score": 0.0,
                "ood_penalty": 0.0,
                "n_components": 2,
                "new_component_count": 1,
                "feature_feature_a": True,
            },
        ]
    )
    cfg = fake_pievo_cfg()
    cfg.ensemble_disagreement_guard_enabled = True
    cfg.ensemble_disagreement_guard_max_std_c = 25.0
    selected, diagnostics = select_by_ids(
        candidates,
        principles,
        {"ensemble_guard_test": 1.0},
        {"ensemble_guard_test": DistanceVarianceExpert()},
        [],
        fake_agent_cfg(),
        cfg,
        np.random.default_rng(42),
    )
    assert selected["formula_id"] == "low_disagreement"
    assert bool(diagnostics.loc[0, "pievo_selection_pool_member"]) is True
    assert bool(diagnostics.loc[1, "pievo_selection_pool_member"]) is False
    assert diagnostics.loc[0, "pievo_selection_method"] == "ensemble_disagreement_guard_warmup_max_variance"
    assert bool(diagnostics.loc[0, "pievo_ensemble_disagreement_guard_active"]) is True
    assert diagnostics.loc[0, "pievo_ensemble_disagreement_guard_candidate_count"] == 1


def test_surprisal_score_increases_with_residual() -> None:
    low = surprisal_score(y=0.9, mean=0.88, model_variance=0.01, observation_noise=0.05)
    high = surprisal_score(y=0.9, mean=0.1, model_variance=0.01, observation_noise=0.05)
    assert high > low
    assert 0.0 <= low < 1.0
    assert 0.0 <= high < 1.0
