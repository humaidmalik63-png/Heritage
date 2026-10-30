# Phase 6P — Safe Candidate Index Builder

## Step 1 — Verify Current State

### 1.1 Verified Image Hash and Validation

| Property | Value |
|---|---|
| **Image path** | `data/raw/global/abu_simbel/Abu_Simbel_Temples.jpg` |
| **File exists** | ✅ Yes |
| **File size** | 3,526,382 bytes |
| **SHA-256 hash** | `2940d45d2fd0f09af7d40add21d105323e9ad5253cdcc3ebc5437ae9f27ed15b` |
| **Matches reported hash** | ✅ Yes (exact 64 hex chars, matches reported value) |
| **Format** | JPEG (binary header: `\xff\xd8` SOI marker confirmed) |
| **Duplicate check** | ✅ Not found among 12 existing images in `data/raw/global/` |
| **Abu Simbel in active mapping** | ❌ 0 entries (not indexed) |
| **Abu Simbel in manifest** | ❌ 0 entries (not in `global_image_manifest.json`) |

### 1.2 Current Active Index and Mapping

| Artifact | Path | Size (bytes) | SHA-256 Hash | Vector Count | Unique Site IDs |
|---|---|---|---|---|---|
| **FAISS index** | `data/processed/index/clip_index.faiss` | 55,341 | `f3de11a36ca9a10b33417cc26e9d9bd7b5786d798673bea63bd0138dd5ffa2c1` | 27 | 17 |
| **Mapping JSON** | `data/processed/index/mapping.json` | 3,558 | `08de12168ca8d6f7b86d64ae7a1b22a140123b003fad36cef3813adb4d985dcb` | 27 image_ids | 17 unique site_ids |

**Site IDs with vectors in current index** (with counts):
- adziubzha_church_georgia: 1, ajanta_caves: 3, akhutsa_fortress_abkhazia: 1, ambara_church_georgia: 1, anacopia_fortress_republic_of_: 1, aradu_church_abkhazia: 1, azanta_castle_georgia: 1, category_casbah_of_algiers_algeria: 1, cathedrale_notre_dame_de_l_immaculee_conception_in_porto_novo_benin: 1, fort_amsterdam_curacao: 1, jama_masjid_delhi: 1, konark_sun_temple: 3, queen_of_the_most_holy_rosary_cathedral_willemstad_kingdom_of_t: 1, qutub_minar: 3, red_fort_delhi: 3, svislac_castle_belarus: 1, taj_mahal: 3

**Abu Simbel**: Not in active index, not in mapping, not in manifest.

### 1.3 Manifest Schema

From `global_image_manifest.json`, each entry has these keys:

| Key | Type | Example Value |
|---|---|---|
| `site_id` | str | `"adziubzha_church_georgia"` |
| `name` | str | `"Adziubzha Church Georgia"` |
| `city` | str | `"Tbilisi"` |
| `country` | str | `"Georgia"` |
| `image_count` | int | `1` |
| `images` | list of dicts | (see below) |

**Image dict keys** (from first manifest entry):
- `image_id`: str (e.g., `"adziubzha_church_georgia_01"`)
- `local_path`: str (e.g., `"data/raw/global/adziubzha_church_georgia/File_3AAdzubja_church.jpg"`)
- `source`: str (e.g., `"Wikimedia Commons"`)
- `source_url`: str (e.g., `"https://commons.wikimedia.org/wiki/File%3AAdzubja_church.jpg"`)
- `commons_file_url`: str or None
- `author`: str (e.g., `"Surprizi"`)
- `license`: str (e.g., `"CC BY-SA 4.0"`)
- `license_url`: str or None
- `attribution`: str (e.g., `"Surprizi / CC BY-SA 4.0"`)
- `view_type`: str (e.g., `"other"`)
- `width`: int (e.g., `1040`)
- `height`: int (e.g., `584`)
- `downloaded`: bool (e.g., `True`)
- `file_size`: int (e.g., `61179`)
- `mime_type`: str (e.g., `"image/jpeg"`)
- `download_error`: str or None (e.g., `None`)
- `sha256`: str (e.g., `"9335b5b3b708d420bbf528ee5bab2f3a5afe2be80d2424a6dd5806aa5d3ec091"`)
- `width_local`: int (e.g., `1040`)
- `height_local`: int (e.g., `584`)

### 1.4 Existing Abu Simbel Metadata and Evidence

| Artifact | Status |
|---|---|
| **Catalogue** (`global_monument_catalogue.json`) | ✅ Present: site_id=`abu_simbel`, name=`Abu Simbel Temples`, complete record |
| **Metadata** (`heritage_metadata.json`) | ✅ Present: id=`abu_simbel`, name, country=Egypt, category=Temple, etc. |
| **Evidence** (`heritage_evidence.json`) | ✅ Present: 3 claims (description, historical significance, architectural features), all from UNESCO source |
| **Active FAISS index** | ✅ Present: 27 vectors, 17 unique sites, byte-for-byte preserved |
| **Active mapping** | ✅ Present: 27 image_ids → 27 paths → 27 site_ids, byte-for-byte preserved |

