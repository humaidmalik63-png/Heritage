# Evaluation Plan – Visual Heritage Retrieval

## Objective
Compare the existing retrieval methods quantitatively and reproducibly:

| Method | Module | Type |
|---|---|---|
| Classical baseline | `ml/baseline_retrieval.py` | RGB color-histogram + cosine |
| Visual embedding | `ml/visual_embedding.py` | CLIP ViT-B/32 512-dim L2-normalised |

## Dataset format
A JSON-lines manifest, one record per line, each with at minimum:

```json
{"image_path": "img1.jpg", "entity_id": "taj_mahal", "split": "gallery"}
{"image_path": "q1.jpg",   "entity_id": "taj_mahal", "split": "query"}
```

Fields:
- `image_path` – path to the image file (relative or absolute).
- `entity_id` – ground-truth heritage site / entity label.
- `split` – `"gallery"` or `"query"`.

The manifest is the single source of truth for the benchmark; no heritage sites are hard-coded anywhere.

## Train / gallery / query separation
- **Gallery**: reference images against which queries are searched.
- **Query**: images for which retrieval is performed.
- Ground-truth relevance is defined implicitly: a query's relevant gallery items are all gallery records sharing the same `entity_id`.
- No training is involved – the methods are zero-shot / retrieval-only.

## Metrics (per query, then averaged)
| Metric | Definition |
|---|---|
| Precision@K | hits in top-K / K |
| Recall@K | hits in top-K / \|relevant\| |
| MRR | 1 / rank of first relevant item (0 if none) |
| mAP | mean of per-query average precision |
| nDCG@K | normalised DCG with binary relevance |

## Reproducibility
- Metrics are deterministic functions of rankings; no stochasticity in the framework.
- `BenchmarkDataset.from_manifest` always reads the same manifest → same numbers.
- Use a pinned, seeded environment (see `requirements.txt`).

## How to run later
```python
import ml.baseline_retrieval as baseline
from evaluation.benchmark import BenchmarkDataset, run_benchmark

ds = BenchmarkDataset.from_manifest("data/evaluation/metadata.json")
result = run_benchmark(ds, baseline.rank_candidates, k=5, top_k=5)
print(result["mean"])
```

## Meaningful comparison
- Same manifest, same `k`, same `top_k` for both methods.
- Use `run_benchmark` for the baseline and either `run_benchmark`
  (with a stub or a wrapper that calls `VisualEmbeddingExtractor`) for CLIP.
- Report per-query and mean metrics; inspect the per-query list for outliers.
