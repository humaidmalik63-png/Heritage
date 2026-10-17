import faiss
import json
import re

index = faiss.read_index('data/processed/index/clip_index.faiss')
print(f'Index dimension: {index.d}')
print(f'Index size (ntotal): {index.ntotal}')
print(f'Index type: {type(index)}')

with open('data/processed/index/mapping.json') as f:
    mapping = json.load(f)
print(f'Image IDs count: {len(mapping["image_ids"])}')
print(f'Image IDs: {mapping["image_ids"]}')

_IMAGE_INDEX_SUFFIX = re.compile(r'_\d+$')
def parse_site_id(image_id):
    return _IMAGE_INDEX_SUFFIX.sub('', image_id)

site_ids = [parse_site_id(img_id) for img_id in mapping['image_ids']]
print(f'Derived site_ids: {site_ids}')
print(f'Unique site_ids: {set(site_ids)}')

with open('data/metadata/heritage_metadata.json') as f:
    metadata = json.load(f)
print(f'\nMetadata sites: {[m["id"] for m in metadata]}')