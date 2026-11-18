package io.github.cleanyourtv.partymode;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.media.AudioManager;
import android.media.MediaMetadata;
import android.media.session.MediaController;
import android.media.session.MediaSessionManager;
import android.media.session.PlaybackState;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Base64;
import android.view.KeyEvent;
import android.webkit.JavascriptInterface;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.util.List;

/**
 * window.SpotiPartyTV in the screen: what plays on the TV itself (its media session; needs notification access,
 * see {@link PartyListener}) and the remote's play, pause and skip. The web app uses it only when the Hub has no
 * song of its own, and for the Hub's commands to this screen.
 *
 * JavascriptInterface methods run on a WebView thread, not the main thread.
 */
final class TvBridge {
    interface HubSink { void use(String address); }

    private final Context ctx;
    private final SharedPreferences prefs;
    private final HubSink hubSink;
    private final Handler main = new Handler(Looper.getMainLooper());
    private MediaSessionManager sessions;
    private volatile MediaController controller;
    private volatile boolean access;
    private final MediaSessionManager.OnActiveSessionsChangedListener changed = this::pick;

    TvBridge(Context ctx, SharedPreferences prefs, HubSink hubSink) {
        this.ctx = ctx;
        this.prefs = prefs;
        this.hubSink = hubSink;
    }

    /** While the screen is shown: follow the TV's media sessions. */
    void start() {
        try {
            sessions = ctx.getSystemService(MediaSessionManager.class);
            ComponentName listener = new ComponentName(ctx, PartyListener.class);
            sessions.addOnActiveSessionsChangedListener(changed, listener, main);
            pick(sessions.getActiveSessions(listener));
            access = true;
        } catch (SecurityException e) {
            sessions = null;
            access = false;
            controller = null;
        }
    }

    void stop() {
        if (sessions != null) sessions.removeOnActiveSessionsChangedListener(changed);
        sessions = null;
        controller = null;
    }

    /** Spotify when it has a session, else whatever plays (or is paused). */
    private void pick(List<MediaController> list) {
        MediaController best = null;
        int bestScore = -1;
        if (list != null) {
            for (MediaController c : list) {
                PlaybackState s = c.getPlaybackState();
                if (c.getMetadata() == null || s == null) continue;
                int score = (s.getState() == PlaybackState.STATE_PLAYING ? 2 : s.getState() == PlaybackState.STATE_PAUSED ? 1 : 0)
                        + (PartyListener.SPOTIFY.equals(c.getPackageName()) ? 3 : 0);
                if (score > bestScore) { best = c; bestScore = score; }
            }
        }
        controller = best;
    }

    private MediaController current() {
        // The session list changes on its own; ask again now and then (cheap).
        if (sessions != null) {
            try {
                pick(sessions.getActiveSessions(new ComponentName(ctx, PartyListener.class)));
            } catch (SecurityException e) {
                access = false;
            }
        }
        return controller;
    }

    @JavascriptInterface
    public boolean hasAccess() { return access; }

    /** {title, artist, album, durationMs, positionMs, playing} of what plays on the TV, or "" for nothing. */
    @JavascriptInterface
    public String nowPlaying() {
        MediaController c = current();
        if (c == null) return "";
        MediaMetadata m = c.getMetadata();
        PlaybackState s = c.getPlaybackState();
        if (m == null || s == null) return "";
        try {
            boolean playing = s.getState() == PlaybackState.STATE_PLAYING;
            long pos = s.getPosition();
            if (playing && s.getLastPositionUpdateTime() > 0) {
                pos += (long) ((SystemClock.elapsedRealtime() - s.getLastPositionUpdateTime()) * s.getPlaybackSpeed());
            }
            return new JSONObject()
                    .put("title", text(m, MediaMetadata.METADATA_KEY_TITLE))
                    .put("artist", text(m, MediaMetadata.METADATA_KEY_ARTIST))
                    .put("album", text(m, MediaMetadata.METADATA_KEY_ALBUM))
                    .put("durationMs", Math.max(0, m.getLong(MediaMetadata.METADATA_KEY_DURATION)))
                    .put("positionMs", Math.max(0, pos))
                    .put("playing", playing)
                    .toString();
        } catch (Exception e) {
            return "";
        }
    }

