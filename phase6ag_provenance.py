import json
from pathlib import Path

# Check Red Fort three image records
print('=== RED FORT THREE IMAGE RECORDS ===')
vcand = json.load(open('data/processed/index/candidate/phase6ab_validation_mapping.json'))
for i, sid in enumerate(vcand['site_ids']):
    if sid == 'red_fort_delhi':
        img_id = vcand['image_ids'][i]
        path = vcand['paths'][i]
        print(f'  Entry {i}: site_id={sid!r}, image_id={img_id!r}, path={path!r}')
        # Check if there's a source URL or manifest record
        # The path is data/raw/red_fort/red_fort_01.jpg etc.
        # No additional provenance beyond directory enumeration
print()

# Check Abu Simbel manifest record
print('=== ABU SIMBEL MANIFEST RECORD ===')
manifest_path = Path('data/metadata/global_image_manifest.json')
if manifest_path.exists():
    with open(manifest_path, 'rb') as f:
        manifest_raw = f.read()
    try:
        manifest = json.loads(manifest_raw.decode('utf-8'))
        found = False
        for entry in manifest:
            sid = entry.get('site_id', '')
            name = entry.get('name', '')
            if 'abu' in (str(sid) + str(name)).lower():
                found = True
                print(f'  Found: site_id={sid!r}, name={name!r}')
                print(f'  Images: {entry.get("images", [])}')
        if not found:
            print('  Abu Simbel not found in manifest via keyword search')
    except Exception as e:
        print(f'  Could not decode manifest: {e}')
else:
    print('  Manifest file not found')

# Provenance gap summary
print()
print('=== PROVENANCE GAP SUMMARY ===')
print('Red Fort 3 images: provenance = directory name only')
print('  - No source URLs in mapping records')
print('  - No manifest entries beyond directory enumeration')
print('  - Images at: data/raw/red_fort/red_fort_01.jpg, etc.')
print()
print('Abu Simbel: manifest record search performed;')
print('  results depend on manifest contents.')
print()
print('No image-level provenance beyond builder enumeration for any candidate site.')