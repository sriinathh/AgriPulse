@echo off
rem Set PYTHONPATH to backend directory
set "PYTHONPATH=%~dp0"
rem Use full path to python executable in virtual environment
"C:\Users\Arpitha Medharametla\Documents\smart-irrigation\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000