    /** The cover of what plays, as a data: URL (asked once per song), or "". */
    @JavascriptInterface
    public String art() {
        MediaController c = current();
        MediaMetadata m = c == null ? null : c.getMetadata();
        if (m == null) return "";
        Bitmap b = m.getBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART);
        if (b == null) b = m.getBitmap(MediaMetadata.METADATA_KEY_ART);
        if (b == null) b = m.getBitmap(MediaMetadata.METADATA_KEY_DISPLAY_ICON);
        if (b == null) {
            String uri = text(m, MediaMetadata.METADATA_KEY_ALBUM_ART_URI);
            if (uri.isEmpty()) uri = text(m, MediaMetadata.METADATA_KEY_ART_URI);
            return uri.startsWith("https://") ? uri : "";
        }
        try {
            int max = 640;
            if (b.getWidth() > max || b.getHeight() > max) {
                float f = max / (float) Math.max(b.getWidth(), b.getHeight());
                b = Bitmap.createScaledBitmap(b, Math.round(b.getWidth() * f), Math.round(b.getHeight() * f), true);
            }
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            b.compress(Bitmap.CompressFormat.JPEG, 85, out);
            return "data:image/jpeg;base64," + Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP);
        } catch (Exception e) {
            return "";
        }
    }

    @JavascriptInterface
    public boolean canControl() { return current() != null; }

    /** play, pause, toggle, next, previous, volume_up, volume_down. "" when done, else why not (for the dashboard). */
    @JavascriptInterface
    public String control(String cmd) {
        if ("volume_up".equals(cmd) || "volume_down".equals(cmd)) {
            AudioManager audio = ctx.getSystemService(AudioManager.class);
            if (audio == null) return "het volume is niet te regelen.";
            audio.adjustStreamVolume(AudioManager.STREAM_MUSIC, "volume_up".equals(cmd)
                    ? AudioManager.ADJUST_RAISE : AudioManager.ADJUST_LOWER, AudioManager.FLAG_SHOW_UI);
            return "";
        }
        MediaController c = current();
        if (c == null) return access ? "er speelt niets op de tv." : "geen meldingstoegang op de tv.";
        MediaController.TransportControls t = c.getTransportControls();
        PlaybackState s = c.getPlaybackState();
        switch (cmd == null ? "" : cmd) {
            case "play": t.play(); return "";
            case "pause": t.pause(); return "";
            case "toggle":
                if (s != null && s.getState() == PlaybackState.STATE_PLAYING) t.pause(); else t.play();
                return "";
            case "next": t.skipToNext(); return "";
            case "previous": t.skipToPrevious(); return "";
            default: return "onbekende opdracht.";
        }
    }

    /** The remote's media keys, as a command for {@link #control}; null for other keys. */
    static String mediaKey(int keyCode) {
        switch (keyCode) {
            case KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE: return "toggle";
            case KeyEvent.KEYCODE_MEDIA_PLAY: return "play";
            case KeyEvent.KEYCODE_MEDIA_PAUSE: return "pause";
            case KeyEvent.KEYCODE_MEDIA_NEXT: return "next";
            case KeyEvent.KEYCODE_MEDIA_PREVIOUS: return "previous";
            default: return null;
        }
    }

    /** This TV's name in the dashboard, until one is set. */
    @JavascriptInterface
    public String deviceName() {
        String n = Settings.Global.getString(ctx.getContentResolver(), "device_name");
        if (n == null || n.isEmpty()) n = Build.MODEL;
        return n == null || n.isEmpty() ? "Android TV" : n;
    }

    /** The Hub's address typed in on the screen ("" = search the network again). */
    @JavascriptInterface
    public void useHub(String address) { hubSink.use(address == null ? "" : address); }

    /** The address typed in last time, for the start page. */
    @JavascriptInterface
    public String typedHub() { return prefs.getString("hub", ""); }

    @JavascriptInterface
    public boolean autoOpen() { return prefs.getBoolean("auto_open", false); }

    @JavascriptInterface
    public void setAutoOpen(boolean on) { prefs.edit().putBoolean("auto_open", on).apply(); }

    /** The TV's settings page for notification access. */
    @JavascriptInterface
    public void openAccess() {
        main.post(() -> {
            try {
                ctx.startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            } catch (Exception e) {
                // Some TVs hide this page: then only ADB can give access (see the docs).
            }
        });
    }

    @JavascriptInterface
    public String version() {
        try {
            return ctx.getPackageManager().getPackageInfo(ctx.getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "";
        }
    }

    private static String text(MediaMetadata m, String key) {
        CharSequence s = m.getText(key);
        return s == null ? "" : s.toString();
    }
}
