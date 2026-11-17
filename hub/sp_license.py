"""SpotiParty Pro licence keys: ECDSA P-256 / SHA-256 signatures, checked offline with no packages.

A key looks like  SPOTI-<payload>.<signature>  (both base64url). The payload is compact JSON:

    {"v": 1, "id": "1001", "to": "Naam of e-mail", "ed": "pro", "iat": "2026-11-16"}

The signature is the 64-byte raw r||s form (what WebCrypto and Node's dsaEncoding "ieee-p1363" give).
Only the public key ships with SpotiParty; the private key stays with the seller (Netlify env var and
the tools/license.py key file). A key can't be forged without it, and it carries the buyer's name,
which every screen and the dashboard show: sharing a key means sharing your name with it.

The same check lives in web/license.js (for the Home Assistant card) and shop/netlify/functions/ (issuing).
"""
import base64
import hashlib
import json
import secrets

# ---- the SpotiParty public key (x, y on P-256). Replace both together with tools/license.py keygen. ----
PUBLIC_X = 0x021708034108A773173BF428109A60D43A7A8677B112BCAF00A9D583AE36951D
PUBLIC_Y = 0x2AF1C50DA7C33F929FCD75E420AF11ADB6D922EA3A2EAC619937EAF641696C86

PREFIX = "SPOTI-"

# ---- P-256 ----
P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
A = P - 3
B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
G = (0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
     0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5)


def _on_curve(pt):
    x, y = pt
    return 0 <= x < P and 0 <= y < P and (y * y - (x * x * x + A * x + B)) % P == 0


def _add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    (x1, y1), (x2, y2) = p1, p2
    if x1 == x2:
        if (y1 + y2) % P == 0:
            return None
        m = (3 * x1 * x1 + A) * pow(2 * y1, -1, P) % P
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, P) % P
    x3 = (m * m - x1 - x2) % P
    return x3, (m * (x1 - x3) - y1) % P


def _mul(k, pt):
    out = None
    while k:
        if k & 1:
            out = _add(out, pt)
        pt = _add(pt, pt)
        k >>= 1
    return out


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _hash(msg: bytes) -> int:
    return int.from_bytes(hashlib.sha256(msg).digest(), "big")


def verify_sig(pub, msg: bytes, sig: bytes) -> bool:
    if len(sig) != 64 or not _on_curve(pub):
        return False
    r, s = int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:], "big")
    if not (1 <= r < N and 1 <= s < N):
        return False
    w = pow(s, -1, N)
    pt = _add(_mul(_hash(msg) * w % N, G), _mul(r * w % N, pub))
    return pt is not None and pt[0] % N == r


def sign_sig(d: int, msg: bytes) -> bytes:
    e = _hash(msg)
    while True:
        k = secrets.randbelow(N - 1) + 1
        r = _mul(k, G)[0] % N
        s = pow(k, -1, N) * (e + r * d) % N
        if r and s:
            return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def new_keypair():
    d = secrets.randbelow(N - 1) + 1
    return d, _mul(d, G)


def public_of(d: int):
    return _mul(d, G)


def issue(d: int, to: str, lic_id: str, edition: str = "pro", iat: str = "") -> str:
    payload = {"v": 1, "id": str(lic_id), "to": to, "ed": edition, "iat": iat}
    body = _b64e(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())
    return PREFIX + body + "." + _b64e(sign_sig(d, body.encode()))


def check(key: str, pub=None):
    """The licence's payload dict if `key` is a genuine SpotiParty key, else None."""
    pub = pub or (PUBLIC_X, PUBLIC_Y)
    try:
        key = "".join(key.split())
        if not key.startswith(PREFIX):
            return None
        body, sig = key[len(PREFIX):].split(".", 1)
        if not verify_sig(pub, body.encode(), _b64d(sig)):
            return None
        data = json.loads(_b64d(body))
        return data if isinstance(data, dict) and data.get("v") == 1 else None
    except Exception:
        return None
