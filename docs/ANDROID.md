# VeriCoach Android App & APK Build Guide

This document describes how VeriCoach is wrapped with [Capacitor](https://capacitorjs.com/) for Android, how it communicates with the backend from an emulator, and the exact steps to build and run the debug APK.

---

## 1. Architecture & Package Configuration

- **Wrapper Framework:** Capacitor 7 (`@capacitor/core`, `@capacitor/cli`, `@capacitor/android`)
- **Package ID / Application ID:** `com.vericoach.app`
- **App Name:** VeriCoach
- **Native Android Directory:** `app/frontend/android`
- **Web App Distribution:** `app/frontend/dist`

### Android Emulator Backend Resolution (`10.0.2.2`)

In standard Android emulators (AVD / Android Studio), the IP address `127.0.0.1` refers to the emulator's own loopback device, not your host development machine.
To connect to the VeriCoach backend running on the host machine (`http://localhost:8000`), the emulator must route requests to:

```
http://10.0.2.2:8000
```

- In `app/frontend/src/config/api.ts`, Capacitor's `Capacitor.getPlatform() === 'android'` automatically detects Android environments and defaults the API base URL to `http://10.0.2.2:8000`.
- Users and QA testers can also view or override this URL at runtime using the **Settings** modal in the top navigation bar.

### Network Security & Cleartext HTTP

Modern Android versions (API 28+) block unencrypted HTTP traffic by default. VeriCoach includes a custom network security configuration in:
- `app/frontend/android/app/src/main/res/xml/network_security_config.xml`:
  ```xml
  <?xml version="1.0" encoding="utf-8"?>
  <network-security-config>
      <domain-config cleartextTrafficPermitted="true">
          <domain includeSubdomains="true">10.0.2.2</domain>
          <domain includeSubdomains="true">localhost</domain>
          <domain includeSubdomains="true">127.0.0.1</domain>
      </domain-config>
      <base-config cleartextTrafficPermitted="true">
          <trust-anchors>
              <certificates src="system" />
              <certificates src="user" />
          </trust-anchors>
      </base-config>
  </network-security-config>
  ```
- `app/frontend/android/app/src/main/AndroidManifest.xml` has:
  ```xml
  android:usesCleartextTraffic="true"
  android:networkSecurityConfig="@xml/network_security_config"
  ```
This enables development testing against local backend servers without requiring HTTPS or certificate installation on the emulator.

---

## 2. Prerequisites

To build the native Android debug APK, the development environment must have:

1. **Node.js**: v20 or v24 LTS (`node --version`)
2. **Java Development Kit (JDK)**: JDK 17 or JDK 21 LTS (`java -version` and `JAVA_HOME` environment variable).
   > *Note:* Android Gradle Plugin 8.7+ requires Java 17+. Java 8 is incompatible.
3. **Android SDK**:
   - Android SDK Platform 34 or 35
   - Android SDK Build-Tools 34.0.0+
   - Android SDK Platform-Tools (`adb`)
4. **Environment Variables**:
   ```bash
   # Windows (System Properties -> Environment Variables)
   JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-17.0.x-hotspot"
   ANDROID_HOME="C:\Users\<username>\AppData\Local\Android\Sdk"
   PATH="%JAVA_HOME%\bin;%ANDROID_HOME%\platform-tools;%PATH%"

   # macOS / Linux
   export JAVA_HOME="/usr/lib/jvm/java-17-openjdk"
   export ANDROID_HOME="$HOME/Android/Sdk"
   export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"
   ```

---

## 3. Exact Build Steps

### Step 1: Start Backend (Mock Mode)
In one terminal, start the VeriCoach backend:
```bash
# From workspace root:
cd app
.venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
> Specifying `--host 0.0.0.0` ensures the backend listens on all interfaces so the Android emulator can reach it via `10.0.2.2`.

### Step 2: Build Web Assets and Sync with Capacitor
```bash
cd app/frontend
npm install
npm run build
npm run cap:sync
```
Or use the combined shortcut:
```bash
npm run build:android
```

### Step 3: Compile the Debug APK

**On Windows:**
```bash
cd app/frontend/android
.\gradlew.bat assembleDebug
```
Or from `app/frontend`:
```bash
npm run build:apk
```

**On Linux / macOS:**
```bash
cd app/frontend/android
./gradlew assembleDebug
```
Or from `app/frontend`:
```bash
npm run build:apk:unix
```

### Step 4: Locate the Output APK
Once the Gradle build finishes, the debug APK is located at:
```
app/frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 4. Installing and Running on an Emulator

1. Start your Android emulator from Android Studio or command line:
   ```bash
   emulator -avd Pixel_7_API_34
   ```
2. Verify the emulator is connected via adb:
   ```bash
   adb devices
   ```
3. Install the debug APK:
   ```bash
   adb install -r app/frontend/android/app/build/outputs/apk/debug/app-debug.apk
   ```
4. Launch the app on the emulator:
   ```bash
   adb shell am start -n com.vericoach.app/com.vericoach.app.MainActivity
   ```

---

## 5. Diagnostic Status on Current Build Machine

When attempting to build the APK via `gradlew.bat assembleDebug` on the current machine:

1. **Java Version:**
   `openjdk version "1.8.0_504"` (Java 8).
   Android Gradle Plugin 8.7.2 fails with:
   ```
   Could not resolve com.android.tools.build:gradle:8.7.2.
   Dependency requires at least JVM runtime version 11. This build uses a Java 8 JVM.
   ```
2. **Android SDK:**
   Neither `ANDROID_HOME` nor `ANDROID_SDK_ROOT` is set, and `C:\Users\Acer\AppData\Local\Android\Sdk` is not present.

### Required Actions on Host Machine to Complete APK Compilation:
1. Install JDK 17 (e.g. Eclipse Temurin 17 or OpenJDK 17) and set `JAVA_HOME`.
2. Install Android Studio (or Android Command Line Tools) and download the Android 34/35 SDK platform.
3. Set `ANDROID_HOME` to the Android SDK directory.
4. Run `npm run build:apk` in `app/frontend`.
