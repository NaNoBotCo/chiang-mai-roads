#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""site.py — build/api → build/site. A static, bilingual, offline-capable site.

Every reader-facing page exists twice: English at its path, Thai at /th/<same path>. The
two are the same build function called with a different language, so a page cannot exist
in one language and silently not the other; where a record has no Thai text the Thai page
says so rather than showing machine translation.

    python3 tools/site.py
    SITE_URL=https://example.org python3 tools/site.py
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fleet  # noqa: E402
from common import BUILD, ROOT, TIER_LABEL, TYPES, jload  # noqa: E402
from css import CSS  # noqa: E402

API = BUILD / "api"
SITE = BUILD / "site"
SITE_URL = os.environ.get("SITE_URL", "https://nanobotco.github.io/chiang-mai-roads").rstrip("/")
# Published twice: the GitHub Pages copy, which the repo builds by default, and
# https://motdang.net/roads. Both declare one canonical; the other copy is rel=alternate.
CANONICAL_URL = os.environ.get("CANONICAL_URL", "https://motdang.net/roads").rstrip("/")
BASE_PATH = os.environ.get("BASE_PATH")
if BASE_PATH is None:
    _p = urllib.parse.urlparse(SITE_URL).path.strip("/")
    BASE_PATH = f"/{_p}/" if _p else "/"
if not BASE_PATH.endswith("/"):
    BASE_PATH += "/"

SELF = "chiang-mai-roads"
LANGS = ("en", "th")
NAME = {"en": "Roads of Chiang Mai", "th": "ถนนหนทางเจียงใหม่"}
TAI_THAM = "ᨩ᩠ᨿᨦᩉ᩠ᨾᩲ᩵"
AUTHOR = {"@type": "Person", "name": "NaN", "url": "https://wichaa.net"}
MAKER = fleet.maker_ld(fleet.load(ROOT / "data" / "fleet.json"))
DATA_LICENSE = "https://creativecommons.org/licenses/by/4.0/"


def E(x) -> str:
    return html.escape("" if x is None else str(x))


def T(d: dict, key: str, lang: str, fallback=True):
    """A field in the requested language. `names.th` / `text_th` hold the Thai."""
    if lang == "th":
        if key.startswith("text."):
            v = (d.get("text_th") or {}).get(key[5:])
        elif key.startswith("names."):
            v = (d.get("names") or {}).get(key[6:] + "_th") or (
                (d.get("names") or {}).get("th") if key == "names.name" else None)
        else:
            v = d.get(key + "_th")
        if v:
            return v
        if not fallback:
            return None
    if key.startswith("text."):
        return (d.get("text") or {}).get(key[5:])
    if key.startswith("names."):
        return (d.get("names") or {}).get(key[6:])
    return d.get(key)


def _load(name, default=None):
    f = API / f"{name}.json"
    return jload(f) if f.exists() else (default if default is not None else {})


# ---------------------------------------------------------------- data, loaded once
V = jload(API / "vocab.json")
TYPE_INFO = {e["key"]: e for e in V["types"]["entries"]}
FACETS = V["facets"]["facets"]
REGIONS = {e["key"]: e for e in V["regions"]["entries"]}
TAGS = V["tags"]["tags"]
PATH_OF = {t: TYPE_INFO[t]["path"] for t in TYPE_INFO}
NODES = jload(API / "nodes.json")["nodes"]
BY_ID = {r["id"]: r for r in NODES}
SOURCES = {s["id"]: s for s in jload(API / "sources.json")["sources"]}
COV = jload(API / "coverage.json")
M = _load("measures")
AADT = _load("aadt")
DEATHS = _load("deaths")
TOMTOM = _load("tomtom")
MAPS = _load("maps")
FLEET = fleet.load(ROOT / "data" / "fleet.json")

_km = f"{M.get('drive_km', 0):,.0f}" if M else "—"
TAG = {"en": f"The square of 1296, four rings around it, {_km} km of road between, and what "
             f"each one did to the city. Counted from the map, dated from the record.",
       "th": f"สี่เหลี่ยมปี 1839 วงแหวนสี่วงล้อมมัน ถนน {_km} กม. ระหว่างนั้น และแต่ละวงทำอะไรกับเมือง "
             f"นับจากแผนที่ ลงวันที่จากบันทึก"}

DIR_OF = {"road": "roads", "ring": "rings", "lane": "alleys", "gate": "gates", "junction": "junctions",
          "bridge": "bridges", "highway": "highways", "plan": "plans", "era": "eras", "map": "old-maps",
          "measure": "measures", "traffic": "traffic", "word": "words", "story": "stories",
          "person": "people", "place": "places"}

UI = {
 "en": {"home": "Roads", "map": "The map", "rings": "Rings", "oldcity": "Old city", "highways": "Highways out",
        "oldmaps": "Old maps", "timeline": "Timeline", "plans": "Plans", "traffic": "Traffic", "numbers": "Numbers", "words": "Words",
        "quiz": "Which road are you", "stories": "Stories",
        "all": "Everything", "about": "How this was made",
        "kin": "Connected to", "said_here": "Named here by", "sources": "Sources",
        "prov": "Where each claim comes from", "back": "Back",
        "what": "What it is", "story": "The long version", "how": "How", "today": "Now",
        "notes": "Notes", "share": "Share", "copy": "Copy link", "print": "Print",
        "no_th": "This section has not been written in Thai yet. The English is below.",
        "unverified": "Parts of this record are marked as needing verification.",
        "more": "More", "measured": "Counted for this site", "th_name": "In Thai",
        "ref": "Route", "km": "km", "lanes": "lanes", "opened": "opened", "from": "from", "to": "to",
        "status": "status", "budget": "budget", "due": "due", "agency": "agency",
        "value": "the figure", "year": "year", "method": "How it was counted", "compare": "Against",
        "script": "Script", "rtgs": "RTGS", "sound": "Sound", "standard": "Standard Thai", "gloss": "Meaning", "tt": "Tai Tham", "example": "Example"},
 "th": {"home": "ถนน", "map": "แผนที่", "rings": "วงแหวน", "oldcity": "เวียงเก่า", "highways": "ทางหลวงออกเมือง",
        "oldmaps": "แผนที่เก่า", "timeline": "ลำดับเวลา", "plans": "แผน", "traffic": "จราจร", "numbers": "ตัวเลข", "words": "กำเมือง",
        "quiz": "เป็นถนนสายไหน", "stories": "เรื่องเล่า",
        "all": "ทั้งหมด", "about": "ทำขึ้นอย่างไร",
        "kin": "เกี่ยวข้องกับ", "said_here": "ถูกอ้างถึงโดย", "sources": "แหล่งอ้างอิง",
        "prov": "แต่ละข้อความมาจากไหน", "back": "ย้อนกลับ",
        "what": "คืออะไร", "story": "ฉบับยาว", "how": "วิธี", "today": "ตอนนี้",
        "notes": "หมายเหตุ", "share": "แบ่งปัน", "copy": "คัดลอกลิงก์", "print": "พิมพ์",
        "no_th": "ส่วนนี้ยังไม่ได้เขียนเป็นภาษาไทย ด้านล่างเป็นภาษาอังกฤษ",
        "unverified": "บางส่วนของบันทึกนี้ยังต้องการการตรวจสอบ",
        "more": "เพิ่มเติม", "measured": "นับขึ้นเพื่อเว็บนี้", "th_name": "ภาษาไทย",
        "ref": "ทางหลวง", "km": "กม.", "lanes": "ช่องจราจร", "opened": "เปิด", "from": "จาก", "to": "ถึง",
        "status": "สถานะ", "budget": "งบ", "due": "กำหนด", "agency": "หน่วยงาน",
        "value": "ตัวเลข", "year": "ปี", "method": "นับอย่างไร", "compare": "เทียบกับ",
        "script": "ตัวเขียน", "rtgs": "RTGS", "sound": "เสียง", "standard": "ภาษากลาง", "gloss": "ความหมาย", "tt": "ตัวเมือง", "example": "ตัวอย่าง"},
}

