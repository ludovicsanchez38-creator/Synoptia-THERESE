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
