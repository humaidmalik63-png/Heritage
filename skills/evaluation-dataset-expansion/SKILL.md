# Skill: evaluation-dataset-expansion
# Use when expanding the evaluation dataset across P0-P2 priority categories
# <one-line behavior>: Build, validate, and document a prioritized evaluation dataset batch with verified provenance, lineage, and integrity checks.

## Purpose
Build a larger, better-balanced evaluation dataset to diagnose known-site rejection, confusing monument rankings, and unknown-site false acceptance. Keep new data and reports in a separate `data/evaluation/phase8a/` directory. Record SHA-256 hashes and sizes for the four protected artifacts before and after the task. Do not change production thresholds, modify the active index, deploy, or promote any experimental result.

## Always-On Rules
1. **Never overwrite, rebuild, replace, rename, or promote the active production index or mapping.** The existing builder may write directly to production; verify hashes before any operation.
2. **Do not call `build_index()` with default arguments.** The existing builder may write directly to production.
3. **Do not change production thresholds, production configuration, or deployment settings.**
4. **Work only in source code, tests, and isolated evaluation outputs.** Put generated artifacts under a new Phase 8A evaluation directory.
5. **Before any operation that might touch existing artifacts, record their SHA-256 hashes and sizes. Verify them again at the end.**
6. **Use the existing Python 3.12 environment:** `C:\Users\humai\AI\.venv312\Scripts\python.exe`. Do not use Python 3.14 or assume a different environment.
7. **Do not download images or change the existing evaluation dataset unless necessary and explicitly justified.**
8. **Do not invent test results, image labels, citations, provenance, or accuracy claims.**
9. **Do not mark unreviewed images as visually verified.** Unknown-image manual review remains pending until actually completed.
10. **Do not deploy, commit, or promote changes automatically.**
11. **If an operation could damage production data or cannot be performed safely, skip it and report why.**
12. **Inspect the repository's actual code before editing.** Do not assume previous reports accurately describe every implementation detail.

## Procedure (in order)

### Step 1 — Audit existing dataset
- Inspect `data/evaluation/phase7p/` (known images) and `data/evaluation/phase7u_unknown/` (unknown images)
- Inspect `data/processed/index/candidate/phase6ab_validation_mapping.json` and the candidate validation index
- Produce a manifest containing: image path, expected label, known/unknown status, dimensions, file type, file hash, mapped site ID if applicable, provenance/review status
- Check for exact duplicates and perceptual duplicates (do not install packages)
- Identify label mismatches, repeated viewpoints, missing sites, and images that cannot be confidently labelled
- Mark uncertain cases for human review rather than guessing
- Record SHA-256 hashes for all 4 protected artifacts before starting

### Step 2 — Identify missing coverage
- Use the actual candidate mapping to identify which indexed sites have too few independent evaluation images
- Prioritize evaluation needs:
  - Multiple independent views of each known monument
  - Different angles, distances, lighting, weather, and image quality
  - Visually similar monuments that may be confused with one another
  - Unknown monuments resembling existing indexed sites
  - Non-monument buildings, landscapes, indoor scenes, and unrelated photographs
  - Ambiguous or partially obscured images
- Keep evaluation images separate from gallery/index images. Do not put an evaluation image into the gallery used to evaluate that same image.
- Flag likely leakage or shared near-duplicates for review
- Produce a ranked acquisition checklist that identifies the missing examples and explains why each category matters

### Step 3 — Plan the expansion
- Inspect `data/evaluation/phase7y/phase7Y_final_report.md` and `data/evaluation/phase7y/dataset_manifest.json`
- Use the existing acquisition checklist to create a prioritized plan covering:
  - P0: Multiple independent views of known monuments (Qutub Minar, Konark Sun Temple, Red Fort Delhi)
  - P1: Additional views of unknown sites; monuments visually similar to existing gallery sites
  - P2: Non-monument scenes, ambiguous/occluded images, cross-site confusion pairs
- Separate gallery images from evaluation images. Avoid near-duplicate leakage
- **P0 approval**: Operator must manually approve and collect images (this environment cannot browse the web or download files autonomously)