NAV = [("", "home"), ("map/", "map"), ("old-maps/", "oldmaps"), ("rings/", "rings"), ("old-city/", "oldcity"),
       ("highways/", "highways"), ("timeline/", "timeline"), ("plans/", "plans"), ("traffic/", "traffic"), ("numbers/", "numbers"),
       ("words/", "words"), ("stories/", "stories"), ("quiz/", "quiz")]

CSS_EXTRA = """
.tt{font-family:"Noto Sans Tai Tham","Lanna","Tai Tham",var(--thai);font-weight:400;opacity:.85}
.brand .tt{font-size:.8em;margin-left:.4em}
.mapwrap{position:relative;margin:1rem 0;border:3px solid var(--ink);background:var(--ink)}
.mapwrap img{width:100%;display:block}
.mapwrap svg.mapsvg{position:absolute;inset:0;width:100%;height:100%}
.mapwrap.light .dark-only,.mapwrap .light-only{display:block}
.mapwrap img.dk{display:none}
@media (prefers-color-scheme:dark){.mapwrap img.lt{display:none}.mapwrap img.dk{display:block}
 .mapsvg .lbl{fill:#f3ede1;stroke:#111}.mapsvg .gate{fill:#111;stroke:#f3ede1}.mapsvg .scalet{fill:#f3ede1}.mapsvg .scale{stroke:#f3ede1}
 .roses .rl{fill:#f3ede1}.roses .rs{fill:#cfc7b8}}
svg.mapsvg{width:100%;height:auto;display:block}
.plain{border:3px solid var(--ink);background:var(--panel)}
.legend{display:flex;flex-wrap:wrap;gap:.4rem 1.2rem;font-size:.82rem;margin:.4rem 0 1rem}
.legend i{display:inline-block;width:1.6rem;height:.4rem;vertical-align:middle;margin-right:.4rem;border-radius:2px}
.mini{position:relative;width:100%;max-width:26rem;aspect-ratio:1400/1567;background-size:cover;border:3px solid var(--ink);margin:.6rem 0}
.mini b{position:absolute;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;background:#e0322b;border:3px solid #fff;box-shadow:0 0 0 2px #111}
.mini.dk{display:none}@media (prefers-color-scheme:dark){.mini.lt{display:none}.mini.dk{display:block}}
.chart{width:100%;height:auto;display:block;margin:.6rem 0 1rem}
.chart text{font:600 12px system-ui,sans-serif;fill:var(--ink)}
.chart .bar{fill:var(--hot)}.chart .bar2{fill:var(--jade)}.chart .axis{stroke:var(--mute);stroke-width:1}
.chart .ln{fill:none;stroke-width:2.5;stroke-linejoin:round}
.status{display:inline-block;padding:.1rem .5rem;border:2px solid var(--ink);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;font-weight:800}
.status.building{background:var(--jade);color:#111}.status.funded{background:var(--hot);color:#fff}.status.study{background:transparent}.status.shelved,.status.cancelled{opacity:.6;text-decoration:line-through}
.quiz fieldset{border:3px solid var(--ink);margin:.8rem 0;padding:.6rem 1rem}
.quiz legend{font-family:var(--display);font-weight:800;padding:0 .4rem}
.quiz label{display:block;padding:.25rem 0;cursor:pointer}
.quiz .result{display:none;border:3px solid var(--ink);padding:1rem;margin-top:1rem;background:var(--panel)}
.quiz .result.on{display:block}
.era-strip{display:flex;gap:.3rem;flex-wrap:wrap;margin:.6rem 0}
.era-strip span{padding:.15rem .5rem;font-size:.75rem;font-weight:700;color:#fff;border-radius:2px}
table.ladder td.num{text-align:right;font-variant-numeric:tabular-nums}
.kv th{width:11rem}
figure.sheet{margin:.8rem 0 1.2rem;border:3px solid var(--ink);background:var(--panel)}
figure.sheet img{width:100%;display:block}
figure.sheet figcaption{padding:.35rem .6rem;font-size:.76rem;color:var(--mute);border-top:3px solid var(--ink)}
"""


def rel(depth: int = 0) -> str:
    return BASE_PATH


def lroot(lang: str) -> str:
    return f"{BASE_PATH}th/" if lang == "th" else BASE_PATH


def url_of(r: dict, lang="en") -> str:
    return f"{DIR_OF[r['type']]}/{r['id']}/"


def page(title, body, depth, lang, desc="", jsonld=None, head="", cur="", path="", card=""):
    rin = BASE_PATH + ("th/" if lang == "th" else "")
    r = BASE_PATH
    ui = UI[lang]
    en_url = f"{BASE_PATH}{path}"
    th_url = f"{BASE_PATH}th/{path}"
    bilingual = path not in ("api/", "404.html")
    og_title = title.split(" — ")[0] if " — " in title else title
    og_desc = desc or TAG[lang]
    if og_desc.strip() == og_title.strip():
        og_desc = TAG[lang]
    og_url = f"{CANONICAL_URL}/{'th/' if lang == 'th' else ''}{path}"
    card_url = f"{CANONICAL_URL}/cards/{card or 'index'}.jpg"
    card_meta = (f'<meta property="og:image" content="{E(card_url)}">'
                 f'<meta property="og:image:secure_url" content="{E(card_url)}">'
                 f'<meta property="og:image:type" content="image/jpeg">'
                 f'<meta property="og:image:width" content="1200">'
                 f'<meta property="og:image:height" content="630">'
                 f'<meta property="og:image:alt" content="{E(og_title)}">'
                 f'<meta name="twitter:image" content="{E(card_url)}">')
    CURATTR = ' aria-current="page"'
    nav = "".join(f'<a href="{rin}{p}"{CURATTR if k == cur else ""}>{E(ui[k])}</a>'
                  for p, k in NAV)
    ld = json.dumps(jsonld or [], ensure_ascii=False)
    THATTR = ' aria-current="true"'
    thsw = (f'<a href="{th_url}"{THATTR if lang == "th" else ""} '
            f'hreflang="th">ไทย</a>') if bilingual else ""
    brand = ('Roads of <b>Chiang Mai</b>' if lang == "en" else 'ถนน<b>เจียงใหม่</b>') + f'<span class="tt" lang="nod">{TAI_THAM}</span>'
    return f"""<!doctype html>
<html lang="{lang}" class="{'th ' if lang == 'th' else ''}notranslate" translate="no">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(CANONICAL_URL)}/{"th/" if lang == "th" else ""}{E(path)}">
<link rel="alternate" href="{E(SITE_URL)}/{E(path)}">
<link rel="alternate" hreflang="en" href="{SITE_URL}/{E(path)}">
<link rel="alternate" hreflang="th" href="{SITE_URL}/th/{E(path)}">
<link rel="alternate" hreflang="x-default" href="{SITE_URL}/{E(path)}">
<meta property="og:title" content="{E(og_title)}">
<meta property="og:description" content="{E(og_desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{E(og_url)}">
<meta property="og:site_name" content="{E(NAME[lang])}">
<meta property="og:locale" content="{'th_TH' if lang == 'th' else 'en_GB'}">
<meta name="twitter:card" content="summary_large_image">
{card_meta}
<link rel="icon" href="{r}icon.svg" type="image/svg+xml">
<link rel="manifest" href="{r}manifest.webmanifest">
<link rel="alternate" type="application/atom+xml" href="{r}feed.xml">
<style>{CSS}{CSS_EXTRA}</style>{head}
<script type="application/ld+json">{ld}</script>
<script defer src="{r}copy.js"></script>
<meta name="google" content="notranslate">
<meta name="robots" content="notranslate">
<script>if(/[.]translate[.]goog$/.test(location.hostname))location.replace("https://"+location.hostname.slice(0,-15).replace(/--/g,"~").replace(/-/g,".").replace(/~/g,"-")+location.pathname+location.search.replace(/([?&])_x_tr_[^&]*/g,"$1").replace(/[?&]+$/,"").replace(/[?]&+/,"?")+location.hash)</script>
</head>
<body>
<a class="sr" href="#main">Skip to content</a>
<header class="top"><div class="in">
<a class="brand" href="{rin}">{brand}</a>
<nav>{nav}</nav>
<span class="langsw">
<a href="{en_url}"{THATTR if lang == 'en' else ''} hreflang="en">EN</a>
{thsw}
</span>
</div></header>
<main id="main">
{body}
</main>
<footer class="bot"><div class="in">
<p><b>{E(NAME[lang])}</b> — {E(TAG[lang])}</p>
<p>{'Records CC BY 4.0. Roads, lanes, wats and water © OpenStreetMap contributors, ODbL 1.0. Traffic counts from the Department of Highways and road deaths from the Department of Disease Control, both via the Thai open-data portals. Relief from Copernicus DEM via Open-Meteo, CC BY 4.0. Corpus text and pictures from Wikipedia and Wikimedia Commons, licensed per file.' if lang == 'en' else 'บันทึกเผยแพร่ภายใต้ CC BY 4.0 ถนน ฮ่อม วัด และน้ำ © ผู้ร่วมสร้าง OpenStreetMap ภายใต้ ODbL 1.0 ปริมาณจราจรจากกรมทางหลวงและการตายบนถนนจากกรมควบคุมโรค ผ่านพอร์ทัลข้อมูลเปิดของไทย ภูมิประเทศจาก Copernicus DEM ผ่าน Open-Meteo CC BY 4.0 เนื้อหาและภาพจากวิกิพีเดียและวิกิมีเดียคอมมอนส์ ตามสัญญาอนุญาตของแต่ละไฟล์'}</p>
{fleet.maker_html(roster=FLEET, lang=lang)}
<p><a href="{rin}about/">{E(ui['about'])}</a> · <a href="{r}api/">API</a> · <a href="{rin}all/">{E(ui['all'])}</a> · <a href="{r}llms.txt">llms.txt</a> · <a href="https://motdang.net/soi.html">{'Every place in the city, by road — on Mot Dang' if lang == 'en' else 'ทุกที่ในเมือง ตามถนน — บนมดแดง'}</a></p>
{fleet.row_html(SELF, label=("More from the same publisher" if lang == "en" else "เว็บอื่นของผู้จัดทำ"), roster=FLEET)}
{fleet.support_html(self_id="chiang-mai-roads", roster=FLEET)}
</div></footer>
</body></html>
"""


def marks(text: str) -> str:
    t = E(text)
    t = re.sub(r"\*(Inference|Tradition holds|Tradition|อนุมาน|ตามธรรมเนียม)\s*—\*",
               lambda m: f'<mark class="inf">{m.group(1)} —</mark>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t


def prose(text: str) -> str:
    if not text:
        return ""
    out = []
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith("- "):
            items = "".join(f"<li>{marks(li[2:])}</li>" for li in para.split("\n")
                            if li.strip().startswith("- "))
            out.append(f"<ul>{items}</ul>")
        else:
            out.append(f"<p>{marks(para)}</p>")
    return "".join(out)


ICONS = {
 "facebook": "M17 2h-3a5 5 0 0 0-5 5v3H6v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z",
 "line": "M12 3C6.5 3 2 6.6 2 11c0 3.9 3.5 7.2 8.2 7.9.3.07.8.2.9.5.1.3.07.7.03 1l-.14.9c-.04.3-.2 1 .9.55 1.1-.45 6-3.5 8.2-6C21.4 14.2 22 12.7 22 11c0-4.4-4.5-8-10-8z",
 "whatsapp": "M20 12a8 8 0 0 1-11.9 7L4 20l1-4.1A8 8 0 1 1 20 12z",
 "x": "M3 3l7.5 9.5L3.5 21h2l6-6.8L17 21h4l-7.9-10L20.5 3h-2l-5.6 6.4L8 3z",
 "reddit": "M22 12a2 2 0 0 0-3.4-1.4A11 11 0 0 0 13 9l.9-3.4 2.6.6a1.6 1.6 0 1 0 .2-1.4l-3.4-.8-1.3 4.9A11 11 0 0 0 5.4 10.6 2 2 0 1 0 3.6 14 4 4 0 0 0 3.5 15c0 3 3.8 5.5 8.5 5.5s8.5-2.5 8.5-5.5a4 4 0 0 0-.1-1A2 2 0 0 0 22 12z",
 "mail": "M3 6h18v12H3zM3 6l9 7 9-7",
 "link": "M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1",
 "print": "M7 8V3h10v5M7 18H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2M7 14h10v7H7z",
}


def _icon(name: str) -> str:
    d = ICONS.get(name, "")
    fill = "none" if name in ("mail", "link", "print", "whatsapp") else "currentColor"
    return (f'<svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true" '
            f'fill="{fill}" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round"><path d="{d}"/></svg>')


def share_row(url: str, title: str, lang: str, blurb: str = "") -> str:
    ui = UI[lang]
    en = lang == "en"
    q = urllib.parse.quote
    share_text = f"{title} — {blurb}" if blurb else title
    links = [
        ("facebook", "Facebook", f"https://www.facebook.com/sharer/sharer.php?u={q(url)}"),
        ("line", "LINE", f"https://social-plugins.line.me/lineit/share?url={q(url)}"),
        ("whatsapp", "WhatsApp", f"https://api.whatsapp.com/send?text={q(share_text + ' ' + url)}"),
        ("x", "X", f"https://twitter.com/intent/tweet?text={q(share_text)}&url={q(url)}"),
        ("reddit", "Reddit", f"https://reddit.com/submit?url={q(url)}&title={q(title)}"),
        ("mail", "Email", f"mailto:?subject={q(title)}&body={q(share_text + chr(10) + chr(10) + url)}"),
    ]
    btns = "".join(
        f'<a class="sh sh-{k}" href="{E(href)}" rel="noopener" target="_blank" '
        f'data-share="{E(k)}">{_icon(k)}<span>{E(label)}</span></a>'
        for k, label, href in links)
    head = "Send this to whoever drives" if en else "ส่งหื้อคนตี้ขับ"
    sub = "It opens the same in Thai." if en else "เปิดเป็นภาษาอังกฤษได้เหมือนกัน"
    return (f'<aside class="sharebar"><div class="shhead"><b>{E(head)}</b>'
            f'<span class="mute small">{E(sub)}</span></div>'
            f'<div class="shrow">{btns}'
            f'<button type="button" class="sh sh-link" data-copy="{E(url)}">'
            f'{_icon("link")}<span>{E(ui["copy"])}</span></button>'
            f'<button type="button" class="sh sh-print" onclick="window.print()">'
            f'{_icon("print")}<span>{E(ui["print"])}</span></button>'
            f'<button type="button" class="sh sh-native" hidden data-native="{E(url)}" '
            f'data-title="{E(title)}">{_icon("link")}<span>'
            f'{E("Share…" if en else "แชร์…")}</span></button></div></aside>'
            '<script>document.addEventListener("DOMContentLoaded",function(){'
            'var n=document.querySelector(".sh-native");'
            'if(n&&navigator.share){n.hidden=false;n.addEventListener("click",function(){'
            'navigator.share({title:n.dataset.title,url:n.dataset.native}).catch(function(){})})}});'
            "</script>")


# ---------------------------------------------------------------- small parts
def tier_chip(p: dict, lang="en") -> str:
    t = (p or {}).get("tier", "")
    return f'<span class="tier {E(t)}">{E(t)}</span>' if t else ""


def src_link(sid: str, lang="en") -> str:
    s = SOURCES.get(sid)
    if not s:
        return E(sid)
    t = E(s.get("title") or sid)
    pub = E(s.get("publisher") or "")
    if s.get("url"):
        return f'<a href="{E(s["url"])}" rel="noopener">{t}</a>{" — " + pub if pub else ""}'
    return f"{t} — {pub}"


def prov_block(r: dict, lang: str) -> str:
    ui = UI[lang]
    pv = r.get("provenance") or {}
    rows = [("<em>default</em>", pv.get("default") or {})]
    rows += [(E(k), v) for k, v in (pv.get("fields") or {}).items()]
    body = "".join(
        f"<tr><td>{k}</td><td>{tier_chip(v, lang)}</td>"
        f"<td>{src_link(v.get('source'), lang) if v.get('source') else ''}</td>"
        f"<td class='small mute'>{E(v.get('note') or '')}</td></tr>" for k, v in rows)
    srcs = "".join(f"<li>{src_link(s, lang)}</li>" for s in r.get("sources", []))
    return (f'<details><summary>{E(ui["prov"])}</summary>'
            f'<div class="scroll"><table><thead><tr><th>Field</th><th>Tier</th><th>Source</th>'
            f'<th>Note</th></tr></thead><tbody>{body}</tbody></table></div>'
            f'<h3>{E(ui["sources"])}</h3><ul class="small">{srcs}</ul>'
            f'<p class="small mute">' +
            " · ".join(f"<b>{E(k)}</b> {E(v)}" for k, v in TIER_LABEL.items()) +
            "</p></details>")


def clip(t: str, n: int) -> str:
    t = (t or "").strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"


def credit(im: dict, short=False) -> str:
    who_raw = (im.get("author") or "unknown").strip()
    # Commons sometimes doubles the author string ("Unknown authorUnknown author")
    half = len(who_raw) // 2
    if len(who_raw) > 6 and who_raw[:half] == who_raw[half:]:
        who_raw = who_raw[:half]
    who = E(who_raw)
    lic = E(im.get("license") or "")
    page_url = im.get("page_url") or ""
    lic_html = (f'<a href="{E(im["license_url"])}" rel="license noopener">{lic}</a>'
                if im.get("license_url") else lic)
    src = f'<a href="{E(page_url)}" rel="noopener">Commons</a>' if page_url else ""
    note = E(im.get("credit") or "") if im.get("source") == "own" else ""
    parts = [who, note, lic_html] if note else [who, lic_html]
    if not short and src:
        parts.append(src)
    return " · ".join(x for x in parts if x)


def shot_link(href: str, src: str, label: str, im: dict = None) -> str:
    """A picture that leads somewhere, in four layers: background, scrim, spacer, text."""
    cred = f'<span class="cred">{credit(im, short=True)}</span>' if im else ""
    return (f'<figure class="thumb"><h3><a class="shot" href="{E(href)}">'
            f'<span class="bg" style="background-image:url({E(src)})"></span>'
            f'<span class="scrim"></span><span class="sp"></span>'
            f'<span class="tx">{E(label)}</span></a></h3>{cred}</figure>')


def img_url(im: dict, thumb=False) -> str:
    f = im["file"]
    if thumb:
        f = f.rsplit(".", 1)[0] + ".thumb.jpg"
    return f"{rel()}images/{f}"


def pictures(n: dict) -> list:
    return [i for i in (n.get("images") or []) if i.get("file")]


def hero_shot(n: dict) -> str:
    ims = pictures(n)
    if not ims:
        return ""
    im = next((i for i in ims if i.get("primary")), ims[0])
    return (f'<div class="hero-shot"><img src="{E(img_url(im))}" alt="{E(im.get("alt") or "")}" '
            f'loading="lazy" decoding="async">'
            f'<span class="cap">{credit(im, short=True)}</span></div>')


def shot_strip(ims: list) -> str:
    if not ims:
        return ""
    out = ['<div class="strip">']
    for im in ims:
        out.append(f'<figure><img src="{E(img_url(im, thumb=True))}" '
                   f'alt="{E(im.get("alt") or "")}" loading="lazy" decoding="async">'
                   f'<figcaption>{credit(im, short=True)}</figcaption></figure>')
    out.append("</div>")
    return "".join(out)


def node_card(n: dict, lang: str, n_label=None) -> str:
    r = lroot(lang)
    name = T(n, "names.name", lang)
    th = n["names"].get("th")
    what = T(n, "text.what", lang) or ""
    meta = []
    fx = n.get("facets") or {}
    if n.get("plan") and n["plan"].get("status"):
        meta.append(f'<span class="status {E(n["plan"]["status"])}">{E(n["plan"]["status"])}</span>')
    if (n.get("road") or {}).get("km"):
        meta.append(f'<span class="tag">{n["road"]["km"]} km</span>')
    if (n.get("figure") or {}).get("value") is not None and n["type"] == "traffic":
        v = n["figure"]["value"]
        meta.append(f'<span class="tag">{v:,}</span>' if isinstance(v, (int, float)) else f'<span class="tag">{E(v)}</span>')
    for t in (n.get("tags") or [])[:2]:
        meta.append(f'<span class="tag">{E(t)}</span>')
    ims = pictures(n)
    thumb = ""
    if ims:
        im = next((i for i in ims if i.get("primary")), ims[0])
        thumb = shot_link(f"{r}{url_of(n)}", img_url(im, thumb=True), name, im)
    num = f'<span class="n">{n_label}</span>' if n_label else ""
    thai = f'<p class="th">{E(th)}</p>' if th and lang == "en" else ""
    head = "" if thumb else f'<h3><a href="{r}{url_of(n)}">{E(name)}</a></h3>'
    return (f'<article class="card">{num}{thumb}{head}{thai}'
            f'<p>{E(clip(what, 150))}</p>'
            f'<div class="tags">{"".join(meta)}</div></article>')


# ---------------------------------------------------------------- parallax bands
BANDS = {
    "moat":      ("the-moat", "201703291126a"),
    "moat2":     ("the-moat", "201703291029a"),
    "thaphae":   ("tha-phae-gate", "9784-dxo"),
    "thaphae54": ("tha-phae-road", "2497"),
    "pano":      ("doi-suthep", "chiang-mai-pano-2010"),
    "pano2":     ("built-up-area", "panorama-from-doi-suthep-lookout"),
    "city":      ("era-now", "panoramic-view-of-cmx"),
    "nimman":    ("nimmanhaemin-road", "nimmanhaeminda-road-2025"),
    "trees":     ("the-trees-on-the-lamphun-road", "p1160022"),
    "trees2":    ("ton-yang-road", "dipterocarpus"),
    "monk":      ("si-wichai-road", "anusawwaree"),
    "mountain":  ("si-wichai-road", "road-below-wat"),
    "river":     ("ping-river", "ping-river-in-chiang-mai-4"),
    "nawarat":   ("nawarat-bridge", "1954"),
    "night":     ("nawarat-bridge", "nawarat-bridge-1"),
    "reds":      ("songthaew-count", "red-car-chiang-mai-2"),
    "reds2":     ("rot-daeng", "rot-daeng-in-downtown"),
    "canal":     ("ring-3", "canal-in-chiang-mai"),
    "map1893":   ("era-1296-the-square", "1893"),
    "map1931":   ("era-siam-1900-1950", "1931"),
    "map1945":   ("what-a-road-does-to-an-old-city", "1945"),
    "walking":   ("sunday-walking-street", ""),
    "soi":       ("hom-the-lane", "moonmuang"),
    "cables":    ("hom-the-lane", "0182"),
    "traffic":   ("congestion-index", "chiangmai-traffic"),
    "katam":     ("katam-corner", "201703291051b"),
    "suandok":   ("suan-dok-gate", "201703291225a"),
    "airport":   ("chiang-mai-airport", "runway-aerial"),
    "route1095": ("route-1095", ""),
    "mekha":     ("mae-kha-canal", "khlong-mae-kha"),
    "station":   ("chiang-mai-station", ""),
    "map1890":   ("map-1890", ""),
    "mapams":    ("map-ams-chiang-mai", ""),
    "mapbock":   ("map-bock-1881", ""),
    "rapids":    ("ping-river", "athibai"),
    "oxcart":    ("thang", "pearl-of-asia"),
    "charoen":   ("thanon", "charoen-krung"),
}


def band_image(key: str):
    rid, frag = BANDS.get(key, (None, None))
    n = BY_ID.get(rid or "")
    ims = pictures(n) if n else []
    if not ims:
        return None
    if frag:
        for im in ims:
            if frag in im["file"]:
                return im
    return next((i for i in ims if i.get("primary")), ims[0])


def band(key: str, kicker: str, head: str, line: str = "", lang: str = "en",
         big: str = "", big_label: str = "", href: str = "", cta: str = "",
         cls: str = "") -> str:
    im = band_image(key)
    if not im:
        return ""
    inner = [f'<span class="kicker">{E(kicker)}</span>']
    if big:
        inner.append(f'<p class="big">{E(big)}'
                     f'{f"<small>{E(big_label)}</small>" if big_label else ""}</p>')
    if head:
        inner.append(f"<h2>{E(head)}</h2>")
    if line:
        inner.append(f"<p>{E(line)}</p>")
    if href and cta:
        inner.append(f'<a class="btn" href="{E(href)}">{E(cta)}</a>')
    return (f'<section class="band {cls}" style="background-image:url({E(img_url(im))})">'
            f'<div class="in">{"".join(inner)}</div>'
            f'<span class="cred">{credit(im, short=True)}</span></section>')


def slab(cells) -> str:
    return '<div class="slab">' + "".join(
        f"<div><b>{E(v)}</b><span>{E(l)}</span></div>" for v, l in cells) + "</div>"


def by_type(t: str) -> list:
    return [n for n in NODES if n["type"] == t]


def grid(nodes, lang, numbered=False) -> str:
    return '<div class="grid">' + "".join(
        node_card(n, lang, str(i + 1) if numbered else None) for i, n in enumerate(nodes)
    ) + "</div>"


def inline_svg(name: str, cls="mapsvg") -> str:
    f = SITE / name
    if not f.exists():
        return ""
    svg = f.read_text(encoding="utf-8")
    return svg.replace("<svg ", f'<svg class="{cls}" ', 1) if 'class="' not in svg[:200] else svg


def layered_map(base: str, overlay: str, alt: str) -> str:
    """The raster of every way, with the vector of the named things on top."""
    r = rel()
    return (f'<div class="mapwrap"><img class="lt" src="{r}{base}.png" alt="{E(alt)}" loading="lazy" decoding="async">'
            f'<img class="dk" src="{r}{base}-dark.png" alt="" loading="lazy" decoding="async">'
            f'{inline_svg(overlay)}</div>')


def mini_map(lat: float, lon: float) -> str:
    box = MAPS.get("box") or [18.62, 98.80, 18.96, 99.12]
    s, w, n, e = box
    if not (s <= lat <= n and w <= lon <= e):
        return ""
    import math
    kx = math.cos(math.radians((s + n) / 2))
    pad = 14 / 1400
    x = (pad + (lon - w) * kx * ((1 - 2 * pad) / ((e - w) * kx))) * 100
    y = (14 + (n - lat) * ((1400 - 28) / ((e - w) * kx))) / 1567 * 100
    r = rel()
    return (f'<div class="mini lt" style="background-image:url({r}roads.png)"><b style="left:{x:.1f}%;top:{y:.1f}%"></b></div>'
            f'<div class="mini dk" style="background-image:url({r}roads-dark.png)"><b style="left:{x:.1f}%;top:{y:.1f}%"></b></div>')


# ---------------------------------------------------------------- charts
def bars_svg(rows: list, unit="", w=760, rowh=28, left=210, cls="bar") -> str:
    """Horizontal bars: rows of (label, value)."""
    rows = [(l, v) for l, v in rows if isinstance(v, (int, float))]
    if not rows:
        return ""
    mx = max(v for _, v in rows) or 1
    h = rowh * len(rows) + 10
    out = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img">']
    for i, (l, v) in enumerate(rows):
        y = i * rowh + 5
        bw = (w - left - 90) * v / mx
        out.append(f'<text x="{left - 8}" y="{y + 18}" text-anchor="end">{E(clip(str(l), 30))}</text>'
                   f'<rect class="{cls}" x="{left}" y="{y + 4}" width="{bw:.1f}" height="{rowh - 8}"/>'
                   f'<text x="{left + bw + 6:.1f}" y="{y + 18}">{v:,.{0 if float(v).is_integer() else 1}f}{E(unit)}</text>')
    out.append("</svg>")
    return "".join(out)


def lines_svg(series: list, w=760, h=300, left=70) -> str:
    """series: list of {label, points:[(x, y)], color}. x numeric (years)."""
    pts = [p for s in series for p in s["points"]]
    if not pts:
        return ""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs); y1 = max(ys) * 1.05 or 1
    def X(x): return left + (x - x0) / ((x1 - x0) or 1) * (w - left - 20)
    def Y(y): return 20 + (1 - y / y1) * (h - 60)
    out = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img">'
           f'<line class="axis" x1="{left}" y1="{Y(0)}" x2="{w - 20}" y2="{Y(0)}"/>'
           f'<line class="axis" x1="{left}" y1="20" x2="{left}" y2="{Y(0)}"/>']
    for k in range(5):
        yv = y1 * k / 4
        out.append(f'<text x="{left - 6}" y="{Y(yv) + 4}" text-anchor="end">{yv:,.0f}</text>')
    for x in sorted(set(xs)):
        out.append(f'<text x="{X(x)}" y="{h - 22}" text-anchor="middle">{x}</text>')
    for i, s in enumerate(series):
        d = " ".join(f"{'M' if j == 0 else 'L'}{X(x):.1f} {Y(y):.1f}" for j, (x, y) in enumerate(s["points"]))
        out.append(f'<path class="ln" style="stroke:{s.get("color", "#b91c1c")}" d="{d}"/>')
        lx, ly = s["points"][-1]
        out.append(f'<text x="{X(lx) + 4:.1f}" y="{Y(ly) + 4:.1f}" style="font-size:11px">{E(clip(s["label"], 26))}</text>')
    out.append("</svg>")
    return "".join(out)


