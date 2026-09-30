# API Contract

Source of truth: `backend/app/models.py` (Pydantic) ↔ mirrored in `frontend/src/types.ts`.
Examples of every payload live in `/fixtures`. Change only via a `contract:` PR (see `CLAUDE.md`).

Base URL: `/api` (the Vite dev server proxies it to `http://localhost:8000`). Interactive docs: http://localhost:8000/docs

## Flow

```
POST /api/documents  ──► doc_id
GET  /api/documents/{doc_id}/stream   (SSE: status* concept* edge* … done)
POST /api/quiz  {graph_id = doc_id}  ──► Quiz (no answers)
POST /api/quiz/{quiz_id}/next {answers so far} ──► NextQuestion   (optional, B6 adaptive order)
POST /api/assess {quiz_id, answers}  ──► AssessmentResult
```

## Endpoints

### `POST /api/documents`  (multipart/form-data)
Fields: `file` (pdf/txt/md/code) **or** `text`, optional `title`.
→ `DocumentCreated { doc_id, title }`

### `GET /api/documents/{doc_id}/stream`  (Server-Sent Events)
| event | data |
|---|---|
| `status` | `{ message: string, progress: 0..1 }` |
| `concept` | `Concept` |
| `edge` | `Edge`, sent only after both endpoints were sent as concepts |
| `done` | `Graph`, the final merged graph. The client replaces its state with it |
| `error` | `{ message }` |

### `GET /api/graphs/{graph_id}` → `Graph`  (`demo` always returns the fixture)

### `POST /api/quiz`  `{ graph_id, num_questions: 5..10 = 8 }` → `Quiz`
Answers (`answer_index`, `explanation`) stay on the server until `/assess`.

### `POST /api/quiz/{quiz_id}/next`  `{ answers: Answer[] }` → `NextQuestion`  (B6, optional)
Adaptive order over the same quiz: after a miss, returns the unanswered question on the failed
concept's weakest prerequisite; otherwise the next question in quiz order. `question` is `null`
when all are answered. Mock mode (`MOCK_LEARNER=true`) returns `fixtures/sample_next_question.json`.

### `POST /api/assess`  `{ quiz_id, answers: Answer[], learner_id?: string }` → `AssessmentResult`

Optional `learner_id` (B7): repeat attempts by the same learner on the same graph share evidence for untested concepts. Omit it for a stateless assessment.

## Types

```ts
Concept  { id: snake_case, name, definition, source_excerpt, importance: 0..1, cluster: string|null }
Edge     { source: prereq_id, target: dependent_id, relation: "prerequisite", confidence: 0..1, evidence }
Graph    { id, title, concepts: Concept[], edges: Edge[] }
Question { id, concept_id, prompt, options: string[4], difficulty: "easy"|"medium"|"hard" }
Quiz     { quiz_id, graph_id, questions: Question[] }
Answer   { question_id, choice_index, confidence: 0..1, time_ms: number|null }
NextQuestion { question: Question|null, target_concept_id: string|null, reason, remaining }

MasteryStatus = "mastered" | "shaky" | "gap" | "careless" | "untested"
ConceptMastery { concept_id, p_known: 0..1, status, evidence_count }
RootGap        { concept_id (root), failed_concept_id, path: [root … failed], explanation }
NextTopic      { concept_id, order, reason }
AssessmentResult {
  quiz_id, graph_id, score: { correct, total },
  mastery: ConceptMastery[]   // exactly one per concept in the graph
  root_gaps: RootGap[], careless_slips: concept_id[], next_topics: NextTopic[],
  per_question: { question_id, correct, correct_index, explanation }[]
}
```

## Demo scenario encoded in the fixtures

Chapter: *How Neural Networks Learn* (13 concepts). The learner in `sample_answers.json`:
- misses **Chain Rule** slowly with low confidence, which is a **real gap**
- misses **Backpropagation**, whose **root gap is Chain Rule** (path `chain_rule → backpropagation`)
- misses **Gradient Descent** fast (2.5 s) with high confidence while its prereqs are mastered, which is a **careless slip**

`backend/tests/test_learner.py` asserts exactly this. Pillar B is done when those tests pass.
