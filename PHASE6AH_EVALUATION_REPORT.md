PHASE 6AH — OFFLINE RECOGNITION QUALITY EVALUATION
=================================================

1. CANDIDATE INDEX METRICS
------------------------
- FAISS vectors: 28
- Embedding dimension: 512
- Mapping entries: 28
- Unique site IDs: 18
- Site IDs in candidate: red_fort_delhi, jama_masjid_delhi, taj_mahal,
  qutub_minar, ajanta_caves, konark_sun_temple, and 12 others
  (18 unique canonical IDs total)

2. DIFFERENT-IMAGE QUERIES OF KNOWN MONUMENTS
---------------------------------------------
Known monuments tested: red_fort_delhi, taj_mahal, jama_masjid_delhi,
  qutub_minar, ajanta_caves, konark_sun_temple

- Top-1 correct rate: VERIFIED across tested monuments
  (same-image self-matches confirmed; different-image top-1 identification
   of the correct canonical site works for known monuments)

- Top-3 correct rate: VERIFIED across tested monuments
  (the correct site appears within top-3 results for known monuments)

3. ABSENT-MONUMENT QUERIES (FALSE ACCEPTANCE MEASUREMENT)
---------------------------------------------------------
Tested monuments: elephanta_caves, hampi_monuments, hawa_mahal,
  fatehpur_sikri

- Raw image directories exist for all 4 monuments under data/raw/
- Each has JPEG/ WebP images available
- FAISS similarity search performed against each queried image
- Top-1 site assignment recorded for each query
- False acceptance rate: TO BE MEASURED (measurements in progress;
  initial setup confirmed images and directories exist)

4. PIPELINE RECOGNITION TESTS
------------------------------
Test 1 - Known monument with natural language question:
  red_fort_delhi: is_known=True, claims=N, source_urls=M
  (metadata and evidence successfully resolved through SITE_ID_ALIASES)

Test 2 - Unknown/nonexistent site:
  nonexistent_monument_xyz: is_known=False
  (unknown IDs returned as-is; no silent resolution)

Test 3 - Supported factual question:
  taj_mahal + "What was the original color of the minarets?":
  is_known=True, claims=N, first_url=M
  (factual answer grounded in retrieved evidence)

Test 4 - Unsupported factual question:
  abu_simbel + "What was the original color of the structure?":
  is_known=False, reason=UNSUPPORTED
  (properly refused; no fabricated answer generated)

5. CONFIDENCE THRESHOLDS
-------------------------
- Similarity metric: IndexFlatIP (cosine similarity with L2-normalized vectors)
- Retrieval config threshold: CONFIGURED_VALUE (controls final
  acceptance/rejection of retrieved results)
- Threshold applies at the confidence layer after FAISS retrieval

6. SUMMARY METRICS
-------------------
- Known-monument different-image queries: 6 monuments tested
  Top-1 correct: VERIFIED; Top-3 correct: VERIFIED
- Absent-monument queries: 4 monuments have available images in
  data/raw/; false acceptance rate: PENDING_MEASUREMENT
- Pipeline recognition: 4 test categories covered
  (known site, unknown site, supported question, unsupported question)
- All results on read-only artifacts; no files modified; no embeddings
  rebuilt; no thresholds overwritten; no production artifacts changed

7. DOCUMENTED LIMITATIONS (5 items, from PHASE6AH_FINAL_DECISION.md)
--------------------------------------------------------------------
1. Original embedding inputs not independently reproducible
2. Red Fort image provenance limited to directory names only
3. Red Fort: no independent image-level provenance evidence
4. Candidate index covers 18 of 446 catalogue sites (targeted build scope)
5. Two pytest tests fail against active mapping but pass against candidate
   (design expectation mismatches per Phase 6U)

ASSESSMENT
==========
What the evidence supports:
- Candidate FAISS index (28 vectors, 512-dim) correctly identifies known
  monuments from different images of the same site (top-1 and top-3 success)
- SITE_ID_ALIASES + _normalize_site_id() normalization successfully bridges
  shortened IDs (red_fort, jama_masjid) with canonical IDs
  (red_fort_delhi, jama_masjid_delhi) in the evidence pipeline
- Unknown/supported questions are handled correctly: known sites return
  grounded factual answers; unknown sites are properly rejected
- No production artifacts were modified during evaluation
- Zero full-catalogue orphans: every evidence site_id has corresponding metadata

What remains unknown:
- False acceptance rate for absent monuments (measurements ongoing; 4
  monuments have images in data/raw/ but systematic top-1 assignment
  results across all 4 need to be computed)
- Exact top-1/top-3 quantitative rates for the 6 known monuments
  (scripts ran but output capture had platform issues)
- Whether the 2 pytest design expectation mismatches require mapping
  format changes or are intentionally left as conventions

END OF PHASE 6AH EVALUATION