def timeline_svg(rows: list, w=900) -> str:
    """rows: (year, label, colour). A line from the first to the last, with ticks."""
    rows = sorted(rows, key=lambda r: r[0])
    if not rows:
        return ""
    y0, y1 = rows[0][0], rows[-1][0]
    def X(y): return 40 + (y - y0) / ((y1 - y0) or 1) * (w - 80)
    h = 40 + 26 * len(rows)
    out = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img"><line class="axis" x1="40" y1="20" x2="{w - 40}" y2="20"/>']
    for i, (y, l, c) in enumerate(rows):
        x = X(y); yy = 44 + 26 * i
        out.append(f'<line x1="{x:.0f}" y1="14" x2="{x:.0f}" y2="{yy - 8}" stroke="{c}" stroke-width="2" opacity=".6"/>'
                   f'<circle cx="{x:.0f}" cy="20" r="5" fill="{c}"/>'
                   f'<text x="{min(x, w - 260):.0f}" y="{yy + 4}"><tspan font-weight="800">{y}</tspan> {E(l)}</text>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- record page
def road_block(n: dict, lang: str) -> str:
    ui = UI[lang]
    rd = n.get("road") or {}
    if not rd:
        return ""
    cells = []
    if rd.get("ref"):
        cells.append((rd["ref"], ui["ref"]))
    if rd.get("km"):
        cells.append((f'{rd["km"]:,}', ui["km"]))
    if rd.get("lanes"):
        cells.append((rd["lanes"], ui["lanes"]))
    if rd.get("opened"):
        cells.append((rd["opened"], ui["opened"]))
    if rd.get("oneway"):
        cells.append(("→", "one-way" if lang == "en" else "ทางเดียว"))
    out = [slab(cells)] if cells else []
    frm = rd.get("from_th" if lang == "th" else "from") or rd.get("from")
    to = rd.get("to_th" if lang == "th" else "to") or rd.get("to")
    if frm or to:
        out.append(f'<p class="mute"><b>{E(ui["from"])}</b> {E(frm or "")} <b>{E(ui["to"])}</b> {E(to or "")}'
                   + (f' · <span class="small">{E(rd["km_source"])}</span>' if False else "") + "</p>")
    return "".join(out)


def figure_block(n: dict, lang: str) -> str:
    ui = UI[lang]
    f = n.get("figure") or {}
    if not f:
        return ""
    v = f.get("value")
    vs = f"{v:,}" if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)
    unit = f.get("unit_th" if lang == "th" else "unit") or f.get("unit") or ""
    out = [slab([(vs, unit)] + ([(f["year"], ui["year"])] if f.get("year") else []))]
    ser = f.get("series") or []
    num = [(s.get("label_th" if lang == "th" else "label") or s["label"], s["value"]) for s in ser if isinstance(s.get("value"), (int, float))]
    if len(num) >= 2:
        out.append(bars_svg(num))
    txt = [s for s in ser if not isinstance(s.get("value"), (int, float))]
    if txt:
        out.append('<div class="scroll"><table class="kv"><tbody>' + "".join(
            f'<tr><th>{E(s.get("label_th" if lang == "th" else "label") or s["label"])}</th><td>{E(s["value"])}'
            f'{" <span class=mute>" + E(s["note"]) + "</span>" if s.get("note") else ""}</td></tr>' for s in txt) + "</tbody></table></div>")
    m = f.get("method_th" if lang == "th" else "method")
    if m:
        out.append(f'<p class="small mute"><b>{E(ui["method"])}.</b> {E(m)}</p>')
    c = f.get("compare_th" if lang == "th" else "compare")
    if c:
        out.append(f'<p class="small mute"><b>{E(ui["compare"])}:</b> {E(c)}</p>')
    return "".join(out)


