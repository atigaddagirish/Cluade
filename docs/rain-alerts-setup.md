# Commute rain alerts — setup (5 minutes)

Weather Watch can message your phone **before each commute** if rain is likely at
**Manikonda** or **Office**, timed to your trips:
- **Morning** ~08:45 IST → checks the **09:30–10:30** window (Manikonda → Office, ~50 min)
- **Evening** ~17:45 IST → checks the **18:30–19:30** window (Office → Manikonda)

It only pings you **when rain crosses the threshold** (no spam). Delivery is via a
**Telegram bot** — the most reliable free push to a phone (web-push from a static
site is flaky). Forecast source: Open-Meteo (ECMWF/GFS), which cloud servers can
reach.

## One-time setup
1. **Create a bot:** in Telegram, message **@BotFather** → `/newbot` → pick a name.
   It gives you a **bot token** like `1234567890:AA...`.
2. **Start a chat with your new bot** (search its @username, tap Start, say "hi").
3. **Get your chat id:** open this URL in a browser (paste your token):
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Find `"chat":{"id":123456789,...}` — that number is your **chat id**.
4. **Add two repo secrets:** GitHub → repo **Settings → Secrets and variables →
   Actions → New repository secret**:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `TELEGRAM_CHAT_ID` = your chat id
5. **Test it now:** Actions tab → **"Commute rain alert"** → **Run workflow**.
   You should get a Telegram message within a minute (or the run log shows what it
   *would* send if a secret is missing).

That's it — from then on it runs automatically morning and evening.

## Tuning (optional)
Edit `.github/workflows/rain-alert.yml` / `scripts/rain_alert.py`:
- **Locations / times:** change `LOCS` and `WINDOWS` in `rain_alert.py` (or set a
  `LOCS` env as JSON). Travel time is baked into the window (30 min before + ~50 min after departure).
- **Sensitivity:** env `RAIN_MM` (default 0.3 mm) and `RAIN_PROB` (default 50%).
- **Always notify** (even when dry): set `ALERT_ALWAYS: "1"` in the workflow.

## Notes
- GitHub cron is best-effort and can slip a few minutes; the checks are scheduled
  ~45 min before departure to stay ahead of it.
- Alerts use the **forecast** (not live radar) so they can run on GitHub's servers.
  For live rain right before you leave, open the app — Now tab "Rain — next 2 h"
  and the Maps RainViewer radar.
