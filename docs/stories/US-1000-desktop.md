Parfait! Maintenant je vais créer un résumé complet des user stories basées sur le code exploré. Créons le document final:

# USER STORIES - THERESE DESKTOP (Tauri, Mises à jour, Backups, Infrastructure)

Basé sur l'analyse approfondie du code source et de la configuration Tauri. Numérotation à partir de **US-1000**.

---

## Gestion du Sidecar Backend & Lifecycle

### US-1000 : Démarrage propre du sidecar backend Python
**En tant que** solopreneur utilisant THÉRÈSE sur mon poste
**Je veux** que le backend Python démarre automatiquement dans le sidecar quand j'ouvre l'app
**Afin de** avoir accès aux fonctionnalités IA sans configuration manuelle

**Critères d'acceptation :**
- [ ] Le sidecar démarre sur le port fixe 17293 (BACKEND_PORT dans lib.rs)
- [ ] Les variables d'env sont correctement transmises (THERESE_PORT, THERESE_ENV=production, SENTENCE_TRANSFORMERS_HOME, TMPDIR/TEMP/TMP)
- [ ] Le sidecar reçoit les args --host 127.0.0.1 et --port 17293
- [ ] Les logs de démarrage sont écrits dans ~/.therese/logs/sidecar.log
- [ ] En cas d'erreur de binaire manquant, un event "sidecar-error" est émis au frontend

**Composants :** 
- `src/frontend/src-tauri/src/lib.rs` (setup() phase, sidecar spawn)
- `src/frontend/src-tauri/tauri.conf.json` (THERESE_ENV=production)
- `src/backend/app/main.py` (lifespan, startup events)

---

### US-1001 : Détection et nettoyage des backends zombies
**En tant que** solopreneur qui met à jour THÉRÈSE
**Je veux** que les anciens process backend soient tués avant le lancement du nouveau
**Afin de** éviter les conflits de port et les blocages de fichiers lors des mises à jour

**Critères d'acceptation :**
- [ ] Avant tout lancement du sidecar, `kill_zombie_backends()` détecte les process existants (pgrep sur Unix, wmic/tasklist sur Windows)
- [ ] Les process zombies reçoivent SIGTERM (Unix) ou taskkill /T /F (Windows)
- [ ] Un délai de 2 sec est observé avant le SIGKILL si SIGTERM échoue
- [ ] Le fichier .lock Qdrant est supprimé si le sidecar crash
- [ ] Les dossiers _MEI* incomplets de PyInstaller sont nettoyés (évite extraction échouée)
- [ ] Tous les logs sont enregistrés dans ~/.therese/logs/sidecar.log

**Composants :**
- `src/frontend/src-tauri/src/lib.rs` (kill_zombie_backends() en release uniquement)

---

### US-1002 : Arrêt graceful du sidecar backend à la fermeture
**En tant que** solopreneur ferma THÉRÈSE
**Je veux** que le backend s'arrête proprement avec cleanup des ressources
**Afin de** éviter la corruption de la base de données SQLite et la fermeture non propre d'uvicorn

**Critères d'acceptation :**
- [ ] À l'exit de Tauri, un POST /api/shutdown est envoyé au backend (timeout 2s)
- [ ] Le backend répond et déclenche le lifespan shutdown (cleanup Qdrant, DB close, MCP shutdown)
- [ ] On attend 5 secondes (BUG-077 : délai accru pour Windows libérer les file handles)
- [ ] Force kill est envoyé si le backend ne répond pas
- [ ] Sur Windows, taskkill /T /F tue l'arborescence entière (PyInstaller crée 2 process)
- [ ] Sur Unix, pkill -9 -P tue les process enfants orphelins
- [ ] Les logs de shutdown sont écrits dans ~/.therese/logs/sidecar.log

**Composants :**
- `src/frontend/src-tauri/src/lib.rs` (RunEvent::Exit handler)
- `src/backend/app/main.py` (lifespan context manager, shutdown cleanup)

