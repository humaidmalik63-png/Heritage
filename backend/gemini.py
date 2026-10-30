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

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import httpx
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_GEMINI_TIMEOUT = 30.0
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

REASON_NON_HERITAGE = "non_heritage"

GEMINI_VISION_PROMPT = """Analyze this image and determine whether it depicts a GENUINE heritage site, historic monument, ancient temple, fort, palace, archaeological site, sacred site, rock-cut cave monument, or UNESCO World Heritage site.

You must respond with valid JSON strictly matching this schema:
{
  "unknown": boolean,
  "site_name": string or null,
  "country_or_region": string or null,
  "city": string or null,
  "country": string or null,
  "visual_evidence": string,
  "confidence": number between 0.0 and 1.0,
  "uncertainty": string or null,
  "alternatives": [string, ...],
  "limitations": string or null,
  "is_heritage": boolean,
  "historical_period": string or null,
  "founder_built_by": string or null,
  "architectural_style": string or null,
  "significance": string or null,
  "interesting_facts": [string, ...]
}

Rules:
1. Only set "unknown": false when the image depicts a GENUINE heritage monument or site (historic monument, ancient temple, fort, palace, archaeological site, UNESCO site, sacred site, historic religious building, or rock-cut cave complex including interior shrines and carved halls):
   - "unknown": false
   - "is_heritage": true
   - "site_name": the exact common name of the monument (e.g. "Ajanta Caves", "Hawa Mahal", "Colosseum", "Angkor Wat", "Abu Simbel Temples")
   - "country_or_region": country or region where it is located (e.g. "Egypt", "Maharashtra, India")
   - "city": city or region where it is located (or null)
   - "country": country where it is located (or null)
   - "visual_evidence": 1-3 sentences describing the key visible architectural details, carvings, materials, statues, or distinctive structures identifying it
   - "confidence": estimated confidence score between 0.0 and 1.0
   - "uncertainty": null if certain, or a brief note explaining any uncertainty
   - "alternatives": list of other plausible candidate sites if not 100% certain, or []
   - "limitations": any limitations of the visual analysis (e.g. "Partial view", "Low resolution", "Obscured by crowd") or null
   - "historical_period": approximate construction period or dynasty (e.g. "2nd century BCE - 6th century CE"). Omit if unreliable.
   - "founder_built_by": the ruler, patron, or culture that built it. Omit if unreliable.
   - "architectural_style": the recognized architectural tradition (e.g. "Rock-cut Buddhist architecture", "Mughal architecture"). Omit if unreliable.
   - "significance": 1-2 sentences on why the site matters historically, culturally, or architecturally.
   - "interesting_facts": 3–5 short factual highlights about the monument. Keep them verifiable; do NOT invent claims.
2. If the image depicts an ordinary non-heritage object, modern commercial structure, modern building, vehicle, or everyday scene:
   - "unknown": true, "is_heritage": false
   - "site_name": null, "country_or_region": null, "city": null, "country": null, "confidence": 0.0
   - "visual_evidence": briefly describe what was observed and why it is not a heritage site
   - "alternatives": []
   - "limitations": null
   - Leave all profile fields null/empty.
3. If you cannot identify the structure or place at all:
   - "unknown": true, "is_heritage": false, "site_name": null, "country_or_region": null, "city": null, "country": null, "confidence": 0.0
   - "visual_evidence": brief explanation why it could not be identified
   - "alternatives": []
   - "limitations": describe visual limitations that hindered recognition
   - Leave all profile fields null/empty.
4. Output raw JSON only. Do not include markdown code fences or extra text."""


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

    @model_validator(mode="before")
    @classmethod
    def _reconcile_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)

        # 1. unknown vs identified vs uncertain
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

        # 2. visual_evidence vs reason
        ve = d.get("visual_evidence")
        r = d.get("reason")
        if ve and not r:
            d["reason"] = str(ve)
        elif r and not ve:
            d["visual_evidence"] = str(r)

        # 3. country_or_region vs country / city
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

        # 4. alternatives
        alts = d.get("alternatives")
        if alts is None:
            d["alternatives"] = []
        elif isinstance(alts, str):
            d["alternatives"] = [alts] if alts.strip() else []

        # 5. interesting_facts
        facts = d.get("interesting_facts")
        if facts is None:
            d["interesting_facts"] = []
        elif isinstance(facts, str):
            d["interesting_facts"] = [facts] if facts.strip() else []

        # 6. confidence clamping
        conf = d.get("confidence")
        if conf is not None:
            try:
                conf_val = float(conf)
                d["confidence"] = max(0.0, min(1.0, conf_val))
            except (ValueError, TypeError):
                d["confidence"] = 0.0
        else:
            d["confidence"] = 0.0

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
        }


