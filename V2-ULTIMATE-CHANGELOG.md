# NutriTrack V2.0 Ultimate — prepared upgrade

## Included in this prepared build
- Product photo selection from the Android image picker; the photo is resized/compressed before being stored with the product.
- Product records with name, barcode text, serving size, calories, protein, fat, carbohydrates and sugar fields.
- Saved products become searchable alongside the existing reference and custom foods.
- Food database manager for searching, editing and deleting custom foods/products. Deleting a database item does not delete historical diary entries.
- Export/import of the custom food and product database as JSON.
- Existing `nutritrack_v2_data` local data key retained; missing new fields are migrated with safe defaults.
- Android file chooser now uses the requested file type, supporting image selection as well as JSON backup restore.
- New NutriTrack leaf mark in the app header and Android launcher icon resources.
- Android app versionCode 3 / versionName 2.0.0.

## Important limitations
- Arabic nutrition-label OCR is not included yet. Enter values from the photographed label and verify them before saving; this avoids silently saving incorrect OCR values.
- Barcode is stored and searchable when typed, but live barcode camera scanning / online product lookup is not included.
- Product photos are stored in local app data. Keep regular JSON backups; if storage fills, export a backup and remove unused product photos.
- A local Android build was not run in this environment because Gradle/Android SDK are not installed here. Use the repository GitHub Actions workflow to produce the APK and install-test it before replacing the existing app.
