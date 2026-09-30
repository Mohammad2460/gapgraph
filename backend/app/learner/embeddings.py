"""Graph embeddings + mastery over time.  [Pillar B — task B7, stretch]

Spectral node embeddings (numpy only): concepts close in the prerequisite graph get
similar vectors. After each assessment, UNTESTED concepts borrow evidence from
(a) their own score in earlier attempts on the same graph and (b) similar concepts
tested now. Tested concepts, statuses and root gaps are never changed.
"""

import networkx as nx
import numpy as np

from app.graph.algorithms import to_nx
from app.models import AssessmentResult, ConceptMastery, Graph

DIM = 4  # spectral dimensions (capped by graph size)
SIM_MIN = 0.3  # ignore weakly similar concepts
TOP_K = 3  # similar tested concepts to borrow from
HISTORY_WEIGHT = 2.0  # weight of the latest past observation
DECAY = 0.7  # per-attempt decay of older observations
MAX_HISTORY = 10

Snapshot = dict[str, float]  # concept_id -> p_known, tested concepts only

_HISTORY: dict[str, list[Snapshot]] = {}  # graph_id -> snapshots, oldest first (in-memory)


def spectral_embeddings(graph: Graph, dim: int = DIM) -> dict[str, np.ndarray]:
    """Unit vectors from the smallest non-trivial eigenvectors of the normalized Laplacian."""
    g = to_nx(graph).to_undirected()
    ids = sorted(g.nodes)
    if len(ids) < 3:
        return {cid: np.eye(max(len(ids), 1))[i] for i, cid in enumerate(ids)}
    adj = nx.to_numpy_array(g, nodelist=ids)
    d_inv_sqrt = 1 / np.sqrt(np.maximum(adj.sum(axis=1), 1e-9))
    lap = np.eye(len(ids)) - d_inv_sqrt[:, None] * adj * d_inv_sqrt[None, :]
    _, vecs = np.linalg.eigh(lap)
    k = min(dim, len(ids) - 1)
    emb = vecs[:, 1 : 1 + k]
    emb = emb * np.sign(emb[np.argmax(np.abs(emb), axis=0), range(k)])  # deterministic signs
    emb = emb / np.maximum(np.linalg.norm(emb, axis=1, keepdims=True), 1e-9)
    return {cid: emb[i] for i, cid in enumerate(ids)}


def similarity(emb: dict[str, np.ndarray], a: str, b: str) -> float:
    return float(emb[a] @ emb[b])


def snapshot(mastery: dict[str, ConceptMastery]) -> Snapshot:
    return {cid: m.p_known for cid, m in mastery.items() if m.evidence_count > 0}


def refine(
    graph: Graph, mastery: dict[str, ConceptMastery], history: list[Snapshot]
) -> dict[str, ConceptMastery]:
    """Blend each untested concept's p_known with past attempts and similar tested concepts."""
    emb = spectral_embeddings(graph)
    tested = [cid for cid, m in mastery.items() if m.evidence_count > 0 and cid in emb]
    out = dict(mastery)
    for cid, m in mastery.items():
        if m.evidence_count > 0 or cid not in emb:
            continue
        num, den = m.p_known, 1.0
        for age, snap in enumerate(reversed(history)):
            if cid in snap:
                w = HISTORY_WEIGHT * DECAY**age
                num, den = num + w * snap[cid], den + w
                break
        sims = sorted(((similarity(emb, cid, t), t) for t in tested), reverse=True)
        for s, t in sims[:TOP_K]:
            if s >= SIM_MIN:
                num, den = num + s * mastery[t].p_known, den + s
        out[cid] = m.model_copy(update={"p_known": round(min(max(num / den, 0.01), 0.99), 3)})
    return out


def apply_history(graph: Graph, result: AssessmentResult) -> AssessmentResult:
    """Refine an assessment with this graph's history, then record this attempt."""
    mastery = {m.concept_id: m for m in result.mastery}
    past = _HISTORY.setdefault(graph.id, [])
    refined = refine(graph, mastery, past)
    past.append(snapshot(mastery))
    del past[:-MAX_HISTORY]
    return result.model_copy(update={"mastery": [refined[m.concept_id] for m in result.mastery]})
