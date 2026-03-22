$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root "logs\server.pid"

if (!(Test-Path $pidFile)) {
    Write-Host "NO PID FILE. SERVICE MAY NOT BE RUNNING." -ForegroundColor Yellow
    exit 1
}

$pidText = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
$pidNum = 0
[int]::TryParse($pidText, [ref]$pidNum) | Out-Null

if ($pidNum -le 0) {
    Write-Host "INVALID PID FILE." -ForegroundColor Red
    exit 1
}

$proc = Get-Process -Id $pidNum -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "RUNNING PID=$pidNum" -ForegroundColor Green
} else {
    Write-Host "NOT RUNNING. PID=$pidNum NOT FOUND." -ForegroundColor Red
}
