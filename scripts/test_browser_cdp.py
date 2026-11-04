"""
CDP Browser automation test for frontend camera and responsive UI
"""

import asyncio
import json
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "http://127.0.0.1:8080/#recognition"


async def main():
    print("Launching Headless Chrome on port 9222...")
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--disable-gpu",
        "--no-sandbox",
        "--use-fake-ui-for-media-stream",  # auto-grants camera permission in Chrome
        "--use-fake-device-for-media-stream",  # feeds synthetic test video
        "--window-size=360,740",
    ])
    try:
        await asyncio.sleep(2.0)
        # Fetch websocket debug target
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5).read()
        targets = json.loads(targets_raw.decode("utf-8"))
        ws_url = targets[0]["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url) as ws:
            async def send_cmd(method, params=None):
                cmd_id = int(time.time() * 1000) % 100000
                msg = {"id": cmd_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(msg))
                while True:
                    res_raw = await ws.recv()
                    res = json.loads(res_raw)
                    if res.get("id") == cmd_id:
                        return res.get("result", {})

            await send_cmd("Page.enable")
            await send_cmd("Runtime.enable")
            
            # Navigate to index.html and wait for Page.loadEventFired
            await send_cmd("Page.navigate", {"url": "http://127.0.0.1:8080/index.html"})
            
            # Wait for load event
            loaded = False
            for _ in range(50):
                msg_raw = await ws.recv()
                msg = json.loads(msg_raw)
                if msg.get("method") == "Page.loadEventFired":
                    loaded = True
                    break
            await asyncio.sleep(1.0)

            # Evaluate mobile DOM state
            eval_res = await send_cmd("Runtime.evaluate", {
                "expression": """
                (function() {
                    const cameraModal = document.getElementById('camera-modal');
                    const uploadCameraBtn = document.getElementById('upload-camera');
                    const cameraInput = document.getElementById('camera-input');
                    const fallbackBtn = document.getElementById('camera-fallback-btn');
                    const snapBtn = document.getElementById('camera-snap');
                    
                    return {
                        hasModal: !!cameraModal,
                        modalHiddenInitial: cameraModal ? cameraModal.hidden : null,
                        cameraBtnExists: !!uploadCameraBtn,
                        acceptAttr: cameraInput ? cameraInput.getAttribute('accept') : null,
                        captureAttr: cameraInput ? cameraInput.getAttribute('capture') : null,
                        hasFallbackBtn: !!fallbackBtn,
                        hasSnapBtn: !!snapBtn
                    };
                })()
                """,
                "returnByValue": True
            })
            print("DOM State in Chrome:", eval_res["result"]["value"])
            val = eval_res["result"]["value"]
            assert val["acceptAttr"] == "image/*", "acceptAttr must be image/*"
            assert val["captureAttr"] == "environment", "captureAttr must be environment"
            assert val["hasFallbackBtn"] is True, "fallback button must exist"

            # Test clicking Take Photo in Chrome (with fake media stream)
            click_res = await send_cmd("Runtime.evaluate", {
                "expression": """
                (function() {
                    document.getElementById('upload-camera').click();
                    return {
                        modalHiddenAfterClick: document.getElementById('camera-modal').hidden
                    };
                })()
                """,
                "returnByValue": True
            })
            print("Modal state after click:", click_res["result"]["value"])
            assert click_res["result"]["value"]["modalHiddenAfterClick"] is False, "Camera modal should open"

            # Test closing camera modal
            close_res = await send_cmd("Runtime.evaluate", {
                "expression": """
                (function() {
                    document.getElementById('camera-cancel').click();
                    return {
                        modalHiddenAfterCancel: document.getElementById('camera-modal').hidden
                    };
                })()
                """,
                "returnByValue": True
            })
            print("Modal state after cancel:", close_res["result"]["value"])
            assert close_res["result"]["value"]["modalHiddenAfterCancel"] is True, "Camera modal should close"

            print("[SUCCESS] All Chrome Headless mobile browser tests passed!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(main())
