"""Root-cause gap tracing — our core differentiator.  [Pillar B — task B2]"""

import networkx as nx

from app.learner.mastery import GAP_BELOW
from app.models import ConceptMastery, Graph, RootGap

WEAK = {"gap", "shaky"}


def find_root_gaps(graph: Graph, mastery: dict[str, ConceptMastery]) -> list[RootGap]:
    """Trace each gap to its deepest weak prerequisite and explain the path.

    Prefer weak ancestors with no weak prerequisite earlier in the chain. If there are
    several, choose the furthest upstream, then the lowest mastery probability,
    then the concept id. Keep one trace per failed concept, even for shared roots.
    """
    concepts = {concept.id: concept for concept in graph.concepts}
    dag = nx.DiGraph()
    dag.add_nodes_from(concepts)
    dag.add_edges_from(sorted(
        (edge.source, edge.target) for edge in graph.edges
        if edge.source in concepts and edge.target in concepts
    ))
    prerequisites = dag.reverse(copy=False)
    weak = {
        concept_id for concept_id in concepts
        if concept_id in mastery and (
            mastery[concept_id].status in WEAK
            or (
                mastery[concept_id].status == "untested"
                and mastery[concept_id].p_known < GAP_BELOW
            )
        )
    }
    weak_roots = {
        concept_id for concept_id in weak
        if not (nx.ancestors(dag, concept_id) & weak)
    }

    roots = []
    for failed_id in concepts:
        if failed_id not in mastery or mastery[failed_id].status != "gap":
            continue
        distances = nx.single_source_shortest_path_length(prerequisites, failed_id)
        candidates = [
            concept_id for concept_id in distances
            if concept_id != failed_id and concept_id in weak_roots
        ]
        root_id = min(
            candidates,
            key=lambda concept_id: (
                -distances[concept_id], mastery[concept_id].p_known, concept_id,
            ),
        ) if candidates else failed_id
        path = nx.shortest_path(dag, root_id, failed_id)
        root_name = concepts[root_id].name
        explanation = (
            f"Your answers suggest {root_name} needs more practice. "
            f"Review {root_name} first."
        )
        if root_id != failed_id:
            chain = " ".join(
                f"{concepts[target].name} builds on {concepts[source].name}."
                for source, target in zip(path, path[1:])
            )
            explanation = f"You missed {concepts[failed_id].name}. {chain} {explanation}"
        roots.append(RootGap(
            concept_id=root_id,
            failed_concept_id=failed_id,
            path=path,
            explanation=explanation,
        ))
    return roots
