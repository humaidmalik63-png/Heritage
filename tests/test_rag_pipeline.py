"""
Focused integration tests for the grounded RAG pipeline.

Provider behaviour is mocked throughout; no external API is used.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.evidence.loader import EvidenceRepository
from rag.generator import Provider
from rag.pipeline import GroundedPipeline


class _MockProvider:
    """Records what the generator received and returns a scripted answer."""

    def __init__(self, response):
        self.response = response
        self.received_contexts = []
        self.received_questions = []

    def generate(self, question, context):
        self.received_questions.append(question)
        self.received_contexts.append(context)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class TestGroundedPipeline:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.metadata_path = Path(self.tmpdir) / "metadata.json"
        self.evidence_path = Path(self.tmpdir) / "evidence.json"

        metadata = [{
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
        evidence = [
            {
                "site_id": "taj_mahal",
                "claim": "The Taj Mahal is a white marble mausoleum commissioned in 1632 by Shah Jahan.",
                "source_name": "UNESCO",
                "source_url": "https://whc.unesco.org/en/list/252",
            },
            {
                "site_id": "taj_mahal",
                "claim": "The monument is located in Agra, Uttar Pradesh, India.",
                "source_name": "ASI",
                "source_url": "https://asi.nic.in/monuments",
            },
        ]

        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f)
        with open(self.evidence_path, "w") as f:
            json.dump(evidence, f)

        self.repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        self.claims = [e["claim"] for e in evidence]
        self.urls = [e["source_url"] for e in evidence]

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_1_retrieves_evidence(self):
        provider = _MockProvider(self.claims[0])
        result = GroundedPipeline(self.repo, provider).run("taj_mahal", "Who built it?")
        assert result.stages == ["retrieve", "generate", "validate"]
        assert result.context.is_known is True
        assert result.context.site_id == "taj_mahal"
        assert result.context.claims == self.claims
        assert result.context.source_urls == self.urls

    def test_2_generator_receives_retrieved_evidence(self):
        provider = _MockProvider(self.claims[0])
        GroundedPipeline(self.repo, provider).run("taj_mahal", "Where is it located?")

        assert len(provider.received_contexts) == 1
        ctx = provider.received_contexts[0]
        assert ctx.site_id == "taj_mahal"
        assert ctx.claims == self.claims
        assert ctx.relevant_claims, "question must select relevant evidence"
        assert ctx.relevant_source_urls == [self.urls[1]]
        assert provider.received_questions == ["Where is it located?"]

    def test_3_generated_answer_contains_citations(self):
        provider = _MockProvider(self.claims[0])
        result = GroundedPipeline(self.repo, provider).run("taj_mahal", "Who built it?")

        assert result.answer.is_grounded is True
        assert result.answer.source_urls, "answer must carry source URLs"
        assert set(result.answer.source_urls).issubset(set(self.urls))
        assert result.answer.source_names

    def test_4_validator_checks_answer_against_retrieved_evidence(self):
        provider = _MockProvider(self.claims[0])
        result = GroundedPipeline(self.repo, provider).run("taj_mahal", "Who built it?")

        assert result.validation.checked_sentences == 1
        assert isinstance(result.is_valid, bool)

    def test_5_fully_supported_answer_is_accepted(self):
        provider = _MockProvider(self.claims[0])
        result = GroundedPipeline(self.repo, provider).run("taj_mahal", "Who built it?")

        assert result.is_valid is True, [i.to_dict() for i in result.validation.issues]
        assert result.validation.issues == []
        assert result.validation.unsupported == []
        assert result.validation.missing_citations == []
        assert result.validation.invalid_citations == []

    def test_6_unsupported_claim_is_rejected(self):
        fabricated = "The Taj Mahal was built by extraterrestrial engineers in 4000 BC."
        provider = _MockProvider(fabricated)
        result = GroundedPipeline(self.repo, provider).run("taj_mahal", "Who built it?")

        assert result.is_valid is False
        assert len(result.validation.unsupported) == 1
        assert "extraterrestrial" in result.validation.unsupported[0].sentence

    def test_unsupported_multi_sentence_answer_accepted_partially(self):
        supported = " ".join(self.claims)
        text = " ".join([supported, "It glows green at midnight."])
        provider = _MockProvider(text)
        result = GroundedPipeline(self.repo, provider).run("taj_mahal", "Tell me everything")

        assert result.is_valid is False
        assert len(result.validation.unsupported) == 1
        assert "midnight" in result.validation.unsupported[0].sentence

    def test_unknown_site_produces_safe_declination(self):
        provider = _MockProvider("Anything at all.")
        result = GroundedPipeline(self.repo, provider).run("not_a_site", "Who built it?")

        assert result.context.is_known is False
        assert result.answer.is_grounded is False
        assert result.answer.site_id == "unknown"
        assert result.answer.source_urls == []
        assert result.validation.is_abstained is True
        assert result.is_valid is True

    def test_offline_default_pipeline(self):
        result = GroundedPipeline(self.repo, None).run("taj_mahal", "Who built it?")
        assert result.answer.is_grounded is True
        assert result.is_valid is True

    def test_provider_satisfies_protocol(self):
        assert isinstance(_MockProvider("x"), Provider)

    def test_to_dict_roundtrip(self):
        provider = _MockProvider(self.claims[0])
        result = GroundedPipeline(self.repo, provider).run("taj_mahal", "Who built it?")
        d = result.to_dict()
        assert d["stages"] == ["retrieve", "generate", "validate"]
        assert d["is_valid"] is True
        assert d["context"]["site_id"] == "taj_mahal"
        assert d["answer"]["source_urls"] == list(self.urls)
        assert d["validation"]["issues"] == []
