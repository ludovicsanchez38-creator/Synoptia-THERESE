# Règles de Tests - THÉRÈSE V2

## Philosophie
Chaque fonctionnalité doit être testée avant d'être considérée comme terminée. Les tests sont la documentation vivante du comportement attendu.

## Stack de tests

### Backend (Python)
- **Framework** : pytest + pytest-asyncio
- **Couverture** : 118+ tests unitaires/intégration
- **Fixtures** : conftest.py avec DB in-memory et mocks
- **Runner** : `make test-backend` ou `uv run pytest tests/ -v`

### Frontend (TypeScript)
- **Framework** : Vitest + React Testing Library
- **Couverture** : Tests de stores, hooks et utilitaires
- **Runner** : `npm run test` dans src/frontend/

### E2E (End-to-End)
- **Framework** : Playwright
- **Couverture** : 18 tests (onboarding, chat, guided prompts)
- **Runner** : `make test-e2e` (headless) ou `make test-e2e-headed`
- **Sandbox** : Environnement isolé (~/.therese-test-sandbox)

## Architecture des tests backend

### Structure des fichiers
```
tests/
├── conftest.py                    # Fixtures globales
├── test_routers_chat.py           # Tests chat (8)
├── test_routers_memory.py         # Tests mémoire (8)
├── test_routers_config.py         # Tests config (9)
├── test_routers_email.py          # Tests email (22)
├── test_routers_calendar.py       # Tests calendrier (21)
├── test_routers_crm.py            # Tests CRM (32)
├── test_routers_skills.py         # Tests skills Office (6)
├── test_routers_images.py         # Tests images (5)
├── test_services_llm.py           # Tests LLM providers (25)
├── test_services_encryption.py    # Tests chiffrement (14)
├── test_services_web_search.py    # Tests recherche web (10)
├── test_services_mcp.py           # Tests MCP (19)
├── test_error_handling.py         # Tests erreurs (19)
├── test_backup.py                 # Tests sauvegarde (11)
├── test_services_security.py      # Tests sécurité (10)
├── test_performance.py            # Tests performance (17)
├── test_personalisation.py        # Tests personnalisation (15)
├── test_escalation.py             # Tests escalation (16)
└── e2e/                           # Tests Playwright
    ├── conftest.py                # Fixtures E2E (sandbox, serveurs)
    ├── test_onboarding.py         # Tests wizard (6)
    ├── test_chat.py               # Tests chat (6)
    └── test_guided_prompts.py     # Tests prompts guidés (6)
```

### Fixtures principales (conftest.py)

```python
@pytest.fixture
async def db_session():
    """Session SQLite in-memory, fresh par test"""

@pytest.fixture
async def async_client(db_session):
    """AsyncClient avec session override"""

@pytest.fixture
def client(async_client):
    """Alias pour async_client"""

@pytest.fixture
def sync_client():
    """TestClient synchrone pour tests simples"""
```

### Conventions de nommage
- Fichiers : `test_{router|service}_{domaine}.py`
- Fonctions : `async def test_{action}_{scenario}()`
- Exemples :
  - `test_create_contact_success`
  - `test_create_contact_missing_name`
  - `test_stream_message_with_tools`
  - `test_encrypt_decrypt_roundtrip`

### Structure d'un test type

```python
@pytest.mark.asyncio
async def test_create_contact_success(client):
    """Création d'un contact avec tous les champs."""
    # Arrange
    payload = {"first_name": "Jean", "last_name": "Dupont", "email": "jean@test.fr"}

    # Act
    response = await client.post("/api/memory/contacts", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Jean"
    assert data["id"] is not None
```

### Règles des tests backend
1. **Chaque test est indépendant** - pas d'état partagé entre tests
2. **DB in-memory** - recréée pour chaque test
3. **Mocks pour les services externes** - LLM, Qdrant, APIs tierces
4. **Async par défaut** - utiliser @pytest.mark.asyncio
5. **Arrange-Act-Assert** - structure AAA obligatoire
6. **Un assert principal** par test (+ asserts secondaires acceptés)
7. **Nommage descriptif** - le nom du test décrit le scénario
8. **Pas de sleep()** - utiliser des événements async
9. **Pas de données en dur** - utiliser des fixtures ou factories

