"""
Google Gemini Vision client for global heritage monument recognition fallback.

Communicates with Google Gemini API to identify monuments globally when local
open-set recognition cannot make a confident identification.

Adheres to strict security and reliability rules:
- API key must never be hard-coded or logged.
- Never crashes the caller on network failure, timeout, or malformed response.
- Returns a safe, structured unknown result on any failure.
- Uses official Google Gemini REST API via existing httpx dependency.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import random
import re
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import httpx
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass
from PIL import Image, ImageOps
from pydantic import BaseModel, Field, model_validator

def is_live_gemini_disabled() -> bool:
    """
    Check whether live external Gemini API calls are disabled by the test environment.
    Returns True if DISABLE_LIVE_GEMINI is set to '1', 'true', 'yes', or 'on'.
    """
    val = os.getenv("DISABLE_LIVE_GEMINI", "0").strip().lower()
    return val in ("1", "true", "yes", "on")


def ensure_env_loaded() -> None:
    """
    Ensure project-root .env is loaded without overriding existing environment variables.
    Preserves explicitly set test flags (e.g. DISABLE_LIVE_GEMINI) and process-level overrides.
    """
    try:
        from dotenv import load_dotenv

        _project_root = Path(__file__).resolve().parent.parent
        _env_file = _project_root / ".env"
        if _env_file.exists():
            load_dotenv(dotenv_path=_env_file, override=False)
        else:
            load_dotenv(override=False)
    except ImportError:
        pass


# Run initial safe load on module import
ensure_env_loaded()

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_GEMINI_TIMEOUT = 30.0
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

REASON_NON_HERITAGE = "non_heritage"
REASON_INSUFFICIENT_EVIDENCE = "insufficient_visual_evidence"

VISUAL_CATEGORIES = (
    "clearly_identifiable_heritage",
    "possible_heritage_insufficient_evidence",
    "generic_natural_rock_or_sandstone",
    "generic_building_or_wall",
    "landscape_without_identifiable_monument",
    "non_heritage_object",
    "closeup_texture_or_detail",
    "blurry_or_unusable",
    "unknown",
    "service_unavailable",
)

GEMINI_VISION_PROMPT = """Analyze this image to determine whether it contains sufficient distinctive architectural evidence to reliably identify a specific cultural heritage monument.

First classify the visual subject into one "visual_category":
- "clearly_identifiable_heritage": distinctive architectural structure clearly visible with sufficient unique features.
- "possible_heritage_insufficient_evidence": structure or ruin visible but lacking distinctive features to confirm identity.
- "generic_natural_rock_or_sandstone": natural rock, cliffs, boulders, or sandstone formations without carved monument architecture.
- "generic_building_or_wall": ordinary masonry, plain brick/stone wall, or modern building.
- "landscape_without_identifiable_monument": natural scenery, mountains, forest, desert, or water without an identifiable monument.
- "non_heritage_object": modern vehicle, everyday object, animal, person, or furniture.
- "closeup_texture_or_detail": close-up texture, surface material, or unidentifiable fragment.
- "blurry_or_unusable": severely degraded, dark, or out-of-focus image.
- "unknown": ambiguous or unrecognized visual subject.

Mandatory Evidence Rules:
1. Specific monuments must ONLY be identified if "visual_category" is "clearly_identifiable_heritage" with distinctive architectural evidence.
   - For Petra: require distinctive carved Nabataean monumental facades (e.g. Al-Khazneh columns, capitals, pediment, urn). Generic red/pink sandstone or rock canyon alone is STRICTLY INSUFFICIENT.
   - For Taj Mahal: require distinctive Mughal dome and minarets. Generic white marble or arch alone is STRICTLY INSUFFICIENT.
   - For Colosseum: require multi-tiered elliptical Roman amphitheatre arcades. Generic stone arches alone are STRICTLY INSUFFICIENT.
   - For Machu Picchu: require distinctive Inca dry-stone terraced ruins. Generic mountain scenery alone is STRICTLY INSUFFICIENT.
2. If "visual_category" is ANY OTHER CATEGORY (e.g. generic rock, sandstone, wall, landscape, close-up texture, insufficient evidence):
   Set "unknown": true, "is_heritage": false, "site_name": null, "confidence": 0.0, "evidence_tier": "insufficient", and explain clearly in "visual_evidence" why evidence is insufficient. Do NOT speculate or guess based on color or texture.
3. Confidence & Evidence Tiers:
   For confirmed monuments: "evidence_tier" can be "substantial" (confidence 0.80-0.88) or "moderate" (confidence 0.65-0.79). Never assign 0.95-1.00.
   For unconfirmed/insufficient evidence: "evidence_tier" must be "insufficient" (confidence 0.0).

