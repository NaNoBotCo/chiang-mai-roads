#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""harvest_osm.py — every road, lane and alley OpenStreetMap holds for Chiang Mai.

Three verbs, each writing one harvest file under data/harvest/. A harvest file is never a
record: it carries the licence (ODbL 1.0, share-alike), the fetch time and the query, so
an absence reads as "not in OSM on that date" rather than "not there".

  --city     every highway=* way inside the city box, tiled, with geometry -> osm-city.json
  --region   motorway/trunk/primary/secondary across the province and the roads out to
             Lampang, Lamphun, Chiang Rai, Mae Hong Son, Fang -> osm-region.json
  --places   wats, gates, markets, schools, hospitals, the moat and the canals, traffic
             signals, bridges, parking -> osm-places.json
  --all      all of the above

Raw tile replies are cached under data/harvest/_raw/ so a rebuild never refetches.

    python3 tools/harvest_osm.py --all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HARVEST, jdump, jload  # noqa: E402

UA = "chiang-mai-roads-build/0.1 (https://wichaa.net; nan@motdang.net) python-urllib"
ENDPOINTS = ["https://overpass-api.de/api/interpreter",
             "https://overpass.kumi.systems/api/interpreter",
             "https://overpass.private.coffee/api/interpreter"]

# The city box: the whole of the outer ring road (Route 121) and a margin, Mae Rim in the
# north to Hang Dong and Saraphi in the south, Doi Suthep's foot in the west to San
# Kamphaeng in the east.  S, W, N, E
CITY = (18.66, 98.86, 18.92, 99.10)
# The region box: the province's middle and the roads out. Lampang and Chiang Rai lie
# outside it; those roads are fetched by ref instead.
REGION = (18.20, 98.40, 19.40, 99.40)

RAW = HARVEST / "_raw"

CITY_KEEP = ("highway", "name", "name:en", "name:th", "alt_name", "ref", "oneway", "lanes",
             "maxspeed", "surface", "lit", "width", "bridge", "tunnel", "layer", "junction",
             "construction", "start_date", "opening_date", "check_date", "sidewalk",
             "cycleway", "access", "motor_vehicle", "service", "living_street",
             "destination", "old_name", "official_name", "wikidata", "wikipedia",
             "toll", "expressway", "motorroad", "smoothness", "tracktype", "operator")

PLACE_KINDS = [
    ("wat",      'nwr["amenity"="place_of_worship"]["religion"="buddhist"]'),
    ("gate",     'nwr["historic"~"^(city_gate|citywalls|wall|fort|ruins)$"]'),
    ("gate",     'nwr["barrier"="city_wall"]'),
    ("moat",     'way["waterway"~"^(moat|canal|river|stream|ditch)$"]'),
    ("moat",     'way["natural"="water"]["water"="moat"]'),
    ("market",   'nwr["amenity"="marketplace"]'),
    ("school",   'nwr["amenity"~"^(school|university|college)$"]'),
    ("hospital", 'nwr["amenity"~"^(hospital|clinic)$"]'),
    ("signal",   'node["highway"="traffic_signals"]'),
    ("crossing", 'node["highway"="crossing"]'),
    ("bus_stop", 'node["highway"="bus_stop"]'),
    ("bus_station", 'nwr["amenity"="bus_station"]'),
    ("parking",  'nwr["amenity"="parking"]'),
    ("fuel",     'nwr["amenity"="fuel"]'),
    ("rail",     'way["railway"="rail"]'),
    ("station",  'nwr["railway"="station"]'),
    ("airport",  'nwr["aeroway"="aerodrome"]'),
    ("bridge",   'way["man_made"="bridge"]'),
    ("tree",     'node["natural"="tree"]'),
    ("place",    'node["place"~"^(city|town|village|suburb|neighbourhood|quarter)$"]'),
    ("landuse",  'way["landuse"~"^(residential|commercial|retail|industrial|farmland|orchard)$"]'),
]
PLACE_KEEP = ("name", "name:en", "name:th", "amenity", "historic", "barrier", "waterway",
              "natural", "water", "place", "religion", "railway", "aeroway", "landuse",
              "population", "wikidata", "wikipedia", "crossing", "bus", "parking",
              "capacity", "operator", "species", "man_made", "start_date", "description")


def overpass(query: str, tries: int = 3):
    err = None
    for i in range(tries):
        ep = ENDPOINTS[i % len(ENDPOINTS)]
        try:
            req = urllib.request.Request(ep, data=urllib.parse.urlencode({"data": query}).encode(),
                                         headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=240) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            err = e
            print(f"  {ep.split('/')[2]}: {e}; retrying", flush=True)
            time.sleep(10 + 10 * i)
    raise RuntimeError(f"Overpass failed: {err}")


