#!/bin/bash
# Build the public site into docs/ — the directory GitHub Pages serves.
#
# The canonical host comes from docs/CNAME when a domain is attached, and falls back to
# the GitHub Pages address. To attach a domain later:  CNAME=example.com ./publish.sh
# To make this copy the canonical one rather than motdang.net:
#   CANONICAL_URL=https://nanobotco.github.io/chiang-mai-roads ./publish.sh
# The motdang copy is built with SITE_URL=https://motdang.net/roads.
set -euo pipefail
cd "$(dirname "$0")"

DOMAIN="${CNAME:-$(head -1 docs/CNAME 2>/dev/null || true)}"
if [ -n "$DOMAIN" ]; then SITE_URL="https://$DOMAIN"
else SITE_URL="${SITE_URL:-https://nanobotco.github.io/chiang-mai-roads}"; fi

export PYTHONUTF8=1

STYLE="$HOME/.claude/bin/stylecheck.py"
if [ -f "$STYLE" ]; then
  # the corpus is Wikipedia text and is not this project's prose, so it is not gated
  python3 "$STYLE" tools data/nodes data/vocab data/sources schema README.md NOTICE.txt || {
    echo "REFUSED: style. See ~/.claude/STYLE.md"; exit 4; }
fi

python3 tools/validate.py
python3 tools/measure.py
SITE_URL="$SITE_URL" python3 tools/build.py
python3 tools/terrain.py --width 1400
python3 tools/terrain.py --width 1400 --dark --out build/site/terrain-dark.png
python3 tools/maps.py
SITE_URL="$SITE_URL" python3 tools/site.py
python3 tools/cards.py
# the cards did not exist when the pages were written, so the pages are written again
# with the card each one now has
SITE_URL="$SITE_URL" python3 tools/site.py

# every internal reference, resolved where the host mounts the site — and again from
# the URL without its trailing slash, which is the one people type and the one a host
# may answer with a 200 instead of a redirect
python3 tools/links.py

rm -rf docs
mkdir -p docs
cp -R build/site/ docs/
touch docs/.nojekyll                      # so /api/ and dot-files are served as-is
[ -n "$DOMAIN" ] && echo "$DOMAIN" > docs/CNAME

# nothing that names this machine may be published
if grep -rl "/Users/" docs >/dev/null 2>&1; then
  echo "REFUSED: host paths found in docs/"; exit 2
fi
echo "docs/ built for $SITE_URL — $(find docs -name '*.html' | wc -l | tr -d ' ') pages, $(du -sh docs | cut -f1)"
