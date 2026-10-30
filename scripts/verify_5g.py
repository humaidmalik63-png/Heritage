import faiss, json, os

# Check active index
index = faiss.read_index('C:/Users/humai/AI/data/processed/index/clip_index.faiss')
print(f'Active Index: ntotal={index.ntotal}, dimension={index.d}')

# Check mapping
with open('C:/Users/humai/AI/data/processed/index/mapping.json', 'r') as f:
    mapping = json.load(f)

print(f'Mapping: image_ids={len(mapping["image_ids"])}, paths={len(mapping["paths"])}, site_ids={len(mapping["site_ids"])}')
unique_sites = len(set(mapping['site_ids']))
print(f'Unique Site IDs: {unique_sites}')

# Check paths exist
missing = 0
for path in mapping['paths']:
    clean_path = path.replace('\\\\', '/').lstrip('/')
    full = os.path.join('C:/Users/humai/AI', clean_path)
    if not os.path.exists(full):
        missing += 1
        print(f'  MISSING: {full}')
print(f'Missing images: {missing}')

# Check catalogue
with open('C:/Users/humai/AI/data/metadata/global_monument_catalogue.json', 'r') as f:
    catalogue = json.load(f)
cat_sites = {c['site_id'] for c in catalogue}
missing_from_cat = [s for s in set(mapping['site_ids']) if s not in cat_sites]
print(f'Site IDs not in catalogue: {missing_from_cat if missing_from_cat else "None"}')

# Check red_fort_delhi in mapping
red_entries = [s for s in mapping['site_ids'] if 'red_fort' in s]
print(f'Red Fort entries in mapping: {red_entries}')

# Verify jama_masjid_delhi too
jama_entries = [s for s in mapping['site_ids'] if 'jama_masjid' in s]
print(f'Jama Masjid entries in mapping: {jama_entries}')