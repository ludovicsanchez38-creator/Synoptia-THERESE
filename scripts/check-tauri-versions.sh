#!/bin/bash
# check-tauri-versions.sh - Vérifie l'alignement des versions Tauri Rust/NPM
# Utilisé par /release-therese pour éviter les mismatch qui cassent le build CI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../src/frontend"
CARGO_LOCK="$FRONTEND_DIR/src-tauri/Cargo.lock"
PKG_LOCK="$FRONTEND_DIR/package-lock.json"

if [ ! -f "$CARGO_LOCK" ]; then
  echo "ERREUR: $CARGO_LOCK introuvable"
  exit 1
fi
if [ ! -f "$PKG_LOCK" ]; then
  echo "ERREUR: $PKG_LOCK introuvable"
  exit 1
fi

errors=0

check_pair() {
  local crate="$1"
  local npm_pkg="$2"

  # Version Rust depuis Cargo.lock
  # B-118 : sans le « || true », un crate absent fait echouer l affectation sous
  # « set -euo pipefail » et tue le script AVANT le message ci-dessous, qui etait
  # donc du code mort : le controle s arretait muet au milieu de sa liste.
  local rust_ver
  rust_ver=$(grep -A1 "name = \"$crate\"" "$CARGO_LOCK" | grep 'version' | head -1 | sed 's/.*"\(.*\)"/\1/') || true
  local rust_mm
  rust_mm=$(echo "$rust_ver" | cut -d. -f1-2)

  # Version NPM depuis package-lock.json
  local npm_ver
  npm_ver=$(node -e "const l=require('$PKG_LOCK'); console.log(l.packages?.['node_modules/$npm_pkg']?.version || 'N/A')" 2>/dev/null)
  local npm_mm
  npm_mm=$(echo "$npm_ver" | cut -d. -f1-2)

  # B-118 : une paire attendue et introuvable est un ECHEC du controle, pas un
  # SKIP. Un renommage cote npm sortait en 0 sur « Toutes les versions Tauri
  # sont alignées » alors que la paire n avait jamais ete comparee.
  if [ -z "$rust_ver" ]; then
    echo "ERREUR: $crate non trouvé dans Cargo.lock (crate renommé ou retiré ?)"
    errors=$((errors + 1))
    return
  fi

  if [ "$npm_ver" = "N/A" ] || [ -z "$npm_ver" ]; then
    echo "ERREUR: $npm_pkg non trouvé dans package-lock.json (paquet renommé ou retiré ?)"
    errors=$((errors + 1))
    return
  fi

  if [ "$rust_mm" != "$npm_mm" ]; then
    echo "MISMATCH: $crate=$rust_ver vs $npm_pkg=$npm_ver (${rust_mm} != ${npm_mm})"
    errors=$((errors + 1))
  else
    echo "OK: $crate=$rust_ver ~ $npm_pkg=$npm_ver"
  fi
}

check_pair "tauri" "@tauri-apps/api"
check_pair "tauri-plugin-dialog" "@tauri-apps/plugin-dialog"
check_pair "tauri-plugin-fs" "@tauri-apps/plugin-fs"
check_pair "tauri-plugin-shell" "@tauri-apps/plugin-shell"
check_pair "tauri-plugin-process" "@tauri-apps/plugin-process"
check_pair "tauri-plugin-updater" "@tauri-apps/plugin-updater"
check_pair "tauri-plugin-mic-recorder" "tauri-plugin-mic-recorder-api"

echo ""
if [ $errors -gt 0 ]; then
  echo "ERREUR: $errors anomalie(s) Tauri détectée(s) (écart de version ou paire introuvable)"
  echo "Corriger avec: cargo update -p <crate> --precise <version>"
  echo "Si une paire a été renommée, mettre à jour la liste check_pair de ce script."
  exit 1
fi

echo "Toutes les versions Tauri sont alignées."
