"""
Unit tests for the heritage application service layer.

Retrieval, the evidence repository and the embedding extractor are all
faked, so these run instantly with no model download and no network.
"""

import sys
from pathlib import Path

import faiss
import numpy as np
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from backend.heritage_service import (
    REASON_ANSWER_DECLINED,
    REASON_LOW_SIMILARITY,
    REASON_NO_EVIDENCE,
    REASON_UNGROUNDED_ANSWER,
    HeritageService,
    RecognitionResult,
)
from data.evidence.loader import EvidenceRepository
from ml.confidence import ConfidenceLayer, RetrievalConfig

SITES = [
    ("taj_mahal", [1.0, 0.0, 0.0, 0.0]),
    ("taj_mahal", [0.9, 0.1, 0.0, 0.0]),
    ("red_fort", [0.0, 1.0, 0.0, 0.0]),
    ("red_fort", [0.0, 0.9, 0.1, 0.0]),
]
IMAGE_IDS = ["taj_mahal_01", "taj_mahal_02", "red_fort_01", "red_fort_02"]
PATHS = [f"data/raw/{i.rsplit('_', 1)[0]}/{i}.jpg" for i in IMAGE_IDS]

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
}, {
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
}]

EVIDENCE = [{
    "site_id": "taj_mahal",
    "claim": "The Taj Mahal is a white marble mausoleum commissioned in 1632 by Shah Jahan.",
    "source_name": "UNESCO",
    "source_url": "https://whc.unesco.org/en/list/252",
}, {
    "site_id": "taj_mahal",
    "claim": "The monument is located in Agra, Uttar Pradesh, India.",
    "source_name": "ASI",
    "source_url": "https://asi.nic.in/monuments",
}, {
    "site_id": "red_fort",
    "claim": "The Red Fort was the primary residence of Mughal emperors from 1648 to 1857.",
    "source_name": "UNESCO",
    "source_url": "https://whc.unesco.org/en/list/231",
}]


class _FakeExtractor:
    """Returns a fixed embedding and records the paths it was given."""

    def __init__(self, embedding):
        self.embedding = np.asarray(embedding, dtype=np.float32)
        self.paths = []

    def extract(self, path):
        self.paths.append(str(path))
        return self.embedding


class _ScriptedProvider:
    def __init__(self, response):
        self.response = response

    def generate(self, question, context):
        return self.response


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


def _repo(tmp_path):
    import json

    meta = tmp_path / "m.json"
    ev = tmp_path / "e.json"
    meta.write_text(json.dumps(METADATA))
    ev.write_text(json.dumps(EVIDENCE))
    return EvidenceRepository(meta, ev)


@pytest.fixture
def repo(tmp_path):
    return _repo(tmp_path)


def _service(repo, embedding, provider=None, top_k=5):
    return HeritageService(
        confidence_layer=_layer(),
        repository=repo,
        extractor=_FakeExtractor(embedding),
        provider=provider,
        top_k=top_k,
    )


class TestRecognizeKnownSite:
    def test_returns_site_similarity_and_decision(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0])
        r = svc.recognize("query.jpg")
        assert isinstance(r, RecognitionResult)
        assert r.site_id == "taj_mahal"
        assert r.similarity == pytest.approx(1.0, abs=1e-4)
        assert r.confident is True
        assert r.decision == "match"

    def test_returns_site_metadata(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0])
        r = svc.recognize("query.jpg")
        assert r.metadata["name"] == "Taj Mahal"
        assert r.metadata["location"] == "Agra"
        assert r.metadata["historical_period"] == "Mughal Empire (17th century)"

    def test_returns_retrieved_evidence(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0])
        r = svc.recognize("query.jpg")
        assert len(r.evidence["claims"]) == 2
        assert len(r.evidence["source_names"]) == 2
        assert "https://whc.unesco.org/en/list/252" in r.evidence["source_urls"]

    def test_accepts_image_path_and_passes_it_to_extractor(self, repo):
        extractor = _FakeExtractor([1.0, 0.0, 0.0, 0.0])
        svc = HeritageService(_layer(), repo, extractor=extractor)
        svc.recognize("some/photo.jpg")
        assert extractor.paths == ["some/photo.jpg"]

    def test_accepts_precomputed_embedding(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0])
        r = svc.recognize(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32))
        assert r.site_id == "taj_mahal"


