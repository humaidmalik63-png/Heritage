"""
Live Gemini API Validation Script.
STRICT REQUIREMENT: Exactly TWO live API calls authorized.
Call 1: Generic reddish rock / sandstone texture (False-positive distractor)
Call 2: Genuine Petra photograph with distinctive carved Nabataean facade

Verifies conservative, evidence-based recognition and qualitative evidence assessment.
"""

import asyncio
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.gemini import GeminiVisionClient, GeminiVisionResult

# Ensure stdout is line buffered
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)


def create_sandstone_image() -> bytes:
    """Generate generic reddish sandstone texture matching user's scenario."""
    sandstone = np.zeros((512, 512, 3), dtype=np.uint8)
    for y in range(512):
        # Layered striations in shades of red/pink sandstone
        band = np.sin(y * 0.05) * 25
        sandstone[y, :, 0] = np.clip(185 + band + np.random.randint(-12, 12, 512), 140, 240)
        sandstone[y, :, 1] = np.clip(95 + band * 0.6 + np.random.randint(-10, 10, 512), 60, 150)
        sandstone[y, :, 2] = np.clip(75 + band * 0.5 + np.random.randint(-10, 10, 512), 50, 130)
    img = Image.fromarray(sandstone)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def load_genuine_petra_image() -> bytes:
    """Load genuine Petra photograph with distinctive Al-Khazneh carved facade."""
    petra_path = PROJECT_ROOT / "frontend" / "assets" / "images" / "slideshow" / "petra.jpg"
    with open(petra_path, "rb") as f:
        return f.read()


async def main():
    print("=" * 70)
    print("LIVE GEMINI 3.1 FLASH-LITE VALIDATION SUITE (STRICT 2-CALL LIMIT)")
    print("=" * 70)

    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not configured!")
        sys.exit(1)

    client = GeminiVisionClient(api_key=api_key)
    live_calls_made = 0

    results = {}

    # -------------------------------------------------------------
    # CALL 1: Generic Sandstone Texture (False-Positive Scenario)
    # -------------------------------------------------------------
    print("\n[CALL 1/2] Sending Generic Red Sandstone Texture to Gemini Vision...")
    sandstone_bytes = create_sandstone_image()
    print(f"  Image size: {len(sandstone_bytes)} bytes (512x512 JPEG)")
    
    t0 = time.perf_counter()
    res1: GeminiVisionResult = await client.identify_monument(sandstone_bytes)
    t1 = time.perf_counter()
    live_calls_made += 1
    
    latency1 = t1 - t0
    print(f"  Latency: {latency1:.2f}s")
    print(f"  Visual Category: {res1.visual_category}")
    print(f"  Is Heritage: {res1.is_heritage}")
    print(f"  Site Name: {res1.site_name}")
    print(f"  Confidence: {res1.confidence}")
    print(f"  Evidence Tier: {res1.evidence_tier}")
    print(f"  Reason: {res1.reason}")
    print(f"  Visual Evidence: {res1.visual_evidence}")
    print(f"  Decision Identified: {res1.identified}")
    print(f"  Unknown Flag: {res1.unknown}")

    results["call_1_generic_sandstone"] = {
        "latency_sec": round(latency1, 2),
        "visual_category": res1.visual_category,
        "is_heritage": res1.is_heritage,
        "site_name": res1.site_name,
        "confidence": res1.confidence,
        "evidence_tier": res1.evidence_tier,
        "reason": res1.reason,
        "visual_evidence": res1.visual_evidence,
        "identified": res1.identified,
        "unknown": res1.unknown,
    }

    # Verify Call 1 assertions
    assert res1.visual_category in (
        "generic_natural_rock_or_sandstone",
        "closeup_texture_or_detail",
        "landscape_without_identifiable_monument",
        "possible_heritage_insufficient_evidence",
        "unknown"
    ), f"Unexpected category for sandstone: {res1.visual_category}"
    assert res1.unknown is True, f"Expected unknown=True, got {res1.unknown}"
    assert res1.identified is False, f"Expected identified=False, got {res1.identified}"
    assert res1.site_name is None, f"Expected site_name=None, got {res1.site_name}"
    assert res1.confidence == 0.0, f"Expected confidence=0.0, got {res1.confidence}"
    print("  --> [VERIFIED] Generic sandstone was correctly rejected as unknown (0.0% confidence, no false Petra identification)!")

    # -------------------------------------------------------------
    # CALL 2: Genuine Petra Photograph with Nabataean Facade
    # -------------------------------------------------------------
    print("\n[CALL 2/2] Sending Genuine Petra Photo with Nabataean Facade to Gemini Vision...")
    petra_bytes = load_genuine_petra_image()
    print(f"  Image size: {len(petra_bytes)} bytes")
    
    t0 = time.perf_counter()
    res2: GeminiVisionResult = await client.identify_monument(petra_bytes)
    t1 = time.perf_counter()
    live_calls_made += 1

    latency2 = t1 - t0
    print(f"  Latency: {latency2:.2f}s")
    print(f"  Visual Category: {res2.visual_category}")
    print(f"  Is Heritage: {res2.is_heritage}")
    print(f"  Site Name: {res2.site_name}")
    print(f"  Confidence: {res2.confidence}")
    print(f"  Evidence Tier: {res2.evidence_tier}")
    print(f"  Reason: {res2.reason}")
    print(f"  Visual Evidence: {res2.visual_evidence}")
    print(f"  Decision Identified: {res2.identified}")
    print(f"  Unknown Flag: {res2.unknown}")

    results["call_2_genuine_petra"] = {
        "latency_sec": round(latency2, 2),
        "visual_category": res2.visual_category,
        "is_heritage": res2.is_heritage,
        "site_name": res2.site_name,
        "confidence": res2.confidence,
        "evidence_tier": res2.evidence_tier,
        "reason": res2.reason,
        "visual_evidence": res2.visual_evidence,
        "identified": res2.identified,
        "unknown": res2.unknown,
    }

    # Verify Call 2 assertions
    assert res2.visual_category == "clearly_identifiable_heritage", f"Expected clearly_identifiable_heritage, got {res2.visual_category}"
    assert res2.is_heritage is True, f"Expected is_heritage=True, got {res2.is_heritage}"
    assert ("petra" in (res2.site_name or "").lower() or "khazneh" in (res2.site_name or "").lower() or "petra" in (res2.reason or "").lower()), f"Expected 'petra' or 'khazneh' in identification, got {res2.site_name}"
    assert res2.identified is True, f"Expected identified=True"
    assert res2.unknown is False, f"Expected unknown=False, got {res2.unknown}"
    assert res2.evidence_tier == "substantial", f"Expected substantial evidence, got {res2.evidence_tier}"
    print(f"  --> [VERIFIED] Genuine Petra monument successfully identified with {res2.evidence_tier} evidence tier!")

    print("\n" + "=" * 70)
    print(f"TOTAL LIVE CALLS CONSUMED: {live_calls_made} (STRICT LIMIT: 2)")
    print("=" * 70)

    # Save validation results to JSON for documentation
    out_path = PROJECT_ROOT / "scripts" / "live_gemini_validation_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved validation output to {out_path}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
