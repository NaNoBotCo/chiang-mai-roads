#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""maps.py — the drawn maps, from the harvest.

  roads.png / roads-dark.png   every way in the city box, by class, over the relief
  city.svg                     the rings, the moat, the gates, the river and the labels,
                               inlined over roads.png by the page
  oldcity.svg                  the square inside the moat, every lane drawn, gates named
  roses.svg                    one orientation rose per zone (Boeing's method)
  eras.svg                     the named roads coloured by the era that built them
  region.png / region.svg      the roads out, by ref, Lampang to Fang

Raster where the element count would sink an SVG (60,000 ways), vector where a reader
might want to read a label. Every map shares one projection, geo.Proj, so an overlay
lines up with its base by construction.

    python3 tools/maps.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo  # noqa: E402
from common import BUILD, ROOT, jload, load_harvest, load_nodes  # noqa: E402
from measure import CENTRE, MOAT, ZONES, place_point, zone_of  # noqa: E402

SITE = BUILD / "site"
WIDTH = 1400

CLASS_STYLE = {   # (light colour, dark colour, width px at WIDTH)
    "motorway": ((200, 60, 40), (255, 120, 90), 3.2), "motorway_link": ((200, 60, 40), (255, 120, 90), 1.6),
    "trunk": ((200, 60, 40), (255, 120, 90), 3.0), "trunk_link": ((200, 60, 40), (255, 120, 90), 1.4),
    "primary": ((215, 110, 40), (255, 170, 90), 2.4), "primary_link": ((215, 110, 40), (255, 170, 90), 1.2),
    "secondary": ((190, 150, 60), (240, 205, 110), 1.8), "secondary_link": ((190, 150, 60), (240, 205, 110), 1.0),
    "tertiary": ((120, 110, 90), (200, 190, 160), 1.3), "tertiary_link": ((120, 110, 90), (200, 190, 160), 0.9),
    "residential": ((90, 85, 75), (170, 160, 140), 0.8), "living_street": ((90, 85, 75), (170, 160, 140), 0.8),
    "unclassified": ((90, 85, 75), (170, 160, 140), 0.8), "service": ((110, 105, 95), (120, 115, 100), 0.5),
    "construction": ((230, 40, 160), (255, 120, 220), 2.2),
}
WALK = {"footway", "path", "pedestrian", "steps", "cycleway", "track"}

E = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;")


def draw_roads(ways: list, box, out: Path, dark=False, base: Path = None, width=WIDTH):
    from PIL import Image, ImageDraw
    p = geo.Proj(box=box, width=width)
    W, H = int(p.width), int(p.height)
    if base and base.exists():
        img = Image.open(base).convert("RGB").resize((W, H))
        # soften the relief so the roads read on top of it
        veil = Image.new("RGB", (W, H), (18, 16, 13) if dark else (246, 242, 232))
        img = Image.blend(img, veil, 0.42)
    else:
        img = Image.new("RGB", (W, H), (18, 16, 13) if dark else (246, 242, 232))
    d = ImageDraw.Draw(img)
    order = ["service", "unclassified", "living_street", "residential", "tertiary_link", "tertiary",
             "secondary_link", "secondary", "primary_link", "primary", "trunk_link", "trunk",
             "motorway_link", "motorway", "construction"]
    byc = {}
    for w in ways:
        hw = w["tags"].get("highway")
        if hw in CLASS_STYLE:
            byc.setdefault(hw, []).append(w)
    for hw in order:
        light, darkc, wd = CLASS_STYLE[hw]
        col = darkc if dark else light
        for w in byc.get(hw, []):
            pts = [p.xy(a, b) for a, b in w["pts"]]
            if len(pts) > 1:
                d.line(pts, fill=col, width=max(1, round(wd)))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"{out.name}: {W}x{H}, {out.stat().st_size // 1024} KB, {sum(len(v) for v in byc.values())} ways")
    return p


def svg_head(p: geo.Proj, cls="mapsvg") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {p.width:.0f} {p.height:.0f}" '
            f'class="{cls}" role="img">\n<style>'
            '.ring{fill:none;stroke-linejoin:round;stroke-linecap:round}'
            '.r0{stroke:#1d4ed8;stroke-width:5}.r1{stroke:#b91c1c;stroke-width:5}'
            '.r2{stroke:#b45309;stroke-width:5}.r3{stroke:#15803d;stroke-width:5}'
            '.water{fill:none;stroke:#3b82f6;stroke-width:3;opacity:.8}'
            '.moatw{fill:none;stroke:#2563eb;stroke-width:6;opacity:.85}'
            '.lbl{font:700 22px/1 system-ui,sans-serif;fill:#111;paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round}'
            '.lbl.th{font-size:20px}.lbl.small{font-size:16px;font-weight:600}'
            '.gate{fill:#fff;stroke:#111;stroke-width:2.5}.wat{fill:#f59e0b;opacity:.6}'
            '.scale{stroke:#111;stroke-width:3}.scalet{font:600 16px system-ui,sans-serif;fill:#111}'
            '</style>\n')


