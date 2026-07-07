# CLAUDE.md - THERESE V2

> Contexte projet pour Claude Code

## Projet

**THERESE v2** - Assistant IA desktop souverain pour solopreneurs et TPE francais.
Memoire persistante, UX premium dark mode, donnees 100% locales.

- **Repo** : `github.com/ludovicsanchez38-creator/Synoptia-THERESE` - branche `main`
- **Open source, gratuit** - alpha en cours
- **CI** : GitHub Actions - workflow CI (lint + tests) + workflow Release (build Tauri macOS/Windows/Linux)

## Stack technique

- **Frontend** : Tauri 2.0 + React 19 + TailwindCSS 4 + Framer Motion + Zustand 5
- **Backend** : Python FastAPI + UV + SQLModel + Alembic (migrations)
- **Database** : SQLite (donnees) + Qdrant (embeddings vectoriels, nomic-embed-text-v1.5, 768 dim)
- **LLM** : Multi-provider (Anthropic, OpenAI, Gemini, Mistral, Grok, OpenRouter, Ollama) + Brave Search (web)
- **Skills Office** : python-docx, python-pptx, openpyxl (sandbox code-execution)
- **Desktop** : Tauri 2.0 (Rust) avec sidecar PyInstaller
- **Securite** : Fernet/Keychain, anti-injection prompt, rate limiting, CORS restrictif
- **MCP** : 19 presets (transport stdio, JSON-RPC)
- **Tests** : Vitest (frontend), pytest (backend), Playwright (E2E)

## Commandes essentielles

```bash
make dev                  # Backend + Tauri simultanes
make dev-backend          # Backend seul (uvicorn :17293)
make dev-frontend         # Frontend seul (Vite :1420)
make test                 # Tous les tests
make test-backend         # pytest (hors E2E)
make lint                 # Ruff (Python) + ESLint (TS)
make build                # Production (Tauri .app)
make build-release        # Build complete (sidecar + Tauri)
make install              # uv sync + npm install
make db-migrate           # Alembic upgrade head
```

**URLs** : Backend http://localhost:17293 | Frontend http://localhost:1420 | Docs http://localhost:17293/docs

## Architecture

```
src/backend/app/
  main.py              # FastAPI app avec lifespan
  models/              # entities.py (SQLModel), schemas.py (Pydantic), board.py
  routers/             # chat, memory, config, skills, images, board, mcp, files, data, crm, email, calendar...
  services/            # llm.py (orchestrateur), providers/ (7 LLM), skills/ (code_executor, generators)
                       # qdrant.py, embeddings.py, mcp_service.py, encryption.py, prompt_security.py...

src/frontend/src/
  App.tsx              # Entry point (onboarding check, panel routing)
  components/          # chat/, guided/, board/, memory/, settings/, onboarding/, sidebar/, panels/, ui/
  services/api/        # 14 modules (chat, memory, config, mcp, skills, images, board, etc.)
  stores/              # Zustand (chatStore, emailStore, calendarStore, etc.)
  hooks/               # useKeyboardShortcuts, useVoiceRecorder, etc.

src/frontend/src-tauri/ # Configuration Tauri 2.0 (Rust)
```

## Conventions de code

- **Python** : UV pour dependances, type hints obligatoires, ruff pour lint
- **TypeScript** : ESLint, composants React fonctionnels
- **Git** : Commits en francais avec accents
- **PPTX/DOCX** : Ne PAS generer de preview LibreOffice
- **Fenetres Tauri** : Ne PAS utiliser `onCloseRequested`, utiliser `once('tauri://destroyed')`

## Donnees utilisateur

- **Repertoire** : `~/.therese/` (DB, images, backups, mcp_servers.json)
- **Sandbox tests** : `~/.therese-test-sandbox/`
- **Cles API** : chiffrees Fernet (cle dans macOS Keychain via `keyring`)

## Identite visuelle

```yaml
palette:
  background: "#0B1226"
  surface: "#131B35"
  text_primary: "#E6EDF7"
  text_muted: "#B6C7DA"
  accent_cyan: "#22D3EE"
  accent_magenta: "#E11D8D"
```

## Modules fonctionnels

