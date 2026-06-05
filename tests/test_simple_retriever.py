from __future__ import annotations

from trail.rag.simple_retriever import retrieve


def test_retrieve_ignores_single_character_and_numeric_noise() -> None:
    docs = [
        ("noisy", "C " * 200 + "0 " * 200),
        ("strict", "strict generation_feedback_strict replacement_rejections functional_group_replacement"),
    ]

    results = retrieve("target Tg 195 C strict replacement_rejections 0", docs, top_k=1)

    assert results[0][0] == "strict"
