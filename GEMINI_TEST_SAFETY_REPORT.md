# GEMINI TEST SAFETY & DUAL-ENVIRONMENT INTEGRATION REPORT

**System:** Visual Heritage Recognition and Grounded Cultural Discovery Platform  
**Component:** Gemini Vision Fallback Pipeline & Test Safety Guard (`backend/gemini.py`, `tests/test_gemini.py`)  
**Date:** November 4, 2026  
**Status:** RESTORED, VERIFIED & PASSING (ZERO LIVE CALLS CONSUMED)  

---

## 1. Executive Summary

This engineering report documents the restoration and formalization of the **`DISABLE_LIVE_GEMINI`** test safety safeguard within the Heritage Recognition Platform.

### The Problem
- The platform previously used `DISABLE_LIVE_GEMINI=1` to prevent automated test suites from accidentally consuming Google Gemini API quota or making live external network calls.
- When resolving environment loading for normal local execution, an initial fix removed this safeguard to allow `.env` keys to load properly into the backend server.
- However, removing the safeguard left a vulnerability where unmocked test invocations could potentially dispatch live API calls if an API key was present in the environment or `.env`.

### The Harmonized Solution
A robust dual-mode architecture has been implemented that satisfies both operational requirements simultaneously:
1. **Normal Local Execution:** Automatically and deterministically loads `.env` anchored to the project root (`Path(__file__).resolve().parent.parent / ".env"`), allowing Uvicorn, developers, and scripts to access the configured `GEMINI_API_KEY` seamlessly regardless of the process current working directory.
2. **Guaranteed Test Safety:** When `DISABLE_LIVE_GEMINI=1` is set by a test runner or CI environment:
   - **Mock Transports Work Naturally:** If a test passes a mock HTTP transport (`transport=httpx.MockTransport(...)`), mock requests execute with 100% fidelity in-memory.
   - **Zero Live Network Requests:** If no mock transport is provided (`_transport is None`), the client intercepts all calls before any socket, DNS, or HTTP connection is initiated, safely returning a structured fallback with `error_type="live_calls_disabled"`.
   - **Non-Overwritable by `.env`:** Environment loading uses `override=False`, guaranteeing that loading `.env` will never silently clear or override an explicit `DISABLE_LIVE_GEMINI=1` flag.

---

## 2. Architecture & Implementation

### 2.1 Test Safety Flag Detection (`backend/gemini.py`)
```python
def is_live_gemini_disabled() -> bool:
    """
    Check whether live external Gemini API calls are disabled by the test environment.
    Returns True if DISABLE_LIVE_GEMINI is set to '1', 'true', 'yes', or 'on'.
    """
    val = os.getenv("DISABLE_LIVE_GEMINI", "0").strip().lower()
    return val in ("1", "true", "yes", "on")
```

### 2.2 Safe, Non-Overwriting Project-Root `.env` Loading
```python
def ensure_env_loaded() -> None:
    """
    Ensure project-root .env is loaded without overriding existing environment variables.
    Preserves explicitly set test flags (e.g. DISABLE_LIVE_GEMINI) and process-level overrides.
    """
    try:
        from dotenv import load_dotenv

        _project_root = Path(__file__).resolve().parent.parent
        _env_file = _project_root / ".env"
        if _env_file.exists():
            load_dotenv(dotenv_path=_env_file, override=False)
        else:
            load_dotenv(override=False)
    except ImportError:
        pass
```

### 2.3 Intelligent Initialization Logic (`GeminiVisionClient.__init__`)
The client distinguishes between real live network operations and in-memory mock transports:
```python
self._transport = transport
self.live_disabled = is_live_gemini_disabled()

if api_key is not None:
    self.api_key = api_key
elif self.live_disabled and self._transport is None:
    # Test safety safeguard: live external calls disabled and no mock transport provided.
    # Do not load or expose live production credentials.
    self.api_key = None
else:
    # Normal mode or mocked transport mode:
    # Read from environment, loading project-root .env if not yet in os.environ.
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        ensure_env_loaded()
        key = os.getenv("GEMINI_API_KEY")
    # If in mock transport test mode and no key provided, supply safe dummy key for mock tests
    if not key and self._transport is not None:
        key = "mock-test-key"
    self.api_key = key
```

