"""
Ollama Vision client for global heritage monument recognition fallback.

Communicates with Ollama Cloud or local Ollama server to identify monuments
globally when local open-set recognition cannot make a confident identification.

Adheres to strict security rules:
- API key must never be hard-coded or logged.
- Never crashes the caller on network failure, timeout, or malformed response.
- Returns a safe, structured unknown result on any failure.
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
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_BASE_URL = "https://ollama.com/api"
DEFAULT_OLLAMA_VISION_MODEL = "llama3.2-vision"
DEFAULT_OLLAMA_TIMEOUT = 30.0

# Rejection reason used when the global vision fallback identifies a place that
# is NOT a genuine heritage monument/site.  Kept as a module-level constant so
# the service layer can import and assert on it without duplicating the string.
REASON_NON_HERITAGE = "non_heritage"

# Structured prompt instructing Ollama to output strict JSON.
#
# The critical contract here is the ``is_heritage`` flag.  The vision model is
# asked to recognise famous places globally, and many famous places are NOT
# heritage monuments (e.g. modern skyscrapers, public squares, bridges,
# observation towers, beaches, ordinary cityscapes).  Those must be rejected at
# this global-identification layer instead of being presented as confirmed
# heritage sites.  No specific place names are hard-coded anywhere in this
# module; the distinction is purely structural (heritage monument vs. ordinary
# landmark/place/scene).
#
# When the image depicts a genuine heritage monument, the model should also
# provide a structured historical profile.  That profile is NOT a substitute for
# the local evidence records: every claim should be factual and, where possible,
# traceable to a public source (e.g. UNESCO, ASI, national archives).  If the
# model cannot verify a field reliably, it must leave the field empty rather
# than invent one.
OLLAMA_VISION_PROMPT = """Analyze this image and determine whether it depicts a GENUINE heritage site, historic monument, ancient temple, fort, palace, archaeological site, sacred site, or UNESCO World Heritage site.

You must respond with valid JSON strictly matching this schema:
{
  "identified": boolean,
  "site_name": string or null,
  "city": string or null,
  "country": string or null,
  "confidence": number between 0.0 and 1.0,
  "reason": string,
  "uncertain": boolean,
  "is_heritage": boolean,
  "historical_period": string or null,
  "founder_built_by": string or null,
  "architectural_style": string or null,
  "significance": string or null,
  "interesting_facts": [string, ...]
}

Rules:
1. Only set "identified": true when the image depicts a GENUINE heritage monument or site (historic monument, ancient temple, fort, palace, archaeological site, UNESCO site, sacred site, or historic religious building):
   - "identified": true
   - "is_heritage": true
   - "site_name": the exact common name of the monument (e.g. "Hawa Mahal", "Colosseum", "Angkor Wat")
   - "city": city or region where it is located
   - "country": country where it is located
   - "confidence": confidence score (e.g. 0.85)
   - "reason": 1-2 sentences on the key visual features identifying it
   - "uncertain": false
   - "historical_period": approximate construction period or dynasty (e.g. "Mughal Empire (17th century)"). Omit if unreliable.
   - "founder_built_by": the ruler, patron, or culture that built it (e.g. "Shah Jahan", "Eastern Ganga Dynasty"). Omit if unreliable.
   - "architectural_style": the recognized architectural tradition (e.g. "Mughal architecture", "Nagara-style temple"). Omit if unreliable.
   - "significance": 1-2 sentences on why the site matters historically, culturally, or architecturally.
   - "interesting_facts": 3–5 short factual highlights about the monument. Keep them verifiable; do NOT invent claims.
2. If the image depicts a NON-HERITAGE landmark, place, or ordinary scene, set "identified": false and "is_heritage": false. This includes, but is not limited to:
   - modern commercial buildings, skyscrapers, office towers, shopping malls
   - public squares, plazas, streetscapes, bridges, train stations, airports
   - statues, fountains, obelisks, memorials that are not heritage monuments
   - observation towers, Ferris wheels, modern amusement or sports structures
   - natural scenery: beaches, mountains, forests, parks, lakes, waterfalls
   - ordinary cityscapes, roads, vehicles, boats, airplanes, interiors, people
   - any famous place that is primarily a modern commercial, transport, or recreational landmark rather than a historic heritage site
   - "site_name": null, "city": null, "country": null, "confidence": 0.0, "uncertain": true
   - "reason": briefly describe what was observed and why it is NOT a heritage site
   - Leave all other profile fields null/empty.
3. If you cannot identify the structure or place at all (unknown building, blurry image, unrelated scene):
   - "identified": false, "is_heritage": false, "site_name": null, "city": null, "country": null, "confidence": 0.0, "uncertain": true
   - "reason": brief explanation why it could not be identified
   - Leave all other profile fields null/empty.
