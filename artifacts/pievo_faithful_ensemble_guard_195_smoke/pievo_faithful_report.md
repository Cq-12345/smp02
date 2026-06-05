# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 195.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 6

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 6
- Total authority weight: 6.000
- Posterior entropy: 3.610702
- MAP principle: aromatic_backbones_raise_tg
- Target guard: True within 5.00 C
- Predictor ensemble disagreement: True
- Ensemble disagreement guard: True within std <= 25.00 C

## External Evidence

- External ledger enabled: False
- Accepted external rows: 0
- Rejected external rows: 0
- External source counts: {}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | target guard | ensemble guard | risk-feasible candidates | ensemble std (C) | review | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- | ---: | --- |
| 1 | 197.64 | 2.64 | 0.5899 | target_and_ensemble_guard_warmup_max_variance | True | True | 3 | 14.57 | standard_surrogate_review | 0 | - |
| 2 | 191.81 | 3.19 | 0.5284 | target_and_ensemble_guard_warmup_max_variance | True | True | 5 | 15.72 | standard_surrogate_review | 0 | - |
| 3 | 195.06 | 0.06 | 0.9883 | target_and_ensemble_guard_ids_min_regret2_over_information | True | True | 7 | 20.33 | standard_surrogate_review | 0 | - |
| 4 | 194.04 | 0.96 | 0.8254 | target_and_ensemble_guard_ids_min_regret2_over_information | True | True | 5 | 15.91 | standard_surrogate_review | 0 | - |
| 5 | 195.89 | 0.89 | 0.8377 | target_and_ensemble_guard_ids_min_regret2_over_information | True | True | 4 | 10.62 | standard_surrogate_review | 0 | - |
| 6 | 196.61 | 1.61 | 0.7252 | target_and_ensemble_guard_ids_min_regret2_over_information | True | True | 5 | 21.24 | standard_surrogate_review | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| aromatic_backbones_raise_tg | 0.030260 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.030260 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| cyanate_ester_triazine | 0.030260 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.030260 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| high_functionality_crosslink_density | 0.030260 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| flexible_ether_penalty | 0.030260 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| peg_like_penalty | 0.030260 | peg_like_risk | -1.0 | PEG-like segments are a strong low-Tg risk. |
| long_aliphatic_penalty | 0.030260 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| peptide_like_out_of_domain | 0.030260 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| heavy_halogen_practical_risk | 0.030260 | heavy_halogen_risk | -1.0 | Iodinated or brominated drug-like structures are lower-priority monomer hypotheses. |
| druglike_hetero_complexity_penalty | 0.030260 | druglike_hetero_complexity_risk | -1.0 | High HBA/HBD complexity is a risk for out-of-library monomer transfer. |
| formal_charge_practical_penalty | 0.030260 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.030260 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.030260 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.030260 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.030260 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.030260 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| reaction_aab22a9380a2 | 0.030260 | reaction::马来酰亚胺与烯基共聚/加成。 | 1.0 | Reaction principle: 马来酰亚胺与烯基共聚/加成。 |
| stereochemical_complexity_penalty | 0.025463 | stereochemical_complexity_risk | -1.0 | Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability. |
| reaction_ee82a65db02c | 0.025463 | reaction::氰酸酯三聚形成三嗪网络。 | 1.0 | Reaction principle: 氰酸酯三聚形成三嗪网络。 |
| reaction_839cd29ef5d7 | 0.025461 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |
| reaction_5cde50869441 | 0.025461 | reaction::环氧-仲胺开环固化。 | 1.0 | Reaction principle: 环氧-仲胺开环固化。 |
| reaction_8122f963caab | 0.025461 | reaction::环氧-酸酐固化，常需催化剂。 | 1.0 | Reaction principle: 环氧-酸酐固化，常需催化剂。 |
| reaction_b793ac896a4f | 0.025461 | reaction::环氧-羧酸开环酯化。 | 1.0 | Reaction principle: 环氧-羧酸开环酯化。 |
| reaction_cc7f1a60f1af | 0.025461 | reaction::环氧-羟基醚化，常需催化剂。 | 1.0 | Reaction principle: 环氧-羟基醚化，常需催化剂。 |

## Validation

```json
{
  "selected_rows":6,
  "ratio_sum_ok":6,
  "has_out_of_library":6,
  "n_range_ok":6,
  "compatibility_nonempty":6,
  "rdkit_valid":6,
  "all_selected_pass":true
}
```

## Interpretation

- Posterior belief is evidence-weighted model belief, not physical truth.
- External ledger observations enter `observation_history.csv`; only rows marked `surrogate_selected` are written as new PiEvo recommendations in `selected_formulations.csv`.
- A principle with low posterior is not deleted immediately; it should be dormant/pruned only after enough independent observations.
- Real synthesis/DSC observations should be appended as higher-authority evidence and can override surrogate-only beliefs.
