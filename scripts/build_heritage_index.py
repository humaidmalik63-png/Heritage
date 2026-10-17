"""Generic heritage index builder.

Discovers all monument folders under data/raw/, indexes every valid image
(JPG/JPEG/PNG/WebP), and rebuilds the FAISS index plus mapping.json.

Usage:
    python -m scripts.build_heritage_index [--data_root data/raw]
"""

import argparse
import json
import sys
from pathlib import Path

import faiss
import numpy as np
from tqdm import tqdm

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.visual_embedding import VisualEmbeddingExtractor

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def discover_images(data_root: Path):
    """Recursively discover all image files, grouped by monument folder."""
    monuments = {}
    for dir_path in sorted(data_root.iterdir()):
        if not dir_path.is_dir():
            continue
        site_id = dir_path.name
        images = []
        for ext in IMAGE_EXTENSIONS:
            for f in dir_path.glob(f"*{ext}"):
                if f.is_file():
                    images.append(f)
        if images:
            monuments[site_id] = sorted(images)
    return monuments


def build_index(monuments: dict, output_index: Path, output_mapping: Path):
    """Build FAISS index and mapping.json from discovered monuments."""
    extractor = VisualEmbeddingExtractor()

    image_ids = []
    paths = []
    site_ids = []
    all_embeddings = []

    for site_id, images in monuments.items():
        for img in images:
            img_id = img.stem  # e.g. "jama_masjid_01"
            image_ids.append(img_id)
            # Store relative path from project root
            paths.append(str(img.relative_to(ROOT)))
            site_ids.append(site_id)

            emb = extractor.extract(img)
            all_embeddings.append(emb)

    embeddings = np.stack(all_embeddings).astype(np.float32)

    # Build FAISS index (inner product for cosine similarity on normalized vectors)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # Save index
    output_index.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output_index))

    # Save mapping
    mapping = {
        "image_ids": image_ids,
        "paths": paths,
        "site_ids": site_ids,
    }
    with open(output_mapping, "w") as f:
        json.dump(mapping, f, indent=2)

    return index, mapping


def verify_index(index, mapping):
    """Quick verification: search for each monument's first image."""
    print("\nVerification:")
    for site_id, images in globals().get("_monuments", {}).items():
        if not images:
            continue
        first = images[0]
        # Re-load extractor for verification
        from ml.visual_embedding import VisualEmbeddingExtractor
        extractor = VisualEmbeddingExtractor()
        emb = extractor.extract(first)
        scores, indices = index.search(emb.reshape(1, -1).astype("float32"), 3)
        top_site = mapping["site_ids"][indices[0][0]]
        print(f"  {site_id}: top-1 = {top_site} (sim={scores[0][0]:.3f})")


def main():
    parser = argparse.ArgumentParser(description="Build heritage FAISS index")
    parser.add_argument("--data_root", default="data/raw", help="Root directory with monument folders")
    parser.add_argument("--index_path", default="data/processed/index/clip_index.faiss")
    parser.add_argument("--mapping_path", default="data/processed/index/mapping.json")
    args = parser.parse_args()

    data_root = ROOT / args.data_root
    index_path = ROOT / args.index_path
    mapping_path = ROOT / args.mapping_path

    print(f"Discovering images in {data_root}...")
    monuments = discover_images(data_root)

    if not monuments:
        print("ERROR: No monuments found with images")
        return 1

    print(f"Found {len(monuments)} monuments:")
    total_images = 0
    for site_id, images in monuments.items():
        print(f"  {site_id}: {len(images)} images")
        total_images += len(images)
    print(f"\nTotal images to index: {total_images}")

    print("\nBuilding index...")
    index, mapping = build_index(monuments, index_path, mapping_path)
    globals()["_monuments"] = monuments

    print(f"\nIndex saved: {index_path}")
    print(f"  Vectors: {index.ntotal}")
    print(f"  Dimension: {index.d}")
    print(f"Mapping saved: {mapping_path}")
    print(f"  Entries: {len(mapping['image_ids'])}")

    verify_index(index, mapping)

    return 0


if __name__ == "__main__":
    sys.exit(main())
