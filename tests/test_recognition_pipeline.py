"""
Integration unit tests for the open-set recognition + Ollama vision fallback pipeline.

All Ollama HTTP requests are strictly mocked using httpx.MockTransport.
Zero network requests are made.
"""

import json
from pathlib import Path
from typing import Optional

import faiss
import httpx
import numpy as np
import pytest

from backend.heritage_service import (
    DEFAULT_TOP_K,
    REASON_LOW_SIMILARITY,
    REASON_NON_HERITAGE,
    HeritageService,
    RecognitionResult,
)
from backend.ollama import OllamaVisionClient
from data.evidence.loader import EvidenceRepository
from ml.confidence import ConfidenceLayer, RetrievalConfig
from ml.open_set import OpenSetRejection

SITES = [
    ("taj_mahal", [1.0, 0.0, 0.0, 0.0]),
    ("taj_mahal", [0.9, 0.1, 0.0, 0.0]),
    ("red_fort", [0.0, 1.0, 0.0, 0.0]),
    ("red_fort", [0.0, 0.9, 0.1, 0.0]),
]
IMAGE_IDS = ["taj_mahal_01", "taj_mahal_02", "red_fort_01", "red_fort_02"]
PATHS = [f"data/raw/{i.rsplit('_', 1)[0]}/{i}.jpg" for i in IMAGE_IDS]

METADATA = [
    {
        "id": "taj_mahal",
        "name": "Taj Mahal",
        "alternate_name": "Taj",
        "location": "Agra",
        "state": "Uttar Pradesh",
        "country": "India",
        "description": "A white marble mausoleum.",
        "historical_period": "Mughal Empire (17th century)",
        "category": "monument",
        "preservation_context": "UNESCO World Heritage Site",
    },
    {
        "id": "red_fort",
        "name": "Red Fort",
        "alternate_name": "Lal Qila",
        "location": "Delhi",
        "state": "Delhi",
        "country": "India",
        "description": "A historic fort complex.",
        "historical_period": "Mughal Empire (17th century)",
        "category": "fort",
        "preservation_context": "UNESCO World Heritage Site",
    },
]

EVIDENCE = [
    {
        "site_id": "taj_mahal",
        "claim": "The Taj Mahal is a white marble mausoleum commissioned in 1632 by Shah Jahan.",
        "source_name": "UNESCO",
        "source_url": "https://whc.unesco.org/en/list/252",
    },
    {
        "site_id": "red_fort",
        "claim": "The Red Fort was the primary residence of Mughal emperors from 1648 to 1857.",
        "source_name": "UNESCO",
        "source_url": "https://whc.unesco.org/en/list/231",
    },
]


class _FakeExtractor:
    def __init__(self, embedding):
        self.embedding = np.asarray(embedding, dtype=np.float32)
        self.paths = []

    def extract(self, path):
        self.paths.append(str(path))
        return self.embedding


def _unit(vec):
    v = np.asarray(vec, dtype=np.float32)
    return v / np.linalg.norm(v)


def _layer(threshold=0.65):
    vectors = np.stack([_unit(v) for _, v in SITES]).astype(np.float32)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return ConfidenceLayer(
        index, IMAGE_IDS, PATHS, RetrievalConfig(similarity_threshold=threshold)
    )


@pytest.fixture
def repo(tmp_path):
    meta = tmp_path / "m.json"
    ev = tmp_path / "e.json"
    meta.write_text(json.dumps(METADATA))
    ev.write_text(json.dumps(EVIDENCE))
    return EvidenceRepository(meta, ev)


def _service_with_mock_ollama(
    repo,
    embedding,
    handler,
    api_key="test-api-key",
    base_url="https://ollama.com/api",
    threshold=0.65,
    open_set=None,
):
    transport = httpx.MockTransport(handler)
    ollama_client = OllamaVisionClient(
        api_key=api_key,
        base_url=base_url,
        transport=transport,
    )
    layer = _layer(threshold=threshold)
    return HeritageService(
        confidence_layer=layer,
        repository=repo,
        extractor=_FakeExtractor(embedding),
        open_set=open_set,
        ollama_client=ollama_client,
    )


