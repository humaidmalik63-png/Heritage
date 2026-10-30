import faiss, json, os

# 1. Catalogue site count and geographic distribution
with open('data/metadata/global_monument_catalogue.json', 'r') as f:
    catalogue = json.load(f)
cat_count = len(catalogue)
cat_countries = {}
cat_regions = {}
for c in catalogue:
    country = c.get('country', 'unknown')
    region = c.get('region', 'unknown')
    cat_countries[country] = cat_countries.get(country, 0) + 1
    cat_regions[region] = cat_regions.get(region, 0) + 1

print(f'=== CATALOGUE ===')
print(f'Total catalogue entries: {cat_count}')
print(f'Countries: {len(cat_countries)}')
for c, n in sorted(cat_countries.items(), key=lambda x: -x[1])[:20]:
    print(f'  {c}: {n}')
print(f'Regions: {len(cat_regions)}')
for r, n in sorted(cat_regions.items(), key=lambda x: -x[1])[:20]:
    print(f'  {r}: {n}')

# 2. Indexed sites, vectors, and images
index = faiss.read_index('data/processed/index/clip_index.faiss')
print(f'\\n=== ACTIVE INDEX ===')
print(f'Vectors (ntotal): {index.ntotal}')
print(f'Dimension: {index.d}')

with open('data/processed/index/mapping.json', 'r') as f:
    mapping = json.load(f)
image_count = len(mapping['image_ids'])
path_count = len(mapping['paths'])
site_ids = mapping['site_ids']
unique_sites = len(set(site_ids))
print(f'Image IDs: {image_count}')
print(f'Paths: {path_count}')
print(f'Unique site IDs: {unique_sites}')

# 3. Catalogue sites with usable local images
local_base = 'C:/Users/humai/AI/data/raw'
print(f'\\n=== LOCAL IMAGE CHECK ===')
local_image_count = 0
for i, path in enumerate(mapping['paths']):
    clean = path.replace('\\\\', '/').lstrip('/')
    full = os.path.join('C:/Users/humai/AI', clean)
    if os.path.exists(full):
        local_image_count += 1
print(f'Local images that exist: {local_image_count}/{image_count}')

# 4. Sites with evidence and metadata
from data.evidence.loader import load_repository
repo = load_repository()
indexed_sites = {i.rsplit('_', 1)[0] for i in mapping['image_ids']}
sites_with_meta = sum(1 for s in indexed_sites if repo.get_metadata(s) is not None)
sites_with_evidence = sum(1 for s in indexed_sites if repo.get_evidence(s))
print(f'\\n=== EVIDENCE/METADATA ===')
print(f'Sites with metadata: {sites_with_meta}/{len(indexed_sites)}')
print(f'Sites with evidence: {sites_with_evidence}/{len(indexed_sites)}')

# 5. Recognition coverage by country
print(f'\\n=== COUNTRY COVERAGE (catalogue) ===')
for country, n in sorted(cat_countries.items(), key=lambda x: -x[1])[:30]:
    print(f'  {country}: {n}')