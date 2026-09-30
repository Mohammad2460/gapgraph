"""Document -> stream of graph events.  [Pillar A — task A4]

Yields (event_name, payload_dict) tuples; api/documents.py turns them into SSE.
Event names/payloads are defined in app/models.py (see SSE comment block).
"""

import asyncio
from collections.abc import AsyncIterator

from app.extraction.concepts import extract_chunk
from app.fixtures import sample_graph
from app.graph.builder import GraphBuilder
from app.ingest.chunker import chunk
from app.ingest.parser import to_text
from app.models import ExtractionResult
from app.store import Document

Event = tuple[str, dict]
CONCURRENCY = 3


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
    """Real pipeline: parse -> chunk -> extract (CONCURRENCY at a time) -> merge -> done.

    New concepts/edges stream as each chunk finishes. A failed chunk is reported
    in a status event and skipped; only if nothing at all is extracted do we error.
    """
    try:
        chunks = chunk(to_text(doc.raw, doc.filename))
    except Exception as e:
        yield "error", {"message": f"Could not read the document: {e}"}
        return
    if not chunks:
        yield "error", {"message": "No readable text found in the document."}
        return

    builder = GraphBuilder(doc.doc_id, doc.title)
    sem = asyncio.Semaphore(CONCURRENCY)

    async def run(i: int, text: str) -> tuple[int, ExtractionResult | Exception]:
        async with sem:
            try:
                return i, await extract_chunk(text, list(builder.concepts.values()))
            except Exception as e:  # keep going: one bad chunk shouldn't kill the demo
                return i, e

    n = len(chunks)
    yield "status", {"message": f"Reading {n} section{'s' if n > 1 else ''}…", "progress": 0.0}
    tasks = [asyncio.create_task(run(i, c)) for i, c in enumerate(chunks)]
    last_error: Exception | None = None
    try:
        for done_count, next_done in enumerate(asyncio.as_completed(tasks), start=1):
            i, result = await next_done
            progress = done_count / n
            if isinstance(result, Exception):
                last_error = result
                msg = f"Skipped section {i + 1}: {result}"
                yield "status", {"message": msg, "progress": progress}
                continue
            new_concepts, new_edges = builder.merge(result)
            for c in new_concepts:
                yield "concept", c.model_dump()
            for e in new_edges:
                yield "edge", e.model_dump()
            msg = f"Section {done_count}/{n}: {len(builder.concepts)} concepts"
            yield "status", {"message": msg, "progress": progress}
    finally:
        for t in tasks:
            t.cancel()

    if not builder.concepts:
        reason = f": {last_error}" if last_error else ""
        yield "error", {"message": f"No concepts could be extracted{reason}"}
        return
    yield "done", builder.finalize().model_dump()