Chat multi-LLM, Memoire (contacts/projets/recherche semantique), Skills Office (DOCX/PPTX/XLSX), Email (Gmail OAuth + IMAP/SMTP), Calendrier (Google + CalDAV + local), CRM (pipeline, scoring, sync Google Sheets), Facturation (devis/facture/avoir, PDF conforme), Board de decision IA (5 conseillers), Generation d'images, Transcription vocale, MCP (19 presets), RGPD (export, anonymisation), Atelier documentaire (trame, redaction guidee par section en streaming, pistes, export md/docx)

## Dette technique

> **v0.24.5-alpha RELEASÉE le 14/06/2026** (12 P1 du rapport tests Syn 14/06, build 3 OS OK, landing + latest.json à jour, app installée localement, rapport `docs/releases/v0.24.5-alpha.md`). Détail des fixes + dette résiduelle : section « Depuis fixes P1 rapport Syn 14/06 » ci-dessous. À valider en réel : Gemini 3 + outils (A1), connexion OAuth Google, coûts/tokens affichés.

> **v0.24.4-alpha RELEASÉE le 13/06/2026** (3 fixes testeurs du 12/06, build 3 OS OK, landing + latest.json à jour, rapport `docs/releases/v0.24.4-alpha.md`). BUG-108 (boucle lecture mails Mistral : message à tool_calls force `content=None` dans `_append_openai_tool_turn`), BUG-109 + boucle « connexion expirée » (403 calendrier reformulé sans « reconnecte » + helper `classifyCalendarError` qui désarme `needsReauth` sur un 403), BUG-107 (historique conv d'agent : `setConversationMessages` ne vide plus une conv non synced + garde sidebar). Dette restante :
> - [ ] **BUG-108 — validation réelle Mistral en attente** : le contrat `content=None` + tool_calls n'est confirmable qu'en conditions réelles (lcjp, Windows + clé Mistral) après cette release.
> - [ ] **BUG-109 — 403 chat-agent non couvert** : le 403 calendrier dans le chat passe par `workspace_tools._get_calendar_provider → GoogleCalendarProvider`, pas par `calendar._raise_if_google_403` ; la reformulation ne profite qu'à l'UI CalendarPanel. Mapper le 403 actionnable côté chat-agent si besoin d'un message clair dans la conversation.
> - [ ] **provider badge au restore** : `useConversationSync.loadConversationMessages` ne mappe pas `msg.provider` (contrairement à `ConversationSidebar`) → badge local/cloud perdu au restore startup. À harmoniser.

> **v0.24.1 RELEASÉE le 11/06/2026** (3 fixes lcjp + fix mypy 32f8dae).
> lcjp répondu sur #bugs. Reste : son retour réel (validation multi-tours
> Mistral) et le résultat du test updater 0.24.0 → 0.24.1 mené par Ludo.
>
> **4 bugs Ludo corrigés sur main (11/06 fin de journée, PAS encore releasé)** :
> (1) `fix(images)` 7e0bfd0 : `image_generator._get_api_key_from_db` lisait la
> clé via `create_engine("sqlite://")` standard, KO sur base chiffrée SQLCipher
> (US-014) → « clé non configurée » alors que le test de clé passait. Passe par
> `db_connect`. Touche GPT/Gemini/Fal. (2) `fix(gemini)` e8525a3 : les noms
> d'outils MCP partaient bruts dans `functionDeclarations[].name` → 400 « Invalid
> function name » sur toute la requête → chat Gemini muet. Sanitisation conforme
> + table nom-sanitisé→réel pour le retour + re-sanitisation du tour rejoué.
> (3) `fix(email)` 83564ad : barre d'actions du mail sans `shrink-0` → « Générer
> une réponse » coupé en bas. (4) `fix(prompts)` 917200f : overlay biblio sans
> hauteur fixe (`max-h` seul + enfant `h-full`) → 1re carte coupée en haut →
> `h-[85vh] overflow-hidden`. Backend 1173 verts, frontend 26 verts (composants).
> **RELEASÉ v0.24.2-alpha le 11/06** (build 3 OS OK, landing + latest.json à
> jour, rapport `docs/releases/v0.24.2-alpha.md`). Vérif visuelle des 2 fixes UI
> reportée (économie tokens) : Ludo la fera dans l'app installée.


(Section maintenue par le workflow /release-therese et Zezette)

