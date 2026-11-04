# VeriCoach Mobile Automation Setup Guide

This guide describes how to configure, launch, and run automated Appium tests for the **VeriCoach Android Application** on an Android emulator (**Pixel 7, API 34**).

The test suite runs against Appium 2.x using the **UiAutomator2** driver and the **Appium Python Client**, integrating directly into the unified Allure reporting pipeline alongside web and API test results.

---

## 1. Prerequisites & Environment Variables

### System Requirements
1. **Node.js**: v20+ LTS (`node --version`)
2. **Java Development Kit**: JDK 17 or JDK 21 LTS (`java -version`, `javac -version`)
3. **Android SDK**: Command Line Tools, Platform-Tools (`adb`), and API 34 System Images.
4. **Python**: 3.11 (`python --version`) with dependencies installed in `qa/.venv`.

### Required Environment Variables

#### Windows (PowerShell or System Environment)
```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.x-hotspot"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:PATH = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\emulator;$env:PATH"
```

#### macOS / Linux
```bash
export JAVA_HOME="/usr/lib/jvm/java-17-openjdk" # or /Library/Java/JavaVirtualMachines/...
export ANDROID_HOME="$HOME/Android/Sdk"          # or "$HOME/Library/Android/sdk"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"
```

---

## 2. Step 1: Install Appium 2.x, UiAutomator2 Driver, and Appium Doctor

Install Appium 2.x globally and register the UiAutomator2 driver:

```bash
# 1. Install Appium 2.x
npm install -g appium

# 2. Verify Appium version (must be >= 2.0.0)
appium -v

# 3. Install UiAutomator2 driver
appium driver install uiautomator2

# 4. Verify installed drivers
appium driver list --installed
# Expected output:
# - uiautomator2@x.y.z [installed (npm)]

# 5. Install Appium Doctor diagnostic utility
npm install -g @appium/doctor

# 6. Run diagnostic check for Android
appium-doctor --android
```

Ensure all mandatory Android checks (JAVA_HOME, ANDROID_HOME, adb, android/emulator binaries) pass.

---

## 3. Step 2: Create Android Emulator (Pixel 7, API 34)

Download Android 34 packages and construct a Pixel 7 Android Virtual Device (AVD):

```bash
# 1. Accept SDK licenses
yes | sdkmanager --licenses

# 2. Install required SDK platform and system image
sdkmanager --install "platform-tools" "platforms;android-34" "system-images;android-34;google_apis;x86_64"

# 3. Create the Pixel 7 API 34 AVD named 'Pixel_7_API_34'
avdmanager create avd \
  -n "Pixel_7_API_34" \
  -k "system-images;android-34;google_apis;x86_64" \
  --device "pixel_7" \
  --force

# 4. Verify the emulator exists
emulator -list-avds
# Expected output:
# Pixel_7_API_34
```

---

## 4. Step 3: Launch Android Emulator & Verify ADB

Start the newly created emulator:

```bash
# Launch emulator in background or separate terminal
emulator -avd Pixel_7_API_34 -netdelay none -netspeed full
```

Wait until the device boots and verify adb sees it:

```bash
# Wait for adb connection
adb wait-for-device

# Wait until Android OS boot finishes completely
adb shell 'while [[ "$(getprop sys.boot_completed)" != "1" ]]; do sleep 1; done'

# Confirm online status
adb devices
# Output should list device, for example:
# List of devices attached
# emulator-5554    device
```

---

## 5. Step 4: Build and Install VeriCoach Debug APK

Compile the frontend assets, sync Capacitor, and assemble the debug APK:

```bash
# 1. Build web application and sync native wrapper
cd app/frontend
npm install
npm run build
npm run cap:sync

# 2. Compile debug APK
# On Windows:
cd android && .\gradlew.bat assembleDebug && cd ../../..
# On macOS / Linux:
cd android && ./gradlew assembleDebug && cd ../../..

# 3. Locate compiled APK:
# app/frontend/android/app/build/outputs/apk/debug/app-debug.apk

# 4. Install the APK to the running emulator
adb install -r app/frontend/android/app/build/outputs/apk/debug/app-debug.apk

# 5. Verify package installation on emulator
adb shell pm list packages | grep com.vericoach.app
# Expected output:
# package:com.vericoach.app
```

