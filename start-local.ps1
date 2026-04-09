$ErrorActionPreference = "Stop"

Set-StrictMode -Version Latest

function Write-Info {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-WarnLine {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Ok {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "[ OK ] $Message" -ForegroundColor Green
}

function Get-ProxyPoolProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Role
    )

    $escapedRoot = [Regex]::Escape($script:ProjectRoot)
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -eq "python.exe" -and
            $_.CommandLine -match $escapedRoot -and
            $_.CommandLine -match "proxyPool\.py\s+$Role(\s|$)"
        } |
        Select-Object -First 1
}

function Test-ApiReady {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:5010/count/" -TimeoutSec 5
        return $response.Content
    }
    catch {
        return $null
    }
}

$script:ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeRoot = Join-Path $script:ProjectRoot ".runtime"
$redisRoot = Join-Path $runtimeRoot "redis\dist\Redis-8.6.2-Windows-x64-msys2"
$redisExe = Join-Path $redisRoot "redis-server.exe"
$redisCli = Join-Path $redisRoot "redis-cli.exe"
$pythonExe = Join-Path $script:ProjectRoot ".venv311\Scripts\python.exe"
$serverStdout = Join-Path $runtimeRoot "server.stdout.log"
$serverStderr = Join-Path $runtimeRoot "server.stderr.log"
$scheduleStdout = Join-Path $runtimeRoot "schedule.stdout.log"
$scheduleStderr = Join-Path $runtimeRoot "schedule.stderr.log"
$redisStdout = Join-Path $runtimeRoot "redis.stdout.log"
$redisStderr = Join-Path $runtimeRoot "redis.stderr.log"

Write-Info "Project root: $script:ProjectRoot"

if (-not (Test-Path $runtimeRoot)) {
    New-Item -ItemType Directory -Path $runtimeRoot | Out-Null
    Write-Info "Created .runtime directory"
}

if (-not (Test-Path $pythonExe)) {
    throw "Python runtime not found: $pythonExe"
}

if (-not (Test-Path $redisExe)) {
    throw "Redis executable not found: $redisExe"
}

if (-not (Test-Path $redisCli)) {
    throw "Redis CLI not found: $redisCli"
}

# Disable proxy settings only for this script and child processes.
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""
$env:http_proxy = ""
$env:https_proxy = ""
$env:all_proxy = ""
$env:NO_PROXY = "*"
$env:no_proxy = "*"
$env:REDISCLI_AUTH = "pwd"

Write-Info "Checking Redis"
$redisReady = $false
try {
    $pingResult = & $redisCli ping 2>$null
    if ($pingResult -match "PONG") {
        $redisReady = $true
    }
}
catch {
    $redisReady = $false
}

if (-not $redisReady) {
    Write-Info "Starting local Redis"
    Start-Process `
        -FilePath $redisExe `
        -ArgumentList '--bind 127.0.0.1 --port 6379 --requirepass pwd --appendonly no --save ""' `
        -WorkingDirectory $redisRoot `
        -RedirectStandardOutput $redisStdout `
        -RedirectStandardError $redisStderr |
        Out-Null

    Start-Sleep -Seconds 3

    $pingResult = & $redisCli ping 2>$null
    if ($pingResult -notmatch "PONG") {
        throw "Redis failed to start. Check: $redisStderr"
    }
}

Write-Ok "Redis is ready"

$serverProcess = Get-ProxyPoolProcess -Role "server"
if ($null -eq $serverProcess) {
    Write-Info "Starting ProxyPool API server"
    Start-Process `
        -FilePath $pythonExe `
        -ArgumentList "proxyPool.py", "server" `
        -WorkingDirectory $script:ProjectRoot `
        -RedirectStandardOutput $serverStdout `
        -RedirectStandardError $serverStderr |
        Out-Null
}
else {
    Write-WarnLine "API server already running, PID=$($serverProcess.ProcessId)"
}

$scheduleProcess = Get-ProxyPoolProcess -Role "schedule"
if ($null -eq $scheduleProcess) {
    Write-Info "Starting ProxyPool scheduler"
    Start-Process `
        -FilePath $pythonExe `
        -ArgumentList "proxyPool.py", "schedule" `
        -WorkingDirectory $script:ProjectRoot `
        -RedirectStandardOutput $scheduleStdout `
        -RedirectStandardError $scheduleStderr |
        Out-Null
}
else {
    Write-WarnLine "Scheduler already running, PID=$($scheduleProcess.ProcessId)"
}

Write-Info "Waiting for API readiness"
$apiContent = $null
for ($i = 0; $i -lt 10; $i++) {
    Start-Sleep -Seconds 1
    $apiContent = Test-ApiReady
    if ($apiContent) {
        break
    }
}

if (-not $apiContent) {
    throw "API did not become ready in time. Check: $serverStderr"
}

Write-Ok "ProxyPool is up"
Write-Host ""
Write-Host "URL: http://127.0.0.1:5010/" -ForegroundColor White
Write-Host "Status: $apiContent" -ForegroundColor White
Write-Host "Logs:" -ForegroundColor White
Write-Host "  $redisStderr" -ForegroundColor DarkGray
Write-Host "  $serverStderr" -ForegroundColor DarkGray
Write-Host "  $scheduleStderr" -ForegroundColor DarkGray
