# Build a Nuitka standalone Windows client (amd64 or arm64, matching the host).
# Packaging Python defaults to 3.11 so pyWinhook wheels resolve on amd64.
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
$IsWinArm64 = $ArchName -match "Arm64"
$OutDir = "build_windows"
$Jobs = [Environment]::ProcessorCount
if ($Jobs -lt 1) { $Jobs = 4 }

Write-Host "Host architecture: $ArchName"
Write-Host "Packaging Python: $PythonVersion"

uv python install $PythonVersion
uv sync --group packaging --python $PythonVersion

if (Test-Path -LiteralPath $OutDir) {
    cmd /c "rmdir /s /q `"$OutDir`""
    if (Test-Path -LiteralPath $OutDir) {
        Remove-Item -LiteralPath $OutDir -Recurse -Force
    }
}
New-Item -ItemType Directory -Path $OutDir | Out-Null

$nuitkaArgs = @(
    "--standalone",
    "--windows-console-mode=disable",
    "--windows-icon-from-ico=icons\icon.ico",
    "--product-name=KVM Card Mini",
    "--file-description=USB KVM Card Mini desktop client",
    "--file-version=0.1.0",
    "--product-version=0.1.0",
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

if ($IsWinArm64) {
    $nuitkaArgs = @("--nofollow-import-to=pyWinhook") + $nuitkaArgs
    Write-Host "Windows ARM64: System hook (pyWinhook) is not packaged."
} else {
    $nuitkaArgs = @("--include-module=pyWinhook") + $nuitkaArgs
}

uv run --python $PythonVersion --group packaging python -m nuitka @nuitkaArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$DistPath = $null
foreach ($candidate in @("$OutDir\Mini-KVM.dist", "$OutDir\KVM-Card-Mini.dist")) {
    if (Test-Path -LiteralPath $candidate) {
        $DistPath = $candidate
        break
    }
}

if (-not $DistPath) {
    Write-Error "Nuitka finished but no .dist folder was found in $OutDir"
    Get-ChildItem -LiteralPath $OutDir | Format-Table
    exit 1
}

$ExePath = Join-Path $DistPath "KVM-Card-Mini.exe"
if (-not (Test-Path -LiteralPath $ExePath)) {
    $fallback = Get-ChildItem -LiteralPath $DistPath -Filter "*.exe" | Select-Object -First 1
    if ($fallback) {
        $ExePath = $fallback.FullName
    }
}

$DistPathUnix = $DistPath -replace '\\', '/'
Set-Content -LiteralPath (Join-Path $OutDir ".build-output") -Value $DistPathUnix -NoNewline
Write-Host ""
Write-Host "Built: $ExePath"
Write-Host "Dist:  $DistPath"
