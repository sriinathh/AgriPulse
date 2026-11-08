$ErrorActionPreference = "Stop"
$uri = "http://127.0.0.1:8000/fields"
# Read farmer ID and trim whitespace/newlines
$farmerId = (Get-Content -Path (Join-Path $PSScriptRoot "farmer_id.txt") -Raw).Trim()

$payload = @{
    farmer_id = $farmerId
    crop_type = "corn"
    name = "Test Field"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json" -Body $payload
    $response | ConvertTo-Json -Depth 10
    if ($response.field_id) {
        Set-Content -Path (Join-Path $PSScriptRoot "field_id.txt") -Value $response.field_id
        Write-Output "FIELD_ID=$($response.field_id)"
    }
}
catch {
    Write-Output "REQUEST_FAILED=$($_.Exception.Message)"
    if ($_.ErrorDetails.Message) { Write-Output $_.ErrorDetails.Message }
    exit 1
}
