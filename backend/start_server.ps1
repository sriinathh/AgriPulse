$env:PYTHONPATH = 'C:\Users\Arpitha Medharametla\Documents\smart-irrigation\backend'
Set-Location -LiteralPath 'C:\Users\Arpitha Medharametla\Documents\smart-irrigation\backend'
$uvicorn = 'C:\Users\Arpitha Medharametla\Documents\smart-irrigation\.venv\Scripts\uvicorn.exe'
$proc = Start-Process -FilePath $uvicorn -ArgumentList 'app.main:app','--host','127.0.0.1','--port','8001' -NoNewWindow -PassThru

