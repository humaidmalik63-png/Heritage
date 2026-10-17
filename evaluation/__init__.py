"""Evaluation framework for image retrieval methods.

This package provides a modular, dependency-light evaluation framework for
comparing retrieval methods on image-query datasets.  It is intentionally
decoupled from any specific model or dataset: retrieval methods are pluggable
callables, datasets are plain metadata files, and metrics operate on
rankings (lists of retrieved item identifiers with scores).
"""

from evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    average_precision,
    ndcg_at_k,
    evaluate_ranking,
    evaluate_rankings,
)
from evaluation.benchmark import (
    BenchmarkDataset,
    RetrievalMethod,
    run_benchmark,
)

__all__ = [
    "precision_at_k",
    "recall_at_k",
    "mrr",
    "map_at_k",
    "ndcg_at_k",
    "evaluate_ranking",
    "evaluate_rankings",
    "BenchmarkDataset",
    "RetrievalMethod",
    "run_benchmark",
]