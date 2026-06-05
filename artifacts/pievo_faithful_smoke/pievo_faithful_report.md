# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 250.00 C
- Reward: exp(-abs(predicted_Tg - target_Tg) / 5.00)
- Rounds: 4

## PiEvo State

- Active principles: 40
- Posterior entropy: 3.663544
- MAP principle: aromatic_backbones_raise_tg

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| 1 | 267.69 | 17.69 | 0.0291 | warmup_max_variance | 0 | - |
| 2 | 156.51 | 93.49 | 0.0000 | warmup_max_variance | 0 | - |
| 3 | 230.51 | 19.49 | 0.0203 | ids_min_regret2_over_information | 0 | - |
| 4 | 266.89 | 16.89 | 0.0341 | ids_min_regret2_over_information | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| aromatic_backbones_raise_tg | 0.025766 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.025766 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| imide_anhydride_networks_raise_tg | 0.025766 | imide_or_anhydride | 1.0 | Imide or anhydride-derived networks often provide high Tg. |
| cyanate_ester_triazine | 0.025766 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.025766 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| sulfone_diamine_rigidity | 0.025766 | sulfone_linker | 1.0 | Sulfone-linked aromatic diamines are common high-Tg hard segments. |
| high_functionality_crosslink_density | 0.025766 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| flexible_ether_penalty | 0.025766 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| peg_like_penalty | 0.025766 | peg_like_risk | -1.0 | PEG-like segments are a strong low-Tg risk. |
| long_aliphatic_penalty | 0.025766 | long_aliphatic_risk | -1.0 | Long aliphatic segments usually lower Tg. |
| peptide_like_out_of_domain | 0.025766 | peptide_like_risk | -1.0 | Peptide-like ChEMBL molecules are poor monomer hypotheses. |
| too_flexible_penalty | 0.025766 | too_flexible_risk | -1.0 | High rotatable-bond count increases flexibility risk. |
| heavy_halogen_practical_risk | 0.025766 | heavy_halogen_risk | -1.0 | Iodinated or brominated drug-like structures are lower-priority monomer hypotheses. |
| stereochemical_complexity_penalty | 0.025766 | stereochemical_complexity_risk | -1.0 | Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability. |
| druglike_hetero_complexity_penalty | 0.025766 | druglike_hetero_complexity_risk | -1.0 | High HBA/HBD complexity is a risk for out-of-library monomer transfer. |
| formal_charge_practical_penalty | 0.025766 | formal_charge_practical_risk | -1.0 | Charged molecules are lower-priority thermoset monomer hypotheses unless specifically justified. |
| reaction_1d41d1c7896e | 0.025766 | reaction::酸酐-酚羟基酯化。 | 1.0 | Reaction principle: 酸酐-酚羟基酯化。 |
| reaction_bc75cf8f07d2 | 0.025766 | reaction::异氰酸酯-酚羟基形成氨基甲酸酯。 | 1.0 | Reaction principle: 异氰酸酯-酚羟基形成氨基甲酸酯。 |
| reaction_michael_thiol_ene | 0.025766 | reaction::硫醇-Michael/thiol-ene 反应。 | 1.0 | Reaction principle: 硫醇-Michael/thiol-ene 反应。 |
| reaction_bd312644298f | 0.025766 | reaction::自由基共聚。 | 1.0 | Reaction principle: 自由基共聚。 |
| reaction_461e81fa276b | 0.025766 | reaction::自由基均/共聚形成交联网络。 | 1.0 | Reaction principle: 自由基均/共聚形成交联网络。 |
| reaction_michael | 0.025766 | reaction::马来酰亚胺-硫醇 Michael 加成。 | 1.0 | Reaction principle: 马来酰亚胺-硫醇 Michael 加成。 |
| reaction_aab22a9380a2 | 0.025766 | reaction::马来酰亚胺与烯基共聚/加成。 | 1.0 | Reaction principle: 马来酰亚胺与烯基共聚/加成。 |
| reaction_ee82a65db02c | 0.025611 | reaction::氰酸酯三聚形成三嗪网络。 | 1.0 | Reaction principle: 氰酸酯三聚形成三嗪网络。 |
| reaction_839cd29ef5d7 | 0.025462 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |

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
- A principle with low posterior is not deleted immediately; it should be dormant/pruned only after enough independent observations.
- Real synthesis/DSC observations should be appended as higher-authority evidence and can override surrogate-only beliefs.
