"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes.prescriptions import router as prescriptions_router
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("medico")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Medico API v%s starting — gemini=%s firebase=%s",
        __version__,
        "configured" if settings.gemini_configured else "MISSING (set GEMINI_API_KEY)",
        "configured" if settings.firebase_configured else "not configured (demo data)",
    )
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Prescription intelligence & medicine availability platform — "
                "OCR a prescription, understand it with Gemini and check pharmacy stock.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(prescriptions_router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
async def root():
    return {"service": settings.app_name, "version": __version__, "docs": "/docs"}
