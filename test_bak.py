#!/usr/bin/env python
import subprocess, sys, os, time, urllib.request

proc = subprocess.Popen(
    ['.venv312\\Scripts\\python', '-m', 'uvicorn', 'backend:app', '--host', '127.0.0.1', '--port', '8000'],
    cwd='C:\\Users\\humai\\AI',
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

time.sleep(8)

results = []
try:
    req = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)
    results.append(('HEALTH', req.status, req.read().decode()))
except Exception as e:
    results.append(('HEALTH', None, str(e)))

proc.terminate()
proc.wait(timeout=5)

print('=== BACKEND TEST RESULTS ===')
for name, status, text in results:
    if status:
        print(f'{name}: HTTP {status} - {text[:100]}...')
    else:
        print(f'{name}: FAILED - {text}')
" > /tmp/btest.log 2>&1