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


@dataclass
class EvidenceRepository:
    """
    Repository providing access to heritage site metadata and evidence.

    Loads data from JSON files and provides lookup by site_id.
    """
    metadata_path: Path
    evidence_path: Path

    _metadata: dict[str, SiteMetadata] = None
    _evidence: dict[str, list[SiteEvidence]] = None

    def __post_init__(self):
        if self._metadata is None:
            self._load()

    def _load(self) -> None:
        """Load metadata and evidence from JSON files."""
        # Load metadata
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            raw_metadata = json.load(f)

        self._metadata = {}
        for item in raw_metadata:
            # heritage_metadata.json uses "id" as the site identifier key
            payload = dict(item)
            if "id" in payload and "site_id" not in payload:
                payload["site_id"] = payload.pop("id")
            meta = SiteMetadata(**payload)
            self._metadata[meta.site_id] = meta

        # Load evidence
        with open(self.evidence_path, "r", encoding="utf-8") as f:
            raw_evidence = json.load(f)

        self._evidence = {}
        for item in raw_evidence:
            ev = SiteEvidence(**item)
            if ev.site_id not in self._evidence:
                self._evidence[ev.site_id] = []
            self._evidence[ev.site_id].append(ev)

    def get_metadata(self, site_id: str) -> Optional[SiteMetadata]:
        """Get metadata for a site by ID. Returns None if not found."""
        return self._metadata.get(site_id)

    def get_evidence(self, site_id: str) -> list[SiteEvidence]:
        """Get all evidence entries for a site. Returns empty list if not found."""
        return self._evidence.get(site_id, [])

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