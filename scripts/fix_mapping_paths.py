import json
import os

# Load current mapping
with open('C:/Users/humai/AI/data/processed/index/mapping.json', 'r') as f:
    mapping = json.load(f)

# Define path corrections
path_corrections = {
    'data\\\\\\\\raw\\\\global\\\\jama_masjid': 'data\\\\\\\\raw\\\\jama_masjid',
    'data\\\\\\\\raw\\\\global\\\\red_fort': 'data\\\\\\\\raw\\\\red_fort',
}

# Apply corrections to each path
for i, path in enumerate(mapping['paths']):
    for old, new in path_corrections.items():
        if path.startswith(old):
            mapping['paths'][i] = new + path[len(old):]
            print(f'Fixed path {i}: {path} -> {mapping["paths"][i]}')
            break

# Verify the fixes
print('\nVerification:')
missing_images = []
for i, path in enumerate(mapping['paths']):
    full_path = os.path.join('C:/Users/humai/AI', path.replace('\\\\', '/').lstrip('/'))
    exists = os.path.exists(full_path)
    if not exists:
        missing_images.append(full_path)
    print(f'Path {i}: {"EXISTS" if exists else "MISSING"} -> {path}')

if missing_images:
    print(f'\nMissing images: {len(missing_images)}')
    for m in missing_images:
        print(f'  - {m}')
else:
    print('\nAll candidate images exist on disk!')

# Save corrected mapping
with open('C:/Users/humai/AI/data/processed/index/mapping.json', 'w') as f:
    json.dump(mapping, f, indent=2)

print('\nMapping saved with corrected paths.')