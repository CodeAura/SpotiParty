// A QR code for a short text (the Jam link): byte mode, error correction M, versions 1 to 15.
// A straight port of the add-on's Qr.java (after Project Nayuki's MIT-licensed generator); no library.
"use strict";
const Qr = (() => {
  const ECC = [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24];
  const BLOCKS = [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10];

  function rawModules(v) {
    let r = (16 * v + 128) * v + 64;
    if (v >= 2) {
      const n = Math.floor(v / 7) + 2;
      r -= (25 * n - 10) * n - 55;
      if (v >= 7) r -= 36;
    }
    return r;
  }
  const dataCodewords = v => Math.floor(rawModules(v) / 8) - ECC[v] * BLOCKS[v];

  function mul(x, y) {
    let z = 0;
    for (let i = 7; i >= 0; i--) {
      z = (z << 1) ^ ((z >>> 7) * 0x11d);
      z ^= ((y >>> i) & 1) * x;
    }
    return z & 0xff;
  }
  function rsDivisor(deg) {
    const r = new Array(deg).fill(0);
    r[deg - 1] = 1;
    let root = 1;
    for (let i = 0; i < deg; i++) {
      for (let j = 0; j < deg; j++) {
        r[j] = mul(r[j], root);
        if (j + 1 < deg) r[j] ^= r[j + 1];
      }
      root = mul(root, 2);
    }
    return r;
  }
  function rsRemainder(data, div) {
    const r = new Array(div.length).fill(0);
    for (const b of data) {
      const f = b ^ r.shift();
      r.push(0);
      for (let i = 0; i < r.length; i++) r[i] ^= mul(div[i], f);
    }
    return r;
  }
  function withEcc(v, data) {
    const blocks = BLOCKS[v], eccLen = ECC[v], raw = Math.floor(rawModules(v) / 8);
    const shortBlocks = blocks - (raw % blocks), shortLen = Math.floor(raw / blocks);
    const div = rsDivisor(eccLen);
    const all = [];
    for (let i = 0, k = 0; i < blocks; i++) {
      const len = shortLen - eccLen + (i < shortBlocks ? 0 : 1);
      const dat = data.slice(k, k + len);
      k += len;
      const block = dat.concat(new Array(shortLen + 1 - len).fill(0));
      const ecc = rsRemainder(dat, div);
      for (let e = 0; e < eccLen; e++) block[block.length - eccLen + e] = ecc[e];
      all.push(block);
    }
    const out = [];
    for (let i = 0; i < shortLen + 1; i++)
      for (let j = 0; j < blocks; j++)
        if (i !== shortLen - eccLen || j >= shortBlocks) out.push(all[j][i]);
    return out;
  }

  function encode(text) {
    const bytes = Array.from(new TextEncoder().encode(text));
    for (let v = 1; v <= 15; v++) {
      const cap = dataCodewords(v) * 8, countBits = v < 10 ? 8 : 16;
      if (4 + countBits + bytes.length * 8 > cap) continue;
      const bits = [];
      const add = (val, n) => { for (let i = n - 1; i >= 0; i--) bits.push((val >>> i) & 1); };
      add(4, 4);
      add(bytes.length, countBits);
      bytes.forEach(b => add(b, 8));
      add(0, Math.min(4, cap - bits.length));
      add(0, (8 - (bits.length % 8)) % 8);
      for (let pad = 0xec; bits.length < cap; pad ^= 0xec ^ 0x11) add(pad, 8);
      const data = [];
      for (let i = 0; i < bits.length; i += 8) data.push(parseInt(bits.slice(i, i + 8).join(""), 2));
      return draw(v, withEcc(v, data));
    }
    return null;
  }

  function draw(v, codewords) {
    const size = v * 4 + 17;
    const dark = Array.from({ length: size }, () => new Array(size).fill(false));
    const fn = Array.from({ length: size }, () => new Array(size).fill(false));
    const set = (x, y, d) => { dark[y][x] = d; fn[y][x] = true; };
    const bit = (val, i) => ((val >>> i) & 1) !== 0;

    function format(mask) {
      const data = (0 << 3) | mask;
      let rem = data;
      for (let i = 0; i < 10; i++) rem = (rem << 1) ^ ((rem >>> 9) * 0x537);
      const b = ((data << 10) | rem) ^ 0x5412;
      for (let i = 0; i <= 5; i++) set(8, i, bit(b, i));
      set(8, 7, bit(b, 6)); set(8, 8, bit(b, 7)); set(7, 8, bit(b, 8));
      for (let i = 9; i < 15; i++) set(14 - i, 8, bit(b, i));
      for (let i = 0; i < 8; i++) set(size - 1 - i, 8, bit(b, i));
      for (let i = 8; i < 15; i++) set(8, size - 15 + i, bit(b, i));
      set(8, size - 8, true);
    }
    function finder(x, y) {
      for (let dy = -4; dy <= 4; dy++)
        for (let dx = -4; dx <= 4; dx++) {
          const d = Math.max(Math.abs(dx), Math.abs(dy)), xx = x + dx, yy = y + dy;
          if (xx >= 0 && xx < size && yy >= 0 && yy < size) set(xx, yy, d !== 2 && d !== 4);
        }
    }
    for (let i = 0; i < size; i++) { set(6, i, i % 2 === 0); set(i, 6, i % 2 === 0); }
    finder(3, 3); finder(size - 4, 3); finder(3, size - 4);
    let align = [];
    if (v > 1) {
      const n = Math.floor(v / 7) + 2;
      const step = Math.floor((v * 4 + n * 2 + 1) / (n * 2 - 2)) * 2;
      align = new Array(n);
      align[0] = 6;
      for (let i = n - 1, pos = v * 4 + 10; i >= 1; i--, pos -= step) align[i] = pos;
    }
    const n = align.length;
    for (let i = 0; i < n; i++)
      for (let j = 0; j < n; j++) {
        if ((i === 0 && j === 0) || (i === 0 && j === n - 1) || (i === n - 1 && j === 0)) continue;
        for (let dy = -2; dy <= 2; dy++)
          for (let dx = -2; dx <= 2; dx++)
            set(align[i] + dx, align[j] + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
      }
    format(0);
    if (v >= 7) {
      let rem = v;
      for (let i = 0; i < 12; i++) rem = (rem << 1) ^ ((rem >>> 11) * 0x1f25);
      const b = (v << 12) | rem;
      for (let i = 0; i < 18; i++) {
        const a = size - 11 + (i % 3), c = Math.floor(i / 3);
        set(a, c, bit(b, i)); set(c, a, bit(b, i));
      }
    }
    // codewords
    let k = 0;
    for (let right = size - 1; right >= 1; right -= 2) {
      if (right === 6) right = 5;
      for (let vert = 0; vert < size; vert++)
        for (let j = 0; j < 2; j++) {
          const x = right - j, up = ((right + 1) & 2) === 0, y = up ? size - 1 - vert : vert;
          if (!fn[y][x] && k < codewords.length * 8) {
            dark[y][x] = ((codewords[k >>> 3] >>> (7 - (k & 7))) & 1) !== 0;
            k++;
          }
        }
    }
    const masks = [
      (x, y) => (x + y) % 2 === 0, (x, y) => y % 2 === 0, (x) => x % 3 === 0,
      (x, y) => (x + y) % 3 === 0, (x, y) => (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0,
      (x, y) => ((x * y) % 2) + ((x * y) % 3) === 0, (x, y) => (((x * y) % 2) + ((x * y) % 3)) % 2 === 0,
      (x, y) => (((x + y) % 2) + ((x * y) % 3)) % 2 === 0,
    ];
    const apply = m => {
      for (let y = 0; y < size; y++)
        for (let x = 0; x < size; x++) if (!fn[y][x] && masks[m](x, y)) dark[y][x] = !dark[y][x];
    };
    function penalty() {
      let p = 0;
      for (let a = 0; a < size; a++) {
        let rr = 1, cr = 1;
        for (let b = 1; b < size; b++) {
          if (dark[a][b] === dark[a][b - 1]) { if (++rr === 5) p += 3; else if (rr > 5) p++; } else rr = 1;
          if (dark[b][a] === dark[b - 1][a]) { if (++cr === 5) p += 3; else if (cr > 5) p++; } else cr = 1;
        }
      }
      let dc = 0;
      for (let y = 0; y < size; y++)
        for (let x = 0; x < size; x++) {
          if (dark[y][x]) dc++;
          if (x + 1 < size && y + 1 < size && dark[y][x] === dark[y][x + 1] &&
              dark[y][x] === dark[y + 1][x] && dark[y][x] === dark[y + 1][x + 1]) p += 3;
        }
      const total = size * size;
      const kk = Math.floor((Math.abs(dc * 20 - total * 10) + total - 1) / total) - 1;
      return p + Math.max(kk, 0) * 10;
    }
    let best = 0, bestP = Infinity;
    for (let m = 0; m < 8; m++) {
      apply(m); format(m);
      const p = penalty();
      if (p < bestP) { best = m; bestP = p; }
      apply(m);
    }
    apply(best); format(best);
    return dark;
  }

  /** Draws the code on a canvas, black on white with a 2-module quiet zone. */
  function paint(canvas, text) {
    const g = canvas.getContext("2d");
    const m = text ? encode(text) : null;
    const px = canvas.width;
    g.clearRect(0, 0, px, px);
    if (!m) return false;
    const n = m.length + 4, s = px / n;
    g.fillStyle = "#fff";
    g.beginPath();
    g.roundRect ? g.roundRect(0, 0, px, px, px * 0.06) : g.rect(0, 0, px, px);
    g.fill();
    g.fillStyle = "#000";
    for (let y = 0; y < m.length; y++)
      for (let x = 0; x < m.length; x++)
        if (m[y][x]) g.fillRect(Math.floor((x + 2) * s), Math.floor((y + 2) * s), Math.ceil(s), Math.ceil(s));
    return true;
  }

  return { encode, paint };
})();
