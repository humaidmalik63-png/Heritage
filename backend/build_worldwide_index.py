#!/usr/bin/env python3
"""
Build worldwide FAISS index from global_monument_catalogue.json + global_image_manifest.json.

Generates CLIP embeddings for every monument that has at least one real image,
builds an IndexFlatIP index, and writes mapping.json + the index.

Run with the Python that has torch/transformers/faiss:
    C:/Users/humai/AppData/Local/Python/bin/python3.14.exe backend/build_worldwide_index.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import numpy as np

# Add project root for imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.visual_embedding import VisualEmbeddingExtractor

CATALOGUE_PATH = ROOT / "data" / "metadata" / "global_monument_catalogue.json"
IMAGE_MANIFEST_PATH = ROOT / "data" / "metadata" / "global_image_manifest.json"
OUTPUT_DIR = ROOT / "data" / "processed" / "index"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = OUTPUT_DIR / "clip_index.faiss"
MAPPING_PATH = OUTPUT_DIR / "mapping.json"

# Explicit, documented site ID aliases: raw directory names → canonical IDs.
# These directories exist under data/raw/ and their names differ from the
# canonical site_ids used in global_monument_catalogue.json and evidence files.
# Each mapping is unambiguous: a single raw directory name maps to exactly one
# canonical ID.  Unknown raw directory names pass through unchanged.
SITE_ID_ALIASES: dict[str, str] = {
    "red_fort": "red_fort_delhi",
    "jama_masjid": "jama_masjid_delhi",
}


def load_data() -> Tuple[List[Dict], Dict]:
    """Load catalogue and image manifest."""
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        catalogue = json.load(f)

    with open(IMAGE_MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    # manifest is a list of objects, each with 'site_id' and 'images'
    # Convert to dict: site_id -> {images: [...], ...}
    images: Dict = {}
    for entry in manifest:
        sid = entry.get("site_id")
        if sid:
            images[sid] = entry

    return catalogue, images


def resolve_image_path(site_id: str, entry: Dict) -> Path | None:
    """Resolve the local filesystem path for a monument's card image."""
    # Try the first image in the entry
    imgs = entry.get("images", [])
    if imgs:
        local_path = imgs[0].get("local_path")
        if local_path:
            p = ROOT / local_path
            if p.exists():
                return p

    # Try local sites/ directory (frontend_new assets)
    local = ROOT / "frontend_new" / "assets" / "images" / "sites" / f"{site_id}.webp"
    if local.exists():
        return local

    return None


def collect_local_raw_images() -> List[Tuple[str, Path]]:
    """Collect all images from data/raw/ (indexed monuments)."""
    raw_dir = ROOT / "data" / "raw"
    results = []
    if not raw_dir.exists():
        return results

    for site_dir in sorted(raw_dir.iterdir()):
        if not site_dir.is_dir() or site_dir.name == "global":
            continue
        site_id = site_dir.name
        for img_file in sorted(site_dir.iterdir()):
            if img_file.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                results.append((site_id, img_file))
    return results


