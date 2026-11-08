$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot "backend"
$env:PYTHONPATH = "${backendDir};$env:PYTHONPATH"
& "${projectRoot}\.venv\Scripts\pytest.exe" -q