### 1.5 Image Already in Manifest or Mapping?

- **Manifest**: ❌ No entry for `site_id: abu_simbel` (manifest has 290 entries, Abu Simbel absent)
- **Mapping**: ❌ No entries with site_id containing "abu" (0 out of 27)
- **Active index**: ❌ No vectors for Abu Simbel (0 out of 27 total)

---

## Step 2 — Design Candidate-Only Output

### 2.1 How `build_worldwide_index.py` Writes Output

The script has **no CLI argument parser**. It writes to fixed, hardcoded paths defined at the top of the file (lines 35-36):

```python
OUTPUT_DIR = ROOT / "data" / "processed" / "index"
INDEX_PATH = OUTPUT_DIR / "clip_index.faiss"
MAPPING_PATH = OUTPUT_DIR / "mapping.json"
```

The `build_index()` function (line 157) always writes:
```python
faiss.write_index(index, str(INDEX_PATH))  # overwrites active index
```

And the mapping is always written (line 166-168):
```python
with open(MAPPING_PATH, "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=1)
    f.write("\n")
```

There is **no parameter** to control output paths. The script always overwrites the production index and mapping.

### 2.2 Smallest Safe Way to Support Candidate-Only Output

**Option A: Modify `build_worldwide_index.py` to accept optional output-path parameters**

The minimal change would be to add two optional parameters to `build_index()`:

```python
def build_index(index_output: Union[str, Path, None] = None,
                mapping_output: Union[str, Path, None] = None) -> None:
```

Inside the function, resolve the output paths:

```python
# Use provided paths or fall back to defaults
final_index_path = Path(index_output) if index_output else INDEX_PATH
final_mapping_path = Path(mapping_output) if mapping_output else MAPPING_PATH
```

Then use `final_index_path` and `final_mapping_path` instead of `INDEX_PATH` and `MAPPING_PATH` in the write calls.

**Files/functions that would change**:
- `backend/build_worldwide_index.py` — the `build_index()` function signature and 2 write calls

**Why this is the smallest change**:
- Only 1 function signature change
- Only 2 file path references need to be parameterized
- All existing logic (embedding extraction, index building, self-test) remains identical
- No changes to the script's CLI behavior when called without arguments (defaults preserve current behavior)

**Option B: Create a wrapper script**

Create a new script (e.g., `build_candidate_index.py`) that imports from `build_worldwide_index.py` and calls `build_index()` with custom output paths.

**Downside**: Creates new file, requires importing from another module; more complex than Option A.

**Option C: Use environment variables**

Add `INDEX_OUTPUT_PATH` and `MAPPING_OUTPUT_PATH` environment variable checks inside the function.

**Downside**: Less explicit; harder to test; not Python-idiomatic for this use case.

### 2.3 Proposed Candidate Output Directory

```
data/processed/index/candidate/
```

With files:
- `clip_index_candidate.faiss` — FAISS index with 28 vectors (27 original + 1 Abu Simbel)
- `mapping_candidate.json` — mapping with 28 entries including Abu Simbel

**Why this directory**: It's a sibling to the active `data/processed/index/` directory, keeping the active files completely untouched. The name `candidate` clearly signals this is a proposed index, not the production one.

### 2.3 Implementation Plan (if proceeding)

1. **Modify `backend/build_worldwide_index.py`**:
   - Add `index_output` and `mapping_output` optional parameters to `build_index()`
   - Use resolved paths instead of hardcoded `INDEX_PATH` and `MAPPING_PATH`

2. **Run the script with candidate paths**:
   ```bash
   python backend/build_worldwide_index.py \
     --index-output data/processed/index/candidate/clip_index_candidate.faiss \
     --mapping-output data/processed/index/candidate/mapping_candidate.json
   ```
   Or, after the code change, just:
   ```bash
   python backend/build_worldwide_index.py \
     data/processed/index/candidate/clip_index_candidate.faiss \
     data/processed/index/candidate/mapping_candidate.json
   ```

3. **Verify the candidate index**:
   - Check vector count: should be 28 (27 + 1 Abu Simbel)
   - Check Abu Simbel site_id appears in site_ids list
   - Verify SHA-256 hashes of candidate files differ from active files
   - Run test suite against candidate (if possible)

4. **Present candidate to user for approval**:
   - If approved, the candidate could be promoted to active by replacing the production files
   - If not approved, no production files were modified

### 2.4 What Was NOT Done (preservation rules)

- ❌ Did NOT modify `build_worldwide_index.py` (waiting for approval)
- ❌ Did NOT modify `global_image_manifest.json` (Abu Simbel entry not added yet)
- ❌ Did NOT modify the active FAISS index or mapping (preserved byte-for-byte)
- ❌ Did NOT modify catalogue, metadata, or evidence files
- ❌ Did NOT install Python packages or change environments
- ❌ Did NOT run the builder against production paths

---

## Step 3 — Check Runtime Dependencies

### 3.1 Python Environments

