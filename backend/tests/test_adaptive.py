"""B6 — adaptive probing: after a miss, ask about the failed concept's weakest prerequisite."""

import networkx as nx
from fastapi.testclient import TestClient

from app.config import settings
from app.fixtures import sample_graph, sample_next_question, sample_quiz_key
from app.graph.algorithms import to_nx
from app.learner.adaptive import next_question
from app.main import app
from app.models import Answer


def _answer(quiz, concept_id: str, correct: bool) -> Answer:
    q = next(q for q in quiz.questions if q.concept_id == concept_id)
    choice = q.answer_index if correct else (q.answer_index + 1) % 4
    return Answer(question_id=q.id, choice_index=choice, confidence=0.5, time_ms=10000)


def test_b6_miss_probes_a_prerequisite_of_the_failed_concept():
    graph, quiz = sample_graph(), sample_quiz_key()
    answers = [_answer(quiz, "derivatives", True), _answer(quiz, "backpropagation", False)]
    nq = next_question(graph, quiz, answers)
    assert nq.target_concept_id == nq.question.concept_id == "chain_rule"
    assert "Backpropagation" in nq.reason and "Chain Rule" in nq.reason
    assert nq.remaining == len(quiz.questions) - 3  # 2 answered + this one
    assert not hasattr(nq.question, "answer_index")


def test_b6_falls_back_to_earlier_miss_then_quiz_order():
    graph, quiz = sample_graph(), sample_quiz_key()
    g = to_nx(graph)
    answers = [
        _answer(quiz, "derivatives", True),
        _answer(quiz, "backpropagation", False),
        _answer(quiz, "chain_rule", False),  # its only prereq (derivatives) already answered
    ]
    nq = next_question(graph, quiz, answers)
    assert nq.target_concept_id in nx.ancestors(g, "backpropagation")

    fresh = next_question(graph, quiz, [_answer(quiz, "derivatives", True)])
    assert fresh.question.id == next(q.id for q in quiz.questions if q.concept_id != "derivatives")


def test_b6_all_answered_returns_no_question():
    graph, quiz = sample_graph(), sample_quiz_key()
    answers = [_answer(quiz, q.concept_id, True) for q in quiz.questions]
    nq = next_question(graph, quiz, answers)
    assert nq.question is None and nq.remaining == 0


def test_b6_fixture_matches_engine():
    graph, quiz = sample_graph(), sample_quiz_key()
    answers = [_answer(quiz, "derivatives", True), _answer(quiz, "backpropagation", False)]
    assert next_question(graph, quiz, answers) == sample_next_question()


def test_b6_endpoint(monkeypatch):
    monkeypatch.setattr(settings, "mock_extraction", True)
    client = TestClient(app)
    quiz = client.post("/api/quiz", json={"graph_id": "demo"}).json()
    key = sample_quiz_key()
    body = {"answers": [_answer(key, "backpropagation", False).model_dump()]}
    for mock in (False, True):
        monkeypatch.setattr(settings, "mock_learner", mock)
        r = client.post(f"/api/quiz/{quiz['quiz_id']}/next", json=body)
        assert r.status_code == 200
        data = r.json()
        assert data["question"]["concept_id"] and "answer_index" not in data["question"]
    assert client.post("/api/quiz/nope/next", json=body).status_code == 404