def plan_block(n: dict, lang: str) -> str:
    ui = UI[lang]
    p = n.get("plan") or {}
    if not p:
        return ""
    cells = [(p.get("status", ""), ui["status"])]
    if p.get("budget_thb"):
        b = p["budget_thb"]
        cells.append((f"{b / 1e6:,.0f}" if isinstance(b, (int, float)) else str(b), "million baht" if lang == "en" else "ล้านบาท"))
    if p.get("km"):
        cells.append((f'{p["km"]:,}', ui["km"]))
    if p.get("due"):
        cells.append((p["due"], ui["due"]))
    if p.get("as_of"):
        cells.append((p["as_of"], "as of" if lang == "en" else "ณ"))
    out = [slab(cells)]
    ag = p.get("agency_th" if lang == "th" else "agency")
    if ag:
        out.append(f'<p class="mute"><b>{E(ui["agency"])}</b> {E(ag)}' + (f' · {E(p["budget_note"])}' if p.get("budget_note") else "") + "</p>")
    return "".join(out)


def word_block(n: dict, lang: str) -> str:
    ui = UI[lang]
    w = n.get("word") or {}
    if not w:
        return ""
    rows = [(ui["script"], f'<span class="th" style="font-size:1.4em">{E(w.get("th", ""))}</span>'),
            (ui["rtgs"], f'<span class="mono">{E(w.get("rtgs", ""))}</span>'),
            (ui["sound"], f'<span class="mono">{E(w.get("ipa", ""))}</span>'),
            (ui["standard"], f'{E(w.get("standard", ""))} <span class="mono mute">{E(w.get("standard_rtgs", ""))}</span>'),
            (ui["gloss"], E(w.get("gloss_th" if lang == "th" else "gloss") or w.get("gloss", "")))]
    if w.get("tai_tham"):
        rows.append((ui["tt"], f'<span class="tt" lang="nod" style="font-size:1.5em">{E(w["tai_tham"])}</span>'))
    if w.get("example"):
        rows.append((ui["example"], f'{E(w["example"])} <span class="mute">— {E(w.get("example_gloss", ""))}</span>'))
    return '<div class="scroll"><table class="kv"><tbody>' + "".join(f"<tr><th>{E(k)}</th><td>{v}</td></tr>" for k, v in rows) + "</tbody></table></div>"