Respond strictly with valid JSON:
{
  "visual_category": "clearly_identifiable_heritage",
  "unknown": false,
  "is_heritage": true,
  "site_name": "Monument Name or null",
  "country_or_region": "Country or Region or null",
  "city": "City or null",
  "country": "Country or null",
  "confidence": 0.85,
  "evidence_tier": "substantial",
  "visual_evidence": "1-2 concise sentences describing visible distinctive architectural features, or reasons why evidence is insufficient.",
  "uncertainty": null,
  "alternatives": [],
  "limitations": null,
  "historical_period": "Approximate dynasty or era (or null)",
  "founder_built_by": "Ruler, patron, or culture (or null)",
  "architectural_style": "Recognized architectural tradition (or null)",
  "significance": "1-2 concise sentences on historical or cultural importance (or null)",
  "interesting_facts": ["2-3 factual highlights"]
}
Raw JSON only. No markdown formatting."""


class GeminiVisionResult(BaseModel):
    """Structured response from Google Gemini vision identification."""

    unknown: bool = Field(
        default=True,
        description="True if unknown or unidentified, False ONLY if confidently identified.",
    )
    identified: bool = Field(
        default=False,
        description="Whether the monument was confidently identified.",
    )
    site_name: Optional[str] = Field(
        default=None,
        description="Name of the monument or None.",
    )
    country_or_region: Optional[str] = Field(
        default=None,
        description="Country or region where monument is located or None.",
    )
    city: Optional[str] = Field(
        default=None,
        description="City where monument is located or None.",
    )
    country: Optional[str] = Field(
        default=None,
        description="Country where monument is located or None.",
    )
    visual_category: str = Field(
        default="unknown",
        description="Visual classification category.",
    )
    evidence_tier: str = Field(
        default="insufficient",
        description="Qualitative evidence tier: substantial, moderate, limited, or insufficient.",
    )
    visual_evidence: str = Field(
        default="",
        description="Visual features and evidence observed in the image.",
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence score between 0.0 and 1.0 (estimated, not calibrated).",
    )
    uncertainty: Optional[str] = Field(
        default=None,
        description="Any uncertainty notes or null.",
    )
    alternatives: list[str] = Field(
        default_factory=list,
        description="Alternative candidate sites or possibilities.",
    )
    limitations: Optional[str] = Field(
        default=None,
        description="Limitations of the visual analysis.",
    )
    reason: str = Field(
        default="",
        description="Reason for the decision or visual explanation.",
    )
    uncertain: bool = Field(
        default=True,
        description="True if uncertain or unidentified, False ONLY if confidently identified.",
    )
    is_heritage: bool = Field(
        default=False,
        description=(
            "True ONLY when the identified place is a genuine heritage monument/site."
        ),
    )
    explicit_non_heritage: bool = Field(
        default=False,
        description=(
            "True ONLY when the vision model explicitly classified the image as non-heritage."
        ),
    )
    historical_period: Optional[str] = Field(
        default=None,
        description="Approximate construction period or dynasty.",
    )
    founder_built_by: Optional[str] = Field(
        default=None,
        description="The ruler, patron, or culture that built it.",
    )
    architectural_style: Optional[str] = Field(
        default=None,
        description="The recognized architectural tradition.",
    )
    significance: Optional[str] = Field(
        default=None,
        description="1-2 sentences on why the site matters historically/culturally.",
    )
    interesting_facts: list[str] = Field(
        default_factory=list,
        description="3-5 well-established factual highlights.",
    )
    status: Optional[str] = Field(
        default=None,
        description="Recognition or error status.",
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Error classification type if request failed or was unavailable.",
    )

    @model_validator(mode="before")
    @classmethod
    def _reconcile_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)

        # 1. visual_category reconciliation
        if "visual_category" in d and d["visual_category"]:
            raw_cat = str(d["visual_category"]).strip().lower()
            if raw_cat not in VISUAL_CATEGORIES:
                raw_cat = "unknown"
        elif d.get("unknown") is False and d.get("is_heritage") is True and d.get("site_name"):
            raw_cat = "clearly_identifiable_heritage"
        else:
            raw_cat = "unknown"
        d["visual_category"] = raw_cat

        # If visual category is not clearly identifiable heritage, force unknown
        if raw_cat != "clearly_identifiable_heritage":
            d["unknown"] = True
            d["identified"] = False
            d["is_heritage"] = False
            d["site_name"] = None
            d["confidence"] = 0.0
            if d.get("evidence_tier") != "unavailable":
                d["evidence_tier"] = "insufficient"
            if not d.get("visual_evidence") and not d.get("reason"):
                d["visual_evidence"] = f"Insufficient visual evidence: image classified as {raw_cat.replace('_', ' ')}."
                d["reason"] = d["visual_evidence"]

        # 2. unknown vs identified vs uncertain
        if "unknown" in d and d["unknown"] is not None:
            is_unk = bool(d["unknown"])
            d["unknown"] = is_unk
            if "identified" not in d or d["identified"] is None:
                d["identified"] = not is_unk
            if "uncertain" not in d or d["uncertain"] is None:
                d["uncertain"] = is_unk
        elif "identified" in d and d["identified"] is not None:
            is_id = bool(d["identified"])
            d["identified"] = is_id
            if "unknown" not in d or d["unknown"] is None:
                d["unknown"] = not is_id
            if "uncertain" not in d or d["uncertain"] is None:
                d["uncertain"] = not is_id
        elif "uncertain" in d and d["uncertain"] is not None:
            is_unc = bool(d["uncertain"])
            d["uncertain"] = is_unc
            d.setdefault("unknown", is_unc)
            d.setdefault("identified", not is_unc)

        # 3. visual_evidence vs reason
        ve = d.get("visual_evidence")
        r = d.get("reason")
        if ve and not r:
            d["reason"] = str(ve)
        elif r and not ve:
            d["visual_evidence"] = str(r)

        # 4. country_or_region vs country / city
        cor = d.get("country_or_region")
        c = d.get("country")
        ct = d.get("city")
        if not cor:
            if ct and c:
                d["country_or_region"] = f"{ct}, {c}"
            else:
                d["country_or_region"] = c or ct
        elif not c and cor:
            if "," in cor:
                part1, _, part2 = cor.rpartition(",")
                d["city"] = d.get("city") or part1.strip()
                d["country"] = part2.strip()
            else:
                d["country"] = cor.strip()

        # 5. alternatives
        alts = d.get("alternatives")
        if alts is None:
            d["alternatives"] = []
        elif isinstance(alts, str):
            d["alternatives"] = [alts] if alts.strip() else []

        # 6. interesting_facts
        facts = d.get("interesting_facts")
        if facts is None:
            d["interesting_facts"] = []
        elif isinstance(facts, str):
            d["interesting_facts"] = [facts] if facts.strip() else []

        # 7. confidence clamping & qualitative tier calibration
        conf = d.get("confidence")
        if conf is not None:
            try:
                conf_val = float(conf)
                # Uncalibrated confidence protection: clamp between 0.0 and 0.88 max
                d["confidence"] = max(0.0, min(0.88, conf_val))
            except (ValueError, TypeError):
                d["confidence"] = 0.0
        else:
            d["confidence"] = 0.0

        if d.get("unknown") or not d.get("is_heritage"):
            d["confidence"] = 0.0
            if d.get("evidence_tier") != "unavailable":
                d["evidence_tier"] = "insufficient"
        else:
            tier = str(d.get("evidence_tier") or "").strip().lower()
            if tier not in ("substantial", "moderate", "limited"):
                d["evidence_tier"] = "substantial" if d["confidence"] >= 0.80 else "moderate"
            else:
                d["evidence_tier"] = tier

        return d

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict matching global_identification shape expected by frontend."""
        return {
            "unknown": self.unknown,
            "identified": self.identified,
            "site_name": self.site_name,
            "country_or_region": self.country_or_region,
            "city": self.city,
            "country": self.country,
            "visual_category": self.visual_category,
            "evidence_tier": self.evidence_tier,
            "visual_evidence": self.visual_evidence,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "alternatives": list(self.alternatives),
            "limitations": self.limitations,
            "reason": self.reason,
            "uncertain": self.uncertain,
            "is_heritage": self.is_heritage,
            "explicit_non_heritage": self.explicit_non_heritage,
            "historical_period": self.historical_period,
            "founder_built_by": self.founder_built_by,
            "architectural_style": self.architectural_style,
            "significance": self.significance,
            "interesting_facts": list(self.interesting_facts),
            "status": self.status,
            "error_type": self.error_type,
        }


