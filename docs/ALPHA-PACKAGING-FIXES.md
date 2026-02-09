# THÉRÈSE Alpha - Corrections Packaging & Distribution

> Document de suivi des bugs et corrections à apporter avant distribution aux testeurs alpha.
> Créé le 9 février 2026 - Dernière mise à jour : 9 février 2026

---

## Bugs critiques (bloquent le lancement)

### 1. scipy manquant dans le sidecar PyInstaller

- **Statut** : CORRIGÉ (backend.spec)
- **Symptôme** : L'app affiche "Le backend ne répond pas" puis timeout
- **Cause** : `scipy` était dans la liste `excludes` du `backend.spec` alors que `sentence_transformers -> sklearn -> scipy` en a besoin
- **Erreur** : `ModuleNotFoundError: No module named 'scipy'`
- **Fix** : Retiré `scipy` des excludes, ajouté `scipy` et `sklearn` dans `hidden_imports`
- **Fichier** : `src/backend/backend.spec` (lignes 47-48 et 112)
- **Impact** : Aucune plateforme ne pouvait lancer l'app (macOS, Windows, Linux)
- **Validation** : Rebuilder le sidecar et vérifier que le backend démarre

### 2. Build Linux échoue (OOM / disque plein)

- **Statut** : EN COURS - contourné (release sans Linux)
- **Symptôme** : Le runner GitHub Actions Linux perd la connexion ou manque d'espace
- **Cause** : Le runner a 7 Go RAM et ~30 Go disque libre après nettoyage. Le sidecar PyInstaller (195 Mo) + Rust compilation dépassent les limites
- **Corrections appliquées** :
  - Nettoyage agressif du disque (dotnet, android, ghc, docker prune)
  - Swap 4 Go sur `/mnt/swapfile`
  - `CARGO_BUILD_JOBS=3` pour limiter la mémoire Rust
  - Suppression de `dist/`, `build/`, `.venv` après copie du sidecar
  - `save-if: true` sur le cache Rust pour persister même en cas d'échec
- **TODO** : Tester le prochain build (le cache Rust persisté devrait accélérer)
- **Alternative** : Utiliser un runner self-hosted ou un runner large (4 CPU, 16 Go)

---

## Bugs UX (n'empêchent pas le lancement mais dégradent l'expérience)

### 3. macOS Gatekeeper bloque l'app ("THÉRÈSE est endommagé")

- **Statut** : DOCUMENTÉ (instructions sur la page alpha)
- **Symptôme** : "THÉRÈSE est endommagé et ne peut pas être ouvert"
- **Cause** : App non signée (pas de certificat Apple Developer)
- **Fix utilisateur** : `xattr -cr /Applications/THÉRÈSE.app` dans le Terminal
- **Fix long terme** : Apple Developer Program (99 USD/an) + code signing dans le CI
- **Page alpha** : Instructions ajoutées sur synoptia.fr/therese/alpha/

### 4. Windows - Faux positif antivirus

- **Statut** : DOCUMENTÉ (instructions sur la page alpha)
- **Symptôme** : Windows Defender ou antivirus bloque le .exe
- **Cause** : PyInstaller est régulièrement flaggé comme suspect par les antivirus
- **Fix utilisateur** : Ajouter une exclusion dans l'antivirus
- **Fix long terme** : Certificat de signature code Windows (70-300 EUR/an)

### 5. Téléchargement sans feedback visuel

- **Statut** : CORRIGÉ (page alpha)
- **Symptôme** : Clic sur "Télécharger" sans retour visuel
- **Fix** : Toast notification "Téléchargement lancé !" ajouté sur la page alpha

### 6. Liens de téléchargement en 404 si non connecté GitHub

- **Statut** : CONNU - en attente
- **Symptôme** : Les liens GitHub Releases retournent 404 pour les utilisateurs non connectés
- **Cause** : Le repo est privé
- **Fix** : Passer le repo en public OU héberger les binaires ailleurs (S3, CDN)
- **TODO** : Décider de la stratégie de distribution

