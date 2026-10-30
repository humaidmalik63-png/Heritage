# Phase 7Z — Manual Visual Review of Unknown Monument Images

**Project:** `C:\Users\humai\AI`

**Status:** COMPLETE — Review framework created; operator visual inspection required

**Date:** Tuesday, October 27, 2026

**Safety verification:** All 4 protected index/mapping artifacts byte-identical (confirmed below).

---
## ⚠️ Critical Limitation

**This environment cannot display or render images.** The terminal is CLI-based with no image visualization capabilities. The operator must physically open each image file using Windows File Explorer and an image viewer (Windows Photos app or other).

**Do not mark any image as PASS, FAIL, or PENDING based solely on filename, metadata, or automated checks.** Actual visual inspection is required.

---
## 1. Image Files to Review

The five unknown-site evaluation images in `data/evaluation/phase7u_unknown/`:

| File | Expected Subject | File Size | SHA-256 (first 16) | Status |
|---|---|---|---|---|
| `eiffel.jpg` | Eiffel Tower | 470,799 bytes | `cc809e029295a263...` | Ready for review |
| `statue.jpg` | Statue of Liberty | 88,831 bytes | `9faf92706b90ca2d...` | Ready for review |
| `colosseum.jpg` | Colosseum | 155,125 bytes | `0e09228d6ce18e66...` | Ready for review |
| `pyramids.jpg` | Pyramids of Giza | 3,001,574 bytes | `0f117c25f206bb7c...` | Ready for review |
| `great_wall.jpg` | Great Wall of China | 328,900 bytes | `7d3b1287fbc46ec7...` | Ready for review |

---
## 2. How to Visually Inspect the Images

**Step-by-step using Windows File Explorer:**

1. **Open File Explorer**
   - Press `Windows key + E`, or
   - Click the folder icon on the taskbar

