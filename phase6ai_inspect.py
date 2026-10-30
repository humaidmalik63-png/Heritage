#!/usr/bin/env python3
"""Phase 6AI Step 1 — Inspect candidate index and available images."""
import json, faiss, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load candidate index (read-only)
mapping_path = Path('data/processed/index/candidate/phase6ab_validation_mapping.json')
m = json.load(open(mapping_path))
i = faiss.read_index(str(mapping_path).replace('mapping.json', 'faiss'))

print('=== CANDIDATE INDEX INSPECTION ===')
print(f'FAISS vectors: {i.ntotal}')
print(f'Embedding dim: {i.d}')
print(f'Mapping entries: {len(m["site_ids"])}')
print()

# Build site_id -> positions
site_to_positions = {}
for pos, sid in enumerate(m['site_ids']):
    if sid not in site_to_positions:
        site_to_positions[sid] = []
    site_to_positions[sid].append(pos)

print('=== ALL SITES IN CANDIDATE INDEX ===')
for sid in sorted(site_to_positions.keys()):
    positions = site_to_positions[sid]
    print(f'  {sid}: {len(positions)} images')
    for pos in positions:
        img_id = m['image_ids'][pos]
        path = m['paths'][pos]
        exists = Path(path).exists()
        print(f'    - pos={pos} id={img_id} path={path} exists={exists}')
print()

# Check which of the 6 known monuments are in the candidate index
known = ['red_fort_delhi', 'taj_mahal', 'jama_masjid_delhi', 'qutub_minar', 'ajanta_caves', 'konark_sun_temple']
print('=== KNOWN MONUMENTS IN CANDIDATE INDEX ===')
for mon in known:
    if mon in site_to_positions:
        print(f'  {mon}: PRESENT ({len(site_to_positions[mon])} images)')
    else:
        print(f'  {mon}: ABSENT')
print()

# Check absent monuments
absent = ['elephanta_caves', 'hampi_monuments', 'hawa_mahal', 'fatehpur_sikri']
print('=== ABSENT MONUMENTS IN CANDIDATE INDEX ===')
for mon in absent:
    if mon in site_to_positions:
        print(f'  {mon}: PRESENT (unexpected)')
    else:
        print(f'  {mon}: ABSENT (expected)')
print()

# Check data/raw for absent monuments
print('=== DATA/RAW IMAGE AVAILABILITY FOR ABSENT MONUMENTS ===')
for mon in absent:
    raw_dir = Path(f'data/raw/{mon}')
    if raw_dir.exists():
        imgs = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            imgs.extend(raw_dir.glob(ext))
        print(f'  {mon}: {len(imgs)} images in data/raw/')
        for img in sorted(imgs)[:3]:
            print(f'    - {img.name}')
    else:
        print(f'  {mon}: NO data/raw/ directory')
print()

# Check data/raw for known monuments
print('=== DATA/RAW IMAGE AVAILABILITY FOR KNOWN MONUMENTS ===')
for mon in known:
    raw_dir = Path(f'data/raw/{mon}')
    if raw_dir.exists():
        imgs = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            imgs.extend(raw_dir.glob(ext))
        print(f'  {mon}: {len(imgs)} images in data/raw/')
        for img in sorted(imgs)[:3]:
            print(f'    - {img.name}')
    else:
        print(f'  {mon}: NO data/raw/ directory')