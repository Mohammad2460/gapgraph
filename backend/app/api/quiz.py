"""Quiz generation.  [Pillar A]"""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.extraction.quiz_gen import generate_quiz
from app.fixtures import sample_graph, sample_quiz_key
from app.models import Question, Quiz, QuizRequest
from app.store import store

router = APIRouter()


@router.post("/quiz", response_model=Quiz)
async def create_quiz(req: QuizRequest) -> Quiz:
    graph = sample_graph() if req.graph_id == "demo" else store.graphs.get(req.graph_id)
    if graph is None:
        raise HTTPException(404, "Unknown graph")

    if settings.mock_extraction:
        key = sample_quiz_key()
        key.graph_id = graph.id
    else:
        key = await generate_quiz(graph, req.num_questions)

    store.quizzes[key.quiz_id] = key
    # Strip answers before sending to the client.
    return Quiz(
        quiz_id=key.quiz_id,
        graph_id=key.graph_id,
        questions=[Question.model_validate(q.model_dump()) for q in key.questions],
    )
