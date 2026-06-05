from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx
import yaml


def build_graph(knowledge_path: Path, ontology_path: Path) -> nx.MultiDiGraph:
    knowledge = yaml.safe_load(knowledge_path.read_text(encoding="utf-8"))
    ontology = yaml.safe_load(ontology_path.read_text(encoding="utf-8"))
    graph = nx.MultiDiGraph()
    for cls, attrs in ontology["classes"].items():
        graph.add_node(cls, kind="class", **attrs)
    for rel, attrs in ontology["relations"].items():
        graph.add_node(rel, kind="relation", **attrs)
    for feature in knowledge["priors"]["high_tg_features"]:
        graph.add_node(feature, kind="prior_feature", effect="raises_Tg")
        graph.add_edge(feature, "glass_transition_temperature", relation="influences")
    for feature in knowledge["priors"]["lower_tg_risk_features"]:
        graph.add_node(feature, kind="prior_feature", effect="lowers_Tg_risk")
        graph.add_edge(feature, "glass_transition_temperature", relation="influences")
    for name, principle in knowledge["reaction_principles"].items():
        graph.add_node(name, kind="reaction_principle", expected_network=principle["expected_network"])
        for group in principle["groups"]:
            graph.add_node(group, kind="functional_group")
            graph.add_edge(group, name, relation="compatible_via")
    return graph


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
    (out / "smp_knowledge_graph.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

