"""Merge per-chunk extractions into one clean DAG.  [Pillar A — task A3]"""

import re

import networkx as nx

from app.models import Concept, Edge, ExtractionResult, Graph

MAX_NODES = 40
_STOPWORDS = {"the", "a", "an", "of"}


def _slug(text: str) -> str:
    return "_".join(re.findall(r"[a-z0-9]+", text.lower()))


def _singular(word: str) -> str:
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def _key(text: str) -> str:
    """Dedupe key: slug with stopwords dropped and each word singularized."""
    return "_".join(_singular(w) for w in _slug(text).split("_") if w not in _STOPWORDS)


class GraphBuilder:
    def __init__(self, graph_id: str, title: str):
        self.graph_id = graph_id
        self.title = title
        self.concepts: dict[str, Concept] = {}
        self.edges: dict[tuple[str, str], Edge] = {}
        self._alias: dict[str, str] = {}  # dedupe key -> canonical id
        self._g = nx.DiGraph()

    def _resolve(self, raw: str) -> str | None:
        return self._alias.get(_key(raw))

    def merge(self, result: ExtractionResult) -> tuple[list[Concept], list[Edge]]:
        """Add a chunk's result; return only the NEW concepts/edges (for streaming)."""
        new_concepts: list[Concept] = []
        for c in result.concepts:
            existing = self._resolve(c.id) or self._resolve(c.name)
            if existing:
                self._absorb(self.concepts[existing], c)
                continue
            cid = _slug(c.id) or _slug(c.name)
            if not cid:
                continue
            concept = c.model_copy(update={"id": cid})
            self.concepts[cid] = concept
            self._alias[_key(cid)] = cid
            self._alias.setdefault(_key(c.name), cid)
            self._g.add_node(cid)
            new_concepts.append(concept)

        new_edges: list[Edge] = []
        for e in result.edges:
            src, tgt = self._resolve(e.source), self._resolve(e.target)
            if src is None or tgt is None or src == tgt or (src, tgt) in self.edges:
                continue
            if nx.has_path(self._g, tgt, src):  # would close a cycle
                continue
            edge = e.model_copy(update={"source": src, "target": tgt})
            self.edges[(src, tgt)] = edge
            self._g.add_edge(src, tgt)
            new_edges.append(edge)
        return new_concepts, new_edges

    @staticmethod
    def _absorb(kept: Concept, dup: Concept) -> None:
        if len(dup.definition) > len(kept.definition):
            kept.definition = dup.definition
        if not kept.source_excerpt:
            kept.source_excerpt = dup.source_excerpt
        if kept.cluster is None:
            kept.cluster = dup.cluster
        kept.importance = max(kept.importance, dup.importance)

    def finalize(self) -> Graph:
        """Score importance when the LLM gave flat values, cap to MAX_NODES, return Graph."""
        concepts = list(self.concepts.values())
        if len({c.importance for c in concepts}) <= 1 and concepts:
            degree = dict(self._g.degree())
            top = max(degree.values()) or 1
            for c in concepts:
                c.importance = round(0.3 + 0.7 * degree[c.id] / top, 3)
        concepts = sorted(concepts, key=lambda c: c.importance, reverse=True)[:MAX_NODES]
        keep = {c.id for c in concepts}
        return Graph(
            id=self.graph_id,
            title=self.title,
            concepts=concepts,
            edges=[e for e in self.edges.values() if e.source in keep and e.target in keep],
        )