---

## 6. Step 5: Start Host Backend Server

The Android emulator connects to the host machine backend via `http://10.0.2.2:8000`.

Start the backend listening on all network interfaces (`0.0.0.0`):

```bash
# In one terminal, activate app virtual environment:
cd app
# Windows:
.venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
# macOS / Linux:
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

> **Reverse Port Forwarding (Optional):**
> You can also map host port 8000 directly into the emulator so `localhost:8000` resolves to host:
> ```bash
> adb reverse tcp:8000 tcp:8000
> ```

---

## 7. Step 6: Start Appium Server

In another dedicated terminal, start the Appium 2.x server:

```bash
appium --address 127.0.0.1 --port 4723 --allow-insecure chromedriver_autodownload
```

Verify Appium is alive:
```bash
curl http://127.0.0.1:4723/status
# Expected response: {"value":{"ready":true,"message":"The server is ready to accept new connections"...}}
```

---

## 8. Step 7: Run Environment Diagnostics

Run the automated diagnostic check before launching the tests:

```bash
# From workspace root:
bash scripts/check_mobile_env.sh
```

The script verifies:
1. `adb` finds an active emulator/device.
2. Appium server responds with HTTP 200 on port 4723.
3. `com.vericoach.app` is installed.

---

## 9. Step 8: Execute Mobile Automation Test Suite

Execute the tests using `pytest`. Test capabilities are loaded directly from the framework config (`qa/framework/config.py` and `qa/.env`):

```bash
cd qa

# Run all mobile tests
python -m pytest mobile -v --alluredir=allure-results

# Run critical smoke tests only
python -m pytest mobile -m smoke -v --alluredir=allure-results

# Run specific test
python -m pytest mobile/test_mobile_chat.py -k test_mobile_launch_and_ask_question_english -v
```

### Test Cases Executed:
1. **`test_mobile_launch_and_ask_question_english`**:
   - Launches app, asserts chat is ready.
   - Dispatches synthetic user finance query in English.
   - Waits for response with explicit waits and validates advisory text.
2. **`test_mobile_switch_to_hindi_and_telugu`**:
   - Switches language to Hindi and verifies Devanagari script (`\u0900-\u097F`).
   - Switches language to Telugu and verifies Telugu script (`\u0C00-\u0C7F`).
3. **`test_mobile_scroll_to_citations`**:
   - Dispatches query generating source citations.
   - Scrolls down to citation toggle, expands panel, and asserts source items.
4. **`test_mobile_background_and_foreground_keeps_conversation`**:
   - Sends query, puts app into background for 2 seconds, resumes, and asserts conversation history is intact.
5. **`test_mobile_rotate_device`**:
   - Rotates device to LANDSCAPE, validates layout remains interactive, and returns to PORTRAIT.
6. **`test_mobile_airplane_mode_offline_banner`**:
   - Toggles airplane mode and verifies instant appearance of offline alert banner.
   - Disables airplane mode and verifies banner dismissal.
7. **Failure Artifact Retention**:
   - On test failure, pytest hooks immediately capture a high-res screenshot and stop/attach MP4 screen recording into Allure.

---

## 10. Unified Allure Reporting

All mobile, web (Playwright & Selenium), and API tests store their results in the single directory `qa/allure-results`.

To generate and view the unified report:

```bash
cd qa

# Generate compiled report
npx allure-commandline generate allure-results -o allure-report --clean

# Serve report locally in browser
npx allure-commandline open allure-report
```

In the generated Allure report, the **Mobile Application** feature displays alongside **Web Interface** and **Core API**, complete with screenshots, recordings, and triage logs.

