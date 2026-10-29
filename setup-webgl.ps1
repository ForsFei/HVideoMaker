param([switch]$InstallChromium)
$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Run setup.ps1 first" }
& $python -m pip install 'playwright>=1.49,<2' --timeout 20 --retries 1 --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { throw "Playwright installation failed" }
Push-Location $PSScriptRoot
try {
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'package-lock.json')) { npm.cmd ci --no-audit --no-fund } else { npm.cmd install --no-audit --no-fund }
    if ($LASTEXITCODE -ne 0) { throw "Three.js installation failed" }
} finally { Pop-Location }
if ($InstallChromium) {
    & $python -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw "Chromium installation failed" }
}
& $python -X utf8 -m hvideo doctor --webgl
if ($LASTEXITCODE -ne 0) { throw "WebGL check failed" }
