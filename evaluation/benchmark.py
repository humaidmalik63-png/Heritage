"""
Modular retrieval benchmark for image-query evaluation.

The benchmark is designed to be **dataset-agnostic** and **model-agnostic**:

* A *dataset* is represented by :class:`BenchmarkDataset`, which loads a simple
  JSON-lines metadata manifest and exposes the gallery (reference) items and
  the queries with their ground-truth relevant sets.

* A *retrieval method* is a callable ``(query_path, gallery_paths) -> list`` that
  returns ranked ``(image_path, score)`` tuples.  The existing
  ``ml.baseline_retrieval.rank_candidates`` and
  ``ml.visual_embedding.rank_candidates`` both already conform to this
  signature, so no adapter is needed for either.

* The benchmark itself does **not** download any model or dataset; it simply
  invokes the supplied method callback for each query and aggregates metrics.

Example
-------
>>> from evaluation.benchmark import BenchmarkDataset, run_benchmark
>>> import ml.baseline_retrieval as baseline
>>> ds = BenchmarkDataset.from_manifest("data/evaluation/metadata.json")
>>> results = run_benchmark(ds, baseline.rank_candidates, k=5, top_k=5)
>>> print(results["mean"]["mrr"])
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from evaluation.metrics import evaluate_ranking, evaluate_rankings

__all__ = ["BenchmarkDataset", "RetrievalMethod", "run_benchmark"]


# ── type aliases ──────────────────────────────────────────────────────────────

_RankedItem = Tuple[str, float]
QueryRanked = List[_RankedItem]
RetrievalMethod = Callable[..., List[_RankedItem]]


# ── dataset container ─────────────────────────────────────────────────────────

@dataclass
class BenchmarkDataset:
    """
    A dataset container holding gallery and query records.

    Each record is a dict with at least:
    - ``image_path``: path to the image file
    - ``entity_id``: ground-truth entity/site label

    Additional fields are preserved and ignored by the benchmark.
    """

    gallery: List[Dict[str, Any]] = field(default_factory=list)
    queries: List[Dict[str, Any]] = field(default_factory=list)
    name: str = "unnamed"

    # ── constructors ────────────────────────────────────────────────────────

    @classmethod
    def from_manifest(cls, path: Union[str, Path]) -> "BenchmarkDataset":
        """
        Load a dataset from a JSON-lines manifest.

        Each line is a JSON object with at minimum ``image_path``,
        ``entity_id`` and ``split`` (``"gallery"`` or ``"query"``).
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")

        gallery: List[Dict[str, Any]] = []
        queries: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON on line {line_no} of {path}: {exc}"
                    ) from exc

                split = record.get("split")
                if split == "gallery":
                    gallery.append(record)
                elif split == "query":
                    queries.append(record)
                else:
                    raise ValueError(
                        f"Unknown split '{split}' on line {line_no}; "
                        f"expected 'gallery' or 'query'."
                    )

        return cls(gallery=gallery, queries=queries, name=path.stem)

    @classmethod
    def from_records(
        cls,
        records: Iterable[Dict[str, Any]],
        name: str = "unnamed",
    ) -> "BenchmarkDataset":
        """Build a dataset from an in-memory iterable of records."""
        gallery = [r for r in records if r.get("split") == "gallery"]
        queries = [r for r in records if r.get("split") == "query"]
        return cls(gallery=gallery, queries=queries, name=name)

    # ── helpers ─────────────────────────────────────────────────────────────

    def _gallery_paths(self) -> List[str]:
        return [str(Path(r["image_path"])) for r in self.gallery]

    def _relevant_for(self, query_record: Dict[str, Any]) -> List[str]:
        """Gallery paths whose entity_id matches the query's entity_id."""
        target = query_record["entity_id"]
        return [
            str(Path(r["image_path"]))
            for r in self.gallery
            if r.get("entity_id") == target
        ]

    def n_queries(self) -> int:
        return len(self.queries)

    def n_gallery(self) -> int:
        return len(self.gallery)


# ── benchmark runner ─────────────────────────────────────────────────────────

def run_benchmark(
    dataset: BenchmarkDataset,
    retrieve: RetrievalMethod,
    k: int = 5,
    top_k: int = 5,
    **retrieve_kwargs: Any,
) -> Dict[str, Any]:
    """
    Run a retrieval benchmark over a dataset.

    Parameters
    ----------
    dataset : BenchmarkDataset
        The dataset to evaluate against.
    retrieve : RetrievalMethod
        A callable with signature ``retrieve(query_path, gallery_paths,
        top_k=...) -> list[(path, score)]``.
    k : int
        Cutoff used for precision/recall/ndcg metrics.
    top_k : int
        Number of candidates the retrieval method should return (passed as
        ``top_k`` to the method).
    **retrieve_kwargs
        Extra keyword arguments forwarded to ``retrieve``.

    Returns
    -------
    dict
        ``{"dataset": ..., "method": ..., "per_query": [...], "mean": {...}}``
        The ``"mean"`` dict holds averaged metrics; ``"per_query"`` is a list
        of per-query result dicts.
    """
    if dataset.n_queries() == 0:
        return {
            "dataset": dataset.name,
            "method": getattr(retrieve, "__name__", "unknown"),
            "per_query": [],
            "mean": {"n_queries": 0},
        }

    gallery_paths = dataset._gallery_paths()
    rankings: List[_RankedItem] = []  # (retrieved_paths, relevant_paths)
    per_query: List[Dict[str, Any]] = []

    for q_rec in dataset.queries:
        query_path = str(Path(q_rec["image_path"]))
        relevant = dataset._relevant_for(q_rec)

        ranked = retrieve(query_path, gallery_paths, top_k=top_k, **retrieve_kwargs)
        retrieved_paths = [p for p, _ in ranked]

        rankings.append((retrieved_paths, relevant))
        per_query.append({
            "query": query_path,
            "entity_id": q_rec.get("entity_id"),
            "retrieved": retrieved_paths,
            "relevant": relevant,
            "metrics": evaluate_ranking(retrieved_paths, relevant, k=k),
        })

    mean = evaluate_rankings(rankings, k=k)
    mean["method"] = getattr(retrieve, "__name__", "unknown")
    mean["dataset"] = dataset.name
    mean["k"] = k

    return {
        "dataset": dataset.name,
        "method": mean["method"],
        "per_query": per_query,
        "mean": mean,
    }


def compare_methods(
    dataset: BenchmarkDataset,
    methods: Dict[str, RetrievalMethod],
    k: int = 5,
    top_k: int = 5,
    **common_kwargs: Any,
) -> Dict[str, Any]:
    """
    Compare multiple retrieval methods on the same dataset.

    Parameters
    ----------
    dataset : BenchmarkDataset
    methods : dict
        Mapping ``name -> callable``.
    k, top_k, **common_kwargs
        Forwarded to :func:`run_benchmark` for each method.

    Returns
    -------
    dict
        ``{method_name: benchmark_result_dict}``.
    """
    results: Dict[str, Any] = {}
    for name, method in methods.items():
        result = run_benchmark(
            dataset, method, k=k, top_k=top_k, **common_kwargs
        )
        results[name] = result
    return results