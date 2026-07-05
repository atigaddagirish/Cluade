#!/usr/bin/env python3
"""Find IMD's current satellite / radar image URLs.

The Maps tab hot-links a few IMD product images; IMD periodically renames the
paths, which breaks them. This runner-side probe (a) scrapes IMD's satellite &
radar pages for the <img> URLs they actually use now, and (b) HEAD/GET-tests a
list of candidate image URLs, reporting status + content-type + size so we can
pick the live ones. One-off build aid.
"""
import re
import sys
import urllib.request

UA = "Mozilla/5.0 (Linux; Android 14) Chrome/126.0 Mobile Safari/537.36"

PAGES = [
    "https://mausam.imd.gov.in/responsive/satellite.php",
    "https://mausam.imd.gov.in/responsive/hydroestimator.php",
    "https://mausam.imd.gov.in/responsive/satellite_hydro.php",
    "https://mausam.imd.gov.in/imd_latest/contents/satellite.php",
    "https://mausam.imd.gov.in/responsive/radar.php",
    "https://mausam.imd.gov.in/responsive/rainfallinformation.php",
]

CANDIDATE_IMAGES = [
    "https://mausam.imd.gov.in/Satellite/3Dasiasec_ir1.jpg",
    "https://mausam.imd.gov.in/Satellite/3Dasiasec_vis.jpg",
    "https://mausam.imd.gov.in/Radar/caz_hyd.gif",
    # candidate satellite-rainfall product names
    "https://mausam.imd.gov.in/Satellite/3Dasiasec_imr.jpg",
    "https://mausam.imd.gov.in/Satellite/3Dimg_imr.jpg",
    "https://mausam.imd.gov.in/Satellite/3Dasiasec_hemin.jpg",
    "https://mausam.imd.gov.in/Satellite/3Dasiasec_rain.jpg",
    # observed (gauge) rainfall maps
    "https://mausam.imd.gov.in/Rainfall/SUBDIVISION_RAINFALL_MAP_COUNTRY_INDIA_cd.JPG",
    "https://mausam.imd.gov.in/Satellite/Converted/IR1.gif",
    # MOSDAC INSAT hydro-estimator (satellite rainfall)
    "https://www.mosdac.gov.in/look/3D_IMG/gis/3DIMG_HEM.jpg",
]


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace"), r.geturl()


def test_image(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                 "Referer": "https://mausam.imd.gov.in/"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read(200000)
            return f"{r.status} {r.headers.get('Content-Type','?')} {len(body)}B"
    except Exception as e:  # noqa: BLE001
        return f"ERR {type(e).__name__}: {e}"


def main():
    print("=== PAGES: <img>/background image URLs found ===")
    for url in PAGES:
        try:
            html, final = fetch_text(url)
        except Exception as e:  # noqa: BLE001
            print(f"[page] {url} -> FAIL {type(e).__name__}: {e}")
            continue
        imgs = set(re.findall(r'(?:src|href)=["\']([^"\']+\.(?:jpg|jpeg|png|gif))["\']', html, re.I))
        # also catch JS-referenced image paths
        imgs |= set(re.findall(r'["\']([^"\']*(?:hem|ir1|vis|imgr|caz|radar)[^"\']*\.(?:jpg|png|gif))["\']', html, re.I))
        rel = sorted(i for i in imgs if any(k in i.lower()
                     for k in ("hem", "ir", "vis", "sat", "caz", "radar", "3d")))
        print(f"\n[page] {url}  (len={len(html)}) matches={len(rel)}")
        for i in rel[:25]:
            print("   ", i)

    print("\n=== CANDIDATE IMAGE URLS ===")
    for url in CANDIDATE_IMAGES:
        print(f"  {test_image(url):45s}  {url}")


if __name__ == "__main__":
    sys.exit(main())
