#!/usr/bin/env bash
# ==============================================================================
# VeriCoach Mobile Environment Diagnostics Script
#
# Verifies:
# 1. Android Debug Bridge (adb) is accessible and sees at least one online device/emulator.
# 2. Appium 2.x server is actively running and reachable on port 4723.
# 3. VeriCoach Android application package (com.vericoach.app) is installed on device.
# ==============================================================================

set -uo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_PACKAGE="${TEST_MOBILE_APP_PACKAGE:-com.vericoach.app}"
APPIUM_URL="${TEST_MOBILE_SERVER_URL:-http://127.0.0.1:4723}"

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   VeriCoach Mobile Automation Environment Check     ${NC}"
echo -e "${BLUE}======================================================${NC}"

FAILED=0

# ------------------------------------------------------------------------------
# 1. Check ADB and Connected Devices
# ------------------------------------------------------------------------------
echo -n "Checking ADB binary and active device/emulator... "
if ! command -v adb >/dev/null 2>&1; then
    if [ -n "${ANDROID_HOME:-}" ] && [ -x "${ANDROID_HOME}/platform-tools/adb" ]; then
        export PATH="${ANDROID_HOME}/platform-tools:${PATH}"
    fi
fi

if ! command -v adb >/dev/null 2>&1; then
    echo -e "${RED}[FAILED]${NC}"
    echo -e "  ${YELLOW}Reason:${NC} 'adb' command not found in PATH."
    echo -e "  ${YELLOW}Fix:${NC} Install Android Platform-Tools or set ANDROID_HOME and add \$ANDROID_HOME/platform-tools to PATH."
    FAILED=1
else
    # Query connected devices
    ACTIVE_DEVICES=$(adb devices 2>/dev/null | grep -E "\b(device)\b" | grep -v "List of devices" || true)
    if [ -z "${ACTIVE_DEVICES}" ]; then
        echo -e "${RED}[FAILED]${NC}"
        echo -e "  ${YELLOW}Reason:${NC} No active Android device or emulator detected by adb."
        echo -e "  ${YELLOW}Fix:${NC} Start an emulator using: emulator -avd Pixel_7_API_34"
        echo -e "         or connect a physical device with USB debugging enabled."
        FAILED=1
    else
        DEVICE_COUNT=$(echo "${ACTIVE_DEVICES}" | wc -l | tr -d ' ')
        FIRST_DEV=$(echo "${ACTIVE_DEVICES}" | head -n 1 | awk '{print $1}')
        echo -e "${GREEN}[OK]${NC} (${DEVICE_COUNT} device(s) online, primary: ${FIRST_DEV})"
    fi
fi

# ------------------------------------------------------------------------------
# 2. Check Appium 2.x Server Health
# ------------------------------------------------------------------------------
echo -n "Checking Appium 2.x server at ${APPIUM_URL}/status... "
APPIUM_STATUS=0
if command -v curl >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${APPIUM_URL}/status" --max-time 3 || echo "000")
    if [ "${HTTP_CODE}" = "200" ]; then
        APPIUM_STATUS=1
    fi
fi

if [ "${APPIUM_STATUS}" -eq 1 ]; then
    echo -e "${GREEN}[OK]${NC} (HTTP 200 - Appium ready)"
else
    echo -e "${RED}[FAILED]${NC}"
    echo -e "  ${YELLOW}Reason:${NC} Appium server not responding at ${APPIUM_URL}/status."
    echo -e "  ${YELLOW}Fix:${NC} Start Appium in another terminal:"
    echo -e "         appium --address 127.0.0.1 --port 4723 --allow-insecure chromedriver_autodownload"
    FAILED=1
fi

# ------------------------------------------------------------------------------
# 3. Check App Package Installation
# ------------------------------------------------------------------------------
echo -n "Checking if ${APP_PACKAGE} is installed on device... "
if command -v adb >/dev/null 2>&1 && [ -n "${ACTIVE_DEVICES:-}" ]; then
    PACKAGE_CHECK=$(adb shell pm list packages 2>/dev/null | grep "${APP_PACKAGE}" || true)
    if [ -n "${PACKAGE_CHECK}" ]; then
        echo -e "${GREEN}[OK]${NC} (Package '${APP_PACKAGE}' found)"
    else
        echo -e "${RED}[FAILED]${NC}"
        echo -e "  ${YELLOW}Reason:${NC} Package '${APP_PACKAGE}' is not installed on the target device."
        echo -e "  ${YELLOW}Fix:${NC} Install debug APK using:"
        echo -e "         adb install -r app/frontend/android/app/build/outputs/apk/debug/app-debug.apk"
        FAILED=1
    fi
else
    echo -e "${YELLOW}[SKIPPED]${NC} (Skipped because adb device check failed)"
fi

echo -e "${BLUE}======================================================${NC}"
if [ "${FAILED}" -eq 0 ]; then
    echo -e "${GREEN}All mobile environment checks passed! Ready to run tests:${NC}"
    echo -e "  pytest qa/mobile -v --alluredir=qa/allure-results"
    exit 0
else
    echo -e "${RED}One or more mobile checks failed. Please see the fixes above.${NC}"
    exit 1
fi