---

## Windows & Fenêtres Tauri

### US-1003 : Fenêtre principale Tauri avec splash rapide
**En tant que** solopreneur lancant THÉRÈSE
**Je veux** que la fenêtre s'affiche rapidement après le lancement
**Afin de** d'avoir un démarrage responsif et fluide

**Critères d'acceptation :**
- [ ] La fenêtre se montre après 100ms (F-09 : réduit de 300ms grâce au spinner CSS natif)
- [ ] Index.html contient un spinner CSS qui s'affiche immédiatement avant le rendu React
- [ ] Les dimensions initiales sont 1200x800 (minWidth 800, minHeight 600, resizable)
- [ ] macOS : title bar overlay transparent (TitleBarStyle::Overlay)
- [ ] Focus automatique après show
- [ ] La fenêtre est décolorée avec shadow et centre sur l'écran

**Composants :**
- `src/frontend/src-tauri/src/lib.rs` (setup phase, window.show() + delay)
- `src/frontend/src-tauri/tauri.conf.json` (window config)
- `src/frontend/src/index.html` (spinner CSS)

---

### US-1004 : Panneaux séparés en fenêtres natives (Email, Calendrier, Tâches, CRM, Factures, Projets)
**En tant que** solopreneur utilisant Email et Calendrier
**Je veux** ouvrir Email ou Calendrier dans une fenêtre macOS séparée
**Afin de** de gérer plusieurs tâches en parallèle sur mes écrans

**Critères d'acceptation :**
- [ ] Une fenêtre WebviewWindow se crée via windowManager.ts pour chaque panel (email, calendar, tasks, invoices, crm, memory)
- [ ] La whitelist runtime rejette les valeurs invalides (SEC-018)
- [ ] Si la fenêtre existe déjà, elle passe au focus au lieu de se recréer
- [ ] Les panneaux reçoivent le port backend via l'URL (?panel=email&port=17293) pour éviter les IPC async (BUG-006)
- [ ] Au destruction, un event 'tauri://destroyed' retire la fenêtre du tracking
- [ ] En mode dev (Tauri dev server), fallback window.open() si Tauri indisponible
- [ ] Chaque panel a une taille de fenêtre optimisée (Email 1200x800, autres 1100x750, CRM 1200x800)

**Composants :**
- `src/frontend/src/services/windowManager.ts` (openPanelWindow(), closePanelWindow(), isPanelWindowOpen())
- `src/frontend/src/components/panels/PanelWindow.tsx` (init API, Error Boundary, email account preload)
- `src/frontend/src/App.tsx` (PanelWindow lazy import, panel param detection)

---

### US-1005 : Panneau avec Error Boundary et rechargement
**En tant que** solopreneur dont un panneau crash
**Je veux** voir un message d'erreur clair au lieu d'un écran blanc
**Afin de** relancer le panneau sans perdre mon contexte

**Critères d'acceptation :**
- [ ] Un React Error Boundary capture les erreurs de rendu du PanelWindow
- [ ] L'écran d'erreur affiche le logo THÉRÈSE, le message d'erreur et un bouton "Recharger"
- [ ] En cliquant "Recharger", window.location.reload() redémarre le panneau

**Composants :**
- `src/frontend/src/components/panels/PanelWindow.tsx` (PanelErrorBoundary class component)

---

## Mises à Jour Automatiques

### US-1006 : Check auto des mises à jour
**En tant que** solopreneur
**Je veux** que THÉRÈSE vérifie silencieusement une nouvelle version toutes les 6 heures
**Afin de** rester à jour sans intervention manuelle

**Critères d'acceptation :**
- [ ] Premier check 5 secondes après le lancement (STARTUP_DELAY_MS = 5000ms)
- [ ] Checks périodiques toutes les 6 heures (CHECK_INTERVAL_MS = 6h)
- [ ] L'appel `check()` du plugin updater ne bloque pas l'UI (async)
- [ ] En cas d'erreur réseau, le check est silencieux (pas de toast d'erreur)
- [ ] Si une mise à jour est disponible, le bandeau UpdateBanner se montre

