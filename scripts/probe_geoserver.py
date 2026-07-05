#!/usr/bin/env python3
"""Probe IMD's GeoServer WFS layers: coverage, fields (rainfall?), CORS headers.

The homepage map (mausam.imd.gov.in) loads live station data from
reactjs.imd.gov.in/geoserver. If these layers are CORS-open, the phone can
fetch them directly (official IMD, any coordinate, no proxy, no key).
One-off build aid.
"""
import json
import urllib.request

UA = "Mozilla/5.0 (Linux; Android 14) Chrome/126.0 Mobile Safari/537.36"
BASE = ("https://reactjs.imd.gov.in/geoserver/imd/ows?service=WFS&version=1.0.0"
        "&request=GetFeature&typeName=imd:{layer}&outputFormat=application/json")

LAYERS = ["aws_data_layer", "synop_data_layer", "metar_data_layer",
          "city_forecast_layer", "district_nowcast_layer", "rainfall_data_layer"]


def main():
    # list all available layers first
    cap = ("https://reactjs.imd.gov.in/geoserver/imd/ows?service=WFS&version=2.0.0"
           "&request=GetCapabilities")
    try:
        req = urllib.request.Request(cap, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=40) as r:
            caps = r.read().decode("utf-8", errors="replace")
        import re
        names = sorted(set(re.findall(r"<Name>(imd:[^<]+)</Name>", caps)))
        print("=== available imd layers ===")
        for n in names:
            print("  ", n)
    except Exception as e:  # noqa: BLE001
        print(f"GetCapabilities FAIL: {type(e).__name__}: {e}")

    for layer in LAYERS:
        url = BASE.format(layer=layer)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                         "Origin": "https://atigaddagirish.github.io"})
            with urllib.request.urlopen(req, timeout=40) as r:
                acao = r.headers.get("Access-Control-Allow-Origin", "<none>")
                body = r.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            feats = data.get("features", [])
            props = sorted(feats[0]["properties"].keys()) if feats else []
            geom = feats[0]["geometry"] if feats else None
            print(f"\n=== {layer} ===")
            print(f"  CORS Access-Control-Allow-Origin: {acao}")
            print(f"  features: {len(feats)}")
            print(f"  geometry sample: {json.dumps(geom)[:90] if geom else None}")
            print(f"  properties: {props}")
            if feats:
                print(f"  first feature props: {json.dumps(feats[0]['properties'])[:400]}")
        except Exception as e:  # noqa: BLE001
            print(f"\n=== {layer} === FAIL: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
