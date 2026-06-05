# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 250.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 6

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 10
- Total authority weight: 10.000
- Posterior entropy: 3.552262
- MAP principle: heavy_halogen_practical_risk
- Target guard: True within 5.00 C

## External Evidence

- External ledger enabled: True
- Accepted external rows: 4
- Rejected external rows: 0
- External source counts: {'surrogate': 4}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | guard active | feasible candidates | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| 1 | 251.40 | 1.40 | 0.7561 | target_guard_ids_min_regret2_over_information | True | 5 | 0 | - |
| 2 | 249.17 | 0.83 | 0.8471 | target_guard_ids_min_regret2_over_information | True | 11 | 0 | - |
| 3 | 249.47 | 0.53 | 0.8995 | target_guard_ids_min_regret2_over_information | True | 9 | 0 | - |
| 4 | 249.63 | 0.37 | 0.9296 | target_guard_ids_min_regret2_over_information | True | 12 | 0 | - |
| 5 | 249.90 | 0.10 | 0.9804 | target_guard_ids_min_regret2_over_information | True | 14 | 0 | - |
| 6 | 249.86 | 0.14 | 0.9718 | target_guard_ids_min_regret2_over_information | True | 13 | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| heavy_halogen_practical_risk | 0.037261 | heavy_halogen_risk | -1.0 | Iodinated or brominated drug-like structures are lower-priority monomer hypotheses. |
| maleimide_rigid_network | 0.037258 | maleimide | 1.0 | Bismaleimide motifs can create rigid high-Tg networks. |
| reaction_michael | 0.037258 | reaction::马来酰亚胺-硫醇 Michael 加成。 | 1.0 | Reaction principle: 马来酰亚胺-硫醇 Michael 加成。 |
| reaction_aab22a9380a2 | 0.037258 | reaction::马来酰亚胺与烯基共聚/加成。 | 1.0 | Reaction principle: 马来酰亚胺与烯基共聚/加成。 |
| imide_anhydride_networks_raise_tg | 0.037255 | imide_or_anhydride | 1.0 | Imide or anhydride-derived networks often provide high Tg. |
| aromatic_backbones_raise_tg | 0.035438 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.035438 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| cyanate_ester_triazine | 0.035438 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.035438 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| high_functionality_crosslink_density | 0.035438 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| flexible_ether_penalty | 0.035438 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| long_aliphatic_penalty | 0.035438 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| peptide_like_out_of_domain | 0.035438 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| formal_charge_practical_penalty | 0.035438 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.035438 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.035438 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.035438 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.035438 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.035438 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| peg_like_penalty | 0.020674 | peg_like_risk | -1.0 | PEG-like segments are a strong low-Tg risk. |
| too_flexible_penalty | 0.020674 | too_flexible_risk | -1.0 | High rotatable-bond count increases flexibility risk. |
| druglike_hetero_complexity_penalty | 0.020674 | druglike_hetero_complexity_risk | -1.0 | High HBA/HBD complexity is a risk for out-of-library monomer transfer. |
| reaction_5cde50869441 | 0.017839 | reaction::环氧-仲胺开环固化。 | 1.0 | Reaction principle: 环氧-仲胺开环固化。 |
| reaction_8122f963caab | 0.017839 | reaction::环氧-酸酐固化，常需催化剂。 | 1.0 | Reaction principle: 环氧-酸酐固化，常需催化剂。 |
| reaction_b793ac896a4f | 0.017839 | reaction::环氧-羧酸开环酯化。 | 1.0 | Reaction principle: 环氧-羧酸开环酯化。 |

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
