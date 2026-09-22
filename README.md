# Roads of Chiang Mai · ถนนหนทางเจียงใหม่

The square of 1296, four rings around it, the roads between, and what each one did to the
city. Counted from the map, dated from the record. Bilingual, English and Thai in the
northern register.

- **Live:** https://motdang.net/roads/ (canonical) · https://nanobotco.github.io/chiang-mai-roads/
- **Thai:** https://motdang.net/roads/th/
- **API:** https://motdang.net/roads/api/ — every figure on the site, as JSON

## What is in it

Fifteen kinds of record: roads, rings, lanes (the *hom*), gates and corners, junctions,
bridges, highways out, plans, eras, measurements, traffic figures, Kam Mueang words,
stories, people and places. Every reader-facing field exists in English and in Thai; a
record with no Thai says so.

Pages: the map (every way over shaded relief, the rings on top, every lane inside the
moat, an orientation rose per zone, the named roads coloured by era, the roads out), rings,
the old city measured, highways out, a timeline from 1296 to the light rail's latest
opening date, plans with status and money, traffic (the highway department's 81 counting
stations, five years; road deaths by year; TomTom's minutes; the red trucks), numbers,
words, stories, and a quiz.

## Where the numbers come from

- **OpenStreetMap** by Overpass, in a hundred tiles, for every `highway=*` way in a box
  from Mae Rim to Saraphi and Doi Suthep to San Kamphaeng, plus the wats, the water, the
  signals and the bridges. ODbL. `tools/harvest_osm.py`, cached under `data/harvest/_raw/`.
- **The measurements** (`tools/measure.py`): kilometres by class, intersections per km²,
  dead-end share, median block length, Boeing's orientation-order index φ, one-way share,
  soi share, wats and signals, in five zones — the square inside the moat and bands of
  distance from its centre. Intersections, dead ends, blocks and orientation use the
  drivable network without service lanes. The old-city page prints the table and says
  what each column is.
- **Traffic counts**: the Department of Highways' open-data AADT CSVs, 2563–2568 BE,
  filtered to the province. Motorcycles are a separate column and the page says so.
- **Road deaths**: the Department of Disease Control's three-database file, one row per
  death, filtered to the province of death.
- **Dates and money**: Thai and English Wikipedia at named revisions, a 2005 Chiang Mai
  University geography thesis, the municipality's own data sheet, department releases and
  the newspapers. Every source is in `data/sources/sources.json` and every claim carries
  a tier: cited, harvested, tradition or inference.
- **Relief**: Copernicus DEM through Open-Meteo, 4,485 points, shaded and tinted.
- **Pictures**: Wikimedia Commons, free licences only, author and licence beside each.

Counts on the site are computed at build time from these files; the README carries none
that could drift.

## Build

```bash
python3 tools/harvest_osm.py --all      # OpenStreetMap, cached
python3 tools/harvest_base.py --elevation
python3 tools/harvest_commons.py --harvest --apply && python3 tools/shrink.py
./publish.sh                            # validate · measure · build · maps · site · cards · links → docs/
python3 tools/serve.py 8820             # local preview
```

`publish.sh` builds the GitHub Pages copy; the motdang copy is built with
`SITE_URL=https://motdang.net/roads`.

## Layout

```
data/nodes/<type>/<id>.json   the records
data/sources/sources.json     every source, by id
data/vocab/                   types, regions, facets, tags
data/harvest/                 OSM, elevation, AADT, deaths, TomTom, measures
data/images/<id>/             pictures with sidecar JSON
tools/                        harvest · measure · build · maps · terrain · site · pages · cards · links
schema/node.schema.json       what a record is
docs/                         the built site
```

## Licence

Records, prose and pages CC BY 4.0. Code MIT. Third-party data under its own terms, listed
in NOTICE.txt.

Made by [hongdam.net](https://hongdam.net/), a bilingual web studio in Chiang Rai.

<!-- fleet-roster -->

## Elsewhere from the same publisher

- [Mot Dang](https://motdang.net/) — city directory for Chiang Mai and Chiang Rai
- [The Mae Hong Son Loop](https://nanobotco.github.io/mae-hong-son-loop/) — motorcycling the 600 km loop out of Chiang Mai — curves counted, air measured
- [Muay Thai](https://motdang.net/muay-thai/) — the eight limbs, the thirty named techniques, the ceremony, and every gym on the map
- [wichaa](https://wichaa.net/) — Lanna manuscripts, the amulet market, and the traditions around them
- [Hand Poke](https://nanobotco.github.io/hand-poke/) — 28 traditions of marking skin by hand — the leg-tattoo zone of Burma, the Shan States and Lanna, counted
- [Black Holes, Drawn](https://nanobotco.github.io/black-holes/) — black holes modelled and drawn from the equations — generators, the past, present and future, the legends
- [Quantum Computing, plainly](https://nanobotco.github.io/quantum-computing/) — the history and theory of quantum computing in plain words, with demos; refreshed weekly
- [Goin' Fast](https://nanobotco.github.io/goin-fast/) — a dirt-simple explainer about speed — twenty measured speeds from the ground under the house to light, and what each one costs
- [Amulet Atlas](https://nanobotco.github.io/amulet-atlas/) — amulets, charms and talismans worldwide
- [Carolina Barbecue](https://nanobotco.github.io/carolina-barbecue/) — barbecue in North and South Carolina
- [Wing Country](https://nanobotco.github.io/buffalo-wings/) — the American chicken wing
- [Pink Box](https://nanobotco.github.io/pink-box/) — the American mom-and-pop donut shop
- [Basque Tables](https://nanobotco.github.io/basque-tables/) — Basque dining rooms of California, Nevada and Idaho
- [Pinot Country](https://nanobotco.github.io/pinot-noir/) — pinot noir: the vine, the regions, the cellars
- [Care Abroad](https://nanobotco.github.io/care-abroad/) — treatment across borders, with published prices and their dates
- [Thai Roots](https://nanobotco.github.io/thairoots/) — a root dictionary of Thai, with a word decomposer
- [The index](https://nanobotco.github.io/index/) — every corpus, site and repository, counted
- [Uptake](https://nanobotco.github.io/uptake/) — a field manual on publishing for machines that copy
- [NaNoBotCo](https://nanobotco.github.io/) — the portal
- [ฮักฝรั่ง](https://hakfarang.net/) — เรื่องเงิน วีซ่า และชีวิตกับแฟนฝรั่ง
- [Offrampt](https://offrampt.net/) — turning crypto into spendable local money, Thailand first

All of it, counted: https://nanobotco.github.io/index/ · roster as JSON: https://nanobotco.github.io/index/fleet.json
