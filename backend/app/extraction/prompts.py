"""Prompt drafts.  [Pillar A — task A3/A5 tunes these]"""

EXTRACT_SYSTEM = """You build prerequisite knowledge graphs from learning material \
(textbook chapters, lecture notes, source code, or past assessments).

For the given chunk:
- Extract the key teachable concepts (aim for 3-8 per chunk; skip trivia).
- One concept = ONE idea a quiz question could test on its own. Never merge two
  ideas into one node ("functions_and_derivatives" is wrong: make "functions" and
  "derivatives" with an edge between them). Names are 1-4 words, singular noun phrases.
- Each concept id is a lowercase snake_case slug of its name, e.g. "chain_rule".
- If a concept matches one already known (listed below), REUSE that exact id.
- definition: one plain sentence a student could learn from.
- source_excerpt must be a verbatim sentence copied from the chunk that grounds the concept.
- cluster: a short snake_case topic group shared by related concepts (e.g. "calculus",
  "linear_algebra", "training"); use 2-5 clusters per document.
- importance: 0.9+ for the chapter's main goal concepts, ~0.5 for supporting ideas,
  ~0.3 for background the chapter assumes.
- Add a prerequisite edge source -> target only when a learner genuinely needs
  `source` to understand `target`. Direction: foundation -> advanced. Put the
  justifying text from the chunk in `evidence`.
- Include prerequisites the text relies on even if briefly mentioned, so chains are complete.
- Never create cycles. Prefer fewer, high-confidence edges over many weak ones.
- For source code: concepts are programming ideas the code teaches or relies on (e.g.
  "recursion", "hash_map", "topological_sort"), not variable, function, or file names.
  source_excerpt may be a verbatim line of code or comment."""

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
