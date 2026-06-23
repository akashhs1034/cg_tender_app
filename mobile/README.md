# Opporta — Android app (Flutter)

Native Android frontend for Opporta, talking to the **same Supabase backend** as
the web app (auth, tenders, jobs, offline tenders, profile, document vault). The
Python scrapers + Supabase + Gemini stay exactly as they are — this is just a
fast native client on top of them.

> **Status: v1 foundation — verified.** `flutter analyze` is clean and
> `flutter build web` compiles the whole app successfully (Flutter 3.44.3).
> The Android build uses the identical Dart code. Follow the steps below to run
> it on a device/emulator; we then add the Bid Workshop, document upload, and
> push notifications screen by screen.

---

## What's in v1
- Email + password auth (Supabase) — same accounts as the web app.
- Bottom nav: **Profile · Tenders · Jobs · Analytics**.
- **Tenders**: search + state + sector filters, **Eligible / Not Eligible** badge
  (binary, profile-based — no percentage), tap a card to open the official link.
- **Jobs**: search + state filter, tap to open.
- **Profile**: your details + document vault (with expiry status), log out.
- **Analytics**: live counts + tenders-by-sector.

## Bid Workshop — deploy the Edge Function (one time)
The Bid Workshop screen calls a Supabase **Edge Function** (`supabase/functions/
bid-engine`) that holds the Gemini key server-side (never shipped in the APK).
Deploy it once from the repo root:
```bash
# install the Supabase CLI first: https://supabase.com/docs/guides/cli
supabase login
supabase link --project-ref iujzepmdnkawbmpupuzk
supabase functions deploy bid-engine
supabase secrets set GEMINI_API_KEY=<your AQ. Gemini key>
```
Until it's deployed, the Bid Workshop shows a clear "function not deployed" message;
everything else works without it.

## Not yet ported (next sessions)
Push notifications (deadline / document-expiry alerts via FCM), app icon + splash.

---

## One-time setup
1. Install **Flutter** (stable): https://docs.flutter.dev/get-started/install/windows
2. Install **Android Studio** (gives you the Android SDK + an emulator).
3. Verify the toolchain:
   ```bash
   flutter doctor
   ```
   Resolve anything it flags (accept Android licenses: `flutter doctor --android-licenses`).

## Generate the platform folders + run
This folder has the Dart source (`lib/`) and `pubspec.yaml`, but not the
generated `android/` shell. Generate it (this won't overwrite `lib/`):
```bash
cd mobile
flutter create . --org com.opporta --project-name opporta --platforms=android
flutter pub get
flutter run            # with an emulator running, or a phone in USB-debug mode
```

## Required AndroidManifest edits (after `flutter create`)
`flutter create` does **not** add these, and the **release** build fails silently
without them. Open `android/app/src/main/AndroidManifest.xml` and add — inside
`<manifest>` but above `<application>`:
```xml
<!-- Supabase / network calls (release builds have no internet without this) -->
<uses-permission android:name="android.permission.INTERNET"/>

<!-- url_launcher needs to "see" the browser intent on Android 11+ -->
<queries>
  <intent>
    <action android:name="android.intent.action.VIEW" />
    <data android:scheme="https" />
  </intent>
</queries>
```

## Build for the Play Store
```bash
# one-time: create an upload keystore (KEEP IT SAFE — losing it = can't update the app)
keytool -genkey -v -keystore opporta-upload.jks -keyalg RSA -keysize 2048 \
        -validity 10000 -alias upload

# then wire it in android/key.properties + android/app/build.gradle (signingConfigs),
# and build the Play-Store bundle:
flutter build appbundle      # -> build/app/outputs/bundle/release/app-release.aab
```
Upload the `.aab` to **Play Console → your app → Production / Internal testing**.

---

## Play Store launch checklist
- [ ] **Google Play Console** account ($25 one-time).
- [ ] **Always-on backend** — Supabase is already always-on; only the *web* app's
      Streamlit host sleeps. The mobile app talks to Supabase directly, so it's fine.
- [ ] **App signing** keystore created + backed up.
- [ ] **Data Safety** form (collects email; auth via Supabase) + **content rating**.
- [ ] **Privacy Policy** URL (you already have one in the web app).
- [ ] App icon (512×512) + feature graphic (1024×500) + screenshots.
- [ ] Internal testing track first → then Production.

## Security notes
- `lib/config.dart` ships the Supabase **anon (publishable) key** — this is safe;
  Row-Level Security protects all user data. **Never** put the `service_role` key here.
- Gemini API key must **never** be embedded in the app — AI features will call a
  Supabase Edge Function that holds the key server-side (added next).
