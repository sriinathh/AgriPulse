# PowerShell script to start FastAPI server using uvicorn from the virtual environment
$projectRoot = "C:\Users\Arpitha Medharametla\Documents\smart-irrigation"
# Ensure the project root is in PYTHONPATH for proper imports
$env:PYTHONPATH = $projectRoot
# Path to uvicorn executable inside the virtual environment
$uvicornPath = "$projectRoot\.venv\Scripts\uvicorn.exe"
# Launch the FastAPI app
Start-Process -NoNewWindow -FilePath $uvicornPath -ArgumentList "backend.app.main:app","--host","127.0.0.1","--port","8001","--reload"