#!/usr/bin/env python3
"""Discover IMD's city/station list source (ids, names, and coords if present).

Runs on a GitHub runner (open internet). Dumps each candidate source to
/tmp/disc/ so we can see which one carries the full forecast-city list and
whether coordinates are embedded. Output is published to the weather-data
branch for inspection; this script is a one-off build aid, not part of the
live relay.
"""
import os
import re
import urllib.request

UA = ("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36")

CANDIDATES = [
    "https://city.imd.gov.in/citywx/city_weather.php",
    "https://city.imd.gov.in/citywx/city_weather_test_try.php?id=43213",
    "https://city.imd.gov.in/",
    "https://mausam.imd.gov.in/imd_latest/contents/index_new.php",
    "https://mausam.imd.gov.in/",
    "https://city.imd.gov.in/api/citylist.php",
    "https://city.imd.gov.in/api/cityname.php",
    "https://mausam.imd.gov.in/api/citylist_api.php",
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def main():
    os.makedirs("/tmp/disc", exist_ok=True)
    summary = []
    for i, url in enumerate(CANDIDATES):
        try:
            body = fetch(url)
            # count <option value=..> pairs (dropdown of cities)
            opts = re.findall(r'<option[^>]*value=["\']?(\d+)["\']?[^>]*>([^<]+)</option>',
                              body, re.I)
            has_latlon = bool(re.search(r'lat[\'"]?\s*[:=]\s*[-\d.]+', body, re.I))
            fname = f"/tmp/disc/cand_{i}.txt"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(body)
            line = f"[{i}] OK {url} len={len(body)} options={len(opts)} latlon={has_latlon}"
            if opts[:5]:
                line += " sample=" + "; ".join(f"{v}={n.strip()}" for v, n in opts[:5])
            summary.append(line)
        except Exception as e:  # noqa: BLE001
            summary.append(f"[{i}] FAIL {url} -> {type(e).__name__}: {e}")
    text = "\n".join(summary)
    with open("/tmp/disc/summary.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