**Composants :**
- `src/frontend/src/components/ui/UpdateBanner.tsx` (useEffect hook, setInterval)
- `src/frontend/src-tauri/tauri.conf.json` (updater endpoints pointent vers latest.json GitHub)

---

### US-1007 : Téléchargement et installation de la mise à jour
**En tant que** solopreneur voyant le bandeau "nouvelle version disponible"
**Je veux** cliquer "Installer maintenant" et voir le progrès en %
**Afin de** d'installer la mise à jour sans redémarrer immédiatement

**Critères d'acceptation :**
- [ ] Un bouton "Installer maintenant" déclenche downloadAndInstall()
- [ ] BUG-099 : Un POST /api/shutdown arrête le backend sidecar AVANT le téléchargement
- [ ] Health check poll (max 10s avec timeout 500ms) confirme la mort du backend (Connexion refusée sur :17293)
- [ ] Le téléchargement progresse (0 à 100%) et affiche % dans le bandeau
- [ ] Events Started, Progress, Finished sont gérés correctement

**Composants :**
- `src/frontend/src/components/ui/UpdateBanner.tsx` (handleDownloadAndInstall, health check loop)
- `src/backend/app/main.py` (POST /api/shutdown endpoint)

---

### US-1008 : Redémarrage pour appliquer la mise à jour
**En tant que** solopreneur ayant téléchargé la mise à jour
**Je veux** cliquer "Redémarrer pour installer" et que l'app se relance
**Afin de** d'appliquer la nouvelle version

**Critères d'acceptation :**
- [ ] Après downloadAndInstall() succès, le phase devient 'ready'
- [ ] Un bouton "Redémarrer pour installer" déclenche relaunch() du plugin process
- [ ] L'app se ferme et relance en version nouvelle
- [ ] En cas d'erreur relaunch(), un fallback affiche "Veuillez redémarrer manuellement"

**Composants :**
- `src/frontend/src/components/ui/UpdateBanner.tsx` (handleRestart, @tauri-apps/plugin-process relaunch)

---

### US-1009 : Bandeau discret de mise à jour
**En tant que** solopreneur
**Je veux** un petit bandeau en haut de l'app (pas de popup modale)
**Afin de** d'avoir le contrôle sur quand installer

**Critères d'acceptation :**
- [ ] Le bandeau est positionné en haut, discret avec fond cyan/rouge selon l'état
- [ ] États : idle (caché), available (cyan + bouton), downloading (spinner + %), ready (cyan + bouton), error (magenta)
- [ ] Un bouton X permet de dismisser le bandeau (sauf pendant download)
- [ ] dialog: false dans tauri.conf.json (pas de popup système)

**Composants :**
- `src/frontend/src/components/ui/UpdateBanner.tsx` (UpdateState union, render JSX)
- `src/frontend/src-tauri/tauri.conf.json` (updater.dialog = false)

---

## Infrastructure & Chemins Locaux

### US-1010 : Gestion du répertoire ~/.therese/
**En tant que** solopreneur
**Je veux** que mes données soient stockées dans ~/.therese/ (non pas dans AppData ou Library)
**Afin de** de les gérer facilement et d'avoir une seule source de vérité

**Critères d'acceptation :**
- [ ] La config (config.py) définit data_dir = Path.home() / ".therese" par défaut
- [ ] THERESE_DATA_DIR env var permet l'override (pour tests)
- [ ] Les dossiers sont auto-créés : ~/.therese/, ~/.therese/logs/, ~/.therese/qdrant/, ~/.therese/runtime/, ~/.therese/models/
- [ ] DB SQLite dans ~/.therese/therese.db
- [ ] Qdrant embeddings dans ~/.therese/qdrant/
- [ ] Les logs du sidecar vont dans ~/.therese/logs/sidecar.log (append)