class TestTopK:
    def test_default_top_k_is_used(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0], top_k=2)
        r = svc.recognize("q.jpg")
        assert r.top_k == 2
        assert len(r.matches) == 2

    def test_explicit_top_k_overrides_default(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0], top_k=5)
        r = svc.recognize("q.jpg", top_k=3)
        assert r.top_k == 3
        assert len(r.matches) == 3

    def test_top_k_is_clamped_to_index_size(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0], top_k=5)
        r = svc.recognize("q.jpg", top_k=99)
        assert len(r.matches) == 4

    def test_matches_are_ranked_by_similarity(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0], top_k=4)
        r = svc.recognize("q.jpg")
        scores = [m["similarity"] for m in r.matches]
        assert scores == sorted(scores, reverse=True)
        assert r.matches[0]["site_id"] == "taj_mahal"


class TestGroundedAnswer:
    def test_grounded_answer_and_citations_returned(self, repo):
        claim = EVIDENCE[0]["claim"]
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0], _ScriptedProvider(claim))
        r = svc.recognize("q.jpg", "Who commissioned it?")
        assert r.answer == claim
        assert r.is_grounded is True
        assert r.reason is None
        assert r.citations
        assert r.citations[0]["source_url"] == "https://whc.unesco.org/en/list/252"

    def test_no_question_still_identifies_the_site(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0])
        r = svc.recognize("q.jpg")
        assert r.site_id == "taj_mahal"
        assert r.answer is None

    def test_fabricated_answer_is_never_surfaced(self, repo):
        fabricated = "The Taj Mahal was built by aliens in 4000 BC."
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0], _ScriptedProvider(fabricated))
        r = svc.recognize("q.jpg", "Who built it?")
        assert r.answer is None
        assert r.is_grounded is False
        assert r.reason == REASON_UNGROUNDED_ANSWER

    def test_provider_abstention_reports_reason(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0], _ScriptedProvider(None))
        r = svc.recognize("q.jpg", "How many tourists in 2023?")
        assert r.answer is None
        assert r.reason == REASON_ANSWER_DECLINED


class TestRejection:
    def test_low_similarity_is_rejected(self, repo):
        noise = _unit([0.3, 0.4, 0.5, 0.6])
        svc = _service(repo, noise)
        r = svc.recognize("q.jpg")
        assert r.site_id == "unknown"
        assert r.decision == "unknown"
        assert r.confident is False
        assert r.reason == REASON_LOW_SIMILARITY

    def test_rejected_result_has_no_metadata_or_evidence(self, repo):
        noise = _unit([0.3, 0.4, 0.5, 0.6])
        svc = _service(repo, noise)
        r = svc.recognize("q.jpg")
        assert r.metadata == {}
        assert r.evidence == {}
        assert r.answer is None
        assert r.citations == []

    def test_site_without_evidence_reports_no_evidence(self, repo):
        # a confident match on a site the evidence store does not know
        layer = _layer()
        layer._site_ids = ["unknown_site"] * 4
        svc = HeritageService(layer, repo, extractor=_FakeExtractor([1.0, 0, 0, 0]))
        r = svc.recognize("q.jpg")
        assert r.confident is True
        assert r.reason == REASON_NO_EVIDENCE
        assert r.answer is None


class TestResultShape:
    def test_to_dict_is_serialisable(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0], _ScriptedProvider(EVIDENCE[0]["claim"]))
        d = svc.recognize("q.jpg", "Who built it?").to_dict()
        import json
        json.dumps(d)
        for key in (
            "site_id", "similarity", "confident", "decision", "matches",
            "metadata", "evidence", "answer", "citations", "reason",
        ):
            assert key in d

    def test_rejects_invalid_query_type(self, repo):
        svc = _service(repo, [1.0, 0.0, 0.0, 0.0])
        with pytest.raises(TypeError):
            svc.recognize(12345)

    def test_service_without_extractor_rejects_image_query(self, repo):
        svc = HeritageService(_layer(), repo, extractor=None)
        with pytest.raises(RuntimeError):
            svc.recognize("q.jpg")

    def test_threshold_is_configurable(self, repo):
        extractor = _FakeExtractor(_unit([0.6, 0.5, 0.3, 0.2]))
        strict = HeritageService(_layer(threshold=0.99), repo, extractor=extractor)
        assert strict.recognize("q.jpg").reason == REASON_LOW_SIMILARITY
