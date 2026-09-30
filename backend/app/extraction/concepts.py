"""One chunk -> concepts + prerequisite edges via Claude.  [Pillar A — task A2]"""

from app.extraction import llm, prompts
from app.models import Concept, ExtractionResult


async def extract_chunk(chunk: str, known: list[Concept]) -> ExtractionResult:
    """TODO(A2): call llm.structured(prompts.EXTRACT_SYSTEM, prompts.EXTRACT_USER.format(...),
    ExtractionResult). `known` = "id: name" lines so Claude reuses ids across chunks."""
    _ = (llm, prompts)
    raise NotImplementedError("A2: extract concepts from a chunk")
