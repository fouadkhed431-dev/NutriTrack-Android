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
