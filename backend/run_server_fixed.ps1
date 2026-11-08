# PowerShell script to start FastAPI server
$pythonPath = "C:\Users\Arpitha Medharametla\Documents\smart-irrigation\.venv\Scripts\python.exe"
# Ensure PYTHONPATH includes project root for imports
$projectRoot = "C:\Users\Arpitha Medharametla\Documents\smart-irrigation"
$env:PYTHONPATH = $projectRoot
& "$pythonPath" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload