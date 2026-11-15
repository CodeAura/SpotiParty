"""SpotiParty on the PC: serves this folder on http://127.0.0.1:8769/ and opens it in the browser.

    python serve.py            # then add http://127.0.0.1:8769/index.html as a Redirect URI in your Spotify app
    python serve.py --port 9000 --no-browser

Only the loopback address is used: Spotify accepts http:// redirects there, and nothing is open to the network.
No packages needed beyond Python 3.
"""
import argparse
import functools
import http.server
import pathlib
import webbrowser


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8769)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    root = pathlib.Path(__file__).resolve().parent
    server = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), functools.partial(Handler, directory=str(root)))
    url = f"http://127.0.0.1:{a.port}/index.html"
    print(f"SpotiParty: {url}  (Ctrl+C stops)")
    if not a.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
