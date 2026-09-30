"""Pillar A acceptance tests. Remove the xfail marker once each task is done."""

import asyncio

import networkx as nx

from app.api import quiz as quiz_api
from app.extraction import cache as cache_mod
from app.extraction import concepts as concepts_mod
from app.extraction import pipeline as pipeline_mod
from app.extraction import quiz_gen as quiz_mod
from app.fixtures import sample_chapter, sample_graph
from app.graph.algorithms import to_nx
from app.graph.builder import GraphBuilder
from app.ingest.chunker import chunk
from app.ingest.parser import to_text
from app.models import Concept, Edge, ExtractionResult, QuestionKey, QuizKey
from app.store import Document


def test_a1_parse_and_chunk():
    text = to_text(sample_chapter().encode(), "chapter.txt")
    chunks = chunk(text, max_chars=1500)
    assert 2 <= len(chunks) <= 6
    assert all(len(c) <= 1500 for c in chunks)


def test_a2_extract_chunk_sends_known_ids_and_returns_result(monkeypatch):
    calls = {}
    result = ExtractionResult(concepts=[Concept(id="x", name="X", definition="x")], edges=[])

    async def fake_structured(system, user, schema, **kw):
        calls.update(system=system, user=user, schema=schema)
        return result

    monkeypatch.setattr(concepts_mod.llm, "structured", fake_structured)
    known = [Concept(id="chain_rule", name="Chain Rule", definition="d")]
    out = asyncio.run(concepts_mod.extract_chunk("Backprop uses the chain rule.", known))

    assert out is result
    assert calls["schema"] is ExtractionResult
    assert "chain_rule: Chain Rule" in calls["user"]
    assert "Backprop uses the chain rule." in calls["user"]


def test_a3_merge_dedupes_and_blocks_cycles():
    b = GraphBuilder("g", "T")
    c = lambda i, n: Concept(id=i, name=n, definition=n)  # noqa: E731
    b.merge(
        ExtractionResult(concepts=[c("a", "A"), c("b", "B")], edges=[Edge(source="a", target="b")])
    )
    new_c, new_e = b.merge(
        ExtractionResult(concepts=[c("b", "B"), c("c", "C")], edges=[Edge(source="b", target="a")])
    )
    assert [x.id for x in new_c] == ["c"]  # "b" already known
    assert new_e == []  # b -> a would create a cycle
    assert len(b.finalize().concepts) == 3


def test_a3_normalizes_ids_and_merges_near_duplicates():
    b = GraphBuilder("g", "T")
    b.merge(
        ExtractionResult(
            concepts=[Concept(id="Chain Rule", name="Chain Rule", definition="short")],
            edges=[],
        )
    )
    new_c, new_e = b.merge(
        ExtractionResult(
            concepts=[
                Concept(id="chain_rules", name="The chain rules", definition="a longer definition"),
                Concept(id="Derivatives", name="Derivatives", definition="d"),
            ],
            edges=[
                Edge(source="derivative", target="chain-rule"),
                Edge(source="chain_rule", target="chain_rule"),  # self-loop
                Edge(source="ghost", target="chain_rule"),  # unknown endpoint
            ],
        )
    )
    assert [c.id for c in new_c] == ["derivatives"]
    assert [(e.source, e.target) for e in new_e] == [("derivatives", "chain_rule")]
    g = b.finalize()
    assert sorted(c.id for c in g.concepts) == ["chain_rule", "derivatives"]
    assert next(c for c in g.concepts if c.id == "chain_rule").definition == "a longer definition"


def test_a3_finalize_scores_flat_importance_and_caps_nodes():
    b = GraphBuilder("g", "T")
    cs = [Concept(id=f"c{i}", name=f"C{i}", definition="d") for i in range(45)]
    hub_edges = [Edge(source="c0", target=f"c{i}") for i in range(1, 10)]
    b.merge(ExtractionResult(concepts=cs, edges=hub_edges))
    g = b.finalize()
    assert len(g.concepts) == 40
    ids = {c.id for c in g.concepts}
    assert all(e.source in ids and e.target in ids for e in g.edges)
    imp = {c.id: c.importance for c in g.concepts}
    assert imp["c0"] == max(imp.values())
    assert all(0.0 <= v <= 1.0 for v in imp.values())


def _run_pipeline(raw: bytes, monkeypatch, fake_extract) -> list[tuple[str, dict]]:
    monkeypatch.setattr(pipeline_mod, "extract_chunk", fake_extract)
    doc = Document(doc_id="d1", title="Ch 1", filename="ch.txt", raw=raw)

    async def collect():
        return [ev async for ev in pipeline_mod.build_graph_stream(doc)]

    return asyncio.run(collect())


def test_a4_pipeline_streams_concepts_then_edges_then_done(monkeypatch):
    async def fake_extract(chunk, known):
        return ExtractionResult(
            concepts=[
                Concept(id="derivatives", name="Derivatives", definition="d"),
                Concept(id="chain_rule", name="Chain Rule", definition="c"),
            ],
            edges=[Edge(source="derivatives", target="chain_rule")],
        )

    events = _run_pipeline(sample_chapter().encode(), monkeypatch, fake_extract)
    names = [n for n, _ in events]
    assert names[0] == "status" and names[-1] == "done"
    sent: set[str] = set()
    for name, payload in events:
        if name == "concept":
            sent.add(payload["id"])
        if name == "edge":
            assert {payload["source"], payload["target"]} <= sent
    assert names.count("concept") == 2 and names.count("edge") == 1
    assert all(0 <= p["progress"] <= 1 for n, p in events if n == "status")
    done = events[-1][1]
    assert (done["id"], done["title"]) == ("d1", "Ch 1")
    assert len(done["concepts"]) == 2


