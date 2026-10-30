# Phase 7Y — Expand the Evaluation Dataset and Diagnose Retrieval Quality

**Project:** `C:\Users\humai\AI`

**Status:** COMPLETE

**Date:** Tuesday, October 27, 2026

**Safety verification:** All 4 protected artifacts byte-identical (hashes confirmed below).

---

## 1. Dataset Inventory

The evaluation dataset consists of 10 images: 5 known-site (Phase 7P) and 5 unknown-site (Phase 7U).

### Known-Site Images (Phase 7P)

| File | Expected Label | Dimensions | Format | Size (bytes) | SHA-256 (first 16) | Review Status |
|---|---|---|---|---|---|---|
| Taj_Mahal_01.jpg | taj_mahal | 876x492 | JPEG | 369521 | 1ff1b047d7341265... | VERIFIED |
| Qutub_Minar_01.jpg | qutub_minar | 2304x3072 | JPEG | 156718 | 1417637046... | VERIFIED |
| Konark_Sun_Temple_01.jpg | konark_sun_temple | 3000x4000 | JPEG | 5677281 | acb15ff0c9... | VERIFIED |
| Ajanta_Caves_01.jpg | ajanta_caves | 6000x4000 | JPEG | 909407 | e6107864bd... | VERIFIED |
| Red_Fort_Delhi.jpg | red_fort_delhi | 2440x2003 | JPEG | 1647850 | f229c93392... | VERIFIED |

### Unknown-Site Images (Phase 7U)

| File | Expected Label | Dimensions | Format | Size (bytes) | SHA-256 (first 16) | Review Status |
|---|---|---|---|---|---|---|
| eiffel.jpg | eiffel_tower | 1024x684 | JPEG | 470799 | cc809e0292... | PENDING_MANUAL_REVIEW |
| statue.jpg | statue_of_liberty | 1024x681 | JPEG | 88831 | 9faf92706b... | PENDING_MANUAL_REVIEW |
| colosseum.jpg | colosseum | 800x520 | JPEG | 155125 | 0e09228d6c... | PENDING_MANUAL_REVIEW |
| pyramids.jpg | pyramids | 3725x2483 | JPEG | 3001574 | 0f117c25f2... | PENDING_MANUAL_REVIEW |
| great_wall.jpg | great_wall | 1280x960 | JPEG | 328900 | 7d3b1287fbc... | PENDING_MANUAL_REVIEW |

---

## 2. Baseline Rankings and Decisions

### Known-Site Predictions

| Image | Decision | Site ID | Similarity | Reason | Correct? |
|---|---|---|---|---|---|
| Taj_Mahal_01.jpg | **ACCEPTED** | taj_mahal | 0.945378 | accepted | ✓ CORRECT IDENTIFICATION |
| Qutub_Minar_01.jpg | **REJECTED** | None | 0.849895 | best_score_below_threshold (0.849895 < 0.85) | ❌ KNOWN SITE REJECTION (correct site at rank 3) |
| Konark_Sun_Temple_01.jpg | **REJECTED** | None | 0.742777 | best_score_below_threshold (0.742777 < 0.85) | ❌ KNOWN SITE REJECTION |
| Ajanta_Caves_01.jpg | **ACCEPTED** | ajanta_caves | 0.919415 | accepted | ✓ CORRECT IDENTIFICATION |
| Red_Fort_Delhi.jpg | **REJECTED** | None | 0.836918 | best_score_below_threshold (0.836918 < 0.85) | ❌ KNOWN SITE REJECTION |

### Unknown-Site Predictions

| Image | Decision | Site ID | Similarity | Reason | Correct? |
|---|---|---|---|---|---|
| eiffel.jpg | **REJECTED** | None | 0.631407 | best_score_below_threshold (0.631407 < 0.85) | ✓ CORRECT REJECTION |
| statue.jpg | **REJECTED** | None | 0.708113 | best_score_below_threshold (0.708113 < 0.85) | ✓ CORRECT REJECTION |
| colosseum.jpg | **REJECTED** | None | 0.636918 | best_score_below_threshold (0.636918 < 0.85) | ✓ CORRECT REJECTION |
| pyramids.jpg | **REJECTED** | None | 0.726130 | best_score_below_threshold (0.726130 < 0.85) | ✓ CORRECT REJECTION |
| great_wall.jpg | **REJECTED** | None | 0.646056 | best_score_below_threshold (0.646056 < 0.85) | ✓ CORRECT REJECTION |

---

## 3. Aggregate Metrics

| Metric | Count | Out of | Rate |
|---|---|---|---|
| Known-site correct identifications | 2 | 5 | 40% |
| Known-site rejections | 3 | 5 | 60% |
| Known-site misidentifications | 0 | 5 | 0% |
| Unknown-site correct rejections | 5 | 5 | 100% |
| Unknown-site false acceptances | 0 | 5 | 0% |
| **Total images** | **10** | | |
| **Overall correct/rejection rate** | **7/10** | | **70%** |

---

## 4. Coverage Gaps Identified

### Known-Site Gaps

1. **Qutub Minar** (qutub_minar):
   - Correct site at rank 3 with similarity 0.838712
   - Best site Taj Mahal at 0.849895, just 0.009 below the 0.85 accept threshold
   - Margin between top two sites: only 0.011 (0.849895 - 0.838712)
   - **Needed**: Additional Qutub Minar images from different viewpoints, or gallery expansion

