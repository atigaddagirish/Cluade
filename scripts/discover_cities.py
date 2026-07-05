#!/usr/bin/env python3
"""Discover IMD's city marker data source (ids, names, coords).

Runs on a GitHub runner. Fetches main.js (which builds the homepage Leaflet
map) plus any endpoints it references, and dumps everything to /tmp/disc/ for
inspection. One-off build aid, not part of the live relay.
"""
import os
import re
import urllib.request

UA = ("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36")

SEEDS = [
    "https://mausam.imd.gov.in/responsive/js/main.js",
    "https://mausam.imd.gov.in/responsive/js/cityForecast.js",
    "https://mausam.imd.gov.in/responsive/js/citywise.js",
    # common IMD marker/data endpoints (guesses to confirm/deny)
    "https://mausam.imd.gov.in/api/cityweather_api.php",
    "https://city.imd.gov.in/api/allcity.php",
    "https://mausam.imd.gov.in/responsive/allIndiaCityForecast.php",
    "https://mausam.imd.gov.in/responsive/citylist.php",
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def main():
    os.makedirs("/tmp/disc2", exist_ok=True)
    summary = []
    seen = set()

    def probe(url, depth=0):
        if url in seen or depth > 1:
            return
        seen.add(url)
        try:
            body = fetch(url)
        except Exception as e:  # noqa: BLE001
            summary.append(f"FAIL {url} -> {type(e).__name__}: {e}")
            return
        fname = f"/tmp/disc2/{re.sub(r'[^A-Za-z0-9]', '_', url)[-80:]}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(body)
        latlon = len(re.findall(r'\b\d{1,2}\.\d{2,}\s*,\s*\d{2,3}\.\d{2,}', body))
        ids = len(set(re.findall(r'id=(\d{4,6})', body)))
        php = sorted(set(re.findall(r'[A-Za-z0-9_./?=-]*\.php[A-Za-z0-9_?=&-]*', body)))
        summary.append(f"OK {url} len={len(body)} latlon_pairs={latlon} ids={ids}")
        for p in php[:25]:
            summary.append(f"    ref: {p}")
        # follow .php endpoints referenced by main.js one level deep
        if url.endswith("main.js"):
            for p in php:
                if any(k in p.lower() for k in ("city", "forecast", "marker", "station", "list")):
                    full = p if p.startswith("http") else \
                        "https://mausam.imd.gov.in/" + p.lstrip("./")
                    probe(full, depth + 1)

    for s in SEEDS:
        probe(s)

    text = "\n".join(summary)
    with open("/tmp/disc2/summary.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