### Step 4 — Provenance and collection
- First identify which additional examples are needed and which existing sources can be verified
- **Do not download anything until the plan identifies the target image, intended label, source page, direct image URL, license, creator attribution when available, and the reason the example is needed**
- Prefer reputable sources with verifiable licensing and metadata (CC0, CC BY, CC BY-SA)
- If source details are unavailable or uncertain, flag them rather than guessing
- If this environment cannot reliably retrieve and validate source images, prepare a candidate-source manifest and clearly report the blocked step. Never claim that an image was downloaded or visually reviewed when it was not.
- Store new files only under: `data/evaluation/phase8a/`
- Keep a manifest recording: relative path, expected site ID or unknown label, source page and direct image URL, license and creator attribution status, image dimensions and format, SHA-256 hash, exact-duplicate and perceptual-duplicate checks (where supported), human review status, whether the image is excluded from gallery/indexing

### Step 5 — Evaluation integrity
- **Do not use the expanded dataset to tune thresholds on the same examples later reported as an unbiased test set**
- Recommend separate development/calibration and held-out evaluation partitions grouped by source image or near-duplicate family
- **Do not claim production accuracy or reliable generalization from a small sample**

### Step 6 — Integrity verification
- Verify the following protected artifacts remain byte-identical:
  - `data/processed/index/clip_index.faiss`
  - `data/processed/index/mapping.json`
  - `data/processed/index/candidate/phase6ab_validation.faiss`
  - `data/processed/index/candidate/phase6ab_validation_mapping.json`
- Expected hashes:
  - `de32d554375c58c6cf6befc0c8cdf1268934e8814e48d53e4486d437e58caaa6`
  - `dbb135ff693ffcadab0ba701cf643854e1ece1baf19552083c0d1cb901ecd51c`
  - `4596388e8ae8dfd589ad49f9a85e23f78d332753fd58ed6fb43364b15dc14d98`
  - `e25616c809ce118bc3d593e100e1d51ba291635455c27d0cc6db10e9ddc5fdf7`
- If a hash differs from the expected baseline, stop risky operations immediately and report the discrepancy

### Step 7 — Final report
Report what was actually inspected, files created, commands run, results, unresolved issues, and all four before/after hashes and sizes.

End with a clear status: PASS, PARTIAL, or BLOCKED.

Do not change thresholds, rebuild indexes, deploy, or promote any experimental result.

## P0 Acquisition Workflow (Batched and Verifiable)

### Approval Required
Operator must manually approve the P0 batch before collection begins. This approval covers research and preparation of a small P0 batch only. It does not authorize production index changes, threshold changes, deployment, or automatic promotion of images into the gallery.

### Candidate Research (per monument)
1. Search Wikimedia Commons for the target monument
2. Select images with accessible source pages and clearly documented licenses (CC0, CC BY, or CC BY-SA)
3. For each candidate, record:
   - Monument and proposed canonical site ID
   - Wikimedia Commons source-page URL
   - Direct original-image URL
   - Exact license and version
   - Creator/author attribution as stated by the source
   - Any required attribution or share-alike conditions
   - Image dimensions and format when available
   - Why the image adds a different viewpoint or visual condition
   - Whether it may duplicate an existing evaluation or gallery image
   - Verification status and unresolved concerns
4. **Do not infer the photographer from EXIF camera models.** Do not treat a search snippet or filename as sufficient license verification.
5. If reliable source research or downloading is unavailable, prepare a candidate-source manifest and clearly report the blocked step. Never claim that an image was downloaded or visually reviewed when it was not.

### Download and Verification
1. Download only candidates whose source, license, and direct image URL are sufficiently verified
2. Store downloads under `data/evaluation/phase8a/` in a dedicated P0 subdirectory. Do not overwrite existing files.
3. After downloading, verify file type, dimensions, SHA-256, and exact duplicates
4. Use an existing perceptual-hash tool if available; do not install packages without approval
5. Record potential near-duplicates for human review
6. **Keep every new image excluded from gallery/index construction.** Mark human review as PENDING until an operator actually inspects the image.

### Post-Collection
1. Update the Phase 8A manifest with candidate and collection statuses
2. Create `data/evaluation/phase8a/phase8a_p0_collection_report.md` clearly separating:
   - Sources researched
   - Images actually downloaded
   - License and attribution checks
   - Automated integrity checks
   - Human visual review still required
   - Blockers and next actions
3. Finish with PASS, PARTIAL, or BLOCKED. Stop after P0; do not proceed to P1 or P2 without further approval.

## Supporting References

### `references/p0-acquisition-checklist.md`
Prioritized checklist of image categories needed (P0, P1, P2) with rationales linked to Phase 7Y findings.

### `references/canonical-ids-decision-table.md`
Decision table mapping legacy site IDs (`red_fort`, `jama_masjid`) to canonical IDs (`red_fort_delhi`, `jama_masjid_delhi`) as used across the pipeline, with references to the catalogue entry, metadata key, evidence site_id, and mapping `site_ids` position.

