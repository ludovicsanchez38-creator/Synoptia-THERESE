# THÉRÈSE v2 - Guide d'installation (développeurs)

> Guide pour installer THÉRÈSE v2 depuis les sources. Si tu es testeur alpha, télécharge plutôt le .dmg ou .exe depuis les [GitHub Releases](https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/releases).

---

## Table des matières

1. [Prérequis](#1-prérequis)
2. [Installation](#2-installation)
3. [Configuration initiale](#3-configuration-initiale)
4. [Lancement](#4-lancement)
5. [Build de l'application](#5-build-de-lapplication)
6. [Dépannage](#6-dépannage)

---

## 1. Prérequis

Avant de commencer, vérifiez que votre environnement remplit les conditions suivantes.

### Système

- **macOS 14+** (Sonoma ou plus récent) ou **Windows 10+** (build 1903+)
- **macOS** : [Homebrew](https://brew.sh) installé
- **Windows** : [Winget](https://learn.microsoft.com/en-us/windows/package-manager/) ou [Scoop](https://scoop.sh)

### Outils à installer

#### macOS

| Outil | Version minimale | Commande d'installation |
|-------|-----------------|------------------------|
| Python | 3.11+ | `brew install python@3.13` |
| Node.js | 20+ | `brew install node` |
| UV | dernière version | `brew install uv` (ou `pip install uv`) |
| Rust | stable | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |
| Docker | dernière version | [Docker Desktop pour Mac](https://www.docker.com/products/docker-desktop/) |

#### Windows

| Outil | Version minimale | Commande d'installation |
|-------|-----------------|------------------------|
| Python | 3.11+ | `winget install Python.Python.3.13` |
| Node.js | 20+ | `winget install OpenJS.NodeJS.LTS` |
| UV | dernière version | `pip install uv` (ou `irm https://astral.sh/uv/install.ps1 \| iex`) |
| Rust | stable | [rustup-init.exe](https://rustup.rs) (+ Visual Studio Build Tools C++) |
| Docker | dernière version | [Docker Desktop pour Windows](https://www.docker.com/products/docker-desktop/) |

### Vérification rapide

```bash
python3 --version    # Python 3.11+  (Windows : python --version)
node --version       # v20+
uv --version         # uv 0.x+
rustc --version      # rustc 1.x+
docker --version     # Docker 2x+
```

### Services externes

- **Docker** (obligatoire) - nécessaire pour faire tourner Qdrant
- **Qdrant** (base de données vectorielle) - lancé via Docker (voir section Lancement)

---

## 2. Installation

### Cloner le dépôt

```bash
git clone https://github.com/ludovicsanchez38-creator/Synoptia-THERESE.git
cd Synoptia-THERESE
```

### Installation automatique (recommandé)

Depuis la racine du projet :

```bash
make install
```

Cette commande exécute les deux étapes suivantes automatiquement.

### Installation manuelle

Si vous préférez installer les dépendances séparément :

**Backend** (Python/FastAPI) :

```bash
uv sync
```

> `uv sync` installe toutes les dépendances Python déclarées dans `pyproject.toml` (à la racine du projet) et crée l'environnement virtuel `.venv`.

**Frontend** (React/Tauri) :

```bash
cd src/frontend
npm install
cd ../..
```

> `npm install` installe les dépendances Node.js (React, TailwindCSS, Tauri, Framer Motion, etc.).

---

## 3. Configuration initiale

### Assistant de configuration

Au premier lancement de THERESE, un **assistant de configuration en 6 étapes** vous guide automatiquement :

1. **Bienvenue** - Présentation de THERESE
2. **Profil** - Votre nom, entreprise, rôle (optionnel : import depuis un fichier CLAUDE.md)
3. **LLM** - Choix du fournisseur IA et saisie de la clé API
4. **Sécurité** - Avertissements sur les connexions cloud (acknowledgement requis)
5. **Dossier de travail** - Sélection du répertoire par défaut pour vos fichiers
6. **Terminé** - Récapitulatif de la configuration

### Clé API LLM (obligatoire)

Vous devez disposer d'au moins une clé API pour un fournisseur LLM. **Anthropic est recommandé**.

| Fournisseur | Où obtenir la clé | Préfixe de la clé |
|-------------|-------------------|-------------------|
| **Anthropic** (recommandé) | [console.anthropic.com](https://console.anthropic.com) | `sk-ant-` |
| OpenAI | [platform.openai.com](https://platform.openai.com) | `sk-` |
| Google Gemini | [aistudio.google.com](https://aistudio.google.com) | `AIza` |
| Mistral | [console.mistral.ai](https://console.mistral.ai) | - |
| Grok (xAI) | [console.x.ai](https://console.x.ai) | `xai-` |
| Ollama (local) | [ollama.com](https://ollama.com) | Aucune clé requise |

### Clés optionnelles

| Fonctionnalité | Fournisseur | Où obtenir la clé |
|----------------|-------------|-------------------|
| Transcription vocale | Groq | [console.groq.com](https://console.groq.com) (clé préfixée `gsk_`) |
| Génération d'images | OpenAI (GPT Image 1.5) | [platform.openai.com](https://platform.openai.com) |
| Génération d'images | Google (Nano Banana Pro) | [aistudio.google.com](https://aistudio.google.com) |

> Les clés optionnelles peuvent être ajoutées plus tard depuis **Settings > LLM**.

---

## 4. Lancement

THERESE nécessite **3 processus** lancés simultanément dans des terminaux séparés.

### Terminal 1 - Qdrant (base vectorielle)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

> Qdrant stocke les embeddings pour la mémoire sémantique (contacts, projets, fichiers). Il doit tourner en permanence pendant l'utilisation de THERESE.

### Terminal 2 - Backend (API FastAPI)

```bash
cd src/backend
uv run uvicorn app.main:app --reload --port 8000
```

> Le backend démarre sur `http://127.0.0.1:8000`. Le flag `--reload` active le rechargement automatique en cas de modification du code.

### Terminal 3 - Frontend (application Tauri)

```bash
cd src/frontend
npm run tauri dev
```

> L'application de bureau THERESE s'ouvre automatiquement. Le frontend Vite tourne sur `http://localhost:1420` et Tauri encapsule l'interface dans une fenêtre native.

### Mode web uniquement (sans Tauri)

Si vous ne souhaitez pas compiler le wrapper Rust/Tauri, vous pouvez lancer le frontend en mode web :

```bash
cd src/frontend
npm run dev
```

> L'interface est alors accessible dans votre navigateur à l'adresse `http://localhost:5173`. Certaines fonctionnalités natives (fenêtres indépendantes, drag & drop fichiers Tauri, File Browser) ne seront pas disponibles dans ce mode.

### Raccourci Makefile

Depuis la racine du projet, la commande suivante lance le backend et Tauri simultanément (nécessite que Qdrant soit déjà démarré) :

```bash
make dev
```

Autres commandes utiles :

| Commande | Description |
|----------|-------------|
| `make dev-backend` | Lance le backend seul |
| `make dev-frontend` | Lance le frontend Vite seul (sans Tauri) |
| `make tauri` | Lance Tauri seul (frontend + wrapper natif) |
| `make help` | Affiche toutes les commandes disponibles |

---

## 5. Build de l'application

Pour générer l'application macOS distribuable :

```bash
make build
```

Ou manuellement :

```bash
cd src/frontend
npm run tauri build
```

Le bundle généré se trouve dans :

```
src/frontend/src-tauri/target/release/bundle/
```

Vous y trouverez :
- Un fichier `.app` (application macOS)
- Un fichier `.dmg` (image disque pour distribution)

> **Note** : le build de production nécessite Rust et peut prendre plusieurs minutes lors de la première compilation. L'application n'est pas encore signée (pas de certificat Apple Developer), macOS affichera donc un avertissement de sécurité au premier lancement.

---

## 5b. Build Windows

Pour générer l'application Windows distribuable :

```bash
make build
```

Le bundle généré se trouve dans :

```
src/frontend/src-tauri/target/release/bundle/
```

Vous y trouverez :
- Un fichier `.exe` (installeur Windows)
- Un fichier `.msi` (installeur MSI pour déploiement)

> **Note** : le code signing Windows n'est pas encore disponible. Au premier lancement, Windows SmartScreen affichera un avertissement "Application non reconnue". Cliquez sur **Informations complémentaires** puis **Exécuter quand même** pour continuer.

---

## 6. Dépannage

### Port 8000 déjà utilisé

Si le backend refuse de démarrer avec une erreur de type "Address already in use" :

```bash
# Identifier le processus qui utilise le port 8000
lsof -i :8000

# Arrêter le processus (remplacer PID par le numéro affiché)
kill PID
```

### Port 8000 déjà utilisé (Windows)

Si le backend refuse de démarrer sur Windows avec une erreur "Address already in use" :

```bash
# Identifier le processus qui utilise le port 8000
netstat -ano | findstr :8000

# Arrêter le processus (remplacer XXXX par le PID affiché)
taskkill /PID XXXX /F
```

### Antivirus faux positif

Si Windows Defender ou un autre antivirus bloque THÉRÈSE :

1. Ouvrez **Windows Defender** > **Protection contre les virus et menaces** > **Paramètres**
2. Dans **Exclusions**, ajoutez le dossier du projet (ex. `C:\Users\...\Synoptia-THERESE`)
3. Relancez l'application

### Qdrant non accessible

Si THERESE signale que Qdrant n'est pas joignable :

1. Vérifiez que Docker est lancé :
   ```bash
   docker ps
   ```
2. Si aucun conteneur Qdrant n'apparaît, relancez-le :
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```
3. Vérifiez que le port 6333 est accessible :
   ```bash
   curl http://localhost:6333/healthz
   ```

> THERESE fonctionne en **mode dégradé** si Qdrant est indisponible : le chat reste utilisable, mais la mémoire sémantique (recherche de contacts, projets, fichiers) est désactivée.

### Erreur "No API key"

Si THERESE affiche une erreur liée à la clé API :

1. Ouvrez **Settings** (roue dentée en haut à droite, ou `Cmd + ,` / `Ctrl + ,`)
2. Allez dans l'onglet **LLM**
3. Sélectionnez votre fournisseur et saisissez votre clé API
4. Vérifiez que le préfixe de la clé est correct (voir tableau section 3)

### Le frontend ne se connecte pas au backend

1. Vérifiez que le backend tourne bien sur le port 8000 :
   ```bash
   curl http://127.0.0.1:8000/api/health
   ```
2. Si la réponse est `{"status": "ok"}`, le backend fonctionne. Le problème vient peut-être d'un blocage CORS ou d'un pare-feu local.

### Erreur de compilation Tauri / Rust

Si `npm run tauri dev` échoue :

1. Vérifiez que Rust est à jour :
   ```bash
   rustup update
   ```
2. Nettoyez le cache de build :
   ```bash
   make clean
   ```
3. Relancez la compilation.

### Réinitialiser la configuration initiale

Pour relancer l'assistant de configuration (utile pour les tests) :

```bash
make reset-onboarding
```

### Réinitialiser complètement THERESE

Pour supprimer toutes les données locales et repartir de zéro :

```bash
# Supprimer les données utilisateur
mv ~/.therese ~/.Trash/

# Réinstaller les dépendances
make clean-all
make install
```

---

## Raccourcis clavier utiles

| macOS | Windows | Action |
|-------|---------|--------|
| `Cmd + B` | `Ctrl + B` | Ouvrir/fermer la sidebar des conversations |
| `Cmd + M` | `Ctrl + M` | Ouvrir/fermer l'espace de travail (mémoire) |
| `Cmd + K` | `Ctrl + K` | Palette de commandes |
| `Cmd + D` | `Ctrl + D` | Board de décision stratégique |
| `Cmd + N` | `Ctrl + N` | Nouvelle conversation |
| `Cmd + ,` | `Ctrl + ,` | Paramètres |

---

## Besoin d'aide ?

- **Documentation technique** : voir les autres fichiers dans le dossier `docs/`
- **Rapport de bug** : ouvrir une issue sur le dépôt GitHub
- **Contact** : ludo@synoptia.fr
