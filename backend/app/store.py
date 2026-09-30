"""In-memory store. Fine for a hackathon demo; lost on restart."""

from dataclasses import dataclass, field

from app.models import Graph, QuizKey


@dataclass
class Document:
    doc_id: str
    title: str
    filename: str | None
    raw: bytes


@dataclass
class Store:
    documents: dict[str, Document] = field(default_factory=dict)
    graphs: dict[str, Graph] = field(default_factory=dict)  # keyed by graph_id == doc_id
    quizzes: dict[str, QuizKey] = field(default_factory=dict)


store = Store()
