import os

root = r'C:\Users\humai\AI'
print('AI root contents:')
for item in sorted(os.listdir(root)):
    full = os.path.join(root, item)
    if os.path.isdir(full):
        print(f'  [DIR] {item}')
        # List subdirs
        for sub in sorted(os.listdir(full)):
            subfull = os.path.join(full, sub)
            if os.path.isdir(subfull):
                img_count = 0
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                    img_count += len(list(Path(subfull).glob(ext)))
                print(f'    [DIR] {sub} ({img_count} images)')
            else:
                print(f'    [FILE] {sub}')
    elif os.path.isfile(full):
        print(f'  [FILE] {item}')