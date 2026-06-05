# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 250.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 4

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 6
- Total authority weight: 10.000
- Posterior entropy: 3.663558
- MAP principle: maleimide_rigid_network

## External Evidence

- External ledger enabled: True
- Accepted external rows: 2
- Rejected external rows: 0
- External source counts: {'surrogate': 1, 'real_dsc': 1}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| 1 | 267.69 | 17.69 | 0.0291 | ids_min_regret2_over_information | 0 | - |
| 2 | 249.17 | 0.83 | 0.8471 | ids_min_regret2_over_information | 0 | - |
| 3 | 249.63 | 0.37 | 0.9296 | ids_min_regret2_over_information | 0 | - |
| 4 | 249.32 | 0.68 | 0.8732 | ids_min_regret2_over_information | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| maleimide_rigid_network | 0.025713 | maleimide | 1.0 | Bismaleimide motifs can create rigid high-Tg networks. |
| reaction_5cde50869441 | 0.025713 | reaction::环氧-仲胺开环固化。 | 1.0 | Reaction principle: 环氧-仲胺开环固化。 |
| aromatic_backbones_raise_tg | 0.025709 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.025709 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| cyanate_ester_triazine | 0.025709 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.025709 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| high_functionality_crosslink_density | 0.025709 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| flexible_ether_penalty | 0.025709 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| peg_like_penalty | 0.025709 | peg_like_risk | -1.0 | PEG-like segments are a strong low-Tg risk. |
| long_aliphatic_penalty | 0.025709 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| peptide_like_out_of_domain | 0.025709 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| too_flexible_penalty | 0.025709 | too_flexible_risk | -1.0 | High rotatable-bond count increases flexibility risk. |
| heavy_halogen_practical_risk | 0.025709 | heavy_halogen_risk | -1.0 | Iodinated or brominated drug-like structures are lower-priority monomer hypotheses. |
| druglike_hetero_complexity_penalty | 0.025709 | druglike_hetero_complexity_risk | -1.0 | High HBA/HBD complexity is a risk for out-of-library monomer transfer. |
| formal_charge_practical_penalty | 0.025709 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.025709 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.025709 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.025709 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.025709 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.025709 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| sulfone_diamine_rigidity | 0.025707 | sulfone_linker | 1.0 | Sulfone-linked aromatic diamines are common high-Tg hard segments. |
| reaction_839cd29ef5d7 | 0.025562 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |
| reaction_8122f963caab | 0.025562 | reaction::环氧-酸酐固化，常需催化剂。 | 1.0 | Reaction principle: 环氧-酸酐固化，常需催化剂。 |
| reaction_b793ac896a4f | 0.025562 | reaction::环氧-羧酸开环酯化。 | 1.0 | Reaction principle: 环氧-羧酸开环酯化。 |
| reaction_cc7f1a60f1af | 0.025562 | reaction::环氧-羟基醚化，常需催化剂。 | 1.0 | Reaction principle: 环氧-羟基醚化，常需催化剂。 |

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
