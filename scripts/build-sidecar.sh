#!/usr/bin/env bash
# =============================================================
# THÉRÈSE v2 - Build du sidecar backend (PyInstaller)
#
# Détecte la target triple, lance PyInstaller, copie le binaire
# dans src/frontend/src-tauri/binaries/backend-{triple}
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/src/backend"
TAURI_BINARIES="$PROJECT_ROOT/src/frontend/src-tauri/binaries"

# ---- Détection de la target triple ----
detect_target_triple() {
    local os arch triple

    case "$(uname -s)" in
        Darwin) os="apple-darwin" ;;
        Linux)  os="unknown-linux-gnu" ;;
        MINGW*|MSYS*|CYGWIN*) os="pc-windows-msvc" ;;
        *)
            echo "❌ OS non supporté : $(uname -s)"
            exit 1
            ;;
    esac

    case "$(uname -m)" in
        arm64|aarch64) arch="aarch64" ;;
        x86_64|amd64)  arch="x86_64" ;;
        *)
            echo "❌ Architecture non supportée : $(uname -m)"
            exit 1
            ;;
    esac

    triple="${arch}-${os}"
    echo "$triple"
}

TARGET_TRIPLE=$(detect_target_triple)
echo "🎯 Target triple : $TARGET_TRIPLE"

# ---- Build PyInstaller ----
echo "📦 Build du backend avec PyInstaller..."

cd "$BACKEND_DIR"

# Utiliser le venv du projet
PYINSTALLER="$PROJECT_ROOT/.venv/bin/pyinstaller"
if [ ! -f "$PYINSTALLER" ]; then
    echo "❌ PyInstaller non trouvé. Exécuter 'uv sync --dev' d'abord."
    exit 1
fi

# Nettoyer les builds précédents
rm -rf "$BACKEND_DIR/build" "$BACKEND_DIR/dist"

# Lancer PyInstaller avec le spec
"$PYINSTALLER" backend.spec --noconfirm --clean

# ---- Copie du binaire ----
echo "📁 Copie du binaire dans Tauri..."

mkdir -p "$TAURI_BINARIES"

# B-950 (23/09/2026) : sous Linux, backend.spec produit un dossier onedir
# (BUG-044), pas un binaire unique. Même traitement que release.yml : un
# wrapper shell comme sidecar, et le contenu du dossier dans backend-libs/.
if [[ "$TARGET_TRIPLE" == *"linux"* ]]; then
    ONEDIR="$BACKEND_DIR/dist/backend"
    if [ ! -d "$ONEDIR" ] || [ ! -f "$ONEDIR/backend" ]; then
        echo "❌ Sortie onedir introuvable : $ONEDIR/backend"
        exit 1
    fi
    LIBS_DIR="$TAURI_BINARIES/backend-libs"
    WRAPPER="$TAURI_BINARIES/backend-$TARGET_TRIPLE"
    rm -rf "$LIBS_DIR"
    mkdir -p "$LIBS_DIR"
    cp -r "$ONEDIR/." "$LIBS_DIR/"
    chmod +x "$LIBS_DIR/backend"
    printf '%s\n' \
        '#!/bin/sh' \
        '# THERESE - wrapper backend Linux (PyInstaller onedir, BUG-044)' \
        '# THERESE_BACKEND_LIBS est passe par lib.rs via app.path().resource_dir()' \
        'LIBS_DIR="${THERESE_BACKEND_LIBS:-$(cd "$(dirname "$0")" && pwd)/backend-libs}"' \
        'exec "$LIBS_DIR/backend" "$@"' \
        > "$WRAPPER"
    chmod +x "$WRAPPER"
    echo "✅ Sidecar prêt : $WRAPPER (onedir : $LIBS_DIR)"
    echo "   Taille : $(du -sh "$LIBS_DIR" | cut -f1)"
    exit 0
fi

BINARY_NAME="backend"
# Sur Windows, l'exécutable a une extension .exe
if [[ "$TARGET_TRIPLE" == *"windows"* ]]; then
    BINARY_NAME="backend.exe"
fi

SOURCE="$BACKEND_DIR/dist/$BINARY_NAME"
if [ ! -f "$SOURCE" ]; then
    echo "❌ Binaire non trouvé : $SOURCE"
    exit 1
fi

# Tauri résout automatiquement backend-{triple} selon la plateforme
DEST="$TAURI_BINARIES/backend-$TARGET_TRIPLE"
if [[ "$TARGET_TRIPLE" == *"windows"* ]]; then
    DEST="${DEST}.exe"
fi

cp "$SOURCE" "$DEST"
chmod +x "$DEST"

echo "✅ Sidecar prêt : $DEST"
echo "   Taille : $(du -sh "$DEST" | cut -f1)"