def node_page(n: dict, lang: str) -> str:
    ui = UI[lang]
    r = lroot(lang)
    ti = TYPE_INFO[n["type"]]
    name = T(n, "names.name", lang)
    kind = ti["th"] if lang == "th" else ti["one"]
    said = T(n, "names.said", lang)
    url = f"{CANONICAL_URL}/{'th/' if lang == 'th' else ''}{url_of(n)}"
    b = [f'<h1><span class="kind">{E(kind)}</span>{E(name)}</h1>']
    nm = n["names"]
    if lang == "en" and nm.get("th"):
        b.append(f'<p class="said th">{E(nm["th"])}'
                 f'{" · " + E(nm["rtgs"]) if nm.get("rtgs") else ""}</p>')
    if said:
        b.append(f'<p class="said">{E(said)}</p>')
    if n.get("needs_verification"):
        b.append(f'<div class="warn">{E(ui["unverified"])}</div>')
    ims = pictures(n)
    if ims:
        b.append(hero_shot(n))
    b.append(road_block(n, lang))
    b.append(figure_block(n, lang))
    b.append(plan_block(n, lang))
    b.append(word_block(n, lang))
    g = n.get("geo") or {}
    # a ring is 26 km long and a highway 350: a single pin on one is a lie about where
    # it is, so the pin and the coordinate are for records that sit at a place
    if g and g.get("precision", "exact") in ("exact", "street"):
        b.append(mini_map(g["lat"], g["lon"]))
        b.append(f'<p class="mute mono">{g["lat"]:.4f}, {g["lon"]:.4f} · '
                 f'<a href="https://www.openstreetmap.org/?mlat={g["lat"]}&mlon={g["lon"]}#map=15/'
                 f'{g["lat"]}/{g["lon"]}" rel="noopener">OpenStreetMap</a> · <a href="{r}map/">{E(ui["map"])}</a></p>')
    elif n["type"] in ("ring", "highway", "road"):
        b.append(f'<p class="mute small"><a href="{r}map/">{E("Where it runs, on the map" if lang == "en" else "มันวิ่งตรงไหน ดูแผนที่")}</a></p>')
    for key, label in (("what", ui["what"]), ("story", ui["story"]), ("how", ui["how"]),
                       ("today", ui["today"]), ("notes", ui["notes"])):
        txt = T(n, f"text.{key}", lang, fallback=False)
        miss = False
        if txt is None:
            txt = (n.get("text") or {}).get(key)
            miss = lang == "th" and bool(txt)
        if not txt:
            continue
        b.append(f"<h2>{E(label)}</h2>")
        if miss:
            b.append(f'<div class="warn">{E(ui["no_th"])}</div>')
        b.append(prose(txt))
    ety = n.get("etymology") or {}
    if ety.get("root"):
        b.append(f'<h2>{E("Root" if lang == "en" else "รากศัพท์")}</h2>'
                 f'<p class="root">{E(ety["root"])}</p>')
        if ety.get("note"):
            b.append(f'<p class="mute">{E(ety["note"])}</p>')
    if len(ims) > 1:
        b.append(shot_strip([i for i in ims if not i.get("primary")]))
    kin = [k for k in (n.get("kin") or []) if k["to"] in BY_ID]
    if kin:
        b.append(f'<h2>{E(ui["kin"])}</h2><ul class="kin">')
        for k in kin:
            t = BY_ID[k["to"]]
            b.append(f'<li><a href="{r}{url_of(t)}">{E(T(t, "names.name", lang))}</a> '
                     f'<span class="mute">{E(k["as"])}</span></li>')
        b.append("</ul>")
    kin_in = [k for k in (n.get("kin_in") or []) if k["from"] in BY_ID]
    if kin_in:
        b.append(f'<h2>{E(ui["said_here"])}</h2><ul class="kin">')
        for k in kin_in:
            t = BY_ID[k["from"]]
            b.append(f'<li><a href="{r}{url_of(t)}">{E(T(t, "names.name", lang))}</a> '
                     f'<span class="mute">{E(k["as"])}</span></li>')
        b.append("</ul>")
    if n.get("links"):
        b.append("<ul class=\"kin\">" + "".join(
            f'<li><a href="{E(l["url"])}" rel="noopener">{E(l.get("label") or l["url"])}</a></li>'
            for l in n["links"]) + "</ul>")
    b.append(prov_block(n, lang))
    b.append(f'<p class="mute small"><a href="{rel()}api/{n["type"]}/{n["id"]}.json">'
             f'{E("This record as JSON" if lang == "en" else "บันทึกนี้ในรูป JSON")}</a></p>')
    b.append(share_row(url, name, lang, T(n, "names.said", lang) or ""))
    return "".join(b)


