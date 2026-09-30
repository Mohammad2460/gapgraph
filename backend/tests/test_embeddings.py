"""B7 — graph embeddings + mastery history: similar concepts share evidence across attempts."""

import numpy as np
from fastapi.testclient import TestClient

from app.config import settings
from app.fixtures import sample_answers, sample_graph, sample_quiz_key
from app.learner import embeddings as emb
from app.learner.mastery import estimate_mastery
from app.main import app


def _demo_mastery(skip_concept: str | None = None):
    graph, quiz = sample_graph(), sample_quiz_key()
    skip = {q.id for q in quiz.questions if q.concept_id == skip_concept}
    answers = [a for a in sample_answers() if a.question_id not in skip]
    return graph, estimate_mastery(graph, quiz.questions, answers)


def test_b7_spectral_embeddings_put_neighbours_close():
    graph = sample_graph()
    e = emb.spectral_embeddings(graph)
    assert set(e) == {c.id for c in graph.concepts}
    assert all(np.isclose(np.linalg.norm(v), 1.0) for v in e.values())
    sim = emb.similarity
    assert sim(e, "chain_rule", "derivatives") > sim(e, "chain_rule", "vectors")
    assert sim(e, "chain_rule", "backpropagation") > sim(e, "chain_rule", "perceptron")
    again = emb.spectral_embeddings(graph)
    assert all(np.allclose(e[k], again[k]) for k in e)


def test_b7_untested_concepts_borrow_from_similar_tested_ones():
    graph, mastery = _demo_mastery()
    refined = emb.refine(graph, mastery, history=[])
    for cid, m in mastery.items():
        assert refined[cid].status == m.status
        if m.evidence_count:
            assert refined[cid] == m  # tested concepts untouched
    # functions' neighbours (derivatives, activation_function) are mastered
    assert refined["functions"].p_known > mastery["functions"].p_known


def test_b7_history_carries_evidence_to_next_attempt():
    graph, first = _demo_mastery()
    assert first["chain_rule"].status == "gap"
    _, second = _demo_mastery(skip_concept="chain_rule")
    assert second["chain_rule"].status == "untested"
    no_hist = emb.refine(graph, second, history=[])
    with_hist = emb.refine(graph, second, history=[emb.snapshot(first)])
    assert with_hist["chain_rule"].p_known < no_hist["chain_rule"].p_known
    assert with_hist["chain_rule"].status == "untested"


def test_b7_assess_endpoint_remembers_previous_attempt(monkeypatch):
    monkeypatch.setattr(settings, "mock_extraction", True)
    monkeypatch.setattr(settings, "mock_learner", False)
    monkeypatch.setattr(emb, "_HISTORY", {})
    client = TestClient(app)
    quiz = client.post("/api/quiz", json={"graph_id": "demo"}).json()
    answers = [a.model_dump() for a in sample_answers()]
    chain_q = next(q["id"] for q in quiz["questions"] if q["concept_id"] == "chain_rule")

    def p_chain(ans):
        r = client.post("/api/assess", json={"quiz_id": quiz["quiz_id"], "answers": ans}).json()
        return next(m for m in r["mastery"] if m["concept_id"] == "chain_rule")

    assert p_chain(answers)["status"] == "gap"
    later = p_chain([a for a in answers if a["question_id"] != chain_q])
    monkeypatch.setattr(emb, "_HISTORY", {})
    fresh = p_chain([a for a in answers if a["question_id"] != chain_q])
    assert later["status"] == fresh["status"] == "untested"
    assert later["p_known"] < fresh["p_known"]
