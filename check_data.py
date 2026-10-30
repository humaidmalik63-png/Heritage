import os
from pathlib import Path

root = r'C:\Users\humai\AI'
data_dir = os.path.join(root, 'data')
print(f"data dir exists: {os.path.exists(data_dir)}")

if os.path.exists(data_dir):
    print(f"\ndata contents: {sorted(os.listdir(data_dir))}")

    # Check metadata
    meta_dir = os.path.join(data_dir, 'metadata')
    print(f"\nmetadata dir exists: {os.path.exists(meta_dir)}")
    if os.path.exists(meta_dir):
        print(f"metadata contents: {sorted(os.listdir(meta_dir))}")
        # Check global_image_manifest.json
        manifest = os.path.join(meta_dir, 'global_image_manifest.json')
        if os.path.exists(manifest):
            print(f"global_image_manifest.json exists, size: {os.path.getsize(manifest)} bytes")

    # Check processed index
    proc_dir = os.path.join(data_dir, 'processed', 'index')
    print(f"\nprocessed/index dir exists: {os.path.exists(proc_dir)}")
    if os.path.exists(proc_dir):
        print(f"processed/index contents: {sorted(os.listdir(proc_dir))}")

    # Check candidate
    cand_dir = os.path.join(data_dir, 'processed', 'index', 'candidate')
    print(f"\ncandidate dir exists: {os.path.exists(cand_dir)}")
    if os.path.exists(cand_dir):
        print(f"candidate contents: {sorted(os.listdir(cand_dir))}")