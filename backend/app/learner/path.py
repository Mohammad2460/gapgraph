"""Suggested next topics.  [Pillar B — task B4]"""

from app.models import ConceptMastery, Graph, NextTopic, RootGap


def suggest_next_topics(
    graph: Graph,
    mastery: dict[str, ConceptMastery],
    root_gaps: list[RootGap],
    careless: list[str],
    limit: int = 5,
) -> list[NextTopic]:
    """TODO(B4):
    - Collect every concept on a root-gap path (root first).
    - Order with graph.algorithms.learning_order(g, subset) so prereqs come first.
    - reason: "Root gap: blocks X" / "Retry once Y is solid".
    - Append careless concepts last with reason "Quick re-check only".
    - If no gaps: suggest the next UNTESTED concepts whose prereqs are all mastered
      ("Ready to learn").
    """
    raise NotImplementedError("B4: next topics")