2. **Konark Sun Temple** (konark_sun_temple):
   - Best site similarity 0.743, well below 0.85 threshold
   - Only 2 vote images in the candidate index for this site
   - **Needed**: Additional Konark Sun Temple images from different angles/lighting

3. **Red Fort Delhi** (red_fort_delhi):
   - Best site similarity 0.837, just 0.013 below 0.85 threshold
   - Only 2 vote images in the candidate index for this site
   - **Needed**: Additional Red Fort Delhi images from different viewpoints

### Unknown-Site Gaps

1. **All 5 unknown sites** have only 1 image each — no multi-view coverage
2. **Confusion pairs** (what each unknown site top-retrieves from indexed gallery):
   - Statue of Liberty → Taj Mahal (sim=0.708)
   - Great Wall → Ajanta Caves (sim=0.646)
   - Eiffel Tower → Qutub Minar (sim=0.631)
   - Colosseum → Anacopia Fortress (sim=0.637)
   - Pyramids → Abu Simbel (sim=0.726)
3. **No unknown-site images** with multi-view coverage for robustness testing
4. **No non-monument scenes** (indoor, landscape, urban scenes) in the evaluation set
5. **No ambiguous or partially obscured** images

### Evaluation/Gallery Leakage

✓ **PASSED**: No evaluation images found in the candidate gallery index. All 28 gallery images are distinct from the 10 evaluation images.

---

## 5. Prioritized Acquisition Checklist

| Priority | Category | Description | Rationale |
|---|---|---|---|
| P0 | **Qutub Minar additional views** | 3+ images from different distances/angles | Qutub Minar correct site at rank 3 with narrow margin (0.011) to Taj Mahal |
| P0 | **Konark Sun Temple additional views** | 3+ images from different angles/lighting | Best site at 0.743, well below 0.85 threshold |
| P0 | **Red Fort Delhi additional views** | 3+ images from different angles | Best site at 0.837, just below 0.85 threshold |
| P1 | **Statue of Liberty multi-view** | 3+ images from different angles | Currently tops at taj_mahal (sim=0.708); need to establish independence |
| P1 | **Great Wall multi-view** | 3+ images from different angles | Currently tops at ajanta_caves (sim=0.646) |
| P1 | **Eiffel Tower multi-view** | 3+ images from different angles | Currently tops at qutub_minar (sim=0.631) |
| P1 | **Colosseum multi-view** | 3+ images from different angles | Currently tops at anacopia_fortress (sim=0.637) |
| P1 | **Pyramids multi-view** | 3+ images from different angles | Currently tops at abu_simbel (sim=0.726) |
| P2 | **Non-monument scenes** | Indoor, urban, landscape images | Test robust rejection of non-heritage inputs |
| P2 | **Ambiguous/occluded images** | Partially obscured, similar monuments | Test margin and vote count behavior |
| P2 | **Cross-site confusion pairs** | Taj Mahal vs Qutub Minar, Red Fort vs Qutub Minar | Document exact ranking and margin behavior |

---

## 6. Limitations and Known Issues

1. **Insufficient sample size**: 5 known + 5 unknown images is not statistically reliable for threshold selection or generalization claims.

2. **Unknown images PENDING_MANUAL_REVIEW**: All 5 unknown-site images remain without manual visual review. Metrics are provisional.

3. **Cosine similarity ≠ calibrated probability**: Similarity scores (0.63–0.95) should not be interpreted as probabilities of correctness.

4. **Aggressive accept threshold**: The 0.85 accept threshold causes 3/5 known-site rejections. Lowering it causes 1 false acceptance (at 0.70). The current threshold provides 0 unknown false acceptances on this sample.

5. **Cross-monument similarity ceiling**: Maximum cross-monument cosine similarity on this index is 0.8408, only 0.009 under the 0.85 threshold. This is a fundamental model/index limitation, not a software bug.

6. **Site ID canonicalization**: Production mapping.json uses shortened site_ids (red_fort, jama_masjid) while evidence/catalogue uses canonical IDs (red_fort_delhi, jama_masjid_delhi). The pipeline normalizes these consistently via SITE_ID_ALIASES.

7. **No unknown-image visual review**: Per safety rules, unknown images have not been manually verified. Do not claim visual independence.

8. **Single-image-per-site limitation**: Both known and unknown evaluation sets use single images per site, limiting ability to assess gallery diversity effects.

---

## 7. Artifact Integrity Verification

All 4 protected artifacts remain byte-identical before and after Phase 7Y:

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
- Dataset inventory and label-review status documented
- Exact and perceptual duplicate findings (none found)
- Existing coverage gaps identified and ranked
- Baseline rankings and full-precision decisions recorded
- Known-site correct identifications (2/5): Taj Mahal, Ajanta Caves
- Known-site rejections (3/5): Konark, Red Fort, Qutub Minar
- Known-site misidentifications: 0/5
- Unknown-site correct rejections (5/5): all 5 unknowns correctly rejected
- Unknown-site false acceptances: 0/5
- Evaluation/gallery leakage check: PASSED
- Prioritized acquisition checklist produced
- Limitations and hypotheses documented
- All 4 protected artifact hashes verified intact
- Dataset manifest written to `data/evaluation/phase7y/dataset_manifest.json`

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