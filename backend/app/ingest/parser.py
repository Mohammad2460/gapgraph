"""Uploaded bytes -> plain text.  [Pillar A — task A1]"""

CODE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rb", ".ipynb"}


def to_text(raw: bytes, filename: str | None) -> str:
    """Return the document as plain text.

    TODO(A1):
    - .pdf  -> PyMuPDF: `import pymupdf; doc = pymupdf.open(stream=raw, filetype="pdf")`,
               join `page.get_text()` for every page.
    - code  -> decode utf-8; optionally prefix "Source code file: {filename}".
    - else  -> decode utf-8 (errors="ignore").
    """
    raise NotImplementedError("A1: parse PDF / text / code")
