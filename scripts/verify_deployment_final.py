import faiss
import json
import os

# Load active index after deployment
print("LOADING ACTIVE INDEX AFTER DEPLOYMENT")
index = faiss.read_index('C:/Users/humai/AI/data/processed/index/clip_index.faiss')
print(f'ACTIVE ntotal: {index.ntotal}, dimension: {index.d}')

# Load active mapping after deployment
with open('C:/Users/humai/AI/data/processed/index/mapping.json', 'r') as f:
    mapping = json.load(f)

print(f'ACTIVE mapping lengths: image_ids={len(mapping["image_ids"])}, paths={len(mapping["paths"])}, site_ids={len(mapping["site_ids"])}')
unique_sites = len(set(mapping['site_ids']))
print(f'ACTIVE unique site IDs: {unique_sites}')

print('ACTIVE SITE IDS:', mapping['site_ids'])

# Check catalogue
with open('C:/Users/humai/AI/data/metadata/global_monument_catalogue.json', 'r') as f:
    catalogue = json.load(f)
catalogue_sites = {c['site_id'] for c in catalogue}
missing_sites = [sid for sid in mapping['site_ids'] if sid not in catalogue_sites]
print(f'Missing catalogue sites: {missing_sites if missing_sites else "None"}')

# Check images
missing_images = []
for i, path in enumerate(mapping['paths']):
    full_path = os.path.join('C:/Users/humai/AI', path.replace('\\\\', '/').lstrip('/'))
    exists = os.path.exists(full_path)
    status = "EXISTS" if exists else "MISSING"
    print(f'Path {i}: {status} -> {path}')
    if not exists:
        missing_images.append(full_path)

print(f'\nMissing images count: {len(missing_images)}')
if missing_images:
    for m in missing_images:
        print(f'  - {m}')
else:
    print('All active images exist on disk!')
