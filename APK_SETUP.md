# RoadSoS — APK Build & Distribution Guide

Everything you need to go from source code to an installable Android APK,
including the free GitHub Actions path that requires no local Android tooling.

---

## What was added to the project

| File | What it does |
|------|-------------|
| `static/css/style.css` (appended) | Safe-area insets, car display, foldable, TV, smartwatch, high-contrast, print |
| `static/manifest.json` | App shortcuts (SOS / Hospital / First Aid), maskable icons, share target |
| `static/sw.js` | Offline cache, push notifications, background sync |
| `templates/index.html` | iOS/Android PWA meta tags, device detection, install banner |
| `android/` | Complete TWA project — see breakdown below |
| `static/.well-known/assetlinks.json` | Proves APK ownership to Android (hides browser bar) |
| `app.py` | `/.well-known/assetlinks.json` Flask route (fixed — now above `__main__`) |

### Android project files

| File | Purpose |
|------|---------|
| `android/app/src/main/AndroidManifest.xml` | Permissions, deep links, TWA config |
| `android/app/build.gradle` | TWA dependency, signing, min/target SDK |
| `android/build.gradle` | Root build — AGP 8.3 |
| `android/settings.gradle` | Module declaration |
| `android/gradle.properties` | AndroidX, JVM heap |
| `android/gradlew` + `gradlew.bat` | Gradle wrapper scripts (Unix / Windows) |
| `android/gradle/wrapper/gradle-wrapper.properties` | Pins Gradle 8.9 |
| `android/bootstrap.sh` | Downloads `gradle-wrapper.jar` on first run |
| `android/.github/workflows/build.yml` | CI — auto-builds APK on every push |
| `android/app/src/main/res/values/colors.xml` | Brand colours |
| `android/app/src/main/res/values/strings.xml` | App name, notification strings |
| `android/app/src/main/res/values/styles.xml` | NoActionBar theme, cutout mode |
| `android/app/src/main/res/drawable/splash.xml` | Dark-blue splash background |
| `android/app/src/main/res/xml/file_paths.xml` | FileProvider paths for SOS share |

---

## Device support matrix

| Device type | Works? | Notes |
|-------------|--------|-------|
| Android phone (5″–7″) | ✅ Full | Native APK via TWA |
| iPhone / iOS | ✅ PWA | Safari → Share → Add to Home Screen |
| Android tablet | ✅ Full | Responsive layout |
| Car display / Android Auto | ✅ Optimised | Large targets, no animations, forced dark |
| Foldable / dual screen | ✅ Spanning | Uses `viewport-segment-width` |
| Smart TV / large monitor | ✅ Wider panels | ≥ 1920 px breakpoint |
| Smartwatch / tiny screen | ✅ Map-only | ≤ 320 px breakpoint |

---

## Step 1 — Deploy the web app (required before building APK)

The Android TWA wraps your **live HTTPS website**. You need a public URL first.

### Option A — Render (free, easiest)

