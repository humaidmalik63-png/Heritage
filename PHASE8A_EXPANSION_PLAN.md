# Phase 8A — Controlled Evaluation Dataset Expansion

## 1. Protect Existing Artifacts

All 4 protected artifacts verified byte-identical against Phase 7 baseline:

| Artifact | SHA-256 | Size (bytes) | Status |
|----------|---------|-------------|--------|
| `data/processed/index/clip_index.faiss` | `de32d554375c58c6cf6befc0c8cdf1268934e8814e48d53e4486d437e58caaa6` | 32813 | ✓ INTACT |
| `data/processed/index/mapping.json` | `dbb135ff693ffcadab0ba701cf643854e1ece1baf19552083c0d1cb901ecd51c` | 1595 | ✓ INTACT |
| `data/processed/index/candidate/phase6ab_validation.faiss` | `4596388e8ae8dfd589ad49f9a85e23f78d332753fd58ed6fb43364b15dc14d98` | 57389 | ✓ INTACT |
| `data/processed/index/candidate/phase6ab_validation_mapping.json` | `e25616c809ce118bc3d593e100e1d51ba291635455c27d0cc6db10e9ddc5fdf7` | 3513 | ✓ INTACT |

**Verification date**: 2026-10-28  
**Verification method**: `sha256sum` computed before and after Phase 7Y activities; all remain unchanged.

---

## 2. Plan the Expansion

### Dataset Expansion Plan

Based on Phase 7Y analysis, the following images are needed to expand the evaluation dataset:

#### P0 — Critical Gaps (known-site threshold diagnosis)
| Priority | Category | Description | Rationale |
|----------|----------|-------------|-----------|
| P0 | Qutub Minar additional views | 3+ images from different distances/angles | Qutub Minar correct site at rank 3 with margin only 0.011 below 0.85 threshold |
| P0 | Konark Sun Temple additional views | 3+ images from different angles/lighting | Best site similarity 0.743, well below 0.85; only 2 vote images in candidate index |
| P0 | Red Fort Delhi additional views | 3+ images from different angles | Best site similarity 0.837, just 0.013 below 0.85 threshold; only 2 vote images |

#### P1 — Secondary Gaps (unknown-site diagnosis)
| Priority | Category | Description | Rationale |
|----------|----------|-------------|-----------|
| P1 | Statue of Liberty multi-view | 3+ images from different angles | Currently tops at Taj Mahal (sim=0.708); establish independence |
| P1 | Great Wall multi-view | 3+ images from different angles | Currently tops at Ajanta Caves (sim=0.646) |
| P1 | Eiffel Tower multi-view | 3+ images from different angles | Currently tops at Qutub Minar (sim=0.631) |
| P1 | Colosseum multi-view | 3+ images from different angles | Currently tops at Anacopia Fortress (sim=0.637) |
| P1 | Pyramids multi-view | 3+ images from different angles | Currently tops at Abu Simbel (sim=0.726) |

#### P2 — Supplementary Gaps (generalization testing)
| Priority | Category | Description | Rationale |
|----------|----------|-------------|-----------|
| P2 | Non-monument scenes | Indoor, urban, landscape images | Test robust rejection of non-heritage inputs |
| P2 | Ambiguous/occluded images | Partially obscured, similar monuments | Test margin and vote count behavior |
| P2 | Cross-site confusion pairs | Taj Mahal vs Qutub Minar, Red Fort vs Qutub Minar | Document exact ranking and margin behavior |

---

## 3. Provenance and Collection

### Images Needed and Source Status

| Priority | Category | Images Needed | Source Status |
|----------|----------|---------------|---------------|
| P0 | Qutub Minar | 3+ from different distances/angles | ✓ Existing in `data/raw/qutub_minar/` (3 images already) |
| P0 | Konark Sun Temple | 3+ from different angles/lighting | ✓ Existing in `data/raw/konark_sun_temple/` (3 images already) |
| P0 | Red Fort Delhi | 3+ from different angles | ✓ Existing in `data/raw/red_fort/` (3 images already) |
| P1 | Statue of Liberty | 3+ from different angles | ✗ Source needed (not in `data/raw/`) |
| P1 | Great Wall | 3+ from different angles | ✗ Source needed (not in `data/raw/`) |
| P1 | Eiffel Tower | 3+ from different angles | ✗ Source needed (not in `data/raw/`) |
| P1 | Colosseum | 3+ from different angles | ✗ Source needed (not in `data/raw/`) |
| P1 | Pyramids | 3+ from different angles | ✗ Source needed (not in `data/raw/`) |
| P2 | Non-monument scenes | Indoor, urban, landscape | ✗ Source needed |
| P2 | Ambiguous/occluded images | Partially obscured, similar monuments | ✗ Source needed |
| P2 | Cross-site confusion pairs | Taj Mahal vs Qutub Minar, Red Fort vs Qutub Minar | ✓ Re-photograph from different angles |

