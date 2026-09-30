"""Graph -> 5-10 diagnostic questions.  [Pillar A — task A5]"""

from app.models import Graph, QuizKey


async def generate_quiz(graph: Graph, num_questions: int) -> QuizKey:
    """TODO(A5):
    - Pick `num_questions` concepts: prefer high importance + good graph coverage
      (include the most advanced nodes AND some of their prerequisites, so the
      gap locator has evidence along the chains).
    - Ask Claude (prompts.QUIZ_SYSTEM/QUIZ_USER) for one QuestionKey per concept
      (wrap in a small pydantic model with `questions: list[QuestionKey]`).
    - Assign ids q1..qN, return QuizKey(quiz_id=<uuid>, graph_id=graph.id, ...).
    """
    raise NotImplementedError("A5: quiz generation")
