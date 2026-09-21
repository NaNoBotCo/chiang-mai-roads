#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measure.py — what the road network says about the city, counted from the harvest.

Reads data/harvest/osm-city.json and osm-places.json, writes data/harvest/measures.json.
Every figure the site prints about the network comes from here, with the method beside
it, so the page and the API cannot drift apart.

Zones. The old city is the square inside the moat. Outside it, the rings are taken as
distance from the moat's centre: to 3 km (the Superhighway and the canal road close a
ring at about that radius), 3 to 5.5 km (the middle ring), 5.5 to 9 km (the outer ring,
Route 121) and beyond. A radius is a stand-in for the road itself; the page says so.

Measures, per zone:
  km by class · intersections per km² · dead-end share · median block length ·
  orientation entropy (Boeing 2019, 36 bins) · one-way share · named share · soi share
Intersections, dead ends, blocks and orientation use the network proper — drivable ways
minus service lanes — so a car park's aisles do not count as streets.

    python3 tools/measure.py
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HARVEST, jdump, load_harvest  # noqa: E402

CENTRE = (18.7883, 98.9855)          # the moat square's middle, near Wat Chedi Luang
MOAT = (18.7808, 98.9775, 18.7962, 98.9938)   # S, W, N, E — the water's inner line
ZONES = [("moat", 0.0), ("ring1", 3.0), ("ring2", 5.5), ("ring3", 9.0), ("beyond", 99.0)]
ZONE_LABEL = {"moat": "inside the moat", "ring1": "moat to 3 km", "ring2": "3 to 5.5 km",
              "ring3": "5.5 to 9 km", "beyond": "past 9 km"}
BOX = (18.66, 98.86, 18.92, 99.10)   # the harvest box, S W N E; harvest_osm.CITY
ZONE_TH = {"moat": "ในเวียง", "ring1": "นอกคูเมืองถึง 3 กม.", "ring2": "3 ถึง 5.5 กม.",
           "ring3": "5.5 ถึง 9 กม.", "beyond": "เกิน 9 กม."}

DRIVE = ("motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
         "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
         "residential", "living_street", "service")
MAJOR = ("motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
         "secondary", "secondary_link")
LANE = ("residential", "living_street", "service", "unclassified")
# the street network proper: drivable ways minus service lanes (parking aisles and
# driveways), which is what OSMnx calls the drive network and what Boeing's roses use
NET = tuple(c for c in DRIVE if c != "service")
WALK = ("footway", "path", "pedestrian", "steps", "cycleway", "track")
CLASS_GROUP = {}
for c in MAJOR:
    CLASS_GROUP[c] = "major"
for c in ("tertiary", "tertiary_link"):
    CLASS_GROUP[c] = "tertiary"
for c in LANE:
    CLASS_GROUP[c] = "lane"
for c in WALK:
    CLASS_GROUP[c] = "walk"
CLASS_GROUP["construction"] = "construction"

SOI = re.compile(r"(^|\s)(ซอย|ซ\.|soi)\b", re.I)


def haversine(a, b) -> float:
    R = 6371.0088
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def bearing(a, b) -> float:
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1])
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def in_moat(p) -> bool:
    return MOAT[0] <= p[0] <= MOAT[2] and MOAT[1] <= p[1] <= MOAT[3]


def zone_of(p) -> str:
    if in_moat(p):
        return "moat"
    d = haversine(p, CENTRE)
    for z, r in ZONES[1:]:
        if d <= r:
            return z
    return "beyond"


