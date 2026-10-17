"""
Tests for the site context builder.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.evidence.context import (
    SiteContext,
    build_site_context,
    UNKNOWN_SITE_ID,
)
from data.evidence.loader import EvidenceRepository


class TestBuildSiteContext:
    """Test build_site_context."""

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
                "claim": "Commissioned in 1632 by Shah Jahan.",
                "source_name": "UNESCO",
                "source_url": "https://whc.unesco.org/en/list/252",
            },
            {
                "site_id": "taj_mahal",
                "claim": "Located in Agra, India.",
                "source_name": "ASI",
                "source_url": "https://asi.nic.in/monuments",
            },
        ]

        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f)
        with open(self.evidence_path, "w") as f:
            json.dump(evidence, f)

        self.repo = EvidenceRepository(self.metadata_path, self.evidence_path)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_known_site_metadata(self):
        ctx = build_site_context("taj_mahal", self.repo)
        assert ctx.is_known is True
        assert ctx.site_id == "taj_mahal"
        assert ctx.name == "Taj Mahal"
        assert ctx.location == "Agra"
        assert ctx.state == "Uttar Pradesh"
        assert ctx.country == "India"
        assert ctx.category == "monument"

    def test_known_site_historical_info(self):
        ctx = build_site_context("taj_mahal", self.repo)
        assert ctx.historical_period == "Mughal Empire (17th century)"
        assert ctx.description == "A white marble mausoleum."
        assert ctx.preservation_context == "UNESCO World Heritage Site"

    def test_known_site_claims_and_sources(self):
        ctx = build_site_context("taj_mahal", self.repo)
        assert len(ctx.claims) == 2
        assert ctx.claims[0] == "Commissioned in 1632 by Shah Jahan."
        assert ctx.source_names == ["UNESCO", "ASI"]
        assert ctx.source_urls[0] == "https://whc.unesco.org/en/list/252"

    def test_unknown_site_is_safe(self):
        ctx = build_site_context("does_not_exist", self.repo)
        assert isinstance(ctx, SiteContext)
        assert ctx.is_known is False
        assert ctx.site_id == UNKNOWN_SITE_ID
        assert ctx.name == ""
        assert ctx.claims == []
        assert ctx.source_names == []
        assert ctx.source_urls == []

    def test_to_dict(self):
        ctx = build_site_context("taj_mahal", self.repo)
        d = ctx.to_dict()
        assert d["site_id"] == "taj_mahal"
        assert d["is_known"] is True
        assert d["name"] == "Taj Mahal"
        assert len(d["source_urls"]) == 2

    def test_known_site_without_evidence(self):
        metadata = [dict(id="solo_site", **{k: v for k, v in
                         json.load(open(self.metadata_path))[0].items() if k != "id"})]
        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f)
        with open(self.evidence_path, "w") as f:
            json.dump([], f)

        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        ctx = build_site_context("solo_site", repo)
        assert ctx.is_known is True
        assert ctx.claims == []
        assert ctx.source_names == []
