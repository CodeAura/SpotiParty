// Shopify "Order payment" webhook → SpotiParty Pro licence keys, mailed to the buyer.
//
// Shopify: Settings → Notifications → Webhooks → Create webhook
//   Event: Order payment   Format: JSON   URL: https://<your-site>/.netlify/functions/shopify-order
//
// Netlify environment variables (Site configuration → Environment variables):
//   SHOPIFY_WEBHOOK_SECRET   the "signed by" secret shown under the webhooks list in Shopify
//   SPOTIPARTY_LICENSE_JWK   contents of ~/.spotiparty/license-private.json (from tools/license.py keygen)
//   RESEND_API_KEY           resend.com API key, for the mail with the key(s)
//   MAIL_FROM                e.g. "SpotiParty <licentie@jouwdomein.nl>" (a domain verified in Resend)
//   SHOPIFY_SHOP             optional: jouwwinkel.myshopify.com  } also store the keys on the order
//   SHOPIFY_ADMIN_TOKEN      optional: Admin API token           } (metafield spotiparty.licenses)
//
// Which products give keys, and how many per unit (by SKU):
const SKUS = { "SPOTIPARTY-PRO": 1, "SPOTIPARTY-PRO-3": 3 };

import crypto from "node:crypto";

const b64url = buf => Buffer.from(buf).toString("base64url");

export function issue(jwk, to, id, iat) {
  const body = b64url(JSON.stringify({ v: 1, id: String(id), to, ed: "pro", iat }));
  const key = crypto.createPrivateKey({ key: jwk, format: "jwk" });
  const sig = crypto.sign("sha256", Buffer.from(body), { key, dsaEncoding: "ieee-p1363" });
  return `SPOTI-${body}.${b64url(sig)}`;
}

export function verifyShopify(raw, hmac, secret) {
  if (!hmac || !secret) return false;
  const want = crypto.createHmac("sha256", secret).update(raw).digest();
  const got = Buffer.from(hmac, "base64");
  return got.length === want.length && crypto.timingSafeEqual(got, want);
}

export function keysFor(order, jwk) {
  const c = order.customer || {}, addr = order.billing_address || {};
  const name = [c.first_name || addr.first_name, c.last_name || addr.last_name].filter(Boolean).join(" ");
  const email = order.email || order.contact_email || c.email || "";
  const to = name && email ? `${name} <${email}>` : name || email || "SpotiParty-koper";
  const iat = (order.processed_at || order.created_at || new Date().toISOString()).slice(0, 10);
  const out = [];
  for (const item of order.line_items || []) {
    const per = SKUS[(item.sku || "").trim().toUpperCase()];
    if (!per) continue;
    for (let i = 0; i < per * (item.quantity || 1); i++) {
      const id = `${String(order.name || order.id).replace(/^#/, "")}-${out.length + 1}`;
      out.push({ id, key: issue(jwk, to, id, iat) });
    }
  }
  return { to, email, keys: out };
}

function mailHtml(name, keys) {
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  return `<div style="font:16px/1.5 system-ui,sans-serif;max-width:560px">
    <h2>Bedankt voor je aankoop van SpotiParty Pro! 🎉</h2>
    <p>Hoi ${esc(name || "")}, hieronder staat je licentiecode${keys.length > 1 ? "s (één per installatie)" : ""}.</p>
    ${keys.map(k => `<p style="background:#f2f2f5;padding:12px;border-radius:8px;word-break:break-all;font-family:monospace;font-size:13px">${esc(k.key)}</p>`).join("")}
    <p><b>Activeren:</b> open het SpotiParty Hub-dashboard (in de desktop-app: <i>Dashboard</i>, of
      <code>http://&lt;je-pc-of-pi&gt;:8770</code>), ga naar <b>Licentie</b> en plak de code. Voor de Home
      Assistant-kaart zet je hem bij <code>license:</code> in de kaart.</p>
    <p>De code staat op jouw naam en is voor jouw eigen huis. Bewaar deze mail goed.</p>
    <p>Veel feestplezier!<br>SpotiParty</p></div>`;
}

async function sendMail(to, name, keys) {
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: process.env.MAIL_FROM, to: [to],
      subject: keys.length > 1 ? "Je SpotiParty Pro-licentiecodes" : "Je SpotiParty Pro-licentiecode",
      html: mailHtml(name, keys),
      text: `Bedankt voor je aankoop van SpotiParty Pro!\n\n${keys.map(k => k.key).join("\n\n")}\n\n`
        + "Plak de code in het SpotiParty Hub-dashboard onder Licentie.",
    }),
  });
  if (!r.ok) throw new Error(`Resend ${r.status}: ${await r.text()}`);
}

async function saveOnOrder(order, keys) {
  const shop = process.env.SHOPIFY_SHOP, token = process.env.SHOPIFY_ADMIN_TOKEN;
  if (!shop || !token || !order.admin_graphql_api_id) return;
  const r = await fetch(`https://${shop}/admin/api/2025-01/graphql.json`, {
    method: "POST",
    headers: { "X-Shopify-Access-Token": token, "Content-Type": "application/json" },
    body: JSON.stringify({
      query: `mutation($m:[MetafieldsSetInput!]!){metafieldsSet(metafields:$m){userErrors{message}}}`,
      variables: { m: [{ ownerId: order.admin_graphql_api_id, namespace: "spotiparty", key: "licenses",
        type: "multi_line_text_field", value: keys.map(k => k.key).join("\n") }] },
    }),
  });
  if (!r.ok) console.warn("metafield", r.status, await r.text());
}

export default async (req) => {
  if (req.method !== "POST") return new Response("POST only", { status: 405 });
  const raw = Buffer.from(await req.arrayBuffer());
  if (!verifyShopify(raw, req.headers.get("x-shopify-hmac-sha256"), process.env.SHOPIFY_WEBHOOK_SECRET)) {
    return new Response("bad signature", { status: 401 });
  }
  const order = JSON.parse(raw.toString("utf8"));
  const jwk = JSON.parse(process.env.SPOTIPARTY_LICENSE_JWK || "{}");
  const { to, email, keys } = keysFor(order, jwk);
  if (!keys.length) return new Response("no SpotiParty items", { status: 200 });
  console.log(`order ${order.name}: ${keys.length} key(s) for ${email ? "buyer" : "unknown buyer"}`);
  // A failure here returns 500, so Shopify retries the webhook later (up to 48 hours).
  await saveOnOrder(order, keys);
  if (email) await sendMail(email, to.replace(/\s*<.*$/, ""), keys);
  return new Response(JSON.stringify({ keys: keys.length }), { status: 200, headers: { "Content-Type": "application/json" } });
};
