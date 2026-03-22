$ErrorActionPreference = "Stop"

Write-Host "[1/3] 清理 8080 端口占用..." -ForegroundColor Cyan
$conn = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    $procIds = $conn | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $procIds) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Host "已停止进程 PID=$procId" -ForegroundColor Yellow
        }
        catch {
            Write-Host "停止 PID=$procId 失败: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "8080 无占用" -ForegroundColor Green
}

Write-Host "[2/3] 设置 UTF-8 运行环境..." -ForegroundColor Cyan
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "[3/3] 启动数字公司服务..." -ForegroundColor Cyan
Write-Host "保持该窗口不要关闭。" -ForegroundColor Magenta
python -u .\main.py