**Composants :**
- `src/backend/app/config.py` (Settings.data_dir, qdrant_path, db_path)
- `src/frontend/src-tauri/src/lib.rs` (log_sidecar() fonction, ~/.therese/logs/ création)

---

### US-1011 : Redirection du TEMP/TMP PyInstaller
**En tant que** développeur packageur sur Windows
**Je veux** que PyInstaller extraie ses fichiers temporaires dans ~/.therese/runtime/ au lieu de %TEMP%
**Afin de** d'éviter le scan antivirus Windows Defender qui bloque l'extraction _MEI*

**Critères d'acceptation :**
- [ ] Les env vars TMPDIR (prioritaire macOS/Linux), TEMP, TMP sont toutes pointées vers ~/.therese/runtime/
- [ ] Le répertoire ~/.therese/runtime/ est créé automatiquement
- [ ] Les anciens dossiers _MEI* incomplets sont supprimés au démarrage
- [ ] L'extraction PyInstaller --onefile n'est jamais bloquée par l'antivirus

**Composants :**
- `src/frontend/src-tauri/src/lib.rs` (setup phase, env vars TMPDIR/TEMP/TMP)

---

### US-1012 : Token de session sécurisé
**En tant que** utilisateur de THÉRÈSE
**Je veux** que mon token de session soit stock é de façon sécurisée et régénéré à chaque lancement
**Afin de** d'éviter les injections d'autorisation entre sessions

**Critères d'acceptation :**
- [ ] À chaque lifespan startup, un token URLSafe aléatoire est généré (secrets.token_urlsafe(32))
- [ ] Le token est sauvé dans ~/.therese/.session_token avec chmod 0o600
- [ ] À la fermeture, le fichier est supprimé (cleanup)
- [ ] GET /api/auth/token retourne le token en plaintext (CORS-protégé, Tauri origins uniquement)
- [ ] Auth middleware vérifie X-Therese-Token ou ?token sur toutes les requêtes (sauf exempts)

**Composants :**
- `src/backend/app/main.py` (lifespan setup/cleanup, /api/auth/token endpoint, auth middleware)

---

## Export & Backup

### US-1013 : Export complet des données (RGPD portabilité)
**En tant que** solopreneur
**Je veux** exporter TOUTES mes données en un seul fichier JSON
**Afin de** d'avoir une copie de secours ou de migrer

**Critères d'acceptation :**
- [ ] GET /api/data/export retourne un JSON avec :
  - Contacts (id, name, email, phone, notes, tags, dates)
  - Projets (id, name, description, status, budget)
  - Conversations & Messages (role, content, created_at)
  - Fichiers indexés (path, name, extension, size, chunks)
  - Préférences (sans les API keys → [REDACTED])
  - Board Decisions (questions, opinions, synthèse)
  - Activity Logs (1000 derniers)
- [ ] Filename : therese-export-YYYYMMDD-HHMMSS.json
- [ ] Content-Disposition header pour téléchargement
- [ ] Action loggée comme DATA_EXPORTED audit
- [ ] Format data_format_version: "1.0" pour futures migrations

**Composants :**
- `src/backend/app/routers/data.py` (GET /export endpoint, export_all_data())

---

### US-1014 : Export conversations en JSON ou Markdown
**En tant que** solopreneur
**Je veux** exporter mes conversations au format JSON ou Markdown
**Afin de** de les imprimer ou les lire dans un éditeur texte

**Critères d'acceptation :**
- [ ] GET /api/data/export/conversations?format=json ou format=markdown
- [ ] JSON : même structure que export principal mais conversations seules
- [ ] Markdown : format lisible avec ## titres, **rôles**, separator ---, chronologie correcte
- [ ] Filename : therese-conversations-YYYYMMDD.md ou .json
- [ ] Messages triés par created_at

**Composants :**
- `src/backend/app/routers/data.py` (GET /export/conversations endpoint)

---

