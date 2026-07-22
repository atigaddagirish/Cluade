#!/usr/bin/env python3
"""Commute rain alerts for Weather Watch — sends a Telegram message if rain is
likely for the user's trip windows (Manikonda <-> Office, ~50 min travel).

Runs from GitHub Actions cron (see .github/workflows/rain-alert.yml). Uses the
free Open-Meteo forecast (ECMWF/GFS), which is reachable from cloud IPs (unlike
IMD/Telangana). Only sends a message when rain crosses the threshold, so it does
not spam — set ALERT_ALWAYS=1 to also get an "all clear" note.

Tuned for a BIKE rider carrying a laptop: sensitive thresholds (a drizzle can
wet the bag), a lead-time hint ("dry until ~HH:MM — leave before then"), and a
clear protect-the-bag verdict.

Secrets/env:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  (Telegram) and/or NTFY_TOPIC (ntfy push)
  ALERT_MODE = morning | evening | auto  (auto picks by current IST hour)
  WET_MM=0.2  WET_PROB=40    "carry a cover" bar
  HEAVY_MM=2.0 HEAVY_PROB=70 "protect the bag / rethink" bar
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

# Trip windows in IST, widened for buffer (leave a bit early/late + ~50 min ride).
WINDOWS = {
    "morning": ("09:15", "10:45", "Manikonda → Office"),
    "evening": ("18:15", "19:45", "Office → Manikonda"),
}
# Thresholds tuned for a BIKE rider carrying a laptop → be sensitive (even a
# drizzle can wet the bag). WET = worth a rain cover; HEAVY = protect it / rethink.
WET_MM = float(os.environ.get("WET_MM", "0.2"))
WET_PROB = float(os.environ.get("WET_PROB", "40"))
HVY_MM = float(os.environ.get("HEAVY_MM", "2.0"))
HVY_PROB = float(os.environ.get("HEAVY_PROB", "70"))


def is_wet(mm, pr):
    return mm >= WET_MM or pr >= WET_PROB


def is_heavy(mm, pr):
    return mm >= HVY_MM or pr >= HVY_PROB


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def forecast(lat, lon):
    url = ("https://api.open-meteo.com/v1/forecast?"
           f"latitude={lat}&longitude={lon}&timezone=Asia%2FKolkata"
           "&hourly=precipitation,precipitation_probability,weathercode"
           "&minutely_15=precipitation&forecast_days=2")
    return get(url)


def window_series(fc, start, end):
    """Return [(hh:mm, mm, prob%), …] over today's [start,end] IST, at 15-min
    resolution when available (minutely_15 precip + that hour's probability),
    else hourly."""
    today = datetime.now(IST).strftime("%Y-%m-%d")
    h = fc.get("hourly", {})
    hour_pr, hour_mm = {}, {}
    for i, t in enumerate(h.get("time", [])):
        if t.startswith(today):
            hour_pr[t[11:13]] = h["precipitation_probability"][i] or 0
            hour_mm[t[11:13]] = h["precipitation"][i] or 0
    out = []
    m = fc.get("minutely_15") or {}
    if m.get("time"):
        for i, t in enumerate(m["time"]):
            if t.startswith(today) and start <= t[11:16] <= end:
                out.append((t[11:16], m["precipitation"][i] or 0, hour_pr.get(t[11:13], 0)))
    else:
        for i, t in enumerate(h.get("time", [])):
            if t.startswith(today) and start <= t[11:16] <= end:
                out.append((t[11:16], h["precipitation"][i] or 0, h["precipitation_probability"][i] or 0))
    return out


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

    lines = []
    overall = "dry"          # dry < wet < heavy
    first_wet = None         # earliest time rain crosses the wet bar (any location)
    for name, (lat, lon) in LOCS.items():
        try:
            series = window_series(forecast(lat, lon), start, end)
        except Exception as e:  # noqa: BLE001
            print(f"{name}: forecast failed: {e}", file=sys.stderr)
            continue
        peak_mm = max((mm for _, mm, _ in series), default=0.0)
        peak_pr = max((pr for _, _, pr in series), default=0.0)
        wet_hits = [hm for hm, mm, pr in series if is_wet(mm, pr)]
        level = ("heavy" if any(is_heavy(mm, pr) for _, mm, pr in series)
                 else "wet" if wet_hits else "dry")
        if level == "heavy" or (level == "wet" and overall != "heavy"):
            overall = level if level == "heavy" else ("wet" if overall == "dry" else overall)
        if wet_hits:
            t0 = wet_hits[0]
            first_wet = t0 if first_wet is None else min(first_wet, t0)
        icon = {"heavy": "🔴", "wet": "🟠", "dry": "🟢"}[level]
        when = f", from ~{wet_hits[0]}" if wet_hits else ""
        tail = "dry" if level == "dry" else f"{round(peak_mm, 1)}mm / {int(peak_pr)}%{when}"
        lines.append(f"{icon} <b>{name}</b>: {tail}")

    header = f"🏍️ <b>Bike commute — {route}</b> ({start}–{end} IST)"
    body = header + "\n" + "\n".join(lines)

    # lead-time hint
    if first_wet and first_wet > start:
        body += f"\n\n🕒 Dry until ~{first_wet} — leave before then to beat it."
    elif first_wet:
        body += f"\n\n🕒 Rain around from the start of your window (~{first_wet})."

    if overall == "heavy":
        body += ("\n🔴 <b>Protect the bag</b> — rain likely on the ride. Use a waterproof "
                 "cover / line the bag, or take a cab / wait it out.")
        notify(body, True)
    elif overall == "wet":
        body += ("\n🟠 <b>Rain possible</b> — carry a rain cover for the laptop bag "
                 "and keep an eye on the sky.")
        notify(body, True)
    elif os.environ.get("ALERT_ALWAYS") == "1":
        body += "\n🟢 <b>Looks dry</b> — good to ride."
        notify(body, False)
    else:
        print("no rain over threshold; not sending.\n" + body, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
