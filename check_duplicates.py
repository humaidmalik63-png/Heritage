import hashlib, os

# Get SHA-256 hashes of all existing images in data/raw/global/
global_dir = r'C:\Users\humai\AI\data\raw\global'
existing_hashes = {}

for site_dir in os.listdir(global_dir):
    site_path = os.path.join(global_dir, site_dir)
    if not os.path.isdir(site_path):
        continue
    for img_file in os.listdir(site_path):
        if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            img_path = os.path.join(site_path, img_file)
            try:
                with open(img_path, 'rb') as f:
                    sha256 = hashlib.sha256(f.read()).hexdigest()
                existing_hashes[img_file] = {
                    'site_id': site_dir,
                    'sha256': sha256,
                    'path': img_path
                }
            except Exception as e:
                print(f'Error reading {img_path}: {e}')

# Also check the new Abu Simbel image
abu_path = r'C:\Users\humai\AI\data\raw\global\abu_simbel\Abu_Simbel_Temples.jpg'
with open(abu_path, 'rb') as f:
    abu_sha256 = hashlib.sha256(f.read()).hexdigest()

print('Abu Simbel SHA-256:', abu_sha256)
print()

# Check for duplicates
print('=== Duplicate check ===')
abu_in_system = False
for fname, info in existing_hashes.items():
    if info['sha256'] == abu_sha256:
        print('DUPLICATE FOUND:', fname, 'from', info['site_id'])
        print('  SHA-256 matches:', abu_sha256)
        abu_in_system = True
    # Also check if it's a near-duplicate by comparing just the hash prefix
if not abu_in_system:
    print('No duplicate found - Abu Simbel image is unique in the system')

# List all existing hashes for reference
print()
print('=== Existing image hashes (first 10) ===')
count = 0
for fname, info in existing_hashes.items():
    if count >= 10:
        break
    print(f'  {fname}: {info["sha256"][:16]}...')
    count += 1

if len(existing_hashes) > 10:
    print(f'  ... and {len(existing_hashes) - 10} more')

print()
print('Total existing images:', len(existing_hashes))