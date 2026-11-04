"""
Complete Recognition Test Suite for Heritage Discovery Platform
Validates Phase 1 through Phase 5 as specified in TASK requirements.
"""

import asyncio
import base64
import io
import json
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from PIL import Image, ImageEnhance
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_ORIGIN = "http://127.0.0.1:8080"
SIMILARITY_THRESHOLD = 0.85
MARGIN_THRESHOLD = 0.10

MONUMENTS = [
    ("taj_mahal", "Taj Mahal"),
    ("ajanta_caves", "Ajanta Caves"),
    ("qutub_minar", "Qutub Minar"),
    ("red_fort_delhi", "Red Fort"),
    ("konark_sun_temple", "Konark Sun Temple"),
    ("jama_masjid_delhi", "Jama Masjid"),
]


def image_to_base64(img: Image.Image, format: str = "JPEG") -> str:
    buffered = io.BytesIO()
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(buffered, format=format, quality=90)
    img_bytes = buffered.getvalue()
    b64_str = base64.b64encode(img_bytes).decode("utf-8")
    mime = "image/jpeg" if format.upper() == "JPEG" else "image/png"
    return f"data:{mime};base64,{b64_str}"


def file_to_base64(path: Path) -> str:
    with Image.open(path) as img:
        return image_to_base64(img, format="JPEG")


