# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 190.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 6

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 19
- Total authority weight: 19.000
- Posterior entropy: 3.284226
- MAP principle: reaction_a5dd26ae10ad
- Target guard: True within 5.00 C

## External Evidence

- External ledger enabled: True
- Accepted external rows: 13
- Rejected external rows: 0
- External source counts: {'surrogate': 13}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | guard active | feasible candidates | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| 1 | 187.18 | 2.82 | 0.5687 | target_guard_ids_min_regret2_over_information | True | 3 | 0 | - |
| 2 | 189.84 | 0.16 | 0.9689 | target_guard_ids_min_regret2_over_information | True | 12 | 0 | - |
| 3 | 189.74 | 0.26 | 0.9489 | target_guard_ids_min_regret2_over_information | True | 10 | 0 | - |
| 4 | 188.69 | 1.31 | 0.7702 | target_guard_ids_min_regret2_over_information | True | 10 | 0 | - |
| 5 | 188.78 | 1.22 | 0.7836 | target_guard_ids_min_regret2_over_information | True | 4 | 0 | - |
| 6 | 190.06 | 0.06 | 0.9886 | target_guard_ids_min_regret2_over_information | True | 10 | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| reaction_a5dd26ae10ad | 0.093122 | reaction::异氰酸酯-伯胺形成聚脲。 | 1.0 | Reaction principle: 异氰酸酯-伯胺形成聚脲。 |
| stereochemical_complexity_penalty | 0.092291 | stereochemical_complexity_risk | -1.0 | Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability. |
| reaction_839cd29ef5d7 | 0.046395 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |
| long_aliphatic_penalty | 0.045547 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| aromatic_backbones_raise_tg | 0.042067 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.042067 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| sulfone_diamine_rigidity | 0.042067 | sulfone_linker | 1.0 | Sulfone-linked aromatic diamines are common high-Tg hard segments. |
| high_functionality_crosslink_density | 0.042067 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| peg_like_penalty | 0.042067 | peg_like_risk | -1.0 | PEG-like segments are a strong low-Tg risk. |
| peptide_like_out_of_domain | 0.042067 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| formal_charge_practical_penalty | 0.042067 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.042067 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.042067 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.042067 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.042067 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.042067 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| druglike_hetero_complexity_penalty | 0.036167 | druglike_hetero_complexity_risk | -1.0 | High HBA/HBD complexity is a risk for out-of-library monomer transfer. |
| too_flexible_penalty | 0.028541 | too_flexible_risk | -1.0 | High rotatable-bond count increases flexibility risk. |
| reaction_8122f963caab | 0.015221 | reaction::环氧-酸酐固化，常需催化剂。 | 1.0 | Reaction principle: 环氧-酸酐固化，常需催化剂。 |
| flexible_ether_penalty | 0.014780 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| imide_anhydride_networks_raise_tg | 0.014547 | imide_or_anhydride | 1.0 | Imide or anhydride-derived networks often provide high Tg. |
| reaction_536dfe22d324 | 0.009197 | reaction::氰酸酯-胺共反应。 | 1.0 | Reaction principle: 氰酸酯-胺共反应。 |
| cyanate_ester_triazine | 0.008880 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.008880 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| reaction_5cde50869441 | 0.005918 | reaction::环氧-仲胺开环固化。 | 1.0 | Reaction principle: 环氧-仲胺开环固化。 |

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
