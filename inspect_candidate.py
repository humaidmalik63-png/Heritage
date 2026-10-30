import json, faiss
from pathlib import Path

m = json.load(open('data/processed/index/candidate/phase6ab_validation_mapping.json'))
i = faiss.read_index('data/processed/index/candidate/phase6ab_validation.faiss')

print('=== Candidate Index Inspection ===')
print(f'Vectors: {i.ntotal}')
print(f'Dimension: {i.d}')
print(f'Sites in mapping: {len(m["site_ids"])}')
print(f'Unique sites: {len(set(m["site_ids"]))}')
print(f'Site IDs: {sorted(set(m["site_ids"]))}')

# Check for key sites
key_sites = ['red_fort_delhi', 'jama_masjid_delhi', 'abu_simbel', 'taj_mahal', 'qutub_minar', 'ajanta_caves', 'konark_sun_temple']
for s in key_sites:
    present = s in set(m['site_ids'])
    print(f'  {s}: {\"PRESENT\" if present else \"MISSING\"}')

# Check image counts per site
site_to_imgs = {}
for i, sid in enumerate(m['site_ids']):
    if sid not in site_to_imgs:
        site_to_imgs[sid] = []
    site_to_imgs[sid].append({
        'image_id': m['image_ids'][i],
        'path': m['paths'][i]
    })

for sid in sorted(site_to_imgs.keys()):
    imgs = site_to_imgs[sid]
    print(f'  {sid}: {len(imgs)} images')
    for img in imgs[:1]:  # Show first image per site
        print(f'    - {img["image_id"]}: {img["path"]}')