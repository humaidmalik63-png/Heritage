#!/usr/bin/env python3
"""Phase 7C — Controlled Candidate Integration Tests"""
import json, faiss, sys
from pathlib import Path

ROOT = Path('C:/Users/humai/AI')
sys.path.insert(0, str(ROOT))

from data.evidence.loader import load_repository, EvidenceRepository
from rag.retriever import retrieve_context, build_site_context
from ml.visual_embedding import VisualEmbeddingExtractor
from ml.confidence import build_confidence_layer

print('=' * 60)
print('PHASE 7C — CONTROLLED CANDIDATE INTEGRATION TESTS')
print('=' * 60)
print()

# Load candidate artifacts (read-only)
cand_idx = ROOT / 'data/processed/index/candidate/phase6ab_validation.faiss'
cand_map = ROOT / 'data/processed/index/candidate/phase6ab_validation_mapping.json'
faiss_idx = faiss.read_index(str(cand_idx))
cand_map_data = json.load(open(cand_map))
print(f'Candidate FAISS: {faiss_idx.ntotal} vectors, {faiss_idx.d} dim')
print(f'Candidate mapping: {len(cand_map_data["site_ids"])} entries')
print()

# Load production artifacts (read-only)
prod_idx_path = ROOT / 'data/processed/index/clip_index.faiss'
prod_map_path = ROOT / 'data/processed/index/mapping.json'
prod_idx = faiss.read_index(str(prod_idx_path))
prod_map = json.load(open(prod_map_path))
print(f'Production FAISS: {prod_idx.ntotal} vectors, {prod_idx.d} dim')
print(f'Production mapping: {len(prod_map["image_ids"])} entries')
print()

# Load evidence repository
repo = load_repository()

# Build site_id -> positions for candidate
site_to_positions = {}
for pos, sid in enumerate(cand_map_data['site_ids']):
    if sid not in site_to_positions:
        site_to_positions[sid] = []
    site_to_positions[sid].append(pos)

known_monuments = ['red_fort_delhi', 'taj_mahal', 'jama_masjid_delhi', 'qutub_minar',
                   'ajanta_caves', 'konark_sun_temple']

extractor = VisualEmbeddingExtractor()

# Helper: extract embedding from file path
def get_embedding(img_path):
    p = ROOT / img_path
    if p.exists():
        return extractor.extract(str(p))
    return None

results = []

# ==========================================
# CASE 1: Supported monument with metadata and evidence
# ==========================================
print('1. Supported monument with metadata and evidence (taj_mahal)')
print('-' * 60)

# Test with retrieve_context (uses production repo with normalization)
r1 = retrieve_context('taj_mahal', 'Tell me about this site', repo)
ctx1 = build_site_context('taj_mahal', repo)
results.append({
    'case': 'supported_monument',
    'input': 'taj_mahal + natural language question',
    'retrieved_site_id': r1.site_id if hasattr(r1, 'site_id') else 'N/A',
    'is_known': r1.is_known,
    'claims': len(r1.claims),
    'source_urls': len(r1.source_urls),
    'answer_outcome': 'grounded' if r1.is_known and r1.claims else 'unavailable',
})

print(f'  is_known: {r1.is_known}')
print(f'  claims: {len(r1.claims)}')
print(f'  source_urls: {len(r1.source_urls)}')
print(f'  first_url: {r1.source_urls[0] if r1.source_urls else "N/A"}')
print()

# ==========================================
# CASE 2: Red Fort using canonical ID red_fort_delhi
# ==========================================
print('2. Red Fort using canonical ID red_fort_delhi')
print('-' * 60)

# Test with retrieve_context using canonical ID
r2 = retrieve_context('red_fort_delhi', 'Tell me about this site', repo)
ctx2 = build_site_context('red_fort_delhi', repo)
results.append({
    'case': 'red_fort_canonical',
    'input': 'red_fort_delhi + natural language question',
    'retrieved_site_id': 'red_fort_delhi',
    'is_known': r2.is_known,
    'claims': len(r2.claims),
    'source_urls': len(r2.source_urls),
    'answer_outcome': 'grounded' if r2.is_known and r2.claims else 'unavailable',
})

print(f'  is_known: {r2.is_known}')
print(f'  claims: {len(r2.claims)}')
print(f'  source_urls: {len(r2.source_urls)}')
print()

# ==========================================
# CASE 3: Jama Masjid using canonical ID jama_masjid_delhi
# ==========================================
print('3. Jama Masjid using canonical ID jama_masjid_delhi')
print('-' * 60)

r3 = retrieve_context('jama_masjid_delhi', 'Tell me about this site', repo)
ctx3 = build_site_context('jama_masjid_delhi', repo)
results.append({
    'case': 'jama_masjid_canonical',
    'input': 'jama_masjid_delhi + natural language question',
    'retrieved_site_id': 'jama_masjid_delhi',
    'is_known': r3.is_known,
    'claims': len(r3.claims),
    'source_urls': len(r3.source_urls),
    'answer_outcome': 'grounded' if r3.is_known and r3.claims else 'unavailable',
})

print(f'  is_known: {r3.is_known}')
print(f'  claims: {len(r3.claims)}')
print(f'  source_urls: {len(r3.source_urls)}')
print()

# ==========================================
# CASE 4: Abu Simbel (previously reported missing metadata)
# ==========================================
print('4. Abu Simbel (previously reported missing metadata)')
print('-' * 60)

