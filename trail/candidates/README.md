# Candidate Component Inventory

This folder contains utilities for organizing the current small-molecule candidate component dataset.

Current boundary:

- Use single-molecule SMILES / MoleCode-compatible molecules.
- Do not model commodity mixtures, polymers, or hypergraph component representations yet.

Sources:

- `library`: monomers appearing in `data/SMP_Dataset.xlsx`.
- `generated`: thermoset-inspired generated monomer seeds from `src/smp02/agent_discovery.py`.
- `chembl`: screened molecules from `data/chembl_36_chemreps.txt`.
- `generation_record`: generated hypotheses from the generation ledger; these are not trusted as library molecules.

Source registry:

- `source_registry.yaml`: authority level, provenance files, intended use, and trust notes for each source.

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

Source audit:

```bash
PYTHONPATH=src python scripts/audit_candidate_sources.py \
  --inventory artifacts/trail/candidates_smoke/component_inventory.csv \
  --registry trail/candidates/source_registry.yaml \
  --out-dir artifacts/trail/candidates_source_audit \
  --report reports/candidate_source_audit.md
```

Audit outputs:

- `candidate_source_summary.csv`: source type, authority level, component count, and top functional groups.
- `functional_group_source_coverage.csv`: functional-group coverage split by source.
- `candidate_source_audit_summary.json`: sparse high-value groups that need literature or curated-template expansion.
