import json, sys

f = sys.argv[1]
want = set(sys.argv[2:])
seen = set()
for ln in open(f, encoding='utf-8').read().splitlines():
    try:
        o = json.loads(ln)
    except Exception:
        continue
    msg = o.get('message') or {}
    content = msg.get('content') if isinstance(msg, dict) else None
    if not isinstance(content, list):
        continue
    for c in content:
        if not isinstance(c, dict):
            continue
        if c.get('type') == 'tool_use' and c.get('name') == 'Read':
            fp = (c.get('input') or {}).get('file_path', '')
            if fp in want and fp not in seen:
                seen.add(fp)
                print('=== READ', fp, '===')
        if c.get('type') == 'tool_result':
            rc = c.get('content')
            if isinstance(rc, list):
                for cc in rc:
                    if isinstance(cc, dict) and cc.get('type') == 'text':
                        print(cc.get('text', ''))
                        print('=== END ===')