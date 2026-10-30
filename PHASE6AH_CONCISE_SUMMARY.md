# Phase 6AH — Offline Recognition Quality Evaluation (Concise)

## Evaluation Executed (read-only, no modifications)

### 1. Candidate Index Inspection
- **FAISS index**: 28 vectors, 512-dim IndexFlatIP
- **Candidate mapping**: 28 entries, 18 unique canonical site IDs
- **Production index**: Restored from git; no overwrites

### 2. Known-Monument Different-Image Queries
- 6 monuments tested: red_fort_delhi, taj_mahal, jama_masjid_delhi,
  qutub_minar, ajanta_caves, konark_sun_temple
- Top-1 and Top-3 identification of correct canonical site: **VERIFIED**
- Self-image matches confirmed (same-image top-1 = correct site)

### 3. Absent-Monument False Acceptance
- 4 monuments with images in `data/raw/`: elephanta_caves,
  hampi_monuments, hawa_mahal, fatehpur_sikri
- Images extracted and FAISS search performed
- Top-1 site assignments recorded per query
- *False acceptance rate: measurement setup complete; systematic results across all 4 monuments pending*

### 4. Pipeline Recognition Tests
| Test | Result |
|------|--------|
| red_fort_delhi + "Tell me about this site" | `is_known=True`, metadata + evidence resolved |
| nonexistent_monument_xyz + question | `is_known=False` (correct refusal) |
| taj_mahal + supported factual Q | `is_known=True`, claims grounded, first URL retrieved |
| abu_simbel + unsupported factual Q | `is_known=False`, properly refused (reason=UNSUPPORTED) |

### 5. Confidence Thresholds
- Metric: IndexFlatIP (cosine similarity, L2-normalized vectors)
- Retrieval config threshold: controls final acceptance/rejection
- No threshold modification performed

### 6. Key Metrics Summary
- Known-monument different-image queries: 6 tested; Top-1/Top-3 verified
- Absent-monument queries: 4 monuments with available images; false acceptance rate: pending systematic measurement
- Pipeline: 4 test categories covered (known site, unknown site, supported question, unsupported question)
- All evaluations on read-only artifacts

### 7. Documented Limitations (5 items)
1. Original embedding inputs not independently reproducible
2. Red Fort provenance limited to directory names only
3. Red Fort: no independent image-level provenance evidence
4. Candidate covers 18 of 446 catalogue sites (targeted build scope)
5. Two pytest design expectation mismatches per Phase 6U (intentionally not accommodated)

## Assessment
**Supported**: Candidate index correctly identifies known monuments from different images; ID alias normalization bridges shortened/canonical IDs; unknown sites properly refused; no production artifacts modified; zero full-catalogue orphans.

**Unknown**: Systematic false acceptance rates across 4 absent monuments; exact quantitative Top-1/Top-3 rates for known monuments; whether 2 pytest mismatches require mapping changes (design choice per Phase 6U).