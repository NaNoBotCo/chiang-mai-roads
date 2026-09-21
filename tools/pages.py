# -*- coding: utf-8 -*-
"""pages.py — the site's assembled pages. site.py imports this and calls each with a
language; every helper it needs lives in site.py, so this module imports that one."""
from __future__ import annotations

import site_roads as S  # noqa: E402  (site.py registers itself under this name before importing us)

E, T, prose, band, slab, grid, by_type, BY_ID = S.E, S.T, S.prose, S.band, S.slab, S.grid, S.by_type, S.BY_ID
lroot, url_of, share_row, inline_svg, layered_map = S.lroot, S.url_of, S.share_row, S.inline_svg, S.layered_map
bars_svg, lines_svg, timeline_svg, clip = S.bars_svg, S.lines_svg, S.timeline_svg, S.clip
M, AADT, DEATHS, TOMTOM, COV, MAPS, UI, NAME, TAG, CANONICAL_URL = S.M, S.AADT, S.DEATHS, S.TOMTOM, S.COV, S.MAPS, S.UI, S.NAME, S.TAG, S.CANONICAL_URL

ZONE_ORDER = ["moat", "ring1", "ring2", "ring3", "beyond"]


def _z(z):
    return (M.get("zones") or {}).get(z) or {}


def _n(v, d=0):
    return "—" if v is None else (f"{v:,.{d}f}" if isinstance(v, (int, float)) else str(v))


def _pct(v):
    return "—" if v is None else f"{v * 100:.0f}%"


def ids(*xs):
    return [BY_ID[x] for x in xs if x in BY_ID]


def hdr(en, th, lang, lede_en="", lede_th=""):
    b = [f"<h1>{E(en if lang == 'en' else th)}</h1>"]
    if lede_en:
        b.append(f'<p class="lede">{E(lede_en if lang == "en" else lede_th)}</p>')
    return "".join(b)


def share(path, en, th, lang):
    return share_row(f"{CANONICAL_URL}/{'th/' if lang == 'th' else ''}{path}", en if lang == "en" else th, lang)


