package io.github.cleanyourtv.partymode;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.LinkAddress;
import android.net.LinkProperties;
import android.net.Network;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Inet4Address;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/**
 * A tiny web server for the phone, on the home network only, and only while the app's screen is open
 * (start in onStart, stop in onStop). Every request must carry the session key from the QR code
 * ("?k=..."); a new key is drawn each time the screen opens, so an old link stops working.
 */
final class PhoneLink {
    interface Handler {
        /** Runs on the server thread. path has no query; body is empty for GET. */
        Response handle(String method, String path, Map<String, String> query, byte[] body) throws Exception;
    }

    static final class Response {
        final int code;
        final String type;
        final byte[] body;

        Response(int code, String type, byte[] body) {
            this.code = code;
            this.type = type;
            this.body = body;
        }

        static Response text(int code, String text) {
            return new Response(code, "text/plain; charset=utf-8", text.getBytes(StandardCharsets.UTF_8));
        }

        static Response html(String html) {
            return new Response(200, "text/html; charset=utf-8", html.getBytes(StandardCharsets.UTF_8));
        }
    }

    private static final int MAX_HEADER = 16 * 1024;
    private static final int MAX_BODY = 16 * 1024 * 1024;

    final int port;
    final String key;
    private final Handler handler;
    private volatile ServerSocket server;

    PhoneLink(int port, Handler handler) {
        this.port = port;
        this.handler = handler;
        SecureRandom random = new SecureRandom();
        StringBuilder k = new StringBuilder();
        String alphabet = "abcdefghjkmnpqrstuvwxyz23456789";
        for (int i = 0; i < 10; i++) k.append(alphabet.charAt(random.nextInt(alphabet.length())));
        key = k.toString();
    }

    void start() {
        Thread thread = new Thread(this::serve, "phone-link");
        thread.setDaemon(true);
        thread.start();
    }

    void stop() {
        ServerSocket s = server;
        server = null;
        if (s != null) {
            try {
                s.close();
            } catch (IOException ignored) {
                // closing anyway
            }
        }
    }

    private void serve() {
        try (ServerSocket s = new ServerSocket()) {
            s.setReuseAddress(true);
            s.bind(new InetSocketAddress(port));
            server = s;
            while (server == s) {
                try (Socket socket = s.accept()) {
                    socket.setSoTimeout(20_000);
                    answer(socket);
                } catch (IOException ignored) {
                    // one bad request or the socket closing in stop()
                }
            }
        } catch (IOException ignored) {
            // port busy or stopped
        }
    }

    private void answer(Socket socket) throws IOException {
        InputStream in = new BufferedInputStream(socket.getInputStream());
        OutputStream out = socket.getOutputStream();
        String head = readHead(in);
        if (head == null) return;
        String[] lines = head.split("\r\n");
        String[] request = lines[0].split(" ");
        if (request.length < 2) return;
        String method = request[0];
        String target = request[1];
        int contentLength = 0;
        for (int i = 1; i < lines.length; i++) {
            int colon = lines[i].indexOf(':');
            if (colon > 0 && lines[i].substring(0, colon).trim().equalsIgnoreCase("content-length")) {
                try {
                    contentLength = Integer.parseInt(lines[i].substring(colon + 1).trim());
                } catch (NumberFormatException e) {
                    contentLength = -1;
                }
            }
        }
        Response response;
        if (contentLength < 0 || contentLength > MAX_BODY) {
            response = Response.text(413, "Too large");
        } else {
            byte[] body = readBody(in, contentLength);
            String path = target;
            Map<String, String> query = new HashMap<>();
            int q = target.indexOf('?');
            if (q >= 0) {
                path = target.substring(0, q);
                query = parseForm(target.substring(q + 1));
            }
            if (!key.equals(query.get("k"))) {
                response = Response.text(403, "This link has expired. Scan the code on the TV again.");
            } else {
                try {
                    response = handler.handle(method, path, query, body);
                } catch (Exception e) {
                    response = Response.text(500, "Error: " + e.getMessage());
                }
                if (response == null) response = Response.text(404, "Not found");
            }
        }
        String status = response.code == 200 ? "OK" : "Error";
        String header = "HTTP/1.1 " + response.code + " " + status + "\r\n"
                + "Content-Type: " + response.type + "\r\n"
                + "Content-Length: " + response.body.length + "\r\n"
                + "Cache-Control: no-store\r\n"
                + "Connection: close\r\n\r\n";
        out.write(header.getBytes(StandardCharsets.US_ASCII));
        out.write(response.body);
        out.flush();
    }

