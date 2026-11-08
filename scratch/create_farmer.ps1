$ErrorActionPreference = "Stop"
$uri = "http://127.0.0.1:8000/farmers"

$payload = @{
    name  = "Milestone2 Test Farm"
    phone = "555-123-4567"
    email = "milestone2@example.test"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json" -Body $payload
    $response | ConvertTo-Json -Depth 10

    if ($response.farmer_id) {
        Set-Content -Path (Join-Path $PSScriptRoot "farmer_id.txt") -Value $response.farmer_id
        Write-Output "FARMER_ID=$($response.farmer_id)"
    }
}
catch {
    Write-Output "REQUEST_FAILED=$($_.Exception.Message)"
    if ($_.ErrorDetails.Message) {
        Write-Output $_.ErrorDetails.Message
    }
    exit 1
}