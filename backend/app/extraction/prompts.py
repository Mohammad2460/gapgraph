"""Prompt drafts.  [Pillar A — task A3/A5 tunes these]"""

EXTRACT_SYSTEM = """You build prerequisite knowledge graphs from learning material \
(textbook chapters, lecture notes, source code, or past assessments).

For the given chunk:
- Extract the key teachable concepts (aim for 3-8 per chunk; skip trivia).
- Each concept id is a lowercase snake_case slug of its name, e.g. "chain_rule".
- If a concept matches one already known (listed below), REUSE that exact id.
- source_excerpt must be a verbatim sentence from the chunk that grounds the concept.
- Add a prerequisite edge source -> target only when a learner genuinely needs
  `source` to understand `target`. Put the justifying text in `evidence`.
- Never create cycles. Prefer fewer, high-confidence edges over many weak ones.
- For source code: concepts are programming ideas used (e.g. "recursion",
  "list_comprehension"), not variable names."""

EXTRACT_USER = """Known concepts so far (reuse these ids when they match):
{known}

Chunk:
<chunk>
{chunk}
</chunk>"""

QUIZ_SYSTEM = """You write short diagnostic multiple-choice questions for a knowledge graph.
- One question per concept listed; each has exactly 4 options and one correct answer.
- Test understanding, not wording recall. Distractors must be plausible misconceptions.
- Ground every question in the concept definition and excerpt provided.
- difficulty: easy for foundational concepts, hard for the most advanced ones.
- explanation: one sentence on why the correct option is right."""

QUIZ_USER = """Write one question for each of these concepts (id: name — definition — excerpt):
{concepts}"""
