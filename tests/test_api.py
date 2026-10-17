"""
Focused API tests.

The service layer is faked, so these exercise routing, validation, response
shaping and error handling only -- no model, index or network access.
"""

import base64
import io
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from backend.heritage_service import (
    REASON_LOW_SIMILARITY,
    REASON_NO_EVIDENCE,
    HeritageService,
    RecognitionResult,
)
from backend import api as api_module

import faiss
import numpy as np

from data.evidence.loader import EvidenceRepository
from ml.confidence import ConfidenceLayer, RetrievalConfig

METADATA = [{
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
}]
EVIDENCE = [{
    "site_id": "taj_mahal",
    "claim": "The Taj Mahal is a white marble mausoleum commissioned in 1632 by Shah Jahan.",
    "source_name": "UNESCO",
    "source_url": "https://whc.unesco.org/en/list/252",
}]

IMAGE_IDS = ["taj_mahal_01", "taj_mahal_02"]
PATHS = ["data/raw/taj_mahal/taj_mahal_01.jpg"] * 2


class _StubExtractor:
    """Embeds by returning a fixed vector, or raising for a 'bad' marker."""

    def __init__(self, embedding, fail_on=None):
        self.embedding = np.asarray(embedding, dtype=np.float32)
        self.fail_on = fail_on
        self.seen = []

    def extract(self, path):
        self.seen.append(str(path))
        if self.fail_on and self.fail_on in str(path):
            raise ValueError("Cannot open image: truncated file")
        return self.embedding


class _StubProvider:
    def __init__(self, response):
        self.response = response

    def generate(self, question, context):
        return self.response


def _repo(tmp_path):
    meta = tmp_path / "m.json"
    ev = tmp_path / "e.json"
    meta.write_text(json.dumps(METADATA))
    ev.write_text(json.dumps(EVIDENCE))
    return EvidenceRepository(meta, ev)


def _service(repo, embedding=(1.0, 0.0, 0.0, 0.0), provider=None, fail_on=None,
             index_vectors=None, threshold=0.65):
    # Default index vectors are *not* orthonormal against the query, so a
    # wrong-direction query genuinely scores low.
    if index_vectors is None:
        index_vectors = [[0.95, 0.30, 0.0, 0.0], [0.90, 0.40, 0.10, 0.0]]

    vectors = np.asarray(index_vectors, dtype=np.float32)
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    layer = ConfidenceLayer(
        index, IMAGE_IDS, PATHS, RetrievalConfig(similarity_threshold=threshold)
    )
    return HeritageService(
        confidence_layer=layer,
        repository=repo,
        extractor=_StubExtractor(embedding, fail_on=fail_on),
        provider=provider,
    )


