#!/usr/bin/env python3
"""Fetch IMD GeoServer station + warning layers → compact CORS-open stations.json.

One WFS fetch returns every station in India (with coordinates), so the phone
can find the nearest station to ANY typed coordinate after downloading this
once. Data © India Meteorological Department (reactjs.imd.gov.in/geoserver).

Emits arrays (not objects) per station to keep the payload small. Also dumps
the warning layers' field names to stderr so they can be wired precisely.
"""
import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone

UA = "Mozilla/5.0 (Linux; Android 14) Chrome/126.0 Mobile Safari/537.36"
WFS = ("https://reactjs.imd.gov.in/geoserver/imd/ows?service=WFS&version=1.0.0"
       "&request=GetFeature&typeName=imd:{layer}&outputFormat=application/json")
TIMEOUT = 60


def get_layer(layer):
    req = urllib.request.Request(WFS.format(layer=layer), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def num(v):
    """Return a rounded float for a numeric-ish value, else None."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.upper() in ("NULL", "NA", "NIL", "NONE"):
        return None
    try:
        return round(float(s), 1)
    except ValueError:
        return None


def coords(feat):
    g = feat.get("geometry") or {}
    c = g.get("coordinates")
    if c and len(c) >= 2:
        try:
            return round(float(c[1]), 3), round(float(c[0]), 3)  # lat, lon
        except (TypeError, ValueError):
            return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="stations.json")
    a = ap.parse_args()

    doc = {
        "fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "attribution": "Data (c) India Meteorological Department, Ministry of Earth Sciences",
        "source": "reactjs.imd.gov.in/geoserver (WFS)",
        # column legend for the compact arrays below
        "aws_cols": ["lat", "lon", "name", "rain_mm", "temp_c", "rh_pct", "wind_kmph"],
        "synop_cols": ["lat", "lon", "id", "rain24_mm", "temp_c", "rh_pct"],
        "aws": [], "synop": [], "warnings": [], "ok": {},
    }

    # AWS: dense network, per-station rainfall + temp
    try:
        fc = get_layer("aws_data_layer")
        for f in fc.get("features", []):
            ll = coords(f)
            if not ll:
                continue
            p = f["properties"]
            doc["aws"].append([ll[0], ll[1], (p.get("station") or "").strip(),
                               num(p.get("rainfall")), num(p.get("temp")),
                               num(p.get("rh")), num(p.get("windspeed"))])
        doc["ok"]["aws"] = len(doc["aws"])
    except Exception as e:  # noqa: BLE001
        doc["ok"]["aws"] = f"FAIL {type(e).__name__}: {e}"

    # SYNOP: authoritative 24-hour rainfall
    try:
        fc = get_layer("synop_data_layer")
        for f in fc.get("features", []):
            ll = coords(f)
            if not ll:
                continue
            p = f["properties"]
            doc["synop"].append([ll[0], ll[1], p.get("station_id"),
                                 num(p.get("24hrlyrain")), num(p.get("dbtemp")),
                                 num(p.get("rh"))])
        doc["ok"]["synop"] = len(doc["synop"])
    except Exception as e:  # noqa: BLE001
        doc["ok"]["synop"] = f"FAIL {type(e).__name__}: {e}"

    # Nowcast warnings (next ~3 h) from the station layer (point geometry so
    # "nearest warning to me" works). Keep only ACTIVE ones (Color > 1) — most
    # of the 1219 stations are green/no-warning and would just bloat the file.
    # Color: 1=green(none) 2=yellow(watch) 3=orange(alert) 4=red(warning).
    doc["warn_cols"] = ["lat", "lon", "station", "color", "active_cats", "msg", "valid_upto"]
    try:
        fc = get_layer("NowcastWarningStation")
        for f in fc.get("features", []):
            p = f["properties"]
            color = p.get("Color")
            try:
                color = int(color)
            except (TypeError, ValueError):
                color = 0
            if color <= 1:
                continue
            ll = coords(f)
            if not ll:
                continue
            cats = [i for i in range(1, 20)
                    if str(p.get(f"cat{i}", "")).strip() in ("1", "1.0")]
            doc["warnings"].append([ll[0], ll[1], (p.get("Station") or "").strip(),
                                    color, cats, (p.get("message") or "").strip(),
                                    (p.get("vupto") or "").strip()])
        doc["ok"]["warnings"] = len(doc["warnings"])
    except Exception as e:  # noqa: BLE001
        doc["ok"]["warnings"] = f"FAIL {type(e).__name__}: {e}"

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    import os
    print(f"wrote {a.out} ok={doc['ok']} warnings={len(doc['warnings'])} "
          f"bytes={os.path.getsize(a.out)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
