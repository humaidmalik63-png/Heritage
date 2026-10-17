"""
Tests for the grounded answer generator.

A mocked provider is used throughout; no network access occurs.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.evidence.loader import EvidenceRepository
from rag.retriever import retrieve_context
from rag.generator import (
    EchoProvider,
    GroundedAnswer,
    Provider,
    generate_answer,
)


class _MockProvider:
    """Provider stub returning a scripted response."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, question, context):
        self.calls.append((question, context))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class TestGenerateAnswer:
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
        self.ctx = retrieve_context("taj_mahal", "", self.repo)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_provider_protocol(self):
        assert isinstance(EchoProvider(), Provider)
        assert isinstance(_MockProvider("x"), Provider)

    def test_answer_from_context_with_sources(self):
        provider = _MockProvider(self.ctx.claims[0])
        ans = generate_answer("Who built it?", self.ctx, provider)
        assert isinstance(ans, GroundedAnswer)
        assert ans.is_grounded is True
        assert ans.answer == self.ctx.claims[0]
        assert ans.source_names == ["UNESCO", "ASI"]
        assert ans.source_urls[0] == "https://whc.unesco.org/en/list/252"

    def test_answer_sources_scoped_to_relevant_claim(self):
        ctx = retrieve_context("taj_mahal", "Where is it located?", self.repo)
        provider = _MockProvider(ctx.relevant_claims[0])
        ans = generate_answer("Where is it located?", ctx, provider)
        assert ans.is_grounded is True
        assert ans.source_names == ["ASI"]
        assert ans.source_urls == ["https://asi.nic.in/monuments"]

    def test_ungrounded_provider_output_is_rejected(self):
        fabricated = "The Taj Mahal was built by aliens in 4000 BC."
        provider = _MockProvider(fabricated)
        ans = generate_answer("Who built it?", self.ctx, provider)
        assert ans.is_grounded is False
        assert ans.reason == "ungrounded_answer"
        assert ans.source_names == []
        assert ans.source_urls == []
        # the rejected text is preserved for the validator to inspect, but it
        # is never marked grounded or cited
        assert ans.answer == fabricated

    def test_none_provider_output_declines(self):
        ans = generate_answer("Who built it?", self.ctx, _MockProvider(None))
        assert ans.is_grounded is False
        assert ans.reason == "no_supporting_claim"

    def test_empty_provider_output_declines(self):
        ans = generate_answer("Who built it?", self.ctx, _MockProvider("   "))
        assert ans.is_grounded is False

    def test_provider_exception_declines_safely(self):
        ans = generate_answer("Who built it?", self.ctx, _MockProvider(RuntimeError("boom")))
        assert ans.is_grounded is False
        assert ans.reason == "provider_error"

    def test_unknown_site_declines(self):
        ctx = retrieve_context("not_a_site", "", self.repo)
        ans = generate_answer("Who built it?", ctx, _MockProvider("anything"))
        assert ans.is_grounded is False
        assert ans.reason == "unknown_site"
        assert ans.site_id == "unknown"
        assert "does not contain" in ans.answer

    def test_site_without_evidence_declines(self):
        with open(self.evidence_path, "w") as f:
            json.dump([], f)
        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        ctx = retrieve_context("taj_mahal", "", repo)
        ans = generate_answer("Who built it?", ctx, _MockProvider("anything"))
        assert ans.is_grounded is False
        assert ans.reason == "no_evidence"

    def test_default_provider_is_offline_and_grounded(self):
        ans = generate_answer("Who built it?", self.ctx)
        assert ans.is_grounded is True
        assert ans.answer in self.ctx.claims
        assert ans.source_urls

    def test_to_dict(self):
        provider = _MockProvider(self.ctx.claims[0])
        ans = generate_answer("Who built it?", self.ctx, provider)
        d = ans.to_dict()
        assert d["site_id"] == "taj_mahal"
        assert d["is_grounded"] is True
        assert len(d["source_names"]) == 2
