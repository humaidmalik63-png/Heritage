"""
Context builder for heritage sites.

Assembles a single structured context record for a site from the evidence
repository: metadata, historical information, evidence claims and sources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data.evidence.loader import EvidenceRepository, load_repository

__all__ = ["SiteContext", "build_site_context", "UNKNOWN_SITE_ID"]

UNKNOWN_SITE_ID = "unknown"


@dataclass
class SiteContext:
    """
    Structured context for a single heritage site.

    ``is_known`` is False when the requested site_id was not found; in that
    case ``site_id`` becomes ``"unknown"`` and every list is empty.
    """

    site_id: str
    is_known: bool
    name: str = ""
    alternate_name: str = ""
    location: str = ""
    state: str = ""
    country: str = ""
    category: str = ""
    preservation_context: str = ""
    description: str = ""
    historical_period: str = ""
    claims: List[str] = field(default_factory=list)
    source_names: List[str] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return the context as a plain dictionary."""
        return {
            "site_id": self.site_id,
            "is_known": self.is_known,
            "name": self.name,
            "alternate_name": self.alternate_name,
            "location": self.location,
            "state": self.state,
            "country": self.country,
            "category": self.category,
            "preservation_context": self.preservation_context,
            "description": self.description,
            "historical_period": self.historical_period,
            "claims": list(self.claims),
            "source_names": list(self.source_names),
            "source_urls": list(self.source_urls),
        }


def build_site_context(
    site_id: str,
    repository: Optional[EvidenceRepository] = None,
) -> SiteContext:
    """
    Build the structured context for ``site_id``.

    Parameters
    ----------
    site_id : str
        The site identifier to look up.
    repository : EvidenceRepository, optional
        Pre-loaded repository.  When omitted the default project data files
        are loaded.

    Returns
    -------
    SiteContext
        Full context for a known site, or an ``is_known=False`` context for an
        unknown site.
    """
    repo = repository if repository is not None else load_repository()

    meta = repo.get_metadata(site_id)
    if meta is None:
        return SiteContext(site_id=UNKNOWN_SITE_ID, is_known=False)

    evidence = repo.get_evidence(site_id)

    return SiteContext(
        site_id=meta.site_id,
        is_known=True,
        name=meta.name,
        alternate_name=meta.alternate_name,
        location=meta.location,
        state=meta.state,
        country=meta.country,
        category=meta.category,
        preservation_context=meta.preservation_context,
        description=meta.description,
        historical_period=meta.historical_period,
        claims=[ev.claim for ev in evidence],
        source_names=[ev.source_name for ev in evidence],
        source_urls=[ev.source_url for ev in evidence],
    )