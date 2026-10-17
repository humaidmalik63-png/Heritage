"""
Tests that the FAISS index and the evidence store cover the same site_ids.

The RAG evaluation showed three indexed sites had no evidence, so the
pipeline could never answer for them.  These tests pin the two lists together.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from data.evidence.loader import load_repository
from data.evidence.context import build_site_context
from rag.retriever import retrieve_context

MAPPING = ROOT / "data/processed/index/mapping.json"
METADATA = ROOT / "data/metadata/heritage_metadata.json"
EVIDENCE = ROOT / "data/evidence/heritage_evidence.json"

EXPECTED_SITES = {
    "taj_mahal",
    "qutub_minar",
    "red_fort",
    "ajanta_caves",
    "konark_sun_temple",
    "jama_masjid",
}


def _index_site_ids():
    with open(MAPPING) as f:
        mapping = json.load(f)
    return {iid.rsplit("_", 1)[0] for iid in mapping["image_ids"]}


@pytest.fixture(scope="module")
def repo():
    return load_repository(METADATA, EVIDENCE)


class TestIndexEvidenceAlignment:
    def test_index_has_the_five_expected_sites(self):
        assert _index_site_ids() == EXPECTED_SITES

    def test_every_indexed_site_has_evidence(self, repo):
        missing = [s for s in EXPECTED_SITES if not repo.get_evidence(s)]
        assert not missing, f"indexed sites without evidence: {missing}"

    def test_every_indexed_site_has_metadata(self, repo):
        missing = [s for s in EXPECTED_SITES if repo.get_metadata(s) is None]
        assert not missing, f"indexed sites without metadata: {missing}"

    def test_all_six_sites_have_evidence(self, repo):
        assert sum(1 for s in EXPECTED_SITES if repo.get_evidence(s)) == 6

    def test_every_evidence_entry_has_required_fields(self, repo):
        for site in EXPECTED_SITES:
            for ev in repo.get_evidence(site):
                assert ev.site_id == site
                assert ev.claim.strip()
                assert ev.source_name.strip()
                assert ev.source_url.startswith("https://")

    def test_existing_evidence_preserved(self, repo):
        # taj_mahal and red_fort keep their original, pre-existing claims
        taj = {e.source_url for e in repo.get_evidence("taj_mahal")}
        red = {e.source_url for e in repo.get_evidence("red_fort")}
        assert "https://whc.unesco.org/en/list/252" in taj
        assert "https://asi.nic.in/monuments" in taj
        assert "https://whc.unesco.org/en/list/231" in red
        assert "https://india.gov.in" in red

    def test_new_sites_use_the_existing_schema(self):
        with open(EVIDENCE) as f:
            records = json.load(f)
        for record in records:
            assert set(record) == {"site_id", "claim", "source_name", "source_url"}

    def test_every_indexed_site_yields_a_context(self, repo):
        for site in EXPECTED_SITES:
            ctx = build_site_context(site, repo)
            assert ctx.is_known is True, site
            assert ctx.name.strip(), site
            assert ctx.claims, site

    def test_every_indexed_site_is_answerable(self, repo):
        """Each indexed site must produce citable, non-empty RAG context."""
        for site in EXPECTED_SITES:
            ctx = retrieve_context(site, "", repo)
            assert ctx.is_known is True, site
            assert ctx.claims, site
            assert ctx.source_urls, site
            assert len(ctx.source_urls) == len(ctx.claims), site

    def test_no_orphan_evidence(self, repo):
        """Every evidence site_id must have matching metadata."""
        with open(EVIDENCE) as f:
            records = json.load(f)
        orphans = {r["site_id"] for r in records} - set(repo.list_sites())
        assert not orphans, f"evidence without metadata: {orphans}"
