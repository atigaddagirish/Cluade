#!/usr/bin/env python3
"""Fetch official IMD weather JSON for the solar site and write a relay file.

Run by .github/workflows/imd-weather.yml every 30 min; the output (imd.json)
is force-pushed to the orphan branch `weather-data`, from where weather.html
reads it via raw.githubusercontent.com (which sends CORS *) whenever the
phone cannot reach IMD's servers directly.

All data originates from India Meteorological Department public services:
  mausam.imd.gov.in / city.imd.gov.in
No API key required for these legacy endpoints; the newer gated gateway is
api.imd.gov.in (registered access) if IMD ever retires these.

Usage: fetch_imd.py [--station 43213] [--city 43213] [--district ID] [--out imd.json]
Exit code is 0 if at least one source succeeded, 1 if all failed.
"""
import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone

UA = "Mozilla/5.0 (weather-relay; +https://github.com/atigaddagirish/Cluade)"
TIMEOUT = 30


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = r.read().decode("utf-8", errors="replace")
    return json.loads(body)


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
    urls = {
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

    any_ok = False
    for name, url in urls.items():
        entry = {"url": url}
        try:
            entry["data"] = get_json(url)
            entry["ok"] = True
            any_ok = True
        except Exception as e:  # noqa: BLE001 - relay must record any failure and continue
            entry["ok"] = False
            entry["error"] = f"{type(e).__name__}: {e}"
        doc["sources"][name] = entry
        print(f"{name}: {'OK' if entry['ok'] else 'FAIL - ' + entry['error']}", file=sys.stderr)

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"wrote {a.out}", file=sys.stderr)
    return 0 if any_ok else 1


if __name__ == "__main__":
    sys.exit(main())
