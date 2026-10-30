"""
Evidence repository loader for heritage site metadata and evidence.

Loads and provides access to structured heritage site data and supporting evidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__all__ = [
    "SiteMetadata",
    "SiteEvidence",
    "EvidenceRepository",
    "load_repository",
    "_normalize_site_id",
]


@dataclass
class SiteMetadata:
    """Structured heritage site metadata."""
    site_id: str
    name: str
    alternate_name: str
    location: str
    state: str
    country: str
    description: str
    historical_period: str
    category: str
    preservation_context: str


@dataclass
class SiteEvidence:
    """Evidence supporting a heritage site claim."""
    site_id: str
    claim: str
    source_name: str
    source_url: str


# Canonical site ID aliases: shortened/alternative IDs → canonical IDs.
# Derived from ``data/raw/`` directory names vs. ``global_monument_catalogue.json``
# canonical entries. Each mapping is unambiguous: a single shortened ID maps
# to exactly one canonical ID.
SITE_ID_ALIASES: dict[str, str] = {
    "red_fort": "red_fort_delhi",
    "jama_masjid": "jama_masjid_delhi",
}


def _normalize_site_id(site_id: str, aliases: dict[str, str] = SITE_ID_ALIASES) -> str:
    """
    Normalize a site ID to its canonical form.

    Shortened/alternative IDs (e.g. ``red_fort``, ``jama_masjid``) are
    mapped to their canonical forms (e.g. ``red_fort_delhi``,
    ``jama_masjid_delhi``) derived from the ``global_monument_catalogue.json``
    catalogue. Canonical IDs pass through unchanged. Unknown IDs are
    returned as-is.

    This enables lookups by either the shortened ID used in the FAISS
    mapping or the canonical ID used in the catalogue and evidence files,
    without silently resolving ambiguous IDs.
    """
    normalized = aliases.get(site_id)
    if normalized is not None:
        return normalized
    return site_id


@dataclass
class EvidenceRepository:
    metadata_path: Path
    evidence_path: Path

    _metadata: dict[str, SiteMetadata] = None
    _evidence: dict[str, list[SiteEvidence]] = None

    def __post_init__(self) -> None:
        if self._metadata is None:
            self._load()

    def _normalize_site_id(self, site_id: str) -> str:
        return _normalize_site_id(site_id)

    def _load(self) -> None:
        """Load metadata and evidence from JSON files."""
        # Load metadata - primary source
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            raw_metadata = json.load(f)

        self._metadata = {}
        for item in raw_metadata:
            # heritage_metadata.json uses "id" as the site identifier key
            payload = dict(item)
            if "id" in payload and "site_id" not in payload:
                payload["site_id"] = payload.pop("id")
            meta = SiteMetadata(**payload)
            # Normalize the stored site_id to canonical form
            meta.site_id = self._normalize_site_id(meta.site_id)
            self._metadata[meta.site_id] = meta

        # Try to load legacy metadata for backwards compatibility
        legacy_path = Path(self.metadata_path).parent.parent / "metadata" / "heritage_metadata.json"
        if legacy_path.exists() and legacy_path != self.metadata_path:
            with open(legacy_path, "r", encoding="utf-8") as f:
                legacy_metadata = json.load(f)
            for item in legacy_metadata:
                sid = item.get("id") or item.get("site_id")
                if sid and sid not in self._metadata:
                    payload = dict(item)
                    if "id" in payload and "site_id" not in payload:
                        payload["site_id"] = payload.pop("id")
                    meta = SiteMetadata(**payload)
                    meta.site_id = self._normalize_site_id(meta.site_id)
                    self._metadata[meta.site_id] = meta

        # Load evidence
        with open(self.evidence_path, "r", encoding="utf-8") as f:
            raw_evidence = json.load(f)

        self._evidence = {}
        for item in raw_evidence:
            ev = SiteEvidence(**item)
            # Normalize the evidence site_id to canonical form
            ev.site_id = self._normalize_site_id(ev.site_id)
            if ev.site_id not in self._evidence:
                self._evidence[ev.site_id] = []
            self._evidence[ev.site_id].append(ev)

    def get_metadata(self, site_id: str) -> Optional[SiteMetadata]:
        """Get metadata for a site by ID. Returns None if not found."""
        return self._metadata.get(self._normalize_site_id(site_id))

    def get_evidence(self, site_id: str) -> list[SiteEvidence]:
        """Get all evidence entries for a site. Returns empty list if not found."""
        return self._evidence.get(self._normalize_site_id(site_id), [])

    def has_site(self, site_id: str) -> bool:
        """Check if a site exists in the repository."""
        return site_id in self._metadata

    def list_sites(self) -> list[str]:
        """Return list of all known site IDs."""
        return list(self._metadata.keys())

    def get_full_record(self, site_id: str) -> Optional[dict]:
        """
        Get combined metadata and evidence for a site.

        Returns None if site not found.
        """
        meta = self.get_metadata(site_id)
        if meta is None:
            return None

        evidence = self.get_evidence(site_id)
        return {
            "metadata": meta,
            "evidence": evidence,
        }


def load_repository(
    metadata_path: str | Path = "data/metadata/heritage_metadata.json",
    evidence_path: str | Path = "data/evidence/heritage_evidence.json",
) -> EvidenceRepository:
    """
    Factory function to create and load an EvidenceRepository.

    Args:
        metadata_path: Path to heritage_metadata.json
        evidence_path: Path to heritage_evidence.json

    Returns:
        Loaded EvidenceRepository instance
    """
    return EvidenceRepository(
        metadata_path=Path(metadata_path),
        evidence_path=Path(evidence_path),
    )