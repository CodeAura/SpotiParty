package io.github.cleanyourtv.partymode;

import android.app.Activity;
import android.content.ComponentName;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Outline;
import android.graphics.RenderEffect;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.media.MediaMetadata;
import android.media.session.MediaController;
import android.media.session.MediaSessionManager;
import android.media.session.PlaybackState;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewOutlineProvider;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * SpotiParty: the song Spotify is playing on the TV, full screen. The cover fills the background (blurred and
 * darkened), the lyrics run along with the song, and a QR code lets friends join the host's Spotify Jam.
 * The Jam link is pasted from the host's phone (the code in the corner while none is set, or Menu).
 */
public class MainActivity extends Activity {
    private static final int PORT = 8768;
    private static final Uri LYRICS = Uri.parse("content://io.github.cleanyourtv.lyrics.widget/lyrics");
    private static final long TICK_MS = 150;
    private static final long LYRIC_LEAD_MS = 200;
    /** Which of the lyric lines on screen is the one being sung. */
    private static final int NOW = 1;

    private SharedPreferences prefs;
    private PhoneLink link;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    /** Spotify's position, on a thread of its own so a slow cover or lyrics lookup never delays it. */
    private final ExecutorService syncWorker = Executors.newSingleThreadExecutor();
    private volatile boolean syncLoading;
    /** Every 4 s while open and linked: where Spotify says the song is, so the lyrics stay in time. */
    private final Runnable progressPoll = new Runnable() {
        @Override
        public void run() {
            handler.removeCallbacks(this);   // one chain, also after a song change asked early
            if (!started) return;
            if (!syncLoading && SpotifyApi.linked(prefs)) {
                syncLoading = true;
                syncWorker.execute(() -> {
                    SpotifyApi.Progress p = SpotifyApi.progress(prefs);
                    // Keep the last good answer for this song when a request fails; a new song clears it.
                    if (p != null) apiProgress = p;
                    if (p != null && p.durationMs > 0 && sameSong(p.title, lastTitle)) {
                        // The TV's session can give no length or a wrong one (Spotify Connect): the lyrics were then
                        // looked up for another version, or not found. Again, with the length Spotify itself gives.
                        handler.post(() -> {
                            if (Math.abs(lyricsDuration - p.durationMs) <= 3000 || trackKey.isEmpty()
                                    || !sameSong(p.title, lastTitle)) return;
                            android.util.Log.i(SpotifyApi.TAG, "lyrics: length " + lyricsDuration / 1000 + " s on the TV, "
                                    + p.durationMs / 1000 + " s at Spotify: looked up again");
                            lyricsDuration = p.durationMs;
                            loadLyrics(trackKey, lastArtist, lastTitle, lastAlbum, p.durationMs);
                        });
                    }
                    android.util.Log.i(SpotifyApi.TAG, p == null ? "sync: no answer from Spotify"
                            : "sync: " + p.ms + " ms, playing=" + p.playing + ", title match="
                            + sameSong(p.title, lastTitle));
                    if (p != null && !sameSong(p.title, lastTitle)) {
                        // Spotify still reports the song before: ask again in a second.
                        handler.post(() -> {
                            handler.removeCallbacks(progressPoll);
                            handler.postDelayed(progressPoll, 1000);
                        });
                    }
                    syncLoading = false;
                });
            }
            handler.postDelayed(this, 4000);
        }
    };

    private ImageView backdrop;
    private ImageView cover;
    private TextView title;
    private TextView artist;
    private ProgressBar progress;
    private TextView[] lyricViews;
    private TextView idle;
    private View songBlock;
    private QrView qr;
    private TextView qrTitle;
    private TextView qrText;
    private TextView resetButton;
    private TextView nextUp;
    private boolean queueLoading;

    // SpotiParty Hub: notices, the break countdown, guest Wi-Fi and "which screen is this?".
    private HubLink hub;
    private HubLink.State hubState;
    private String hubStatus = "";
    /** A notice fills the screen like the break: a big card over the dimmed party. */
    private FrameLayout notice;
    private LinearLayout noticeCard;
    private TextView noticeIcon;
    private TextView noticeKind;
    private TextView noticeText;
    private ProgressBar noticeBar;
    private String shownNotice = "";
    /** When this song was first seen (elapsedRealtime), for a position of our own when the session's is useless. */
    private long songSeenAt;
    /** The title on screen, for the sync log (read off the main thread). */
    private volatile String lastTitle = "";
    private String lastArtist = "";
    private String lastAlbum = "";
    /** The song length the current lyrics were looked up with (0 = unknown: maybe another version's lyrics). */
    private long lyricsDuration;
    /** The position Spotify's servers report (fetched with the queue), for songs that play on another device. */
    private volatile SpotifyApi.Progress apiProgress;
    /** The Jam link from the dashboard (for every screen); "" = use the one set from the phone. */
    private String hubJam = "";
    /** The hub state the Jam card was last drawn for (null = no hub). */
    private HubLink.State hubShown;
    /** Command ids already run, so a repeated answer never pauses or skips twice. */
    private final java.util.Set<String> doneCmds = new java.util.HashSet<>();
    private LinearLayout pauseView;
    private TextView pauseTitle;
    private TextView pauseClock;
    private TextView pauseSub;
    private ProgressBar pauseBar;
    private TextView identView;
    private LinearLayout wifiCard;
    private QrView wifiQr;
    private TextView wifiText;
    private String shownWifi = "";

    /** Every 10 s while SpotiParty is open: what comes next in the host's queue (friends add to it in the Jam). */
    private final Runnable queuePoll = new Runnable() {
        @Override
        public void run() {
            if (!started) return;
            loadNext();
            handler.postDelayed(this, 10_000);
        }
    };

    /** The cover gives way to a two-line title and the "Next" line, so the progress bar stays on screen. */
    private void fitCover() {
        float dp = getResources().getDisplayMetrics().density;
        int base = title.getLineCount() > 1 ? 190 : 230;
        if (nextUp.getVisibility() == View.VISIBLE) base -= 20;
        int side = Math.round(base * dp);
        ViewGroup.LayoutParams lp = cover.getLayoutParams();
        if (lp.width != side) {
            lp.width = side;
            lp.height = side;
            cover.post(() -> cover.setLayoutParams(lp));
        }
    }

    private void loadNext() {
        if (queueLoading || !SpotifyApi.linked(prefs)) {
            if (!SpotifyApi.linked(prefs)) nextUp.setVisibility(View.GONE);
            return;
        }
        queueLoading = true;
        worker.execute(() -> {
            SpotifyApi.Next next = SpotifyApi.next(prefs);
            handler.post(() -> {
                queueLoading = false;
                if (next.title != null && !next.title.isEmpty()) {
                    nextUp.setText(getString(R.string.next_up, next.title,
                            next.artist == null || next.artist.isEmpty() ? "" : " · " + next.artist));
                    nextUp.setVisibility(View.VISIBLE);
                } else if ("login".equals(next.error)) {
                    nextUp.setText(R.string.next_login);
                    nextUp.setVisibility(View.VISIBLE);
                } else if ("forbidden".equals(next.error)) {
                    nextUp.setText(R.string.next_forbidden);
                    nextUp.setVisibility(View.VISIBLE);
                } else if ("idle".equals(next.error)) {
                    nextUp.setText(R.string.next_idle);   // the linked account plays nothing: another account on the TV?
                    nextUp.setVisibility(View.VISIBLE);
                } else if (next.error != null && next.error.startsWith("error")) {
                    nextUp.setText(getString(R.string.next_error, next.error.substring(5).trim()));
                    nextUp.setVisibility(View.VISIBLE);
                } else {
                    nextUp.setVisibility(View.GONE);   // an empty queue, or offline this time
                }
                fitCover();
            });
        });
    }
    private boolean showingSetup;

