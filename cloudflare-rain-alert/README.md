# Punctual commute rain alerts — Cloudflare Worker

**Why:** GitHub Actions cron is "best-effort" and was firing your alerts **2–3 hours
late** (morning check arriving at 11:38, evening at 20:04 — after you'd already
ridden). **Cloudflare Cron Triggers fire on time** (~minute accuracy) and are free.
This Worker runs the same bike-commuter rain check and pushes to your Telegram bot.

## Deploy (one-time, ~5 min) — dashboard, no CLI needed
1. Sign in at **https://dash.cloudflare.com** (free account).
2. **Workers & Pages → Create → Create Worker** → name it `commute-rain-alert` → **Deploy**.
3. **Edit code** → delete the sample → paste all of `worker.js` → **Deploy**.
4. **Settings → Variables and Secrets** → add (type: *Secret*):
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `TELEGRAM_CHAT_ID` = `7716436720`
   - (optional) `NTFY_TOPIC` = `wwrain-98cfa8f8dd`
   Save/Deploy.
5. **Settings → Triggers → Cron Triggers → Add** these four (UTC):
   `0 2 * * *`, `15 3 * * *`, `15 11 * * *`, `15 12 * * *`
   (= 07:30 / 08:45 / 16:45 / 17:45 IST). Save.
6. **Test:** open your Worker URL with `?test=1`, e.g.
   `https://commute-rain-alert.<you>.workers.dev/?test=1` → you get a Telegram alert.

## Deploy via CLI (alternative)
```
npm i -g wrangler
wrangler login
cd cloudflare-rain-alert
wrangler secret put TELEGRAM_BOT_TOKEN
wrangler secret put TELEGRAM_CHAT_ID
# optional: wrangler secret put NTFY_TOPIC
wrangler deploy        # crons come from wrangler.toml
```

## After it works
Turn off the GitHub Actions schedule so you don't get duplicate (late) messages —
tell me and I'll disable the cron in `.github/workflows/rain-alert.yml` (keeping
manual runs). Same bot, same message format — just punctual now.

## Tuning
Edit the constants at the top of `worker.js`: `LOCS`, `WINDOWS`, `WET_MM/WET_PROB`,
`HVY_MM/HVY_PROB`. Redeploy.
