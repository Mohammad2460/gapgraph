"""Suggested next topics.  [Pillar B — task B4]"""

from app.graph.algorithms import learning_order, prerequisites, to_nx
from app.models import ConceptMastery, Graph, NextTopic, RootGap


def suggest_next_topics(
    graph: Graph,
    mastery: dict[str, ConceptMastery],
    root_gaps: list[RootGap],
    careless: list[str],
    limit: int = 5,
) -> list[NextTopic]:
    """Study plan: root-gap paths in learning order (root first), careless slips last.

    With no gaps, suggest untested concepts whose prerequisites are all mastered.
    """
    g = to_nx(graph)
    names = {c.id: c.name for c in graph.concepts}
    slips = [c for c in careless if c in names]

    on_path = {c for gap in root_gaps for c in gap.path if c in names} - set(slips)
    roots = {gap.concept_id for gap in root_gaps}
    blocks: dict[str, list[str]] = {}
    retry_after: dict[str, str] = {}
    for gap in root_gaps:
        if gap.failed_concept_id != gap.concept_id:
            blocks.setdefault(gap.concept_id, []).append(names[gap.failed_concept_id])
        for prev, cur in zip(gap.path, gap.path[1:], strict=False):
            retry_after.setdefault(cur, prev)

    plan: list[tuple[str, str]] = []
    for cid in learning_order(g, on_path):
        if cid in roots:
            blocked = ", ".join(dict.fromkeys(blocks.get(cid, [])))
            reason = f"Root gap: blocks {blocked}" if blocked else "Root gap: review first"
            plan.append((cid, reason))
        else:
            plan.append((cid, f"Retry once {names[retry_after[cid]]} is solid"))

    if not plan:
        ready = {
            cid
            for cid, m in mastery.items()
            if cid in names
            and m.status == "untested"
            and all(mastery[p].status == "mastered" for p in prerequisites(g, cid))
        }
        plan = [(cid, "Ready to learn") for cid in learning_order(g, ready)]

    plan += [(cid, "Quick re-check only") for cid in slips]
    return [
        NextTopic(concept_id=cid, order=i, reason=reason)
        for i, (cid, reason) in enumerate(plan[:limit], start=1)
    ]