def cached(query: str, label: str):
    RAW.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(query.encode()).hexdigest()[:12]
    f = RAW / f"{label}-{key}.json"
    if f.exists():
        return jload(f)
    t0 = time.time()
    d = overpass(query)
    d["_query"] = query
    d["_fetched"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    jdump(d, f, indent=0)
    print(f"  {label}: {len(d.get('elements', []))} elements in {time.time() - t0:.0f}s", flush=True)
    return d


def tiles(box, rows, cols):
    s, w, n, e = box
    dy, dx = (n - s) / rows, (e - w) / cols
    for r in range(rows):
        for c in range(cols):
            yield (round(s + r * dy, 4), round(w + c * dx, 4), round(s + (r + 1) * dy, 4), round(w + (c + 1) * dx, 4))


def way_row(el, keep):
    t = el.get("tags", {})
    row = {"id": el["id"], "tags": {k: v for k, v in t.items() if k in keep}}
    if "geometry" in el:
        row["pts"] = [[round(p["lat"], 6), round(p["lon"], 6)] for p in el["geometry"]]
        row["nodes"] = el.get("nodes", [])
    elif "lat" in el:
        row["lat"], row["lon"] = round(el["lat"], 6), round(el["lon"], 6)
    elif "center" in el:
        row["lat"], row["lon"] = round(el["center"]["lat"], 6), round(el["center"]["lon"], 6)
    row["kind_osm"] = el["type"]
    return row


def fetch_tile(t, label, ways, depth=0):
    """One tile; when the servers will not give it whole, four quarters, and so on. A
    dense tile that times out at 2.6 km on a side goes through at 1.3."""
    q = f'[out:json][timeout:150];way["highway"]({t[0]},{t[1]},{t[2]},{t[3]});out geom;'
    try:
        d = cached(q, label)
    except RuntimeError as e:
        if depth >= 2:
            raise
        print(f"  {label}: splitting after {e}", flush=True)
        for j, sub in enumerate(tiles(t, 2, 2)):
            fetch_tile(sub, f"{label}-{j}", ways, depth + 1)
        return
    for el in d["elements"]:
        if el["type"] == "way":
            ways[el["id"]] = way_row(el, CITY_KEEP)
    time.sleep(2)


def harvest_city():
    ways = {}
    for i, t in enumerate(tiles(CITY, 10, 10)):
        fetch_tile(t, f"city-{i:02d}", ways)
    out = {"licence": "ODbL 1.0", "attribution": "© OpenStreetMap contributors",
           "fetched": time.strftime("%Y-%m-%d"), "box": CITY, "count": len(ways),
           "ways": list(ways.values())}
    jdump(out, HARVEST / "osm-city.json", indent=0)
    print(f"osm-city.json: {len(ways)} ways", flush=True)


def fetch_sel(sel, box, label, ways, depth=0):
    """A selector over a box, split into quarters when the servers will not serve it."""
    q = f'[out:json][timeout:180];{sel}({box[0]},{box[1]},{box[2]},{box[3]});out geom;'
    try:
        d = cached(q, label)
    except RuntimeError as e:
        if depth >= 2:
            raise
        print(f"  {label}: splitting after {e}", flush=True)
        for j, sub in enumerate(tiles(box, 2, 2)):
            fetch_sel(sel, sub, f"{label}-{j}", ways, depth + 1)
        return
    for el in d["elements"]:
        if el["type"] == "way":
            ways[el["id"]] = way_row(el, CITY_KEEP)
    time.sleep(2)


def harvest_region():
    ways = {}
    major = ('way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|primary_link|'
             'secondary|secondary_link|construction)$"]')
    for i, t in enumerate(tiles(REGION, 2, 2)):
        fetch_sel(major, t, f"region-major-{i}", ways)
    # the roads out, by ref, to the neighbouring cities. Route 1 is a thousand
    # kilometres long and is not fetched; the region box already holds its Lampang end.
    OUT = (17.90, 97.90, 20.10, 100.00)
    for ref in ("11", "118", "107", "108", "1001", "1095", "106", "121", "1317", "1006", "1269", "1141"):
        fetch_sel(f'way["highway"]["ref"~"^{ref}$"]', OUT, f"ref-{ref}", ways)
    out = {"licence": "ODbL 1.0", "attribution": "© OpenStreetMap contributors",
           "fetched": time.strftime("%Y-%m-%d"), "box": REGION, "count": len(ways),
           "ways": list(ways.values())}
    jdump(out, HARVEST / "osm-region.json", indent=0)
    print(f"osm-region.json: {len(ways)} ways", flush=True)


def harvest_places():
    rows = []
    for kind, sel in PLACE_KINDS:
        box = CITY
        if kind in ("place", "airport", "rail", "station", "wat"):
            box = REGION
        q = f'[out:json][timeout:240];{sel}({box[0]},{box[1]},{box[2]},{box[3]});out center tags geom;'
        if kind in ("moat", "rail", "bridge", "landuse", "gate"):
            q = f'[out:json][timeout:240];{sel}({box[0]},{box[1]},{box[2]},{box[3]});out geom;'
        try:
            d = cached(q, f"place-{kind}-{sel[:12].replace(chr(34), '')}")
        except RuntimeError as e:
            print(f"  place {kind}: skipped after {e}", flush=True)
            continue
        for el in d["elements"]:
            r = way_row(el, PLACE_KEEP)
            r["kind"] = kind
            rows.append(r)
        time.sleep(2)
    out = {"licence": "ODbL 1.0", "attribution": "© OpenStreetMap contributors",
           "fetched": time.strftime("%Y-%m-%d"), "count": len(rows), "rows": rows}
    jdump(out, HARVEST / "osm-places.json", indent=0)
    print(f"osm-places.json: {len(rows)} rows", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", action="store_true")
    ap.add_argument("--region", action="store_true")
    ap.add_argument("--places", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.all or a.city:
        harvest_city()
    if a.all or a.region:
        harvest_region()
    if a.all or a.places:
        harvest_places()
