"""Plain text -> chunks for extraction.  [Pillar A — task A1]"""


def chunk(text: str, max_chars: int = 6000) -> list[str]:
    """Split text into chunks of <= max_chars, breaking on headings/paragraphs.

    TODO(A1): split on blank lines, greedily pack paragraphs up to max_chars.
    Fewer, bigger chunks = fewer LLM calls = faster demo. A 10-page chapter
    should be ~3-6 chunks.
    """
    raise NotImplementedError("A1: chunk text")