def label(p, lat, lon, text, cls="lbl", dx=0, dy=0, anchor="middle") -> str:
    x, y = p.xy(lat, lon)
    return f'<text class="{cls}" x="{x + dx:.0f}" y="{y + dy:.0f}" text-anchor="{anchor}">{E(text)}</text>\n'


def ways_matching(ways, names=(), refs=()):
    out = []
    for w in ways:
        t = w["tags"]
        nm = (t.get("name") or "") + "|" + (t.get("name:en") or "") + "|" + (t.get("name:th") or "") + "|" + (t.get("alt_name") or "")
        ref = t.get("ref") or ""
        refs_here = [r.strip() for r in ref.replace(",", ";").split(";") if r.strip()]
        if any(n and n in nm for n in names) or any(r in refs_here for r in refs):
            out.append(w)
    return out


def paths(p, ways, cls) -> str:
    return "".join(f'<path class="{cls}" d="{p.path(w["pts"])}"/>\n' for w in ways if len(w["pts"]) > 1)


def city_svg(p, ways, places, recs) -> str:
    s = [svg_head(p)]
    rivers = [r for r in places if r.get("kind") == "moat" and r.get("pts") and r["tags"].get("waterway") in ("river", "canal")]
    s.append(paths(p, [r for r in rivers if r["tags"].get("waterway") == "canal"], "water"))
    s.append(paths(p, [r for r in rivers if r["tags"].get("waterway") == "river"], "water"))
    moat = [r for r in places if r.get("kind") == "moat" and r.get("pts") and (r["tags"].get("waterway") == "moat" or r["tags"].get("water") == "moat")]
    s.append(paths(p, moat, "moatw"))
    by_id = {r["id"]: r for r in recs}
    for rid, cls in (("moat-loop", "ring r0"), ("ring-1", "ring r1"), ("ring-2", "ring r2"), ("ring-3", "ring r3")):
        rd = (by_id.get(rid) or {}).get("road") or {}
        s.append(paths(p, ways_matching(ways, rd.get("osm_names", []), rd.get("osm_refs", [])), cls))
    for r in recs:
        if r["type"] == "gate" and r.get("geo") and r["geo"].get("precision", "exact") == "exact":
            x, y = p.xy(r["geo"]["lat"], r["geo"]["lon"])
            s.append(f'<circle class="gate" cx="{x:.0f}" cy="{y:.0f}" r="5"/>\n')
    s.append(label(p, 18.7883, 98.9855, "เวียง · the old city", "lbl", dy=-40))
    s.append(label(p, 18.815, 98.99, "Ring 1 · Superhighway", "lbl small", dy=-6))
    s.append(label(p, 18.845, 98.99, "Ring 2 · 700 Years Road", "lbl small"))
    s.append(label(p, 18.885, 98.985, "Ring 3 · Route 121", "lbl small"))
    s.append(label(p, 18.80, 98.92, "ดอยสุเทพ Doi Suthep", "lbl", anchor="start"))
    s.append(label(p, 18.83, 99.02, "แม่ปิง Ping", "lbl small", anchor="start"))
    s.append(label(p, 18.766, 98.965, "สนามบิน airport", "lbl small"))
    s.append(geo.scalebar(p, km=5))
    s.append("</svg>")
    return "".join(s)


