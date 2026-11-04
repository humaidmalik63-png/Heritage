"""
Automated Test Suite for Gemini HTTP 503 Handling & Frontend Error Classification.

Tests all 9 requirements without making any live Gemini API calls:
1. Gemini HTTP 503 followed by success.
2. Two consecutive HTTP 503 responses (bounded retry, max 1 retry).
3. HTTP 429 quota error (no retry, separate recognition).
4. HTTP 400 invalid request (no retry).
5. Network failure (httpx.ConnectError).
6. Backend timeout (httpx.TimeoutException).
7. Manual retry (errors not cached).
8. User cancellation during retry backoff.
9. Correct frontend error classification via Chrome CDP.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import websockets

from backend.gemini import (
    GeminiVisionClient,
    GeminiVisionResult,
    fallback_unknown_result,
)
from backend.heritage_service import (
    HeritageService,
    RecognitionResult,
    REASON_LOW_SIMILARITY,
    REASON_NON_HERITAGE,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_503_suite")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9226
FRONTEND_URL = "http://127.0.0.1:8080/frontend/index.html#recognition"

SAMPLE_IMAGE_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00"

MOCK_ANGKOR_WAT_PAYLOAD = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": json.dumps({
                            "visual_category": "clearly_identifiable_heritage",
                            "unknown": False,
                            "site_name": "Angkor Wat",
                            "country_or_region": "Siem Reap, Cambodia",
                            "city": "Siem Reap",
                            "country": "Cambodia",
                            "visual_evidence": "Five lotus-bud towers with extensive sandstone galleries.",
                            "confidence": 0.86,
                            "evidence_tier": "substantial",
                            "uncertainty": None,
                            "alternatives": [],
                            "limitations": None,
                            "is_heritage": True,
                            "historical_period": "12th century (Khmer Empire)",
                            "founder_built_by": "Suryavarman II",
                            "architectural_style": "Khmer architecture",
                            "significance": "Largest religious monument in the world.",
                            "interesting_facts": ["Originally dedicated to Vishnu, later transformed into a Buddhist temple."],
                        })
                    }
                ],
                "role": "model",
            },
            "finishReason": "STOP",
        }
    ]
}


async def test_1_http_503_followed_by_success() -> Dict[str, Any]:
    """Test 1: Gemini HTTP 503 followed by success (verifies 1 automatic retry succeeds)."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, text='{"error": {"code": 503, "message": "Service Unavailable"}}')
        return httpx.Response(200, json=MOCK_ANGKOR_WAT_PAYLOAD)

    transport = httpx.MockTransport(handler)
    client = GeminiVisionClient(api_key="mock-key", transport=transport)
    res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

    passed = (attempts == 2 and res.identified is True and res.site_name == "Angkor Wat" and not res.unknown)
    return {
        "test": "1. Gemini HTTP 503 followed by success",
        "attempts": attempts,
        "site_name": res.site_name,
        "status": "PASS" if passed else "FAIL",
        "detail": f"Completed in {attempts} attempt(s); identified as '{res.site_name}'",
    }


async def test_2_two_consecutive_503_responses() -> Dict[str, Any]:
    """Test 2: Two consecutive HTTP 503 responses (verifies bounded retry: max 1 retry)."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, text='{"error": {"code": 503, "message": "The service is currently unavailable."}}')

    transport = httpx.MockTransport(handler)
    client = GeminiVisionClient(api_key="mock-key", transport=transport)
    res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

    # Also test HeritageService wrapper
    service = MagicMock(spec=HeritageService)
    service.recognize.return_value = RecognitionResult(
        site_id="unknown",
        similarity=0.7360,
        margin=0.0037,
        confident=False,
        confirmed=False,
        decision="unknown",
        recognition_source="unknown",
        top_k=5,
    )
    svc_client = MagicMock(spec=GeminiVisionClient)
    svc_client.identify_monument = AsyncMock(return_value=res)
    service.gemini_client = svc_client
    service.recognize_async = HeritageService.recognize_async.__get__(service, HeritageService)

    svc_res = await service.recognize_async(SAMPLE_IMAGE_BYTES)

    passed = (
        attempts == 2  # exactly 1 initial + 1 retry
        and res.unknown is True
        and res.status == "external_service_unavailable"
        and res.error_type == "service_unavailable"
        and res.evidence_tier == "unavailable"
        and svc_res.recognition_status == "external_service_unavailable"
        and svc_res.site_id == "unknown"
        and svc_res.confirmed is False
    )
    return {
        "test": "2. Two consecutive HTTP 503 responses",
        "attempts": attempts,
        "recognition_status": svc_res.recognition_status,
        "evidence_tier": res.evidence_tier,
        "status": "PASS" if passed else "FAIL",
        "detail": f"Bounded to exactly {attempts} attempt(s); returned recognition_status='{svc_res.recognition_status}' with tier='{res.evidence_tier}'",
    }


async def test_3_http_429_quota_error() -> Dict[str, Any]:
    """Test 3: HTTP 429 quota error (verifies NO automatic retry)."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, text='{"error": {"code": 429, "message": "Resource has been exhausted"}}')

    transport = httpx.MockTransport(handler)
    client = GeminiVisionClient(api_key="mock-key", transport=transport)
    res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

    passed = (
        attempts == 1
        and res.unknown is True
        and res.status == "external_rate_limited"
        and res.error_type == "rate_limited"
    )
    return {
        "test": "3. HTTP 429 quota error",
        "attempts": attempts,
        "status_code": 429,
        "error_type": res.error_type,
        "status": "PASS" if passed else "FAIL",
        "detail": f"Dispatched {attempts} call; returned error_type='{res.error_type}' without retrying",
    }


