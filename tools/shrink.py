#!/usr/bin/env python3
"""shrink.py — take the harvested pictures down to a size a phone on a hill can load.

Commons is asked for 1200 px renditions, which is right for a source file and wrong for a
page carrying four of them on a mountain road with one bar of signal. This re-encodes in
place to a maximum edge of 1100 px and quality 74, and writes a 480 px thumbnail beside
each one for cards and strips.

The sidecar JSON keeps the original URL, so the full-size file is always one click away
and nothing about the licence or the attribution changes.

    python3 tools/shrink.py            # re-encode anything not already done
    python3 tools/shrink.py --force
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import IMAGES, ROOT, jdump, jload  # noqa: E402

MAX_EDGE = 1100
# A map sheet is read, not glanced at: at 1100 px a 1:5,000 city plan is a grey smudge.
# Records whose id starts with map- keep four times the pixels and a higher quality.
MAP_EDGE = 2600
MAP_QUALITY = 82
# A PNG under the pixel cap is never touched by the resize branch, and a scanned map can
# be nine megabytes at 2,592 px. Anything over this budget is re-encoded as JPEG and
# renamed, and the records that point at it are corrected in the same pass.
BYTE_BUDGET = 1_500_000
THUMB_EDGE = 480
QUALITY = 74
THUMB_QUALITY = 70


def repoint(old_rel: str, new_rel: str):
    """A file was renamed; every record that names it says the new name."""
    for f in sorted((ROOT / "data" / "nodes").rglob("*.json")):
        d = jload(f)
        hit = False
        for im in (d.get("images") or []):
            if im.get("file") == old_rel:
                im["file"] = new_rel
                hit = True
        if hit:
            jdump(d, f)


def main() -> int:
    from PIL import Image, ImageOps
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    before = after = 0
    done = thumbs = 0
    for p in sorted(IMAGES.rglob("*")):
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp") or ".thumb." in p.name:
            continue
        before += p.stat().st_size
        thumb = p.with_suffix(".thumb.jpg")
        try:
            im = ImageOps.exif_transpose(Image.open(p))
            im.load()
        except Exception as e:  # noqa: BLE001
            print(f"  ! {p.name}: {e}")
            after += p.stat().st_size
            continue
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        w, h = im.size
        # A map sheet is read, not glanced at: at 1100 px a 1:5,000 city plan is a grey
        # smudge, so records whose id starts with map- keep more pixels and more quality.
        is_map = p.parent.name.startswith("map-")
        edge = MAP_EDGE if is_map else MAX_EDGE
        q = MAP_QUALITY if is_map else QUALITY
        if max(w, h) > edge:
            s = edge / max(w, h)
            im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
            im.save(p, "JPEG", quality=q, optimize=True, progressive=True)
            done += 1
        elif a.force:
            im.save(p, "JPEG", quality=q, optimize=True, progressive=True)
            done += 1
        # an oversized PNG becomes a JPEG, under its own name
        if p.suffix.lower() == ".png" and p.stat().st_size > BYTE_BUDGET:
            newp = p.with_suffix(".jpg")
            im.save(newp, "JPEG", quality=q, optimize=True, progressive=True)
            rel_old = str(p.relative_to(IMAGES))
            side = p.with_suffix(p.suffix + ".json")
            if side.exists():
                side.rename(newp.with_suffix(newp.suffix + ".json"))
            p.unlink()
            repoint(rel_old, str(newp.relative_to(IMAGES)))
            print(f"  {p.name} → {newp.name}")
            p = newp
            thumb = p.with_suffix(".thumb.jpg")
            done += 1

        if a.force or not thumb.exists():
            t = im.copy()
            tw, th = t.size
            s = THUMB_EDGE / max(tw, th)
            if s < 1:
                t = t.resize((round(tw * s), round(th * s)), Image.LANCZOS)
            t.save(thumb, "JPEG", quality=THUMB_QUALITY, optimize=True, progressive=True)
            thumbs += 1
        after += p.stat().st_size + (thumb.stat().st_size if thumb.exists() else 0)
    print(f"shrink: {done} re-encoded, {thumbs} thumbnails · "
          f"{before / 1e6:.1f} MB → {after / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
