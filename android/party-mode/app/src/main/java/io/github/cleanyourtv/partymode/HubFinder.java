package io.github.cleanyourtv.partymode;

import android.content.SharedPreferences;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Finding the SpotiParty Hub: the address typed in, or a UDP broadcast ("SPOTIPARTY_HUB?" to port 8771) that the
 * Hub answers with "SPOTIPARTY_HUB <port> <name>". Network calls: never on the main thread.
 */
final class HubFinder {
    static final int DISCOVERY_PORT = 8771;

    private HubFinder() {}

    /** "http://host:port" of a Hub that answers, or null. */
    static String find(SharedPreferences prefs) {
        String typed = normalize(prefs.getString("hub", ""));
        if (typed != null && ping(typed)) return typed;
        String found = discover();
        if (found != null) return found;
        String last = normalize(prefs.getString("hub_url", ""));
        return last != null && ping(last) ? last : null;
    }

    /** "192.168.1.20", "192.168.1.20:8770" or "http://..." to "http://host:port"; null when empty or odd. */
    static String normalize(String s) {
        if (s == null) return null;
        s = s.trim().replaceAll("/+$", "");
        if (s.isEmpty()) return null;
        if (!s.matches("(?i)https?://.*")) s = "http://" + s;
        try {
            URL u = new URL(s);
            if (u.getHost().isEmpty()) return null;
            int port = u.getPort() > 0 ? u.getPort() : 8770;
            return u.getProtocol().toLowerCase() + "://" + u.getHost() + ":" + port;
        } catch (Exception e) {
            return null;
        }
    }

    /** True when a Hub answers /api/ping at this address. */
    static boolean ping(String base) {
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(base + "/api/ping").openConnection();
            c.setConnectTimeout(2500);
            c.setReadTimeout(2500);
            return c.getResponseCode() == 200;
        } catch (Exception e) {
            return false;
        } finally {
            if (c != null) c.disconnect();
        }
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
            return "http://" + reply.getAddress().getHostAddress() + ":" + port;
        } catch (Exception e) {
            return null;
        }
    }
}
