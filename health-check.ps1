$ErrorActionPreference = "Stop"

$urls = @(
    "http://127.0.0.1:8080/api/health",
    "http://localhost:8080/api/health",
    "http://127.0.0.1:8080/api/dashboard"
)

foreach ($url in $urls) {
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
        Write-Host "[OK] $url" -ForegroundColor Green
        Write-Host $resp.Content
    }
    catch {
        Write-Host "[FAIL] $url" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }

    Write-Host "----------------------------------------"
}
