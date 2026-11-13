package com.nutritrack.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.graphics.Color;
import android.widget.Toast;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.content.ContentValues;
import android.util.Base64;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import com.googlecode.tesseract.android.TessBaseAPI;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

public class MainActivity extends Activity {
private WebView webView;
private ValueCallback<Uri[]> filePathCallback;
private static final int FILE_CHOOSER_REQUEST = 1001;

@Override  
protected void onCreate(Bundle savedInstanceState) {  
    super.onCreate(savedInstanceState);  
    Window w = getWindow();  
    w.setStatusBarColor(Color.rgb(23,107,85));  
    w.setNavigationBarColor(Color.rgb(23,107,85));  
    w.getDecorView().setSystemUiVisibility(0);  

    webView = new WebView(this);  
    webView.setBackgroundColor(Color.rgb(243,246,244));  
    webView.getSettings().setJavaScriptEnabled(true);  
    webView.getSettings().setDomStorageEnabled(true);  
    webView.getSettings().setDatabaseEnabled(true);  
    webView.getSettings().setAllowFileAccess(true);  
    webView.getSettings().setAllowContentAccess(true);  
    webView.getSettings().setJavaScriptCanOpenWindowsAutomatically(false);  
    webView.addJavascriptInterface(new AndroidBridge(), "AndroidBridge");  

    webView.setWebViewClient(new WebViewClient() {  
        @Override  
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {  
            Uri uri = request.getUrl();  
            return !"file".equals(uri.getScheme());  
        }  
    });  
    webView.setWebChromeClient(new WebChromeClient() {  
        @Override  
        public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {  
            if (filePathCallback != null) filePathCallback.onReceiveValue(null);  
            filePathCallback = callback;  
            Intent intent;  
            try {  
                intent = params.createIntent();  
                intent.addCategory(Intent.CATEGORY_OPENABLE);  
                startActivityForResult(Intent.createChooser(intent, "Choose photo or backup file"), FILE_CHOOSER_REQUEST);  
            } catch (Exception e) {  
                filePathCallback = null;  
                return false;  
            }  
            return true;  
        }  
    });  
    setContentView(webView);  
    webView.loadUrl("file:///android_asset/index.html");  
}  

public class AndroidBridge {
    // Offline OCR after the Arabic and English language packs have been downloaded once.
    @JavascriptInterface
    public String recognizeNutritionLabel(String imageDataUrl) {
        TessBaseAPI tess = null;
        try {
            if (imageDataUrl == null) return "ERROR:No image was supplied";
            int comma = imageDataUrl.indexOf(',');
            String encoded = comma >= 0 ? imageDataUrl.substring(comma + 1) : imageDataUrl;
            byte[] imageBytes = Base64.decode(encoded, Base64.DEFAULT);
            Bitmap bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.length);
            if (bitmap == null) return "ERROR:Could not decode image";

            File baseDir = new File(getFilesDir(), "nutritrack-ocr");
            File dataDir = new File(baseDir, "tessdata");
            if (!dataDir.exists() && !dataDir.mkdirs()) throw new IOException("Cannot create OCR data folder");
            ensureLanguageFile(dataDir, "eng");
            ensureLanguageFile(dataDir, "ara");

            tess = new TessBaseAPI();
            if (!tess.init(baseDir.getAbsolutePath(), "eng+ara")) {
                tess.recycle();
                return "ERROR:OCR engine could not initialize";
            }
            tess.setImage(bitmap);
            String result = tess.getUTF8Text();
            tess.clear();
            bitmap.recycle();
            return result == null ? "" : result;
        } catch (Exception e) {
            return "ERROR:" + (e.getMessage() == null ? "OCR failed" : e.getMessage());
        } finally {
            if (tess != null) {
                try { tess.recycle(); } catch (Exception ignored) { }
            }
        }
    }

    private void ensureLanguageFile(File dataDir, String language) throws IOException {
        File target = new File(dataDir, language + ".traineddata");
        if (target.exists() && target.length() > 100000) return;
        URL url = new URL("https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/" + language + ".traineddata");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setConnectTimeout(20000);
        connection.setReadTimeout(60000);
        connection.setInstanceFollowRedirects(true);
        try {
            int code = connection.getResponseCode();
            if (code != 200) throw new IOException("Could not download " + language + " OCR data (HTTP " + code + ")");
            File temp = new File(dataDir, language + ".traineddata.tmp");
            try (InputStream in = connection.getInputStream(); FileOutputStream out = new FileOutputStream(temp)) {
                byte[] buffer = new byte[8192];
                int count;
                while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
            }
            if (!temp.renameTo(target)) {
                temp.delete();
                throw new IOException("Could not save OCR language data");
            }
        } finally {
            connection.disconnect();
        }
    }
    @JavascriptInterface  
    public void saveFile(String filename, String base64Data, String mimeType) {  
        try {  
            byte[] bytes = Base64.decode(base64Data, Base64.DEFAULT);  
            String safeName = filename == null ? "nutritrack-export" : filename.replaceAll("[^a-zA-Z0-9._-]", "_");  
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {  
                ContentValues values = new ContentValues();  
                values.put(MediaStore.Downloads.DISPLAY_NAME, safeName);  
                values.put(MediaStore.Downloads.MIME_TYPE, mimeType == null ? "application/octet-stream" : mimeType);  
                values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/NutriTrack");  
                values.put(MediaStore.Downloads.IS_PENDING, 1);  
                Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);  
                if (uri == null) throw new IOException("Could not create download");  
                try (OutputStream out = getContentResolver().openOutputStream(uri)) { out.write(bytes); }  
                values.clear();  
                values.put(MediaStore.Downloads.IS_PENDING, 0);  
                getContentResolver().update(uri, values, null, null);  
            } else {  
                File dir = new File(getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "NutriTrack");  
                if (!dir.exists()) dir.mkdirs();  
                try (FileOutputStream out = new FileOutputStream(new File(dir, safeName))) { out.write(bytes); }  
            }  
            runOnUiThread(() -> Toast.makeText(MainActivity.this, "Saved to Downloads / NutriTrack", Toast.LENGTH_LONG).show());  
        } catch (Exception e) {  
            runOnUiThread(() -> Toast.makeText(MainActivity.this, "Could not save export: " + e.getMessage(), Toast.LENGTH_LONG).show());  
        }  
    }  
}  

@Override  
protected void onActivityResult(int requestCode, int resultCode, Intent data) {  
    super.onActivityResult(requestCode, resultCode, data);  
    if (requestCode == FILE_CHOOSER_REQUEST && filePathCallback != null) {  
        Uri result = (resultCode == RESULT_OK && data != null) ? data.getData() : null;  
        filePathCallback.onReceiveValue(result == null ? null : new Uri[]{result});  
        filePathCallback = null;  
    }  
}  

@Override  
public void onBackPressed() {  
    if (webView != null && webView.canGoBack()) webView.goBack();  
    else super.onBackPressed();  
}  

@Override  
protected void onDestroy() {  
    if (webView != null) { webView.destroy(); webView = null; }  
    super.onDestroy();  
}

}
