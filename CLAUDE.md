# GapGraph — Live Knowledge Graph Builder & Learning Gap Locator

10-hour hackathon project (Track 2: Smart Education, problem 2.1). Upload a chapter
(PDF/text/code) → Claude extracts concepts + prerequisites → live interactive graph →
learner takes a 5–10 question quiz → weak concepts light up, the **root-cause gap** is
traced back through prerequisites, **careless slips are separated from real gaps**, and
next topics are suggested in order.

Task board: `TASKS.md`. API contract: `docs/CONTRACT.md`.

## Commands

```bash
make setup          # uv sync (backend) + npm install (frontend)
make dev-backend    # FastAPI on :8000  (uvicorn --reload)
make dev-frontend   # Vite on :5173, proxies /api -> :8000
make test           # backend pytest
make check          # lint + tests + frontend typecheck/build — run before every push
```

Single backend test: `cd backend && uv run pytest tests/test_learner.py::test_b2_root_gap_is_chain_rule -q`

## Architecture

```
frontend (React + Vite + Tailwind + react-force-graph-2d)
   │  /api/*  (Vite proxy)
backend (FastAPI)
   ├─ api/documents.py   POST /documents, GET /documents/{id}/stream (SSE), GET /graphs/{id}
   ├─ api/quiz.py        POST /quiz
   ├─ api/assess.py      POST /assess
   ├─ ingest/            bytes -> text -> chunks
   ├─ extraction/        Claude calls (llm.py = structured outputs), prompts, pipeline, quiz_gen
   ├─ graph/             NetworkX: builder (merge/dedupe/DAG), algorithms (shared helpers)
   └─ learner/           BKT mastery, careless-vs-gap, root-gap tracing, next topics
fixtures/                shared demo data (graph, quiz key, answers, expected assessment)
```

- Edge direction is always **prerequisite → dependent** (`source` must be learned before `target`).
- State is in-memory (`app/store.py`). Graph id == doc id. `"demo"` graph id always serves the fixture.
- Claude access: `app/extraction/llm.py::structured()` — returns a validated Pydantic model via
  `client.messages.parse(output_format=...)`. Model `claude-opus-5-5` (env `CLAUDE_MODEL`),
  speed/quality via `CLAUDE_EFFORT` (low|medium|high). Always go through this helper.

## Mock switches (why nobody is ever blocked)

| Flag | Where | Effect |
|---|---|---|
| `MOCK_EXTRACTION=true` | `.env` | `/documents` stream + `/quiz` replay fixtures (Pillar A not needed) |
| `MOCK_LEARNER=true` | `.env` | `/assess` returns `fixtures/sample_assessment.json` (Pillar B not needed) |
| `VITE_USE_MOCK=true` | `frontend/.env.local` | Frontend runs fully offline from fixtures (backend not needed) |

Each pillar flips **its own** flag to `false` once its real implementation passes its tests.

## Pillars & file ownership — ONLY edit files in your pillar

| Pillar | Owns | Tests |
|---|---|---|
| **A — AI & Graph** | `backend/app/ingest/`, `backend/app/extraction/`, `backend/app/graph/`, `backend/app/api/documents.py`, `backend/app/api/quiz.py` | `tests/test_graph.py` |
| **B — Learner Engine** | `backend/app/learner/`, `backend/app/api/assess.py` | `tests/test_learner.py` |
| **C — Frontend** | `frontend/src/**` (except `types.ts`) | `npm run build` |
| **Shared (contract)** | `backend/app/models.py`, `frontend/src/types.ts`, `docs/CONTRACT.md`, `fixtures/*`, `pyproject.toml`, `package.json` | `tests/test_contract.py` |

Rules:
1. **Contract files change only in a PR titled `contract: …`** that updates `models.py` + `types.ts` +
   `CONTRACT.md` + fixtures together, and is announced in team chat. Adding an *optional* field is safe;
   renaming/removing is not.
2. Pillar B may **add** functions to `backend/app/graph/algorithms.py`, never change existing ones.
3. Dependencies are pre-installed. Need a new one? Ask in chat; one person adds it.
4. `backend/app/main.py`, `config.py`, `store.py` should not need changes — ask first.
5. When a task's code is done, remove its `@pytest.mark.xfail` marker in the tests; `make check` must pass.

## Git workflow

- Branch per task: `a/A2-extract`, `b/B2-root-gap`, `c/C5-results`. Keep branches < 1 hour old.
- `git pull --rebase origin main` before pushing. Merge (squash) to `main` as soon as `make check` passes.
- Never force-push `main`. Never commit `.env`.

## Conventions

- Python 3.11+, type hints, Pydantic v2 models from `app/models.py` (don't define parallel dicts).
- Ruff (E, F, I, UP), line length 100. TS strict, no `enum` (erasableSyntaxOnly), Tailwind for styling.
- Keep Claude output grounded: every concept carries `source_excerpt`, every edge `evidence`.
- Demo safety: anything slow must stream progress; anything that can fail must show an error in the UI.