    private MediaSessionManager sessions;
    private MediaController controller;
    private String trackKey = "";
    /** The cover on screen now, so a later update of the same song with its cover is not missed or redrawn. */
    private Bitmap shownArt;
    private long[] times = new long[0];
    private String[] lines = new String[0];
    private boolean synced;
    private int shownLine = -2;
    private boolean started;

    private final MediaSessionManager.OnActiveSessionsChangedListener sessionsChanged = this::pick;

    private final MediaController.Callback callback = new MediaController.Callback() {
        @Override public void onMetadataChanged(MediaMetadata metadata) { update(); }
        @Override public void onPlaybackStateChanged(PlaybackState state) { update(); }
        @Override public void onSessionDestroyed() { setController(null); }
    };

    private final Runnable tick = new Runnable() {
        @Override
        public void run() {
            if (!started) return;
            showPosition();
            showBreak();
            handler.postDelayed(this, TICK_MS);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        prefs = getSharedPreferences("party", MODE_PRIVATE);
        float dp = getResources().getDisplayMetrics().density;

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(0xFF0B0B10);
        backdrop = new ImageView(this);
        backdrop.setScaleType(ImageView.ScaleType.CENTER_CROP);
        root.addView(backdrop, match());
        View shade = new View(this);
        shade.setBackground(new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,
                new int[]{0xB3000000, 0x8C000000, 0xA6000000}));
        root.addView(shade, match());

        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        int pad = Math.round(52 * dp);
        row.setPadding(pad, Math.round(40 * dp), pad, Math.round(40 * dp));
        root.addView(row, match());

        // Left: cover, title, artist, progress.
        LinearLayout song = new LinearLayout(this);
        song.setOrientation(LinearLayout.VERTICAL);
        songBlock = song;
        cover = new ImageView(this);
        cover.setScaleType(ImageView.ScaleType.CENTER_CROP);
        cover.setBackgroundColor(0x33FFFFFF);
        int radius = Math.round(16 * dp);
        cover.setOutlineProvider(new ViewOutlineProvider() {
            @Override
            public void getOutline(View v, Outline outline) {
                outline.setRoundRect(0, 0, v.getWidth(), v.getHeight(), radius);
            }
        });
        cover.setClipToOutline(true);
        cover.setElevation(24 * dp);
        int coverSize = Math.round(230 * dp);
        song.addView(cover, new LinearLayout.LayoutParams(coverSize, coverSize));
        title = label(26, 0xFFFFFFFF, Typeface.BOLD);
        title.setPadding(0, Math.round(16 * dp), 0, 0);
        // A title on two lines takes the room of the progress bar: the cover gives way so everything stays on screen.
        title.addOnLayoutChangeListener((v, l, t, r, b, ol, ot, or, ob) -> fitCover());
        title.setMaxLines(2);
        title.setEllipsize(TextUtils.TruncateAt.END);
        song.addView(title, new LinearLayout.LayoutParams(coverSize + Math.round(70 * dp), ViewGroup.LayoutParams.WRAP_CONTENT));
        artist = label(17, 0xCCFFFFFF, Typeface.NORMAL);
        artist.setSingleLine(true);
        artist.setEllipsize(TextUtils.TruncateAt.END);
        song.addView(artist, new LinearLayout.LayoutParams(coverSize + Math.round(70 * dp), ViewGroup.LayoutParams.WRAP_CONTENT));
        // "Next: song · artist" from the host's Spotify queue, once Spotify is linked.
        nextUp = label(13, 0x99FFFFFF, Typeface.NORMAL);
        nextUp.setSingleLine(true);
        nextUp.setEllipsize(TextUtils.TruncateAt.END);
        nextUp.setPadding(0, Math.round(4 * dp), 0, 0);
        nextUp.setVisibility(View.GONE);
        song.addView(nextUp, new LinearLayout.LayoutParams(coverSize + Math.round(70 * dp), ViewGroup.LayoutParams.WRAP_CONTENT));
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(1000);
        LinearLayout.LayoutParams pl = new LinearLayout.LayoutParams(coverSize, Math.round(5 * dp));
        pl.topMargin = Math.round(14 * dp);
        song.addView(progress, pl);
        row.addView(song, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        // Right: the lyrics, the line being sung in the middle.
        LinearLayout lyrics = new LinearLayout(this);
        lyrics.setOrientation(LinearLayout.VERTICAL);
        lyrics.setGravity(Gravity.CENTER_VERTICAL);
        // Above the QR card: one line back, the line now, and the two coming up.
        lyrics.setPadding(Math.round(52 * dp), 0, 0, Math.round(110 * dp));
        lyricViews = new TextView[4];
        int[] sizes = {19, 34, 22, 17};
        int[] colors = {0x59FFFFFF, 0xFFFFFFFF, 0x99FFFFFF, 0x59FFFFFF};
        for (int i = 0; i < lyricViews.length; i++) {
            TextView t = label(sizes[i], colors[i], i == NOW ? Typeface.BOLD : Typeface.NORMAL);
            t.setMaxLines(i == NOW ? 2 : 1);
            t.setEllipsize(TextUtils.TruncateAt.END);
            t.setPadding(0, Math.round((i == NOW ? 9 : 4) * dp), 0, Math.round((i == NOW ? 9 : 4) * dp));
            lyricViews[i] = t;
            lyrics.addView(t);
        }
        row.addView(lyrics, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, 1f));

        idle = label(22, 0xFFFFFFFF, Typeface.BOLD);
        idle.setGravity(Gravity.CENTER);
        idle.setText(R.string.idle);
        int ip = Math.round(140 * dp);
        idle.setPadding(ip, 0, ip, 0);
        FrameLayout.LayoutParams il = new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP);
        il.topMargin = Math.round(150 * dp);
        root.addView(idle, il);

        // Bottom right: the QR card.
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        GradientDrawable glass = new GradientDrawable();
        glass.setColor(0x99000000);
        glass.setCornerRadius(18 * dp);
        glass.setStroke(Math.max(1, Math.round(dp)), 0x33FFFFFF);
        card.setBackground(glass);
        int cp = Math.round(9 * dp);
        card.setPadding(cp, cp, Math.round(14 * dp), cp);
        qr = new QrView(this);
        int qs = Math.round(70 * dp);
        card.addView(qr, new LinearLayout.LayoutParams(qs, qs));
        LinearLayout qrWords = new LinearLayout(this);
        qrWords.setOrientation(LinearLayout.VERTICAL);
        qrWords.setPadding(Math.round(11 * dp), 0, 0, 0);
        qrTitle = label(14, 0xFFFFFFFF, Typeface.BOLD);
        qrText = label(11, 0xCCFFFFFF, Typeface.NORMAL);
        qrTitle.setSingleLine(true);
        qrWords.addView(qrTitle);
        qrWords.addView(qrText);
        resetButton = makeResetButton(dp);
        LinearLayout.LayoutParams bl = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        bl.topMargin = Math.round(7 * dp);
        qrWords.addView(resetButton, bl);
        // A fixed width, so the title and the wrapped text keep their room next to the button.
        card.addView(qrWords, new LinearLayout.LayoutParams(Math.round(190 * dp), ViewGroup.LayoutParams.WRAP_CONTENT));
        // The guest Wi-Fi card (from the Hub) sits to the left of the Jam card.
        wifiCard = new LinearLayout(this);
        wifiCard.setOrientation(LinearLayout.HORIZONTAL);
        wifiCard.setGravity(Gravity.CENTER_VERTICAL);
        wifiCard.setBackground(glass.getConstantState().newDrawable().mutate());
        wifiCard.setPadding(cp, cp, Math.round(14 * dp), cp);
        wifiQr = new QrView(this);
        wifiCard.addView(wifiQr, new LinearLayout.LayoutParams(qs, qs));
        LinearLayout wifiWords = new LinearLayout(this);
        wifiWords.setOrientation(LinearLayout.VERTICAL);
        wifiWords.setPadding(Math.round(11 * dp), 0, 0, 0);
        TextView wifiTitle = label(14, 0xFFFFFFFF, Typeface.BOLD);
        wifiTitle.setText(R.string.wifi_title);
        wifiText = label(11, 0xCCFFFFFF, Typeface.NORMAL);
        wifiWords.addView(wifiTitle);
        wifiWords.addView(wifiText);
        wifiCard.addView(wifiWords, new LinearLayout.LayoutParams(Math.round(150 * dp), ViewGroup.LayoutParams.WRAP_CONTENT));
        wifiCard.setVisibility(View.GONE);

