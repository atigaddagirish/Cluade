#!/usr/bin/env python3
"""Diagnostic probe: which IMD endpoints are still publicly reachable, and how.

Run in GitHub Actions (open internet) via imd-probe.yml. Prints one line per
attempt: status, content-type, and a body snippet — enough to decide whether
the relay can work without an api.imd.gov.in key, needs specific headers, or
must scrape the public HTML pages instead.
"""
import json
import urllib.request
import urllib.error

BROWSER_UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36")

CASES = [
    # (label, url, extra headers)
    ("legacy current plain",
     "https://mausam.imd.gov.in/api/current_wx_api.php?id=43213", {}),
    ("legacy current +referer",
     "https://mausam.imd.gov.in/api/current_wx_api.php?id=43213",
     {"Referer": "https://mausam.imd.gov.in/", "Origin": "https://mausam.imd.gov.in"}),
    ("legacy current +xhr",
     "https://mausam.imd.gov.in/api/current_wx_api.php?id=43213",
     {"Referer": "https://mausam.imd.gov.in/imd_latest/contents/index_new.php",
      "X-Requested-With": "XMLHttpRequest"}),
    ("legacy cityweather plain",
     "https://city.imd.gov.in/api/cityweather.php?id=43213", {}),
    ("legacy cityweather +referer",
     "https://city.imd.gov.in/api/cityweather.php?id=43213",
     {"Referer": "https://city.imd.gov.in/citywx/citywxnew.php?id=43213"}),
    ("legacy cityweather_loc",
     "https://city.imd.gov.in/api/cityweather_loc.php?lat=16.0879&lon=78.0999", {}),
    ("legacy nowcast station",
     "https://mausam.imd.gov.in/api/nowcastapi.php?id=43213", {}),
    ("city HTML page (scrape fallback?)",
     "https://city.imd.gov.in/citywx/city_weather_test_try.php?id=43213", {}),
    ("citywxnew HTML page",
     "https://city.imd.gov.in/citywx/citywxnew.php?id=43213", {}),
    ("new gateway current_wx no key",
     "https://api.imd.gov.in/api/v1/current_wx?id=43213", {}),
    ("new gateway root",
     "https://api.imd.gov.in/public/api_reference.html", {}),
    ("aws district rainfall (hydromet)",
     "https://city.imd.gov.in/api/districtwise_rainfall_api.php", {}),
    ("mausam warnings api",
     "https://mausam.imd.gov.in/api/warnings_district_api.php?id=1", {}),
]


def probe(label, url, extra):
    headers = {"User-Agent": BROWSER_UA, "Accept": "application/json, text/html;q=0.9"}
    headers.update(extra)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read(120000)
            ct = r.headers.get("Content-Type", "?")
            cors = r.headers.get("Access-Control-Allow-Origin", "-")
            snip = body[:220].decode("utf-8", errors="replace").replace("\n", " ")
            kind = "?"
            try:
                json.loads(body.decode("utf-8", errors="replace"))
                kind = "JSON"
            except Exception:
                kind = "HTML/other"
            print(f"[{label}] {r.status} ct={ct} cors={cors} kind={kind} len={len(body)}")
            print(f"    body: {snip}")
    except urllib.error.HTTPError as e:
        hdr = {k: v for k, v in e.headers.items()
               if k.lower() in ("www-authenticate", "content-type", "server",
                                 "access-control-allow-origin")}
        snip = e.read(200).decode("utf-8", errors="replace").replace("\n", " ")
        print(f"[{label}] HTTP {e.code} hdrs={hdr}")
        print(f"    body: {snip}")
    except Exception as e:  # noqa: BLE001 - probe reports every failure mode
        print(f"[{label}] EXC {type(e).__name__}: {e}")


if __name__ == "__main__":
    for label, url, extra in CASES:
        probe(label, url, extra)
