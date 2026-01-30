# Rapport Tests & Fiabilite - THERESE V2

**Date** : 28 janvier 2026
**Auditeur** : Claude Opus 4.5 (audit automatise)
**Version** : MVP v3.1 (CRM Sync)

---

## Resume executif

THERESE V2 dispose d'une base de tests significative mais **inegalement repartie**. Les modules recents (email, calendar, tasks, invoices, CRM, RGPD) n'ont **aucun test unitaire ni d'integration**. Les chemins de securite (chiffrement, OAuth, MCP) sont insuffisamment testes. Le SSE streaming n'est teste qu'au niveau E2E (flaky). Les tests E2E dependent d'un backend reel et de cles API valides, ce qui les rend non-reproductibles en CI.

**Couverture globale estimee** : ~35-40% du code backend, ~15% du code frontend

**Points forts** :
- Tests unitaires solides sur les calculateurs, board, config, memory
- Tests frontend Vitest bien structures (chatStore, utils, hooks)
- Infrastructure de test E2E avec sandbox isole (Playwright)
- Deux conftest.py independants avec DB en memoire

**Points critiques** :
- 7 routers sans aucun test (email, calendar, tasks, invoices, CRM, RGPD, data)
- 12+ services sans test (encryption, oauth, mcp_service, gmail, CRM sync, etc.)
- Aucun test de securite reel (chiffrement, injection, auth)
- Tests E2E non executables en CI (cles API requises)
- Tests tautologiques identifies (error-handling frontend)

---

## Inventaire des tests

### Tests Python unitaires/integration : 16 fichiers, ~269 tests

| Emplacement | Fichiers | Tests |
|-------------|----------|-------|
| `tests/` (racine) | 11 fichiers | 166 tests |
| `src/backend/tests/` | 6 fichiers | 103 tests |
| **Total Python** | **17 fichiers** | **269 tests** |

Detail `tests/` :
- `test_routers_board.py` : 14 tests
- `test_routers_calculators.py` : 18 tests
- `test_routers_chat.py` : 20 tests
- `test_routers_config.py` : 23 tests
- `test_routers_images.py` : 13 tests
- `test_routers_mcp.py` : 14 tests
- `test_routers_memory.py` : 16 tests
- `test_routers_skills.py` : 13 tests
- `test_routers_voice.py` : 9 tests
- `test_services_llm.py` : 16 tests
- `test_services_web_search.py` : 10 tests

Detail `src/backend/tests/` :
- `test_error_handling.py` : 20 tests
- `test_backup.py` : 13 tests
- `test_services_security.py` : 20 tests
- `test_performance.py` : 20 tests
- `test_personalisation.py` : 13 tests
- `test_escalation.py` : 17 tests

### Tests Frontend (Vitest) : 7 fichiers, ~82 tests

| Fichier | Tests |
|---------|-------|
| `lib/utils.test.ts` | 17 tests |
| `stores/chatStore.test.ts` | 15 tests |
| `hooks/useKeyboardShortcuts.test.ts` | 9 tests |
| `lib/accessibility.test.tsx` | 14 tests |
| `lib/error-handling.test.ts` | 11 tests |
| `hooks/useHealthCheck.test.ts` | 7 tests |
| `hooks/useVoiceRecorder.test.ts` | 9 tests |

### Tests E2E (Playwright) : 8 fichiers, ~47 tests

| Fichier | Tests |
|---------|-------|
| `test_onboarding.py` | 5 tests |
| `test_chat.py` | 7 tests |
| `test_guided_prompts.py` | 6 tests (dont 3 parametrises) |
| `test_board.py` | 4 tests |
| `test_images.py` | 6 tests |
| `test_mcp.py` | 5 tests |
| `test_memory.py` | 8 tests |
| `test_skills.py` | 6 tests |

---

## Matrice de couverture par module

### Routers

