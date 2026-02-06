<p align="center">
  <img src="assets/screenshots/therese-hero.png" alt="THÉRÈSE - Assistant IA desktop" width="720" />
</p>

<h1 align="center">THÉRÈSE</h1>

<p align="center">
  <strong>L'assistante IA desktop pour les entrepreneurs, TPE, mairies et associations françaises.</strong><br />
  <em>"Humain d'abord - IA en soutien"</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/licence-MIT-blue.svg" alt="MIT License" /></a>
  <a href="https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/actions"><img src="https://img.shields.io/github/actions/workflow/status/ludovicsanchez38-creator/Synoptia-THERESE/ci.yml?branch=main&label=CI" alt="CI" /></a>
  <img src="https://img.shields.io/badge/version-0.1.0--alpha-orange" alt="Version" />
</p>

<p align="center">
  <strong>Open source et gratuit - pour toujours.</strong>
</p>

---

## ✨ Fonctionnalités

- 🤖 **Chat multi-LLM** - Claude, GPT, Gemini, Mistral, Grok, Ollama (local)
- 🧠 **Mémoire persistante** - Contacts, projets, fichiers : tout reste sur ta machine
- 📧 **Email et Calendrier** - IMAP/Gmail, CalDAV/Google Calendar intégrés
- 📊 **CRM et Facturation** - Local ou sync Google Sheets, PDF conforme (mentions légales FR)
- 🎯 **Board de Décision IA** - 5 conseillers virtuels pour t'aider à trancher
- 📝 **Skills Office** - Génération Word, Excel, PowerPoint en un prompt
- 🔌 **Outils MCP** - 19 presets pour connecter services externes
- 🔒 **Local-first** - 100+ endpoints API, données chiffrées, rien dans le cloud

## 📥 Télécharger (alpha fermée)

> THÉRÈSE est en **alpha fermée** avec 20 testeurs (6 semaines).

Les installeurs sont disponibles dans les [GitHub Releases](https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/releases).

| Plateforme | Fichier |
|------------|---------|
| macOS (Apple Silicon) | `THERESE_x.x.x_aarch64.dmg` |
| Windows (x64) | `THERESE_x.x.x_x64-setup.exe` |

> **macOS** : Clic droit sur l'app > Ouvrir > Confirmer (Gatekeeper, app non signée pour l'instant).
> **Windows** : SmartScreen peut afficher un avertissement, clique sur "Informations complémentaires" > "Exécuter quand même".

Tu as besoin d'une **clé API LLM** pour utiliser THÉRÈSE (Anthropic recommandé : [console.anthropic.com](https://console.anthropic.com)).

## 🚀 Premiers pas

1. **Télécharge et installe** la dernière build depuis les [Releases](https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/releases)
2. **Suis le wizard d'onboarding** qui te guide étape par étape
3. **Commence à discuter** avec THÉRÈSE !

👉 Guide complet pour les testeurs : [docs/USER_GUIDE_ALPHA.md](docs/USER_GUIDE_ALPHA.md)

## 🐛 Signaler un bug

- **Discord** : mentionne `@Thérèse bug : [description]` dans `#bugs` ([serveur therese-alpha](https://discord.gg/therese-alpha))
- **GitHub** : ouvre une [issue](https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/issues/new?template=bug_report.md)
- **Email** : ludo@synoptia.fr avec l'objet `[THÉRÈSE Alpha] Bug`

## 🛠 Pour les développeurs

### Prérequis

- Python 3.11+ (via [UV](https://docs.astral.sh/uv/))
- Node.js 22+
- Rust stable (pour [Tauri 2.0](https://v2.tauri.app/))

### Installation et lancement

```bash
make install    # Installer toutes les dépendances
make dev        # Lancer backend + Tauri en mode dev
```

### Commandes utiles

```bash
make dev              # Backend + Tauri simultanés
make dev-backend      # Backend seul (uvicorn :8000)
make test             # Tous les tests
make lint             # Vérifier le code (ruff + eslint)
make build-release    # Build complète de production
make help             # Toutes les commandes disponibles
```

👉 Installation détaillée : [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
👉 Contribuer : [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 📁 Structure du projet

```
Synoptia-THERESE/
├── src/
│   ├── frontend/           # React + Tauri 2.0 + TailwindCSS
│   │   ├── src/            # Composants, stores, hooks, services
│   │   └── src-tauri/      # Configuration Rust (Tauri)
│   └── backend/            # Python FastAPI
│       └── app/            # Routers, services, models, providers
├── tests/                  # pytest + Vitest + Playwright
├── docs/                   # Documentation complète
├── scripts/                # Scripts de build et utilitaires
└── .github/workflows/      # CI/CD
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Guide Alpha](docs/USER_GUIDE_ALPHA.md) | Guide complet pour les testeurs |
| [Installation](docs/GETTING_STARTED.md) | Installation depuis les sources |
| [Contribuer](docs/CONTRIBUTING.md) | Guide de contribution |
| [API](docs/API.md) | Documentation de l'API backend |
| [Architecture](docs/architecture.md) | Architecture technique détaillée |
| [Changelog](docs/CHANGELOG.md) | Historique des versions |

## 🔐 Sécurité

Voir [SECURITY.md](SECURITY.md) pour la politique de sécurité et le signalement de vulnérabilités.

## 📄 Licence

[MIT](LICENSE) - Synoptïa (Ludovic Sanchez)

## 📬 Contact

**Ludo Sanchez** - [Synoptïa](https://synoptia.fr) - ludo@synoptia.fr

*"Humain d'abord - IA en soutien"*