---

## Améliorations à faire avant distribution large

### 7. Onboarding ne s'affiche pas après purge des données

- **Statut** : CORRIGÉ (diagnostic)
- **Symptôme** : Après suppression de `~/.therese/`, l'onboarding ne réapparaît pas
- **Cause** : Le backend garde la DB SQLite en mémoire (comportement Unix). Même après suppression du fichier, le processus conserve les données
- **Fix** : Redémarrer le backend (ou THÉRÈSE) après purge
- **TODO** : Ajouter un bouton "Réinitialiser" dans les paramètres qui :
  1. Purge `~/.therese/`
  2. Efface le localStorage WebKit
  3. Redémarre le sidecar
  4. Relance l'onboarding

### 8. Modèle LLM par défaut à vérifier

- **Statut** : À VÉRIFIER
- **Config** : `claude-sonnet-4-20250514` dans `src/backend/app/config.py`
- **TODO** : Vérifier que cet ID est toujours valide chez Anthropic
- **Risque** : Si le modèle n'existe plus, le premier message de chat échouera

### 9. WebView2 sur Windows

- **Statut** : À DOCUMENTER
- **Symptôme potentiel** : Écran blanc au lancement sur Windows
- **Cause** : Tauri 2.0 nécessite Microsoft Edge WebView2 Runtime
- **Fix** : Le mode `downloadBootstrapper` l'installe automatiquement, mais documenter au cas où
- **TODO** : Ajouter une note dans les instructions d'installation Windows

### 10. Mise à jour automatique

- **Statut** : NON IMPLÉMENTÉ
- **Impact** : Les testeurs devront manuellement télécharger chaque nouvelle version
- **TODO** : Intégrer `tauri-plugin-updater` avec endpoint de vérification
- **Priorité** : Moyenne (acceptable pour l'alpha)

### 11. Health check sans timeout

- **Statut** : À CORRIGER
- **Symptôme potentiel** : L'endpoint `/health` peut bloquer si Qdrant ou la DB est lente
- **Cause** : Les vérifications de service dans le health check n'ont pas de timeout
- **Fix** : Ajouter `asyncio.wait_for(check, timeout=3.0)` sur chaque vérification
- **Fichier** : `src/backend/app/main.py` (endpoint health)

### 12. Clé API requise pour utiliser THÉRÈSE

- **Statut** : BLOQUANT pour les testeurs non-techniques
- **Symptôme** : Les testeurs sans clé API Anthropic/OpenAI ne peuvent rien faire
- **Options** :
  - A) Proxy API partagé (Ludo paie, testeurs utilisent)
  - B) Clé API de test avec quota limité
  - C) Support Ollama local (gratuit, mais nécessite installation)
  - D) Documentation pas-à-pas pour obtenir une clé API gratuite
- **TODO** : Choisir une stratégie et l'implémenter

---

### 13. Email : "Impossible de charger les messages" au premier lancement

- **Statut** : CORRIGÉ (EmailList.tsx)
- **Symptôme** : Le panneau Email affiche "Impossible de charger les messages" à la première ouverture, fonctionne au deuxième
- **Cause** : Race condition - `EmailList` charge les messages avant que le token OAuth Gmail soit prêt
- **Fix** : Retry automatique (3 tentatives, délai croissant 1.5s/3s/4.5s) dans `EmailList.loadMessages()`
- **Fichier** : `src/frontend/src/components/email/EmailList.tsx`

### 14. CRM Sync Google Sheets : "Failed to initiate OAuth: Bad Request"

