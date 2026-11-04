
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
                                "visual_category": "clearly_identifiable_heritage",
                                "unknown": False,
                                "site_name": "Angkor Wat",
                                "country_or_region": "Siem Reap, Cambodia",
                                "city": "Siem Reap",
                                "country": "Cambodia",
                                "visual_evidence": "Five lotus-bud towers with extensive sandstone galleries.",
                                "confidence": 0.86,
                                "evidence_tier": "substantial",
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
        assert res.confidence == 0.86
        assert res.evidence_tier == "substantial"
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

    @pytest.mark.anyio
    async def test_generic_sandstone_rejected_even_if_petra_claimed(self):
        # Simulates the exact user problem: generic red sandstone claiming to be Petra
        false_positive_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "visual_category": "generic_natural_rock_or_sandstone",
                                    "unknown": False,
                                    "is_heritage": True,
                                    "site_name": "Petra Archaeological Park",
                                    "country_or_region": "Wadi Musa, Jordan",
                                    "visual_evidence": "Red sandstone rock formation and canyon cliff surface.",
                                    "confidence": 0.95,
                                    "evidence_tier": "substantial",
                                })
                            }
                        ]
                    }
                }
            ]
        }
        transport = httpx.MockTransport(lambda req: httpx.Response(200, json=false_positive_payload))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True, "Generic sandstone must NEVER be accepted as Petra"
        assert res.identified is False
        assert res.site_name is None
        assert res.confidence == 0.0
        assert "sandstone" in res.reason.lower() or "insufficient" in res.reason.lower()

    @pytest.mark.anyio
    async def test_genuine_petra_with_carved_facade_accepted(self):
        # Genuine Petra with distinctive carved facade
        genuine_petra_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "visual_category": "clearly_identifiable_heritage",
                                    "unknown": False,
                                    "is_heritage": True,
                                    "site_name": "Petra",
                                    "country_or_region": "Ma'an, Jordan",
                                    "city": "Wadi Musa",
                                    "country": "Jordan",
                                    "visual_evidence": "Distinctive Nabataean rock-cut monumental facade of Al-Khazneh featuring carved Corinthian columns, entablature, and central tholos.",
                                    "confidence": 0.85,
                                    "evidence_tier": "substantial",
                                    "historical_period": "1st century AD (Nabataean Kingdom)",
                                    "architectural_style": "Hellenistic-Nabataean rock-cut architecture",
                                })
                            }
                        ]
                    }
                }
            ]
        }
        transport = httpx.MockTransport(lambda req: httpx.Response(200, json=genuine_petra_payload))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is False
        assert res.identified is True
        assert res.site_name == "Petra"
        assert res.confidence == 0.85
        assert res.evidence_tier == "substantial"
        assert res.visual_category == "clearly_identifiable_heritage"

    @pytest.mark.anyio
    async def test_taj_mahal_generic_marble_rejected(self):
        generic_marble_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "visual_category": "clearly_identifiable_heritage",
                                    "unknown": False,
                                    "is_heritage": True,
                                    "site_name": "Taj Mahal",
                                    "country_or_region": "Agra, India",
                                    "visual_evidence": "White marble texture and plain stone wall surface.",
                                    "confidence": 0.80,
                                })
                            }
                        ]
                    }
                }
            ]
        }
        transport = httpx.MockTransport(lambda req: httpx.Response(200, json=generic_marble_payload))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True, "Generic white marble without dome/minarets must be rejected"
        assert res.identified is False
        assert res.site_name is None

    @pytest.mark.anyio
    async def test_colosseum_generic_wall_rejected(self):
        generic_wall_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "visual_category": "generic_building_or_wall",
                                    "unknown": False,
                                    "is_heritage": True,
                                    "site_name": "Colosseum",
                                    "country_or_region": "Rome, Italy",
                                    "visual_evidence": "Stone brick wall with an ordinary arch.",
                                    "confidence": 0.75,
                                })
                            }
                        ]
                    }
                }
            ]
        }
        transport = httpx.MockTransport(lambda req: httpx.Response(200, json=generic_wall_payload))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True
        assert res.identified is False

    @pytest.mark.anyio
    async def test_machu_picchu_generic_mountain_rejected(self):
        generic_mountain_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "visual_category": "landscape_without_identifiable_monument",
                                    "unknown": False,
                                    "is_heritage": True,
                                    "site_name": "Machu Picchu",
                                    "country_or_region": "Cusco, Peru",
                                    "visual_evidence": "Green mountain peaks in morning mist.",
                                    "confidence": 0.80,
                                })
                            }
                        ]
                    }
                }
            ]
        }
        transport = httpx.MockTransport(lambda req: httpx.Response(200, json=generic_mountain_payload))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True
        assert res.identified is False

    @pytest.mark.anyio
    async def test_confidence_clamping_and_tier_derivation(self):
        high_conf_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps({
                                    "visual_category": "clearly_identifiable_heritage",
                                    "unknown": False,
                                    "is_heritage": True,
                                    "site_name": "Great Wall of China",
                                    "country_or_region": "Beijing, China",
                                    "visual_evidence": "Stone masonry watchtower and crenellated ramparts along mountain ridge.",
                                    "confidence": 0.99,
                                })
                            }
                        ]
                    }
                }
            ]
        }
        transport = httpx.MockTransport(lambda req: httpx.Response(200, json=high_conf_payload))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.identified is True
        # Must be clamped to 0.88 max to avoid uncalibrated certainty claims
        assert res.confidence == 0.88
        assert res.evidence_tier == "substantial"


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
            visual_category="clearly_identifiable_heritage",
            unknown=False,
            identified=True,
            site_name="Angkor Wat",
            country_or_region="Cambodia",
            city="Siem Reap",
            country="Cambodia",
            visual_evidence="Lotus-bud towers.",
            confidence=0.85,
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


