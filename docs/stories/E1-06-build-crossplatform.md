# Story E1-06 : Configurer le build cross-platform

## Description

En tant que **développeur**,
Je veux **pouvoir builder THÉRÈSE pour macOS, Windows et Linux**,
Afin de **distribuer l'application à tous les utilisateurs**.

## Contexte technique

- **Composants impactés** : Build system, CI/CD
- **Dépendances** : E1-01, E1-02, E1-05
- **Fichiers concernés** :
  - `src-tauri/tauri.conf.json` (màj)
  - `.github/workflows/build.yml` (nouveau)
  - `Makefile` (màj)
  - `scripts/build.sh` (nouveau)

## Critères d'acceptation

- [ ] `make build-macos` génère un .dmg fonctionnel
- [ ] `make build-windows` génère un .msi (cross-compile ou CI)
- [ ] `make build-linux` génère un .AppImage
- [ ] Backend Python bundlé avec PyInstaller
- [ ] Taille bundle macOS < 50 Mo
- [ ] Code signing configuré (macOS)
- [ ] GitHub Actions pour CI build

## Notes techniques

### Bundle du backend Python

```bash
# Script de bundle backend
# scripts/bundle-backend.sh

#!/bin/bash
cd src/backend

# Installer PyInstaller
uv add --dev pyinstaller

# Build executable
uv run pyinstaller \
  --name therese-backend \
  --onefile \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops \
  --hidden-import uvicorn.protocols \
  therese/main.py

# Copier dans le dossier Tauri
cp dist/therese-backend ../src-tauri/binaries/
```

### Configuration Tauri build

```json
// src-tauri/tauri.conf.json
{
  "bundle": {
    "active": true,
    "targets": ["dmg", "app"],
    "identifier": "fr.synoptia.therese",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "externalBin": [
      "binaries/therese-backend"
    ],
    "macOS": {
      "minimumSystemVersion": "10.15",
      "signingIdentity": null,
      "entitlements": null
    },
    "windows": {
      "certificateThumbprint": null,
      "wix": null
    },
    "linux": {
      "appimage": {
        "bundleMediaFramework": false
      }
    }
  }
}
```

### Makefile targets

```makefile
# Makefile

.PHONY: build build-macos build-windows build-linux bundle-backend

# Bundle backend Python
bundle-backend:
	@echo "📦 Bundling Python backend..."
	./scripts/bundle-backend.sh

# Build macOS
build-macos: bundle-backend
	@echo "🍎 Building for macOS..."
	cd src-tauri && cargo tauri build --target aarch64-apple-darwin

# Build Windows (requires cross-compile toolchain)
build-windows: bundle-backend
	@echo "🪟 Building for Windows..."
	cd src-tauri && cargo tauri build --target x86_64-pc-windows-msvc

# Build Linux
build-linux: bundle-backend
	@echo "🐧 Building for Linux..."
	cd src-tauri && cargo tauri build --target x86_64-unknown-linux-gnu

# All platforms
build: build-macos
	@echo "✅ Build complete!"
```

### GitHub Actions CI

```yaml
# .github/workflows/build.yml
name: Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        include:
          - platform: macos-latest
            target: aarch64-apple-darwin
          - platform: macos-latest
            target: x86_64-apple-darwin
          - platform: ubuntu-latest
            target: x86_64-unknown-linux-gnu
          - platform: windows-latest
            target: x86_64-pc-windows-msvc

    runs-on: ${{ matrix.platform }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Setup Rust
        uses: dtolnay/rust-action@stable

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install UV
        run: pip install uv

      - name: Bundle backend
        run: make bundle-backend

      - name: Build Tauri
        uses: tauri-apps/tauri-action@v0
        with:
          tagName: ${{ github.ref_name }}
          releaseName: 'THÉRÈSE v__VERSION__'
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Definition of Done

- [ ] Build macOS génère un .dmg fonctionnel
- [ ] Bundle < 50 Mo
- [ ] CI GitHub Actions configuré
- [ ] Documentation de release

---

*Sprint : 1*
*Assigné : Agent Dev*
