"""
OCR service — extracts raw text from prescription images/PDFs with PaddleOCR.

Design notes
------------
* The PaddleOCR engine is heavyweight (model load takes seconds and the first
  run downloads models), so it is created lazily and cached for the process
  lifetime.
* Both the modern PaddleOCR 3.x API (`predict`) and the legacy 2.x API
  (`ocr`) are supported, so the code works across paddleocr versions.
* PDFs are rasterised to PNG pages with PyMuPDF before OCR.
"""

import logging
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf",
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


class OCRError(Exception):
    """Raised when OCR cannot be performed (bad input, engine failure…)."""


@dataclass
class OCRResult:
    text: str
    confidence: float
    pages: int


def paddle_available() -> bool:
    """Cheap check used by /api/health — does not initialise the engine."""
    try:
        import paddleocr  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


class OCRService:
    _engine: Any = None
    _engine_init_attempted = False

    # ------------------------------------------------------------------
    # Engine lifecycle
    # ------------------------------------------------------------------

    def _get_engine(self) -> Any:
        if self._engine is not None:
            return self._engine
        if self._engine_init_attempted:
            raise OCRError(
                "PaddleOCR is not installed in this environment. "
                "Install backend dependencies with: pip install -r requirements.txt"
            )

        self._engine_init_attempted = True
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:  # noqa: BLE001
            raise OCRError(
                f"PaddleOCR could not be imported ({exc}). "
                "Install it with: pip install paddleocr paddlepaddle"
            ) from exc

        try:
            # PaddleOCR >= 3.x constructor
            self._engine = PaddleOCR(
                lang="en",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
            )
        except TypeError:
            # PaddleOCR 2.x constructor
            self._engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        except Exception as exc:  # noqa: BLE001
            raise OCRError(f"Failed to initialise PaddleOCR: {exc}") from exc

        logger.info("PaddleOCR engine initialised")
        return self._engine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_text(self, data: bytes, content_type: Optional[str], filename: str) -> OCRResult:
        """OCR an uploaded file. Images are processed directly; PDFs page by page."""
        if not data:
            raise OCRError("Uploaded file is empty")

        kind = self._sniff_kind(data, content_type, filename)
        pages = self._to_page_images(data, kind)

        engine = self._get_engine()

        page_texts: list[str] = []
        all_scores: list[float] = []

        for page_bytes in pages:
            texts, scores = self._ocr_image(engine, page_bytes)
            page_texts.append("\n".join(texts))
            all_scores.extend(scores)

        full_text = "\n".join(part for part in page_texts if part.strip()).strip()
        if not full_text:
            raise OCRError(
                "No readable text was found on the prescription. "
                "Make sure the photo is sharp, well-lit and the text is in frame."
            )

        confidence = sum(all_scores) / len(all_scores) if all_scores else 0.0
        return OCRResult(text=full_text, confidence=round(confidence, 4), pages=len(pages))

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    @staticmethod
    def _sniff_kind(data: bytes, content_type: Optional[str], filename: str) -> str:
        ext = os.path.splitext(filename or "")[1].lower()
        ctype = (content_type or "").lower().split(";")[0].strip()

        if ctype in ALLOWED_CONTENT_TYPES:
            return "pdf" if ctype == "application/pdf" else "image"
        if ext in {".pdf"}:
            return "pdf"
        if ext in {".jpg", ".jpeg", ".png", ".webp"}:
            return "image"
        # Content sniffing fallback
        if data[:4] == b"%PDF":
            return "pdf"
        if data[:8] == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]):
            return "image"
        if data[:3] == b"\xFF\xD8\xFF":
            return "image"
        raise OCRError(
            "Unsupported file type. Please upload a JPG, PNG, WEBP image or a PDF."
        )

    @staticmethod
    def _to_page_images(data: bytes, kind: str) -> list[bytes]:
        if kind == "image":
            return [data]
        # PDF → one PNG per page at 2x zoom for reliable OCR
        try:
            import fitz  # PyMuPDF
        except Exception as exc:  # noqa: BLE001
            raise OCRError("PDF support is unavailable (PyMuPDF not installed)") from exc

        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:  # noqa: BLE001
            raise OCRError("The PDF file appears to be corrupted") from exc

        if doc.page_count == 0:
            raise OCRError("The PDF contains no pages")

        pages = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            pages.append(pix.tobytes("png"))
        doc.close()
        return pages

    # ------------------------------------------------------------------
    # Engine invocation (PaddleOCR 2.x + 3.x compatible)
    # ------------------------------------------------------------------

    def _ocr_image(self, engine: Any, image_bytes: bytes) -> tuple[list[str], list[float]]:
        # PaddleOCR reads from a path — write a temp file
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            raw = self._run_engine(engine, tmp_path)
        except OCRError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise OCRError(f"OCR engine failed while processing the image: {exc}") from exc
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        return self._flatten_result(raw)

    @staticmethod
    def _run_engine(engine: Any, path: str) -> Any:
        if hasattr(engine, "predict"):  # paddleocr >= 3.0
            return engine.predict(path)
        return engine.ocr(path, cls=True)  # paddleocr 2.x

    @staticmethod
    def _flatten_result(raw: Any) -> tuple[list[str], list[float]]:
        texts: list[str] = []
        scores: list[float] = []

        pages = raw if isinstance(raw, list) else [raw]
        for page in pages:
            if page is None:
                continue

            # PaddleOCR 3.x — dict-like OCRResult with rec_texts / rec_scores
            if isinstance(page, dict) or hasattr(page, "get"):
                page_texts = page.get("rec_texts") if hasattr(page, "get") else None
                if page_texts:
                    page_scores = page.get("rec_scores") or []
                    texts.extend(str(t) for t in page_texts)
                    scores.extend(float(s) for s in page_scores)
                    continue

            # PaddleOCR 2.x — list of [bbox, (text, confidence)]
            if isinstance(page, list):
                for item in page:
                    if not item or not isinstance(item, (list, tuple)) or len(item) < 2:
                        continue
                    payload = item[1]
                    if isinstance(payload, (list, tuple)) and len(payload) == 2:
                        text, score = payload
                        texts.append(str(text))
                        scores.append(float(score))

        return texts, scores
