# Guide de Contribution - THÉRÈSE V2

## Bienvenue

THÉRÈSE V2 est l'assistante souveraine des entrepreneurs français. Ce guide décrit les conventions et processus pour contribuer au projet.

## Prérequis

### Environnement requis

- **macOS** 10.15+ (Catalina ou supérieur) ou **Windows** 10+
- **Python** 3.11+ (via pyenv ou homebrew)
- **Node.js** 20+ (via nvm)
- **Rust** (pour Tauri, installé via rustup)
- **UV** (gestionnaire Python) : `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Git** configuré avec accès au repo

### Installation complète

```bash
# Cloner le projet
git clone https://github.com/ludovicsanchez38-creator/Synoptia-THERESE.git
cd Synoptia-THERESE

# Installation automatique
make install

# Ou manuellement :
# Backend
cd src/backend && uv sync && cd ../..

# Frontend
cd src/frontend && npm install && cd ../..

# E2E (optionnel)
make install-e2e
```

### Lancement en développement

```bash
# Tout lancer (backend + frontend + Tauri)
make dev

# Backend seul (hot-reload)
make dev-backend

# Frontend seul (Vite)
make dev-frontend
```

### Vérification de l'installation

```bash
# Tests backend
make test-backend

# Tests frontend
cd src/frontend && npm run test

# Lint
make lint
```

## Architecture du projet

```
THÉRÈSE V2/
├── src/
│   ├── backend/          # FastAPI Python (services, API, DB)
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── models/   # SQLModel + Pydantic schemas
│   │   │   ├── routers/  # 23 routers API
│   │   │   └── services/ # 40+ services métier
│   │   ├── tests/
│   │   └── alembic/      # Migrations DB
│   └── frontend/         # Tauri + React
│       ├── src/
│       │   ├── components/  # 40+ composants React
│       │   ├── stores/      # 6 stores Zustand
│       │   ├── hooks/       # 13 hooks personnalisés
│       │   ├── services/    # 14 modules API
│       │   └── lib/         # Utilitaires
│       └── src-tauri/       # Config Tauri (Rust)
├── docs/                 # Documentation
│   ├── rules/            # Règles par métier
│   ├── sessions/         # Logs de sessions
│   └── stories/          # User stories
├── tests/                # Tests backend
├── Makefile              # Commandes de développement
└── CLAUDE.md             # Contexte pour Claude Code
```

## Conventions de code

### Python (Backend)

| Convention | Règle |
|-----------|-------|
| Style | PEP 8 + Ruff |
| Types | Type hints obligatoires sur tous les paramètres et retours |
| Async | Tous les endpoints et services sont async |
| Nommage | snake_case partout |
| Imports | Absolus depuis `app.*` |
| Docs | Docstrings en français |
| Logging | Module logging (jamais print()) |
| Gestionnaire | UV (pas pip) |

**Exemple** :

```python
from app.models.entities import Contact
from app.services.qdrant import qdrant_service

async def create_contact(
    session: AsyncSession,
    data: ContactCreate,
) -> Contact:
    """Créer un nouveau contact et générer son embedding."""
    contact = Contact(**data.model_dump())
    session.add(contact)
    await session.commit()
    await qdrant_service.add_entity(contact)
    return contact