| Module | Fichier source | Test existant | Couverture estimee | Priorite |
|--------|---------------|---------------|-------------------|----------|
| chat | `routers/chat.py` | `test_routers_chat.py` | 40% | HIGH |
| memory | `routers/memory.py` | `test_routers_memory.py` | 50% | MEDIUM |
| config | `routers/config.py` | `test_routers_config.py` | 60% | LOW |
| board | `routers/board.py` | `test_routers_board.py` | 55% | MEDIUM |
| calculators | `routers/calculators.py` | `test_routers_calculators.py` | 80% | LOW |
| skills | `routers/skills.py` | `test_routers_skills.py` | 40% | MEDIUM |
| images | `routers/images.py` | `test_routers_images.py` | 35% | MEDIUM |
| mcp | `routers/mcp.py` | `test_routers_mcp.py` | 30% | HIGH |
| voice | `routers/voice.py` | `test_routers_voice.py` | 30% | MEDIUM |
| files | `routers/files.py` | Aucun | 0% | HIGH |
| **email** | `routers/email.py` | **Aucun** | **0%** | **CRITICAL** |
| **email_setup** | `routers/email_setup.py` | **Aucun** | **0%** | **HIGH** |
| **calendar** | `routers/calendar.py` | **Aucun** | **0%** | **CRITICAL** |
| **tasks** | `routers/tasks.py` | **Aucun** | **0%** | **HIGH** |
| **invoices** | `routers/invoices.py` | **Aucun** | **0%** | **CRITICAL** |
| **crm** | `routers/crm.py` | **Aucun** | **0%** | **CRITICAL** |
| **rgpd** | `routers/rgpd.py` | **Aucun** | **0%** | **CRITICAL** |
| **data** | `routers/data.py` | **Aucun** | **0%** | **HIGH** |
| personalisation | `routers/personalisation.py` | `test_personalisation.py` | 55% | MEDIUM |
| performance | `routers/performance.py` | `test_performance.py` | 50% | LOW |
| escalation | `routers/escalation.py` | `test_escalation.py` | 60% | LOW |

### Services

| Module | Fichier source | Test existant | Couverture estimee | Priorite |
|--------|---------------|---------------|-------------------|----------|
| llm | `services/llm.py` | `test_services_llm.py` | 25% | HIGH |
| web_search | `services/web_search.py` | `test_services_web_search.py` | 40% | MEDIUM |
| error_handler | `services/error_handler.py` | `test_error_handling.py` | 50% | MEDIUM |
| token_tracker | `services/token_tracker.py` | `test_escalation.py` (partiel) | 30% | MEDIUM |
| **encryption** | `services/encryption.py` | **Aucun** | **0%** | **CRITICAL** |
| **oauth** | `services/oauth.py` | **Aucun** | **0%** | **CRITICAL** |
| **mcp_service** | `services/mcp_service.py` | **Aucun** | **0%** | **CRITICAL** |
| **gmail_service** | `services/gmail_service.py` | **Aucun** | **0%** | **CRITICAL** |
| **crm_sync** | `services/crm_sync.py` | **Aucun** | **0%** | **HIGH** |
| **crm_export** | `services/crm_export.py` | **Aucun** | **0%** | **HIGH** |
| **crm_import** | `services/crm_import.py` | **Aucun** | **0%** | **HIGH** |
| **sheets_service** | `services/sheets_service.py` | **Aucun** | **0%** | **HIGH** |
| **calendar_service** | `services/calendar_service.py` | **Aucun** | **0%** | **HIGH** |
| **email/ (providers)** | `services/email/` | **Aucun** | **0%** | **CRITICAL** |
| **calendar/ (providers)** | `services/calendar/` | **Aucun** | **0%** | **HIGH** |
| **invoice_pdf** | `services/invoice_pdf.py` | **Aucun** | **0%** | **HIGH** |
| **scoring** | `services/scoring.py` | **Aucun** | **0%** | **MEDIUM** |
| **audit** | `services/audit.py` | **Aucun** | **0%** | **MEDIUM** |
| **entity_extractor** | `services/entity_extractor.py` | **Aucun** | **0%** | **MEDIUM** |
| **user_profile** | `services/user_profile.py` | **Aucun** | **0%** | **LOW** |
| **file_parser** | `services/file_parser.py` | **Aucun** | **0%** | **MEDIUM** |
| embeddings | `services/embeddings.py` | **Aucun** | **0%** | **MEDIUM** |
| qdrant | `services/qdrant.py` | **Aucun** | **0%** | **HIGH** |
| skills/ | `services/skills/*.py` | **Aucun** (seulement router) | **0%** | **MEDIUM** |

### Frontend

| Module | Fichier source | Test existant | Couverture estimee | Priorite |
|--------|---------------|---------------|-------------------|----------|
| chatStore | `stores/chatStore.ts` | `chatStore.test.ts` | 70% | LOW |
| utils | `lib/utils.ts` | `utils.test.ts` | 90% | LOW |
| useKeyboardShortcuts | `hooks/useKeyboardShortcuts.ts` | `useKeyboardShortcuts.test.ts` | 80% | LOW |
| useHealthCheck | `hooks/useHealthCheck.ts` | `useHealthCheck.test.ts` | 50% | MEDIUM |
| useVoiceRecorder | `hooks/useVoiceRecorder.ts` | `useVoiceRecorder.test.ts` | 40% | MEDIUM |
| **api.ts** | `services/api.ts` | **Aucun** | **0%** | **HIGH** |
| **ChatInput** | `components/chat/ChatInput.tsx` | **Aucun** | **0%** | **HIGH** |
| **MessageBubble** | `components/chat/MessageBubble.tsx` | **Aucun** | **0%** | **MEDIUM** |
| **SettingsModal** | `components/settings/SettingsModal.tsx` | **Aucun** | **0%** | **MEDIUM** |
| **MemoryPanel** | `components/memory/MemoryPanel.tsx` | **Aucun** | **0%** | **MEDIUM** |
| **BoardPanel** | `components/board/BoardPanel.tsx` | **Aucun** | **0%** | **MEDIUM** |
| **personalisationStore** | `stores/personalisationStore.ts` | **Aucun** | **0%** | **LOW** |

