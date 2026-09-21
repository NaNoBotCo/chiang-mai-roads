#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build.py — records + harvests → build/api.

Everything the site prints is computed here and written as JSON, so the API a reader or a
bot can fetch is the same data the pages are made from. Each figure is computed once, and
the pages read it rather than restating it.

    python3 tools/build.py
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (BUILD, TYPES, jdump, load_harvest, load_nodes,  # noqa: E402
                    load_sources, load_vocab)

API = BUILD / "api"


def aadt(h: dict) -> dict:
    """The highway department's counts, by station and by year, plus the ladder."""
    if not h:
        return {}
    rows = h["rows"]
    years = sorted({r["year"] for r in rows})
    by_year = {y: [r for r in rows if r["year"] == y] for y in years}
    latest = years[-1]
    top = sorted(by_year[latest], key=lambda r: -r["aadt"])
    # a station key that survives the km column changing its spelling year to year
    def key(r):
        return (r["route"], r["section"], r["km"].replace("km", "").strip())
    series = {}
    for r in rows:
        series.setdefault(key(r), {"route": r["route"], "name": r["name"], "km": r["km"].replace("km", ""), "years": {}})
        series[key(r)]["years"][r["year"]] = {"aadt": r["aadt"], "mc": r["motorcycles"]}
    trend = [v for v in series.values() if len(v["years"]) >= 4]
    trend.sort(key=lambda v: -max(y["aadt"] for y in v["years"].values()))
    sums = {y: {"stations": len(by_year[y]), "aadt": sum(r["aadt"] for r in by_year[y]),
                "mc": sum(r["motorcycles"] for r in by_year[y])} for y in years}
    return {"source": h["source"], "catalog": h["catalog"], "licence": h["licence"], "note": h["note"],
            "years": years, "latest": latest, "sums": sums,
            "ladder": [{"route": r["route"], "name": r["name"], "km": r["km"].replace("km", ""), "aadt": r["aadt"],
                        "mc": r["motorcycles"], "pct_heavy": r["pct_heavy"], "district": r["district"]} for r in top],
            "trend": trend[:16], "count": len(rows)}


def main() -> int:
    recs = load_nodes()
    sources = load_sources()
    vocab = {n: load_vocab(n) for n in ("types", "regions", "facets", "tags")}
    measures = load_harvest("measures") or {}
    counts = aadt(load_harvest("doh-aadt"))
    deaths = load_harvest("road-deaths") or {}
    tomtom = load_harvest("tomtom") or {}

    for r in recs:
        r.pop("_path", None)
        r.pop("_dir_type", None)

    back = {}
    for r in recs:
        for k in r.get("kin", []):
            back.setdefault(k["to"], []).append({"from": r["id"], "type": r["type"],
                                                 "name": r["names"]["name"], "as": k["as"]})
    for r in recs:
        r["kin_in"] = back.get(r["id"], [])

    cov = {
        "built": time.strftime("%Y-%m-%d %H:%M"),
        "records": len(recs),
        "by_type": {t: sum(1 for r in recs if r["type"] == t) for t in TYPES},
        "kin_edges": sum(len(r.get("kin", [])) for r in recs),
        "sources": len(sources),
        "needs_verification": sum(1 for r in recs if r.get("needs_verification")),
        "bilingual": sum(1 for r in recs if r.get("text_th")),
        "th_fields": sum(len(r.get("text_th") or {}) for r in recs),
        "images": sum(len(r.get("images") or []) for r in recs),
        "records_with_images": sum(1 for r in recs if r.get("images")),
        "ways": measures.get("ways", 0),
        "total_km": measures.get("total_km", 0),
        "drive_km": measures.get("drive_km", 0),
        "stations": counts.get("sums", {}).get(counts.get("latest", 0), {}).get("stations", 0),
        "tiers": {},
    }
    for r in recs:
        t = (r.get("provenance", {}).get("default") or {}).get("tier", "?")
        cov["tiers"][t] = cov["tiers"].get(t, 0) + 1

    API.mkdir(parents=True, exist_ok=True)
    jdump({"count": len(recs), "nodes": recs}, API / "nodes.json")
    jdump(measures, API / "measures.json")
    jdump(counts, API / "aadt.json")
    jdump(deaths, API / "deaths.json")
    jdump(tomtom, API / "tomtom.json")
    jdump({"sources": list(sources.values())}, API / "sources.json")
    jdump(vocab, API / "vocab.json")
    jdump(cov, API / "coverage.json")
    for t in TYPES:
        rows = [r for r in recs if r["type"] == t]
        jdump({"type": t, "count": len(rows), "nodes": rows}, API / f"{t}.json")
        for r in rows:
            jdump(r, API / t / f"{r['id']}.json")

    print(f"build: {len(recs)} records · {cov['kin_edges']} kin · {len(sources)} sources · "
          f"{cov['th_fields']} Thai fields · {cov['images']} images")
    print(f"       network: {cov['ways']} ways, {cov['total_km']} km, {cov['drive_km']} drivable")
    print(f"       counts: {counts.get('count')} station-years, {cov['stations']} stations in {counts.get('latest')}")
    print(f"       tiers: {cov['tiers']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
