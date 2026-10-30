import faiss
import json
import os

# Load active index
print("LOADING ACTIVE INDEX")
index = faiss.read_index('C:/Users/humai/AI/data/processed/index/clip_index.faiss')
print(f'ACTIVE ntotal: {index.ntotal}, dimension: {index.d}')

# Load active mapping
with open('C:/Users/humai/AI/data/processed/index/mapping.json', 'r') as f:
    mapping = json.load(f)

print(f'ACTIVE mapping lengths: image_ids={len(mapping["image_ids"])}, paths={len(mapping["paths"])}, site_ids={len(mapping["site_ids"])}')
unique_sites = len(set(mapping['site_ids']))
print(f'ACTIVE unique site IDs: {unique_sites}')

# Print the actual site IDs
print('ACTIVE SITE IDS:', mapping['site_ids'])

# Load backup index
print("\nLOADING BACKUP INDEX")
backup_index = faiss.read_index('C:/Users/humai/AI/data/processed/index/tmp/clip_index_backup.faiss')
print(f'BACKUP ntotal: {backup_index.ntotal}, dimension: {backup_index.d}')

# Load backup mapping
with open('C:/Users/humai/AI/data/processed/index/tmp/mapping_backup.json', 'r') as f:
    backup_mapping = json.load(f)

print(f'BACKUP mapping lengths: image_ids={len(backup_mapping["image_ids"])}, paths={len(backup_mapping["paths"])}, site_ids={len(backup_mapping["site_ids"])}')
backup_unique_sites = len(set(backup_mapping['site_ids']))
print(f'BACKUP unique site IDs: {backup_unique_sites}')

# Print the actual site IDs
print('BACKUP SITE IDS:', backup_mapping['site_ids'])

# Load candidate index
print("\nLOADING CANDIDATE INDEX")
candidate_index = faiss.read_index('C:/Users/humai/AI/data/processed/index/tmp/clip_index.faiss')
print(f'CANDIDATE ntotal: {candidate_index.ntotal}, dimension: {candidate_index.d}')

# Load candidate mapping
with open('C:/Users/humai/AI/data/processed/index/tmp/mapping.json', 'r') as f:
    candidate_mapping = json.load(f)

print(f'CANDIDATE mapping lengths: image_ids={len(candidate_mapping["image_ids"])}, paths={len(candidate_mapping["paths"])}, site_ids={len(candidate_mapping["site_ids"])}')
candidate_unique_sites = len(set(candidate_mapping['site_ids']))
print(f'CANDIDATE unique site IDs: {candidate_unique_sites}')

# Print the actual site IDs
print('CANDIDATE SITE IDS:', candidate_mapping['site_ids'])
