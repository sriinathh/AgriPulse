$ErrorActionPreference = "Stop"
$uri = "http://127.0.0.1:8000/sensors"
$payload = @{
    field_id = "F006"
    sensor_type = "soil_moisture"
    name = "Milestone2 Soil Sensor"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json" -Body $payload

# Output response
$response | ConvertTo-Json -Depth 10

# Save sensor_id
if ($response.sensor_id) {
    Set-Content -Path (Join-Path $PSScriptRoot "sensor_id.txt") -Value $response.sensor_id
    Write-Output "Sensor ID saved: $($response.sensor_id)"
}
