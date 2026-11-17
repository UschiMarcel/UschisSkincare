package de.uschi.leser;

import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;

public class MainActivity extends Activity {
    private WebView web;
    private ValueCallback<Uri[]> chooser;
    private static final int PICK = 7;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        web = new WebView(this);
        setContentView(web);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setAllowUniversalAccessFromFileURLs(true);
        web.addJavascriptInterface(new Bridge(), "AndroidBridge");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, String url) {
                if (url.startsWith("file:")) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); } catch (Exception e) { }
                return true;
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> cb, FileChooserParams p) {
                if (chooser != null) chooser.onReceiveValue(null);
                chooser = cb;
                Intent i = new Intent(Intent.ACTION_GET_CONTENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("*/*");
                try { startActivityForResult(i, PICK); } catch (Exception e) { chooser = null; return false; }
                return true;
            }
        });
        web.loadUrl("file:///android_asset/index.html");
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        if (req == PICK && chooser != null) {
            Uri[] r = null;
            if (res == RESULT_OK && data != null && data.getData() != null) r = new Uri[]{data.getData()};
            chooser.onReceiveValue(r);
            chooser = null;
        }
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }

    public class Bridge {
        @JavascriptInterface
        public void save(String name, String mime, String base64) {
            try {
                byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
                boolean img = mime != null && mime.startsWith("image/");
                String sub = img ? "Skincare" : "";
                if (Build.VERSION.SDK_INT >= 29) {
                    ContentValues v = new ContentValues();
                    v.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
                    v.put(MediaStore.MediaColumns.MIME_TYPE, mime);
                    v.put(MediaStore.MediaColumns.RELATIVE_PATH, (img ? Environment.DIRECTORY_PICTURES + "/Skincare" : Environment.DIRECTORY_DOWNLOADS));
                    Uri base = img ? MediaStore.Images.Media.EXTERNAL_CONTENT_URI : MediaStore.Downloads.EXTERNAL_CONTENT_URI;
                    Uri u = getContentResolver().insert(base, v);
                    OutputStream o = getContentResolver().openOutputStream(u);
                    o.write(bytes);
                    o.close();
                } else {
                    File dir = new File(Environment.getExternalStoragePublicDirectory(img ? Environment.DIRECTORY_PICTURES : Environment.DIRECTORY_DOWNLOADS), sub);
                    dir.mkdirs();
                    FileOutputStream o = new FileOutputStream(new File(dir, name));
                    o.write(bytes);
                    o.close();
                }
                toast("Gespeichert: " + (img ? "Bilder/Skincare/" : "Downloads/") + name);
            } catch (Exception e) {
                toast("Speichern fehlgeschlagen: " + e.getMessage());
            }
        }

        private void toast(final String t) {
            runOnUiThread(new Runnable() { public void run() { Toast.makeText(MainActivity.this, t, Toast.LENGTH_LONG).show(); } });
        }
    }
}
