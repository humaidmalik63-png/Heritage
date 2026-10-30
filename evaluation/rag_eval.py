"""
End-to-end RAG evaluation over the heritage dataset.

Drives the real pipeline — FAISS retrieval → confidence → evidence context →
grounded generation → grounding validation — across representative query
cases.  Language-model behaviour is supplied by a mock provider so the
evaluation runs offline and deterministically.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from data.evidence.loader import EvidenceRepository, load_repository
from ml.confidence import ConfidenceLayer, RetrievalConfig, build_confidence_layer
from ml.visual_embedding import VisualEmbeddingExtractor
from rag.generator import GroundedAnswer, generate_answer
from rag.retriever import GroundedContext, retrieve_context
from rag.validator import ValidationReport, validate_answer

__all__ = [
    "AMBIGUITY_MARGIN",
    "CaseResult",
    "EvalCase",
    "GroundedEvaluator",
    "run_evaluation",
]

# Two different sites scoring within this margin of each other are treated as
# visually ambiguous: the top-1 label alone is not a reliable answer.
AMBIGUITY_MARGIN = 0.02


@dataclass
class EvalCase:
    """One evaluation case."""

    name: str
    question: str
    image_path: Optional[str] = None
    embedding: Optional[np.ndarray] = None
    expected_site_id: str = "unknown"
    expect_evidence: bool = False
    expect_grounded: bool = False
    expect_ambiguous: bool = False
    provider_response: Optional[str] = None


@dataclass
class CaseResult:
    """Outcome of one evaluation case."""

    name: str
    question: str
    retrieved_site_id: str
    retrieval_similarity: float
    retrieval_confident: bool
    context_is_known: bool
    evidence_claim_count: int
    answer_grounded: bool
    answer_declined: bool
    citation_count: int
    is_valid: bool
    passed: bool
    top_site_scores: List[str] = field(default_factory=list)
    checks: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "question": self.question,
            "retrieved_site_id": self.retrieved_site_id,
            "retrieval_similarity": self.retrieval_similarity,
            "retrieval_confident": self.retrieval_confident,
            "top_site_scores": list(self.top_site_scores),
            "context_is_known": self.context_is_known,
            "evidence_claim_count": self.evidence_claim_count,
            "answer_grounded": self.answer_grounded,
            "answer_declined": self.answer_declined,
            "citation_count": self.citation_count,
            "is_valid": self.is_valid,
            "passed": self.passed,
            "checks": dict(self.checks),
        }


class _ScriptedProvider:
    """Mock provider returning a fixed answer, or abstaining when None."""

    def __init__(self, response: Optional[str]) -> None:
        self.response = response
        self.calls: List[GroundedContext] = []

    def generate(self, question, context):
        self.calls.append(context)
        return self.response


class GroundedEvaluator:
    """Runs evaluation cases through the full grounded RAG pipeline."""

    def __init__(
        self,
        confidence_layer: ConfidenceLayer,
        repository: EvidenceRepository,
        extractor: VisualEmbeddingExtractor,
    ) -> None:
        self.layer = confidence_layer
        self.repository = repository
        self.extractor = extractor

    def embed(self, image_path: str) -> np.ndarray:
        """Embed one image with the existing extractor."""
        return self.extractor.extract(image_path)

    def top_sites(self, query: np.ndarray, limit: int = 2) -> List[tuple]:
        """Return [(site_id, score), ...] for the best hit per site.

        This reads the confidence layer's own index, so no second retrieval
        implementation is introduced.
        """
        q = np.asarray(query, dtype=np.float32).ravel().reshape(1, -1)
        scores, indices = self.layer.index.search(
            q, min(self.layer.config.top_k, self.layer.index.ntotal)
        )
        best: Dict[str, float] = {}
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            site = self.layer._site_ids[idx]
            value = float(score)
            if site not in best or value > best[site]:
                best[site] = value
        return sorted(best.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    def run_case(self, case: EvalCase) -> CaseResult:
        """Run a single case end to end and check its expectations."""
        if case.embedding is not None:
            query = np.asarray(case.embedding, dtype=np.float32).ravel()
        elif case.image_path is not None:
            query = self.embed(case.image_path)
        else:
            raise ValueError(f"case {case.name!r} needs an image_path or embedding")

        # 1. retrieval + confidence
        retrieval = self.layer.query(query)
        site_id = retrieval.site_id

        # Ambiguity: another site scores (almost) as well as the top hit, so
        # the top-1 label alone is not a reliable answer.  This only applies to
        # a *plausible* match -- two near-zero scores are not a tie worth
        # worrying about, they are simply both irrelevant.
        top_scores = self.top_sites(query, limit=2)
        is_ambiguous = (
            len(top_scores) >= 2
            and top_scores[0][0] != top_scores[1][0]
            and top_scores[0][1] >= self.layer.config.similarity_threshold
            and (top_scores[0][1] - top_scores[1][1]) <= AMBIGUITY_MARGIN
        )

        # 2. evidence context for the retrieved site
        context = retrieve_context(site_id, case.question, self.repository)

        # 3. grounded generation (mocked provider)
        provider = _ScriptedProvider(case.provider_response)
        answer = generate_answer(case.question, context, provider)

        # 4. grounding / citation validation
        validation = validate_answer(answer, context)

        declined = not answer.is_grounded
        checks = {
            "ambiguity_detected": is_ambiguous == case.expect_ambiguous,
            "retrieved_expected_site": (
                is_ambiguous
                or site_id == case.expected_site_id
            ),
            "evidence_availability": context.is_known == case.expect_evidence,
            "answer_behavior": answer.is_grounded == case.expect_grounded,
            "grounding_valid": validation.is_valid is True,
            "citations_present_when_grounded": (
                bool(answer.source_urls) if case.expect_grounded else True
            ),
            "no_citations_when_declining": (
                not answer.source_urls if not case.expect_grounded else True
            ),
            "unknown_rejected": (
                True if not case.expect_grounded else context.is_known
            ),
        }

        return CaseResult(
            name=case.name,
            question=case.question,
            retrieved_site_id=site_id,
            retrieval_similarity=round(retrieval.similarity, 4),
            retrieval_confident=retrieval.confident,
            context_is_known=context.is_known,
            evidence_claim_count=len(context.claims),
            answer_grounded=answer.is_grounded,
            answer_declined=declined,
            citation_count=len(answer.source_urls),
            is_valid=validation.is_valid,
            passed=all(checks.values()),
            top_site_scores=[f"{s}:{round(sc, 4)}" for s, sc in top_scores],
            checks=checks,
        )

    def run(self, cases: List[EvalCase]) -> List[CaseResult]:
        return [self.run_case(c) for c in cases]


def _ambiguous_query(evaluator: GroundedEvaluator, paths: List[str]) -> np.ndarray:
    """Average of two real embeddings -> a genuinely ambiguous query."""
    vectors = [evaluator.embed(p) for p in paths]
    mean = np.mean(np.stack(vectors), axis=0)
    norm = np.linalg.norm(mean)
    return mean / norm if norm > 0 else mean


def _unrelated_query(seed: int = 123) -> np.ndarray:
    """A deterministic non-heritage vector that matches no monument."""
    rng = np.random.default_rng(seed)
    vector = rng.standard_normal(512).astype(np.float32)
    return vector / np.linalg.norm(vector)


def default_cases(evaluator: GroundedEvaluator, root: Path) -> List[EvalCase]:
    """Build the five standard evaluation cases against the real dataset."""
    taj_test = root / "taj_mahal" / "taj_mahal_03.jpg"
    red_test = root / "red_fort" / "red_fort_03.jpg"

    # A real evidence claim, used as the grounded provider response.
    taj_ctx = retrieve_context("taj_mahal", "", evaluator.repository)
    taj_claim = taj_ctx.claims[0] if taj_ctx.claims else None

    red_ctx = retrieve_context("red_fort_delhi", "", evaluator.repository)
    red_claim = red_ctx.claims[0] if red_ctx.claims else None

    # A fixed, deterministic non-heritage vector, so the "unknown" case does
    # not depend on a site that may or may not carry evidence.
    unrelated = _unrelated_query()

    ambiguous = _ambiguous_query(
        evaluator,
        [str(taj_test), str(red_test)],
    )

    return [
        EvalCase(
            name="known_heritage_query",
            question="Who commissioned the Taj Mahal?",
            image_path=str(taj_test),
            expected_site_id="taj_mahal",
            expect_evidence=True,
            expect_grounded=True,
            provider_response=taj_claim,
        ),
        EvalCase(
            name="second_known_heritage_query",
            question="Where is the Red Fort located?",
            image_path=str(red_test),
            expected_site_id="red_fort_delhi",
            expect_evidence=True,
            expect_grounded=True,
            provider_response=red_claim,
        ),
        EvalCase(
            name="visually_ambiguous_query",
            question="Which monument is this?",
            embedding=ambiguous,
            # The top-1 label lands on a real site whose evidence exists, but
            # the runner-up scores within AMBIGUITY_MARGIN of it, so the
            # evaluation records the ambiguity rather than trusting the label.
            # The pipeline must still stay grounded and never guess.
            expected_site_id="ambiguous",
            expect_evidence=True,
            expect_grounded=False,
            expect_ambiguous=True,
            provider_response=None,
        ),
        EvalCase(
            name="unsupported_factual_question",
            question="How many tourists visited this monument in 2023?",
            image_path=str(red_test),
            expected_site_id="red_fort_delhi",
            expect_evidence=True,
            expect_grounded=False,
            provider_response=None,
        ),
        EvalCase(
            name="unknown_unrelated_query",
            question="Describe this site.",
            # A non-heritage query vector: it must not clear the confidence
            # threshold for any indexed monument, so the pipeline declines.
            embedding=unrelated,
            expected_site_id="unknown",
            expect_evidence=False,
            expect_grounded=False,
            provider_response=None,
        ),
    ]


def run_evaluation(
    index_path: str = "data/processed/index/clip_index.faiss",
    mapping_path: str = "data/processed/index/mapping.json",
    metadata_path: str = "data/metadata/heritage_metadata.json",
    evidence_path: str = "data/evidence/heritage_evidence.json",
    root: str = "data/raw",
    threshold: float = 0.65,
) -> List[CaseResult]:
    """Run the standard five-case evaluation against the real dataset."""
    layer = build_confidence_layer(index_path, mapping_path, threshold=threshold)
    repository = load_repository(metadata_path, evidence_path)
    evaluator = GroundedEvaluator(layer, repository, VisualEmbeddingExtractor())
    return evaluator.run(default_cases(evaluator, Path(root)))
