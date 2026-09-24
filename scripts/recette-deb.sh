#!/usr/bin/env bash
# P-099 (acceptée par Ludo le 24/09/2026) : recette automatique du paquet .deb,
# porte du workflow de release. B-948 (DOCX en échec sur .deb depuis la 0.4.6)
# et B-949 (bibliothèques du bundle prêtées aux outils du poste) ne se voyaient
# qu'en ouvrant le .deb publié : aucun contrôle ne regardait l'artefact Linux.
#
# Usage : bash scripts/recette-deb.sh <chemin/vers/therese_X.Y.Z_amd64.deb> [version attendue]
#
# Le paquet est EXTRAIT (dpkg-deb -x), pas installé : aucun droit administrateur,
# même arborescence que /usr/lib, rendue non inscriptible (chmod -R a-w) pour
# reproduire le bundle en lecture seule qu'installe dpkg.
# Étapes : 1. les dossiers témoins docx/parts, pptx/oxml, pptx/shapes sont dans
# le paquet ; 2. le moteur démarre depuis l'arborescence en lecture seule et
# annonce la bonne version ; 3. il génère un DOCX avec pied de page (le chemin
# de B-948). B-949 (LD_LIBRARY_PATH prêté aux outils du poste) reste couvert
# par tests/test_b949_environnement_sous_processus.py, pas par cette recette.
set -uo pipefail

DEB="${1:?chemin du .deb requis}"
ATTENDUE="${2:-}"
PORT="${THERESE_RECETTE_PORT:-17593}"
TRAVAIL="$(mktemp -d)"
RACINE="$TRAVAIL/racine"
DONNEES="$TRAVAIL/donnees"
JOURNAL="$TRAVAIL/moteur.log"
PID=""
echecs=0

nettoyer() {
  [ -n "$PID" ] && kill "$PID" 2>/dev/null
  chmod -R u+w "$RACINE" 2>/dev/null
}
trap nettoyer EXIT

ok() { echo "[OK] $*"; }
ko() { echo "[ÉCHEC] $*"; echecs=$((echecs + 1)); }

echo "== Recette du paquet : $DEB"
[ -f "$DEB" ] || { echo "[ÉCHEC] paquet introuvable"; exit 1; }

# 1. Contenu du paquet
contenu="$(dpkg-deb -c "$DEB")"
for requis in docx/parts pptx/oxml pptx/shapes docx/templates/default-footer.xml; do
  # Pas de tube vers grep -q : sous pipefail, la coupure de printf ferait échouer le test.
  if grep -q "/_internal/$requis" <<< "$contenu"; then ok "le paquet contient $requis"; else ko "le paquet ne contient pas $requis (B-948)"; fi
done

# 2. Extraction en lecture seule, puis démarrage du moteur
mkdir -p "$RACINE" "$DONNEES"
dpkg-deb -x "$DEB" "$RACINE"
MOTEUR="$(find "$RACINE" -type f -name backend -perm -u+x -path '*backend-libs*' | head -1)"
[ -n "$MOTEUR" ] || MOTEUR="$(find "$RACINE" -type f -name backend -perm -u+x | head -1)"
if [ -z "$MOTEUR" ]; then ko "exécutable du moteur introuvable dans le paquet"; echo "== $echecs échec(s)"; exit 1; fi
ok "moteur : ${MOTEUR#"$RACINE"}"
chmod -R a-w "$RACINE"
if [ -w "$(dirname "$MOTEUR")" ]; then ko "l'arborescence extraite reste inscriptible (contre-épreuve invalide)"; else ok "arborescence en lecture seule"; fi

THERESE_DATA_DIR="$DONNEES" HOME="$TRAVAIL" "$MOTEUR" --host 127.0.0.1 --port "$PORT" > "$JOURNAL" 2>&1 &
PID=$!
etat=""
for _ in $(seq 1 180); do
  etat="$(curl -s -m 2 "http://127.0.0.1:$PORT/health" || true)"
  [ -n "$etat" ] && break
  kill -0 "$PID" 2>/dev/null || break
  sleep 1
done
if [ -z "$etat" ]; then
  ko "le moteur n'a pas répondu sur /health"; tail -40 "$JOURNAL"; echo "== $echecs échec(s)"; exit 1
fi
version="$(printf '%s' "$etat" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("version",""))')"
ok "moteur prêt, version $version"
if [ -n "$ATTENDUE" ] && [ "$version" != "$ATTENDUE" ]; then ko "version $version, attendue $ATTENDUE"; fi

# 3. DOCX avec pied de page (profil d'export par défaut : « Généré par THÉRÈSE - Synoptïa »)
JETON="$(curl -s "http://127.0.0.1:$PORT/api/auth/token" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("token",""))')"
api() { curl -s -m 60 -H "X-Therese-Token: $JETON" -H "Content-Type: application/json" "$@"; }
doc="$(api -X POST "http://127.0.0.1:$PORT/api/documents" -d '{"title":"Recette paquet","brief":"Contrôle du .deb"}' | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))')"
sec="$(api -X POST "http://127.0.0.1:$PORT/api/documents/$doc/sections" -d '{"title":"Introduction","brief":"","order":10,"depth":0}' | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))')"
api -X PATCH "http://127.0.0.1:$PORT/api/documents/sections/$sec" -d '{"content":"Paragraphe de contrôle du paquet Linux."}' > /dev/null
export_json="$(api "http://127.0.0.1:$PORT/api/documents/$doc/export?format=docx")"
url="$(printf '%s' "$export_json" | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("download_url") or "")
except Exception: print("")')"
chemin="$TRAVAIL/export.docx"
[ -n "$url" ] && curl -s -m 60 -H "X-Therese-Token: $JETON" -o "$chemin" "http://127.0.0.1:$PORT$url"
if [ -n "$url" ] && [ -s "$chemin" ]; then
  ok "DOCX généré ($(wc -c < "$chemin") octets)"
  if python3 - "$chemin" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    pieds = [n for n in z.namelist() if n.startswith("word/footer")]
    texte = "".join(z.read(n).decode("utf-8", "replace") for n in pieds)
sys.exit(0 if "THÉRÈSE" in texte else 1)
PY
  then ok "pied de page présent (chemin de B-948)"; else ko "DOCX sans pied de page"; fi
else
  ko "export DOCX en échec : ${export_json:0:300}"
fi
if grep -qE "FileNotFoundError|Traceback" "$JOURNAL"; then ko "trace au journal du moteur"; grep -nE "FileNotFoundError|Traceback" "$JOURNAL" | head -5; fi

echo "== $echecs échec(s)"
[ "$echecs" -eq 0 ]
