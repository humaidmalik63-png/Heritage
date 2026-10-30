import hashlib, os

image_path = 'data/raw/global/abu_simbel/Abu_Simbel_Temples.jpg'
full_path = 'C:\\Users\\humai\\AI\\' + image_path

print('File exists:', os.path.exists(full_path))
print('File size:', os.path.getsize(full_path), 'bytes')

# Compute SHA-256
with open(full_path, 'rb') as f:
    sha256 = hashlib.sha256(f.read()).hexdigest()
print('SHA-256:', sha256)
print('SHA-256 valid (64 hex chars):', len(sha256) == 64 and all(c in '0123456789abcdef' for c in sha256))

# Check file headers for JPEG signature
with open(full_path, 'rb') as f:
    header = f.read(8)
    print('File header (bytes):', header.hex())
    print('JPEG SOI marker:', header[:2] == b'\xff\xd8')