        LinearLayout corner = new LinearLayout(this);
        corner.setOrientation(LinearLayout.HORIZONTAL);
        corner.setGravity(Gravity.BOTTOM);
        LinearLayout.LayoutParams wl = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        wl.rightMargin = Math.round(12 * dp);
        corner.addView(wifiCard, wl);
        corner.addView(card);
        FrameLayout.LayoutParams cl = new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM | Gravity.END);
        cl.setMargins(0, 0, Math.round(40 * dp), Math.round(30 * dp));
        root.addView(corner, cl);

        // The break: a big countdown over everything.
        pauseView = new LinearLayout(this);
        pauseView.setOrientation(LinearLayout.VERTICAL);
        pauseView.setGravity(Gravity.CENTER);
        pauseView.setBackgroundColor(0xE6000000);
        pauseView.setClickable(true);
        pauseTitle = label(44, 0xFFFFFFFF, Typeface.BOLD);
        pauseTitle.setGravity(Gravity.CENTER);
        pauseClock = label(150, 0xFF1ED760, Typeface.BOLD);
        pauseClock.setGravity(Gravity.CENTER);
        pauseClock.setFontFeatureSettings("tnum");
        pauseBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        pauseBar.setMax(1000);
        pauseBar.setProgressTintList(android.content.res.ColorStateList.valueOf(0xFF1ED760));
        pauseSub = label(22, 0xCCFFFFFF, Typeface.NORMAL);
        pauseSub.setGravity(Gravity.CENTER);
        pauseView.addView(pauseTitle);
        pauseView.addView(pauseClock);
        LinearLayout.LayoutParams pbl = new LinearLayout.LayoutParams(Math.round(420 * dp), Math.round(8 * dp));
        pbl.topMargin = Math.round(8 * dp);
        pbl.bottomMargin = Math.round(16 * dp);
        pauseView.addView(pauseBar, pbl);
        pauseView.addView(pauseSub);
        pauseView.setVisibility(View.GONE);
        root.addView(pauseView, match());

        // A notice from the Hub: full screen like the break (and above it): icon, kind, the text big, time left.
        notice = new FrameLayout(this);
        notice.setBackgroundColor(0xD9000000);
        notice.setClickable(true);
        notice.setVisibility(View.GONE);
        noticeCard = new LinearLayout(this);
        noticeCard.setOrientation(LinearLayout.VERTICAL);
        noticeCard.setGravity(Gravity.CENTER_HORIZONTAL);
        int np = Math.round(40 * dp);
        noticeCard.setPadding(np * 2, np, np * 2, np);
        noticeCard.setElevation(30 * dp);
        noticeIcon = label(80, 0xFFFFFFFF, Typeface.NORMAL);
        noticeIcon.setShadowLayer(0, 0, 0, 0);
        noticeIcon.setGravity(Gravity.CENTER);
        noticeKind = label(22, 0xFF1ED760, Typeface.BOLD);
        noticeKind.setGravity(Gravity.CENTER);
        noticeKind.setLetterSpacing(0.12f);
        noticeKind.setPadding(0, Math.round(10 * dp), 0, Math.round(8 * dp));
        noticeText = label(56, 0xFFFFFFFF, Typeface.BOLD);
        noticeText.setGravity(Gravity.CENTER);
        noticeText.setMaxLines(5);
        noticeText.setEllipsize(TextUtils.TruncateAt.END);
        noticeBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        noticeBar.setMax(1000);
        noticeCard.addView(noticeIcon);
        noticeCard.addView(noticeKind);
        noticeCard.addView(noticeText);
        LinearLayout.LayoutParams nbl = new LinearLayout.LayoutParams(Math.round(520 * dp), Math.round(10 * dp));
        nbl.topMargin = Math.round(26 * dp);
        noticeCard.addView(noticeBar, nbl);
        FrameLayout.LayoutParams ncl = new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER);
        ncl.leftMargin = ncl.rightMargin = Math.round(110 * dp);
        notice.addView(noticeCard, ncl);
        root.addView(notice, match());

        // "Aanwijzen" in the dashboard: this screen's name, big, for a few seconds.
        identView = label(90, 0xFF0B0B10, Typeface.BOLD);
        identView.setShadowLayer(0, 0, 0, 0);
        identView.setGravity(Gravity.CENTER);
        identView.setBackgroundColor(0xFF1ED760);
        identView.setVisibility(View.GONE);
        root.addView(identView, match());

        setContentView(root);
        root.setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }

    /**
     * "Reset Jam": forgets the Jam link (a stopped Jam's link no longer works) and shows the code to set a new one.
     * It asks for a second OK within 4 s, so a friend holding the remote does not end the party's code by accident.
     */
    private TextView makeResetButton(float dp) {
        TextView b = label(12, 0xFFFFFFFF, Typeface.BOLD);
        b.setText(R.string.reset_jam);
        b.setShadowLayer(0, 0, 0, 0);
        int hp = Math.round(11 * dp);
        int vp = Math.round(5 * dp);
        b.setPadding(hp, vp, hp, vp);
        GradientDrawable idle = new GradientDrawable();
        idle.setColor(0x33FFFFFF);
        idle.setCornerRadius(18 * dp);
        GradientDrawable focused = new GradientDrawable();
        focused.setColor(0xFF1ED760);
        focused.setCornerRadius(18 * dp);
        android.graphics.drawable.StateListDrawable states = new android.graphics.drawable.StateListDrawable();
        states.addState(new int[]{android.R.attr.state_focused}, focused);
        states.addState(new int[]{}, idle);
        b.setBackground(states);
        b.setFocusable(true);
        b.setOnFocusChangeListener((v, has) -> b.setTextColor(has ? 0xFF0B0B10 : 0xFFFFFFFF));
        b.setOnClickListener(v -> {
            long now = SystemClock.uptimeMillis();
            if (!resetArmed) {
                resetArmed = true;
                armedAt = now;
                b.setText(R.string.reset_confirm);
                handler.postDelayed(disarmReset, 4000);
                return;
            }
            // A double press (or one press arriving twice) is not a confirmation: the second OK must be deliberate.
            if (now - armedAt < 600) return;
            handler.removeCallbacks(disarmReset);
            resetArmed = false;
            prefs.edit().remove("jam").apply();
            showingSetup = false;
            showQr();
        });
        return b;
    }

    private boolean resetArmed;
    private long armedAt;

    private final Runnable disarmReset = () -> {
        resetArmed = false;
        if (resetButton != null) resetButton.setText(R.string.reset_jam);
    };

    private static FrameLayout.LayoutParams match() {
        return new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
    }

    private TextView label(int sp, int color, int style) {
        TextView t = new TextView(this);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        t.setTextColor(color);
        t.setTypeface(Typeface.create("sans-serif", style));
        t.setShadowLayer(8 * getResources().getDisplayMetrics().density, 0, 2, 0x99000000);
        return t;
    }

    /** On screen now: PartyListener does not open SpotiParty again over itself. */
    static volatile boolean visible;

    @Override
    protected void onResume() {
        super.onResume();
        visible = true;
    }

    @Override
    protected void onPause() {
        visible = false;
        super.onPause();
    }

    @Override
    protected void onStart() {
        super.onStart();
        started = true;
        link = new PhoneLink(PORT, this::handle);
        link.start();
        showQr();
        hub = new HubLink(prefs, this::onHub);
        reportPlayer();
        hub.start();
        try {
            sessions = getSystemService(MediaSessionManager.class);
            ComponentName listener = new ComponentName(this, PartyListener.class);
            sessions.addOnActiveSessionsChangedListener(sessionsChanged, listener, handler);
            pick(sessions.getActiveSessions(listener));
        } catch (SecurityException e) {
            sessions = null;
            idle.setText(R.string.needs_access);
            idle.setVisibility(View.VISIBLE);
            songBlock.setVisibility(View.INVISIBLE);
        }
        handler.post(tick);
        handler.post(queuePoll);
        handler.post(progressPoll);
    }

    @Override
    protected void onStop() {
        started = false;
        handler.removeCallbacks(tick);
        handler.removeCallbacks(queuePoll);
        handler.removeCallbacks(progressPoll);
        if (sessions != null) sessions.removeOnActiveSessionsChangedListener(sessionsChanged);
        sessions = null;
        setController(null);
        if (link != null) link.stop();
        link = null;
        if (hub != null) hub.stop();
        hub = null;
        onHub(null, "");
        super.onStop();
    }

    @Override
    protected void onDestroy() {
        worker.shutdownNow();
        syncWorker.shutdownNow();
        super.onDestroy();
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_MENU) {
            showingSetup = !showingSetup;
            showQr();
            return true;
        }
        if (keyCode == KeyEvent.KEYCODE_BACK && showingSetup) {
            showingSetup = false;
            showQr();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    /** The Jam's code once a link is set; until then (or with Menu) the code to set it from the phone. */
    /**
     * A media command from the Hub, on whatever plays on the TV (Spotify, or any app with a media session).
     * Returns null when done, or why not, in words for the dashboard.
     */
    private String runMedia(String cmd) {
        if ("volume_up".equals(cmd) || "volume_down".equals(cmd)) {
            android.media.AudioManager audio = getSystemService(android.media.AudioManager.class);
            if (audio == null) return "het volume is niet te regelen.";
            audio.adjustStreamVolume(android.media.AudioManager.STREAM_MUSIC, "volume_up".equals(cmd)
                    ? android.media.AudioManager.ADJUST_RAISE : android.media.AudioManager.ADJUST_LOWER,
                    android.media.AudioManager.FLAG_SHOW_UI);
            return null;
        }
        MediaController c = controller;
        if (c == null) return sessions == null ? "geen meldingstoegang op de tv." : "er speelt niets op de tv.";
        MediaController.TransportControls t = c.getTransportControls();
        switch (cmd) {
            case "play": t.play(); return null;
            case "pause": t.pause(); return null;
            case "next": t.skipToNext(); return null;
            case "previous": t.skipToPrevious(); return null;
            default: return "onbekende opdracht.";
        }
    }

    private void showQr() {
        // Once this TV has seen a Hub, the Jam link comes from its dashboard only (kept between connections);
        // the link once set from the phone is no longer used.
        boolean hubbed = prefs.getBoolean("hub_seen", false);
        if (hubbed && hubJam.isEmpty()) hubJam = prefs.getString("hub_jam", "");
        String jam = hubbed ? hubJam : prefs.getString("jam", "");
        String setup = link == null ? null : link.address(this);
        View card = (View) qr.getParent();
        // With a Hub the Jam link is set in the dashboard: no "set the Jam" code on the TV then (Menu still shows it).
        if (jam.isEmpty() && (hubState != null || hubbed) && !showingSetup) {
            card.setVisibility(View.GONE);
            resetButton.setVisibility(View.GONE);
            return;
        }
        card.setVisibility(View.VISIBLE);
        if (!jam.isEmpty() && !showingSetup) {
            qr.setText(jam);
            qrTitle.setText(R.string.jam_title);
            qrText.setText(R.string.jam_text);
        } else {
            qr.setText(setup);
            qrTitle.setText(R.string.setup_title);
            qrText.setText(setup == null ? getString(R.string.no_network) : getString(R.string.setup_text));
        }
        // The reset button only for a Jam link set from the phone (the dashboard's has its own Weghalen); it has the
        // remote's focus then, so OK reaches it.
        boolean hasJam = !jam.isEmpty() && !hubbed;
        resetButton.setVisibility(hasJam ? View.VISIBLE : View.GONE);
        resetButton.setText(R.string.reset_jam);
        if (hasJam) resetButton.requestFocus();
    }

    private void pick(List<MediaController> list) {
        MediaController best = null;
        if (list != null) {
            for (MediaController c : list) {
                PlaybackState s = c.getPlaybackState();
                if (c.getMetadata() == null || s == null) continue;
                if (s.getState() == PlaybackState.STATE_PLAYING) {
                    best = c;
                    break;
                }
                if (best == null && s.getState() == PlaybackState.STATE_PAUSED) best = c;
            }
        }
        setController(best);
    }

    private void setController(MediaController c) {
        if (controller != null) controller.unregisterCallback(callback);
        controller = c;
        if (controller != null) controller.registerCallback(callback, handler);
        update();
    }

    /** Tells the Hub whether this TV can control its music and whether it plays (for the dashboard's buttons). */
    private void reportPlayer() {
        MediaController c = controller;
        PlaybackState s = c == null ? null : c.getPlaybackState();
        if (hub != null) hub.setPlayer(c != null, s != null && s.getState() == PlaybackState.STATE_PLAYING);
    }

    private void update() {
        reportPlayer();
        MediaController c = controller;
        MediaMetadata m = c == null ? null : c.getMetadata();
        PlaybackState s = c == null ? null : c.getPlaybackState();
        boolean show = m != null && s != null && s.getState() != PlaybackState.STATE_STOPPED
                && s.getState() != PlaybackState.STATE_NONE && s.getState() != PlaybackState.STATE_ERROR;
        if (!show) {
            if (sessions != null) idle.setText(R.string.idle);
            idle.setVisibility(View.VISIBLE);
            songBlock.setVisibility(View.INVISIBLE);
            for (TextView t : lyricViews) t.setText("");
            trackKey = "";
            if (hub != null) hub.setSong("");
            return;
        }
        idle.setVisibility(View.GONE);
        songBlock.setVisibility(View.VISIBLE);
        String songTitle = text(m, MediaMetadata.METADATA_KEY_TITLE);
        String songArtist = text(m, MediaMetadata.METADATA_KEY_ARTIST);
        String album = text(m, MediaMetadata.METADATA_KEY_ALBUM);
        long duration = m.getLong(MediaMetadata.METADATA_KEY_DURATION);
        lastTitle = songTitle;
        lastArtist = songArtist;
        lastAlbum = album;
        title.setText(songTitle);
        artist.setText(songArtist);
        if (hub != null) hub.setSong(songArtist.isEmpty() ? songTitle : songTitle + " – " + songArtist);
        songBlock.animate().alpha(s.getState() == PlaybackState.STATE_PAUSED ? 0.55f : 1f).setDuration(250).start();

        String key = songArtist + "\n" + songTitle;
        // Spotify sends the title first and the cover in a later update of the same song: every update is checked
        // for a cover, not only the first one of a song.
        Bitmap art = m.getBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART);
        if (art == null) art = m.getBitmap(MediaMetadata.METADATA_KEY_ART);
        if (art == null) art = m.getBitmap(MediaMetadata.METADATA_KEY_DISPLAY_ICON);
        boolean newSong = !key.equals(trackKey);
        if (art != null && art != shownArt) {
            showArt(art);
        } else if (art == null && newSong) {
            cover.setImageDrawable(null);   // the old song's cover must not stand for the new one; the backdrop stays
            shownArt = null;
            String uri = text(m, MediaMetadata.METADATA_KEY_ALBUM_ART_URI);
            if (uri.isEmpty()) uri = text(m, MediaMetadata.METADATA_KEY_ART_URI);
            loadArtUri(uri, key);
        }
        if (!newSong) return;
        trackKey = key;
        songSeenAt = SystemClock.elapsedRealtime() - Math.max(0, Math.min(s.getPosition(), 15_000));
        apiProgress = null;
        handler.removeCallbacks(progressPoll);
        handler.postDelayed(progressPoll, 800);
        times = new long[0];
        lines = new String[0];
        synced = false;
        shownLine = -2;
        for (TextView t : lyricViews) t.setText("");
        lyricsDuration = duration;
        loadLyrics(key, songArtist, songTitle, album, duration);
        // A new song moved the queue: ask again once Spotify's servers have caught up.
        handler.removeCallbacks(queuePoll);
        handler.postDelayed(queuePoll, 1500);
    }

    private static String text(MediaMetadata m, String key) {
        CharSequence v = m.getText(key);
        return v == null ? "" : v.toString().trim();
    }

    /** The cover, and the same cover blurred behind everything, tinted with its own colour for the progress bar. */
    private void showArt(Bitmap art) {
        shownArt = art;
        cover.setImageBitmap(art);
        if (art == null) {
            backdrop.setImageDrawable(null);
            return;
        }
        Bitmap background;
        if (Build.VERSION.SDK_INT >= 31) {
            background = Bitmap.createScaledBitmap(art, 320, 320, true);
            backdrop.setRenderEffect(RenderEffect.createBlurEffect(70f, 70f, Shader.TileMode.CLAMP));
        } else {
            background = Bitmap.createScaledBitmap(art, 16, 16, true);   // scaled back up, it is a soft blur
        }
        // Straight in, with a short lift instead of a fade from black.
        backdrop.animate().cancel();
        backdrop.setAlpha(0.6f);
        backdrop.setImageBitmap(background);
        backdrop.animate().alpha(1f).setDuration(220).start();
        int accent = average(art);
        progress.setProgressTintList(android.content.res.ColorStateList.valueOf(accent));
        progress.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(0x40FFFFFF));
    }

    /** A cover the app gives only as an address (content:// or https://), loaded in the background. */
    private void loadArtUri(String uri, String key) {
        if (uri.isEmpty()) return;
        worker.execute(() -> {
            Bitmap bitmap = null;
            try {
                java.io.InputStream in;
                if (uri.startsWith("https://")) {
                    java.net.HttpURLConnection c = (java.net.HttpURLConnection) new java.net.URL(uri).openConnection();
                    c.setConnectTimeout(4000);
                    c.setReadTimeout(6000);
                    in = c.getInputStream();
                } else if (uri.startsWith("content://") || uri.startsWith("android.resource://")) {
                    in = getContentResolver().openInputStream(Uri.parse(uri));
                } else {
                    return;
                }
                try (java.io.InputStream stream = in) {
                    bitmap = android.graphics.BitmapFactory.decodeStream(stream);
                }
            } catch (Exception ignored) {
                // no cover
            }
            Bitmap loaded = bitmap;
            handler.post(() -> {
                if (loaded != null && key.equals(trackKey) && shownArt == null) showArt(loaded);
            });
        });
    }

    /** The cover's average colour, lifted so it stays visible on the dark background. */
    private static int average(Bitmap art) {
        Bitmap one = Bitmap.createScaledBitmap(art, 1, 1, true);
        int c = one.getPixel(0, 0);
        float[] hsv = new float[3];
        Color.colorToHSV(c, hsv);
        hsv[1] = Math.max(hsv[1], 0.55f);
        hsv[2] = Math.max(hsv[2], 0.85f);
        return Color.HSVToColor(hsv);
    }

    private void loadLyrics(String key, String songArtist, String songTitle, String album, long duration) {
        worker.execute(() -> {
            List<Long> t = new ArrayList<>();
            List<String> l = new ArrayList<>();
            boolean addOn = true;
            try (Cursor c = getContentResolver().query(LYRICS, null, null, new String[]{songArtist, songTitle, album,
                    String.valueOf(duration / 1000)}, null)) {
                if (c == null) {
                    addOn = false;
                } else {
                    while (c.moveToNext()) {
                        t.add(c.getLong(0));
                        l.add(c.getString(1));
                    }
                }
            } catch (Exception e) {
                addOn = false;
            }
            boolean available = addOn;
            handler.post(() -> {
                if (!key.equals(trackKey)) return;
                times = new long[t.size()];
                for (int i = 0; i < times.length; i++) times[i] = t.get(i);
                lines = l.toArray(new String[0]);
                synced = times.length > 0 && times[0] >= 0;
                shownLine = -2;
                if (lines.length == 0) {
                    lyricViews[NOW].setText(available ? R.string.no_lyrics : R.string.no_lyrics_addon);
                    lyricViews[NOW].setTextSize(TypedValue.COMPLEX_UNIT_SP, 22);
                } else {
                    lyricViews[NOW].setTextSize(TypedValue.COMPLEX_UNIT_SP, 34);
                    if (!synced) showLines(0);
                }
            });
        });
    }

    /** Spotify's title and the TV's can differ a little ("Song - Radio Edit", "Song (feat. X)"). */
    private static boolean sameSong(String a, String b) {
        String x = a.toLowerCase(Locale.ROOT).trim(), y = b.toLowerCase(Locale.ROOT).trim();
        return !x.isEmpty() && !y.isEmpty() && (x.equals(y) || x.startsWith(y) || y.startsWith(x));
    }

    private void showPosition() {
        MediaController c = controller;
        PlaybackState s = c == null ? null : c.getPlaybackState();
        MediaMetadata m = c == null ? null : c.getMetadata();
        if (s == null || m == null) return;
        long now = SystemClock.elapsedRealtime();
        long position = s.getPosition();
        if (s.getState() == PlaybackState.STATE_PLAYING) {
            position += (long) ((now - s.getLastPositionUpdateTime()) * s.getPlaybackSpeed());
        }
        long duration = m.getLong(MediaMetadata.METADATA_KEY_DURATION);
        // Spotify's own position comes first: the TV's session is often wrong for a song that plays on another
        // device (Spotify Connect). It keeps a frozen position that, counted on, drifts away from the song or
        // lands far past its end (the lyrics then stay on the last, empty line).
        // One good answer from Spotify holds for the whole song: counted on from then it stays right, also when a
        // later request fails on a shaky Wi-Fi (the TV's own clock would start late and run behind).
        SpotifyApi.Progress p = apiProgress;
        if (p != null && sameSong(p.title, title.getText().toString())) {
            position = p.ms + (p.playing ? now - p.at : 0);
            if (p.durationMs > 0) duration = p.durationMs;   // the session's length can be wrong as well
        } else if (position < 0 || (duration > 0 && position > duration + 3000)
                || s.getPosition() == PlaybackState.PLAYBACK_POSITION_UNKNOWN) {
            position = now - songSeenAt;   // no Spotify link: our own clock since the song came up
        }
        if (duration > 0) position = Math.min(position, duration);
        if (duration > 0) progress.setProgress((int) Math.min(1000, position * 1000 / duration));
        if (!synced) return;
        // A line shows a little before it is sung: reading takes a moment, and sound reaches you after the TV draws.
        long ahead = position + LYRIC_LEAD_MS;
        int index = -1;
        for (int i = 0; i < times.length; i++) {
            if (times[i] <= ahead) index = i; else break;
        }
        if (index != shownLine) {
            shownLine = index;
            showLines(index);
        }
    }

    /** One line before, the line now, two after. */
    private void showLines(int index) {
        for (int i = 0; i < lyricViews.length; i++) {
            int at = index + i - NOW;
            String s = at >= 0 && at < lines.length ? lines[at] : "";
            lyricViews[i].setText(s.isEmpty() && i == NOW ? "♪" : s);
        }
        TextView now = lyricViews[NOW];
        now.setAlpha(0.2f);
        now.setTranslationY(18 * getResources().getDisplayMetrics().density);
        now.animate().alpha(1f).translationY(0).setDuration(260).start();
    }

    private PhoneLink.Response handle(String method, String path, Map<String, String> query, byte[] body) {
        if ("GET".equals(method) && "/".equals(path)) {
            return PhoneLink.Response.html(PhoneLink.page(getString(R.string.app_name), PHONE_PAGE));
        }
        if ("GET".equals(method) && "/jam".equals(path)) {
            return PhoneLink.Response.text(200, prefs.getString("jam", ""));
        }
        if ("POST".equals(method) && "/jam".equals(path)) {
            String jam = new String(body, StandardCharsets.UTF_8).trim();
            if (!jam.isEmpty() && !isSpotifyLink(jam)) {
                return PhoneLink.Response.text(400, getString(R.string.bad_link));
            }
            prefs.edit().putString("jam", jam).apply();
            runOnUiThread(() -> {
                showingSetup = false;
                showQr();
            });
            return PhoneLink.Response.text(200, getString(jam.isEmpty() ? R.string.cleared : R.string.saved));
        }
        if ("GET".equals(method) && "/spotify".equals(path)) {
            return PhoneLink.Response.text(200, (SpotifyApi.linked(prefs) ? "linked" : "no") + "\n"
                    + prefs.getString("sp_client", ""));
        }
        if ("POST".equals(method) && "/spotify/login".equals(path)) {
            String client = new String(body, StandardCharsets.UTF_8).trim();
            if (!client.matches("[0-9a-fA-F]{32}")) {
                return PhoneLink.Response.text(400, "Dat lijkt geen Client ID (32 tekens, cijfers en a-f).");
            }
            return PhoneLink.Response.text(200, SpotifyApi.authorizeUrl(prefs, client));
        }
        if ("POST".equals(method) && "/spotify/code".equals(path)) {
            String pasted = new String(body, StandardCharsets.UTF_8);
            try {
                String problem = SpotifyApi.finishLogin(prefs, pasted);
                if (problem != null) {
                    android.util.Log.w(SpotifyApi.TAG, "login not finished: " + problem);
                    return PhoneLink.Response.text(400, problem);
                }
                android.util.Log.i(SpotifyApi.TAG, "login finished, tokens saved");
            } catch (SpotifyApi.ApiError e) {
                android.util.Log.w(SpotifyApi.TAG, "code exchange refused: " + e.getMessage());
                return PhoneLink.Response.text(400, "Spotify weigerde de code (" + e.code + "). "
                        + "Klopt de Redirect URI precies (" + SpotifyApi.REDIRECT + ")? Log anders opnieuw in.");
            } catch (Exception e) {
                android.util.Log.w(SpotifyApi.TAG, "code exchange failed: " + e);
                return PhoneLink.Response.text(400, "Spotify is niet bereikbaar vanaf de tv. Probeer het zo nog eens.");
            }
            SpotifyApi.Next next = SpotifyApi.next(prefs);
            runOnUiThread(this::loadNext);
            if ("forbidden".equals(next.error)) {
                return PhoneLink.Response.text(200, "Gekoppeld, maar Spotify geeft deze app (nog) geen toegang tot "
                        + "de wachtrij. Controleer in het Spotify-dashboard of jouw account onder User Management staat.");
            }
            return PhoneLink.Response.text(200, next.title != null
                    ? "Gekoppeld! Hierna: " + next.title + ". Dit staat nu ook op de tv."
                    : "Gekoppeld! Zodra er iets in de wachtrij staat, zie je het op de tv.");
        }
        if ("POST".equals(method) && "/spotify/unlink".equals(path)) {
            SpotifyApi.unlink(prefs);
            runOnUiThread(this::loadNext);
            return PhoneLink.Response.text(200, "Ontkoppeld. De tv vergeet je Spotify-login.");
        }
        if ("GET".equals(method) && "/hub".equals(path)) {
            return PhoneLink.Response.text(200, prefs.getString("hub", "") + "\n" + prefs.getString("screen_name", "")
                    + "\n" + hubStatus);
        }
        if ("POST".equals(method) && "/hub".equals(path)) {
            String[] v = (new String(body, StandardCharsets.UTF_8) + "\n").split("\n", -1);
            String addr = v[0].trim(), name = v[1].trim();
            if (!addr.isEmpty() && !addr.matches("(https?://)?[A-Za-z0-9.\\-]+(:\\d{1,5})?/?")) {
                return PhoneLink.Response.text(400, "Dat is geen adres. Bijvoorbeeld: 192.168.1.20:8770");
            }
            if (name.length() > 60) name = name.substring(0, 60);
            prefs.edit().putString("hub", addr).putString("screen_name", name).apply();
            runOnUiThread(() -> { if (hub != null) hub.kick(); });
            return PhoneLink.Response.text(200, addr.isEmpty()
                    ? "Opgeslagen. De tv zoekt de Hub zelf op het netwerk."
                    : "Opgeslagen. De tv verbindt met " + addr + ".");
        }
        if ("GET".equals(method) && "/auto".equals(path)) {
            return PhoneLink.Response.text(200, (prefs.getBoolean("auto_open", true) ? "on" : "off") + "\n"
                    + (android.provider.Settings.canDrawOverlays(this) ? "allowed" : "blocked"));
        }
        if ("POST".equals(method) && "/auto".equals(path)) {
            boolean on = "on".equals(new String(body, StandardCharsets.UTF_8).trim());
            prefs.edit().putBoolean("auto_open", on).apply();
            return PhoneLink.Response.text(200, on
                    ? "SpotiParty opent nu vanzelf zodra Spotify begint te spelen."
                    : "SpotiParty opent niet meer vanzelf.");
        }
        return null;
    }

    private static final String PHONE_PAGE =
            "<p>Zet de link van je Spotify Jam op de tv. Je vrienden scannen daarna de code op het scherm.</p>"
            + "<ol style='color:#b9bcc6;padding-left:20px'>"
            + "<li>Open Spotify op je telefoon en speel af op de tv.</li>"
            + "<li>Tik op het apparaat-icoon (of de drie puntjes) en kies <b>Start een Jam</b>.</li>"
            + "<li>Open de <b>Jam-instellingen</b> en zet <b>Gasten mogen afspelen bedienen</b> uit "
            + "(in het Engels: <i>Let guests control playback</i>; de naam kan per Spotify-versie iets "
            + "verschillen). Dan kunnen vrienden alleen nummers toevoegen "
            + "aan de wachtrij: niet overslaan, pauzeren of het volume veranderen.</li>"
            + "<li>Tik op <b>Uitnodigen</b> en <b>Link kopi&euml;ren</b>, en plak hem hieronder.</li></ol>"
            + "<label for=jam>Jam-link</label>"
            + "<input id=jam inputmode=url autocapitalize=off placeholder='https://spotify.link/...'>"
            + "<button id=save>Op de tv zetten</button>"
            + "<button id=clear style='background:#3a3e4a'>Jam-code weghalen</button><div id=msg></div>"
            + "<script>"
            + "const k=new URLSearchParams(location.search).get('k');const $=id=>document.getElementById(id);"
            + "fetch('/jam?k='+k).then(r=>r.text()).then(t=>{$('jam').value=t;});"
            + "async function send(v){$('msg').textContent='Bezig...';"
            + "try{const r=await fetch('/jam?k='+k,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:v});"
            + "$('msg').textContent=await r.text();}catch(e){$('msg').textContent='De tv is niet bereikbaar. Staat SpotiParty nog open?';}}"
            + "$('save').onclick=()=>send($('jam').value.trim());"
            + "$('clear').onclick=()=>{$('jam').value='';send('');};"
            + "</script>"
            + "<h1 style='margin-top:40px'>Vanzelf openen</h1>"
            + "<p>SpotiParty springt naar voren zodra Spotify op de tv begint te spelen (niet bij elk volgend nummer, "
            + "en niet opnieuw als je hem zelf sluit terwijl de muziek doorgaat).</p>"
            + "<label style='display:flex;gap:12px;align-items:center'><input id=auto type=checkbox "
            + "style='width:28px;height:28px'> Vanzelf openen als Spotify start</label>"
            + "<div id=automsg></div>"
            + "<script>"
            + "fetch('/auto?k='+k).then(r=>r.text()).then(t=>{const [a,p]=t.split('\\n');$('auto').checked=a==='on';"
            + "if(p!=='allowed')$('automsg').textContent='Nog nodig op de tv: Weergeven vóór andere apps toestaan voor SpotiParty.';});"
            + "$('auto').onchange=async()=>{try{const r=await fetch('/auto?k='+k,{method:'POST',body:$('auto').checked?'on':'off'});"
            + "$('automsg').textContent=await r.text();}catch(e){$('automsg').textContent='De tv is niet bereikbaar.';}};"
            + "</script>"
            + "<h1 style='margin-top:40px'>SpotiParty Hub</h1>"
            + "<p>Met de Hub stuur je meldingen, een pauze-aftelklok en de gasten-wifi naar al je "
            + "schermen. De tv vindt de Hub zelf; vul alleen een adres in als dat niet lukt.</p>"
            + "<div id=hubstate style='color:#1ed760'></div>"
            + "<label for=hub>Adres van de Hub (leeg: zelf zoeken)</label>"
            + "<input id=hub inputmode=url autocapitalize=off autocomplete=off placeholder='192.168.1.20:8770'>"
            + "<label for=sname>Naam van deze tv</label>"
            + "<input id=sname autocomplete=off maxlength=60 placeholder='Woonkamer'>"
            + "<button id=hubsave>Opslaan</button><div id=hubmsg></div>"
            + "<script>"
            + "fetch('/hub?k='+k).then(r=>r.text()).then(t=>{const [a,n,s]=t.split('\\n');$('hub').value=a||'';"
            + "$('sname').value=n||'';$('hubstate').textContent=s||'';});"
            + "$('hubsave').onclick=async()=>{$('hubmsg').textContent='Bezig...';try{const r=await fetch('/hub?k='+k,"
            + "{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:$('hub').value.trim()+'\\n'+$('sname').value.trim()});"
            + "$('hubmsg').textContent=await r.text();}catch(e){$('hubmsg').textContent='De tv is niet bereikbaar.';}};"
            + "</script>"
            + "<h1 style='margin-top:40px'>Volgende nummer tonen</h1>"
            + "<p>Spotify geeft de wachtrij niet aan de tv door. Koppel je Spotify-account (alleen lezen), dan "
            + "zet SpotiParty <b>Hierna: nummer</b> onder de artiest. Eenmalig:</p>"
            + "<ol style='color:#b9bcc6;padding-left:20px'>"
            + "<li>Ga naar <b>developer.spotify.com/dashboard</b>, log in en tik op <b>Create app</b>.</li>"
            + "<li>Naam en omschrijving mag je zelf kiezen. Zet bij <b>Redirect URIs</b> precies: "
            + "<code style='color:#fff'>" + SpotifyApi.REDIRECT + "</code> en vink <b>Web API</b> aan.</li>"
            + "<li>Kopieer de <b>Client ID</b> van je app en plak hem hieronder.</li></ol>"
            + "<div id=spstate style='color:#1ed760'></div>"
            + "<label for=client>Client ID</label>"
            + "<input id=client autocapitalize=off autocomplete=off placeholder='32 tekens'>"
            + "<button id=login style='background:#1ed760;color:#000'>Inloggen bij Spotify</button>"
            + "<a id=go class=pick target=_blank rel=noopener style='display:none;background:#1ed760;color:#000;"
            + "text-decoration:none'>Open de Spotify-login</a>"
            + "<p id=after style='display:none'>Na het inloggen probeert je telefoon <b>127.0.0.1</b> te openen en "
            + "zegt dat het niet lukt. Dat hoort zo. Kopieer dat hele adres uit de adresbalk en plak het hier:</p>"
            + "<input id=code style='display:none' autocapitalize=off autocomplete=off placeholder='http://127.0.0.1:8768/callback?code=...'>"
            + "<button id=finish style='display:none'>Koppelen</button>"
            + "<button id=unlink style='background:#3a3e4a'>Spotify ontkoppelen</button><div id=spmsg></div>"
            + "<script>"
            + "async function sp(path,v){const r=await fetch(path+'?k='+k,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:v||''});return [r.ok,await r.text()];}"
            + "fetch('/spotify?k='+k).then(r=>r.text()).then(t=>{const [s,c]=t.split('\\n');$('client').value=c||'';"
            + "$('spstate').textContent=s==='linked'?'Spotify is gekoppeld.':'';});"
            + "$('login').onclick=async()=>{$('spmsg').textContent='Bezig...';"
            + "try{const [ok,t]=await sp('/spotify/login',$('client').value.trim());"
            + "if(!ok){$('spmsg').textContent=t;return;}"
            + "$('go').href=t;$('go').style.display='block';$('after').style.display='block';"
            + "$('code').style.display='block';$('finish').style.display='block';"
            + "$('spmsg').textContent='Tik op Open de Spotify-login.';}"
            + "catch(e){$('spmsg').textContent='De tv is niet bereikbaar.';}};"
            + "$('finish').onclick=async()=>{$('spmsg').textContent='Koppelen...';"
            + "try{const [ok,t]=await sp('/spotify/code',$('code').value.trim());$('spmsg').textContent=t;"
            + "if(ok)$('spstate').textContent='Spotify is gekoppeld.';}catch(e){$('spmsg').textContent='De tv is niet bereikbaar.';}};"
            + "$('unlink').onclick=async()=>{try{const [ok,t]=await sp('/spotify/unlink');$('spmsg').textContent=t;"
            + "$('spstate').textContent='';}catch(e){$('spmsg').textContent='De tv is niet bereikbaar.';}};"
            + "</script>";

    /** What the Hub wants on this screen (null: no hub). */
    private void onHub(HubLink.State s, String status) {
        hubState = s;
        hubStatus = status == null ? "" : status;
        float dp = getResources().getDisplayMetrics().density;

        // The Jam link from the dashboard replaces the one set from the phone, on every screen at once.
        // Kept when the hub can't be reached for a moment: the TV must not fall back to an old link from the phone.
        String jam;
        if (s == null) {
            jam = prefs.getString("hub_jam", "");
        } else {
            jam = isSpotifyLink(s.jam) ? s.jam : "";
            if (!prefs.getBoolean("hub_seen", false) || !jam.equals(prefs.getString("hub_jam", ""))) {
                prefs.edit().putBoolean("hub_seen", true).putString("hub_jam", jam).apply();
            }
        }
        boolean linkChanged = (s == null) != (hubShown == null);
        hubShown = s;
        if (!jam.equals(hubJam) || linkChanged) {
            hubJam = jam;
            showQr();
        }

        // Play, pause, skip, volume: from the dashboard's buttons or the break.
        if (s != null) {
            for (String[] c : s.cmds) {
                if (!doneCmds.add(c[0])) continue;
                String why = runMedia(c[1]);
                if (hub != null) hub.setResult(c[0] + (why == null ? ":ok" : ":err:" + why));
            }
            if (doneCmds.size() > 200) doneCmds.clear();
        }

        if (s == null || s.noticeId == null) {
            notice.setVisibility(View.GONE);
            shownNotice = "";
        } else if (!s.noticeId.equals(shownNotice)) {
            shownNotice = s.noticeId;
            GradientDrawable bg = new GradientDrawable();
            bg.setCornerRadius(40 * dp);
            int text = 0xFFFFFFFF, kind = 0xFF1ED760, bar = 0xFF1ED760;
            String icon = "📢", word = getString(R.string.notice_info);
            if ("party".equals(s.noticeStyle)) {
                bg.setOrientation(GradientDrawable.Orientation.TL_BR);
                bg.setColors(new int[]{0xFF1ED760, 0xFFFF4FD8, 0xFFFFB547});
                text = kind = bar = 0xFF000000;
                icon = "🎉";
                word = getString(R.string.notice_party);
            } else if ("alert".equals(s.noticeStyle)) {
                bg.setColor(0xF28E1D17);
                bg.setStroke(Math.round(4 * dp), 0xFFFFB4AB);
                kind = bar = 0xFFFFDAD6;
                icon = "⚠️";
                word = getString(R.string.notice_alert);
            } else {
                bg.setColor(0xF015161D);
                bg.setStroke(Math.round(4 * dp), 0xFF1ED760);
            }
            noticeCard.setBackground(bg);
            noticeIcon.setText(icon);
            noticeKind.setText(word.toUpperCase(Locale.ROOT));
            noticeKind.setTextColor(kind);
            noticeText.setTextColor(text);
            noticeText.setShadowLayer(text == 0xFF000000 ? 0 : 8 * dp, 0, 2, 0x99000000);
            noticeText.setTextSize(TypedValue.COMPLEX_UNIT_SP, s.noticeText.length() > 70 ? 40 : 56);
            noticeText.setText(s.noticeText);
            noticeBar.setProgressTintList(android.content.res.ColorStateList.valueOf(bar));
            noticeBar.setProgressBackgroundTintList(android.content.res.ColorStateList.valueOf(0x33FFFFFF));
            notice.setVisibility(View.VISIBLE);
            notice.setAlpha(0f);
            noticeCard.setScaleX(0.85f);
            noticeCard.setScaleY(0.85f);
            notice.animate().alpha(1f).setDuration(300).start();
            noticeCard.animate().scaleX(1f).scaleY(1f).setDuration(450)
                    .setInterpolator(new android.view.animation.OvershootInterpolator(1.4f)).start();
        }

        String wifi = s == null || s.wifiQr == null || s.wifiQr.isEmpty() ? "" : s.wifiQr;
        if (!wifi.equals(shownWifi)) {
            shownWifi = wifi;
            boolean on = !wifi.isEmpty() && wifiQr.setText(wifi);
            if (on) {
                wifiText.setText(getString(R.string.wifi_text, s.wifiSsid)
                        + (s.wifiPassword.isEmpty() ? "" : "\n" + s.wifiPassword));
            }
            wifiCard.setVisibility(on ? View.VISIBLE : View.GONE);
        }

        identView.setVisibility(s != null && s.ident ? View.VISIBLE : View.GONE);
        if (s != null && s.ident) identView.setText(s.name);
        showBreak();
    }

    private void showBreak() {
        HubLink.State s = hubState;
        // The notice's time running out (no bar for "until I remove it").
        boolean timed = s != null && s.noticeId != null && s.noticeUntil > 0 && s.noticeSecs > 0;
        noticeBar.setVisibility(timed ? View.VISIBLE : View.GONE);
        if (timed) {
            noticeBar.setProgress((int) Math.max(0, Math.min(1000, (s.noticeUntil - s.hubNow()) / Math.max(1, s.noticeSecs))));
        }
        if (s == null || s.breakUntil == 0) {
            if (pauseView.getVisibility() != View.GONE) pauseView.setVisibility(View.GONE);
            return;
        }
        long left = s.breakUntil - s.hubNow();
        if (pauseView.getVisibility() != View.VISIBLE) pauseView.setVisibility(View.VISIBLE);
        if (left > 0) {
            long secs = (left + 999) / 1000;
            pauseTitle.setText(s.breakTitle);
            pauseClock.setText(secs >= 3600
                    ? String.format(Locale.ROOT, "%d:%02d:%02d", secs / 3600, secs / 60 % 60, secs % 60)
                    : String.format(Locale.ROOT, "%d:%02d", secs / 60, secs % 60));
            pauseSub.setText(R.string.break_sub);
            pauseBar.setProgress((int) Math.max(0, Math.min(1000, left * 1000 / Math.max(1, (long) (s.breakMinutes * 60000)))));
        } else {
            pauseTitle.setText(R.string.break_done);
            pauseClock.setText("0:00");
            pauseSub.setText("");
            pauseBar.setProgress(0);
        }
    }

    /** Only a Spotify address goes on the screen, so the code cannot send friends anywhere else. */
    static boolean isSpotifyLink(String s) {
        try {
            Uri u = Uri.parse(s);
            String host = u.getHost() == null ? "" : u.getHost().toLowerCase(Locale.ROOT);
            return "https".equals(u.getScheme()) && s.length() <= 300
                    && (host.equals("spotify.link") || host.endsWith(".spotify.link") || host.equals("open.spotify.com")
                    || host.endsWith(".spotify.com") || host.equals("spotify.app.link"));
        } catch (Exception e) {
            return false;
        }
    }
}
