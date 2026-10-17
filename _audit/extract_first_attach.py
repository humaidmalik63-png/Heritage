import json, sys

f = sys.argv[1]
want = set(sys.argv[2:])
seen = {}
for ln in open(f, encoding='utf-8').read().splitlines():
    try:
        o = json.loads(ln)
    except Exception:
        continue
    if o.get('type') != 'attachment':
        continue
    att = o.get('attachment') or {}
    if att.get('type') != 'file':
        continue
    fp = att.get('filename', '')
    if fp in want and fp not in seen:
        seen[fp] = att['content']['file']['content']
        print('=== FIRST ATTACH', fp, '===')
        print(att['content']['file']['content'])
        print('=== END ===')