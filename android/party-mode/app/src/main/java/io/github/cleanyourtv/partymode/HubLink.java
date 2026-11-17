package io.github.cleanyourtv.partymode;

import android.content.SharedPreferences;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;

/**
 * The TV as a screen of the SpotiParty Hub: notices, the break countdown, the guest Wi-Fi QR and
 * "which screen is this?". Only while the screen is open (start in onStart, stop in onStop).
 *
 * The hub is found with a UDP broadcast ("SPOTIPARTY_HUB?" to port 8771), or set by hand from the phone page.
 * Then the TV asks GET http://hub:port/api/screen every 2 s; the hub never connects to the TV.
 */
final class HubLink {
    static final int DISCOVERY_PORT = 8771;
    private static final int POLL_MS = 2000;

    interface Listener {
        /** On the main thread; null when there is no hub. */
        void onHub(State state, String status);
    }

    static final class State {
        long offset;            // hub clock minus the TV's clock, ms
        String name = "";
        boolean pro;            // notices, break, Wi-Fi and "identify" (the hub always sends true)
        String jam = "";        // the Jam link set in the dashboard, for every screen; "" = none
        final java.util.List<String[]> cmds = new java.util.ArrayList<>();   // {id, cmd} to run once
        String noticeId, noticeText, noticeStyle;
        long noticeUntil;       // hub clock, ms; 0 = until removed
        int noticeSecs;
        String breakTitle;
        double breakMinutes;
        long breakUntil;        // hub clock, ms; 0 = no break
        String wifiSsid, wifiPassword, wifiQr;
        boolean ident;

        long hubNow() { return System.currentTimeMillis() + offset; }
    }

    private final SharedPreferences prefs;
    private final Listener listener;
    private final Handler main = new Handler(Looper.getMainLooper());
    private volatile boolean running;
    private volatile String song = "";
    private volatile boolean canControl, playing;
    private volatile String result = "";
    private Thread thread;
    private volatile String found;   // "host:port" from discovery

    HubLink(SharedPreferences prefs, Listener listener) {
        this.prefs = prefs;
        this.listener = listener;
    }

    void setSong(String s) { song = s == null ? "" : s; }

    /** What the hub shows about this TV: can it control the music, is it playing. */
    void setPlayer(boolean canControl, boolean playing) {
        this.canControl = canControl;
        this.playing = playing;
    }

    /** How the last command went ("id:ok" or "id:err:why"), sent with the next poll. */
    void setResult(String r) { result = r == null ? "" : r; }

    String screenId() {
        String id = prefs.getString("screen_id", "");
        if (!id.matches("[A-Za-z0-9_-]{4,40}")) {
            byte[] b = new byte[6];
            new SecureRandom().nextBytes(b);
            StringBuilder sb = new StringBuilder("t-");
            for (byte x : b) sb.append(String.format("%02x", x));
            id = sb.toString();
            prefs.edit().putString("screen_id", id).apply();
        }
        return id;
    }

    String screenName() {
        String n = prefs.getString("screen_name", "");
        return n.isEmpty() ? (Build.MODEL == null || Build.MODEL.isEmpty() ? "Android TV" : Build.MODEL) : n;
    }

    void start() {
        if (running) return;
        running = true;
        thread = new Thread(this::loop, "hub-link");
        thread.setDaemon(true);
        thread.start();
    }

    void stop() {
        running = false;
        if (thread != null) thread.interrupt();
        thread = null;
    }

    /** Wake the loop now (after the address or name changed on the phone page). */
    void kick() {
        found = null;
        if (thread != null) thread.interrupt();
    }

    private void loop() {
        int fails = 0;
        long nextDiscovery = 0;
        while (running) {
            String manual = prefs.getString("hub", "").trim();
            String target = !manual.isEmpty() ? manual : found;
            if (target == null && System.currentTimeMillis() >= nextDiscovery) {
                target = found = discover();
                if (target == null) {
                    nextDiscovery = System.currentTimeMillis() + 10_000;
                    post(null, "Geen SpotiParty Hub gevonden op het netwerk.");
                }
            }
            if (target != null) {
                try {
                    State s = poll(target);
                    fails = 0;
                    post(s, "Verbonden met de Hub als “" + s.name + "”.");
                } catch (Exception e) {
                    if (++fails >= 3) {
                        fails = 0;
                        found = null;
                        nextDiscovery = 0;
                        post(null, "De Hub op " + target + " antwoordt niet.");
                    }
                }
            }
            try {
                Thread.sleep(POLL_MS);
            } catch (InterruptedException ignored) {
                // kick() or stop()
            }
        }
    }

