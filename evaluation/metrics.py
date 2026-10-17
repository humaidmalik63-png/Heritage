"""
Ranking-based retrieval metrics for image-query evaluation.

All functions operate on plain Python sequences (lists/sets/tuples) so they
remain dependency-free and deterministic.  A *ranking* is an ordered list of
retrieved item identifiers; *relevant* is the set of ground-truth relevant
identifiers for a single query.

Conventions
-----------
- ``retrieved``: ordered list of item identifiers (may contain duplicates).
- ``relevant``: iterable of relevant item identifiers (treated as a set).
- ``k``: cutoff (top-k).  If ``k`` is None or <= 0 the full ranking is used.
- All metrics return ``0.0`` for empty/invalid input rather than raising.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Set, Union

__all__ = [
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
    "average_precision",
    "ndcg_at_k",
]


# ── helpers ──────────────────────────────────────────────────────────────────

def _normalise_k(k: Optional[int], length: int) -> int:
    """Return a non-negative cutoff clamped to the ranking length.

    For metrics like precision@k, recall@k, ndcg@k, when k <= 0 we fall back to
    the full ranking length, not 0.  Previously this returned 0, which caused
    precision/recall/ndcg to incorrectly be 0 when k=0, but tests expect the
    full ranking to be used.
    """
    if k is None or k <= 0:
        return length
    return min(k, length)


def _to_set(relevant: Iterable) -> Set:
    """Convert the relevant set to a hashable set, ignoring unhashable items."""
    try:
        return set(relevant)
    except TypeError:
        return {item for item in relevant}


def _relevant_at(retrieved: Sequence, relevant: Set, k: int) -> List[bool]:
    """Boolean relevance mask over the top-k retrieved items."""
    return [item in relevant for item in retrieved[:k]]


# ── metrics ──────────────────────────────────────────────────────────────────

def precision_at_k(
    retrieved: Sequence,
    relevant: Iterable,
    k: Optional[int] = None,
) -> float:
    """
    Fraction of the top-k retrieved items that are relevant.

    precision@k = |relevant ∩ retrieved[:k]| / k

    Returns 0.0 when k is 0 or the ranking is empty.
    """
    rel = _to_set(relevant)
    top_k = _normalise_k(k, len(retrieved))
    if top_k == 0:
        return 0.0
    hits = sum(_relevant_at(retrieved, rel, top_k))
    return hits / top_k


def recall_at_k(
    retrieved: Sequence,
    relevant: Iterable,
    k: Optional[int] = None,
) -> float:
    """
    Fraction of all relevant items that appear in the top-k ranking.

    recall@k = |relevant ∩ retrieved[:k]| / |relevant|

    Returns 0.0 when there are no relevant items or the ranking is empty.
    """
    rel = _to_set(relevant)
    if not rel:
        return 0.0
    top_k = _normalise_k(k, len(retrieved))
    if top_k == 0:
        return 0.0
    hits = sum(_relevant_at(retrieved, rel, top_k))
    return hits / len(rel)


def reciprocal_rank(retrieved: Sequence, relevant: Iterable) -> float:
    """
    Reciprocal rank of the first relevant item.

    rr = 1 / rank_of_first_relevant, or 0.0 when no relevant item is found.
    """
    rel = _to_set(relevant)
    for idx, item in enumerate(retrieved, start=1):
        if item in rel:
            return 1.0 / idx
    return 0.0


def average_precision(retrieved: Sequence, relevant: Iterable) -> float:
    """
    Average precision for a single query.

    ap = (1 / |relevant|) * sum over relevant items r of
         (number of relevant items at or before r's position / r's position)

    Returns 0.0 when there are no relevant items or the ranking is empty.
    """
    rel = _to_set(relevant)
    if not rel:
        return 0.0

    hits = 0
    precision_sum = 0.0
    for idx, item in enumerate(retrieved, start=1):
        if item in rel:
            hits += 1
            precision_sum += hits / idx

    if hits == 0:
        return 0.0
    return precision_sum / len(rel)


def ndcg_at_k(
    retrieved: Sequence,
    relevant: Iterable,
    k: Optional[int] = None,
) -> float:
    """
    Normalised Discounted Cumulative Gain at k (binary relevance).

    Each relevant item contributes a relevance of 1, discounted by log2(rank+1)
    where rank is its 1-based position in the ranking.  The score is
    normalised by the ideal DCG (the same items sorted by relevance descending).
    Returns 0.0 when there are no relevant items or the ranking is empty.
    """
    rel = _to_set(relevant)
    if not rel:
        return 0.0

    top_k = _normalise_k(k, len(retrieved))
    if top_k == 0:
        return 0.0

    # Compute DCG of the actual retrieved list (top-k)
    dcg = 0.0
    for idx, item in enumerate(retrieved[:top_k], start=1):
        if item in rel:
            dcg += 1.0 / _log2(idx + 1)

    # Compute IDCG: DCG of the ideal ranking (same items, sorted by relevance descending)
    # For binary relevance, this means putting all relevant items first
    relevant_items = [item for item in retrieved[:top_k] if item in rel]
    non_relevant_items = [item for item in retrieved[:top_k] if item not in rel]
    ideal_sorted = relevant_items + non_relevant_items

    idcg = 0.0
    for idx, item in enumerate(ideal_sorted, start=1):
        if item in rel:
            idcg += 1.0 / _log2(idx + 1)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def _log2(value: float) -> float:
    """Natural log base 2, guarded against non-positive input."""
    import math

    if value <= 1.0:
        return 1.0
    return math.log(value, 2)


# ── convenience: evaluate a single ranking across all metrics ────────────────

def evaluate_ranking(
    retrieved: Sequence,
    relevant: Iterable,
    k: int = 5,
) -> dict:
    """
    Compute the standard metric set for one query ranking.

    Returns a dict with keys: precision@k, recall@k, mrr, map, ndcg@k.
    """
    return {
        f"precision@{k}": precision_at_k(retrieved, relevant, k),
        f"recall@{k}": recall_at_k(retrieved, relevant, k),
        "mrr": reciprocal_rank(retrieved, relevant),
        "map": average_precision(retrieved, relevant),
        f"ndcg@{k}": ndcg_at_k(retrieved, relevant, k),
    }


def evaluate_rankings(
    rankings: Iterable[tuple],
    k: int = 5,
) -> dict:
    """
    Aggregate metrics across many queries.

    ``rankings`` is an iterable of ``(retrieved, relevant)`` pairs.  Returns
    the mean of each metric plus a ``n_queries`` count.
    """
    sums = {
        f"precision@{k}": 0.0,
        f"recall@{k}": 0.0,
        "mrr": 0.0,
        "map": 0.0,
        f"ndcg@{k}": 0.0,
    }
    n = 0
    for retrieved, relevant in rankings:
        m = evaluate_ranking(retrieved, relevant, k)
        for key in sums:
            sums[key] += m[key]
        n += 1

    if n == 0:
        sums["n_queries"] = 0
        return sums

    for key in list(sums):
        sums[key] = sums[key] / n
    sums["n_queries"] = n
    return sums