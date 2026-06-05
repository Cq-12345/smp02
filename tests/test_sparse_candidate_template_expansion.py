from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.expand_sparse_candidate_templates import run_expansion
from trail.candidates.build_component_inventory import functional_group_index


def test_sparse_template_expansion_adds_registered_high_value_groups(tmp_path: Path) -> None:
    base = tmp_path / "base.csv"
    base.write_text(
        "\n".join(
            [
                "smiles,source,label,groups",
                "N#COc1ccccc1,library,existing,aromatic;cyanate_ester",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    templates = tmp_path / "templates.yaml"
    templates.write_text(
        "\n".join(
            [
                "source: literature_template",
                "templates:",
                "  - {label: duplicate, intended_group: cyanate_ester, family: cyanate_ester, smiles: 'N#COc1ccccc1'}",
                "  - {label: cyanate_new, intended_group: cyanate_ester, family: cyanate_ester, smiles: 'N#COc1ccc(OC#N)cc1'}",
                "  - {label: maleimide_new, intended_group: maleimide, family: maleimide, smiles: 'O=C1C=CC(=O)N1c1ccccc1'}",
                "  - {label: invalid_group, intended_group: thiol, family: thiol, smiles: 'CCO'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        "\n".join(
            [
                "sources:",
                "  library: {source_type: literature_dataset, authority_level: 4}",
                "  literature_template: {source_type: curated_literature_template, authority_level: 2}",
                "functional_group_priorities:",
                "  sparse_high_value:",
                "    - cyanate_ester",
                "audit:",
                "  sparse_group_threshold: 2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    report = tmp_path / "report.md"

    expanded, summary = run_expansion(
        argparse.Namespace(
            base_inventory=str(base),
            templates=str(templates),
            registry=str(registry),
            out_dir=str(out_dir),
            report=str(report),
        )
    )
    rejected = pd.read_csv(out_dir / "template_expansion_rejected.csv")

    assert summary["added_templates"] == 2
    assert "literature_template" in set(expanded["source"])
    assert "cyanate_ester" not in summary["sparse_high_value_groups_needing_expansion"]
    assert set(rejected["reason"]) == {"duplicate_with_existing_inventory", "intended_group_not_detected"}


def test_inventory_functional_group_index_ignores_blank_groups() -> None:
    inventory = pd.DataFrame(
        [
            {"smiles": "CCO", "source": "library", "label": "blank", "groups": float("nan")},
            {"smiles": "N#COc1ccccc1", "source": "library", "label": "cyanate", "groups": "aromatic;cyanate_ester"},
        ]
    )

    groups = functional_group_index(inventory)

    assert set(groups["group"]) == {"aromatic", "cyanate_ester"}
