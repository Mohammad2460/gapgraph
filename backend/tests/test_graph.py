"""Pillar A acceptance tests. Remove the xfail marker once each task is done."""

import pytest

from app.fixtures import sample_chapter
from app.graph.builder import GraphBuilder
from app.ingest.chunker import chunk
from app.ingest.parser import to_text
from app.models import Concept, Edge, ExtractionResult


@pytest.mark.xfail(reason="TODO A1", raises=NotImplementedError, strict=True)
def test_a1_parse_and_chunk():
    text = to_text(sample_chapter().encode(), "chapter.txt")
    chunks = chunk(text, max_chars=1500)
    assert 2 <= len(chunks) <= 6
    assert all(len(c) <= 1500 for c in chunks)


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
