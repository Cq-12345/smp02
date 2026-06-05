# Candidate Component Inventory

This folder contains utilities for organizing the current small-molecule candidate component dataset.

Current boundary:

- Use single-molecule SMILES / MoleCode-compatible molecules.
- Do not model commodity mixtures, polymers, or hypergraph component representations yet.

Sources:

- `library`: monomers appearing in `data/SMP_Dataset.xlsx`.
- `generated`: thermoset-inspired generated monomer seeds from `src/smp02/agent_discovery.py`.
- `chembl`: screened molecules from `data/chembl_36_chemreps.txt`.

Build:

```bash
PYTHONPATH=src python trail/candidates/build_component_inventory.py \
  --chembl-limit 5000 \
  --out artifacts/trail/candidates
```

Outputs:

- `component_inventory.csv`: candidate molecules with source, label, functional groups, and structural-prior features.
- `functional_group_index.csv`: one row per `(functional_group, molecule)` relation.
- `component_inventory_summary.json`: source counts and top functional groups.