def test_a4_pipeline_skips_failed_chunk_but_errors_when_nothing_extracted(monkeypatch):
    calls = {"n": 0}

    async def flaky(chunk, known):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return ExtractionResult(concepts=[Concept(id="x", name="X", definition="x")], edges=[])

    text = ("para one. " * 200 + "\n\n") * 3  # several chunks
    events = _run_pipeline(text.encode(), monkeypatch, flaky)
    assert events[-1][0] == "done"

    async def always_fail(chunk, known):
        raise RuntimeError("api down")

    events = _run_pipeline(text.encode(), monkeypatch, always_fail)
    assert events[-1][0] == "error" and "api down" in events[-1][1]["message"]

    events = _run_pipeline(b"   ", monkeypatch, always_fail)
    assert events[-1][0] == "error"


def test_a5_selects_advanced_nodes_with_prereq_chain_in_learning_order():
    graph = sample_graph()
    g = to_nx(graph)
    picked = quiz_mod.select_concepts(graph, 8)
    assert len(picked) == len(set(picked)) == 8
    most_advanced = max(g.nodes, key=lambda n: len(nx.ancestors(g, n)))
    assert most_advanced in picked
    assert set(g.predecessors(most_advanced)) & set(picked)
    pos = {c: i for i, c in enumerate(picked)}
    assert all(pos[u] < pos[v] for u, v in g.edges if u in pos and v in pos)


def test_a5_generate_quiz_validates_and_numbers_questions(monkeypatch):
    graph = sample_graph()
    seen = {}

    def q(cid, options=("a", "b", "c", "d"), answer=1):
        return QuestionKey(
            id="zz",
            concept_id=cid,
            prompt=f"about {cid}",
            options=list(options),
            answer_index=answer,
            explanation="e",
        )

    async def fake_structured(system, user, schema, **kw):
        seen["user"] = user
        picked = quiz_mod.select_concepts(graph, 5)
        bad = [q("ghost"), q(picked[0], options=("a", "b", "c")), q(picked[1], answer=7)]
        return schema(questions=[q(c) for c in picked] + bad + [q(picked[0])])

    monkeypatch.setattr(quiz_mod.llm, "structured", fake_structured)
    key = asyncio.run(quiz_mod.generate_quiz(graph, 5))
    assert key.graph_id == graph.id and key.quiz_id
    assert [x.id for x in key.questions] == ["q1", "q2", "q3", "q4", "q5"]
    assert len({x.concept_id for x in key.questions}) == 5
    assert all(len(x.options) == 4 and 0 <= x.answer_index < 4 for x in key.questions)
    names = {c.id: c.name for c in graph.concepts}
    assert all(names[x.concept_id] in seen["user"] for x in key.questions)


def _live_api(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from app.config import settings
    from app.main import app

    monkeypatch.setattr(settings, "mock_extraction", False)
    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    return TestClient(app)


def _stream_events(client, doc_id):
    text = client.get(f"/api/documents/{doc_id}/stream").text
    return [line.split(": ", 1)[1] for line in text.splitlines() if line.startswith("event")]


def test_a7_real_run_is_cached_then_replayed_without_llm(monkeypatch, tmp_path):
    client = _live_api(monkeypatch, tmp_path)

    async def fake_extract(chunk, known):
        return ExtractionResult(
            concepts=[
                Concept(id="a", name="A", definition="a"),
                Concept(id="b", name="B", definition="b"),
            ],
            edges=[Edge(source="a", target="b")],
        )

    async def fake_quiz(graph, n):
        q = QuestionKey(
            id="q1",
            concept_id="a",
            prompt="?",
            options=list("abcd"),
            answer_index=0,
            explanation="e",
        )
        return QuizKey(quiz_id="live1", graph_id=graph.id, questions=[q])

    monkeypatch.setattr(pipeline_mod, "extract_chunk", fake_extract)
    monkeypatch.setattr(quiz_api, "generate_quiz", fake_quiz)
    doc1 = client.post("/api/documents", data={"text": "same chapter", "title": "T"}).json()
    assert _stream_events(client, doc1["doc_id"])[-1] == "done"
    assert client.post("/api/quiz", json={"graph_id": doc1["doc_id"]}).status_code == 200

    async def boom(*a, **k):
        raise RuntimeError("API down")

    monkeypatch.setattr(pipeline_mod, "extract_chunk", boom)
    monkeypatch.setattr(quiz_api, "generate_quiz", boom)
    doc2 = client.post("/api/documents", data={"text": "same chapter", "title": "T2"}).json()
    events = _stream_events(client, doc2["doc_id"])
    assert events[-1] == "done" and events.count("concept") == 2 and "edge" in events
    graph = client.get(f"/api/graphs/{doc2['doc_id']}").json()
    assert graph["id"] == doc2["doc_id"] and len(graph["concepts"]) == 2
    quiz = client.post("/api/quiz", json={"graph_id": doc2["doc_id"]}).json()
    assert quiz["graph_id"] == doc2["doc_id"] and len(quiz["questions"]) == 1


def test_a7_quiz_failure_returns_clear_error(monkeypatch, tmp_path):
    client = _live_api(monkeypatch, tmp_path)

    async def fake_extract(chunk, known):
        return ExtractionResult(concepts=[Concept(id="a", name="A", definition="a")], edges=[])

    async def boom(*a, **k):
        raise RuntimeError("API down")

    monkeypatch.setattr(pipeline_mod, "extract_chunk", fake_extract)
    monkeypatch.setattr(quiz_api, "generate_quiz", boom)
    doc = client.post("/api/documents", data={"text": "other chapter"}).json()
    _stream_events(client, doc["doc_id"])
    r = client.post("/api/quiz", json={"graph_id": doc["doc_id"]})
    assert r.status_code == 502 and "API down" in r.json()["detail"]
