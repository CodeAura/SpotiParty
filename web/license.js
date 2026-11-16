// SpotiParty Pro licence check in the browser: ECDSA P-256 / SHA-256, with BigInt only.
// No WebCrypto on purpose: that needs HTTPS, and Home Assistant often runs on plain http:// at home.
// Same format and public key as hub/sp_license.py; see there for the details.
"use strict";
const License = (() => {
  const PUB = [0x3577A1D987914146B97F9F74F502E31AADA70359F7035CEA45254126C6525269n,
               0x4403FAEEE2F49F7D471BF4717FE946E2C67F0C3C169E51813291395FACEF2741n];
  const P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFn;
  const A = P - 3n;
  const N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551n;
  const G = [0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296n,
             0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5n];

  const mod = (a, m) => ((a % m) + m) % m;
  function inv(a, m) {
    let [r0, r1, s0, s1] = [mod(a, m), m, 1n, 0n];
    while (r1) { const q = r0 / r1; [r0, r1] = [r1, r0 - q * r1]; [s0, s1] = [s1, s0 - q * s1]; }
    return mod(s0, m);
  }
  function add(p, q) {
    if (!p) return q;
    if (!q) return p;
    let m;
    if (p[0] === q[0]) {
      if (mod(p[1] + q[1], P) === 0n) return null;
      m = mod((3n * p[0] * p[0] + A) * inv(2n * p[1], P), P);
    } else m = mod((q[1] - p[1]) * inv(q[0] - p[0], P), P);
    const x = mod(m * m - p[0] - q[0], P);
    return [x, mod(m * (p[0] - x) - p[1], P)];
  }
  function mul(k, p) {
    let out = null;
    while (k) { if (k & 1n) out = add(out, p); p = add(p, p); k >>= 1n; }
    return out;
  }

  // SHA-256 (FIPS 180-4), small and synchronous.
  const K = new Uint32Array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98,
    0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8,
    0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819,
    0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
    0xc67178f2]);
  function sha256(bytes) {
    const len = bytes.length, total = ((len + 9 + 63) >> 6) << 6, m = new Uint8Array(total);
    m.set(bytes);
    m[len] = 0x80;
    const dv = new DataView(m.buffer);
    dv.setUint32(total - 4, len * 8);
    dv.setUint32(total - 8, Math.floor(len / 0x20000000));
    const h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
    const w = new Uint32Array(64), rot = (x, n) => (x >>> n) | (x << (32 - n));
    for (let o = 0; o < total; o += 64) {
      for (let i = 0; i < 16; i++) w[i] = dv.getUint32(o + i * 4);
      for (let i = 16; i < 64; i++) {
        const s0 = rot(w[i - 15], 7) ^ rot(w[i - 15], 18) ^ (w[i - 15] >>> 3);
        const s1 = rot(w[i - 2], 17) ^ rot(w[i - 2], 19) ^ (w[i - 2] >>> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
      }
      let [a, b, c, d, e, f, g, hh] = h;
      for (let i = 0; i < 64; i++) {
        const t1 = (hh + (rot(e, 6) ^ rot(e, 11) ^ rot(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i]) >>> 0;
        const t2 = ((rot(a, 2) ^ rot(a, 13) ^ rot(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
        [hh, g, f, e, d, c, b, a] = [g, f, e, (d + t1) >>> 0, c, b, a, (t1 + t2) >>> 0];
      }
      [a, b, c, d, e, f, g, hh].forEach((v, i) => { h[i] = (h[i] + v) >>> 0; });
    }
    return [...h].map(x => x.toString(16).padStart(8, "0")).join("");
  }

  function b64d(s) {
    const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - s.length % 4) % 4));
    return Uint8Array.from(bin, c => c.charCodeAt(0));
  }
  const hex = b => BigInt("0x" + [...b].map(x => x.toString(16).padStart(2, "0")).join(""));

  /** The licence payload ({id, to, ed, iat}) if `key` is genuine, else null. */
  function check(key) {
    try {
      key = String(key || "").replace(/\s+/g, "");
      if (!key.startsWith("SPOTI-")) return null;
      const [body, sigTxt] = key.slice(6).split(".");
      const sig = b64d(sigTxt);
      if (sig.length !== 64) return null;
      const r = hex(sig.slice(0, 32)), s = hex(sig.slice(32));
      if (r < 1n || r >= N || s < 1n || s >= N) return null;
      const e = BigInt("0x" + sha256(new TextEncoder().encode(body)));
      const w = inv(s, N);
      const pt = add(mul(mod(e * w, N), G), mul(mod(r * w, N), PUB));
      if (!pt || mod(pt[0], N) !== r) return null;
      const data = JSON.parse(new TextDecoder().decode(b64d(body)));
      return data && data.v === 1 ? data : null;
    } catch { return null; }
  }

  return { check, sha256 };
})();
if (typeof window !== "undefined") window.SpotiPartyLicense = License;
if (typeof module !== "undefined") module.exports = License;
