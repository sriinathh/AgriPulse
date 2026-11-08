$ErrorActionPreference = "Stop"
$uri = "http://127.0.0.1:8000/irrigation/predict"
$payload = @{
    # days_after_sowing omitted to trigger validation error
    soil_moisture_0600 = 25.0
    soil_moisture_change_24h = -2.5
    temperature_0600 = 28.0
    humidity_0600 = 55.0
    rain_prev24h_mm = 0.0
    rain_forecast_next24h_mm = 1.2
    irrigation_prev7d_mm = 15.0
    days_since_irrigation = 5
    crop_type = "wheat"
    soil_type = "loam"
    irrigation_type = "drip"
    growth_stage = "vegetative"
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json" -Body $payload -ErrorAction Stop
    Write-Output ($response | ConvertTo-Json -Depth 5)
} catch {
    Write-Error $_
}
