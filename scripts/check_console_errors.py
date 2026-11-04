"""
Check for console errors in Chrome when loading frontend
"""

import asyncio
import json
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "http://127.0.0.1:8080/index.html"


async def main():
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--remote-debugging-port=9224",
        "--disable-gpu",
    ])
    try:
        await asyncio.sleep(2.0)
        targets_raw = urllib.request.urlopen("http://127.0.0.1:9224/json", timeout=5).read()
        targets = json.loads(targets_raw.decode("utf-8"))
        ws_url = targets[0]["webSocketDebuggerUrl"]

        console_errors = []

        async with websockets.connect(ws_url) as ws:
            # Enable console and runtime
            await ws.send(json.dumps({"id": 1, "method": "Console.enable"}))
            await ws.send(json.dumps({"id": 2, "method": "Runtime.enable"}))
            await ws.send(json.dumps({"id": 3, "method": "Page.enable"}))
            await ws.send(json.dumps({"id": 4, "method": "Page.navigate", "params": {"url": URL}}))

            start_t = time.time()
            while time.time() - start_t < 4.0:
                try:
                    msg_raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    msg = json.loads(msg_raw)
                    if msg.get("method") == "Console.messageAdded":
                        entry = msg.get("params", {}).get("message", {})
                        if entry.get("level") == "error":
                            console_errors.append(entry.get("text"))
                    elif msg.get("method") == "Runtime.exceptionThrown":
                        details = msg.get("params", {}).get("exceptionDetails", {})
                        console_errors.append(details.get("text", "") + ": " + str(details.get("exception", {}).get("description", "")))
                except asyncio.TimeoutError:
                    pass

        print("Console errors count:", len(console_errors))
        if console_errors:
            print("Errors detected:", console_errors)
        else:
            print("[PASS] Zero console errors during page load and script initialization!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(main())

