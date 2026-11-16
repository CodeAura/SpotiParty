"""SpotiParty licence tool, for the seller only.

    python tools/license.py keygen              # once: makes the signing key (keep it secret, back it up)
    python tools/license.py sign "Jan Jansen <jan@example.com>" 1001
    python tools/license.py check SPOTI-...

The private key is kept in ~/.spotiparty/license-private.json (a JWK, so the Netlify function can use the
same file as the SPOTIPARTY_LICENSE_JWK environment variable). It is never part of the repository.
"""
import argparse
import base64
import datetime
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "hub"))
import sp_license as L  # noqa: E402

KEY_FILE = pathlib.Path.home() / ".spotiparty" / "license-private.json"


def b64(n: int) -> str:
    return base64.urlsafe_b64encode(n.to_bytes(32, "big")).rstrip(b"=").decode()


def unb64(s: str) -> int:
    return int.from_bytes(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)), "big")


def load_private() -> int:
    if not KEY_FILE.exists():
        sys.exit(f"No signing key at {KEY_FILE}. Run: python tools/license.py keygen")
    return unb64(json.loads(KEY_FILE.read_text())["d"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("keygen")
    k.add_argument("--force", action="store_true", help="overwrite an existing key (every sold key stops working)")
    s = sub.add_parser("sign")
    s.add_argument("to", help="buyer's name and/or e-mail, shown on every screen")
    s.add_argument("id", help="order number or another unique id")
    s.add_argument("--edition", default="pro")
    c = sub.add_parser("check")
    c.add_argument("key")
    a = ap.parse_args()

    if a.cmd == "keygen":
        if KEY_FILE.exists() and not a.force:
            sys.exit(f"{KEY_FILE} already exists. Every key you sold depends on it; use --force only on purpose.")
        d, (x, y) = L.new_keypair()
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        jwk = {"kty": "EC", "crv": "P-256", "x": b64(x), "y": b64(y), "d": b64(d)}
        KEY_FILE.write_text(json.dumps(jwk))
        os.chmod(KEY_FILE, 0o600)
        print(f"Private key written to {KEY_FILE} (back it up somewhere safe).\n")
        print("Public key, for hub/sp_license.py and web/license.js:")
        print(f"PUBLIC_X = 0x{x:064X}\nPUBLIC_Y = 0x{y:064X}")
    elif a.cmd == "sign":
        d = load_private()
        key = L.issue(d, a.to, a.id, a.edition, datetime.date.today().isoformat())
        assert L.check(key, L.public_of(d))
        print(key)
    else:
        print(json.dumps(L.check(a.key), ensure_ascii=False) if L.check(a.key) else "INVALID")


if __name__ == "__main__":
    main()
