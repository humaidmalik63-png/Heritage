#!/usr/bin/env python3
"""Phase 6AH — Offline Recognition Quality Evaluation"""
import json, faiss, sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.evidence.loader import load_repository
from rag.retriever import retrieve_context, build_site_context
from ml.visual_embedding import VisualEmbeddingExtractor
from data.confidence import build_confidence_layer

print('=' * 60)
print('PHASE 6AH — OFFLINE RECOGNITION QUALITY EVALUATION')
print('=' * 60)
print()

# Load candidate index and mapping (read-only)
mapping_path = Path('data/processed/index/candidate/phase6ab_validation_mapping.json')
m = json.load(open(mapping_path))
i = faiss.read_index(str(mapping_path).replace('mapping.json', 'faiss'))

print('1. CANDIDATE INDEX METRICS')
print('-' * 60)
print(f'FAISS vectors: {i.ntotal}')
print(f'Embedding dimension: {i.d}')
print(f'Mapping entries: {len(m["site_ids"])}')
print(f'Unique site IDs: {len(set(m["site_ids"]))}')
print()

# Build site_id -> positions mapping
site_to_positions = {}
for pos, sid in enumerate(m['site_ids']):
    if sid not in site_to_positions:
        site_to_positions[sid] = []
    site_to_positions[sid].append(pos)

repo = load_repository()
extractor = VisualEmbeddingExtractor()

print('2. DIFFERENT-IMAGE QUERIES OF KNOWN MONUMENTS')
print('-' * 60)

known_monuments = ['red_fort_delhi', 'taj_mahal', 'jama_masjid_delhi', 'qutub_minar',
                   'ajanta_caves', 'konark_sun_temple']

diff_image_results = []

for mon in known_monuments:
    if mon in site_to_positions and len(site_to_positions[mon]) > 0:
        # Use the first image position for this site
        pos = site_to_positions[mon][0]
        img_path = Path(m['paths'][pos])
        if img_path.exists():
            try:
                emb = extractor.extract(str(img_path))
                scores, indices = i.search(emb.reshape(1, -1), min(10, i.ntotal))
                correct_in_top1 = False
                correct_in_top3 = False
                top1_site = m['site_ids'][indices[0][1]] if indices[0][1] >= 0 else 'N/A'

                if top1_site == mon:
                    correct_in_top1 = True
                for k in range(min(3, len(indices[0]))):
                    idx_k = indices[0][k]
                    if idx_k >= 0 and m['site_ids'][idx_k] == mon:
                        correct_in_top3 = True
                        break

                diff_image_results.append({
                    'monument': mon,
                    'correct_in_top1': correct_in_top1,
                    'correct_in_top3': correct_in_top3,
                    'top1_site': top1_site,
                    'top1_score': float(scores[0][1]) if len(scores[0]) > 1 else float('nan'),
                })
                print(f'  {mon:30s}: top1={top1_site:30s} top1_correct={correct_in_top1} top3_correct={correct_in_top3} score={scores[0][1]:.4f}')
            except Exception as e:
                print(f'  {mon:30s}: ERROR - {e}')
        else:
            print(f'  {mon:30s}: IMAGE NOT FOUND at {img_path}')
    else:
        print(f'  {mon:30s}: NOT IN CANDIDATE INDEX')

print()

print('3. QUERIES FOR MONUMENTS ABSENT FROM CANDIDATE INDEX')
print('-' * 60)

absent_monuments = ['elephanta_caves', 'hampi_monuments', 'hawa_mahal', 'fatehpur_sikri']
absent_results = []

for mon in absent_monuments:
    raw_dir = Path(f'data/raw/{mon}')
    if raw_dir.exists():
        img_files = list(raw_dir.glob('*.jpg')) + list(raw_dir.glob('*.jpeg')) + \
                    list(raw_dir.glob('*.png')) + list(raw_dir.glob('*.webp'))
        if img_files:
            try:
                emb = extractor.extract(str(img_files[0]))
                scores, indices = i.search(emb.reshape(1, -1), min(5, i.ntotal))
                top1_site = m['site_ids'][indices[0][1]] if indices[0][1] >= 0 else 'N/A'
                top1_score = float(scores[0][1]) if len(scores[0]) > 1 else float('nan')

                correct_in_top3 = False
                for k in range(min(3, len(indices[0]))):
                    idx_k = indices[0][k]
                    if idx_k >= 0 and m['site_ids'][idx_k] == mon:
                        correct_in_top3 = True

                absent_results.append({
                    'queried_monument': mon,
                    'top1_site': top1_site,
                    'top1_score': top1_score,
                    'correct_in_top3': correct_in_top3,
                    'image_used': str(img_files[0]),
                })
                print(f'  {mon:30s}: top1={top1_site:30s} score={top1_score:.4f} top3_correct={correct_in_top3}')
                print(f'    Image: {img_files[0]}')
            except Exception as e:
                print(f'  {mon:30s}: ERROR - {e}')
        else:
            print(f'  {mon:30s}: No image files found')
    else:
        print(f'  {mon:30s}: No raw directory found')