### Depuis bump sécurité dépendances (07/07/2026, pré-release 0.26.2)
- [ ] **Bump starlette 1.3.x + httpx2 - à faire À FROID, hors release** : starlette 1.2.1 gardé volontairement avec 2 exceptions pip-audit (PYSEC-2026-248 spoofing request.url, PYSEC-2026-249 limites form-urlencoded ignorées - surface réduite : serveur loopback + token de session). Le TestClient de starlette 1.3 passe à `httpx2` (à ajouter au groupe dev) et le fallback httpx est cassé (`AttributeError: 'ByteStream' object has no attribute 'write'`) ; même avec httpx2, les requêtes longues (vrai appel LLM local pendant les tests) se désynchronisent : le POST rend un 500 immédiat pendant que le handler continue en fond. À investiguer posément (timeout du TestClient httpx2, interaction BaseHTTPMiddleware + GZip) avec la suite complète en local AVANT de merger.
- [ ] **Gotcha suite locale** : si un Ollama local répond sur 11434 (ex. Tïa), certains tests `test_routers_chat.py` font de VRAIS appels LLM (le mock ne couvre pas ce chemin) - durées de tests gonflées et résultats dépendants du modèle local. Mocker le provider dans ces tests ou forcer un `OLLAMA_BASE_URL` mort dans le conftest.

