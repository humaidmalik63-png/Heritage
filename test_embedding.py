import os
import sys
import hashlib
import numpy as np

interpreter = r"C:\Users\humai\AI\.venv312\Scripts\python.exe"

# Record SHA-256 of the four artifacts before
files_before = {}
file_paths = [
    r"data/processed/index/clip_index.faiss",
    r"data/processed/index/mapping.json",
    r"data/processed/index/candidate/phase6ab_validation.faiss",
    r"data/processed/index/candidate/phase6ab_validation_mapping.json",
]

for f_path in file_paths:
    full = os.path.join("C:/Users/humai/AI", f_path)
    if os.path.exists(full):
        with open(full, "rb") as fh:
            files_before[f_path] = hashlib.sha256(fh.read()).hexdigest()
        size = os.path.getsize(full)
        print(f"Before: {f_path}: SHA-256={files_before[f_path][:20]}... size={size} bytes")
    else:
        print(f"Before: {f_path}: NOT FOUND")

print()

# Test embedding
img_path = r"data/raw/red_fort/red_fort_01.jpg"
print(f"Testing embedding on: {img_path}")
print(f"File exists: {os.path.exists(img_path)}")

try:
    from ml.visual_embedding import VisualEmbeddingExtractor
    extractor = VisualEmbeddingExtractor()
    emb = extractor.extract(img_path)
    
    print(f"\nEmbedding shape: {emb.shape}")
    print(f"Embedding dtype: {emb.dtype}")
    print(f"All finite: {np.all(np.isfinite(emb))}")
    norm = np.linalg.norm(emb)
    print(f"L2 norm: {norm:.6f}")
    print(f"Is 512-dim: {emb.shape[0] == 512}")
    print(f"Norm close to 1.0: {abs(norm - 1.0) < 1e-5}")
    
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()

# Record SHA-256 after
files_after = {}
for f_path in file_paths:
    full = os.path.join("C:/Users/humai/AI", f_path)
    if os.path.exists(full):
        with open(full, "rb") as fh:
            files_after[f_path] = hashlib.sha256(fh.read()).hexdigest()
        size = os.path.getsize(full)
        before = files_before.get(f_path, "N/A")
        after = files_after[f_path]
        match = before == after
        print(f"{f_path}: {'MATCH' if match else 'MISMATCH'}")
        print(f"  Before:  {before[:20]}...")
        print(f"  After:   {after[:20]}...")

all_unchanged = all(files_before.get(f) == files_after.get(f) for f in file_paths if files_before.get(f))

print(f"\nAll four artifacts unchanged: {all_unchanged}")

# Final verdict
print("\n=== 5. Final verdict ===")
if 'emb' in dir():
    print("emb exists in local scope")
elif 'emb' in dir() if 'dir' in dir() else False:
    pass

# Check using different method
if 'emb' in dir():
    print("emb was created successfully")
    if __builtins__.shape and hasattr(__builtins__.shape, '__call__'):
        pass
    
# Direct check
if 'emb' in dir():
    s = __builtins__.shape(emb) if hasattr(__builtins__, 'shape') else 'N/A'
    print(f"shape call result: {s}")

# Check locals
import inspect
frame = inspect.currentframe()
locals_dict = frame.f_locals if frame else {}
if 'emb' in locals_dict:
    emb_val = locals_dict['emb']
    print(f"emb in locals: shape={emb_val.shape}, norm={np.linalg.norm(emb_val):.6f}")
    
if emb.shape[0] == 512 and abs(np.linalg.norm(emb) - 1.0) < 1e-5 and all_unchanged:
    print("✅ PASS: real image produces finite, normalized 512-dim embedding; all artifacts unchanged")
elif 'emb' in dir() or ('emb' in locals() if 'locals' in dir() else False):
    print("⚠️ PARTIAL: embedding works but criteria not fully met")
else:
    print("❌ FAIL: embedding generation did not produce valid result")