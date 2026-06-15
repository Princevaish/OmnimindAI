"""
Document text extraction layer.

Separates text extraction from chunking so each step can be audited
independently. Supports PDF, TXT, and DOCX with explicit error handling
for image-only PDFs (the most common silent failure mode).
"""

import io
from app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from uploaded file bytes.

    Supports: .pdf, .txt, .md, .docx
    Returns an empty string (never raises) so the caller can decide
    how to handle extraction failures.

    Args:
        file_bytes: Raw file content as bytes.
        filename:   Original filename — used to determine extraction strategy.

    Returns:
        Extracted plain text string.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    logger.info("extract_text — file=%r  ext=%s  bytes=%d", filename, ext, len(file_bytes))

    text = ""

    if ext == "pdf":
        text = _extract_pdf(file_bytes, filename)
    elif ext in ("txt", "md"):
        text = _extract_plaintext(file_bytes, filename)
    elif ext == "docx":
        text = _extract_docx(file_bytes, filename)
    else:
        # Attempt UTF-8 decode as a fallback
        logger.warning("extract_text — unknown extension %r, attempting UTF-8 decode", ext)
        try:
            text = file_bytes.decode("utf-8", errors="replace")
        except Exception as exc:
            logger.error("extract_text — UTF-8 fallback failed: %s", exc)

    logger.info(
        "extract_text — extracted %d chars from %r",
        len(text), filename,
    )
    if len(text) < 50:
        logger.warning(
            "extract_text — very short extraction (%d chars). "
            "Possible causes: image-based PDF, encrypted file, or empty document.",
            len(text),
        )
    else:
        # Log a sample to confirm extraction looks sane
        sample = text[:200].replace("\n", " ")
        logger.info("extract_text — sample: %r", sample)

    return text


def _extract_pdf(file_bytes: bytes, filename: str) -> str:
    """Extract text from a PDF using PyMuPDF (fitz), with pdfplumber fallback."""
    text_parts: list[str] = []

    # ── Strategy 1: PyMuPDF (fastest, best for text PDFs) ────────────────────
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_pages = len(doc)
        logger.info("_extract_pdf [fitz] — %d pages in %r", total_pages, filename)

        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)
            else:
                logger.debug(
                    "_extract_pdf [fitz] — page %d has no text layer "
                    "(may be scanned/image)", page_num + 1,
                )

        doc.close()

        if text_parts:
            full = "\n\n".join(text_parts)
            logger.info(
                "_extract_pdf [fitz] — extracted %d chars across %d/%d pages",
                len(full), len(text_parts), total_pages,
            )
            return full

        logger.warning(
            "_extract_pdf [fitz] — zero text extracted from %r. "
            "PDF may be entirely image-based. Trying pdfplumber…", filename,
        )

    except ImportError:
        logger.warning("_extract_pdf — PyMuPDF not installed, trying pdfplumber")
    except Exception as exc:
        logger.error("_extract_pdf [fitz] — error: %s", exc)

    # ── Strategy 2: pdfplumber (better for tables) ────────────────────────────
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_pages = len(pdf.pages)
            logger.info("_extract_pdf [pdfplumber] — %d pages in %r", total_pages, filename)
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text)
                else:
                    logger.debug(
                        "_extract_pdf [pdfplumber] — page %d empty", page_num + 1
                    )

        if text_parts:
            full = "\n\n".join(text_parts)
            logger.info("_extract_pdf [pdfplumber] — extracted %d chars", len(full))
            return full

        logger.error(
            "_extract_pdf — both strategies returned empty text for %r. "
            "This is likely an image-only PDF. OCR would be required.", filename,
        )
        return ""

    except ImportError:
        logger.error("_extract_pdf — neither PyMuPDF nor pdfplumber is installed")
        return ""
    except Exception as exc:
        logger.error("_extract_pdf [pdfplumber] — error: %s", exc)
        return ""


def _extract_plaintext(file_bytes: bytes, filename: str) -> str:
    """Extract text from plain text files with encoding fallback chain."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            logger.info(
                "_extract_plaintext — decoded %r with %s (%d chars)",
                filename, encoding, len(text),
            )
            return text
        except UnicodeDecodeError:
            continue
    logger.error("_extract_plaintext — all encoding attempts failed for %r", filename)
    return ""


def _extract_docx(file_bytes: bytes, filename: str) -> str:
    """Extract text from .docx files using python-docx."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n\n".join(paragraphs)
        logger.info(
            "_extract_docx — %d paragraphs, %d chars from %r",
            len(paragraphs), len(text), filename,
        )
        return text
    except ImportError:
        logger.error("_extract_docx — python-docx not installed")
        return ""
    except Exception as exc:
        logger.error("_extract_docx — error: %s", exc)
        return ""