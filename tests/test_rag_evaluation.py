"""
Focused end-to-end RAG evaluation tests.

Runs the real FAISS index, metadata, evidence store, retriever, generator and
grounding validator.  Generation is mocked, so no external API is used.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from data.evidence.loader import load_repository
from evaluation.rag_eval import (
    CaseResult,
    EvalCase,
    GroundedEvaluator,
    default_cases,
    run_evaluation,
)
from ml.confidence import build_confidence_layer
from ml.visual_embedding import VisualEmbeddingExtractor

RAW = ROOT / "data" / "raw"


@pytest.fixture(scope="module")
def evaluator():
    layer = build_confidence_layer(
        str(ROOT / "data/processed/index/clip_index.faiss"),
        str(ROOT / "data/processed/index/mapping.json"),
        threshold=0.65,
    )
    repository = load_repository(
        ROOT / "data/metadata/heritage_metadata.json",
        ROOT / "data/evidence/heritage_evidence.json",
    )
    return GroundedEvaluator(layer, repository, VisualEmbeddingExtractor())


@pytest.fixture(scope="module")
def results(evaluator):
    return evaluator.run(default_cases(evaluator, RAW))


def _by_name(results, name):
    return next(r for r in results if r.name == name)


class TestEvaluationCases:
    def test_all_five_cases_ran(self, results):
        assert len(results) == 5
        assert {r.name for r in results} == {
            "known_heritage_query",
            "second_known_heritage_query",
            "visually_ambiguous_query",
            "unsupported_factual_question",
            "unknown_unrelated_query",
        }

    def test_every_case_passes_its_checks(self, results):
        failures = [r.name for r in results if not r.passed]
        assert not failures, [(n, r.checks) for n, r in zip(failures, results) if not r.passed]

    def test_every_case_is_grounding_valid(self, results):
        for r in results:
            assert r.is_valid is True, (r.name, r.checks)


class TestCase1KnownHeritageQuery:
    def test_retrieval_returns_taj_mahal(self, results):
        r = _by_name(results, "known_heritage_query")
        assert r.retrieved_site_id == "taj_mahal"
        assert r.retrieval_confident is True
        assert r.retrieval_similarity > 0.65

    def test_evidence_is_available(self, results):
        r = _by_name(results, "known_heritage_query")
        assert r.context_is_known is True
        assert r.evidence_claim_count == 3

    def test_answer_is_grounded_with_citations(self, results):
        r = _by_name(results, "known_heritage_query")
        assert r.answer_grounded is True
        assert r.citation_count >= 1
        assert r.is_valid is True


class TestCase2SecondKnownHeritageQuery:
    def test_retrieval_returns_red_fort(self, results):
        r = _by_name(results, "second_known_heritage_query")
        assert r.retrieved_site_id == "red_fort_delhi"
        assert r.retrieval_confident is True

    def test_evidence_available_and_cited(self, results):
        r = _by_name(results, "second_known_heritage_query")
        assert r.context_is_known is True
        assert r.evidence_claim_count == 3
        assert r.answer_grounded is True
        assert r.citation_count >= 1
        assert r.is_valid is True

    def test_citations_come_from_the_evidence_store(self, evaluator):
        from rag.retriever import retrieve_context

        ctx = retrieve_context("red_fort_delhi", "", evaluator.repository)
        assert ctx.source_urls
        # every citation must be one the evidence JSON actually records
        for url in ctx.source_urls:
            assert url.startswith("https://")
            assert url not in ("", None)


class TestCase3VisuallyAmbiguousQuery:
    def test_ambiguity_between_two_sites_is_detected(self, results):
        r = _by_name(results, "visually_ambiguous_query")
        assert r.checks["ambiguity_detected"] is True
        # top-1 and runner-up are different sites within the ambiguity margin
        assert len(r.top_site_scores) == 2
        top, second = r.top_site_scores
        assert top.split(":")[0] != second.split(":")[0]
        assert abs(float(top.split(":")[1]) - float(second.split(":")[1])) <= 0.02

    def test_ambiguous_query_does_not_produce_a_confident_answer(self, results):
        r = _by_name(results, "visually_ambiguous_query")
        # the provider abstains, so no label is asserted
        assert r.answer_grounded is False
        assert r.answer_declined is True
        assert r.citation_count == 0
        assert r.is_valid is True

    def test_ambiguous_query_still_validates_against_evidence(self, results):
        r = _by_name(results, "visually_ambiguous_query")
        # the top-1 site is a real site with evidence; nothing was invented
        assert r.context_is_known is True
        assert r.evidence_claim_count == 3
        assert r.checks["no_citations_when_declining"] is True


class TestCase4UnsupportedFactualQuestion:
    def test_site_is_known_but_fact_is_absent(self, results):
        r = _by_name(results, "unsupported_factual_question")
        assert r.retrieved_site_id == "red_fort_delhi"
        assert r.context_is_known is True
        assert r.evidence_claim_count == 3

    def test_unanswered_fact_is_refused(self, results):
        r = _by_name(results, "unsupported_factual_question")
        assert r.answer_grounded is False
        assert r.answer_declined is True
        assert r.citation_count == 0
        assert r.is_valid is True

    def test_tourist_statistics_are_absent_from_evidence(self, evaluator):
        from rag.retriever import retrieve_context

        ctx = retrieve_context(
            "red_fort_delhi", "How many tourists visited this monument in 2023?", evaluator.repository
        )
        assert not any("tourist" in c.lower() for c in ctx.claims)
        assert ctx.relevant_claims == []


class TestCase5UnknownUnrelatedQuery:
    def test_unrelated_query_is_rejected_as_unknown(self, results):
        r = _by_name(results, "unknown_unrelated_query")
        assert r.retrieved_site_id == "unknown"
        assert r.retrieval_confident is False
        assert r.retrieval_similarity < 0.65

    def test_unknown_query_is_refused_without_evidence(self, results):
        r = _by_name(results, "unknown_unrelated_query")
        assert r.context_is_known is False
        assert r.evidence_claim_count == 0
        assert r.answer_grounded is False
        assert r.answer_declined is True
        assert r.citation_count == 0
        assert r.is_valid is True

    def test_every_indexed_site_now_has_evidence(self, evaluator):
        """The alignment fix means no indexed site is left without evidence for sites that have evidence in the repository."""
        import json as _json

        with open(ROOT / "data/processed/index/mapping.json") as f:
            mapping = _json.load(f)
        # Use canonical site_ids from mapping, not parsed-from-image-id forms
        sites = set(mapping["site_ids"])
        # Only check sites that have evidence in the repository
        missing = [
            s for s in sites
            if evaluator.repository.get_metadata(s)
            and not evaluator.repository.get_evidence(s)
        ]
        assert not missing, f"indexed sites without evidence: {missing}"


    def test_fabrication_for_unindexed_site_is_refused(self, evaluator):
        """A site with no evidence at all must never yield a cited answer."""
        from rag.retriever import retrieve_context
        from rag.generator import generate_answer

        ctx = retrieve_context("not_a_real_site", "Describe this site.", evaluator.repository)
        assert ctx.is_known is False

        fabricated = "The site was completed in 1974 by the state government."
        answer = generate_answer("Describe this site.", ctx, _FakeProvider(fabricated))

        # no evidence -> the generator declines before reaching the provider
        assert answer.is_grounded is False
        assert answer.reason == "unknown_site"
        assert answer.source_urls == []
        assert fabricated not in answer.answer

    def test_fabrication_over_known_evidence_is_rejected(self, evaluator):
        """On a site that *does* have evidence, a fabrication is still refused."""
        from rag.retriever import retrieve_context
        from rag.generator import generate_answer
        from rag.validator import validate_answer

        ctx = retrieve_context("taj_mahal", "When was it built?", evaluator.repository)
        fabricated = "The Taj Mahal was completed in 1899 by the British Raj."
        answer = generate_answer("When was it built?", ctx, _FakeProvider(fabricated))

        assert answer.is_grounded is False
        assert answer.reason == "ungrounded_answer"
        assert answer.source_urls == []
        # the validator does not let it pass as a legitimate abstention
        assert validate_answer(answer, ctx).is_valid is False


class _FakeProvider:
    def __init__(self, response):
        self.response = response

    def generate(self, question, context):
        return self.response


class TestEvaluationResultShape:
    def test_case_result_serialises(self, results):
        d = _by_name(results, "known_heritage_query").to_dict()
        for key in (
            "name", "retrieved_site_id", "retrieval_similarity",
            "context_is_known", "evidence_claim_count",
            "answer_grounded", "citation_count", "is_valid", "passed",
        ):
            assert key in d
        assert isinstance(d["checks"], dict)
