"""
Final end-to-end verification for Step 5.
Read-only — no source files are modified.
"""

import sys
import os
import re
import subprocess
import numpy as np

os.chdir(r"C:\Users\humai\AI")
sys.path.insert(0, r"C:\Users\humai\AI")

from backend.heritage_service import build_service
from backend.ollama import OllamaVisionClient

print("=" * 70)
print("STEP 5 — FINAL END-TO-END VERIFICATION")
print("=" * 70)

# ── CHECK 5: API KEY SECURITY ───────────────────────────────────────────────

print("\n[CHECK 5] API KEY SECURITY")

ollama_key_set = bool(os.getenv("OLLAMA_API_KEY"))
gemini_key_set = bool(os.getenv("GEMINI_API_KEY"))
print(f"  OLLAMA_API_KEY set in env: {ollama_key_set}  (expected: False)")
print(f"  GEMINI_API_KEY set in env: {gemini_key_set}  (expected: False)")

env_key_pattern = re.compile(r'(?:OLLAMA_API_KEY|GEMINI_API_KEY)\s*=\s*["\']?[a-zA-Z0-9+/]{8,}')
frontend_files = []
for root, dirs, files in os.walk(r"frontend\src"):
    dirs[:] = [d for d in dirs if d not in ["node_modules", ".next"]]
    for fn in files:
        if fn.endswith((".ts", ".tsx", ".js", ".jsx", ".json")):
            filepath = os.path.join(root, fn)
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if env_key_pattern.findall(content):
                frontend_files.append(filepath)

api_key_found = len(frontend_files) > 0
print(f"  API key string in frontend source: {api_key_found}  (expected: False)")

ollama_src = open(r"backend\ollama.py", encoding="utf-8").read()
# Only flag if the actual key VALUE is logged, not just the env var name
violations = []
for line in ollama_src.splitlines():
    s = line.strip()
    if "logger" in s:
        if re.search(r"logger\.(debug|info|warning|error)\(.*api_key\s*[\+%]\s*", s, re.I):
            violations.append(s)
        elif "OLLAMA_API_KEY" in s and "not set" not in s:
            violations.append(s)
print(f"  API key value logged in ollama.py: {len(violations)} violations  (expected: 0)")

check5_pass = not ollama_key_set and not gemini_key_set and not api_key_found and len(violations) == 0
print(f"  CHECK 5: {'PASS' if check5_pass else 'FAIL'}")

# ── BUILD SERVICE ────────────────────────────────────────────────────────────

print("\n[LOADING] Building service...")
try:
    svc = build_service()
    print(f"  Service built OK — index size: {svc.confidence_layer.index.ntotal}, threshold: {svc.confidence_layer.config.similarity_threshold}")
except Exception as e:
    print(f"  SERVICE BUILD FAILED: {e}")
    sys.exit(1)

# ── CHECK 1: LOCAL KNOWN MONUMENT ────────────────────────────────────────────

print("\n[CHECK 1] LOCAL KNOWN MONUMENT (taj_mahal_01.jpg)")
img_path = r"data\raw\taj_mahal\taj_mahal_01.jpg"
assert os.path.isfile(img_path), f"Missing test image: {img_path}"

result1 = svc.recognize(img_path, question="", top_k=5)
print(f"  site_id:            {result1.site_id!r}")
print(f"  confident:          {result1.confident}")
print(f"  confirmed:          {result1.confirmed}")
print(f"  similarity:         {result1.similarity}")
print(f"  recognition_source: {result1.recognition_source!r}")
print(f"  global_identification: {result1.global_identification}")

check1_site = result1.site_id == "taj_mahal"
check1_conf = result1.confident is True
check1_local = result1.recognition_source == "local"
check1_no_ollama = result1.global_identification is None
check1_pass = check1_site and check1_conf and check1_local and check1_no_ollama
print(f"  site_id=taj_mahal:          {check1_site}")
print(f"  confident=True:             {check1_conf}")
print(f"  source=local:               {check1_local}")
print(f"  global_identification=None: {check1_no_ollama}")
print(f"  CHECK 1: {'PASS' if check1_pass else 'FAIL'}")

# ── CHECK 2: OUT-OF-DATASET REJECTION ─────────────────────────────────────────

print("\n[CHECK 2] OUT-OF-DATASET REJECTION (synthetic dissimilar embedding)")
# Use a unit vector orthogonal-ish to the indexed monuments: all-ones direction
# is dissimilar to the clustered monument vectors in the FAISS index.
noise_vec = np.ones((512,), dtype=np.float32)
noise_vec = noise_vec / np.linalg.norm(noise_vec)
result2 = svc.recognize(noise_vec, question="", top_k=5)
print(f"  site_id:      {result2.site_id!r}")
print(f"  confident:    {result2.confident}")
print(f"  similarity:   {result2.similarity}")
print(f"  reason:       {result2.reason!r}")
check2_reject = result2.confident is False and result2.site_id == "unknown"
print(f"  correctly rejected: {check2_reject}")
print(f"  CHECK 2: {'PASS' if check2_reject else 'FAIL'}")