class TestGeminiOptimizations:
    @pytest.mark.anyio
    async def test_in_memory_caching_skips_second_network_call(self, mock_gemini_response_payload):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json=mock_gemini_response_payload)

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport)

        # First call hits the mock transport
        res1 = await client.identify_monument(SAMPLE_IMAGE_BYTES)
        assert res1.identified is True
        assert res1.site_name == "Angkor Wat"
        assert call_count == 1

        # Second call with identical image MUST be served from cache
        res2 = await client.identify_monument(SAMPLE_IMAGE_BYTES)
        assert res2.identified is True
        assert res2.site_name == "Angkor Wat"
        assert call_count == 1, "Cache hit must not trigger a second network request"

    @pytest.mark.anyio
    async def test_errors_and_rate_limits_are_not_cached(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(429, text="Rate limit exceeded")

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport)

        res1 = await client.identify_monument(SAMPLE_IMAGE_BYTES)
        assert res1.unknown is True
        assert "429" in res1.reason
        assert call_count == 1

        # Error must NOT be cached; subsequent query must attempt network request again
        res2 = await client.identify_monument(SAMPLE_IMAGE_BYTES)
        assert res2.unknown is True
        assert call_count == 2, "Errors and rate limits must never be stored in cache"

    def test_prepare_gemini_image_resizes_large_image(self, tmp_path):
        from PIL import Image
        from backend.gemini import prepare_gemini_image

        large_img = Image.new("RGB", (2500, 1500), color=(100, 150, 200))
        img_path = tmp_path / "large_test.jpg"
        large_img.save(img_path, format="JPEG")

        mime, b64_str, byte_len, sha256_hash = prepare_gemini_image(img_path, max_edge=1024)
        assert mime == "image/jpeg"
        assert len(b64_str) > 0
        assert byte_len > 0
        assert len(sha256_hash) == 64

        # Verify decoded dimensions are <= 1024
        import base64
        import io
        decoded = base64.b64decode(b64_str)
        with Image.open(io.BytesIO(decoded)) as decoded_img:
            assert max(decoded_img.size) <= 1024
            assert decoded_img.size[0] == 1024
            assert decoded_img.size[1] == 614

    @pytest.mark.anyio
    async def test_thinking_level_minimal_serialization(self, mock_gemini_response_payload):
        captured_payload = None

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_payload
            captured_payload = json.loads(request.read())
            return httpx.Response(200, json=mock_gemini_response_payload)

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport, thinking_level="MINIMAL")
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.identified is True
        assert captured_payload is not None
        gen_config = captured_payload["generationConfig"]
        assert "thinkingConfig" in gen_config
        assert gen_config["thinkingConfig"]["thinkingLevel"] == "MINIMAL"
        assert "thinking_budget" not in gen_config["thinkingConfig"]
        assert "thinkingBudget" not in gen_config["thinkingConfig"]

    @pytest.mark.anyio
    async def test_thinking_level_low_serialization(self, mock_gemini_response_payload):
        captured_payload = None

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_payload
            captured_payload = json.loads(request.read())
            return httpx.Response(200, json=mock_gemini_response_payload)

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport, thinking_level="LOW")
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.identified is True
        assert captured_payload is not None
        gen_config = captured_payload["generationConfig"]
        assert "thinkingConfig" in gen_config
        assert gen_config["thinkingConfig"]["thinkingLevel"] == "LOW"
        assert "thinking_budget" not in gen_config["thinkingConfig"]
        assert "thinkingBudget" not in gen_config["thinkingConfig"]