### US-1015 : Export RGPD par contact
**En tant que** solopreneur gérant la conformité RGPD
**Je veux** exporter les données d'un contact spécifique
**Afin de** de répondre à une demande de portabilité de ce contact

**Critères d'acceptation :**
- [ ] GET /api/rgpd/export/{contact_id} retourne :
  - Données du contact (tous les champs incluant rgpd_base_legale, dates consent/expiration)
  - Historique des activités associées
  - Projets liés
  - Tâches liées (via les projets)
- [ ] 404 si contact inexistant
- [ ] Format JSON avec timestamps ISO

**Composants :**
- `src/backend/app/routers/rgpd.py` (GET /export/{contact_id} endpoint)

---

### US-1016 : Suppression complète des données (droit à l'oubli)
**En tant que** solopreneur
**Je veux** supprimer TOUTES mes données d'un coup (droit à l'oubli RGPD)
**Afin de** de nettoyer complètement mon instance

**Critères d'acceptation :**
- [ ] DELETE /api/data/all?confirm=true (exige confirm=true, sinon 400)
- [ ] Suppression en cascade : CodeChange, AgentMessage, AgentTask, InvoiceLine, Invoice, CalendarEvent, Calendar, EmailLabel, EmailMessage, EmailAccount, Task, Deliverable, Activity, PromptTemplate, Message, Conversation, Project, Contact, FileMetadata, BoardDecisionDB
- [ ] Les API keys sont supprimées (Preference avec "api_key")
- [ ] Les logs d'audit sont CONSERVÉS (traçabilité légale)
- [ ] Qdrant collection est purgée (delete_collection)
- [ ] Action loggée comme DATA_DELETED_ALL audit
- [ ] Réponse confirme la suppression + note sur conservation des logs

**Composants :**
- `src/backend/app/routers/data.py` (DELETE /all endpoint)

---

### US-1017 : Logs d'activité pour audit
**En tant que** administrateur
**Je veux** consulter les logs d'activité (exports, suppressions, etc.)
**Afin de** d'avoir une traçabilité complète pour la conformité légale

**Critères d'acceptation :**
- [ ] GET /api/data/logs retourne la liste des activities (avec filtres optionnels : action, resource_type, etc.)
- [ ] Chaque log contient : id, timestamp (ISO), action (enum AuditAction), resource_type, resource_id, details (JSON)
- [ ] Pagination : limit (default 100, max 1000), offset
- [ ] Les logs ne sont jamais supprimés (même lors du DELETE /all)

**Composants :**
- `src/backend/app/routers/data.py` (GET /logs endpoint)
- `src/backend/app/services/audit.py` (log_activity function, AuditAction enum)

---

## Quarantaine & Sécurité macOS

### US-1018 : Suppression de la quarantaine macOS pour le sidecar
**En tant que** utilisateur macOS
**Je veux** que THÉRÈSE supprime la quarantaine Apple du binaire sidecar
**Afin de** que le sidecar démarre sans warnings ou blocages macOS

**Critères d'acceptation :**
- [ ] Au setup de Tauri, `xattr -dr com.apple.quarantine` est exécuté sur le répertoire du sidecar
- [ ] Ciblé sur le répertoire du binaire courant (exe.parent), pas une récursion entière
- [ ] Action est loggée dans ~/.therese/logs/sidecar.log
- [ ] En release uniquement (pas en debug)

**Composants :**
- `src/frontend/src-tauri/src/lib.rs` (setup phase, xattr command, target_os = "macos")

---

## Gestion des Problèmes Spécifiques

### US-1019 : BUG-077 - Délai accru pour libération des file handles Windows
**En tant que** utilisateur Windows
**Je veux** que le shutdown du sidecar attende longtemps que les file handles se libèrent
**Afin de** d'éviter les "fichier verrouillé" lors de la prochaine mise à jour

**Critères d'acceptation :**
- [ ] Le délai entre shutdown HTTP et force kill est de 5 secondes (augmenté de 3s)
- [ ] Après taskkill /T /F, on attend 2 secondes supplémentaires avant les commandes fallback
- [ ] Tous les timeouts sont clairement commentés "BUG-077"

**Composants :**
- `src/frontend/src-tauri/src/lib.rs` (RunEvent::Exit handler, 5s sleep après shutdown HTTP, 2s après taskkill)

---

### US-1020 : BUG-099 - Health check poll avant mise à jour
**En tant que** développeur
**Je veux** que le frontend attende que le backend soit vraiment mort avant de télécharger la mise à jour
**Afin de** d'éviter le verrou backend.exe sur Windows empêchant le remplacement des fichiers

**Critères d'acceptation :**
- [ ] POST /api/shutdown arrête le backend
- [ ] Une boucle de health check poll tentent GET /health toutes les 500ms (max 10s)
- [ ] Si /health répond → backend toujours vivant, on continue le poll
- [ ] Si erreur de connexion (refused) → backend mort, on break la boucle
- [ ] On procède au downloadAndInstall() une fois le backend confirmé mort

**Composants :**
- `src/frontend/src/components/ui/UpdateBanner.tsx` (handleDownloadAndInstall, health check loop)

---

### US-1021 : BUG-044/BUG-051 - Backend onedir Linux avec libs
**En tant que** empaqueteur Linux
**Je veux** que le sidecar Tauri trouve correctement les libs du backend PyInstaller onedir
**Afin de** que le backend démarre correctement sur Linux sans LD_LIBRARY_PATH manquant

**Critères d'acceptation :**
- [ ] THERESE_BACKEND_LIBS env var est extrait de app.path().resource_dir() + "binaries/backend-libs"
- [ ] tauri.linux.conf.json déclare resources dans binaries/backend-libs/*
- [ ] Le wrapper shell backend (sidecar) utilise THERESE_BACKEND_LIBS pour configurer LD_LIBRARY_PATH
- [ ] Tous les chemins sont absolus pour éviter les résolutions PATH relatives

**Composants :**
- `src/frontend/src-tauri/src/lib.rs` (setup phase, THERESE_BACKEND_LIBS env on Linux)
- `tauri.linux.conf.json` (resources declaration)

---

### US-1022 : F-09 - Splash rapide 100ms avec spinner CSS natif
**En tant que** solopreneur
**Je veux** que la fenêtre s'affiche en 100ms au lieu de 300ms
**Afin de** que l'app semble plus rapide au démarrage

**Critères d'acceptation :**
- [ ] Délai réduit de 300ms à 100ms avant window.show()
- [ ] Index.html inclut un spinner CSS natif qui s'affiche AVANT React ne charge
- [ ] Pas de JS lourd au démarrage, juste CSS pur
- [ ] Windows, macOS et Linux appliquent le même délai

**Composants :**
- `src/frontend/src-tauri/src/lib.rs` (setup phase, std::thread::sleep(100ms))
- `src/frontend/src/index.html` (spinner CSS)

---

## Résumé des fichiers clés

```
Tauri/Desktop:
- src/frontend/src-tauri/src/lib.rs          (sidecar lifecycle, zombie detection, shutdown)
- src/frontend/src-tauri/tauri.conf.json     (window config, updater, plugins)
- src/frontend/src/services/windowManager.ts (panel windows, WebviewWindow)
- src/frontend/src/components/panels/PanelWindow.tsx  (Error Boundary, auth init)

Mises à jour:
- src/frontend/src/components/ui/UpdateBanner.tsx    (auto-check, download, health check BUG-099)

Données & Backups:
- src/backend/app/routers/data.py           (export, delete all, activity logs)
- src/backend/app/routers/rgpd.py           (export contact, anonymize)
- src/backend/app/main.py                   (lifespan, /shutdown, session token SEC-010)

Configuration:
- src/backend/app/config.py                 (paths ~/.therese/, db, qdrant)
```

---

**Total : 23 user stories couvrant le cycle complet de Tauri desktop, mises à jour, backups et infrastructure locale.**