```

### TypeScript (Frontend)

| Convention | Règle |
|-----------|-------|
| Style | ESLint + Prettier |
| Composants | Fonctionnels uniquement (pas de classes) |
| State | Zustand (pas de prop drilling) |
| Styling | TailwindCSS (pas de CSS custom) |
| Nommage | PascalCase (composants), camelCase (fonctions/variables) |
| Types | Interfaces TypeScript pour toutes les props |

**Exemple** :

```typescript
interface ContactCardProps {
  contact: Contact;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function ContactCard({ contact, onEdit, onDelete }: ContactCardProps) {
  return (
    <motion.div
      variants={fadeInUp}
      className="bg-surface rounded-xl border border-border p-4 hover:border-accent_cyan/30"
    >
      {/* ... */}
    </motion.div>
  );
}
```

### Accents et langue

- **Tout le texte en français** avec accents corrects
- Commentaires, docstrings, messages de commit, documentation : en français
- "Generer" → "Générer", "Etape" → "Étape", "metier" → "métier"
- Pas de tirets longs (-) - uniquement tirets courts (-) ou parenthèses

## Workflow de développement

### 1. Créer une branche

```bash
git checkout -b feature/nom-de-la-feature
# ou
git checkout -b fix/description-du-bug
```

### 2. Développer avec les tests

- Écrire les tests AVANT ou PENDANT le développement
- Vérifier que les tests existants passent toujours
- Ajouter des tests pour toute nouvelle fonctionnalité

### 3. Vérifier la qualité

```bash
make lint          # Vérifier le style
make test          # Lancer tous les tests
make typecheck     # Vérifier les types TypeScript
```

### 4. Committer

```bash
git add fichiers_modifiés
git commit -m "feat: description courte en français"
```

**Types de commit** :

| Type | Usage |
|------|-------|
| feat | Nouvelle fonctionnalité |
| fix | Correction de bug |
| refactor | Refactoring sans changement fonctionnel |
| test | Ajout ou modification de tests |
| docs | Documentation |
| perf | Optimisation de performance |
| style | Style de code (pas de changement fonctionnel) |
| chore | Tâches de maintenance |

### 5. Push et Pull Request

```bash
git push origin feature/nom-de-la-feature
# Créer une PR sur GitHub
```

## Ajout d'un nouveau router API

1. Créer le fichier dans `src/backend/app/routers/`
2. Définir les schemas dans `src/backend/app/models/schemas.py`
3. Créer le(s) service(s) dans `src/backend/app/services/`
4. Enregistrer le router dans `src/backend/app/main.py`
5. Écrire les tests dans `tests/test_routers_xxx.py`
6. Documenter dans `docs/API.md`

## Ajout d'un nouveau composant React

1. Créer le fichier dans `src/frontend/src/components/`
2. Utiliser TailwindCSS pour le styling
3. Utiliser Framer Motion pour les animations
4. Connecter au store Zustand si nécessaire
5. Ajouter le module API dans `src/frontend/src/services/api/`
6. Écrire les tests dans le même dossier (*.test.tsx)

## Ajout d'un nouveau provider LLM

1. Créer le fichier dans `src/backend/app/services/providers/`
2. Hériter de `BaseProvider`
3. Implémenter `stream_response()` et `get_models()`
4. Enregistrer dans le registre `llm.py`
5. Ajouter le modèle frontend dans `api/config.ts`
6. Écrire les tests dans `tests/test_services_llm.py`
7. Documenter dans `docs/rules/RULES-LLM.md`

## Base de données

### Modifier le schéma

1. Modifier le modèle SQLModel dans `app/models/entities.py`
2. Créer une migration : `make db-revision msg="Description"`
3. Appliquer la migration : `make db-migrate`
4. Tester sur une base neuve
5. Jamais de modification directe de la DB

## Règles impératives

- **Jamais de rm** → `mv fichier ~/.Trash/`
- **Jamais de tirets longs** → tirets courts (-) ou parenthèses
- **Toujours les accents** en français
- **Toujours tester** avant de considérer un fix comme terminé
- **Toujours lire les logs** avant de spéculer sur un bug
- **Proposer un plan** avant toute implémentation non triviale
- **Pas de sur-ingénierie** - minimum viable, puis itérer

## Ressources

### Documentation

- `docs/rules/` - Règles par métier (backend, frontend, sécurité, LLM, tests, design, données, DevOps)
- `docs/architecture.md` - Architecture technique détaillée
- `docs/prd-therese.md` - Product Requirements Document
- `docs/USER_STORIES.md` - 100 user stories
- `docs/API.md` - Documentation API complète

### Benchmarks

- `docs/benchmark-cowork.md` - Analyse vs Cowork
- `docs/benchmark-memoire.md` - État de l'art mémoire IA
- `docs/benchmark-ux.md` - Patterns UX et design system

## Contact

- **Porteur du projet** : Ludovic "Ludo" Sanchez
- **Email** : ludo@synoptia.fr
- **Site** : synoptia.fr
- **Marque** : Synoptia