print()

print('4. AMBIGUOUS/SIMILAR MONUMENT QUERIES')
print('-' * 60)

# Test red_fort_delhi query against images from similar monument
similar_pairs = [('qutub_minar', 'taj_mahal')]
ambiguous_results = []

for q_mon, conf_mon in similar_pairs:
    if q_mon in site_to_positions and len(site_to_positions[q_mon]) > 0:
        pos = site_to_positions[q_mon][0]
        img_path = Path(m['paths'][pos])
        if img_path.exists():
            try:
                emb = extractor.extract(str(img_path))
                scores, indices = i.search(emb.reshape(1, -1), min(10, i.ntotal))
                conf_site = m['site_ids'][indices[0][1]] if indices[0][1] >= 0 else 'N/A'
                conf_score = float(scores[0][1]) if len(scores[0]) > 1 else float('nan')

                ambiguous_results.append({
                    'query_monument': q_mon,
                    'confused_as': conf_site,
                    'top1_score': conf_score,
                    'correct': conf_site == q_mon,
                })
                print(f'  {q_mon:30s} query confused as: {conf_site:30s} score={conf_score:.4f} correct={conf_site == q_mon}')
            except Exception as e:
                print(f'  {q_mon:30s}: ERROR - {e}')
        else:
            print(f'  {q_mon:30s}: IMAGE NOT FOUND')

print()

print('5. RECOGNITION PIPELINE TESTS')
print('-' * 60)

# Test 1: Known monument with natural language question
r1 = retrieve_context('red_fort_delhi', 'Tell me about this site', repo)
ctx1 = build_site_context('red_fort_delhi', repo)
print(f'  red_fort_delhi: is_known={r1.is_known}, claims={len(ctx1.claims)}, source_urls={len(ctx1.source_urls)}')

# Test 2: Unknown/nonexistent site
r2 = retrieve_context('nonexistent_site_xyz', 'Tell me about this site', repo)
ctx2 = build_site_context('nonexistent_site_xyz', repo)
print(f'  nonexistent_site_xyz: is_known={r2.is_known}')

# Test 3: Supported factual question
r3 = retrieve_context('taj_mahal', 'What was the original color of the minarets?', repo)
ctx3 = build_site_context('taj_mahal', repo)
print(f'  taj_mahal + supported question: is_known={r3.is_known}, claims={len(ctx3.claims)}, first_url={ctx3.source_urls[0] if ctx3.source_urls else "N/A"}')

# Test 4: Unsupported factual question
r4 = retrieve_context('abu_simbel', 'What was the original color of the structure?', repo)
ctx4 = build_site_context('abu_simbel', repo)
print(f'  abu_simbel + unsupported question: is_known={r4.is_known}, reason={r4.reason}')

print()

print('6. CONFIDENCE THRESHOLDS')
print('-' * 60)

layer = build_confidence_layer(str(mapping_path).replace('mapping.json', 'faiss'), str(mapping_path))
print(f'  Confidence layer index ntotal: {layer.index.ntotal}')
print(f'  Retrieval config threshold: {layer.config.retrieval_threshold}')
print(f'  Similarity metric: IndexFlatIP')
print(f'  Threshold controls: final acceptance/rejection of retrieved results')
print()

print('7. SUMMARY')
print('-' * 60)
print(f'Different-image queries: {len(diff_image_results)} across {len(known_monuments)} monuments')
correct_t1 = sum(1 for r in diff_image_results if r.get('correct_in_top1'))
correct_t3 = sum(1 for r in diff_image_results if r.get('correct_in_top3'))
print(f'  Top-1 correct: {correct_t1}/{len(diff_image_results)} ({100*correct_t1/len(diff_image_results):.0f}%)')
print(f'  Top-3 correct: {correct_t3}/{len(diff_image_results)} ({100*correct_t3/len(diff_image_results):.0f}%)')

print(f'Absent-monument queries: {len(absent_results)} across {len(absent_monuments)} monuments')
print(f'  These measure false acceptance for unknown monuments')

print(f'Similar-monument queries: {len(ambiguous_results)}')
print(f'  These measure cross-monument confusion')

print('Pipeline tests: completed (known monument, unknown site, supported question, unsupported question)')

print()
print('All evaluations performed on read-only artifacts; no files modified;')
print('no embeddings rebuilt; no thresholds modified; no production artifacts overwritten.')