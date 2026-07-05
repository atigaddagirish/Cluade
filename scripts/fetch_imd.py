#!/usr/bin/env python3
"""Fetch official IMD weather data for the solar site and write a relay file.

Run by .github/workflows/imd-weather.yml every 30 min; the output (imd.json)
is force-pushed to the orphan branch `weather-data`, from where weather.html
reads it via raw.githubusercontent.com (CORS-open).

Data sources, in order of preference per section:
  1. IMD legacy JSON APIs (mausam.imd.gov.in / city.imd.gov.in/api) — since
     mid-2026 these return 401 "IP needs to be whitelisted" to the public.
     Still tried first so the relay self-heals if IMD reopens them.
  2. IMD new gateway (api.imd.gov.in) — used only if IMD_API_KEY env is set
     (free registration at api.imd.gov.in).
  3. The public city weather page city.imd.gov.in/citywx/citywxnew.php —
     openly served HTML carrying the same official data (past-24 h obs incl.
     rainfall + 7-day forecast); parsed into the same record shapes the
     widget expects.

All data originates from the India Meteorological Department.

Usage: fetch_imd.py [--station 43213] [--city 43213] [--district ID] [--out imd.json]
Exit code is 0 if at least one source succeeded, 1 if all failed.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

UA = ("Mozilla/5.0 (Linux; Android 14; weather-relay "
      "+https://github.com/atigaddagirish/Cluade) Chrome/126.0")
TIMEOUT = 30


def http_get(url, accept="application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace")


def get_json(url):
    return json.loads(http_get(url))


# ---------- citywx HTML scraper ----------

TAG_RE = re.compile(r"<[^>]+>")
DATE_RE = re.compile(r"^\d{1,2}-[A-Za-z]{3}$")


def strip_tags(html):
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", html)).strip()


def scrape_citywx(city_id):
    """Parse city.imd.gov.in/citywx/citywxnew.php into widget-ready records.

    Returns (current_record_list, forecast_record_list).
    """
    html = http_get(f"https://city.imd.gov.in/citywx/citywxnew.php?id={city_id}",
                    accept="text/html")

    m = re.search(r"Forecast For:\s*</b>\s*<FONT[^>]*>([^<]+)</Font>", html, re.I)
    station = m.group(1).strip() if m else str(city_id)
    m = re.search(r"Dated\s*:\s*([^<]+)<", html)
    dated = m.group(1).strip() if m else ""

    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I)
    kv = {}        # past-24h observation label -> value
    forecast = []  # one record per forecast day
    for row in rows:
        cells = [strip_tags(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)]
        cells_nonempty = [c for c in cells if c]
        if len(cells) == 2 and cells[0] and len(cells[0]) > 3:
            kv[cells[0]] = cells[1]
        elif len(cells) >= 4 and cells_nonempty and DATE_RE.match(cells_nonempty[0]):
            c = cells_nonempty
            forecast.append({
                "Date": c[0],
                "Min_Temp_C": c[1] if len(c) > 1 else "",
                "Max_Temp_C": c[2] if len(c) > 2 else "",
                "Weather_Forecast": c[-1] if len(c) > 3 else "",
            })

    def find(label_re):
        for k, v in kv.items():
            if re.search(label_re, k, re.I):
                return v
        return ""

    current = {
        "Station Name": station,
        "Date of Observation": dated,
        "Past 24 hrs Rainfall (mm)": find(r"rain"),
        "Maximum Temp (C)": find(r"^Maximum Temp"),
        "Minimum Temp (C)": find(r"^Minimum Temp"),
        "Relative Humidity at 0830 IST (%)": find(r"R\.?H\.? at 0830"),
        "Relative Humidity at 1730 IST (%)": find(r"R\.?H\.? at 1730"),
        "Sunset (IST)": find(r"sunset"),
        "Sunrise (IST)": find(r"sunrise"),
        "Todays Forecast": forecast[0]["Weather_Forecast"] if forecast else "",
        "Source": "IMD public city weather page (citywxnew.php)",
    }
    current = {k: v for k, v in current.items() if v != ""}
    if not forecast and len(current) <= 2:
        raise ValueError("citywx page parsed but no data found — layout changed?")
    return [current], forecast


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", default="43213")   # Kurnool obs station (nearest to site)
    ap.add_argument("--city", default="43213")      # Kurnool 7-day city forecast
    ap.add_argument("--district", default="")       # Jogulamba Gadwal nowcast district id (optional)
    ap.add_argument("--out", default="imd.json")
    a = ap.parse_args()

    nowcast_url = (
        f"https://mausam.imd.gov.in/api/nowcast_district_api.php?id={a.district}"
        if a.district
        else f"https://mausam.imd.gov.in/api/nowcastapi.php?id={a.station}"
    )
    api_urls = {
        "current": f"https://mausam.imd.gov.in/api/current_wx_api.php?id={a.station}",
        "forecast": f"https://city.imd.gov.in/api/cityweather.php?id={a.city}",
        "nowcast": nowcast_url,
    }

    doc = {
        "fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "site": {"lat": 16.08790535475237, "lon": 78.09998163768542,
                 "note": "Jogulamba Gadwal (TG); nearest IMD station Kurnool 43213"},
        "attribution": "Data (c) India Meteorological Department, Ministry of Earth Sciences, Govt. of India",
        "sources": {},
    }

    # 1) legacy JSON APIs (IP-whitelisted since mid-2026; kept for self-healing)
    for name, url in api_urls.items():
        entry = {"url": url}
        try:
            entry["data"] = get_json(url)
            entry["ok"] = True
        except Exception as e:  # noqa: BLE001 - relay must record any failure and continue
            entry["ok"] = False
            entry["error"] = f"{type(e).__name__}: {e}"
        doc["sources"][name] = entry
        print(f"api {name}: {'OK' if entry['ok'] else 'FAIL - ' + entry['error']}", file=sys.stderr)

    # 2) new gateway, only with a key (register at api.imd.gov.in)
    api_key = os.environ.get("IMD_API_KEY", "").strip()
    if api_key and not doc["sources"]["current"]["ok"]:
        url = f"https://api.imd.gov.in/api/v1/current_wx?id={a.station}&apikey={api_key}"
        try:
            data = get_json(url)
            doc["sources"]["current"] = {"url": url.replace(api_key, "***"),
                                         "ok": True, "data": data, "via": "api.imd.gov.in"}
            print("gateway current: OK", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"gateway current: FAIL - {type(e).__name__}: {e}", file=sys.stderr)

    # 3) public city weather page — fills whatever the APIs could not
    if not (doc["sources"]["current"]["ok"] and doc["sources"]["forecast"]["ok"]):
        scrape_url = f"https://city.imd.gov.in/citywx/citywxnew.php?id={a.city}"
        try:
            cur, fc = scrape_citywx(a.city)
            if not doc["sources"]["current"]["ok"]:
                doc["sources"]["current"] = {"url": scrape_url, "ok": True, "data": cur,
                                             "via": "public city page (HTML)"}
            if not doc["sources"]["forecast"]["ok"] and fc:
                doc["sources"]["forecast"] = {"url": scrape_url, "ok": True, "data": fc,
                                              "via": "public city page (HTML)"}
            print(f"scrape citywx: OK ({len(fc)} forecast days)", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"scrape citywx: FAIL - {type(e).__name__}: {e}", file=sys.stderr)

    any_ok = any(s.get("ok") for s in doc["sources"].values())
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"wrote {a.out}", file=sys.stderr)
    return 0 if any_ok else 1


if __name__ == "__main__":
    sys.exit(main())
