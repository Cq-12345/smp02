# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 195.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 6

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 17
- Total authority weight: 17.000
- Posterior entropy: 1.304661
- MAP principle: long_aliphatic_penalty
- Target guard: True within 5.00 C

## External Evidence

- External ledger enabled: True
- Accepted external rows: 11
- Rejected external rows: 0
- External source counts: {'surrogate': 11}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | guard active | feasible candidates | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| 1 | 195.98 | 0.98 | 0.8214 | target_guard_ids_min_regret2_over_information | True | 3 | 0 | - |
| 2 | 195.28 | 0.28 | 0.9454 | target_guard_ids_min_regret2_over_information | True | 10 | 0 | - |
| 3 | 194.99 | 0.01 | 0.9989 | target_guard_ids_min_regret2_over_information | True | 11 | 0 | - |
| 4 | 195.88 | 0.88 | 0.8387 | target_guard_ids_min_regret2_over_information | True | 8 | 0 | - |
| 5 | 195.78 | 0.78 | 0.8553 | target_guard_ids_min_regret2_over_information | True | 9 | 0 | - |
| 6 | 196.11 | 1.11 | 0.8015 | target_guard_ids_min_regret2_over_information | True | 11 | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| long_aliphatic_penalty | 0.769864 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| reaction_a5dd26ae10ad | 0.022402 | reaction::异氰酸酯-伯胺形成聚脲。 | 1.0 | Reaction principle: 异氰酸酯-伯胺形成聚脲。 |
| druglike_hetero_complexity_penalty | 0.014540 | druglike_hetero_complexity_risk | -1.0 | High HBA/HBD complexity is a risk for out-of-library monomer transfer. |
| stereochemical_complexity_penalty | 0.013138 | stereochemical_complexity_risk | -1.0 | Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability. |
| too_flexible_penalty | 0.013108 | too_flexible_risk | -1.0 | High rotatable-bond count increases flexibility risk. |
| reaction_536dfe22d324 | 0.012910 | reaction::氰酸酯-胺共反应。 | 1.0 | Reaction principle: 氰酸酯-胺共反应。 |
| cyanate_ester_triazine | 0.012910 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.012910 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| reaction_839cd29ef5d7 | 0.010155 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |
| aromatic_backbones_raise_tg | 0.007372 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.007372 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| high_functionality_crosslink_density | 0.007372 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| peg_like_penalty | 0.007372 | peg_like_risk | -1.0 | PEG-like segments are a strong low-Tg risk. |
| peptide_like_out_of_domain | 0.007372 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| formal_charge_practical_penalty | 0.007372 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.007372 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.007372 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.007372 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.007372 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.007372 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| reaction_aab22a9380a2 | 0.002280 | reaction::马来酰亚胺与烯基共聚/加成。 | 1.0 | Reaction principle: 马来酰亚胺与烯基共聚/加成。 |
| reaction_michael | 0.002280 | reaction::马来酰亚胺-硫醇 Michael 加成。 | 1.0 | Reaction principle: 马来酰亚胺-硫醇 Michael 加成。 |
| reaction_5cde50869441 | 0.002082 | reaction::环氧-仲胺开环固化。 | 1.0 | Reaction principle: 环氧-仲胺开环固化。 |
| reaction_8122f963caab | 0.002082 | reaction::环氧-酸酐固化，常需催化剂。 | 1.0 | Reaction principle: 环氧-酸酐固化，常需催化剂。 |
| reaction_b793ac896a4f | 0.002082 | reaction::环氧-羧酸开环酯化。 | 1.0 | Reaction principle: 环氧-羧酸开环酯化。 |

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
