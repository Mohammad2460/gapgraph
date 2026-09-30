"""API CONTRACT — shared by every pillar.

Mirrored 1:1 in frontend/src/types.ts and documented in docs/CONTRACT.md.
Do NOT change a field without a "contract:" PR that updates all three files
and the fixtures in /fixtures. Adding an optional field is fine; renaming or
removing one breaks the other pillars.
"""

from typing import Literal

from pydantic import BaseModel, Field

MasteryStatus = Literal["mastered", "shaky", "gap", "careless", "untested"]
Difficulty = Literal["easy", "medium", "hard"]


# ---------- Knowledge graph (Pillar A produces, everyone consumes) ----------


class Concept(BaseModel):
    id: str = Field(description="snake_case slug, unique within a graph, e.g. 'chain_rule'")
    name: str = Field(description="Human-readable name, e.g. 'Chain Rule'")
    definition: str = Field(description="One-sentence definition")
    source_excerpt: str = Field("", description="Verbatim sentence from the source that grounds it")
    importance: float = Field(0.5, description="0..1, how central the concept is")
    cluster: str | None = Field(None, description="Topic group for colouring/layout")


class Edge(BaseModel):
    source: str = Field(description="Prerequisite concept id (learn this first)")
    target: str = Field(description="Dependent concept id")
    relation: Literal["prerequisite"] = "prerequisite"
    confidence: float = Field(0.8, description="0..1 confidence that the dependency is real")
    evidence: str = Field("", description="Source text that justifies the edge")


class Graph(BaseModel):
    id: str
    title: str
    concepts: list[Concept]
    edges: list[Edge]


class ExtractionResult(BaseModel):
    """What the LLM returns for one chunk (before merging into a Graph)."""

    concepts: list[Concept]
    edges: list[Edge]


class DocumentCreated(BaseModel):
    doc_id: str
    title: str


# SSE events on GET /api/documents/{doc_id}/stream  (event name -> data payload)
#   "status"  -> {"message": str, "progress": float 0..1}
#   "concept" -> Concept
#   "edge"    -> Edge            (only sent once both endpoints were sent)
#   "done"    -> Graph           (final merged graph; replaces client state)
#   "error"   -> {"message": str}


# ---------- Quiz (Pillar A generates) ----------


class Question(BaseModel):
    id: str
    concept_id: str
    prompt: str
    options: list[str] = Field(description="Exactly 4 options")
    difficulty: Difficulty = "medium"


class QuestionKey(Question):
    """Server-side only. Never send answer_index to the client before /assess."""

    answer_index: int
    explanation: str


class QuizKey(BaseModel):
    quiz_id: str
    graph_id: str
    questions: list[QuestionKey]


class QuizRequest(BaseModel):
    graph_id: str
    num_questions: int = Field(8, ge=5, le=10)


class Quiz(BaseModel):
    quiz_id: str
    graph_id: str
    questions: list[Question]


# ---------- Assessment (Pillar B computes) ----------


class Answer(BaseModel):
    question_id: str
    choice_index: int
    confidence: float = Field(0.5, ge=0, le=1, description="Learner self-rating 0..1")
    time_ms: int | None = None


class AssessRequest(BaseModel):
    quiz_id: str
    answers: list[Answer]


class ConceptMastery(BaseModel):
    concept_id: str
    p_known: float = Field(description="0..1 probability the learner knows it")
    status: MasteryStatus
    evidence_count: int = 0


class RootGap(BaseModel):
    concept_id: str = Field(description="The root-cause weak prerequisite")
    failed_concept_id: str = Field(description="The concept the learner visibly failed")
    path: list[str] = Field(description="Concept ids from root gap -> failed concept")
    explanation: str


class NextTopic(BaseModel):
    concept_id: str
    order: int
    reason: str


class Score(BaseModel):
    correct: int
    total: int


class QuestionResult(BaseModel):
    question_id: str
    correct: bool
    correct_index: int
    explanation: str


class AssessmentResult(BaseModel):
    quiz_id: str
    graph_id: str
    score: Score
    mastery: list[ConceptMastery] = Field(description="One entry per concept in the graph")
    root_gaps: list[RootGap]
    careless_slips: list[str] = Field(description="Concept ids judged careless, not real gaps")
    next_topics: list[NextTopic]
    per_question: list[QuestionResult]
