import faiss
import json
import os
import shutil

# Load the current active index
active_index_path = 'C:/Users/humai/AI/data/processed/index/clip_index.faiss'
active_mapping_path = 'C:/Users/humai/AI/data/processed/index/mapping.json'

print(f'Active index: {active_index_path}')
print(f'Active mapping: {active_mapping_path}')

# Read active index
with open(active_index_path, 'rb') as f:
    active_index_bytes = f.read()

# Read active mapping
with open(active_mapping_path, 'r') as f:
    active_mapping = json.load(f)

print(f'\nACTIVE INDEX METRICS:')
print(f'Vector count: {len(active_index_bytes)} bytes (file size)')
print(f'Mapping lengths: image_ids={len(active_mapping["image_ids"])}, paths={len(active_mapping["paths"])}, site_ids={len(active_mapping["site_ids"])}')
unique_sites = len(set(active_mapping['site_ids']))
print(f'Unique site IDs: {unique_sites}')

# Check catalogue existence
with open('C:/Users/humai/AI/data/metadata/global_monument_catalogue.json', 'r') as f:
    catalogue = json.load(f)
catalogue_sites = {c['site_id'] for c in catalogue}
missing_sites = [sid for sid in active_mapping['site_ids'] if sid not in catalogue_sites]
print(f'Missing catalogue sites: {missing_sites if missing_sites else "None"}')

# Verify image paths
missing_images = []
for path in active_mapping['paths']:
    full_path = os.path.join('C:/Users/humai/AI', path.replace('\\', '/').lstrip('/'))
    if not os.path.exists(full_path):
        missing_images.append(full_path)

print(f'Missing images count: {len(missing_images)}')
if missing_images:
    print(f'First missing image: {missing_images[0]}')
else:
    print('All active images exist on disk!')

# Read backup index if it exists
backup_index_path = 'C:/Users/humai/AI/data/processed/index/tmp/clip_index_backup.faiss'
backup_mapping_path = 'C:/Users/humai/AI/data/processed/index/tmp/mapping_backup.json'

if os.path.exists(backup_index_path) and os.path.exists(backup_mapping_path):
    print(f'\nBACKUP INDEX METRICS:')
    with open(backup_index_path, 'rb') as f:
        backup_index_bytes = f.read()
    print(f'Backup vector count (file size): {len(backup_index_bytes)} bytes')
    
    with open(backup_mapping_path, 'r') as f:
        backup_mapping = json.load(f)
    print(f'Backup mapping lengths: image_ids={len(backup_mapping["image_ids"])}, paths={len(backup_mapping["paths"])}, site_ids={len(backup_mapping["site_ids"])}')
    backup_unique_sites = len(set(backup_mapping['site_ids']))
    print(f'Backup unique site IDs: {backup_unique_sites}')
    
    # Check backup image paths
    backup_missing_images = []
    for path in backup_mapping['paths']:
        full_path = os.path.join('C:/Users/humai/AI', path.replace('\\', '/').lstrip('/'))
        if not os.path.exists(full_path):
            backup_missing_images.append(full_path)
    
    print(f'Backup missing images count: {len(backup_missing_images)}')
    if backup_missing_images:
        print(f'First backup missing image: {backup_missing_images[0]}')
    else:
        print('All backup images exist on disk!')
