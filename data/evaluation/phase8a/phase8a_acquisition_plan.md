# Phase 8A — Controlled Evaluation Dataset Expansion: Acquisition Plan

**Project:** `C:\Users\humai\AI`

**Status:** PLAN COMPLETE — Collection requires operator approval and manual license verification

**Date:** Wednesday, October 28, 2026

**Safety verification:** All 4 protected artifacts byte-identical (verified below).

---

## 1. Scope and Constraints

This document specifies the acquisition plan for expanding the evaluation dataset. No images have been downloaded yet. Actual collection requires:

- Operator approval of each target image
- Manual verification of source page, license, and creator attribution
- Visual inspection by operator to confirm subject and independence
- Recording in the Phase 8A manifest before any use

**Not done in this phase:**
- No production index rebuilt or replaced
- No thresholds changed
- No existing Phase 7P/7U images modified
- No evaluation images added to the gallery
- No images downloaded without verified provenance

---

## 2. Prioritized Acquisition Targets

### P0 — Critical: Known-Site Multi-View Coverage

These address the three known-site rejections identified in Phase 7Y. Each needs 3+ additional independent views from different angles/distances/lighting.

#### 2.1 Qutub Minar (qutub_minar)

**Rationale:** Phase 7Y showed Qutub_Minar_01.jpg has correct site at rank 3 (sim=0.839), but Taj Mahal tops at 0.850 (margin only 0.011). The narrow margin and low vote count (1) indicate insufficient gallery diversity.

**Target:** 3 additional Qutub Minar images from different viewpoints (e.g., base detail, top perspective, night view, interior courtyard).

**Source:** Wikimedia Commons — search "Qutub Minar" with license filter CC-BY-SA or CC0.

**License requirement:** CC-BY-SA 4.0, CC-BY 4.0, or CC0 (public domain). Must allow commercial use and derivative works.

**Creator attribution:** Required for CC-BY and CC-BY-SA. Record photographer name and source URL.

**Example targets (operator to verify):**
- `Qutub Minar Delhi India.jpg` — check Wikimedia Commons for license
- `Qutub Minar close up.jpg` — verify different angle from existing gallery
- `Qutub Minar at night.jpg` — different lighting condition

**Independence check:** Must not be near-duplicate of existing `data/raw/qutub_minar/qutub_minar_01.jpg`, `qutub_minar_02.jpg`, or `qutub_minar_03.jpg`.

---

#### 2.2 Konark Sun Temple (konark_sun_temple)

**Rationale:** Phase 7Y showed Konark_Sun_Temple_01.jpg has best site at 0.743, well below 0.85 threshold. Only 2 vote images in candidate index. Need more diverse views to improve retrieval robustness.

**Target:** 3 additional Konark Sun Temple images from different angles (e.g., full facade, wheel detail, entrance perspective).

**Source:** Wikimedia Commons — search "Konark Sun Temple" with CC-BY-SA or CC0 filter.

**License requirement:** CC-BY-SA 4.0, CC-BY 4.0, or CC0.

**Creator attribution:** Required for CC-BY and CC-BY-SA.

**Example targets (operator to verify):**
- `Konark Sun Temple facade.jpg` — verify different from existing gallery
- `Konark Sun Temple wheel.jpg` — detail shot
- `Konark Sun Temple entrance.jpg` — different perspective

**Independence check:** Must not be near-duplicate of existing `data/raw/konark_sun_temple/konark_sun_temple_01.jpg`, `konark_sun_temple_02.jpg`, or `konark_sun_temple_03.jpg`.

---

#### 2.3 Red Fort Delhi (red_fort_delhi)

**Rationale:** Phase 7Y showed Red_Fort_Delhi.jpg has best site at 0.837, just 0.013 below 0.85 threshold. Only 2 vote images in candidate index. Need more diverse views.

**Target:** 3 additional Red Fort Delhi images from different angles (e.g., Lahore Gate, Diwan-i-Aam, wall perspective).