class TestGeminiTransientErrorHandling:
    @pytest.mark.anyio
    async def test_503_followed_by_success_retries_and_succeeds(self, mock_gemini_response_payload):
        attempts = 0
        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return httpx.Response(503, text="Service Unavailable")
            return httpx.Response(200, json=mock_gemini_response_payload)

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert attempts == 2
        assert res.identified is True
        assert res.site_name == "Angkor Wat"
        assert res.unknown is False

    @pytest.mark.anyio
    async def test_two_consecutive_503_bounded_to_one_retry_returns_service_unavailable(self):
        attempts = 0
        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            return httpx.Response(503, text="Service Unavailable")

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert attempts == 2  # exactly 1 initial + 1 retry
        assert res.unknown is True
        assert res.identified is False
        assert res.status == "external_service_unavailable"
        assert res.error_type == "service_unavailable"
        assert res.evidence_tier == "unavailable"
        assert "HTTP 503" in res.reason

    @pytest.mark.anyio
    async def test_http_429_quota_error_does_not_retry(self):
        attempts = 0
        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            return httpx.Response(429, text="Resource has been exhausted")

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert attempts == 1  # 429 must NEVER retry automatically
        assert res.unknown is True
        assert res.status == "external_rate_limited"
        assert res.error_type == "rate_limited"

    @pytest.mark.anyio
    async def test_http_400_invalid_request_does_not_retry(self):
        attempts = 0
        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            return httpx.Response(400, text="Bad Request")

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert attempts == 1
        assert res.unknown is True
        assert res.status == "external_invalid_request"
        assert res.error_type == "invalid_request"

    @pytest.mark.anyio
    async def test_network_failure_returns_structured_error(self):
        transport = httpx.MockTransport(lambda req: (_ for _ in ()).throw(httpx.ConnectError("Network unreachable")))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True
        assert res.status == "external_network_error"
        assert res.error_type == "network_error"

    @pytest.mark.anyio
    async def test_backend_timeout_returns_structured_error(self):
        transport = httpx.MockTransport(lambda req: (_ for _ in ()).throw(httpx.TimeoutException("Read timed out")))
        client = GeminiVisionClient(api_key="test-key", transport=transport)
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        assert res.unknown is True
        assert res.status == "external_timeout"
        assert res.error_type == "timeout"

    @pytest.mark.anyio
    async def test_503_not_cached_allows_subsequent_manual_retry(self, mock_gemini_response_payload):
        call_count = 0
        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return httpx.Response(503, text="Service Unavailable")
            return httpx.Response(200, json=mock_gemini_response_payload)

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport)

        # First user request fails after 1 initial + 1 retry (call_count = 2)
        res1 = await client.identify_monument(SAMPLE_IMAGE_BYTES)
        assert res1.unknown is True
        assert call_count == 2
        assert len(client._cache) == 0  # Crucial: 503 is NOT cached

        # Second user request (manual retry) triggers fresh network request and succeeds
        res2 = await client.identify_monument(SAMPLE_IMAGE_BYTES)
        assert res2.identified is True
        assert res2.site_name == "Angkor Wat"
        assert call_count == 3

    @pytest.mark.anyio
    async def test_user_cancellation_during_retry_backoff(self):
        import asyncio
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="Service Unavailable")

        transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(api_key="test-key", transport=transport)

        task = asyncio.create_task(client.identify_monument(SAMPLE_IMAGE_BYTES))
        # Allow attempt 1 to complete and enter sleep
        await asyncio.sleep(0.05)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        # In-flight map must be cleanly purged
        assert len(client._in_flight) == 0

    @pytest.mark.anyio
    async def test_heritage_service_recognize_async_classifies_503_properly(self):
        service = MagicMock(spec=HeritageService)
        service.recognize.return_value = RecognitionResult(
            site_id="unknown",
            similarity=0.7360,
            margin=0.0037,
            confident=False,
            confirmed=False,
            decision="unknown",
            recognition_source="unknown",
            top_k=5,
        )
        gemini_client = MagicMock(spec=GeminiVisionClient)
        gemini_client.identify_monument = AsyncMock(return_value=fallback_unknown_result(
            reason="Gemini server error (HTTP 503)",
            error_type="service_unavailable",
            status="external_service_unavailable",
            evidence_tier="unavailable",
            visual_category="service_unavailable",
        ))
        service.gemini_client = gemini_client
        service.recognize_async = HeritageService.recognize_async.__get__(service, HeritageService)

        res = await service.recognize_async(SAMPLE_IMAGE_BYTES)

        assert res.recognition_status == "external_service_unavailable"
        assert res.site_id == "unknown"
        assert res.confirmed is False
        assert res.confident is False
        assert res.decision == "unknown"
        assert res.similarity == 0.7360
        assert res.margin == 0.0037
        assert res.global_identification["status"] == "external_service_unavailable"
        assert res.global_identification["error_type"] == "service_unavailable"
        assert res.global_identification["evidence_tier"] == "unavailable"