def fallback_unknown_result(
    reason: str = "Monument not identified",
    visual_category: str = "unknown",
    error_type: Optional[str] = None,
    status: Optional[str] = None,
    evidence_tier: Optional[str] = "insufficient",
) -> GeminiVisionResult:
    """Return a safe unconfirmed result representing unknown or failed recognition."""
    if error_type == "service_unavailable" or status == "external_service_unavailable":
        evidence_tier = "unavailable"
        uncertainty = "Service temporarily unavailable"
    elif error_type in ("rate_limited", "timeout", "authentication", "network_error"):
        evidence_tier = "unavailable"
        uncertainty = f"Service {error_type}"
    else:
        uncertainty = "Unknown or unverified"

    return GeminiVisionResult(
        unknown=True,
        identified=False,
        site_name=None,
        country_or_region=None,
        city=None,
        country=None,
        visual_category=visual_category,
        evidence_tier=evidence_tier,
        visual_evidence=reason,
        confidence=0.0,
        uncertainty=uncertainty,
        alternatives=[],
        limitations=None if not error_type else f"External vision unavailable ({error_type})",
        reason=reason,
        uncertain=True,
        is_heritage=False,
        explicit_non_heritage=False,
        historical_period=None,
        founder_built_by=None,
        architectural_style=None,
        significance=None,
        interesting_facts=[],
        status=status,
        error_type=error_type,
    )


