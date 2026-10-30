import subprocess, sys, os, time, urllib.request

# Start the backend
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'backend:app', '--host', '127.0.0.1', '--port', '8000'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

# Wait for it to start
time.sleep(8)

# Try health endpoint
results = []
try:
    req = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)
    results.append(('HEALTH', req.status, req.read().decode()))
except Exception as e:
    results.append(('HEALTH', None, str(e)))

# Terminate the process
proc.terminate()
proc.wait(timeout=5)

# Print results
print('=== BACKEND TEST RESULTS ===')
for name, status, text in results:
    if status:
        print(f'{name}: HTTP {status} - {text[:100]}...')
    else:
        print(f'{name}: FAILED - {text}')
" > /tmp/backend_test.log 2>&1