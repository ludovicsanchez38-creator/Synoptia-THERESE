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

## Updater : relaunch auto post-update KO, fallback manuel (v0.24, 11/06/2026)
Le cycle updater N→N+1 fonctionne (bandeau → téléchargement signé → install)
mais le redémarrage automatique ne relance pas l'app : bandeau « Redémarre
THÉRÈSE manuellement pour appliquer la mise à jour ». Cause probable :
la séquence d'arrêt (shutdown graceful sidecar 5 s + kills dans RunEvent::Exit)
interfère avec le relaunch du plugin process. L'installation est déjà faite à
ce stade : un quit/relance manuel suffit. À corriger ou assumer (le bandeau
fallback est honnête).

## pytest : os._exit du conftest avale le résumé final en sortie redirigée (11/06/2026)
Quand la sortie pytest part dans un pipe/fichier, le hook de sortie forcée
(`pytest_sessionfinish` → `os._exit`, anti-hang threads orphelins) coupe le
process AVANT l'écriture du résumé « N passed/failed ». NE PAS conclure au
vert sur l'absence de FAILED dans le tail : vérifier l'EXIT CODE et compter
les F des lignes de progression (`grep -oE "^[.sFEx]+ +\[" | fold -w1`).
A failli masquer 3 FAILED à la release 0.24. **Le plus fiable : `--junit-xml`
et parser le XML** (compte exact + noms des testcase en failure/error),
insensible à l'os._exit (utilisé pour identifier les 2 FAILED de la 0.24.5).

## Porte qualité release : lancer la SUITE COMPLÈTE, pas juste test_regression (14/06/2026)
Un fix qui modifie une constante consommée ailleurs casse des tests hors
`test_regression.py`. Ex 0.24.5 : le fix du défaut de port OAuth (`RUNTIME_PORT`
8000→settings.port) a cassé 2 tests de `test_services_oauth.py` (fixture
`redirect_uri` en `:8000` codé en dur, désormais hors `ALLOWED_REDIRECT_URIS`).
Invisible pendant la session (seul `test_regression.py` était lancé), rattrapé
par la porte qualité release. Toujours `uv run pytest tests/ --ignore=tests/e2e`
AVANT le tag (et `uv run`, jamais `.venv/bin/python` direct : package mal
installé → échecs en masse trompeurs).

## GitHub Actions : Node.js 20 déprécié, bascule forcée Node 24 le 16/06/2026
Le workflow Release émet une annotation : `actions/checkout@v4`,
`setup-node@v4`, `setup-python@v5`, `sccache-action@v0.0.7` tournent sur Node 20.
Non bloquant au 14/06 mais à mettre à jour avant le 16/06/2026 (sinon
`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` puis suppression Node 20 le 16/09/2026).

## Une remédiation de finding introduit sa propre régression (26/08/2026)
Motif observé 7 fois sur le jalon 0.48 puis **5 fois sur le seul hotfix
0.48.1** : la forme sobre des erreurs a rendu le circuit breaker aveugle aux
pannes réseau ; `raise_on_error=True` a court-circuité `record_failure` ; la
scission du hook de focus a volé le focus au resize puis cassé la
restauration ; l'exclusion des modales de l'isolation a faussé l'ordre
d'empilement ; la promotion des messages provider a ouvert une fuite du corps
des réponses à l'écran. Un correctif se relit comme « la ligne fautive est
réparée » alors qu'il change un comportement dont d'autres chemins dépendaient.
**Traiter chaque vague de remédiation comme du code neuf** : test rouge, gates
complets après CHAQUE vague, et une passe de revue sur le diff de remédiation.
Ne jamais clore un chantier sur la vague qui ferme les derniers findings.

## L'ordre de déclaration des effets React EST un contrat (26/08/2026)
React nettoie les effets dans leur ordre de déclaration. Un effet qui pose
`inert` sur une zone doit donc être déclaré AVANT celui qui restaure le focus,
sinon le focus revient dans une zone encore inerte et le navigateur le jette.
Découvert par régression pendant le hotfix 0.48.1 (`useDialogFocusTrap`, quatre
effets ordonnés : capture + focus initial / isolation / restauration / clavier).
Un commentaire au-dessus de chaque effet rappelle pourquoi l'ordre compte.

## Un z-index ne compte que sur un élément positionné (26/08/2026)
Sur `position: static`, un `z-index` n'a **aucun** effet visuel. Un calcul de
z-order qui remonte les ancêtres en prenant le premier z-index numérique
rencontré se trompe : il faut ignorer les ancêtres statiques. Trouvé en
auto-contrôle sur le hotfix 0.48.1, après que la revue avait déjà invalidé une
première hypothèse (« l'ordre d'ouverture donne l'ordre d'empilement », faux).
Le z-order réel = z-index effectif d'un élément positionné, puis ordre du DOM.

## jsdom n'implémente pas `inert` (26/08/2026)
Un test vitest ne peut pas prouver qu'une zone est réellement inerte : jsdom
pose l'attribut sans en appliquer la sémantique (clics, focus et scroll
continuent de fonctionner). Les tests vérifient donc la POSE de l'attribut sur
les bons nœuds ; la vérification du comportement réel demande un navigateur.

## Une correction d'ordre ne suffit pas s'il reste un await entre (26/08/2026)
Corrigé une fois : `terminer()` retirait l'adaptateur du registre AVANT
d'écrire l'état terminal, donc un commit en échec laissait une tâche active
et inannulable. La correction (écrire d'abord) a ouvert la faille inverse :
sortir du contexte de session EST un `await`, et une demande d'arrêt passée
dans cette fenêtre coupait un producteur déjà terminé, en répondant
« arrêté » alors que la base disait `done`. **En asyncio, deux opérations ne
sont solidaires que s'il n'y a AUCUN point d'attente entre elles** : le
retrait vit désormais collé au `await session.commit()`, à l'intérieur du
`async with`. Le remonter d'un cran rouvre la fenêtre.

## Un message d'erreur français n'est pas reconnu par une détection anglaise (26/08/2026)
`_is_provider_outage()` cherche « API error: {code} » et des marqueurs. Le
chemin HTTP d'OpenRouter produisait « Erreur API OpenRouter (503) » : jamais
reconnu, donc jamais compté, donc pas de repli sur un autre fournisseur. Même
piège sur les formes sobres introduites pour fermer une fuite : assainir un
message casse sa CLASSIFICATION si l'on ne vérifie pas que la détection le
reconnaît encore. **Tout message d'erreur destiné au circuit breaker doit
être testé à travers `_is_provider_outage`, pas relu à l'œil.**

## Gemini 3 : la thought signature est obligatoire au rejeu (26/08/2026)
Un modèle Gemini 3 refuse (400) un tour d'outils dont la `thoughtSignature`
manque - « you must pass back thought signatures during function calling ».
C'est un champ du PART, à côté de `functionCall`, et seul le PREMIER appel
d'une étape la porte. La jeter casse tout usage d'outil au SECOND tour, sans
rien casser au premier : le bug est invisible sur un test à un seul tour.
En revanche `temperature` n'est PAS rejetée par Gemini 3, elle est acceptée
puis ignorée - un guide de migration qui dit « strip X » ne dit pas que X
provoque une erreur. Vérifier la conséquence, pas seulement la consigne.

## Le bump de version rend obsolete l'index des noms (29/08/2026)

`docs/INDEX-DES-NOMS.md` est genere par `scripts/index-des-noms.mjs` et porte le
numero de version dans son titre. `tests/test_index_des_noms.py` verifie que le
fichier commite est bien celui que le code produit.

Consequence : tout bump de version cassait la CI backend, et le tag etait deja
pousse au moment ou ca se voyait. Une suite locale verte lancee AVANT le bump ne
dit rien de l'etat d'apres.

Corrige a la 0.57.0 : `scripts/bump-version.sh` regenere l'index. Si un autre
fichier genere venait a porter la version, l'ajouter au meme endroit.

## CI mypy : `uv sync --dev` peut épuiser le timeout en téléchargeant CUDA (04/09/2026)

Le job `Typage (mypy, baseline)` installe tout le groupe de développement avec
`uv sync --dev`. Sur un runner Linux sans cache UV chaud, cette commande peut
télécharger Torch et plusieurs gigaoctets de paquets NVIDIA/CUDA sans rapport
avec le contrôle de types. Le run `33878695650` a ainsi été annulé au bout de
dix minutes pendant l'installation, avant même le démarrage de mypy, alors que
les mêmes sources avaient passé le CI `33869741967` et le gate de release
`33873778753`.

Ne pas classer ce cas comme un échec de typage sans lire les étapes et les logs.
À corriger : limiter ce job aux dépendances nécessaires à mypy ou installer la
variante CPU de Torch, puis dimensionner le timeout sur l'installation réelle.

Correction retenue le 04/09/2026 après la release : le job exporte le lockfile
avec `--prune torch`, installe cette liste sans résoudre à nouveau les
dépendances, puis ajoute la roue `torch==2.9.1` CPU déjà utilisée par le build.
L'export Linux ne contient ainsi aucun paquet `nvidia-*` ni `triton`.
Les dépendances métier restent présentes car leur suppression change réellement
le cliquet : 987 erreurs avec les paquets installés contre 1 595 avec
`--no-site-packages` sur macOS. `uv run --no-sync` empêche enfin la commande
mypy de resynchroniser le projet complet.

## Windows : le harnais B-306 peut dépasser 300 s au teardown (04/09/2026)

Le test `test_le_dossier_src_backend_tests_tient_seul` lance tout
`src/backend/tests` dans un sous-processus borné à 300 secondes. Sur le premier
essai du run `33878695584`, la sortie avait atteint 99 % mais le sous-processus
n'avait pas rendu la main avant le plafond : un seul échec sur 3 387 tests,
aucune erreur. La seconde tentative du même run est verte avec les mêmes 3 387
tests, zéro échec, zéro erreur et 22 tests ignorés.

Lire le JUnit avant de parler de régression. Un rerun unique peut confirmer le
caractère intermittent, mais il ne remplace pas le traitement de la cause :
identifier le teardown qui retient le processus Windows et mesurer séparément
le temps d'exécution et le temps de sortie. Ne pas relever le timeout par
réflexe, car B-306 doit justement empêcher un blocage sans fin.

Correction retenue le 04/09/2026 après la release : le workflow Windows lance
`src/backend/tests/` directement dans un job autonome, ce qui prouve son
autonomie sans `tests/conftest.py`. La suite principale lance en parallèle
`tests/` en excluant uniquement `test_le_dossier_src_backend_tests_tient_seul`,
devenu redondant ; les collectes autonomes fichier par fichier restent actives.
Chaque racine est donc exécutée une seule fois et produit son propre rapport
JUnit.

Le premier essai de ce découpage, run `33900470184`, a affiché les 175 tests à
100 % en 8 min 03, puis GitHub a coupé l'étape exactement à sa limite de huit
minutes avant le résumé JUnit. Le budget du job autonome passe à dix minutes,
avec un plafond de 60 secondes par test. Il reste ainsi borné et ne consomme
plus le budget de la suite principale grâce à l'exécution parallèle.

## Binaires lourds : garde pre-commit locale de 3 Mo, captures en JPEG hors PNG (05/09/2026)

L'historique portait 56 Mo de captures PNG du guide de présentation (cinq commits
des 03-04/09) et 21 Mo de vidéos Playwright `src/frontend/test-results/*.webm`
entrées le 15/07 par un commit automatique `wip(auto)` et retirées deux jours
plus tard. Le `.git` pesait 184 Mo pour un dépôt de code.

Règles posées :

- `docs/presentation/_build/shots-web/` (JPEG 1300 px, q78, 9,5 Mo pour 92
  captures) est la source versionnée du guide ; `shots/` (PNG) est ignoré et
  les originaux vivent hors dépôt sur le Mac
  (`~/.claude/docs/therese-guide-0.66-captures-png/`). `build.sh` ne
  reconvertit que si des PNG sont présents.
- `_build/guide.pdf` n'est plus suivi : le livrable est
  `docs/presentation/THERESE-0.66-guide-de-presentation.pdf`, seul.
- Une garde locale `.git/hooks/pre-commit` sur le Mac de Ludo refuse tout
  fichier indexé de plus de 3 Mo (`ALLOW_BIG=1 git commit …` pour un
  livrable voulu, comme le PDF du guide). Elle s'applique aussi au commit
  automatique de fin de tour, origine des deux accidents.
- Les fichiers AppleDouble `._*` sont ignorés à la racine.

La purge de l'historique (réécriture, force push, re-clone par Katia,
Zézette et Codex) reste une décision de Ludo.

## Historique réécrit le 05/09/2026 : tout clone antérieur se resynchronise par fetch + reset, jamais par pull

Purge validée par Ludo (`git filter-repo`, sauvegarde miroir complète conservée sur le
Mac dans `Synoptia-THERESE-avant-purge-20260905.git`) : captures PNG du guide (56 Mo),
vidéos Playwright `src/frontend/test-results` (21 Mo) et quatre anciennes versions du
PDF (32 Mo). Le dépôt passe de 161 à 65 Mo. Périmètre : les 48 refs postérieures au
13/07 (main, 8 branches, 39 tags depuis `v0.40.0-alpha`) ; les 145 refs antérieures
gardent leurs SHA. Les arbres sont identiques, seuls les identifiants de commits
changent (`main` : 3935a36e devient 75fe7161, `v0.66.1-alpha` : 79d51c25 devient
d2d804d4). Les releases GitHub restent rattachées à leurs tags et à leurs dix
assets. Un commit vide a été élagué (`07a5143c`, wip automatique du 03/09 qui ne
touchait que des captures).

Résiduel connu : 14,6 Mo de vidéos dans `test-results/` à la racine, entrées le
07/04 et retirées le 14/07 ; les purger aurait réécrit tous les tags depuis avril.
Les refs `refs/pull/*` de GitHub gardent l'ancien historique côté serveur ; sans
effet sur les clones.

Sur un clone existant : `git fetch --prune --prune-tags --force origin` puis
`git reset --hard origin/main` (ou `git switch -C main origin/main`), jamais
`git pull` qui fusionnerait les deux historiques. Clones resynchronisés le 05/09 :
Mac, Katia (`~/therese-v2` sur le VPS Agents), Codex.
