# Mobile Camera Capture Fix Report

**Implementation Status:** Completed & Validated Locally  
**Target Devices:** Samsung Galaxy (Android Chrome) & Modern Mobile/Desktop Browsers  
**Files Modified:**
- `frontend/index.html` (Native camera input attribute fix & live modal controls)
- `frontend/app.js` (Dual capture logic, secure context detection, stream cleanup, flexible MIME handling)
- `frontend/styles.css` (Mobile-responsive camera modal layout and touch targets)
- Verification scripts: `scripts/test_frontend_camera.py`, `scripts/check_console_errors.py`

---

## 1. Problem Diagnosis

Testing on mobile devices (specifically Samsung Android Chrome) revealed four critical blockers in the previous implementation:

1. **Android Intent Filter Block on Specific MIME Types:**
   In `frontend/index.html`, the camera input was configured as:
   ```html
   <input type="file" id="camera-input" accept="image/jpeg,image/jpg,image/png,image/webp" capture="environment">
   ```
   On Samsung Chrome and Android Chromium, listing comma-separated specific MIME types causes the Android Intent system to treat the input as a generic file document picker. Consequently, Android Chrome opens the "Files / Downloads" system dialog instead of directly launching the Samsung Camera hardware.
2. **Hardcoded Mobile Bypass of Live Viewfinder:**
   `frontend/app.js` contained an unconditional `if (isMobile) { cameraInput.click(); return; }` branch. This prevented mobile devices from using the direct browser camera stream (Method B) even when `navigator.mediaDevices.getUserMedia` was fully supported and permitted.
3. **Strict MIME Rejection on Samsung Camera Photos:**
   Samsung Android cameras frequently pass photo files with an empty `file.type` (`""`) or `image/pjpeg` when returning from intent capture. The existing `acceptFile` function strictly checked `if (ACCEPTED.indexOf(file.type) < 0)`, which rejected genuine photos as `"Unsupported file type"`.
4. **Missing Mobile Viewport Layout in CSS:**
   The `.modal-card--camera` and `.modal-foot--camera` lacked responsive media queries for narrow viewports ($\le 640\text{px}$), resulting in awkward button stacking and sub-44px touch targets on mobile screens.

---

## 2. Technical Implementation Details

We implemented a robust **Dual-Capture Architecture**:

```
[User Taps "Take Photo"]
           │
           ▼
 Is window.isSecureContext &&
 navigator.mediaDevices.getUserMedia available?
      ├── YES ──► Launch Method B: Direct Live Camera Viewfinder Modal
      │                │
      │                ├── [User clicks "Capture Photo"] ──► Draw video frame to Canvas
      │                │                                         │
      │                │                                         ▼
      │                │                                     toBlob(JPEG) ──► File Object ──► acceptFile(file)
      │                │                                                                          │
      │                ├── [User clicks "System Camera"] ─┐                                      ▼
      │                │                                  │                                  Downscale ──► Preview
      │                ├── [Camera Permission Denied] ────┼──► Close modal & stop tracks         │
      │                └── [OverconstrainedError] ────────┘         │                             ▼
      │                                                             ▼                       Execute Recognition
      └── NO (or on fallback) ──────────────► Launch Method A: Native Camera File Input
                                                  <input type="file" accept="image/*" capture="environment">
```

### Method A: Native Mobile Camera
- Updated `frontend/index.html`:
  ```html
  <input type="file" id="camera-input" class="visually-hidden"
         accept="image/*" capture="environment" />
  ```
  Using `accept="image/*"` with `capture="environment"` complies strictly with the HTML5 Media Capture specification and guarantees that Samsung Chrome opens the native Samsung Camera app with the rear-facing sensor activated.
- In `frontend/app.js`:
  Enhanced `acceptFile(file, isCamera)` to accept files where `file.type` is empty or generic if the filename extension matches `\.(jpe?g|png|webp)$`.

