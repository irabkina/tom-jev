"""Graph construction and queries over scenario structure.

Builds a directed graph whose nodes are the scenario's entities and whose
edges come from observations — useful for inspecting structure and for
checking that matched scenarios in a `scenario_set` really are structurally
parallel.

Mental states are not edges here. They are held by an agent about a
proposition rather than relating two entities, and folding them in would
blur the sparse/rich distinction the experiment depends on.
"""

from __future__ import annotations

import networkx as nx

from .models import Scenario


def build(scenario: Scenario) -> nx.MultiDiGraph:
    """Build a directed graph of a scenario's entities and observations.

    A MultiDiGraph, because the same pair of entities may be related more
    than once (an agent can act on an object repeatedly).
    """
    g = nx.MultiDiGraph()
    for kind, group in (
        ("agent", scenario.entities.agents),
        ("location", scenario.entities.locations),
        ("object", scenario.entities.objects),
    ):
        for entity in group:
            g.add_node(entity.id, name=entity.name, kind=kind)

    for obs in scenario.observations:
        for role, target in obs.arguments().items():
            if isinstance(target, str) and target in g:
                g.add_edge(obs.agent, target, kind=obs.type, role=role)
    return g


def describe(g: nx.MultiDiGraph) -> str:
    """Render a graph back to text for inspection."""
    return "\n".join(
        f"{g.nodes[u].get('name', u)} --{d.get('kind', '?')}--> {g.nodes[v].get('name', v)}"
        for u, v, d in g.edges(data=True)
    )
