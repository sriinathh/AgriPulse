@echo off
set "PYTHONPATH=%CD%\\backend"
call ".venv\\Scripts\\pytest.exe" -vv
