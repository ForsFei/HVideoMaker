$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Run .\setup.ps1 first."
}
& $venvPython -X utf8 -m hvideo @args
exit $LASTEXITCODE
