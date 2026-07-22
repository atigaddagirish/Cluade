# Commute rain alerts — setup

Weather Watch messages your phone **before each commute** if rain is likely at
**Manikonda** or **Office**:
- **Morning** ~08:45 IST → checks the **09:30–10:30** window (Manikonda → Office, ~50 min)
- **Evening** ~17:45 IST → checks the **18:30–19:30** window (Office → Manikonda)

It only pings you **when rain crosses the threshold** (no spam). Forecast source:
Open-Meteo (ECMWF/GFS), reachable from GitHub's servers.

## Easiest — ntfy (no account, no bot, no tokens) ✅ default
The alerts already send to the ntfy topic **`wwrain-98cfa8f8dd`**. All you do is
subscribe to it:

1. Install the free **ntfy** app — [Android (Play Store / F-Droid)](https://ntfy.sh/) or iOS.
   (Or use the web app at https://ntfy.sh in Chrome and click "Subscribe".)
2. Tap **＋ / Subscribe to topic**, enter exactly: **`wwrain-98cfa8f8dd`**, Subscribe.
3. Done. Test it: GitHub → **Actions → "Commute rain alert" → Run workflow**
   (leave *test* ticked) → you get a push within a minute.

That topic is private-by-obscurity. To make it truly private, add a repo secret
`NTFY_TOPIC` with your own random name and subscribe to that instead.

## Alternative — Telegram (if you prefer)
Set repo secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` and it sends there too:
1. Telegram → **@BotFather** → `/newbot` → get the **token**.
2. Message your new bot "hi", then open `https://api.telegram.org/bot<TOKEN>/getUpdates`
   and copy the `"chat":{"id":…}` number.
3. GitHub → **Settings → Secrets and variables → Actions** → add both secrets.

## Tuning (optional)
Edit `.github/workflows/rain-alert.yml` / `scripts/rain_alert.py`:
- **Locations / times:** `LOCS` and `WINDOWS` in `rain_alert.py`.
- **Sensitivity:** env `RAIN_MM` (default 0.3 mm), `RAIN_PROB` (default 50%).
- **Always notify** (even when dry): set `ALERT_ALWAYS: "1"` in the workflow.

## Notes
- GitHub cron is best-effort (can slip a few min); checks run ~45 min before departure.
- Alerts use the **forecast** so they can run on GitHub's servers. For live rain
  right before leaving, open the app — Now tab "Rain — next 2 h" + Maps radar.
