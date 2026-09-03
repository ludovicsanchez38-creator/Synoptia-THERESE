#!/usr/bin/env bash
# Fabrique le PDF du guide de présentation depuis guide.html.
# 1. Les captures de shots/ (PNG) sont converties en JPEG dans shots-web/ (hors dépôt) pour tenir sous la limite Discord.
# 2. Chrome headless rend le PDF. Vérifier ensuite page par page avec qlmanage (moteur Apple), jamais pdftoppm seul.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p shots-web
for f in shots/*.png; do b=$(basename "$f" .png); sips -Z 1300 -s format jpeg -s formatOptions 78 "$f" --out "shots-web/$b.jpg" >/dev/null; done
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-sandbox --no-pdf-header-footer \
  --allow-file-access-from-files --virtual-time-budget=8000 --print-to-pdf=guide.pdf "file://$PWD/guide.html"
cp guide.pdf ../THERESE-0.66-guide-de-presentation.pdf
ls -la guide.pdf
