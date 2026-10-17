"""
Unit tests for backend/ollama.py.

All tests use mocked HTTP transports. Never makes real network or Ollama requests.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Dict

import httpx
import pytest

from backend.ollama import (
    OllamaVisionClient,
    OllamaVisionResult,
    encode_image_to_base64,
    fallback_unknown_result,
    identify_monument_global,
    resolve_chat_endpoint,
)

SAMPLE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"


def _make_client(handler, api_key="test-api-key", base_url="https://ollama.com/api", timeout=5.0):
    transport = httpx.MockTransport(handler)
    return OllamaVisionClient(
        api_key=api_key,
        base_url=base_url,
        model="llama3.2-vision",
        timeout=timeout,
        transport=transport,
    )


class TestOllamaVisionClient:
    """Test suite for OllamaVisionClient."""

    @pytest.mark.anyio
    async def test_valid_identified_response(self):
        """Test parsing of a successful identification from Ollama."""
        expected_content = {
            "identified": True,
            "site_name": "Hawa Mahal",
            "city": "Jaipur",
            "country": "India",
            "confidence": 0.92,
            "reason": "Distinctive pink sandstone facade with honeycomb windows",
            "uncertain": False,
            "is_heritage": True,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "Authorization" in request.headers
            assert request.headers["Authorization"] == "Bearer test-api-key"
            body = json.loads(request.read())
            assert body["model"] == "llama3.2-vision"
            assert body["format"] == "json"
            assert len(body["messages"][0]["images"]) == 1

            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_content)}},
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert isinstance(result, OllamaVisionResult)
        assert result.identified is True
        assert result.site_name == "Hawa Mahal"
        assert result.city == "Jaipur"
        assert result.country == "India"
        assert result.confidence == 0.92
        assert result.uncertain is False
        assert "honeycomb" in result.reason

    @pytest.mark.anyio
    async def test_unknown_response(self):
        """Test parsing of an explicit unknown result."""
        expected_content = {
            "identified": False,
            "site_name": None,
            "city": None,
            "country": None,
            "confidence": 0.0,
            "reason": "Modern office building with glass exterior; not a recognized monument",
            "uncertain": True,
            "is_heritage": False,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_content)}},
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.site_name is None
        assert result.city is None
        assert result.country is None
        assert result.confidence == 0.0
        assert result.uncertain is True
        assert result.is_heritage is False
        assert "Modern office building" in result.reason

    @pytest.mark.anyio
    async def test_non_heritage_landmark_is_rejected(self):
        """A famous but non-heritage landmark must never be presented as a confirmed heritage site.

        Times Square is a famous public square, not a historic monument.  The
        vision model may confidently identify the place, but the global layer
        must reject it because it is not a heritage site.
        """
        expected_content = {
            "identified": True,
            "site_name": "Times Square",
            "city": "New York",
            "country": "United States",
            "confidence": 0.97,
            "reason": "Famous commercial intersection with large digital billboards and skyscrapers",
            "uncertain": False,
            "is_heritage": False,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_content)}},
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        # The place was recognised, but it is NOT a heritage site, so the
        # client must return a safe unknown result instead of a confirmed
        # heritage identification.
        assert result.identified is False
        assert result.site_name is None
        assert result.city is None
        assert result.country is None
        assert result.confidence == 0.0
        assert result.uncertain is True
        assert result.is_heritage is False
        assert "Times Square" not in (result.site_name or "")

    @pytest.mark.anyio
    async def test_non_heritage_ordinary_scene_is_rejected(self):
        """An ordinary scene (beach, mountains, modern building) is rejected."""
        expected_content = {
            "identified": True,
            "site_name": "Copacabana Beach",
            "city": "Rio de Janeiro",
            "country": "Brazil",
            "confidence": 0.91,
            "reason": "Sandy beach with waves, boardwalk and mountains in the background",
            "uncertain": False,
            "is_heritage": False,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_content)}},
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert result.is_heritage is False
        assert result.site_name is None

    @pytest.mark.anyio
    async def test_non_heritage_missing_flag_is_treated_as_rejected(self):
        """If the model omits is_heritage on an identified landmark, reject it.

        The flag defaults to False, so an identified place without an
        explicit is_heritage=true must never be promoted to a confirmed
        heritage site.
        """
        expected_content = {
            "identified": True,
            "site_name": "Some Famous Tower",
            "city": "Some City",
            "country": "Some Country",
            "confidence": 0.88,
            "reason": "A tall tower visible in the city skyline",
            "uncertain": False,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_content)}},
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert result.is_heritage is False
        assert result.site_name is None

    @pytest.mark.anyio
    async def test_markdown_code_block_stripped(self):
        """Test that JSON wrapped in markdown code fences is cleaned and parsed."""
        raw_json = json.dumps({
            "identified": True,
            "site_name": "Hawa Mahal",
            "city": "Jaipur",
            "country": "India",
            "confidence": 0.99,
            "reason": "Distinctive pink sandstone honeycomb facade",
            "uncertain": False,
            "is_heritage": True,
        })
        wrapped_content = f"```json\n{raw_json}\n```"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": wrapped_content}},
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is True
        assert result.site_name == "Hawa Mahal"
        assert result.uncertain is False

    @pytest.mark.anyio
    async def test_malformed_json_response(self):
        """Test graceful fallback when Ollama returns invalid JSON text."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": "I could not format this as JSON: Taj Mahal"}},
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.site_name is None
        assert result.uncertain is True
        assert "Malformed JSON" in result.reason

    @pytest.mark.anyio
    async def test_malformed_http_response_body(self):
        """Test graceful fallback when the HTTP response body itself is invalid JSON."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                text="<html><body>Bad Gateway</body></html>",
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert "Malformed response" in result.reason

    @pytest.mark.anyio
    async def test_http_401_unauthorized(self):
        """Test graceful handling of HTTP 401 without crashing or leaking keys."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=401, json={"error": "Invalid API key"})

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert "401" in result.reason

    @pytest.mark.anyio
    async def test_http_403_forbidden(self):
        """Test graceful handling of HTTP 403."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=403, json={"error": "Access forbidden"})

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert "403" in result.reason

    @pytest.mark.anyio
    async def test_http_429_rate_limit(self):
        """Test graceful handling of HTTP 429 rate limit exceeded."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=429, json={"error": "Rate limit exceeded"})

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert "429" in result.reason

    @pytest.mark.anyio
    async def test_http_500_server_error(self):
        """Test graceful handling of HTTP 500 server error."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=500, json={"error": "Internal error"})

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert "500" in result.reason

    @pytest.mark.anyio
    async def test_http_503_service_unavailable(self):
        """Test graceful handling of HTTP 503 service unavailable."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=503, json={"error": "Service overloaded"})

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert "503" in result.reason

    @pytest.mark.anyio
    async def test_timeout_handling(self):
        """Test strict timeout handling when server does not respond."""
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Request read timed out")

        client = _make_client(handler, timeout=2.0)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert "timed out" in result.reason.lower()

    @pytest.mark.anyio
    async def test_connect_error_handling(self):
        """Test connection failure handling (e.g. host unreachable)."""
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is False
        assert result.uncertain is True
        assert "connect" in result.reason.lower()

    @pytest.mark.anyio
    async def test_missing_api_key_for_cloud(self, monkeypatch):
        """Test that cloud endpoint with missing API key returns a safe fallback without making HTTP calls."""
        # Hermetic: ensure the process environment cannot leak a key loaded
        # from a .env file into this test's client construction.
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        called = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal called
            called = True
            return httpx.Response(200, json={})

        # Client targeting ollama.com with api_key=None
        client = OllamaVisionClient(
            api_key=None,
            base_url="https://ollama.com/api",
            transport=httpx.MockTransport(handler),
        )
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert called is False  # HTTP call must NOT be attempted
        assert result.identified is False
        assert result.uncertain is True
        assert "API_KEY" in result.reason

    @pytest.mark.anyio
    async def test_credentials_never_exposed(self, caplog):
        """Verify that API keys are never surfaced in results or error logs."""
        secret_key = "super_secret_production_key_98765"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=401, json={"error": "Unauthorized"})

        client = _make_client(handler, api_key=secret_key)
        with caplog.at_level(logging.DEBUG):
            result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert secret_key not in result.reason
        for record in caplog.records:
            assert secret_key not in record.getMessage()

    @pytest.mark.anyio
    async def test_accepts_data_url_and_filepath(self, tmp_path):
        """Verify client accepts base64 data URLs and file paths."""
        # 1. Test data URL string
        b64_str = base64.b64encode(SAMPLE_IMAGE_BYTES).decode("utf-8")
        data_url = f"data:image/png;base64,{b64_str}"

        # 2. Test file path
        img_file = tmp_path / "test_monument.png"
        img_file.write_bytes(SAMPLE_IMAGE_BYTES)

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            assert body["messages"][0]["images"][0] == b64_str
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps({
                    "identified": True,
                    "site_name": "Konark Sun Temple",
                    "city": "Konark",
                    "country": "India",
                    "confidence": 0.95,
                    "reason": "Stone carved chariot wheel",
                    "uncertain": False,
                    "is_heritage": True,
                })}},
            )

        client = _make_client(handler)

        r1 = await client.identify_monument(data_url)
        assert r1.identified is True
        assert r1.site_name == "Konark Sun Temple"

        r2 = await client.identify_monument(img_file)
        assert r2.identified is True
        assert r2.site_name == "Konark Sun Temple"

    @pytest.mark.anyio
    async def test_convenience_function(self):
        """Test identify_monument_global function."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps({
                    "identified": True,
                    "site_name": "Taj Mahal",
                    "city": "Agra",
                    "country": "India",
                    "confidence": 0.99,
                    "reason": "White marble mausoleum",
                    "uncertain": False,
                    "is_heritage": True,
                })}},
            )

        client = _make_client(handler)
        result = await identify_monument_global(SAMPLE_IMAGE_BYTES, client=client)
        assert result.identified is True
        assert result.site_name == "Taj Mahal"

    def test_to_dict_contract(self):
        """Verify OllamaVisionResult.to_dict() matches the required contract."""
        res = OllamaVisionResult(
            identified=True,
            site_name="Taj Mahal",
            city="Agra",
            country="India",
            confidence=0.95,
            reason="White marble dome",
            uncertain=False,
            is_heritage=True,
            historical_period="Mughal Empire (17th century)",
            founder_built_by="Shah Jahan",
            architectural_style="Mughal architecture",
            significance="A mausoleum built entirely for memory.",
            interesting_facts=["Built in 1632", "Made of white marble"],
        )
        d = res.to_dict()
        assert d == {
            "identified": True,
            "site_name": "Taj Mahal",
            "city": "Agra",
            "country": "India",
            "confidence": 0.95,
            "reason": "White marble dome",
            "uncertain": False,
            "is_heritage": True,
            "explicit_non_heritage": False,
            "historical_period": "Mughal Empire (17th century)",
            "founder_built_by": "Shah Jahan",
            "architectural_style": "Mughal architecture",
            "significance": "A mausoleum built entirely for memory.",
            "interesting_facts": ["Built in 1632", "Made of white marble"],
        }

    @pytest.mark.anyio
    async def test_heritage_profile_is_preserved(self):
        """A confirmed heritage identification carries its historical profile."""
        expected_content = {
            "identified": True,
            "site_name": "Hawa Mahal",
            "city": "Jaipur",
            "country": "India",
            "confidence": 0.92,
            "reason": "Distinctive pink sandstone facade with honeycomb windows",
            "uncertain": False,
            "is_heritage": True,
            "historical_period": "Rajput Kingdom of Jaipur (18th century)",
            "founder_built_by": "Sawai Pratap Singh",
            "architectural_style": "Rajput architecture",
            "significance": "A landmark of Jaipur and a symbol of Rajput royal culture.",
            "interesting_facts": [
                "Built in 1799",
                "Has 953 small windows called jharokhas",
                "Modelled in the form of Lord Krishna's crown",
            ],
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_content)}},
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is True
        assert result.is_heritage is True
        assert result.historical_period == "Rajput Kingdom of Jaipur (18th century)"
        assert result.founder_built_by == "Sawai Pratap Singh"
        assert result.architectural_style == "Rajput architecture"
        assert result.significance == "A landmark of Jaipur and a symbol of Rajput royal culture."
        assert result.interesting_facts == [
            "Built in 1799",
            "Has 953 small windows called jharokhas",
            "Modelled in the form of Lord Krishna's crown",
        ]
        d = result.to_dict()
        assert d["interesting_facts"] == result.interesting_facts

    @pytest.mark.anyio
    async def test_missing_profile_fields_are_null_not_invented(self):
        """When the model omits a profile field it stays null, never a guess."""
        expected_content = {
            "identified": True,
            "site_name": "Some Ancient Monument",
            "city": "Some City",
            "country": "Some Country",
            "confidence": 0.8,
            "reason": "Ancient stone structure",
            "uncertain": False,
            "is_heritage": True,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_content)}},
            )

        client = _make_client(handler)
        result = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert result.identified is True
        assert result.historical_period is None
        assert result.founder_built_by is None
        assert result.architectural_style is None
        assert result.significance is None
        assert result.interesting_facts == []

    def test_endpoint_resolution(self):
        """Verify chat endpoint URL normalization."""
        assert resolve_chat_endpoint("https://ollama.com/api") == "https://ollama.com/api/chat"
        assert resolve_chat_endpoint("https://ollama.com/api/") == "https://ollama.com/api/chat"
        assert resolve_chat_endpoint("http://localhost:11434") == "http://localhost:11434/api/chat"
        assert resolve_chat_endpoint("http://localhost:11434/api/chat") == "http://localhost:11434/api/chat"
