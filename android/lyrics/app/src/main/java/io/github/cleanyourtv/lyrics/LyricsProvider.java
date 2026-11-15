package io.github.cleanyourtv.lyrics;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Lyrics for the launcher's Now playing panel, guarded by a signature permission.
 *
 *   query(content://io.github.cleanyourtv.lyrics.widget/lyrics, null, null, {artist, title, album, seconds}, null)
 *
 * gives rows of (time_ms, line), sorted; time_ms is -1 for every row when only unsynced lyrics exist, and no rows
 * when there are none. Lyrics come from lrclib.net (free, no account) and are kept for 30 days, a miss for a day.
 */
public class LyricsProvider extends ContentProvider {
    private static final String API = "https://lrclib.net/api/";
    private static final String AGENT = "CleanYourTV-Lyrics/1.0 (+https://github.com/Gathin23/cleanyourtv)";
    private static final long KEEP_MS = 30L * 24 * 3600 * 1000;
    private static final long MISS_MS = 24L * 3600 * 1000;
    private static final Pattern STAMP = Pattern.compile("\\[(\\d+):(\\d+(?:\\.\\d+)?)\\]");

    @Override
    public Cursor query(Uri uri, String[] projection, String selection, String[] args, String sort) {
        MatrixCursor cursor = new MatrixCursor(new String[]{"time_ms", "line"});
        if (!"lyrics".equals(uri.getLastPathSegment()) || args == null || args.length < 2) return cursor;
        String artist = args[0] == null ? "" : args[0].trim();
        String title = args[1] == null ? "" : args[1].trim();
        String album = args.length > 2 && args[2] != null ? args[2].trim() : "";
        int seconds = 0;
        try {
            if (args.length > 3 && args[3] != null) seconds = Integer.parseInt(args[3]);
        } catch (NumberFormatException ignored) {
            // no length: the search still works
        }
        if (artist.isEmpty() || title.isEmpty()) return cursor;
        String lrc = lyrics(artist, title, album, seconds);
        for (Object[] row : parse(lrc)) cursor.addRow(row);
        return cursor;
    }

    /** "S" + synced LRC, "P" + plain text, or "" for none. Cached on disk. */
    private synchronized String lyrics(String artist, String title, String album, int seconds) {
        File cache = new File(getContext().getCacheDir(), "l_" + hash(artist + "\n" + title) + ".txt");
        long age = System.currentTimeMillis() - cache.lastModified();
        if (cache.isFile()) {
            String cached = read(cache);
            if (cached != null && age < (cached.isEmpty() ? MISS_MS : KEEP_MS)) return cached;
        }
        String found;
        try {
            found = fetch(artist, title, album, seconds);
        } catch (IOException e) {
            return "";   // offline: try again next time, nothing cached
        }
        write(cache, found);
        return found;
    }

    private static String fetch(String artist, String title, String album, int seconds) throws IOException {
        // Spotify lists every artist ("Mqx, Tevvez"); lrclib usually knows the first.
        String first = artist.split(",| & | feat\\.? | ft\\.? ", 2)[0].trim();
        String exact = API + "get?artist_name=" + enc(artist) + "&track_name=" + enc(title)
                + (album.isEmpty() ? "" : "&album_name=" + enc(album))
                + (seconds > 0 ? "&duration=" + seconds : "");
        String body = get(exact);
        if (body != null) {
            try {
                String result = pick(new JSONObject(body));
                if (result != null) return result;
            } catch (Exception ignored) {
                // an answer it cannot read: try the search
            }
        }
        String search = API + "search?track_name=" + enc(title) + "&artist_name=" + enc(first);
        body = get(search);
        if (body != null) {
            try {
                JSONArray results = new JSONArray(body);
                String plain = null;
                for (int i = 0; i < results.length(); i++) {
                    JSONObject item = results.getJSONObject(i);
                    int length = item.optInt("duration", 0);
                    if (seconds > 0 && length > 0 && Math.abs(length - seconds) > 4) continue;
                    String result = pick(item);
                    if (result == null) continue;
                    if (result.startsWith("S")) return result;
                    if (plain == null) plain = result;
                }
                if (plain != null) return plain;
            } catch (Exception ignored) {
                // an answer it cannot read: no lyrics
            }
        }
        return "";
    }

    private static String pick(JSONObject item) {
        String synced = item.optString("syncedLyrics", "");
        if (!synced.isEmpty() && !"null".equals(synced)) return "S" + synced;
        String plain = item.optString("plainLyrics", "");
        if (!plain.isEmpty() && !"null".equals(plain)) return "P" + plain;
        return null;
    }

    /** The body on 200, null on 404; other failures throw, so they are not cached as "no lyrics". */
    private static String get(String url) throws IOException {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(6000);
        c.setReadTimeout(10000);
        c.setRequestProperty("User-Agent", AGENT);
        try {
            int code = c.getResponseCode();
            if (code == 404) return null;
            if (code != 200) throw new IOException("HTTP " + code);
            try (InputStream in = c.getInputStream()) {
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                byte[] buffer = new byte[8192];
                int n;
                while ((n = in.read(buffer)) > 0) {
                    out.write(buffer, 0, n);
                    if (out.size() > 2 * 1024 * 1024) throw new IOException("too large");
                }
                return out.toString("UTF-8");
            }
        } finally {
            c.disconnect();
        }
    }

    static List<Object[]> parse(String stored) {
        List<Object[]> rows = new ArrayList<>();
        if (stored == null || stored.length() < 2) return rows;
        String text = stored.substring(1);
        if (stored.charAt(0) == 'P') {
            for (String line : text.split("\n")) {
                if (!line.trim().isEmpty()) rows.add(new Object[]{-1L, line.trim()});
            }
            return rows;
        }
        for (String line : text.split("\n")) {
            Matcher m = STAMP.matcher(line);
            List<Long> times = new ArrayList<>();
            int end = 0;
            while (m.find() && m.start() == end) {
                times.add(Math.round((Integer.parseInt(m.group(1)) * 60 + Double.parseDouble(m.group(2))) * 1000));
                end = m.end();
            }
            String words = line.substring(end).trim();
            for (long t : times) rows.add(new Object[]{t, words});
        }
        Collections.sort(rows, (a, b) -> Long.compare((Long) a[0], (Long) b[0]));
        return rows;
    }

    private static String enc(String s) {
        try {
            return URLEncoder.encode(s, "UTF-8");
        } catch (Exception e) {
            return "";
        }
    }

    private static String hash(String s) {
        try {
            byte[] d = MessageDigest.getInstance("SHA-1").digest(s.toLowerCase(Locale.ROOT).getBytes(StandardCharsets.UTF_8));
            StringBuilder b = new StringBuilder();
            for (int i = 0; i < 10; i++) b.append(String.format(Locale.ROOT, "%02x", d[i]));
            return b.toString();
        } catch (Exception e) {
            return Integer.toHexString(s.hashCode());
        }
    }

    private static String read(File f) {
        try (InputStream in = new FileInputStream(f)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int n;
            while ((n = in.read(buffer)) > 0) out.write(buffer, 0, n);
            return out.toString("UTF-8");
        } catch (IOException e) {
            return null;
        }
    }

    private static void write(File f, String s) {
        try (FileOutputStream out = new FileOutputStream(f)) {
            out.write(s.getBytes(StandardCharsets.UTF_8));
        } catch (IOException ignored) {
            // not cached: asked again next time
        }
    }

    @Override public boolean onCreate() { return true; }
    @Override public String getType(Uri uri) { return null; }
    @Override public Uri insert(Uri uri, ContentValues values) { return null; }
    @Override public int delete(Uri uri, String selection, String[] args) { return 0; }
    @Override public int update(Uri uri, ContentValues values, String selection, String[] args) { return 0; }
}