def oldcity_svg(ways, places, recs) -> str:
    box = (MOAT[0] - 0.004, MOAT[1] - 0.004, MOAT[2] + 0.004, MOAT[3] + 0.004)
    p = geo.Proj(box=box, width=1100)
    s = [svg_head(p).replace("</style>", ".ln{fill:none;stroke:#6b6257;stroke-width:1.6;stroke-linecap:round}"
                                            ".mj{fill:none;stroke:#b45309;stroke-width:3.5;stroke-linecap:round}"
                                            ".ow{fill:none;stroke:#1d4ed8;stroke-width:2.6;stroke-dasharray:8 5}</style>")]
    inside = [w for w in ways if w.get("pts") and box[0] <= w["pts"][len(w["pts"]) // 2][0] <= box[2] and box[1] <= w["pts"][len(w["pts"]) // 2][1] <= box[3]]
    moat = [r for r in places if r.get("kind") == "moat" and r.get("pts") and (r["tags"].get("waterway") == "moat" or r["tags"].get("water") == "moat")]
    s.append(paths(p, moat, "moatw"))
    lanes = [w for w in inside if w["tags"].get("highway") in ("residential", "living_street", "service", "unclassified", "pedestrian")]
    major = [w for w in inside if w["tags"].get("highway") in ("primary", "secondary", "tertiary", "primary_link", "secondary_link", "tertiary_link")]
    s.append(paths(p, lanes, "ln"))
    s.append(paths(p, major, "mj"))
    s.append(paths(p, [w for w in inside if w["tags"].get("oneway") == "yes" and w["tags"].get("highway") in ("primary", "secondary", "tertiary", "residential")], "ow"))
    for r in recs:
        if r["type"] == "gate" and r.get("geo") and r["geo"].get("precision", "exact") == "exact":
            x, y = p.xy(r["geo"]["lat"], r["geo"]["lon"])
            s.append(f'<circle class="gate" cx="{x:.0f}" cy="{y:.0f}" r="7"/>\n')
            nm = r["names"].get("th", r["names"]["name"])
            s.append(label(p, r["geo"]["lat"], r["geo"]["lon"], nm, "lbl small", dy=-14))
    wats = [q for q in (place_point(r) for r in places if r.get("kind") == "wat")
            if q and box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3]]
    for q in wats:
        x, y = p.xy(q[0], q[1])
        s.append(f'<circle class="wat" cx="{x:.0f}" cy="{y:.0f}" r="4"/>\n')
    s.append(label(p, 18.788, 98.988, "ถนนราชดำเนิน Ratchadamnoen", "lbl small", dy=-6))
    s.append(geo.metre_bar(p, 500))
    s.append("</svg>")
    return "".join(s), len(lanes), len(major), len(wats)


def roses_svg(measures: dict) -> str:
    """One rose per zone, 36 bins over 0–180 mirrored to a full circle, radius by share."""
    zones = [z for z, _ in ZONES if z in measures.get("zones", {})]
    R, gap = 110, 30
    W = len(zones) * (2 * R + gap) + gap
    H = 2 * R + 90
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" class="mapsvg roses" role="img">'
         '<style>.rose{fill:#b45309;fill-opacity:.55;stroke:#7c2d12;stroke-width:1}.axis{stroke:#999;stroke-width:1}'
         '.rl{font:700 17px system-ui,sans-serif;fill:#111;text-anchor:middle}.rs{font:600 13px system-ui,sans-serif;fill:#555;text-anchor:middle}</style>']
    for i, z in enumerate(zones):
        zo = measures["zones"][z]
        bins = zo["bins"]
        total = sum(bins) or 1
        cx, cy = gap + R + i * (2 * R + gap), R + 10
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" class="axis"/>')
        s.append(f'<line x1="{cx - R}" y1="{cy}" x2="{cx + R}" y2="{cy}" class="axis"/><line x1="{cx}" y1="{cy - R}" x2="{cx}" y2="{cy + R}" class="axis"/>')
        mx = max(bins) / total
        for k, b in enumerate(bins):
            for half in (0, 180):
                a0 = math.radians(k * 5 + half - 90)
                a1 = math.radians(k * 5 + 5 + half - 90)
                r = R * math.sqrt((b / total) / mx) if mx else 0
                x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
                x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
                s.append(f'<path class="rose" d="M{cx} {cy}L{x0:.1f} {y0:.1f}A{r:.1f} {r:.1f} 0 0 1 {x1:.1f} {y1:.1f}Z"/>')
        phi = zo["orientation"].get("phi")
        s.append(f'<text class="rl" x="{cx}" y="{cy + R + 28}">{E(zo["label"])}</text>')
        s.append(f'<text class="rs" x="{cx}" y="{cy + R + 48}">{E(zo["label_th"])} · φ {phi if phi is not None else "–"}</text>')
    s.append("</svg>")
    return "".join(s)


ERA_COLOUR = {"mangrai": "#1d4ed8", "lanna": "#6d28d9", "kawila": "#0f766e", "siam": "#b45309",
              "srivichai": "#be123c", "superhighway": "#b91c1c", "rings": "#15803d", "now": "#111827", "planned": "#db2777"}


def eras_svg(p, ways, recs) -> str:
    s = [svg_head(p).replace("</style>", ".era{fill:none;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}</style>")]
    used = {}
    for r in recs:
        if r["type"] not in ("road", "ring", "highway", "bridge"):
            continue
        era = (r.get("facets") or {}).get("era")
        rd = r.get("road") or {}
        if not era or era not in ERA_COLOUR or not (rd.get("osm_names") or rd.get("osm_refs")):
            continue
        ws = ways_matching(ways, rd.get("osm_names", []), rd.get("osm_refs", []))
        if ws:
            used[r["id"]] = (era, len(ws))
        s.append("".join(f'<path class="era" style="stroke:{ERA_COLOUR[era]}" d="{p.path(w["pts"])}"/>\n' for w in ws if len(w["pts"]) > 1))
    s.append(label(p, 18.7883, 98.9855, "1296", "lbl", dy=6))
    s.append(geo.scalebar(p, km=5))
    s.append("</svg>")
    return "".join(s), used


