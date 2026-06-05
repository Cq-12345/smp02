# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 195.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 4

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 46
- Total authority weight: 46.000
- Posterior entropy: 3.353029
- MAP principle: reaction_839cd29ef5d7
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
| 1 | 197.11 | 2.11 | 0.6561 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 2 | 195.12 | 0.12 | 0.9765 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 3 | 195.06 | 0.06 | 0.9883 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 4 | 195.58 | 0.58 | 0.8898 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| reaction_839cd29ef5d7 | 0.074072 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |
| flexible_ether_penalty | 0.072867 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| reaction_a5dd26ae10ad | 0.071747 | reaction::异氰酸酯-伯胺形成聚脲。 | 1.0 | Reaction principle: 异氰酸酯-伯胺形成聚脲。 |
| druglike_hetero_complexity_penalty | 0.069853 | druglike_hetero_complexity_risk | -1.0 | High HBA/HBD complexity is a risk for out-of-library monomer transfer. |
| reaction_b793ac896a4f | 0.069398 | reaction::环氧-羧酸开环酯化。 | 1.0 | Reaction principle: 环氧-羧酸开环酯化。 |
| reaction_7deb10577c5e | 0.068136 | reaction::酸酐-胺开环形成酰胺酸。 | 1.0 | Reaction principle: 酸酐-胺开环形成酰胺酸。 |
| aromatic_backbones_raise_tg | 0.029499 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.029499 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| high_functionality_crosslink_density | 0.029499 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| peptide_like_out_of_domain | 0.029499 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| heavy_halogen_practical_risk | 0.029499 | heavy_halogen_risk | -1.0 | Iodinated or brominated drug-like structures are lower-priority monomer hypotheses. |
| formal_charge_practical_penalty | 0.029499 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.029499 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.029499 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.029499 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.029499 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.029499 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| reaction_michael | 0.028849 | reaction::马来酰亚胺-硫醇 Michael 加成。 | 1.0 | Reaction principle: 马来酰亚胺-硫醇 Michael 加成。 |
| cyanate_ester_triazine | 0.017513 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.017513 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| reaction_536dfe22d324 | 0.017181 | reaction::氰酸酯-胺共反应。 | 1.0 | Reaction principle: 氰酸酯-胺共反应。 |
| long_aliphatic_penalty | 0.016751 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| maleimide_rigid_network | 0.016460 | maleimide | 1.0 | Bismaleimide motifs can create rigid high-Tg networks. |
| imide_anhydride_networks_raise_tg | 0.016301 | imide_or_anhydride | 1.0 | Imide or anhydride-derived networks often provide high Tg. |
| stereochemical_complexity_penalty | 0.015897 | stereochemical_complexity_risk | -1.0 | Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability. |

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
