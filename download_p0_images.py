#!/usr/bin/env python
import urllib.request
import hashlib
import os
from PIL import Image

# Create the phase8a directory
os.makedirs('data/evaluation/phase8a', exist_ok=True)

# Known good Wikimedia Commons URLs for P0 monuments
# These are direct image URLs that should work
images_to_download = [
    # Qutub Minar - use a stable URL
    ('Qutub Minar', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Qutub_Minar_2.jpg/800px-Qutub_Minar_2.jpg', 'qutub_minar'),
    # If that fails, try alternative
    ('Qutub Minar alt', 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Qutub_Minar_3.jpg/800px-Qutub_Minar_3.jpg', 'qutub_minar'),
    # Konark Sun Temple
    ('Konark Sun Temple', 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/9e/Konark_Sun_Temple.jpg/800px-Konark_Sun_Temple.jpg', 'konark_sun_temple'),
    # Red Fort Delhi
    ('Red Fort Delhi', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Red_Fort_Lahore_Gate.jpg/800px-Red_Fort_Lahore_Gate.jpg', 'red_fort_delhi'),
]

for name, url, label in images_to_download:
    try:
        print(f'Downloading {label}...')
        urllib.request.urlretrieve(url, f'data/evaluation/phase8a/{label}.jpg')
        
        # Verify the file
        h = hashlib.sha256()
        with open(f'data/evaluation/phase8a/{label}.jpg', 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        
        size = os.path.getsize(f'data/evaluation/phase8a/{label}.jpg')
        print(f'  Downloaded: {label}.jpg, Size: {size} bytes, SHA-256: {h.hexdigest()[:32]}...')
        
        # Verify it's a valid image
        try:
            from PIL import Image
            img = Image.open(f'data/evaluation/phase8a/{label}.jpg')
            print(f'  Dimensions: {img.size}, Format: {img.format}')
        except Exception as e:
            print(f'  Not a valid image: {e}')
            # Remove the file if it's not valid
            os.remove(f'data/evaluation/phase8a/{label}.jpg')
            print(f'  Removed invalid file')
            
    except Exception as e:
        print(f'  Error downloading {label}: {e}')
" 2>&1