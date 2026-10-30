import json, sys, io, chardet

# Detect encoding
with open('data/metadata/global_monument_catalogue.json', 'rb') as f:
    raw = f.read()
encoding = chardet.detect(raw)['encoding']
print(f'Detected encoding: {encoding}')

# Load catalogue
cat = json.loads(raw.decode(encoding))

# Search for Red Fort entries
red_fort_entries = [r for r in cat if 'red_fort' in r.get('name', '').lower()]
jama_masjid_entries = [r for r in cat if 'jama' in r.get('name', '').lower()]

print('=== Red Fort entries ===')
for r in red_fort_entries:
    print(f'  site_id: {r["site_id"]}')
    print(f'  name: {r["name"]}')
    print(f'  alternative_names: {r.get("alternate_names", [])}')
    print(f'  country: {r["country"]}')
    print(f'  region: {r.get("region", "")}')
    print(f'  city: {r.get("city", "")}')
    print(f'  type: {r.get("type", "")}')
    print(f'  period: {r.get("period", "")}')
    print()

print('=== Jama Masjid entries ===')
for r in jama_masjid_entries:
    print(f'  site_id: {r["site_id"]}')
    print(f'  name: {r["name"]}')
    print(f'  alternative_names: {r.get("alternate_names", [])}')
    print(f'  country: {r["country"]}')
    print()
"