# Change to backend folder
Set-Location -LiteralPath 'C:\Users\Arpitha Medharametla\Documents\smart-irrigation\backend'
# Run uvicorn from the virtual environment
& 'C:\Users\Arpitha Medharametla\Documents\smart-irrigation\.venv\Scripts\uvicorn.exe' app.main:app --host 127.0.0.1 --port 8001