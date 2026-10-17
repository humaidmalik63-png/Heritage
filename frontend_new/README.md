# Heritage Discovery — Heritage Frontend (Vanilla)

A standalone, cinematic single-page frontend for the Heritage Discovery
recognition service. Pure HTML, CSS and vanilla JavaScript — no React, no
Next.js, no Tailwind, no Bootstrap, no CDN, no external runtime JavaScript.

This folder is **self-contained and isolated**. It reads the existing FastAPI
backend for recognition and a local copy of the monument catalogue for
browsing. It does not modify the backend, the ML code, the existing frontend,
or any data file.

---

## 1. Running it

### Backend (must be running first)

```bash
cd C:\Users\humai\AI
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd C:\Users\humai\AI\frontend_new
python -m http.server 8080
```

Then open:

```
http://localhost:8080
```

> Serve it over HTTP. Opening `index.html` directly as a `file://` URL blocks
> the catalogue fetch and the recognition call in some browsers.

### If port 8080 is already in use

`backend/api.py` only allows the CORS origins `http://localhost:3000`,
`http://localhost:3001` and `http://localhost:8080`, and it must **not** be
edited to add another. Use one of those three ports.

To find out what holds 8080:

```bash
netstat -ano | findstr :8080
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"ProcessId=<PID>\" | Select-Object ProcessId,CommandLine | Format-List"
```

If the listener is an unrelated application, stop it first (verify the command
line is what you expect before stopping anything).

### Where the frontend calls the backend

The API base URL is resolved in `app.js` (`API_BASE`) as
`http://<current-hostname>:8000`. That matches the CORS origins already
configured in `backend/api.py` for `localhost:8080`. If you serve this
frontend on a port that is **not** listed there, the browser will block the
request — use port 8080.

The browser never talks to Ollama directly and no API key is ever present in
this frontend. The full path stays:

```
Browser → FastAPI → CLIP + FAISS → open-set decision → Ollama fallback → response → Browser
```

---

## 2. Files

| Path | Purpose |
| --- | --- |
| `index.html` | Single page; all five views are sections swapped by JS. |
| `styles.css` | Design system: tokens, chamfered frame, glass surfaces, responsive rules, reduced-motion. |
| `app.js` | Router, upload, recognition rendering, explorer, detail view, parallax. |
| `assets/images/hero.webp` | Full-screen hero background. |
| `assets/images/sites/*.webp` | Per-site thumbnails for monuments with local photographs. |
| `assets/images/gallery/<site_id>/*.webp` | Hero + thumbnail derivatives of the real photographs in `data/raw/`. **Generated** — see §4. |
| `assets/data/gallery.json` | Manifest of the gallery images that actually exist. **Generated** — see §4. |
| `assets/data/global_monument_catalogue.json` | Bundled copy of the catalogue (see §5). |
| `scripts/prepare_gallery.py` | Builds the gallery assets from `data/raw/`. Read-only on the source photos. |
| `assets/fonts/` | Empty by design — the type stack is system-resident (see §6). |

---

## 3. Backend contract used

Derived from `backend/api.py`, `backend/heritage_service.py` and
`backend/ollama.py`. No endpoint or field is invented.

**`GET /health`** → `{ status, service_ready, index_size, default_top_k, similarity_threshold }`

**`POST /recognize`**

```jsonc
{
  "image_base64": "data:image/jpeg;base64,…",  // or image_path
  "question": "",
  "top_k": 5
}
```

Response fields consumed: `site_id`, `confidence`, `confirmed`,
`recognition_source`, `global_identification`, `metadata`, `evidence`,
`answer`, `citations`, `reason`, `is_grounded`.

`confidence` is rendered **exactly as the API returns it**, and only when it
is present:

| API value | Rendered |
| --- | --- |
| `0.923` | `92.3%` |
| `0.684` | `68.4%` |
| `0.41` | `41%` |
| `0.9` | `90%` |
| `null` | the confidence block is **not rendered at all** |

There is no fallback value. A successful identification is never shown as
`100%`, a qualitative status is never converted into a percentage, and a
missing number is never invented.

### Fields deliberately NOT rendered

