"""Separate careless slips from real gaps.  [Pillar B — task B3, the STRETCH GOAL]

A wrong answer is likely CARELESS when most of these hold:
  - all direct prerequisites are mastered
  - learner confidence was high (>= 0.7)
  - answer was fast (time_ms well below the median for the quiz)
  - (if >1 question on the concept) other answers on it were correct
Otherwise it's a REAL gap.
"""

from app.models import Answer, ConceptMastery, Graph, QuestionKey


def careless_score(
    graph: Graph,
    question: QuestionKey,
    answer: Answer,
    mastery: dict[str, ConceptMastery],
    median_time_ms: float,
) -> float:
    """TODO(B3): return 0..1 likelihood this wrong answer was a slip. Weighted sum of
    the signals above is fine — keep it explainable for the demo."""
    raise NotImplementedError("B3: careless score")


def classify_careless(
    graph: Graph,
    questions: list[QuestionKey],
    answers: list[Answer],
    mastery: dict[str, ConceptMastery],
    threshold: float = 0.6,
) -> list[str]:
    """TODO(B3): for each WRONG answer with careless_score >= threshold, set that
    concept's status to "careless" (and restore p_known toward its prior, since
    the evidence is unreliable). Mutates `mastery`; returns careless concept ids."""
    raise NotImplementedError("B3: classify careless slips")