async def test_4_http_400_invalid_request() -> Dict[str, Any]:
    """Test 4: HTTP 400 invalid request (verifies NO automatic retry)."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(400, text='{"error": {"code": 400, "message": "Invalid argument"}}')

    transport = httpx.MockTransport(handler)
    client = GeminiVisionClient(api_key="mock-key", transport=transport)
    res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

    passed = (
        attempts == 1
        and res.unknown is True
        and res.status == "external_invalid_request"
        and res.error_type == "invalid_request"
    )
    return {
        "test": "4. HTTP 400 invalid request",
        "attempts": attempts,
        "error_type": res.error_type,
        "status": "PASS" if passed else "FAIL",
        "detail": f"Dispatched {attempts} call; returned error_type='{res.error_type}' without retrying",
    }


async def test_5_network_failure() -> Dict[str, Any]:
    """Test 5: Network failure (verifies structured network_error result)."""
    transport = httpx.MockTransport(lambda req: (_ for _ in ()).throw(httpx.ConnectError("Connection refused")))
    client = GeminiVisionClient(api_key="mock-key", transport=transport)
    res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

    passed = (
        res.unknown is True
        and res.status == "external_network_error"
        and res.error_type == "network_error"
        and "connect" in res.reason.lower()
    )
    return {
        "test": "5. Network failure (ConnectError)",
        "error_type": res.error_type,
        "status": "PASS" if passed else "FAIL",
        "detail": f"Caught ConnectError gracefully; returned status='{res.status}'",
    }


async def test_6_backend_timeout() -> Dict[str, Any]:
    """Test 6: Backend timeout (verifies structured timeout result)."""
    transport = httpx.MockTransport(lambda req: (_ for _ in ()).throw(httpx.TimeoutException("Read timed out")))
    client = GeminiVisionClient(api_key="mock-key", transport=transport)
    res = await client.identify_monument(SAMPLE_IMAGE_BYTES)

    passed = (
        res.unknown is True
        and res.status == "external_timeout"
        and res.error_type == "timeout"
        and "timed out" in res.reason.lower()
    )
    return {
        "test": "6. Backend timeout (TimeoutException)",
        "error_type": res.error_type,
        "status": "PASS" if passed else "FAIL",
        "detail": f"Caught TimeoutException; returned status='{res.status}'",
    }


async def test_7_manual_retry_not_cached() -> Dict[str, Any]:
    """Test 7: Manual retry (verifies 503 errors are NOT cached, allowing subsequent retry)."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return httpx.Response(503, text="Service Unavailable")
        return httpx.Response(200, json=MOCK_ANGKOR_WAT_PAYLOAD)

    transport = httpx.MockTransport(handler)
    client = GeminiVisionClient(api_key="mock-key", transport=transport)

    # First request: 503 + retry 503 -> fails
    res1 = await client.identify_monument(SAMPLE_IMAGE_BYTES)
    cache_len_after_fail = len(client._cache)

    # Second user request (manual retry)
    res2 = await client.identify_monument(SAMPLE_IMAGE_BYTES)

    passed = (
        res1.unknown is True
        and cache_len_after_fail == 0  # 503 was NOT cached
        and res2.identified is True
        and res2.site_name == "Angkor Wat"
        and call_count == 3  # exactly 2 calls for first request + 1 call for manual retry
    )
    return {
        "test": "7. Manual retry (no error caching)",
        "cache_len_after_fail": cache_len_after_fail,
        "total_calls": call_count,
        "second_call_result": res2.site_name,
        "status": "PASS" if passed else "FAIL",
        "detail": f"503 not cached (cache size={cache_len_after_fail}); manual retry triggered fresh call (total {call_count}) and succeeded",
    }


