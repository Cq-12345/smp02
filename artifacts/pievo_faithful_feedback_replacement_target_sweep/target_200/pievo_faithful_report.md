# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 200.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 6

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 17
- Total authority weight: 17.000
- Posterior entropy: 2.877774
- MAP principle: too_flexible_penalty
- Target guard: True within 5.00 C

## External Evidence

- External ledger enabled: True
- Accepted external rows: 11
- Rejected external rows: 0
- External source counts: {'surrogate': 11}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | guard active | feasible candidates | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| 1 | 201.66 | 1.66 | 0.7168 | target_guard_ids_min_regret2_over_information | True | 7 | 0 | - |
| 2 | 200.23 | 0.23 | 0.9544 | target_guard_ids_min_regret2_over_information | True | 13 | 0 | - |
| 3 | 200.34 | 0.34 | 0.9351 | target_guard_ids_min_regret2_over_information | True | 11 | 0 | - |
| 4 | 200.29 | 0.29 | 0.9433 | target_guard_ids_min_regret2_over_information | True | 9 | 0 | - |
| 5 | 200.48 | 0.48 | 0.9093 | target_guard_ids_min_regret2_over_information | True | 12 | 0 | - |
| 6 | 199.80 | 0.20 | 0.9599 | target_guard_ids_min_regret2_over_information | True | 11 | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| too_flexible_penalty | 0.256779 | too_flexible_risk | -1.0 | High rotatable-bond count increases flexibility risk. |
| stereochemical_complexity_penalty | 0.090954 | stereochemical_complexity_risk | -1.0 | Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability. |
| reaction_839cd29ef5d7 | 0.073866 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |
| reaction_536dfe22d324 | 0.072952 | reaction::氰酸酯-胺共反应。 | 1.0 | Reaction principle: 氰酸酯-胺共反应。 |
| cyanate_ester_triazine | 0.072948 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.072948 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| long_aliphatic_penalty | 0.026311 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| imide_anhydride_networks_raise_tg | 0.026310 | imide_or_anhydride | 1.0 | Imide or anhydride-derived networks often provide high Tg. |
| reaction_2f387d801461 | 0.026273 | reaction::酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 | 1.0 | Reaction principle: 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 |
| flexible_ether_penalty | 0.022500 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| reaction_cc7f1a60f1af | 0.017803 | reaction::环氧-羟基醚化，常需催化剂。 | 1.0 | Reaction principle: 环氧-羟基醚化，常需催化剂。 |
| aromatic_backbones_raise_tg | 0.013092 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.013092 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| high_functionality_crosslink_density | 0.013092 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| peptide_like_out_of_domain | 0.013092 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| heavy_halogen_practical_risk | 0.013092 | heavy_halogen_risk | -1.0 | Iodinated or brominated drug-like structures are lower-priority monomer hypotheses. |
| druglike_hetero_complexity_penalty | 0.013092 | druglike_hetero_complexity_risk | -1.0 | High HBA/HBD complexity is a risk for out-of-library monomer transfer. |
| formal_charge_practical_penalty | 0.013092 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.013092 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.013092 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.013092 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.013092 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.013092 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| maleimide_rigid_network | 0.013049 | maleimide | 1.0 | Bismaleimide motifs can create rigid high-Tg networks. |
| reaction_michael | 0.013049 | reaction::马来酰亚胺-硫醇 Michael 加成。 | 1.0 | Reaction principle: 马来酰亚胺-硫醇 Michael 加成。 |

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
