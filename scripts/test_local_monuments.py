import urllib.request
import json
import base64
from pathlib import Path

monuments = [
    ("taj_mahal", "data/raw/taj_mahal/taj_mahal_01.jpg"),
    ("ajanta_caves", "data/raw/ajanta_caves/ajanta_caves_01.jpg"),
    ("qutub_minar", "data/raw/qutub_minar/qutub_minar_01.jpg"),
    ("red_fort_delhi", "data/raw/red_fort/red_fort_01.jpg"),
    ("konark_sun_temple", "data/raw/konark_sun_temple/konark_sun_temple_01.jpg"),
    ("jama_masjid_delhi", "data/raw/jama_masjid/jama_masjid_01.jpg"),
]

print("=== LOCAL RECOGNITION REGRESSION TEST (ALL 6 CATALOGUE MONUMENTS) ===")
all_ok = True
for expected_id, img_path in monuments:
    raw = Path(img_path).read_bytes()
    b64 = "data:image/jpeg;base64," + base64.b64encode(raw).decode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/recognize",
        data=json.dumps({"image_base64": b64, "question": "", "top_k": 5}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:8080"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        match_ok = (data["site_id"] == expected_id and data["confirmed"] is True and data["recognition_source"] == "local")
        if not match_ok:
            all_ok = False
        print(f"[{'PASS' if match_ok else 'FAIL'}] {expected_id}: site_id={data['site_id']}, similarity={data['similarity']:.4f}, confirmed={data['confirmed']}, source={data['recognition_source']}")

print(f"\nAll 6 Local Monuments Passed: {all_ok}")