# ---------------------------------------------------------------- front
def front(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    mo, r3 = _z("moat"), _z("ring3")
    b = [f'<h1>{E("Roads of Chiang Mai" if en else "ถนนหนทางเจียงใหม่")}</h1>',
         f'<p class="lede">{E(TAG[lang])}</p>']
    b.append(slab([
        ("1296", "the square" if en else "สี่เหลี่ยม"),
        ("4", "rings" if en else "วงแหวน"),
        (f"{M.get('drive_km', 0):,.0f}", "km of road, counted" if en else "กม. ถนน นับแล้ว"),
        (f"{M.get('intersections', 0):,}", "intersections" if en else "ทางแยก"),
        (f"{(M.get('soi') or {}).get('named_count', 0):,}", "named sois" if en else "ซอยที่มีชื่อ"),
        (f"{COV.get('stations', 0)}", "counting stations" if en else "จุดนับรถ"),
    ]))
    b.append(band("moat",
                  "Start with the water" if en else "เริ่มที่น้ำ",
                  "A square drawn in 1296, and every road since has had to deal with it" if en else "สี่เหลี่ยมที่ขีดไว้ปี 1839 และถนนทุกสายตั้งแต่นั้นต้องมาว่ากับมัน",
                  ("6.54 km of moat, five gates, four corners, two one-way loops. The old city is the ruler everything on this site is measured against." if en else
                   "คู 6.54 กม. ห้าประตู สี่แจ่ง วงทางเดียวสองวง เวียงเก่าคือไม้บรรทัดที่ทุกอย่างบนเว็บนี้ถูกวัดเทียบ"),
                  lang=lang, href=f"{r}old-city/", cta=("The old city, measured" if en else "เวียงเก่า วัดแล้ว")))

    b.append(f'<h2>{E("The map" if en else "แผนที่")}</h2>')
    b.append(layered_map("roads", "city.svg", "Every road in the city box over shaded relief, with the moat and the three rings drawn on top"))
    b.append(f'<p><a class="btn" href="{r}map/">{E("All the maps" if en else "แผนที่ทั้งหมด")}</a></p>')

    if mo.get("orientation", {}).get("phi") is not None:
        b.append(band("map1893",
                      "Counted for this site" if en else "นับขึ้นเพื่อเว็บนี้",
                      ("The oldest neighbourhood is the best connected" if en else "ย่านที่เก่าสุดเชื่อมกันดีสุด"),
                      (f"Grid score inside the moat {mo['orientation']['phi']:.2f}, outer ring {r3.get('orientation', {}).get('phi', 0):.2f}. "
                       f"Intersections per km²: {_n(mo.get('inter_per_km2'))} inside, {_n(r3.get('inter_per_km2'))} out at the third ring. "
                       f"Dead ends: {_pct(mo.get('dead_end_share'))} of lane ends inside, {_pct(r3.get('dead_end_share'))} out there." if en else
                       f"คะแนนตารางในคู {mo['orientation']['phi']:.2f} วงแหวนรอบนอก {r3.get('orientation', {}).get('phi', 0):.2f} "
                       f"ทางแยกต่อตารางกิโลเมตร ในเวียง {_n(mo.get('inter_per_km2'))} ที่วงสาม {_n(r3.get('inter_per_km2'))} "
                       f"ทางตัน ในเวียง {_pct(mo.get('dead_end_share'))} ข้างนอก {_pct(r3.get('dead_end_share'))}"),
                      lang=lang, big=f"{mo['orientation']['phi']:.2f}", big_label=("grid score, inside the moat (1 = perfect grid)" if en else "คะแนนตาราง ในเวียง (1 = ตารางสมบูรณ์)"),
                      href=f"{r}stories/what-a-road-does-to-an-old-city/", cta=("What a road does to an old city" if en else "ถนนทำอะไรกับเมืองเก่า")))

    b.append(f'<h2>{E("Start here" if en else "เริ่มที่นี่")}</h2>')
    b.append(grid(ids("moat-loop", "ring-1", "ring-2", "ring-3", "hom-the-lane", "tha-phae-road", "nimmanhaemin-road", "si-wichai-road"), lang))

    top = (AADT.get("ladder") or [{}])[0]
    b.append(band("traffic",
                  "The count" if en else "การนับ",
                  (f"{top.get('aadt', 0):,} vehicles a day on Mahidol Road" if en else f"{top.get('aadt', 0):,} คันต่อวันบนถนนมหิดล"),
                  (f"The highway department counts at {COV.get('stations', 0)} stations in the province and leaves the motorcycle out of the headline. "
                   f"Deaths: {(DEATHS.get('rows') or [{}])[-2].get('deaths', '—') if len(DEATHS.get('rows', [])) > 1 else '—'} in 2024, four in five on a motorcycle." if en else
                   f"กรมทางหลวงนับที่ {COV.get('stations', 0)} สถานีในจังหวัดและตัดมอเตอร์ไซค์ออกจากพาดหัว "
                   f"ผู้เสียชีวิต {(DEATHS.get('rows') or [{}])[-2].get('deaths', '—') if len(DEATHS.get('rows', [])) > 1 else '—'} คนปี 2567 สี่ในห้าอยู่บนมอเตอร์ไซค์"),
                  lang=lang, href=f"{r}traffic/", cta=("Traffic" if en else "จราจร")))

    b.append(f'<h2>{E("What this holds" if en else "เว็บนี้มีอะไร")}</h2>')
    cards = []
    for t in S.TYPES:
        rows = by_type(t)
        if not rows:
            continue
        ti = S.TYPE_INFO[t]
        cards.append(
            f'<article class="card"><h3><a href="{r}{S.DIR_OF[t]}/">'
            f'{E(ti["th"] if lang == "th" else ti["name"])}</a> '
            f'<span class="n">{len(rows)}</span></h3>'
            f'<p>{E(ti["th_blurb"] if lang == "th" else ti["blurb"])}</p></article>')
    b.append('<div class="grid">' + "".join(cards) + "</div>")

    b.append(band("trees",
                  "The exception" if en else "ข้อยกเว้น",
                  "A thousand trees, saved by a bypass" if en else "ต้นยางพันต้น รอดเพราะทางเลี่ยง",
                  ("The yang-na on the Lamphun road were planted in 1882 for an emperor's commissioner. They are alive because the Superhighway took the Bangkok traffic off them in 1969." if en else
                   "ยางนาบนถนนลำพูนปลูกปี 2425 ให้ข้าหลวงของสยาม มันยังอยู่เพราะซุปเปอร์ไฮเวย์เอารถกรุงเทพฯ ออกไปปี 2512"),
                  lang=lang, href=f"{r}stories/the-trees-on-the-lamphun-road/", cta=("The trees" if en else "ต้นยาง")))

    b.append(band("monk",
                  "1935" if en else "2478",
                  "Eleven and a half kilometres up a mountain, by hand, in five months and twenty-two days" if en else "สิบเอ็ดกิโลครึ่งขึ้นดอย ด้วยมือ ห้าเดือนยี่สิบสองวัน",
                  ("The only road in the catalogue built by a congregation. Sixty-seven metres of mountain road a day." if en else "ถนนสายเดียวในบัญชีที่ศรัทธาสร้าง ถนนภูเขาวันละหกสิบเจ็ดเมตร"),
                  lang=lang, big="11.53", big_label="km", href=f"{r}stories/the-monk-who-built-a-road/", cta=("The monk's road" if en else "ถนนครูบา")))

    b.append(band("nawarat",
                  "5 October 2024" if en else "5 ตุลาคม 2567",
                  "5.30 m at noon, and the busiest road in the north under water" if en else "5.30 เมตรตอนเที่ยง และถนนตี้รถนักสุดของภาคเหนือจมน้ำ",
                  ("The founders built a kilometre from the bank because of exactly this. The square stayed dry." if en else "ผู้สร้างเมืองสร้างห่างตลิ่งหนึ่งกิโลเพราะสิ่งนี้แหละ สี่เหลี่ยมยังแห้ง"),
                  lang=lang, href=f"{r}stories/the-day-the-river-came-up-tha-phae/", cta=("The flood, as a list of roads" if en else "น้ำท่วม ในรูปรายการถนน")))

    b.append(band("map1890",
                  "On paper" if en else "บนกระดาษ",
                  "Sixteen sheets, 1693 to 1959, at the size they can be read at" if en else "สิบหกแผ่น ตั้งแต่ พ.ศ. 2236 ถึง 2502 ในขนาดที่อ่านออก",
                  ("The 1931 city map labels the moat KOO VIENG CANAL and names a gate after a short bridge. The 1945 sheet "
                   "was compiled from air photographs taken that March." if en else
                   "แผนที่เมืองปี 2474 กำกับคูเมืองว่า KOO VIENG CANAL และตั้งชื่อประตูตามขัวสั้น แผ่นปี 2488 จัดทำจากภาพถ่ายทางอากาศเดือนมีนาคมปีนั้น"),
                  lang=lang, big="1693", big_label=("the oldest sheet" if en else "แผ่นเก่าสุด"),
                  href=f"{r}old-maps/", cta=("The old maps" if en else "แผนที่เก่า")))

    b.append(f'<h2>{E("Fun" if en else "สนุก")}</h2>')
    b.append(f'<p><a class="btn" href="{r}quiz/">{E("Which Chiang Mai road are you?" if en else "คุณเป็นถนนสายไหนของเจียงใหม่")}</a> '
             f'<a class="btn" href="{r}words/">{E("Say it in Kam Mueang" if en else "อู้กำเมือง")}</a></p>')
    b.append(share_row(f"{CANONICAL_URL}/{'th/' if lang == 'th' else ''}", NAME[lang], lang, TAG[lang]))
    return "".join(b)


# ---------------------------------------------------------------- map
LEGEND = [("#c83c28", "motorway · trunk"), ("#d76e28", "primary"), ("#be963c", "secondary"), ("#78685a", "tertiary"),
          ("#5a554b", "residential · unclassified"), ("#6e695f", "service"), ("#e628a0", "under construction")]


def map_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    b = [hdr("The map", "แผนที่", lang,
             f"{M.get('ways', 0):,} ways from OpenStreetMap, {M.get('total_km', 0):,.0f} km, drawn over the relief. Rasters where the count would sink a vector, vectors where there is a name to read.",
             f"{M.get('ways', 0):,} เส้นทางจาก OpenStreetMap {M.get('total_km', 0):,.0f} กม. วาดบนภูมิประเทศ ราสเตอร์ตรงที่จำนวนจะจมเวกเตอร์ เวกเตอร์ตรงที่มีชื่อให้อ่าน")]
    b.append(f'<h2>{E("The city and its rings" if en else "เมืองและวงแหวน")}</h2>')
    b.append(layered_map("roads", "city.svg", "Every road in the city box over shaded relief"))
    b.append('<div class="legend">' + "".join(f'<span><i style="background:{c}"></i>{E(l)}</span>' for c, l in LEGEND)
             + '<span><i style="background:#1d4ed8"></i>moat loop</span><span><i style="background:#b91c1c"></i>ring 1</span>'
             + '<span><i style="background:#b45309"></i>ring 2</span><span><i style="background:#15803d"></i>ring 3</span><span><i style="background:#3b82f6"></i>water</span></div>')
    b.append(f'<h2>{E("Inside the moat, every lane" if en else "ในคู ทุกฮ่อม")}</h2>')
    oc = MAPS.get("oldcity") or {}
    nl, nm, nw = oc.get("lanes", 0), oc.get("major", 0), oc.get("wats", 0)
    b.append('<p class="mute">' + E(f"{nl} lanes, {nm} main streets, {nw} wats inside the square; dashed blue is one-way." if en else f"ฮ่อม {nl} สาย ถนนหลัก {nm} สาย วัด {nw} วัดในสี่เหลี่ยม เส้นประน้ำเงินคือทางเดียว") + "</p>")
    b.append(f'<div class="plain">{inline_svg("oldcity.svg")}</div>')
    b.append(f'<h2>{E("Which way the streets run" if en else "ถนนหันไปทางไหน")}</h2>')
    b.append(f'<p class="mute">{E("One rose per zone. A grid shows as four spikes; a city that grew along whatever track was there shows as a blur. Boeing’s method, 36 bins, each way weighted by its length." if en else "หนึ่งดอกกุหลาบต่อโซน ตารางแสดงเป็นสี่แฉก เมืองที่โตตามทางที่มีอยู่แสดงเป็นเบลอ วิธีของ Boeing 36 ช่อง แต่ละเส้นถ่วงด้วยความยาว")}</p>')
    b.append(f'<div class="plain">{inline_svg("roses.svg")}</div>')
    b.append(f'<h2>{E("Coloured by the era that built it" if en else "ระบายสีตามยุคที่สร้าง")}</h2>')
    eras = [("mangrai", "1296"), ("kawila", "1796–1900"), ("siam", "1900–1950"), ("srivichai", "1935"), ("superhighway", "1960s–70s"), ("rings", "1984–2006"), ("now", "2010s–")]
    b.append('<div class="era-strip">' + "".join('<span style="background:' + _era_col(k) + '">' + E(l) + "</span>" for k, l in eras) + "</div>")
    b.append(layered_map("roads", "eras.svg", "Named roads coloured by era"))
    b.append(f'<p class="mute small">{E("Only the roads with a record on this site are coloured; the grey underneath is everything else. A road built in one era and widened in another wears the era it was built." if en else "ระบายสีเฉพาะถนนที่มีบันทึกบนเว็บนี้ สีเทาข้างใต้คือที่เหลือ ถนนที่สร้างยุคหนึ่งและขยายอีกยุคใส่สียุคที่สร้าง")}</p>')
    if (S.SITE / "region.png").exists():
        b.append(f'<h2>{E("The roads out" if en else "ถนนออกเมือง")}</h2>')
        b.append(layered_map("region", "region.svg", "The intercity roads from Chiang Mai"))
    b.append(f'<h2>{E("How the maps were made" if en else "ทำแผนที่อย่างไร")}</h2>')
    b.append(prose(("Every way tagged highway in a box from Mae Rim to Saraphi and Doi Suthep to San Kamphaeng, fetched from OpenStreetMap by Overpass in a hundred tiles and cached. The relief is Copernicus DEM sampled at 4,485 points through Open-Meteo, shaded and tinted. One equirectangular projection scaled by the cosine of the latitude serves every map, so an overlay lines up with its base by construction. The measurements page says what was counted on it." if en else
                    "ทุกเส้นทางที่ติดแท็ก highway ในกรอบจากแม่ริมถึงสารภี และดอยสุเทพถึงสันกำแพง ดึงจาก OpenStreetMap ผ่าน Overpass เป็นร้อยช่องและเก็บไว้ ภูมิประเทศคือ Copernicus DEM สุ่ม 4,485 จุดผ่าน Open-Meteo แรเงาและย้อมสี ใช้การฉายแบบ equirectangular ปรับด้วยโคไซน์ละติจูดเดียวสำหรับทุกแผนที่ ชั้นทับจึงตรงกับพื้นโดยการสร้าง หน้าการวัดบอกว่านับอะไรบนมัน")))
    b.append(share("map/", "The map", "แผนที่", lang))
    return "".join(b)


def _era_col(k):
    from maps import ERA_COLOUR
    return ERA_COLOUR.get(k, "#333")


# ---------------------------------------------------------------- rings
def rings_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    b = [hdr("Rings", "วงแหวน", lang,
             "The moat loop and three rings around it, each a decision about where the city ends, each overtaken by the city in ten to fifteen years.",
             "วงรอบคูเมืองและวงแหวนสามวงรอบมัน แต่ละวงคือการตัดสินใจว่าเมืองจบตรงไหน แต่ละวงถูกเมืองโตข้ามในสิบถึงสิบห้าปี")]
    b.append(layered_map("roads", "city.svg", "The rings"))
    rows = ids("moat-loop", "ring-1", "ring-2", "ring-3", "ring-4")
    cells = []
    for n in rows:
        rd = n.get("road") or {}
        cells.append((f'{rd.get("km", (n.get("plan") or {}).get("km", "—"))}', T(n, "names.name", lang).split(",")[0]))
    b.append(slab(cells))
    b.append('<div class="scroll"><table><thead><tr><th>' + ("Ring" if en else "วง") + "</th><th>km</th><th>" + ("lanes" if en else "ช่อง") + "</th><th>" + ("opened" if en else "เปิด") + "</th><th>" + ("zone, measured" if en else "โซนที่วัด") + "</th><th>" + ("intersections / km²" if en else "แยก / ตร.กม.") + "</th><th>" + ("dead ends" if en else "ทางตัน") + "</th><th>" + ("grid score" if en else "คะแนนตาราง") + "</th></tr></thead><tbody>")
    for n, z in zip(rows, ZONE_ORDER):
        rd = n.get("road") or {}
        zo = _z(z)
        b.append(f'<tr><td><a href="{r}{url_of(n)}">{E(T(n, "names.name", lang))}</a></td><td>{E(rd.get("km", (n.get("plan") or {}).get("km", "")))}</td><td>{E(rd.get("lanes", ""))}</td><td>{E(rd.get("opened", ""))}</td>'
                 f'<td>{E(zo.get("label_th" if lang == "th" else "label", ""))}</td><td>{_n(zo.get("inter_per_km2"), 1)}</td><td>{_pct(zo.get("dead_end_share"))}</td><td>{_n((zo.get("orientation") or {}).get("phi"), 2)}</td></tr>')
    b.append("</tbody></table></div>")
    b.append(f'<p class="mute small">{E("The zone a ring is measured against is a radius from the moat’s centre, not the ring’s own line; the measurements page explains." if en else "โซนที่ใช้วัดแต่ละวงคือรัศมีจากกลางคู ไม่ใช่แนวของวงเอง หน้าการวัดอธิบาย")}</p>')
    b.append(band("canal", "Ring 3" if en else "วงสาม", "52.96 km, and five interchanges for 3,145 million baht" if en else "52.96 กิโล และทางแยกต่างระดับห้าแห่ง 3,145 ล้านบาท",
                  "The west side runs along the irrigation canal under Doi Suthep. An elevated road on top of it is under study, and the objection on record is the view." if en else "ด้านตะวันตกวิ่งเลียบคลองชลประทานใต้ดอยสุเทพ ทางยกระดับบนมันอยู่ระหว่างศึกษา และข้อคัดค้านที่บันทึกไว้คือวิว",
                  lang=lang, href=f"{r}rings/ring-3/", cta=("Route 121" if en else "ทางหลวง 121")))
    b.append(grid(rows, lang))
    b.append(f'<h2>{E("The junctions the rings go under" if en else "แยกที่วงแหวนลอดใต้")}</h2>')
    b.append(grid(by_type("junction"), lang))
    b.append(share("rings/", "Rings", "วงแหวน", lang))
    return "".join(b)


# ---------------------------------------------------------------- old city and measurements
def zone_table(lang: str) -> str:
    en = lang == "en"
    cols = [("drive_km", "km of road" if en else "กม.ถนน", 1), ("km_per_km2", "km per km²" if en else "กม./ตร.กม.", 1),
            ("inter_per_km2", "intersections / km²" if en else "แยก/ตร.กม.", 1), ("dead_end_share", "dead-end share" if en else "สัดส่วนทางตัน", "p"),
            ("block_m_median", "median block, m" if en else "บล็อกมัธยฐาน ม.", 0), ("phi", "grid score φ" if en else "คะแนนตาราง φ", 2),
            ("oneway_share", "one-way" if en else "ทางเดียว", "p"), ("soi_share", "km named soi" if en else "กม.ที่ชื่อซอย", "p"),
            ("named_share", "named" if en else "มีชื่อ", "p"), ("wats", "wats" if en else "วัด", 0), ("signals", "signals" if en else "ไฟสัญญาณ", 0)]
    out = ['<div class="scroll"><table class="ladder"><thead><tr><th>' + ("zone" if en else "โซน") + "</th><th>" + ("area km²" if en else "พื้นที่ ตร.กม.") + "</th>" + "".join(f"<th>{E(l)}</th>" for _, l, _ in cols) + "</tr></thead><tbody>"]
    for z in ZONE_ORDER:
        zo = _z(z)
        if not zo:
            continue
        out.append(f'<tr><td><b>{E(zo.get("label_th" if lang == "th" else "label"))}</b></td><td class="num">{_n(zo.get("area_km2"), 1)}</td>')
        for k, _, d in cols:
            v = (zo.get("orientation") or {}).get("phi") if k == "phi" else zo.get(k)
            out.append(f'<td class="num">{_pct(v) if d == "p" else _n(v, d)}</td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def oldcity_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    mo = _z("moat")
    b = [hdr("The old city, measured", "เวียงเก่า วัดแล้ว", lang,
             "The square inside the moat against the rings outside it, on the same questions: how connected, how many dead ends, how long a block, how much of a grid.",
             "สี่เหลี่ยมในคูเทียบวงแหวนข้างนอก ด้วยคำถามเดียวกัน เชื่อมกันแค่ไหน ทางตันกี่สาย บล็อกยาวเท่าไร เป็นตารางแค่ไหน")]
    b.append(slab([(_n(mo.get("drive_km"), 1), "km of road inside the moat" if en else "กม.ถนนในคู"),
                   (_n(mo.get("intersections")), "intersections" if en else "ทางแยก"),
                   (_pct(mo.get("dead_end_share")), "dead ends" if en else "ทางตัน"),
                   (_n((mo.get("orientation") or {}).get("phi"), 2), "grid score" if en else "คะแนนตาราง"),
                   (_n(mo.get("wats")), "wats" if en else "วัด"),
                   (_pct(mo.get("oneway_share")), "one-way" if en else "ทางเดียว")]))
    b.append(f'<div class="plain">{inline_svg("oldcity.svg")}</div>')
    b.append(f'<h2>{E("Zone by zone" if en else "ทีละโซน")}</h2>')
    b.append(zone_table(lang))
    b.append(prose(("**How to read it.** The moat zone is the square itself. The rings are bands of distance from the square’s centre: to 3 km, where the Superhighway and the canal road close a ring; 3 to 5.5 km for the middle ring; 5.5 to 9 km for the outer; then the rest of the box. A band is a stand-in for the road, chosen so the same arithmetic runs everywhere.\n\n**The grid score** is Boeing’s φ: the entropy of street bearings in 36 bins over a half-circle, each way weighted by length, rescaled so 1 is a perfect grid and 0 is every direction equally. **Dead-end share** is nodes of degree one divided by nodes of degree one plus nodes of degree three or more, on the drivable network without service lanes. **Block length** is the median run between two intersections. All of it is OpenStreetMap, which means all of it is a floor: a lane nobody has drawn does not count." if en else
                    "**อ่านอย่างไร** โซนคูคือสี่เหลี่ยมเอง วงแหวนคือแถบระยะจากกลางสี่เหลี่ยม ถึง 3 กม. ตี้ซุปเปอร์ไฮเวย์และถนนคลองชลประทานปิดวง 3 ถึง 5.5 กม. สำหรับวงกลาง 5.5 ถึง 9 กม. สำหรับวงนอก แล้วที่เหลือของกรอบ แถบคือตัวแทนของถนน เลือกให้เลขคณิตเดียวกันวิ่งได้ทุกที่\n\n**คะแนนตาราง** คือ φ ของ Boeing เอนโทรปีของทิศถนนใน 36 ช่องบนครึ่งวงกลม แต่ละเส้นถ่วงด้วยความยาว ปรับให้ 1 คือตารางสมบูรณ์ 0 คือทุกทิศเท่ากัน **สัดส่วนทางตัน** คือจุดดีกรีหนึ่งหารด้วยจุดดีกรีหนึ่งบวกจุดดีกรีสามขึ้นไป บนโครงข่ายรถวิ่งได้ไม่รวมทางบริการ **ความยาวบล็อก** คือมัธยฐานของช่วงระหว่างสองแยก ทั้งหมดคือ OpenStreetMap ซึ่งแปลว่าทั้งหมดคือค่าต่ำสุด ฮ่อมที่ไม่มีใครวาดไม่ถูกนับ")))
    b.append(f'<div class="plain">{inline_svg("roses.svg")}</div>')
    b.append(band("thaphae", "The finding" if en else "ข้อค้นพบ", "Seven centuries of building have not laid out a neighbourhood as well-connected as the first one" if en else "การสร้างเจ็ดศตวรรษยังวางย่านที่เชื่อมกันดีเท่าย่านแรกบ่ได้",
                  "" , lang=lang, href=f"{r}stories/what-a-road-does-to-an-old-city/", cta=("The argument" if en else "ข้อโต้แย้ง")))
    b.append(f'<h2>{E("Gates and corners" if en else "ประตูและแจ่ง")}</h2>')
    b.append(grid(by_type("gate"), lang))
    b.append(f'<h2>{E("Lanes and alleys" if en else "ฮ่อมและซอย")}</h2>')
    soi = M.get("soi") or {}
    b.append(slab([(_n(soi.get("named_count")), "named sois on the map" if en else "ซอยที่มีชื่อบนแผนที่"), (_n(soi.get("km"), 0), "km of them" if en else "กม."),
                   (_n(soi.get("with_wat_in_name")), "named after a wat" if en else "ชื่อตามวัด"), (_n(soi.get("numbered")), "numbered" if en else "มีเลข"),
                   (_n(M.get("unnamed_lane_km"), 0), "km of lane with no name" if en else "กม.ฮ่อมไม่มีชื่อ")]))
    b.append(grid(by_type("lane"), lang))
    if soi.get("longest"):
        b.append(f'<h3>{E("The longest sois, by name" if en else "ซอยที่ยาวสุด ตามชื่อ")}</h3>')
        b.append(bars_svg([(x["name"], x["km"]) for x in soi["longest"][:15]], unit=" km"))
    b.append(f'<h2>{E("Measurements" if en else "การวัด")}</h2>')
    b.append(grid(by_type("measure"), lang))
    b.append(share("old-city/", "The old city, measured", "เวียงเก่า วัดแล้ว", lang))
    return "".join(b)


# ---------------------------------------------------------------- highways
def highways_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    b = [hdr("Highways out", "ทางหลวงออกเมือง", lang,
             "The numbered roads to Lamphun, Lampang and Bangkok, Chiang Rai, Fang, Pai, Mae Hong Son and Samoeng, with the count at the city end of each.",
             "ทางหลวงหมายเลขไปลำพูน ลำปาง กรุงเทพฯ เชียงราย ฝาง ปาย แม่ฮ่องสอน และสะเมิง พร้อมจุดนับที่ปลายเมืองของแต่ละสาย")]
    if (S.SITE / "region.png").exists():
        b.append(layered_map("region", "region.svg", "The intercity roads"))
    rows = by_type("highway")
    ladder = {x["route"]: x for x in reversed(AADT.get("ladder") or [])}
    b.append('<div class="scroll"><table class="ladder"><thead><tr><th>' + ("Route" if en else "ทางหลวง") + "</th><th></th><th>km</th><th>" + ("to" if en else "ถึง") + "</th><th>" + (f"vehicles/day at the city end, {AADT.get('latest', '')}" if en else f"คัน/วัน ปลายเมือง {AADT.get('latest', '')}") + "</th><th>" + ("motorcycles" if en else "จักรยานยนต์") + "</th></tr></thead><tbody>")
    for n in sorted(rows, key=lambda x: -(ladder.get((x.get("road") or {}).get("ref", ""), {}).get("aadt", 0))):
        rd = n.get("road") or {}
        st = ladder.get(rd.get("ref", ""), {})
        b.append(f'<tr><td><b>{E(rd.get("ref", ""))}</b></td><td><a href="{r}{url_of(n)}">{E(T(n, "names.name", lang))}</a></td><td class="num">{E(rd.get("km", ""))}</td><td>{E(rd.get("to_th" if lang == "th" else "to", ""))}</td><td class="num">{_n(st.get("aadt"))}</td><td class="num">{_n(st.get("mc"))}</td></tr>')
    b.append("</tbody></table></div>")
    b.append(f'<p class="mute small">{E("The count is the station on that route nearest the city with the largest figure; the station name and kilometre are on the traffic page." if en else "จุดนับคือสถานีบนสายนั้นใกล้เมืองที่มีตัวเลขมากสุด ชื่อสถานีและกิโลเมตรอยู่บนหน้าจราจร")}</p>')
    b.append(band("route1095", "Northwest" if en else "ตะวันตกเฉียงเหนือ", "The road to Pai has doubled its count in five years" if en else "ถนนสายปายเพิ่มจำนวนรถสองเท่าในห้าปี",
                  "2,631 a day in 2020; 5,782 in 2025. The loop site counts its curves; this one only counts what comes off it." if en else "วันละ 2,631 ปี 2563 5,782 ปี 2568 เว็บวงรอบนับโค้ง เว็บนี้นับแค่ที่ออกมา",
                  lang=lang, href="https://motdang.net/loop/", cta=("The Mae Hong Son Loop" if en else "วงรอบแม่ฮ่องสอน")))
    dirs = S.FACETS.get("direction", {}).get("values", {})
    for k, label in dirs.items():
        grp = [n for n in rows if (n.get("facets") or {}).get("direction") == k]
        if grp:
            b.append(f"<h2>{E(label)}</h2>")
            b.append(grid(grp, lang))
    b.append(share("highways/", "Highways out", "ทางหลวงออกเมือง", lang))
    return "".join(b)


# ---------------------------------------------------------------- timeline
def timeline_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    b = [hdr("Timeline", "ลำดับเวลา", lang,
             "Seven chapters of road-building, and the dated roads on one line from 1296 to the light rail’s latest opening date.",
             "เจ็ดยุคของการสร้างถนน และถนนที่มีวันที่บนเส้นเดียวจากปี 1839 ถึงวันเปิดล่าสุดของรถไฟฟ้า")]
    rows = []
    for n in S.NODES:
        rd = n.get("road") or {}
        y = None
        import re as _re
        for cand in (rd.get("opened"), (n.get("plan") or {}).get("due"), (n.get("facets") or {}).get("year")):
            m = _re.search(r"(1[2-9]\d\d|20\d\d)", str(cand or ""))
            if m:
                y = int(m.group(1)); break
        if y and n["type"] in ("road", "ring", "highway", "bridge", "junction", "plan", "gate"):
            rows.append((y, T(n, "names.name", lang), _era_col((n.get("facets") or {}).get("era", "now"))))
    rows.append((1296, "The square" if en else "สี่เหลี่ยม", _era_col("mangrai")))
    rows.append((1921, "The railway arrives" if en else "รถไฟมาถึง", _era_col("siam")))
    rows.append((1948, "The moat roads" if en else "ถนนรอบคู", _era_col("siam")))
    b.append(timeline_svg(sorted(set(rows))))
    eras = sorted(by_type("era"), key=lambda n: (n.get("facets") or {}).get("order", 0))
    for n in eras:
        b.append(f'<h2><a href="{r}{url_of(n)}">{E(T(n, "names.name", lang))}</a></h2>')
        b.append(S.hero_shot(n))
        b.append(f'<p class="said">{E(T(n, "names.said", lang) or "")}</p>')
        b.append(prose(T(n, "text.what", lang)))
    b.append(share("timeline/", "Timeline", "ลำดับเวลา", lang))
    return "".join(b)


# ---------------------------------------------------------------- plans
def plans_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    rows = by_type("plan") + [n for n in by_type("ring") if n.get("plan")] + [n for n in by_type("junction") if n.get("plan")]
    b = [hdr("Plans", "แผน", lang,
             "Proposed, funded, under construction, shelved. Each with its status, its date, and its money as the sources give it.",
             "เสนอ ได้งบ กำลังสร้าง เงียบไป แต่ละอย่างมีสถานะ วันที่ และเงินตามที่แหล่งให้")]
    total = sum(p["plan"]["budget_thb"] for p in rows if isinstance((p.get("plan") or {}).get("budget_thb"), (int, float)))
    b.append(slab([(str(len(rows)), "plans" if en else "แผน"), (f"{total / 1e9:,.0f}", "billion baht, summed as published" if en else "พันล้านบาท รวมตามที่เผยแพร่"),
                   (str(sum(1 for p in rows if p["plan"].get("status") == "building")), "under construction" if en else "กำลังสร้าง"),
                   (str(sum(1 for p in rows if p["plan"].get("status") == "study")), "under study" if en else "กำลังศึกษา")]))
    b.append('<div class="scroll"><table class="ladder"><thead><tr><th>' + ("Plan" if en else "แผน") + "</th><th>" + ("status" if en else "สถานะ") + "</th><th>" + ("million baht" if en else "ล้านบาท") + "</th><th>km</th><th>" + ("due" if en else "กำหนด") + "</th><th>" + ("as of" if en else "ณ") + "</th></tr></thead><tbody>")
    order = {"building": 0, "funded": 1, "study": 2, "shelved": 3, "cancelled": 4, "built": 5, "unknown": 6}
    for n in sorted(rows, key=lambda x: (order.get(x["plan"].get("status"), 9), -(x["plan"].get("budget_thb") or 0) if isinstance(x["plan"].get("budget_thb"), (int, float)) else 0)):
        p = n["plan"]
        bud = p.get("budget_thb")
        b.append(f'<tr><td><a href="{r}{url_of(n)}">{E(T(n, "names.name", lang))}</a></td><td><span class="status {E(p.get("status", ""))}">{E(p.get("status", ""))}</span></td>'
                 f'<td class="num">{f"{bud / 1e6:,.0f}" if isinstance(bud, (int, float)) else E(bud or "")}</td><td class="num">{E(p.get("km", ""))}</td><td>{E(p.get("due", ""))}</td><td>{E(p.get("as_of", ""))}</td></tr>')
    b.append("</tbody></table></div>")
    b.append(bars_svg(sorted([(T(n, "names.name", lang), n["plan"]["budget_thb"] / 1e6) for n in rows if isinstance(n["plan"].get("budget_thb"), (int, float))], key=lambda x: -x[1]), unit=" m"))
    b.append(band("city", "Status" if en else "สถานะ", "Half of these have moved their date at least once" if en else "ครึ่งหนึ่งของแผนเหล่านี้เลื่อนวันมาแล้วอย่างน้อยหนึ่งครั้ง",
                  "The light rail has three published lengths and four opening years. A plan is a rumour until someone puts money against it, and the table says which ones have." if en else "รถไฟฟ้ามีความยาวเผยแพร่สามค่าและปีเปิดสี่ปี แผนคือข่าวลือจนกว่าจะมีใครวางเงิน และตารางบอกว่าอันไหนมีแล้ว",
                  lang=lang, href=f"{r}plans/lrt-red-line/", cta=("The Red Line" if en else "สายสีแดง")))
    b.append(grid(rows, lang))
    b.append(share("plans/", "Plans", "แผน", lang))
    return "".join(b)


# ---------------------------------------------------------------- traffic
def traffic_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    b = [hdr("Traffic", "จราจร", lang,
             "The highway department’s counts, the disease control department’s deaths, TomTom’s minutes, the cooperative’s red trucks. Each with its year and its source.",
             "การนับของกรมทางหลวง การตายของกรมควบคุมโรค นาทีของทอมทอม รถแดงของสหกรณ์ แต่ละอย่างมีปีและแหล่งที่มา")]
    lat = AADT.get("latest")
    sums = (AADT.get("sums") or {}).get(str(lat)) or (AADT.get("sums") or {}).get(lat) or {}
    dr = DEATHS.get("rows") or []
    d24 = next((x for x in dr if x["year"] == 2024), {})
    b.append(slab([(_n(sums.get("stations")), f"stations, {lat}" if en else f"สถานี {lat}"), (_n(sums.get("aadt")), "vehicles a day, summed" if en else "คัน/วัน รวม"),
                   (_n(sums.get("mc")), "motorcycles, summed" if en else "จักรยานยนต์ รวม"), (_n(d24.get("deaths")), "deaths, 2024" if en else "ผู้เสียชีวิต 2567"),
                   (TOMTOM.get("chiang_mai", {}).get("min_per_10km", "—"), "min per 10 km" if en else "นาทีต่อ 10 กม."), (_n(TOMTOM.get("chiang_mai", {}).get("hours_lost")), "hours lost a year" if en else "ชั่วโมงที่เสียต่อปี")]))
    b.append(f'<h2>{E(f"The ladder, {lat}: every station in the province" if en else f"ลำดับ {lat} ทุกสถานีในจังหวัด")}</h2>')
    b.append('<div class="scroll"><table class="ladder"><thead><tr><th>#</th><th>' + ("route" if en else "ทางหลวง") + "</th><th>" + ("station" if en else "สถานี") + "</th><th>km</th><th>" + ("vehicles/day" if en else "คัน/วัน") + "</th><th>" + ("motorcycles" if en else "จักรยานยนต์") + "</th><th>" + ("heavy %" if en else "รถหนัก %") + "</th></tr></thead><tbody>")
    for i, x in enumerate(AADT.get("ladder") or []):
        b.append(f'<tr><td>{i + 1}</td><td><b>{E(x["route"])}</b></td><td>{E(x["name"])}</td><td>{E(x["km"])}</td><td class="num">{x["aadt"]:,}</td><td class="num">{x["mc"]:,}</td><td class="num">{x["pct_heavy"]:.1f}</td></tr>')
    b.append("</tbody></table></div>")
    b.append(f'<p class="mute small">{E(AADT.get("note", ""))}</p>')
    b.append(f'<h2>{E("Five years at the busiest stations" if en else "ห้าปีที่สถานีรถมากสุด")}</h2>')
    cols = ["#b91c1c", "#b45309", "#15803d", "#1d4ed8", "#6d28d9", "#be123c", "#0f766e", "#a16207"]
    series = []
    for i, tr in enumerate((AADT.get("trend") or [])[:8]):
        pts = sorted((int(y), v["aadt"]) for y, v in tr["years"].items())
        series.append({"label": f'{tr["route"]} {tr["name"]}', "points": pts, "color": cols[i % len(cols)]})
    b.append(lines_svg(series))
    b.append(f'<h2>{E("Deaths, by year" if en else "ผู้เสียชีวิต รายปี")}</h2>')
    b.append(bars_svg([(str(x["year"]), x["deaths"]) for x in dr]))
    b.append(f'<p class="mute small">{E(DEATHS.get("method", ""))}</p>')
    if TOMTOM.get("chiang_mai", {}).get("monthly_2025"):
        b.append(f'<h2>{E("Congestion by month, 2025 and 2024" if en else "ความติดขัดรายเดือน 2568 และ 2567")}</h2>')
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        b.append(lines_svg([{"label": "2025", "points": list(zip(range(1, 13), TOMTOM["chiang_mai"]["monthly_2025"])), "color": "#b91c1c"},
                            {"label": "2024", "points": list(zip(range(1, 13), TOMTOM["chiang_mai"]["monthly_2024"])), "color": "#6b7280"}]).replace(">1<", ">Jan<").replace(">12<", ">Dec<"))
        b.append(f'<p class="mute small">{E(TOMTOM["chiang_mai"].get("monthly_note", ""))} · {E("Percent above free-flow travel time." if en else "ร้อยละที่เกินเวลาเดินทางเมื่อถนนโล่ง")}</p>')
    b.append(band("reds", "The vehicle nobody counts" if en else "พาหนะที่บ่มีใครนับ", "2,100 red trucks, 3,000 to 4,000 app cars, 102 bus passengers a day" if en else "รถแดง 2,100 รถแอป 3,000–4,000 ผู้โดยสารรถเมล์วันละ 102",
                  "" , lang=lang, href=f"{r}traffic/songthaew-count/", cta=("The red trucks" if en else "รถแดง")))
    b.append(grid(by_type("traffic"), lang))
    b.append(share("traffic/", "Traffic", "จราจร", lang))
    return "".join(b)


# ---------------------------------------------------------------- numbers
def numbers_page(lang: str) -> str:
    en = lang == "en"
    b = [hdr("Numbers", "ตัวเลข", lang, "Everything on this site that was counted rather than repeated, with the method beside it.", "ทุกอย่างบนเว็บนี้ที่ถูกนับ ไม่ใช่เล่าต่อ พร้อมวิธีการอยู่ข้าง ๆ")]
    def block(head, cells, note):
        return f"<h2>{E(head)}</h2>" + slab(cells) + f'<p class="mute">{E(note)}</p>'
    b.append(block("The network" if en else "โครงข่าย",
                   [(_n(M.get("ways")), "ways" if en else "เส้นทาง"), (_n(M.get("total_km"), 0), "km, all" if en else "กม. ทั้งหมด"), (_n(M.get("drive_km"), 0), "km drivable" if en else "กม. รถวิ่งได้"),
                    (_n(M.get("walk_km"), 0), "km foot and path" if en else "กม. ทางเท้าและทางเดิน"), (_n(M.get("lane_km"), 0), "km of lane" if en else "กม. ฮ่อม"), (_n(M.get("unnamed_lane_km"), 0), "km of lane, no name" if en else "กม. ฮ่อมไม่มีชื่อ")],
                   f"OpenStreetMap by Overpass, fetched {M.get('fetched', '')}, box {M.get('box', '')}. A floor: a lane nobody has drawn does not count." if en else f"OpenStreetMap ผ่าน Overpass ดึง {M.get('fetched', '')} กรอบ {M.get('box', '')} ค่าต่ำสุด ฮ่อมที่ไม่มีใครวาดไม่ถูกนับ"))
    b.append(block("Nodes" if en else "จุด",
                   [(_n(M.get("intersections")), "intersections" if en else "ทางแยก"), (_n(M.get("dead_ends")), "dead ends" if en else "ทางตัน"), (_n(M.get("signals")), "traffic signals" if en else "ไฟสัญญาณ"),
                    (_n(M.get("wats")), "wats in the box" if en else "วัดในกรอบ"), (_n(len(M.get("ping_bridges") or [])), "road bridges over the Ping" if en else "ขัวรถข้ามแม่ปิง"), (_n(M.get("construction_km"), 1), "km under construction" if en else "กม. กำลังสร้าง")],
                   "Intersections are nodes shared by three or more drivable ways, service lanes excluded; a Ping bridge is a bridge way that crosses a way named Ping, dual carriageways collapsed." if en else "ทางแยกคือจุดที่เส้นทางรถวิ่งได้สามเส้นขึ้นไปใช้ร่วมกัน ไม่รวมทางบริการ ขัวแม่ปิงคือเส้นทางสะพานที่ตัดเส้นทางชื่อปิง รวมถนนคู่ขนานเป็นหนึ่ง"))
    b.append(zone_table(lang))
    soi = M.get("soi") or {}
    b.append(block("Sois" if en else "ซอย",
                   [(_n(soi.get("named_count")), "named" if en else "มีชื่อ"), (_n(soi.get("km"), 0), "km" if en else "กม."), (_n(soi.get("with_wat_in_name")), "named for a wat" if en else "ชื่อตามวัด"), (_n(soi.get("numbered")), "numbered" if en else "มีเลข")],
                   "A way counts as a soi when its name carries ซอย, ซ. or Soi; ways sharing a name are summed." if en else "เส้นทางนับเป็นซอยเมื่อชื่อมีคำว่า ซอย ซ. หรือ Soi เส้นทางที่ชื่อเดียวกันรวมกัน"))
    lat = AADT.get("latest"); sums = (AADT.get("sums") or {}).get(str(lat)) or {}
    b.append(block("Counts" if en else "การนับรถ",
                   [(_n(sums.get("stations")), f"stations, {lat}" if en else f"สถานี {lat}"), (_n(sums.get("aadt")), "vehicles/day, summed" if en else "คัน/วัน รวม"), (_n(sums.get("mc")), "motorcycles, summed" if en else "จักรยานยนต์ รวม"), (_n(AADT.get("count")), "station-years" if en else "สถานี-ปี")],
                   AADT.get("note", "")))
    b.append(f'<h2>{E("The records" if en else "บันทึก")}</h2>')
    b.append(slab([(str(COV["records"]), "records" if en else "บันทึก"), (str(COV["sources"]), "sources" if en else "แหล่ง"), (str(COV["th_fields"]), "fields in Thai" if en else "ช่องภาษาไทย"), (str(COV["images"]), "pictures" if en else "ภาพ"), (str(COV["kin_edges"]), "links between records" if en else "ลิงก์ระหว่างบันทึก")]))
    b.append(grid(by_type("measure"), lang))
    b.append(share("numbers/", "Numbers", "ตัวเลข", lang))
    return "".join(b)


# ---------------------------------------------------------------- words
def words_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    ui = UI[lang]
    rows = by_type("word")
    b = [hdr("Kam Mueang, the road words", "กำเมือง คำเรื่องถนน", lang,
             "The northern speech has its own words for the alley, the bridge, the corner and the market, and the city still uses them. Script, sound, standard equivalent, root.",
             "คำเมืองมีคำของตัวเองสำหรับฮ่อม ขัว แจ่ง และกาด และเมืองยังใช้อยู่ ตัวเขียน เสียง คำภาษากลาง รากศัพท์")]
    b.append(f'<p class="tt" lang="nod" style="font-size:2.2rem;margin:.2rem 0 1rem">{S.TAI_THAM} <span class="mute" style="font-family:var(--body);font-size:1rem">— Chiang Mai in Tai Tham, the Lanna script</span></p>')
    b.append('<div class="scroll"><table class="ladder"><thead><tr><th>' + ui["script"] + "</th><th>" + ui["rtgs"] + "</th><th>" + ui["sound"] + "</th><th>" + ui["standard"] + "</th><th>" + ui["gloss"] + "</th></tr></thead><tbody>")
    for n in rows:
        w = n.get("word") or {}
        b.append(f'<tr><td class="th" style="font-size:1.25em"><a href="{r}{url_of(n)}">{E(w.get("th", ""))}</a></td><td class="mono">{E(w.get("rtgs", ""))}</td><td class="mono">{E(w.get("ipa", ""))}</td><td>{E(w.get("standard", ""))}</td><td>{E(w.get("gloss_th" if lang == "th" else "gloss") or w.get("gloss", ""))}</td></tr>')
    b.append("</tbody></table></div>")
    b.append(band("reds2", "Say it" if en else "อู้ดู", "Khuen rot daeng" if en else "ขึ้นรถแดง",
                  "Get in a red truck. Directions in this city run from chaeng to chaeng and yaek to yaek, and the names outlive the buildings." if en else "การบอกทางในเมืองนี้วิ่งจากแจ่งถึงแจ่ง แยกถึงแยก และชื่ออยู่นานกว่าตึก",
                  lang=lang, href=f"{r}words/rot-daeng/", cta=("รถแดง" if en else "รถแดง")))
    b.append(grid(rows, lang))
    b.append(share("words/", "Kam Mueang, the road words", "กำเมือง คำเรื่องถนน", lang))
    return "".join(b)


# ---------------------------------------------------------------- stories
def stories_page(lang: str) -> str:
    en = lang == "en"
    b = [hdr("Stories", "เรื่องเล่า", lang, "The long reads: what a road does to an old city, why the moat runs one way, the trees, the flood, the monk.", "ฉบับยาว ถนนทำอะไรกับเมืองเก่า ทำไมรอบคูวิ่งทางเดียว ต้นยาง น้ำท่วม ครูบา")]
    lead = BY_ID.get("what-a-road-does-to-an-old-city")
    if lead:
        b.append(S.hero_shot(lead))
        b.append(prose(T(lead, "text.what", lang)))
        b.append(f'<p><a class="btn" href="{lroot(lang)}{url_of(lead)}">{E("The whole argument" if en else "ข้อโต้แย้งทั้งหมด")}</a></p>')
    b.append(grid([n for n in by_type("story") if n["id"] != "what-a-road-does-to-an-old-city"], lang))
    b.append(f'<h2>{E("People" if en else "บุคคล")}</h2>')
    b.append(grid(by_type("person"), lang))
    b.append(f'<h2>{E("Places" if en else "สถานที่")}</h2>')
    b.append(grid(by_type("place"), lang))
    b.append(share("stories/", "Stories", "เรื่องเล่า", lang))
    return "".join(b)


# ---------------------------------------------------------------- quiz
QUIZ = [
 ("It is 5 pm on a Friday. You are", "ห้าโมงเย็นวันศุกร์ คุณ", [
   ("looping the moat again because I missed the cut-through", "วนคูอีกรอบเพราะพลาดช่องตัด", "moat-loop"),
   ("under Khuang Sing, not stopping", "ลอดข่วงสิงห์ บ่หยุด", "ring-2"),
   ("on a bench in the back of a red truck", "นั่งม้านั่งท้ายรถแดง", "rot-daeng"),
   ("walking, because it is nearly Sunday", "เตียว เพราะใกล้วันอาทิตย์แล้ว", "ratchadamnoen-road"),
   ("leaning into a hairpin somewhere above Mae Malai", "เอียงเข้าโค้งหักศอกเหนือแม่มาลัย", "route-1095")]),
 ("Your ideal width", "ความกว้างในฝัน", [
   ("two metres and a cat", "สองเมตรกับแมวตัวหนึ่ง", "hom-the-lane"),
   ("six lanes and a median", "หกเลนมีเกาะกลาง", "ring-2"),
   ("one lane, one way, water on one side", "เลนเดียว ทางเดียว น้ำข้างหนึ่ง", "moat-loop"),
   ("whatever the trees allow", "เท่าที่ต้นยางยอม", "ton-yang-road"),
   ("a footpath, closed to cars", "ทางเท้า ปิดรถ", "ratchadamnoen-road")]),
 ("What you are named after", "ตั้งชื่อตามอะไร", [
   ("a family that gave land away", "ตระกูลที่หื้อที่ดิน", "nimmanhaemin-road"),
   ("a monk", "ครูบา", "si-wichai-road"),
   ("a hotel that closed", "โฮงแฮมที่ปิดไปแล้ว", "rincome-junction"),
   ("a fish trap at a corner", "เครื่องดักปลาที่แจ่ง", "moat-loop"),
   ("the city’s 700th birthday", "วันเกิด 700 ปีของเมือง", "ring-2")]),
 ("Your relationship with the river", "ความสัมพันธ์กับแม่น้ำ", [
   ("I cross it twice and never look", "ข้ามสองครั้ง บ่เคยมอง", "ring-3"),
   ("I went under it in October 2024", "จมไปเมื่อตุลาคม 2567", "mahidol-road"),
   ("I keep a kilometre away on purpose", "อยู่ห่างหนึ่งกิโลโดยตั้งใจ", "moat-loop"),
   ("I have a gauge on me", "มีสถานีวัดน้ำอยู่บนตัว", "nawarat-bridge"),
   ("what river", "แม่น้ำอะไร", "route-1095")]),
 ("Your budget line", "บรรทัดงบของคุณ", [
   ("10,070 million baht and twelve years", "10,070 ล้านบาทกับสิบสองปี", "ring-2"),
   ("zero baht and 4,000 volunteers", "ศูนย์บาทกับศรัทธา 4,000 คน", "si-wichai-road"),
   ("180,000 baht a square wa", "ตารางวาละ 180,000", "nimmanhaemin-road"),
   ("thirty baht, flat", "สามสิบบาทตลอดสาย", "rot-daeng"),
   ("nobody has ever counted me", "บ่มีใครเคยนับ", "hom-the-lane")]),
 ("The word for you in Kam Mueang", "คำเรียกคุณในกำเมือง", [
   ("ฮ่อม", "ฮ่อม", "hom-the-lane"),
   ("ขัว", "ขัว", "nawarat-bridge"),
   ("แจ่ง", "แจ่ง", "moat-loop"),
   ("ทางลอด", "ทางลอด", "ring-2"),
   ("ทางหลวง", "ทางหลวง", "route-1095")]),
]
OUTCOMES = {
 "moat-loop": ("You are the moat loop.", "คุณคือถนนรอบคูเมือง", "6.54 km, one way, and everyone who has ever lived here has driven you twice by mistake. You are the oldest thing on the site and you know it.", "6.54 กิโล ทางเดียว และใผตี้เคยอยู่ที่นี่ก็เคยขับคุณสองรอบโดยพลาด คุณเก่าสุดบนเว็บนี้และคุณฮู้"),
 "ring-2": ("You are the 700 Years Road.", "คุณคือถนนสมโภช 700 ปี", "Six lanes, seven underpasses, and you never stop for anyone. It took twelve years and 10,070 million baht to make you, and the city grew past you in ten.", "หกเลน ทางลอดเจ็ดแห่ง และคุณบ่เคยหยุดหื้อใผ ใช้เวลาสิบสองปีกับ 10,070 ล้านสร้างคุณ และเมืองโตข้ามคุณในสิบปี"),
 "rot-daeng": ("You are a red truck.", "คุณคือรถแดง", "No route, only a direction and a fare. There were 2,800 of you in 2017 and 2,100 now, and you are still how the city moves.", "บ่มีเส้นทาง มีแต่ทิศกับค่าโดยสาร ปี 2560 มีคุณ 2,800 คัน ตอนนี้ 2,100 และคุณยังเป็นวิธีที่เมืองเคลื่อน"),
 "ratchadamnoen-road": ("You are Ratchadamnoen.", "คุณคือถนนราชดำเนิน", "Gate to temple, the founding axis, one-way for pedestrians since 2021 and a market every Sunday. A road that became a floor.", "ประตูถึงวัด แกนตั้งเมือง ทางเดียวเพื่อคนเดินตั้งแต่ 2564 และกาดทุกวันอาทิตย์ ถนนที่กลายเป็นพื้น"),
 "route-1095": ("You are Route 1095.", "คุณคือทางหลวง 1095", "Two thousand curves by your own account and a count that doubled in five years. You do not live in the city; you leave it.", "สองพันโค้งตามที่คุณว่าเอง และจำนวนรถที่เพิ่มสองเท่าในห้าปี คุณบ่ได้อยู่ในเมือง คุณออกจากมัน"),
 "hom-the-lane": ("You are a hom.", "คุณคือฮ่อม", "Two metres wide, a cat, twenty families and a dead end. Most of the city’s kilometres are you, and nobody counts you.", "กว้างสองเมตร แมวหนึ่งตัว ยี่สิบครอบครัว และทางตัน กิโลเมตรส่วนใหญ่ของเมืองคือคุณ และบ่มีใครนับคุณ"),
 "ton-yang-road": ("You are the Yang Tree Road.", "คุณคือถนนต้นยาง", "Planted in 1882, bypassed in 1969, polled in 2020. You are the only road on the site that a new road did a favour.", "ปลูกปี 2425 ถูกเลี่ยงปี 2512 ทำโพลปี 2563 คุณคือถนนสายเดียวบนเว็บที่ถนนใหม่ทำคุณหื้อ"),
 "nimmanhaemin-road": ("You are Nimman.", "คุณคือนิมมาน", "1.327 km given away in 1963 and priced like a mine. Seventeen sois and each one is a different evening.", "1.327 กิโลหื้อไปปี 2506 และราคาเหมือนเหมือง สิบเจ็ดซอยและแต่ละซอยคือค่ำคืนคนละแบบ"),
 "si-wichai-road": ("You are the monk’s road.", "คุณคือถนนครูบา", "11.53 km up a mountain by hand in five months and twenty-two days. Nobody has built anything the way you were built since.", "11.53 กิโลขึ้นดอยด้วยมือในห้าเดือนยี่สิบสองวัน บ่มีใครสร้างอะไรแบบที่คุณถูกสร้างอีกเลย"),
 "rincome-junction": ("You are Rincome junction.", "คุณคือแยกรินคำ", "Named for a hotel that closed and the worst light in the city by the planners’ own count. Everyone knows where you are; nobody wants to be there at five.", "ตั้งชื่อตามโฮงแฮมที่ปิดแล้ว และไฟแดงแย่สุดตามที่นักวางแผนนับเอง ใผ ๆ ก็ฮู้ว่าคุณอยู่ไหน บ่มีใครอยากอยู่ตรงนั้นตอนห้าโมง"),
 "ring-3": ("You are Route 121.", "คุณคือทางหลวง 121", "52.96 km round, along the canal under the mountain, and five interchanges on the way for 3,145 million baht. The money is going to you now.", "ยาวรอบ 52.96 กิโล เลียบคลองใต้ดอย และทางแยกต่างระดับห้าแห่งกำลังมา 3,145 ล้าน เงินกำลังไหลไปหาคุณ"),
 "mahidol-road": ("You are Mahidol Road.", "คุณคือถนนมหิดล", "121,403 vehicles a day, the busiest count in the north, on the floodplain the founders avoided. You went under in October 2024 and were back by Monday.", "121,403 คันต่อวัน จุดนับรถนักสุดของภาคเหนือ บนที่ราบน้ำท่วมที่ผู้สร้างเมืองหลบ คุณจมตุลาคม 2567 และกลับมาภายในวันจันทร์"),
 "nawarat-bridge": ("You are the Nawarat Bridge.", "คุณคือสะพานนวรัฐ", "Teak, then steel, then concrete. The gauge that read 5.30 m is on you and so is the name of the last ruler.", "ไม้สัก แล้วเหล็ก แล้วคอนกรีต สถานีวัดน้ำที่อ่านได้ 5.30 เมตรอยู่บนคุณ ชื่อเจ้าหลวงองค์สุดท้ายก็อยู่บนคุณ"),
}


def quiz_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    b = [hdr("Which Chiang Mai road are you?", "คุณเป็นถนนสายไหนของเจียงใหม่", lang,
             "Six questions. The answer is a record on this site, and it is not flattering to everyone.", "หกคำถาม คำตอบคือบันทึกบนเว็บนี้ และมันบ่ได้ยอทุกคน")]
    b.append('<form class="quiz" id="quiz">')
    for qi, (q, qth, opts) in enumerate(QUIZ):
        b.append(f'<fieldset><legend>{qi + 1}. {E(q if en else qth)}</legend>')
        for oi, (o, oth, key) in enumerate(opts):
            b.append(f'<label><input type="radio" name="q{qi}" value="{E(key)}"{" required" if oi == 0 else ""}> {E(o if en else oth)}</label>')
        b.append("</fieldset>")
    b.append(f'<p><button class="btn" type="submit">{E("Tell me" if en else "บอกมา")}</button></p></form>')
    for key, (t, tth, txt, txtth) in OUTCOMES.items():
        n = BY_ID.get(key)
        href = f"{r}{url_of(n)}" if n else "#"
        b.append(f'<div class="result" id="res-{E(key)}"><h2>{E(t if en else tth)}</h2><p>{E(txt if en else txtth)}</p><p><a class="btn" href="{href}">{E("Your record" if en else "บันทึกของคุณ")}</a> <a class="btn" href="#quiz">{E("Again" if en else "อีกที")}</a></p></div>')
    b.append('''<script>document.getElementById("quiz").addEventListener("submit",function(e){e.preventDefault();
var t={};new FormData(e.target).forEach(function(v){t[v]=(t[v]||0)+1});var best=null,bv=0;
for(var k in t){if(t[k]>bv){bv=t[k];best=k}}
document.querySelectorAll(".result").forEach(function(x){x.classList.remove("on")});
var el=document.getElementById("res-"+best);if(el){el.classList.add("on");el.scrollIntoView({behavior:"smooth"})}});</script>''')
    b.append(f'<h2>{E("And some arithmetic" if en else "และเลขคณิตนิดหน่อย")}</h2>')
    laps = 696 / 6.54
    b.append(slab([(f"{laps:.0f}", "laps of the moat to reach Bangkok’s distance" if en else "รอบคูเมือง เท่าระยะไปกรุงเทพฯ"),
                   (f"{6.54 / 0.06:.0f}", "moat laps to one Doi Suthep road (by km, not by effort)" if en else "รอบคูต่อถนนขึ้นดอยหนึ่งสาย (ตามกิโล ไม่ใช่ตามแรง)"),
                   (f"{11530 / 173:.0f}", "metres of mountain road a day, 1934–35" if en else "เมตรถนนภูเขาต่อวัน 2477–78"),
                   (f"{6.54 / 100 * 7 * 39.94:.0f}", "baht of Gasohol 95 for one lap at 7 L/100 km" if en else "บาท แก๊สโซฮอล์ 95 ต่อหนึ่งรอบที่ 7 ลิตร/100 กม.")]))
    b.append(f'<p class="mute small">{E("The lap figure uses the 6.54 km circuit and the 696 km road distance; the fuel figure uses the price on the day this was built and a made-up consumption, which is why it is on the fun page." if en else "ตัวเลขรอบใช้วงรอบ 6.54 กม. และระยะทางถนน 696 กม. ตัวเลขน้ำมันใช้ราคาวันที่สร้างกับอัตราสิ้นเปลืองที่สมมติขึ้น นี่คือเหตุที่มันอยู่หน้าสนุก")}</p>')
    b.append(share("quiz/", "Which Chiang Mai road are you?", "คุณเป็นถนนสายไหนของเจียงใหม่", lang))
    return "".join(b)


# ---------------------------------------------------------------- about
def about(lang: str) -> str:
    en = lang == "en"
    b = [f'<h1>{E("How this was made" if en else "ทำขึ้นอย่างไร")}</h1>']
    if en:
        b.append(prose(
            f"A static site built from {COV['records']} records in a public repository. Every figure printed anywhere on it is computed at build time from those files and from the harvests, so a number on a page and a number in the API cannot drift apart.\n\n"
            f"**The harvests.** OpenStreetMap by Overpass, in a hundred tiles, for {M.get('ways', 0):,} ways and {M.get('total_km', 0):,.0f} km in a box from Mae Rim to Saraphi; the same source for the wats, the water, the signals and the bridges. The Department of Highways’ open-data traffic counts, five years of CSV, filtered to the province’s {COV.get('stations', 0)} stations. The Department of Disease Control’s three-database road-death file, one row per death, filtered to the province. TomTom’s city index, parsed off the page. Copernicus DEM through Open-Meteo for the relief. Thai and English Wikipedia at named revisions, a 2005 Chiang Mai University thesis, the municipality’s own data sheet, and the newspapers, for the dates and the money.\n\n"
            f"**The measurements** follow Boeing’s 2019 method for street orientation and the usual definitions for intersections, dead ends and block length, on the drivable network without service lanes, in five zones: the square inside the moat and four bands of distance from its centre. The old-city page prints the table and says what each column is.\n\n"
            f"**Tiers.** Every claim carries one: *cited* names a source, *harvested* came out of an open dataset with its licence, *tradition* is general knowledge and is hedged, *inference* is this project’s own reasoning from the above. The record page for anything you doubt has the table at the bottom.\n\n"
            f"**Both languages, or neither.** Each page is one build function called twice. The Thai is written in the northern register where the register fits, and marked as this project’s writing, not a translation. {COV['th_fields']} fields are in Thai.\n\n"
            f"**What it does not have** is on its own page, linked from the stories.\n\n"
            f"**Who made it.** hongdam.net, a bilingual web studio in Chiang Rai. The enriched, graphical sites in this family are all built there."))
    else:
        b.append(prose(
            f"เว็บสถิตที่สร้างจากบันทึก {COV['records']} ชิ้นในคลังสาธารณะ ตัวเลขทุกตัวที่พิมพ์ที่ไหนก็ตามบนเว็บนี้คำนวณตอนสร้างจากไฟล์เหล่านั้นและจากการเก็บข้อมูล ตัวเลขบนหน้าเว็บกับตัวเลขใน API จึงเคลื่อนออกจากกันไม่ได้\n\n"
            f"**การเก็บข้อมูล** OpenStreetMap ผ่าน Overpass เป็นร้อยช่อง ได้ {M.get('ways', 0):,} เส้นทาง {M.get('total_km', 0):,.0f} กม. ในกรอบจากแม่ริมถึงสารภี แหล่งเดียวกันสำหรับวัด น้ำ ไฟสัญญาณ และขัว ข้อมูลเปิดปริมาณจราจรของกรมทางหลวง CSV ห้าปี กรองเหลือ {COV.get('stations', 0)} สถานีของจังหวัด ไฟล์การตายบนถนนสามฐานของกรมควบคุมโรค หนึ่งแถวต่อหนึ่งการตาย กรองตามจังหวัด ดัชนีเมืองของทอมทอม อ่านจากหน้าเว็บ Copernicus DEM ผ่าน Open-Meteo สำหรับภูมิประเทศ วิกิพีเดียไทยและอังกฤษที่รุ่นแก้ไขระบุไว้ วิทยานิพนธ์ ม.เชียงใหม่ ปี 2548 เอกสารข้อมูลของเทศบาลเอง และหนังสือพิมพ์ สำหรับวันที่และเงิน\n\n"
            f"**การวัด** ใช้วิธีของ Boeing 2019 สำหรับทิศทางถนน และนิยามทั่วไปสำหรับทางแยก ทางตัน และความยาวบล็อก บนโครงข่ายรถวิ่งได้ไม่รวมทางบริการ ในห้าโซน สี่เหลี่ยมในคูและแถบระยะสี่แถบจากกลางมัน หน้าเวียงเก่าพิมพ์ตารางและบอกว่าแต่ละคอลัมน์คืออะไร\n\n"
            f"**ชั้นของข้อความ** ทุกข้อความมีชั้นกำกับ *cited* ระบุแหล่ง *harvested* มาจากชุดข้อมูลเปิดพร้อมสัญญาอนุญาต *tradition* คือความรู้ทั่วไปและมีการกันไว้ *inference* คือการให้เหตุผลของโครงการนี้เอง หน้าบันทึกของสิ่งที่คุณสงสัยมีตารางอยู่ด้านล่าง\n\n"
            f"**สองภาษา หรือไม่มีเลย** แต่ละหน้าคือฟังก์ชันเดียวที่ถูกเรียกสองครั้ง ภาษาไทยเขียนในสำเนียงเหนือตรงที่สำเนียงเข้ากับที่ และระบุว่าเป็นงานเขียนของโครงการนี้ ไม่ใช่การแปล มีช่องภาษาไทย {COV['th_fields']} ช่อง\n\n"
            f"**สิ่งที่เว็บนี้ไม่มี** อยู่ในหน้าของตัวเอง ลิงก์จากเรื่องเล่า\n\n"
            f"**ใครทำ** hongdam.net สตูดิโอเว็บสองภาษาในเชียงราย เว็บชุดนี้ที่เนื้อหาแน่นและมีภาพประกอบมาก สร้างที่นั่นทั้งหมด"))
    b.append(f'<p class="mute small">{E("Built" if en else "สร้างเมื่อ")} {E(COV["built"])} · '
             f'<a href="{S.rel()}api/">API</a> · '
             f'<a href="https://github.com/NaNoBotCo/chiang-mai-roads" rel="noopener">GitHub</a></p>')
    return "".join(b)


# ---------------------------------------------------------------- old maps
def maps_page(lang: str) -> str:
    en = lang == "en"
    r = lroot(lang)
    ui = UI[lang]
    rows = sorted(by_type("map"), key=lambda n: (n.get("facets") or {}).get("order", 0))
    city = [n for n in rows if "moat" in n["region"] or "city" in n["region"] or "ring3" in n["region"] or "province" in n["region"]]
    country = [n for n in rows if n not in city]
    b = [hdr("Old maps", "แผนที่เก่า", lang,
             f"{len(rows)} sheets, 1693 to 1959, at the size they can be read at. What each one shows about the roads is under it.",
             f"{len(rows)} แผ่น ตั้งแต่ พ.ศ. 2236 ถึง 2502 ในขนาดที่อ่านออก ใต้แต่ละแผ่นคือสิ่งที่มันบอกเรื่องถนน")]
    b.append(slab([(str(len(rows)), "sheets" if en else "แผ่น"),
                   ("1693", "the oldest" if en else "เก่าสุด"),
                   ("1959", "the newest" if en else "ใหม่สุด"),
                   ("1:5,000", "the closest" if en else "ละเอียดสุด"),
                   (str(len(city)), "of the city" if en else "ของเมือง")]))
    b.append(prose(
        ("**Two sheets are worth the visit on their own.** The 1931 city map is bilingual at 1:5,000 and labels the moat "
         "คูเวียง KOO VIENG CANAL, names eight gates including ประตูขัวก้อม Kua Kom, the gate of the short bridge, and "
         "marks the teak houses by name. The 1945 sheet was compiled from a Siamese map of 1930 and air photographs of "
         "March 1945, and its glossary quietly translates every word this site is built on." if en else
         "**สองแผ่นคุ้มค่าที่จะมาดูด้วยตัวมันเอง** แผนที่เมืองปี 2474 เป็นสองภาษา มาตราส่วน 1:5,000 กำกับคูเมืองว่า "
         "คูเวียง KOO VIENG CANAL ตั้งชื่อประตูแปดประตูรวมถึงประตูขัวก้อม ประตูของขัวสั้น และทำเครื่องหมายห้างไม้สักไว้เป็นชื่อ "
         "แผ่นปี 2488 จัดทำจากแผนที่ของสยามปี 2473 และภาพถ่ายทางอากาศเดือนมีนาคม 2488 และอภิธานของมันแปลทุกคำที่เว็บนี้สร้างขึ้นจาก")))
    b.append(band("rapids", "Before the roads" if en else "ก่อนมีถนน",
                  "You came up the Ping, and a boat is not a road" if en else "คุณขึ้นมาทางแม่ปิง และเรือบ่ใช่ถนน",
                  "Carl Bock walked and floated to Chiang Saen in 1881 and drew the way he went as a strip. Everything either side of the line is blank." if en else
                  "คาร์ล บ็อก เดินและล่องไปเชียงแสนปี 2424 แล้ววาดทางที่เขาไปเป็นแถบ ทุกอย่างสองข้างเส้นว่างเปล่า",
                  lang=lang, href=f"{r}old-maps/#map-bock-1881", cta=("Bock's strip" if en else "แถบของบ็อก")))
    for group, head_en, head_th in ((city, "The city", "เมือง"), (country, "The country", "ประเทศ")):
        if not group:
            continue
        b.append(f'<h2>{E(head_en if en else head_th)}</h2>')
        for n in group:
            sh = n.get("sheet") or {}
            ims = S.pictures(n)
            im = next((i for i in ims if i.get("primary")), ims[0]) if ims else None
            b.append(f'<h3 id="{E(n["id"])}"><a href="{r}{url_of(n)}">{E(T(n, "names.name", lang))}</a> '
                     f'<span class="n">{E(sh.get("year", ""))}</span></h3>')
            b.append(f'<p class="said">{E(T(n, "names.said", lang) or "")}</p>')
            if im:
                b.append(f'<figure class="sheet"><a href="{S.img_url(im)}"><img src="{S.img_url(im)}" '
                         f'alt="{E(im.get("alt") or T(n, "names.name", lang))}" loading="lazy" decoding="async"></a>'
                         f'<figcaption>{S.credit(im)}</figcaption></figure>')
            meta = []
            for k, label in (("maker", "drawn by" if en else "ผู้จัดทำ"), ("scale", "scale" if en else "มาตราส่วน"),
                             ("sheet_no", "sheet" if en else "แผ่นที่"), ("holding", "held" if en else "เก็บที่"),
                             ("extent", "size" if en else "ขนาด")):
                v = sh.get(k + "_th" if lang == "th" and (k + "_th") in sh else k)
                if v:
                    meta.append(f"<b>{E(label)}</b> {E(v)}")
            if meta:
                b.append('<p class="mute small">' + " · ".join(meta) + "</p>")
            shows = sh.get("shows_th" if lang == "th" else "shows")
            if shows:
                b.append(f'<p><b>{E("What it shows" if en else "มันแสดงอะไร")}:</b> {E(shows)}</p>')
            if sh.get("year_note"):
                b.append(f'<p class="mute small">{E(sh["year_note"])}</p>')
            b.append(prose(T(n, "text.what", lang)))
            b.append(f'<p class="small"><a href="{r}{url_of(n)}">'
                     f'{E("The record, with what was read off the sheet" if en else "บันทึก พร้อมสิ่งที่อ่านจากแผ่น")}</a></p>')
    b.append(f'<h2>{E("Where they came from" if en else "มาจากไหน")}</h2>')
    b.append(prose(
        ("Every sheet here is on Wikimedia Commons under a free licence, and the author and licence sit under each one. "
         "The 1:250,000 and 1:50,000 sheets are US Army Map Service series L509 and L708, public domain, digitised by "
         "the Perry-Castañeda Library at the University of Texas. The two railway maps are from the Bibliothèque "
         "nationale de France. Nothing here was redrawn: they are the sheets, scanned." if en else
         "ทุกแผ่นที่นี่อยู่บนวิกิมีเดียคอมมอนส์ภายใต้สัญญาอนุญาตเสรี และชื่อผู้ทำกับสัญญาอนุญาตอยู่ใต้แต่ละแผ่น "
         "แผ่นมาตราส่วน 1:250,000 และ 1:50,000 คือชุด L509 และ L708 ของ US Army Map Service สาธารณสมบัติ "
         "แปลงเป็นดิจิทัลโดยห้องสมุด Perry-Castañeda มหาวิทยาลัยเท็กซัส แผนที่รถไฟสองแผ่นมาจากหอสมุดแห่งชาติฝรั่งเศส "
         "ไม่มีอะไรที่นี่ถูกวาดใหม่ มันคือแผ่นจริง ที่สแกนมา")))
    b.append(share("old-maps/", "Old maps", "แผนที่เก่า", lang))
    return "".join(b)
