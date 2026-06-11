# Known Patterns - THÉRÈSE

> Patterns identifiés lors des audits de release. Ce fichier est lu par les agents d'audit pour éviter de re-valider des anti-patterns déjà connus.

## Patterns acceptés (ne pas remonter comme warning)

### `navigator.platform` (depuis v0.2.11)
- **Contexte** : Utilisé dans 5+ fichiers frontend pour détecter macOS vs Windows/Linux
- **Statut** : Déprécié par les standards web, mais seul choix fiable sur Tauri (WKWebView ne supporte pas `navigator.userAgentData`)
- **Action** : Centraliser dans un helper `isMac()` / `isWindows()` (backlog)
- **Ne pas bloquer** : tant que Tauri ne fournit pas d'alternative

### `createPortal(document.body)` (depuis v0.2.9)
- **Contexte** : Utilisé pour échapper au stacking context créé par Framer Motion (CSS transform sur les parents)
- **Fichiers** : `ResponseGeneratorModal.tsx`, `EmailSetupWizard.tsx`
- **Statut** : Fonctionnel, idéalement utiliser un `<div id="portal-root">`
- **Ne pas bloquer** : pattern courant et sans risque

### Z-index non centralisés (depuis v0.1.7)
- **Contexte** : 20+ composants utilisent z-50, quelques-uns z-[60] ou z-[70]
- **Action** : Créer un fichier de constantes (backlog)
- **Ne pas bloquer** : pas de conflit fonctionnel constaté

### `|| true` sur audits CI (depuis v0.6.2)
- **Contexte** : `npm audit` et `pip-audit` dans le job `security-audit` utilisent `|| true`
- **Statut** : Intentionnel pour l'alpha (informatif, pas bloquant)
- **Action** : Retirer `|| true` quand les dépendances sont assainies
- **Ne pas bloquer** : choix conscient, planifié P1

### hljs Light avec 9 langages (depuis v0.6.2)
- **Contexte** : Migration de Prism (tous langages) vers hljs Light (python, js, ts, bash, json, css, xml, yaml, sql)
- **Statut** : Gain -236KB bundle. Langages manquants : rust, go, markdown, dockerfile
- **Action** : Ajouter les langages manquants au fur et à mesure (P1)
- **Ne pas bloquer** : les langages principaux de la cible TPE/solopreneurs sont couverts

### DialogShell overlay convention (depuis v0.6.2)
- **Contexte** : Les modales utilisent `bg-black/60 backdrop-blur-sm` comme standard
- **Statut** : DialogShell aligné sur cette convention
- **Action** : Migrer progressivement les 13 modales restantes vers DialogShell
- **Ne pas bloquer** : migration en cours, les attributs ARIA sont déjà ajoutés

## Anti-patterns à surveiller

### Excludes torch dans PyInstaller (v0.1.7 - CASSÉ)
- **NE JAMAIS** exclure de sous-modules torch dans `backend.spec`
- torch les importe tous à l'init, l'exclusion casse le sidecar sur toutes les plateformes
- Corrigé en v0.1.8

