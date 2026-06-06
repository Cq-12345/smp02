from __future__ import annotations

from pathlib import Path

from scripts.build_todo_completion_audit import build_audit


def test_todo_completion_audit_counts_present_missing_and_deferred(tmp_path: Path) -> None:
    existing = tmp_path / "existing.md"
    existing.write_text("ok", encoding="utf-8")
    entries = [
        {
            "task_id": "implemented",
            "todo_area": "implemented task",
            "status": "implemented",
            "evidence_paths": ["existing.md"],
            "next_action": "none",
        },
        {
            "task_id": "missing",
            "todo_area": "missing task",
            "status": "implemented",
            "evidence_paths": ["missing.md"],
            "next_action": "add evidence",
        },
        {
            "task_id": "deferred",
            "todo_area": "deferred task",
            "status": "deferred_by_user",
            "evidence_paths": ["existing.md"],
            "next_action": "wait",
        },
    ]

    frame, summary = build_audit(tmp_path, entries)

    assert len(frame) == 3
    assert summary["implemented_rows"] == 2
    assert summary["deferred_rows"] == 1
    assert summary["all_evidence_present_rows"] == 2
    assert summary["missing_evidence_rows"] == 1
    assert summary["non_deferred_all_evidence_present"] is False
    assert summary["missing_evidence_task_ids"] == ["missing"]