    private void post(State s, String status) {
        if (!running) return;
        main.post(() -> { if (running) listener.onHub(s, status); });
    }

    private static String discover() {
        try (DatagramSocket socket = new DatagramSocket()) {
            socket.setBroadcast(true);
            socket.setSoTimeout(1500);
            byte[] ask = "SPOTIPARTY_HUB?".getBytes(StandardCharsets.US_ASCII);
            socket.send(new DatagramPacket(ask, ask.length, InetAddress.getByName("255.255.255.255"), DISCOVERY_PORT));
            byte[] buf = new byte[256];
            DatagramPacket reply = new DatagramPacket(buf, buf.length);
            socket.receive(reply);
            String[] parts = new String(buf, 0, reply.getLength(), StandardCharsets.UTF_8).split(" ", 3);
            if (parts.length < 2 || !"SPOTIPARTY_HUB".equals(parts[0])) return null;
            int port = Integer.parseInt(parts[1].trim());
            return reply.getAddress().getHostAddress() + ":" + port;
        } catch (Exception e) {
            return null;
        }
    }

    private State poll(String target) throws Exception {
        String base = target.startsWith("http") ? target : "http://" + target;
        if (!base.substring(base.indexOf("//") + 2).contains(":")) base += ":8770";
        String url = base.replaceAll("/+$", "") + "/api/screen?id=" + enc(screenId()) + "&name=" + enc(screenName())
                + "&kind=tv&v=tv-2&song=" + enc(song) + "&ctl=" + (canControl ? 1 : 0) + "&playing=" + (playing ? 1 : 0)
                + "&res=" + enc(result);
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(3000);
        c.setReadTimeout(3000);
        c.setUseCaches(false);
        try {
            if (c.getResponseCode() != 200) throw new java.io.IOException("HTTP " + c.getResponseCode());
            long sent = System.currentTimeMillis();
            JSONObject o = new JSONObject(read(c.getInputStream()));
            State s = new State();
            s.offset = o.optLong("now", sent) - sent;
            s.name = o.optString("name");
            s.pro = o.optBoolean("pro");
            s.jam = o.optString("jam", "");
            org.json.JSONArray cmds = o.optJSONArray("cmds");
            for (int i = 0; cmds != null && i < cmds.length(); i++) {
                JSONObject x = cmds.optJSONObject(i);
                if (x != null) s.cmds.add(new String[]{x.optString("id"), x.optString("cmd")});
            }
            JSONObject n = o.optJSONObject("notice");
            if (n != null) {
                s.noticeId = n.optString("id");
                s.noticeText = n.optString("text");
                s.noticeStyle = n.optString("style", "info");
                s.noticeUntil = n.optLong("until");
                s.noticeSecs = n.optInt("secs");
            }
            JSONObject b = o.optJSONObject("brk");
            if (b != null) {
                s.breakTitle = b.optString("title", "Pauze");
                s.breakMinutes = b.optDouble("minutes", 1);
                s.breakUntil = b.optLong("until");
            }
            JSONObject w = o.optJSONObject("wifi");
            if (w != null) {
                s.wifiSsid = w.optString("ssid");
                s.wifiPassword = w.optString("password");
                s.wifiQr = w.optString("qr");
            }
            s.ident = o.optBoolean("ident");
            return s;
        } finally {
            c.disconnect();
        }
    }

    private static String enc(String s) throws Exception {
        return URLEncoder.encode(s == null ? "" : s, "UTF-8");
    }

    private static String read(InputStream in) throws Exception {
        try (InputStream is = in) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[4096];
            int n;
            while ((n = is.read(buf)) > 0 && out.size() < 64 * 1024) out.write(buf, 0, n);
            return out.toString("UTF-8");
        }
    }
}
