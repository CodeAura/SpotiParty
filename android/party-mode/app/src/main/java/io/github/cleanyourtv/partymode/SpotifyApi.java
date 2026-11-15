package io.github.cleanyourtv.partymode;

import android.content.SharedPreferences;
import android.net.Uri;
import android.util.Base64;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;

/**
 * The host's Spotify queue, read with Spotify's Web API (authorization code with PKCE, no client secret).
 * Only the read scopes are asked for: SpotiParty can see what plays and what comes next, and control nothing.
 * Spotify only accepts http:// redirect addresses on the loopback, so after logging in on the phone the host
 * copies the 127.0.0.1 address the browser could not open and pastes it on the phone page.
 */
final class SpotifyApi {
    static final String REDIRECT = "http://127.0.0.1:8768/callback";
    /** logcat tag; what Spotify answered, never a token or code. */
    static final String TAG = "PartyMode";
    private static final String SCOPES = "user-read-playback-state user-read-currently-playing";
    private static final String ACCOUNTS = "https://accounts.spotify.com/";

    /** The next track in the queue, or a reason there is none. */
    static final class Next {
        final String title;
        final String artist;
        final String error;

        Next(String title, String artist, String error) {
            this.title = title;
            this.artist = artist;
            this.error = error;
        }
    }

    static final class ApiError extends IOException {
        final int code;

        ApiError(int code, String body) {
            super("HTTP " + code + (body == null ? "" : ": " + body));
            this.code = code;
        }
    }

    private SpotifyApi() {}

    static boolean linked(SharedPreferences prefs) {
        return !prefs.getString("sp_refresh", "").isEmpty() && !prefs.getString("sp_client", "").isEmpty();
    }

    /** A fresh login address; the verifier and state wait in prefs for the pasted answer. */
    static String authorizeUrl(SharedPreferences prefs, String clientId) {
        String verifier = random(64);
        String state = random(16);
        prefs.edit().putString("sp_client", clientId).putString("sp_verifier", verifier)
                .putString("sp_state", state).apply();
        return ACCOUNTS + "authorize?response_type=code"
                + "&client_id=" + enc(clientId)
                + "&scope=" + enc(SCOPES)
                + "&redirect_uri=" + enc(REDIRECT)
                + "&code_challenge_method=S256"
                + "&code_challenge=" + challenge(verifier)
                + "&state=" + state;
    }

    /** Trades the pasted 127.0.0.1 address (or the code alone) for tokens. Returns null or what went wrong. */
    static String finishLogin(SharedPreferences prefs, String pasted) throws IOException {
        String code = pasted.trim();
        int question = code.indexOf('?');
        if (question >= 0 || code.contains("code=")) {
            // Read the query by hand: a phone often copies the address without "http://"
            // ("127.0.0.1:8768/callback?code=..."), which Uri.parse takes for an opaque URI.
            java.util.Map<String, String> query = new java.util.HashMap<>();
            String q = question >= 0 ? code.substring(question + 1) : code;
            int hash = q.indexOf('#');
            if (hash >= 0) q = q.substring(0, hash);
            for (String pair : q.split("&")) {
                int eq = pair.indexOf('=');
                if (eq <= 0) continue;
                try {
                    query.put(pair.substring(0, eq), java.net.URLDecoder.decode(pair.substring(eq + 1), "UTF-8"));
                } catch (Exception ignored) {
                    // a malformed part is skipped
                }
            }
            if (query.get("error") != null) return "Spotify zei: " + query.get("error");
            String state = query.get("state");
            if (state != null && !state.equals(prefs.getString("sp_state", ""))) {
                return "Dit adres hoort bij een oudere login. Tik nog eens op Inloggen bij Spotify.";
            }
            code = query.get("code");
        }
        if (code == null || code.isEmpty()) return "Er staat geen code in dit adres.";
        String verifier = prefs.getString("sp_verifier", "");
        if (verifier.isEmpty()) return "Tik eerst op Inloggen bij Spotify.";
        JSONObject token = post(ACCOUNTS + "api/token", "grant_type=authorization_code"
                + "&code=" + enc(code)
                + "&redirect_uri=" + enc(REDIRECT)
                + "&client_id=" + enc(prefs.getString("sp_client", ""))
                + "&code_verifier=" + enc(verifier));
        save(prefs, token);
        prefs.edit().remove("sp_verifier").remove("sp_state").apply();
        return null;
    }

    static void unlink(SharedPreferences prefs) {
        prefs.edit().remove("sp_access").remove("sp_refresh").remove("sp_expires")
                .remove("sp_verifier").remove("sp_state").apply();
    }

    private static void save(SharedPreferences prefs, JSONObject token) {
        SharedPreferences.Editor e = prefs.edit()
                .putString("sp_access", token.optString("access_token"))
                .putLong("sp_expires", System.currentTimeMillis() + token.optLong("expires_in", 3600) * 1000 - 60_000);
        String refresh = token.optString("refresh_token", "");
        if (!refresh.isEmpty()) e.putString("sp_refresh", refresh);
        e.apply();
    }

