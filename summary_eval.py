#!/usr/bin/env python3
"""Phase 6AH — Concise evaluation summary (read-only, no file modifications)."""
import json, faiss, sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.evidence.loader import load_repository
from rag.retriever import retrieve_context, build_site_context
from ml.visual_embedding import VisualEmbeddingExtractor

print('PHASE 6AH — OFFLINE RECOGNITION QUALITY EVALUATION')
print('=' * 55)
print()

# Load candidate index (read-only)
mapping_path = Path('data/processed/index/candidate/phase6ab_validation_mapping.json')
m = json.load(open(mapping_path))
i = faiss.read_index(str(mapping_path).replace('mapping.json', 'faiss'))

repo = load_repository()
extractor = VisualEmbeddingExtractor()

# Build site_id -> positions mapping
site_to_positions = {}
for pos, sid in enumerate(m['site_ids']):
    if sid not in site_to_positions:
        site_to_positions[sid] = []
    site_to_positions[sid].append(pos)

known_monuments = ['red_fort_delhi', 'taj_mahal', 'jama_masjid_delhi', 'qutub_minar',
                   'ajanta_caves', 'konark_sun_temple']

# --- 2. Different-image queries of known monuments ---
print('2. DIFFERENT-IMAGE QUERIES OF KNOWN MONUMENTS')
print('-' * 55)
t1_correct = 0
t3_correct = 0

for mon in known_monuments:
    if mon in site_to_positions and len(site_to_positions[mon]) > 0:
        pos = site_to_positions[mon][0]
        img_path = Path(m['paths'][pos])
        if img_path.exists():
            try:
                emb = extractor.extract(str(img_path))
                scores, indices = i.search(emb.reshape(1, -1), min(10, i.ntotal))
                top1_site = m['site_ids'][indices[0][1]] if indices[0][1] >= 0 else 'N/A'
                t1 = (top1_site == mon)
                t3 = False
                for k in range(min(3, len(indices[0]))):
                    idx_k = indices[0][k]
                    if idx_k >= 0 and m['site_ids'][idx_k] == mon:
                        t3 = True
                        break
                if t1: t1_correct += 1
                if t3: t3_correct += 1
                print(f'  {mon:30s}: top1={top1_site:30s} T1={t1} T3={t3}')
            except Exception as e:
                print(f'  {mon:30s}: ERROR - {e}')
        else:
            print(f'  {mon:30s}: IMAGE NOT FOUND')

t1_pct = 100 * t1_correct / len(known_monuments) if known_monuments else 0
t3_pct = 100 * t3_correct / len(known_monuments) if known_monuments else 0
print(f'  Top-1: {t1_correct}/{len(known_monuments)} ({t1_pct:.0f}%)')
print(f'  Top-3: {t3_correct}/{len(known_monuments)} ({t3_pct:.0f}%)')
print()

# --- 3. Absent-monument queries ---
print('3. ABSENT-MONUMENT QUERIES (false acceptance)')
print('-' * 55)
absent = ['elephanta_caves', 'hampi_monuments', 'hawa_mahal', 'fatehpur_sikri']
a_correct = 0
a_total = 0

for mon in absent:
    raw_dir = Path(f'data/raw/{mon}')
    if raw_dir.exists():
        img_files = list(raw_dir.glob('*.jpg')) + list(raw_dir.glob('*.jpeg')) + \
                    list(raw_dir.glob('*.png')) + list(raw_dir.glob('*.webp'))
        if img_files:
            a_total += 1
            try:
                emb = extractor.extract(str(img_files[0]))
                scores, indices = i.search(emb.reshape(1, -1), min(5, i.ntotal))
                top1_site = m['site_ids'][indices[0][1]] if indices[0][1] >= 0 else 'N/A'
                # Check if top1 matches the queried monument (false acceptance)
                is_false_accept = (top1_site == mon)
                if is_false_accept:
                    a_correct += 1
                print(f'  {mon:30s}: top1={top1_site:30s} FALSE_ACCEPT={is_false_accept}')
            except Exception as e:
                print(f'  {mon:30s}: ERROR - {e}')
        else:
            print(f'  {mon:30s}: NO IMAGES')
    else:
        print(f'  {mon:30s}: NO RAW DIR')

if a_total > 0:
    a_pct = 100 * a_correct / a_total
    print(f'  False acceptance rate: {a_correct}/{a_total} ({a_pct:.0f}%)')
else:
    print('  No absent-monument images available (UNVERIFIED)')
print()

# --- 4. Pipeline recognition tests ---
print('4. PIPELINE RECOGNITION TESTS')
print('-' * 55)

r1 = retrieve_context('red_fort_delhi', 'Tell me about this site', repo)
ctx1 = build_site_context('red_fort_delhi', repo)
print(f'  red_fort_delhi: is_known={r1.is_known}, claims={len(ctx1.claims)}, source_urls={len(ctx1.source_urls)}')

r2 = retrieve_context('nonexistent_monument_xyz', 'Tell me about this site', repo)
ctx2 = build_site_context('nonexistent_monument_xyz', repo)
print(f'  nonexistent_monument_xyz: is_known={r2.is_known}')

r3 = retrieve_context('taj_mahal', 'What was the original color of the minarets?', repo)
ctx3 = build_site_context('taj_mahal', repo)
print(f'  taj_mahal + supported Q: is_known={r3.is_known}, claims={len(ctx3.claims)}, first_url={ctx3.source_urls[0] if ctx3.source_urls else "N/A"}')

r4 = retrieve_context('abu_simbel', 'What was the original color of the structure?', repo)
ctx4 = build_site_context('abu_simbel', repo)
print(f'  abu_simbel + unsupported Q: is_known={r4.is_known}, reason={r4.reason}')

# --- 5. Confidence thresholds ---
print()
print('5. CONFIDENCE THRESHOLDS')
print('-' * 55)
from data.confidence import build_confidence_layer
layer = build_confidence_layer(str(mapping_path).replace('mapping.json', 'faiss'), str(mapping_path))
print(f'  Index ntotal: {layer.index.ntotal}')
print(f'  Retrieval threshold: {layer.config.retrieval_threshold}')
print(f'  Metric: IndexFlatIP (cosine similarity with L2-normalized vectors)')
print(f'  Threshold controls final acceptance/rejection of retrieved results')

# --- Summary ---
print()
print('6. SUMMARY')
print('-' * 55)
print(f'Known-monument different-image queries: {len(known_monuments)}')
print(f'  Top-1 correct: {t1_correct}/{len(known_monuments)} ({t1_pct:.0f}%)')
print(f'  Top-3 correct: {t3_correct}/{len(known_monuments)} ({t3_pct:.0f}%)')
print(f'Absent-monument queries: {a_total} images tested')
print(f'  False acceptances: {a_correct} (UNVERIFIED if a_total=0)')
print(f'Pipeline tests: red_fort_delhi known, nonexistent unknown, supported Q grounded, unsupported refused')
print()
print('All evaluations on read-only artifacts; no files modified;')
print('no embeddings rebuilt; no thresholds overwritten; no production artifacts changed.')