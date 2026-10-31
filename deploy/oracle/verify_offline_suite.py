"""
Self-contained ARM64 verification test suite for Oracle Cloud VM.
Tests local PyTorch CLIP embedding extraction, FAISS vector search,
6 core monuments, and out-of-catalog image rejection.
"""

import glob
import os
import sys
import time
from pathlib import Path
from PIL import Image

# Ensure project root is in path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.heritage_service import build_service

print("=" * 60)
print("HERITAGE RECOGNITION PLATFORM — ARM64 VERIFICATION SUITE")
print("=" * 60)

t0 = time.time()
print("\n[1/3] Loading PyTorch CLIP model and FAISS vector index...")
service = build_service()
print(f"      Service initialized in {time.time() - t0:.2f}s")

SITE_MAP = {
    "ajanta_caves": "data/raw/ajanta_caves/*.jpg",
    "jama_masjid_delhi": "data/raw/jama_masjid/*.jpg",
    "konark_sun_temple": "data/raw/konark_sun_temple/*.jpg",
    "qutub_minar": "data/raw/qutub_minar/*.jpg",
    "red_fort_delhi": "data/raw/red_fort/*.jpg",
    "taj_mahal": "data/raw/taj_mahal/*.jpg",
}

print("\n[2/3] Testing Core Catalogue Monuments (Threshold: >= 0.85):")
results = []
for expected_site, pattern in SITE_MAP.items():
    files = glob.glob(str(ROOT / pattern))
    if not files:
        print(f"      [!] No image file found for {expected_site}")
        continue
    img_path = files[0]
    t_start = time.time()
    res = service.recognize(img_path, top_k=5)
    dur = time.time() - t_start
    passed = (res.site_id == expected_site and res.confirmed and res.similarity >= 0.85)
    status = "[PASS]" if passed else "[FAIL]"
    results.append((expected_site, res.site_id, res.similarity, res.margin, passed, dur))
    print(f"      {status} {expected_site:<20} -> Match: {res.site_id:<20} Sim: {res.similarity:.4f} Margin: {res.margin:.4f} ({dur:.2f}s)")

print("\n[3/3] Testing Unknown / Out-of-Catalog Image Rejection:")
im_noise = Image.new("RGB", (300, 300), color=(128, 128, 128))
noise_path = ROOT / "data" / "processed" / "noise_test_tmp.jpg"
im_noise.save(noise_path)
try:
    t_start = time.time()
    res_unk = service.recognize(str(noise_path), top_k=5)
    dur = time.time() - t_start
    passed_unk = (res_unk.decision in ("unknown", "rejected") and not res_unk.confirmed and res_unk.site_id == "unknown")
    status_unk = "[PASS]" if passed_unk else "[FAIL]"
    print(f"      {status_unk} Grey Noise Image     -> Decision: {res_unk.decision:<10} Site: {res_unk.site_id} Sim: {res_unk.similarity:.4f} ({dur:.2f}s)")
finally:
    if noise_path.exists():
        os.remove(noise_path)

all_passed = all(r[4] for r in results) and passed_unk
print("\n" + "=" * 60)
if all_passed:
    print("ALL RECOGNITION AND REJECTION CHECKS PASSED SUCCESSFULLY (100%)")
else:
    print("SOME CHECKS FAILED — REVIEW LOGS ABOVE")
print("=" * 60)

sys.exit(0 if all_passed else 1)
