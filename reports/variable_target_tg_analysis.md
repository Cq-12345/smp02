# 可变目标 Tg 批量分析

本文档用于回应 TODO 中“真实 Tg 温度不固定”的要求。这里不重新训练模型，而是读取已有候选池，对多个目标 Tg 重新计算目标距离和 reward。

- 候选来源：`artifacts/agent_discovery_250/candidate_formulations.csv`
- Reward：`exp(-abs(predicted_Tg - target_Tg) / 5)`

## 目标汇总

| target Tg (C) | best predicted Tg (C) | best distance (C) | best reward | within 1C | within 5C | within 10C |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 190.0 | 189.999 | 0.001 | 0.9998 | 1088 | 5285 | 10499 |
| 195.0 | 195.000 | 0.000 | 1.0000 | 1059 | 5163 | 10480 |
| 200.0 | 199.997 | 0.003 | 0.9994 | 1085 | 5195 | 10408 |
| 250.0 | 250.000 | 0.000 | 1.0000 | 992 | 4652 | 9149 |

## 每个目标的 Top 5

### Target 190.0 C

| target_tg_c | target_rank | predicted_tg_mean_c | target_distance_c | target_reward | smiles | ratios | sources | compatibility_reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 190.0000 | 1 | 189.9991 | 0.0009 | 0.9998 | COc1ccc(OCC2CO2)c(CCCC(=O)OCCCOC(=O)CCc2ccc(OCC3CO3)c(OC)c2)c1\|O=C1OCC2=C1C(c1ccc(F)cc1)c1c(c3cccnc3c3ncccc13)N2 | 0.44446:0.55554 | library\|chembl | 环氧-仲胺开环固化。 |
| 190.0000 | 2 | 190.0016 | 0.0016 | 0.9997 | C=CCc1ccc(OCC2CO2)c(-c2cc(CC=C)ccc2OCC2CO2)c1\|COc1cc2c(cc1OC)CN(CCc1ccc(NC(=O)c3cc(Cl)ccc3NC(=O)c3cnc4ccccc4c3)cc1)CC2 | 0.60918:0.39082 | library\|chembl | 环氧-仲胺开环固化。 |
| 190.0000 | 3 | 189.9979 | 0.0021 | 0.9996 | COc1ccc(-n2c(C)cc(/C=C(\C#N)C(=O)OCC(=O)Nc3ccc(Cl)c(C(F)(F)F)c3)c2C)cc1\|Cn1cc(C2=C(c3coc4ccccc34)C(=O)NC2=O)c2ccc(O)cc21 | 0.45000:0.55000 | chembl\|chembl | 马来酰亚胺与烯基共聚/加成。 |
| 190.0000 | 4 | 189.9967 | 0.0033 | 0.9993 | C(=N/c1ccc(OCC2CO2)cc1)\c1ccc(OCC2CO2)cc1\|CC1(C)[C@H](C(=O)O)N2C(=O)[C@@H](Cc3cn(-c4ccc(O)cc4)nn3)[C@H]2S1(=O)=O\|NS(=O)(=O)c1ccc(/C=C/c2ccc(O)cc2)cc1 | 0.38156:0.29794:0.32050 | library\|chembl\|chembl | 环氧-羟基醚化，常需催化剂。\|环氧-羧酸开环酯化。 |
| 190.0000 | 5 | 189.9942 | 0.0058 | 0.9988 | O=C(Nc1ccc(Oc2ccnc3[nH]c(=O)cnc23)cc1F)Nc1cc(C(F)(F)F)ccc1F\|O=C=Nc1ccc(Cc2ccc(N=C=O)cc2)cc1 | 0.65000:0.35000 | chembl\|library | 异氰酸酯-仲胺形成脲键。 |

### Target 195.0 C

| target_tg_c | target_rank | predicted_tg_mean_c | target_distance_c | target_reward | smiles | ratios | sources | compatibility_reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 195.0000 | 1 | 194.9998 | 0.0002 | 1.0000 | Cc1c(C)c2c(c(C)c1O)CCC(C)(COc1ccc(CC3SC(=O)NC3=O)cc1)O2\|Cc1cc(OCc2nc(-c3ccc(C(=O)N(C)C(C)C)cc3)c(-c3ccc(OC(F)(F)F)cc3)s2)ccc1OCC(=O)O\|O=c1cc(-c2ccc(OCC3CO3)cc2)oc2cc(OCC3CO3)ccc12 | 0.47941:0.05400:0.46659 | chembl\|chembl\|library | 环氧-羟基醚化，常需催化剂。\|环氧-羧酸开环酯化。 |
| 195.0000 | 2 | 195.0013 | 0.0013 | 0.9997 | C=CCOCC(CO)(COCC=C)COCC=C\|Nc1nc(O)c2cc(S(=O)(=O)c3ccc4ccccc4c3)ccc2n1\|c1ccc(C(c2ccc(OCC3CO3)cc2)c2ccc(OCC3CO3)cc2)cc1 | 0.33104:0.46490:0.20406 | library\|chembl\|generated | 环氧-羟基醚化，常需催化剂。 |
| 195.0000 | 3 | 194.9978 | 0.0022 | 0.9996 | Cn1cc(C2=C(c3cn(CCCCCN)c4ccccc34)C(=O)NC2=O)c2ccccc21\|Nc1ccc(Cc2ccc(N)cc2)cc1 | 0.15000:0.85000 | chembl\|library | 马来酰亚胺-胺 Michael 加成。 |
| 195.0000 | 4 | 195.0028 | 0.0028 | 0.9994 | CC1(C)CC(=O)C2=C(C1)Nc1c(O)cccc1N(C(=O)c1cccc(F)n1)C2c1ccc(OCc2ccccc2)cc1F\|COc1cc2nc(N3CCN(C(=O)/C(F)=C/c4ccccc4)CC3)nc(N)c2cc1OC\|Cc1ccc(S(=O)(=O)N2C[C@@H](C(=O)O)[C@H](SCCc3ccccc3 | 0.16223:0.71971:0.06212:0.05594 | chembl\|chembl\|chembl\|chembl | 马来酰亚胺-胺 Michael 加成。\|马来酰亚胺与烯基共聚/加成。 |
| 195.0000 | 5 | 195.0028 | 0.0028 | 0.9994 | CC1=CC(C)(C)Nc2cc3oc(=O)cc(C(F)(F)F)c3cc21\|CN(C)CCCn1cc(C2=C(c3c[nH]c4ccccc34)C(=O)NC2=O)c2ccccc21 | 0.95000:0.05000 | chembl\|chembl | 马来酰亚胺与烯基共聚/加成。 |

### Target 200.0 C

| target_tg_c | target_rank | predicted_tg_mean_c | target_distance_c | target_reward | smiles | ratios | sources | compatibility_reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 200.0000 | 1 | 199.9970 | 0.0030 | 0.9994 | CC(C)(c1ccc(O)cc1)c1ccc(O)cc1\|CCc1cc2c(O)ncnc2s1\|O=C1OC(=O)c2cc(-c3ccc4c(c3)C(=O)OC4=O)ccc21 | 0.51580:0.30744:0.17676 | generated\|chembl\|library | 酸酐-羟基酯化。 |
| 200.0000 | 2 | 200.0038 | 0.0038 | 0.9992 | Cc1cccc(Nc2nc(-c3ccncc3)c(C(N)=O)s2)c1\|Cn1cc(C2=C(c3cn(CCCCCSC(=N)N)c4ccccc34)C(=O)NC2=O)c2ccccc21 | 0.86109:0.13891 | chembl\|chembl | 马来酰亚胺-胺 Michael 加成。 |
| 200.0000 | 3 | 200.0041 | 0.0041 | 0.9992 | C[C@@H](Oc1cc(-n2cnc3cc(-c4ccnc(N)c4)ccc32)sc1C(N)=O)c1ccccc1C(F)(F)F\|O=C1C=CC(=O)N1c1ccc(Oc2ccc(N3C(=O)C=CC3=O)cc2)cc1 | 0.15000:0.85000 | chembl\|generated | 马来酰亚胺-胺 Michael 加成。 |
| 200.0000 | 4 | 200.0058 | 0.0058 | 0.9988 | CCOC(=O)c1ccc(NC(=O)Nc2cc3c(cc2C)SC(C)(C)CC3(C)C)cc1\|Cc1ccc(N=C=O)cc1N=C=O\|O=C(Nc1ccc(Cl)cc1)Nc1ccc(C(=O)NCCN2CCOCC2)cc1\|OC(COC1COC2C(OCC3CO3)COC12)COC1COC2C(OCC3CO3)COC12 | 0.07419:0.43304:0.38141:0.11136 | chembl\|library\|chembl\|library | 异氰酸酯-仲胺形成脲键。\|异氰酸酯-羟基形成聚氨酯。\|环氧-仲胺开环固化。 |
| 200.0000 | 5 | 199.9941 | 0.0059 | 0.9988 | CCCc1cc(C(=O)O)ccc1OC(C(=O)NS(=O)(=O)c1ccc(C(C)C)cc1)c1ccc2c(c1)OCO2\|Cc1cc(OCC2CO2)c(C(C)(C)C)cc1-c1cc(C)c(OCC2CO2)c(C(C)(C)C)c1 | 0.28501:0.71499 | chembl\|library | 环氧-羧酸开环酯化。 |

### Target 250.0 C

| target_tg_c | target_rank | predicted_tg_mean_c | target_distance_c | target_reward | smiles | ratios | sources | compatibility_reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 250.0000 | 1 | 250.0001 | 0.0001 | 1.0000 | CS(=O)(=O)Nc1ccc(Sc2ccc(NC3=NCCN3)cc2)cc1\|Cc1cc(C)nc(N/C=C(\C#N)C(=O)c2cccc(CSc3ccccc3)c2)n1\|c1cc(N(CC2CO2)CC2CO2)ccc1Cc1ccc(N(CC2CO2)CC2CO2)cc1 | 0.40984:0.15367:0.43649 | chembl\|chembl\|library | 环氧-仲胺开环固化。 |
| 250.0000 | 2 | 250.0009 | 0.0009 | 0.9998 | COc1cc(CC2CO2)ccc1OCc1ccc(COc2ccc(CC3CO3)cc2OC)cc1\|O=C(NC1CC1)c1ccc(Cl)c(Nc2nncc3c2cnn3-c2ccccc2Cl)c1 | 0.62319:0.37681 | library\|chembl | 环氧-仲胺开环固化。 |
| 250.0000 | 3 | 249.9970 | 0.0030 | 0.9994 | COc1cc2nc(N3CCN(C(=O)/C(F)=C/c4ccccc4)CC3)nc(N)c2cc1OC\|N#COc1ccc(-c2ccc(OC#N)cc2)cc1 | 0.77844:0.22156 | chembl\|generated | 氰酸酯-胺共反应。 |
| 250.0000 | 4 | 249.9942 | 0.0058 | 0.9988 | CN(C)CCCn1cc(C2=C(c3cn(CCOCCO)c4ccccc34)C(=O)NC2=O)c2ccccc21\|COc1cc(CO)cc(-c2cc(CO)cc(OC)c2OCC2CO2)c1OCC1CO1\|Cc1ccccc1NC(=O)Nc1ccc([N+](=O)[O-])cc1O\|O=C1c2cc(Nc3ccccc3)c(Nc3ccccc3) | 0.09208:0.11726:0.41149:0.37917 | chembl\|library\|chembl\|chembl | 环氧-仲胺开环固化。\|环氧-羟基醚化，常需催化剂。 |
| 250.0000 | 5 | 250.0077 | 0.0077 | 0.9985 | CN(C)CCCn1cc(C2=C(c3cn(CCOCCO)c4ccccc34)C(=O)NC2=O)c2ccccc21\|Nc1nc(N)c2cc(NC(=O)Cc3cccc(C(F)(F)F)c3)ccc2n1 | 0.22824:0.77176 | chembl\|chembl | 马来酰亚胺-胺 Michael 加成。 |

## 结论

- 同一个候选池可以服务多个 Tg 目标，目标温度不应写死在算法里。
- 对每个目标都应分别计算 `target_distance` 和 `target_reward`，再进入 Harness、PiEvo IDS 或人工筛选。
- 若某个目标的 within-5C 候选很少，应扩展该目标附近的生成策略，而不是只沿用 250 C 候选。
