"""NetworkX helpers shared by Pillar A (build) and Pillar B (gap logic).

Owner: Pillar A. Pillar B may ADD functions here; don't change existing signatures.
Edge direction: prerequisite -> dependent (source -> target).
"""

import networkx as nx

from app.models import Graph


def to_nx(graph: Graph) -> nx.DiGraph:
    g = nx.DiGraph()
    for c in graph.concepts:
        g.add_node(c.id, **c.model_dump())
    for e in graph.edges:
        if e.source in g and e.target in g:
            g.add_edge(e.source, e.target, **e.model_dump())
    return g


def prerequisites(g: nx.DiGraph, concept_id: str) -> list[str]:
    """Direct prerequisites of a concept."""
    return list(g.predecessors(concept_id))


def all_prerequisites(g: nx.DiGraph, concept_id: str) -> set[str]:
    """Every concept upstream of `concept_id`."""
    return nx.ancestors(g, concept_id)


def dependents(g: nx.DiGraph, concept_id: str) -> list[str]:
    return list(g.successors(concept_id))


def learning_order(g: nx.DiGraph, subset: set[str] | None = None) -> list[str]:
    """Topological order (prereqs first), optionally restricted to `subset`."""
    h = g.subgraph(subset) if subset is not None else g
    return list(nx.topological_sort(h))
