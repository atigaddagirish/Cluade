// Commute rain alert — Cloudflare Worker (punctual cron, unlike GitHub Actions).
//
// Fires on schedule (see wrangler.toml), checks Open-Meteo rain for the trip
// windows, and pushes a bike-commuter alert to Telegram (and/or ntfy). Cloudflare
// Cron Triggers run on time (~minute accuracy), so alerts land before you ride.
//
// Set as Worker secrets/vars (wrangler secret put …, or dashboard → Settings → Variables):
//   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID   (Telegram)   and/or   NTFY_TOPIC (ntfy)
//
// Manual test in a browser:  https://<your-worker-url>/?test=1

const LOCS = { Manikonda: [17.400695, 78.365313], Office: [17.444606, 78.465291] };
const WINDOWS = {
  morning: ["09:15", "10:45", "Manikonda → Office"],
  evening: ["18:15", "19:45", "Office → Manikonda"],
};
const WET_MM = 0.2, WET_PROB = 40, HVY_MM = 2.0, HVY_PROB = 70;

// which cron does what (UTC crons from wrangler.toml)
const CRON_MAP = {
  "0 2 * * *":  { mode: "morning", stage: "early", always: false }, // 07:30 IST
  "15 3 * * *": { mode: "morning", stage: "final", always: true },  // 08:45 IST
  "15 11 * * *":{ mode: "evening", stage: "early", always: false }, // 16:45 IST
  "15 12 * * *":{ mode: "evening", stage: "final", always: true },  // 17:45 IST
};

const isWet = (mm, pr) => mm >= WET_MM || pr >= WET_PROB;
const isHeavy = (mm, pr) => mm >= HVY_MM || pr >= HVY_PROB;

function istToday() {
  return new Date(Date.now() + 5.5 * 3600 * 1000).toISOString().slice(0, 10);
}

async function forecast(lat, lon) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
    `&timezone=Asia%2FKolkata&hourly=precipitation,precipitation_probability,weathercode` +
    `&minutely_15=precipitation&forecast_days=2`;
  const r = await fetch(url, { cf: { cacheTtl: 0 } });
  return r.json();
}

function windowSeries(fc, start, end) {
  const today = istToday();
  const h = fc.hourly || {};
  const hourPr = {}, hourMm = {};
  (h.time || []).forEach((t, i) => {
    if (t.startsWith(today)) { hourPr[t.slice(11, 13)] = h.precipitation_probability[i] || 0; hourMm[t.slice(11, 13)] = h.precipitation[i] || 0; }
  });
  const out = [];
  const m = fc.minutely_15 || {};
  if (m.time && m.time.length) {
    m.time.forEach((t, i) => {
      const hm = t.slice(11, 16);
      if (t.startsWith(today) && hm >= start && hm <= end) out.push([hm, m.precipitation[i] || 0, hourPr[t.slice(11, 13)] || 0]);
    });
  } else {
    (h.time || []).forEach((t, i) => {
      const hm = t.slice(11, 16);
      if (t.startsWith(today) && hm >= start && hm <= end) out.push([hm, h.precipitation[i] || 0, h.precipitation_probability[i] || 0]);
    });
  }
  return out;
}

async function buildMessage(mode, stage) {
  const [start, end, route] = WINDOWS[mode];
  const lines = [];
  let overall = "dry", firstWet = null;
  const order = route.split("→").map(s => s.trim());   // list in travel order (origin first)
  for (const name of order) {
    const loc = LOCS[name];
    if (!loc) continue;
    const [lat, lon] = loc;
    let series;
    try { series = windowSeries(await forecast(lat, lon), start, end); }
    catch (e) { continue; }
    const peakMm = series.reduce((a, s) => Math.max(a, s[1]), 0);
    const peakPr = series.reduce((a, s) => Math.max(a, s[2]), 0);
    const wetHits = series.filter(s => isWet(s[1], s[2])).map(s => s[0]);
    const level = series.some(s => isHeavy(s[1], s[2])) ? "heavy" : (wetHits.length ? "wet" : "dry");
    if (level === "heavy") overall = "heavy";
    else if (level === "wet" && overall === "dry") overall = "wet";
    if (wetHits.length) firstWet = firstWet ? (wetHits[0] < firstWet ? wetHits[0] : firstWet) : wetHits[0];
    const icon = { heavy: "🔴", wet: "🟠", dry: "🟢" }[level];
    const tail = level === "dry" ? "dry" : `${Math.round(peakMm * 10) / 10}mm / ${Math.round(peakPr)}%${wetHits.length ? `, from ~${wetHits[0]}` : ""}`;
    lines.push(`${icon} <b>${name}</b>: ${tail}`);
  }
  const tag = stage === "early" ? " · early heads-up" : "";
  let body = `🏍️ <b>Bike commute — ${route}</b> (${start}–${end} IST${tag})\n` + lines.join("\n");
  if (firstWet && firstWet > start) body += `\n\n🕒 Dry until ~${firstWet} — leave before then to beat it.`;
  else if (firstWet) body += `\n\n🕒 Rain around from the start of your window (~${firstWet}).`;
  if (overall === "heavy") body += "\n🔴 <b>Protect the bag</b> — rain likely on the ride. Use a waterproof cover / line the bag, or take a cab / wait it out.";
  else if (overall === "wet") body += "\n🟠 <b>Rain possible</b> — carry a rain cover for the laptop bag and keep an eye on the sky.";
  else body += "\n🟢 <b>Looks dry</b> — good to ride.";
  return { body, rainy: overall !== "dry" };
}

async function sendTelegram(env, text) {
  const tok = (env.TELEGRAM_BOT_TOKEN || "").replace(/\s/g, "");
  const chat = (env.TELEGRAM_CHAT_ID || "").replace(/\s/g, "");
  if (!tok || !chat) return;
  await fetch(`https://api.telegram.org/bot${tok}/sendMessage`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chat, text, parse_mode: "HTML", disable_web_page_preview: true }),
  });
}

async function sendNtfy(env, text, rainy) {
  const topic = (env.NTFY_TOPIC || "").trim();
  if (!topic) return;
  await fetch(`https://ntfy.sh/${topic}`, {
    method: "POST", body: text.replace(/<[^>]+>/g, ""),
    headers: { Title: "Commute rain alert", Priority: rainy ? "high" : "default", Tags: rainy ? "umbrella,rain_cloud" : "sunny" },
  });
}

async function run(env, mode, stage, always) {
  const { body, rainy } = await buildMessage(mode, stage);
  if (rainy || always) { await sendTelegram(env, body); await sendNtfy(env, body, rainy); return body; }
  return "(dry, not sending)\n" + body;
}

export default {
  async scheduled(event, env, ctx) {
    const cfg = CRON_MAP[event.cron];
    if (cfg) ctx.waitUntil(run(env, cfg.mode, cfg.stage, cfg.always));
  },
  async fetch(req, env) {
    const u = new URL(req.url);
    if (u.searchParams.get("test") != null) {
      const mode = u.searchParams.get("mode") || (new Date(Date.now() + 5.5 * 3600e3).getUTCHours() < 14 ? "morning" : "evening");
      const out = await run(env, mode, "final", true);
      return new Response(out, { headers: { "content-type": "text/plain; charset=utf-8" } });
    }
    return new Response("commute-rain-alert worker. Add ?test=1 to send a test.", { headers: { "content-type": "text/plain" } });
  },
};
