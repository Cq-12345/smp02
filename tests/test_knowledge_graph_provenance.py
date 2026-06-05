from __future__ import annotations

from pathlib import Path

from trail.knowledge.build_kg import build_graph, graph_summary


def test_knowledge_graph_contains_sources_and_process_templates() -> None:
    graph = build_graph(Path("trail/knowledge/smp_prior_knowledge.yaml"), Path("trail/knowledge/ontology.yaml"))
    summary = graph_summary(graph)
    assert summary["node_kinds"]["literature_source"] >= 5
    assert summary["node_kinds"]["process_condition_template"] >= 8
    assert summary["edge_relations"]["supported_by_source"] >= 30
    assert summary["edge_relations"]["conditioned_by_process"] == 20
    assert graph.has_edge("epoxy_primary_amine", "epoxy_amine_thermal_cure")
    assert graph.has_edge("aromatic_backbones_raise_tg", "teimouri_2024_ml_smp")
