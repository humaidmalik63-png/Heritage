import hashlib, os

artifacts = [
    'data/processed/index/clip_index.faiss',
    'data/processed/index/mapping.json',
    'data/processed/index/candidate/phase6ab_validation.faiss',
    'data/processed/index/candidate/phase6ab_validation_mapping.json',
]

expected = {
    'data/processed/index/clip_index.faiss': 'de32d554375c58c6cf6befc0c8cdf1268934e8814e48d53e4486d437e58caaa6',
    'data/processed/index/mapping.json': 'dbb135ff693ffcadab0ba701cf643854e1ece1baf19552083c0d1cb901ecd51c',
    'data/processed/index/candidate/phase6ab_validation.faiss': '4596388e8ae8dfd589ad49f9a85e23f78d332753fd58ed6fb43364b15dc14d98',
    'data/processed/index/candidate/phase6ab_validation_mapping.json': 'e25616c809ce118bc3d593e100e1d51ba291635455c27d0cc6db10e9ddc5fdf7',
]

print('=== FINAL ARTIFACT INTEGRITY ===')
all_ok = True
for art in artifacts:
    h = hashlib.sha256()
    with open(art, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    actual = h.hexdigest()
    exp = expected.get(art, '')
    match = actual == exp
    if not match:
        all_ok = False
    print(f'{art}: {\"MATCH\" if match else \"MISMATCH\"}')

print(f'\\nAll 4 artifacts intact: {all_ok}')

# List key files
print('\\n=== KEY FILES ===')
import os
key_files = [
    'PHASE8A_DEPLOYMENT_READINESS_REPORT.md',
    'data/evaluation/phase8a/phase8a_manifest.json',
    'data/evaluation/phase8a/phase8a_acquisition_plan.md',
    'data/evaluation/phase8a/phase8a_p0_collection_report.md',
    'data/evaluation/phase7y/phase7Y_final_report.md',
    'data/evaluation/phase7y/dataset_manifest.json',
    'data/evaluation/phase7y/phase7Z_visual_review.md',
]
for f in key_files:
    if os.path.exists(f):
        sz = os.path.getsize(f)
        print(f'  {f}: {sz} bytes')
    else:
        print(f'  {f}: MISSING')