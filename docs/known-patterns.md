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

### `confirm()` natif dans WebView (v0.2.10)
- **NE PAS** utiliser `confirm()` ou `alert()` dans les composants React
- Bloque la WebView Tauri sur certaines plateformes
- Remplacer par des dialogs inline (mini-modal dans le composant)

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
