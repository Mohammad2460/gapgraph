"""Uploaded bytes -> plain text.  [Pillar A — task A1]"""

from pathlib import Path

CODE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rb", ".ipynb"}


def to_text(raw: bytes, filename: str | None) -> str:
    """Return the document as plain text (PDF via PyMuPDF, code and text decoded as utf-8)."""
    ext = Path(filename or "").suffix.lower()
    if ext == ".pdf":
        import pymupdf

        with pymupdf.open(stream=raw, filetype="pdf") as doc:
            return "\n\n".join(page.get_text() for page in doc).strip()
    text = raw.decode("utf-8", errors="ignore").strip()
    if ext in CODE_EXTENSIONS:
        return f"Source code file: {filename}\n\n{text}"
    return text
