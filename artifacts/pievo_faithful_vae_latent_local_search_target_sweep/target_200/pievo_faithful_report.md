# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 200.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 4

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 45
- Total authority weight: 45.000
- Posterior entropy: 3.200494
- MAP principle: sulfone_diamine_rigidity
- Target guard: True within 5.00 C
- Predictor ensemble disagreement: False
- Ensemble disagreement guard: False within std <= 25.00 C

## External Evidence

- External ledger enabled: True
- Accepted external rows: 41
- Rejected external rows: 0
- External source counts: {'surrogate': 41}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | target guard | ensemble guard | risk-feasible candidates | ensemble std (C) | review | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- | ---: | --- |
| 1 | 201.80 | 1.80 | 0.6983 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 2 | 198.24 | 1.76 | 0.7033 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 3 | 199.80 | 0.20 | 0.9616 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |
| 4 | 199.96 | 0.04 | 0.9915 | target_guard_ids_min_regret2_over_information | True | False | 0 | - | - | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| sulfone_diamine_rigidity | 0.077824 | sulfone_linker | 1.0 | Sulfone-linked aromatic diamines are common high-Tg hard segments. |
| cyanate_ester_triazine | 0.073040 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.073040 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| reaction_536dfe22d324 | 0.072758 | reaction::氰酸酯-胺共反应。 | 1.0 | Reaction principle: 氰酸酯-胺共反应。 |
| stereochemical_complexity_penalty | 0.061571 | stereochemical_complexity_risk | -1.0 | Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability. |
| maleimide_rigid_network | 0.059750 | maleimide | 1.0 | Bismaleimide motifs can create rigid high-Tg networks. |
| imide_anhydride_networks_raise_tg | 0.059317 | imide_or_anhydride | 1.0 | Imide or anhydride-derived networks often provide high Tg. |
| long_aliphatic_penalty | 0.051361 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| reaction_a5dd26ae10ad | 0.043368 | reaction::异氰酸酯-伯胺形成聚脲。 | 1.0 | Reaction principle: 异氰酸酯-伯胺形成聚脲。 |
| reaction_aab22a9380a2 | 0.040678 | reaction::马来酰亚胺与烯基共聚/加成。 | 1.0 | Reaction principle: 马来酰亚胺与烯基共聚/加成。 |
| flexible_ether_penalty | 0.040503 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| peg_like_penalty | 0.040373 | peg_like_risk | -1.0 | PEG-like segments are a strong low-Tg risk. |
| reaction_5cde50869441 | 0.039770 | reaction::环氧-仲胺开环固化。 | 1.0 | Reaction principle: 环氧-仲胺开环固化。 |
| reaction_cc7f1a60f1af | 0.039139 | reaction::环氧-羟基醚化，常需催化剂。 | 1.0 | Reaction principle: 环氧-羟基醚化，常需催化剂。 |
| reaction_michael | 0.019570 | reaction::马来酰亚胺-硫醇 Michael 加成。 | 1.0 | Reaction principle: 马来酰亚胺-硫醇 Michael 加成。 |
| aromatic_backbones_raise_tg | 0.017026 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.017026 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| high_functionality_crosslink_density | 0.017026 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| peptide_like_out_of_domain | 0.017026 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| formal_charge_practical_penalty | 0.017026 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.017026 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.017026 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.017026 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.017026 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.017026 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |

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
