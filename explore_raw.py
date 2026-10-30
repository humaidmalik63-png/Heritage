import os
from pathlib import Path

raw_dir = Path('C:/Users/humai/AI/data/raw')
if raw_dir.exists():
    print("data/raw/ exists!")
    for site_dir in sorted(raw_dir.iterdir()):
        if site_dir.is_dir():
            img_count = len(list(site_dir.glob('*.jpg')) + list(site_dir.glob('*.jpeg')) + list(site_dir.glob('*.png')) + list(site_dir.glob('*.webp')))
            print(f"  {site_dir.name}: {img_count} images")
            for img in sorted(site_dir.glob('*.jpg'))[:2]:
                print(f"    - {img.name}")
else:
    print("data/raw/ does NOT exist")