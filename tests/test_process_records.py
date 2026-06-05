from __future__ import annotations

from pathlib import Path

from trail.experiments.import_process_records import import_process_records


def test_process_records_require_template_fields(tmp_path: Path) -> None:
    records = tmp_path / "process.csv"
    records.write_text(
        "\n".join(
            [
                "process_record_id,linked_observation_id,source_type,target_tg_c,observed_tg_c,smiles,ratios,reaction_principle,process_template,review_status,mix_temperature_c,cure_temperature_c,cure_time_h,post_cure_temperature_c,post_cure_time_h",
                "p1,o1,real_dsc,195,196,CCO|NCC,0.5:0.5,epoxy_primary_amine,epoxy_amine_thermal_cure,approved_for_active_ledger,25,120,2,180,1",
                "p2,o2,literature,195,180,CCO|NCC,0.5:0.5,epoxy_primary_amine,epoxy_amine_thermal_cure,needs_process_details,,,,,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ledger, summary = import_process_records(
        records,
        Path("trail/experiments/process_record_schema.yaml"),
        Path("trail/knowledge/smp_prior_knowledge.yaml"),
    )
    assert summary["input_rows"] == 2
    assert summary["process_record_pass_rows"] == 2
    assert summary["ready_for_active_ledger_rows"] == 1
    assert bool(ledger.loc[0, "ready_for_active_ledger"]) is True
    assert "mix_temperature_c" in ledger.loc[1, "missing_process_fields"]