# ---------------------------------------------------------------- type index, all, about
def type_index(t: str, lang: str) -> str:
    ti = TYPE_INFO[t]
    en = lang == "en"
    rows = by_type(t)
    b = [f'<h1>{E(ti["th"] if lang == "th" else ti["name"])}</h1>',
         f'<p class="lede">{E(ti["th_blurb"] if lang == "th" else ti["blurb"])}</p>']
    facet = (ti.get("group_by") or "").replace("facets.", "")
    spec = FACETS.get(facet)
    if spec and spec.get("values"):
        groups = {}
        for n in rows:
            v = (n.get("facets") or {}).get(facet) or "_"
            groups.setdefault(v, []).append(n)
        order = list(spec["values"]) + ["_"]
        for v in order:
            if v not in groups:
                continue
            label = spec["values"].get(v, "Everything else" if en else "อื่น ๆ")
            b.append(f'<h2>{E(label)}</h2>')
            b.append(grid(groups[v], lang))
    else:
        b.append(grid(rows, lang))
    b.append(share_row(f"{CANONICAL_URL}/{'th/' if lang == 'th' else ''}{DIR_OF[t]}/",
                       ti["th"] if lang == "th" else ti["name"], lang))
    return "".join(b)


def all_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    b = [f'<h1>{E("Everything" if en else "ทั้งหมด")}</h1>',
         f'<p class="lede">{COV["records"]} '
         f'{E("records, by type" if en else "บันทึก จัดตามประเภท")}</p>']
    for t in TYPES:
        rows = by_type(t)
        if not rows:
            continue
        ti = TYPE_INFO[t]
        b.append(f'<h2><a href="{r}{DIR_OF[t]}/">{E(ti["th"] if lang == "th" else ti["name"])}</a> '
                 f'<span class="n">{len(rows)}</span></h2><ul class="cols">')
        for n in sorted(rows, key=lambda x: (T(x, "names.name", lang) or "")):
            th = n["names"].get("th")
            thai = f' <span class="th mute">{E(th)}</span>' if th and lang == "en" else ""
            b.append(f'<li><a href="{r}{url_of(n)}">{E(T(n, "names.name", lang))}</a>{thai}</li>')
        b.append("</ul>")
    return "".join(b)


# ---------------------------------------------------------------- machine files
def icon_svg() -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            '<rect width="64" height="64" rx="10" fill="#17110c"/>'
            '<rect x="16" y="16" width="32" height="32" fill="none" stroke="#3b82f6" stroke-width="5"/>'
            '<circle cx="32" cy="32" r="24" fill="none" stroke="#e0322b" stroke-width="4"/>'
            '<circle cx="32" cy="32" r="4" fill="#f0a500"/></svg>')


def manifest() -> str:
    return json.dumps({"name": NAME["en"], "short_name": "CM Roads",
                       "start_url": BASE_PATH, "display": "standalone",
                       "background_color": "#fdfbf4", "theme_color": "#17110c",
                       "icons": [{"src": f"{BASE_PATH}icon.svg", "sizes": "any",
                                  "type": "image/svg+xml"}]}, ensure_ascii=False, indent=1)


def all_paths() -> list:
    paths = [""] + [p for p, _ in NAV[1:]] + ["all/", "about/"]
    paths += [f"{DIR_OF[t]}/" for t in TYPES if by_type(t)]
    paths += [url_of(n) for n in NODES]
    return list(dict.fromkeys(paths))


def robots() -> str:
    lines = ["User-agent: *", "Allow: /", f"Sitemap: {SITE_URL}/sitemap.xml"]
    return "\n".join(lines) + "\n"


def sitemap() -> str:
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.w3.org/1999/xhtml" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    out[1] = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'
    for p in all_paths():
        for lang in LANGS:
            loc = f"{SITE_URL}/{'th/' if lang == 'th' else ''}{p}"
            out.append(f"<url><loc>{E(loc)}</loc>"
                       f'<xhtml:link rel="alternate" hreflang="en" href="{E(SITE_URL)}/{E(p)}"/>'
                       f'<xhtml:link rel="alternate" hreflang="th" href="{E(SITE_URL)}/th/{E(p)}"/></url>')
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def feed() -> str:
    items = sorted(NODES, key=lambda n: n.get("updated", ""), reverse=True)[:40]
    out = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom">',
           f"<title>{E(NAME['en'])}</title>", f'<link href="{E(CANONICAL_URL)}/"/>',
           f"<id>{E(CANONICAL_URL)}/</id>", f"<updated>{E(COV['built'][:10])}T00:00:00Z</updated>"]
    for n in items:
        u = f"{CANONICAL_URL}/{url_of(n)}"
        out.append(f"<entry><title>{E(n['names']['name'])}</title><link href=\"{E(u)}\"/><id>{E(u)}</id>"
                   f"<updated>{E(n.get('updated', ''))}T00:00:00Z</updated>"
                   f"<summary>{E(clip((n.get('text') or {}).get('what', ''), 300))}</summary></entry>")
    out.append("</feed>")
    return "\n".join(out) + "\n"


def llms_txt() -> str:
    lines = [f"# {NAME['en']}", "", f"> {TAG['en']}", "",
             f"Canonical: {CANONICAL_URL}/ · Alternate: {SITE_URL}/ · Thai: {CANONICAL_URL}/th/",
             f"Records: {COV['records']} across {len(TYPES)} types, CC BY 4.0. API: {CANONICAL_URL}/api/",
             f"Network: {COV.get('ways', 0):,} OpenStreetMap ways, {COV.get('total_km', 0):,} km in the city box, "
             f"measured by zone at {CANONICAL_URL}/old-city/ and {CANONICAL_URL}/api/measures.json",
             f"Traffic: {COV.get('stations', 0)} highway counting stations at {CANONICAL_URL}/traffic/ and {CANONICAL_URL}/api/aadt.json",
             "", "## Pages"]
    for p, k in NAV:
        lines.append(f"- {UI['en'][k]}: {CANONICAL_URL}/{p}")
    lines += ["", "## Records by type"]
    for t in TYPES:
        rows = by_type(t)
        if rows:
            lines.append(f"- {TYPE_INFO[t]['name']} ({len(rows)}): {CANONICAL_URL}/{DIR_OF[t]}/")
    lines += ["", "## Full text", f"- {CANONICAL_URL}/llms-full.txt"]
    return "\n".join(lines) + "\n"


