# GEMINI HTTP 503 ERROR HANDLING & CLASSIFICATION REPORT

**System:** Visual Heritage Recognition and Grounded Cultural Discovery Platform  
**Component:** External Recognition Fallback Pipeline (`backend/gemini.py`, `backend/heritage_service.py`, `frontend/app.js`)  
**Date:** November 4, 2026  
**Status:** VALIDATED & READY FOR REVIEW (ZERO LIVE API CALLS CONSUMED)  

---

## 1. Executive Summary

During open-set image recognition, uncatalogued heritage sites (such as *Hawa Mahal*, *Fatehpur Sikri*, or genuine unindexed monuments) are correctly rejected by local CLIP embeddings (similarity < 0.85, competitor margin < 0.10) and routed to Gemini Vision fallback (`gemini-3.1-flash-lite`).

However, when Google's upstream API returns an **HTTP 503 Service Unavailable** (or upstream gateway 502/504) due to high demand or transient cluster hiccups, the platform previously suffered from critical classification flaws:
1. **Misclassification as Inconclusive / Generic Rock:** HTTP 503 errors were caught generically, yielding an empty/fallback `GeminiVisionResult` which was reported to the user as *"Identification Declined — Inconclusive Visual Match"* with an `"insufficient"` evidence tier, incorrectly implying the user's photograph lacked architectural details.
2. **Premature Failure on Transient Spikes:** The backend lacked bounded retry logic for transient errors, immediately failing on temporary upstream hiccups.
3. **Loss of User Context / Unfriendly Recovery:** The frontend lacked clear service unavailable messaging, forcing the user to re-upload or abandon their photograph rather than retrying.

This release implements a robust, safe transient-error recovery mechanism in `backend/gemini.py`, adds explicit status classification across `backend/heritage_service.py` and `backend/api.py`, and equips `frontend/app.js` with an isolated Service Unavailable card featuring state preservation and single-click retry.

---

## 2. Root Cause Analysis of HTTP 503

### Upstream Google Generative AI Behavior
- **Endpoint:** `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent`
- **Error Payload:**
  ```json
  {
    "error": {
      "code": 503,
      "message": "The model is overloaded. Please try again later.",
      "status": "UNAVAILABLE"
    }
  }
  ```
- **Origin:** The HTTP 503 originates from Google's regional load balancers and inference model routers when demand spikes exceed immediate TPU allocation. It is **not** an authentication error (HTTP 401/403), not a bad prompt request (HTTP 400), and **not** a billing/quota exhaust limit (HTTP 429).
- **Previous Defect:** In `backend/gemini.py`, all HTTP client errors and exceptions were lumped into generic fallback handling:
  ```python
  # Former code in backend/gemini.py
  except Exception as exc:
      logger.error("Gemini Vision request failed: %s", exc)
      return fallback_unknown_result("service_unavailable")
  ```
  While `service_unavailable` was passed as a category, downstream `_reconcile_fields` coerced unrecognized categories into `"generic_rock_cliff"` or `"architectural_facade"`, and confidence reconciliation forced `evidence_tier = "insufficient"`. The frontend displayed *"Identification Declined — Inconclusive Visual Match"*, confusing users into believing their authentic monument photo was defective or considered "generic rock".

---

## 3. Architecture & Implementation

### 3.1 Bounded Transient Retry with Jitter (`backend/gemini.py`)
To absorb brief upstream TPU router reconnections without causing request storms:
1. **Targeted Status Codes:** Only HTTP `502`, `503`, and `504` trigger automatic retry.
2. **Strict Retry Cap:** At most **ONE** automatic retry (`max_transient_retries = 1`, total attempts = 2).
3. **Exponential Backoff with Full Jitter:**
   $$\text{delay} = 1.0 \times 1.5^{\text{attempt}-1} + \text{random.uniform}(0.1, 0.4)$$
   - Attempt 1 failure $\to$ delay $\approx 1.10 - 1.40$ seconds.
4. **Overall Backend Deadline Enforcement:**
   - Every request checks against `overall_deadline = overall_start + self.timeout` (default 60.0s).
   - If `(overall_deadline - current_time) <= 0.5s`, the retry is immediately skipped to prevent exceeding client watchdogs.
5. **No Retry for Non-Transient Errors:**
   - `HTTP 429`: Mapped to `status="external_rate_limited"` and returned immediately without auto-retry.
   - `HTTP 400`: Mapped to `status="external_invalid_request"` and returned immediately.
   - `HTTP 401` / `403`: Mapped to `status="external_auth_error"` and returned immediately.
6. **Task Cancellation & In-Flight Tracking:**
   - Preserves `_in_flight` set integrity in `finally` blocks.
   - Accurately re-raises `asyncio.CancelledError` upon user abort or watchdog cancellation.

### 3.2 Secure Diagnostic Logging
- Logs exact response snippets truncated to a maximum of 200 characters.
- Query parameters, authorization headers, and API keys (`x-goog-api-key`) are strictly scrubbed/omitted.
- Elapsed time and attempt count are recorded in diagnostic logging for auditability.

### 3.3 Status Classification Contract
The pipeline introduces explicit `recognition_status` values across layers:

| Status Code | Meaning | `site_id` | `confirmed` | `evidence_tier` |
| :--- | :--- | :--- | :--- | :--- |
| `local_confirmed` | Local FAISS $\ge 0.85$, margin $\ge 0.10$ | `taj_mahal`, etc. | `true` | N/A |
| `external_match` | Gemini verified monument | canonical ID | `true` | `sufficient` |
| `inconclusive` | Genuine visual rejection / low evidence | `unknown` | `false` | `insufficient` |
| `external_service_unavailable` | Gemini 503/502/504 persisted after 1 retry | `unknown` | `false` | `unavailable` |
| `external_rate_limited` | Gemini HTTP 429 quota/rate limit | `unknown` | `false` | `rate_limited` |
| `external_timeout` | Gemini request timed out (> 60s) | `unknown` | `false` | `unavailable` |

`backend/heritage_service.py` preserves `site_id = "unknown"`, `confirmed = False`, and assigns `recognition_status = "external_service_unavailable"`. No fake confidence percentage or hallucinated monument names are emitted.

### 3.4 Frontend User Experience (`frontend/app.js`)
When `recognition_status === "external_service_unavailable"` or API returns HTTP 503:
1. **Dedicated Banner & Headline:**
   ```html
   <h2 class="result-monument-name">EXTERNAL IDENTIFICATION TEMPORARILY UNAVAILABLE</h2>
   ```
2. **Clear Explanation:**
   > *"The external recognition service is temporarily unavailable. Your photograph has been preserved. Please try again shortly."*
3. **State Preservation:**
   - The user's uploaded image file (`selectedFile`) and preview canvas are preserved intact.
   - No forced re-upload is required.
4. **Actionable Retry:**
   - A prominent `#retry-rec-btn` (`"Retry Recognition"`) is rendered directly inside the card.
   - Clicking retry immediately re-invokes `runRecognition()` using the stored image file.
5. **Accurate Metrics (No Misleading Data):**
   - Fake confidence percentage is hidden.
   - Misleading evidence tiers (`"insufficient"`, `"none"`) are omitted.
   - Shows diagnostic transparency: `Service Status: Temporarily Unavailable`, `Attempts: 2 (1 automatic retry)`.
6. **Separation from Inconclusive Results:**
   - Genuine non-heritage images (sandstone, rock, ordinary walls) continue to display `"IDENTIFICATION DECLINED — INCONCLUSIVE VISUAL MATCH"` with `"Evidence Tier: Insufficient"`.

---

## 4. Verification & Automated Test Results

A comprehensive automated test suite (`scripts/test_gemini_503_suite.py`) verified all requirements against simulated upstream states without making any live calls:

| Test Case | Scenario Description | Expected Outcome | Result |
| :---: | :--- | :--- | :---: |
| **1** | First attempt 503 $\to$ Second attempt 200 (Success) | 1 retry triggered with backoff; returns valid match | **PASS** |
| **2** | First attempt 503 $\to$ Second attempt 503 (Exhausted) | Exactly 2 attempts; returns `external_service_unavailable` | **PASS** |
| **3** | Non-503 Error: HTTP 429 Rate Limit | Exactly 1 attempt (0 retries); returns `external_rate_limited` | **PASS** |
| **4** | Non-503 Error: HTTP 400 Bad Request | Exactly 1 attempt (0 retries); returns `external_invalid_request` | **PASS** |
| **5** | Deadline Enforcement: Remaining Time < 0.5s | Immediate abort of retry; respects overall timeout | **PASS** |
| **6** | HeritageService Orchestration | Sets `recognition_status="external_service_unavailable"`, `site_id="unknown"` | **PASS** |
| **7** | Safe Logging Verification | Snippet logged, 0 API keys logged, timings recorded | **PASS** |
| **8** | Cancellation Cleanliness | `CancelledError` re-raised; in-flight tasks cleanly pruned | **PASS** |
| **9** | Frontend DOM: Dedicated Card & Headline | Renders `EXTERNAL IDENTIFICATION TEMPORARILY UNAVAILABLE` | **PASS** |
| **10** | Frontend DOM: Retry Button & Photo Intact | `#retry-rec-btn` visible; uploaded photo preserved in canvas | **PASS** |
| **11** | Frontend DOM: Zero Misleading Metrics | No fake confidence %; no `"insufficient"` tier on 503 | **PASS** |
| **12** | Contrast Check: Genuine Sandstone Rejection | Sandstone displays `"IDENTIFICATION DECLINED"`, not 503 | **PASS** |

**Summary: 12 / 12 test assertions PASSED (100.0%).**  
**Pytest Suite: 291 / 291 unit & integration tests PASSED (0 regressions).**

---

## 5. System Invariants Maintained

- **Model Configuration:** Preserved `gemini-3.1-flash-lite` and `MINIMAL` thinking level.
- **Local Catalogue:** Maintained 40 vectors, dimension 512, similarity threshold 0.85, competitor margin 0.10.
- **Zero Live Quota Consumed:** All tests executed with mock HTTP transports and `DISABLE_LIVE_GEMINI=1` protection.
- **Production Independence:** Zero dependencies on Ollama or local LLMs in production inference.
- **Frontend Watchdog Alignment:** Frontend watchdog remains at 75s, smoothly encompassing the 60s backend timeout and backoff delays.

---

## 6. Recommendations & Maintenance

1. **Production Alerting:** Monitor Prometheus/log aggregators for `external_service_unavailable` clusters exceeding 5 occurrences per minute, indicating broader Google Cloud regional incidents.
2. **Future Circuit Breaker:** If Google API experiences prolonged regional outages (> 15 consecutive minutes), consider a temporary 60-second circuit breaker to immediately fail fast without executing upstream calls.