4. NEVER set "identified": true for a non-heritage landmark. A non-heritage landmark is NOT a confirmed heritage site, even if it is famous.
5. Do NOT guess or fabricate a monument name, dates, or historical claims. When you cannot verify a field, return it as null (not an empty string, not a guess).
6. For "interesting_facts", include only well-established facts that are traceable to public heritage documentation (UNESCO, national archaeological surveys, academic sources). If you are unsure about a fact, omit it.
7. Output raw JSON only. Do not include markdown code blocks or extra text."""


class OllamaVisionResult(BaseModel):
    """Structured response from Ollama vision identification."""

    identified: bool = Field(
        ...,
        description="Whether the monument was confidently identified.",
    )
    site_name: Optional[str] = Field(
        default=None,
        description="Name of the monument or None.",
    )
    city: Optional[str] = Field(
        default=None,
        description="City where monument is located or None.",
    )
    country: Optional[str] = Field(
        default=None,
        description="Country where monument is located or None.",
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence score between 0.0 and 1.0.",
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
            "True ONLY when the identified place is a genuine heritage monument/"
            "site (historic monument, ancient temple, fort, palace, archaeological "
            "site, UNESCO site, sacred site, or historic religious building). "
            "False for any non-heritage landmark, modern structure, or ordinary scene."
        ),
    )
    explicit_non_heritage: bool = Field(
        default=False,
        description=(
            "True ONLY when the vision model EXPLICITLY classified the image as a "
            "non-heritage landmark/place/scene (rather than being unable to "
            "identify it at all).  Used by the service layer to distinguish a "
            "non-heritage rejection from a generic low-similarity/unknown result."
        ),
    )
    # ── optional historical profile (filled only when is_heritage=true) ──────
    historical_period: Optional[str] = Field(
        default=None,
        description="Approximate construction period or dynasty. Omit if unreliable.",
    )
    founder_built_by: Optional[str] = Field(
        default=None,
        description="The ruler, patron, or culture that built it. Omit if unreliable.",
    )
    architectural_style: Optional[str] = Field(
        default=None,
        description="The recognized architectural tradition. Omit if unreliable.",
    )
    significance: Optional[str] = Field(
        default=None,
        description="1-2 sentences on why the site matters historically/culturally.",
    )
    interesting_facts: list[str] = Field(
        default_factory=list,
        description="3-5 well-established factual highlights traceable to public sources.",
    )

    @field_validator("interesting_facts", mode="before")
    @classmethod
    def _null_facts_to_empty(cls, v: Any) -> Any:
        """Accept ``null`` for ``interesting_facts`` and normalise it to ``[]``.

        The vision model emits ``null`` whenever it has no facts to offer.  The
        field is declared ``list[str]``, so that single null previously failed
        ``model_validate`` and discarded the *entire* identification.  Existing
        lists pass through untouched; every other field is unaffected.
        """
        return [] if v is None else v

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (TypeError, ValueError):
            return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation matching the project contract."""
        return {
            "identified": self.identified,
            "site_name": self.site_name,
            "city": self.city,
            "country": self.country,
            "confidence": self.confidence,
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


def fallback_unknown_result(reason: str = "Uncertain or unverified") -> OllamaVisionResult:
    """Construct a safe unknown / unverified result."""
    return OllamaVisionResult(
        identified=False,
        site_name=None,
        city=None,
        country=None,
        confidence=0.0,
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


def encode_image_to_base64(image: Union[bytes, str, Path]) -> str:
    """
    Encode an image to standard base64 string.

    Accepts raw bytes, filesystem path (str or Path), or pre-encoded base64 string.
    """
    if isinstance(image, bytes):
        return base64.b64encode(image).decode("utf-8")

    if isinstance(image, Path) or (isinstance(image, str) and os.path.isfile(image)):
        with open(image, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    if isinstance(image, str):
        # Handle data URL if present
        if image.startswith("data:"):
            _, _, b64_part = image.partition(",")
            return b64_part.strip()
        return image.strip()

    raise TypeError(f"Unsupported image input type: {type(image).__name__}")


def resolve_chat_endpoint(base_url: str) -> str:
    """Normalize base URL to the Ollama chat endpoint."""
    cleaned = base_url.rstrip("/")
    if cleaned.endswith("/chat"):
        return cleaned
    if cleaned.endswith("/api"):
        return f"{cleaned}/chat"
    return f"{cleaned}/api/chat"


class OllamaVisionClient:
    """
    Async client for Ollama vision-capable models.

    Handles structured JSON generation, authentication, timeouts, and fail-safe
    error handling without exposing credentials.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = DEFAULT_OLLAMA_TIMEOUT,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("OLLAMA_API_KEY")
        self.base_url = (
            base_url
            if base_url is not None
            else os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
        )
        self.model = (
            model
            if model is not None
            else os.getenv("OLLAMA_VISION_MODEL", DEFAULT_OLLAMA_VISION_MODEL)
        )
        try:
            self.timeout = float(os.getenv("OLLAMA_TIMEOUT", timeout))
        except (ValueError, TypeError):
            self.timeout = timeout

        self.endpoint_url = resolve_chat_endpoint(self.base_url)
        self._transport = transport

    def _is_cloud_endpoint(self) -> bool:
        """Check if target endpoint is Ollama cloud requiring authentication."""
        url_lower = self.base_url.lower()
        return "ollama.com" in url_lower

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers without exposing the API key in representation."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _parse_response_payload(self, text: str) -> OllamaVisionResult:
        """Parse Ollama response body and extract structured OllamaVisionResult."""
        try:
            outer = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("Ollama response body is not valid JSON")
            return fallback_unknown_result(reason="Malformed response from Ollama")

        # Extract message content (from chat API) or response text (from generate API)
        raw_content = ""
        if isinstance(outer, dict):
            if "message" in outer and isinstance(outer["message"], dict):
                raw_content = outer["message"].get("content", "")
            elif "response" in outer:
                raw_content = outer.get("response", "")
            elif "identified" in outer:
                # Direct JSON payload returned
                raw_content = text

        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            # Strip markdown code fence e.g. ```json ... ```
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            parsed_data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning("Ollama vision content could not be parsed as JSON: %s", exc)
            return fallback_unknown_result(reason="Malformed JSON response from Ollama")

        if not isinstance(parsed_data, dict):
            return fallback_unknown_result(reason="Malformed JSON response from Ollama (expected object)")

        try:
            result = OllamaVisionResult.model_validate(parsed_data)
        except Exception as exc:
            logger.warning("Ollama response failed schema validation: %s", exc)
            return fallback_unknown_result(reason="Malformed JSON response from Ollama")

        # Normalize unknown states
        if not result.identified:
            return OllamaVisionResult(
                identified=False,
                site_name=None,
                city=None,
                country=None,
                confidence=0.0,
                reason=result.reason or "Monument not identified",
                uncertain=True,
                is_heritage=False,
            )

        # A non-heritage landmark (e.g. Times Square, Eiffel Tower) is NOT a
        # confirmed heritage site.  The vision model may have confidently
        # identified the place, but it is not something this system should
        # present as a heritage monument.  Reject it at the global layer
        # instead of surfacing it as a confirmed recognition.
        if not result.is_heritage:
            return OllamaVisionResult(
                identified=False,
                site_name=None,
                city=None,
                country=None,
                confidence=0.0,
                reason=result.reason or REASON_NON_HERITAGE,
                uncertain=True,
                is_heritage=False,
                explicit_non_heritage=True,
            )

        # Normalize confirmed heritage states — carry over the optional profile
        # fields so the frontend can render a full heritage profile.
        return OllamaVisionResult(
            identified=True,
            site_name=result.site_name,
            city=result.city,
            country=result.country,
            confidence=result.confidence,
            reason=result.reason,
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
    ) -> OllamaVisionResult:
        """
        Identify a monument globally using Ollama vision.

        Parameters
        ----------
        image : bytes | str | Path
            Raw image bytes, image filepath, or base64 data string.

        Returns
        -------
        OllamaVisionResult
            Parsed structured identification or safe unknown fallback.
        """
        # 1. Check for missing credentials when targeting cloud
        if self._is_cloud_endpoint() and not self.api_key:
            logger.warning("Ollama cloud endpoint requested but OLLAMA_API_KEY is not set")
            return fallback_unknown_result(reason="Missing OLLAMA_API_KEY for Ollama Cloud")

        # 2. Encode image
        try:
            b64_image = encode_image_to_base64(image)
        except Exception as exc:
            logger.warning("Failed to encode image for Ollama vision: %s", exc)
            return fallback_unknown_result(reason="Failed to encode query image")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": OLLAMA_VISION_PROMPT,
                    "images": [b64_image],
                }
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
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

            # Check status code
            status = response.status_code
            if status == 200:
                return self._parse_response_payload(response.text)

            if status in (401, 403):
                logger.warning("Ollama authentication/authorization failed (HTTP %d)", status)
                reason = "Ollama authentication failed (HTTP 401)" if status == 401 else "Ollama access denied (HTTP 403)"
                return fallback_unknown_result(reason=reason)

            if status == 429:
                logger.warning("Ollama rate limit reached (HTTP 429)")
                return fallback_unknown_result(reason="Ollama rate limit exceeded (HTTP 429)")

            if status >= 500:
                logger.warning("Ollama server error (HTTP %d)", status)
                return fallback_unknown_result(reason=f"Ollama server error (HTTP {status})")

            logger.warning("Ollama request failed with HTTP %d", status)
            return fallback_unknown_result(reason=f"Ollama request failed with HTTP {status}")

        except httpx.TimeoutException:
            logger.warning("Ollama vision request timed out after %.1fs", self.timeout)
            return fallback_unknown_result(reason=f"Ollama request timed out after {self.timeout:.1f}s")
        except (httpx.ConnectError, httpx.NetworkError):
            logger.warning("Failed to connect to Ollama endpoint at %s", self.base_url)
            return fallback_unknown_result(reason="Could not connect to Ollama service")
        except Exception as exc:
            # Never leak internal details or credentials
            logger.warning("Ollama vision query failed: %s", type(exc).__name__)
            return fallback_unknown_result(reason=f"Ollama vision request failed: {type(exc).__name__}")


async def identify_monument_global(
    image: Union[bytes, str, Path],
    client: Optional[OllamaVisionClient] = None,
) -> OllamaVisionResult:
    """Convenience helper to identify a monument with a default or custom client."""
    active_client = client if client is not None else OllamaVisionClient()
    return await active_client.identify_monument(image)
