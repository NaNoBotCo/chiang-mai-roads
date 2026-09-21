#!/usr/bin/env python3
"""fetch_wiki.py — the drafting corpus: Wikipedia articles as plain text, one per file.

Pulls the English article and, where it exists, the Thai one, so a bilingual record can
cite both. Each file carries its URL, its revision id and the fetch date at the top.
Wikipedia is CC BY-SA 4.0. The corpus is a working input: .gitignore excludes it and
publish.sh does not copy it into docs/.

    python3 tools/fetch_wiki.py                 # into data/corpus/
    python3 tools/fetch_wiki.py --out /tmp/x    # somewhere else
    python3 tools/fetch_wiki.py --list          # print the article list and stop
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, jdump, slugify  # noqa: E402

UA = "chiang-mai-roads-build/0.1 (https://wichaa.net; nan@motdang.net) python-urllib"

EN = """
Chiang Mai
Chiang Mai province
History of Chiang Mai
Tha Phae Gate
Nimmanhaemin Road
Thailand Route 11
Thailand Route 1
Thailand Route 118
Thailand Route 107
Thailand Route 108
Thailand Route 1095
Thailand Route 106
Thailand Route 121
Thailand Route 1001
Thailand Route 1317
Thai highway network
Chiang Mai International Airport
Chiang Mai railway station
Ping River
Doi Suthep
Wat Phra That Doi Suthep
Khruba Srivichai
Mangrai
Kawila
Lanna
Northern Thai language
Tai Tham script
Songthaew
Transport in Thailand
Chiang Mai Light Rail Transit
Northern high-speed railway (Thailand)
Wiang Kum Kam
Kraisri Nimmanahaeminda
Mueang Chiang Mai district
Chiang Mai Night Bazaar
Wat Ket Karam
Iron Bridge (Chiang Mai)
Nawarat Bridge
2024 Southeast Asian floods
Road traffic safety in Thailand
Warorot Market
Kad Suan Kaew
Central Chiang Mai Airport
Lamphun
Lampang
Chiang Rai
Mae Hong Son
Hang Dong district
Saraphi district
San Kamphaeng district
Mae Rim district
Doi Saket district
""".strip().splitlines()

TH = """
เชียงใหม่
จังหวัดเชียงใหม่
เทศบาลนครเชียงใหม่
ประตูท่าแพ
ประตูช้างเผือก
ประตูสวนดอก
ประตูเชียงใหม่
ประตูแสนปุง
แจ่งศรีภูมิ
แจ่งก๊ะต้ำ
แจ่งหัวลิน
แจ่งกู่เฮือง
กำแพงเมืองเชียงใหม่
คูเมืองเชียงใหม่
กำแพงดิน (เชียงใหม่)
ถนนท่าแพ
ถนนนิมมานเหมินท์
ถนนช้างคลาน
ถนนห้วยแก้ว
ถนนราชดำเนิน (เชียงใหม่)
ถนนวัวลาย
ถนนช้างม่อย
ถนนเจริญประเทศ
ถนนสุเทพ
ถนนศรีวิชัย
ถนนมหิดล (เชียงใหม่)
ถนนซุปเปอร์ไฮเวย์ เชียงใหม่-ลำปาง
ทางหลวงแผ่นดินหมายเลข 11
ทางหลวงแผ่นดินหมายเลข 1
ทางหลวงแผ่นดินหมายเลข 118
ทางหลวงแผ่นดินหมายเลข 107
ทางหลวงแผ่นดินหมายเลข 108
ทางหลวงแผ่นดินหมายเลข 1095
ทางหลวงแผ่นดินหมายเลข 106
ทางหลวงแผ่นดินหมายเลข 121
ทางหลวงแผ่นดินหมายเลข 1001
ทางหลวงแผ่นดินหมายเลข 1317
ทางหลวงแผ่นดินหมายเลข 1006
ทางหลวงแผ่นดินหมายเลข 1141
ทางหลวงแผ่นดินหมายเลข 1013
ถนนวงแหวนรอบนอกเชียงใหม่
ถนนวงแหวนรอบกลางเชียงใหม่
ถนนวงแหวนรอบในเชียงใหม่
ถนนเชียงใหม่-ลำพูน
ถนนคลองชลประทาน (เชียงใหม่)
ทางหลวงพิเศษระหว่างเมืองสายเชียงใหม่–เชียงราย
รถไฟฟ้าเชียงใหม่
รถไฟฟ้ารางเบาเชียงใหม่ สายสีแดง
รถไฟความเร็วสูงสายเหนือ
ท่าอากาศยานเชียงใหม่
ท่าอากาศยานเชียงใหม่แห่งที่ 2
สถานีรถไฟเชียงใหม่
สถานีขนส่งผู้โดยสารจังหวัดเชียงใหม่
แม่น้ำปิง
คลองแม่ข่า
สะพานนวรัฐ
สะพานจันทร์สมอนุสรณ์
สะพานเหล็ก (เชียงใหม่)
สะพานเม็งราย
สะพานนครพิงค์
สะพานรัตนโกสินทร์ (เชียงใหม่)
ครูบาศรีวิชัย
พญามังราย
พระเจ้ากาวิละ
ไกรศรี นิมมานเหมินท์
รถสองแถว
รถแดง (เชียงใหม่)
คำเมือง
อักษรธรรมล้านนา
เวียงกุมกาม
ดอยสุเทพ
อุทกภัยในประเทศไทย พ.ศ. 2567
กาดหลวง (เชียงใหม่)
กาดสวนแก้ว
ไนท์บาซาร์ (เชียงใหม่)
ถนนคนเดินท่าแพ
ผังเมืองรวมเมืองเชียงใหม่
""".strip().splitlines()


def fetch(title: str, lang: str) -> dict | None:
    api = f"https://{lang}.wikipedia.org/w/api.php"
    q = {"action": "query", "format": "json", "prop": "extracts|info", "explaintext": 1,
         "redirects": 1, "inprop": "url", "titles": title}
    req = urllib.request.Request(api + "?" + urllib.parse.urlencode(q), headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
    except Exception as e:  # noqa: BLE001
        print(f"  ! {title}: {e}")
        return None
    for p in d.get("query", {}).get("pages", {}).values():
        if "missing" in p or not p.get("extract"):
            return None
        return {"title": p["title"], "url": p.get("fullurl", ""), "rev": p.get("lastrevid"),
                "lang": lang, "text": p["extract"]}
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "corpus"))
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print("\n".join(EN + TH))
        return 0
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    today = time.strftime("%Y-%m-%d")
    index, missing = [], []
    for lang, titles in (("en", EN), ("th", TH)):
        for t in titles:
            t = t.strip()
            if not t:
                continue
            d = fetch(t, lang)
            if not d:
                missing.append(f"{lang}:{t}")
                print(f"  MISSING {lang}:{t}")
                continue
            slug = slugify(d["title"]) or re.sub(r"\W+", "-", d["title"])[:60]
            name = f"{'wp' if lang == 'en' else 'th'}-{slug}.txt"
            (out / name).write_text(
                f"# {d['title']}\n# {d['url']}\n# revision {d['rev']}\n# fetched {today}\n"
                f"# Wikipedia, CC BY-SA 4.0\n\n{d['text']}\n", encoding="utf-8")
            index.append({"id": f"s:{'wp' if lang == 'en' else 'thwp'}-{slug}", "kind": "web",
                          "title": d["title"], "publisher": f"Wikipedia ({lang})", "url": d["url"],
                          "accessed": today, "file": name, "words": len(d["text"].split())})
            print(f"  {name}  {len(d['text'].split())} words")
            time.sleep(0.4)
    jdump({"fetched": today, "licence": "CC BY-SA 4.0", "articles": index, "missing": missing},
          out / "_index.json")
    print(f"\n{len(index)} articles into {out}; {len(missing)} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
