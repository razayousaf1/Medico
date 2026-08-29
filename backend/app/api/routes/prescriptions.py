"""Prescription analysis endpoints."""

import logging

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.core.config import get_settings
from app.models.schemas import HealthStatus, PrescriptionAnalysis
from app.services.availability_service import AvailabilityService
from app.services.firestore_service import get_store
from app.services.llm_service import LLMError
from app.services.ocr_service import OCRError, paddle_available

logger = logging.getLogger(__name__)
router = APIRouter()

_settings = get_settings()
_availability = AvailabilityService()


@router.post(
    "/analyze-prescription",
    response_model=PrescriptionAnalysis,
    summary="Upload a prescription, run OCR + Gemini, return medicine availability",
)
async def analyze_prescription(
    file: UploadFile = File(..., description="JPG, PNG, WEBP or PDF prescription"),
    lat: float | None = Query(None, ge=-90, le=90, description="User latitude"),
    lng: float | None = Query(None, ge=-180, le=180, description="User longitude"),
) -> PrescriptionAnalysis:
    data = await _read_upload(file)

    try:
        return await _availability.analyze(
            data=data,
            content_type=file.content_type,
            filename=file.filename or "prescription",
            lat=lat,
            lng=lng,
        )
    except OCRError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface a clean message, log the stack
        logger.exception("Unexpected error while analysing prescription")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while analysing the prescription. Please try again.",
        ) from exc


async def _read_upload(file: UploadFile) -> bytes:
    """Read and validate the uploaded file (size + type)."""
    settings = get_settings()

    declared_type = (file.content_type or "").split(";")[0].strip().lower()
    if declared_type and declared_type not in {
        "image/jpeg", "image/jpg", "image/png", "image/webp",
        "application/pdf", "application/octet-stream",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{declared_type}'. Upload a JPG, PNG, WEBP image or a PDF.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty.")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File is too large. Maximum size is {settings.max_upload_mb} MB.",
        )
    return data


@router.get("/health", response_model=HealthStatus, summary="Service health & configuration")
async def health() -> HealthStatus:
    store = get_store()
    return HealthStatus(
        status="ok",
        app_env=_settings.app_env,
        gemini_configured=_settings.gemini_configured,
        firebase_configured=_settings.firebase_configured,
        using_demo_data=store.is_demo,
        ocr_available=paddle_available(),
        model=_settings.gemini_model,
    )
