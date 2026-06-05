from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_pre_experiment_validation_plan import build_validation_plan


def test_pre_experiment_validation_plan_prioritizes_sparse_high_tg_high_sigma(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    pd.DataFrame(
        [
            {
                "review_rank": 7,
                "linked_observation_id": "sparse_250_1",
                "target_tg_c": 250.0,
                "observed_tg_c": 249.97,
                "target_distance_c": 0.03,
                "predicted_tg_sigma_c": 78.0,
                "candidate_origin": "sparse_target_replacement_250",
                "reaction_principle": "epoxy_anhydride",
                "process_template": "epoxy_anhydride_catalyzed_cure",
                "missing_process_fields": "catalyst_loading;cure_temperature_c;post_cure_temperature_c",
                "review_priority": "process_design_for_dsc",
                "ood_penalty": 1.0,
                "new_component_count": 0,
                "smiles": "CC1CO1|O=C1OC(=O)c2ccccc21",
                "ratios": "0.60000:0.40000",
            },
            {
                "review_rank": 1,
                "linked_observation_id": "latent_195_1",
                "target_tg_c": 195.0,
                "observed_tg_c": 195.2,
                "target_distance_c": 0.2,
                "predicted_tg_sigma_c": 20.0,
                "candidate_origin": "vae_latent_local_search",
                "reaction_principle": "cyanate_ester_amine",
                "process_template": "cyanate_ester_triazine_cure",
                "missing_process_fields": "trimerization_temperature_c;catalyst_loading;post_cure_temperature_c",
                "review_priority": "process_design_for_dsc",
                "ood_penalty": 0.2,
                "new_component_count": 0,
                "smiles": "N#COc1ccc(OC#N)cc1|Nc1ccccc1",
                "ratios": "0.90000:0.10000",
            },
        ]
    ).to_csv(queue, index=False)

    plan, summary = build_validation_plan(
        queue,
        Path("trail/knowledge/smp_prior_knowledge.yaml"),
        high_sigma_c=50.0,
        top_k=2,
    )

    sparse = plan[plan["linked_observation_id"] == "sparse_250_1"].iloc[0]
    latent = plan[plan["linked_observation_id"] == "latent_195_1"].iloc[0]
    assert sparse["validation_lane"] == "process_plus_high_fidelity"
    assert "high_tg_target" in sparse["risk_flags"]
    assert "sparse_target_origin" in sparse["risk_flags"]
    assert "thermal_stability_pre_screen" in sparse["validation_methods"]
    assert latent["validation_lane"] == "process_completion_before_dsc"
    assert summary["target_counts"] == {"195.0": 1, "250.0": 1}
    assert summary["high_fidelity_required_rows"] == 1
    assert summary["process_completion_required_rows"] == 2