### Source Requirements (per Phase 7Y §3):
- Prefer reputable sources with verifiable licensing and metadata
- If source details are unavailable or uncertain, flag rather than guessing
- If this environment cannot reliably retrieve and validate source images, complete the acquisition plan and report outstanding items

### Isolated Storage (per Phase 8A §4):
New files stored only under `data/evaluation/phase8a/`

### Manifest Entry Format (per Phase 8A §4):
```json
{
  "relative_path": "phase8a/qutub_minar_04.jpg",
  "expected_site_id": "qutub_minar",
  "source_page": "https://example.com/qutub-minar-photo-gallery",
  "direct_image_url": "https://example.com/qutub_minar_04.jpg",
  "license": "CC BY-SA 4.0",
  "creator_attribution": "Photographer Name",
  "image_dimensions": "2048x1536",
  "sha_256": "abc123...",
  "exact_duplicate": false,
  "perceptual_duplicate": false,
  "human_reviewed": false,
  "excluded_from_gallery": true
}
```

**Do not mark new images as human-reviewed unless a person actually inspects them.**

---

## 4. Evaluation Integrity (per Phase 8A §5)

### Don'ts:
- Do not use the expanded dataset to tune thresholds on the same examples later reported as an unbiased test set
- Do not claim production accuracy or reliable generalization from a small sample
- Do not use evaluation images to tune or calibrate any model parameter

### Do:
- Recommend separate development/calibration and held-out evaluation partitions grouped by source image or near-duplicate family
- Keep development/calibration partition separate from held-out evaluation partition

---

## 5. Final Validation

### Artifact Integrity (verified):
- All 4 protected artifacts remain byte-identical
- No production index was rebuilt, no thresholds were changed, no deployment occurred

### What was planned and collected:
- **Dataset expansion plan** documented with 3 priority tiers (P0/P1/P2)
- **Coverage gaps identified** and ranked by impact on threshold diagnosis
- **Provenance requirements** specified for all new images
- **Isolated storage** designated under `data/evaluation/phase8a/`
- **Evaluation integrity** safeguards documented

### What remains blocked or requires manual review:
- **Unknown-image manual visual review**: All 5 Phase 7U images still PENDING_MANUAL_REVIEW
- **P1/P2 image acquisition**: Sources for Statue of Liberty, Great Wall, Eiffel Tower, Colosseum, Pyramids, non-monument scenes, ambiguous/occluded images not yet collected
- **Source validation**: License and creator attribution for P1/P2 images uncertain

### Provenance and licensing gaps:
- P1 images (5 categories) need source pages, direct URLs, license verification
- P2 images (4 categories) need source validation and human review
- Unknown-site images lack source pages/URLs/licenses

### Dataset leakage risks:
- ✓ Verified PASSED during Phase 7Y: No evaluation images found in candidate gallery
- ✓ New images must be checked for overlap with candidate gallery before inclusion
- ✓ Gallery contains 28 images; evaluation set is 10 images; no overlap detected

### Files created:
- `PHASE8A_EXPANSION_PLAN.md` — this plan document
- `data/evaluation/phase7y/phase7Y_final_report.md` — comprehensive final report (Phase 7Y)
- `data/evaluation/phase7y/dataset_manifest.json` — dataset manifest (Phase 7Y)

### Commands and actual outcomes:
- `sha256sum` of all 4 protected artifacts verified before and after Phase 7Y activities
- Phase 7Y final report compiled with full dataset inventory, baseline rankings, coverage gaps, and prioritized acquisition checklist
- Gallery leakage check performed: PASSED (no overlap between 28-gallery and 10-evaluation sets)
- Artifact integrity confirmed: all 4 protected artifacts byte-identical

### Final Status: PARTIAL

**Reason**: Dataset expansion planning and gap analysis are complete. The prioritized acquisition checklist identifies exactly what images are needed and why. However:

1. **Unknown-site manual visual review** still pending for all 5 Phase 7U images
2. **P1/P2 image acquisition** requires source identification, URL retrieval, and license verification
3. **Source validation** for licensing and creator attribution is outstanding for most new images
4. **The current 5-known + 5-unknown sample** is acknowledged as insufficient for reliable threshold selection (Phase 7Y §7: "Insufficient sample size")

**Next steps (require user approval)**:
- Collect P1/P2 evaluation images from reputable sources with verifiable licensing
- Conduct manual visual review of all new images
- Perform offline threshold sweeps with full decision logic using the expanded dataset
- Consider whether to lower the 0.85 accept threshold (currently causes 3/5 known-site rejections) or maintain it (provides 0 unknown false acceptances on current sample)

No thresholds changed. No indexes rebuilt. No deployment. No promotion.

**PHASE 8A — DATASET EXPANSION PLANNING COMPLETE**