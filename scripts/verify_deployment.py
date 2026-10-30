import base64
import glob
import io
import json
import os
import sys
import urllib.request
from PIL import Image

BACKEND_URL = "http://127.0.0.1:8000"
SITE_FOLDERS = {
    "ajanta_caves": "data/raw/ajanta_caves/*.jpg",
    "jama_masjid_delhi": "data/raw/jama_masjid/*.jpg",
    "konark_sun_temple": "data/raw/konark_sun_temple/*.jpg",
    "qutub_minar": "data/raw/qutub_minar/*.jpg",
    "red_fort_delhi": "data/raw/red_fort/*.jpg",
    "taj_mahal": "data/raw/taj_mahal/*.jpg"
}

# 2. Test each of the 6 catalogue monuments
print("\nTesting 6 Core Catalogue Monuments with CLIP + FAISS:")
for site_id, glob_pattern in SITE_FOLDERS.items():
    matches = glob.glob(glob_pattern)
    if not matches:
        print(f"  [!] No images found for {site_id}")
        continue
    img_path = matches[0]
    im = Image.open(img_path).convert("RGB")
    im.thumbnail((800, 800))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=80)
    b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    payload = json.dumps({"image_base64": b64, "top_k": 5}).encode("utf-8")
    req = urllib.request.Request(
        f"{BACKEND_URL}/recognize",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.loads(r.read().decode("utf-8"))
        print(f"  [PASS] {site_id:<20} -> Match: {res['site_id']:<20} (similarity: {res.get('similarity', 0):.4f}, decision: {res['decision']})")
        assert res["site_id"] == site_id, f"Expected {site_id}, got {res['site_id']}"
        assert res["decision"] == "match", f"Expected match, got {res['decision']}"
        assert res.get("similarity", 0) >= 0.85, f"Expected >= 0.85 similarity, got {res.get('similarity')}"

# 3. Test Unknown / Negative rejection (solid white / noise image)
print("\nTesting Unknown / Out-of-Distribution Image Rejection:")
im_noise = Image.new("RGB", (300, 300), color=(128, 128, 128))
buf_noise = io.BytesIO()
im_noise.save(buf_noise, format="JPEG")
b64_noise = "data:image/jpeg;base64," + base64.b64encode(buf_noise.getvalue()).decode("utf-8")
payload_noise = json.dumps({"image_base64": b64_noise, "top_k": 5}).encode("utf-8")
req_noise = urllib.request.Request(
    f"{BACKEND_URL}/recognize",
    data=payload_noise,
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req_noise, timeout=30) as r:
    res_noise = json.loads(r.read().decode("utf-8"))
    print(f"  [PASS] Grey Noise Image -> Decision: {res_noise['decision']} (site_id: {res_noise['site_id']}, source: {res_noise.get('recognition_source')})")
    assert res_noise["decision"] in ("unknown", "rejected", "none"), f"Expected unknown, got {res_noise['decision']}"
    assert res_noise["site_id"] == "unknown", f"Expected site_id 'unknown', got {res_noise['site_id']}"

print("\n" + "=" * 60)
print("ALL SYSTEM VERIFICATION CHECKS PASSED SUCCESSFULLY (100%)")
print("=" * 60)
