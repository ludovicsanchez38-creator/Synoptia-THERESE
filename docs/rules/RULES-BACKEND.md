# Règles Backend - THÉRÈSE V2

> Document de référence pour toutes les conventions, patterns et règles du backend THÉRÈSE V2.
> Dernière mise à jour : 2026-02-03

---

## 1. Stack technique

| Composant | Technologie | Version / Détails |
|-----------|-------------|-------------------|
| Langage | Python | 3.11+ avec type hints obligatoires |
| Framework | FastAPI | Async-first, lifespan events |
| ORM / Modèles | SQLModel | Pydantic v2 + SQLAlchemy |
| Base de données | SQLite | Via aiosqlite (async) |
| Gestionnaire de paquets | UV | Remplace pip/poetry |
| Vecteurs | Qdrant | Embeddings vectoriels |
| Embeddings | sentence-transformers | nomic-embed-text-v1.5, 768 dimensions |
| Migrations | Alembic | Versionnement schéma DB |
| Tests | pytest + pytest-asyncio | 118+ tests minimum |
| Linter | Ruff | Check + fix automatique |

---

## 2. Architecture des fichiers

```
src/backend/app/
├── main.py          # Point d'entrée FastAPI, middleware, lifespan
├── config.py        # Configuration Pydantic-settings
├── models/
│   ├── entities.py  # SQLModel (Contact, Project, Conversation, Message, etc.)
│   └── schemas.py   # Pydantic v2 (request/response schemas)
├── routers/         # 23 routers (chat, memory, files, config, skills, etc.)
├── services/        # 40+ services (llm, providers/, mcp, encryption, etc.)
└── utils/           # Utilitaires
```

### Principes d'organisation

