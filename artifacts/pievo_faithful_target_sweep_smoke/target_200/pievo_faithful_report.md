# PiEvo-Faithful SMP Discovery Report

This run uses the VAE-WVCM predictor as the experiment environment, while the agent state follows PiEvo's principle-posterior mathematics.

## Objective

- Target Tg: 200.00 C
- Reward: exp(-abs(observed_or_predicted_Tg - target_Tg) / 5.00)
- Rounds: 4

## PiEvo State

- Active principles: 40
- Total observations in posterior history: 4
- Total authority weight: 4.000
- Posterior entropy: 3.663562
- MAP principle: maleimide_rigid_network

## External Evidence

- External ledger enabled: False
- Accepted external rows: 0
- Rejected external rows: 0
- External source counts: {}

## Selected Observations

| Round | Tg mean (C) | target distance (C) | reward | selected by | anomalies | added principles |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| 1 | 267.69 | 67.69 | 0.0000 | warmup_max_variance | 0 | - |
| 2 | 156.51 | 43.49 | 0.0002 | warmup_max_variance | 0 | - |
| 3 | 156.77 | 43.23 | 0.0002 | ids_min_regret2_over_information | 0 | - |
| 4 | 239.72 | 39.72 | 0.0004 | ids_min_regret2_over_information | 0 | - |

## Top Posterior Principles

| Principle | posterior | feature | effect | description |
| --- | ---: | --- | ---: | --- |
| maleimide_rigid_network | 0.025641 | maleimide | 1.0 | Bismaleimide motifs can create rigid high-Tg networks. |
| reaction_839cd29ef5d7 | 0.025641 | reaction::环氧-伯胺开环固化。 | 1.0 | Reaction principle: 环氧-伯胺开环固化。 |
| reaction_5cde50869441 | 0.025641 | reaction::环氧-仲胺开环固化。 | 1.0 | Reaction principle: 环氧-仲胺开环固化。 |
| reaction_8122f963caab | 0.025641 | reaction::环氧-酸酐固化，常需催化剂。 | 1.0 | Reaction principle: 环氧-酸酐固化，常需催化剂。 |
| reaction_b793ac896a4f | 0.025641 | reaction::环氧-羧酸开环酯化。 | 1.0 | Reaction principle: 环氧-羧酸开环酯化。 |
| reaction_cc7f1a60f1af | 0.025641 | reaction::环氧-羟基醚化，常需催化剂。 | 1.0 | Reaction principle: 环氧-羟基醚化，常需催化剂。 |
| reaction_2f387d801461 | 0.025641 | reaction::酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 | 1.0 | Reaction principle: 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 |
| reaction_7deb10577c5e | 0.025641 | reaction::酸酐-胺开环形成酰胺酸。 | 1.0 | Reaction principle: 酸酐-胺开环形成酰胺酸。 |
| reaction_e3ab71c1126b | 0.025641 | reaction::酸酐-羟基酯化。 | 1.0 | Reaction principle: 酸酐-羟基酯化。 |
| reaction_aaba7fbe7783 | 0.025641 | reaction::异氰酸酯-羟基形成聚氨酯。 | 1.0 | Reaction principle: 异氰酸酯-羟基形成聚氨酯。 |
| reaction_a5dd26ae10ad | 0.025641 | reaction::异氰酸酯-伯胺形成聚脲。 | 1.0 | Reaction principle: 异氰酸酯-伯胺形成聚脲。 |
| reaction_a67f85420c33 | 0.025641 | reaction::异氰酸酯-仲胺形成脲键。 | 1.0 | Reaction principle: 异氰酸酯-仲胺形成脲键。 |
| reaction_1ef23bb55506 | 0.025641 | reaction::硫醇-烯点击反应。 | 1.0 | Reaction principle: 硫醇-烯点击反应。 |
| reaction_2ee4496097cb | 0.025641 | reaction::氰酸酯-酚共固化/催化三聚。 | 1.0 | Reaction principle: 氰酸酯-酚共固化/催化三聚。 |
| reaction_536dfe22d324 | 0.025641 | reaction::氰酸酯-胺共反应。 | 1.0 | Reaction principle: 氰酸酯-胺共反应。 |
| imide_anhydride_networks_raise_tg | 0.025641 | imide_or_anhydride | 1.0 | Imide or anhydride-derived networks often provide high Tg. |
| stereochemical_complexity_penalty | 0.025641 | stereochemical_complexity_risk | -1.0 | Many stereocenters often indicate bioactive-molecule complexity rather than monomer suitability. |
| reaction_ee82a65db02c | 0.025641 | reaction::氰酸酯三聚形成三嗪网络。 | 1.0 | Reaction principle: 氰酸酯三聚形成三嗪网络。 |
| aromatic_backbones_raise_tg | 0.025641 | aromatic_backbone | 1.0 | Aromatic backbones tend to raise Tg. |
| multi_aromatic_rigidity | 0.025641 | rigid_multi_aromatic | 1.0 | Multiple aromatic rings increase chain rigidity. |
| cyanate_ester_triazine | 0.025641 | cyanate_ester | 1.0 | Cyanate ester triazine networks can be high Tg. |
| nitrile_rich_rigidity | 0.025641 | nitrile_rich | 1.0 | Nitrile-rich aromatic monomers often stiffen networks. |
| high_functionality_crosslink_density | 0.025641 | high_functionality | 1.0 | Higher reactive functionality can increase crosslink density. |
| flexible_ether_penalty | 0.025641 | flexible_ether_risk | -1.0 | Long flexible ether segments can lower Tg. |
| peg_like_penalty | 0.025641 | peg_like_risk | -1.0 | PEG-like segments are a strong low-Tg risk. |

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