@pytest.fixture
def client(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    api_module.set_service(_service(repo, provider=_StubProvider(EVIDENCE[0]["claim"])))
    monkeypatch.chdir(ROOT)
    with TestClient(api_module.app, raise_server_exceptions=False) as c:
        yield c
    api_module.set_service(None)


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / "query.png"
    Image.new("RGB", (32, 32), (255, 0, 0)).save(path)
    return path


def _b64():
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (0, 255, 0)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service_ready"] is True
        assert body["index_size"] == 2
        assert body["similarity_threshold"] == 0.65

    def test_health_reports_degraded_when_service_unavailable(self, client, monkeypatch):
        def boom():
            raise RuntimeError("no index")

        monkeypatch.setattr(api_module, "get_service", boom)
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "degraded"
        assert r.json()["service_ready"] is False


class TestRecognizeSuccess:
    def test_recognize_by_path(self, client, image_file):
        r = client.post("/recognize", json={"image_path": str(image_file)})
        assert r.status_code == 200
        body = r.json()
        assert body["site_id"] == "taj_mahal"
        assert body["confident"] is True
        assert body["decision"] == "match"
        assert body["similarity"] > 0.65

    def test_recognize_includes_metadata(self, client, image_file):
        body = client.post(
            "/recognize", json={"image_path": str(image_file)}
        ).json()
        assert body["metadata"]["name"] == "Taj Mahal"
        assert body["metadata"]["location"] == "Agra"

    def test_recognize_includes_evidence(self, client, image_file):
        body = client.post(
            "/recognize", json={"image_path": str(image_file)}
        ).json()
        assert len(body["evidence"]["claims"]) == 1
        assert "https://whc.unesco.org/en/list/252" in body["evidence"]["source_urls"]

    def test_recognize_with_question_returns_grounded_answer(self, client, image_file):
        body = client.post("/recognize", json={
            "image_path": str(image_file),
            "question": "Who commissioned it?",
        }).json()
        assert body["answer"] == EVIDENCE[0]["claim"]
        assert body["is_grounded"] is True
        assert body["citations"][0]["source_url"].startswith("https://")

    def test_recognize_by_base64(self, client):
        r = client.post("/recognize", json={"image_base64": _b64()})
        assert r.status_code == 200
        assert r.json()["site_id"] == "taj_mahal"

    def test_recognize_accepts_data_url_prefix(self, client):
        r = client.post(
            "/recognize",
            json={"image_base64": f"data:image/png;base64,{_b64()}"},
        )
        assert r.status_code == 200
        assert r.json()["site_id"] == "taj_mahal"

    def test_top_k_is_configurable(self, client, image_file):
        body = client.post("/recognize", json={
            "image_path": str(image_file), "top_k": 1,
        }).json()
        assert body["top_k"] == 1
        assert len(body["matches"]) == 1

    def test_response_is_json_serialisable(self, client, image_file):
        r = client.post("/recognize", json={"image_path": str(image_file)})
        json.dumps(r.json())


class TestUnknownAndLowConfidence:
    def test_low_confidence_returns_200_with_unknown(self, client, tmp_path, image_file):
        api_module.set_service(
            _service(_repo(tmp_path), embedding=(0.0, 0.0, 1.0, 0.0))
        )
        r = client.post("/recognize", json={"image_path": str(image_file)})
        assert r.status_code == 200
        body = r.json()
        assert body["site_id"] == "unknown"
        assert body["decision"] == "unknown"
        assert body["confident"] is False
        assert body["reason"] == REASON_LOW_SIMILARITY

    def test_low_confidence_has_no_answer_or_evidence(self, client, image_file, tmp_path):
        api_module.set_service(
            _service(_repo(tmp_path), embedding=(0.0, 0.0, 1.0, 0.0))
        )
        r = client.post("/recognize", json={"image_path": str(image_file)})
        body = r.json()
        assert body["answer"] is None
        assert body["metadata"] == {}
        assert body["evidence"] == {}
        assert body["citations"] == []

    def test_match_without_evidence_reports_reason(self, client, image_file, tmp_path):
        empty = tmp_path / "e2.json"
        empty.write_text(json.dumps([]))
        meta = tmp_path / "m2.json"
        meta.write_text(json.dumps(METADATA))
        api_module.set_service(
            _service(EvidenceRepository(meta, empty),
                     provider=_StubProvider("anything"))
        )
        body = client.post("/recognize", json={
            "image_path": str(image_file), "question": "Tell me about it",
        }).json()
        assert body["reason"] == REASON_NO_EVIDENCE
        assert body["answer"] is None


class TestValidation:
    def test_missing_both_inputs_is_422(self, client):
        r = client.post("/recognize", json={})
        assert r.status_code == 422

    def test_both_inputs_is_422(self, client, image_file):
        r = client.post("/recognize", json={
            "image_path": str(image_file), "image_base64": _b64(),
        })
        assert r.status_code == 422

    def test_empty_body_is_422(self, client):
        assert client.post("/recognize", json=None).status_code in (422, 400)

    def test_top_k_out_of_range_is_422(self, client, image_file):
        assert client.post("/recognize", json={
            "image_path": str(image_file), "top_k": 0,
        }).status_code == 422
        assert client.post("/recognize", json={
            "image_path": str(image_file), "top_k": 999,
        }).status_code == 422

    def test_top_k_wrong_type_is_422(self, client, image_file):
        assert client.post("/recognize", json={
            "image_path": str(image_file), "top_k": "many",
        }).status_code == 422

    def test_missing_file_is_404(self, client, tmp_path):
        r = client.post("/recognize", json={
            "image_path": str(tmp_path / "nope.jpg"),
        })
        assert r.status_code == 404
        assert r.json()["error"] == "not_found"

    def test_invalid_base64_is_400(self, client):
        r = client.post("/recognize", json={"image_base64": "!!!not-base64!!!"})
        assert r.status_code == 400
        assert r.json()["error"] == "invalid_input"

    def test_empty_base64_is_400(self, client):
        assert client.post(
            "/recognize", json={"image_base64": ""}
        ).status_code == 422

    def test_corrupt_image_is_422(self, client, tmp_path):
        # the real service raises ValueError for an undecodable image; the stub
        # reproduces that for any path containing "corrupt"
        bad = tmp_path / "corrupt.jpg"
        bad.write_bytes(b"this is not an image")
        api_module.set_service(
            _service(_repo(tmp_path), fail_on="corrupt")
        )
        r = client.post("/recognize", json={"image_path": str(bad)})
        assert r.status_code == 422
        assert r.json()["error"] == "unprocessable_image"


class TestErrorSafety:
    def test_unexpected_error_returns_500_without_traceback(self, client, image_file, monkeypatch):
        class Boom:
            confidence_layer = None

            def recognize(self, *a, **k):
                raise MemoryError("secret internal detail")

        api_module.set_service(Boom())
        r = client.post("/recognize", json={"image_path": str(image_file)})
        assert r.status_code == 500
        body = r.json()
        assert body["error"] == "internal_error"
        text = json.dumps(body).lower()
        assert "traceback" not in text
        assert "secret internal detail" not in text
        assert "memoryerror" not in text

    def test_service_unavailable_returns_503(self, client, image_file, monkeypatch):
        def boom():
            raise RuntimeError("no index")

        monkeypatch.setattr(api_module, "get_service", boom)
        r = client.post("/recognize", json={"image_path": str(image_file)})
        assert r.status_code == 503
        assert r.json()["error"] == "internal_error"

    def test_no_logical_duplication_in_api_module(self, client):
        """The API must delegate, not reimplement, pipeline logic."""
        source = (ROOT / "backend" / "api.py").read_text(encoding="utf-8")
        for banned in ("faiss.", "np.linalg", "IndexFlatIP", "get_image_features"):
            assert banned not in source, f"API duplicates logic: {banned}"
