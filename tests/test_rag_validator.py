"""
Tests for the grounding / citation validator.

A mocked provider is used to build answers; no network access occurs.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.evidence.loader import EvidenceRepository
from rag.retriever import retrieve_context
from rag.generator import GroundedAnswer, generate_answer
from rag.validator import validate_answer


class _MockProvider:
    def __init__(self, response):
        self.response = response

    def generate(self, question, context):
        return self.response


class TestValidateAnswer:
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

    # ── 1. fully grounded answer ────────────────────────────────────────────

    def test_fully_grounded_answer(self):
        ans = generate_answer("Who built it?", self.ctx, _MockProvider(self.ctx.claims[0]))
        report = validate_answer(ans, self.ctx)
        assert report.is_valid is True
        assert report.issues == []
        assert report.unsupported == []
        assert report.missing_citations == []
        assert report.invalid_citations == []
        assert report.checked_sentences == 1

    def test_fully_grounded_both_claims_with_all_citations(self):
        text = " ".join(self.ctx.claims)
        ans = GroundedAnswer(
            question="Tell me about it",
            site_id="taj_mahal",
            answer=text,
            is_grounded=True,
            source_names=["UNESCO", "ASI"],
            source_urls=[
                "https://whc.unesco.org/en/list/252",
                "https://asi.nic.in/monuments",
            ],
        )
        report = validate_answer(ans, self.ctx)
        assert report.is_valid is True, [i.to_dict() for i in report.issues]
        assert report.checked_sentences == 2

    # ── 2. partially unsupported answer ─────────────────────────────────────

    def test_partially_unsupported_answer(self):
        fabricated = "The mausoleum was secretly built by extraterrestrial engineers."
        text = " ".join([self.ctx.claims[0], fabricated])
        ans = GroundedAnswer(
            question="Who built it?",
            site_id="taj_mahal",
            answer=text,
            is_grounded=True,
            source_names=["UNESCO"],
            source_urls=["https://whc.unesco.org/en/list/252"],
        )
        report = validate_answer(ans, self.ctx)
        assert report.is_valid is False
        assert len(report.unsupported) == 1
        assert "extraterrestrial" in report.unsupported[0].sentence
        # the supported sentence is still not flagged
        assert not any("mausoleum commissioned" in i.sentence for i in report.unsupported)

    # ── 3. missing citation ─────────────────────────────────────────────────

    def test_missing_citation(self):
        ans = GroundedAnswer(
            question="Who built it?",
            site_id="taj_mahal",
            answer=self.ctx.claims[0],
            is_grounded=True,
            source_names=[],
            source_urls=[],
        )
        report = validate_answer(ans, self.ctx)
        assert report.is_valid is False
        assert len(report.missing_citations) == 1
        assert "https://whc.unesco.org/en/list/252" in report.missing_citations[0].detail

    def test_partially_missing_citation(self):
        text = " ".join(self.ctx.claims)
        ans = GroundedAnswer(
            question="Tell me about it",
            site_id="taj_mahal",
            answer=text,
            is_grounded=True,
            source_names=["UNESCO"],
            source_urls=["https://whc.unesco.org/en/list/252"],
        )
        report = validate_answer(ans, self.ctx)
        assert report.is_valid is False
        assert len(report.missing_citations) == 1
        assert "asi.nic.in" in report.missing_citations[0].detail

    # ── 4. invalid citation ────────────────────────────────────────────────

    def test_invalid_citation(self):
        ans = GroundedAnswer(
            question="Who built it?",
            site_id="taj_mahal",
            answer=self.ctx.claims[0],
            is_grounded=True,
            source_names=["Fake News"],
            source_urls=["https://example.invalid/made-up"],
        )
        report = validate_answer(ans, self.ctx)
        assert report.is_valid is False
        assert len(report.invalid_citations) == 1
        assert "example.invalid" in report.invalid_citations[0].detail

    # ── 5. insufficient-evidence answer ─────────────────────────────────────

    def test_insufficient_evidence_answer_accepted(self):
        ctx = retrieve_context("taj_mahal", "zeppelin aeronautics", self.repo)
        ans = generate_answer("What about zeppelins?", ctx, _MockProvider(None))
        assert ans.is_grounded is False
        report = validate_answer(ans, ctx)
        assert report.is_valid is True
        assert report.is_abstained is True
        assert report.issues == []

    def test_insufficient_evidence_for_unknown_site_accepted(self):
        ctx = retrieve_context("not_a_site", "", self.repo)
        ans = generate_answer("Who built it?", ctx, _MockProvider(None))
        report = validate_answer(ans, ctx)
        assert report.is_valid is True
        assert report.is_abstained is True

    def test_decline_is_rejected_when_evidence_exists(self):
        ans = generate_answer("Who built it?", self.ctx, _MockProvider(None))
        report = validate_answer(ans, self.ctx)
        assert report.is_valid is False
        assert report.issues[0].kind == "insufficient_evidence"

    # ── 6. model output is never treated as evidence ───────────────────────

    def test_answer_is_not_its_own_evidence(self):
        fabricated = "The Taj Mahal was built by aliens in 4000 BC."
        ans = GroundedAnswer(
            question="Who built it?",
            site_id="taj_mahal",
            answer=fabricated,
            is_grounded=True,
            source_names=["Model"],
            source_urls=["https://whc.unesco.org/en/list/252"],
        )
        report = validate_answer(ans, self.ctx)
        assert report.is_valid is False
        assert len(report.unsupported) == 1

    def test_repeated_fabrication_is_still_unsupported(self):
        fabricated = "The Taj Mahal was built by aliens in 4000 BC."
        for _ in range(3):
            ans = GroundedAnswer(
                question="Who built it?",
                site_id="taj_mahal",
                answer=fabricated,
                is_grounded=True,
                source_names=["Model"],
                source_urls=["https://whc.unesco.org/en/list/252"],
            )
            report = validate_answer(ans, self.ctx)
            assert report.is_valid is False
            assert len(report.unsupported) == 1

    def test_none_answer_is_invalid(self):
        report = validate_answer(None, self.ctx)
        assert report.is_valid is False

    def test_report_to_dict(self):
        ans = generate_answer("Who built it?", self.ctx, _MockProvider(self.ctx.claims[0]))
        d = validate_answer(ans, self.ctx).to_dict()
        assert d["is_valid"] is True
        assert d["checked_sentences"] == 1
        assert d["issues"] == []