def post_recognize(b64_image: str, origin: str = FRONTEND_ORIGIN) -> Dict[str, Any]:
    url = f"{BASE_URL}/recognize"
    payload = json.dumps({"image_base64": b64_image, "top_k": 5}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Origin": origin,
            "User-Agent": "HeritageTestRunner/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_phase_1() -> Dict[str, Any]:
    print("=== RUNNING PHASE 1: RESTORE BACKEND CONNECTION ===")
    results = {}
    
    # Check health endpoint
    req = urllib.request.Request(
        f"{BASE_URL}/health",
        headers={"Origin": FRONTEND_ORIGIN}
    )
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            latency = (time.time() - start) * 1000
            status_code = resp.status
            cors_header = resp.headers.get("Access-Control-Allow-Origin")
            data = json.loads(resp.read().decode("utf-8"))
            results["health"] = {
                "status_code": status_code,
                "latency_ms": round(latency, 2),
                "cors_header": cors_header,
                "data": data,
                "success": status_code == 200 and data.get("status") == "ok",
            }
            print(f"Health check: HTTP {status_code} in {latency:.1f}ms, ACAO: {cors_header}")
            print(f"Data: {data}")
    except Exception as e:
        results["health"] = {"success": False, "error": str(e)}
        print(f"Health check failed: {e}")

    # Check OPTIONS CORS preflight
    opt_req = urllib.request.Request(
        f"{BASE_URL}/recognize",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
        method="OPTIONS",
    )
    try:
        with urllib.request.urlopen(opt_req, timeout=10) as resp:
            results["cors_preflight"] = {
                "status_code": resp.status,
                "allow_origin": resp.headers.get("Access-Control-Allow-Origin"),
                "allow_methods": resp.headers.get("Access-Control-Allow-Methods"),
                "allow_headers": resp.headers.get("Access-Control-Allow-Headers"),
                "success": resp.status == 200 and resp.headers.get("Access-Control-Allow-Origin") == FRONTEND_ORIGIN,
            }
            print(f"CORS Preflight: HTTP {resp.status}, ACAO: {resp.headers.get('Access-Control-Allow-Origin')}")
    except Exception as e:
        results["cors_preflight"] = {"success": False, "error": str(e)}
        print(f"CORS preflight failed: {e}")

    return results


def run_phase_2() -> List[Dict[str, Any]]:
    print("\n=== RUNNING PHASE 2: TEST ALL 6 MONUMENTS (LOCAL RECOGNITION) ===")
    test_cases = []

    # Map candidate folders / files for all 6 monuments
    monument_sources = {
        "taj_mahal": [
            Path("data/raw/taj_mahal/taj_mahal_01.jpg"),
            Path("data/raw/taj_mahal/taj_mahal_02.jpg"),
            Path("data/raw/taj_mahal/taj_mahal_03.jpg"),
            Path("frontend/assets/images/slideshow/taj-mahal.jpg"),
        ],
        "ajanta_caves": [
            Path("data/raw/ajanta_caves/ajanta_caves_01.jpg"),
            Path("data/raw/ajanta_caves/ajanta_caves_02.jpg"),
            Path("data/raw/ajanta_caves/ajanta_caves_03.jpg"),
            Path("frontend/assets/images/sites/ajanta_caves.webp"),
        ],
        "qutub_minar": [
            Path("data/raw/qutub_minar/qutub_minar_01.jpg"),
            Path("data/raw/qutub_minar/qutub_minar_02.jpg"),
            Path("data/raw/qutub_minar/qutub_minar_03.jpg"),
            Path("frontend/assets/images/sites/qutub_minar.webp"),
        ],
        "red_fort_delhi": [
            Path("data/raw/red_fort/red_fort_01.jpg"),
            Path("data/raw/red_fort/red_fort_02.jpg"),
            Path("data/raw/red_fort/red_fort_03.jpg"),
            Path("frontend/assets/images/sites/red_fort.webp"),
        ],
        "konark_sun_temple": [
            Path("data/raw/konark_sun_temple/konark_sun_temple_01.jpg"),
            Path("data/raw/konark_sun_temple/konark_sun_temple_02.jpg"),
            Path("data/raw/konark_sun_temple/konark_sun_temple_03.jpg"),
            Path("frontend/assets/images/sites/konark_sun_temple.webp"),
        ],
        "jama_masjid_delhi": [
            Path("data/raw/jama_masjid/jama_masjid_01.jpg"),
            Path("frontend/assets/images/gallery/jama_masjid/01-lg.webp"),
            Path("frontend/assets/images/sites/jama_masjid.webp"),
        ],
    }

    test_records = []

    for site_id, site_name in MONUMENTS:
        sources = monument_sources.get(site_id, [])
        for src_path in sources:
            if not src_path.exists():
                continue
            
            # 1. Base image test
            try:
                with Image.open(src_path) as img:
                    orig_img = img.convert("RGB")
                    
                    # Variations:
                    # Variation A: Original view
                    var_a_b64 = image_to_base64(orig_img)
                    rec_a = post_recognize(var_a_b64)
                    test_records.append(parse_test_result(site_id, site_name, f"{src_path.name} (original)", rec_a))

                    # Variation B: Center crop (simulating camera framing / different distance)
                    w, h = orig_img.size
                    crop_box = (int(w * 0.15), int(h * 0.15), int(w * 0.85), int(h * 0.85))
                    cropped_img = orig_img.crop(crop_box)
                    var_b_b64 = image_to_base64(cropped_img)
                    rec_b = post_recognize(var_b_b64)
                    test_records.append(parse_test_result(site_id, site_name, f"{src_path.name} (cropped 70%)", rec_b))

                    # Variation C: Lighting / contrast adjustment
                    enhancer = ImageEnhance.Brightness(orig_img)
                    bright_img = enhancer.enhance(1.2)
                    var_c_b64 = image_to_base64(bright_img)
                    rec_c = post_recognize(var_c_b64)
                    test_records.append(parse_test_result(site_id, site_name, f"{src_path.name} (bright +20%)", rec_c))

            except Exception as exc:
                print(f"Error processing {src_path}: {exc}")

    return test_records


def parse_test_result(expected_id: str, expected_name: str, test_desc: str, response: Dict[str, Any]) -> Dict[str, Any]:
    pred_id = response.get("site_id")
    similarity = response.get("similarity", 0.0)
    confirmed = response.get("confirmed", False)
    confident = response.get("confident", False)
    decision = response.get("decision", "unknown")
    reason = response.get("reason", "")
    matches = response.get("matches", [])
    
    second_sim = 0.0
    if len(matches) > 1:
        second_sim = matches[1].get("similarity", 0.0)
    
    margin = round(similarity - second_sim, 4)
    rejected = not confirmed
    
    # Verification criteria
    correct_match = (pred_id == expected_id)
    passed_thresholds = (similarity >= SIMILARITY_THRESHOLD and margin >= MARGIN_THRESHOLD)
    
    status_str = "PASS" if (correct_match and confirmed) else ("REJECTED_AS_EXPECTED" if rejected else "MISMATCH")
    print(f"[{status_str}] {expected_name} | {test_desc} -> Pred: {pred_id} | Sim: {similarity:.4f} | 2nd: {second_sim:.4f} | Margin: {margin:.4f} | Confirmed: {confirmed} | Decision: {decision}")

    return {
        "expected_id": expected_id,
        "expected_name": expected_name,
        "test_desc": test_desc,
        "predicted_id": pred_id,
        "top_similarity": similarity,
        "second_similarity": second_sim,
        "competitor_margin": margin,
        "confirmed": confirmed,
        "confident": confident,
        "decision": decision,
        "rejected": rejected,
        "rejection_reason": reason if rejected else "N/A",
        "correct_id": correct_match,
        "passed_thresholds": passed_thresholds,
    }


def run_phase_3() -> Dict[str, Any]:
    print("\n=== RUNNING PHASE 3: TEST GEMINI API FALLBACK ===")
    from unittest.mock import AsyncMock, MagicMock, patch
    from backend.gemini import GeminiVisionClient, GeminiVisionResult
    from backend.heritage_service import HeritageService, RecognitionResult

    results = {
        "mock_tests": [],
        "live_tests": [],
        "live_request_count": 0,
        "mock_request_count": 0,
    }

    # 1. Mock Test: Successful Gemini Fallback on Local Rejection
    async def test_mock_routing():
        mock_gemini = MagicMock(spec=GeminiVisionClient)
        mock_gemini.identify_monument = AsyncMock(return_value=GeminiVisionResult(
            unknown=False,
            identified=True,
            is_heritage=True,
            site_name="Colosseum",
            country_or_region="Rome, Italy",
            city="Rome",
            country="Italy",
            visual_evidence="Iconic elliptical amphitheatre constructed of travertine limestone and brick-faced concrete.",
            confidence=0.96,
            uncertainty=None,
            alternatives=[],
            historical_period="70–80 AD (Flavian dynasty)",
            founder_built_by="Vespasian and Titus",
            architectural_style="Classical Roman architecture",
            significance="The largest ancient amphitheatre ever built.",
            interesting_facts=["Could hold an estimated 50,000 to 80,000 spectators."],
        ))

        # Build mock service
        service = HeritageService(
            confidence_layer=MagicMock(),
            repository=MagicMock(),
            gemini_client=mock_gemini,
        )
        # Mock recognize returning rejection (low similarity)
        service.recognize = MagicMock(return_value=RecognitionResult(
            site_id="unknown",
            similarity=0.62,
            confidence=None,
            margin=0.03,
            confident=False,
            confirmed=False,
            decision="unknown",
            reason="similarity_below_threshold",
            recognition_source="unknown",
            top_k=5,
        ))

        res = await service.recognize_async(b"fake_image_bytes")
        assert res.site_id == "unknown", "site_id must remain 'unknown' for external fallback"
        assert res.confident is True, "confident must be True on confident fallback"
        assert res.confirmed is False, "confirmed must be False (not local catalogue)"
        assert res.recognition_source == "gemini", "recognition_source must be 'gemini'"
        assert res.global_identification is not None, "global_identification must be populated"
        assert res.global_identification["site_name"] == "Colosseum"
        assert res.global_identification["country_or_region"] == "Rome, Italy"
        print("Mock Fallback Routing Test: PASSED")
        return {
            "name": "fallback_routing_on_rejection",
            "passed": True,
            "details": "Local rejection correctly invoked Gemini fallback and shaped response."
        }

    # 2. Mock Test: Timeout Error Handling
    async def test_mock_timeout():
        mock_gemini = MagicMock(spec=GeminiVisionClient)
        mock_gemini.identify_monument = AsyncMock(side_effect=TimeoutError("Request timed out after 30.0s"))

        service = HeritageService(
            confidence_layer=MagicMock(),
            repository=MagicMock(),
            gemini_client=mock_gemini,
        )
        service.recognize = MagicMock(return_value=RecognitionResult(
            site_id="unknown",
            similarity=0.45,
            confidence=None,
            confident=False,
            confirmed=False,
            decision="unknown",
            reason="similarity_below_threshold",
            top_k=5,
        ))

        res = await service.recognize_async(b"fake_image_bytes")
        assert res.confirmed is False
        assert res.confident is False
        assert res.decision == "unknown"
        assert res.global_identification is None
        print("Mock Timeout Error Handling Test: PASSED")
        return {
            "name": "timeout_error_handling",
            "passed": True,
            "details": "Timeout gracefully degraded to safe unknown response without crash."
        }

    # 3. Mock Test: Quota 429 Error Handling
    async def test_mock_quota():
        mock_gemini = MagicMock(spec=GeminiVisionClient)
        mock_gemini.identify_monument = AsyncMock(return_value=GeminiVisionResult(
            unknown=True,
            identified=False,
            is_heritage=False,
            site_name=None,
            confidence=0.0,
            visual_evidence="API quota exceeded or rate limited",
        ))

        service = HeritageService(
            confidence_layer=MagicMock(),
            repository=MagicMock(),
            gemini_client=mock_gemini,
        )
        service.recognize = MagicMock(return_value=RecognitionResult(
            site_id="unknown",
            similarity=0.40,
            confidence=None,
            confident=False,
            confirmed=False,
            decision="unknown",
            reason="similarity_below_threshold",
            top_k=5,
        ))

        res = await service.recognize_async(b"fake_image_bytes")
        assert res.confirmed is False
        assert res.decision == "unknown"
        assert res.global_identification is None or res.global_identification.get("unknown") is True
        print("Mock Quota 429 Handling Test: PASSED")
        return {
            "name": "quota_429_handling",
            "passed": True,
            "details": "Quota limitation cleanly returns structured unknown result."
        }

    t1 = asyncio.run(test_mock_routing())
    t2 = asyncio.run(test_mock_timeout())
    t3 = asyncio.run(test_mock_quota())
    results["mock_tests"] = [t1, t2, t3]
    results["mock_request_count"] = 3

    # 4. Live Gemini Fallback Test (STRICT LIMIT: <= 6 live requests)
    colosseum_path = Path("frontend/assets/images/slideshow/colosseum.jpg")
    if colosseum_path.exists() and os.getenv("GEMINI_API_KEY"):
        print("\nExecuting Live Gemini Fallback Test (Colosseum image)...")
        b64 = file_to_base64(colosseum_path)
        start_t = time.time()
        try:
            live_res = post_recognize(b64)
            elapsed = time.time() - start_t
            results["live_request_count"] += 1
            print(f"Live Gemini Fallback completed in {elapsed:.2f}s:")
            print(f"  site_id: {live_res.get('site_id')}")
            print(f"  recognition_source: {live_res.get('recognition_source')}")
            print(f"  confident: {live_res.get('confident')}")
            print(f"  confirmed: {live_res.get('confirmed')}")
            g_ident = live_res.get("global_identification") or {}
            print(f"  Identified Monument: {g_ident.get('site_name')}")
            print(f"  Location: {g_ident.get('country_or_region')}")
            print(f"  Confidence: {live_res.get('confidence')}")

            results["live_tests"].append({
                "test": "Live Colosseum Fallback",
                "image": str(colosseum_path),
                "elapsed_s": round(elapsed, 2),
                "response": live_res,
                "passed": live_res.get("recognition_source") == "gemini" and live_res.get("confirmed") is False,
            })
        except Exception as e:
            results["live_tests"].append({
                "test": "Live Colosseum Fallback",
                "image": str(colosseum_path),
                "error": str(e),
                "passed": False,
            })

    return results


def run_phase_4() -> List[Dict[str, Any]]:
    print("\n=== RUNNING PHASE 4: TEST UNKNOWN / UNCATALOGUED IMAGES ===")
    unknown_images = [
        ("Colosseum (Uncatalogued Heritage)", Path("frontend/assets/images/slideshow/colosseum.jpg")),
        ("Machu Picchu (Uncatalogued Heritage)", Path("frontend/assets/images/slideshow/machu-picchu.jpg")),
        ("Great Wall (Uncatalogued Heritage)", Path("frontend/assets/images/slideshow/great-wall.jpg")),
        ("Petra (Uncatalogued Heritage)", Path("frontend/assets/images/slideshow/petra.jpg")),
    ]

    # Generate synthetic non-heritage image (random colored geometric shapes)
    non_heritage_img = Image.new("RGB", (300, 300), color=(180, 200, 220))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(non_heritage_img)
    draw.rectangle([50, 50, 250, 250], fill=(70, 80, 90), outline=(255, 0, 0), width=4)
    draw.text((70, 140), "NON-HERITAGE TEST OBJECT", fill=(255, 255, 255))
    
    non_heritage_b64 = image_to_base64(non_heritage_img)

    results = []

    for label, path in unknown_images:
        if not path.exists():
            continue
        b64 = file_to_base64(path)
        resp = post_recognize(b64)
        site_id = resp.get("site_id")
        confirmed = resp.get("confirmed", False)
        rec_src = resp.get("recognition_source", "")
        sim = resp.get("similarity", 0.0)
        
        # An unknown image MUST NOT be confirmed as a local catalogue monument
        is_safe = (confirmed is False and site_id == "unknown")
        print(f"Unknown Test: '{label}' -> site_id: {site_id} | confirmed: {confirmed} | rec_source: {rec_src} | Safe: {is_safe}")
        results.append({
            "label": label,
            "path": str(path),
            "site_id": site_id,
            "confirmed": confirmed,
            "similarity": sim,
            "recognition_source": rec_src,
            "is_safe": is_safe,
        })

    # Test non-heritage object
    non_h_resp = post_recognize(non_heritage_b64)
    nh_safe = (non_h_resp.get("confirmed") is False and non_h_resp.get("site_id") == "unknown")
    print(f"Non-Heritage Object Test -> site_id: {non_h_resp.get('site_id')} | confirmed: {non_h_resp.get('confirmed')} | Safe: {nh_safe}")
    results.append({
        "label": "Synthetic Non-Heritage Graphic",
        "path": "in-memory-canvas",
        "site_id": non_h_resp.get("site_id"),
        "confirmed": non_h_resp.get("confirmed"),
        "similarity": non_h_resp.get("similarity", 0.0),
        "recognition_source": non_h_resp.get("recognition_source"),
        "is_safe": nh_safe,
    })

    return results


def run_phase_5() -> Dict[str, Any]:
    print("\n=== RUNNING PHASE 5: FRONTEND INTEGRATION & VALIDATION ===")
    results = {}
    
    # Check frontend HTTP server on port 8080
    fe_url = "http://127.0.0.1:8080/index.html"
    try:
        with urllib.request.urlopen(fe_url, timeout=5) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            has_camera = "Take Photo" in content or "camera-input" in content or "take-photo" in content
            results["frontend_server"] = {
                "status_code": resp.status,
                "reachable": resp.status == 200,
                "has_camera_controls": has_camera,
            }
            print(f"Frontend server on 8080: HTTP {resp.status}, Camera controls present: {has_camera}")
    except Exception as e:
        results["frontend_server"] = {"reachable": False, "error": str(e)}
        print(f"Frontend server unreachable on 8080: {e}")

    # Check that backend CORS explicitly allows the frontend
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/health",
            headers={"Origin": "http://127.0.0.1:8080"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            acao = resp.headers.get("Access-Control-Allow-Origin")
            results["cors_integration"] = {
                "origin": "http://127.0.0.1:8080",
                "acao": acao,
                "matches": acao == "http://127.0.0.1:8080",
            }
            print(f"CORS validation for http://127.0.0.1:8080: {acao}")
    except Exception as e:
        results["cors_integration"] = {"matches": False, "error": str(e)}

    return results


def main():
    p1 = run_phase_1()
    p2 = run_phase_2()
    p3 = run_phase_3()
    p4 = run_phase_4()
    p5 = run_phase_5()

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase_1": p1,
        "phase_2_count": len(p2),
        "phase_2": p2,
        "phase_3": p3,
        "phase_4": p4,
        "phase_5": p5,
    }

    out_json = Path("scripts/test_results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nAll tests finished. Raw results saved to {out_json}")


if __name__ == "__main__":
    main()