async def test_8_user_cancellation_during_retry() -> Dict[str, Any]:
    """Test 8: User cancellation during retry backoff."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    transport = httpx.MockTransport(handler)
    client = GeminiVisionClient(api_key="mock-key", transport=transport)

    task = asyncio.create_task(client.identify_monument(SAMPLE_IMAGE_BYTES))
    await asyncio.sleep(0.05)  # Let attempt 1 finish and enter sleep
    task.cancel()

    cancelled_properly = False
    try:
        await task
    except asyncio.CancelledError:
        cancelled_properly = True

    in_flight_purged = len(client._in_flight) == 0
    passed = cancelled_properly and in_flight_purged
    return {
        "test": "8. User cancellation during retry backoff",
        "cancelled_properly": cancelled_properly,
        "in_flight_purged": in_flight_purged,
        "status": "PASS" if passed else "FAIL",
        "detail": f"Cancelled cleanly ({cancelled_properly}) and in-flight tasks purged ({in_flight_purged})",
    }


async def test_9_frontend_cdp_verification(ws_url: str) -> List[Dict[str, Any]]:
    """Test 9: Frontend Error Classification via Chrome CDP."""
    records = []

    async with websockets.connect(ws_url) as ws:
        cmd_id = 0

        async def send(method: str, params: Dict[str, Any] = None):
            nonlocal cmd_id
            cmd_id += 1
            msg = {"id": cmd_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(msg))
            while True:
                raw = await ws.recv()
                res = json.loads(raw)
                if res.get("id") == cmd_id:
                    return res.get("result", {})

        async def eval_js(code: str):
            r = await send("Runtime.evaluate", {"expression": code, "returnByValue": True, "awaitPromise": True})
            return r.get("result", {}).get("value")

        await send("Page.enable")
        await send("Runtime.enable")
        await send("Page.navigate", {"url": FRONTEND_URL})
        await asyncio.sleep(1.5)

        # 9A: Simulate 503 response from backend
        payload_503 = {
            "site_id": "unknown",
            "similarity": 0.7360,
            "confidence": None,
            "margin": 0.0037,
            "confident": False,
            "confirmed": False,
            "decision": "unknown",
            "recognition_source": "unknown",
            "recognition_status": "external_service_unavailable",
            "global_identification": {
                "unknown": True,
                "identified": False,
                "status": "external_service_unavailable",
                "error_type": "service_unavailable",
                "evidence_tier": "unavailable",
                "confidence": 0.0,
                "reason": "Gemini server error (HTTP 503)",
                "visual_evidence": "The external recognition service is temporarily unavailable (HTTP 503).",
            },
            "top_k": 5,
            "matches": [],
            "metadata": {},
            "evidence": {},
            "answer": None,
            "citations": [],
            "reason": "Gemini server error (HTTP 503)",
            "is_grounded": False,
            "is_valid": True,
        }

        # 9A: Create real image blob and upload to activate UI
        ready = await eval_js("""
        (async function() {
            const canvas = document.createElement('canvas');
            canvas.width = 120; canvas.height = 120;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#b22222'; ctx.fillRect(0, 0, 120, 120);
            const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg'));
            const file = new File([blob], 'hawa_mahal.jpg', { type: 'image/jpeg' });
            const dt = new DataTransfer(); dt.items.add(file);
            const fi = document.getElementById('file-input');
            fi.files = dt.files;
            fi.dispatchEvent(new Event('change', { bubbles: true }));

            for (let i = 0; i < 30; i++) {
                const rec = document.getElementById('recognize-btn');
                if (rec && !rec.disabled) return true;
                await new Promise(r => setTimeout(r, 100));
            }
            return false;
        })()
        """)

        # 9A: Override fetch to return 503 response and click Recognize
        await eval_js(f"""
        (async function() {{
            const data503 = {json.dumps(payload_503)};
            const origFetch = window.fetch;
            window.fetch = function(url, options) {{
                if (typeof url === 'string' && url.includes('/recognize')) {{
                    return Promise.resolve(new Response(JSON.stringify(data503), {{
                        status: 200,
                        headers: {{ 'Content-Type': 'application/json' }}
                    }}));
                }}
                return origFetch.apply(this, arguments);
            }};
            
            const recBtn = document.getElementById('recognize-btn');
            if (recBtn) recBtn.click();

            for (let i = 0; i < 40; i++) {{
                const r = document.getElementById('result-region');
                if (r && r.children.length > 0) break;
                await new Promise(res => setTimeout(res, 100));
            }}
        }})()
        """)
        await asyncio.sleep(0.4)

        # Inspect UI elements
        ui_res = await eval_js("""
        (function() {
            const region = document.getElementById('result-region');
            const card = region ? region.querySelector('.result') : null;
            const nameEl = card ? card.querySelector('.result__name') : null;
            const descEl = card ? card.querySelector('.result__text') : null;
            const badgeEl = card ? card.querySelector('.result__badge') : null;
            const retryBtn = document.getElementById('retry-rec-btn');
            const recStatus = document.getElementById('recognition-status');
            const previewImg = document.getElementById('preview-img');
            const bodyText = card ? card.innerText : '';
            
            return {
                cardClass: card ? card.className : '',
                nameText: nameEl ? nameEl.innerText.trim() : '',
                descText: descEl ? descEl.innerText.trim() : '',
                badgeText: badgeEl ? badgeEl.innerText.trim() : '',
                hasRetryBtn: !!retryBtn,
                retryBtnText: retryBtn ? retryBtn.innerText.trim() : '',
                statusText: recStatus ? recStatus.innerText.trim() : '',
                hasPreview: !!previewImg && !previewImg.hidden,
                hasFakePercent: bodyText.includes('95%') || bodyText.includes('0%'),
                hasMisleadingTier: bodyText.toLowerCase().includes('insufficient evidence') || bodyText.toLowerCase().includes('generic rock')
            };
        })()
        """)

        # 9A: Heading verification
        h_ok = "EXTERNAL IDENTIFICATION TEMPORARILY UNAVAILABLE" in ui_res["nameText"]
        records.append({
            "test": "9A. Heading displays 'EXTERNAL IDENTIFICATION TEMPORARILY UNAVAILABLE'",
            "observed": ui_res["nameText"],
            "status": "PASS" if h_ok else "FAIL",
            "detail": f"Headline rendered: '{ui_res['nameText']}'",
        })

        # 9B: Message verification
        m_ok = "The external recognition service is temporarily unavailable. Your photograph has been preserved. Please try again shortly." in ui_res["descText"]
        records.append({
            "test": "9B. Message displays photograph preserved & try again shortly",
            "observed": ui_res["descText"],
            "status": "PASS" if m_ok else "FAIL",
            "detail": f"Message rendered: '{ui_res['descText']}'",
        })

        # 9C: Retry button exists and photograph is preserved
        btn_ok = ui_res["hasRetryBtn"] and "retry" in ui_res["retryBtnText"].lower() and ui_res["hasPreview"]
        records.append({
            "test": "9C. Retry button provided & query photograph preserved",
            "hasRetryBtn": ui_res["hasRetryBtn"],
            "retryBtnText": ui_res["retryBtnText"],
            "hasPreview": ui_res["hasPreview"],
            "status": "PASS" if btn_ok else "FAIL",
            "detail": f"Retry button present ('{ui_res['retryBtnText']}'), preview image preserved",
        })

        # 9D: No misleading evidence tier and no fake confidence percentage
        no_fake = not ui_res["hasFakePercent"] and not ui_res["hasMisleadingTier"]
        records.append({
            "test": "9D. No misleading evidence tier and no fake confidence percentage",
            "hasFakePercent": ui_res["hasFakePercent"],
            "hasMisleadingTier": ui_res["hasMisleadingTier"],
            "status": "PASS" if no_fake else "FAIL",
            "detail": "Verified zero fake percentage (0%/95%) and zero misleading 'insufficient evidence' or 'generic rock' claims",
        })

        # 9E: Compare against genuine insufficient evidence (sandstone rejection)
        payload_sandstone = {
            "site_id": "unknown",
            "similarity": 0.8052,
            "confidence": None,
            "margin": None,
            "confident": False,
            "confirmed": False,
            "decision": "unknown",
            "recognition_source": "unknown",
            "recognition_status": "inconclusive",
            "global_identification": {
                "unknown": True,
                "identified": False,
                "visual_category": "generic_natural_rock_or_sandstone",
                "evidence_tier": "insufficient",
                "visual_evidence": "Insufficient visual evidence: image classified as generic natural rock or sandstone.",
                "confidence": 0.0,
                "reason": "Insufficient visual evidence: generic reddish sandstone without distinctive carved architecture.",
            },
            "top_k": 5,
            "matches": [],
            "metadata": {},
            "evidence": {},
            "answer": None,
            "citations": [],
            "reason": "insufficient_visual_evidence",
            "is_grounded": False,
            "is_valid": True,
        }

        await eval_js(f"""
        (async function() {{
            const dataSandstone = {json.dumps(payload_sandstone)};
            const origFetch = window.fetch;
            window.fetch = function(url, options) {{
                if (typeof url === 'string' && url.includes('/recognize')) {{
                    return Promise.resolve(new Response(JSON.stringify(dataSandstone), {{
                        status: 200,
                        headers: {{ 'Content-Type': 'application/json' }}
                    }}));
                }}
                return origFetch.apply(this, arguments);
            }};
            const retryBtn = document.getElementById('retry-rec-btn') || document.getElementById('recognize-btn');
            if (retryBtn) retryBtn.click();

            for (let i = 0; i < 40; i++) {{
                const card = document.querySelector('.result');
                if (card && card.innerText.includes('Inconclusive Visual Match')) break;
                await new Promise(res => setTimeout(res, 100));
            }}
        }})()
        """)
        await asyncio.sleep(0.3)

        sandstone_ui = await eval_js("""
        (function() {
            const card = document.querySelector('.result');
            const nameEl = card ? card.querySelector('.result__name') : null;
            const verdictEl = card ? card.querySelector('.result__verdict') : null;
            const bodyText = card ? card.innerText : '';
            return {
                nameText: nameEl ? nameEl.innerText.trim() : '',
                verdictText: verdictEl ? verdictEl.innerText.trim() : '',
                hasInsufficientTier: bodyText.toLowerCase().includes('insufficient'),
                hasSandstoneCategory: bodyText.toLowerCase().includes('sandstone')
            };
        })()
        """)

        s_ok = (
            "inconclusive visual match" in sandstone_ui["nameText"].lower()
            and "identification declined" in sandstone_ui["verdictText"].lower()
            and sandstone_ui["hasInsufficientTier"]
        )
        records.append({
            "test": "9E. Genuine insufficient evidence displays proper Inconclusive Visual Match",
            "observed_name": sandstone_ui["nameText"],
            "observed_verdict": sandstone_ui["verdictText"],
            "hasInsufficientTier": sandstone_ui["hasInsufficientTier"],
            "status": "PASS" if s_ok else "FAIL",
            "detail": f"Properly distinguished: genuine sandstone renders '{sandstone_ui['verdictText']}' - '{sandstone_ui['nameText']}'",
        })

    return records


async def main():
    print("=" * 75)
    print("STARTING GEMINI HTTP 503 ERROR HANDLING & CLASSIFICATION ACCEPTANCE SUITE")
    print("=" * 75)

    results = []

    # Run Backend & Client Tests
    results.append(await test_1_http_503_followed_by_success())
    results.append(await test_2_two_consecutive_503_responses())
    results.append(await test_3_http_429_quota_error())
    results.append(await test_4_http_400_invalid_request())
    results.append(await test_5_network_failure())
    results.append(await test_6_backend_timeout())
    results.append(await test_7_manual_retry_not_cached())
    results.append(await test_8_user_cancellation_during_retry())

    # Launch Chrome on isolated port 9226 for CDP Frontend Test
    user_data_dir = tempfile.mkdtemp(prefix="gemini_503_chrome_")
    print(f"\nLaunching Headless Chrome on CDP port {CDP_PORT}...")
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--disable-popup-blocking",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        # Wait for CDP endpoint to be available
        ws_url = None
        for _ in range(30):
            await asyncio.sleep(0.5)
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"http://127.0.0.1:{CDP_PORT}/json")
                    if resp.status_code == 200:
                        targets = resp.json()
                        for t in targets:
                            if t.get("type") == "page":
                                ws_url = t.get("webSocketDebuggerUrl")
                                break
                        if ws_url:
                            break
            except Exception:
                pass

        if not ws_url:
            raise RuntimeError(f"Could not connect to Headless Chrome on port {CDP_PORT}")

        print(f"Connected to Chrome CDP WebSocket: {ws_url}")
        frontend_records = await test_9_frontend_cdp_verification(ws_url)
        results.extend(frontend_records)

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()

    # Print Summary Table
    print("\n" + "=" * 75)
    print("RESULTS SUMMARY")
    print("=" * 75)
    all_passed = True
    for r in results:
        status = r["status"]
        if status != "PASS":
            all_passed = False
        print(f"[{status}] {r['test']}: {r.get('detail', '')}")

    print("=" * 75)
    print(f"FINAL OUTCOME: {'ALL 12 CHECKS PASSED (100%)' if all_passed else 'SOME CHECKS FAILED'}")
    print("=" * 75)

    # Save results to JSON
    out_file = Path("scripts/gemini_503_test_results.json")
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved test results to {out_file.resolve()}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    code = asyncio.run(main())
    sys.exit(code)
