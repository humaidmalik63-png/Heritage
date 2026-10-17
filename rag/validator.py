"""
Grounding and citation validation.

Checks that a generated answer is fully supported by the retrieved context:
every factual sentence must be traceable to a supplied evidence claim or
site metadata field, and its citations must match the sources backing that
claim.

The validator never treats the answer itself as evidence — only the supplied
:class:`~rag.retriever.GroundedContext` is trusted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rag.retriever import GroundedContext, _tokenize, _STOPWORDS

__all__ = [
    "ValidationIssue",
    "ValidationReport",
    "validate_answer",
    "INSUFFICIENT_MARKERS",
]

# Phrases that legitimately decline to answer.
INSUFFICIENT_MARKERS = (
    "does not contain",
    "not contain enough information",
    "insufficient",
    "no information",
    "cannot be answered",
    "unable to answer",
    "not available in the context",
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Metadata fields that are legitimate factual evidence on their own.
_METADATA_FIELDS = (
    "name",
    "alternate_name",
    "location",
    "state",
    "country",
    "category",
    "preservation_context",
    "description",
    "historical_period",
)


@dataclass
class ValidationIssue:
    """A single validation problem."""

    kind: str
    detail: str
    sentence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "detail": self.detail, "sentence": self.sentence}


@dataclass
class ValidationReport:
    """Outcome of validating one answer against its context."""

    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    checked_sentences: int = 0
    is_abstained: bool = False

    @property
    def unsupported(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.kind == "unsupported_claim"]

    @property
    def missing_citations(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.kind == "missing_citation"]

    @property
    def invalid_citations(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.kind == "invalid_citation"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "is_abstained": self.is_abstained,
            "checked_sentences": self.checked_sentences,
            "issues": [i.to_dict() for i in self.issues],
        }


def _split_sentences(text: str) -> List[str]:
    """Split an answer into non-empty sentences."""
    return [s.strip() for s in _SENTENCE_SPLIT.split(text or "") if s and s.strip()]


def _is_abstention(answer_text: str) -> bool:
    """True when the answer declines rather than asserting a fact."""
    lowered = (answer_text or "").lower()
    return any(marker in lowered for marker in INSUFFICIENT_MARKERS)


def _evidence_texts(context: GroundedContext) -> List[str]:
    """All text that legitimately counts as evidence for this site."""
    texts: List[str] = list(context.claims)
    for field_name in _METADATA_FIELDS:
        value = context.metadata.get(field_name)
        if isinstance(value, str) and value.strip():
            texts.append(value)
    return texts


def _content_tokens(text: str) -> set[str]:
    return _tokenize(text) - _STOPWORDS


def _is_supported(sentence: str, evidence_texts: List[str]) -> Optional[str]:
    """Return the evidence text supporting ``sentence``, else None."""
    sentence_tokens = _content_tokens(sentence)
    if not sentence_tokens:
        return None

    best: Optional[str] = None
    best_overlap = 0
    for text in evidence_texts:
        overlap = len(sentence_tokens & _content_tokens(text))
        if overlap > best_overlap:
            best_overlap = overlap
            best = text

    # Require most of the sentence's content words to appear in one
    # single piece of evidence, so a patchwork of unrelated facts fails.
    if best is not None and best_overlap >= max(1, int(0.6 * len(sentence_tokens))):
        return best
    return None


def _sources_for_text(context: GroundedContext, text: str) -> List[str]:
    """All source URLs attached to ``text`` within the context."""
    urls: List[str] = []
    for claim, url in zip(context.claims, context.source_urls):
        if claim == text:
            urls.append(url)
    for claim, url in zip(context.relevant_claims, context.relevant_source_urls):
        if claim == text and url not in urls:
            urls.append(url)
    return urls


def _valid_urls(context: GroundedContext) -> set[str]:
    return set(context.source_urls) | set(context.relevant_source_urls)


def validate_answer(
    answer: Any,
    context: GroundedContext,
) -> ValidationReport:
    """
    Validate that ``answer`` is grounded in ``context``.

    Parameters
    ----------
    answer : GroundedAnswer | str
        The generated answer to check.
    context : GroundedContext
        The retrieved evidence.  This is the *only* trusted source of facts.

    Returns
    -------
    ValidationReport
        ``is_valid`` is True only when no issue was found.
    """
    if answer is None:
        return ValidationReport(
            is_valid=False,
            issues=[ValidationIssue("missing_citation", "no answer produced")],
        )

    if isinstance(answer, str):
        answer_text = answer
        cited_urls: List[str] = []
        is_grounded_flag: Optional[bool] = None
        decline_reason = ""
    else:
        answer_text = getattr(answer, "answer", "") or ""
        cited = getattr(answer, "source_urls", []) or []
        cited_urls = list(cited)
        is_grounded_flag = getattr(answer, "is_grounded", None)
        decline_reason = getattr(answer, "reason", "") or ""

    # ``is_grounded=False`` is not by itself a licence to abstain: the
    # generator also sets it when it *rejects* a provider response as
    # fabricated.  A genuine abstention must carry a reason recorded by the
    # generator, so an ungrounded answer is only accepted when it is worded
    # as a decline *and* the generator did not flag it as ungrounded.
    if is_grounded_flag is False or _is_abstention(answer_text):
        declines = _is_abstention(answer_text) and decline_reason != "ungrounded_answer"

        if not isinstance(context, GroundedContext) or not context.is_known:
            if declines:
                return ValidationReport(is_valid=True, is_abstained=True)
            return ValidationReport(
                is_valid=False,
                issues=[
                    ValidationIssue(
                        "ungrounded_answer",
                        "answer asserts facts for a site with no retrieved context",
                        answer_text,
                    )
                ],
            )

        if not declines:
            # The generator rejected this text as ungrounded.  Fall back to
            # per-sentence analysis so the offending sentence is pinpointed
            # rather than reporting one opaque issue for the whole answer.
            if not isinstance(context, GroundedContext) or not context.is_known:
                return ValidationReport(
                    is_valid=False,
                    issues=[
                        ValidationIssue(
                            "ungrounded_answer",
                            "answer asserts facts for a site with no retrieved context",
                            answer_text,
                        )
                    ],
                )
            sentences = _split_sentences(answer_text)
            found = [
                ValidationIssue(
                    "unsupported_claim",
                    "sentence is not supported by the retrieved evidence",
                    sentence,
                )
                for sentence in sentences
                if _is_supported(sentence, _evidence_texts(context)) is None
            ]
            if not found:
                found = [
                    ValidationIssue(
                        "ungrounded_answer",
                        "answer is not supported by the retrieved evidence",
                        answer_text,
                    )
                ]
            return ValidationReport(
                is_valid=False,
                issues=found,
                checked_sentences=len(sentences),
            )

        # Declining is only valid when no claim supports the question; the
        # caller signals that by supplying no relevant claims.
        if not context.relevant_claims:
            return ValidationReport(is_valid=True, is_abstained=True)
        return ValidationReport(
            is_valid=False,
            is_abstained=True,
            issues=[
                ValidationIssue(
                    "insufficient_evidence",
                    "answer declines but relevant evidence exists",
                    answer_text,
                )
            ],
        )

    if not isinstance(context, GroundedContext) or not context.is_known:
        return ValidationReport(
            is_valid=False,
            issues=[
                ValidationIssue("unknown_site", "no retrieved context for the site")
            ],
        )

    evidence_texts = _evidence_texts(context)
    if not evidence_texts:
        return ValidationReport(
            is_valid=False,
            issues=[
                ValidationIssue(
                    "insufficient_evidence",
                    "retrieved context contains no evidence",
                    answer_text,
                )
            ],
        )

    valid_urls = _valid_urls(context)
    invalid_urls = [u for u in cited_urls if u not in valid_urls]

    sentences = _split_sentences(answer_text)
    issues: List[ValidationIssue] = []
    supporting_urls: List[str] = []

    for url in invalid_urls:
        issues.append(
            ValidationIssue("invalid_citation", f"citation not in context: {url}")
        )

    for sentence in sentences:
        matched = _is_supported(sentence, evidence_texts)
        if matched is None:
            issues.append(
                ValidationIssue(
                    "unsupported_claim",
                    "sentence is not supported by the retrieved evidence",
                    sentence,
                )
            )
            continue

        expected_urls = _sources_for_text(context, matched)
        if not expected_urls:
            continue

        for url in expected_urls:
            if url not in cited_urls:
                issues.append(
                    ValidationIssue(
                        "missing_citation",
                        f"claim requires a citation but {url} was not cited",
                        sentence,
                    )
                )
            else:
                supporting_urls.append(url)

    report = ValidationReport(
        is_valid=not issues,
        issues=issues,
        checked_sentences=len(sentences),
    )
    return report
