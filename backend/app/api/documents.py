"""Upload + live graph stream.  [Pillar A]"""

import json
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.extraction import cache
from app.extraction.pipeline import build_graph_stream, mock_stream
from app.fixtures import sample_chapter, sample_graph
from app.models import DocumentCreated, Graph
from app.store import Document, store

router = APIRouter()


@router.post("/documents", response_model=DocumentCreated)
async def create_document(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    title: str | None = Form(None),
) -> DocumentCreated:
    if file is None and not text:
        raise HTTPException(400, "Send a file or text")
    raw = await file.read() if file else text.encode()
    if raw.strip() == b"demo":  # frontend "Use demo chapter" button -> the real sample chapter
        raw = sample_chapter().encode()
    filename = file.filename if file else None
    doc = Document(
        doc_id=uuid.uuid4().hex[:8],
        title=title or filename or "Untitled chapter",
        filename=filename,
        raw=raw,
    )
    store.documents[doc.doc_id] = doc
    return DocumentCreated(doc_id=doc.doc_id, title=doc.title)


@router.get("/documents/{doc_id}/stream")
async def stream_document(doc_id: str) -> EventSourceResponse:
    doc = store.documents.get(doc_id)
    if doc is None:
        raise HTTPException(404, "Unknown document")

    async def events():
        cached = None if settings.mock_extraction else cache.load_graph(doc.raw)
        if settings.mock_extraction:
            source = mock_stream()
        elif cached is not None:  # demo safety: same upload seen before -> replay, no API call
            source = mock_stream(delay=0.12, graph=cached)
        else:
            source = build_graph_stream(doc)
        try:
            async for name, payload in source:
                if name == "done":
                    graph = Graph.model_validate(payload)
                    if not settings.mock_extraction and cached is None:
                        cache.save(doc.raw, graph)
                    graph.id, graph.title = doc.doc_id, doc.title
                    store.graphs[doc.doc_id] = graph
                    payload = graph.model_dump()
                yield {"event": name, "data": json.dumps(payload)}
        except Exception as e:  # surface pipeline errors to the UI instead of a dead stream
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

    return EventSourceResponse(events())


@router.get("/graphs/{graph_id}", response_model=Graph)
async def get_graph(graph_id: str) -> Graph:
    if graph_id == "demo":
        return sample_graph()
    graph = store.graphs.get(graph_id)
    if graph is None:
        raise HTTPException(404, "Unknown graph")
    return graph
