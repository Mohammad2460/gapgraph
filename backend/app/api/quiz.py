"""Quiz generation.  [Pillar A]"""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.extraction import cache
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

    doc = store.documents.get(req.graph_id)
    if settings.mock_extraction:
        key = sample_quiz_key()
        key.graph_id = graph.id
    elif doc is not None and (cached := cache.load_quiz(doc.raw)) is not None:
        key = cached  # demo safety: replay the quiz saved from a real run
        key.graph_id = graph.id
    else:
        try:
            key = await generate_quiz(graph, req.num_questions)
        except Exception as e:
            raise HTTPException(502, f"Quiz generation failed: {e}") from e
        if doc is not None:
            cache.save(doc.raw, key)

    store.quizzes[key.quiz_id] = key
    # Strip answers before sending to the client.
    return Quiz(
        quiz_id=key.quiz_id,
        graph_id=key.graph_id,
        questions=[Question.model_validate(q.model_dump()) for q in key.questions],
    )
