"""
Open-set recognition layer for heritage image classification.

This module implements a generic open-set rejection mechanism that:
1. Aggregates FAISS top-K results by site_id
2. Computes site-level scores (max and mean similarity)
3. Analyzes competitor/margin between top site and competitors
4. Uses calibrated thresholds to accept or reject

A candidate is only confirmed if:
- Its best similarity score exceeds the acceptance threshold
- The similarity gap (margin) to the next best competing site exceeds the rejection threshold
- The site has sufficient representation in the top-K results

Otherwise the result is classified as 'unknown'.

This prevents high-similarity but incorrect FAISS nearest neighbors from
being automatically accepted when the query image belongs to an
out-of-catalog or visually dissimilar monument.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


# Default calibrated thresholds (can be overridden)
# Calibrated against the real CLIP + FAISS index: true matches score 1.0,
# while the highest cross-monument similarity (an indexed image's best score
# against a *different* site) is 0.8408.  The accept threshold must sit above
# that ceiling so out-of-catalog images are rejected and routed to the global
# vision fallback instead of being accepted as a local match.
DEFAULT_ACCEPT_THRESHOLD = 0.85    # Minimum best similarity to consider a site
DEFAULT_MARGIN_THRESHOLD = 0.10    # Minimum gap between top site and next
DEFAULT_AGGREGATE_MIN_COUNT = 1    # Min # of top-K votes for a site to be valid


@dataclass
class SiteScore:
    """Score for a single candidate site."""
    site_id: str
    best_score: float  # Maximum similarity for this site
    mean_score: float  # Mean similarity across all votes for this site
    vote_count: int    # How many times this site appeared in top-K
    all_scores: List[float] = field(default_factory=list)


@dataclass
class OpenSetDecision:
    """Result of open-set decision."""
    confirmed: bool
    site_id: Optional[str]
    similarity: Optional[float]
    reason: str
    site_scores: Dict[str, SiteScore]


class OpenSetRejection:
    """
    Open-set rejection layer for heritage monument recognition.

    Uses multiple signals to decide whether a FAISS top-K result can be
    confidently accepted as the correct monument, or should be rejected
    as 'unknown'.
    """

    def __init__(
        self,
        accept_threshold: float = DEFAULT_ACCEPT_THRESHOLD,
        margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
        aggregate_min_count: int = DEFAULT_AGGREGATE_MIN_COUNT,
        top_k: int = 5,
    ):
        self.accept_threshold = accept_threshold
        self.margin_threshold = margin_threshold
        self.aggregate_min_count = aggregate_min_count
        self.top_k = top_k

    def aggregate_by_site(
        self,
        matches: List[dict],
    ) -> Dict[str, SiteScore]:
        """
        Aggregate top-K FAISS results by site_id.

        Each match dict must contain 'site_id' and 'similarity'.
        Returns a dict mapping site_id -> SiteScore.
        """
        site_data: Dict[str, List[float]] = {}

        for match in matches:
            sid = match["site_id"]
            sim = match["similarity"]
            if sid not in site_data:
                site_data[sid] = []
            site_data[sid].append(sim)

        site_scores = {}
        for sid, scores in site_data.items():
            site_scores[sid] = SiteScore(
                site_id=sid,
                best_score=max(scores),
                mean_score=np.mean(scores),
                vote_count=len(scores),
                all_scores=list(scores),
            )

        return site_scores

    def compute_margin(
        self,
        top_site: SiteScore,
        all_sites: Dict[str, SiteScore],
    ) -> float:
        """
        Compute the similarity margin between top site and competitors.

        Returns the minimum gap between top site's best score and any
        other site's best score.
        """
        if len(all_sites) <= 1:
            return float("inf")

        other_best = max(
            s.best_score for s in all_sites.values() if s.site_id != top_site.site_id
        )
        return top_site.best_score - other_best

    def decide(
        self,
        matches: List[dict],
        top_k: Optional[int] = None,
    ) -> OpenSetDecision:
        """
        Make open-set decision on top-K FAISS results.

        Returns an OpenSetDecision with confirmed flag, site_id (or None),
        similarity (or None), and reason for acceptance or rejection.
        """
        if not matches:
            return OpenSetDecision(
                confirmed=False,
                site_id=None,
                similarity=None,
                reason="no_candidates",
                site_scores={},
            )

        effective_k = top_k or self.top_k
        top_matches = matches[:effective_k]

        # Aggregate matches by site
        site_scores = self.aggregate_by_site(top_matches)

        if not site_scores:
            return OpenSetDecision(
                confirmed=False,
                site_id=None,
                similarity=None,
                reason="no_site_matches",
                site_scores={},
            )

        # Sort by best score descending
        sorted_sites = sorted(
            site_scores.values(),
            key=lambda s: s.best_score,
            reverse=True,
        )

        top_site = sorted_sites[0]

        # Check acceptance criteria
        if top_site.best_score < self.accept_threshold:
            return OpenSetDecision(
                confirmed=False,
                site_id=None,
                similarity=None,
                reason=f"best_score_below_threshold ({top_site.best_score:.3f} < {self.accept_threshold})",
                site_scores=site_scores,
            )

        # Check vote/min-count for confidence
        min_votes = min(self.aggregate_min_count, effective_k)
        if top_site.vote_count < min_votes:
            return OpenSetDecision(
                confirmed=False,
                site_id=None,
                similarity=None,
                reason=f"insufficient_votes ({top_site.vote_count} < {min_votes})",
                site_scores=site_scores,
            )

        # Check margin against competitors
        margin = self.compute_margin(top_site, site_scores)

        if margin < self.margin_threshold:
            # The top site is not significantly better than competitors
            # This could indicate an ambiguous / out-of-distribution query
            # or an image matching multiple monuments
            return OpenSetDecision(
                confirmed=False,
                site_id=None,
                similarity=None,
                reason=f"margin_too_small ({margin:.3f} < {self.margin_threshold})",
                site_scores=site_scores,
            )

        # All checks passed - accept the match
        return OpenSetDecision(
            confirmed=True,
            site_id=top_site.site_id,
            similarity=top_site.best_score,
            reason="accepted",
            site_scores=site_scores,
        )


def open_set_decide(
    matches: List[dict],
    accept_threshold: float = DEFAULT_ACCEPT_THRESHOLD,
    margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
    aggregate_min_count: int = DEFAULT_AGGREGATE_MIN_COUNT,
    top_k: int = 5,
) -> OpenSetDecision:
    """
    Convenience function to perform open-set decision.

    Args:
        matches: List of dicts with 'site_id' and 'similarity' keys
        accept_threshold: Minimum similarity to consider a site
        margin_threshold: Minimum gap between top site and competitors
        aggregate_min_count: Min votes needed for a site
        top_k: Number of top candidates to analyze

    Returns:
        OpenSetDecision with confirmed, site_id, similarity, reason
    """
    rejection = OpenSetRejection(
        accept_threshold=accept_threshold,
        margin_threshold=margin_threshold,
        aggregate_min_count=aggregate_min_count,
        top_k=top_k,
    )
    return rejection.decide(matches, top_k)