$ErrorActionPreference = "Stop"

function Invoke-Json($method, $url, $bodyObj) {
    if ($null -ne $bodyObj) {
        $body = $bodyObj | ConvertTo-Json -Depth 20
        return Invoke-RestMethod -Method $method -Uri $url -ContentType "application/json; charset=utf-8" -Body $body
    }
    return Invoke-RestMethod -Method $method -Uri $url
}

$base = "http://127.0.0.1:8080"

Write-Host "[1] Health check" -ForegroundColor Cyan
$health = Invoke-Json "GET" "$base/api/health" $null
if (-not $health.success) { throw "health check failed" }
Write-Host "OK health"

Write-Host "[2] Submit chairman command" -ForegroundColor Cyan
$submit = Invoke-Json "POST" "$base/api/chairman/command" @{ command = "评估并落地A股量化，预算上限100万，季度内试运行" }
if (-not $submit.success) { throw "submit command failed" }
$decisionId = $submit.decision.id
$approvalId = $submit.decision.approval_id
if (-not $decisionId) { throw "decision id missing" }
if (-not $approvalId) { throw "approval id missing" }
if (-not $submit.decision.summary) { throw "decision summary missing" }
Write-Host "OK submit decision_id=$decisionId"

Write-Host "[3] Approve execution" -ForegroundColor Cyan
$approve = Invoke-Json "POST" "$base/api/approvals/$approvalId/approve" @{ comments = "smoke test approve" }
if (-not $approve.success) { throw "approve failed" }
Write-Host "OK approve approval_id=$approvalId"

Write-Host "[4] Verify executive dashboard" -ForegroundColor Cyan
$dash = Invoke-Json "GET" "$base/api/dashboard/executive" $null
if (-not $dash.success) { throw "executive dashboard failed" }
Write-Host "OK dashboard pending=$($dash.dashboard.governance.pending_approvals_count)"

Write-Host "[5] Weekly report" -ForegroundColor Cyan
$report = Invoke-Json "GET" "$base/api/reports/weekly/latest" $null
if (-not $report.success) { throw "weekly report failed" }
Write-Host "OK weekly report"

Write-Host "SMOKE TEST PASSED" -ForegroundColor Green
