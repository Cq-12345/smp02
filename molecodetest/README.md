# MoleCode Verification

This folder verifies the MoleCode analysis against local executable evidence.

Run from the project root:

```bash
conda run -n mhc_pyg314 python molecodetest/verify_molecode.py
```

The script writes:

- `outputs/verification_results.json`: structured result payload.
- `outputs/verification_results.csv`: one row per verification item.
- `outputs/verification_report.md`: concise Chinese report.
- `outputs/graphs/*.mmd`: MoleCode/Mermaid graphs used as evidence.

Scope:

- Small-molecule SMILES <-> MoleCode <-> SMILES round trips.
- Project SMP monomer examples, including BPAB/BPADA from the paper comparison.
- Compatibility with the existing SMARTS functional-group constraints.
- Polymer PSMILES <-> MoleCode <-> PSMILES round trips.
- Markush-style abbreviation nodes and graph-isomorphism behavior.

This verification does not claim MoleCode is a Tg predictor. It only tests MoleCode as a structural representation and as a possible generation/constraint/audit layer around the existing SMP model.