def detect_mime_type_and_base64(image: Union[bytes, str, Path]) -> tuple[str, str]:
    """
    Given raw bytes, a filepath, or base64 data string, return (mime_type, base64_string).
    """
    if isinstance(image, (str, Path)):
        s_val = str(image)
        if s_val.startswith("data:"):
            header, _, b64_data = s_val.partition(",")
            mime = "image/jpeg"
            if ";" in header:
                mime_part = header[5:].split(";")[0].strip().lower()
                if mime_part:
                    mime = mime_part
            return mime, b64_data.strip()

        # Check if it is a file path
        p = Path(image)
        if p.exists() and p.is_file():
            raw_bytes = p.read_bytes()
            ext = p.suffix.lower()
            mime = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
                ".gif": "image/gif",
            }.get(ext, "image/jpeg")
            b64_str = base64.b64encode(raw_bytes).decode("utf-8")
            return mime, b64_str

        # Plain base64 string
        cleaned = re.sub(r"\s+", "", s_val)
        return "image/jpeg", cleaned

    if isinstance(image, (bytes, bytearray)):
        b = bytes(image)
        mime = "image/jpeg"
        if b.startswith(b"\xff\xd8\xff"):
            mime = "image/jpeg"
        elif b.startswith(b"\x89PNG\r\n\x1a\n"):
            mime = "image/png"
        elif b.startswith(b"RIFF") and len(b) > 12 and b[8:12] == b"WEBP":
            mime = "image/webp"
        b64_str = base64.b64encode(b).decode("utf-8")
        return mime, b64_str

    raise ValueError(f"Unsupported image type: {type(image).__name__}")


def prepare_gemini_image(
    image: Union[bytes, bytearray, str, Path],
    max_edge: int = 1024,
    quality: int = 85,
) -> Tuple[str, str, int, str]:
    """
    Prepare an optimized, standardized image payload for Gemini Vision fallback.

    - Resolves raw image bytes from bytes, filepath, or base64 data URL.
    - Computes SHA-256 hash over original bytes for bounded memory caching.
    - Applies EXIF orientation transposition to avoid orientation artifacts.
    - Converts RGBA/paletted images to RGB.
    - Resizes high-resolution images keeping aspect ratio so longest edge <= max_edge.
    - Compresses in-memory to JPEG at calibrated quality (85) to eliminate network lag.

    Returns
    -------
    tuple[str, str, int, str]
        (mime_type, base64_str, byte_len, sha256_hash)
    """
    raw_bytes: bytes = b""
    if isinstance(image, (str, Path)):
        s_val = str(image)
        if s_val.startswith("data:"):
            _, _, b64_data = s_val.partition(",")
            try:
                raw_bytes = base64.b64decode(b64_data)
            except Exception:
                raw_bytes = b64_data.encode("ascii")
        else:
            p = Path(image)
            if p.exists() and p.is_file():
                raw_bytes = p.read_bytes()
            else:
                try:
                    cleaned = re.sub(r"\s+", "", s_val)
                    raw_bytes = base64.b64decode(cleaned)
                except Exception:
                    raw_bytes = s_val.encode("utf-8")
    elif isinstance(image, (bytes, bytearray)):
        raw_bytes = bytes(image)
    else:
        raise ValueError(f"Unsupported image type: {type(image).__name__}")

    raw_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Attempt PIL optimization
    try:
        with Image.open(io.BytesIO(raw_bytes)) as pil_img:
            pil_img = ImageOps.exif_transpose(pil_img)
            if pil_img.mode in ("RGBA", "P"):
                pil_img = pil_img.convert("RGB")

            w, h = pil_img.size
            longest = max(w, h)
            if longest > max_edge:
                scale = max_edge / longest
                new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
                pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=quality, optimize=True)
            opt_bytes = buf.getvalue()
            b64_str = base64.b64encode(opt_bytes).decode("ascii")
            return "image/jpeg", b64_str, len(opt_bytes), raw_hash
    except Exception as exc:
        logger.debug("PIL optimization bypassed or failed (%s); falling back to direct encoding", exc)
        mime, b64_str = detect_mime_type_and_base64(raw_bytes)
        return mime, b64_str, len(raw_bytes), raw_hash


