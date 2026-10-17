import json, sys

f = sys.argv[1]
want = set(sys.argv[2:])
mapping = {}
for ln in open(f, encoding='utf-8').read().splitlines():
    try:
        o = json.loads(ln)
    except Exception:
        continue
    if o.get('type') != 'file-history-snapshot':
        continue
    snap = o.get('snapshot') or {}
    for path, info in (snap.get('trackedFileBackups') or {}).items():
        p = path.replace('\\', '/')
        if p in want or any(p.endswith(w) for w in want):
            mapping.setdefault(p, []).append((info.get('backupFileName'), info.get('version')))
for k, v in sorted(mapping.items()):
    print(k, '->', v)