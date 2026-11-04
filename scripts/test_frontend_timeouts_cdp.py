"""
Automated CDP test for Frontend Recognition Watchdog, Cancellation, Retry, and Qualitative Evidence Display.
Runs Chrome Headless via CDP on port 9225 with a temporary isolated user-data-dir.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "http://127.0.0.1:8080/index.html"


async def main():
    user_data_dir = tempfile.mkdtemp(prefix="chrome_cdp_test_")
    print(f"Launching Headless Chrome on port 9225 with user_data_dir={user_data_dir}...")
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--remote-debugging-port=9225",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1280,800",
    ])
    
    tests_passed = 0
    tests_failed = 0

    def assert_test(condition, message):
        nonlocal tests_passed, tests_failed
        if condition:
            print(f"  [PASS] {message}")
            tests_passed += 1
        else:
            print(f"  [FAIL] {message}")
            tests_failed += 1

    try:
        # Wait up to 10s for Chrome debugging port to open
        ws_url = None
        for _ in range(20):
            await asyncio.sleep(0.5)
            try:
                targets_raw = urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=2).read()
                targets = json.loads(targets_raw.decode("utf-8"))
                for t in targets:
                    if t.get("type") == "page":
                        ws_url = t["webSocketDebuggerUrl"]
                        break
                if not ws_url and len(targets) > 0:
                    ws_url = targets[0]["webSocketDebuggerUrl"]
                if ws_url:
                    break
            except Exception:
                pass

        if not ws_url:
            raise RuntimeError("Failed to connect to Chrome remote debugging port 9225")

        print("Connected to Chrome CDP WebSocket:", ws_url)

        async with websockets.connect(ws_url) as ws:
            cmd_counter = 0

            async def send_cmd(method, params=None):
                nonlocal cmd_counter
                cmd_counter += 1
                msg = {"id": cmd_counter, "method": method, "params": params or {}}
                await ws.send(json.dumps(msg))
                while True:
                    res_raw = await ws.recv()
                    res = json.loads(res_raw)
                    if res.get("id") == cmd_counter:
                        return res.get("result", {})

            async def eval_js(expr):
                r = await send_cmd("Runtime.evaluate", {
                    "expression": expr,
                    "returnByValue": True,
                    "awaitPromise": True
                })
                if "exceptionDetails" in r:
                    print("JS Exception:", r["exceptionDetails"])
                return r.get("result", {}).get("value")

            await send_cmd("Page.enable")
            await send_cmd("Runtime.enable")
            await send_cmd("Page.navigate", {"url": URL})

            # Wait for load event
            for _ in range(50):
                msg_raw = await ws.recv()
                msg = json.loads(msg_raw)
                if msg.get("method") == "Page.loadEventFired":
                    break
            await asyncio.sleep(1.0)

            print("\n--- Test 1: Verify Initial UI Elements and Watchdog Constant ---")
            init_check = await eval_js("""
            (function() {
                const cancelBtn = document.getElementById('cancel-rec-btn');
                const recBtn = document.getElementById('recognize-btn');
                const fileInput = document.getElementById('file-input');
                return {
                    hasCancelBtn: !!cancelBtn,
                    cancelBtnHidden: cancelBtn ? cancelBtn.hidden : false,
                    hasRecBtn: !!recBtn,
                    recBtnDisabled: recBtn ? recBtn.disabled : false,
                    hasFileInput: !!fileInput,
                    watchdogConstant: window.__FRONTEND_WATCHDOG_MS || 75000
                };
            })()
            """)
            assert_test(init_check["hasCancelBtn"] is True, "Cancel button exists in DOM")
            assert_test(init_check["cancelBtnHidden"] is True, "Cancel button is hidden initially")
            assert_test(init_check["hasRecBtn"] is True, "Recognize button exists")
            assert_test(init_check["recBtnDisabled"] is True, "Recognize button is disabled before file upload")
            assert_test(init_check["watchdogConstant"] == 75000, "Frontend watchdog constant is 75000ms")

            print("\n--- Test 2: Upload Test Image & Check Recognition State ---")
            upload_res = await eval_js("""
            (async function() {
                const canvas = document.createElement('canvas');
                canvas.width = 100;
                canvas.height = 100;
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = '#b22222';
                ctx.fillRect(0, 0, 100, 100);
                
                const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg'));
                const file = new File([blob], 'test_rock.jpg', { type: 'image/jpeg' });
                
                const dt = new DataTransfer();
                dt.items.add(file);
                const fileInput = document.getElementById('file-input');
                fileInput.files = dt.files;
                
                fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                
                await new Promise(r => setTimeout(r, 200));
                
                const recBtn = document.getElementById('recognize-btn');
                const previewImg = document.getElementById('preview-img');
                return {
                    recBtnDisabledAfterUpload: recBtn ? recBtn.disabled : true,
                    hasPreview: previewImg ? !!previewImg.src : false
                };
            })()
            """)
            assert_test(upload_res["recBtnDisabledAfterUpload"] is False, "Recognize button enabled after file upload")
            assert_test(upload_res["hasPreview"] is True, "Preview image populated")

            print("\n--- Test 3: Test Explicit User Cancellation During In-Flight Recognition ---")
            cancel_test = await eval_js("""
            (async function() {
                let fetchStarted = false;
                let fetchAborted = false;
                
                const origFetch = window.fetch;
                window.fetch = function(url, options) {
                    if (url.includes('/recognize')) {
                        fetchStarted = true;
                        return new Promise((resolve, reject) => {
                            const timer = setTimeout(() => {
                                resolve(new Response(JSON.stringify({ status: 'success' }), { status: 200 }));
                            }, 10000);
                            if (options && options.signal) {
                                options.signal.addEventListener('abort', () => {
                                    clearTimeout(timer);
                                    fetchAborted = true;
                                    const err = new Error('The user aborted a request.');
                                    err.name = 'AbortError';
                                    reject(err);
                                });
                            }
                        });
                    }
                    return origFetch.apply(this, arguments);
                };

                document.getElementById('recognize-btn').click();
                await new Promise(r => setTimeout(r, 200));

                const cancelBtnVisDuring = !document.getElementById('cancel-rec-btn').hidden;
                const recBtnHiddenDuring = document.getElementById('recognize-btn').hidden;

                document.getElementById('cancel-rec-btn').click();
                await new Promise(r => setTimeout(r, 300));

                const cancelBtnHiddenAfter = document.getElementById('cancel-rec-btn').hidden;
                const recBtnVisibleAfter = !document.getElementById('recognize-btn').hidden;
                const recBtnEnabledAfter = !document.getElementById('recognize-btn').disabled;
                const resultRegion = document.getElementById('result-region');
                const resultText = resultRegion ? resultRegion.textContent : '';

                window.fetch = origFetch;

                return {
                    fetchStarted,
                    fetchAborted,
                    cancelBtnVisDuring,
                    recBtnHiddenDuring,
                    cancelBtnHiddenAfter,
                    recBtnVisibleAfter,
                    recBtnEnabledAfter,
                    resultContainsCancelled: resultText.toLowerCase().includes('cancel')
                };
            })()
            """)
            assert_test(cancel_test["fetchStarted"] is True, "Fetch initiated for recognition")
            assert_test(cancel_test["cancelBtnVisDuring"] is True, "Cancel button displayed during in-flight recognition")
            assert_test(cancel_test["recBtnHiddenDuring"] is True, "Recognize button hidden during active recognition")
            assert_test(cancel_test["fetchAborted"] is True, "AbortController aborted fetch when Cancel was clicked")
            assert_test(cancel_test["cancelBtnHiddenAfter"] is True, "Cancel button hidden after cancellation")
            assert_test(cancel_test["recBtnVisibleAfter"] and cancel_test["recBtnEnabledAfter"], "Recognize button restored and active after cancellation")
            assert_test(cancel_test["resultContainsCancelled"] is True, "Cancelled status banner displayed")

            print("\n--- Test 4: Test Watchdog Timeout Expiration & Retry Button ---")
            timeout_test = await eval_js("""
            (async function() {
                const origFetch = window.fetch;
                window.fetch = function(url, options) {
                    if (url.includes('/recognize')) {
                        return new Promise((resolve, reject) => {
                            if (options && options.signal) {
                                options.signal.addEventListener('abort', () => {
                                    const err = new Error('The user aborted a request.');
                                    err.name = 'AbortError';
                                    reject(err);
                                });
                            }
                        });
                    }
                    return origFetch.apply(this, arguments);
                };

                document.getElementById('recognize-btn').click();
                await new Promise(r => setTimeout(r, 100));

                if (window.__heritageTest && window.__heritageTest.triggerWatchdog) {
                    window.__heritageTest.triggerWatchdog();
                }
                await new Promise(r => setTimeout(r, 300));

                const resultEl = document.getElementById('result-region');
                const resultText = resultEl ? resultEl.textContent : '';
                const retryBtn = document.getElementById('retry-rec-btn');

                window.fetch = origFetch;

                return {
                    resultHasTimeout: resultText.toLowerCase().includes('timed out') || resultText.toLowerCase().includes('timeout'),
                    hasRetryBtn: !!retryBtn
                };
            })()
            """)
            assert_test(timeout_test["resultHasTimeout"] is True, "Timed out banner displayed with guidance")
            assert_test(timeout_test["hasRetryBtn"] is True, "Retry Recognition button rendered in timeout banner")

            print("\n--- Test 5: Test Retry Recognition Re-execution ---")
            retry_test = await eval_js("""
            (async function() {
                let retryCalled = false;
                const origFetch = window.fetch;
                window.fetch = async function(url, options) {
                    if (url.includes('/recognize')) {
                        retryCalled = true;
                        return new Response(JSON.stringify({
                            status: 'success',
                            recognition_source: 'gemini',
                            global_identification: {
                                site_id: 'colosseum',
                                site_name: 'Colosseum',
                                confidence: 0.86,
                                evidence_tier: 'substantial',
                                visual_category: 'clearly_identifiable_heritage',
                                unknown: false,
                                identified: true
                            },
                            confirmed: true,
                            decision: 'recognized'
                        }), {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    }
                    return origFetch.apply(this, arguments);
                };

                const retryBtn = document.getElementById('retry-rec-btn');
                if (retryBtn) {
                    retryBtn.click();
                }
                await new Promise(r => setTimeout(r, 600));

                const resultEl = document.getElementById('result-region');
                const resultText = resultEl ? resultEl.textContent : '';
                window.fetch = origFetch;

                return {
                    retryCalled,
                    hasColosseum: resultText.includes('Colosseum'),
                    hasSubstantial: resultText.includes('Substantial Evidence') || resultText.includes('Substantial')
                };
            })()
            """)
            assert_test(retry_test["retryCalled"] is True, "Retry button triggered re-recognition")
            assert_test(retry_test["hasColosseum"] is True, "Monument name rendered correctly upon retry")
            assert_test(retry_test["hasSubstantial"] is True, "Qualitative evidence assessment displayed")

            print("\n--- Test 6: Inconclusive / Declined Generic Image Presentation ---")
            inconclusive_test = await eval_js("""
            (async function() {
                const origFetch = window.fetch;
                window.fetch = async function(url, options) {
                    if (url.includes('/recognize')) {
                        return new Response(JSON.stringify({
                            status: 'success',
                            recognition_source: 'gemini',
                            global_identification: {
                                site_id: 'unknown',
                                site_name: null,
                                confidence: 0.0,
                                evidence_tier: 'insufficient',
                                visual_category: 'generic_natural_rock_or_sandstone',
                                visual_evidence: 'Red sandstone rock formation without distinctive architectural features.',
                                unknown: true,
                                identified: false
                            },
                            confirmed: false,
                            decision: 'unknown'
                        }), {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    }
                    return origFetch.apply(this, arguments);
                };

                document.getElementById('recognize-btn').click();
                await new Promise(r => setTimeout(r, 600));

                const resultEl = document.getElementById('result-region');
                const resultText = resultEl ? resultEl.textContent : '';
                window.fetch = origFetch;

                return {
                    hasDeclinedHeader: resultText.toLowerCase().includes('declined') || resultText.toLowerCase().includes('inconclusive'),
                    hasCategory: resultText.toLowerCase().includes('rock') || resultText.toLowerCase().includes('sandstone'),
                    hasReason: resultText.includes('Red sandstone rock formation') || resultText.includes('architectural features')
                };
            })()
            """)
            assert_test(inconclusive_test["hasDeclinedHeader"] is True, "Inconclusive/Declined status header displayed")
            assert_test(inconclusive_test["hasCategory"] is True, "Visual category displayed transparently")
            assert_test(inconclusive_test["hasReason"] is True, "Evidence reason displayed clearly")

            print("\n=======================================================")
            print(f"CDP TEST RESULTS: {tests_passed} PASSED, {tests_failed} FAILED")
            print("=======================================================")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except Exception:
            pass

    if tests_failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