---

## Findings

### TEST-001 : Aucun test pour le router Email (Gmail + IMAP/SMTP)
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/routers/email.py`
- **Description** : Le module email est un des piliers fonctionnels de THERESE (Phase 1). Il gere OAuth Google, la synchronisation Gmail, l'envoi et la reception d'emails. Aucun test n'existe pour valider ces flux critiques. Un bug dans l'envoi d'email pourrait envoyer des donnees sensibles au mauvais destinataire.
- **Tests manquants** :
  - OAuth flow complet (initiation, callback, token refresh)
  - Listing des emails avec pagination
  - Envoi d'email (validation from/to/subject/body)
  - Recherche d'emails
  - Gestion des labels
  - Sync incrementale
  - Gestion des erreurs (token expire, quota, rate limit)
  - Provider IMAP/SMTP (connexion, deconnexion, fallback)
- **Remediation** : Creer `tests/test_routers_email.py` avec mocks pour Gmail API et IMAP. Minimum 25 tests.

### TEST-002 : Aucun test pour le router Calendar
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/routers/calendar.py`
- **Description** : Le calendrier gere des rendez-vous et evenements. Aucun test ne valide le CRUD evenements, la synchronisation Google Calendar, ni les providers CalDAV. Un bug pourrait creer des doublons ou supprimer des rendez-vous importants.
- **Tests manquants** :
  - CRUD evenements (create, read, update, delete)
  - Liste des calendriers
  - Sync Google Calendar
  - Provider CalDAV (Nextcloud, iCloud)
  - Gestion des fuseaux horaires
  - Evenements recurrents
  - Quick add
- **Remediation** : Creer `tests/test_routers_calendar.py` avec mocks CalendarService. Minimum 20 tests.

### TEST-003 : Aucun test pour le router Invoices (Facturation)
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/routers/invoices.py`
- **Description** : La facturation est critique pour un outil de solopreneur. Un bug dans la generation de numero de facture, le calcul de TVA ou la generation PDF pourrait avoir des consequences legales. Aucun test n'existe.
- **Tests manquants** :
  - Generation numero facture sequentiel (FACT-YYYY-NNN)
  - CRUD factures et lignes
  - Calcul montant HT/TVA/TTC
  - Generation PDF
  - Marquage paiement
  - Recherche et filtrage
  - Validation des donnees (montant negatif, TVA invalide)
- **Remediation** : Creer `tests/test_routers_invoices.py`. Minimum 20 tests. Priorite sur la numerotation et les calculs TVA.

### TEST-004 : Aucun test pour le router CRM
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/routers/crm.py`
- **Description** : Le CRM gere le pipeline clients, le scoring, les activites, les livrables et la synchronisation Google Sheets. La sync bidirectionnelle Google Sheets est un flux complexe sans aucun test. Un bug de sync pourrait corrompre les donnees CRM.
- **Tests manquants** :
  - Pipeline CRM (stages, transitions)
  - Scoring contacts (calcul, mise a jour)
  - Activites (creation, listing, filtrage)
  - Livrables (CRUD, status)
  - Sync Google Sheets (config, import, export)
  - Export CRM (CSV, JSON)
  - Import CRM avec validation
  - Gestion des conflits de sync
- **Remediation** : Creer `tests/test_routers_crm.py` avec mocks sheets_service. Minimum 25 tests.

### TEST-005 : Aucun test pour le router RGPD
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/routers/rgpd.py`
- **Description** : Le module RGPD implemente des obligations legales (droit de portabilite, droit a l'oubli). Un bug ici pourrait entrainer un non-respect de la reglementation europeenne. Les fonctions d'anonymisation et d'export de donnees ne sont pas testees.
- **Tests manquants** :
  - Export donnees contact (portabilite Art. 20)
  - Anonymisation contact (oubli Art. 17)
  - Renouvellement consentement
  - Statistiques RGPD
  - Validation que les donnees exportees sont completes
  - Validation que l'anonymisation est irreversible
  - Contact inexistant (404)
- **Remediation** : Creer `tests/test_routers_rgpd.py`. Minimum 15 tests.

### TEST-006 : Service de chiffrement (encryption.py) non teste
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/services/encryption.py`
- **Description** : Le service Fernet chiffre toutes les cles API et tokens OAuth stockes en base. Le test `test_services_security.py` existe mais ne teste pas directement le EncryptionService (singleton, generation de cle, chiffrement/dechiffrement, gestion erreurs). Un bug pourrait exposer les cles API en clair ou empecher le dechiffrement apres un redemarrage.
- **Tests manquants** :
  - Singleton pattern (meme instance)
  - Generation et persistance de la cle
  - Chiffrement/dechiffrement roundtrip
  - Detection de valeur chiffree (`is_value_encrypted`)
  - Gestion d'erreur si cle invalide/corrompue
  - Gestion d'erreur si fichier cle absent
  - Permissions fichier cle (0600)
  - Chiffrement de chaines vides, None, unicode
