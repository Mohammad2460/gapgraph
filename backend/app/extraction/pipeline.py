"""Document -> stream of graph events.  [Pillar A — task A4]

Yields (event_name, payload_dict) tuples; api/documents.py turns them into SSE.
Event names/payloads are defined in app/models.py (see SSE comment block).
"""

import asyncio
from collections.abc import AsyncIterator

from app.fixtures import sample_graph
from app.store import Document

Event = tuple[str, dict]


async def mock_stream(delay: float = 0.25) -> AsyncIterator[Event]:
    """Replays the fixture graph node-by-node. Used while MOCK_EXTRACTION=1."""
    graph = sample_graph()
    yield "status", {"message": "Reading chapter…", "progress": 0.0}
    sent: set[str] = set()
    for i, concept in enumerate(graph.concepts):
        await asyncio.sleep(delay)
        sent.add(concept.id)
        yield "concept", concept.model_dump()
        for edge in graph.edges:
            touches_new = concept.id in (edge.source, edge.target)
            if touches_new and edge.source in sent and edge.target in sent:
                yield "edge", edge.model_dump()
        progress = (i + 1) / len(graph.concepts)
        yield "status", {"message": f"Found {concept.name}", "progress": progress}
    yield "done", graph.model_dump()


async def build_graph_stream(doc: Document) -> AsyncIterator[Event]:
    """Real pipeline. TODO(A4):

    1. text = ingest.parser.to_text(doc.raw, doc.filename); chunks = ingest.chunker.chunk(text)
    2. For each chunk (run 2-3 concurrently with asyncio for speed):
         result = await extraction.concepts.extract_chunk(chunk, known)
         merge into graph via graph.builder.merge(...)  -> yield "concept"/"edge" for NEW items
         yield "status" with progress
    3. graph = graph.builder.finalize(...)  (dedupe, break cycles, importance)
    4. yield "done", graph.model_dump()   (graph.id = doc.doc_id, title = doc.title)
    On exception: yield "error", {"message": str(e)}.
    """
    raise NotImplementedError("A4: real extraction pipeline")
    yield  # pragma: no cover  (keeps this an async generator)
