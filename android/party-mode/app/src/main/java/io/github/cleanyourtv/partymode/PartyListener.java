package io.github.cleanyourtv.partymode;

import android.content.ComponentName;
import android.content.Intent;
import android.media.session.MediaController;
import android.media.session.MediaSessionManager;
import android.media.session.PlaybackState;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.provider.Settings;
import android.service.notification.NotificationListenerService;
import android.util.Log;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Notification access is what lets SpotiParty see which song plays (MediaSessionManager needs an enabled listener
 * of the calling app). It reads no notifications.
 *
 * It also opens SpotiParty when Spotify starts playing on the TV ("auto_open", off by default; switch it on from the phone page): only on the step
 * from not playing to playing, so leaving SpotiParty while the music goes on does not bring it back, and a skip
 * between songs does not count. Starting an activity from the background needs "Display over other apps"
 * (SYSTEM_ALERT_WINDOW); without it Android blocks the start and the log says so.
 */
public class PartyListener extends NotificationListenerService {
    static final String SPOTIFY = "com.spotify.tv.android";
    /** Playback has to have stopped at least this long for a start to count as a new start, not a skip. */
    private static final long QUIET_MS = 3000;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private MediaSessionManager sessions;
    private final Map<MediaController, MediaController.Callback> watched = new HashMap<>();
    private boolean playing;
    private long stoppedAt;

    private final MediaSessionManager.OnActiveSessionsChangedListener changed = this::watch;

    @Override
    public void onListenerConnected() {
        super.onListenerConnected();
        try {
            sessions = getSystemService(MediaSessionManager.class);
            ComponentName me = new ComponentName(this, PartyListener.class);
            sessions.addOnActiveSessionsChangedListener(changed, me, handler);
            List<MediaController> list = sessions.getActiveSessions(me);
            playing = anyPlaying(list);   // music already playing when the TV starts: not a new start
            stoppedAt = 0;
            watch(list);
        } catch (SecurityException e) {
            sessions = null;
        }
    }

    @Override
    public void onListenerDisconnected() {
        if (sessions != null) sessions.removeOnActiveSessionsChangedListener(changed);
        sessions = null;
        for (Map.Entry<MediaController, MediaController.Callback> e : watched.entrySet()) {
            e.getKey().unregisterCallback(e.getValue());
        }
        watched.clear();
        super.onListenerDisconnected();
    }

    private void watch(List<MediaController> list) {
        for (Map.Entry<MediaController, MediaController.Callback> e : watched.entrySet()) {
            e.getKey().unregisterCallback(e.getValue());
        }
        watched.clear();
        if (list == null) return;
        for (MediaController c : list) {
            if (!SPOTIFY.equals(c.getPackageName())) continue;
            MediaController.Callback callback = new MediaController.Callback() {
                @Override
                public void onPlaybackStateChanged(PlaybackState state) {
                    check(state);
                }
            };
            c.registerCallback(callback, handler);
            watched.put(c, callback);
            check(c.getPlaybackState());
        }
    }

    private static boolean anyPlaying(List<MediaController> list) {
        if (list == null) return false;
        for (MediaController c : list) {
            PlaybackState s = c.getPlaybackState();
            if (SPOTIFY.equals(c.getPackageName()) && s != null && s.getState() == PlaybackState.STATE_PLAYING) {
                return true;
            }
        }
        return false;
    }

    private void check(PlaybackState state) {
        int s = state == null ? PlaybackState.STATE_NONE : state.getState();
        if (s == PlaybackState.STATE_PLAYING) {
            boolean wasQuiet = !playing && (stoppedAt == 0 || SystemClock.elapsedRealtime() - stoppedAt >= QUIET_MS);
            playing = true;
            if (wasQuiet) openPartyMode();
        } else if (s == PlaybackState.STATE_BUFFERING || s == PlaybackState.STATE_SKIPPING_TO_NEXT
                || s == PlaybackState.STATE_SKIPPING_TO_PREVIOUS || s == PlaybackState.STATE_CONNECTING) {
            // between songs: still the same listening session
        } else if (playing) {
            playing = false;
            stoppedAt = SystemClock.elapsedRealtime();
        }
    }

    private void openPartyMode() {
        if (!getSharedPreferences("party", MODE_PRIVATE).getBoolean("auto_open", false)) return;
        if (MainActivity.visible) return;
        if (!Settings.canDrawOverlays(this)) {
            Log.w(MainActivity.TAG, "Spotify started, but SpotiParty may not open itself: "
                    + "allow 'Display over other apps' for SpotiParty");
            return;
        }
        Log.i(MainActivity.TAG, "Spotify started playing: opening SpotiParty");
        Intent open = new Intent(this, MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        try {
            startActivity(open);
        } catch (Exception e) {
            Log.w(MainActivity.TAG, "could not open SpotiParty: " + e);
        }
    }
}
