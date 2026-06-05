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
- Posterior entropy: 3.556355
- MAP principle: reaction_839cd29ef5d7
- Target guard: True within 5.00 C

## External Evidence

- External ledger enabled: True
- Accepted external rows: 2
- Rejected external rows: 0
- External source counts: {'surrogate': 1, 'real_dsc': 1}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | guard active | feasible candidates | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| 1 | 251.19 | 1.19 | 0.7879 | target_guard_ids_min_regret2_over_information | True | 5 | 0 | - |
| 2 | 246.85 | 3.15 | 0.5330 | target_guard_ids_min_regret2_over_information | True | 8 | 0 | - |
| 3 | 251.72 | 1.72 | 0.7089 | target_guard_ids_min_regret2_over_information | True | 11 | 0 | - |
| 4 | 249.63 | 0.37 | 0.9296 | target_guard_ids_min_regret2_over_information | True | 10 | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| reaction_839cd29ef5d7 | 0.041531 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |
| reaction_8122f963caab | 0.041531 | reaction::环氧-酸酐固化，常需催化剂。 | 1.0 | Reaction principle: 环氧-酸酐固化，常需催化剂。 |
| reaction_b793ac896a4f | 0.041531 | reaction::环氧-羧酸开环酯化。 | 1.0 | Reaction principle: 环氧-羧酸开环酯化。 |
| reaction_cc7f1a60f1af | 0.041531 | reaction::环氧-羟基醚化，常需催化剂。 | 1.0 | Reaction principle: 环氧-羟基醚化，常需催化剂。 |
| reaction_2f387d801461 | 0.041531 | reaction::酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 | 1.0 | Reaction principle: 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 |
| reaction_7deb10577c5e | 0.041531 | reaction::酸酐-胺开环形成酰胺酸。 | 1.0 | Reaction principle: 酸酐-胺开环形成酰胺酸。 |
| reaction_e3ab71c1126b | 0.041531 | reaction::酸酐-羟基酯化。 | 1.0 | Reaction principle: 酸酐-羟基酯化。 |
| reaction_aaba7fbe7783 | 0.041531 | reaction::异氰酸酯-羟基形成聚氨酯。 | 1.0 | Reaction principle: 异氰酸酯-羟基形成聚氨酯。 |
| reaction_a5dd26ae10ad | 0.041531 | reaction::异氰酸酯-伯胺形成聚脲。 | 1.0 | Reaction principle: 异氰酸酯-伯胺形成聚脲。 |
| reaction_a67f85420c33 | 0.041531 | reaction::异氰酸酯-仲胺形成脲键。 | 1.0 | Reaction principle: 异氰酸酯-仲胺形成脲键。 |
| reaction_1ef23bb55506 | 0.041531 | reaction::硫醇-烯点击反应。 | 1.0 | Reaction principle: 硫醇-烯点击反应。 |
| reaction_ee82a65db02c | 0.041531 | reaction::氰酸酯三聚形成三嗪网络。 | 1.0 | Reaction principle: 氰酸酯三聚形成三嗪网络。 |
| reaction_2ee4496097cb | 0.041531 | reaction::氰酸酯-酚共固化/催化三聚。 | 1.0 | Reaction principle: 氰酸酯-酚共固化/催化三聚。 |
| reaction_536dfe22d324 | 0.041531 | reaction::氰酸酯-胺共反应。 | 1.0 | Reaction principle: 氰酸酯-胺共反应。 |
| aromatic_backbones_raise_tg | 0.017215 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.017215 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| cyanate_ester_triazine | 0.017215 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.017215 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| high_functionality_crosslink_density | 0.017215 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| flexible_ether_penalty | 0.017215 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| peg_like_penalty | 0.017215 | peg_like_risk | -1.0 | PEG-like segments are a strong low-Tg risk. |
| long_aliphatic_penalty | 0.017215 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| peptide_like_out_of_domain | 0.017215 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| too_flexible_penalty | 0.017215 | too_flexible_risk | -1.0 | High rotatable-bond count increases flexibility risk. |
| heavy_halogen_practical_risk | 0.017215 | heavy_halogen_risk | -1.0 | Iodinated or brominated drug-like structures are lower-priority monomer hypotheses. |

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
