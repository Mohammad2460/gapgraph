# GapGraph

**Live Knowledge Graph Builder & Learning Gap Locator.** Track 2 (Smart Education), problem 2.1.

> Scores tell you *what* you got wrong. GapGraph tells you *why*, and what to fix first.

Upload a chapter (PDF, notes, or code). Claude extracts the concepts and their prerequisites
into a live, interactive graph. Take a 5–10 question quiz and GapGraph will:

- light up weak concepts on the graph
- trace each failure back through prerequisites to its **root-cause gap**
- separate **careless slips** from **real gaps** (confidence, response time, prerequisite mastery)
- suggest **what to study next**, in dependency order, grounded in quotes from your own material

## Quick start

```bash
cp .env.example .env              # add ANTHROPIC_API_KEY (optional in mock mode)
make setup
make dev-backend                  # terminal 1 → http://localhost:8000/docs
make dev-frontend                 # terminal 2 → http://localhost:5173
```

Everything runs in **mock mode** by default (fixture data, no API key needed). Flip
`MOCK_EXTRACTION`, `MOCK_LEARNER` (`.env`) and `VITE_USE_MOCK` (`frontend/.env.local`) to
`false` as the real pieces land.

## Stack

Claude API (structured outputs) · FastAPI · NetworkX · React + Vite + Tailwind · react-force-graph (D3)

## Team docs

- `TASKS.md`: the task board, split by pillar with milestones
- `CLAUDE.md`: architecture, file ownership, workflow rules
- `docs/CONTRACT.md`: API contract between pillars