### Depuis atelier documentaire (07/07/2026, branche feat/atelier-documentaire)
Dette triée par la revue finale de branche (vague de fixes bloquants/minors, tous corrigés dans le même lot sauf mention contraire) :
- [ ] **Fenêtre étroite au flush périodique du draft** : `_draft_stream` (documents.py) flushe un partiel brut toutes les `DRAFT_FLUSH_INTERVAL_SECONDS` (2 s) - si le stream s'interrompt juste après un flush partiel ET que la complétion finale parse à vide (0 contenu exploitable), le partiel brut (avec un éventuel bloc `PISTES:` non retiré) reste en base à la place de l'ancien contenu propre. Suivi : restauration du contenu pré-draft côté backend dans ce cas précis (le store frontend restaure déjà côté client quand 0 chunk texte a été reçu - cf `documentStore.ts`, mais ne couvre pas ce cas où des chunks ONT été reçus puis la complétion finale est vide).
- [ ] **Sentinelle `PISTES:` majuscule seule mi-texte** : `parse_draft_output` (document_orchestrator.py) coupe au DERNIER marqueur exact `PISTES:` en fin de ligne. Un modèle qui répondrait ce marqueur exact au milieu d'un texte SANS reprendre de bloc final ensuite verrait la prose qui suit reclassée en pistes (mésusage du protocole imposé au modèle par le prompt, pas un bug de parsing en soi). Protégé dès qu'un vrai bloc final existe (c'est le dernier marqueur qui fait foi).
- [ ] **`_draft_stream` réutilise la session request-scoped après le teardown du `Depends`** : le flush périodique et le filet `finally` commitent sur la même session FastAPI injectée, dont le cycle de vie est normalement lié à la requête - ça fonctionne car la `StreamingResponse` garde le générateur (et donc la session) vivants jusqu'à la fin du stream, mais c'est un couplage implicite. Safe avec starlette 1.2.1 épinglé (cf bloc dette sécurité ci-dessus) - À RE-TESTER explicitement au bump starlette 1.3 déjà en dette.
- [ ] **PATCH `content=""` flippe une section vide->brouillon** : un contenu vide explicite (`{"content": ""}`) est traité comme "la rédaction a démarré" (même condition que n'importe quelle chaîne). Comportement figé, pas un bug.
- [ ] **Ids dupliqués dans un payload de reorder** : absorbés silencieusement (le dernier gagne pour cet id) plutôt que rejetés - l'invariant de complétude (ensemble d'ids) ne détecte pas les doublons intra-payload, seulement les écarts avec la base.
- [ ] **TOCTOU check-then-insert sur les routes de création** (`create_section`, `create_piste`, génération de trame) : pattern préexistant du router (pas spécifique à l'atelier documentaire), db check puis insert sans transaction verrouillante - fenêtre théorique de double-écriture sous forte concurrence, non observée en usage réel (single-user desktop).
- [ ] **Duplication du bloc d'export md/docx** entre `chat.py::export_conversation` et `documents.py::export_document` (même mécanique `registry.execute("docx-pro", ...)` / écriture directe du md, dupliquée plutôt que factorisée) + **renderer markdown dupliqué** entre l'éditeur de section de l'atelier et `MessageBubble` (chat). Refactor à prévoir si un 3e consommateur apparaît.
- [ ] **`error` du documentStore est mono-slot** : une seule erreur affichable à la fois, rendue à la fois dans `OutlineTree` ET `SectionEditor` (les deux composants souscrivent au même `error` du store) - un message d'erreur sur une action de trame peut donc s'afficher en double si les deux composants sont montés simultanément. Pas de confusion fonctionnelle (même message, même cause), mais redondant visuellement.
- [ ] **Sections orphelines affichées/draggables mais exclues du payload reorder** : `OutlineTree` les affiche et les rend `draggable`, mais `reorderPayload.ts` les filtre avant l'envoi (l'invariant de complétude ne porte que sur les sections non-orphelines). Sans conséquence en V1 : aucune route ne pose encore `orphan=True` (la régénération de trame actuelle remplace, elle ne détache jamais) - le cas ne peut être fabriqué qu'en manipulant la base directement (cf `test_export_section_orpheline_...`).
- [ ] **`.session_token` écrit en dur dans `~/.therese`** même quand `THERESE_DATA_DIR` est personnalisé (piège pour les instances de test qui pointent ailleurs - le token de session, lui, ne suit pas). Préexistant, pas introduit par l'atelier documentaire, mais touché par les tests de cette branche.
- [ ] **`Document.project_id`/`contact_id` pendants** si le projet ou le contact lié est supprimé ensuite (pas de `ON DELETE SET NULL` ni de nettoyage applicatif) - champ non affiché dans l'atelier V1 donc sans impact visible, mais à traiter si un futur écran affiche le projet/contact lié à un document.
- [x] **`Document.updated_at` figé** : CORRIGÉ dans la même vague (`_touch_document`, appelé par `update_section`, `create_section`, `reorder_sections`, `create_piste`, `validate_section` et chaque flush de `_draft_stream`) - un document qui vit (section retouchée/créée/réordonnée/validée, piste ajoutée, rédaction en cours) remonte désormais dans la liste triée par `updated_at desc`.
- [x] **CORRECTION d'une dette obsolète (BUG-041/TaskKanban)** : voir l'item corrigé dans le bloc « Depuis BUG-041 » ci-dessous - le pattern poignée-seule n'existe plus dans `TaskKanban.tsx`, déjà fixé.

### Depuis BUG-041 drag & drop projets (02/07/2026, PR #92 mergée, PAS releasé)
- [x] **TaskKanban : même pattern poignée-seule que le BUG-041 -> DÉJÀ CORRIGÉ, item obsolète (constaté 07/07/2026, revue finale atelier documentaire)** : `TaskKanban.tsx` a déjà le fix whole-row (`{...attributes} {...listeners}` sur le wrapper de carte, `onDragCancel`, `activationConstraint: { distance: 8 }`) - le pattern poignée-seule décrit ci-dessous n'existe plus dans le fichier. Item laissé pour trace, plus d'action requise.
- ~~dans `TaskKanban.tsx`, les listeners `useSortable` ne couvrent que le `GripVertical` (16px quasi invisible) - attraper la carte tâche par son corps ne démarre aucun drag. Aucun bug testeur ouvert dessus, mais à harmoniser avec le fix `ProjectsKanban.tsx` (listeners sur le wrapper entier + `onDragCancel`, clics préservés par l'activationConstraint 8px ; test de régression modèle : `ProjectsKanban.test.tsx`).~~

- [x] **Calendrier Google 403 → RÉSOLU fcc9b48 (message actionnable + guide corrigé)**. Historique : : `calendarList` 403 (API Calendar non activée dans le projet GCP du testeur) remonte en 500 + « ça coince » dans le chat. Mapper accessNotConfigured/403 vers un message actionnable (« Active l'API Google Calendar dans ta console GCP puis reconnecte »). Et compléter USER_GUIDE_ALPHA : activer Gmail API ET Google Calendar API, type de client « Application Web » (l'URI de redirection de la consigne 403 n'existe pas sur un client Desktop).
- [x] **Score CRM expéditeurs → RÉSOLU c6ce235 (lookup SQL get_crm_contact_by_email)**. Historique : : email.py:1283/1350 `qdrant.search(entity_type='contact')` = TypeError (le paramètre est `memory_types`) + `results[0].payload` sur des dicts. Warnings en rafale, contact_score toujours None. Double fix + test.

### Depuis fixes P1 rapport Syn 14/06/2026 (commits 36922e9..62a4d8c, RELEASÉ en v0.24.5-alpha le 14/06)
12 P1 backend du rapport de tests Syn corrigés (chacun = fix + test de régression). Reste à faire et dette résiduelle :
- [ ] **`/api/shutdown` sans token (CSRF)** : NON corrigé (nécessite un changement Rust (`lib.rs`) + rebuild Tauri signé par les 2 appelants, token `~/.therese/.session_token`). Risque accepté en l'état (ferme l'app, récupérable ; atténué par Private Network Access navigateur).
- [ ] **GitHub Actions Node.js 20 déprécié** : `checkout@v4`, `setup-node@v4`, `setup-python@v5`, `sccache-action` → bascule forcée Node 24 le 16/06/2026, suppression Node 20 le 16/09/2026. Mettre à jour les actions.
- [ ] **Usage tokens estimé, pas réel** : chat non-stream ET board estiment `~2 tokens/mot` (`len(text.split())*2`) au lieu de lire l'usage réel des providers (`usage.input_tokens` Anthropic, `usageMetadata.promptTokenCount` Gemini, etc.). Suffisant pour le budget/garde-fou, mais imprécis. Propager l'usage réel = refactor providers (chaque `stream_response_with_tools` devrait émettre un StreamEvent de métriques en fin de tour).
- [ ] **`stream_response` : erreurs encore avalées par 3 appelants** : le flag `raise_on_error` (défaut False) n'est activé que par chat non-stream et la synthèse deep-research. `entity_extractor`, `action_agents` et `agents/runtime` (branche else non-stream) tolèrent toujours une réponse vide sur erreur provider (dégradation silencieuse acceptable, mais à reconsidérer si un cas réel le justifie). Les conseillers du board gardent leur propre try/except (affichent « Erreur : ... »).
- [ ] **Board token tracking : `conversation_id="board"`** : étiquette générique (le tracker ne pose pas de FK). Si on veut ventiler le coût par délibération, générer l'id de décision en amont de `deliberate` et le propager à `_track_usage`.

### Depuis chantier UX/DA (11/06/2026, commits 203b752..254321a)
- [ ] **window-state et moniteur debranche** : le plugin restaure la POSITION brute sans verifier que le moniteur existe encore (limitation connue tauri-plugin-window-state) - fenetre potentiellement hors ecran apres debranchement d'un externe. Garde possible : post-restore, re-center si hors bornes de `available_monitors()` (lib.rs setup).
- [ ] **bump-version.sh ne regenere pas uv.lock** : la 0.23 est partie avec un uv.lock en 0.22.0 (rattrape commit a1b7422). Ajouter `uv lock` au script (ou a l'etape bump du skill /release-therese, comme le `npm install --package-lock-only` deja prevu).
- [ ] **Doublons macOS dans tests/protocols/app/personas/** : `A1-sophie-freelance 2.md`, `A2-marc-consultant 2.md`, `A3-lea-power-user 2.md` (copies accidentelles, non annotees sidebar-fermee). A supprimer apres confirmation Ludo.
- [ ] **DA brutaliste partielle** : Button.tsx + home + badges PARTOUT (lot 2 badges fait le 11/06, commits a88e127/0031b67 : tous les badges d'etat en tags carres rounded-[6px], restent ronds compteur cloche/toggles/radios/avatars). Pastilles d'icones duotone bordees partout (1d90de7, fin des degrades cyan-magenta - lanceur guide, skills, settings, board, sidebar). Cartes de panneaux, inputs, modales, bulles de message, SideToggle gardent l'ancien style doux - lot 3 eventuel. Balayage final c7cf627 : 37 pastilles degradees converties (panels, settings, modales, wizard email, About, avatars) - PLUS AUCUNE pastille gradient dans l'app. Conserves volontairement : orbe decorative GuidedPrompts, barres de progression gradient, titres gradient-text de marque, rails SideToggle.

### Depuis Sprint 3 (11/06/2026)
- [ ] **E2E Playwright hors CI** : tests/e2e toujours exclus (`--ignore=tests/e2e`) - ils exigent Vite + uvicorn + navigateur, flaky en CI. US-018 a durci le reste (audits bloquants, clippy -D warnings, mypy baseline) ; un job e2e nightly (pas par PR) reste à concevoir.
- [ ] **mypy baseline 1059 erreurs** (ci.yml job mypy) : gate anti-régression seulement. Faire baisser le compteur module par module et mettre à jour MYPY_BASELINE à chaque baisse.
- [ ] **torch 2.9.1 épinglé avec 3 CVE ignorées** (ci.yml security-audit) : bump vers 2.10 à planifier (PyInstaller 3 OS + release.yml à mettre à jour ensemble). transformers 4.57.6 : attendre la 5.0 stable.

### Depuis Sprint 2 (11/06/2026, findings minor de la revue adversariale, non bloquants)
- [x] **Multi-tours d'outils — RÉSOLU 675e209 (11/06/2026)** : ToolTurn + prior_turns sur les 9 providers, accumulation à la récursion chat.py, résultats rejoués tronqués 4000c. Reste à VALIDER EN RÉEL avec Mistral (le provider du bug lcjp) après release 0.24.1. Historique : : confirmé en production chez lcjp (Mistral, Windows 0.21) : `read_emails` exécuté 3x en 1 s sans erreur, résultats jamais réinjectés, le modèle finit par INVENTER une « erreur d'authentification » (l'utilisateur croit à un problème OAuth de son côté). `_execute_tools_and_continue` (chat.py) rappelle `continue_with_tool_results` avec le contexte ORIGINAL : les functionCall/résultats du tour précédent disparaissent de l'historique envoyé au modèle (qui peut re-demander un outil déjà exécuté). Pattern partagé par TOUS les providers (pas introduit par US-009, mais désormais atteignable sur Grok/Ollama/Gemini). Garde-fous existants : cap de créations, max 5 itérations, dédup par nom. Fix : accumuler les tours d'outils dans le contexte de la récursion.
- [ ] **Gemini 2.x + tools = grounding perdu silencieusement** : dès que des tools sont fournis (toujours en chat), google_search est écarté sur gemini-2.x (combinaison non documentée hors Gemini 3) et chat.py n'ajoute pas WEB_SEARCH_TOOL en compensation (commentaire chat.py:866 devenu faux). Impact limité : l'UI ne propose plus que du 3.x. Fix : ajouter WEB_SEARCH_TOOL aux tools Gemini quand le grounding est écarté.
- [ ] **Protocoles de test manuels vs virtualisation** : les personas (tests/protocols/app/personas/*.md) comptent les messages via querySelectorAll('[data-testid="chat-message-item"]') - avec react-virtuoso, seuls les items de la fenêtre de rendu sont dans le DOM. Mettre à jour les protocoles (compter via useChatStore.getState() ou scroller avant de cibler).
- [ ] **debouncedStorage** : wrapper testé isolément mais pas de test d'intégration avec le persist/rehydrate Zustand réel. Le flush de fermeture repose sur beforeunload+pagehide+visibilitychange ; un flush explicite déclenché côté Rust avant destruction de la fenêtre serait plus sûr (à câbler avec lib.rs au prochain chantier Rust).
- [ ] **Arguments d'outils JSON invalides → {} silencieux** : openai.py:135 (hérité par grok/deepseek/openrouter/perplexity/infomaniak) et ollama.py retombent sur des arguments vides en cas de JSONDecodeError - l'outil est exécuté sans arguments au lieu de signaler. Comportement figé par test (test_grok_arguments_invalides_comportement_fige) ; à reconsidérer si un cas réel montre qu'un échec explicite serait préférable.

### Depuis v0.22.0-alpha (10/06/2026, Sprint 0 remédiation audit)
- [ ] **US-016 (perf, issu d'US-001)** : la sandbox d'exécution de code tourne désormais dans un sous-process `spawn` (sécurité). Le child ré-importe `app.services` (donc torch) à chaque génération de document → surcoût de démarrage. À régler par l'import paresseux de torch (retirer la réexport `app/services/__init__.py` + import dans la property `model` d'`embeddings.py`). Voir plan de remédiation Sprint 3.
- [ ] **CSRF `/api/shutdown` (US-005)** : l'endpoint est exempté de l'auth (sinon le shutdown graceful ne s'exécutait jamais). Risque CSRF accepté (ferme l'app, récupérable ; atténué par Private Network Access navigateur). Durcissement possible : faire signer l'appel par les 2 appelants (token lu depuis `~/.therese/.session_token`) — nécessite un changement Rust (`lib.rs`) testé au build.
- [ ] **Reste du plan de remédiation** (`~/Desktop/Plan-remediation-THERESE-2026-06-09.md`) : Sprint 1 (US-006 défenses API rate limit/MCP/fs, US-007 signature binaires + updater, US-008 résilience, US-011 backup complet) puis P2 (chiffrement DB au repos, migrations Alembic unifiées, CI bloquante).

### Dette issue de la vue Accueil (09/06/2026, branche `feat/dashboard-accueil`)
- [ ] **`setup-status` `has_email`** (`dashboard.py`) : teste la simple existence d'une ligne `EmailAccount`, pas la validité du token. Un compte dont l'OAuth a expiré reste compté « branché » et la carte de mise en route disparaît. Acceptable pour l'onboarding ; raffiner si on veut distinguer « configuré » de « connecté valide » (réutiliser la logique de `email auth status`).

### Dette issue de la revue adversariale des correctifs 0.20 (09/06/2026, branche `fix/bugs-post-0.20`)
Findings non-bloquants relevés par la revue 3 agents (les bloquants F1/F2/F3 ont été corrigés dans le commit `fix(review)`). À traiter plus tard :
- [ ] **Valider le fuseau IANA côté backend** (`calendar.py` `_create_event_google` + `update_event`) : `request.timezone` est passé tel quel à Google sans contrôle, alors que le chemin local (`local_provider.py`) le valide via `pytz` avec fallback `Europe/Paris`. Parité à rétablir (un fuseau invalide d'un client mal codé → 400 Google remonté en 500 générique). Valider via `zoneinfo.ZoneInfo(tz)`, fallback Paris.
- [ ] **Sanitiser le `body_html` des mails côté backend** au moment du cache (`email.py get_message`), comme c'est déjà fait pour les signatures (`nh3`). Aujourd'hui la sanitisation est 100 % côté front (`sanitizeEmailHtml` dans `EmailDetail`) : sûr tant que c'est le seul point de rendu, mais fragile si un futur écran affiche le corps sans repasser par le sanitizer. Défense en profondeur.
- [ ] **Contraste des libellés de statut du Kanban projets en thème clair** (`ProjectsKanban.tsx:38-43`) : couleurs Tailwind brutes `text-{green,yellow,blue,red}-400` (surtout `yellow-400`) sous le seuil WCAG AA sur fond clair. Préexistant (pattern partagé CRM/Mémoire) mais plus visible depuis le passage en vue plein écran. Remplacer par les tokens sémantiques theme-aware `text-{success,warning,info,error}`.
- [ ] **Citation des mails HTML-only** (`EmailDetail.tsx` `buildQuotedReply` + `handleForward`) : si `body_plain` est null (mail HTML pur, fréquent), la citation retombe sur le `snippet` tronqué. Dériver un texte du HTML sanitizé (helper `htmlToText`) pour citer le corps complet.
- [ ] **Re-fetch d'un mail réellement vide** (`EmailDetail.tsx`) : un message sans corps (`body_html` ET `body_plain` null : pièce jointe seule, ou erreur serveur) re-déclenche un fetch à chaque ouverture (le garde `if (body_html || body_plain) return` reste faux). Sans effet de bord néfaste, mais inutile. Un flag `bodyFetched` par message l'éliminerait.

### Depuis v0.20.0 (revue produit, 06/06/2026)
- [ ] **Quick-add calendrier local en langage naturel** : la route `POST /api/calendar/events/quick-add` ne fait du parsing NL que via l'API Google quickAdd (Google uniquement). Pour un calendrier local/CalDAV, on renvoie désormais un 400 explicite (au lieu d'un 404 "Account not found" trompeur). Feature à implémenter : un parser de dates FR souverain (stdlib ou dépendance `dateparser`) pour le quick-add local. Tant que ce n'est pas fait, l'événement local se crée via le formulaire.
- [ ] **Boucle d'outils manquante sur Grok / Gemini / Ollama** : leur `stream()` n'émet pas de `tool_call` et `continue_with_tool_results` est un stub (`yield done end_turn`). Conséquence : avec ces fournisseurs, le chat répond en texte mais ne peut pas appeler les outils (CRM, génération de documents, calendrier...). Pas de bug "réponse vide" (le stub n'est jamais atteint puisque le stream n'émet pas d'appel d'outil), contrairement à Mistral qui, lui, émettait des `tool_call` sans relance (corrigé en 0.20.0 en s'alignant sur `openai.py`). À implémenter : parsing tool_calls + continuation pour Grok (format OpenAI, port direct de `openai.py`), Ollama (format Ollama `tools`), Gemini (functionDeclarations/functionResponse).

### Depuis v0.13.2-alpha (04/06/2026)
- [ ] **`config.py:47`** (`ollama_model = "mistral:7b"`) : réglage mort (aucun usage dans le backend, confirmé au grep). À supprimer pour éviter la confusion avec le défaut Ollama dynamique (`detect_default_ollama_model`).
- [ ] **Onboarding `LLMStep.tsx`** : le plafond `max-h-48` a été retiré (BUG-100, masquait Ollama sur macOS). Si la liste des providers devient trop longue sur petit écran, préférer un défilement avec indicateur visible (gradient/affordance) plutôt qu'un conteneur court sans repère.

### Depuis v0.11.8-alpha (29/05/2026)
- [ ] **Mocker** `test_select_openai_provider` / `test_select_gemini_provider` (`tests/test_routers_images.py`, actuellement `@pytest.mark.skip`) : ils déclenchaient une génération d'image réelle (appel externe) -> hang/timeout CI. Rétablir la couverture provider via un mock du service `image_generator`.
- [ ] **27 warnings ESLint** préexistants (`react-hooks/exhaustive-deps`, `react-refresh/only-export-components`) : seuil `--max-warnings` rehaussé 26 -> 27 dans `src/frontend/package.json`. Correction = revue des dépendances de hooks composant par composant (risque de régression, à faire posément).
- [ ] Harmoniser le ton du message de confirmation `/rdv` (délègue à `execute_workspace_tool` -> format "Evenement cree : ..." sans accent et différent de `/contact`/`/projet`). Idéalement wrapper le retour calendrier + accentuer dans `workspace_tools.py`.
- [ ] Découvrabilité de la syntaxe `clé=valeur` des commandes déterministes : `handleSlashCommandSelect` (ChatInput.tsx) n'insère que le préfixe ; envisager un template/placeholder.
- Note infra : hook `pytest_sessionfinish` ajouté dans `tests/conftest.py` (force `os._exit` après la suite) pour contrer le hang de sortie dû aux threads orphelins des tests async (CI tuée à 5 min sinon).

## Backlog fonctionnel (suggestions testeurs 22/03/2026)

### P1
- [ ] Découplage données lourdes : retranscriptions hors champ description SQLite (stocker dans Qdrant ou fichiers, preview dans DB) - risque perf

### P2
- [ ] Export tâches en .ics (vEvent) + envoi par mail
- [ ] Import/export contacts VCard (.vcf) depuis fichier local ou téléphone
- [ ] UX CRM drag & drop : déplacer un contact ne doit pas forcer la création d'une activité
- [ ] Doc : pré-requis matériels SSD (DWPD/TBW) pour IA locale

### P3
- [ ] Import .ics depuis mail ou fichier local (parser icalendar)

### Refusé
- BYOS (connexion via compte ChatGPT/Claude sans API) : violation ToS, fragile, non maintenable

## Tests de non-regression

Avant chaque release :
1. `uv run pytest tests/test_regression.py -v`
2. `uv run pytest tests/ --ignore=tests/e2e -q --timeout=30`
3. Si un test echoue, NE PAS publier
4. Chaque fix critique = un test de regression

## Documentation

- `docs/CHANGELOG.md` - Historique structure par version
- `docs/DEVLOG.md` - Journal de developpement
- `docs/architecture.md` - Architecture technique detaillee
- `docs/API.md` - Documentation API
- `docs/prd-therese.md` - PRD complet
- `docs/stories/` - User stories et epics
