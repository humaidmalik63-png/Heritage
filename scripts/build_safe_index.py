#!/usr/bin/env python3
"""
Phase 5C-B: Safe Multi-Image Index Building Script
"""

from __future__ import annotations

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image

import faiss
import numpy as np

# Add project root for imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml.visual_embedding import VisualEmbeddingExtractor

CATALOGUE_PATH = ROOT / "data" / "metadata" / "global_monument_catalogue.json"
IMAGE_MANIFEST_PATH = ROOT / "data" / "metadata" / "global_image_manifest.json"
OUTPUT_DIR = ROOT / "data" / "processed" / "index"
TEMP_DIR = OUTPUT_DIR / "tmp"
FALLBACK_DIR = ROOT / "frontend_new" / "assets" / "images" / "sites"

INDEX_PATH = OUTPUT_DIR / "clip_index.faiss"
MAPPING_PATH = OUTPUT_DIR / "mapping.json"
FAILED_LOG_PATH = OUTPUT_DIR / "failed_log.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_safe_index() -> None:
    print("Starting Phase 5C-B Safe Multi-Image Index Building...")

    # Load catalogue and manifest
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        catalogue = json.load(f)
    valid_site_ids = {c["site_id"] for c in catalogue}

    with open(IMAGE_MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_map = {entry.get("site_id"): entry for entry in manifest if entry.get("site_id")}

    # Backup existing index and mapping
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    if INDEX_PATH.exists():
        backup_index = TEMP_DIR / "clip_index_backup.faiss"
        faiss.write_index(faiss.read_index(str(INDEX_PATH)), str(backup_index))
        print(f"Backed up current index to {backup_index}")
    if MAPPING_PATH.exists():
        backup_mapping = TEMP_DIR / "mapping_backup.json"
        with open(MAPPING_PATH, encoding="utf-8") as src, open(backup_mapping, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        print(f"Backed up current mapping to {backup_mapping}")

    extractor = VisualEmbeddingExtractor()
    _ = extractor.embedding_dim # Warmup

    embeddings: List[np.ndarray] = []
    image_ids: List[str] = []
    paths: List[str] = []
    site_ids: List[str] = []

    seen_hashes: set[str] = set()
    failed_log: List[Dict[str, str]] = []

    # Counters
    processed_count = 0
    skipped_count = 0
    dedup_count = 0

    # Process all sites in catalogue order
    for record in catalogue:
        site_id = record.get("site_id")
        if not site_id:
            continue

        entry = manifest_map.get(site_id)
        usable_for_site = 0

        if entry:
            images = entry.get("images", [])
            for img in images:
                processed_count += 1
                img_id = img.get("image_id")
                local_path_str = img.get("local_path")
                download_error = img.get("download_error")

                if not local_path_str:
                    # Check if there is a download_error with http_429_throttled (429) to provide a clearer reason
                    if download_error and "http_429_throttled" in str(download_error):
                        reason = "Manifest download failure (http_429_throttled)"
                        details = f"Image failed to download from manifest due to rate limiting: {download_error}"
                    else:
                        reason = "Manifest download failure"
                        details = download_error or "local_path is null"
                    failed_log.append({
                        "site_id": site_id,
                        "image_id": img_id,
                        "reason": reason,
                        "details": details
                    })
                    skipped_count += 1
                    continue

                p = ROOT / local_path_str
                if not p.exists():
                    failed_log.append({
                        "site_id": site_id,
                        "image_id": img_id,
                        "reason": "Missing local file",
                        "details": f"Path does not exist on disk: {local_path_str}"
                    })
                    skipped_count += 1
                    continue

                # Validate image load & format
                try:
                    with Image.open(p) as pil_img:
                        pil_img.verify()
                except Exception as e:
                    failed_log.append({
                        "site_id": site_id,
                        "image_id": img_id,
                        "reason": "Image decoding failure",
                        "details": str(e)
                    })
                    skipped_count += 1
                    continue

                # Hash content for deduplication
                try:
                    h = sha256_file(p)
                except Exception as e:
                    failed_log.append({
                        "site_id": site_id,
                        "image_id": img_id,
                        "reason": "Embedding failure",
                        "details": f"Hashing error: {e}"
                    })
                    skipped_count += 1
                    continue

                if h in seen_hashes:
                    dedup_count += 1
                    failed_log.append({
                        "site_id": site_id,
                        "image_id": img_id,
                        "reason": "Duplicate image content",
                        "details": f"SHA256 {h} already indexed"
                    })
                    continue

                # Extract embedding
                try:
                    emb = extractor.extract(p)
                except Exception as e:
                    failed_log.append({
                        "site_id": site_id,
                        "image_id": img_id,
                        "reason": "Embedding failure",
                        "details": str(e)
                    })
                    skipped_count += 1
                    continue

                seen_hashes.add(h)
                embeddings.append(emb)
                image_ids.append(img_id)
                paths.append(local_path_str)
                site_ids.append(site_id)
                usable_for_site += 1

        # If no usable manifest images for this site, try site-specific fallback WebP
        if usable_for_site == 0:
            fallback_path = FALLBACK_DIR / f"{site_id}.webp"
            if fallback_path.exists():
                processed_count += 1
                fallback_id = f"{site_id}_fallback"
                try:
                    with Image.open(fallback_path) as pil_img:
                        pil_img.verify()
                except Exception as e:
                    failed_log.append({
                        "site_id": site_id,
                        "image_id": fallback_id,
                        "reason": "Image decoding failure",
                        "details": f"Fallback error: {e}"
                    })
                    skipped_count += 1
                    continue

                try:
                    h = sha256_file(fallback_path)
                except Exception as e:
                    failed_log.append({
                        "site_id": site_id,
                        "image_id": fallback_id,
                        "reason": "Embedding failure",
                        "details": f"Fallback hashing error: {e}"
                    })
                    skipped_count += 1
                    continue

                if h in seen_hashes:
                    dedup_count += 1
                    failed_log.append({
                        "site_id": site_id,
                        "image_id": fallback_id,
                        "reason": "Duplicate image content",
                        "details": f"Fallback SHA256 {h} already indexed"
                    })
                else:
                    try:
                        emb = extractor.extract(fallback_path)
                    except Exception as e:
                        failed_log.append({
                            "site_id": site_id,
                            "image_id": fallback_id,
                            "reason": "Embedding failure",
                            "details": str(e)
                        })
                        skipped_count += 1
                        continue

                    seen_hashes.add(h)
                    embeddings.append(emb)
                    image_ids.append(fallback_id)
                    paths.append(str(fallback_path.relative_to(ROOT)))
                    site_ids.append(site_id)
                    usable_for_site += 1
            else:
                # Also check local raw dir for old Indian monuments if present (e.g. data/raw/taj_mahal/)
                raw_site_dir = ROOT / "data" / "raw" / site_id
                if raw_site_dir.exists() and raw_site_dir.is_dir():
                    for raw_img in sorted(raw_site_dir.iterdir()):
                        if raw_img.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                            processed_count += 1
                            raw_img_id = f"{site_id}_{len([i for i in image_ids if i.startswith(site_id + '_')]) + 1:02d}"
                            try:
                                with Image.open(raw_img) as pil_img:
                                    pil_img.verify()
                            except Exception as e:
                                failed_log.append({
                                    "site_id": site_id,
                                    "image_id": raw_img_id,
                                    "reason": "Image decoding failure",
                                    "details": str(e)
                                })
                                skipped_count += 1
                                continue

                            try:
                                h = sha256_file(raw_img)
                            except Exception as e:
                                failed_log.append({
                                    "site_id": site_id,
                                    "image_id": raw_img_id,
                                    "reason": "Embedding failure",
                                    "details": str(e)
                                })
                                skipped_count += 1
                                continue

                            if h in seen_hashes:
                                dedup_count += 1
                                failed_log.append({
                                    "site_id": site_id,
                                    "image_id": raw_img_id,
                                    "reason": "Duplicate image content",
                                    "details": f"Raw SHA256 {h} already indexed"
                                })
                            else:
                                try:
                                    emb = extractor.extract(raw_img)
                                except Exception as e:
                                    failed_log.append({
                                        "site_id": site_id,
                                        "image_id": raw_img_id,
                                        "reason": "Embedding failure",
                                        "details": str(e)
                                    })
                                    skipped_count += 1
                                    continue

                                seen_hashes.add(h)
                                embeddings.append(emb)
                                image_ids.append(raw_img_id)
                                paths.append(str(raw_img.relative_to(ROOT)))
                                site_ids.append(site_id)
                                usable_for_site += 1

    print(f"\nProcessing complete: Processed {processed_count}, Skipped {skipped_count}, Deduplicated {dedup_count}, Usable {len(embeddings)}")

    if not embeddings:
        print("ERROR: No embeddings generated! Aborting update.")
        sys.exit(1)

    # Build embedding matrix & FAISS index in TEMP_DIR
    emb_matrix = np.vstack(embeddings).astype(np.float32)
    dim = emb_matrix.shape[1]
    tmp_index_path = TEMP_DIR / "clip_index.faiss"
    tmp_mapping_path = TEMP_DIR / "mapping.json"

    new_index = faiss.IndexFlatIP(dim)
    new_index.add(emb_matrix)
    faiss.write_index(new_index, str(tmp_index_path))

    new_mapping = {
        "image_ids": image_ids,
        "paths": paths,
        "site_ids": site_ids
    }
    with open(tmp_mapping_path, "w", encoding="utf-8") as f:
        json.dump(new_mapping, f, indent=1)
        f.write("\n")

    # Validation Checks
    print("\nRunning validation checks on temporary artifacts...")

    # Load test & dimension check
    loaded_index = faiss.read_index(str(tmp_index_path))
    assert loaded_index.is_trained, "Index is not trained"
    # FAISS index dimension is stored as a property
    index_dim = loaded_index.d
    assert index_dim == 512, f"Expected dimension 512, got {index_dim}"

    with open(tmp_mapping_path, encoding="utf-8") as f:
        loaded_mapping = json.load(f)

    # 2. ntotal == len(mapping["image_ids"])
    assert loaded_index.ntotal == len(loaded_mapping["image_ids"]), f"Mismatch: ntotal={loaded_index.ntotal}, image_ids={len(loaded_mapping['image_ids'])}"

    # 3. Consistent lengths of mapping arrays
    n_ids = len(loaded_mapping["image_ids"])
    n_paths = len(loaded_mapping["paths"])
    n_sites = len(loaded_mapping["site_ids"])
    assert n_ids == n_paths == n_sites, f"Mapping array length mismatch: image_ids={n_ids}, paths={n_paths}, site_ids={n_sites}"

    # 4. Verify every mapped site ID exists in the catalogue
    for sid in loaded_mapping["site_ids"]:
        assert sid in valid_site_ids, f"Invalid site ID in mapping: {sid} not found in catalogue"

    print("All validation checks PASSED successfully!")

    # Rollback-safe replacement
    print("Replacing active index and mapping...")
    faiss.write_index(loaded_index, str(INDEX_PATH))
    with open(MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump(loaded_mapping, f, indent=1)
        f.write("\n")

    # Write failed log
    with open(FAILED_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(failed_log, f, indent=2)
    print(f"Failed log written to {FAILED_LOG_PATH} ({len(failed_log)} entries)")

    # Summary report
    unique_sites = len(set(site_ids))
    print("\n=== SUMMARY REPORT ===")
    print(f"Old vector count: 27 | New vector count: {loaded_index.ntotal}")
    print(f"Old unique site count: 17 | New unique site count: {unique_sites}")
    print(f"Images processed: {processed_count}")
    print(f"Images skipped: {skipped_count}")
    print(f"Images deduplicated: {dedup_count}")
    print(f"Mapping validation: SUCCESS (all {n_ids} entries validated against catalogue)")


if __name__ == "__main__":
    build_safe_index()
