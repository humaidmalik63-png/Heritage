$chrome = Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--headless=new', '--remote-debugging-port=9222', '--disable-gpu', 'http://127.0.0.1:8080/' -PassThru
Start-Sleep -Seconds 3
try {
    Write-Host "`n>>> RUNNING TEST SUITE 1: CAMERA & COMPACT CATALOGUE <<<`n"
    node scripts/test_camera_and_catalogue.js
    Write-Host "`n>>> RUNNING TEST SUITE 2: 7-SCREEN PAUSE & MOBILE RESPONSIVENESS <<<`n"
    node scripts/verify_all_requirements.js
} finally {
    if ($chrome -and -not $chrome.HasExited) {
        Stop-Process -Id $chrome.Id -ErrorAction SilentlyContinue
    }
}
