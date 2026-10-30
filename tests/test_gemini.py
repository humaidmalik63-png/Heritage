"""
Tests for the Google Gemini Vision fallback client and integration.
"""

import json
import os
import pytest
import httpx
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from backend.gemini import (
    GeminiVisionClient,
    GeminiVisionResult,
    detect_mime_type_and_base64,
    fallback_unknown_result,
    REASON_NON_HERITAGE,
)
from backend.heritage_service import (
    HeritageService,
    RecognitionResult,
    REASON_LOW_SIMILARITY,
)
from data.evidence.loader import EvidenceRepository


SAMPLE_IMAGE_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00"


@pytest.fixture
def mock_gemini_response_payload():
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "unknown": False,
                                "site_name": "Angkor Wat",
                                "country_or_region": "Siem Reap, Cambodia",
                                "city": "Siem Reap",
                                "country": "Cambodia",
                                "visual_evidence": "Five lotus-bud towers with extensive sandstone galleries.",
                                "confidence": 0.96,
                                "uncertainty": None,
                                "alternatives": [],
                                "limitations": None,
                                "is_heritage": True,
                                "historical_period": "12th century (Khmer Empire)",
                                "founder_built_by": "Suryavarman II",
                                "architectural_style": "Khmer architecture",
                                "significance": "Largest religious monument in the world.",
                                "interesting_facts": ["Originally dedicated to Vishnu, later transformed into a Buddhist temple."],
                            })
                        }
                    ],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ]
    }


class TestMimeTypeAndBase64:
    def test_detect_jpeg_bytes(self):
        mime, b64 = detect_mime_type_and_base64(SAMPLE_IMAGE_BYTES)
        assert mime == "image/jpeg"
        assert len(b64) > 0

    def test_detect_data_url(self):
        data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        mime, b64 = detect_mime_type_and_base64(data_url)
        assert mime == "image/png"
        assert b64.startswith("iVBOR")

    def test_detect_file(self, tmp_path):
        f = tmp_path / "test.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
        mime, b64 = detect_mime_type_and_base64(f)
        assert mime == "image/png"
        assert len(b64) > 0


class TestGeminiVisionClient:
    @pytest.mark.anyio
    async def test_missing_api_key_returns_safe_unknown(self):
        client = GeminiVisionClient(api_key="")
        client.api_key = None
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)
        assert res.unknown is True
        assert res.identified is False
        assert "Missing GEMINI_API_KEY" in res.reason

    @pytest.mark.anyio
    async def test_successful_identification(self, mock_gemini_response_payload):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("x-goog-api-key") == "test-key"
            body = json.loads(request.read())
            assert "contents" in body
            assert body["generationConfig"]["response_mime_type"] == "application/json"
            return httpx.Response(200, json=mock_gemini_response_payload)

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is False
        assert res.identified is True
        assert res.site_name == "Angkor Wat"
        assert res.country == "Cambodia"
        assert res.confidence == 0.96
        assert res.is_heritage is True
        assert res.historical_period == "12th century (Khmer Empire)"

    @pytest.mark.anyio
    async def test_non_heritage_rejection(self):
        non_heritage_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "unknown": True,
                                    "is_heritage": False,
                                    "site_name": None,
                                    "visual_evidence": "Image shows a modern commercial skyscraper.",
                                    "confidence": 0.0,
                                })
                            }
                        ]
                    }
                }
            ]
        }

        transport = httpx.MockTransport(lambda req: httpx.Response(200, json=non_heritage_payload))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True
        assert res.identified is False
        assert res.is_heritage is False

    @pytest.mark.anyio
    async def test_http_rate_limit(self):
        transport = httpx.MockTransport(lambda req: httpx.Response(429, text="Rate limit exceeded"))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True
        assert "429" in res.reason

    @pytest.mark.anyio
    async def test_http_server_error(self):
        transport = httpx.MockTransport(lambda req: httpx.Response(500, text="Internal server error"))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True
        assert "500" in res.reason

    @pytest.mark.anyio
    async def test_malformed_json_response(self):
        transport = httpx.MockTransport(lambda req: httpx.Response(200, text="not a json"))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True
        assert "Malformed" in res.reason


class TestHeritageServiceGeminiIntegration:
    @pytest.mark.anyio
    async def test_known_monument_skips_gemini(self):
        service = MagicMock(spec=HeritageService)
        local_res = RecognitionResult(
            site_id="taj_mahal",
            similarity=0.95,
            confidence=0.95,
            confident=True,
            confirmed=True,
            decision="match",
            recognition_source="local",
            top_k=5,
        )
        service.recognize.return_value = local_res
        service.gemini_client = MagicMock(spec=GeminiVisionClient)
        service.recognize_async = HeritageService.recognize_async.__get__(service, HeritageService)

        res = await service.recognize_async(SAMPLE_IMAGE_BYTES)

        assert res.confirmed is True
        assert res.recognition_source == "local"
        assert res.site_id == "taj_mahal"
        # Gemini must NEVER be called when local recognition succeeds
        service.gemini_client.identify_monument.assert_not_called()

    @pytest.mark.anyio
    async def test_rejected_monument_triggers_gemini(self):
        service = MagicMock(spec=HeritageService)
        unconfirmed_res = RecognitionResult(
            site_id="unknown",
            similarity=0.65,
            confidence=None,
            confident=False,
            confirmed=False,
            decision="unknown",
            recognition_source="unknown",
            top_k=5,
        )
        service.recognize.return_value = unconfirmed_res

        gemini_client = MagicMock(spec=GeminiVisionClient)
        gemini_client.identify_monument = AsyncMock(return_value=GeminiVisionResult(
            unknown=False,
            identified=True,
            site_name="Angkor Wat",
            country_or_region="Cambodia",
            city="Siem Reap",
            country="Cambodia",
            visual_evidence="Lotus-bud towers.",
            confidence=0.95,
            is_heritage=True,
            historical_period="12th century",
            interesting_facts=["Built by Suryavarman II"],
        ))
        service.gemini_client = gemini_client
        service.recognize_async = HeritageService.recognize_async.__get__(service, HeritageService)

        res = await service.recognize_async(SAMPLE_IMAGE_BYTES)

        assert res.confident is True
        assert res.confirmed is False
        assert res.recognition_source == "gemini"
        assert res.site_id == "unknown"
        assert res.global_identification["site_name"] == "Angkor Wat"
        gemini_client.identify_monument.assert_called_once()

    @pytest.mark.anyio
    async def test_gemini_failure_does_not_call_ollama(self):
        service = MagicMock(spec=HeritageService)
        service.recognize.return_value = RecognitionResult(
            site_id="unknown",
            similarity=0.55,
            confident=False,
            confirmed=False,
            decision="unknown",
            recognition_source="unknown",
            top_k=5,
        )
        # Mock Gemini failing
        gemini_client = MagicMock(spec=GeminiVisionClient)
        gemini_client.identify_monument = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        service.gemini_client = gemini_client

        # Mock Ollama client
        ollama_client = MagicMock()
        service.ollama_client = ollama_client
        service.recognize_async = HeritageService.recognize_async.__get__(service, HeritageService)

        res = await service.recognize_async(SAMPLE_IMAGE_BYTES)

        assert res.confirmed is False
        assert res.recognition_source == "unknown"
        # Per rule 4: DO NOT call Ollama automatically if Gemini fails
        ollama_client.identify_monument.assert_not_called()
