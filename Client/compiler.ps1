# Old name. Prefer compiler-windows.ps1.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
& "$PSScriptRoot\compiler-windows.ps1" @args
exit $LASTEXITCODE