- **Statut** : CORRIGÉ (crm.py)
- **Symptôme** : Clic sur "Connecter Google Sheets" dans Paramètres > CRM Sync retourne "Bad Request"
- **Cause** : L'endpoint `/api/crm/sync/connect` cherchait les credentials Google OAuth dans le serveur MCP ou les Preferences, mais aucun des deux n'est configuré sur une install fraîche. Le module Email stocke ses credentials dans `EmailAccount`, pas dans `Preferences`.
- **Fix (3 parties)** :
  1. Ajouté un 3e fallback dans `initiate_sheets_oauth()` qui réutilise les credentials d'un `EmailAccount` Gmail existant
  2. Ajouté les redirect URIs CRM (`/api/crm/sync/callback`) dans la whitelist `ALLOWED_REDIRECT_URIS` du service OAuth
  3. Ajouté `/api/crm/sync/callback` dans les `exempt_paths` du middleware d'auth (le callback vient du navigateur, pas de l'app)
- **Prérequis** : L'utilisateur doit avoir configuré son email Gmail dans THÉRÈSE avant de pouvoir connecter Google Sheets
- **Fichiers** : `src/backend/app/routers/crm.py` + `src/backend/app/services/oauth.py` + `src/backend/app/main.py`
- **Message d'erreur amélioré** : Indique maintenant de configurer Gmail d'abord

### 15. window.open() ne fonctionne pas dans Tauri WebView

- **Statut** : CORRIGÉ (CRMSyncPanel.tsx, EmailConnect.tsx)
- **Symptôme** : Le message "Autorisez l'accès dans le navigateur" apparaît mais rien ne s'ouvre dans le navigateur
- **Cause** : `window.open('...', '_blank')` est bloqué dans une WebView Tauri. Il faut utiliser `open()` de `@tauri-apps/plugin-shell`
- **Fix** : Remplacé `window.open()` par `import('@tauri-apps/plugin-shell').then(m => m.open(url))` avec fallback
- **Fichiers** : `src/frontend/src/components/settings/CRMSyncPanel.tsx`, `src/frontend/src/components/email/EmailConnect.tsx`
- **Aussi concerné mais déjà correct** : `EmailPanel.tsx`, `CalendarPanel.tsx`, `VerifyStep.tsx`

---

## Checklist avant publication d'une release

- [ ] `scipy` et `sklearn` dans hidden_imports du backend.spec
- [ ] Sidecar testé manuellement : `./backend --host 127.0.0.1 --port 8000`
- [ ] Endpoint `/health` retourne `{"status":"healthy"}`
- [ ] Endpoint `/api/config/onboarding-complete` retourne `{"completed":false}` sur base vierge
- [ ] Onboarding wizard s'affiche au premier lancement
- [ ] Les 6 étapes de l'onboarding se complètent sans erreur
- [ ] Chat fonctionne avec une clé API valide
- [ ] macOS : `xattr -cr` documenté dans les notes de release
- [ ] Windows : Exclusion antivirus documentée
- [ ] Liens de téléchargement accessibles (repo public ou hébergement alternatif)
- [ ] Version dans `tauri.conf.json` et `pyproject.toml` synchronisées

---

## Fichiers modifiés lors de cet audit

| Fichier | Modification |
|---------|-------------|
| `src/backend/backend.spec` | Retiré `scipy` des excludes, ajouté `scipy`/`sklearn` aux imports |
| `.github/workflows/release.yml` | Swap, cleanup, `CARGO_BUILD_JOBS`, `save-if: true` |
| `/tmp/synoptia-seo/site/therese/alpha/index.html` | Toast download, instructions macOS/Windows |
| `src/frontend/src/services/api/` | Migration monolithique -> 13 modules |
| `src/frontend/src-tauri/src/lib.rs` | Fix Rust E0597 (MutexGuard lifetime) |
| `src/backend/app/routers/crm.py` | Fallback credentials Google depuis EmailAccount |
| `src/backend/app/services/oauth.py` | Ajout redirect URIs CRM dans whitelist |
| `src/backend/app/main.py` | Ajout `/api/crm/sync/callback` dans exempt_paths auth |