class TestGeminiTestSafetyGuard:
    """Tests for DISABLE_LIVE_GEMINI safety flag and path-independent .env loading."""

    def test_env_loading_does_not_override_test_safety_flag(self, monkeypatch):
        """Verify .env loading never overwrites an explicit DISABLE_LIVE_GEMINI=1."""
        from backend.gemini import ensure_env_loaded, is_live_gemini_disabled

        monkeypatch.setenv("DISABLE_LIVE_GEMINI", "1")
        ensure_env_loaded()
        assert os.getenv("DISABLE_LIVE_GEMINI") == "1"
        assert is_live_gemini_disabled() is True

    def test_valid_environment_key_not_overwritten_by_env(self, monkeypatch):
        """Verify an explicit process-level GEMINI_API_KEY is not overwritten by .env."""
        from backend.gemini import ensure_env_loaded

        monkeypatch.setenv("GEMINI_API_KEY", "explicit-preconfigured-process-key")
        ensure_env_loaded()
        assert os.getenv("GEMINI_API_KEY") == "explicit-preconfigured-process-key"

    @pytest.mark.anyio
    async def test_disable_live_gemini_blocks_network_requests(self, monkeypatch):
        """Verify that when DISABLE_LIVE_GEMINI=1 and no mock transport is set, zero network calls are made."""
        monkeypatch.setenv("DISABLE_LIVE_GEMINI", "1")

        client = GeminiVisionClient()
        assert client.live_disabled is True
        assert client._transport is None

        # Execute identify_monument
        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

        # Must return structured safety fallback without attempting network
        assert res.unknown is True
        assert res.identified is False
        assert res.status == "external_service_unavailable"
        assert res.error_type == "live_calls_disabled"
        assert "DISABLE_LIVE_GEMINI=1" in res.reason
        assert client._client is None  # HTTP client was never created

    @pytest.mark.anyio
    async def test_disable_live_gemini_allows_mock_transport(self, monkeypatch, mock_gemini_response_payload):
        """Verify that mock transports work normally even when DISABLE_LIVE_GEMINI=1 is active."""
        monkeypatch.setenv("DISABLE_LIVE_GEMINI", "1")

        called = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal called
            called = True
            assert request.headers.get("x-goog-api-key") is not None
            return httpx.Response(200, json=mock_gemini_response_payload)

        mock_transport = httpx.MockTransport(handler)
        client = GeminiVisionClient(transport=mock_transport)

        assert client.live_disabled is True
        assert client._transport is not None
        assert client.api_key is not None

        res = await client.identify_monument(SAMPLE_IMAGE_BYTES)
        assert called is True
        assert res.unknown is False
        assert res.identified is True
        assert res.site_name == "Angkor Wat"

    def test_normal_mode_initializes_configured_key_without_exposing_it(self, monkeypatch):
        """Verify normal mode reads configured key without exposing raw key in string representations."""
        monkeypatch.delenv("DISABLE_LIVE_GEMINI", raising=False)
        test_key = "AIzaSyTestKeyForSecurityVerification1234567"
        monkeypatch.setenv("GEMINI_API_KEY", test_key)

        client = GeminiVisionClient()
        assert client.live_disabled is False
        assert client.api_key == test_key

        # Security verification: key must NOT be leaked in representations or logs
        repr_str = repr(client)
        str_str = str(client)
        assert test_key not in repr_str
        assert test_key not in str_str
        assert "api_key=configured" in repr_str

        # Header check: key is placed in request header only
        headers = client._build_headers()
        assert headers.get("x-goog-api-key") == test_key

    def test_env_loading_independent_of_cwd(self, monkeypatch, tmp_path):
        """Verify ensure_env_loaded reliably finds project-root .env from any arbitrary working directory."""
        from backend.gemini import ensure_env_loaded

        # Change working directory to a temporary folder
        orig_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            ensure_env_loaded()
            # GEMINI_MODEL or GEMINI_TIMEOUT should be available from project root .env
            assert os.getenv("GEMINI_MODEL") == "gemini-3.1-flash-lite"
        finally:
            os.chdir(orig_cwd)
