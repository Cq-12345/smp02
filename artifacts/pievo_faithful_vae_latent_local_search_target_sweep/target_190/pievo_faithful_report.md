# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 190.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 4

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 42
- Total authority weight: 42.000
- Posterior entropy: 3.289599
- MAP principle: maleimide_rigid_network
- Target guard: True within 5.00 C
- Predictor ensemble disagreement: False
- Ensemble disagreement guard: False within std <= 25.00 C

## External Evidence

- External ledger enabled: True
- Accepted external rows: 38
- Rejected external rows: 0
- External source counts: {'surrogate': 38}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | target guard | ensemble guard | risk-feasible candidates | ensemble std (C) | review | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- | ---: | --- |
| 1 | 190.00 | 0.00 | 0.9995 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 2 | 185.29 | 4.71 | 0.3902 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 3 | 187.68 | 2.32 | 0.6283 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 4 | 189.56 | 0.44 | 0.9164 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| maleimide_rigid_network | 0.104684 | maleimide | 1.0 | Bismaleimide motifs can create rigid high-Tg networks. |
| reaction_7deb10577c5e | 0.065523 | reaction::酸酐-胺开环形成酰胺酸。 | 1.0 | Reaction principle: 酸酐-胺开环形成酰胺酸。 |
| aromatic_backbones_raise_tg | 0.040477 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.040477 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| high_functionality_crosslink_density | 0.040477 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| peptide_like_out_of_domain | 0.040477 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| heavy_halogen_practical_risk | 0.040477 | heavy_halogen_risk | -1.0 | Iodinated or brominated drug-like structures are lower-priority monomer hypotheses. |
| formal_charge_practical_penalty | 0.040477 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.040477 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.040477 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.040477 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.040477 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.040477 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| reaction_8122f963caab | 0.037408 | reaction::环氧-酸酐固化，常需催化剂。 | 1.0 | Reaction principle: 环氧-酸酐固化，常需催化剂。 |
| reaction_b793ac896a4f | 0.037408 | reaction::环氧-羧酸开环酯化。 | 1.0 | Reaction principle: 环氧-羧酸开环酯化。 |
| reaction_e3ab71c1126b | 0.037408 | reaction::酸酐-羟基酯化。 | 1.0 | Reaction principle: 酸酐-羟基酯化。 |
| reaction_aaba7fbe7783 | 0.037408 | reaction::异氰酸酯-羟基形成聚氨酯。 | 1.0 | Reaction principle: 异氰酸酯-羟基形成聚氨酯。 |
| reaction_a67f85420c33 | 0.037408 | reaction::异氰酸酯-仲胺形成脲键。 | 1.0 | Reaction principle: 异氰酸酯-仲胺形成脲键。 |
| reaction_1ef23bb55506 | 0.037408 | reaction::硫醇-烯点击反应。 | 1.0 | Reaction principle: 硫醇-烯点击反应。 |
| reaction_ee82a65db02c | 0.037408 | reaction::氰酸酯三聚形成三嗪网络。 | 1.0 | Reaction principle: 氰酸酯三聚形成三嗪网络。 |
| too_flexible_penalty | 0.014093 | too_flexible_risk | -1.0 | High rotatable-bond count increases flexibility risk. |
| flexible_ether_penalty | 0.013393 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| stereochemical_complexity_penalty | 0.012747 | stereochemical_complexity_risk | -1.0 | Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability. |
| reaction_2f387d801461 | 0.011061 | reaction::酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 | 1.0 | Reaction principle: 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 |
| long_aliphatic_penalty | 0.010547 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |

## Validation

```json
{
  "selected_rows":4,
  "ratio_sum_ok":4,
  "has_out_of_library":4,
  "n_range_ok":4,
  "compatibility_nonempty":4,
  "rdkit_valid":4,
  "all_selected_pass":true
}
```

## Interpretation

- Posterior belief is evidence-weighted model belief, not physical truth.
- External ledger observations enter `observation_history.csv`; only rows marked `surrogate_selected` are written as new PiEvo recommendations in `selected_formulations.csv`.
- A principle with low posterior is not deleted immediately; it should be dormant/pruned only after enough independent observations.
- Real synthesis/DSC observations should be appended as higher-authority evidence and can override surrogate-only beliefs.