| Environment | Python Version | Packages Status |
|---|---|---|
| **System Python** | 3.15.0 | `faiss-cpu` unavailable; `numpy`, `torch`, `transformers`, `pytest`, `PIL` missing |
| **.venv** | 3.15.0 | Empty (no packages installed) |
| **.venv312** | 3.12.? | Exists but packages not verified |

### 3.2 Dependency Status

| Package | Availability | Notes |
|---|---|---|
| `faiss-cpu` | ❌ Not installable for Python 3.15 | pip: "No matching distribution found" |
| `numpy` | ❌ Not installed in venv | Required by faiss, torch, transformers |
| `torch` | ❌ Not installed | Required for CLIP model |
| `transformers` | ❌ Not installed | Required for CLIP |
| `PIL / Pillow` | ❌ Not installed | Required for image opening/validation |
| `pytest` | ❌ Not installed | Required for test suite |
| `faiss-cpu` (Python 3.12) | ✅ Likely available | Python 3.12 has pre-built wheels |

### 3.3 Safest Test Environment

**Use Python 3.12** via the existing `.venv312` directory or create a new one. This version has:
- Pre-built `faiss-cpu` wheels available
- Compatible `torch` and `transformers` packages
- Compatible `pytest` and `PIL`/`Pillow`

**Do not install packages in the current Python 3.15 environment** — `faiss-cpu` is unavailable, and installing mismatched packages could break the environment.

### 3.4 Recommended Next Steps (after approval)

1. **Switch to Python 3.12**: Activate `.venv312` or create a new Python 3.12 venv
2. **Install dependencies in order**:
   - `pip install numpy`
   - `pip install torch --index-url https://download.pytorch.org/whl/cpu`
   - `pip install transformers pillow faiss-cpu pytest`
3. **Verify**: `python -c "import faiss; import torch; import pytest; print('All imports OK')"`
4. **Run the candidate builder** with modified `build_worldwide_index.py`
5. **Run the test suite** to verify correctness

---

## Step 4 — Report and Wait for Approval

### 4.1 Verified Data Summary

| Item | Value |
|---|---|
| **Verified Abu Simbel SHA-256** | `2940d45d2fd0f09af7d40add21d105323e9ad5253cdcc3ebc5437ae9f27ed15b` |
| **Image confirmed** | JPEG, 3.5MB, no duplicates |
| **Active index hash** | `f3de11a36ca9a10b33417cc26e9d9bd7b5786d798673bea63bd0138dd5ffa2c1` |
| **Active mapping hash** | `08de12168ca8d6f7b86d64ae7a1b22a140123b003fad36cef3813adb4d985dcb` |
| **Active vector count** | 27 |
| **Active unique site count** | 17 |
| **Abu Simbel in manifest** | ❌ Absent (0 entries) |
| **Abu Simbel in mapping** | ❌ Absent (0 entries) |

### 4.2 Files That Need Changing

| File | Change | Impact |
|---|---|---|
| `backend/build_worldwide_index.py` | Add 2 optional parameters to `build_index()`: `index_output` and `mapping_output`; use resolved paths instead of hardcoded `INDEX_PATH` and `MAPPING_PATH` | Minimal change; defaults preserve current behavior; new paths enable candidate building |

### 4.3 Proposed Candidate Output Directory

```
data/processed/index/candidate/
  clip_index_candidate.faiss  (28 vectors: 27 original + 1 Abu Simbel)
  mapping_candidate.json      (28 entries including Abu Simbel)
```

### 4.4 Dependency and Test-Runtime Status

- **Python 3.15**: `faiss-cpu` unavailable; cannot run builder or tests
- **Python 3.12**: Recommended; `faiss-cpu` wheels available; all required packages installable
- **Test suite**: `pytest` + `faiss` + `torch` + `transformers` + `PIL` needed; last successfully verified on Python 3.12

### 4.5 Safe Implementation Plan

| Step | Action | File | Preservation |
|---|---|---|---|
| 1 | **Add optional output-path parameters** to `build_index()` in `backend/build_worldwide_index.py` | `backend/build_worldwide_index.py` | ✅ Defaults preserve current behavior; no production files touched until script is explicitly re-run |
| 2 | **Run builder with candidate paths** | `backend/build_worldwide_index.py` + `data/processed/index/candidate/` | ✅ Active index/mapping remain untouched; candidate files written to new directory |
| 3 | **Verify candidate index** | Inspect `clip_index_candidate.faiss` + `mapping_candidate.json` | ✅ No modification to active files |
| 4 | **Present candidate to user** | Report findings | ✅ User approves or rejects; if rejected, no changes needed |
| 5 | **If approved**: Replace active files with candidate | `data/processed/index/clip_index.faiss` + `mapping.json` | ⚠️ Only after explicit user approval; active files overwrite candidate |

---

**Stop here**: Waiting for user approval on the candidate index builder modification and the proposed `data/processed/index/candidate/` output directory. No project files have been modified beyond the temporary verification scripts (which can be cleaned up). The active FAISS index and mapping are byte-for-byte preserved in their original state.