- **Remediation** : Creer `tests/test_services_encryption.py` avec isolation filesystem (tmpdir). Minimum 12 tests.

### TEST-007 : Service OAuth non teste
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/services/oauth.py`
- **Description** : Le service OAuth gere le flux PKCE pour Gmail, Google Calendar et Google Sheets. Aucun test ne valide la generation du code verifier, le challenge S256, l'echange de tokens, ou le refresh. Un bug pourrait bloquer toute connexion aux services Google ou fuiter le code secret.
- **Tests manquants** :
  - Generation code_verifier (longueur, caracteres)
  - Calcul code_challenge S256
  - Construction URL d'autorisation
  - Echange code -> tokens (mock HTTP)
  - Refresh token (mock HTTP)
  - Gestion token expire
  - Erreurs reseau lors de l'echange
  - Validation des scopes
- **Remediation** : Creer `tests/test_services_oauth.py`. Minimum 15 tests.

### TEST-008 : Service MCP non teste (execution commandes systeme)
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/services/mcp_service.py`
- **Description** : Le MCPService lance des processus systeme (subprocess) pour les serveurs MCP et execute des commandes via JSON-RPC. C'est le composant le plus risque en termes de securite (injection de commandes, lectures de fichiers, etc.). Le test `test_routers_mcp.py` ne teste que les endpoints HTTP, pas le service lui-meme.
- **Tests manquants** :
  - Start/stop serveur (subprocess mock)
  - Decouverte des tools (tools/list)
  - Execution de tool (tools/call)
  - Chainement de tools
  - Timeout d'execution
  - Gestion processus zombie
  - Chiffrement/dechiffrement des env vars au demarrage
  - Persistance config JSON
  - Injection de commande via arguments
  - Erreur si commande inexistante
- **Remediation** : Creer `tests/test_services_mcp.py` avec subprocess mock. Minimum 18 tests. Priorite securite.

### TEST-009 : Aucun test pour le router Tasks
- **Severite** : HIGH
- **Fichier** : `src/backend/app/routers/tasks.py`
- **Description** : Le CRUD des taches locales n'a aucun test. Les filtres par status, priorite et projet ne sont pas valides.
- **Tests manquants** :
  - CRUD taches (create, list, get, update, delete)
  - Filtrage par status (todo, in_progress, done, cancelled)
  - Filtrage par priorite (low, medium, high, urgent)
  - Filtrage par project_id
  - Tache inexistante (404)
  - Validation des donnees
- **Remediation** : Creer `tests/test_routers_tasks.py`. Minimum 12 tests.

### TEST-010 : Aucun test pour le router Data (export/backup)
- **Severite** : HIGH
- **Fichier** : `src/backend/app/routers/data.py`
- **Description** : Le router data gere l'export RGPD et les logs d'activite. Bien que `test_backup.py` existe dans `src/backend/tests/`, il ne couvre pas les endpoints de `data.py`. L'export de donnees ne verifie pas que les cles API sont bien exclues.
- **Tests manquants** :
  - Export complet des donnees
  - Verification que les cles API sont sanitizees
  - Logs d'activite (creation, listing)
  - Export par type de donnee
- **Remediation** : Creer `tests/test_routers_data.py`. Minimum 8 tests.

### TEST-011 : Aucun test pour le router Files
- **Severite** : HIGH
- **Fichier** : `src/backend/app/routers/files.py`
- **Description** : L'upload de fichiers est un vecteur d'attaque classique. Aucun test ne valide la taille max, les types MIME, le path traversal, ou le stockage.
- **Tests manquants** :
  - Upload fichier valide
  - Rejet fichier trop gros
  - Rejet type MIME dangereux (.exe, .bat)
  - Path traversal (../../etc/passwd)
  - Listing des fichiers uploades
  - Suppression de fichier
  - Fichier inexistant (404)
- **Remediation** : Creer `tests/test_routers_files.py`. Minimum 10 tests.

