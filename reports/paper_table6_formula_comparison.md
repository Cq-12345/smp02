# Paper Table 6 Formula Comparison

Source: local paper PDF, Table 5 and Table 6.

The main paper reports three discovered SMPs in Table 5. The experimentally validated formulations with physical Tg values are Table 6 sample A and sample B, both using the BPAB/BPADA monomer pair:

- BPAB: `Nc1ccc(Oc2ccc(-c3ccc(Oc4ccc(N)cc4)cc3)cc2)cc1`
- BPADA: `CC(C)(c1ccc(Oc2ccc3c(c2)C(=O)OC3=O)cc1)c1ccc(Oc2ccc3c(c2)C(=O)OC3=O)cc1`

Both formulations exist in `artifacts/reproduce/discovery/all_ratio_candidates.csv`.

Our model is the current MAPEK-selected best model, `VAE (512) + GaussianProcess_RBF`. The uncertainty is the Gaussian process predictive standard deviation, transformed back to Celsius.

| Sample | BPAB/BPADA ratio | Candidate row | In selected 190-200 C set | Our Tg (C, mean +/- 1 sigma) | Paper ML Tg (C) | Paper experimental Tg (C) | Reference Tg (C) | Our abs error vs experiment (C) | Paper abs error vs experiment (C) |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 45/55 | 17566 | No | 202.01 +/- 18.38 | 192.24 | 178.14 | NA | 23.87 | 14.10 |
| B | 50/50 | 17565 | No | 226.28 +/- 3.38 | 201.00 | 222.07 | 229.60 | 4.21 | 21.07 |

Notes:

- Candidate row IDs are the original zero-based row indices from the all-ratio candidate CSV.
- In our candidate CSV orientation, `smiles_a` is BPADA and `smiles_b` is BPAB for this pair. Therefore paper BPAB/BPADA 45/55 corresponds to CSV `ratio_a=0.55`, `ratio_b=0.45`.
- The paper Table 6 reports sample B with a local DSC experimental value of 222.07 C and a reference value of 229.6 C from Kong et al. [58].
