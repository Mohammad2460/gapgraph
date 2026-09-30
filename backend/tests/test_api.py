"""End-to-end API flow in mock mode (upload -> stream -> quiz -> assess)."""

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_mock_flow(monkeypatch):
    monkeypatch.setattr(settings, "mock_extraction", True)
    monkeypatch.setattr(settings, "mock_learner", True)

    doc = client.post("/api/documents", data={"text": "hello", "title": "T"}).json()
    with client.stream("GET", f"/api/documents/{doc['doc_id']}/stream") as r:
        body = "".join(r.iter_text())
    assert "event: done" in body

    quiz = client.post("/api/quiz", json={"graph_id": doc["doc_id"], "num_questions": 8}).json()
    assert "answer_index" not in quiz["questions"][0]

    answers = [{"question_id": q["id"], "choice_index": 0} for q in quiz["questions"]]
    result = client.post("/api/assess", json={"quiz_id": quiz["quiz_id"], "answers": answers})
    assert result.status_code == 200
    assert result.json()["root_gaps"]