### 2.4 Pre-Network Interception (`identify_monument` and `_execute_api_request`)
At the very entry point of recognition, before preparing network sockets:
```python
# 1. Guard against live external calls if test safety flag is active
if self.live_disabled and self._transport is None:
    logger.info("Live Gemini API call blocked by DISABLE_LIVE_GEMINI=1 test safeguard")
    return fallback_unknown_result(
        reason="Live Gemini API calls disabled (DISABLE_LIVE_GEMINI=1)",
        visual_category="unknown",
        error_type="live_calls_disabled",
        status="external_service_unavailable",
        evidence_tier="unavailable",
    )
```
As defense-in-depth, `_execute_api_request` contains an identical pre-flight check preventing direct calls.

### 2.5 Key Redaction in String Representation
Added `__repr__` to prevent accidental key exposure in debug logs or test assertions:
```python
def __repr__(self) -> str:
    key_status = "configured" if self.api_key else "missing"
    return (
        f"<GeminiVisionClient model={self.model!r} "
        f"api_key={key_status} live_disabled={self.live_disabled} "
        f"has_custom_transport={self._transport is not None}>"
    )
```

---

## 3. Dedicated Verification Tests (`tests/test_gemini.py`)

A new test suite `TestGeminiTestSafetyGuard` was added with 6 dedicated test cases:

| Test Case | Description | Verification Details | Result |
| :--- | :--- | :--- | :---: |
| `test_env_loading_does_not_override_test_safety_flag` | Non-overriding flag check | Sets `DISABLE_LIVE_GEMINI=1`, runs `ensure_env_loaded()`, asserts flag remains `"1"`. | **PASS** |
| `test_valid_environment_key_not_overwritten_by_env` | Explicit process key preservation | Sets process `GEMINI_API_KEY`, runs `ensure_env_loaded()`, asserts process key preserved. | **PASS** |
| `test_disable_live_gemini_blocks_network_requests` | Zero network request proof | Sets flag, calls `identify_monument()`, verifies `_client is None`, returns structured result. | **PASS** |
| `test_disable_live_gemini_allows_mock_transport` | Mock transport integration | Sets flag, injects `MockTransport`, verifies mock handler invoked with auth header & parsed. | **PASS** |
| `test_normal_mode_initializes_configured_key_without_exposing_it` | Normal mode & key redaction | Unsets flag, sets valid test key, verifies key configured, verified absent in `repr(client)`/`str(client)`. | **PASS** |
| `test_env_loading_independent_of_cwd` | CWD independence | Switches `os.chdir` to a temporary directory, verifies project-root `.env` variables load. | **PASS** |

---

## 4. Full Suite Test Results

1. **Gemini Client Unit & Safety Tests (`pytest tests/test_gemini.py`):**
   - **38 / 38 passed** in 10.17 seconds (32 existing + 6 new safety tests).
2. **Full Pytest Regression Suite (`pytest tests/`):**
   - **297 / 297 passed** in 46.08 seconds (0 regressions across API, RAG, CLIP, Confidence, Service layers).
3. **503 & Classification Acceptance Suite (`scripts/test_gemini_503_suite.py`):**
   - **12 / 12 checks passed** (100.0%) using isolated Chrome CDP and mock transports.
4. **Live Server Sanity Check:**
   - Fresh Uvicorn daemon running on port 8000: `/health` returns `200 OK`, index size 40, similarity threshold 0.85.
   - Taj Mahal local recognition verified: `site_id="taj_mahal"`, `confirmed=True`, `source="local"`.

---

## 5. Summary of System Invariants

- **Zero Live Quota Consumed:** All tests and verifications executed strictly via mock transports or disabled safety guards.
- **FAISS Vectors:** Preserved at 40 vectors, dimension 512.
- **Thresholds:** Similarity threshold 0.85, competitor margin 0.10.
- **Gemini Model:** `gemini-3.1-flash-lite`, thinking level `MINIMAL`, timeout 60.0s.
- **Watchdog Timeout:** Frontend watchdog aligned at 75.0s.
- **Production Independence:** Zero dependencies on Ollama in production inference.