The API also returns `similarity`, `decision`, `top_k` and `matches[]`
(`{image_id, site_id, similarity}`). These are **internal diagnostics** — the
CLIP cosine, the open-set decision code and the rejected nearest-neighbour
list — and none of them appear anywhere in the rendered result. No
`LOCAL INDEX` block, no candidate IDs such as `taj_mahal_01`, no raw cosine
values, and no open-set status codes. The `reason` code is translated to a
sentence before display (`low_similarity` → *"No indexed image was similar
enough to accept."*).

### Result states rendered

| `recognition_source` | Shown as |
| --- | --- |
| `local` | **IDENTIFIED** + monument name, location, backend metadata, evidence claims, real citations, and the heritage gallery. |
| `ollama` | **IDENTIFIED** with the banner *IDENTIFIED THROUGH GLOBAL VISION* + `global_identification` fields only. |
| `unknown` | **IDENTIFICATION NOT CONFIRMED** + the reason. No monument, location, confidence or gallery is shown. |

Any field the API does not return is **hidden**, never filled in with a
placeholder. A global-vision result is never given an external citation: when
the backend returns no URL, the sources block reads
*GLOBAL VISION IDENTIFICATION*.

---

## 4. Heritage gallery

The recognition result opens with a gallery of the monument's **real
photographs** — the same images the FAISS index was built from, in
`data/raw/<site>/`.

```bash
cd C:\Users\humai\AI
C:/Users/humai/AppData/Local/Python/bin/python frontend_new/scripts/prepare_gallery.py
```

The script reads **only** `data/raw/` and writes **only** into
`frontend_new/assets/`; no source photograph is modified. It emits a hero and a
thumbnail WebP per photograph plus `assets/data/gallery.json`, which lists
exactly the files that exist.

The project holds **at most three photographs per monument**, so the gallery
shows three frames, not five — the five-image target is a ceiling, and the
shortfall is reported rather than padded with unrelated or fabricated images.
A monument with one photograph gets one frame.

The manifest is joined on `site_id` for a local match. A global-vision result
carries `site_id: "unknown"` by design, so it is joined by an **exact**
catalogue name match, plus the small hand-verified alias table in
`matchCatalogueSite()`. An unmatched name renders no gallery rather than
guessing at a monument.

Desktop shows one large hero with the remaining frames as a shallow 3D fan
below it; clicking one promotes it to the hero. At ≤700 px the gallery becomes
a single-frame swipe carousel with pagination dots that follow the scroll
position.

---

## 5. Catalogue loading

The explorer tries, in order:

1. `../data/metadata/global_monument_catalogue.json` — the real file, used
   when the server root is the project folder.
2. `assets/data/global_monument_catalogue.json` — a bundled copy, so the
   prototype also works when served from this folder alone.

The bundled copy is a **read-only duplicate**. The original at
`data/metadata/global_monument_catalogue.json` is never written to. If the
catalogue changes, refresh the copy:

```bash
cp C:\Users\humai\AI\data\metadata\global_monument_catalogue.json \
   C:\Users\humai\AI\frontend_new\assets\data\global_monument_catalogue.json
```

No backend endpoint was added for this.

---

## 6. Typeface

`Inter` (or the system UI sans) for body copy, and a geometric condensed stack
for labels: `Chakra Petch → Bahnschrift → DIN Condensed → Arial Narrow`.

No font is fetched at runtime and none is bundled — the project ships no
self-hosted font files outside `node_modules`, and loading from a CDN is not
permitted. On Windows, `Bahnschrift` provides the condensed label face.

---

## 7. Accessibility & motion

- Semantic landmarks, real `<button>` elements for every action, one `<h1>`.
- `aria-live="polite"` on the recognition result region and status line.
- `aria-expanded` / `aria-controls` on the menu button, Escape to close,
  click-outside to close, and a Tab loop inside the open panel.
- Visible focus rings everywhere; the upload zone is keyboard operable.
- Decorative images use `alt=""`; meaningful ones are described.
- `prefers-reduced-motion: reduce` disables the parallax, the reveal
  animations and all transitions.
- Pointer parallax runs only for a fine pointer (`hover: hover`,
  `pointer: fine`) and is never attached on touch devices.

---

## 8. Verified behaviour

Tested in Chromium at 1440×900, 1280×800, 1024×768, 768×1024, 548×800,
375×812 and 320×640:

- Home, chapter rail (6 chapters), navigation and mobile glass menu.
- Recognition: upload, preview, replace, remove, and live results for all
  three `recognition_source` states.
- Explorer: search across name/city/country/type, region + country + type
  filters, reset, and incremental loading.
- Monument detail and **Back to Heritage**.
- About, architecture diagram and live health values.
- Reduced motion and keyboard-only navigation.
- No horizontal scrolling at any tested width.