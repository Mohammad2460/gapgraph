"""Fixtures must always satisfy the contract. Run after ANY contract change."""

import networkx as nx

from app.fixtures import sample_answers, sample_assessment, sample_graph, sample_quiz_key
from app.graph.algorithms import to_nx


def test_fixtures_validate():
    graph = sample_graph()
    quiz = sample_quiz_key()
    result = sample_assessment()
    ids = {c.id for c in graph.concepts}

    assert all(e.source in ids and e.target in ids for e in graph.edges)
    assert nx.is_directed_acyclic_graph(to_nx(graph))
    assert 5 <= len(quiz.questions) <= 10
    assert all(q.concept_id in ids and len(q.options) == 4 for q in quiz.questions)
    assert {m.concept_id for m in result.mastery} == ids
    assert len(sample_answers()) == len(quiz.questions)
