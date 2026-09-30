"""Pillar A acceptance tests. Remove the xfail marker once each task is done."""

import asyncio

from app.extraction import concepts as concepts_mod
from app.extraction import pipeline as pipeline_mod
from app.fixtures import sample_chapter
from app.graph.builder import GraphBuilder
from app.ingest.chunker import chunk
from app.ingest.parser import to_text
from app.models import Concept, Edge, ExtractionResult
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
