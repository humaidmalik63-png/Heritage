"""
Application service layer.

Exposes the heritage recognition + grounded RAG pipeline through a single
internal interface.  This module is transport-agnostic: it contains no HTTP
framework, no framework-specific types, and no LLM credentials.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import concurrent.futures
import logging
import os
import numpy as np

from data.evidence.loader import EvidenceRepository, load_repository
from ml.confidence import ConfidenceLayer, RetrievalConfig, build_confidence_layer
from ml.open_set import OpenSetDecision, OpenSetRejection
from ml.visual_embedding import VisualEmbeddingExtractor
from backend.gemini import (
    GeminiVisionClient,
    GeminiVisionResult,
)
from backend.ollama import (
    OllamaVisionClient,
    OllamaVisionResult,
    REASON_NON_HERITAGE,
)
from rag.generator import Provider
from rag.pipeline import GroundedPipeline, PipelineResult

logger = logging.getLogger(__name__)

__all__ = [
    "DEFAULT_TOP_K",
    "REASON_LOW_SIMILARITY",
    "REASON_NO_EVIDENCE",
    "REASON_ANSWER_DECLINED",
    "REASON_UNGROUNDED_ANSWER",
    "RecognitionResult",
    "HeritageService",
    "build_service",
]

DEFAULT_TOP_K = 5

# Decision / rejection reasons.
REASON_LOW_SIMILARITY = "low_similarity"
REASON_NO_EVIDENCE = "no_evidence"
REASON_ANSWER_DECLINED = "answer_declined"
REASON_UNGROUNDED_ANSWER = "ungrounded_answer"


@dataclass
class RecognitionResult:
    """Structured result of one recognition + grounded-answer request."""

    site_id: str
    similarity: float
    confident: bool
    decision: str
    top_k: int
    matches: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    answer: Optional[str] = None
    citations: List[Dict[str, str]] = field(default_factory=list)
    reason: Optional[str] = None
    is_grounded: bool = False
    is_valid: bool = True
    confirmed: bool = False
    recognition_source: str = "local"
    global_identification: Optional[Dict[str, Any]] = None
    # Confidence reported by whichever model made the decision: the local CLIP
    # cosine for a local match, or the vision model's own confidence for an
    # Ollama fallback hit.  ``similarity`` is never repurposed to carry it --
    # that field always stays the local CLIP cosine so the two remain
    # distinguishable.  ``None`` when nothing was confirmed.
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site_id": self.site_id,
            "similarity": self.similarity,
            "confidence": self.confidence,
            "confident": self.confident,
            "confirmed": self.confirmed,
            "decision": self.decision,
            "recognition_source": self.recognition_source,
            "global_identification": dict(self.global_identification) if self.global_identification else None,
            "top_k": self.top_k,
            "matches": list(self.matches),
            "metadata": dict(self.metadata),
            "evidence": dict(self.evidence),
            "answer": self.answer,
            "citations": list(self.citations),
            "reason": self.reason,
            "is_grounded": self.is_grounded,
            "is_valid": self.is_valid,
        }


class HeritageService:
    """
    Clean internal interface over recognition + grounded RAG.

    Compose this once at startup and reuse it; the FAISS index, the evidence
    repository and the CLIP model are all expensive to build.
    """

    def __init__(
        self,
        confidence_layer: ConfidenceLayer,
        repository: EvidenceRepository,
        extractor: Optional[VisualEmbeddingExtractor] = None,
        provider: Optional[Provider] = None,
        top_k: int = DEFAULT_TOP_K,
        open_set: Optional[OpenSetRejection] = None,
        ollama_client: Optional[OllamaVisionClient] = None,
        gemini_client: Optional[GeminiVisionClient] = None,
    ) -> None:
        self.confidence_layer = confidence_layer
        self.repository = repository
        self.extractor = extractor
        self.provider = provider
        self.default_top_k = top_k
        self.pipeline = GroundedPipeline(repository, provider)
        # Open-set rejection uses its own calibrated threshold, NOT the
        # confidence layer's retrieval threshold.  The retrieval threshold
        # governs whether a top-1 FAISS hit is worth considering at all; the
        # open-set threshold governs whether the hit is trustworthy enough to
        # accept as a local match.  Using the retrieval threshold here let
        # cross-monument similarity (measured up to 0.84 on this index) pass
        # through as a confident local match.
        self.open_set = open_set or OpenSetRejection(top_k=top_k)
        self.ollama_client = ollama_client or OllamaVisionClient()
        if gemini_client is not None:
            self.gemini_client = gemini_client
        elif ollama_client is not None:
            # Caller explicitly injected an Ollama client (e.g., tests or rollback)
            self.gemini_client = None
        else:
            self.gemini_client = GeminiVisionClient()

    # ── inputs ───────────────────────────────────────────────────────────────

    def _embed(self, query: Union[str, Path, np.ndarray]) -> np.ndarray:
        """Turn the caller's query input into a CLIP embedding."""
        if isinstance(query, np.ndarray):
            return query.astype(np.float32).ravel()

        if not isinstance(query, (str, Path)):
            raise TypeError(
                f"query must be an image path or an embedding, got {type(query).__name__}"
            )

        if self.extractor is None:
            raise RuntimeError("no embedding extractor configured for image queries")

        return self.extractor.extract(query)

    # ── recognition ───────────────────────────────────────────────────────────

    def _ranked_matches(
        self,
        embedding: np.ndarray,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Return the top_k indexed matches with their score and site_id."""
        index = self.confidence_layer.index
        limit = max(1, min(top_k, index.ntotal))

        scores, indices = index.search(
            embedding.astype(np.float32).reshape(1, -1), limit
        )

        matches: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            matches.append(
                {
                    "image_id": self.confidence_layer.image_ids[idx],
                    "site_id": self.confidence_layer._site_ids[idx],
                    "similarity": round(float(score), 6),
                }
            )
        return matches

    # ── public API ────────────────────────────────────────────────────────────

    def recognize(
        self,
        query: Union[str, Path, np.ndarray],
        question: str = "",
        top_k: Optional[int] = None,
    ) -> RecognitionResult:
        """
        Recognize a heritage site and, when possible, answer a question about it.

        Parameters
        ----------
        query : str | Path | np.ndarray
            An image path, or a precomputed CLIP embedding.
        question : str
            Optional user question.  Empty means "identify only".
        top_k : int, optional
            Number of candidate matches to return.  Defaults to the
            configured value.

        Returns
        -------
        RecognitionResult
            Structured recognition, metadata, evidence, answer and citations,
            with a ``reason`` whenever the service declines to answer.
        """
        effective_k = int(top_k) if top_k else self.default_top_k
        effective_k = max(1, effective_k)

        embedding = self._embed(query)

        # 1. recognition + open-set decision
        matches = self._ranked_matches(embedding, effective_k)
        decision = self.open_set.decide(matches, effective_k)

        top_similarity = (
            round(decision.similarity, 6)
            if decision.similarity is not None
            else (round(matches[0]["similarity"], 6) if matches else 0.0)
        )

        result = RecognitionResult(
            site_id=decision.site_id if decision.confirmed else "unknown",
            similarity=top_similarity,
            confident=decision.confirmed,
            confirmed=decision.confirmed,
            decision="match" if decision.confirmed else "unknown",
            recognition_source="local" if decision.confirmed else "unknown",
            # For a local match the deciding model's confidence IS the CLIP
            # cosine; they are the same quantity, so it is mirrored here
            # rather than conflated with the Ollama fallback's confidence.
            confidence=top_similarity if decision.confirmed else None,
            global_identification=None,
            top_k=effective_k,
            matches=matches,
        )

        # 2. an unconfirmed match stops here: no evidence, no answer
        if not decision.confirmed:
            result.reason = REASON_LOW_SIMILARITY
            return result

        # 3. evidence context + grounded generation + validation
        site_id = decision.site_id
        pipeline_result: PipelineResult = self.pipeline.run(site_id, question)
        context = pipeline_result.context
        answer = pipeline_result.answer

        result.metadata = dict(context.metadata)
        result.evidence = {
            "claims": list(context.claims),
            "source_names": list(context.source_names),
            "source_urls": list(context.source_urls),
            "relevant_claims": list(context.relevant_claims),
        }
        result.is_valid = pipeline_result.validation.is_valid
        result.is_grounded = answer.is_grounded

        if not context.is_known or not context.claims:
            # Either the site is unknown, or it is known but carries no
            # evidence records - in both cases there is nothing to answer from.
            result.reason = REASON_NO_EVIDENCE
            return result

        if not context.is_known or not context.claims:
            # Either the site is unknown, or it is known but carries no
            # evidence records - in both cases there is nothing to answer from.
            result.reason = REASON_NO_EVIDENCE
            return result

        result.citations = [
            {"source_name": name, "source_url": url}
            for name, url in zip(context.source_names, context.source_urls)
        ]

        # No question means identification only: report what was matched and
        # the evidence behind it, but do not volunteer an answer.
        if not question.strip():
            result.is_grounded = False
            return result

        if answer.is_grounded:
            result.answer = answer.answer
            result.citations = [
                {"source_name": name, "source_url": url}
                for name, url in zip(answer.source_names, answer.source_urls)
            ]
        else:
            # Never surface an ungrounded provider response as the answer.
            result.reason = (
                REASON_UNGROUNDED_ANSWER
                if answer.reason == "ungrounded_answer"
                else REASON_ANSWER_DECLINED
            )

        return result

    # ── public async API (Gemini fallback) ───────────────────────────────────

    async def recognize_async(
        self,
        query: Union[str, Path, np.ndarray],
        question: str = "",
        top_k: Optional[int] = None,
    ) -> RecognitionResult:
        """
        Async wrapper around :meth:`recognize` that falls back to Google Gemini
        vision when open-set recognition rejects the local match.
        """
        result = self.recognize(query, question=question, top_k=top_k)

        # 1. Local match accepted: return the local result directly
        if result.confident and result.confirmed:
            return result

        # 2. Local match rejected: call Gemini vision fallback if image is available
        if isinstance(query, (str, Path, bytes)) and self.gemini_client is not None:
            try:
                gemini_res = await self.gemini_client.identify_monument(query)
                # Only accept the global identification when Gemini reports a
                # GENUINE heritage monument and not unknown.
                if not gemini_res.unknown and gemini_res.identified and gemini_res.is_heritage:
                    # Model found a plausible identification:
                    # Mark source as "gemini", keep separate from local FAISS matches,
                    # and do NOT mark as independently confirmed.
                    result.confident = True
                    result.confirmed = False  # Model proposal: not independently verified against local catalogue
                    result.decision = "match"
                    result.recognition_source = "gemini"
                    result.site_id = "unknown"  # NEVER turn external response into local site_id
                    result.confidence = gemini_res.confidence  # Model-estimated confidence
                    # result.similarity remains the local CLIP cosine score!
                    result.global_identification = gemini_res.to_dict()
                    result.reason = gemini_res.visual_evidence or gemini_res.reason

                    result.citations = []
                    result.is_grounded = False
                    result.metadata = {}
                    result.evidence = {
                        "claims": [],
                        "source_names": [],
                        "source_urls": [],
                        "relevant_claims": [],
                    }
                    result.answer = None
                else:
                    # If Gemini cannot identify the image, or
                    # identified place is non-heritage, return safe unknown result.
                    result.confirmed = False
                    result.confident = False
                    result.site_id = "unknown"
                    result.decision = "unknown"
                    result.recognition_source = "unknown"
                    result.global_identification = None
                    result.confidence = None
                    result.citations = []
                    result.answer = None
                    result.is_grounded = False
                    result.reason = (
                        REASON_NON_HERITAGE
                        if gemini_res.explicit_non_heritage
                        else REASON_LOW_SIMILARITY
                    )
            except Exception as exc:
                # Failure, timeout, malformed data, or missing credentials
                logger.warning("Gemini vision fallback failed: %s", type(exc).__name__)
                result.confirmed = False
                result.confident = False
                result.site_id = "unknown"
                result.decision = "unknown"
                result.recognition_source = "unknown"
                result.global_identification = None
                result.confidence = None
                result.citations = []
                result.answer = None
                result.is_grounded = False
                result.reason = REASON_LOW_SIMILARITY

        elif isinstance(query, (str, Path, bytes)) and self.ollama_client is not None:
            # Rollback fallback path when Gemini client is disabled or omitted
            try:
                ollama_res = await self.ollama_client.identify_monument(query, question=question)
                if not ollama_res.unknown and ollama_res.identified and ollama_res.is_heritage:
                    result.confident = True
                    result.confirmed = False
                    result.decision = "match"
                    result.recognition_source = "ollama"
                    result.site_id = "unknown"
                    result.confidence = ollama_res.confidence
                    result.global_identification = ollama_res.to_dict()
                    result.reason = ollama_res.visual_evidence or ollama_res.reason
                    result.citations = []
                    result.is_grounded = False
                    result.metadata = {}
                    result.evidence = {
                        "claims": [],
                        "source_names": [],
                        "source_urls": [],
                        "relevant_claims": [],
                    }
                    if question and question.strip():
                        if ollama_res.answer and ollama_res.answer.strip():
                            result.answer = ollama_res.answer.strip()
                        else:
                            result.answer = (
                                "This question could not be answered from the visual information "
                                "available for this monument."
                            )
                    else:
                        result.answer = None
                else:
                    result.confirmed = False
                    result.confident = False
                    result.site_id = "unknown"
                    result.decision = "unknown"
                    result.recognition_source = "unknown"
                    result.global_identification = None
                    result.confidence = None
                    result.citations = []
                    result.answer = None
                    result.is_grounded = False
                    result.reason = (
                        REASON_NON_HERITAGE
                        if ollama_res.explicit_non_heritage
                        else REASON_LOW_SIMILARITY
                    )
            except Exception as exc:
                logger.warning("Ollama vision fallback failed: %s", type(exc).__name__)
                result.confirmed = False
                result.confident = False
                result.site_id = "unknown"
                result.decision = "unknown"
                result.recognition_source = "unknown"
                result.global_identification = None
                result.confidence = None
                result.citations = []
                result.answer = None
                result.is_grounded = False
                result.reason = REASON_LOW_SIMILARITY

        return result


def build_service(
    index_path: Union[str, Path] = "data/processed/index/clip_index.faiss",
    mapping_path: Union[str, Path] = "data/processed/index/mapping.json",
    metadata_path: Union[str, Path] = "data/evidence/heritage_metadata.json",
    evidence_path: Union[str, Path] = "data/evidence/heritage_evidence.json",
    threshold: float = 0.85,
    top_k: int = DEFAULT_TOP_K,
    provider: Optional[Provider] = None,
    extractor: Optional[VisualEmbeddingExtractor] = None,
    open_set: Optional[OpenSetRejection] = None,
    ollama_client: Optional[OllamaVisionClient] = None,
    gemini_client: Optional[GeminiVisionClient] = None,
) -> HeritageService:
    """Build a ready-to-use service from the project's persisted artefacts."""
    layer = build_confidence_layer(
        str(index_path), str(mapping_path), threshold=threshold
    )
    repository = load_repository(str(metadata_path), str(evidence_path))
    return HeritageService(
        confidence_layer=layer,
        repository=repository,
        extractor=extractor if extractor is not None else VisualEmbeddingExtractor(),
        provider=provider,
        top_k=top_k,
        open_set=open_set,
        ollama_client=ollama_client,
        gemini_client=gemini_client,
    )