### `confirm()` natif dans WebView (v0.2.10 - PARTIELLEMENT CORRIGÉ v0.6.4)
- **NE PAS** utiliser `confirm()` ou `alert()` dans les composants React
- Bloque la WebView Tauri sur certaines plateformes
- Remplacer par des dialogs inline (mini-modal dans le composant)
- Corrigé dans InvoicesPanel.tsx (v0.6.4, PR #45) : dialogue React avec state
- Reste : `confirm()` dans `handleSendEmail` (InvoicesPanel L88), `handleMarkPaid` (InvoiceForm L153)

### Port hardcodé (v0.1.2)
- Le port backend est fixé à 17293 depuis v0.1.19
- Ne jamais revenir à un port dynamique (source de bugs IPC)

### Filtre fichiers frontend != capacités backend (v0.2.12)
- **NE PAS** ajouter d'extensions au filtre ChatInput sans vérifier que `extract_text()` les supporte
- Extensions supportées (v0.2.12) : `.txt`, `.md`, `.pdf`, `.docx`, `.xlsx`, `.json`, `.csv` + fichiers code
- `.doc`, `.xls`, `.ods`, `.pptx`, `.ppt`, `.odt` ne sont PAS supportés
- Corrigé en v0.2.12 (PR #20)

### `extract_text()` avale les exceptions (v0.2.12 - DETTE)
- `file_parser.py` a un `except Exception` qui retourne `None` au lieu de propager
- Le caller (files.py) ne peut pas distinguer "format non supporté" de "erreur d'extraction"
- À corriger : propager les exceptions ou retourner un message explicite

### `asyncio.get_event_loop()` déprécié (v0.2.12 - CORRIGÉ)
- **NE PLUS** utiliser `get_event_loop()` dans le backend
- Remplacé par `get_running_loop()` dans imap_smtp_provider.py (PR #19) et caldav_provider.py (PR #23)
- Test de régression scanne tout `src/backend/app/` pour empêcher toute régression

### Dialogue suppression sans focus trap (v0.6.4 - DETTE)
- `InvoicesPanel.tsx` : le dialogue de confirmation de suppression n'a pas de focus trap ni de handler Escape
- Le composant `DialogShell.tsx` fournit ces fonctionnalités - à utiliser ou reproduire
- Non bloquant fonctionnellement, mais manque WCAG 2.1 (SC 2.1.2 / SC 2.4.3)

### Statuts projet front/back désalignés (v0.6.4 - DETTE)
- `ProjectModal.tsx` propose 3 statuts (active, on_hold, completed)
- `ProjectsKanban.tsx` affiche 4 colonnes (+ cancelled)
- Backend accepte 4 statuts via `VALID_PROJECT_STATUSES`
- Les projets existants "cancelled" apparaissent sans statut visible dans le formulaire d'édition
- À harmoniser : soit garder "cancelled" dans le modal, soit le retirer du Kanban + migration

### Dual state décimaux InvoiceForm (v0.7.4 - ACCEPTÉ)
- `lineInputs` (string[]) pour l'affichage + `lines` (InvoiceLineRequest[]) pour les données
- Les valeurs numériques dans `lines[i].quantity` ne sont jamais mises à jour lors de la saisie
- La normalisation se fait à la soumission via `parseDecimalDraft()`
- **Ne pas bloquer** : pattern fonctionnel mais fragile. Ne pas lire `lines[i].quantity` directement

### alert() dans les formulaires (v0.7.4 - DETTE)
- 6 occurrences de `alert()` dans `InvoiceForm.tsx`
- Anti-pattern dans WebView Tauri (bloque le thread, style natif non dark mode)
- **Ne pas bloquer** : acceptable en alpha, à remplacer par validation inline

### PATH enrichi dupliqué dans mcp.py (v0.10.8 - DETTE)
- 3 copies de la logique de résolution PATH enrichi (nvm, fnm, volta, homebrew) dans `mcp.py`
- À extraire dans une fonction utilitaire commune
- **Ne pas bloquer** : fonctionnel, pas de risque

### String matching erreurs email (v0.10.8 - DETTE)
- `workspace_tools.py` : détection auth/connexion via str(e).lower() contenant "authentication", "login", "connection"
- Fragile si provider renvoie des messages en français ou si les messages changent entre versions
- Préférer le catch de `smtplib.SMTPAuthenticationError` ou les codes SMTP (535, 530)
- **Ne pas bloquer** : le fallback est un message générique, pas de crash

### Fix d'accent sur un libellé peut casser un test (v0.12.0)
- **Contexte** : ajouter un accent à un libellé affiché (ex. `Creer` → `Créer`) change l'accessible name. Un test qui requête par `getByRole('button', { name: /Cre/i })` ne matche plus (`é` casse la séquence `Cre`).
- **Cas réel** : `InvoiceForm.test.tsx` requête `/Cre/i` → corrigé en `/Créer/i`.
- **Action** : après tout fix d'accent sur un libellé, grep les tests pour les requêtes `getByRole/getByText/findBy*` ciblant l'ancien texte et les aligner.
- **Ne pas bloquer** : c'est une conséquence attendue, pas un anti-pattern du code source.

### La CI backend exécute le répertoire `tests/` RACINE, pas `src/backend/tests/` (v0.13.0)
- **Contexte** : le job `Tests Backend (Python)` de `ci.yml` n'a PAS de `working-directory` → il tourne depuis la racine du repo et lance `pytest tests/` = le `tests/` racine (~1063 tests, dont `test_regression.py`, `test_services_llm.py`, `test_routers_*`). Le dossier `src/backend/tests/` (~149 tests) n'est PAS exécuté par ce job.
- **Piège** : modifier/valider `src/backend/tests/` ne reflète pas la CI. Toujours viser `tests/` (racine) pour reproduire les échecs CI backend.
- **Reproduire en local** : `cd <repo> && THERESE_ENV=test TRANSFORMERS_OFFLINE=1 uv run pytest tests/ --ignore=tests/e2e -q` (les tests `async_client` peuvent demander des services ; les tests unitaires purs tournent seuls).
- **Aggravant** : le job est parfois tué au teardown (threads orphelins) AVANT d'imprimer la section FAILURES + le résumé → les échecs sont invisibles dans le log. Un hook `pytest_runtest_logreport` qui imprime `[TEST-FAILED] <nodeid>` sur stderr (flush) aide (présent dans `src/backend/tests/conftest.py`, à ajouter aussi côté racine si besoin).

## Release : 403 « Resource not accessible by integration » à la création de release (11/06/2026)

Depuis ~11/06/2026, tauri-action n'arrive plus à CRÉER la release avec le
GITHUB_TOKEN (403 sur POST /releases), alors que `permissions: contents: write`
est identique aux runs qui passaient la veille (durcissement côté GitHub).
L'UPLOAD d'assets sur une release existante fonctionne, lui.

**Contournement validé** : pré-créer la draft via `gh release create vX.Y.Z-alpha
--draft --prerelease --notes-file ...` (auth locale) AVANT le build ou avant un
`gh run rerun --failed` - tauri-action prend alors le chemin « draft trouvée ->
upload ». À intégrer au début du skill /release-therese (créer la draft juste
après le push du tag).

## CI job rust : factices requis pour tauri-codegen (11/06/2026)

`cargo clippy` sur src-tauri exige : (1) le sidecar externalBin
(`binaries/backend-<triple>`), (2) le dossier `../dist` avec au moins un
fichier (feature custom-protocol par défaut), (3) les globs de
`tauri.linux.conf.json` - AUTO-chargé sur Linux - satisfaits
(`binaries/backend-libs/` + `_internal/`), et (4) `libasound2-dev` dans
les paquets apt (alsa-sys du plugin micro).