r4 = retrieve_context('abu_simbel', 'Tell me about this site', repo)
ctx4 = build_site_context('abu_simbel', repo)
results.append({
    'case': 'abu_simbel',
    'input': 'abu_simbel + natural language question',
    'retrieved_site_id': 'abu_simbel',
    'is_known': r4.is_known,
    'claims': len(r4.claims),
    'source_urls': len(r4.source_urls),
    'answer_outcome': 'supported' if r4.is_known and r4.claims else 'unsupported' if not r4.is_known and r4.reason else 'unavailable',
})

print(f'  is_known: {r4.is_known}')
print(f'  reason: {r4.reason if hasattr(r4, "reason") else "N/A"}')
print(f'  claims: {len(r4.claims)}')
print(f'  source_urls: {len(r4.source_urls)}')
print()

# ==========================================
# CASE 5: Unknown or unsupported monument query
# ==========================================
print('5. Unknown or unsupported monument query')
print('-' * 60)

r5 = retrieve_context('nonexistent_monument_xyz', 'Tell me about this site', repo)
ctx5 = build_site_context('nonexistent_monument_xyz', repo)
results.append({
    'case': 'unknown_monument',
    'input': 'nonexistent_monument_xyz + natural language question',
    'retrieved_site_id': 'nonexistent_monument_xyz',
    'is_known': r5.is_known,
    'claims': len(r5.claims),
    'answer_outcome': 'rejected' if not r5.is_known else 'unavailable',
})

print(f'  is_known: {r5.is_known}')
print(f'  outcome: {r5.reason if hasattr(r5, "reason") else "N/A"}')
print()

# ==========================================
# CASE 6: Supported monument with unsupported factual question
# ==========================================
print('6. Supported monument with unsupported factual question')
print('-' * 60)

r6 = retrieve_context('taj_mahal', 'What was the original color of the structure?', repo)
ctx6 = build_site_context('taj_mahal', repo)
results.append({
    'case': 'supported_unsupported_question',
    'input': 'taj_mahal + unsupported factual question',
    'retrieved_site_id': 'taj_mahal',
    'is_known': r6.is_known,
    'claims': len(r6.claims),
    'source_urls': len(r6.source_urls),
    'answer_outcome': 'supported' if r6.is_known and r6.claims else 'unsupported' if not r6.is_known and hasattr(r6, 'reason') and r6.reason else 'unavailable',
    'reason': r6.reason if hasattr(r6, 'reason') else None,
})

print(f'  is_known: {r6.is_known}')
print(f'  reason: {r6.reason if hasattr(r6, "reason") else "N/A"}')
print()

# ==========================================
# Additional: Same-image smoke tests (read only)
# ==========================================
print('7. Same-image smoke tests (read-only verification)')
print('-' * 60)

same_image_correct = 0
same_image_total = 0
for pos in range(min(28, faiss_idx.ntotal)):
    img_id = cand_map_data['image_ids'][pos]
    site_id = cand_map_data['site_ids'][pos]
    img_path = ROOT / cand_map_data['paths'][pos]
    if img_path.exists():
        emb = get_embedding(cand_map_data['paths'][pos])
        if emb is not None:
            scores, indices = faiss_idx.search(emb.reshape(1, -1), 5)
            self_site = cand_map_data['site_ids'][indices[0][1]] if indices[0][1] >= 0 else 'N/A'
            same_image_total += 1
            if self_site == site_id:
                same_image_correct += 1

same_pct = 100 * same_image_correct / same_image_total if same_image_total > 0 else 0
print(f'  Same-image self-matches: {same_image_correct}/{same_image_total} ({same_pct:.0f}%)')
print()

# ==========================================
# Summary
# ==========================================
print('8. SUMMARY')
print('-' * 60)
total_cases = len(results)
passed = sum(1 for r in results if r.get('answer_outcome') in ['grounded', 'supported', 'rejected'])
failed = sum(1 for r in results if r.get('answer_outcome') not in ['grounded', 'supported', 'rejected'])

print(f'Total pipeline test cases: {total_cases}')
print(f'Passed (grounded/supported/rejected): {passed}')
print(f'Failed/unavailable: {failed}')
print()
print('Case results:')
for r in results:
    outcome = r.get('answer_outcome', 'N/A')
    print(f'  {r["case"]:35s}: {outcome}')
print()
print('Key findings:')
print(f'  - Supported monument (taj_mahal): is_known={results[0]["is_known"]}, claims={results[0]["claims"]}')
print(f'  - Red Fort canonical (red_fort_delhi): is_known={results[1]["is_known"]}, claims={results[1]["claims"]}')
print(f'  - Jama Masjid canonical (jama_masjid_delhi): is_known={results[2]["is_known"]}, claims={results[2]["claims"]}')
print(f'  - Abu Simbel: is_known={results[3]["is_known"]}, reason={results[3].get("reason", "N/A")}')
print(f'  - Unknown monument: is_known={results[4]["is_known"]}')
print(f'  - Supported + unsupported Q: is_known={results[5]["is_known"]}, reason={results[5].get("reason", "N/A")}')
print()
print('All evaluations on read-only artifacts; no files modified;')
print('no embeddings rebuilt; no thresholds overwritten; no production artifacts changed.')
print('No artifacts deployed or promoted.')