# NutriTrack Phase 0 — Data Safety Audit

## Baseline
- Supplied source archive: `NutriTrack-Android-V2.4.0-Source.zip`.
- The archive's Gradle metadata identifies the app as versionName `2.6.2`, versionCode `11`.
- The embedded reference-food array contains 608 records.
- Diary and user-created data are stored under localStorage key `nutritrack_v2_data`.
- The current project includes local JSON backup/restore and CSV export paths.

## Phase 0 changes
1. Save now serializes state, writes it, reads it back, and compares the stored value before reporting success.
2. If persistence fails, the in-memory state rolls back to the last successfully persisted snapshot and the user receives an explicit failure message.
3. All ordinary save call sites stop before success UI or navigation when persistence fails.
4. Backup restore validates the top-level structure, required arrays, targets, diary records, foods, meals, and weight records before replacing current state.
5. Restore reports success only after the new state has been persisted and verified.
6. Android automatic backup is disabled to follow the selected local-only backup policy. Users can still export an explicit JSON backup from the app.
7. The PWA manifest display name is aligned to version 2.6.2.

## Regression checks
The Node.js test suite checks inline JavaScript syntax, guarded save calls, successful verified persistence, rollback after simulated storage failure, and backup validation/normalization.

## Build status
The GitHub Actions workflow is configured to extract the supplied source archive, apply the Phase 0 patch, run regression checks, build the Android debug APK, and verify package/version/backup metadata. The APK is not considered complete until that workflow run succeeds and its artifact is inspected.

## Scope and limitations
- The reference-food database and its nutrient values are not changed by Phase 0.
- This is a data-integrity hardening pass, not yet the V2.7 dashboard or later roadmap work.
- The tests simulate browser storage in Node.js; they do not replace device-level testing on Android.
