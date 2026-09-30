"""Demo safety: cache real graphs/quizzes by upload content, replay if seen again.  [Pillar A — A7]

Every successful real run is saved to fixtures/demo/cache/<sha>.{graph,quiz}.json.
Uploading the same file again replays it instantly — no API call, works offline.
"""

import hashlib
from pathlib import Path

from app.config import FIXTURES_DIR
from app.models import Graph, QuizKey

CACHE_DIR: Path = FIXTURES_DIR / "demo" / "cache"


def _path(raw: bytes, kind: str) -> Path:
    return CACHE_DIR / f"{hashlib.sha256(raw).hexdigest()[:16]}.{kind}.json"


def load_graph(raw: bytes) -> Graph | None:
    p = _path(raw, "graph")
    return Graph.model_validate_json(p.read_text()) if p.exists() else None


def load_quiz(raw: bytes) -> QuizKey | None:
    p = _path(raw, "quiz")
    return QuizKey.model_validate_json(p.read_text()) if p.exists() else None


def save(raw: bytes, item: Graph | QuizKey) -> None:
    p = _path(raw, "graph" if isinstance(item, Graph) else "quiz")
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(item.model_dump_json(indent=2))
    except OSError:
        pass  # caching is best-effort; never break the demo over it