class GeminiVisionClient:
    """
    Async client for Google Gemini Vision models.

    Handles structured JSON generation, authentication, timeouts, persistent
    connection pooling, in-flight deduplication, and safe in-memory caching.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_GEMINI_TIMEOUT,
        transport: Optional[httpx.AsyncBaseTransport] = None,
        max_cache_size: int = 64,
        thinking_level: Optional[str] = None,
    ):
        self._transport = transport
        self.live_disabled = is_live_gemini_disabled()

        if api_key is not None:
            self.api_key = api_key
        elif self.live_disabled and self._transport is None:
            # Test safety safeguard: live external calls disabled and no mock transport provided.
            # Do not load or expose live production credentials.
            self.api_key = None
        else:
            # Normal mode or mocked transport mode:
            # Read from environment, loading project-root .env if not yet in os.environ.
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                ensure_env_loaded()
                key = os.getenv("GEMINI_API_KEY")
            # If in mock transport test mode and no key provided, supply safe dummy key for mock tests
            if not key and self._transport is not None:
                key = "mock-test-key"
            self.api_key = key

        self.model = (
            model
            if model is not None
            else os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        )
        try:
            self.timeout = float(os.getenv("GEMINI_TIMEOUT", timeout))
        except (ValueError, TypeError):
            self.timeout = timeout

        self.thinking_level = (
            thinking_level
            if thinking_level is not None
            else os.getenv("GEMINI_THINKING_LEVEL", "MINIMAL")
        )
        if self.thinking_level:
            self.thinking_level = self.thinking_level.upper()

        self._transport = transport
        self.endpoint_url = f"{GEMINI_API_BASE_URL}/{self.model}:generateContent"

        # Performance optimizations
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: OrderedDict[str, GeminiVisionResult] = OrderedDict()
        self._in_flight: Dict[str, asyncio.Task[GeminiVisionResult]] = {}
        self._max_cache_size = max_cache_size

    def __repr__(self) -> str:
        key_status = "configured" if self.api_key else "missing"
        return (
            f"<GeminiVisionClient model={self.model!r} "
            f"api_key={key_status} live_disabled={self.live_disabled} "
            f"has_custom_transport={self._transport is not None}>"
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Return or initialize persistent httpx.AsyncClient with HTTP connection pooling."""
        if self._client is None or self._client.is_closed:
            client_kwargs: Dict[str, Any] = {
                "timeout": self.timeout,
                "limits": httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                    keepalive_expiry=60.0,
                ),
            }
            if self._transport is not None:
                client_kwargs["transport"] = self._transport
            self._client = httpx.AsyncClient(**client_kwargs)
        return self._client

    async def close(self) -> None:
        """Close persistent HTTP connection pool and clear cached resources."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        self._cache.clear()
        self._in_flight.clear()

    async def __aenter__(self) -> "GeminiVisionClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers without exposing the API key in representation."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-goog-api-key"] = self.api_key
        return headers

    def _parse_response_payload(self, text: str) -> GeminiVisionResult:
        """Parse Gemini response body and extract structured GeminiVisionResult."""
        try:
            outer = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Gemini response body is not valid JSON")
            return fallback_unknown_result(reason="Malformed response from Gemini API")

        # Extract text from candidates[0].content.parts[0].text
        candidates = outer.get("candidates") if isinstance(outer, dict) else None
        if not candidates or not isinstance(candidates, list) or len(candidates) == 0:
            prompt_feedback = outer.get("promptFeedback") if isinstance(outer, dict) else None
            reason = "No candidate returned by Gemini"
            if prompt_feedback and "blockReason" in prompt_feedback:
                reason = f"Gemini content blocked: {prompt_feedback['blockReason']}"
            return fallback_unknown_result(reason=reason)

        first_cand = candidates[0]
        content = first_cand.get("content", {})
        parts = content.get("parts", [])
        raw_text = parts[0].get("text", "") if parts and isinstance(parts[0], dict) else ""

        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            parsed_data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning("Gemini candidate content could not be parsed as JSON: %s", exc)
            return fallback_unknown_result(reason="Malformed JSON response from Gemini model")

        if not isinstance(parsed_data, dict):
            return fallback_unknown_result(
                reason="Malformed JSON response from Gemini model (expected object)"
            )

        try:
            result = GeminiVisionResult.model_validate(parsed_data)
        except Exception as exc:
            logger.warning("Gemini response failed schema validation: %s", exc)
            return fallback_unknown_result(reason="Malformed JSON response from Gemini")

        # Normalize unknown states
        if result.unknown or not result.identified:
            return fallback_unknown_result(
                reason=result.reason or result.visual_evidence or "Insufficient visual evidence to identify a monument",
                visual_category=result.visual_category,
            )

        # Enforce visual category check
        if result.visual_category != "clearly_identifiable_heritage":
            return fallback_unknown_result(
                reason=f"Insufficient visual evidence: image classified as {result.visual_category.replace('_', ' ')}.",
                visual_category=result.visual_category,
            )

        # Strict evidence validation for known high-risk false-positive candidates:
        name_lower = (result.site_name or "").lower()
        evidence_lower = (result.visual_evidence or "").lower()

        # Petra validation: require distinctive carved Nabataean architectural facade
        if "petra" in name_lower:
            petra_arch_features = (
                "facade", "carve", "column", "pediment", "khazneh", "treasury",
                "capital", "urn", "rock-cut architecture", "monastery", "ad deir", "tomb"
            )
            has_petra_arch = any(feat in evidence_lower for feat in petra_arch_features)
            has_only_rock = any(w in evidence_lower for w in ("sandstone texture", "natural rock", "rock formation", "red rock", "cliff face", "only sandstone", "canyon wall"))
            if not has_petra_arch or (has_only_rock and not has_petra_arch):
                logger.warning("Rejected false positive Petra identification: lacking distinctive carved architectural facade")
                return fallback_unknown_result(
                    reason="Insufficient visual evidence: generic reddish sandstone or rock canyon without distinctive carved Nabataean monumental architecture.",
                    visual_category="generic_natural_rock_or_sandstone",
                )

        # Taj Mahal validation: require distinctive Mughal dome / minarets / symmetry
        if "taj mahal" in name_lower:
            taj_features = ("dome", "minaret", "mausoleum", "iwan", "symmetry", "plinth")
            if not any(feat in evidence_lower for feat in taj_features):
                logger.warning("Rejected false positive Taj Mahal identification: lacking distinctive Mughal architectural features")
                return fallback_unknown_result(
                    reason="Insufficient visual evidence: lacking distinctive Mughal dome, minarets, or symmetric architectural features.",
                    visual_category="generic_building_or_wall",
                )

        # Colosseum validation: require distinctive Roman amphitheatre arcade features
        if "colosseum" in name_lower:
            colosseum_features = ("amphitheatre", "arcade", "arch", "tier", "arena", "elliptical", "flavian")
            if not any(feat in evidence_lower for feat in colosseum_features):
                logger.warning("Rejected false positive Colosseum identification: lacking distinctive Roman amphitheatre arcade features")
                return fallback_unknown_result(
                    reason="Insufficient visual evidence: lacking distinctive multi-tiered Roman amphitheatre arcades.",
                    visual_category="generic_building_or_wall",
                )

        # Machu Picchu validation: require distinctive Inca archaeological ruins
        if "machu picchu" in name_lower:
            mp_features = ("terrace", "dry-stone", "ruin", "citadel", "inca", "enclosure", "huayna picchu")
            if not any(feat in evidence_lower for feat in mp_features):
                logger.warning("Rejected false positive Machu Picchu identification: lacking distinctive Inca archaeological structures")
                return fallback_unknown_result(
                    reason="Insufficient visual evidence: natural mountain scenery without distinctive Inca archaeological terraces or stone enclosures.",
                    visual_category="landscape_without_identifiable_monument",
                )

        # A non-heritage landmark is not a confirmed heritage site
        if not result.is_heritage:
            return GeminiVisionResult(
                unknown=True,
                identified=False,
                site_name=None,
                country_or_region=None,
                city=None,
                country=None,
                visual_category=result.visual_category,
                evidence_tier="insufficient",
                visual_evidence=result.visual_evidence or result.reason or REASON_NON_HERITAGE,
                confidence=0.0,
                uncertainty="Non-heritage structure",
                alternatives=list(result.alternatives),
                limitations=result.limitations,
                reason=result.reason or result.visual_evidence or REASON_NON_HERITAGE,
                uncertain=True,
                is_heritage=False,
                explicit_non_heritage=True,
            )

        return GeminiVisionResult(
            unknown=False,
            identified=True,
            site_name=result.site_name,
            country_or_region=result.country_or_region,
            city=result.city,
            country=result.country,
            visual_category=result.visual_category,
            evidence_tier=result.evidence_tier,
            visual_evidence=result.visual_evidence or result.reason,
            confidence=result.confidence,
            uncertainty=result.uncertainty,
            alternatives=list(result.alternatives),
            limitations=result.limitations,
            reason=result.reason or result.visual_evidence,
            uncertain=False,
            is_heritage=True,
            historical_period=result.historical_period or None,
            founder_built_by=result.founder_built_by or None,
            architectural_style=result.architectural_style or None,
            significance=result.significance or None,
            interesting_facts=list(result.interesting_facts or []),
        )

    async def identify_monument(
        self,
        image: Union[bytes, str, Path],
    ) -> GeminiVisionResult:
        """
        Identify a monument globally using Google Gemini Vision.

        Parameters
        ----------
        image : bytes | str | Path
            Raw image bytes, image filepath, or base64 data string.

        Returns
        -------
        GeminiVisionResult
            Parsed structured identification or safe unknown fallback.
        """
        # 1. Guard against live external calls if test safety flag is active
        if self.live_disabled and self._transport is None:
            logger.info("Live Gemini API call blocked by DISABLE_LIVE_GEMINI=1 test safeguard")
            return fallback_unknown_result(
                reason="Live Gemini API calls disabled (DISABLE_LIVE_GEMINI=1)",
                visual_category="unknown",
                error_type="live_calls_disabled",
                status="external_service_unavailable",
                evidence_tier="unavailable",
            )

        # 2. Check for missing API key
        if not self.api_key:
            logger.warning("Gemini Vision requested but GEMINI_API_KEY is not set")
            return fallback_unknown_result(
                reason="Missing GEMINI_API_KEY",
                visual_category="unknown",
                error_type="missing_api_key",
                status="external_auth_error",
                evidence_tier="unavailable",
            )

        # 2. Encode and optimize image (resolves EXIF, resizes to <=1024px, JPEG 85)
        try:
            mime_type, b64_image, byte_len, image_hash = prepare_gemini_image(image)
        except Exception as exc:
            logger.warning("Failed to prepare image for Gemini Vision: %s", exc)
            return fallback_unknown_result(reason="Failed to encode query image")

        # 3. Check memory cache (instant response for exact duplicate images)
        if image_hash and image_hash in self._cache:
            logger.info("Serving Gemini identification from memory cache: %s", image_hash[:10])
            cached = self._cache[image_hash]
            self._cache.move_to_end(image_hash)
            return cached

        # 4. In-flight request deduplication (prevent duplicate API calls for simultaneous requests)
        if image_hash and image_hash in self._in_flight:
            logger.info("Awaiting in-flight Gemini identification for hash %s", image_hash[:10])
            try:
                return await self._in_flight[image_hash]
            except Exception:
                pass

        # 5. Create task and execute
        task = asyncio.create_task(
            self._execute_api_request(mime_type, b64_image, byte_len)
        )
        if image_hash:
            self._in_flight[image_hash] = task

        try:
            result = await task
            # 6. Cache only genuine, successful heritage matches
            if (
                image_hash
                and result.identified
                and result.is_heritage
                and not result.unknown
            ):
                self._cache[image_hash] = result
                if len(self._cache) > self._max_cache_size:
                    self._cache.popitem(last=False)
            return result
        finally:
            if image_hash:
                self._in_flight.pop(image_hash, None)

    async def _execute_api_request(
        self,
        mime_type: str,
        b64_image: str,
        byte_len: int,
    ) -> GeminiVisionResult:
        """Execute the actual network request to Gemini API with timeout and error handling."""
        if self.live_disabled and self._transport is None:
            logger.info("Direct API request blocked by DISABLE_LIVE_GEMINI=1 test safeguard")
            return fallback_unknown_result(
                reason="Live Gemini API calls disabled (DISABLE_LIVE_GEMINI=1)",
                visual_category="unknown",
                error_type="live_calls_disabled",
                status="external_service_unavailable",
                evidence_tier="unavailable",
            )

        generation_config: Dict[str, Any] = {
            "temperature": 0.1,
            "response_mime_type": "application/json",
            "maxOutputTokens": 800,
        }
        if self.thinking_level and self.thinking_level in ("MINIMAL", "LOW", "MEDIUM", "HIGH"):
            generation_config["thinkingConfig"] = {
                "thinkingLevel": self.thinking_level
            }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": GEMINI_VISION_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_image,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": generation_config,
        }

        headers = self._build_headers()

        overall_start = time.monotonic()
        overall_deadline = overall_start + self.timeout
        max_transient_retries = 1
        attempt = 0

        while attempt <= max_transient_retries:
            attempt += 1
            now = time.monotonic()
            remaining_time = overall_deadline - now
            if remaining_time <= 0.5:
                logger.warning(
                    "Gemini API deadline expired before attempt %d dispatch (%.2fs remaining)",
                    attempt,
                    remaining_time,
                )
                return fallback_unknown_result(
                    reason="Gemini request deadline expired",
                    error_type="timeout",
                    status="external_timeout",
                    evidence_tier="unavailable",
                )

            req_timeout = min(self.timeout, remaining_time)
            req_start = time.monotonic()

            try:
                client = await self._get_client()
                response = await client.post(
                    self.endpoint_url,
                    json=payload,
                    headers=headers,
                    timeout=req_timeout,
                )
                elapsed = time.monotonic() - req_start
                status = response.status_code

                # Redacted response text snippet for diagnostic logging (max 200 chars)
                body_snippet = (response.text or "")[:200].replace("\r", " ").replace("\n", " ").strip()

                if status == 200:
                    logger.info("Gemini API request succeeded (HTTP 200) in %.2fs", elapsed)
                    return self._parse_response_payload(response.text)

                if status in (503, 502, 504):
                    logger.warning(
                        "Gemini transient server error (HTTP %d) in %.2fs (attempt %d/%d). Response snippet: %s",
                        status,
                        elapsed,
                        attempt,
                        max_transient_retries + 1,
                        body_snippet,
                    )
                    if attempt <= max_transient_retries:
                        # Bounded exponential backoff with jitter
                        backoff = 1.0 * (1.5 ** (attempt - 1)) + random.uniform(0.1, 0.4)
                        now_post = time.monotonic()
                        if now_post + backoff + 1.0 < overall_deadline:
                            logger.info(
                                "Retrying Gemini API request in %.2fs (attempt %d/%d) due to transient HTTP %d",
                                backoff,
                                attempt,
                                max_transient_retries,
                                status,
                            )
                            try:
                                await asyncio.sleep(backoff)
                                continue
                            except asyncio.CancelledError:
                                logger.info("Gemini retry cancelled by caller during backoff")
                                raise
                        else:
                            logger.warning(
                                "Insufficient time remaining (%.2fs) to retry Gemini request after HTTP %d",
                                overall_deadline - now_post,
                                status,
                            )

                    # Exhausted or insufficient time:
                    logger.warning(
                        "Gemini service unavailable after %d attempt(s) (HTTP %d)",
                        attempt,
                        status,
                    )
                    return fallback_unknown_result(
                        reason=f"Gemini server error (HTTP {status})",
                        error_type="service_unavailable",
                        status="external_service_unavailable",
                        evidence_tier="unavailable",
                        visual_category="service_unavailable",
                    )

                if status == 429:
                    logger.warning(
                        "Gemini rate limit reached (HTTP 429) in %.2fs. Response snippet: %s",
                        elapsed,
                        body_snippet,
                    )
                    return fallback_unknown_result(
                        reason="Gemini rate limit exceeded (HTTP 429)",
                        error_type="rate_limited",
                        status="external_rate_limited",
                        evidence_tier="unavailable",
                    )

                if status in (401, 403):
                    logger.warning(
                        "Gemini authentication/authorization failed (HTTP %d) in %.2fs",
                        status,
                        elapsed,
                    )
                    reason = "Gemini authentication failed (HTTP 401)" if status == 401 else "Gemini access denied (HTTP 403)"
                    return fallback_unknown_result(
                        reason=reason,
                        error_type="authentication",
                        status="external_auth_error",
                        evidence_tier="unavailable",
                    )

                if status == 400:
                    logger.warning(
                        "Gemini invalid request (HTTP 400) in %.2fs. Response snippet: %s",
                        elapsed,
                        body_snippet,
                    )
                    return fallback_unknown_result(
                        reason="Gemini invalid request (HTTP 400)",
                        error_type="invalid_request",
                        status="external_invalid_request",
                        evidence_tier="unavailable",
                    )

                if status >= 500:
                    logger.warning(
                        "Gemini server error (HTTP %d) in %.2fs. Response snippet: %s",
                        status,
                        elapsed,
                        body_snippet,
                    )
                    return fallback_unknown_result(
                        reason=f"Gemini server error (HTTP {status})",
                        error_type="server_error",
                        status="external_server_error",
                        evidence_tier="unavailable",
                    )

                logger.warning(
                    "Gemini request failed with HTTP %d in %.2fs. Response snippet: %s",
                    status,
                    elapsed,
                    body_snippet,
                )
                return fallback_unknown_result(
                    reason=f"Gemini request failed with HTTP {status}",
                    error_type="request_failed",
                    status="external_request_failed",
                    evidence_tier="unavailable",
                )

            except asyncio.CancelledError:
                logger.info("Gemini vision request cancelled by caller")
                raise
            except httpx.TimeoutException:
                elapsed = time.monotonic() - req_start
                logger.warning("Gemini vision request timed out after %.2fs", elapsed)
                return fallback_unknown_result(
                    reason=f"Gemini request timed out after {elapsed:.1f}s",
                    error_type="timeout",
                    status="external_timeout",
                    evidence_tier="unavailable",
                )
            except (httpx.ConnectError, httpx.NetworkError) as exc:
                elapsed = time.monotonic() - req_start
                logger.warning(
                    "Failed to connect to Gemini API endpoint in %.2fs: %s",
                    elapsed,
                    type(exc).__name__,
                )
                return fallback_unknown_result(
                    reason="Could not connect to Gemini service",
                    error_type="network_error",
                    status="external_network_error",
                    evidence_tier="unavailable",
                )
            except Exception as exc:
                elapsed = time.monotonic() - req_start
                logger.warning("Gemini vision query failed in %.2fs: %s", elapsed, type(exc).__name__)
                return fallback_unknown_result(
                    reason=f"Gemini vision request failed: {type(exc).__name__}",
                    error_type="unknown_error",
                    status="external_unknown_error",
                    evidence_tier="unavailable",
                )

        return fallback_unknown_result(
            reason="Gemini retries exhausted",
            error_type="service_unavailable",
            status="external_service_unavailable",
            evidence_tier="unavailable",
        )

