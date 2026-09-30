"""Merge per-chunk extractions into one clean DAG.  [Pillar A — task A3]"""

from app.models import Concept, Edge, ExtractionResult, Graph


class GraphBuilder:
    def __init__(self, graph_id: str, title: str):
        self.graph_id = graph_id
        self.title = title
        self.concepts: dict[str, Concept] = {}
        self.edges: dict[tuple[str, str], Edge] = {}

    def merge(self, result: ExtractionResult) -> tuple[list[Concept], list[Edge]]:
        """Add a chunk's result; return only the NEW concepts/edges (for streaming).

        TODO(A3):
        - normalize ids (lowercase, snake_case, strip plurals) and merge duplicates
          (same id or near-identical name) — keep the longer definition.
        - drop edges whose endpoints are unknown or that are self-loops.
        - drop an edge if adding it would create a cycle (nx.has_path(target, source)).
        """
        raise NotImplementedError("A3: merge extraction into graph")

    def finalize(self) -> Graph:
        """TODO(A3): compute importance (e.g. normalized PageRank / out-degree) if the
        LLM gave flat values; cap to ~40 nodes by importance; return Graph."""
        return Graph(
            id=self.graph_id,
            title=self.title,
            concepts=list(self.concepts.values()),
            edges=list(self.edges.values()),
        )
