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

# README : badge de version (suffixe -alpha conventionnel ; shields.io escape '-' en '--')
README="$ROOT/README.md"
if [ -f "$README" ]; then
    sed -i '' -E 's|(badge/version-)[0-9]+\.[0-9]+\.[0-9]+(--alpha)|\1'"$NEW"'\2|' "$README"
    if grep -q "badge/version-$NEW--alpha" "$README"; then
        echo "  OK  README.md (badge version)"
    else
        echo "  ATTENTION  README.md badge non mis a jour (format inattendu, verifier a la main)"
    fi
fi

echo ""

# Regeneration des lockfiles (oublis des releases 0.23/0.24 : uv.lock et
# package-lock.json partaient avec l'ancienne version).
echo "Lockfiles:"
if command -v npm >/dev/null 2>&1; then
    (cd "$ROOT/src/frontend" && npm install --package-lock-only --silent) && echo "  OK  src/frontend/package-lock.json"
else
    echo "  ATTENTION  npm introuvable, package-lock.json non regenere"
fi
if command -v cargo >/dev/null 2>&1; then
    (cd "$ROOT/src/frontend/src-tauri" && cargo update -p therese --quiet 2>/dev/null) && echo "  OK  src/frontend/src-tauri/Cargo.lock" || echo "  ATTENTION  Cargo.lock non regenere (verifier a la main)"
else
    echo "  ATTENTION  cargo introuvable, Cargo.lock non regenere"
fi
if command -v uv >/dev/null 2>&1; then
    (cd "$ROOT" && uv lock --quiet) && echo "  OK  uv.lock"
else
    echo "  ATTENTION  uv introuvable, uv.lock non regenere"
fi

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
echo "Version $NEW appliquee dans les 7 fichiers (+ badge README + lockfiles)."
