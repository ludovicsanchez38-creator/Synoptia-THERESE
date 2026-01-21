# THÉRÈSE v2

> L'assistante souveraine des entrepreneurs français

**"Ta mémoire, tes données, ton business."**

## Vision

THÉRÈSE = Cowork (Anthropic) + mémoire persistante + meilleure UX/UI + souveraineté des données.

### Différenciateurs

1. **Mémoire persistante** - THÉRÈSE se souvient de tes clients, projets, préférences
2. **UX/UI premium** - Dark mode élégant, pensé pour l'efficacité
3. **Souveraineté** - 100% local, tes données restent sur ta machine
4. **Made in France** - Pensé pour les solopreneurs français

## Statut

🚧 En développement (Phase: Discovery)

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Frontend | Tauri 2.0 + React + TailwindCSS |
| Backend | Python (FastAPI) + UV |
| Database | SQLite (données) + Qdrant (embeddings) |
| LLM | Claude API (v1), puis Mistral/local (v2) |

## Identité visuelle

```yaml
palette:
  background: "#0B1226"
  surface: "#131B35"
  text_primary: "#E6EDF7"
  text_muted: "#B6C7DA"
  accent_cyan: "#22D3EE"
  accent_magenta: "#E11D8D"

style:
  - Dark premium
  - Glassmorphism subtil
  - Glow néon discret
  - Coins arrondis (8-12px)
```

## Structure du projet

```
therese-v2/
├── docs/                   # Documentation projet
│   ├── benchmark-*.md      # Analyses comparatives
│   ├── prd-therese.md      # Product Requirements
│   ├── architecture.md     # Specs techniques
│   ├── stories/            # User stories
│   ├── epics/              # Epics BMAD
│   └── planning/           # Sprint planning
├── src/
│   ├── frontend/           # Tauri + React
│   ├── backend/            # Python FastAPI
│   ├── memory/             # Module mémoire (SQLite + Qdrant)
│   └── llm/                # Abstraction LLM
├── tests/
├── assets/
│   └── design/             # Maquettes, assets visuels
└── .bmad-core/             # Config BMAD
```

## Développement

### Prérequis

- Node.js 20+
- Python 3.11+ (via UV)
- Rust (pour Tauri)

### Installation

```bash
# Backend
cd src/backend
uv sync

# Frontend
cd src/frontend
npm install
```

### Lancer le dev

```bash
make dev
```

### Commandes disponibles

```bash
make install   # Installer les dépendances
make dev       # Lancer en mode développement
make test      # Lancer les tests
make lint      # Vérifier le code
make clean     # Nettoyer les fichiers générés
```

## Méthodologie

Projet développé avec **BMAD Method** (Breakthrough Method for Agile AI-Driven Development).

### Agents BMAD utilisés

| Agent | Rôle |
|-------|------|
| Analyst | Benchmarks et recherche |
| UX Designer | Design et wireframes |
| PM | Product Requirements |
| Architect | Architecture technique |
| Scrum Master | User stories |
| Dev | Implémentation |

## Historique

- **THÉRÈSE CLI v1** : Prototype Mistral Large, post viral LinkedIn (140k impressions, 1050 likes)
- **THÉRÈSE v2** : Version desktop complète (projet actuel)

## Auteur

**Ludo Sanchez** - [Synoptïa](https://synoptia.fr)

*"Humain d'abord - IA en soutien"*

---

*Projet initié le 21 janvier 2026*
