"""Plain text -> chunks for extraction.  [Pillar A — task A1]"""

import re


def chunk(text: str, max_chars: int = 6000) -> list[str]:
    """Split text into chunks of <= max_chars, greedily packing blank-line-separated paragraphs.

    Fewer, bigger chunks = fewer LLM calls = faster demo. A paragraph longer than
    max_chars is hard-split so the size limit always holds.
    """
    paragraphs: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        while len(para) > max_chars:
            paragraphs.append(para[:max_chars])
            para = para[max_chars:].strip()
        if para:
            paragraphs.append(para)

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks
