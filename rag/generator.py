"""
Grounded answer generation.

Produces an answer strictly from a :class:`~rag.retriever.GroundedContext`
object.  Any language-model call sits behind :class:`Provider`; without a
configured provider the module falls back to deterministic extractive
grounding so no external API is ever required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from rag.retriever import GroundedContext, _tokenize, _STOPWORDS

__all__ = [
    "Provider",
    "EchoProvider",
    "GroundedAnswer",
    "generate_answer",
    "INSUFFICIENT_CONTEXT",
]

INSUFFICIENT_CONTEXT = "insufficient_context"


@runtime_checkable
class Provider(Protocol):
    """Small interface any language-model backend must satisfy."""

    def generate(
        self,
        question: str,
        context: GroundedContext,
    ) -> Optional[str]:
        """Return an answer grounded in ``context``, or None to abstain."""
        ...


class EchoProvider:
    """Deterministic provider that echoes the most relevant claim.

    Useful as a default and for tests; performs no network access.
    """

    def generate(
        self,
        question: str,
        context: GroundedContext,
    ) -> Optional[str]:
        if not context.is_known:
            return None
        if context.relevant_claims:
            return context.relevant_claims[0]
        if context.claims:
            return context.claims[0]
        return None


@dataclass
class GroundedAnswer:
    """A grounded answer plus the sources it was derived from."""

    question: str
    site_id: str
    answer: str
    is_grounded: bool
    reason: str = ""
    source_names: List[str] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "site_id": self.site_id,
            "answer": self.answer,
            "is_grounded": self.is_grounded,
            "reason": self.reason,
            "source_names": list(self.source_names),
            "source_urls": list(self.source_urls),
        }


def _insufficient(
    question: str,
    context: GroundedContext,
    reason: str,
) -> GroundedAnswer:
    """Build a safe 'not answerable from the context' result."""
    return GroundedAnswer(
        question=question,
        site_id=context.site_id,
        answer=(
            "The supplied context does not contain enough information "
            "to answer this question."
        ),
        is_grounded=False,
        reason=reason,
        source_names=[],
        source_urls=[],
    )


def _sources_for_claims(context: GroundedContext, answer: str) -> tuple[List[str], List[str]]:
    """Return the source names/URLs backing ``answer``."""
    names: List[str] = []
    urls: List[str] = []

    if answer in context.relevant_claims and context.relevant_source_names:
        names = list(context.relevant_source_names)
        urls = list(context.relevant_source_urls)
        return names, urls

    if answer in context.claims and context.source_names:
        names = list(context.source_names)
        urls = list(context.source_urls)

    return names, urls


def generate_answer(
    question: str,
    context: GroundedContext,
    provider: Optional[Provider] = None,
) -> GroundedAnswer:
    """
    Generate a grounded answer from ``context``.

    Parameters
    ----------
    question : str
        The user question.
    context : GroundedContext
        Retrieved evidence context.  The answer is drawn only from it.
    provider : Provider, optional
        Language-model backend.  Defaults to :class:`EchoProvider`, which
        performs no network access.

    Returns
    -------
    GroundedAnswer
        Answer text with the source names and URLs it came from.  When the
        context does not support an answer, ``is_grounded`` is False and the
        answer states that the information is unavailable.
    """
    question_text = question if isinstance(question, str) else ""

    if not isinstance(context, GroundedContext):
        return GroundedAnswer(
            question=question_text,
            site_id="unknown",
            answer=(
                "The supplied context does not contain enough information "
                "to answer this question."
            ),
            is_grounded=False,
            reason="no_context",
        )

    if not context.is_known:
        return _insufficient(question_text, context, "unknown_site")

    if not context.claims:
        return _insufficient(question_text, context, "no_evidence")

    active_provider = provider if provider is not None else EchoProvider()

    try:
        answer = active_provider.generate(question_text, context)
    except Exception:
        # A provider failure must never produce an ungrounded answer.
        return _insufficient(question_text, context, "provider_error")

    if not answer or not isinstance(answer, str) or not answer.strip():
        return _insufficient(question_text, context, "no_supporting_claim")

    # Guard: an answer must be traceable to the supplied context.  The
    # rejected text is preserved so the validator can still inspect it and
    # report the unsupported claim rather than losing it silently.
    if answer not in context.claims and answer not in context.relevant_claims:
        return GroundedAnswer(
            question=question_text,
            site_id=context.site_id,
            answer=answer,
            is_grounded=False,
            reason="ungrounded_answer",
            source_names=[],
            source_urls=[],
        )

    names, urls = _sources_for_claims(context, answer)

    return GroundedAnswer(
        question=question_text,
        site_id=context.site_id,
        answer=answer,
        is_grounded=True,
        source_names=names,
        source_urls=urls,
    )
