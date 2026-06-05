# 250 C Out-of-Library SMP Formula Agent Report

## Run Summary

- Target Tg: 250.0 C.
- Target window for near-hit counting: +/- 5.0 C.
- Components searched: n=1..4.
- Require at least one out-of-library component: True.
- Pool stats: library=179, generated=10, chembl=550, chembl_scanned=6590.
- Iterations: 6; samples per iteration: 18000.
- Selected hard-constraint validation: True (250 rows checked).

## Recommended Candidates

Ranked by `agent_score`, which balances target distance, GPR uncertainty, OOD distance, soft priors, novelty, and component-count cost. The closest-by-Tg table is saved separately as `closest_formulations.csv`.

| Rank | n | Agent score | Tg mean +/- sigma (C) | Distance (C) | OOD | Sources | Ratios | Compatibility | SMILES |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 3 | -2.42 | 249.68 +/- 38.57 | 0.32 | 1.62 | chembl|generated|library | 0.15909:0.18050:0.66041 | 氰酸酯-酚共固化/催化三聚。|酸酐-羟基酯化。 | `COc1ccc2c(O)cc(OC)c(O)c2c1O|N#COc1ccc(-c2ccc(OC#N)cc2)cc1|O=C1OC(=O)c2cc(Oc3ccc4c(c3)C(=O)OC4=O)ccc21` |
| 2 | 3 | -2.20 | 250.04 +/- 42.96 | 0.04 | 2.18 | library|chembl|chembl | 0.45541:0.29245:0.25214 | 氰酸酯-胺共反应。 | `CC(C)(c1ccc(OC#N)cc1)c1ccc(OC#N)cc1|COc1cc2nc(N3CCC(C(=O)NCc4ccccc4)CC3)nc(N)c2cc1OC|Nc1ccc(NS(=O)(=O)c2ccc(N3C(=O)c4ccccc4C3=O)cc2)cc1` |
| 3 | 4 | -1.83 | 250.05 +/- 53.39 | 0.05 | 1.93 | chembl|chembl|library|chembl | 0.26568:0.07808:0.35449:0.30175 | 氰酸酯-酚共固化/催化三聚。|马来酰亚胺与烯基共聚/加成。 | `CCN1C(=O)C=CC1=O|Cc1ccc(OC(=O)N(CC(=O)O)Cc2cccc(OCc3nc(-c4ccc(-c5ccccc5)cc4)oc3C)c2)cc1|N#COc1ccc(CC2CCCC(Cc3ccc(OC#N)cc3)C2)cc1|NS(=O)(=O)c1ccc(/C=C/c2cccc(O)c2)cc1` |
| 4 | 4 | -1.68 | 250.16 +/- 43.76 | 0.16 | 1.59 | library|chembl|chembl|generated | 0.34041:0.24343:0.08334:0.33282 | 马来酰亚胺-胺 Michael 加成。|马来酰亚胺与烯基共聚/加成。 | `C=CC(=O)OCc1ccccc1|NC(CO)(CO)CCc1ccc(-c2ccc(Sc3ccc(Cl)cc3)cc2F)cc1|Nc1nc(N)nc(SCC(=O)NCc2ccc(F)cc2)n1|O=C1C=CC(=O)N1c1ccc(Oc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 5 | 4 | -1.67 | 250.23 +/- 55.98 | 0.23 | 2.36 | chembl|chembl|chembl|library | 0.51927:0.24261:0.13483:0.10329 | 酸酐-羟基酯化。|酸酐-胺开环形成酰胺酸。|酸酐-胺形成聚酰胺酸/聚酰亚胺前体。|马来酰亚胺-胺 Michael 加成。 | `COc1ccc(S(=O)(=O)c2ccc(NC3=NCCN3)cc2)cc1|Cn1cc(C2=C(c3coc4ccccc34)C(=O)NC2=O)c2ccc(O)cc21|Nc1c(S(=O)(=O)O)cc(Nc2ccc(F)cc2)c2c1C(=O)c1ccccc1C2=O|O=C1CCCC(=O)O1` |
| 6 | 3 | -1.63 | 250.57 +/- 33.82 | 0.57 | 1.28 | chembl|library|generated | 0.39533:0.06957:0.53510 | 环氧-伯胺开环固化。|马来酰亚胺-胺 Michael 加成。 | `Nc1nc2ccc(Nc3ccccc3)cc2o1|O=C1C=CC(=O)N1c1ccc(Cc2ccc(N3C(=O)C=CC3=O)cc2)cc1|c1ccc(C(c2ccc(OCC3CO3)cc2)c2ccc(OCC3CO3)cc2)cc1` |
| 7 | 3 | -1.42 | 249.81 +/- 51.08 | 0.19 | 2.03 | chembl|chembl|chembl | 0.15177:0.37722:0.47101 | 马来酰亚胺-胺 Michael 加成。|马来酰亚胺与烯基共聚/加成。 | `CC1=C(C(=O)OC(C)(C)C)C(c2ccccc2)C=CN1c1ccccc1|Cn1cc(C2=C(c3coc4ccccc34)C(=O)NC2=O)c2ccc(O)cc21|Nc1nccc(Nc2ccc(S(N)(=O)=O)cc2)n1` |
| 8 | 4 | -0.86 | 249.86 +/- 66.63 | 0.14 | 3.08 | library|chembl|chembl|chembl | 0.18487:0.28913:0.42047:0.10553 | 硫醇-烯点击反应。|马来酰亚胺-硫醇 Michael 加成。|马来酰亚胺-胺 Michael 加成。|马来酰亚胺与烯基共聚/加成。 | `C=CCn1c(=O)n(CC=C)c(=O)n(CC=C)c1=O|CC1(C)CC(C)(C)c2cc(N/C(S)=N/c3ccc(S(N)(=O)=O)cc3)ccc2S1|COc1cc2nc(N3CCN(C(=O)/C=C/c4cccc(F)c4)CC3)nc(N)c2cc1OC|COc1ccccc1C1=C(Nc2ccccc2)C(=O)NC1=O` |
| 9 | 4 | -0.80 | 249.66 +/- 46.73 | 0.34 | 2.56 | library|chembl|chembl|generated | 0.26975:0.07554:0.51611:0.13860 | 氰酸酯-胺共反应。|环氧-仲胺开环固化。|环氧-伯胺开环固化。 | `COc1cc(CC2CO2)ccc1OC(=O)c1ccc(C(=O)Oc2ccc(CC3CO3)cc2OC)cc1|COc1ccc(/C=C/c2ccc(N)cc2)c(OC)c1|CS(=O)(=O)Nc1ccc(Sc2ccc(NC3=NCCN3)cc2)cc1|N#COc1ccc(-c2ccc(OC#N)cc2)cc1` |
| 10 | 3 | -0.74 | 250.20 +/- 45.65 | 0.20 | 2.28 | chembl|generated|library | 0.30992:0.32247:0.36761 | 环氧-仲胺开环固化。|环氧-羟基醚化，常需催化剂。 | `CN1C(=O)c2cc(Nc3ccccc3)c(Nc3ccccc3)cc2C1=O|O=S(=O)(c1ccc(O)cc1)c1ccc(O)cc1|c1cc(N(CC2CO2)CC2CO2)ccc1Cc1ccc(N(CC2CO2)CC2CO2)cc1` |
| 11 | 4 | -0.69 | 250.03 +/- 51.92 | 0.03 | 1.48 | chembl|chembl|generated|library | 0.29449:0.09420:0.44398:0.16733 | 氰酸酯-胺共反应。|环氧-仲胺开环固化。|环氧-伯胺开环固化。 | `CC(C)OC(=O)CC1C(C(=O)OC(C)C)=C(N)Oc2ccc(-c3ccccc3)cc21|COc1ccc(-n2c(C)cc(/C=C(\C#N)C(=O)OCC(=O)Nc3ccc(Cl)c(C(F)(F)F)c3)c2C)cc1|N#COc1ccc(-c2ccc(OC#N)cc2)cc1|O=c1cc(-c2ccc(OCC3CO3)cc2)oc2cc(OCC3CO3)ccc12` |
| 12 | 3 | -0.58 | 249.03 +/- 33.59 | 0.97 | 2.07 | library|chembl|chembl | 0.65233:0.19107:0.15660 | 环氧-伯胺开环固化。|环氧-羟基醚化，常需催化剂。 | `C=CCc1ccc(OCC2CO2)c(-c2cc(CC=C)ccc2OCC2CO2)c1|Nc1ccc(NS(=O)(=O)c2ccc(N3C(=O)c4ccccc4C3=O)cc2)cc1|O=c1oc2c(O)c(O)ccc2c2ccccc12` |
| 13 | 2 | -0.57 | 249.51 +/- 60.87 | 0.49 | 2.00 | chembl|generated | 0.45000:0.55000 | 氰酸酯-胺共反应。 | `Cn1cc(C2=C(c3cn(CCCCC(=N)N)c4ccccc34)C(=O)NC2=O)c2ccccc21|N#COc1ccc(-c2ccc(OC#N)cc2)cc1` |
| 14 | 4 | -0.56 | 250.11 +/- 49.77 | 0.11 | 2.53 | chembl|chembl|library|generated | 0.09899:0.09255:0.61126:0.19720 | 酸酐-羟基酯化。|酸酐-胺开环形成酰胺酸。 | `CCN(CC)c1ccc(Nc2cc3c(cc2Nc2ccc(N(CC)CC)cc2)C(=O)NC3=O)cc1|FC(F)(F)c1ccc(Sc2ccc(NC3=NCCN3)cc2)cc1|O=C1OC(=O)c2cc(Oc3ccc4c(c3)C(=O)OC4=O)ccc21|O=S(=O)(c1ccc(O)cc1)c1ccc(O)cc1` |
| 15 | 3 | -0.56 | 249.09 +/- 36.83 | 0.91 | 1.49 | chembl|chembl|library | 0.29770:0.19822:0.50408 | 酸酐-羟基酯化。|酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 | `Nc1ccc2nc(N)nc(N)c2c1|O=C(Cn1cccc(NC(=O)c2ccccc2)c1=O)NCCO|O=C1OC(=O)c2cc(Oc3ccc4c(c3)C(=O)OC4=O)ccc21` |
| 16 | 4 | -0.55 | 250.82 +/- 49.07 | 0.82 | 1.71 | chembl|chembl|chembl|library | 0.33693:0.11248:0.49500:0.05559 | 马来酰亚胺-胺 Michael 加成。|马来酰亚胺与烯基共聚/加成。 | `COc1ccccc1C1=C(Nc2ccccc2)C(=O)NC1=O|Nc1c(S(=O)(=O)O)cc(Nc2ccc(F)cc2)c2c1C(=O)c1ccccc1C2=O|O=C(/C=C/c1ccc(O)c(O)c1)N1CCN(c2ccccc2)CC1|O=C(O)CCCCCCCCC(=O)O` |
| 17 | 3 | -0.54 | 251.23 +/- 52.87 | 1.23 | 1.27 | chembl|chembl|library | 0.39016:0.07115:0.53869 | 马来酰亚胺-胺 Michael 加成。|马来酰亚胺与烯基共聚/加成。 | `Cc1ccc(-c2c(COCc3ccc(C(=O)O)cc3)c(C)nc(CC(C)C)c2CN)cc1|NS(=O)(=O)c1ccc(/C=C/c2cccc(O)c2)cc1|O=C1C=CC(=O)N1c1ccc(Cc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 18 | 3 | -0.54 | 249.86 +/- 61.69 | 0.14 | 1.67 | chembl|chembl|generated | 0.28395:0.57236:0.14369 | 硫醇-烯点击反应。|酸酐-羟基酯化。|酸酐-胺开环形成酰胺酸。 | `NS(=O)(=O)c1ccc(/C=C/c2cccc(O)c2)cc1|O=C(NCc1ccc(S(=O)(=O)O)cc1)C(CS)Cc1ccccc1|O=C(c1ccc2c(c1)C(=O)OC2=O)c1ccc2c(c1)C(=O)OC2=O` |
| 19 | 4 | -0.52 | 249.83 +/- 51.90 | 0.17 | 3.28 | library|chembl|chembl|chembl | 0.39798:0.21846:0.08797:0.29559 | 氰酸酯-胺共反应。|氰酸酯-酚共固化/催化三聚。 | `CC(C)(c1ccc(OC#N)cc1)c1ccc(OC#N)cc1|NC(CO)(CO)CCc1ccc(-c2ccc(Sc3ccc(Cl)cc3)cc2F)cc1|O=C(C1=C(O)c2ccccc2S(=O)(=O)N1Cc1ccccc1)c1ccccc1|Oc1cc(Cl)ccc1Oc1ccc(Cl)cc1CN1CCN(C(c2ccccc2)c2ccccc2)CC1` |
| 20 | 2 | -0.51 | 249.17 +/- 40.61 | 0.83 | 2.05 | chembl|library | 0.45000:0.55000 | 马来酰亚胺-胺 Michael 加成。 | `Nc1nccc(Nc2ccc(S(N)(=O)=O)cc2)n1|O=C1C=CC(=O)N1c1ccc(Cc2ccc(N3C(=O)C=CC3=O)cc2)cc1` |
| 21 | 3 | -0.41 | 249.34 +/- 57.36 | 0.66 | 1.48 | chembl|chembl|chembl | 0.41828:0.16710:0.41462 | 马来酰亚胺-胺 Michael 加成。 | `CCC1(c2ccc(N)cc2)CCC(=O)NC1=O|Cn1cc(C2=C(c3coc4ccccc34)C(=O)NC2=O)c2ccc(O)cc21|Nc1nc(N)c2c(S(=O)(=O)c3ccc(Cl)c(Cl)c3)cccc2n1` |
| 22 | 4 | -0.37 | 252.15 +/- 39.84 | 2.15 | 1.19 | library|chembl|chembl|chembl | 0.36980:0.26141:0.06197:0.30682 | 环氧-伯胺开环固化。|环氧-羟基醚化，常需催化剂。|马来酰亚胺-胺 Michael 加成。 | `C(=N/c1ccc(OCC2CO2)cc1)\c1ccc(OCC2CO2)cc1|CNS(=O)(=O)c1cc2c(N=O)c(O)[nH]c2c2c1CCCC2|Cn1cc(C2=C(c3cn(CCC/N=C(\N)N[N+](=O)[O-])c4ccccc34)C(=O)NC2=O)c2ccccc21|Nc1nc2ccc(Nc3ccccc3)cc2o1` |
| 23 | 3 | -0.34 | 250.02 +/- 54.71 | 0.02 | 2.53 | chembl|chembl|chembl | 0.06149:0.48207:0.45644 | 马来酰亚胺-胺 Michael 加成。 | `COc1ccccc1CNC(=O)c1cc(C(F)(F)F)nn1-c1cccc(-c2noc([C@H](C)N)n2)c1|Cn1cc(C2=C(c3cn(CCCO)c4ccccc34)C(=O)NC2=O)c2ccccc21|N=C(N)Nc1ccc(Sc2ccc(N=C3NCCN3)cc2)cc1` |
| 24 | 3 | -0.32 | 252.98 +/- 44.47 | 2.98 | 2.29 | library|chembl|chembl | 0.63747:0.12829:0.23424 | 氰酸酯-胺共反应。|氰酸酯-酚共固化/催化三聚。|马来酰亚胺-胺 Michael 加成。 | `CC(C)(c1ccc(OC#N)cc1)c1ccc(OC#N)cc1|Cn1cc(C2=C(c3cn(CCCCCSC(=N)N)c4ccccc34)C(=O)NC2=O)c2ccccc21|NCCS(=O)(=O)N1CCc2c([nH]c3ccc(Cl)cc23)C1c1cccc(O)c1` |
| 25 | 4 | -0.30 | 249.54 +/- 42.65 | 0.46 | 1.57 | library|chembl|chembl|library | 0.38709:0.15195:0.14200:0.31896 | 环氧-仲胺开环固化。|环氧-羟基醚化，常需催化剂。 | `CC(C)(O)C(=O)c1ccc(OCCO)cc1|CC(O)(CS(=O)(=O)c1ccc(F)cc1)C(=O)Nc1ccc(C#N)c(C(F)(F)F)c1|O=C1NC(=O)c2cc(Nc3ccc(I)cc3)c(Nc3ccc(I)cc3)cc21|O=c1cc(-c2ccc(OCC3CO3)cc2)oc2cc(OCC3CO3)ccc12` |

## Iteration History

| Iteration | Generated | Best Tg (C) | Best distance (C) | Near target | Added principles |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 51420 | 249.99 | 0.01 | 1587 | observed_chembl_transferable_monomers, observed_template_generated_monomers |
| 2 | 18000 | 249.99 | 0.01 | 668 | observed_three_or_more_component_blending |
| 3 | 18000 | 249.99 | 0.01 | 555 | - |
| 4 | 18000 | 250.00 | 0.00 | 641 | - |
| 5 | 18000 | 250.01 | 0.01 | 615 | - |
| 6 | 18000 | 250.00 | 0.00 | 586 | - |

## Current Top Soft Principles

| Principle | Confidence | Weight | Effect |
| --- | ---: | ---: | ---: |
| peptide_like_out_of_domain | 0.800 | 0.750 | -1.0 |
| imide_anhydride_networks_raise_tg | 0.698 | 0.850 | 1.0 |
| cyanate_ester_triazine | 0.606 | 0.900 | 1.0 |
| peg_like_penalty | 0.703 | 0.750 | -1.0 |
| maleimide_rigid_network | 0.580 | 0.750 | 1.0 |
| multi_aromatic_rigidity | 0.650 | 0.650 | 1.0 |
| aromatic_backbones_raise_tg | 0.700 | 0.550 | 1.0 |
| flexible_ether_penalty | 0.657 | 0.550 | -1.0 |
| high_functionality_crosslink_density | 0.620 | 0.550 | 1.0 |
| druglike_hetero_complexity_penalty | 0.623 | 0.500 | -1.0 |
| sulfone_diamine_rigidity | 0.558 | 0.550 | 1.0 |
| formal_charge_practical_penalty | 0.627 | 0.450 | -1.0 |
| too_flexible_penalty | 0.625 | 0.450 | -1.0 |
| long_aliphatic_penalty | 0.601 | 0.450 | -1.0 |
| nitrile_rich_rigidity | 0.557 | 0.450 | 1.0 |
| heavy_halogen_practical_risk | 0.614 | 0.400 | -1.0 |
| stereochemical_complexity_penalty | 0.607 | 0.400 | -1.0 |
| reaction_a67f85420c33 | 0.565 | 0.420 | 1.0 |
| reaction_536dfe22d324 | 0.564 | 0.420 | 1.0 |
| reaction_5cde50869441 | 0.563 | 0.420 | 1.0 |

## Interpretation

- Hard constraints are deterministic and are not changed by the loop: RDKit validity, VAE encodability, ratio simplex, allowed atoms, and functional-group reaction graph validity.
- Soft priors are PiEvo-style beliefs. Their confidence is updated from in-silico predictor observations, so these are model-guidance beliefs, not experimental truth.
- A real synthesis/DSC result should be added as a stronger observation source and should override purely in-silico principle updates.
