# Build a Nuitka onefile Windows client (amd64).
# Packaging Python defaults to 3.11 so pyWinhook wheels resolve.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

if ($env:OS -ne "Windows_NT") {
    Write-Error "This script only runs on Windows."
    exit 1
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is required. Install: https://docs.astral.sh/uv/"
    exit 1
}

if (-not (Test-Path -LiteralPath "icons\icon.ico")) {
    Write-Error "Missing icons\icon.ico"
    exit 1
}

$PythonVersion = if ($env:PYTHON_VERSION) { $env:PYTHON_VERSION } else { "3.11" }
$DataSrc = if (Test-Path -LiteralPath "Data") { "Data" } elseif (Test-Path -LiteralPath "data") { "data" } else { $null }
if (-not $DataSrc) {
    Write-Error "Missing Data\ (or data\) directory"
    exit 1
}

$ArchName = $env:PROCESSOR_ARCHITECTURE
try {
    $ArchName = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
} catch {
    # Windows PowerShell 5.x without RuntimeInformation
}
if ($ArchName -match "Arm64") {
    Write-Error "Windows packaging targets amd64 only. Run this script on an x64 machine."
    exit 1
}

$env:UV_PYTHON = $PythonVersion
$OutDir = "build_windows"
$Jobs = [Environment]::ProcessorCount
if ($Jobs -lt 1) { $Jobs = 4 }

Write-Host "Host architecture: $ArchName"
Write-Host "Packaging Python: $PythonVersion"

uv python install $PythonVersion
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

uv sync --group packaging --python $PythonVersion
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (Test-Path -LiteralPath $OutDir) {
    cmd /c "rmdir /s /q `"$OutDir`""
    if (Test-Path -LiteralPath $OutDir) {
        Remove-Item -LiteralPath $OutDir -Recurse -Force
    }
}
New-Item -ItemType Directory -Path $OutDir | Out-Null

$nuitkaArgs = @(
    "--onefile",
    "--windows-console-mode=disable",
    "--windows-icon-from-ico=icons\icon.ico",
    "--company-name=kiramint",
    "--product-name=KVM Card Mini",
    "--file-description=USB KVM Card Mini desktop client",
    "--file-version=0.1.0",
    "--product-version=0.1.0",
    "--onefile-tempdir-spec={CACHE_DIR}/kiramint/KVM-Card-Mini/0.1.0",
    "--msvc=latest",
    "--enable-plugin=pyside6",
    "--include-qt-plugins=multimedia",
    "--include-data-dir=icons=icons",
    "--include-data-dir=web=web",
    "--include-data-dir=web_s=web_s",
    "--include-data-dir=${DataSrc}=data",
    "--include-data-files=trans_cn.qm=trans_cn.qm",
    "--include-data-files=qtbase_cn.qm=qtbase_cn.qm",
    "--include-module=hid",
    "--include-module=pythoncom",
    "--include-module=pywintypes",
    "--include-module=pyWinhook",
    "--nofollow-import-to=win32api",
    "--nofollow-import-to=win32con",
    "--nofollow-import-to=win32gui",
    "--output-dir=$OutDir",
    "--output-filename=KVM-Card-Mini",
    "--jobs=$Jobs",
    "--lto=no",
    "--assume-yes-for-downloads",
    "--noinclude-qt-translations",
    "--noinclude-dlls=libQt6Charts*",
    "--noinclude-dlls=libQt6Quick3D*",
    "--noinclude-dlls=libQt6Sensors*",
    "--noinclude-dlls=libQt6Test*",
    "--noinclude-dlls=libQt6WebEngine*",
    "--noinclude-dlls=qt6web*",
    "--noinclude-dlls=qt6pdf*",
    "Mini-KVM.py"
)

if (Test-Path -LiteralPath "booting.png") {
    $nuitkaArgs = @("--onefile-windows-splash-screen-image=booting.png") + $nuitkaArgs
}

uv run --python $PythonVersion --group packaging python -m nuitka @nuitkaArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$ExePath = $null
foreach ($candidate in @("$OutDir\KVM-Card-Mini.exe", "$OutDir\Mini-KVM.exe")) {
    if (Test-Path -LiteralPath $candidate) {
        $ExePath = $candidate
        break
    }
}
if (-not $ExePath) {
    $fallback = Get-ChildItem -LiteralPath $OutDir -Filter "*.exe" | Select-Object -First 1
    if ($fallback) {
        $ExePath = $fallback.FullName
    }
}

if (-not $ExePath) {
    Write-Error "Nuitka finished but no .exe was found in $OutDir"
    Get-ChildItem -LiteralPath $OutDir | Format-Table
    exit 1
}

$ExePathUnix = ($ExePath -replace '\\', '/')
Set-Content -LiteralPath (Join-Path $OutDir ".build-output") -Value $ExePathUnix -NoNewline
Write-Host ""
Write-Host "Built: $ExePath"
