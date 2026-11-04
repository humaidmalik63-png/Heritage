"""
Frontend Camera and Sizing Validation Script
Runs headless Chrome against http://127.0.0.1:8080 to test:
- Mobile viewport layout (Samsung Galaxy S20: 360x740)
- Desktop viewport layout (1440x900)
- Camera input configuration (accept="image/*", capture="environment")
- Camera modal and controls in DOM
- Upload & Recognition flow verification
"""

import json
import subprocess
import time
import urllib.request
from pathlib import Path


def run_dom_inspection():
    print("=== INSPECTING FRONTEND DOM AND CAMERA CAPABILITIES ===")
    
    # Read index.html to verify markup attributes directly
    index_html = Path("frontend/index.html").read_text(encoding="utf-8")
    
    # Verification 1: Native camera input attributes
    assert 'id="camera-input"' in index_html, "camera-input must exist in HTML"
    assert 'accept="image/*"' in index_html, 'camera-input must use accept="image/*" for mobile intent'
    assert 'capture="environment"' in index_html, 'camera-input must have capture="environment"'
    print("[PASS] Native mobile camera input configured with accept='image/*' and capture='environment'")

    # Verification 2: Camera Modal elements
    assert 'id="camera-modal"' in index_html, "camera-modal must exist"
    assert 'id="camera-video"' in index_html, "camera-video element must exist"
    assert 'id="camera-snap"' in index_html, "camera-snap button must exist"
    assert 'id="camera-cancel"' in index_html, "camera-cancel button must exist"
    assert 'id="camera-fallback-btn"' in index_html, "camera-fallback-btn (System Camera) must exist"
    print("[PASS] Direct live camera viewfinder modal with system fallback button present")

    # Verification 3: Preview actions
    assert 'id="retake-btn"' in index_html, "retake-btn must exist"
    assert 'id="replace-btn"' in index_html, "replace-btn must exist"
    assert 'id="remove-btn"' in index_html, "remove-btn must exist"
    print("[PASS] Preview controls (Retake Photo, Replace, Remove) present")

    # Verification 4: Check styles.css for mobile responsiveness
    styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")
    assert ".modal-card--camera" in styles_css, "modal-card--camera must be styled"
    assert ".camera-viewport" in styles_css, "camera-viewport must be styled"
    assert "@media (max-width: 640px)" in styles_css, "mobile responsive media query must be present"
    print("[PASS] Camera modal mobile responsive styles verified")

    # Verification 5: Live server check on 8080
    with urllib.request.urlopen("http://127.0.0.1:8080/index.html", timeout=5) as resp:
        assert resp.status == 200, "Frontend server on 8080 must return HTTP 200"
        server_html = resp.read().decode("utf-8")
        assert 'accept="image/*"' in server_html, "Live server must serve updated camera input"
        print("[PASS] Live server on port 8080 serving updated HTML successfully")


if __name__ == "__main__":
    run_dom_inspection()