class TestRecognitionPipelineOllamaIntegration:
    """Test suite verifying open-set recognition + Ollama fallback behavior."""

    @pytest.mark.anyio
    async def test_strong_local_match_does_not_call_ollama(self, repo, tmp_path):
        """When local CLIP + FAISS + open-set confirms a match, Ollama must NOT be called."""
        ollama_called = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal ollama_called
            ollama_called = True
            raise AssertionError("Ollama must not be called on confident local matches!")

        img_path = tmp_path / "query.jpg"
        img_path.write_bytes(b"dummy image data")

        # Query vector matching Taj Mahal strongly (1.0 similarity)
        svc = _service_with_mock_ollama(repo, [1.0, 0.0, 0.0, 0.0], handler)
        result = await svc.recognize_async(img_path)

        assert ollama_called is False
        assert result.confirmed is True
        assert result.confident is True
        assert result.decision == "match"
        assert result.site_id == "taj_mahal"
        assert result.recognition_source == "local"
        assert result.global_identification is None

    @pytest.mark.anyio
    async def test_rejected_local_match_calls_ollama(self, repo, tmp_path):
        """When local recognition is rejected, the image is passed to Ollama vision."""
        ollama_called = False

        expected_ollama = {
            "identified": True,
            "site_name": "Hawa Mahal",
            "city": "Jaipur",
            "country": "India",
            "confidence": 0.88,
            "reason": "Distinctive pink sandstone honeycomb facade",
            "uncertain": False,
            "is_heritage": True,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal ollama_called
            ollama_called = True
            body = json.loads(request.read())
            assert "messages" in body
            assert len(body["messages"][0]["images"]) == 1
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "hawa_mahal.jpg"
        img_path.write_bytes(b"hawa mahal photo bytes")

        # Low similarity vector that will be rejected by local open-set
        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert ollama_called is True
        # The Ollama identification is a model proposal, NOT an independently
        # verified catalogue match.  Per the requirements, it must NOT be
        # marked as confirmed.  It is "confident" in the model's call but
        # "not confirmed" until independently verified.
        assert result.confirmed is False
        assert result.confident is True
        assert result.decision == "match"
        assert result.recognition_source == "ollama"
        # Ollama proposals without independent verification have no verified external sources. Citations list is empty.
        assert len(result.citations) == 0

    @pytest.mark.anyio
    async def test_successful_visual_fallback_structured_fields(self, repo, tmp_path):
        """Verifies successful visual fallback with full structured output fields."""
        ollama_called = False

        expected_ollama = {
            "unknown": False,
            "site_name": "Abu Simbel Temples",
            "country_or_region": "Egypt",
            "city": "Aswan",
            "country": "Egypt",
            "visual_evidence": "Four colossal seated statues of Ramesses II carved into sandstone cliff",
            "confidence": 0.96,
            "uncertainty": None,
            "alternatives": ["Karnak Temple"],
            "limitations": "Direct sunlight causing high dynamic contrast",
            "is_heritage": True,
            "historical_period": "19th Dynasty of Egypt",
            "founder_built_by": "Ramesses II",
            "architectural_style": "Ancient Egyptian rock-cut architecture",
            "significance": "Monumental rock-cut temple dedicated to Ramesses II and Queen Nefertari",
            "interesting_facts": ["Relocated in 1968 to avoid submersion under Lake Nasser"],
        }

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal ollama_called
            ollama_called = True
            body = json.loads(request.read())
            assert "messages" in body
            assert len(body["messages"][0]["images"]) == 1
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "abu_simbel.jpg"
        img_path.write_bytes(b"abu simbel photo bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert ollama_called is True
        # Mark source as ollama, keep separate from local matches, not independently confirmed
        assert result.recognition_source == "ollama"
        assert result.confirmed is False
        assert result.confident is True
        assert result.decision == "match"
        assert result.site_id == "unknown"
        assert result.confidence == 0.96
        # Local CLIP similarity is preserved
        assert isinstance(result.similarity, float)

        # Check structured output fields
        gid = result.global_identification
        assert gid is not None
        assert gid["unknown"] is False
        assert gid["identified"] is True
        assert gid["site_name"] == "Abu Simbel Temples"
        assert gid["country_or_region"] == "Egypt"
        assert gid["visual_evidence"] == "Four colossal seated statues of Ramesses II carved into sandstone cliff"
        assert gid["confidence"] == 0.96
        assert gid["alternatives"] == ["Karnak Temple"]
        assert gid["limitations"] == "Direct sunlight causing high dynamic contrast"
        assert gid["is_heritage"] is True

        # Citations and grounded answers are not fabricated
        assert len(result.citations) == 0
        assert result.answer is None
        assert result.is_grounded is False

    @pytest.mark.anyio
    async def test_local_rejection_margin_failure_triggers_fallback(self, repo, tmp_path):
        """When local top-1 score is high but margin to competitor is too low, open-set rejects and calls Ollama."""
        ollama_called = False

        expected_ollama = {
            "unknown": False,
            "site_name": "Fatehpur Sikri",
            "country_or_region": "India",
            "visual_evidence": "Red sandstone fortified courtyard with ornate pavilion",
            "confidence": 0.85,
            "alternatives": ["Agra Fort"],
            "limitations": None,
            "is_heritage": True,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal ollama_called
            ollama_called = True
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "fatehpur.jpg"
        img_path.write_bytes(b"fatehpur photo bytes")

        # Ambiguous vector close to both taj_mahal ([1,0,0,0]) and red_fort ([0,1,0,0])
        ambiguous_vec = _unit([0.71, 0.70, 0.0, 0.0])
        svc = _service_with_mock_ollama(
            repo,
            ambiguous_vec,
            handler,
            open_set=OpenSetRejection(accept_threshold=0.65, margin_threshold=0.10),
        )
        result = await svc.recognize_async(img_path)

        assert ollama_called is True
        assert result.recognition_source == "ollama"
        assert result.confirmed is False
        assert result.confident is True
        assert result.global_identification["site_name"] == "Fatehpur Sikri"

    @pytest.mark.anyio
    async def test_unknown_visual_fallback(self, repo, tmp_path):
        """When Ollama cannot identify the image, it returns safe unknown result."""
        expected_ollama = {
            "unknown": True,
            "site_name": None,
            "country_or_region": None,
            "visual_evidence": "Unclear image of an ordinary modern concrete structure",
            "confidence": 0.0,
            "alternatives": [],
            "limitations": "Heavy blur and lack of architectural features",
            "is_heritage": False,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "unknown_building.jpg"
        img_path.write_bytes(b"blurry unknown building bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is False
        assert result.confident is False
        assert result.site_id == "unknown"
        assert result.decision == "unknown"
        assert result.recognition_source == "unknown"
        assert result.global_identification is None
        assert result.confidence is None

    @pytest.mark.anyio
    async def test_malformed_response_fallback(self, repo, tmp_path):
        """When Ollama returns a malformed response, service safely returns unknown without crashing."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=200, text="Internal server error occurred: not JSON")

        img_path = tmp_path / "malformed.jpg"
        img_path.write_bytes(b"image bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is False
        assert result.confident is False
        assert result.site_id == "unknown"
        assert result.decision == "unknown"
        assert result.recognition_source == "unknown"
        assert result.global_identification is None

    @pytest.mark.anyio
    async def test_ollama_timeout_fallback(self, repo, tmp_path):
        """When Ollama times out, service returns a safe unknown result without crashing."""
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Read timed out after 30.0s")

        img_path = tmp_path / "timeout.jpg"
        img_path.write_bytes(b"image bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is False
        assert result.confident is False
        assert result.site_id == "unknown"
        assert result.decision == "unknown"
        assert result.recognition_source == "unknown"
        assert result.global_identification is None

    @pytest.mark.anyio
    async def test_ollama_unavailable_fallback(self, repo, tmp_path):
        """When Ollama service is unavailable, service returns safe unknown."""
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused to Ollama server")

        img_path = tmp_path / "conn_error.jpg"
        img_path.write_bytes(b"image bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is False
        assert result.confident is False
        assert result.site_id == "unknown"
        assert result.decision == "unknown"
        assert result.recognition_source == "unknown"
        assert result.global_identification is None

    @pytest.mark.anyio
    async def test_ollama_fallback_with_question_answered(self, repo, tmp_path):
        """When Ollama identifies monument and answers question, answer is returned ungrounded without citations."""
        ollama_prompt_received = ""
        expected_ollama = {
            "unknown": False,
            "site_name": "Abu Simbel Temples",
            "country_or_region": "Egypt",
            "visual_evidence": "Colossal rock statues",
            "confidence": 0.90,
            "is_heritage": True,
            "answer": "The temples were commissioned by Pharaoh Ramesses II in the 13th century BC.",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal ollama_prompt_received
            body = json.loads(request.read())
            ollama_prompt_received = body["messages"][0]["content"]
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "abu_simbel.jpg"
        img_path.write_bytes(b"abu simbel photo bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path, question="Who commissioned this monument?")

        # Question was passed to prompt
        assert "Who commissioned this monument?" in ollama_prompt_received

        # Recognition source and status
        assert result.recognition_source == "ollama"
        assert result.confirmed is False  # Never presented as independently verified
        assert result.confident is True
        assert result.decision == "match"

        # Answer is present, ungrounded, no citations
        assert result.answer == "The temples were commissioned by Pharaoh Ramesses II in the 13th century BC."
        assert result.citations == []
        assert result.is_grounded is False

        # Global identification contains site info and separates answer
        assert result.global_identification is not None
        assert result.global_identification["site_name"] == "Abu Simbel Temples"
        assert "answer" not in result.global_identification

    @pytest.mark.anyio
    async def test_ollama_fallback_without_question(self, repo, tmp_path):
        """When question is empty, Ollama fallback identifies monument and answer is None."""
        expected_ollama = {
            "unknown": False,
            "site_name": "Abu Simbel Temples",
            "country_or_region": "Egypt",
            "visual_evidence": "Colossal rock statues",
            "confidence": 0.90,
            "is_heritage": True,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "abu_simbel.jpg"
        img_path.write_bytes(b"abu simbel photo bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path, question="")

        assert result.recognition_source == "ollama"
        assert result.confirmed is False
        assert result.confident is True
        assert result.answer is None
        assert result.citations == []
        assert result.is_grounded is False

    @pytest.mark.anyio
    async def test_ollama_fallback_question_unanswerable(self, repo, tmp_path):
        """When question cannot be answered by Ollama, identification is preserved and fallback message is returned."""
        expected_ollama = {
            "unknown": False,
            "site_name": "Abu Simbel Temples",
            "country_or_region": "Egypt",
            "visual_evidence": "Colossal rock statues",
            "confidence": 0.90,
            "is_heritage": True,
            "answer": None,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "abu_simbel.jpg"
        img_path.write_bytes(b"abu simbel photo bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path, question="What is inside the closed inner chamber?")

        assert result.recognition_source == "ollama"
        assert result.confirmed is False
        assert result.confident is True
        assert result.global_identification["site_name"] == "Abu Simbel Temples"
        assert (
            result.answer
            == "This question could not be answered from the visual information available for this monument."
        )
        assert result.citations == []
        assert result.is_grounded is False

    @pytest.mark.anyio
    async def test_ollama_fallback_unknown_image_with_question(self, repo, tmp_path):
        """When image is unknown, answer is None even if a question was asked."""
        expected_ollama = {
            "unknown": True,
            "site_name": None,
            "visual_evidence": "Blurry image of an office tower",
            "confidence": 0.0,
            "is_heritage": False,
            "answer": None,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "office.jpg"
        img_path.write_bytes(b"office bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path, question="When was this built?")

        assert result.recognition_source == "unknown"
        assert result.confirmed is False
        assert result.confident is False
        assert result.answer is None
        assert result.citations == []
        assert result.is_grounded is False

    @pytest.mark.anyio
    async def test_ollama_fallback_error_with_question(self, repo, tmp_path):
        """When Ollama request times out or errors, safe unknown is returned with answer None."""
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Ollama timed out")

        img_path = tmp_path / "timeout.jpg"
        img_path.write_bytes(b"image bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path, question="Who built it?")

        assert result.recognition_source == "unknown"
        assert result.confirmed is False
        assert result.confident is False
        assert result.answer is None
        assert result.citations == []
        assert result.is_grounded is False
