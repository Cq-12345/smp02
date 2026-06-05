from __future__ import annotations

from pathlib import Path

from scripts.analyze_generation_feedback import analyze_feedback


def test_generation_feedback_summarizes_failures(tmp_path: Path) -> None:
    ledger = tmp_path / "generation.csv"
    ledger.write_text(
        "\n".join(
            [
                "generation_id,strategy,harness_pass,generation_reward,harness_failure_reason",
                "g1,llm_rag_principle_generation,True,0.9,",
                "g2,llm_smiles_generation,False,,prediction_missing;chemistry_evidence_missing",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rejections = tmp_path / "rejections.csv"
    rejections.write_text(
        "\n".join(
            [
                "proposal_index,reason,shared_groups,tanimoto",
                "1,replacement_formula_failed_reaction_or_ratio_constraints,aromatic;isocyanate,0.2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    strategy_df, reason_df, group_df, summary = analyze_feedback(ledger, rejections)
    assert summary["generation_records"] == 2
    assert summary["replacement_rejections"] == 1
    assert "prediction_missing" in set(reason_df["failure_reason"])
    assert "replacement_formula_failed_reaction_or_ratio_constraints" in set(reason_df["failure_reason"])
    assert strategy_df.loc[strategy_df["strategy"] == "llm_smiles_generation", "policy_weight_delta"].iloc[0] < 0
    assert group_df.iloc[0]["shared_groups"] == "aromatic;isocyanate"
