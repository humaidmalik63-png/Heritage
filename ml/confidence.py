"""
Confidence decision layer for image retrieval.

Provides a simple threshold-based decision mechanism that classifies
retrieval results as either a confident match or 'unknown'.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import numpy as np
import faiss

# image ids are "<site_id>_<NN>", where the site_id itself may contain
# underscores (e.g. "taj_mahal_01" -> "taj_mahal")
_IMAGE_INDEX_SUFFIX = re.compile(r"_\d+$")


def parse_site_id(image_id: str) -> str:
    """Return the site_id of an image id by stripping a trailing _<number>."""
    return _IMAGE_INDEX_SUFFIX.sub("", image_id)


@dataclass
class RetrievalConfig:
    """Configuration for retrieval confidence decisions."""
    similarity_threshold: float = 0.65
    top_k: int = 5


@dataclass
class RetrievalResult:
    """Result of a retrieval query with confidence decision."""
    site_id: str
    image_id: str
    similarity: float
    confident: bool
    is_unknown: bool


class ConfidenceLayer:
    """
    Confidence decision layer on top of FAISS retrieval.

    Uses a configurable similarity threshold to decide whether
    the top-1 result is a confident match or should be classified as 'unknown'.
    """

    def __init__(
        self,
        index: faiss.Index,
        image_ids: list[str],
        paths: list[str],
        config: Optional[RetrievalConfig] = None,
        site_ids: Optional[list[str]] = None,
    ):
        self.index = index
        self.image_ids = image_ids
        self.paths = paths
        self.config = config or RetrievalConfig()

        # Prefer an explicit manifest site_id mapping; otherwise derive the
        # site_id from the image id by stripping the trailing _<number>.
        if site_ids is not None:
            self._site_ids = list(site_ids)
        else:
            self._site_ids = [parse_site_id(img_id) for img_id in image_ids]

    def query(self, query_embedding: np.ndarray) -> RetrievalResult:
        """
        Query the index and return a confidence decision.

        Args:
            query_embedding: Query vector of shape (dim,) or (1, dim)

        Returns:
            RetrievalResult with site_id, similarity, and confidence flag.
        """
        # Ensure 2D shape
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Search index
        distances, indices = self.index.search(query_embedding.astype(np.float32), self.config.top_k)

        top_idx = indices[0][0]
        top_similarity = float(distances[0][0])
        top_site_id = self._site_ids[top_idx]
        top_image_id = self.image_ids[top_idx]

        confident = top_similarity >= self.config.similarity_threshold
        is_unknown = not confident

        return RetrievalResult(
            site_id=top_site_id if confident else "unknown",
            image_id=top_image_id,
            similarity=top_similarity,
            confident=confident,
            is_unknown=is_unknown,
        )

    def set_threshold(self, threshold: float) -> None:
        """Update the similarity threshold."""
        self.config.similarity_threshold = threshold


# Canonical site ID aliases: shortened/alternative IDs → canonical IDs.
# Must match the aliases in data/evidence/loader.py to ensure consistent
# site_id normalization across the pipeline.
SITE_ID_ALIASES: dict[str, str] = {
    "red_fort": "red_fort_delhi",
    "jama_masjid": "jama_masjid_delhi",
}


def _normalize_site_ids(site_ids: list[str], aliases: dict[str, str] = SITE_ID_ALIASES) -> list[str]:
    """Normalize a list of site_ids to canonical form using aliases."""
    return [aliases.get(sid, sid) for sid in site_ids]


def build_confidence_layer(
    index_path: str,
    mapping_path: str,
    threshold: float = 0.85,
    top_k: int = 5,
) -> ConfidenceLayer:
    """
    Factory to build a ConfidenceLayer from persisted index and mapping.

    Args:
        index_path: Path to FAISS index file
        mapping_path: Path to mapping.json with image_ids and paths
        threshold: Similarity threshold for confident match
        top_k: Number of results to retrieve

    Returns:
        Configured ConfidenceLayer instance
    """
    index = faiss.read_index(index_path)
    with open(mapping_path) as f:
        mapping = json.load(f)

    # Normalize site_ids to canonical form (matching evidence/catalogue)
    raw_site_ids = mapping.get("site_ids", [])
    canonical_site_ids = _normalize_site_ids(raw_site_ids)

    config = RetrievalConfig(similarity_threshold=threshold, top_k=top_k)
    return ConfidenceLayer(
        index,
        mapping["image_ids"],
        mapping["paths"],
        config,
        site_ids=canonical_site_ids,
    )


import json