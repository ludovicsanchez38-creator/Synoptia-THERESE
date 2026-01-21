# Story E1-02 : Configurer le backend Python FastAPI

## Description

En tant que **développeur**,
Je veux **avoir un backend Python FastAPI fonctionnel**,
Afin de **pouvoir créer les APIs pour THÉRÈSE**.

## Contexte technique

- **Composants impactés** : Backend Python
- **Dépendances** : Aucune
- **Fichiers concernés** :
  - `src/backend/` (structure complète)
  - `pyproject.toml` (màj)
  - `Makefile` (màj)

## Critères d'acceptation

- [ ] Structure backend créée avec UV
- [ ] FastAPI installé et configuré
- [ ] Endpoint `/health` retourne `{"status": "ok"}`
- [ ] Uvicorn lance le serveur en mode dev
- [ ] Hot reload fonctionne
- [ ] Ruff configuré pour linting
- [ ] Pytest configuré pour tests

## Notes techniques

### Initialisation UV

```bash
cd src/backend
uv init --name therese-backend
uv add fastapi uvicorn[standard]
uv add --dev ruff pytest pytest-asyncio httpx
```

### Structure backend

```
src/backend/
├── therese/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── config.py         # Settings (pydantic-settings)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py
│   ├── services/
│   │   └── __init__.py
│   └── models/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_health.py
├── pyproject.toml
└── README.md
```

### Code minimal

```python
# therese/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="THÉRÈSE Backend",
    version="0.1.0",
    description="Backend API pour THÉRÈSE v2"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

### Configuration pyproject.toml

```toml
[project]
name = "therese-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Definition of Done

- [ ] `uv run uvicorn therese.main:app --reload` fonctionne
- [ ] `/health` retourne 200
- [ ] `uv run pytest` passe
- [ ] `uv run ruff check .` sans erreur

---

*Sprint : 1*
*Assigné : Agent Dev*