def region(ways_region, recs, dark=False):
    box = (18.25, 98.45, 19.35, 99.35)
    p = geo.Proj(box=box, width=1200)
    from PIL import Image, ImageDraw
    W, H = int(p.width), int(p.height)
    img = Image.new("RGB", (W, H), (18, 16, 13) if dark else (246, 242, 232))
    d = ImageDraw.Draw(img)
    for w in ways_region:
        hw = w["tags"].get("highway")
        if hw not in CLASS_STYLE:
            continue
        light, darkc, wd = CLASS_STYLE[hw]
        pts = [p.xy(a, b) for a, b in w["pts"]]
        if len(pts) > 1:
            d.line(pts, fill=darkc if dark else light, width=max(1, round(wd * 0.8)))
    out = SITE / ("region-dark.png" if dark else "region.png")
    img.save(out, "PNG", optimize=True)
    s = [svg_head(p)]
    by_id = {r["id"]: r for r in recs}
    cols = {"route-11": "#b91c1c", "route-118": "#b45309", "route-107": "#15803d", "route-108": "#1d4ed8", "route-1095": "#be123c", "route-106": "#0f766e", "route-1001": "#6d28d9", "route-1317": "#7c2d12", "route-1006": "#a16207", "route-1269": "#db2777"}
    for rid, col in cols.items():
        rd = (by_id.get(rid) or {}).get("road") or {}
        ws = ways_matching(ways_region, [], rd.get("osm_refs", []))
        s.append("".join(f'<path class="ring" style="stroke:{col};stroke-width:4" d="{p.path(w["pts"], every=3)}"/>\n' for w in ws if len(w["pts"]) > 1))
    for txt, lat, lon in (("เชียงใหม่ Chiang Mai", 18.7883, 98.9855), ("ลำพูน Lamphun", 18.574, 99.008), ("แม่ริม Mae Rim", 18.916, 98.94),
                          ("ดอยสะเก็ด Doi Saket", 18.87, 99.14), ("หางดง Hang Dong", 18.69, 98.92), ("สันกำแพง San Kamphaeng", 18.745, 99.12),
                          ("→ ลำปาง · Bangkok 696 km", 18.35, 99.25), ("→ เชียงราย Chiang Rai", 19.3, 99.3), ("→ ฝาง Fang", 19.3, 98.96),
                          ("→ ปาย Pai", 19.05, 98.55), ("→ แม่ฮ่องสอน via Hot", 18.3, 98.5), ("สะเมิง Samoeng", 18.85, 98.73)):
        s.append(label(p, lat, lon, txt, "lbl small"))
    s.append(geo.scalebar(p, km=20))
    s.append("</svg>")
    (SITE / "region.svg").write_text("".join(s), encoding="utf-8")
    print(f"{out.name}: {W}x{H}, {out.stat().st_size // 1024} KB")


def main() -> int:
    city = load_harvest("osm-city")
    places = (load_harvest("osm-places") or {}).get("rows", [])
    measures = load_harvest("measures") or {}
    recs = load_nodes()
    SITE.mkdir(parents=True, exist_ok=True)
    meta = {}
    if city:
        ways = city["ways"]
        box = geo.BOX
        p = draw_roads(ways, box, SITE / "roads.png", dark=False, base=SITE / "terrain.png")
        draw_roads(ways, box, SITE / "roads-dark.png", dark=True, base=SITE / "terrain-dark.png")
        (SITE / "city.svg").write_text(city_svg(p, ways, places, recs), encoding="utf-8")
        svg, nl, nm, nw = oldcity_svg(ways, places, recs)
        (SITE / "oldcity.svg").write_text(svg, encoding="utf-8")
        meta["oldcity"] = {"lanes": nl, "major": nm, "wats": nw}
        svg, used = eras_svg(p, ways, recs)
        (SITE / "eras.svg").write_text(svg, encoding="utf-8")
        meta["eras"] = used
        meta["box"] = list(box)
        print(f"city.svg, oldcity.svg ({nl} lanes, {nm} major, {nw} wats), eras.svg ({len(used)} roads matched)")
    if measures:
        (SITE / "roses.svg").write_text(roses_svg(measures), encoding="utf-8")
    reg = load_harvest("osm-region")
    if reg:
        region(reg["ways"], recs)
        region(reg["ways"], recs, dark=True)
    (BUILD / "api" / "maps.json").parent.mkdir(parents=True, exist_ok=True)
    (BUILD / "api" / "maps.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