def build_index(
    index_output: Union[str, Path, None] = None,
    mapping_output: Union[str, Path, None] = None,
) -> None:
    """Build worldwide FAISS index from global_monument_catalogue.json + global_image_manifest.json.

    If index_output or mapping_output are provided, the index and mapping
    are written to those paths instead of the default production paths.
    This allows building a candidate index without overwriting the production
    artefacts.

    Args:
        index_output: Optional path for the FAISS index. If None, uses the
            default production path (clip_index.faiss).
        mapping_output: Optional path for the mapping JSON. If None, uses
            the default production path (mapping.json).
    """
    catalogue, images = load_data()

    extractor = VisualEmbeddingExtractor()
    # Warm up the model
    _ = extractor.embedding_dim

    embeddings: List[np.ndarray] = []
    image_ids: List[str] = []
    paths: List[str] = []
    site_ids: List[str] = []

    # 1. Process monuments from global manifest
    for record in catalogue:
        site_id = record.get("site_id")
        if not site_id:
            continue

        entry = images.get(site_id)
        if not entry:
            continue

        img_path = resolve_image_path(site_id, entry)
        if not img_path:
            continue

        try:
            emb = extractor.extract(img_path)
            embeddings.append(emb)
            suffix = len([i for i in image_ids if i.startswith(site_id + "_")]) + 1
            image_ids.append(f"{site_id}_{suffix:02d}")
            paths.append(str(img_path.relative_to(ROOT)))
            site_ids.append(site_id)
        except Exception as e:
            print(f"  FAILED {site_id}: {e}")

    # 2. Add local raw images (original 6 Indian monuments)
    # Resolve raw directory names to canonical site IDs using the explicit
    # SITE_ID_ALIASES mapping.  This ensures the FAISS mapping uses the same
    # canonical IDs as the catalogue and evidence files, while preserving
    # backwards compatibility for directories without a documented alias.
    local_images = collect_local_raw_images()
    resolved_images: List[Tuple[str, any]] = []
    for site_id, img_path in local_images:
        # Normalize through the documented alias map; pass through unchanged
        # if no alias is defined.
        canonical_id = SITE_ID_ALIASES.get(site_id, site_id)
        resolved_images.append((canonical_id, img_path))

    for site_id, img_path in resolved_images:
        try:
            emb = extractor.extract(img_path)
            embeddings.append(emb)
            suffix = len([i for i in image_ids if i.startswith(site_id + "_")]) + 1
            image_ids.append(f"{site_id}_{suffix:02d}")
            paths.append(str(img_path.relative_to(ROOT)))
            site_ids.append(site_id)
        except Exception as e:
            print(f"  FAILED local {site_id}: {e}")

    if not embeddings:
        print("No embeddings generated!")
        return

    # Stack embeddings
    emb_matrix = np.vstack(embeddings).astype(np.float32)
    print(f"Generated {len(embeddings)} embeddings, dim={emb_matrix.shape[1]}")

    # Build FAISS index (IndexFlatIP for cosine similarity with normalized vectors)
    index = faiss.IndexFlatIP(emb_matrix.shape[1])
    index.add(emb_matrix)
    print(f"FAISS index total vectors: {index.ntotal}")

    # Resolve output paths: use provided paths or fall back to defaults
    if index_output is None:
        index_output = INDEX_PATH
    if mapping_output is None:
        mapping_output = MAPPING_PATH

    # Ensure output directory exists
    index_out_path = Path(index_output)
    mapping_out_path = Path(mapping_output)
    index_out_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_out_path.parent.mkdir(parents=True, exist_ok=True)

    # Save index
    faiss.write_index(index, str(index_out_path))
    print(f"Index saved to {index_out_path}")

    # Save mapping
    mapping = {
        "image_ids": image_ids,
        "paths": paths,
        "site_ids": site_ids,
    }
    with open(mapping_out_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=1)
        f.write("\n")
    print(f"Mapping saved to {mapping_out_path}")

    # Quick self-test: query first embedding against index
    distances, indices = index.search(emb_matrix[:1], min(5, index.ntotal))
    print(f"Self-test top-5 for {site_ids[0]}:")
    for dist, idx in zip(distances[0], indices[0]):
        if idx >= 0:
            print(f"  {image_ids[idx]}: {dist:.4f}")

    # Check cross-monument similarity ceiling
    max_cross = 0.0
    sample_size = min(50, len(embeddings))
    for i in range(sample_size):
        d, i_idx = index.search(emb_matrix[i:i+1], 2)
        if len(i_idx[0]) > 1 and i_idx[0][1] >= 0:
            other_site = site_ids[i_idx[0][1]]
            if other_site != site_ids[i]:
                max_cross = max(max_cross, float(d[0][1]))

    print(f"\nMax cross-monument similarity (sample of {sample_size}): {max_cross:.4f}")
    print(f"Current accept threshold: 0.85")
    print(f"Gap to threshold: {0.85 - max_cross:.4f}")


if __name__ == "__main__":
    build_index()