### TEST-012 : Tests tautologiques dans error-handling.test.ts
- **Severite** : MEDIUM
- **Fichier** : `src/frontend/src/lib/error-handling.test.ts`
- **Description** : Plusieurs tests mockent `globalThis.fetch` puis appellent `fetch()` directement. Ils testent le comportement du mock, pas celui du code applicatif. Le test "US-ERR-02: Retry on timeout" implemente la logique de retry dans le test lui-meme (inline `fetchWithRetry`) au lieu de tester la vraie implementation. Le test "US-ERR-03: Graceful degradation" mock des URLs specifiques mais ne teste pas le service reel.
- **Tests manquants** :
  - Tests du vrai service `api.ts` avec retry
  - Tests du comportement reel de `chatStore` en cas d'erreur
  - Tests du composant de notification d'erreur
- **Remediation** : Refactorer pour tester le code applicatif reel (`api.ts`, `chatStore`). Les tests actuels sont une specification valide mais ne testent pas le code reel.

### TEST-013 : SSE streaming non teste unitairement
- **Severite** : HIGH
- **Fichier** : `src/backend/app/routers/chat.py`
- **Description** : Le streaming SSE est le coeur du chat. Le test `test_routers_chat.py` ne valide que le header `text/event-stream` mais ne parse pas le flux. Les events SSE (`text`, `status`, `tool_result`, `entities_detected`, `done`) ne sont pas valides individuellement. Un changement de format pourrait casser le frontend sans que les tests le detectent.
- **Tests manquants** :
  - Parsing d'un flux SSE complet
  - Validation event `data: {"type": "text", "content": "..."}`
  - Validation event `done`
  - Event `status` pendant tool calling
  - Event `tool_result`
  - Event `entities_detected`
  - Annulation mid-stream (`/api/chat/cancel/{id}`)
  - Flux avec erreur LLM mid-stream
- **Remediation** : Ajouter dans `test_routers_chat.py` des tests qui parsent le flux SSE avec `httpx-sse` ou un parser custom. Minimum 8 tests.

### TEST-014 : MCP tool calling flow non teste de bout en bout
- **Severite** : HIGH
- **Fichier** : `src/backend/app/routers/chat.py` + `services/llm.py`
- **Description** : Le flow complet (LLM demande tool -> backend execute via MCP -> resultat renvoye au LLM -> continuation) n'est teste ni unitairement ni en integration. Le test E2E `test_mcp.py` est flaky car il depend d'un serveur MCP reel et d'un LLM configure.
- **Tests manquants** :
  - `stream_response_with_tools()` avec tools mock
  - `_execute_tools_and_continue()` avec MCPService mock
  - `continue_with_tool_results()` avec LLM mock
  - Chainement de tools (max 5 iterations)
  - Timeout sur tool execution
  - Tool execution echouee -> message d'erreur au LLM
- **Remediation** : Creer `tests/test_tool_calling.py` avec mocks LLM + MCP. Minimum 10 tests.

### TEST-015 : CRM sync import/export cycle non teste
- **Severite** : HIGH
- **Fichier** : `src/backend/app/services/crm_sync.py`, `crm_export.py`, `crm_import.py`
- **Description** : La synchronisation bidirectionnelle Google Sheets est un flux complexe avec de nombreux points de defaillance (OAuth, parsing, mapping colonnes, gestion des conflits). Aucun test unitaire n'existe pour les 3 services CRM.
- **Tests manquants** :
  - Import depuis Google Sheets (mock sheets_service)
  - Export vers Google Sheets
  - Cycle complet import -> modification locale -> export
  - Gestion des colonnes manquantes
  - Gestion des doublons (meme email)
  - Parsing des types (dates, nombres, tags CSV)
  - Import direct JSON (endpoint `/api/crm/sync/import`)
  - Erreur si spreadsheet_id invalide
- **Remediation** : Creer `tests/test_services_crm.py`. Minimum 15 tests.

### TEST-016 : Conftest.py duplique entre tests/ et src/backend/tests/
- **Severite** : MEDIUM
- **Fichier** : `tests/conftest.py` et `src/backend/tests/conftest.py`
- **Description** : Deux fichiers conftest.py quasi identiques existent. Le premier (`tests/conftest.py`) expose la fixture `client`, le second (`src/backend/tests/conftest.py`) expose `async_client` et `client` (alias). Les fixtures de donnees (sample_*) ne sont presentes que dans `tests/conftest.py`. Le `pyproject.toml` ne configure que `testpaths = ["tests"]`, ce qui signifie que `src/backend/tests/` n'est pas decouvert par defaut.
- **Tests manquants** : Pas de tests manquants, mais risque de confusion et de regression.
- **Remediation** : Fusionner les deux conftest.py dans `tests/conftest.py`. Ajouter `"src/backend/tests"` dans `testpaths` du `pyproject.toml`. Ou bien deplacer tous les tests dans un seul emplacement.

