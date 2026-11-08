$r = Invoke-WebRequest -Uri http://127.0.0.1:8000/health -UseBasicParsing
Write-Output "StatusCode=$($r.StatusCode)"
Write-Output "Body=$($r.Content)"