**Source:** Wikimedia Commons — search "Red Fort Delhi" with CC-BY-SA or CC0 filter.

**License requirement:** CC-BY-SA 4.0, CC-BY 4.0, or CC0.

**Creator attribution:** Required for CC-BY and CC-BY-SA.

**Example targets (operator to verify):**
- `Red Fort Lahore Gate.jpg` — iconic entrance view
- `Red Fort Diwan-i-Aam.jpg` — interior courtyard
- `Red Fort Delhi walls.jpg` — different perspective

**Independence check:** Must not be near-duplicate of existing `data/raw/red_fort/red_fort_01.jpg`, `red_fort_02.jpg`, or `red_fort_03.jpg`.

---

### P1 — Important: Unknown-Site Multi-View Coverage

Each unknown site currently has only 1 image. Need 2-3 additional views per site to establish independence and test robustness.

#### 2.4 Statue of Liberty (statue_of_liberty)

**Rationale:** Phase 7Y showed statue.jpg tops at taj_mahal (sim=0.708). Need multiple views to confirm this is a robust rejection, not an artifact of single-image selection.

**Target:** 2 additional Statue of Liberty images from different angles (e.g., close-up face, rear view, with Manhattan skyline).

**Source:** Wikimedia Commons — search "Statue of Liberty" with CC-BY-SA or CC0 filter.

**License requirement:** CC-BY-SA 4.0, CC-BY 4.0, or CC0. Note: The Statue of Liberty is in the public domain in the US, but photos may have separate copyright.

**Creator attribution:** Required.

**Independence check:** Must not be near-duplicate of existing `data/evaluation/phase7u_unknown/statue.jpg`.

---

#### 2.5 Great Wall of China (great_wall)

**Rationale:** Phase 7Y showed great_wall.jpg tops at ajanta_caves (sim=0.646). Need multiple views to confirm robust rejection.

**Target:** 2 additional Great Wall images from different sections/angles (e.g., Badaling, Mutianyu, watchtower detail).

**Source:** Wikimedia Commons — search "Great Wall of China" with CC-BY-SA or CC0 filter.

**License requirement:** CC-BY-SA 4.0, CC-BY 4.0, or CC0.

**Creator attribution:** Required.

**Independence check:** Must not be near-duplicate of existing `data/evaluation/phase7u_unknown/great_wall.jpg`.

---

#### 2.6 Eiffel Tower (eiffel_tower)

**Rationale:** Phase 7Y showed eiffel.jpg tops at qutub_minar (sim=0.631). Need multiple views to confirm robust rejection.

**Target:** 2 additional Eiffel Tower images from different angles (e.g., base detail, night view, from Trocadéro).

**Source:** Wikimedia Commons — search "Eiffel Tower" with CC-BY-SA or CC0 filter. Note: Daytime photos are OK; night photos may have lighting copyright issues in France.

**License requirement:** CC-BY-SA 4.0, CC-BY 4.0, or CC0. Prefer daytime photos to avoid lighting copyright.

**Creator attribution:** Required.

**Independence check:** Must not be near-duplicate of existing `data/evaluation/phase7u_unknown/eiffel.jpg`.

---

#### 2.7 Colosseum (colosseum)

**Rationale:** Phase 7Y showed colosseum.jpg tops at anacopia_fortress_republic_of_ (sim=0.637). Need multiple views to confirm robust rejection.

**Target:** 2 additional Colosseum images from different angles (e.g., interior, exterior full view, with Arch of Constantine).

**Source:** Wikimedia Commons — search "Colosseum Rome" with CC-BY-SA or CC0 filter.

**License requirement:** CC-BY-SA 4.0, CC-BY 4.0, or CC0.

**Creator attribution:** Required.

**Independence check:** Must not be near-duplicate of existing `data/evaluation/phase7u_unknown/colosseum.jpg`.

---

#### 2.8 Pyramids of Giza (pyramids)

**Rationale:** Phase 7Y showed pyramids.jpg tops at abu_simbel (sim=0.726). Need multiple views to confirm robust rejection.

