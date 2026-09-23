"""Graph construction and queries over scenario structure."""

from __future__ import annotations

import networkx as nx

from .models import Scenario


def build(scenario: Scenario) -> nx.DiGraph:
    """Build a directed graph of a scenario's entities and relations."""
    g = nx.DiGraph()
    for entity in scenario.entities:
        g.add_node(entity.id, name=entity.name, **entity.attributes)
    for relation in scenario.relations:
        g.add_edge(relation.source, relation.target, kind=relation.kind, **relation.attributes)
    return g


def describe(g: nx.DiGraph) -> str:
    """Render a graph back to text for prompting or inspection."""
    lines = [
        f"{g.nodes[u].get('name', u)} --{d.get('kind', '?')}--> {g.nodes[v].get('name', v)}"
        for u, v, d in g.edges(data=True)
    ]
    return "\n".join(lines)
