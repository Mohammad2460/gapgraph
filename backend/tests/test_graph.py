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