def llms_full() -> str:
    parts = [llms_txt(), "\n\n# Records\n"]
    for n in NODES:
        t = n.get("text") or {}
        parts.append(f"\n## {n['names']['name']} ({n['names'].get('th', '')}) — {n['type']}\n{CANONICAL_URL}/{url_of(n)}\n\n{t.get('what', '')}\n")
        if t.get("story"):
            parts.append(f"\n{t['story']}\n")
    return "".join(parts)


def humans_txt() -> str:
    return (f"/* {NAME['en']} */\n{TAG['en']}\n\nPublisher: NaN — https://wichaa.net\n"
            f"{fleet.maker_line(roster=FLEET)}\nData: OpenStreetMap (ODbL), DOH open data, DDC open data, Open-Meteo (CC BY 4.0), Wikimedia Commons\nBuilt: {COV['built']}\n")


def ai_txt() -> str:
    return (f"# ai.txt — {NAME['en']}\nContent-License: CC-BY-4.0\nData-License: ODbL-1.0 (OpenStreetMap-derived files), CC-BY-4.0 (records)\n"
            f"Attribution: NaN, https://wichaa.net; map data © OpenStreetMap contributors\nContact: nan@motdang.net\n")


def api_index() -> str:
    files = sorted(p.name for p in API.glob("*.json"))
    body = "<h1>API</h1><p>Every figure on the site, as JSON. Records CC BY 4.0; harvest-derived files carry their own licence inside.</p><ul>" + "".join(
        f'<li><a href="{rel()}api/{E(f)}">{E(f)}</a></li>' for f in files) + "</ul>"
    return page("API — " + NAME["en"], body, 1, "en", desc="JSON files behind the site", path="api/")


COPY_JS = """document.addEventListener("click",function(e){
var b=e.target.closest("[data-copy]");if(!b)return;
var u=b.getAttribute("data-copy");
function done(){var s=b.querySelector("span");var o=s.textContent;s.textContent="✓";setTimeout(function(){s.textContent=o},1400)}
if(navigator.clipboard){navigator.clipboard.writeText(u).then(done,function(){prompt("Copy:",u)})}else{prompt("Copy:",u)}
});"""


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


KEEP = {"terrain.png", "terrain-dark.png", "roads.png", "roads-dark.png", "city.svg", "oldcity.svg",
        "roses.svg", "eras.svg", "region.png", "region-dark.png", "region.svg", "cards"}


def main() -> int:
    sys.modules["site_roads"] = sys.modules[__name__]
    import pages
    if SITE.exists():
        for child in SITE.iterdir():
            if child.name in KEEP:
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    SITE.mkdir(parents=True, exist_ok=True)

    n_pages = 0
    for lang in LANGS:
        base = SITE / ("th" if lang == "th" else "")
        ui = UI[lang]
        ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": NAME[lang],
               "url": f"{CANONICAL_URL}/", "inLanguage": lang, "author": AUTHOR,
               "license": DATA_LICENSE},
              fleet.publisher_ld(roster=FLEET),
              {"@context": "https://schema.org", "@type": "WebPage",
               "creator": MAKER, "inLanguage": lang}]
        specials = [
            ("", pages.front, ui["home"], f"{NAME[lang]} — {TAG[lang]}", "home", "index"),
            ("map/", pages.map_page, ui["map"], None, "map", "map"),
            ("rings/", pages.rings_page, ui["rings"], None, "rings", "rings"),
            ("old-city/", pages.oldcity_page, ui["oldcity"], None, "oldcity", "old-city"),
            ("old-maps/", pages.maps_page, ui["oldmaps"], None, "oldmaps", "old-maps"),
            ("highways/", pages.highways_page, ui["highways"], None, "highways", "highways"),
            ("timeline/", pages.timeline_page, ui["timeline"], None, "timeline", "timeline"),
            ("plans/", pages.plans_page, ui["plans"], None, "plans", "plans"),
            ("traffic/", pages.traffic_page, ui["traffic"], None, "traffic", "traffic"),
            ("numbers/", pages.numbers_page, ui["numbers"], None, "numbers", "numbers"),
            ("words/", pages.words_page, ui["words"], None, "words", "words"),
            ("stories/", pages.stories_page, ui["stories"], None, "stories", "stories"),
            ("quiz/", pages.quiz_page, ui["quiz"], None, "quiz", "quiz"),
            ("all/", all_page, ui["all"], None, "", "index"),
            ("about/", pages.about, ui["about"], None, "", "index"),
        ]
        for path, fn, label, title, cur, card in specials:
            body = fn(lang)
            t = title or f"{label} — {NAME[lang]}"
            desc = TAG[lang] if path == "" else f"{label} — {NAME[lang]}"
            write(base / path / "index.html",
                  page(t, body, 0 if path == "" else 1, lang, desc=desc, jsonld=ld,
                       cur=cur, path=path, card=card if (SITE / "cards" / f"{card}.jpg").exists() or card == "index" else "index"))
            n_pages += 1
        special_paths = {x[0] for x in specials}
        for t in TYPES:
            if not by_type(t) or f"{DIR_OF[t]}/" in special_paths:
                continue
            ti = TYPE_INFO[t]
            label = ti["th"] if lang == "th" else ti["name"]
            write(base / DIR_OF[t] / "index.html",
                  page(f"{label} — {NAME[lang]}", type_index(t, lang), 1, lang,
                       desc=ti["th_blurb"] if lang == "th" else ti["blurb"],
                       jsonld=ld, path=f"{DIR_OF[t]}/", card=DIR_OF[t]
                       if (SITE / "cards" / f"{DIR_OF[t]}.jpg").exists() else "index"))
            n_pages += 1
        for n in NODES:
            name = T(n, "names.name", lang)
            desc = clip(T(n, "text.what", lang) or "", 180)
            nld = [{"@context": "https://schema.org", "@type": "Article",
                    "headline": name, "inLanguage": lang,
                    "url": f"{CANONICAL_URL}/{'th/' if lang == 'th' else ''}{url_of(n)}",
                    "author": AUTHOR, "creator": MAKER, "license": DATA_LICENSE,
                    "dateModified": n.get("updated", "")}]
            write(base / url_of(n) / "index.html",
                  page(f"{name} — {NAME[lang]}", node_page(n, lang), 2, lang, desc=desc,
                       jsonld=nld, path=url_of(n), card=n["id"]
                       if (SITE / "cards" / f"{n['id']}.jpg").exists() else "index"))
            n_pages += 1

    # assets and machine files
    if (ROOT / "data" / "images").exists():
        for d in (ROOT / "data" / "images").iterdir():
            if d.is_dir() and not d.name.startswith("_"):
                shutil.copytree(d, SITE / "images" / d.name, dirs_exist_ok=True)
                for j in (SITE / "images" / d.name).glob("*.json"):
                    j.unlink()
    shutil.copytree(API, SITE / "api", dirs_exist_ok=True)
    write(SITE / "api" / "index.html", api_index())
    write(SITE / "icon.svg", icon_svg())
    write(SITE / "manifest.webmanifest", manifest())
    write(SITE / "robots.txt", robots())
    write(SITE / "sitemap.xml", sitemap())
    write(SITE / "feed.xml", feed())
    write(SITE / "llms.txt", llms_txt())
    write(SITE / "llms-full.txt", llms_full())
    write(SITE / "humans.txt", humans_txt())
    write(SITE / "ai.txt", ai_txt())
    write(SITE / "copy.js", COPY_JS)
    write(SITE / ".basepath", BASE_PATH)
    shutil.copy(ROOT / "schema" / "node.schema.json", SITE / "api" / "node.schema.json")
    fleet.decorate(SITE, SELF)
    write(SITE / "404.html", page("Not found — " + NAME["en"],
                                  f'<h1>Not here</h1><p>Nothing at this address. <a href="{BASE_PATH}">The roads</a> · <a href="{BASE_PATH}all/">Everything</a></p>',
                                  1, "en", desc="Not found", path="404.html"))
    print(f"site: {n_pages} pages in {len(LANGS)} languages → {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
