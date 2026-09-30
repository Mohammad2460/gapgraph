"""Root-cause gap tracing — our core differentiator.  [Pillar B — task B2]"""

from app.models import ConceptMastery, Graph, RootGap

WEAK = {"gap", "shaky"}


def find_root_gaps(graph: Graph, mastery: dict[str, ConceptMastery]) -> list[RootGap]:
    """TODO(B2): for every concept with status "gap":
    - walk UP prerequisite edges (graph.algorithms.all_prerequisites / prerequisites)
    - the root gap = the deepest weak ancestor (status in WEAK, or untested with low
      p_known) whose own prerequisites are NOT weak. If none, the failed concept is
      its own root.
    - path = shortest path root -> failed (nx.shortest_path on to_nx(graph)).
    - explanation = plain-English sentence naming the chain, e.g.
      "You missed Backpropagation because it depends on the Chain Rule, which you
       also missed. Fix the Chain Rule first."
    Deduplicate: several failed concepts can share one root.
    """
    raise NotImplementedError("B2: root gap tracing")
