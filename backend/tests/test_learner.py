"""Pillar B acceptance tests — the demo scenario from /fixtures.

Remove the xfail marker on a test once its task is done; `make test` must stay green.
"""

import pytest

from app.fixtures import sample_answers, sample_graph, sample_quiz_key
from app.learner.careless import classify_careless
from app.learner.gaps import find_root_gaps
from app.learner.mastery import bkt_update, estimate_mastery
from app.learner.path import suggest_next_topics
from app.learner.service import assess


@pytest.fixture
def demo():
    return sample_graph(), sample_quiz_key(), sample_answers()


@pytest.mark.xfail(reason="TODO B1", raises=NotImplementedError, strict=True)
def test_b1_bkt_and_mastery(demo):
    graph, quiz, answers = demo
    assert bkt_update(0.5, True) > 0.5 > bkt_update(0.5, False)
    m = estimate_mastery(graph, quiz.questions, answers)
    assert set(m) == {c.id for c in graph.concepts}
    assert m["derivatives"].status == "mastered"
    assert m["chain_rule"].status == "gap"
    assert m["vectors"].status == "untested"


@pytest.mark.xfail(reason="TODO B2", raises=NotImplementedError, strict=True)
def test_b2_root_gap_is_chain_rule(demo):
    graph, quiz, answers = demo
    m = estimate_mastery(graph, quiz.questions, answers)
    roots = find_root_gaps(graph, m)
    backprop = [r for r in roots if r.failed_concept_id == "backpropagation"]
    assert backprop and backprop[0].concept_id == "chain_rule"
    assert backprop[0].path[0] == "chain_rule" and backprop[0].path[-1] == "backpropagation"


@pytest.mark.xfail(reason="TODO B3", raises=NotImplementedError, strict=True)
def test_b3_gradient_descent_is_careless(demo):
    graph, quiz, answers = demo
    m = estimate_mastery(graph, quiz.questions, answers)
    careless = classify_careless(graph, quiz.questions, answers, m)
    assert careless == ["gradient_descent"]  # fast + confident + prereqs mastered
    assert m["chain_rule"].status == "gap"  # slow + unsure -> real gap


@pytest.mark.xfail(reason="TODO B4", raises=NotImplementedError, strict=True)
def test_b4_next_topics_start_with_root(demo):
    graph, quiz, answers = demo
    m = estimate_mastery(graph, quiz.questions, answers)
    careless = classify_careless(graph, quiz.questions, answers, m)
    topics = suggest_next_topics(graph, m, find_root_gaps(graph, m), careless)
    assert topics[0].concept_id == "chain_rule"


@pytest.mark.xfail(reason="TODO B5", raises=NotImplementedError, strict=True)
def test_b5_full_assessment(demo):
    graph, quiz, answers = demo
    result = assess(graph, quiz, answers)
    assert result.score.correct == 5 and result.score.total == 8
