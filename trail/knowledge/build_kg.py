from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
import yaml


def add_principle_node(graph: nx.MultiDiGraph, principle: dict, kind: str) -> None:
    pid = str(principle["id"])
    graph.add_node(
        pid,
        kind=kind,
        effect=str(principle.get("effect", "")),
        feature=str(principle.get("feature", "")),
        rationale=str(principle.get("rationale", "")),
    )
    graph.add_edge(pid, "glass_transition_temperature", relation="influences")
    feature = principle.get("feature")
    if feature:
        graph.add_node(str(feature), kind="feature")
        graph.add_edge(str(feature), pid, relation="supports_principle")


def build_graph(knowledge_path: Path, ontology_path: Path) -> nx.MultiDiGraph:
    knowledge = yaml.safe_load(knowledge_path.read_text(encoding="utf-8"))
    ontology = yaml.safe_load(ontology_path.read_text(encoding="utf-8"))
    graph = nx.MultiDiGraph()
    graph.add_node("glass_transition_temperature", kind="target_property", symbol="Tg", unit="Celsius")
    for cls, attrs in ontology["classes"].items():
        graph.add_node(cls, kind="class", **attrs)
    for rel, attrs in ontology["relations"].items():
        graph.add_node(rel, kind="relation", **attrs)

    for constraint in knowledge.get("hard_constraints", []):
        cid = str(constraint["id"])
        graph.add_node(cid, kind="hard_constraint", description=str(constraint.get("description", "")))
        graph.add_edge("SMPRecipe", cid, relation="constrained_by")

    priors = knowledge.get("priors", {})
    for principle in priors.get("structural_principles", []):
        add_principle_node(graph, principle, "structural_principle")
    for principle in priors.get("applicability_principles", []):
        add_principle_node(graph, principle, "applicability_principle")

    for name, principle in knowledge["reaction_principles"].items():
        graph.add_node(
            name,
            kind="reaction_principle",
            expected_network=str(principle.get("expected_network", "")),
            mechanism=str(principle.get("mechanism", "")),
            confidence=str(principle.get("confidence", "")),
            notes=str(principle.get("notes", "")),
        )
        for group in principle["groups"]:
            graph.add_node(group, kind="functional_group")
            graph.add_edge(group, name, relation="compatible_via")
        network = str(principle.get("expected_network", "network"))
        graph.add_node(network, kind="network_type")
        graph.add_edge(name, network, relation="produces_network")

    for name, source in knowledge.get("literature_sources", {}).items():
        graph.add_node(
            name,
            kind="literature_source",
            source_type=str(source.get("source_type", "")),
            local_file=str(source.get("local_file", "")),
            evidence_scope=";".join(source.get("evidence_scope", [])),
            notes=str(source.get("notes", "")),
        )

    for name, template in knowledge.get("process_condition_templates", {}).items():
        graph.add_node(
            name,
            kind="process_condition_template",
            trigger=str(template.get("trigger", "")),
            catalyst=str(template.get("catalyst", "")),
            cure_schedule_fields=";".join(template.get("cure_schedule_fields", [])),
            notes=str(template.get("notes", "")),
        )

    for reaction_name, evidence in knowledge.get("reaction_evidence_map", {}).items():
        if reaction_name not in graph:
            continue
        process_template = evidence.get("process_template")
        if process_template and process_template in graph:
            graph.add_edge(reaction_name, process_template, relation="conditioned_by_process")
        for source_name in evidence.get("evidence_sources", []):
            if source_name in graph:
                graph.add_edge(reaction_name, source_name, relation="supported_by_source")

    for principle_name, source_names in knowledge.get("structural_evidence_map", {}).items():
        if principle_name not in graph:
            continue
        for source_name in source_names:
            if source_name in graph:
                graph.add_edge(principle_name, source_name, relation="supported_by_source")

    for name, source in knowledge.get("candidate_sources", {}).items():
        graph.add_node(name, kind="candidate_source", **source)
        graph.add_edge("Monomer", name, relation="sourced_from")
    return graph


def graph_summary(graph: nx.MultiDiGraph) -> dict[str, object]:
    kind_counts: dict[str, int] = {}
    for _, attrs in graph.nodes(data=True):
        kind = str(attrs.get("kind", "unknown"))
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
    relation_counts: dict[str, int] = {}
    for _, _, attrs in graph.edges(data=True):
        relation = str(attrs.get("relation", "unknown"))
        relation_counts[relation] = relation_counts.get(relation, 0) + 1
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "node_kinds": dict(sorted(kind_counts.items())),
        "edge_relations": dict(sorted(relation_counts.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge", default="trail/knowledge/smp_prior_knowledge.yaml")
    parser.add_argument("--ontology", default="trail/knowledge/ontology.yaml")
    parser.add_argument("--out", default="artifacts/trail/kg")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    graph = build_graph(Path(args.knowledge), Path(args.ontology))
    nx.write_graphml(graph, out / "smp_knowledge_graph.graphml")
    data = nx.node_link_data(graph, edges="edges")
    (out / "smp_knowledge_graph.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "smp_knowledge_graph_summary.json").write_text(
        json.dumps(graph_summary(graph), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
