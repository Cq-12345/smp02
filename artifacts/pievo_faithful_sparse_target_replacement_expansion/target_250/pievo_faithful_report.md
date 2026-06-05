# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 250.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 6

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 48
- Total authority weight: 48.000
- Posterior entropy: 3.277193
- MAP principle: reaction_cc7f1a60f1af
- Target guard: True within 5.00 C
- Predictor ensemble disagreement: False
- Ensemble disagreement guard: False within std <= 25.00 C

## External Evidence

- External ledger enabled: True
- Accepted external rows: 42
- Rejected external rows: 0
- External source counts: {'surrogate': 42}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | target guard | ensemble guard | risk-feasible candidates | ensemble std (C) | review | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- | ---: | --- |
| 1 | 251.40 | 1.40 | 0.7561 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 2 | 249.17 | 0.83 | 0.8471 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 3 | 249.47 | 0.53 | 0.8995 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 4 | 249.90 | 0.10 | 0.9804 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 5 | 249.86 | 0.14 | 0.9718 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 6 | 249.79 | 0.21 | 0.9581 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| reaction_cc7f1a60f1af | 0.180699 | reaction::环氧-羟基醚化，常需催化剂。 | 1.0 | Reaction principle: 环氧-羟基醚化，常需催化剂。 |
| aromatic_backbones_raise_tg | 0.036350 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.036350 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| cyanate_ester_triazine | 0.036350 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.036350 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| high_functionality_crosslink_density | 0.036350 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| peptide_like_out_of_domain | 0.036350 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| formal_charge_practical_penalty | 0.036350 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.036350 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.036350 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.036350 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.036350 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.036350 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| heavy_halogen_practical_risk | 0.036200 | heavy_halogen_risk | -1.0 | Iodinated or brominated drug-like structures are lower-priority monomer hypotheses. |
| reaction_aab22a9380a2 | 0.036199 | reaction::马来酰亚胺与烯基共聚/加成。 | 1.0 | Reaction principle: 马来酰亚胺与烯基共聚/加成。 |
| reaction_michael | 0.036198 | reaction::马来酰亚胺-硫醇 Michael 加成。 | 1.0 | Reaction principle: 马来酰亚胺-硫醇 Michael 加成。 |
| reaction_839cd29ef5d7 | 0.035649 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |
| reaction_5cde50869441 | 0.018083 | reaction::环氧-仲胺开环固化。 | 1.0 | Reaction principle: 环氧-仲胺开环固化。 |
| reaction_b793ac896a4f | 0.018083 | reaction::环氧-羧酸开环酯化。 | 1.0 | Reaction principle: 环氧-羧酸开环酯化。 |
| reaction_aaba7fbe7783 | 0.018083 | reaction::异氰酸酯-羟基形成聚氨酯。 | 1.0 | Reaction principle: 异氰酸酯-羟基形成聚氨酯。 |
| reaction_a67f85420c33 | 0.018083 | reaction::异氰酸酯-仲胺形成脲键。 | 1.0 | Reaction principle: 异氰酸酯-仲胺形成脲键。 |
| reaction_1ef23bb55506 | 0.018083 | reaction::硫醇-烯点击反应。 | 1.0 | Reaction principle: 硫醇-烯点击反应。 |
| reaction_2ee4496097cb | 0.018083 | reaction::氰酸酯-酚共固化/催化三聚。 | 1.0 | Reaction principle: 氰酸酯-酚共固化/催化三聚。 |
| reaction_536dfe22d324 | 0.018083 | reaction::氰酸酯-胺共反应。 | 1.0 | Reaction principle: 氰酸酯-胺共反应。 |
| reaction_ee82a65db02c | 0.018083 | reaction::氰酸酯三聚形成三嗪网络。 | 1.0 | Reaction principle: 氰酸酯三聚形成三嗪网络。 |

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
