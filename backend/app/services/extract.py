from typing import NamedTuple, Optional
import fitz  # PyMuPDF
from docx import Document as Docx
from io import BytesIO

class Extracted(NamedTuple):
    text: str
    page_texts: Optional[list[str]]

def extract_from_bytes(content: bytes, filename: str, mime: str | None) -> Extracted:
    name = filename.lower()
    mime = (mime or "").lower()

    if name.endswith(".pdf") or "pdf" in mime:
        doc = fitz.open(stream=content, filetype="pdf")
        pages = [p.get_text("text") for p in doc]
        return Extracted(text="\n".join(pages), page_texts=pages)

    if name.endswith(".docx") or "word" in mime:
        bio = BytesIO(content)
        d = Docx(bio)
        txt = "\n".join(p.text for p in d.paragraphs)
        return Extracted(text=txt, page_texts=None)

    try:
        txt = content.decode("utf-8")
    except UnicodeDecodeError:
        txt = content.decode("latin-1", errors="ignore")
    return Extracted(text=txt, page_texts=None)
