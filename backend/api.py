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
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Tuple

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

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.heritage_service import HeritageService, build_service

logger = logging.getLogger(__name__)

# Uploads are written to a temp file, so cap the decoded size.
MAX_IMAGE_BYTES = 10 * 1024 * 1024

# Error codes returned to clients.
ERROR_INVALID_INPUT = "invalid_input"
ERROR_NOT_FOUND = "not_found"
ERROR_UNPROCESSABLE = "unprocessable_image"
ERROR_INTERNAL = "internal_error"
ERROR_RATE_LIMITED = "rate_limited"


# ── security & abuse protection ───────────────────────────────────────────────

class InMemoryRateLimiter:
    """Sliding-window rate limiter per client IP address."""

    def __init__(self, requests_per_minute: int = 120):
        self.limit = requests_per_minute
        self.window = 60.0
        self._history: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - self.window
        timestamps = [t for t in self._history[client_ip] if t > window_start]
        self._history[client_ip] = timestamps

        if len(timestamps) >= self.limit:
            retry_after = int(self.window - (now - timestamps[0])) + 1
            return False, max(1, retry_after)

        self._history[client_ip].append(now)
        return True, 0


rate_limiter = InMemoryRateLimiter(
    requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces essential security headers and optional production HTTPS redirects."""

    def __init__(self, app, enforce_https: bool = False):
        super().__init__(app)
        self.enforce_https = enforce_https

    async def dispatch(self, request: Request, call_next) -> Response:
        # Production HTTPS enforcement
        if self.enforce_https:
            proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            if proto == "http":
                url = request.url.replace(scheme="https")
                return Response(status_code=301, headers={"Location": str(url)})

        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:* https:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self';"
        )
        if self.enforce_https or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


app = FastAPI(
    title="Heritage Discovery API",
    version="1.0.0",
    description="Heritage site recognition with grounded, cited answers.",
)

# Apply Security Headers Middleware
enforce_https = os.getenv("ENFORCE_HTTPS", "false").lower() in ("true", "1", "yes")
app.add_middleware(SecurityHeadersMiddleware, enforce_https=enforce_https)

# Allow the local frontends to call POST /recognize.
# Production origins can be supplied via the ALLOWED_ORIGINS environment
# variable as a comma-separated string; localhost defaults are preserved.
raw_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
if not allowed_origins:
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "https://heritage-swg3.vercel.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=os.getenv("ALLOWED_ORIGIN_REGEX", r"^https?://.*"),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["Content-Type", "Accept", "Authorization", "X-Requested-With"],
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
        default="", max_length=500, description="Optional question about the matched site."
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
    margin: Optional[float] = None
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

def _validate_image_magic_bytes(data: bytes) -> str:
    """Validate image binary header and return canonical file extension.

    Raises ValueError if data is not a recognized JPEG, PNG, or WebP.
    """
    if len(data) < 12:
        raise ValueError("Image file is too small to be valid")

    # JPEG: starts with FF D8 FF
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"

    # PNG: starts with 89 50 4E 47 0D 0A 1A 0A
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"

    # WebP: RIFF....WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"

    # GIF fallback
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"

    raise ValueError("File content is not a recognized JPEG, PNG, or WebP image")


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

    if not data or len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail=ERROR_INVALID_INPUT)

    try:
        detected_suffix = _validate_image_magic_bytes(data)
        suffix = detected_suffix or suffix
    except ValueError:
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
async def recognize(request: RecognizeRequest, client_request: Request) -> Any:
    """Recognize a heritage site and optionally answer a question about it."""
    # Spam / abuse rate limiting check
    client_ip = client_request.client.host if client_request.client else "127.0.0.1"
    forwarded = client_request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    allowed, retry_after = rate_limiter.is_allowed(client_ip)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": ERROR_RATE_LIMITED,
                "detail": "Rate limit exceeded. Please wait before submitting more queries.",
            },
            headers={"Retry-After": str(retry_after)},
        )

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
