param(
    [string]$Python = "python",
    [switch]$ReuseSystemPackages
)
$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvArgs = @("-m", "venv", (Join-Path $PSScriptRoot ".venv"))
    if ($ReuseSystemPackages) { $venvArgs += "--system-site-packages" }
    & $Python @venvArgs
    if ($LASTEXITCODE -ne 0) { throw "Could not create virtual environment" }
}
& $venvPython -m pip install -e $PSScriptRoot --disable-pip-version-check --timeout 20 --retries 1
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& $venvPython -m hvideo doctor
if ($LASTEXITCODE -ne 0) { throw "Environment check failed" }
