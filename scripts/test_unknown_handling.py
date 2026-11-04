import urllib.request
import json
import base64
import io
from PIL import Image

print("=== UNKNOWN & NON-HERITAGE REJECTION TEST ===")

# 1. Blank solid color image (non-heritage)
img = Image.new("RGB", (300, 300), color=(128, 128, 128))
buf = io.BytesIO()
img.save(buf, format="JPEG")
b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8000/recognize",
    data=json.dumps({"image_base64": b64, "question": "", "top_k": 5}).encode("utf-8"),
    headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:8080"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print(f"Solid Gray: confirmed={data['confirmed']}, confident={data['confident']}, site_id={data['site_id']}, decision={data['decision']}")
    assert data["confirmed"] is False, "Non-heritage solid color must never be confirmed"
    assert data["site_id"] == "unknown", "Non-heritage site_id must be unknown"

# 2. Random noise image
import numpy as np
noise = np.random.randint(0, 256, (300, 300, 3), dtype=np.uint8)
img_noise = Image.fromarray(noise)
buf = io.BytesIO()
img_noise.save(buf, format="JPEG")
b64_noise = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8000/recognize",
    data=json.dumps({"image_base64": b64_noise, "question": "", "top_k": 5}).encode("utf-8"),
    headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:8080"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print(f"Noise Image: confirmed={data['confirmed']}, confident={data['confident']}, site_id={data['site_id']}, decision={data['decision']}")
    assert data["confirmed"] is False, "Noise image must never be confirmed"
    assert data["site_id"] == "unknown", "Noise image site_id must be unknown"

print("\nUnknown & Non-Heritage Rejection Test: ALL PASSED!")

