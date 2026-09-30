"""Answers -> per-concept mastery.  [Pillar B — task B1]

Simplified Bayesian Knowledge Tracing (Corbett & Anderson 1994):
    P(correct | known)   = 1 - P_SLIP
    P(correct | unknown) = P_GUESS
    posterior P(known) via Bayes after each answer on that concept.
Then propagate weak evidence through the graph:
    - correct on a concept  -> nudge its prerequisites up   (you can't do B without A)
    - untested concepts     -> prior, or average of tested neighbours
"""

from app.models import Answer, ConceptMastery, Graph, QuestionKey

P_INIT = 0.5  # prior P(known)
P_SLIP = 0.1  # knows it, answers wrong anyway
P_GUESS = 0.25  # doesn't know it, guesses right (4 options)

MASTERED_AT = 0.7
GAP_BELOW = 0.4  # between the two -> "shaky"


def bkt_update(p_known: float, correct: bool) -> float:
    """Update the chance of knowing a concept after one answer."""
    if correct:
        known_likelihood, unknown_likelihood = 1 - P_SLIP, P_GUESS
    else:
        known_likelihood, unknown_likelihood = P_SLIP, 1 - P_GUESS
    known_evidence = p_known * known_likelihood
    return known_evidence / (
        known_evidence + (1 - p_known) * unknown_likelihood
    )


def estimate_mastery(
    graph: Graph, questions: list[QuestionKey], answers: list[Answer]
) -> dict[str, ConceptMastery]:
    """Return one mastery estimate per graph concept.

    status: mastered (>= MASTERED_AT), gap (< GAP_BELOW), shaky (between),
    untested (evidence_count == 0). "careless" is assigned later by careless.py.
    """
    probabilities = {concept.id: P_INIT for concept in graph.concepts}
    evidence_counts = {concept_id: 0 for concept_id in probabilities}
    questions_by_id = {question.id: question for question in questions}
    prerequisites: dict[str, list[str]] = {concept_id: [] for concept_id in probabilities}
    for edge in graph.edges:
        if edge.source in probabilities and edge.target in probabilities:
            prerequisites[edge.target].append(edge.source)

    correct_concepts: list[str] = []
    for answer in answers:
        question = questions_by_id.get(answer.question_id)
        if question is None or question.concept_id not in probabilities:
            continue
        concept_id = question.concept_id
        correct = answer.choice_index == question.answer_index
        probabilities[concept_id] = bkt_update(probabilities[concept_id], correct)
        evidence_counts[concept_id] += 1
        if correct:
            correct_concepts.append(concept_id)

    # A correct answer lends a little support to its direct prerequisites.
    # Keep the evidence count direct: inferred knowledge is still untested.
    for concept_id in correct_concepts:
        for prereq_id in prerequisites[concept_id]:
            probabilities[prereq_id] += 0.05 * (1 - probabilities[prereq_id])

    mastery = {}
    for concept_id, p_known in probabilities.items():
        count = evidence_counts[concept_id]
        if count == 0:
            status = "untested"
        elif p_known >= MASTERED_AT:
            status = "mastered"
        elif p_known < GAP_BELOW:
            status = "gap"
        else:
            status = "shaky"
        mastery[concept_id] = ConceptMastery(
            concept_id=concept_id,
            p_known=p_known,
            status=status,
            evidence_count=count,
        )
    return mastery
