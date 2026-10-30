import os
from pathlib import Path

root = r'C:\Users\humai\AI'
data_dir = os.path.join(root, 'data')
print(f"data dir exists: {os.path.exists(data_dir)}")

if os.path.exists(data_dir):
    print(f"\ndata contents: {os.listdir(data_dir)}")

    raw_dir = os.path.join(data_dir, 'raw')
    print(f"\nraw dir exists: {os.path.exists(raw_dir)}")
    if os.path.exists(raw_dir):
        print(f"raw dir contents: {os.listdir(raw_dir)}")
        for site_dir in sorted(os.listdir(raw_dir)):
            site_path = os.path.join(raw_dir, site_dir)
            if os.path.isdir(site_path):
                imgs = []
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                    imgs.extend(Path(site_path).glob(ext))
                print(f"  {site_dir}: {len(imgs)} images")
                for img in sorted(imgs)[:3]:
                    print(f"    - {img.name}")