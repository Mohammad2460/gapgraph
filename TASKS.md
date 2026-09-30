# GapGraph — Task Board (10 hours)

H0 = hackathon start. Tick boxes as you merge. Ownership rules: see `CLAUDE.md`.

## Team split

| Team size | Member 1 | Member 2 | Member 3 | Member 4 | Member 5 |
|---|---|---|---|---|---|
| **2** | Pillar A (AI & Graph) | Pillar B (Learner) + Pillar C polish | — | — | — |
| **3** | Pillar A | Pillar B | Pillar C | — | — |
| **4** | Pillar A | Pillar B | Pillar C | Demo data, PPT, demo script, QA, stretch goals |
| **5** | Pillar A | Pillar B | Pillar C | Pillar D (demo & pitch) | **Pillar E (beginner)** |

The frontend is already functional in mock mode, so Pillar C is mostly polish + integration.
With 2 people, Member 2 does B1–B5 first (the differentiator), then C tasks.

## Milestones

| When | Milestone | Proof |
|---|---|---|
| **H0.5** | M0 — everyone runs the mock demo end to end | `make dev-frontend` → "Use demo chapter" → quiz → red path |
| **H4.5** | M1 — real PDF → real graph streaming in the UI | `MOCK_EXTRACTION=false`, `VITE_USE_MOCK=false` |
| **H6.5** | M2 — full real flow: upload → graph → quiz → real gaps | `MOCK_LEARNER=false`, all tests green |
| **H8** | M3 — **feature freeze**. Bug fixes and demo polish only | |
| **H9** | M4 — demo rehearsed twice, fallback cache ready, PPT final | |
| **H10** | Submit | |

---

## S — Setup (everyone, H0–H0.5)

- [ ] **S1** Clone, `make setup`, `cp .env.example .env`, add `ANTHROPIC_API_KEY`
- [ ] **S2** `make dev-backend` + `make dev-frontend`; open http://localhost:5173; run the demo in mock mode
- [ ] **S3** Pick a real demo chapter (PDF, ~5–10 pages) + one code file; put them in `fixtures/demo/` (Member 4 / whoever is free)

## A — AI & Graph Engine  (`backend/app/ingest|extraction|graph`, `api/documents.py`, `api/quiz.py`)

- [x] **A1** (H0.5–1.5) `ingest/parser.py::to_text` (PDF via PyMuPDF, text, code) + `ingest/chunker.py::chunk`. ✅ `test_a1_parse_and_chunk`
- [x] **A2** (H1.5–2.5) `extraction/concepts.py::extract_chunk` using `llm.structured(..., ExtractionResult)`. Try it on `fixtures/sample_chapter.txt` from a scratch script; check ids, excerpts, edges.
- [x] **A3** (H2.5–3.5) `graph/builder.py::GraphBuilder.merge/finalize`: normalize ids, dedupe, drop unknown/self/cyclic edges, importance, cap ~40 nodes. ✅ `test_a3_merge_dedupes_and_blocks_cycles`
- [x] **A4** (H3.5–4.5) `extraction/pipeline.py::build_graph_stream`: parse → chunk → extract (2–3 concurrent) → merge → yield `concept`/`edge`/`status` → `done`. Set `MOCK_EXTRACTION=false`. **→ M1 with C6**
- [x] **A5** (H4.5–5.5) `extraction/quiz_gen.py::generate_quiz`: choose concepts (advanced nodes + their prereqs), Claude writes QuestionKeys, ids q1..qN.
- [x] **A6** (H5.5–7) Prompt tuning on the real demo chapter + a code file: fewer junk concepts, correct prereq direction, no cycles. Try `CLAUDE_EFFORT=low` for speed.
- [x] **A7** (H7–8) Demo safety: save the real demo chapter's graph + quiz key to `fixtures/demo/` and add a "replay cached" path so the demo works even if the API is slow or down.

## B — Learner Engine  (`backend/app/learner/`, `api/assess.py`)

- [x] **B1** (H0.5–2) `learner/mastery.py`: `bkt_update` + `estimate_mastery` (BKT + light propagation to prereqs). ✅ `test_b1_bkt_and_mastery`
- [x] **B2** (H2–3.5) `learner/gaps.py::find_root_gaps`: walk prerequisites from each gap to the deepest weak ancestor; path + plain-English explanation. ✅ `test_b2_root_gap_is_chain_rule`  ⭐ core differentiator
- [x] **B3** (H3.5–5) `learner/careless.py`: careless score from prereq mastery + confidence + response time + consistency. ✅ `test_b3_gradient_descent_is_careless`  ⭐ official stretch goal
- [x] **B4** (H5–6) `learner/path.py::suggest_next_topics`: topological order of the gap subgraph; careless items last; "ready to learn" when no gaps. ✅ `test_b4_next_topics_start_with_root`
- [x] **B5** (H6–6.5) Verify `learner/service.py::assess` end to end; set `MOCK_LEARNER=false`. ✅ `test_b5_full_assessment` **→ M2**
- [x] **B6** (stretch) Adaptive probing: next question targets the failed concept's weakest prerequisite (needs a `contract:` PR for `POST /api/quiz/{id}/next`).
- [ ] **B7** (stretch) Graph embeddings over time: spectral/node2vec-style node embeddings (numpy) + a per-learner mastery history; similar concepts share evidence across quiz attempts.

