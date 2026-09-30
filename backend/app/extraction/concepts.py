"""One chunk -> concepts + prerequisite edges via Claude.  [Pillar A — task A2]"""

from app.extraction import llm, prompts
from app.models import Concept, ExtractionResult


async def extract_chunk(chunk: str, known: list[Concept]) -> ExtractionResult:
    """Extract concepts + edges from one chunk; `known` lets Claude reuse ids across chunks."""
    known_lines = "\n".join(f"{c.id}: {c.name}" for c in known) or "(none yet)"
    user = prompts.EXTRACT_USER.format(known=known_lines, chunk=chunk)
    return await llm.structured(prompts.EXTRACT_SYSTEM, user, ExtractionResult)
