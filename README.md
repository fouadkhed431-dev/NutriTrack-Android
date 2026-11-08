# NutriTrack Android APK project (V2)

This project packages the NutriTrack V2 food tracker as a standalone Android application.
The app loads its HTML, styling, JavaScript, and 459-food database from the APK's local assets.
It does not need a website or internet connection to track food.

## Build the APK without installing Android Studio on your phone

A ready GitHub Actions workflow is included to build the APK in the cloud:

1. Download and extract this ZIP.
2. Create a new empty GitHub repository (GitHub account required).
3. Upload the extracted project files and folders to the repository root. Make sure `.github/workflows/build-apk.yml` is included.
4. Open the repository's **Actions** tab.
5. Select **Build NutriTrack APK** and press **Run workflow** (or wait for the first push build).
6. When the run finishes, open it and download the artifact named **NutriTrack-Android-APK**.
7. Extract the artifact ZIP on your Android phone and tap `app-debug.apk` to install. If Android asks, allow your browser/file manager to install unknown apps.

The workflow builds a debug APK. It is suitable for personal installation and testing. A release APK for Play Store distribution should be signed with a private release key.

## Build locally (Android Studio)
Open this folder as an Android Studio project and run the `app` configuration, or run:
`gradle assembleDebug`
with Java 17, Gradle 8.9, and Android SDK platform 35 installed.
Output: `app/build/outputs/apk/debug/app-debug.apk`.

## App behavior
- Food database from supplied workbook: 459 entries, English and Arabic names.
- Food diary, targets, custom foods, saved meals, weight history stored locally on the device.
- Backup JSON and CSV export are saved to Downloads/NutriTrack on Android 10+.
- Restore backup opens Android's file picker.
- No login, cloud sync, or network permission is required.

## Important
The APK is not compiled inside this package. The included GitHub Actions workflow builds it and provides the downloadable APK artifact. Do not install the ZIP itself; install `app-debug.apk` produced by the workflow.
