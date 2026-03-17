$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $root "frontend"
$backend = Join-Path $root "backend"
$nodeDir = "C:\Program Files\nodejs"

if (Test-Path $nodeDir) {
  $env:Path = "$nodeDir;$env:Path"
}

Start-Process powershell -ArgumentList "-NoProfile", "-Command", "Set-Location '$backend'; & '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoProfile", "-Command", "Set-Location '$frontend'; if (Test-Path '$nodeDir') { `$env:Path = '$nodeDir;' + `$env:Path }; & '$nodeDir\node.exe' '.\node_modules\next\dist\bin\next' dev"

Write-Host "CreatorLab frontend: http://localhost:3000"
Write-Host "CreatorLab backend: http://localhost:8000"
