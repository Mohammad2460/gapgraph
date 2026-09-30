"""Pillar B acceptance tests — the demo scenario from /fixtures.

Remove the xfail marker on a test once its task is done; `make test` must stay green.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.assess import router as assess_router
from app.api.assess import settings, store
from app.fixtures import sample_answers, sample_graph, sample_quiz_key
from app.learner.careless import careless_score, classify_careless
from app.learner.gaps import find_root_gaps
from app.learner.mastery import bkt_update, estimate_mastery
from app.learner.path import suggest_next_topics
from app.learner.service import assess


@pytest.fixture
def demo():
    return sample_graph(), sample_quiz_key(), sample_answers()


def test_b1_bkt_and_mastery(demo):
    graph, quiz, answers = demo
    assert bkt_update(0.5, True) > 0.5 > bkt_update(0.5, False)
    m = estimate_mastery(graph, quiz.questions, answers)
    assert set(m) == {c.id for c in graph.concepts}
    assert m["derivatives"].status == "mastered"
    assert m["chain_rule"].status == "gap"
    assert m["vectors"].status == "untested"


def test_b2_root_gap_is_chain_rule(demo):
    graph, quiz, answers = demo
    m = estimate_mastery(graph, quiz.questions, answers)
    roots = find_root_gaps(graph, m)
    backprop = [r for r in roots if r.failed_concept_id == "backpropagation"]
    assert backprop and backprop[0].concept_id == "chain_rule"
    assert backprop[0].path[0] == "chain_rule" and backprop[0].path[-1] == "backpropagation"


def test_b2_traces_deepest_weak_ancestor(demo):
    graph, quiz, answers = demo
    concept_ids = ["derivatives", "chain_rule", "backpropagation", "gradient_descent"]
    graph = graph.model_copy(update={
        "concepts": [concept for concept in graph.concepts if concept.id in concept_ids],
        "edges": [
            graph.edges[0].model_copy(update={"source": source, "target": target})
            for source, target in zip(concept_ids, concept_ids[1:])
        ],
    })
    mastery = estimate_mastery(graph, quiz.questions, answers)
    for concept_id in concept_ids:
        mastery[concept_id] = mastery[concept_id].model_copy(update={
            "status": "mastered" if concept_id == "chain_rule" else "gap",
            "p_known": 0.9 if concept_id == "chain_rule" else 0.2,
        })

    roots = find_root_gaps(graph, mastery)
    by_failed = {root.failed_concept_id: root for root in roots}
    assert len(roots) == 3
    assert set(by_failed) == {"derivatives", "backpropagation", "gradient_descent"}
    assert all(root.concept_id == "derivatives" for root in roots)
    assert by_failed["derivatives"].path == ["derivatives"]
    assert by_failed["gradient_descent"].path == concept_ids
    explanation = by_failed["gradient_descent"].explanation
    assert all(concept.name in explanation for concept in graph.concepts)


def test_b2_keeps_upstream_root_when_path_has_shortcut(demo):
    graph, quiz, answers = demo
    concept_ids = ["derivatives", "chain_rule", "backpropagation", "gradient_descent"]
    edges = list(zip(concept_ids, concept_ids[1:])) + [("derivatives", "gradient_descent")]
    graph = graph.model_copy(update={
        "concepts": [concept for concept in graph.concepts if concept.id in concept_ids],
        "edges": [
            graph.edges[0].model_copy(update={"source": source, "target": target})
            for source, target in edges
        ],
    })
    mastery = estimate_mastery(graph, quiz.questions, answers)
    for concept_id in concept_ids:
        mastery[concept_id] = mastery[concept_id].model_copy(update={
            "status": "mastered" if concept_id == "chain_rule" else "gap",
            "p_known": 0.9 if concept_id == "chain_rule" else 0.2,
        })

    root = next(
        root for root in find_root_gaps(graph, mastery)
        if root.failed_concept_id == "gradient_descent"
    )
    assert root.concept_id == "derivatives"
    assert root.path == ["derivatives", "gradient_descent"]


@pytest.mark.parametrize(
    "prereq_status, p_known, expected_root",
    [
        ("shaky", 0.5, "chain_rule"),
        ("untested", 0.2, "chain_rule"),
        ("untested", 0.5, "backpropagation"),
        ("careless", 0.2, "backpropagation"),
    ],
)
def test_b2_uses_weak_prerequisites(demo, prereq_status, p_known, expected_root):
    graph, quiz, answers = demo
    graph = graph.model_copy(update={
        "concepts": [
            concept for concept in graph.concepts
            if concept.id in {"chain_rule", "backpropagation"}
        ],
        "edges": [graph.edges[0].model_copy(update={
            "source": "chain_rule", "target": "backpropagation",
        })],
    })
    mastery = estimate_mastery(graph, quiz.questions, answers)
    mastery["chain_rule"] = mastery["chain_rule"].model_copy(update={
        "status": prereq_status, "p_known": p_known,
    })

    roots = find_root_gaps(graph, mastery)
    assert len(roots) == 1
    assert roots[0].concept_id == expected_root
    assert roots[0].failed_concept_id == "backpropagation"
    assert roots[0].path == (
        ["chain_rule", "backpropagation"] if expected_root == "chain_rule"
        else ["backpropagation"]
    )
    assert roots[0].explanation


def test_b3_gradient_descent_is_careless(demo):
    graph, quiz, answers = demo
    m = estimate_mastery(graph, quiz.questions, answers)
    careless = classify_careless(graph, quiz.questions, answers, m)
    assert careless == ["gradient_descent"]  # fast + confident + prereqs mastered
    assert m["chain_rule"].status == "gap"  # slow + unsure -> real gap
    assert m["gradient_descent"].status == "careless"
    assert m["gradient_descent"].p_known >= 0.5
    assert m["gradient_descent"].evidence_count == 1
    roots = find_root_gaps(graph, m)
    assert all(root.failed_concept_id != "gradient_descent" for root in roots)
    assert next(
        root.concept_id for root in roots if root.failed_concept_id == "backpropagation"
    ) == "chain_rule"


def test_b3_score_uses_prerequisites_confidence_and_speed(demo):
    graph, quiz, answers = demo
    mastery = estimate_mastery(graph, quiz.questions, answers)
    question = next(q for q in quiz.questions if q.concept_id == "gradient_descent")
    answer = next(a for a in answers if a.question_id == question.id)
    prereqs = {edge.source for edge in graph.edges if edge.target == question.concept_id}
    for concept_id in prereqs:
        mastery[concept_id] = mastery[concept_id].model_copy(update={
            "p_known": 0.9, "status": "mastered",
        })
    baseline = careless_score(graph, question, answer, mastery, 10000)
    assert 0.6 <= baseline <= 1
    for changes in ({"confidence": 0.1}, {"time_ms": 20000}, {"time_ms": None}):
        score = careless_score(graph, question, answer.model_copy(update=changes), mastery, 10000)
        assert 0 <= score < baseline
    weak_mastery = dict(mastery)
    for concept_id in prereqs:
        weak_mastery[concept_id] = mastery[concept_id].model_copy(update={
            "p_known": 0.1, "status": "gap",
        })
    assert careless_score(graph, question, answer, weak_mastery, 10000) < 0.6
    correct = answer.model_copy(update={"choice_index": question.answer_index})
    assert careless_score(graph, question, correct, mastery, 10000) == 0


@pytest.mark.parametrize("other_correct", [True, False])
def test_b3_uses_other_answers_on_the_same_concept(demo, other_correct):
    graph, quiz, answers = demo
    question = next(q for q in quiz.questions if q.concept_id == "gradient_descent")
    answer = next(a for a in answers if a.question_id == question.id)
    repeat = question.model_copy(update={"id": "gd_repeat"})
    questions = quiz.questions + [repeat]
    answers = answers + [answer.model_copy(update={
        "question_id": repeat.id,
        "choice_index": question.answer_index if other_correct else answer.choice_index,
    })]
    mastery = estimate_mastery(graph, questions, answers)

    careless = classify_careless(graph, questions, answers, mastery)
    assert careless == (["gradient_descent"] if other_correct else [])
    assert mastery["gradient_descent"].status == ("careless" if other_correct else "gap")


def test_b3_classification_is_independent_of_answer_order(demo):
    graph, quiz, answers = demo
    forward = estimate_mastery(graph, quiz.questions, answers)
    backward = {concept_id: value.model_copy() for concept_id, value in forward.items()}
    assert classify_careless(graph, quiz.questions, answers, forward) == ["gradient_descent"]
    assert classify_careless(graph, quiz.questions, list(reversed(answers)), backward) == [
        "gradient_descent",
    ]
    assert forward == backward


def test_b3_empty_answers_leave_mastery_unchanged(demo):
    graph, quiz, _ = demo
    mastery = estimate_mastery(graph, quiz.questions, [])
    before = {concept_id: value.model_copy() for concept_id, value in mastery.items()}
    assert classify_careless(graph, quiz.questions, [], mastery) == []
    assert mastery == before


def test_b4_next_topics_start_with_root(demo):
    graph, quiz, answers = demo
    m = estimate_mastery(graph, quiz.questions, answers)
    careless = classify_careless(graph, quiz.questions, answers, m)
    topics = suggest_next_topics(graph, m, find_root_gaps(graph, m), careless)
    assert topics[0].concept_id == "chain_rule"


def test_b5_full_assessment(demo):
    graph, quiz, answers = demo
    result = assess(graph, quiz, answers)
    assert result.score.correct == 5 and result.score.total == 8
    assert result.quiz_id == quiz.quiz_id and result.graph_id == graph.id
    assert {entry.concept_id for entry in result.mastery} == {c.id for c in graph.concepts}
    assert len(result.mastery) == len(graph.concepts)
    assert len(result.per_question) == len(answers)
    root = next(r for r in result.root_gaps if r.failed_concept_id == "backpropagation")
    assert root.concept_id == "chain_rule"
    assert root.path == ["chain_rule", "backpropagation"]
    assert "Chain Rule" in root.explanation and "Backpropagation" in root.explanation
    assert result.careless_slips == ["gradient_descent"]
    assert [topic.concept_id for topic in result.next_topics] == [
        "chain_rule", "backpropagation", "gradient_descent",
    ]


def test_b5_duplicate_responses_count_once(demo):
    graph, quiz, answers = demo
    expected = assess(graph, quiz, answers)
    result = assess(graph, quiz, answers + [answers[0]])
    assert result == expected


def test_b5_uses_the_last_response_to_a_question(demo):
    graph, quiz, answers = demo
    question = next(q for q in quiz.questions if q.id == answers[0].question_id)
    latest = answers[0].model_copy(update={"choice_index": (question.answer_index + 1) % 4})
    expected = assess(graph, quiz, [latest] + answers[1:])
    result = assess(graph, quiz, answers + [latest])
    assert result == expected


@pytest.mark.parametrize("answer_mode", ["demo", "all_correct", "empty"])
def test_b5_real_api_uses_submitted_answers(demo, monkeypatch, answer_mode):
    graph, quiz, answers = demo
    graph = graph.model_copy(update={"id": "b5_graph"})
    quiz = quiz.model_copy(update={"quiz_id": "b5_quiz", "graph_id": graph.id})
    if answer_mode == "all_correct":
        by_id = {question.id: question for question in quiz.questions}
        answers = [
            answer.model_copy(update={"choice_index": by_id[answer.question_id].answer_index})
            for answer in answers
        ]
    elif answer_mode == "empty":
        answers = []
    monkeypatch.setattr(settings, "mock_learner", False)
    monkeypatch.setitem(store.graphs, graph.id, graph)
    monkeypatch.setitem(store.quizzes, quiz.quiz_id, quiz)
    app = FastAPI()
    app.include_router(assess_router, prefix="/api")
    with TestClient(app) as client:
        response = client.post("/api/assess", json={
            "quiz_id": quiz.quiz_id,
            "answers": [answer.model_dump() for answer in answers],
        })
    assert response.status_code == 200
    result = response.json()
    assert result == assess(graph, quiz, answers).model_dump(mode="json")
    assert result["score"] == {
        "correct": 5 if answer_mode == "demo" else len(answers), "total": len(answers),
    }
    if answer_mode == "demo":
        assert result["careless_slips"] == ["gradient_descent"]
        assert result["next_topics"][0]["concept_id"] == "chain_rule"
    else:
        assert result["root_gaps"] == [] and result["careless_slips"] == []


def test_b4_path_orders_root_first_and_careless_last(demo):
    graph, quiz, answers = demo
    m = estimate_mastery(graph, quiz.questions, answers)
    topics = suggest_next_topics(graph, m, find_root_gaps(graph, m), ["gradient_descent"])
    assert [t.concept_id for t in topics] == ["chain_rule", "backpropagation", "gradient_descent"]
    assert [t.order for t in topics] == [1, 2, 3]
    assert topics[0].reason.startswith("Root gap") and "Backpropagation" in topics[0].reason
    assert "Chain Rule" in topics[1].reason
    assert topics[-1].reason == "Quick re-check only"


def test_b4_no_gaps_suggests_ready_to_learn(demo):
    graph, quiz, answers = demo
    m = estimate_mastery(graph, quiz.questions, answers)
    for cm in m.values():
        if cm.status != "untested":
            cm.status = "mastered"
    topics = suggest_next_topics(graph, m, [], [])
    assert topics and all(t.reason == "Ready to learn" for t in topics)
    prereqs = {c.id: [e.source for e in graph.edges if e.target == c.id] for c in graph.concepts}
    for t in topics:
        assert m[t.concept_id].status == "untested"
        assert all(m[p].status == "mastered" for p in prereqs[t.concept_id])
