package io.github.cleanyourtv.partymode;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * SpotiParty on Android TV: the same screen as the web app, loaded from the SpotiParty Hub
 * (http://hub:8770/scherm/). Whatever the Hub runs is what the TV shows, so the TV is always as new as the Hub:
 * no app update is needed for a new look or feature.
 *
 * Until a Hub is found (UDP broadcast on 8771, or an address typed in), the TV shows a small start page from the
 * app itself. The page talks to the TV through {@link TvBridge} (window.SpotiPartyTV): what plays on the TV, and
 * the remote's play, pause and skip.
 */
public class MainActivity extends Activity {
    static final String TAG = "SpotiParty";
    private static final String START = "file:///android_asset/start.html";
    /** How often the TV checks that its Hub still answers while the screen is shown. */
    private static final long CHECK_MS = 15_000;

    private SharedPreferences prefs;
    private WebView web;
    private TvBridge bridge;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService net = Executors.newSingleThreadExecutor();
    /** "http://host:port" of the Hub the screen comes from; null while on the start page. */
    private volatile String hub;
    private int misses;
    private boolean started;

    private final Runnable check = new Runnable() {
        @Override
        public void run() {
            main.removeCallbacks(this);
            if (!started) return;
            String h = hub;
            net.execute(() -> {
                if (h == null) {
                    // Still searching: try again (the typed address first, then a broadcast).
                    String found = HubFinder.find(prefs);
                    main.post(() -> { if (started && hub == null && found != null) open(found); });
                } else if (HubFinder.ping(h)) {
                    misses = 0;
                } else if (++misses >= 3) {
                    // Gone, or moved to another address (a new IP from the router): search again.
                    misses = 0;
                    String found = HubFinder.find(prefs);
                    main.post(() -> {
                        if (!started) return;
                        if (found == null) showStart("De Hub op " + host(h) + " antwoordt niet meer. Zoeken...");
                        else if (!found.equals(h)) open(found);
                    });
                }
            });
            main.postDelayed(this, hub == null ? 5_000 : CHECK_MS);
        }
    };

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        prefs = getSharedPreferences("party", MODE_PRIVATE);

        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(11, 11, 16));
        web.setFocusable(true);
        web.setFocusableInTouchMode(true);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);           // the screen keeps its id, name and lyrics in localStorage
        s.setMediaPlaybackRequiresUserGesture(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);   // the Hub says no-store: always its newest version
        s.setUserAgentString(s.getUserAgentString() + " SpotiPartyTV/" + appVersion());
        bridge = new TvBridge(this, prefs, this::useHub);
        web.addJavascriptInterface(bridge, "SpotiPartyTV");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                // Only the Hub's own pages; a link elsewhere (Spotify, lrclib) is not for a TV screen.
                Uri u = req.getUrl();
                String h = hub;
                return h == null || !(u.getScheme() + "://" + u.getAuthority()).equals(h);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError err) {
                if (!req.isForMainFrame() || hub == null) return;
                Log.w(TAG, "screen did not load from " + hub + ": " + err.getDescription());
                String h = hub;
                showStart("Het scherm laadt niet van " + host(h) + ". Opnieuw zoeken...");
            }
        });
        setContentView(web);
        web.requestFocus();

        String last = prefs.getString("hub_url", "");
        if (!last.isEmpty()) open(last);   // the Hub from last time: usually still there, so no wait
        else showStart("");
    }

    @Override
    protected void onStart() {
        super.onStart();
        started = true;
        bridge.start();
        web.onResume();
        main.post(check);
    }

    @Override
    protected void onStop() {
        started = false;
        main.removeCallbacks(check);
        bridge.stop();
        web.onPause();
        super.onStop();
    }

    @Override
    protected void onDestroy() {
        net.shutdownNow();
        web.removeJavascriptInterface("SpotiPartyTV");
        web.destroy();
        super.onDestroy();
    }

    /** The screen from this Hub. */
    private void open(String base) {
        hub = base;
        misses = 0;
        prefs.edit().putString("hub_url", base).apply();
        String q = "?kind=tv";
        web.loadUrl(base + "/scherm/" + q);
        main.removeCallbacks(check);
        main.postDelayed(check, CHECK_MS);
    }

    /** The app's own start page: searching, or why not, with a field for the Hub's address. */
    private void showStart(String why) {
        hub = null;
        web.loadUrl(START + (why.isEmpty() ? "" : "#" + Uri.encode(why)));
        main.removeCallbacks(check);
        main.postDelayed(check, 1_000);
    }

    /** From the page: the address typed in (the start page, or the screen's settings); "" = search the network. */
    private void useHub(String address) {
        main.post(() -> {
            String a = HubFinder.normalize(address);
            prefs.edit().putString("hub", a == null ? "" : a).apply();
            if (a != null) open(a);
            else showStart("");
        });
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        // Menu opens the screen's settings (the web app's own panel); Back closes it first.
        if (keyCode == KeyEvent.KEYCODE_MENU || keyCode == KeyEvent.KEYCODE_SETTINGS) {
            web.evaluateJavascript("typeof openSettings==='function'&&openSettings(!document.getElementById('settings')"
                    + ".classList.contains('open'))", null);
            return true;
        }
        if (keyCode == KeyEvent.KEYCODE_BACK && hub != null) {
            web.evaluateJavascript("(function(){var s=document.getElementById('settings');"
                    + "if(s&&s.classList.contains('open')){openSettings(false);return true}return false})()", open -> {
                if (!"true".equals(open)) finish();
            });
            return true;
        }
        // The remote's media keys go to what plays on the TV (also when the Hub's account plays elsewhere).
        String cmd = TvBridge.mediaKey(keyCode);
        if (cmd != null) {
            bridge.control(cmd);
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    private String appVersion() {
        try {
            return getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "?";
        }
    }

    private static String host(String base) {
        return base.replaceFirst("^https?://", "");
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        }
    }
}
