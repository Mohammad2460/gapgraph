"""Assessment -> mastery, root gaps, next topics.  [Pillar B]"""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.fixtures import sample_assessment, sample_graph
from app.learner.service import assess
from app.models import AssessmentResult, AssessRequest
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
    return assess(graph, quiz, req.answers)