### `templates/phase8a-manifest-template.json`
JSON template for the Phase 8A manifest, with all required fields and example values for P0 images.

### `scripts/verify-artifact-integrity.py`
Verification script that computes SHA-256 hashes and sizes for the four protected artifacts and compares against expected baselines. Outputs a pass/fail report suitable for inclusion in final reports.

## Pitfalls & Fixes

| Pitfall | Fix |
|---|---|
| Parsing site IDs from `image_ids` filenames (`red_fort_01` → `red_fort`) | Use `set(mapping["site_ids"])` instead — the canonical IDs live in the mapping array |
| `evidence_claim_count == 2` assertion | Typically the actual count is 3 (from `description`, `historical_significance`, `architectural_features` fields). Update the assertion, not the evidence. |
| Forgetting to regenerate evidence after index changes | Always run `backend/build_worldwide_evidence.py` first — evidence must be regenerated from the catalogue, not hand-edited. |
| Test failures attributed to "pre-existing" without verification | Always run the failing tests and capture actual tracebacks before assuming they're unchanged. |
| `red_fort` vs `red_fort_delhi` confusion | The catalogue is authoritative. Map all code paths, evidence, and tests to the canonical ID from the catalogue. |
| Attempting web/download in CLI-only environment | Report the exact blocker; operator must manually complete collection from a browser |
| Claiming visual review without actual image inspection | Mark human_review_status as PENDING until operator physically inspects the image |
| Publishing unvalidated acquisition results as production-ready | Keep evaluation datasets separate from production; report blockers transparently |

## Verification Commands

```bash
# Check canonical site IDs from mapping
python -c "import json; m=json.load(open('data/processed/index/mapping.json')); print(set(m['site_ids']))"

# Run Phase 8A integrity check
python -c "
import hashlib, os
artifacts = [
    'data/processed/index/clip_index.faiss',
    'data/processed/index/mapping.json',
    'data/processed/index/candidate/phase6ab_validation.faiss',
    'data/processed/index/candidate/phase6ab_validation_mapping.json',
]
expected = {
    'data/processed/index/clip_index.faiss': 'de32d554375c58c6cf6befc0c8cdf1268934e8814e48d53e4486d437e58caaa6',
    'data/processed/index/mapping.json': 'dbb135ff693ffcadab0ba701cf643854e1ece1baf19552083c0d1cb901ecd51c',
    'data/processed/index/candidate/phase6ab_validation.faiss': '4596388e8ae8dfd589ad49f9a85e23f78d332753fd58ed6fb43364b15dc14d98',
    'data/processed/index/candidate/phase6ab_validation_mapping.json': 'e25616c809ce118bc3d593e100e1d51ba291635455c27d0cc6db10e9ddc5fdf7',
}
all_ok = True
for art in artifacts:
    h = hashlib.sha256()
    with open(art, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    actual = h.hexdigest()
    exp = expected.get(art, '')
    match = actual == exp
    if not match: all_ok = False
    print(f'{art}: {\"MATCH\" if match else \"MISMATCH\"}')
print(f'All 4 artifacts intact: {all_ok}')
"

# Run existing test suites to confirm no regressions
pytest tests/test_recognition_pipeline.py tests/test_evidence_alignment.py tests/test_rag_evaluation.py tests/test_baseline_retrieval.py -v --tb=short
```



## 8. Status

**PARTIAL**

**Completed:**
- Dataset inventory and label-review status documented
- Exact and perceptual duplicate findings (none found)
- Existing coverage gaps identified and ranked
- Baseline rankings and full-precision decisions recorded
- Known-site correct identifications (2/5): Taj Mahal, Ajanta Caves
- Known-site rejections (3/5): Konark, Red Fort, Qutub Minar
- Known-site misidentifications: 0/5
- Unknown-site correct rejections (5/5): all 5 unknowns correctly rejected
- Evaluation/gallery leakage check: PASSED
- Prioritized acquisition checklist produced
- Limitations and hypotheses documented
- All 4 protected artifact hashes verified intact
- Dataset manifest written to 

**Remaining:**
- Unknown-image manual visual review still pending
- Additional evaluation images needed (per acquisition checklist)
- Threshold analysis separate from production settings
- Five known + five unknown images insufficient for reliable threshold selection

**Next steps (require approval):**
- Collect additional evaluation images per the prioritized checklist
- Conduct multi-view retrieval experiments with expanded gallery
- Perform offline threshold sweeps with full decision logic
- Consider manual visual review of unknown-site images

