"""
Unit tests for the evaluation framework.

These tests use only synthetic data and pure-Python stubs so they run
instantly without requiring any model download, dataset, or external
dependency beyond the Python standard library and the project's own code.
"""

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    average_precision,
    ndcg_at_k,
    evaluate_ranking,
    evaluate_rankings,
)
from evaluation.benchmark import BenchmarkDataset, run_benchmark


# ── metric tests ────────────────────────────────────────────────────────────

class TestMetrics(TestCase):
    # precision@k
    def test_precision_at_k_perfect(self):
        self.assertEqual(precision_at_k(["a", "b", "c"], {"a", "b"}, k=2), 1.0)
        self.assertEqual(precision_at_k(["a", "b", "c"], {"a", "b"}, k=3), 2/3)

    def test_precision_at_k_empty(self):
        self.assertEqual(precision_at_k([], {"a"}, k=5), 0.0)
        self.assertEqual(precision_at_k(["a", "b"], set(), k=2), 0.0)
        # k=0 falls back to the full ranking, so precision is computed over all items
        self.assertEqual(precision_at_k(["a", "b"], {"a"}, k=0), 0.5)

    def test_precision_at_k_duplicates(self):
        self.assertEqual(precision_at_k(["a", "a", "b"], {"a", "b"}, k=2), 1.0)

    # recall@k
    def test_recall_at_k_perfect(self):
        self.assertEqual(recall_at_k(["a", "b"], {"a", "b"}, k=2), 1.0)
        self.assertEqual(recall_at_k(["a", "x", "b"], {"a", "b"}, k=3), 1.0)

    def test_recall_at_k_partial(self):
        self.assertEqual(recall_at_k(["a", "x"], {"a", "b", "c"}, k=2), 1/3)

    def test_recall_at_k_empty(self):
        self.assertEqual(recall_at_k([], {"a"}, k=5), 0.0)
        self.assertEqual(recall_at_k(["a", "b"], set(), k=2), 0.0)

    # reciprocal_rank
    def test_reciprocal_rank_first(self):
        self.assertEqual(reciprocal_rank(["a", "b", "c"], {"a"}), 1.0)
        self.assertEqual(reciprocal_rank(["x", "a", "y"], {"a", "z"}), 1/2)

    def test_reciprocal_rank_none(self):
        self.assertEqual(reciprocal_rank(["x", "y"], {"a"}), 0.0)
        self.assertEqual(reciprocal_rank([], {"a"}), 0.0)

    # average_precision
    def test_average_precision_perfect(self):
        self.assertEqual(average_precision(["a", "b"], {"a", "b"}), 1.0)
        self.assertAlmostEqual(average_precision(["a", "x", "b"], {"a", "b"}), 5/6)

    def test_average_precision_none(self):
        self.assertEqual(average_precision(["x", "y"], {"a"}), 0.0)

    def test_average_precision_interleaved(self):
        # relevant at positions 1, 3, 4 -> precisions: 1/1, 2/3, 3/4
        # average = (1 + 2/3 + 3/4) / 3 = (12/12 + 8/12 + 9/12) / 3 = 29/36
        self.assertAlmostEqual(
            average_precision(["a", "x", "b", "c"], {"a", "b", "c"}),
            29/36,
            places=5,
        )

    # ndcg@k
    def test_ndcg_at_k_perfect(self):
        self.assertEqual(ndcg_at_k(["a", "b"], {"a", "b"}, k=2), 1.0)
        self.assertEqual(ndcg_at_k(["a", "b", "c"], {"a", "b"}, k=2), 1.0)

    def test_ndcg_at_k_zero(self):
        self.assertEqual(ndcg_at_k(["a", "b"], set(), k=2), 0.0)
        self.assertEqual(ndcg_at_k([], {"a"}, k=2), 0.0)

    def test_ndcg_at_k_partial(self):
        # retrieved: [rel, non, rel] @ k=3 -> DCG = 1/log2(2) + 0 + 1/log2(4) = 1 + 0.5 = 1.5
        # ideal: [rel, rel] -> IDCG = 1/log2(2) + 1/log2(3) = 1 + 0.6309 = 1.6309
        # ndcg = 1.5 / 1.6309 ≈ 0.919
        self.assertAlmostEqual(
            ndcg_at_k(["rel", "non", "rel"], {"rel"}, k=3),
            0.919,
            places=2,
        )

    # evaluate_ranking / evaluate_rankings
    def test_evaluate_ranking(self):
        out = evaluate_ranking(["a", "b", "c"], {"a", "c"}, k=2)
        self.assertAlmostEqual(out["precision@2"], 0.5)
        self.assertAlmostEqual(out["recall@2"], 0.5)
        self.assertAlmostEqual(out["mrr"], 1.0)
        self.assertAlmostEqual(out["map"], 5/6)
        self.assertAlmostEqual(out["ndcg@2"], 1.0)

    def test_evaluate_rankings(self):
        rankings = [
            (["a", "b"], {"a"}),  # p@1=1, r@1=1, mrr=1, ap=1, ndcg@1=1
            (["b", "a"], {"a"}),  # p@1=0, r@1=0, mrr=1/2, ap=1/2, ndcg@1=0
        ]
        out = evaluate_rankings(rankings, k=1)
        self.assertEqual(out["n_queries"], 2)
        self.assertAlmostEqual(out["precision@1"], 0.5)
        self.assertAlmostEqual(out["recall@1"], 0.5)
        self.assertAlmostEqual(out["mrr"], 0.75)
        self.assertAlmostEqual(out["map"], 0.75)
        self.assertAlmostEqual(out["ndcg@1"], 0.5)


