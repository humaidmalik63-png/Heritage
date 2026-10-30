import urllib.request, hashlib, json, os, re

# Try Aksum file variants
print('=== Trying Aksum file variants ===')
aksu_variants = [
    'Aksum_Stelae',
    'Aksum_Stela',
    'Aksum',
    'Ethiopian_Stelae',
]

for fname in aksu_variants:
    file_url = f'https://commons.wikimedia.org/wiki/File:{fname}.jpg'
    try:
        req = urllib.request.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            if status == 200:
                html = response.read().decode('utf-8')
                if 'Aksum' in html:
                    print(f'  {fname}: VALID (200, contains Aksum)')
                else:
                    print(f'  {fname}: 200 (ok)')
            else:
                print(f'  {fname}: HTTP {status}')
    except Exception as e:
        print(f'  {fname}: Error {e}')

print()
# Now let's actually download the Abu Simbel image from the valid file page
print('=== Downloading Abu Simbel image ===')
abu_file_page = 'https://commons.wikimedia.org/wiki/File:Abu_Simbel'

req = urllib.request.Request(abu_file_page, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as response:
    html = response.read().decode('utf-8')

# Extract the direct image file URL from the page
# The standard pattern on Commons is:
# https://upload.wikimedia.org/wikipedia/commons/thumb/xx/xx/Original_Name.jpg/original
original_pattern = r'href="(/wikipedia/commons/thumb/[^"]+?)"'
original_matches = re.findall(original_pattern, html)
if original_matches:
    print(f'Found {len(original_matches)} potential original links')
    for om in original_matches[:3]:
        full_url = f'https:{om}' if not om.startswith('http') else om
        print(f'  {full_url[:150]}...')
else:
    print('No original links found via this pattern')
    
# Look for any .jpg URLs in the page
jpg_pattern = r'href="([^"]+\.jpg)"'
jpg_matches = re.findall(jpg_pattern, html)
if jpg_matches:
    print(f'Found {len(jpg_matches)} .jpg references')
    for jm in jpg_matches[:5]:
        print(f'  {jm[:100]}...')
else:
    print('No .jpg references found via this pattern')