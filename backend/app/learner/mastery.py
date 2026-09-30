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
    """TODO(B1): one Bayes update step. Return posterior P(known)."""
    raise NotImplementedError("B1: BKT update")


def estimate_mastery(
    graph: Graph, questions: list[QuestionKey], answers: list[Answer]
) -> dict[str, ConceptMastery]:
    """TODO(B1): return one ConceptMastery per concept in graph.concepts.

    status: mastered (>= MASTERED_AT), gap (< GAP_BELOW), shaky (between),
    untested (evidence_count == 0). "careless" is assigned later by careless.py.
    """
    raise NotImplementedError("B1: estimate mastery")
