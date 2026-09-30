"""Graph -> 5-10 diagnostic questions.  [Pillar A — task A5]"""

import uuid

import networkx as nx
from pydantic import BaseModel

from app.extraction import llm, prompts
from app.graph.algorithms import learning_order, to_nx
from app.models import Graph, QuestionKey, QuizKey


class _QuizDraft(BaseModel):
    questions: list[QuestionKey]


def select_concepts(graph: Graph, n: int) -> list[str]:
    """Pick up to n concept ids: the most advanced nodes first, then walk up their
    prerequisite chains, so the gap locator has evidence along each chain.
    Returned in learning order (prerequisites first)."""
    g = to_nx(graph)
    importance = {c.id: c.importance for c in graph.concepts}
    depth = {c: len(nx.ancestors(g, c)) for c in g.nodes}
    ranked = sorted(g.nodes, key=lambda c: (depth[c], importance[c]), reverse=True)

    picked: list[str] = []
    for root in ranked:
        frontier = [root]
        while frontier and len(picked) < n:
            node = frontier.pop(0)
            if node in picked:
                continue
            picked.append(node)
            frontier += sorted(g.predecessors(node), key=lambda c: -importance[c])
        if len(picked) >= n:
            break
    return learning_order(g, set(picked))


async def generate_quiz(graph: Graph, num_questions: int) -> QuizKey:
    """One question per selected concept, validated and numbered q1..qN."""
    by_id = {c.id: c for c in graph.concepts}
    picked = select_concepts(graph, num_questions)
    lines = "\n".join(
        f"{c.id}: {c.name} — {c.definition} — {c.source_excerpt}" for c in map(by_id.get, picked)
    )
    draft = await llm.structured(
        prompts.QUIZ_SYSTEM, prompts.QUIZ_USER.format(concepts=lines), _QuizDraft
    )

    first: dict[str, QuestionKey] = {}
    for q in draft.questions:
        valid = len(q.options) == 4 and 0 <= q.answer_index < 4
        if q.concept_id in picked and valid and q.concept_id not in first:
            first[q.concept_id] = q
    questions = [first[c] for c in picked if c in first]
    if not questions:
        raise RuntimeError("Claude returned no usable quiz questions")
    for i, q in enumerate(questions, start=1):
        q.id = f"q{i}"
    return QuizKey(quiz_id=uuid.uuid4().hex[:8], graph_id=graph.id, questions=questions)
