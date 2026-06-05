from __future__ import annotations

from pathlib import Path

import pandas as pd

from trail.generation.vae_replacement_strategy import propose_replacements


def test_feedback_guided_replacement_preserves_counterpart_reactivity(tmp_path: Path) -> None:
    candidates = tmp_path / "selected_candidates.csv"
    candidates.write_text(
        "\n".join(
            [
                "predicted_tg,smiles_a,smiles_b,groups_a,groups_b",
                "195.0,O=C=Nc1ccccc1,NCCN,aromatic;isocyanate,primary_amine",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    groups = tmp_path / "monomer_functional_groups.csv"
    groups.write_text(
        "\n".join(
            [
                "smiles,groups",
                "O=C=Nc1ccccc1,aromatic;isocyanate",
                "O=C(O)c1ccccc1,aromatic;carboxylic_acid",
                "O=C=Nc1ccc(C)cc1,aromatic;isocyanate",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    proposals = propose_replacements(
        candidates,
        groups,
        top_k=1,
        per_side=5,
        require_counterpart_compatibility=True,
    )

    assert "O=C(O)c1ccccc1" not in set(proposals["replacement_smiles"])
    assert "O=C=Nc1ccc(C)cc1" in set(proposals["replacement_smiles"])
    row = proposals.loc[proposals["replacement_smiles"] == "O=C=Nc1ccc(C)cc1"].iloc[0]
    assert row["feedback_constraint"] == "preserve_complementary_reactive_pair"
    assert pd.notna(row["counterpart_compatibility_reason"])
    assert "异氰酸酯" in row["counterpart_compatibility_reason"]


def test_replacement_can_use_expanded_component_inventory_with_source_provenance(tmp_path: Path) -> None:
    candidates = tmp_path / "selected_candidates.csv"
    candidates.write_text(
        "\n".join(
            [
                "predicted_tg,smiles_a,smiles_b,groups_a,groups_b",
                "195.0,O=C=Nc1ccccc1,NCCN,aromatic;isocyanate,primary_amine",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    inventory = tmp_path / "component_inventory.csv"
    inventory.write_text(
        "\n".join(
            [
                "smiles,source,label,groups,template_family,template_intended_group",
                "O=C=Nc1ccc(C)cc1,literature_template,lt_diisocyanate,aromatic;isocyanate,isocyanate_templates,isocyanate",
                "O=C(O)c1ccccc1,literature_template,lt_acid,aromatic;carboxylic_acid,acid_templates,carboxylic_acid",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    proposals = propose_replacements(
        candidates,
        tmp_path / "unused_groups.csv",
        top_k=1,
        per_side=5,
        require_counterpart_compatibility=True,
        component_inventory=inventory,
    )

    assert "O=C(O)c1ccccc1" not in set(proposals["replacement_smiles"])
    row = proposals.loc[proposals["replacement_smiles"] == "O=C=Nc1ccc(C)cc1"].iloc[0]
    assert row["replacement_source"] == "literature_template"
    assert row["replacement_label"] == "lt_diisocyanate"
    assert row["replacement_template_family"] == "isocyanate_templates"
    assert row["replacement_template_intended_group"] == "isocyanate"
