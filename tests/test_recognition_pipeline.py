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
        assert result.confirmed is True
        assert result.confident is True
        assert result.decision == "match"
        assert result.recognition_source == "ollama"
        # Rule 8: NEVER turn Ollama response into a local site_id automatically
        assert result.site_id == "unknown"
        assert result.global_identification is not None
        assert result.global_identification["site_name"] == "Hawa Mahal"
        assert result.global_identification["city"] == "Jaipur"
        assert result.global_identification["country"] == "India"
        assert result.global_identification["confidence"] == 0.88
        assert result.global_identification["uncertain"] is False
        assert result.similarity == 0.88
        assert result.reason == "Distinctive pink sandstone honeycomb facade"

    @pytest.mark.anyio
    async def test_ollama_identifies_unindexed_monument(self, repo, tmp_path):
        """Global monument identification separate from local catalogue."""
        expected_ollama = {
            "identified": True,
            "site_name": "Colosseum",
            "city": "Rome",
            "country": "Italy",
            "confidence": 0.94,
            "reason": "Flavian Amphitheatre oval structure in travertine limestone",
            "uncertain": False,
            "is_heritage": True,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "colosseum.jpg"
        img_path.write_bytes(b"colosseum bytes")

        noise_vec = _unit([0.0, 0.0, 0.0, 1.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is True
        assert result.recognition_source == "ollama"
        assert result.site_id == "unknown"
        assert result.global_identification["site_name"] == "Colosseum"
        assert result.global_identification["country"] == "Italy"

        d = result.to_dict()
        assert d["confirmed"] is True
        assert d["recognition_source"] == "ollama"
        assert d["global_identification"]["site_name"] == "Colosseum"

    @pytest.mark.anyio
    async def test_ollama_cannot_identify_image_returns_safe_unknown(self, repo, tmp_path):
        """When Ollama cannot identify the image, return a safe unknown result."""
        expected_ollama = {
            "identified": False,
            "site_name": None,
            "city": None,
            "country": None,
            "confidence": 0.0,
            "reason": "Generic modern office building with reflective windows",
            "uncertain": True,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "modern_office.jpg"
        img_path.write_bytes(b"office bytes")

        noise_vec = _unit([0.2, 0.2, 0.7, 0.6])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is False
        assert result.confident is False
        assert result.site_id == "unknown"
        assert result.decision == "unknown"
        assert result.recognition_source == "unknown"
        assert result.global_identification is None

    @pytest.mark.anyio
    async def test_ollama_timeout_returns_safe_unknown(self, repo, tmp_path):
        """When Ollama times out, application does not crash; returns safe unknown."""
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Ollama read timed out")

        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"test bytes")

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
    async def test_ollama_http_500_server_error_returns_safe_unknown(self, repo, tmp_path):
        """When Ollama returns HTTP 500 error, returns safe unknown result."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=500, json={"error": "Model failed to load"})

        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"test bytes")

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
    async def test_missing_ollama_credentials_returns_safe_unknown(self, repo, tmp_path, monkeypatch):
        """When Ollama Cloud credentials are missing, returns safe unknown without calling network."""
        # Hermetic: prevent a key loaded from a .env file into the process
        # environment from leaking into this test's client construction.
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        called = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal called
            called = True
            return httpx.Response(200, json={})

        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"test bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        # api_key is None targeting ollama.com
        svc = _service_with_mock_ollama(repo, noise_vec, handler, api_key=None, base_url="https://ollama.com/api")
        result = await svc.recognize_async(img_path)

        assert called is False
        assert result.confirmed is False
        assert result.confident is False
        assert result.site_id == "unknown"
        assert result.decision == "unknown"
        assert result.recognition_source == "unknown"
        assert result.global_identification is None

    @pytest.mark.anyio
    async def test_never_turns_ollama_name_into_local_site_id(self, repo, tmp_path):
        """Ollama global identification must strictly keep site_id='unknown' to avoid corrupting FAISS mapping."""
        expected_ollama = {
            "identified": True,
            "site_name": "Taj Mahal",  # Same name as local, but identified by Ollama
            "city": "Agra",
            "country": "India",
            "confidence": 0.90,
            "reason": "Dome and minarets observed",
            "uncertain": False,
            "is_heritage": True,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"test bytes")

        # Local match rejected
        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        # site_id must stay 'unknown' because local FAISS did not verify it
        assert result.site_id == "unknown"
        assert result.recognition_source == "ollama"
        assert result.global_identification["site_name"] == "Taj Mahal"

    @pytest.mark.anyio
    async def test_non_heritage_landmark_is_not_presented_as_confirmed_heritage(self, repo, tmp_path):
        """A famous but non-heritage landmark must never be confirmed as a heritage site.

        Times Square is a famous public square, not a historic monument.  The
        vision model confidently identifies the place, but the global layer
        must reject it so the result is a safe unknown instead of a confirmed
        heritage recognition.
        """
        expected_ollama = {
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
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "times_square.jpg"
        img_path.write_bytes(b"times square bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is False
        assert result.confident is False
        assert result.site_id == "unknown"
        assert result.decision == "unknown"
        assert result.recognition_source == "unknown"
        assert result.global_identification is None
        assert result.reason == REASON_NON_HERITAGE

    @pytest.mark.anyio
    async def test_non_heritage_ordinary_scene_is_rejected(self, repo, tmp_path):
        """An ordinary scene (beach, mountains, modern building) is rejected."""
        expected_ollama = {
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
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "beach.jpg"
        img_path.write_bytes(b"beach bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is False
        assert result.confident is False
        assert result.recognition_source == "unknown"
        assert result.global_identification is None
        assert result.reason == REASON_NON_HERITAGE

    @pytest.mark.anyio
    async def test_non_heritage_missing_flag_is_treated_as_rejected(self, repo, tmp_path):
        """An identified landmark without an explicit is_heritage flag is rejected.

        The flag defaults to False, so a confident identification that does
        not explicitly declare is_heritage=true must never be promoted to a
        confirmed heritage site.
        """
        expected_ollama = {
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
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "tower.jpg"
        img_path.write_bytes(b"tower bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is False
        assert result.confident is False
        assert result.recognition_source == "unknown"
        assert result.global_identification is None
        assert result.reason == REASON_NON_HERITAGE

    @pytest.mark.anyio
    async def test_global_identification_has_a_source_entry(self, repo, tmp_path):
        """A global (Ollama) identification must show a SOURCES section.

        The global vision model is itself the source of the identification.
        It is NOT an external historical source, so no verified URL is
        claimed; the label makes that explicit.
        """
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
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "hawa_mahal.jpg"
        img_path.write_bytes(b"hawa mahal bytes")

        noise_vec = _unit([0.0, 0.0, 1.0, 0.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.confirmed is True
        assert result.recognition_source == "ollama"
        assert result.citations == [
            {"source_name": "Global vision identification", "source_url": ""}
        ]

    @pytest.mark.anyio
    async def test_global_identification_does_not_claim_external_sources(self, repo, tmp_path):
        """The global result must never invent verified historical source URLs."""
        expected_ollama = {
            "identified": True,
            "site_name": "Colosseum",
            "city": "Rome",
            "country": "Italy",
            "confidence": 0.94,
            "reason": "Flavian Amphitheatre oval structure in travertine limestone",
            "uncertain": False,
            "is_heritage": True,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"message": {"role": "assistant", "content": json.dumps(expected_ollama)}},
            )

        img_path = tmp_path / "colosseum.jpg"
        img_path.write_bytes(b"colosseum bytes")

        noise_vec = _unit([0.0, 0.0, 0.0, 1.0])
        svc = _service_with_mock_ollama(repo, noise_vec, handler)
        result = await svc.recognize_async(img_path)

        assert result.recognition_source == "ollama"
        assert len(result.citations) == 1
        assert result.citations[0]["source_url"] == ""
        assert result.citations[0]["source_name"] == "Global vision identification"