### Tests de sécurité obligatoires
- Validation des chemins de fichiers (traversal)
- Chiffrement/déchiffrement round-trip
- Token de session (valide/invalide/absent)
- Rate limiting (dépasser la limite)
- CORS (origines autorisées/refusées)
- Injection de prompt (patterns détectés)

## Architecture des tests frontend

### Structure
```
src/frontend/src/
├── stores/
│   └── chatStore.test.ts     # Tests mutations store
├── hooks/
│   └── *.test.ts             # Tests hooks
└── lib/
    └── *.test.ts             # Tests utilitaires
```

### Conventions Vitest
```typescript
describe('chatStore', () => {
  beforeEach(() => {
    // Reset store state
  });

  it('devrait créer une conversation', () => {
    // Arrange
    const store = useChatStore.getState();

    // Act
    store.createConversation();

    // Assert
    expect(store.conversations).toHaveLength(1);
  });
});
```

### Règles des tests frontend
1. **Render + interaction** - Tester le comportement, pas l'implémentation
2. **Queries accessibles** - getByRole, getByText (pas getByTestId sauf nécessité)
3. **Mock des APIs** - vi.mock pour les appels réseau
4. **Mock de Tauri** - Simuler les APIs Tauri (dialog, fs)
5. **State reset** - Store Zustand réinitialisé entre les tests

## Tests E2E (Playwright)

### Environnement sandbox
- Répertoire isolé : `~/.therese-test-sandbox`
- Backend lancé en sous-processus (port dédié)
- Frontend en mode test
- Base de données vide à chaque run
- Screenshots automatiques en cas d'échec

### Conventions E2E
```python
async def test_onboarding_completes(page, backend_url):
    """L'utilisateur peut compléter l'onboarding en 6 étapes."""
    await page.goto(f"{backend_url}")

    # Étape 1 : Bienvenue
    await page.click("text=Commencer")

    # Étape 2 : Profil
    await page.fill("[name=name]", "Test User")
    await page.click("text=Suivant")

    # ... etc

    # Vérification finale
    await expect(page.locator(".chat-layout")).to_be_visible()
```

### Règles E2E
1. **Sandbox obligatoire** - jamais sur les données réelles
2. **Headless par défaut** - headed pour le debug
3. **Timeouts explicites** - pas de waits implicites
4. **Screenshots** - captures automatiques en cas d'échec
5. **Sélecteurs stables** - texte visible ou data-testid
6. **Nettoyage** - sandbox supprimé après les tests

## Matrice de couverture minimale

| Module | Tests min | Type |
|--------|-----------|------|
| Chat | 8 | Router + SSE |
| Mémoire | 8 | CRUD + Search |
| Config | 9 | Préférences + API keys |
| Skills | 6 | Génération Office |
| Board | 5 | Délibération multi-LLM |
| Email | 10 | OAuth + IMAP/SMTP |
| Calendrier | 10 | CRUD événements |
| CRM | 10 | Sync Google Sheets |
| LLM Providers | 25 | Tous les providers |
| Chiffrement | 14 | Fernet + Trousseau |
| MCP | 19 | Transport + outils |
| Sécurité | 10 | SEC-001 à SEC-025 |
| E2E | 18 | Flux complets |

## Commandes

```bash
# Backend
make test-backend                 # Tous les tests backend
uv run pytest tests/ -v          # Verbose
uv run pytest tests/ -k "chat"   # Filtrer par nom
uv run pytest tests/ --tb=short  # Traceback court

# Frontend
cd src/frontend && npm run test        # Tous les tests
cd src/frontend && npm run test -- --ui # Interface UI

# E2E
make install-e2e          # Installer Playwright
make test-e2e             # Headless
make test-e2e-headed      # Visible
```

## Anti-patterns de tests à éviter
- Pas de tests qui dépendent de l'ordre d'exécution
- Pas de tests qui appellent des APIs réelles (toujours mocker)
- Pas de sleep() pour attendre des résultats async
- Pas de tests qui vérifient l'implémentation (tester le comportement)
- Pas de données de test copiées-collées (utiliser des fixtures/factories)
- Pas de tests flaky (si un test échoue aléatoirement, le corriger immédiatement)
- Pas de console.log dans les tests (utiliser les assertions)
