#!/usr/bin/env python3
"""Commute rain alerts for Weather Watch — sends a Telegram message if rain is
likely for the user's trip windows (Manikonda <-> Office, ~50 min travel).

Runs from GitHub Actions cron (see .github/workflows/rain-alert.yml). Uses the
free Open-Meteo forecast (ECMWF/GFS), which is reachable from cloud IPs (unlike
IMD/Telangana). Only sends a message when rain crosses the threshold, so it does
not spam — set ALERT_ALWAYS=1 to also get an "all clear" note.

Secrets/env:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID   (required to actually send)
  ALERT_MODE = morning | evening | auto   (auto picks by current IST hour)
  RAIN_MM = 0.3     precip threshold (mm within a window hour)
  RAIN_PROB = 50    probability threshold (%)
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

# name -> (lat, lon). Edit here (or via env LOCS as JSON) to change places.
LOCS = {"Manikonda": (17.400695, 78.365313), "Office": (17.444606, 78.465291)}
try:
    LOCS = {k: (v[0], v[1]) for k, v in json.loads(os.environ["LOCS"]).items()}
except Exception:  # noqa: BLE001
    pass

# trip windows in IST (start_hour, start_min) .. covers departure + ~50 min travel
WINDOWS = {
    "morning": ("09:30", "10:30", "Manikonda → Office"),
    "evening": ("18:30", "19:30", "Office → Manikonda"),
}
RAIN_MM = float(os.environ.get("RAIN_MM", "0.3"))
RAIN_PROB = float(os.environ.get("RAIN_PROB", "50"))


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def forecast(lat, lon):
    url = ("https://api.open-meteo.com/v1/forecast?"
           f"latitude={lat}&longitude={lon}&timezone=Asia%2FKolkata"
           "&hourly=precipitation,precipitation_probability,weathercode&forecast_days=2")
    return get(url)


def window_rain(fc, start, end):
    """Max precip (mm) and probability (%) over today's [start,end] IST hours."""
    h = fc["hourly"]
    today = datetime.now(IST).strftime("%Y-%m-%d")
    best_mm = best_pr = 0.0
    hrs = []
    for i, t in enumerate(h["time"]):
        if not t.startswith(today):
            continue
        hh = t[11:16]
        if start <= hh <= end:
            mm = h["precipitation"][i] or 0
            pr = h["precipitation_probability"][i] or 0
            best_mm = max(best_mm, mm)
            best_pr = max(best_pr, pr)
            if mm >= 0.1 or pr >= 30:
                hrs.append(f"{hh} {mm}mm/{pr}%")
    return best_mm, best_pr, hrs


import re


def send_ntfy(text, rainy):
    """Push via ntfy.sh — no account/token; user just subscribes to the topic."""
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        return False
    body = re.sub(r"<[^>]+>", "", text).encode("utf-8")   # ntfy body is plain text
    req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=body, headers={
        "Title": "Commute rain alert",
        "Priority": "high" if rainy else "default",
        "Tags": "umbrella,rain_cloud" if rainy else "sunny",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        ok = r.status < 300
    print("ntfy sent:", ok, file=sys.stderr)
    return ok


def resolve_chat_id(tok):
    """If TELEGRAM_CHAT_ID isn't set, find it from the bot's recent chats
    (the user just has to have messaged the bot once)."""
    try:
        with urllib.request.urlopen(
                f"https://api.telegram.org/bot{tok}/getUpdates", timeout=20) as r:
            d = json.loads(r.read())
        for u in reversed(d.get("result", [])):
            m = u.get("message") or u.get("edited_message") or u.get("channel_post") or {}
            cid = (m.get("chat") or {}).get("id")
            if cid is not None:
                return str(cid)
    except Exception as e:  # noqa: BLE001
        print("chat-id auto-resolve failed:", e, file=sys.stderr)
    return ""


def send_telegram(text):
    tok = "".join(os.environ.get("TELEGRAM_BOT_TOKEN", "").split())   # tokens have no spaces; kill stray paste whitespace
    chat = "".join(os.environ.get("TELEGRAM_CHAT_ID", "").split())
    if not tok:
        return False
    if not chat:                                   # only the token secret is needed
        chat = resolve_chat_id(tok)
        if chat:
            print(f"auto-resolved TELEGRAM_CHAT_ID={chat} — add it as a secret to make it permanent",
                  file=sys.stderr)
    if not chat:
        print("have token but no chat id (message the bot, then retry)", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat, "text": text,
                                   "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=30) as r:
        ok = json.loads(r.read()).get("ok", False)
    print("telegram sent:", ok, file=sys.stderr)
    return ok


def notify(text, rainy):
    sent = False
    sent = send_ntfy(text, rainy) or sent
    sent = send_telegram(text) or sent
    if not sent:
        print("no NTFY_TOPIC / TELEGRAM secrets set — would have sent:\n" + text, file=sys.stderr)
    return sent


def main():
    mode = os.environ.get("ALERT_MODE", "auto")
    if mode == "auto":
        mode = "morning" if datetime.now(IST).hour < 14 else "evening"
    start, end, route = WINDOWS.get(mode, WINDOWS["morning"])

    lines, rainy = [], False
    for name, (lat, lon) in LOCS.items():
        try:
            mm, pr, hrs = window_rain(forecast(lat, lon), start, end)
        except Exception as e:  # noqa: BLE001
            print(f"{name}: forecast failed: {e}", file=sys.stderr)
            continue
        wet = mm >= RAIN_MM or pr >= RAIN_PROB
        rainy = rainy or wet
        icon = "🌧️" if wet else "🙂"
        detail = ("; ".join(hrs)) if hrs else "dry"
        lines.append(f"{icon} <b>{name}</b>: peak {mm}mm, {int(pr)}% — {detail}")

    header = f"☔ <b>Commute rain check</b> ({route}, {start}–{end} IST)"
    body = header + "\n" + "\n".join(lines)
    if rainy:
        body += "\n\n⚠️ Rain likely on this trip — carry rain gear / plan buffer."
        notify(body, True)
    elif os.environ.get("ALERT_ALWAYS") == "1":
        body += "\n\n✅ Looks dry for your commute."
        notify(body, False)
    else:
        print("no rain over threshold; not sending.\n" + body, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
