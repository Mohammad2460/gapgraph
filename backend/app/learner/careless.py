"""Separate careless slips from real gaps.  [Pillar B — task B3, the STRETCH GOAL]

A wrong answer is likely CARELESS when most of these hold:
  - all direct prerequisites are mastered
  - learner confidence was high (>= 0.7)
  - answer was fast (time_ms well below the median for the quiz)
  - (if >1 question on the concept) other answers on it were correct
Otherwise it's a REAL gap.
"""

from statistics import fmean, median

from app.learner.mastery import P_INIT
from app.models import Answer, ConceptMastery, Graph, QuestionKey


def careless_score(
    graph: Graph,
    question: QuestionKey,
    answer: Answer,
    mastery: dict[str, ConceptMastery],
    median_time_ms: float,
) -> float:
    """Score a possible slip from prerequisites, confidence, and relative speed.

    This is a heuristic, not a calibrated probability. Consistency with other
    answers on the concept is applied by classify_careless.
    """
    if answer.choice_index == question.answer_index:
        return 0.0
    prereqs = {edge.source for edge in graph.edges if edge.target == question.concept_id}
    prerequisite_mastery = fmean(
        mastery[concept_id].p_known if concept_id in mastery else 0.0
        for concept_id in prereqs
    ) if prereqs else P_INIT
    speed = 0.0
    if answer.time_ms is not None and answer.time_ms > 0 and median_time_ms > 0:
        speed = max(0.0, 1 - answer.time_ms / median_time_ms)
    return 0.4 * prerequisite_mastery + 0.25 * answer.confidence + 0.35 * speed


def classify_careless(
    graph: Graph,
    questions: list[QuestionKey],
    answers: list[Answer],
    mastery: dict[str, ConceptMastery],
    threshold: float = 0.6,
) -> list[str]:
    """Mark concepts whose wrong answers look like slips and soften their evidence.

    Other wrong answers on the same concept lower the score. All its wrong
    answers must meet the threshold before the concept is marked careless.
    """
    concept_ids = {concept.id for concept in graph.concepts}
    questions_by_id = {question.id: question for question in questions}
    by_concept: dict[str, list[tuple[QuestionKey, Answer]]] = {}
    # One response per question; repeated submissions are not independent evidence.
    for answer in {answer.question_id: answer for answer in answers}.values():
        question = questions_by_id.get(answer.question_id)
        if question is None or question.concept_id not in concept_ids:
            continue
        if question.concept_id not in mastery:
            continue
        by_concept.setdefault(question.concept_id, []).append((question, answer))
    times = [
        answer.time_ms for pairs in by_concept.values() for _, answer in pairs
        if answer.time_ms is not None and answer.time_ms > 0
    ]
    median_time_ms = median(times) if times else 0.0
    careless = []
    for concept_id, pairs in sorted(by_concept.items()):
        wrong = [
            (question, answer) for question, answer in pairs
            if answer.choice_index != question.answer_index
        ]
        if not wrong:
            continue
        consistency = 1.0
        if len(pairs) > 1:
            other_correct = (len(pairs) - len(wrong)) / (len(pairs) - 1)
            consistency = 0.5 + 0.5 * other_correct
        scores = [
            careless_score(graph, question, answer, mastery, median_time_ms) * consistency
            for question, answer in wrong
        ]
        if all(score >= threshold for score in scores):
            careless.append(concept_id)

    # Apply decisions together so earlier classifications cannot change later scores.
    for concept_id in careless:
        mastery[concept_id].status = "careless"
        mastery[concept_id].p_known = max(P_INIT, mastery[concept_id].p_known)
    return careless