### Method B: Direct Browser Live Viewfinder (`getUserMedia`)
- Implemented in `openCameraModal()`:
  - Requests `{ video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } } }`.
  - Catches `OverconstrainedError` and automatically retries with `{ video: { facingMode: { ideal: 'environment' } } }` for compatibility with older camera sensors.
  - Added `#camera-fallback-btn` ("System Camera") inside the viewfinder modal, allowing mobile users to switch immediately to Samsung's native camera app if they prefer hardware zoom, optical lenses, or HDR.
  - Video stream capture converts the frame via `<canvas>` into a standard JPEG `File` object (`monument-camera-TIMESTAMP.jpg`) and routes it through the unified `acceptFile()` pipeline.
- **Hardware Lifecycle & Privacy Cleanup:**
  - `closeCameraModal()` iterates over `activeMediaStream.getTracks()` and executes `track.stop()`.
  - Invoked immediately upon photo capture, modal cancel, backdrop click, or ESC key.
  - Guarantees the browser/hardware green camera indicator turns off immediately and no background camera drain occurs.

### Unified Preview & Control Workflow
- **Retake Photo:** `#retake-btn` triggers `triggerCameraCapture()`, letting users retake the photo using either live stream or native camera.
- **Replace Photo:** `#replace-btn` triggers `fileInput.click()`, allowing gallery selection.
- **Remove Photo:** `#remove-btn` invokes `clearSelection()`, clearing preview and resetting the pipeline.
- **Pipeline Preservation:** The captured image flows through the identical `downscale()` and `POST /recognize` recognition pipeline. No separate recognition logic was created.

---

## 3. Styling & Responsive Design

Updated `frontend/styles.css`:
- **Dark Architectural Theme:** Consistent with the Heritage platform's bronze/gold accents (`var(--accent)`), hairline borders, and semi-transparent dark backdrops (`rgba(13, 16, 23, 0.98)`).
- **Responsive Media Query ($\le 640\text{px}$):**
  - Modal card width set to `95vw` with centered positioning.
  - Action buttons set to minimum height `44px` for ergonomic touch targets on Samsung mobile screens.
  - Viewfinder maintains responsive `aspect-ratio: 4 / 3` with `max-height: 55vh`.
  - Actions adapt with `flex-direction: column-reverse` and `flex-wrap: wrap`.

---

## 4. Verification & Testing Results

| Test Scenario | Verification Method | Result | Notes |
| :--- | :--- | :---: | :--- |
| **DOM Element Inspection** | `scripts/test_frontend_camera.py` | **PASS** | `camera-input` has `accept="image/*"` and `capture="environment"`. |
| **Viewfinder Controls** | `scripts/test_frontend_camera.py` | **PASS** | Snap button, cancel button, and system camera fallback button verified. |
| **Chrome Headless DOM Dump** | `chrome --headless=new --dump-dom` | **PASS** | Complete HTML rendering verified on live server `http://127.0.0.1:8080`. |
| **Chrome Console Error Audit** | `scripts/check_console_errors.py` | **PASS** | **0 errors** reported during full script evaluation and execution. |
| **Stream Hardware Cleanup** | Unit & DOM trace | **PASS** | `track.stop()` called on all active tracks; `srcObject` nulled. |
| **Flexible MIME Acceptance** | Unit test | **PASS** | Photos with empty MIME type or `image/pjpeg` from Android cameras successfully processed. |
| **Retake / Replace / Remove** | Event listener audit | **PASS** | Retake re-opens camera; Replace opens gallery; Remove resets preview. |
| **Recognition Execution** | `test_recognition_suite.py` | **PASS** | Captured image payload successfully accepted by backend FAISS + CLIP pipeline. |

---

## 5. Browser Environment & Secure Context Guidance

- **Secure Context Requirement:** In accordance with W3C web security standards, `navigator.mediaDevices.getUserMedia` requires a **secure context** (`https://` or `http://127.0.0.1:*` / `http://localhost:*`).
- **Behavior over HTTP on LAN / Wi-Fi IP:** If the site is accessed via an unencrypted local IP (e.g. `http://192.168.x.x`), Chrome disables `getUserMedia`. The application now detects this automatically via `window.isSecureContext` and seamlessly launches **Method A** (`cameraInput` native camera capture), ensuring zero disruption for the user.
- **Production HTTPS:** When deployed over HTTPS (or Cloudflare tunnel), both Method A and Method B function at full fidelity.
