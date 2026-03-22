#!/bin/bash
# bump-version.sh - Met a jour la version dans les 7 fichiers du projet
# Usage: ./scripts/bump-version.sh 0.6.3

set -euo pipefail

NEW="${1:-}"
if [ -z "$NEW" ]; then
    echo "Usage: $0 <version>"
    echo "Exemple: $0 0.6.3"
    exit 1
fi

# Validation format semver
if ! echo "$NEW" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
    echo "Erreur: format de version invalide '$NEW' (attendu: X.Y.Z ou X.Y.Z-suffix)"
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

FILES=(
    "$ROOT/pyproject.toml"
    "$ROOT/package.json"
    "$ROOT/src/frontend/package.json"
    "$ROOT/src/frontend/src-tauri/tauri.conf.json"
    "$ROOT/src/frontend/src-tauri/Cargo.toml"
    "$ROOT/src/backend/app/config.py"
    "$ROOT/src/backend/app/__init__.py"
)

echo "Bump version -> $NEW"
echo ""

ERRORS=0

for f in "${FILES[@]}"; do
    if [ ! -f "$f" ]; then
        echo "  ERREUR: $f introuvable"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    REL="${f#$ROOT/}"

    case "$REL" in
        pyproject.toml|package.json|src/frontend/package.json)
            # JSON/TOML: "version": "X.Y.Z" ou version = "X.Y.Z"
            sed -i '' -E 's/("version"[[:space:]]*:[[:space:]]*"|version[[:space:]]*=[[:space:]]*")[0-9]+\.[0-9]+\.[0-9]+[^"]*/\1'"$NEW"'/' "$f"
            ;;
        src/frontend/src-tauri/tauri.conf.json)
            # JSON: "version": "X.Y.Z"
            sed -i '' -E 's/("version"[[:space:]]*:[[:space:]]*")[0-9]+\.[0-9]+\.[0-9]+[^"]*/\1'"$NEW"'/' "$f"
            ;;
        src/frontend/src-tauri/Cargo.toml)
            # TOML: version = "X.Y.Z"
            sed -i '' -E 's/(version[[:space:]]*=[[:space:]]*")[0-9]+\.[0-9]+\.[0-9]+[^"]*/\1'"$NEW"'/' "$f"
            ;;
        src/backend/app/config.py)
            # Python: app_version: str = "X.Y.Z"
            sed -i '' -E 's/(app_version[[:space:]]*:[[:space:]]*str[[:space:]]*=[[:space:]]*")[0-9]+\.[0-9]+\.[0-9]+[^"]*/\1'"$NEW"'/' "$f"
            ;;
        src/backend/app/__init__.py)
            # Python: __version__ = "X.Y.Z"
            sed -i '' -E 's/(__version__[[:space:]]*=[[:space:]]*")[0-9]+\.[0-9]+\.[0-9]+[^"]*/\1'"$NEW"'/' "$f"
            ;;
    esac

    echo "  OK  $REL"
done

echo ""

# Verification post-bump
echo "Verification:"
VERIFY_ERRORS=0
for f in "${FILES[@]}"; do
    if [ ! -f "$f" ]; then continue; fi
    REL="${f#$ROOT/}"
    if grep -q "$NEW" "$f"; then
        echo "  OK  $REL contient $NEW"
    else
        echo "  ERREUR  $REL ne contient pas $NEW"
        VERIFY_ERRORS=$((VERIFY_ERRORS + 1))
    fi
done

if [ $ERRORS -gt 0 ] || [ $VERIFY_ERRORS -gt 0 ]; then
    echo ""
    echo "Des erreurs ont ete detectees. Verifier manuellement."
    exit 1
fi

echo ""
echo "Version $NEW appliquee dans les 7 fichiers."
