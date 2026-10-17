"""
Grounded context retrieval.

Builds a grounded answer context for a heritage site by combining the site
metadata with only the evidence entries relevant to the (optional) user
question.  No LLM is involved: this module selects and returns source
material only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data.evidence.context import SiteContext, build_site_context
from data.evidence.loader import EvidenceRepository

__all__ = ["GroundedContext", "retrieve_context", "DEFAULT_QUESTION"]

DEFAULT_QUESTION = ""

_WORD_RE = re.compile(r"[a-z0-9]+")

# Terms too generic to discriminate between evidence claims.
_STOPWORDS = frozenset(
    """
    a an the of in on at to for from by with and or is are was were be been
    being this that these those it its as about into over under what which who
    when where why how do does did can could should would will shall may might
    must tell me please give show find info information about
    """.split()
)


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _score_claim(question_tokens: set[str], claim: str, source_name: str) -> int:
    """Count how many query tokens appear in a claim or its source name."""
    if not question_tokens:
        return 0
    haystack = _tokenize(claim) | _tokenize(source_name)
    return len(question_tokens & haystack)


@dataclass
class GroundedContext:
    """Grounded context for one site, restricted to relevant evidence."""

    site_id: str
    is_known: bool
    question: str = DEFAULT_QUESTION
    metadata: Dict[str, Any] = field(default_factory=dict)
    claims: List[str] = field(default_factory=list)
    source_names: List[str] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)
    relevant_claims: List[str] = field(default_factory=list)
    relevant_source_names: List[str] = field(default_factory=list)
    relevant_source_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site_id": self.site_id,
            "is_known": self.is_known,
            "question": self.question,
            "metadata": dict(self.metadata),
            "claims": list(self.claims),
            "source_names": list(self.source_names),
            "source_urls": list(self.source_urls),
            "relevant_claims": list(self.relevant_claims),
            "relevant_source_names": list(self.relevant_source_names),
            "relevant_source_urls": list(self.relevant_source_urls),
        }


def _empty(site_id: str, question: str) -> GroundedContext:
    """Safe empty result for an unknown site or a known site with no evidence."""
    return GroundedContext(site_id=site_id, is_known=False, question=question)


def _context_from_site(site: SiteContext, question: str) -> GroundedContext:
    metadata = {
        "name": site.name,
        "alternate_name": site.alternate_name,
        "location": site.location,
        "state": site.state,
        "country": site.country,
        "category": site.category,
        "preservation_context": site.preservation_context,
        "description": site.description,
        "historical_period": site.historical_period,
    }

    result = GroundedContext(
        site_id=site.site_id,
        is_known=True,
        question=question,
        metadata=metadata,
        claims=list(site.claims),
        source_names=list(site.source_names),
        source_urls=list(site.source_urls),
    )

    question_tokens = _tokenize(question) - _STOPWORDS
    if not question_tokens:
        # No discriminating question: the whole evidence set is relevant.
        result.relevant_claims = list(site.claims)
        result.relevant_source_names = list(site.source_names)
        result.relevant_source_urls = list(site.source_urls)
        return result

    for claim, source_name, source_url in zip(
        site.claims, site.source_names, site.source_urls
    ):
        if _score_claim(question_tokens, claim, source_name) > 0:
            result.relevant_claims.append(claim)
            result.relevant_source_names.append(source_name)
            result.relevant_source_urls.append(source_url)

    return result


def retrieve_context(
    site_id: str,
    question: str = DEFAULT_QUESTION,
    repository: Optional[EvidenceRepository] = None,
) -> GroundedContext:
    """
    Retrieve the grounded evidence context for ``site_id``.

    Parameters
    ----------
    site_id : str
        Site identifier to retrieve context for.
    question : str, optional
        Optional user question.  When provided, only evidence entries that
        share at least one non-stopword term with it are marked relevant.
    repository : EvidenceRepository, optional
        Pre-loaded repository; the project defaults are used when omitted.

    Returns
    -------
    GroundedContext
        Site metadata plus the site's evidence claims, source names and
        source URLs.  For an unknown ``site_id`` an empty, ``is_known=False``
        result is returned.
    """
    if not isinstance(site_id, str) or not site_id.strip():
        return _empty("", question if isinstance(question, str) else "")

    site = build_site_context(site_id, repository)
    if not site.is_known:
        return _empty("unknown", question if isinstance(question, str) else "")

    return _context_from_site(site, question if isinstance(question, str) else "")
