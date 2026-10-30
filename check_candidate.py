import json

m = json.load(open('data/processed/index/candidate/phase6ab_validation_mapping.json'))
print('Sites in candidate:', len(m['site_ids']))
print('Unique sites:', len(set(m['site_ids'])))
print('Site IDs:', sorted(set(m['site_ids'])))

# Check for key sites
key_sites = ['red_fort_delhi', 'jama_masjid_delhi', 'abu_simbel', 'taj_mahal', 'qutub_minar']
for s in key_sites:
    print(f'  {s}: {\"PRESENT\" if s in set(m[\"site_ids\"]) else \"MISSING\"}')