    private static String readHead(InputStream in) throws IOException {
        ByteArrayOutputStream head = new ByteArrayOutputStream();
        int last4 = 0;
        while (head.size() < MAX_HEADER) {
            int b = in.read();
            if (b < 0) return null;
            head.write(b);
            last4 = (last4 << 8) | b;
            if (last4 == 0x0D0A0D0A) return head.toString("ISO-8859-1");   // \r\n\r\n
        }
        return null;
    }

    private static byte[] readBody(InputStream in, int length) throws IOException {
        byte[] body = new byte[length];
        int read = 0;
        while (read < length) {
            int n = in.read(body, read, length - read);
            if (n < 0) throw new IOException("short body");
            read += n;
        }
        return body;
    }

    static Map<String, String> parseForm(String form) {
        Map<String, String> map = new HashMap<>();
        if (form == null || form.isEmpty()) return map;
        for (String pair : form.split("&")) {
            int eq = pair.indexOf('=');
            String name = eq < 0 ? pair : pair.substring(0, eq);
            String value = eq < 0 ? "" : pair.substring(eq + 1);
            try {
                map.put(URLDecoder.decode(name, "UTF-8"), URLDecoder.decode(value, "UTF-8"));
            } catch (Exception ignored) {
                // a malformed pair is skipped
            }
        }
        return map;
    }

    /** http://<the TV's IPv4 address>:<port>/?k=<key>, or null when the TV has no network. */
    String address(Context context) {
        String ip = ipv4(context);
        return ip == null ? null : "http://" + ip + ":" + port + "/?k=" + key;
    }

    private static String ipv4(Context context) {
        ConnectivityManager cm = context.getSystemService(ConnectivityManager.class);
        if (cm == null) return null;
        Network network = cm.getActiveNetwork();
        LinkProperties props = network == null ? null : cm.getLinkProperties(network);
        if (props == null) return null;
        for (LinkAddress address : props.getLinkAddresses()) {
            if (address.getAddress() instanceof Inet4Address && !address.getAddress().isLoopbackAddress()) {
                return address.getAddress().getHostAddress();
            }
        }
        return null;
    }

    /** The phone page's shared look: big touch targets, dark, readable on any phone. */
    static String page(String title, String body) {
        return "<!doctype html><html lang=en><head><meta charset=utf-8>"
                + "<meta name=viewport content='width=device-width,initial-scale=1'>"
                + "<title>" + title + "</title><style>"
                + ":root{color-scheme:dark}body{margin:0;padding:24px 16px;background:#111318;color:#f2f2f5;"
                + "font:17px/1.45 -apple-system,system-ui,sans-serif}main{max-width:520px;margin:0 auto}"
                + "h1{font-size:26px;margin:0 0 8px}p{color:#b9bcc6}"
                + "label{display:block;margin:18px 0 6px;font-weight:600}"
                + "input,textarea{box-sizing:border-box;width:100%;padding:14px;border-radius:12px;border:1px solid #3a3e4a;"
                + "background:#1d2029;color:#fff;font-size:17px}textarea{min-height:220px;resize:vertical}"
                + "button,.pick{display:block;box-sizing:border-box;width:100%;margin-top:18px;padding:16px;border:0;"
                + "border-radius:14px;background:#0a84ff;color:#fff;font-size:18px;font-weight:600;text-align:center}"
                + "button:disabled{opacity:.5}#status{margin-top:16px;min-height:24px}"
                + "img{max-width:100%;border-radius:12px;margin-top:16px}"
                + "</style></head><body><main><h1>" + title + "</h1>" + body + "</main></body></html>";
    }

    static String lower(String s) {
        return s == null ? "" : s.toLowerCase(Locale.ROOT);
    }
}