    private static String access(SharedPreferences prefs, boolean force) throws IOException {
        String access = prefs.getString("sp_access", "");
        if (!force && !access.isEmpty() && System.currentTimeMillis() < prefs.getLong("sp_expires", 0)) return access;
        JSONObject token = post(ACCOUNTS + "api/token", "grant_type=refresh_token"
                + "&refresh_token=" + enc(prefs.getString("sp_refresh", ""))
                + "&client_id=" + enc(prefs.getString("sp_client", "")));
        save(prefs, token);
        return prefs.getString("sp_access", "");
    }

    /** The first track after the one playing, from the host's queue (a Jam's queue included). */
    static Next next(SharedPreferences prefs) {
        String token;
        try {
            token = access(prefs, false);
        } catch (ApiError e) {
            // The token endpoint refused the saved login (invalid_grant): it has to be done again.
            Log.w(TAG, "token refresh refused: " + e.getMessage());
            if (e.code == 400) unlink(prefs);
            return new Next(null, null, "login");
        } catch (Exception e) {
            Log.w(TAG, "token refresh failed: " + e);
            return new Next(null, null, "offline");
        }
        try {
            JSONObject queue;
            try {
                queue = get("https://api.spotify.com/v1/me/player/queue", token);
            } catch (ApiError e) {
                if (e.code != 401) throw e;
                queue = get("https://api.spotify.com/v1/me/player/queue", access(prefs, true));
            }
            JSONArray items = queue == null ? null : queue.optJSONArray("queue");
            boolean playing = queue != null && queue.optJSONObject("currently_playing") != null;
            Log.i(TAG, "queue: " + (queue == null ? "no content (204)" : (items == null ? 0 : items.length())
                    + " items, currently_playing=" + playing));
            if (queue == null || !playing) return new Next(null, null, "idle");
            if (items == null || items.length() == 0) return new Next(null, null, "empty");
            JSONObject item = items.getJSONObject(0);
            String artist = "";
            JSONArray artists = item.optJSONArray("artists");
            if (artists != null) {
                StringBuilder b = new StringBuilder();
                for (int i = 0; i < artists.length() && i < 3; i++) {
                    if (b.length() > 0) b.append(", ");
                    b.append(artists.getJSONObject(i).optString("name"));
                }
                artist = b.toString();
            } else if (item.optJSONObject("show") != null) {
                artist = item.optJSONObject("show").optString("name");   // a podcast episode
            }
            return new Next(item.optString("name"), artist, null);
        } catch (ApiError e) {
            Log.w(TAG, "queue refused: " + e.getMessage());
            if (e.code == 401) return new Next(null, null, "login");
            if (e.code == 403) return new Next(null, null, "forbidden");
            if (e.code == 429) return new Next(null, null, "busy");
            return new Next(null, null, "error " + e.code);
        } catch (Exception e) {
            Log.w(TAG, "queue failed: " + e);
            return new Next(null, null, "offline");
        }
    }

    private static JSONObject get(String url, String access) throws IOException {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(5000);
        c.setReadTimeout(8000);
        c.setRequestProperty("Authorization", "Bearer " + access);
        return answer(c);
    }

    private static JSONObject post(String url, String form) throws IOException {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(5000);
        c.setReadTimeout(8000);
        c.setRequestMethod("POST");
        c.setDoOutput(true);
        c.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        try (OutputStream out = c.getOutputStream()) {
            out.write(form.getBytes(StandardCharsets.UTF_8));
        }
        return answer(c);
    }

    private static JSONObject answer(HttpURLConnection c) throws IOException {
        try {
            int code = c.getResponseCode();
            if (code == 204) return null;
            InputStream stream = code >= 400 ? c.getErrorStream() : c.getInputStream();
            String body = "";
            if (stream != null) {
                try (InputStream in = stream) {
                    ByteArrayOutputStream out = new ByteArrayOutputStream();
                    byte[] buffer = new byte[8192];
                    int n;
                    while ((n = in.read(buffer)) > 0) {
                        out.write(buffer, 0, n);
                        if (out.size() > 4 * 1024 * 1024) throw new IOException("too large");
                    }
                    body = out.toString("UTF-8");
                }
            }
            if (code >= 400) throw new ApiError(code, body.length() > 200 ? body.substring(0, 200) : body);
            return body.isEmpty() ? null : new JSONObject(body);
        } catch (org.json.JSONException e) {
            throw new IOException("unreadable answer");
        } finally {
            c.disconnect();
        }
    }

    private static String random(int length) {
        String alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        SecureRandom r = new SecureRandom();
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < length; i++) b.append(alphabet.charAt(r.nextInt(alphabet.length())));
        return b.toString();
    }

    private static String challenge(String verifier) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(verifier.getBytes(StandardCharsets.US_ASCII));
            return Base64.encodeToString(digest, Base64.URL_SAFE | Base64.NO_PADDING | Base64.NO_WRAP);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    private static String enc(String s) {
        try {
            return URLEncoder.encode(s, "UTF-8");
        } catch (Exception e) {
            return "";
        }
    }
}
