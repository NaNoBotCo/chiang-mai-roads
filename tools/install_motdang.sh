#!/bin/bash
# Build the motdang.net copy and install it into mot-dang/assets/roads/, from where
# mot-dang's build.py copies it into docs/ (the tree deploy.py syncs).
#
#   ./tools/install_motdang.sh
#   cd ../mot-dang && python3 build.py && python3 publish/deploy.py --only roads --yes
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONUTF8=1
SITE_URL=https://motdang.net/roads python3 tools/build.py
SITE_URL=https://motdang.net/roads python3 tools/site.py
python3 tools/cards.py
SITE_URL=https://motdang.net/roads python3 tools/site.py
python3 tools/links.py
DEST="../mot-dang/assets/roads"
rm -rf "$DEST" && mkdir -p "$DEST"
cp -R build/site/ "$DEST/"
rm -f "$DEST/.basepath"
if grep -rl "/Users/" "$DEST" >/dev/null 2>&1; then echo "REFUSED: host paths"; exit 2; fi
echo "installed $(find "$DEST" -name '*.html' | wc -l | tr -d ' ') pages into $DEST"