- **routers/** : Uniquement la couche HTTP (validation, sérialisation, codes de réponse). Aucune logique métier.
- **services/** : Toute la logique métier. Un service par domaine fonctionnel.
- **models/entities.py** : Modèles SQLModel avec `table=True`. Représentent le schéma de la base.
- **models/schemas.py** : Schemas Pydantic v2 pour les requêtes et réponses API.
- **config.py** : Configuration centralisée via Pydantic-settings (variables d'environnement).
- **main.py** : Bootstrap de l'application, middleware, handlers d'erreur, lifespan.

---

## 3. Conventions de code

### 3.1 Règles générales

- **Tous les endpoints sont async** : toujours `async def`, jamais `def` pour un endpoint.
- **Type hints obligatoires** sur tous les paramètres et tous les retours de fonction.
- **Imports absolus** depuis `app.*` (jamais d'imports relatifs avec des points).
- **Nommage** : `snake_case` partout (fonctions, variables, fichiers, colonnes DB).
- **Docstrings en français** : chaque fonction publique doit avoir une docstring.
- **Pas de `print()`** : utiliser le module `logging` avec le bon niveau (debug, info, warning, error).
- **Pas de tirets longs** (-) : utiliser le tiret court (-) ou des parenthèses.

### 3.2 Exemple de signature correcte

```python
async def get_conversation_messages(
    conversation_id: int,
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[MessageResponse]:
    """Récupère les messages d'une conversation avec pagination."""
    ...
```

### 3.3 Dependency injection

- Utiliser `FastAPI Depends()` pour injecter les dépendances (sessions DB, services, authentification).
- Les sessions DB sont fournies via `AsyncSession` injectée par un générateur async.

```python
@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[MessageResponse]:
    ...
```

### 3.4 Logging

```python
import logging

logger = logging.getLogger(__name__)

# Niveaux appropriés :
logger.debug("Détail technique pour le débogage")
logger.info("Événement normal du flux applicatif")
logger.warning("Situation anormale mais récupérable")
logger.error("Erreur nécessitant une attention", exc_info=True)
```

---

## 4. Patterns architecturaux

### 4.1 Singleton

Les services qui gèrent un état global ou une connexion unique utilisent le pattern Singleton.

- `QdrantService` : connexion unique au serveur Qdrant
- `MCPService` : orchestrateur des outils MCP
- `SkillsRegistry` : registre centralisé des skills

### 4.2 Façade

Le service LLM expose une interface unifiée qui abstrait 6 providers différents (Anthropic, OpenAI, Google, Mistral, etc.). Le code appelant n'a pas besoin de connaître le provider sous-jacent.

### 4.3 Factory

Les factories créent l'implémentation appropriée selon la configuration :

- `EmailProviderFactory` : instancie le bon provider email (Gmail, IMAP, etc.)
- `CalendarProviderFactory` : instancie le bon provider calendrier

### 4.4 Repository

L'accès aux données passe par des sessions SQLModel. Les requêtes sont centralisées dans les services, jamais directement dans les routers.

### 4.5 Stratégie

Les providers LLM implémentent tous la même interface (`BaseProvider` ABC) et sont interchangeables à l'exécution.

```python
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """Classe abstraite pour tous les providers LLM."""

    @abstractmethod
    async def stream_response(self, messages: list, **kwargs) -> AsyncIterator[str]:
        """Génère une réponse en streaming."""
        ...

    @abstractmethod
    async def get_models(self) -> list[ModelInfo]:
        """Retourne la liste des modèles disponibles."""
        ...
```

---

## 5. Conventions de routage

### 5.1 Structure des URLs

- **Préfixe** : `/api/{domain}` (ex: `/api/conversations`, `/api/contacts`, `/api/memory`)
- **CRUD standard** :

| Opération | Méthode | Route | Code retour |
|-----------|---------|-------|-------------|
| Lister | GET | `/api/{domain}/` | 200 OK |
| Créer | POST | `/api/{domain}/` | 201 Created |
| Lire | GET | `/api/{domain}/{id}` | 200 OK |
| Modifier | PATCH | `/api/{domain}/{id}` | 200 OK |
| Supprimer | DELETE | `/api/{domain}/{id}` | 204 No Content |

- **Streaming** : POST avec SSE (Server-Sent Events) pour les réponses LLM.

### 5.2 Codes HTTP standardisés

| Code | Usage |
|------|-------|
| 200 OK | Requête réussie (lecture, mise à jour) |
| 201 Created | Ressource créée avec succès |
| 204 No Content | Suppression réussie |
| 400 Bad Request | Données invalides côté client |
| 404 Not Found | Ressource inexistante |
| 429 Too Many Requests | Rate limit atteint |
| 500 Internal Server Error | Erreur serveur inattendue |

### 5.3 Réponses

Toutes les réponses passent par des schemas Pydantic v2 définis dans `models/schemas.py`. Pas de `dict` brut en retour.

---

## 6. Modèles de données

### 6.1 Entités SQLModel

Les entités héritent de `SQLModel` avec `table=True` :

```python
class Conversation(SQLModel, table=True):
    """Table des conversations."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    project_id: int | None = Field(default=None, foreign_key="project.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    metadata_json: str | None = None  # JSON sérialisé
```

### 6.2 Schemas Pydantic v2

Les schemas request/response sont séparés des entités :

```python
class ConversationCreate(SQLModel):
    """Schema de création d'une conversation."""

    title: str
    project_id: int | None = None

class ConversationResponse(SQLModel):
    """Schema de réponse pour une conversation."""

    id: int
    title: str
    project_id: int | None
    created_at: datetime
    message_count: int = 0
```

### 6.3 Conventions de champs

- **Champs optionnels** : `Optional[type] = None` ou `type | None = None`
- **Champs JSON** : `list[str]` ou `dict` stockés en JSON dans SQLite via sérialisation manuelle
- **Timestamps** : `datetime` avec `default_factory` pour la création
- **Relations** : Foreign keys explicites, joins dans les requêtes (pas de lazy loading)
- **IDs** : `int | None = Field(default=None, primary_key=True)` (auto-incrémenté)

---

## 7. Providers LLM

### 7.1 Interface commune

Tous les providers héritent de `BaseProvider` (ABC) et implémentent obligatoirement :

- `stream_response()` : génération en streaming
- `get_models()` : liste des modèles disponibles

### 7.2 Providers supportés

| Provider | Modèle principal | Format tool calling |
|----------|-----------------|---------------------|
| Anthropic | claude-opus-4-5-20251101 | Format Anthropic natif |
| OpenAI | gpt-5.2 | Format OpenAI natif |
| Google | gemini-3-pro-preview | Format OpenAI compatible |
| Mistral | mistral-large-latest | Format OpenAI compatible |
| Ollama | Local | Format OpenAI compatible |
| LM Studio | Local | Format OpenAI compatible |

### 7.3 Règles

- Les clés API sont chiffrées via le service d'encryption (jamais en clair en DB).
- Un provider de fallback est configurable si le provider principal échoue.
- Le tool calling suit le format natif du provider (Anthropic ou OpenAI).

---

## 8. Sécurité

### Référentiel des règles de sécurité

| Code | Règle | Détails |
|------|-------|---------|
| SEC-001 | Validation des chemins de fichiers | `validate_file_path()` - aucun path traversal autorisé |
| SEC-003 | Restriction des répertoires | Accès uniquement aux dossiers autorisés |
| SEC-010 | Token de session | Header `X-Therese-Token` obligatoire |
| SEC-015 | Rate limiting | slowapi, 60 requêtes/minute par défaut |
| SEC-018 | CORS | Origines restreintes aux origines Tauri uniquement |
| SEC-023 | Headers de sécurité | Headers obligatoires sur toutes les réponses |
| SEC-025 | Comparaison de secrets | `secrets.compare_digest` contre les timing attacks |

### Chiffrement des clés API

- Algorithme : Fernet AES-128-CBC
- Clé de chiffrement stockée dans le Trousseau macOS (Keychain)
- Les clés API ne sont jamais stockées en clair dans la base de données

### Sandbox d'exécution de code

- Imports Python restreints (liste blanche)
- Timeout : 30 secondes maximum par exécution
- Isolation du processus

---

## 9. Tests

### 9.1 Framework et configuration

- **Framework** : pytest + pytest-asyncio
- **Minimum** : 118+ tests
- **Exécution** : `make test-backend`

### 9.2 Fixtures principales

```python
@pytest.fixture
async def db_session():
    """Session de base de données in-memory pour les tests."""
    ...

@pytest.fixture
async def async_client(db_session):
    """Client HTTP async pour tester les endpoints."""
    ...

@pytest.fixture
def client():
    """Client HTTP synchrone (cas simples)."""
    ...
```

### 9.3 Conventions

- **Nommage** : `test_{router_ou_service}_{feature}.py`
- **Indépendance** : chaque test est autonome, pas d'état partagé entre tests.
- **Mocks** : les appels LLM et services externes sont systématiquement mockés.
- **Assertions** : tester le code de retour HTTP ET le contenu de la réponse.

### 9.4 Exemple

```python
@pytest.mark.asyncio
async def test_create_conversation_returns_201(async_client: AsyncClient):
    """Vérifie qu'une conversation est créée avec le code 201."""
    response = await async_client.post(
        "/api/conversations/",
        json={"title": "Test conversation"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test conversation"
    assert "id" in data
```

---

## 10. Migrations (Alembic)

### Commandes

```bash
make db-revision msg="description de la migration"   # Créer une migration
make db-migrate                                       # Appliquer les migrations
```

### Règles

- **Jamais de modification manuelle** de la base de données (toujours via Alembic).
- **Toujours tester** la migration avant de commit (up ET down).
- **Messages descriptifs** en français pour chaque révision.
- Les migrations doivent être réversibles (`upgrade` et `downgrade`).

---

## 11. Gestion d'erreurs

### 11.1 Exception personnalisée

```python
class TheresError(Exception):
    """Exception de base pour THÉRÈSE."""

    def __init__(
        self,
        message: str,
        recoverable: bool = True,
        status_code: int = 500,
        context: dict | None = None,
    ):
        self.message = message
        self.recoverable = recoverable
        self.status_code = status_code
        self.context = context or {}
        super().__init__(message)
```

### 11.2 Règles

- Distinguer les erreurs **récupérables** (recoverable=True) des erreurs **fatales** (recoverable=False).
- Utiliser `HTTPException` avec les codes standardisés (cf. section 5.2).
- Le logging doit inclure le contexte de l'erreur (paramètres, état).
- Un error handler global dans `main.py` intercepte les exceptions non gérées.
- **Jamais de `try/except` vide** : toujours logger l'erreur au minimum.

```python
# Correct
try:
    result = await some_operation()
except SomeError as e:
    logger.error("Échec de l'opération: %s", e, exc_info=True)
    raise HTTPException(status_code=500, detail="Erreur interne")

# Interdit
try:
    result = await some_operation()
except Exception:
    pass  # JAMAIS - l'erreur est avalée silencieusement
```

---

## 12. Performance

### Référentiel des optimisations

| Code | Optimisation | Détails |
|------|-------------|---------|
| PERF-001 | Pool HTTP global | `AsyncClient` avec 20 keepalive, 100 connexions max |
| PERF-002 | Embeddings async | Via `asyncio.to_thread` pour ne pas bloquer l'event loop |
| PERF-003 | Sessions DB async | aiosqlite pour les I/O base de données |
| PERF-004 | Pas de N+1 queries | Utiliser `COUNT(*)` pour les listes, joins explicites |
| PERF-005 | Nettoyage mémoire | Callbacks de nettoyage sur les réponses streaming |

### Règles

- Ne jamais faire d'appel HTTP synchrone dans un handler async (bloque l'event loop).
- Utiliser `asyncio.to_thread()` pour les opérations CPU-bound (embeddings, parsing).
- Préférer les requêtes SQL agrégées aux boucles de requêtes unitaires.
- Fermer explicitement les ressources (sessions, clients HTTP) via les context managers.

---

## 13. Commandes make

```bash
make dev-backend      # Lancer le backend en mode développement (hot-reload)
make test-backend     # Exécuter les tests backend
make lint             # Ruff check + fix automatique
make db-migrate       # Appliquer les migrations Alembic
make db-revision      # Créer une nouvelle révision de migration
```

---

## 14. Anti-patterns à éviter

| Anti-pattern | Correction |
|-------------|------------|
| Logique métier dans les routers | Déléguer aux services dans `services/` |
| Requêtes synchrones | Tout est async (aiosqlite, httpx.AsyncClient) |
| Secrets en dur dans le code | Variables d'environnement + chiffrement Fernet |
| `rm` pour supprimer | `mv fichier ~/.Trash/` ou `trash fichier` |
| Tirets longs (-) | Tiret court (-) ou parenthèses |
| Suppression sans confirmation | Toujours demander confirmation avant suppression |
| `try/except` vide | Toujours logger l'erreur |
| `print()` pour le debug | Utiliser `logging` avec le bon niveau |
| `dict` brut en retour d'endpoint | Toujours un schema Pydantic v2 |
| Imports relatifs (`from .models`) | Imports absolus (`from app.models`) |
| Lazy loading SQLAlchemy | Joins explicites dans les requêtes |
| Modification manuelle de la DB | Toujours passer par Alembic |

---

## 15. Checklist avant commit

- [ ] Type hints sur tous les paramètres et retours
- [ ] Docstrings en français sur les fonctions publiques
- [ ] Pas de `print()` (remplacé par `logging`)
- [ ] Pas de secrets en dur
- [ ] Tests passants (`make test-backend`)
- [ ] Linter propre (`make lint`)
- [ ] Migration créée si le schéma a changé
- [ ] Pas de N+1 queries
- [ ] Gestion d'erreurs avec logging
- [ ] Schemas Pydantic pour les entrées/sorties
