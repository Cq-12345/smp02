from __future__ import annotations

from pathlib import Path

from scripts.audit_candidate_sources import audit_sources


def test_candidate_source_audit_flags_sparse_priority_group(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.csv"
    inventory.write_text(
        "\n".join(
            [
                "smiles,source,label,groups",
                "N#COc1ccccc1,library,l1,aromatic;cyanate_ester",
                "CCO,chembl,c1,hydroxyl",
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
                "  library:",
                "    source_type: literature_dataset",
                "    authority_level: 4",
                "  chembl:",
                "    source_type: database_screen",
                "    authority_level: 1",
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
    summary, coverage, audit_summary = audit_sources(inventory, registry)
    assert set(summary["source"]) == {"library", "chembl"}
    assert "cyanate_ester" in audit_summary["sparse_high_value_groups_needing_expansion"]
    row = coverage[coverage["group"] == "cyanate_ester"].iloc[0]
    assert row["coverage_note"] == "needs_literature_expansion"
