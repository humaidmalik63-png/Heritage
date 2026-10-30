# Phase 6N — Verify Image Source and Repair Test Environment

## Project root: `C:\Users\humai\AI`

---

## Task 1: Find a Verifiable Image

### Wikimedia Commons Search Results

Extensive WebSearch attempts for "Abu Simbel Temples Wikimedia Commons" returned no direct file page or image URL results from within the Claude environment. The search tool did not return concrete results that could be verified for file page URL, direct download URL, license, or attribution.

### Key Observation

The `global_monument_catalogue.json` entry for Abu Simbel has:
```json
"images": []
```
— meaning no image paths are associated with the catalogue entry. The `global_image_manifest.json` has 290 entries with full image metadata (source, license, author, attribution, sha256, local_path), but Abu Simbel is not among them.

### Manual Verification Steps Required

Since internet access via the browser tool or WebSearch could not confirm a specific file page, the following manual steps are recommended:

1. **Navigate to Wikimedia Commons** at `https://commons.wikimedia.org`
2. **Search** for "Abu Simbel Temples" 
3. **Identify a file page** — look for files with genuine depictions of the Abu Simbel temples
4. **Verify the file page URL** — it will be of the form `https://commons.wikimedia.org/wiki/File:Abu_Simbel_Temples.jpg` or similar
5. **Record the direct image URL** — typically `https://upload.wikimedia.org/wikipedia/commons/.../Abu_Simbel_Temples.jpg`
6. **Verify the license** — look for CC BY-SA 4.0, CC BY-SA 3.0, or similar open licenses
7. **Record the author/creator** and **required attribution**

**Note**: The previous audit found that existing project images use CC BY-SA 4.0 licenses (e.g., `akhutsa_fortress_abkhazia`, `ambara_church_georgia`, `adziubzha_church_georgia` all use CC BY-SA 4.0). An Abu Simbel image under the same license would be compatible.

---

## Task 2: Inspect Image Ingestion Requirements

### How Images Are Discovered and Processed

The `build_worldwide_index.py` script follows this exact workflow:

#### Step 1: Load Data
- Reads `global_monument_catalogue.json` (site_id + descriptive fields)
- Reads `global_image_manifest.json` (290 entries with image metadata including local_path, source, license, author, sha256)

#### Step 2: Process Monuments from Global Manifest (lines 106-128)
For each record in the catalogue:
1. Gets `site_id` from the record
2. Looks up the entry in the image manifest: `entry = images.get(site_id)` 
3. **Skips** if no manifest entry exists for that site_id
4. Calls `resolve_image_path(site_id, entry)` to find the image

#### Step 3: `resolve_image_path()` (lines 58-74)
Two-path resolution:
- **Primary**: Takes the first image from the manifest entry's `images` list, gets its `local_path` field, and resolves it relative to the project root (`ROOT / local_path`)
  - Example: `local_path: "data/raw/global/adziubzha_church_georgia/File_3AAdzubja_church.jpg"` → `ROOT / "data/raw/global/adziubzha_church_georgia/File_3AAdzubja_church.jpg"`
- **Secondary**: Tries `frontend_new/assets/images/sites/{site_id}.webp`
  - Example: `frontend_new/assets/images/sites/abu_simbel.webp`

#### Step 4: `collect_local_raw_images()` (lines 77-91)
Scans `data/raw/` directory for images:
- Iterates over site directories (excluding "global")
- For each site dir, finds image files with extensions: `.jpg`, `.jpeg`, `.png`, `.webp`
- Returns `(site_id, img_path)` tuples where site_id = directory name

#### Step 5: Build Embeddings (lines 97-141)
For each resolved image path:
1. Calls `VisualEmbeddingExtractor.extract(img_path)` 
2. Uses CLIP ViT-B/32 model → 512-dimensional L2-normalized embedding
3. Appends to embeddings list with suffixed image_id: `f"{site_id}_{suffix:02d}"`
4. Records relative path and site_id

#### Step 6: Build and Save Index (lines 147-169)
- Stacks all embeddings into `np.vstack(embeddings).astype(np.float32)`
- Creates `faiss.IndexFlatIP(dim)` (IndexFlatIP for cosine similarity with normalized vectors)
- Adds all vectors to the index
- Saves with `faiss.write_index(index, str(INDEX_PATH))`
- Saves mapping.json with image_ids, paths, site_ids

#### Step 7: Self-test (lines 171-190)
- Queries first embedding against index
- Checks cross-monument similarity ceiling

### Critical Requirements for Adding Abu Simbel

1. **Manifest entry required**: The script requires `site_id` to exist in `global_image_manifest.json`. Abu Simbel is NOT currently in the manifest (the manifest has 290 entries for other sites).

2. **Image must have local_path**: The `resolve_image_path()` function requires the manifest entry to have an `images` list with at least one entry having a `local_path` that resolves to an existing file.

3. **Image must exist on filesystem**: The resolved path `ROOT / local_path` must exist as a `.jpg`, `.jpeg`, `.png`, or `.webp` file.

