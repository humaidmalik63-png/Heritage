import hashlib, os
from PIL import Image

image_path = r'data/raw/global/abu_simbel/Abu_Simbel_Temples.jpg'

# Build full path manually
drive, rest = os.path.splitdrive('C:\\Users\\humai\\AI')
full_path = os.path.join(drive, 'Users', 'humai', 'AI', image_path.replace('/', os.sep))

print('Full path:', full_path)
print('File exists:', os.path.exists(full_path))
print('File size:', os.path.getsize(full_path), 'bytes')

try:
    img = Image.open(full_path)
    print('Format:', img.format)
    print('Dimensions:', img.size)  # (width, height)
    print('Mode:', img.mode)

    # Compute SHA-256
    with open(full_path, 'rb') as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    print('SHA-256:', sha256)
    print('SHA-256 valid (64 hex chars):', len(sha256) == 64 and all(c in '0123456789abcdef' for c in sha256))
except Exception as e:
    print('Error opening image:', type(e).__name__, str(e))