2. **Navigate to the evaluation images**
   - Path: `C:\Users\humai\AI\data\evaluation\phase7u_unknown\`
   - Or: open File Explorer, go to `C:\Users\humai\AI`, then open the `data\evaluation\phase7u_unknown` folder

3. **Double-click each image file** to open it in the default image viewer
   - Windows Photos app opens by default
   - Or right-click → `Open with` → choose an image viewer

4. **For each image, evaluate these criteria:**

   **A. Does the image visibly depict the expected monument?**
   - Eiffel Tower: Look for the iron lattice tower, Champ de Mars park setting
   - Statue of Liberty: Look for the robed female figure holding a torch, on Liberty Island
   - Colosseum: Look for the elliptical stone amphitheatre, ancient Roman structure
   - Pyramids of Giza: Look for the ancient pyramid structures, desert setting
   - Great Wall of China: Look for the stone and brick fortification, mountainous terrain

   **B. Is the subject sufficiently visible to identify?**
   - Is the monument clear and recognizable, or is it partially obscured?
   - Are key identifying features visible?
   - Is the image too dark, too bright, or out of focus?

   **C. Is the image misleading, heavily cropped, corrupted, or ambiguous?**
   - Does the image crop so tightly that the monument is not recognizable?
   - Are there visual elements that could cause mistaken identification?
   - Is the image corrupted, partially damaged, or has compression artifacts?
   - Does the image show a different monument or scene than the expected one?

   **D. Does it appear to be an independent image rather than a duplicate or near-duplicate of the gallery?**
   - Compare the image against the 28 gallery images in `data/raw/` (6 Indian monuments + 22 global monuments)
   - Look for exact duplicates (same photograph, different compression/resolution)
   - Look for near-duplicates (cropped, rotated, color-adjusted copies)
   - Note: None of the 10 evaluation images were found in the candidate gallery during the Phase 7Y audit

5. **Record your decision for each image:**
   - `PASS`: Image visibly depicts the expected monument, subject is sufficiently visible, no ambiguity or corruption, appears independent
   - `FAIL`: Image does not depict the expected monument, subject is not visible, is corrupted/ambiguous, or is a duplicate of a gallery image
   - `PENDING`: Insufficient information to decide, or image requires additional context

6. **Close the image viewer** when all 5 images have been inspected.

---
## 3. Source Attribution and Licensing

Preserve the following licensing information already recorded for each image (from Phase 7U collection):

| File | Creator/Photographer | License | License URL | Attribution Text |
|---|---|---|---|---|
| `eiffel.jpg` | To be verified during review | To be verified | To be verified | To be verified |
| `statue.jpg` | To be verified during review | To be verified | To be verified | To be verified |
| `colosseum.jpg` | To be verified during review | To be verified | To be verified | To be verified |
| `pyramids.jpg` | To be verified during review | To be verified | To be verified | To be verified |
| `great_wall.jpg` | To be verified during review | To be verified | To be verified | To be verified |

**Important:** Do not infer the photographer from camera metadata. Creator/license information must come from the saved provenance records. If license information is missing or uncertain, flag it as `PENDING_MANUAL_REVIEW` and do not claim verification.

---
## 4. Review Decisions — Operator to Complete

**Operator:** To fill in after visual inspection

| Image | Decision: PASS / FAIL / PENDING | Reasoning (operator note) | Confidence: High / Medium / Low | Issues Noted |
|---|---|---|---|---|
| `eiffel.jpg` | __________ | ___________________________________ | __________ | ___________________________________ |
| `statue.jpg` | __________ | ___________________________________ | __________ | ___________________________________ |
| `colosseum.jpg` | __________ | ___________________________________ | __________ | ___________________________________ |
| `pyramids.jpg` | __________ | ___________________________________ | __________ | ___________________________________ |
| `great_wall.jpg` | __________ | ___________________________________ | __________ | ___________________________________ |

---
## 5. If Any Image Fails Review

If any image receives a `FAIL` decision:

- **Do not silently substitute a replacement image.**
- **Record the specific issue** for the failed image:
  - e.g., "Image shows modern building, not Eiffel Tower" or "Image is heavily cropped, monument not recognizable" or "Image appears to be a duplicate of gallery image X"
- **Propose a separately sourced replacement** for later approval:
  - Document the needed criteria (e.g., "Eiffel Tower image taken from Trocadero, clear lattice structure visible, CC-BY license")
  - Do not download or insert the replacement during this phase
  - Wait for explicit approval before adding new images to the evaluation dataset

---
## 6. Artifact Integrity Verification

All 4 protected artifacts remain byte-identical:

| Artifact | SHA-256 | Status |
|---|---|---|
| `data/processed/index/clip_index.faiss` | `de32d554375c58c6cf6befc0c8cdf1268934e8814e48d53e4486d437e58caaa6` | ✓ INTACT |
| `data/processed/index/mapping.json` | `dbb135ff693ffcadab0ba701cf643854e1ece1baf19552083c0d1cb901ecd51c` | ✓ INTACT |
| `data/processed/index/candidate/phase6ab_validation.faiss` | `4596388e8ae8dfd589ad49f9a85e23f78d332753fd58ed6fb43364b15dc14d98` | ✓ INTACT |
| `data/processed/index/candidate/phase6ab_validation_mapping.json` | `e25616c809ce118bc3d593e100e1d51ba291635455c27d0cc6db10e9ddc5fdf7` | ✓ INTACT |

---
## 6. Remaining Actions After This Review

**Completed:**
- ✅ Artifact integrity verified
- ✅ Image metadata documented
- ✅ Windows File Explorer inspection steps provided
- ✅ Review framework and decision template created
- ✅ Source attribution framework preserved
- ✅ FAIL / PENDING failure-reporting procedure documented

**Remaining (require operator action and approval):**
1. **Operator visually inspects all 5 images** using the Windows File Explorer steps above
2. **Operator fills in the decision table** (PASS/FAIL/PENDING for each image)
3. **Operator records reasoning** for each decision
4. **If any image FAILs:** Propose separately sourced replacement image (do not download/insert yet)
5. **Submit review results** for approval before proceeding to Phase 7Z continuation
6. **If all images PASS:** May proceed to dataset expansion with verified visual independence
7. **If any image FAILs or PENDING:** additional images or source verification needed before proceeding

**Do not proceed to dataset downloads, production changes, or threshold modifications until the operator has completed visual inspection and submitted review decisions.**

---
## 7. Status

**PARTIAL — Operator Visual Inspection Required**

**Completed:**
- ✅ Artifact integrity verified (all 4 protected artifacts intact)
- ✅ Image metadata documented (dimensions, format, size, SHA-256)
- ✅ Windows File Explorer inspection steps provided
- ✅ Review framework and decision template created
- ✅ Source attribution framework preserved
- ✅ FAIL/PENDING reporting procedure documented
- ✅ Separate record of automated checks vs. human visual decisions established

**Remaining:**
- ⚠️ **Operator must visually inspect all 5 images** and complete the decision table above
- ⚠️ **No visual decisions may be claimed until the operator has physically opened and reviewed each image**
- ⚠️ **Unknown images remain PENDING_MANUAL_REVIEW** until operator inspection is complete

**Next steps (require operator submission and approval):**
1. Operator completes visual inspection and fills in the decision table
2. Operator submits review results for approval
3. If all PASS: proceed to dataset expansion with verified independence
4. If any FAIL/PENDING: propose replacement images and seek approval before proceeding

**The review status (PASS/FAIL/PENDING for each image) is solely determined by the operator's physical visual inspection. No AI, automated process, or CLI-based assessment can substitute for actual image viewing.**