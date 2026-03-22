$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $root "logs\server.pid"

if (Test-Path $pidFile) {
    $pidText = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    $pidNum = 0
    [int]::TryParse($pidText, [ref]$pidNum) | Out-Null

    if ($pidNum -gt 0) {
        try {
            Stop-Process -Id $pidNum -Force -ErrorAction Stop
            Write-Host "已停止服务 PID=$pidNum" -ForegroundColor Green
        }
        catch {
            Write-Host "停止 PID=$pidNum 失败: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

$conn = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    $procIds = $conn | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $procIds) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Host "已额外停止 8080 占用 PID=$procId" -ForegroundColor Yellow
        }
        catch {}
    }
}
