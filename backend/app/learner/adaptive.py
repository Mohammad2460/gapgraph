"""Adaptive probing.  [Pillar B — task B6]

After a wrong answer on concept C, ask next about C's weakest prerequisite, to
locate the root gap in fewer questions. Served by POST /api/quiz/{quiz_id}/next.
"""

import networkx as nx

from app.graph.algorithms import to_nx
from app.learner.mastery import estimate_mastery
from app.models import Answer, Graph, NextQuestion, Question, QuizKey


def next_question(graph: Graph, quiz: QuizKey, answers: list[Answer]) -> NextQuestion:
    """Pick the next unanswered quiz question.

    Walk misses from latest to earliest; for the first one with an unanswered
    prerequisite question, ask the weakest such prerequisite (lowest p_known, then
    least evidence, then closest, then quiz order). Otherwise go in quiz order.
    """
    answered = {a.question_id for a in answers}
    remaining = [q for q in quiz.questions if q.id not in answered]
    if not remaining:
        return NextQuestion(question=None, reason="Quiz complete", remaining=0)

    g = to_nx(graph)
    names = {c.id: c.name for c in graph.concepts}
    by_id = {q.id: q for q in quiz.questions}
    mastery = estimate_mastery(graph, quiz.questions, answers)
    order = {q.id: i for i, q in enumerate(quiz.questions)}

    misses = [
        by_id[a.question_id].concept_id
        for a in answers
        if a.question_id in by_id and a.choice_index != by_id[a.question_id].answer_index
    ]
    for failed in reversed(misses):
        if failed not in g:
            continue
        dist = nx.single_source_shortest_path_length(g.reverse(copy=False), failed)
        probes = [q for q in remaining if q.concept_id != failed and q.concept_id in dist]
        if not probes:
            continue
        pick = min(
            probes,
            key=lambda q: (
                mastery[q.concept_id].p_known if q.concept_id in mastery else 0.5,
                mastery[q.concept_id].evidence_count if q.concept_id in mastery else 0,
                dist[q.concept_id],
                order[q.id],
            ),
        )
        reason = (
            f"You missed {names[failed]}: checking its prerequisite "
            f"{names.get(pick.concept_id, pick.concept_id)}"
        )
        return _result(pick, reason, len(remaining))

    return _result(remaining[0], "Next question", len(remaining))


def _result(q, reason: str, n_remaining: int) -> NextQuestion:
    return NextQuestion(
        question=Question.model_validate(q.model_dump()),
        target_concept_id=q.concept_id,
        reason=reason,
        remaining=n_remaining - 1,
    )
