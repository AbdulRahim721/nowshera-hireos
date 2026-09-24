$pythonOk = Test-Path '.venv\Scripts\python.exe'
if (!$pythonOk) {
  try { py -3 --version | Out-Null; if ($LASTEXITCODE -eq 0) { py -3 -m venv .venv; $pythonOk = Test-Path '.venv\Scripts\python.exe' } } catch { $pythonOk = $false }
}
if ($pythonOk) {
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
} else {
  Write-Host 'Python is unavailable or broken. Starting HireFlow demo server with Node.js.' -ForegroundColor Yellow
  node server.mjs
}