### TEST-017 : Tests E2E non reproductibles en CI
- **Severite** : HIGH
- **Fichier** : `tests/e2e/conftest.py`
- **Description** : Les tests E2E :
  1. Lancent un backend reel (`uv run uvicorn`)
  2. Attendent avec `time.sleep(3)` (race condition)
  3. Requierent des cles API valides (LLM pour le chat, images)
  4. Utilisent `headless=False` par defaut (ne fonctionne pas en CI sans X11)
  5. Reset la DB en supprimant le fichier SQLite (race condition si le backend y accede)
  6. Timeouts tres longs (60-70s pour le board)
  7. Dependent de textes specifiques dans l'UI (fragiles)
- **Tests manquants** :
  - Configuration CI-friendly (headless, mocks LLM)
  - Fixture de demarrage backend plus robuste (polling au lieu de sleep)
  - Data fixtures reproductibles
- **Remediation** : Ajouter un mode `headless=True` par defaut (deja possible via `make test-e2e`). Ajouter des mocks LLM pour les tests qui n'ont pas besoin d'un vrai LLM. Utiliser une fixture backend avec polling + timeout. Reduire la dependance aux textes exacts.

### TEST-018 : Aucun test pour les providers email (IMAP/SMTP/Gmail)
- **Severite** : CRITICAL
- **Fichier** : `src/backend/app/services/email/`
- **Description** : Les providers email (base_provider, gmail_provider, imap_smtp_provider, provider_factory) n'ont aucun test. Le pattern factory pour la selection du provider n'est pas teste. L'envoi d'email via SMTP n'est pas teste. La reception via IMAP n'est pas testee.
- **Tests manquants** :
  - Base provider interface (abstract methods)
  - Gmail provider (list, send, read, labels)
  - IMAP provider (connect, list, read, mark read)
  - SMTP provider (send, validation)
  - Provider factory (selection par type de compte)
  - Email classifier (categorisation)
  - Email response generator
- **Remediation** : Creer `tests/test_services_email_providers.py`. Minimum 20 tests.

