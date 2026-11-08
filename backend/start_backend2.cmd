@echo on
call "C:\Users\Arpitha Medharametla\Documents\smart-irrigation\.venv\Scripts\activate.bat"
set PYTHONPATH=C:\Users\Arpitha Medharametla\Documents\smart-irrigation\backend
uvicorn app.main:app --host 127.0.0.1 --port 8001