def fallback_unknown_result(reason: str = "Monument not identified") -> GeminiVisionResult:
    """Return a safe unconfirmed result representing unknown or failed recognition."""
    return GeminiVisionResult(
        unknown=True,
        identified=False,
        site_name=None,
        country_or_region=None,
        city=None,
        country=None,
        visual_evidence=reason,
        confidence=0.0,
        uncertainty="Unknown or unverified",
        alternatives=[],
        limitations=None,
        reason=reason,
        uncertain=True,
        is_heritage=False,
        explicit_non_heritage=False,
        historical_period=None,
        founder_built_by=None,
        architectural_style=None,
        significance=None,
        interesting_facts=[],
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


class GeminiVisionClient:
    """
    Async client for Google Gemini Vision models.

    Handles structured JSON generation, authentication, timeouts, and fail-safe
    error handling without exposing credentials.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_GEMINI_TIMEOUT,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        self.model = (
            model
            if model is not None
            else os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        )
        try:
            self.timeout = float(os.getenv("GEMINI_TIMEOUT", timeout))
        except (ValueError, TypeError):
            self.timeout = timeout

        self._transport = transport
        self.endpoint_url = f"{GEMINI_API_BASE_URL}/{self.model}:generateContent"

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
                reason=result.reason or result.visual_evidence or "Monument not identified"
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
        # 1. Check for missing API key
        if not self.api_key:
            logger.warning("Gemini Vision requested but GEMINI_API_KEY is not set")
            return fallback_unknown_result(reason="Missing GEMINI_API_KEY")

        # 2. Encode image and get MIME type
        try:
            mime_type, b64_image = detect_mime_type_and_base64(image)
        except Exception as exc:
            logger.warning("Failed to encode image for Gemini Vision: %s", exc)
            return fallback_unknown_result(reason="Failed to encode query image")

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
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }

        headers = self._build_headers()

        # 3. Perform HTTP request with strict timeout and safe error handling
        try:
            client_kwargs: Dict[str, Any] = {"timeout": self.timeout}
            if self._transport is not None:
                client_kwargs["transport"] = self._transport

            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.post(
                    self.endpoint_url,
                    json=payload,
                    headers=headers,
                )

            status = response.status_code
            if status == 200:
                return self._parse_response_payload(response.text)

            if status in (401, 403):
                logger.warning("Gemini authentication/authorization failed (HTTP %d)", status)
                reason = "Gemini authentication failed (HTTP 401)" if status == 401 else "Gemini access denied (HTTP 403)"
                return fallback_unknown_result(reason=reason)

            if status == 429:
                logger.warning("Gemini rate limit reached (HTTP 429)")
                return fallback_unknown_result(reason="Gemini rate limit exceeded (HTTP 429)")

            if status >= 500:
                logger.warning("Gemini server error (HTTP %d)", status)
                return fallback_unknown_result(reason=f"Gemini server error (HTTP {status})")

            logger.warning("Gemini request failed with HTTP %d", status)
            return fallback_unknown_result(reason=f"Gemini request failed with HTTP {status}")

        except httpx.TimeoutException:
            logger.warning("Gemini vision request timed out after %.1fs", self.timeout)
            return fallback_unknown_result(reason=f"Gemini request timed out after {self.timeout:.1f}s")
        except (httpx.ConnectError, httpx.NetworkError):
            logger.warning("Failed to connect to Gemini API endpoint")
            return fallback_unknown_result(reason="Could not connect to Gemini service")
        except Exception as exc:
            logger.warning("Gemini vision query failed: %s", type(exc).__name__)
            return fallback_unknown_result(reason=f"Gemini vision request failed: {type(exc).__name__}")