### TEST-019 : Aucun test pour les skills generators (DOCX/PPTX/XLSX)
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/services/skills/`
- **Description** : Les generateurs de documents Office ne sont testes qu'au niveau du router (`test_routers_skills.py`). Les services internes (docx_generator, pptx_generator, xlsx_generator, registry) ne sont pas testes. Le bug des merged cells XLSX corrige manuellement en v1.3 montre que des tests unitaires auraient permis de detecter le probleme.
- **Tests manquants** :
  - DOCX generator : structure, styles, en-tetes
  - PPTX generator : slides, texte, images
  - XLSX generator : cellules, formules, merged cells
  - Registry : enregistrement/recuperation skills
  - Gestion des templates invalides
  - Gestion des fichiers trop volumineux
- **Remediation** : Creer `tests/test_services_skills.py`. Minimum 15 tests.

### TEST-020 : Edge cases non testes (chaines vides, None, unicode, gros inputs)
- **Severite** : MEDIUM
- **Fichier** : Transversal
- **Description** : Les tests existants couvrent les cas nominaux mais rarement les edge cases. Exemples :
  - `test_routers_memory.py` ne teste pas la creation d'un contact avec un nom vide ou None
  - `test_routers_chat.py` ne teste pas un message vide, un message de 100K caracteres, ou un message avec des caracteres speciaux (emojis, RTL, injection HTML/JS)
  - `test_routers_board.py` ne teste pas une question tres longue (>10K chars)
  - `test_routers_calculators.py` ne teste pas des valeurs extremes (float max, negatifs)
- **Tests manquants** :
  - Input vide ("", None, whitespace-only)
  - Input unicode (emojis, accents, RTL, CJK)
  - Input tres long (buffer overflow)
  - Input avec caracteres speciaux (<script>, SQL injection)
  - Input avec nombres limites (float max, NaN, Infinity)
- **Remediation** : Ajouter des cas edge dans chaque fichier de test existant. Minimum 3-5 edge cases par module.

### TEST-021 : Aucun test pour api.ts (service API frontend)
- **Severite** : HIGH
- **Fichier** : `src/frontend/src/services/api.ts`
- **Description** : Le fichier `api.ts` est le point central de communication frontend-backend. Il contient 50+ fonctions (sendMessage, getConfig, listContacts, etc.) mais aucun test. Les erreurs de serialisation, les headers manquants, ou les URLs incorrectes ne seraient pas detectes.
- **Tests manquants** :
  - Construction des URLs
  - Serialisation des parametres
  - Gestion des erreurs HTTP (4xx, 5xx)
  - Parsing des reponses SSE
  - Timeout/abort
  - Headers (Content-Type, Accept)
- **Remediation** : Creer `src/frontend/src/services/api.test.ts` avec fetch mock. Minimum 20 tests.

### TEST-022 : Service Qdrant non teste
- **Severite** : HIGH
- **Fichier** : `src/backend/app/services/qdrant.py`
- **Description** : Le service Qdrant gere le vector store (embeddings, recherche semantique, suppression par scope). C'est un composant critique pour la memoire de THERESE. Aucun test unitaire n'existe. Le mode degrade si Qdrant est down n'est teste que dans les tests frontend.
- **Tests manquants** :
  - Initialisation collection
  - Insertion de vecteurs
  - Recherche semantique
  - Recherche avec filtrage par scope
  - Suppression par entity_id
  - Suppression par scope
  - Mode degrade (Qdrant down)
  - Gestion des erreurs de connexion
- **Remediation** : Creer `tests/test_services_qdrant.py` avec un client Qdrant mock ou in-memory. Minimum 12 tests.

### TEST-023 : Accessibility tests sur composants synthetiques
- **Severite** : LOW
- **Fichier** : `src/frontend/src/lib/accessibility.test.tsx`
- **Description** : Les tests d'accessibilite testent des composants synthetiques (`AccessibleButton`, `AccessibleModal`) crees dans le fichier de test et non les vrais composants de l'application. Le test `test_buttons_should_respond_to_Enter_key` verifie seulement que le bouton est dans le DOM (`toBeInTheDocument`), pas qu'il repond au clic. Le test de contraste verifie les classes CSS, pas le contraste reel.
- **Tests manquants** :
  - Tests sur les vrais composants (ChatInput, SettingsModal, ContactModal)
  - Tests avec axe-core pour validation WCAG automatique
  - Tests de navigation clavier dans les vrais modaux
  - Tests de focus trap dans les modaux
- **Remediation** : Ajouter `@axe-core/react` et tester les vrais composants. Remplacer les composants synthetiques par les imports reels.

### TEST-024 : Tests E2E Board flaky (timeouts 60-70s)
- **Severite** : MEDIUM
- **Fichier** : `tests/e2e/test_board.py`
- **Description** : Les 4 tests du board utilisent des timeouts de 60-70 secondes car ils attendent les reponses de 5 LLMs differents. `test_board_submit_decision` et `test_board_view_synthesis` sont quasiment identiques (duplications). Le test `test_board_history` utilise une logique conditionnelle (`if history_tab.is_visible()`) qui peut masquer des regressions.
- **Tests manquants** :
  - Test avec LLM mock (rapide, deterministe)
  - Test de timeout (que se passe-t-il apres 70s ?)
  - Test d'annulation de deliberation
- **Remediation** : Ajouter un mode mock LLM pour les tests E2E. Reduire les timeouts. Eliminer les duplications.

### TEST-025 : Aucun test pour le router email_setup
- **Severite** : HIGH
- **Fichier** : `src/backend/app/routers/email_setup.py`
- **Description** : Le wizard de configuration email n'a aucun test. La validation des credentials Google (client_id, client_secret) et la generation de guide ne sont pas testees.
- **Tests manquants** :
  - GET /status
  - POST /validate-credentials
  - POST /generate-guide
  - Validation format client_id / client_secret
  - Status apres configuration
- **Remediation** : Creer `tests/test_routers_email_setup.py`. Minimum 8 tests.

### TEST-026 : Fixture sample_board_request dans conftest mais pas dans src/backend/tests/conftest
- **Severite** : LOW
- **Fichier** : `tests/conftest.py` vs `src/backend/tests/conftest.py`
- **Description** : Les fixtures de donnees (sample_contact_data, sample_project_data, sample_board_request, etc.) ne sont definies que dans `tests/conftest.py`. Les tests dans `src/backend/tests/` n'y ont pas acces. Si un test dans `src/backend/tests/` a besoin de ces fixtures, il faudra les redefinir ou les factoriser.
- **Remediation** : Creer un fichier `tests/fixtures.py` partage et l'importer dans les deux conftest.

### TEST-027 : Service invoice_pdf non teste
- **Severite** : HIGH
- **Fichier** : `src/backend/app/services/invoice_pdf.py`
- **Description** : Le generateur de PDF de factures (reportlab) n'a aucun test. La generation de PDF avec des montants, des lignes, et des calculs TVA est un flux critique pour un outil de facturation. Un bug pourrait generer des factures avec des montants incorrects.
- **Tests manquants** :
  - Generation PDF basique
  - Calcul montant total (somme des lignes)
  - Calcul TVA
  - Formatage des montants (EUR)
  - Gestion du logo/branding
  - Fichier PDF valide et lisible
- **Remediation** : Creer `tests/test_services_invoice_pdf.py`. Minimum 10 tests.

### TEST-028 : pyproject.toml ne configure qu'un seul testpath
- **Severite** : LOW
- **Fichier** : `pyproject.toml`
- **Description** : `testpaths = ["tests"]` ne couvre pas `src/backend/tests/`. Les 103 tests de `src/backend/tests/` ne seront pas decouverts par `pytest` a moins d'etre specifies explicitement. Cela peut donner une fausse impression de couverture.
- **Remediation** : Modifier `testpaths = ["tests", "src/backend/tests"]` ou deplacer les tests.

### TEST-029 : event_loop fixture deprecated
- **Severite** : LOW
- **Fichier** : `tests/conftest.py` et `src/backend/tests/conftest.py`
- **Description** : Les deux conftest.py definissent une fixture `event_loop` avec `scope="session"`. Depuis pytest-asyncio 0.21+, cette fixture est deprecee. La configuration recommandee est `asyncio_mode = "auto"` dans `pyproject.toml` (deja configure) sans fixture event_loop custom.
- **Remediation** : Supprimer la fixture `event_loop` des deux conftest.py. pytest-asyncio la gere automatiquement.

### TEST-030 : Service email_classifier et email_response_generator non testes
- **Severite** : MEDIUM
- **Fichier** : `src/backend/app/services/email_classifier.py`, `email_classifier_v2.py`, `email_response_generator.py`
- **Description** : La classification des emails et la generation de reponses automatiques sont des fonctionnalites IA critiques. Un mauvais classement pourrait entrainer la perte d'emails importants. Aucun test.
- **Tests manquants** :
  - Classification par categorie
  - Priorite des emails
  - Generation de reponse
  - Emails edge cases (spam, vide, multilingue)
- **Remediation** : Creer `tests/test_services_email_classifier.py`. Minimum 10 tests.

---

## Tests critiques manquants (ordonnances par priorite)

### CRITICAL - A implementer immediatement

1. **`tests/test_services_encryption.py`** - Chiffrement des cles API (12+ tests)
   - Roundtrip chiffrement/dechiffrement
   - Gestion de cle corrompue
   - Detection de valeur chiffree
   - Permissions fichier

2. **`tests/test_services_oauth.py`** - OAuth PKCE (15+ tests)
   - Code verifier/challenge
   - Token exchange avec mock HTTP
   - Token refresh
   - Gestion d'erreurs

3. **`tests/test_services_mcp.py`** - MCP Service securite (18+ tests)
   - Subprocess mock pour start/stop
   - Tool execution avec mock
   - Injection de commande
   - Chiffrement env vars

4. **`tests/test_routers_email.py`** - Email complet (25+ tests)
   - OAuth flow
   - CRUD emails
   - Sync
   - Erreurs

5. **`tests/test_routers_invoices.py`** - Facturation (20+ tests)
   - Numerotation
   - Calculs TVA
   - Generation PDF

6. **`tests/test_routers_rgpd.py`** - Conformite legale (15+ tests)
   - Export portabilite
   - Anonymisation
   - Verification completude

### HIGH - A implementer avant release

7. **`tests/test_routers_calendar.py`** (20+ tests)
8. **`tests/test_routers_crm.py`** (25+ tests)
9. **`tests/test_routers_tasks.py`** (12+ tests)
10. **`tests/test_routers_files.py`** (10+ tests)
11. **`tests/test_routers_data.py`** (8+ tests)
12. **`tests/test_routers_email_setup.py`** (8+ tests)
13. **`tests/test_tool_calling.py`** - Flow complet LLM + MCP (10+ tests)
14. **`tests/test_services_crm.py`** - Sync Google Sheets (15+ tests)
15. **`tests/test_services_qdrant.py`** - Vector store (12+ tests)
16. **`tests/test_services_invoice_pdf.py`** - Generation PDF (10+ tests)
17. **`src/frontend/src/services/api.test.ts`** - API frontend (20+ tests)
18. **Tests SSE streaming** dans `test_routers_chat.py` (8+ tests)

### MEDIUM - Prochain sprint

19. **Edge cases** dans tous les tests existants (3-5 par module)
20. **`tests/test_services_skills.py`** - Generators Office (15+ tests)
21. **`tests/test_services_email_classifier.py`** (10+ tests)
22. Refactoring `error-handling.test.ts` pour tester le code reel
23. Consolidation des conftest.py

### LOW - Backlog

24. Suppression fixture `event_loop` deprecated
25. Ajout `src/backend/tests` dans `testpaths`
26. Tests d'accessibilite sur vrais composants avec axe-core
27. Factorisation des fixtures de donnees
28. Tests composants frontend (ChatInput, SettingsModal, BoardPanel)

---

## Statistiques finales

| Categorie | Tests existants | Tests manquants estimes | Total vise |
|-----------|----------------|------------------------|------------|
| Python unitaires/integration | 269 | ~300 | ~570 |
| Frontend (Vitest) | 82 | ~80 | ~160 |
| E2E (Playwright) | 47 | ~20 (ameliorations) | ~67 |
| **Total** | **398** | **~400** | **~797** |

**Couverture actuelle estimee** : ~35%
**Couverture visee** : ~70%

---

*Rapport genere le 28 janvier 2026 par Claude Opus 4.5*
