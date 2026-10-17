"""
Tests for the grounded context retriever.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.evidence.loader import EvidenceRepository
from rag.retriever import GroundedContext, retrieve_context


class TestRetrieveContext:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.metadata_path = Path(self.tmpdir) / "metadata.json"
        self.evidence_path = Path(self.tmpdir) / "evidence.json"

        metadata = [
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
            {
                "site_id": "red_fort",
                "claim": "The Red Fort was the primary residence of Mughal emperors from 1648 to 1857.",
                "source_name": "UNESCO",
                "source_url": "https://whc.unesco.org/en/list/231",
            },
        ]

        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f)
        with open(self.evidence_path, "w") as f:
            json.dump(evidence, f)

        self.repo = EvidenceRepository(self.metadata_path, self.evidence_path)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_returns_site_id_and_metadata(self):
        ctx = retrieve_context("taj_mahal", repository=self.repo)
        assert ctx.site_id == "taj_mahal"
        assert ctx.is_known is True
        assert ctx.metadata["name"] == "Taj Mahal"
        assert ctx.metadata["location"] == "Agra"
        assert ctx.metadata["historical_period"] == "Mughal Empire (17th century)"

    def test_returns_claims_sources_and_urls(self):
        ctx = retrieve_context("taj_mahal", repository=self.repo)
        assert len(ctx.claims) == 2
        assert len(ctx.source_names) == 2
        assert len(ctx.source_urls) == 2
        assert ctx.source_urls[0] == "https://whc.unesco.org/en/list/252"

    def test_evidence_is_scoped_to_site(self):
        ctx = retrieve_context("red_fort", repository=self.repo)
        assert ctx.site_id == "red_fort"
        assert len(ctx.claims) == 1
        assert "Red Fort" in ctx.claims[0]
        assert not any("Taj" in c for c in ctx.claims)

    def test_no_question_keeps_all_evidence_relevant(self):
        ctx = retrieve_context("taj_mahal", repository=self.repo)
        assert ctx.relevant_claims == ctx.claims
        assert ctx.relevant_source_urls == ctx.source_urls

    def test_question_filters_relevant_evidence(self):
        ctx = retrieve_context("taj_mahal", "Where is it located?", self.repo)
        assert len(ctx.claims) == 2
        assert len(ctx.relevant_claims) == 1
        assert "Agra" in ctx.relevant_claims[0]
        assert ctx.relevant_source_names == ["ASI"]
        assert ctx.relevant_source_urls == ["https://asi.nic.in/monuments"]

    def test_question_with_no_term_match_yields_no_relevant(self):
        ctx = retrieve_context("taj_mahal", "zeppelin aeronautics", self.repo)
        assert ctx.is_known is True
        assert ctx.relevant_claims == []

    def test_unknown_site_returns_safe_empty(self):
        ctx = retrieve_context("not_a_site", repository=self.repo)
        assert isinstance(ctx, GroundedContext)
        assert ctx.is_known is False
        assert ctx.site_id == "unknown"
        assert ctx.metadata == {}
        assert ctx.claims == []
        assert ctx.source_names == []
        assert ctx.source_urls == []

    def test_empty_site_id_returns_safe_empty(self):
        ctx = retrieve_context("", repository=self.repo)
        assert ctx.is_known is False
        assert ctx.claims == []

    def test_to_dict(self):
        ctx = retrieve_context("taj_mahal", repository=self.repo)
        d = ctx.to_dict()
        assert d["site_id"] == "taj_mahal"
        assert d["is_known"] is True
        assert d["metadata"]["name"] == "Taj Mahal"
        assert len(d["source_urls"]) == 2
