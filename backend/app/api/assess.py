"""Assessment -> mastery, root gaps, next topics.  [Pillar B]"""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.fixtures import sample_assessment, sample_graph, sample_next_question
from app.learner.adaptive import next_question
from app.learner.embeddings import apply_history
from app.learner.service import assess
from app.models import AssessmentResult, AssessRequest, NextQuestion, NextQuestionRequest
from app.store import store

router = APIRouter()


@router.post("/assess", response_model=AssessmentResult)
async def assess_quiz(req: AssessRequest) -> AssessmentResult:
    quiz = store.quizzes.get(req.quiz_id)
    if quiz is None:
        raise HTTPException(404, "Unknown quiz")
    graph = sample_graph() if quiz.graph_id == "demo" else store.graphs.get(quiz.graph_id)
    if graph is None:
        raise HTTPException(404, "Unknown graph")

    if settings.mock_learner:
        result = sample_assessment()
        result.quiz_id, result.graph_id = quiz.quiz_id, graph.id
        return result
    result = assess(graph, quiz, req.answers)
    if req.learner_id:  # B7 history is opt-in and per learner
        result = apply_history(graph, result, req.learner_id)
    return result


@router.post("/quiz/{quiz_id}/next", response_model=NextQuestion)
async def adaptive_next(quiz_id: str, req: NextQuestionRequest) -> NextQuestion:
    """B6 adaptive probing: after a miss, ask about the failed concept's weakest prerequisite."""
    quiz = store.quizzes.get(quiz_id)
    if quiz is None:
        raise HTTPException(404, "Unknown quiz")
    graph = sample_graph() if quiz.graph_id == "demo" else store.graphs.get(quiz.graph_id)
    if graph is None:
        raise HTTPException(404, "Unknown graph")

    if settings.mock_learner:
        return sample_next_question()
    return next_question(graph, quiz, req.answers)