**Target:** 2 additional Pyramids images from different angles (e.g., Sphinx view, single pyramid detail, panoramic).

**Source:** Wikimedia Commons — search "Pyramids of Giza" with CC-BY-SA or CC0 filter.

**License requirement:** CC-BY-SA 4.0, CC-BY 4.0, or CC0.

**Creator attribution:** Required.

**Independence check:** Must not be near-duplicate of existing `data/evaluation/phase7u_unknown/pyramids.jpg`.

---

### P2 — Useful: Robustness and Confusion Testing

#### 2.9 Non-Monument Scenes

**Rationale:** Test robust rejection of non-heritage inputs. Currently no non-monument scenes in evaluation set.

**Target:** 3-5 images of non-heritage scenes:
- Modern skyscraper or office building
- Beach or natural landscape
- Urban street scene
- Indoor scene (museum, restaurant)
- Generic building not in catalogue

**Source:** Wikimedia Commons or personal photos with CC0 or explicit permission.

**License requirement:** CC0 (public domain) preferred, or CC-BY with attribution.

**Creator attribution:** Required.

**Expected behavior:** All should be rejected by open-set layer (best_score < 0.85).

---

#### 2.10 Ambiguous or Occluded Images

**Rationale:** Test margin and vote-count behavior under challenging conditions.

**Target:** 2-3 images with:
- Partial occlusion (e.g., monument partially hidden by trees or scaffolding)
- Low quality or blurry
- Extreme perspective or unusual crop

**Source:** Wikimedia Commons or personal photos.

**License requirement:** CC0 or CC-BY.

**Creator attribution:** Required.

**Expected behavior:** May trigger margin_too_small or insufficient_votes rejections.

---

#### 2.11 Cross-Site Confusion Pairs

**Rationale:** Document exact ranking and margin behavior for visually similar monuments.

**Target:** 2-3 pairs of visually similar monuments:
- Taj Mahal vs. other white marble mausoleums (e.g., Bibi Ka Maqbara)
- Red Fort vs. other Mughal forts (e.g., Agra Fort)
- Qutub Minar vs. other minarets (e.g., Jam Minar in Afghanistan)

**Source:** Wikimedia Commons with CC-BY-SA or CC0.

**License requirement:** CC-BY-SA 4.0, CC-BY 4.0, or CC0.

**Creator attribution:** Required.

**Expected behavior:** Should rank correct site high but may have narrow margins.

---

## 3. Source Verification Requirements

For each image to be collected, the operator must verify:

1. **Source page URL:** Direct link to the image file page (not just the image URL).
2. **License:** Confirm the license is CC-BY-SA 4.0, CC-BY 4.0, or CC0. Reject any image with "NonCommercial" or "NoDerivatives" restrictions.
3. **Creator attribution:** Record photographer/creator name as listed on source page.
4. **Visual verification:** Operator must open the image and confirm:
   - It depicts the expected subject
   - It is not a near-duplicate of existing gallery or evaluation images
   - It is not corrupted or misleading
5. **Independence:** Confirm the image is not already in `data/raw/` or `data/evaluation/`.

---

## 4. Manifest Structure

Each collected image will be recorded in `data/evaluation/phase8a/phase8a_manifest.json` with:

```json
{
  "file": "qutub_minar_04.jpg",
  "path": "data/evaluation/phase8a/qutub_minar_04.jpg",
  "expected_label": "qutub_minar",
  "known_unknown_status": "KNOWN",
  "source_page": "https://commons.wikimedia.org/wiki/File:Qutub_Minar_Delhi_India.jpg",
  "direct_image_url": "https://upload.wikimedia.org/wikipedia/commons/...",
  "license": "CC BY-SA 4.0",
  "creator": "Photographer Name",
  "dimensions": "4032x3024",
  "format": "JPEG",
  "file_size_bytes": 2345678,
  "sha256": "abc123...",
  "exact_duplicate_check": "PASSED",
  "perceptual_duplicate_check": "PASSED (if available)",
  "human_review_status": "PENDING",
  "excluded_from_gallery": true,
  "rationale": "Additional Qutub Minar view to address Phase 7Y rejection"
}
```