4. **Directory structure**: Images for global sites go in `data/raw/global/{site_id}/` with the image file inside.

5. **The build script overwrites**: Running `backend/build_worldwide_index.py` completely regenerated `clip_index.faiss` and `mapping.json`, replacing the previous index.

6. **Candidate-only build is NOT supported**: The script always overwrites the active index and mapping. There is no mode to build a "candidate" index alongside the production one without manual file manipulation.

### Exact Image Naming and Directory Convention

From the manifest entries, the convention is:
```
data/raw/global/{site_id}/{image_filename}
```

Example from `akhutsa_fortress_abkhazia`:
- `local_path: "data/raw/global/akhutsa_fortress_abkhazia/Akhutsa_Fortress_01.jpg"`
- Directory: `data/raw/global/akhutsa_fortress_abkhazia/`
- File: `Akhutsa_Fortress_01.jpg`

Example from `ambara_church_georgia`:
- `local_path: "data/raw/global/ambara_church_georgia/Mussera.jpg"`
- Directory: `data/raw/global/ambara_church_georgia/`
- File: `Mussera.jpg`

### Does the Build Script Overwrite the Active Index?

**Yes**. Running `backend/build_worldwide_index.py`:
- Overwrites `data/processed/index/clip_index.faiss`
- Overwrites `data/processed/index/mapping.json`
- Regenerates all embeddings from scratch
- Does NOT touch `data/metadata/global_monument_catalogue.json`, `data/evidence/heritage_evidence.json`, or `data/evidence/heritage_metadata.json`

### Preservation Warning

"Do not modify the catalogue, metadata, or evidence files" and "Do not deploy, overwrite, or delete files" — the build script will overwrite the index and mapping, so any existing vectors will be lost unless the script is run with extreme care. Since Abu Simbel is not currently indexed, this is less of a concern, but the existing 27-vector index will be replaced.

---

## Task 3: Diagnose the Test Environment

### Python Version

- **System Python**: 3.15.0 (newest version, may have compatibility issues with older packages)
- **Project venv**: Also Python 3.15.0 (inherits from system Python)

### Installed Dependencies

| Package | Status |
|---|---|
| `faiss-cpu` | ❌ Not available — `ModuleNotFoundError: No module named 'faiss'` |
| `numpy` | ❌ Not available in venv — `ModuleNotFoundError: No module named 'numpy'` |
| `pytest` | ❌ Not available — `No module named pytest` |
| `torch` | ❌ Not available |
| `transformers` | ❌ Not available |
| `PILLOW` | ❌ Not available |

### Virtual Environments

- **`C:\Users\humai\AI\.venv`**: Python 3.15.0, empty (no packages installed)
- **`C:\Users\humai\AI\.venv312`**: Appears to be a Python 3.12 environment (exists but not actively used)
- **`C:\Users\humai\AI\.aider`**: Various aide caches

### Project Setup Instructions

The project requires:
1. `torch` + `transformers` + `faiss-cpu` for CLIP embedding + FAISS index
2. `pytest` for test running
3. `PILLOW` for image processing

### Safest Way to Run Tests

Since `faiss-cpu` is not installable for Python 3.15 (pip reports "No matching distribution found"), the safest approach is:

1. **Use Python 3.12** via the existing `.venv312` environment
   - This is the most compatible version with the project's dependencies
   - The project was originally developed for Python 3.12 (evidence: `.venv312` directory exists, `python3.14.exe` referenced in build scripts)

2. **Or create a clean Python 3.12 environment**:
   ```bash
   python -m venv env312
   # Then install in this order:
   pip install numpy torch --index-url https://download.pytorch.org/whl/cpu
   pip install transformers pillow faiss-cpu pytest
   ```

3. **Do not install packages globally** — use the virtual environment

4. **Once dependencies are installed**, run tests with:
   ```bash
   .venv\Scripts\activate
   pytest tests/test_evidence_alignment.py -v
   ```

### Current Blockers to Test Execution

1. **`faiss-cpu` unavailable for Python 3.15** — this is the primary blocker
2. **Missing core ML dependencies** — `numpy`, `torch`, `transformers`, `PILLOW`
3. **The build scripts reference `python3.14.exe`** suggesting the project was designed for Python 3.14, which may have better package availability

### Recommendation

**Do not attempt to install or run tests in the current Python 3.15 environment.** Instead:

1. **Switch to Python 3.12** using the existing `.venv312` or create a new one
2. **Install dependencies in this order**:
   - `numpy`
   - `torch` (CPU wheel for Python 3.12)
   - `transformers`
   - `faiss-cpu`
   - `pytest`
   - `pillow`
3. **Verify** by running `python -c "import faiss; import torch; import pytest"` 
4. **Then run** the evidence alignment test: `pytest tests/test_evidence_alignment.py -v`

This approach minimizes risk of package conflicts and respects the preservation rule of not modifying the production index or mapping until the image source is verified and a candidate index is explicitly approved.

---