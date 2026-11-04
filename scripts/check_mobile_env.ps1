# ==============================================================================
# VeriCoach Mobile Environment Diagnostics Script (PowerShell)
#
# Verifies:
# 1. Android Debug Bridge (adb) is accessible and sees at least one online device/emulator.
# 2. Appium 2.x server is actively running and reachable on port 4723.
# 3. VeriCoach Android application package (com.vericoach.app) is installed on device.
# ==============================================================================

$ErrorActionPreference = "Continue"

$AppPackage = if ($env:TEST_MOBILE_APP_PACKAGE) { $env:TEST_MOBILE_APP_PACKAGE } else { "com.vericoach.app" }
$AppiumUrl = if ($env:TEST_MOBILE_SERVER_URL) { $env:TEST_MOBILE_SERVER_URL } else { "http://127.0.0.1:4723" }

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   VeriCoach Mobile Automation Environment Check     " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$Failed = $false

# 1. Check ADB
Write-Host -NoNewline "Checking ADB binary and active device/emulator... "
$adbCmd = Get-Command "adb" -ErrorAction SilentlyContinue
if (-not $adbCmd -and $env:ANDROID_HOME) {
    $platformToolsAdb = Join-Path $env:ANDROID_HOME "platform-tools\adb.exe"
    if (Test-Path $platformToolsAdb) {
        $env:PATH = "$($env:ANDROID_HOME)\platform-tools;$($env:PATH)"
        $adbCmd = Get-Command "adb" -ErrorAction SilentlyContinue
    }
}

if (-not $adbCmd) {
    Write-Host "[FAILED]" -ForegroundColor Red
    Write-Host "  Reason: 'adb' command not found in PATH." -ForegroundColor Yellow
    Write-Host "  Fix: Install Android Platform-Tools or set ANDROID_HOME and add %ANDROID_HOME%\platform-tools to PATH." -ForegroundColor Yellow
    $Failed = $true
} else {
    $devicesOutput = & adb devices 2>$null
    $onlineDevices = $devicesOutput | Where-Object { $_ -match "\bdevice\b" -and $_ -notmatch "List of devices" }
    if (-not $onlineDevices) {
        Write-Host "[FAILED]" -ForegroundColor Red
        Write-Host "  Reason: No active Android device or emulator detected by adb." -ForegroundColor Yellow
        Write-Host "  Fix: Start an emulator using: emulator -avd Pixel_7_API_34" -ForegroundColor Yellow
        $Failed = $true
    } else {
        $count = ($onlineDevices | Measure-Object).Count
        Write-Host "[OK] ($count device(s) online)" -ForegroundColor Green
    }
}

# 2. Check Appium Server
Write-Host -NoNewline "Checking Appium 2.x server at $AppiumUrl/status... "
try {
    $response = Invoke-RestMethod -Uri "$AppiumUrl/status" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[OK] (HTTP 200 - Appium ready)" -ForegroundColor Green
} catch {
    Write-Host "[FAILED]" -ForegroundColor Red
    Write-Host "  Reason: Appium server not responding at $AppiumUrl/status." -ForegroundColor Yellow
    Write-Host "  Fix: Start Appium in another terminal:" -ForegroundColor Yellow
    Write-Host "       appium --address 127.0.0.1 --port 4723 --allow-insecure chromedriver_autodownload" -ForegroundColor Yellow
    $Failed = $true
}

# 3. Check Package
Write-Host -NoNewline "Checking if $AppPackage is installed on device... "
if ($adbCmd -and $onlineDevices) {
    $packages = & adb shell pm list packages 2>$null
    if ($packages -match $AppPackage) {
        Write-Host "[OK] (Package '$AppPackage' found)" -ForegroundColor Green
    } else {
        Write-Host "[FAILED]" -ForegroundColor Red
        Write-Host "  Reason: Package '$AppPackage' is not installed on the target device." -ForegroundColor Yellow
        Write-Host "  Fix: Install debug APK using:" -ForegroundColor Yellow
        Write-Host "       adb install -r app/frontend/android/app/build/outputs/apk/debug/app-debug.apk" -ForegroundColor Yellow
        $Failed = $true
    }
} else {
    Write-Host "[SKIPPED] (adb check failed)" -ForegroundColor Yellow
}

Write-Host "======================================================" -ForegroundColor Cyan
if (-not $Failed) {
    Write-Host "All mobile environment checks passed! Ready to run tests:" -ForegroundColor Green
    Write-Host "  pytest qa/mobile -v --alluredir=qa/allure-results"
    exit 0
} else {
    Write-Host "One or more mobile checks failed. Please see the fixes above." -ForegroundColor Red
    exit 1
}