def way_len(pts) -> float:
    return sum(haversine(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def midpoint(pts):
    return pts[len(pts) // 2]


def entropy(bins: list) -> dict:
    """Boeing's orientation entropy. 36 bins over 0–180° (a street runs both ways), each
    segment weighted by its length. phi = 1 - ((H - Hgrid) / (Hmax - Hgrid))²: 1 is a
    perfect grid, 0 is uniform in every direction."""
    total = sum(bins)
    if not total:
        return {"H": None, "phi": None}
    H = -sum((b / total) * math.log(b / total) for b in bins if b)
    n = len(bins)
    Hmax = math.log(n)
    Hgrid = math.log(4)
    phi = 1 - ((H - Hgrid) / (Hmax - Hgrid)) ** 2
    return {"H": round(H, 4), "phi": round(phi, 4), "Hmax": round(Hmax, 4), "Hgrid": round(Hgrid, 4)}


def zone_area_km2(z: str) -> float:
    if z == "moat":
        return haversine((MOAT[0], MOAT[1]), (MOAT[2], MOAT[1])) * haversine((MOAT[0], MOAT[1]), (MOAT[0], MOAT[3]))
    rs = dict(ZONES)
    order = [k for k, _ in ZONES]
    i = order.index(z)
    r_out = rs[z]
    r_in = rs[order[i - 1]] if i > 1 else 0.0
    if z == "beyond":
        # the harvest box, less the outer disc; the box is what was fetched
        bw = haversine((BOX[0], BOX[1]), (BOX[0], BOX[3])); bh = haversine((BOX[0], BOX[1]), (BOX[2], BOX[1]))
        return max(bw * bh - math.pi * r_in ** 2, 1.0)
    a = math.pi * (r_out ** 2 - r_in ** 2)
    if z == "ring1":
        a -= zone_area_km2("moat")
    return a


def place_point(r):
    """Where a place is. A wat is usually a polygon of temple grounds, not a node, so a
    row with geometry and no centre gets the mean of its points; counting only nodes
    missed four fifths of the wats."""
    if "lat" in r:
        return (r["lat"], r["lon"])
    pts = r.get("pts") or []
    if not pts:
        return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def segments_cross(a1, a2, b1, b2) -> bool:
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) > (q[1] - p[1]) * (r[0] - p[0])
    return ccw(a1, b1, b2) != ccw(a2, b1, b2) and ccw(a1, a2, b1) != ccw(a1, a2, b2)


def main() -> int:
    city = load_harvest("osm-city")
    places = load_harvest("osm-places") or {"rows": []}
    if not city:
        print("no osm-city harvest")
        return 1
    ways = city["ways"]
    box = city["box"]

    # ---- node degrees over drivable ways, for intersections and dead ends
    deg = Counter()
    node_pt = {}
    for w in ways:
        hw = w["tags"].get("highway")
        if hw not in NET or not w.get("nodes"):
            continue
        for nid, pt in zip(w["nodes"], w["pts"]):
            node_pt[nid] = pt
        nodes = w["nodes"]
        for i, nid in enumerate(nodes):
            deg[nid] += 2 if 0 < i < len(nodes) - 1 else 1
    # an end node shared by two ways is a continuation (degree 2), not an intersection
    inter = {n for n, d in deg.items() if d >= 3}
    edge_margin = 0.002
    dead = {n for n, d in deg.items() if d == 1 and not (
        abs(node_pt[n][0] - box[0]) < edge_margin or abs(node_pt[n][0] - box[2]) < edge_margin or
        abs(node_pt[n][1] - box[1]) < edge_margin or abs(node_pt[n][1] - box[3]) < edge_margin)}

    Z = {z: {"km": Counter(), "km_group": Counter(), "n_ways": 0, "inter": 0, "dead": 0,
             "bins": [0.0] * 36, "oneway_km": 0.0, "named_km": 0.0, "soi_km": 0.0,
             "drive_km": 0.0, "signals": 0, "wats": 0, "seg_km": [], "lit_km": 0.0,
             "lanes_km": Counter(), "surface_km": Counter()} for z, _ in ZONES}
    for n in inter:
        Z[zone_of(node_pt[n])]["inter"] += 1
    for n in dead:
        Z[zone_of(node_pt[n])]["dead"] += 1

    soi_names = defaultdict(float)
    name_km = defaultdict(float)
    construction = []
    bridges = []
    by_class_total = Counter()
    unnamed_lane_km = 0.0
    lane_km = 0.0
    tunnels = []
    longest_ways = []
    for w in ways:
        t = w["tags"]
        hw = t.get("highway")
        if not hw or not w.get("pts") or len(w["pts"]) < 2:
            continue
        pts = w["pts"]
        L = way_len(pts)
        z = zone_of(midpoint(pts))
        g = CLASS_GROUP.get(hw, "other")
        Z[z]["km"][hw] += L
        Z[z]["km_group"][g] += L
        Z[z]["n_ways"] += 1
        by_class_total[hw] += L
        name = t.get("name") or t.get("name:th") or t.get("name:en") or ""
        if hw == "construction":
            construction.append({"id": w["id"], "name": name, "construction": t.get("construction"),
                                 "km": round(L, 2), "opening_date": t.get("opening_date"),
                                 "start_date": t.get("start_date"), "zone": z,
                                 "lat": midpoint(pts)[0], "lon": midpoint(pts)[1]})
        if t.get("bridge") in ("yes", "viaduct") and hw in DRIVE:
            bridges.append({"id": w["id"], "name": name, "highway": hw, "km": round(L, 3),
                            "pts": pts, "zone": z, "layer": t.get("layer")})
        if t.get("tunnel") in ("yes", "building_passage") and hw in DRIVE:
            tunnels.append({"id": w["id"], "name": name, "highway": hw, "km": round(L, 3), "zone": z,
                            "lat": midpoint(pts)[0], "lon": midpoint(pts)[1]})
        if hw in DRIVE:
            Z[z]["drive_km"] += L
            if t.get("oneway") in ("yes", "-1"):
                Z[z]["oneway_km"] += L
            if name:
                Z[z]["named_km"] += L
                name_km[name] += L
            if t.get("lit") == "yes":
                Z[z]["lit_km"] += L
            if t.get("lanes"):
                Z[z]["lanes_km"][t["lanes"]] += L
            if t.get("surface"):
                Z[z]["surface_km"][t["surface"]] += L
            if SOI.search(name):
                Z[z]["soi_km"] += L
                soi_names[name] += L
            if hw in LANE:
                lane_km += L
                if not name:
                    unnamed_lane_km += L
            # orientation, per segment, weighted by length; the network proper only
            for i in range(len(pts) - 1 if hw in NET else 0):
                sl = haversine(pts[i], pts[i + 1])
                if sl <= 0:
                    continue
                b = bearing(pts[i], pts[i + 1]) % 180
                Z[z]["bins"][int(b // 5) % 36] += sl
            # block length: the way between consecutive intersections
            if w.get("nodes") and hw in NET:
                run = 0.0
                for i in range(len(pts) - 1):
                    run += haversine(pts[i], pts[i + 1])
                    if w["nodes"][i + 1] in inter:
                        Z[z]["seg_km"].append(run)
                        run = 0.0
            longest_ways.append((L, name, hw))

    # ---- places by zone
    river = [r for r in places["rows"] if r.get("kind") == "moat" and r.get("pts")
             and r["tags"].get("waterway") == "river"]
    ping = [r for r in river if "ปิง" in (r["tags"].get("name", "") + r["tags"].get("name:th", "")) or
            "Ping" in (r["tags"].get("name:en", "") + r["tags"].get("name", ""))]
    for r in places["rows"]:
        k = r.get("kind")
        pt = place_point(r)
        if not pt:
            continue
        z = zone_of(pt)
        if k == "wat":
            Z[z]["wats"] += 1
        elif k == "signal":
            Z[z]["signals"] += 1

    # ---- bridges over the Ping: a bridge way that crosses a Ping way
    ping_segs = [(r["pts"][i], r["pts"][i + 1]) for r in ping for i in range(len(r["pts"]) - 1)]
    ping_bridges = []
    for b in bridges:
        hit = False
        for i in range(len(b["pts"]) - 1):
            a1, a2 = b["pts"][i], b["pts"][i + 1]
            for p1, p2 in ping_segs:
                if abs(a1[0] - p1[0]) > 0.01 or abs(a1[1] - p1[1]) > 0.01:
                    continue
                if segments_cross(a1, a2, p1, p2):
                    hit = True
                    break
            if hit:
                break
        if hit:
            ping_bridges.append({k: v for k, v in b.items() if k != "pts"} | {"lat": midpoint(b["pts"])[0], "lon": midpoint(b["pts"])[1]})
    # collapse dual carriageways on the same bridge: group by name, else by 120 m
    grouped = []
    for b in sorted(ping_bridges, key=lambda x: x["lat"]):
        for g in grouped:
            if (b["name"] and b["name"] == g["name"]) or haversine((b["lat"], b["lon"]), (g["lat"], g["lon"])) < 0.12:
                g["ways"] += 1
                break
        else:
            grouped.append(dict(b, ways=1))

    # ---- summarise zones
    zones_out = {}
    for z, _ in ZONES:
        d = Z[z]
        area = zone_area_km2(z)
        segs = d["seg_km"]
        drive = d["drive_km"]
        zones_out[z] = {
            "label": ZONE_LABEL[z], "label_th": ZONE_TH[z], "area_km2": round(area, 2),
            "km": {k: round(v, 2) for k, v in d["km"].most_common()},
            "km_group": {k: round(v, 2) for k, v in d["km_group"].most_common()},
            "drive_km": round(drive, 2),
            "km_per_km2": round(drive / area, 2) if area else None,
            "ways": d["n_ways"],
            "intersections": d["inter"], "dead_ends": d["dead"],
            "inter_per_km2": round(d["inter"] / area, 1) if area else None,
            "dead_end_share": round(d["dead"] / (d["dead"] + d["inter"]), 3) if (d["dead"] + d["inter"]) else None,
            "block_m_mean": round(1000 * sum(segs) / len(segs)) if segs else None,
            "block_m_median": round(1000 * sorted(segs)[len(segs) // 2]) if segs else None,
            "orientation": entropy(d["bins"]),
            "bins": [round(b, 3) for b in d["bins"]],
            "oneway_share": round(d["oneway_km"] / drive, 3) if drive else None,
            "named_share": round(d["named_km"] / drive, 3) if drive else None,
            "soi_share": round(d["soi_km"] / drive, 3) if drive else None,
            "lit_share": round(d["lit_km"] / drive, 3) if drive else None,
            "signals": d["signals"], "wats": d["wats"],
            "wats_per_km2": round(d["wats"] / area, 2) if area else None,
            "lanes_km": {k: round(v, 2) for k, v in d["lanes_km"].most_common(6)},
            "surface_km": {k: round(v, 2) for k, v in d["surface_km"].most_common(6)},
        }

    total_km = sum(by_class_total.values())
    drive_km = sum(v for k, v in by_class_total.items() if k in DRIVE)
    # "ซอย 2" is a hundred different lanes sharing a number; the ladder wants names that
    # belong to one place, so a bare number is left out of it (it still counts above)
    GENERIC = re.compile(r"^(ซอย|ซ\.|soi)\s*\d+\s*$", re.I)
    top_soi = sorted(((n, k) for n, k in soi_names.items() if not GENERIC.match(n)), key=lambda x: -x[1])[:25]
    top_names = sorted(name_km.items(), key=lambda x: -x[1])[:40]
    soi_count = len(soi_names)
    wat_soi = sum(1 for n in soi_names if "วัด" in n or re.search(r"\bwat\b", n, re.I))
    numbered_soi = sum(1 for n in soi_names if re.search(r"\d", n))
    out = {
        "method": __doc__.strip(),
        "source": "OpenStreetMap via Overpass, © OpenStreetMap contributors, ODbL 1.0",
        "fetched": city.get("fetched"), "box": box,
        "centre": CENTRE, "moat": MOAT, "zones_km": [r for _, r in ZONES[1:-1]],
        "ways": len(ways),
        "total_km": round(total_km, 1), "drive_km": round(drive_km, 1),
        "walk_km": round(sum(v for k, v in by_class_total.items() if k in WALK), 1),
        "lane_km": round(lane_km, 1), "unnamed_lane_km": round(unnamed_lane_km, 1),
        "by_class": {k: round(v, 1) for k, v in by_class_total.most_common()},
        "intersections": len(inter), "dead_ends": len(dead),
        "zones": zones_out,
        "soi": {"named_count": soi_count, "km": round(sum(soi_names.values()), 1),
                "with_wat_in_name": wat_soi, "numbered": numbered_soi,
                "longest": [{"name": n, "km": round(k, 2)} for n, k in top_soi]},
        "longest_names": [{"name": n, "km": round(k, 2)} for n, k in top_names],
        "construction": sorted(construction, key=lambda x: -x["km"]),
        "construction_km": round(sum(c["km"] for c in construction), 2),
        "bridges_total": len(bridges), "tunnels": tunnels,
        "ping_bridges": sorted(grouped, key=lambda x: x["lat"]),
        "signals": sum(1 for r in places["rows"] if r.get("kind") == "signal"),
        "wats": sum(1 for r in places["rows"] if r.get("kind") == "wat"
                    and (lambda q: q and box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3])(place_point(r))),
    }
    jdump(out, HARVEST / "measures.json")
    print(f"measures: {len(ways)} ways, {total_km:.0f} km, {drive_km:.0f} drivable; "
          f"{len(inter)} intersections, {len(dead)} dead ends; {soi_count} named soi; "
          f"{len(grouped)} Ping bridges; {len(construction)} construction ways")
    for z, _ in ZONES:
        o = zones_out[z]
        print(f"  {z:7} {o['drive_km']:8.1f} km  inter/km² {o['inter_per_km2']}  dead {o['dead_end_share']}  "
              f"block {o['block_m_median']} m  phi {o['orientation']['phi']}  oneway {o['oneway_share']}  soi {o['soi_share']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
