import json
import os

# Load current mapping
with open('C:/Users/humai/AI/data/processed/index/mapping.json', 'r') as f:
    mapping = json.load(f)

# Correct the red_fort site IDs to red_fort_delhi
print('Before correction:')
for i, site in enumerate(mapping['site_ids']):
    if site == 'red_fort':
        print(f'  Entry {i}: red_fort -> red_fort_delhi')

for i, site in enumerate(mapping['site_ids']):
    if site == 'red_fort':
        mapping['site_ids'][i] = 'red_fort_delhi'

# Save corrected mapping
with open('C:/Users/humai/AI/data/processed/index/mapping.json', 'w') as f:
    json.dump(mapping, f, indent=2)

print('\nAfter correction:')
with open('C:/Users/humai/AI/data/processed/index/mapping.json', 'r') as f:
    mapping = json.load(f)
for i, site in enumerate(mapping['site_ids']):
    if site.startswith('red_fort') or site.startswith('jama'):
        print(f'  Entry {i}: {site}')
