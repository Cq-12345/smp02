# 250 C Out-of-Library SMP Formula Agent Report

## Run Summary

- Target Tg: 250.0 C.
- Target window for near-hit counting: +/- 5.0 C.
- Components searched: n=1..4.
- Require at least one out-of-library component: True.
- Pool stats: library=120, generated=10, chembl=120, chembl_scanned=1695.
- Iterations: 2; samples per iteration: 2500.
- Selected hard-constraint validation: True (80 rows checked).

## Recommended Candidates

Ranked by `agent_score`, which balances target distance, GPR uncertainty, OOD distance, soft priors, novelty, and component-count cost. The closest-by-Tg table is saved separately as `closest_formulations.csv`.

| Rank | n | Agent score | Tg mean +/- sigma (C) | Distance (C) | OOD | Sources | Ratios | Compatibility | SMILES |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 3 | -0.82 | 250.23 +/- 51.74 | 0.23 | 1.90 | library|chembl|generated | 0.53779:0.33602:0.12619 | 马来酰亚胺-胺 Michael 加成。|马来酰亚胺与烯基共聚/加成。 | `CC(C)(c1occc1CN)c1occc1CN|Cn1cc(C2=C(c3coc4ccccc34)C(=O)NC2=O)c2ccc(O)cc21|O=C1C=CC(=O)N1c1ccc(Oc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 2 | 4 | -0.23 | 249.68 +/- 64.90 | 0.32 | 1.90 | library|chembl|chembl|chembl | 0.17187:0.30901:0.45027:0.06885 | 马来酰亚胺-胺 Michael 加成。 | `CC(C)(c1ccc(N)cc1)c1ccc(C(C)(C)c2ccc(N)cc2)cc1|CC1=C(C#N)c2nc(N)c(C#N)c(C)c2/C1=C/c1ccc(-c2ccccc2C(=O)O)o1|COc1ccccc1C1=C(Nc2ccccc2)C(=O)NC1=O|CS(=O)(=O)Nc1cccc(-c2nc(C(c3ccc(F)cc3)c3ccc(F)cc3)sc2CC(=O)O)c1` |
| 3 | 3 | -0.09 | 250.42 +/- 61.70 | 0.42 | 3.30 | library|chembl|generated | 0.37595:0.06688:0.55717 | 氰酸酯-胺共反应。|酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 | `CC(C)(c1ccc(OC#N)cc1)c1ccc(OC#N)cc1|NC(=O)Nc1sc(-c2ccc(CN3CCCCC3)cc2)cc1C(N)=O|O=C(c1ccc2c(c1)C(=O)OC2=O)c1ccc2c(c1)C(=O)OC2=O` |
| 4 | 4 | 0.05 | 248.72 +/- 35.42 | 1.28 | 2.11 | library|library|chembl|library | 0.34878:0.13571:0.18729:0.32822 | 环氧-仲胺开环固化。|环氧-羟基醚化，常需催化剂。|环氧-酸酐固化，常需催化剂。|酸酐-胺开环形成酰胺酸。 | `C=CCc1ccc(OCC2CO2)c(-c2cc(CC=C)ccc2OCC2CO2)c1|COc1cc(C(c2cc(C)c(O)c(O)c2)c2cc(C)c(O)c(O)c2)ccc1OCC1CO1|Cc1ccc(NC(=O)Nc2ccccc2)c(C)c1|O=C1CCCC(=O)O1` |
| 5 | 2 | 0.06 | 250.51 +/- 34.72 | 0.51 | 2.25 | library|chembl | 0.85000:0.15000 | 氰酸酯-酚共固化/催化三聚。 | `N#COc1ccc(CC2CCCC(Cc3ccc(OC#N)cc3)C2)cc1|O=C1NC(=O)c2ccc(I)cc2/C1=C/NCc1ccc(-c2ccoc2)c(O)c1` |
| 6 | 2 | 0.13 | 249.94 +/- 57.54 | 0.06 | 1.79 | library|chembl | 0.55000:0.45000 | 马来酰亚胺-胺 Michael 加成。 | `CC(C)(c1occc1CN)c1occc1CN|Cn1cc(C2=C(c3coc4ccccc34)C(=O)NC2=O)c2ccc(O)cc21` |
| 7 | 2 | 0.28 | 249.15 +/- 40.61 | 0.85 | 1.34 | chembl|library | 0.41286:0.58714 | 酸酐-羟基酯化。 | `COc1ccc2c(O)cc(OC)c(O)c2c1O|O=C1OC(=O)c2cc(Oc3ccc4c(c3)C(=O)OC4=O)ccc21` |
| 8 | 3 | 0.42 | 249.57 +/- 61.48 | 0.43 | 2.56 | chembl|chembl|generated | 0.36328:0.54325:0.09347 | 酸酐-羟基酯化。|酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 | `Nc1nc(N)nc(SCC(=O)NCc2ccc(F)cc2)n1|O=C(C1=C(O)c2ccccc2S(=O)(=O)N1Cc1ccccc1)c1ccccc1|O=C(c1ccc2c(c1)C(=O)OC2=O)c1ccc2c(c1)C(=O)OC2=O` |
| 9 | 2 | 0.48 | 249.11 +/- 51.74 | 0.89 | 2.32 | generated|generated | 0.28681:0.71319 | 马来酰亚胺-胺 Michael 加成。 | `CC(C)(c1ccc(N)cc1)c1ccc(N)cc1|O=C1C=CC(=O)N1c1ccc(Oc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 10 | 2 | 0.60 | 250.13 +/- 44.15 | 0.13 | 1.72 | generated|library | 0.25000:0.75000 | 氰酸酯-胺共反应。 | `CC(C)(c1ccc(N)cc1)c1ccc(N)cc1|N#COc1ccc(CC2CCCC(Cc3ccc(OC#N)cc3)C2)cc1` |
| 11 | 2 | 0.62 | 249.72 +/- 51.49 | 0.28 | 1.59 | chembl|library | 0.75000:0.25000 | 酸酐-羟基酯化。 | `COc1c(O)cc(O)c(C(=N)Cc2ccc(O)cc2)c1O|O=C1OC(=O)c2cc(Oc3ccc4c(c3)C(=O)OC4=O)ccc21` |
| 12 | 2 | 0.72 | 249.57 +/- 55.83 | 0.43 | 2.70 | library|generated | 0.25000:0.75000 | 马来酰亚胺-胺 Michael 加成。 | `Nc1ccc(-c2ccc(N)c(N)c2)c(N)c1|O=C1C=CC(=O)N1c1ccc(Oc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 13 | 2 | 0.73 | 250.99 +/- 48.13 | 0.99 | 2.44 | library|generated | 0.35000:0.65000 | 马来酰亚胺-胺 Michael 加成。 | `Nc1ccc(-c2nc3ccc(N)cc3[nH]2)cc1|O=C1C=CC(=O)N1c1ccc(Oc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 14 | 2 | 0.75 | 250.07 +/- 68.63 | 0.07 | 3.01 | chembl|library | 0.65000:0.35000 | 马来酰亚胺-胺 Michael 加成。 | `COc1ccccc1C1=C(Nc2ccccc2)C(=O)NC1=O|Nc1cccc(S(=O)(=O)c2cccc(N)c2)c1` |
| 15 | 2 | 0.79 | 249.79 +/- 63.16 | 0.21 | 2.27 | library|generated | 0.75000:0.25000 | 马来酰亚胺-胺 Michael 加成。 | `Nc1ccc(Oc2ccc(N)cc2)cc1|O=C1C=CC(=O)N1c1ccc(Oc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 16 | 2 | 0.81 | 251.37 +/- 48.23 | 1.37 | 1.58 | library|generated | 0.45000:0.55000 | 马来酰亚胺-胺 Michael 加成。 | `Nc1ccc(SSc2ccc(N)cc2)cc1|O=C1C=CC(=O)N1c1ccc(Oc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 17 | 2 | 0.97 | 250.12 +/- 66.17 | 0.12 | 2.52 | chembl|library | 0.25000:0.75000 | 马来酰亚胺-胺 Michael 加成。 | `Cn1cc(C2=C(c3coc4ccccc34)C(=O)NC2=O)c2ccc(O)cc21|Nc1ccc(Cc2ccc(N)cc2)cc1` |
| 18 | 2 | 1.00 | 250.18 +/- 69.49 | 0.18 | 2.29 | chembl|chembl | 0.45000:0.55000 | 马来酰亚胺与烯基共聚/加成。 | `C/C(=C\CC1OC(=O)NC1=O)c1cccc(OCCc2nc(-c3ccccc3)oc2C)c1|Cn1cc(C2=C(c3coc4ccccc34)C(=O)NC2=O)c2ccc(O)cc21` |
| 19 | 2 | 1.05 | 249.55 +/- 72.59 | 0.45 | 1.65 | chembl|chembl | 0.50429:0.49571 | 马来酰亚胺与烯基共聚/加成。 | `CC(C)=CCC/C(C)=C/Cc1c(O)cc(/C=C/c2ccccc2)cc1O|COc1ccccc1C1=C(Nc2ccccc2)C(=O)NC1=O` |
| 20 | 2 | 1.10 | 249.38 +/- 62.28 | 0.62 | 3.29 | chembl|library | 0.15000:0.85000 | 马来酰亚胺-胺 Michael 加成。 | `N#Cc1c(N)nc(Sc2ccc(O)cc2)c(C#N)c1-c1ccc(Cl)cc1|O=C1C=CC(=O)N1c1ccc(Cc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 21 | 3 | 1.11 | 248.15 +/- 40.74 | 1.85 | 1.76 | library|chembl|library | 0.56900:0.11254:0.31846 | 酸酐-羟基酯化。|酸酐-胺开环形成酰胺酸。 | `CC(C)(O)C(=O)c1ccc(OCCO)cc1|Cc1ccccc1Nc1nc(Nc2ccccc2C)nc(N2CCN(CCNc3ccnc4cc(Cl)ccc34)CC2)n1|O=C1OC(=O)c2cc(Oc3ccc4c(c3)C(=O)OC4=O)ccc21` |
| 22 | 2 | 1.29 | 251.44 +/- 47.10 | 1.44 | 0.95 | library|generated | 0.65000:0.35000 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 | `Nc1cccc(Oc2cccc(Oc3cccc(N)c3)c2)c1|O=C(c1ccc2c(c1)C(=O)OC2=O)c1ccc2c(c1)C(=O)OC2=O` |
| 23 | 2 | 1.30 | 248.92 +/- 56.20 | 1.08 | 1.58 | library|chembl | 0.55000:0.45000 | 氰酸酯-酚共固化/催化三聚。 | `CC(C)(c1ccc(OC#N)cc1)c1ccc(OC#N)cc1|O=S(=O)(c1ccc(Br)cc1)N1CCN(Cc2ccc3cccnc3c2O)CC1` |
| 24 | 2 | 1.36 | 251.76 +/- 34.33 | 1.76 | 2.26 | library|chembl | 0.85000:0.15000 | 氰酸酯-胺共反应。 | `N#COc1ccc(CC2CCCC(Cc3ccc(OC#N)cc3)C2)cc1|Nc1c(S(=O)(=O)O)cc(Nc2ccc(F)cc2)c2c1C(=O)c1ccccc1C2=O` |
| 25 | 2 | 1.37 | 248.86 +/- 46.93 | 1.14 | 1.92 | library|chembl | 0.65000:0.35000 | 氰酸酯-胺共反应。 | `N#COc1ccc(CC2CCCC(Cc3ccc(OC#N)cc3)C2)cc1|NC(=O)CCC(NS(=O)(=O)c1ccc(Cl)c2ccccc12)C(N)=O` |

## Iteration History

| Iteration | Generated | Best Tg (C) | Best distance (C) | Near target | Added principles |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 10160 | 250.01 | 0.01 | 376 | observed_chembl_transferable_monomers, observed_template_generated_monomers |
| 2 | 2500 | 250.02 | 0.02 | 89 | observed_three_or_more_component_blending |

## Current Top Soft Principles

| Principle | Confidence | Weight | Effect |
| --- | ---: | ---: | ---: |
| peptide_like_out_of_domain | 0.800 | 0.750 | -1.0 |
| imide_anhydride_networks_raise_tg | 0.702 | 0.850 | 1.0 |
| cyanate_ester_triazine | 0.603 | 0.900 | 1.0 |
| peg_like_penalty | 0.700 | 0.750 | -1.0 |
| maleimide_rigid_network | 0.585 | 0.750 | 1.0 |
| multi_aromatic_rigidity | 0.650 | 0.650 | 1.0 |
| aromatic_backbones_raise_tg | 0.700 | 0.550 | 1.0 |
| flexible_ether_penalty | 0.680 | 0.550 | -1.0 |
| high_functionality_crosslink_density | 0.620 | 0.550 | 1.0 |
| druglike_hetero_complexity_penalty | 0.612 | 0.500 | -1.0 |
| sulfone_diamine_rigidity | 0.552 | 0.550 | 1.0 |
| too_flexible_penalty | 0.627 | 0.450 | -1.0 |
| formal_charge_practical_penalty | 0.620 | 0.450 | -1.0 |
| long_aliphatic_penalty | 0.610 | 0.450 | -1.0 |
| heavy_halogen_practical_risk | 0.636 | 0.400 | -1.0 |
| nitrile_rich_rigidity | 0.557 | 0.450 | 1.0 |
| stereochemical_complexity_penalty | 0.612 | 0.400 | -1.0 |
| reaction_aaba7fbe7783 | 0.565 | 0.420 | 1.0 |
| reaction_8122f963caab | 0.565 | 0.420 | 1.0 |
| reaction_michael | 0.557 | 0.420 | 1.0 |

## Interpretation

- Hard constraints are deterministic and are not changed by the loop: RDKit validity, VAE encodability, ratio simplex, allowed atoms, and functional-group reaction graph validity.
- Soft priors are PiEvo-style beliefs. Their confidence is updated from in-silico predictor observations, so these are model-guidance beliefs, not experimental truth.
- A real synthesis/DSC result should be added as a stronger observation source and should override purely in-silico principle updates.
