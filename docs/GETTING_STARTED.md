# THÉRÈSE v2 - Guide d'installation (développeurs)

> Guide pour installer THÉRÈSE v2 depuis les sources. Si tu es testeur alpha, télécharge plutôt le .dmg, le .exe ou le .deb depuis les [GitHub Releases](https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/releases).

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

### Matériel recommandé

- **RAM** : 8 Go minimum (16 Go recommandé avec modèles Ollama locaux)
- **Stockage** : 2 Go minimum pour l'application + données
- **SSD recommandé** : THÉRÈSE utilise des bases vectorielles (Qdrant) et SQLite avec des écritures fréquentes (embeddings, recherche sémantique, index). Sur un usage intensif avec IA locale, privilégier un SSD avec un bon indice d'endurance (TBW/DWPD) pour éviter l'usure prématurée. Les SSD grand public (DWPD < 0.3) conviennent pour un usage normal, les SSD datacenter/pro (DWPD >= 1) sont préférables pour un usage serveur 24/7.

### Outils à installer

#### macOS

| Outil | Version minimale | Commande d'installation |
|-------|-----------------|------------------------|
| Python | 3.11+ | `brew install python@3.13` |
| Node.js | 20+ | `brew install node` |
| UV | dernière version | `brew install uv` (ou `pip install uv`) |
| Rust | stable | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |

#### Windows