1. Push your code to a GitHub repo
2. [render.com](https://render.com) → **New → Web Service** → connect repo
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
4. You get: `https://roadsos-xxxx.onrender.com`

### Option B — Railway

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### Option C — Docker (VPS / cloud VM)

```bash
docker compose up -d
# Expose port 5000 and put nginx + certbot in front for HTTPS
```

### After deploying — update the domain

Edit `android/app/build.gradle` (the `defaultConfig` block):

```groovy
manifestPlaceholders = [
    hostName   : "your-app.onrender.com",     // ← your real domain (no https://)
    defaultUrl : "https://your-app.onrender.com",   // ← full URL
    assetStatements: """[{
      "relation": ["delegate_permission/common.handle_all_urls"],
      "target": {
        "namespace": "web",
        "site": "https://your-app.onrender.com"
      }
    }]"""
]
```

---

## Step 2 — Build the APK

### Option A — GitHub Actions ✅ Recommended (no Android Studio needed)

1. Push the whole project (including `android/`) to GitHub
2. Go to **Actions** tab → **Build RoadSoS APK** → **Run workflow**
3. After ~5 minutes → **Artifacts** section → download `roadsos-debug-apk.zip`
4. Unzip → `app-debug.apk` → ready to install

### Option B — Android Studio (local)

1. Install [Android Studio](https://developer.android.com/studio)
2. **Open** the `android/` folder as a project
3. Wait for Gradle sync (downloads everything automatically)
4. **Build → Build Bundle(s)/APK(s) → Build APK(s)**
5. APK: `android/app/build/outputs/apk/debug/app-debug.apk`

### Option C — Command line (needs JDK 17 + Android SDK)

```bash
cd android

# First time only — downloads gradle-wrapper.jar
sh bootstrap.sh

# Build debug APK
./gradlew assembleDebug
# → app/build/outputs/apk/debug/app-debug.apk

# Build release AAB (needs keystore — see Step 4)
./gradlew bundleRelease
# → app/build/outputs/bundle/release/app-release.aab
```

---

## Step 3 — Install the APK on a phone

1. Transfer `app-debug.apk` to the phone (USB, email, cloud, or direct download)
2. On the phone: **Settings → Apps → Special app access → Install unknown apps**
   → allow your file manager or browser
3. Open the APK file → **Install**

---

## Step 4 — Enable TWA verification (removes the browser bar)

Without this the APK works but shows a URL bar. With it, the app looks fully native.

### 4a — Generate a release keystore (one-time)

```bash
keytool -genkeypair -v \
  -keystore roadsos-release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias roadsos \
  -dname "CN=RoadSoS, OU=App, O=RoadSoS, L=Hyderabad, S=TG, C=IN"
```

Keep `roadsos-release.jks` secret — never commit it to Git.

### 4b — Get the SHA-256 fingerprint

```bash
keytool -list -v -keystore roadsos-release.jks -alias roadsos
# Copy the line: SHA256: AB:12:CD:34:...
```

### 4c — Update assetlinks.json

Edit `static/.well-known/assetlinks.json`:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.roadsos.app",
    "sha256_cert_fingerprints": [
      "AB:12:CD:34:EF:56:..."
    ]
  }
}]
```

Redeploy the web app, then verify:

```
https://your-domain.com/.well-known/assetlinks.json
```

Should return the JSON above with `Content-Type: application/json`.

### 4d — Add keystore to GitHub Secrets (for CI release builds)

GitHub repo → **Settings → Secrets → Actions → New repository secret**:

| Secret name | Value |
|-------------|-------|
| `KEYSTORE_BASE64` | `base64 roadsos-release.jks` (paste the output) |
| `KEYSTORE_PASSWORD` | your keytool password |
| `KEY_ALIAS` | `roadsos` |
| `KEY_PASSWORD` | your key password |

Then push a version tag to trigger a signed release build:

```bash
git tag v1.0.0
git push --tags
# GitHub Actions builds → creates GitHub Release with APK + AAB attached
```

---

## Step 5 — Distribute (free options)

### GitHub Releases (easiest, direct APK download)

```bash
git tag v1.0.0 && git push --tags
# CI auto-creates the release with download link
```

Share: `https://github.com/YOUR/REPO/releases`

### Your own website

```html
<a href="/static/roadsos.apk" download>⬇ Download RoadSoS for Android</a>
```

### Amazon Appstore (free — reaches Fire tablets + Android)

[developer.amazon.com](https://developer.amazon.com/apps-and-games) → free account → submit APK → 1–3 day review.

### Samsung Galaxy Store (free)

[seller.samsungapps.com](https://seller.samsungapps.com) → free for individuals → upload APK.

### Google Play Store ($25 one-time fee)

[play.google.com/console](https://play.google.com/console) → requires AAB (not APK) → use `app-release.aab` from CI.

---

## Testing without building an APK

**PWA on Chrome Android:**
Open Chrome → visit your deployed URL → 3-dot menu → **Add to Home Screen**. Works identically for most purposes.

**Car display in browser DevTools:**
DevTools → Toggle device toolbar → Add custom device:
- Width: `800`, Height: `480`, DPR: `1`
- User agent: `Mozilla/5.0 (Linux; Android 10) CarWebApp`

The car CSS (large tap targets, no animations, forced dark mode) activates automatically.

**iOS Safari PWA:**
Visit URL in Safari → Share button → **Add to Home Screen**.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `gradlew: command not found` | Run `sh android/bootstrap.sh` first |
| `gradle-wrapper.jar` missing | Run `sh android/bootstrap.sh` or open in Android Studio |
| TWA shows browser bar | Check `/.well-known/assetlinks.json` is live and SHA-256 matches your keystore |
| App crashes on launch | Check `defaultUrl` in `build.gradle` points to a live HTTPS URL |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Uninstall the old version first, then reinstall |
| GitHub Actions build fails | Check the Actions log; usually a missing secret or wrong domain |
