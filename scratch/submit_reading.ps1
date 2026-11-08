$ErrorActionPreference = "Stop"
$uri = "http://127.0.0.1:8000/sensor/readings"
$payload = @{
    sensor_id = "SM007"
    field_id = "F006"
    soil_moisture = 28.5
    temperature = 22.4
    humidity = 45.0
    measurement_type = "soil_moisture"
    is_simulated = $false
    timestamp = (Get-Date -Format o)
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json" -Body $payload -ErrorAction Stop
    $status = 201
} catch {
    $errorResponse = $_.Exception.Response
    if ($errorResponse -ne $null) {
        $status = [int]$errorResponse.StatusCode.Value__
        $response = $errorResponse.GetResponseStream() | %{ New-Object System.IO.StreamReader($_) } | %{ $_.ReadToEnd() }
    } else { throw }
}

# Save response and status
$output = @{ status = $status; response = $response } | ConvertTo-Json -Depth 5
Set-Content -Path "C:\Users\Arpitha Medharametla\Documents\smart-irrigation\scratch\reading_response.txt" -Value $output -Encoding utf8

# If successful, extract reading_id and save
if ($status -eq 201) {
    $reading_id = $response.reading.reading_id
    Set-Content -Path "C:\Users\Arpitha Medharametla\Documents\smart-irrigation\scratch\reading_id.txt" -Value $reading_id -Encoding utf8
    Write-Output "Reading submitted with ID: $reading_id"
} else {
    Write-Output "Failed with status $status"
}