# ── benchmark tests ────────────────────────────────────────────────────────

class TestBenchmark(TestCase):
    def setUp(self):
        # tiny synthetic manifest - JSON lines format
        records = [
            {"image_path": "img1.jpg", "entity_id": "e1", "split": "gallery"},
            {"image_path": "img2.jpg", "entity_id": "e2", "split": "gallery"},
            {"image_path": "img3.jpg", "entity_id": "e1", "split": "gallery"},
            {"image_path": "q1.jpg",  "entity_id": "e1", "split": "query"},
            {"image_path": "q2.jpg",  "entity_id": "e2", "split": "query"},
        ]
        self.manifest = "\n".join(json.dumps(r) for r in records)

    def test_dataset_from_manifest(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
            f.write(self.manifest)
            f.flush()
            ds = BenchmarkDataset.from_manifest(f.name)
            self.assertEqual(ds.n_gallery(), 3)
            self.assertEqual(ds.n_queries(), 2)
            self.assertEqual(ds.name, Path(f.name).stem)

    def test_run_benchmark_stub(self):
        def stub_retrieve(query_path, gallery_paths, top_k=5):
            # always return the same order regardless of query
            return [(p, 1.0 - i/len(gallery_paths)) for i, p in enumerate(gallery_paths)]

        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
            f.write(self.manifest)
            f.flush()
            ds = BenchmarkDataset.from_manifest(f.name)
            result = run_benchmark(ds, stub_retrieve, k=2, top_k=5)
            self.assertEqual(result["dataset"], ds.name)
            self.assertEqual(result["method"], "stub_retrieve")
            self.assertEqual(result["mean"]["n_queries"], 2)
            # we don't assert specific numbers because the stub is arbitrary,
            # only that the structure is correct and no exception is raised.

    def test_compare_methods(self):
        def method_a(*args, **kwargs):
            return [("img1.jpg", 1.0), ("img2.jpg", 0.5)]

        def method_b(*args, **kwargs):
            return [("img2.jpg", 1.0), ("img1.jpg", 0.5)]

        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
            f.write(self.manifest)
            f.flush()
            ds = BenchmarkDataset.from_manifest(f.name)
            from evaluation.benchmark import compare_methods
            results = compare_methods(ds, {"A": method_a, "B": method_b}, k=2, top_k=5)
            self.assertIn("A", results)
            self.assertIn("B", results)
            self.assertEqual(results["A"]["method"], "method_a")
            self.assertEqual(results["B"]["method"], "method_b")