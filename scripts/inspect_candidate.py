import faiss
import json
import os

# Load candidate index
index = faiss.read_index('C:/Users/humai/AI/data/processed/index/tmp/clip_index.faiss')
print(f'Candidate ntotal: {index.ntotal}, dimension: {index.d}')

# Load candidate mapping
with open('C:/Users/humai/AI/data/processed/index/tmp/mapping.json', 'r') as f:
    mapping = json.load(f)

print(f'Candidate mapping lengths: image_ids={len(mapping["image_ids"])}, paths={len(mapping["paths"])}, site_ids={len(mapping["site_ids"])}')
unique_sites = len(set(mapping['site_ids']))
print(f'Unique site IDs: {unique_sites}')

# Check catalogue existence
with open('C:/Users/humai/AI/data/metadata/global_monument_catalogue.json', 'r') as f:
    catalogue = json.load(f)
catalogue_sites = {c['site_id'] for c in catalogue}
missing_sites = [sid for sid in mapping['site_ids'] if sid not in catalogue_sites]
print(f'Missing catalogue sites: {missing_sites if missing_sites else "None"}')

# Verify image paths
missing_images = []
for path in mapping['paths']:
    full_path = os.path.join('C:/Users/humai/AI', path.replace('\\', '/').lstrip('/'))
    if not os.path.exists(full_path):
        missing_images.append(full_path)

print(f'Missing images count: {len(missing_images)}')
if missing_images:
    print(f'First missing image: {missing_images[0]}')
else:
    print('All candidate images exist on disk!')
