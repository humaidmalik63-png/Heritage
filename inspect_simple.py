import json, faiss

m = json.load(open('data/processed/index/candidate/phase6ab_validation_mapping.json'))
i = faiss.read_index('data/processed/index/candidate/phase6ab_validation.faiss')

print('Vectors:', i.ntotal)
print('Dim:', i.d)
print('Sites:', len(m['site_ids']), 'unique:', len(set(m['site_ids'])))
sites = sorted(set(m['site_ids']))
for s in sites:
    print('  ', s)