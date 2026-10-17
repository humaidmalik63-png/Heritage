"""
Minimal HTTP API around the heritage service layer.

This module is transport-only: it validates input, calls
:class:`~backend.heritage_service.HeritageService`, and shapes the response.
All recognition, confidence, evidence and RAG logic stays in the service.
"""

from __future__ import annotations

import base64
import binascii
import logging
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

# Load environment variables from a local .env file (if present) before any
# service configuration is read.  This is the only place the project loads
# .env; nothing here hard-codes credentials.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional at runtime — the app still works with
    # variables supplied through the real process environment.
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

from backend.heritage_service import HeritageService, build_service

logger = logging.getLogger(__name__)

# Uploads are written to a temp file, so cap the decoded size.
MAX_IMAGE_BYTES = 10 * 1024 * 1024

# Error codes returned to clients.
ERROR_INVALID_INPUT = "invalid_input"
ERROR_NOT_FOUND = "not_found"
ERROR_UNPROCESSABLE = "unprocessable_image"
ERROR_INTERNAL = "internal_error"

app = FastAPI(
    title="Heritage Discovery API",
    version="1.0.0",
    description="Heritage site recognition with grounded, cited answers.",
)

# Allow the local frontends to call POST /recognize.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8080",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Populated by get_service() on first use.
_service: Optional[HeritageService] = None


def get_service() -> HeritageService:
    """Return the shared service instance, building it on first use."""
    global _service
    if _service is None:
        _service = build_service()
    return _service


def set_service(service: Optional[HeritageService]) -> None:
    """Override the shared service (used by tests and by startup wiring)."""
    global _service
    _service = service


# ── schemas ───────────────────────────────────────────────────────────────────

class RecognizeRequest(BaseModel):
    """Recognition request: an image path or a base64-encoded image."""

    image_path: Optional[str] = Field(
        default=None, description="Filesystem path to a query image."
    )
    image_base64: Optional[str] = Field(
        default=None, description="Base64-encoded query image."
    )
    question: str = Field(
        default="", description="Optional question about the matched site."
    )
    top_k: int = Field(
        default=5, ge=1, le=50, description="Number of candidate matches to return."
    )

    @model_validator(mode="after")
    def _require_one_image(self) -> "RecognizeRequest":
        if not self.image_path and not self.image_base64:
            raise ValueError("either 'image_path' or 'image_base64' is required")
        if self.image_path and self.image_base64:
            raise ValueError("provide only one of 'image_path' or 'image_base64'")
        return self


class ErrorResponse(BaseModel):
    error: str
    detail: str


class HealthResponse(BaseModel):
    status: str
    service_ready: bool
    index_size: int
    default_top_k: int
    similarity_threshold: float


class RecognizeResponse(BaseModel):
    site_id: str
    similarity: float
    confidence: Optional[float] = None
    confident: bool
    confirmed: bool = False
    decision: str
    recognition_source: str = "local"
    global_identification: Optional[Dict[str, Any]] = None
    top_k: int
    matches: list
    metadata: Dict[str, Any]
    evidence: Dict[str, Any]
    answer: Optional[str]
    citations: list
    reason: Optional[str]
    is_grounded: bool
    is_valid: bool


# ── helpers ───────────────────────────────────────────────────────────────────

def _error(status_code: int, code: str, detail: str) -> JSONResponse:
    """Build a safe error response (no internal detail, no stack traces)."""
    return JSONResponse(
        status_code=status_code,
        content={"error": code, "detail": detail},
    )


@contextmanager
def _temp_image(data: bytes, suffix: str) -> Iterator[str]:
    """Write bytes to a temporary file and yield its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        yield path
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


@contextmanager
def _resolve_query(request: RecognizeRequest) -> Iterator[str]:
    """Yield a path the service can embed.

    ``image_path`` is passed through untouched; ``image_base64`` is decoded to
    a temporary file.  Raises HTTPException on invalid input.
    """
    if request.image_path:
        path = request.image_path
        if not os.path.isfile(path):
            raise HTTPException(
                status_code=404,
                detail=ERROR_NOT_FOUND,
            )
        yield path
        return

    raw = request.image_base64 or ""
    # tolerate a data URL prefix, and use its media type for the file suffix
    suffix = ".img"
    if raw.startswith("data:"):
        header, _, raw = raw.partition(",")
        mime = header[5:].split(";")[0].strip().lower()
        suffix = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
        }.get(mime, ".img")

    try:
        data = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail=ERROR_INVALID_INPUT)

    if not data:
        raise HTTPException(status_code=400, detail=ERROR_INVALID_INPUT)

    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail=ERROR_INVALID_INPUT)

    with _temp_image(data, suffix) as path:
        yield path


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness / readiness probe."""
    try:
        service = get_service()
    except Exception:
        logger.exception("service unavailable")
        return HealthResponse(
            status="degraded",
            service_ready=False,
            index_size=0,
            default_top_k=0,
            similarity_threshold=0.0,
        )

    return HealthResponse(
        status="ok",
        service_ready=True,
        index_size=int(service.confidence_layer.index.ntotal),
        default_top_k=int(service.default_top_k),
        similarity_threshold=float(service.confidence_layer.config.similarity_threshold),
    )


@app.post("/recognize", response_model=RecognizeResponse)
async def recognize(request: RecognizeRequest) -> Any:
    """Recognize a heritage site and optionally answer a question about it."""
    try:
        service = get_service()
    except Exception:
        logger.exception("service unavailable")
        return _error(503, ERROR_INTERNAL, "service is not ready")

    try:
        with _resolve_query(request) as path:
            result = await service.recognize_async(
                path,
                question=request.question,
                top_k=request.top_k,
            )
    except HTTPException as exc:
        return _error(exc.status_code, exc.detail, "invalid request")
    except (FileNotFoundError, ValueError) as exc:
        # unreadable / corrupt image
        logger.info("rejected image: %s", exc)
        return _error(422, ERROR_UNPROCESSABLE, "image could not be processed")
    except Exception:
        # never leak an internal stack trace to the client
        logger.exception("recognition failed")
        return _error(500, ERROR_INTERNAL, "internal error")

    payload = result.to_dict()

    # A low-confidence match is a valid, explicit outcome - not an error.
    if not payload["confident"]:
        return JSONResponse(status_code=200, content=payload)

    return payload
