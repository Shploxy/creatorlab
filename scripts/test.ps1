$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$root = Split-Path -Parent $PSScriptRoot
$nodeDir = "C:\Program Files\nodejs"
$backend = Join-Path $root "backend"
$testBackendPort = $null
$testBaseUrl = $null
$startedBackend = $null
$backendReady = $false

if (Test-Path $nodeDir) {
  $env:Path = "$nodeDir;$env:Path"
}

function Test-BackendHealth {
  try {
    $response = Invoke-WebRequest -UseBasicParsing "$testBaseUrl/health" -TimeoutSec 3
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
}

function Assert-LastExitCode {
  param(
    [string]$Step
  )

  if ($LASTEXITCODE -ne 0) {
    throw "$Step failed with exit code $LASTEXITCODE."
  }
}

function Get-FreeTcpPort {
  $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
  $listener.Start()
  try {
    return $listener.LocalEndpoint.Port
  }
  finally {
    $listener.Stop()
  }
}

Push-Location (Join-Path $root "frontend")
& 'C:\Program Files\nodejs\npm.cmd' run build
Assert-LastExitCode "Frontend build"
Pop-Location

try {
  Push-Location $backend
  & '.\.venv\Scripts\python.exe' -m compileall app scripts
  Assert-LastExitCode "Backend compile"

  $testBackendPort = Get-FreeTcpPort
  $testBaseUrl = "http://127.0.0.1:$testBackendPort"

  $startedBackend = Start-Process powershell -PassThru -ArgumentList @(
    "-NoProfile",
    "-Command",
    "`$env:API_PUBLIC_URL='$testBaseUrl'; Set-Location '$backend'; & '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port $testBackendPort"
  )

  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-BackendHealth) {
      $backendReady = $true
      break
    }
  }

  if (-not $backendReady) {
    throw "Backend did not become ready for smoke tests."
  }

  $env:CREATORLAB_BASE_URL = $testBaseUrl
  & '.\.venv\Scripts\python.exe' scripts\e2e_smoke.py
  Assert-LastExitCode "Smoke tests"
  & '.\.venv\Scripts\pytest.exe' -q tests\test_live_api.py
  Assert-LastExitCode "API tests"
}
finally {
  Pop-Location
  Remove-Item Env:CREATORLAB_BASE_URL -ErrorAction SilentlyContinue
  if ($startedBackend -and -not $startedBackend.HasExited) {
    Stop-Process -Id $startedBackend.Id -Force
  }
}

Write-Host "CreatorLab checks completed."
