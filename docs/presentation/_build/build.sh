#!/usr/bin/env bash
# Fabrique le PDF du guide de présentation depuis guide.html.
# 1. Les captures JPEG de shots-web/ (1300 px, q78) sont la source versionnée : 9,5 Mo pour 92 captures.
#    Les PNG d'origine vivent hors dépôt (~/.claude/docs/therese-guide-0.66-captures-png/) ; s'ils sont
#    déposés dans shots/ (ignoré par git), ils sont reconvertis. Ne jamais commiter de PNG : garde pre-commit 3 Mo.
# 2. Chrome headless rend le PDF. Vérifier ensuite page par page avec qlmanage (moteur Apple), jamais pdftoppm seul.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p shots-web
if ls shots/*.png >/dev/null 2>&1; then
  for f in shots/*.png; do b=$(basename "$f" .png); sips -Z 1300 -s format jpeg -s formatOptions 78 "$f" --out "shots-web/$b.jpg" >/dev/null; done
fi
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-sandbox --no-pdf-header-footer \
  --allow-file-access-from-files --virtual-time-budget=8000 --print-to-pdf=guide.pdf "file://$PWD/guide.html"
cp guide.pdf ../THERESE-0.66-guide-de-presentation.pdf
ls -la guide.pdf
