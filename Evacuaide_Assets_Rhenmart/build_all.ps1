# EVACUAIDE - End-to-End Build Automation
# =======================================
# Runs the whole pipeline start to finish, no manual steps:
#   1. Blender: rebuild detailed building from JSON, export FBX+GLB, render maps
#   2. Copy the fresh building + maps into the Unity project
#   3. Unity: import + configure XR + build scene + build the Quest APK
#
# Usage (from anywhere):
#   powershell -ExecutionPolicy Bypass -File build_all.ps1
#
# Optional switches:
#   -SkipBlender   reuse existing exported assets, only run Unity
#   -SkipUnity     only run the Blender asset pipeline
#   -ConfigureOnly configure Unity for Quest but don't build the APK

param(
    [switch]$SkipBlender,
    [switch]$SkipUnity,
    [switch]$ConfigureOnly
)

$ErrorActionPreference = "Stop"

# --- Resolve tools + paths -------------------------------------------------
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path            # ...\Evacuaide_Assets_Rhenmart
$Repo       = Split-Path -Parent $ScriptDir                              # ...\cheche blend
$UnityProj  = Join-Path $Repo "EvacuaideVR"
$BlenderExe = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

# Auto-detect the Unity editor that matches the project version.
$ProjVer = (Get-Content (Join-Path $UnityProj "ProjectSettings\ProjectVersion.txt") |
            Select-String "m_EditorVersion:").ToString().Split(":")[1].Trim()
$UnityExe = "C:\Program Files\Unity\Hub\Editor\$ProjVer\Editor\Unity.exe"

Write-Host "== EVACUAIDE build_all ==" -ForegroundColor Cyan
Write-Host "  Repo:       $Repo"
Write-Host "  Unity proj: $UnityProj (Unity $ProjVer)"
Write-Host "  Blender:    $BlenderExe"

function Assert-Exe($path, $name) {
    if (-not (Test-Path $path)) { throw "$name not found at: $path" }
}

# --- 1. Blender asset pipeline --------------------------------------------
if (-not $SkipBlender) {
    Assert-Exe $BlenderExe "Blender"
    Write-Host "`n[1/3] Blender: building + exporting + rendering maps..." -ForegroundColor Yellow
    & $BlenderExe --background --python (Join-Path $ScriptDir "Scripts\run_all.py")
    Write-Host "  Blender pipeline done."

    # --- 2. Copy fresh assets into Unity ----------------------------------
    Write-Host "`n[2/3] Copying assets into Unity project..." -ForegroundColor Yellow
    $bSrc = Join-Path $ScriptDir "Building"
    $bDst = Join-Path $UnityProj "Assets\Evacuaide\Building"
    Copy-Item (Join-Path $bSrc "OfficeBuilding_5F.fbx") $bDst -Force
    Copy-Item (Join-Path $bSrc "OfficeBuilding_5F.glb") $bDst -Force

    $mSrc = Join-Path $ScriptDir "Renders\FloorMaps"
    $mDst = Join-Path $UnityProj "Assets\Evacuaide\EvacuationMaps"
    if (Test-Path $mSrc) {
        Get-ChildItem "$mSrc\*.png" | ForEach-Object { Copy-Item $_.FullName $mDst -Force }
    }
    Write-Host "  Assets copied."
} else {
    Write-Host "`n[1-2/3] Skipping Blender (using existing exported assets)." -ForegroundColor DarkGray
}

# --- 3. Unity import + build ----------------------------------------------
if (-not $SkipUnity) {
    Assert-Exe $UnityExe "Unity $ProjVer"
    Write-Host "`n[3/3] Unity: import, XR setup, scene + APK build..." -ForegroundColor Yellow

    $common = @("-batchmode", "-quit", "-projectPath", $UnityProj)

    Write-Host "  -> Import & verify..."
    & $UnityExe @common -executeMethod EvacuaideBatch.ImportAndVerify `
        -logFile (Join-Path $UnityProj "unity_import.log")
    Write-Host "     import exit code: $LASTEXITCODE"

    Write-Host "  -> Enable OpenXR (Android)..."
    & $UnityExe @common -executeMethod EvacuaideXRSetup.EnableOpenXRAndroid `
        -logFile (Join-Path $UnityProj "unity_xr.log")
    Write-Host "     xr exit code: $LASTEXITCODE"

    if ($ConfigureOnly) {
        Write-Host "  -> Configure for Quest (no APK)..."
        & $UnityExe @common -executeMethod EvacuaideBuild.ConfigureQuest `
            -logFile (Join-Path $UnityProj "unity_configure.log")
    } else {
        Write-Host "  -> Build Quest APK..."
        & $UnityExe @common -buildTarget Android -executeMethod EvacuaideBuild.BuildQuestApk `
            -logFile (Join-Path $UnityProj "unity_apk.log")
    }
    Write-Host "     build exit code: $LASTEXITCODE"

    $report = Join-Path $UnityProj "UNITY_BUILD_REPORT.txt"
    if (Test-Path $report) { Write-Host "`n--- BUILD REPORT ---"; Get-Content $report }
} else {
    Write-Host "`n[3/3] Skipping Unity." -ForegroundColor DarkGray
}

Write-Host "`n== build_all complete ==" -ForegroundColor Cyan
