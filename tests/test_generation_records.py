from __future__ import annotations

from pathlib import Path

from trail.generation.import_generation_records import import_generation_records


def test_generation_record_import_computes_harness_feedback(tmp_path: Path) -> None:
    source = tmp_path / "generation_records.csv"
    source.write_text(
        "\n".join(
            [
                "generation_id,strategy,stage,target_tg_c,target_window_c,candidate_smiles,candidate_ratios,source_context,compatibility_reasons,predicted_tg_mean_c",
                "g1,llm_rag_principle_generation,harnessed,195,5,CCO|NCC,0.5:0.5,rag,amine-alcohol test,196",
                "g2,llm_smiles_generation,draft,195,5,CCO|NCC,0.6:0.6,rag,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ledger, summary = import_generation_records(source, Path("trail/generation/generation_record_schema.yaml"), 5.0)
    assert summary["input_rows"] == 2
    assert summary["record_pass_rows"] == 1
    assert summary["harness_pass_rows"] == 1
    assert bool(ledger.loc[0, "harness_pass"]) is True
    assert bool(ledger.loc[1, "harness_pass"]) is False
    assert "ratio_sum_not_one" in ledger.loc[1, "harness_failure_reason"]
    assert "prediction_missing" in ledger.loc[1, "harness_failure_reason"]