## C — Frontend  (`frontend/src/**`)

- [x] **C1** (H0.5–1.5) Upload polish: drag-and-drop, file-type badge, title field, sample-file buttons.
- [x] **C2** (H1.5–3) Live graph polish: pop-in animation for new nodes, colour by `cluster` before the quiz, `zoomToFit` on done, status/progress bar.
- [x] **C3** (H3–4) Node detail: show `source_excerpt` prominently (the "no hallucination" proof), prereq + dependent lists, click to jump.
- [x] **C4** (H4–4.5) Quiz UX: progress bar, keyboard 1–4 + Enter, confidence as three buttons (Guessing / Unsure / Sure).
- [x] **C6** (H4.5–5) Integrate the real backend: `VITE_USE_MOCK=false`, handle stream errors and a slow first response. **→ M1 with A4**
- [x] **C5** (H5–6.5) Results "aha" moment: animate the root-gap path (red particles already on), pulse the root node, orange dashed ring for careless, dim unrelated nodes, and a "Study next" list that focuses its node.
- [x] **C7** (H6.5–8) Demo polish: hero/empty state, reset button, loading skeletons, responsive side panel, no console errors.
- [x] **C8** (stretch) Teacher view: heatmap of the % of students weak on each node (simulate 5 learners from fixtures).

## D — Demo & Pitch  (Member 4, or everyone after M3)

- [ ] **D1** Finalize the 5-slide PPT (content already drafted)
- [ ] **D2** 90-second demo script: upload → live graph → click node (source quote) → quiz (one careless fast answer) → red path to the root gap → next topics
- [ ] **D3** Record a backup screen video of the demo at H8.5
- [ ] **D4** README screenshots + architecture diagram

## E — Beginner Track  (`site/`, `scripts/`)  — no React, no FastAPI, no API key needed

Good first tasks for someone new to the stack. Plain HTML/CSS and plain Python (standard library
only: `json`, `random`, `pathlib`). Nothing here is imported by the app, so you **cannot break
anyone else's code**. Each task is its own small PR. Ask a pillar owner if a word is unclear.

- [ ] **E1** (H0.5–2.5) Project landing page `site/index.html` + `site/style.css`. Plain HTML/CSS, no
  framework, opens by double-clicking. Sections: hero ("Find the gap *behind* the gap"), the problem,
  how it works in 4 steps (upload → graph → quiz → root gap), team, link to the repo. Use the
  colours from the app (red = gap, orange = careless). ✅ opens in Chrome with no broken images;
  looks OK on a phone (Chrome DevTools → device toolbar).
- [ ] **E2** (H2.5–3.5) `scripts/graph_stats.py`: read `fixtures/sample_graph.json` and print
  - number of concepts and edges
  - concepts per `cluster`
  - top 3 concepts by `importance`
  - any concept with an empty `source_excerpt`, any edge with empty `evidence` (these are bugs!)
  - any edge whose `source`/`target` is not a concept id

  Take the file path as an argument so Pillar A can run it on real graphs:
  `python3 scripts/graph_stats.py fixtures/sample_graph.json`. ✅ runs with no errors, output matches
  what you count by hand.
- [ ] **E3** (H3.5–5) `scripts/fake_learners.py`: generate 5 simulated learners' answer files
  (same shape as `fixtures/sample_answers.json`) into `scripts/out/learner_1.json … learner_5.json`.
  Use `random.seed(42)` so output is the same every run. Give each learner a "personality"
  (strong, weak at maths, careless/fast, guesser, average) that changes `choice_index`,
  `confidence` and `time_ms`. Answer key: `fixtures/sample_quiz_key.json`. Feeds **C8** teacher view.
  ✅ `python3 -m json.tool scripts/out/learner_1.json` is valid JSON.
- [ ] **E4** (H5–6.5) Write 2 extra demo inputs in `site/samples/` (so it doesn't touch `fixtures/`):
  a ~1-page text chapter on a topic you know (e.g. photosynthesis, SQL joins, fractions) where
  concepts clearly build on each other, and a short well-commented Python file. Great for testing
  Pillar A's prompts on something that isn't the neural-network demo.
- [ ] **E5** (H6.5–8) QA tester: run the full demo 3× following **D2**, file every bug as a GitHub
  issue (steps, what you expected, what happened, screenshot). Try weird inputs: empty file, huge
  file, image-only PDF, answering nothing. Add a "How it works" screenshot row to `site/index.html`.
- [ ] **E6** (stretch) Glossary page `site/glossary.html`: explain BKT, prerequisite graph, root-cause
  gap, careless slip, DAG in 2–3 plain sentences each. Doubles as judge Q&A prep.

**How to open a PR (first time?)**
```bash
git checkout main && git pull
git checkout -b e/E1-landing          # branch name: e/<task>
# ...edit files...
git add site/ && git commit -m "feat(site): landing page"
git push -u origin e/E1-landing       # then open the PR on GitHub
```
