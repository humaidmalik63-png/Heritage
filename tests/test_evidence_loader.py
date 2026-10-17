"""
Tests for the evidence repository loader.
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.evidence.loader import (
    SiteMetadata,
    SiteEvidence,
    EvidenceRepository,
    load_repository,
)


class TestEvidenceRepository:
    """Test evidence repository loader."""

    def setup_method(self):
        """Create temporary metadata and evidence files."""
        self.tmpdir = tempfile.mkdtemp()
        self.metadata_path = Path(self.tmpdir) / "metadata.json"
        self.evidence_path = Path(self.tmpdir) / "evidence.json"

        metadata = [
            {
                "site_id": "taj_mahal",
                "name": "Taj Mahal",
                "alternate_name": "Taj",
                "location": "Agra",
                "state": "Uttar Pradesh",
                "country": "India",
                "description": "A white marble mausoleum.",
                "historical_period": "Mughal Empire",
                "category": "monument",
                "preservation_context": "UNESCO World Heritage Site",
            },
            {
                "site_id": "red_fort",
                "name": "Red Fort",
                "alternate_name": "Lal Qila",
                "location": "Delhi",
                "state": "Delhi",
                "country": "India",
                "description": "A historic fort complex.",
                "historical_period": "Mughal Empire",
                "category": "fort",
                "preservation_context": "UNESCO World Heritage Site",
            },
        ]

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
            {
                "site_id": "red_fort",
                "claim": "Primary Mughal residence.",
                "source_name": "UNESCO",
                "source_url": "https://whc.unesco.org/en/list/231",
            },
        ]

        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f)
        with open(self.evidence_path, "w") as f:
            json.dump(evidence, f)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_load_metadata(self):
        """Test that metadata loads correctly."""
        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        meta = repo.get_metadata("taj_mahal")
        assert meta is not None
        assert meta.name == "Taj Mahal"
        assert meta.site_id == "taj_mahal"
        assert meta.category == "monument"

    def test_load_evidence(self):
        """Test that evidence loads correctly."""
        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        evidence = repo.get_evidence("taj_mahal")
        assert len(evidence) == 2
        assert all(isinstance(e, SiteEvidence) for e in evidence)
        assert evidence[0].source_name == "UNESCO"

    def test_unknown_site_returns_none(self):
        """Test that unknown site returns None for metadata."""
        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        assert repo.get_metadata("nonexistent") is None

    def test_unknown_site_returns_empty_evidence(self):
        """Test that unknown site returns empty list for evidence."""
        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        assert repo.get_evidence("nonexistent") == []

    def test_has_site(self):
        """Test has_site method."""
        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        assert repo.has_site("taj_mahal") is True
        assert repo.has_site("nonexistent") is False

    def test_list_sites(self):
        """Test list_sites method."""
        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        sites = repo.list_sites()
        assert "taj_mahal" in sites
        assert "red_fort" in sites
        assert len(sites) == 2

    def test_get_full_record(self):
        """Test get_full_record method."""
        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        record = repo.get_full_record("taj_mahal")
        assert record is not None
        assert record["metadata"].name == "Taj Mahal"
        assert len(record["evidence"]) == 2

    def test_get_full_record_unknown(self):
        """Test get_full_record for unknown site."""
        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        assert repo.get_full_record("nonexistent") is None

    def test_factory_function(self):
        """Test load_repository factory."""
        repo = load_repository(self.metadata_path, self.evidence_path)
        assert isinstance(repo, EvidenceRepository)
        assert repo.has_site("taj_mahal") is True

    def test_metadata_dataclass(self):
        """Test SiteMetadata dataclass fields."""
        meta = SiteMetadata(
            site_id="test",
            name="Test Site",
            alternate_name="Test",
            location="Test Location",
            state="Test State",
            country="Test Country",
            description="Test description.",
            historical_period="Test period",
            category="monument",
            preservation_context="Test context",
        )
        assert meta.site_id == "test"
        assert meta.category == "monument"

    def test_evidence_dataclass(self):
        """Test SiteEvidence dataclass fields."""
        ev = SiteEvidence(
            site_id="test",
            claim="Test claim.",
            source_name="Test Source",
            source_url="https://example.com",
        )
        assert ev.site_id == "test"
        assert ev.source_url == "https://example.com"


    def test_metadata_key_alias_id(self):
        """heritage_metadata.json uses "id"; it must map to site_id."""
        metadata = [{
            "id": "konark",
            "name": "Konark Sun Temple",
            "alternate_name": "Konark",
            "location": "Konark",
            "state": "Odisha",
            "country": "India",
            "description": "A 13th century temple.",
            "historical_period": "Eastern Ganga Dynasty",
            "category": "temple",
            "preservation_context": "UNESCO World Heritage Site",
        }]
        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f)

        repo = EvidenceRepository(self.metadata_path, self.evidence_path)
        meta = repo.get_metadata("konark")
        assert meta is not None
        assert meta.site_id == "konark"
        assert meta.name == "Konark Sun Temple"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])