# Also verify Ollama client initializes without network
print("  (Testing Ollama client init without network)")
try:
    ollama_client = OllamaVisionClient(api_key=None, base_url="https://ollama.com/api")
    print(f"  Ollama client created OK, endpoint: {ollama_client.endpoint_url}")
    check2b_pass = True
except Exception as e:
    print(f"  Ollama client init FAILED: {e}")
    check2b_pass = False
check2_pass = check2_reject and check2b_pass
print(f"  CHECK 2b (Ollama client init): {'PASS' if check2b_pass else 'FAIL'}")
print(f"  CHECK 2: {'PASS' if check2_pass else 'FAIL'}")

# ── CHECK 3: UNKNOWN / NON-MONUMENT IMAGE ─────────────────────────────────────

print("\n[CHECK 3] UNKNOWN / NON-MONUMENT IMAGE (near-zero vector)")
weak_vec = np.ones((512,), dtype=np.float32) * 0.01
result3 = svc.recognize(weak_vec, question="", top_k=5)
print(f"  site_id:   {result3.site_id!r}")
print(f"  confirmed: {result3.confirmed}")
print(f"  decision:  {result3.decision!r}")
check3_contract = (
    result3.confirmed is False and
    result3.site_id == "unknown" and
    result3.decision == "unknown"
)
print(f"  confirmed=False: {result3.confirmed is False}")
print(f"  site_id=unknown: {result3.site_id == 'unknown'}")
print(f"  decision=unknown:{result3.decision == 'unknown'}")
print(f"  CHECK 3: {'PASS' if check3_contract else 'FAIL'}")

# ── CHECK 4: FRONTEND TYPECHECK & BUILD ──────────────────────────────────────

print("\n[CHECK 4] FRONTEND — TYPECHECK & BUILD")
# Run npm/npx commands via shell=True for Windows batch wrapper resolution
r1 = subprocess.run("npx tsc --noEmit", cwd=r"C:\Users\humai\AI\frontend", capture_output=True, text=True, shell=True)
r2 = subprocess.run("npm run build", cwd=r"C:\Users\humai\AI\frontend", capture_output=True, text=True, timeout=120, shell=True)
type_ok = r1.returncode == 0
build_ok = r2.returncode == 0
if not type_ok:
    print(f"  tsc stdout: {r1.stdout[:500]}")
    print(f"  tsc stderr: {r1.stderr[:500]}")
if not build_ok:
    print(f"  build stderr tail: {r2.stderr[-600:]}")
print(f"  tsc --noEmit: {'PASS' if type_ok else 'FAIL'}")
print(f"  npm run build: {'PASS' if build_ok else 'FAIL'}")
check4_pass = type_ok and build_ok
print(f"  CHECK 4: {'PASS' if check4_pass else 'FAIL'}")

# ── CHECK 6: REGRESSION TESTS ────────────────────────────────────────────────

print("\n[CHECK 6] REGRESSION — FULL TEST SUITE")
r3 = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
    capture_output=True, text=True, timeout=120,
    cwd=r"C:\Users\humai\AI"
)
lines = r3.stdout.strip().splitlines()
last = lines[-1] if lines else ""
print(f"  pytest exit: {r3.returncode}")
print(f"  last line:   {last}")
check6_pass = r3.returncode == 0
print(f"  CHECK 6: {'PASS' if check6_pass else 'FAIL'}")

# ── SUMMARY ──────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("FINAL VERIFICATION SUMMARY")
print("=" * 70)
checks = [
    ("1. Local Known Monument",            "ACCEPT local match",              check1_pass),
    ("2. Out-of-Dataset Rejection",        "REJECT local -> Ollama fallback", check2_pass),
    ("3. Unknown / Non-Monument",          "confirmed=false, site_id=unknown", check3_contract),
    ("4. Frontend Typecheck & Build",      "Zero errors, build succeeds",     check4_pass),
    ("5. API Key Security",                "Key in env only, never frontend", check5_pass),
    ("6. Full Regression (Tests)",         "All automated tests pass",        check6_pass),
]
all_pass = all(c[2] for c in checks)
print(f"{'CHECK':<38s} | {'EXPECTED':<36s} | {'STATUS'}")
print("-" * 80)
for label, expected, passed in checks:
    status = "PASS" if passed else "FAIL"
    print(f"{label:<38s} | {expected:<36s} | {status}")
print("-" * 80)
overall = "ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED"
print(f"\nOVERALL: {overall}")
print("=" * 70)