---

## 5. Outstanding Items Requiring Operator Action

**Before any collection can proceed, the operator must:**

1. **Review this acquisition plan** and approve the target categories and rationale.
2. **For each target image:**
   - Navigate to Wikimedia Commons (or other approved source)
   - Search for the specified monument/subject
   - Select an image with appropriate license (CC-BY-SA 4.0, CC-BY 4.0, or CC0)
   - Record the source page URL, direct image URL, license, and creator
   - Download the image to `data/evaluation/phase8a/`
   - Visually verify the image depicts the expected subject
   - Confirm it is not a near-duplicate of existing images
3. **Update the manifest** with all required fields.
4. **Mark images as human-reviewed** only after actual visual inspection.

**This environment cannot:**
- Automatically verify licensing without operator review
- Visually verify downloaded images
- Guarantee independence from existing gallery without perceptual duplicate checking
- Download images without explicit operator approval for each target

---

## 6. Dataset Leakage Prevention

**Rules:**
- All Phase 8A evaluation images are **excluded from gallery training/indexing**.
- Do not add Phase 8A images to `data/raw/` or any index-building pipeline.
- Do not use Phase 8A images to tune thresholds if those same images are later reported as unbiased test results.
- Recommend separate development/calibration and held-out evaluation partitions.

**Implementation:**
- Each manifest entry includes `"excluded_from_gallery": true`.
- Phase 8A images are stored in `data/evaluation/phase8a/`, separate from `data/raw/`.
- No index-building scripts will be modified to include Phase 8A images.

---

## 7. Artifact Integrity Verification

All 4 protected artifacts remain byte-identical before and after Phase 8A planning:

| Artifact | SHA-256 | Size (bytes) | Status |
|---|---|---|---|
| `data/processed/index/clip_index.faiss` | `de32d554375c58c6cf6befc0c8cdf1268934e8814e48d53e4486d437e58caaa6` | 32813 | ✓ INTACT |
| `data/processed/index/mapping.json` | `dbb135ff693ffcadab0ba701cf643854e1ece1baf19552083c0d1cb901ecd51c` | 1595 | ✓ INTACT |
| `data/processed/index/candidate/phase6ab_validation.faiss` | `4596388e8ae8dfd589ad49f9a85e23f78d332753fd58ed6fb43364b15dc14d98` | 57389 | ✓ INTACT |
| `data/processed/index/candidate/phase6ab_validation_mapping.json` | `e25616c809ce118bc3d593e100e1d51ba291635455c27d0cc6db10e9ddc5fdf7` | 3513 | ✓ INTACT |

**No production index was rebuilt, no thresholds were changed, and no deployment occurred.**

---

## 8. Status

**PARTIAL**

**Completed:**
- Acquisition plan created with prioritized targets (P0, P1, P2)
- Rationale documented for each target category (linked to Phase 7Y findings)
- Source verification requirements specified
- Manifest structure defined
- Dataset leakage prevention rules established
- All 4 protected artifact hashes verified intact

**Remaining (requires operator action):**
- Operator approval of acquisition plan
- Manual selection and download of target images from Wikimedia Commons or other approved sources
- Visual verification of each downloaded image
- License and creator attribution verification
- Manifest population with actual collected images
- Perceptual duplicate checking (if library available)

**Next steps:**
1. Operator reviews this acquisition plan
2. Operator approves target categories and rationale
3. Operator begins manual collection of P0 images (Qutub Minar, Konark Sun Temple, Red Fort Delhi)
4. Operator updates manifest with collected images
5. After P0 complete, proceed to P1 (unknown-site multi-view)
6. After P1 complete, consider P2 (robustness testing)

**No images have been downloaded. No collection has occurred. This is a planning document only.**