| Outil | Version minimale | Commande d'installation |
|-------|-----------------|------------------------|
| Python | 3.11+ | `winget install Python.Python.3.13` |
| Node.js | 20+ | `winget install OpenJS.NodeJS.LTS` |
| UV | dernière version | `pip install uv` (ou `irm https://astral.sh/uv/install.ps1 \| iex`) |
| Rust | stable | [rustup-init.exe](https://rustup.rs) (+ Visual Studio Build Tools C++) |

### Vérification rapide

```bash
python3 --version    # Python 3.11+  (Windows : python --version)
node --version       # v20+
uv --version         # uv 0.x+
rustc --version      # rustc 1.x+
```

### Mémoire vectorielle embarquée

Le backend initialise Qdrant en mode embarqué. L'index est stocké dans `~/.therese/qdrant` par défaut.

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

Au premier lancement de THÉRÈSE, un **assistant de configuration en 6 étapes** vous guide automatiquement :

1. **Bienvenue** - Présentation de THÉRÈSE
2. **Profil** - Votre nom, entreprise, rôle (optionnel : import depuis un fichier CLAUDE.md)
3. **Service d’IA** : choix du fournisseur IA et saisie de la clé API
4. **Sécurité** - Avertissements sur les connexions cloud (confirmation explicite requise si un service cloud est activé)
5. **Dossier** : sélection du répertoire par défaut pour vos fichiers
6. **Terminé** - Récapitulatif de la configuration

### Clé API LLM (sauf Ollama en local)

Une clé API est nécessaire pour un fournisseur distant ; Ollama en local n’en demande pas. **Anthropic est recommandé**.

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

> Les clés optionnelles peuvent être ajoutées plus tard depuis **Paramètres > Services et connecteurs**.

---

## 4. Lancement

THÉRÈSE se lance avec **2 processus**, dans deux terminaux ouverts à la racine du dépôt. Le backend initialise lui-même Qdrant en mode embarqué.

Le démarrage complet depuis les sources n’a pas été essayé sur les systèmes visés dans cette préparation. Les commandes de cette section restent à vérifier dans un profil de développement isolé.

### Terminal 1 - Backend (API FastAPI)

```bash
cd src/backend
uv run uvicorn app.main:app --reload --port 17293
```

> Le backend démarre sur `http://127.0.0.1:17293`. Le flag `--reload` active le rechargement automatique en cas de modification du code.

### Terminal 2 - Frontend (application Tauri)

```bash
cd src/frontend
npm run tauri dev
```

> L'application de bureau THÉRÈSE s'ouvre automatiquement. Le frontend Vite tourne sur `http://localhost:1420` et Tauri encapsule l'interface dans une fenêtre native.

### Mode navigateur (sans Tauri)

Dans la version 0.83, le lancement du frontend Vite seul ne permet pas d’utiliser THÉRÈSE dans un navigateur ordinaire. Sans le jeton privé de session, l’amorçage échoue et l’interface affiche **Authentification impossible**.

Utilisez le lancement de l’application Tauri décrit ci-dessus, qui récupère le jeton par son canal privé. Le démarrage complet depuis les sources n’a pas été essayé dans cette préparation.

### Raccourci Makefile

Depuis la racine du projet, la commande suivante lance le backend et Tauri simultanément. Le backend initialise Qdrant en mode embarqué :

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

La construction complète n’a pas été exécutée dans cette préparation, sur macOS comme sur Windows. Les commandes existantes ci-dessous correspondent aux cibles du Makefile ; leur résultat reste à vérifier sur le système visé avant distribution.

Pour générer l'application macOS distribuable :

```bash
make build-release
```

Le Makefile fait précéder la construction Tauri par celle du backend embarqué avec `build-sidecar`. Une construction manuelle doit respecter cet ordre : `npm run tauri build` seul ne construit pas le backend. La construction manuelle n’a pas été essayée ; aucune recette manuelle n’est proposée ici.

Le bundle généré se trouve dans :

```
src/frontend/src-tauri/target/release/bundle/
```

Vous y trouverez :
- Un fichier `.app` (application macOS)
- Un fichier `.dmg` (image disque pour distribution)

> **Note** : aucun paquet macOS n’a été construit ni vérifié dans cette préparation. Avant de traiter une alerte de sécurité à l’installation, faites vérifier l’origine du paquet et le motif de l’alerte. Conservez la protection du système active si le contrôle ne permet pas de conclure.

---

## 5b. Build Windows

Pour générer l'application Windows distribuable :

```bash
make build-release
```

Le bundle généré se trouve dans :

```
src/frontend/src-tauri/target/release/bundle/
```

Vous y trouverez :
- Un fichier `.exe` (installeur Windows)
- Un fichier `.msi` (installeur MSI pour déploiement)

> **Note** : aucun paquet Windows n’a été construit ni vérifié dans cette préparation. Si SmartScreen affiche une alerte, faites vérifier l’origine du paquet et le motif de l’alerte avant toute nouvelle tentative. Gardez la protection active et demandez de l’aide si le contrôle ne permet pas de conclure.

---

## 6. Dépannage

### Port 17293 déjà utilisé

Si le backend refuse de démarrer avec une erreur de type "Address already in use" :

```bash
# Identifier le processus qui utilise le port 17293
lsof -i :17293

# Arrêter le processus (remplacer PID par le numéro affiché)
kill PID
```

### Port 17293 déjà utilisé (Windows)

Si le backend refuse de démarrer sur Windows avec une erreur "Address already in use" :

```bash
# Identifier le processus qui utilise le port 17293
netstat -ano | findstr :17293

# Arrêter le processus (remplacer XXXX par le PID affiché)
taskkill /PID XXXX /F
```

### Blocage par un antivirus

Si Windows Defender ou un autre antivirus bloque THÉRÈSE, conservez l’alerte et laissez la protection active. N’ajoutez pas d’exclusion du dossier du projet.

Avant une nouvelle tentative, faites vérifier l’origine du paquet et le motif du blocage. Pour demander de l’aide, indiquez le nom de la détection et la version de THÉRÈSE concernée, sans donnée personnelle ni secret. Aucune procédure de déblocage n’a été essayée sur Windows dans cette préparation.

### Qdrant embarqué indisponible

1. Consultez `http://127.0.0.1:17293/health`. Si `services.qdrant` vaut `true`, Qdrant est disponible ; `false` signale une indisponibilité. Si `status` vaut `recovery`, le démarrage des données a échoué et la réponse ne contient pas `services` ; conservez les données et demandez de l'aide.
2. Vérifiez l'espace disque disponible et les droits d'écriture de votre compte sur le dossier de l'index, `~/.therese/qdrant` par défaut. Conservez les fichiers existants.
3. Fermez les autres instances de THÉRÈSE avant de relancer le backend. Si le problème persiste, conservez l'index et demandez de l'aide avec le message d'erreur expurgé de toute donnée personnelle ou secrète.

> THÉRÈSE fonctionne en **mode dégradé** si Qdrant est indisponible : le chat reste utilisable, mais la mémoire sémantique (recherche de contacts, projets, fichiers) est désactivée.

### Erreur "No API key"

Si THÉRÈSE affiche une erreur liée à la clé API :

1. Ouvrez **Paramètres** (roue dentée en haut à droite, ou `Cmd + ,` / `Ctrl + ,`)
2. Allez dans l'onglet **Service d'IA**
3. Sélectionnez votre fournisseur et saisissez votre clé API
4. Vérifiez que le préfixe de la clé est correct (voir tableau section 3)

### Le frontend ne se connecte pas au backend

1. Vérifiez que le backend tourne bien sur le port 17293 :
   ```bash
   curl http://127.0.0.1:17293/health
   ```
2. Si la réponse contient `"status": "healthy"` (ou `"degraded"` quand Qdrant ou la base manquent), le backend fonctionne. Le problème vient peut-être d'un blocage CORS ou d'un pare-feu local.
3. Si `status` vaut `recovery`, le démarrage des données a échoué. La réponse ne contient pas `services` et ne confirme pas que les données sont utilisables. Conservez le dossier de données et demandez de l’aide avant toute remise à zéro.

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

### Réinitialiser complètement THÉRÈSE

Pour repartir avec un dossier de données vide, conservez d'abord une sauvegarde vérifiée.

Les gestes de corbeille décrits ci-dessous n’ont pas été essayés sur les systèmes visés dans cette préparation. La restauration d’essai isolée n’a pas été réalisée ; cette absence d’essai maintient l’arrêt prévu à l’étape 3.

Avant l’étape 1, identifiez le dossier de données effectivement utilisé. Les chemins ci-dessous sont ceux du profil par défaut ; si le dossier a été personnalisé, utilisez le dossier identifié à leur place. Si vous ne pouvez pas confirmer son emplacement, arrêtez-vous. Si la base ou l’index sont stockés hors de ce dossier, demandez une procédure adaptée avant de poursuivre.

1. Dans **Paramètres > Sécurité et confidentialité**, section **Export et sauvegardes**, saisissez une phrase secrète d'au moins 12 caractères dans le champ prévu, puis cliquez sur **Créer une sauvegarde**. Conservez cette phrase dans votre gestionnaire de mots de passe. L'export JSON ne remplace pas cette sauvegarde complète.
2. Copiez l'archive `.tar.gz.enc` créée dans `~/.therese/backups` et son fichier de métadonnées `.json` dans un dossier privé situé hors de `~/.therese`. Sous Windows, le dossier par défaut est `%USERPROFILE%\.therese\backups`. Gardez cette copie hors des dépôts Git et des espaces partagés.
3. Dans les métadonnées de cette sauvegarde, vérifiez uniquement que `encrypted` vaut `true` et que la liste `included` contient `.encryption_key`. N'ouvrez pas le fichier de clé et n'en affichez jamais le contenu. Cet inventaire déclare les fichiers inclus ; il ne prouve pas qu'une restauration réussira. Avant de poursuivre, faites vérifier une restauration de la copie dans un profil d'essai isolé, sans toucher aux données actuelles. Si ce contrôle n'a pas pu être réalisé, conservez le profil actuel et demandez de l'aide.
4. Quittez complètement THÉRÈSE. En développement, arrêtez le frontend et le backend dans leurs terminaux avec `Ctrl + C`.
5. Déplacez le dossier de données à la corbeille avec le gestionnaire de fichiers de votre système :
   - **macOS** : dans le Finder, utilisez **Aller > Départ** pour ouvrir votre dossier personnel, affichez les fichiers cachés avec `Cmd + Maj + .`, puis placez `.therese` à la corbeille.
   - **Windows** : dans l'Explorateur, ouvrez `%USERPROFILE%`, affichez les éléments masqués si nécessaire, puis déplacez le dossier `.therese` dans la Corbeille. Si Windows propose une suppression définitive, annulez.
   - **Linux** : dans votre gestionnaire de fichiers, affichez les fichiers cachés de votre dossier personnel et déplacez `.therese` à la corbeille. Si ce déplacement n'est pas proposé, arrêtez-vous.
6. Relancez THÉRÈSE. Un nouveau dossier de données est créé. Gardez l'ancien dossier dans la corbeille et la sauvegarde privée tant que le nouveau profil n'a pas été vérifié.

Le déplacement du dossier ne retire pas la clé maîtresse éventuellement enregistrée dans le trousseau du système, notamment le Trousseau d'accès macOS ou le Gestionnaire d'informations d'identification Windows. La remise à zéro ne garantit donc pas le renouvellement de cette clé. Conservez les entrées du trousseau pour préserver les possibilités de restauration.

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
