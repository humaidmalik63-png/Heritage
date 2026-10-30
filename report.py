#!/usr/bin/env python3
import json, faiss
from pathlib import Path

# Load candidate index and mapping (read-only)
mapping_path = Path('data/processed/index/candidate/phase6ab_validation_mapping.json')
faiss_path = Path('data/processed/index/candidate/phase6ab_validation.faiss')

m = json.load(open(mapping_path))
i = faiss.read_index(str(faiss_path))

print('=== CANDIDATE INDEX INSPECTION ===')
print(f'FAISS vectors: {i.ntotal}')
print(f'Embedding dimension: {i.d}')
print(f'Mapping entries: {len(m["site_ids"])}')
print(f'Unique site IDs: {len(set(m["site_ids"]))}')
print()

# List all site IDs
sites = sorted(set(m['site_ids']))
print('Site IDs in candidate index:')
for s in sites:
    print(f'  {s}')
print()

# Check for key sites
key_sites = ['red_fort_delhi', 'jama_masjid_delhi', 'abu_simbel', 'taj_mahal',
             'qutub_minar', 'ajanta_caves', 'konark_sun_temple', 'hawa_mahal',
             'fatehpur_sikri', 'elephanta_caves']
print('Key site presence check:')
for s in key_sites:
    present = s in set(m['site_ids'])
    status = 'PRESENT' if present else 'MISSING'
    print(f'  {s:30s} : {status}')
print()

# Check image counts per site
site_to_imgs = {}
for idx_pos, sid in enumerate(m['site_ids']):
    if sid not in site_to_imgs:
        site_to_imgs[sid] = []
    site_to_imgs[sid].append({
        'image_id': m['image_ids'][idx_pos],
        'path': m['paths'][idx_pos]
    })

print('Images per site (first 3 sites shown):')
count = 0
for sid in sorted(site_to_imgs.keys()):
    if count >= 3:
        break
    imgs = site_to_imgs[sid]
    print(f'  {sid}: {len(imgs)} images')
    for img in imgs[:1]:
        print(f'    - {img["image_id"]}: {img["path"]}')
    count += 1

if len(site_to_imgs) > 3:
    print(f'  ... and {len(site_to_imgs) - 3} more sites')
print()

# Check absent sites
absent_monuments = ['elephanta_caves', 'hampi_monuments', 'hawa_mahal', 'fatehpur_sikri']
print('Absent-monument presence check:')
for mon in absent_monuments:
    present = mon in set(m['site_ids'])
    print(f'  {mon:30s} : {\"PRESENT\" if present else "ABSENT"}')
print()