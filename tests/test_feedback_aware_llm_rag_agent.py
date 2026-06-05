from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.run_feedback_aware_llm_rag_agent import (
    build_agent_prompt,
    offline_policy_records,
    policy_from_feedback,
)
from trail.generation.import_generation_records import import_generation_records


def test_policy_from_feedback_suppresses_failed_smiles_generation() -> None:
    feedback = pd.DataFrame(
        [
            {
                "strategy": "llm_rag_principle_generation",
                "pass_rate": 1.0,
                "policy_weight_delta": 0.1,
                "next_constraint": "retain",
            },
            {
                "strategy": "llm_smiles_generation",
                "pass_rate": 0.0,
                "policy_weight_delta": -0.25,
                "top_failure_reason": "prediction_missing",
                "next_constraint": "run predictor before recommendation",
            },
        ]
    )

    policy = policy_from_feedback(feedback)

    assert "llm_rag_principle_generation" in policy["preferred_strategies"]
    assert [item["strategy"] for item in policy["suppressed_strategies"]] == ["llm_smiles_generation"]
    assert any("run predictor" in item for item in policy["constraints"])


def test_offline_policy_records_import_to_generation_ledger(tmp_path: Path) -> None:
    selected = tmp_path / "selected_candidates.csv"
    selected.write_text(
        "\n".join(
            [
                "predicted_tg,smiles_a,smiles_b,ratio_a,ratio_b,groups_a,groups_b,compatibility_reason",
                "195.1,C1CO1,NCCN,0.5,0.5,epoxy,primary_amine,环氧-伯胺开环固化。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    replacement = tmp_path / "replacement_scored.csv"
    replacement.write_text(
        "\n".join(
            [
                "harness_pass,predicted_tg_mean_c,predicted_tg_sigma_c,ood_penalty,smiles,ratios,groups,compatibility_reasons,proposal_index,replace_side,counterpart_compatibility_reason",
                "True,194.9,1.0,0.0,C1CO1|NCCN,0.50000:0.50000,epoxy|primary_amine,环氧-伯胺开环固化。,7,a,环氧-伯胺开环固化。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    policy = {
        "preferred_strategies": ["llm_rag_principle_generation"],
        "suppressed_strategies": [{"strategy": "llm_smiles_generation"}],
        "constraints": ["llm_smiles_generation: run predictor before recommendation"],
    }
    prompt = build_agent_prompt(195.0, 5.0, "query", "docs:0", "digest", policy)

    records = offline_policy_records(
        selected,
        replacement,
        195.0,
        5.0,
        prompt,
        "query",
        "docs:0",
        "digest",
        policy,
    )
    input_path = tmp_path / "records.csv"
    pd.DataFrame(records).to_csv(input_path, index=False)
    ledger, summary = import_generation_records(input_path, Path("trail/generation/generation_record_schema.yaml"), 5.0)

    assert len(records) == 2
    assert summary["harness_pass_rows"] == 2
    assert set(ledger["strategy"]) == {"llm_rag_principle_generation"}
    assert "llm_smiles_generation" in records[0]["candidate_json"]
