"""Pillar A acceptance tests. Remove the xfail marker once each task is done."""

import asyncio

import pytest

from app.extraction import concepts as concepts_mod
from app.fixtures import sample_chapter
from app.graph.builder import GraphBuilder
from app.ingest.chunker import chunk
from app.ingest.parser import to_text
from app.models import Concept, Edge, ExtractionResult


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


@pytest.mark.xfail(reason="TODO A3", raises=NotImplementedError, strict=True)
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
