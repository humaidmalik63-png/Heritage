#!/usr/bin/env python3
"""Phase 6AI Step 1 — Inspect candidate index and available images."""
import json, faiss, sys, os
from pathlib import Path

ROOT = Path('C:/Users/humai/AI')
sys.path.insert(0, str(ROOT))

# Load candidate index (read-only) with absolute paths
mapping_path = ROOT / 'data/processed/index/candidate/phase6ab_validation_mapping.json'
faiss_path = ROOT / 'data/processed/index/candidate/phase6ab_validation.faiss'

m = json.load(open(mapping_path))
i = faiss.read_index(str(faiss_path))

out = []
out.append('=== CANDIDATE INDEX INSPECTION ===')
out.append(f'FAISS vectors: {i.ntotal}')
out.append(f'Embedding dim: {i.d}')
out.append(f'Mapping entries: {len(m["site_ids"])}')
out.append('')

# Build site_id -> positions
site_to_positions = {}
for pos, sid in enumerate(m['site_ids']):
    if sid not in site_to_positions:
        site_to_positions[sid] = []
    site_to_positions[sid].append(pos)

out.append('=== ALL SITES IN CANDIDATE INDEX ===')
for sid in sorted(site_to_positions.keys()):
    positions = site_to_positions[sid]
    out.append(f'  {sid}: {len(positions)} images')
    for pos in positions:
        img_id = m['image_ids'][pos]
        path = m['paths'][pos]
        exists = (ROOT / path).exists()
        out.append(f'    - pos={pos} id={img_id} path={path} exists={exists}')
out.append('')

# Check which of the 6 known monuments are in the candidate index
known = ['red_fort_delhi', 'taj_mahal', 'jama_masjid_delhi', 'qutub_minar', 'ajanta_caves', 'konark_sun_temple']
out.append('=== KNOWN MONUMENTS IN CANDIDATE INDEX ===')
for mon in known:
    if mon in site_to_positions:
        out.append(f'  {mon}: PRESENT ({len(site_to_positions[mon])} images)')
    else:
        out.append(f'  {mon}: ABSENT')
out.append('')

# Check absent monuments
absent = ['elephanta_caves', 'hampi_monuments', 'hawa_mahal', 'fatehpur_sikri']
out.append('=== ABSENT MONUMENTS IN CANDIDATE INDEX ===')
for mon in absent:
    if mon in site_to_positions:
        out.append(f'  {mon}: PRESENT (unexpected)')
    else:
        out.append(f'  {mon}: ABSENT (expected)')
out.append('')

# Check data/raw for absent monuments
out.append('=== DATA/RAW IMAGE AVAILABILITY FOR ABSENT MONUMENTS ===')
for mon in absent:
    raw_dir = ROOT / 'data/raw' / mon
    if raw_dir.exists():
        imgs = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            imgs.extend(raw_dir.glob(ext))
        out.append(f'  {mon}: {len(imgs)} images in data/raw/')
        for img in sorted(imgs)[:3]:
            out.append(f'    - {img.name}')
    else:
        out.append(f'  {mon}: NO data/raw/ directory')
out.append('')

# Check data/raw for known monuments
out.append('=== DATA/RAW IMAGE AVAILABILITY FOR KNOWN MONUMENTS ===')
for mon in known:
    raw_dir = ROOT / 'data/raw' / mon
    if raw_dir.exists():
        imgs = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            imgs.extend(raw_dir.glob(ext))
        out.append(f'  {mon}: {len(imgs)} images in data/raw/')
        for img in sorted(imgs)[:3]:
            out.append(f'    - {img.name}')
    else:
        out.append(f'  {mon}: NO data/raw/ directory')

# Write output to file
out_path = ROOT / 'phase6ai_inspect_result.txt'
with open(out_path, 'w') as f:
    f.write('\n'.join(out))
print('Inspection complete. Written to', out_path)