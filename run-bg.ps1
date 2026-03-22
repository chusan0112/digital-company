$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $root "logs"
if (!(Test-Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory | Out-Null
}

$stdout = Join-Path $logDir "server.out.log"
$stderr = Join-Path $logDir "server.err.log"
$pidFile = Join-Path $logDir "server.pid"

function Stop-Port8080 {
    $conn = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $procIds = $conn | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $procIds) {
            try {
                Stop-Process -Id $procId -Force -ErrorAction Stop
                Write-Host "STOPPED PID=$procId ON PORT 8080" -ForegroundColor Yellow
            }
            catch {
                Write-Host "FAILED TO STOP PID=$procId : $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

function Test-Health {
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8080/api/health" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) {
            return $true
        }
    }
    catch {}
    return $false
}

function Start-ServerProcess {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = "-u main.py"
    $psi.WorkingDirectory = $root
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.EnvironmentVariables["PYTHONUTF8"] = "1"
    $psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $null = $proc.Start()

    $proc.Id | Out-File -FilePath $pidFile -Encoding utf8 -Force
    return $proc
}

Stop-Port8080

$proc = Start-ServerProcess
Write-Host ("STARTED PID=" + $proc.Id) -ForegroundColor Green

$healthy = $false
for ($i = 1; $i -le 10; $i++) {
    Start-Sleep -Seconds 1

    if ($proc.HasExited) {
        break
    }

    if (Test-Health) {
        $healthy = $true
        break
    }
}

if ($healthy) {
    Write-Host "HEALTH CHECK PASSED: http://127.0.0.1:8080/api/health" -ForegroundColor Green
    Write-Host ("STDOUT=" + $stdout) -ForegroundColor Cyan
    Write-Host ("STDERR=" + $stderr) -ForegroundColor Cyan
    exit 0
}

Write-Host "START FAILED OR HEALTH CHECK TIMEOUT" -ForegroundColor Red

if ($proc -and !$proc.HasExited) {
    try { Stop-Process -Id $proc.Id -Force -ErrorAction Stop } catch {}
}

$out = ""
$err = ""
try { $out = $proc.StandardOutput.ReadToEnd() } catch {}
try { $err = $proc.StandardError.ReadToEnd() } catch {}

if ($out) { $out | Out-File -FilePath $stdout -Encoding utf8 -Force }
if ($err) { $err | Out-File -FilePath $stderr -Encoding utf8 -Force }

Write-Host "CHECK LOG FILES:" -ForegroundColor Yellow
Write-Host ("STDOUT=" + $stdout)
Write-Host ("STDERR=" + $stderr)
exit 1
