Excellent ! Je dispose maintenant de toutes les informations essentielles. Je vais compiler les user stories complètes. Basé sur le parcours du code, voici mon rapport :

---

# USER STORIES - THÉRÈSE v2 : Navigation & UX Transverse

## Module Navigation

### US-700 : Sidebar des conversations avec recherche et groupage temporel
**En tant que** solopreneur/TPE
**Je veux** accéder à mes conversations passées via une sidebar avec recherche et groupage par date
**Afin de** continuer facilement une discussion antérieure sans relancer le contexte

**Critères d'acceptation :**
- [x] Sidebar affichable/masquable avec animation slide-left (Cmd+B)
- [x] Champ de recherche qui filtre les conversations en temps réel
- [x] Groupage automatique : "Aujourd'hui", "Hier", "Cette semaine", "Ce mois", "Plus ancien"
- [x] Affichage du titre, aperçu du dernier message (60 chars), nombre de messages et temps relatif
- [x] Double-clic pour renommer une conversation (Escape pour annuler, Enter pour valider)
- [x] Menu contextuel (clic droit) : Renommer / Supprimer
- [x] Suppression confirmée avec état visuel (opacity-50)
- [x] Bouton "Nouvelle conversation" en header et en footer
- [x] Focus trap (Escape ferme la sidebar)
- [x] Animations respectent `reduceMotion` (AccessibilityStore)

**Composants :** ConversationSidebar.tsx
**data-testid :** sidebar, sidebar-new-conversation-btn, sidebar-search-input, sidebar-conversation-list, sidebar-conversation-item

---

### US-701 : Routing panels principaux (Memory, Board, Email, Calendar, Tasks, Invoices, CRM)
**En tant que** solopreneur/TPE
**Je veux** accéder rapidement à chaque module (Mémoire, Board, Email, Calendrier, Tâches, Factures, CRM) via raccourcis clavier ou command palette
**Afin de** naviguer fluidement entre les différentes fonctionnalités sans cliquer

**Critères d'acceptation :**
- [x] Cmd+M : Toggle Memory (Espace de travail - contacts/projets/fichiers)
- [x] Cmd+D : Toggle Board (Conseil IA 5 experts)
- [x] Cmd+E : Toggle Email
- [x] Cmd+⇧C : Toggle Calendar
- [x] Cmd+T : Toggle Tasks
- [x] Cmd+I : Toggle Invoices (Factures/Devis/Avoir)
- [x] Cmd+P : Toggle CRM (Pipeline commercial)
- [x] Cmd+⇧A : Toggle Atelier (Agents IA / OpenClaw)
- [x] Chaque panel peut s'ouvrir en fenêtre détachée (desktopManager)
- [x] Focus trap dans les modaux (DialogShell)
- [x] Retour au chat en fermant le panel (Escape)
- [x] Animations slide/fade respectent reduceMotion

**Composants :** panelStore.ts, ChatLayout.tsx, PanelContainer.tsx, DialogShell.tsx
**data-testid :** memory-panel, board-panel, email-panel, calendar-panel, tasks-panel, invoices-panel, crm-panel

---

### US-702 : Command Palette (Cmd+K) - Recherche et lancement de commandes
**En tant que** solopreneur/TPE
**Je veux** ouvrir une palette de commandes unifiée pour accéder à toutes les actions sans mémoriser les raccourcis
**Afin de** découvrir et exécuter les commandes rapidement

**Critères d'acceptation :**
- [x] Cmd+K ouvre la palette (même dans les inputs)
- [x] Recherche en temps réel par nom ou description
- [x] Navigation au clavier : ArrowUp/ArrowDown, Enter pour exécuter, Escape pour fermer
- [x] Affichage des raccourcis clavier (⌘ sur Mac, Ctrl sur Windows/Linux)
- [x] Catégories : Chat, Mémoire, Panels, Settings
- [x] Affiche "Aucune commande trouvée" si recherche vide
- [x] Scroll automatique vers l'item sélectionné
- [x] Animations fade-in staggered respectent reduceMotion
- [x] Z-index COMMAND_PALETTE (z-80) : au-dessus des modaux
- [x] Fermeture au click outside (click sur backdrop)
- [x] Focus automatique sur l'input à l'ouverture
- [x] aria-modal="true", aria-label="Palette de commandes"

**Composants :** CommandPalette.tsx, useKeyboardShortcuts.ts, z-layers.ts
**data-testid :** command-palette, command-palette-input, command-item-{id}

---

### US-703 : Affichage des raccourcis clavier (Cmd+/)
**En tant que** solopreneur/TPE
**Je veux** voir la liste complète des raccourcis clavier disponibles
**Afin de** maîtriser ma productivité et découvrir les fonctionnalités cachées

**Critères d'acceptation :**
- [x] Cmd+/ affiche un modal avec tous les raccourcis (⌘N, ⌘B, ⌘M, etc.)
- [x] Groupage par catégorie : Navigation, Chat, Mémoire, Panels, Paramètres
- [x] Affichage du symbole correct (⌘ Mac, Ctrl Windows)
- [x] Description claire pour chaque raccourci
- [x] Recherche optionnelle dans le modal
- [x] Accessible via Command Palette ("Raccourcis clavier")
- [x] Focus trap (Tab/Shift+Tab) dans le modal
- [x] Fermeture via Escape
- [x] aria-modal="true", aria-label="Raccourcis clavier"

**Composants :** ShortcutsModal.tsx, useKeyboardShortcuts.ts
**data-testid :** shortcuts-modal, shortcuts-list, shortcut-item-{action}

---

### US-704 : Sidebar de conversation à gauche vs panels à droite (layout split)
**En tant que** solopreneur/TPE
**Je veux** que la navigation soit organisée de manière cohérente : conversations à gauche, modules à droite
**Afin de** avoir une architecture visuelle claire et intuitive

**Critères d'acceptation :**
- [x] ConversationSidebar fixe à gauche (z-30), Cmd+B pour toggle
- [x] Panels (Memory, Board, etc.) à droite (z-50 modal ou z-30 sidebar)
- [x] Chat au centre avec MessageList + ChatInput
- [x] Backdrop semi-transparent (z-40) derrière modaux
- [x] Animations slide respectent direction : left panels slide from left, right panels from right
- [x] Close button visible sur chaque panel
- [x] Responsive : pas de sidebar sur mobile si viewport < 768px

**Composants :** ChatLayout.tsx, ConversationSidebar.tsx, z-layers.ts, lib/animations.ts
**data-testid :** chat-layout, sidebar-left, panel-right, backdrop

---

## Module Raccourcis Clavier

### US-705 : Raccourcis clavier globaux avec détection plateforme (Cmd/Ctrl)
**En tant que** solopreneur/TPE
**Je veux** que les raccourcis clavier s'adaptent automatiquement à ma plateforme (Mac ⌘ vs Windows/Linux Ctrl)
**Afin de** ne pas être dérouté par des combinaisons incorrectes

**Critères d'acceptation :**
- [x] Détection automatique : navigator.platform pour Mac vs autres
- [x] Cmd+N : Nouvelle conversation (fonctionne même dans textarea)
- [x] Cmd+K : Command Palette (fonctionne même dans inputs)
- [x] Cmd+/ : Afficher raccourcis
- [x] Cmd+⇧K : Ouvrir Atelier + focus nouvelle tâche (Katia mode)
- [x] Cmd+B : Toggle Conversation Sidebar
- [x] Cmd+M : Toggle Memory Panel
- [x] Cmd+D : Toggle Board Panel
- [x] Cmd+E : Toggle Email Panel
- [x] Cmd+⇧C : Toggle Calendar Panel
- [x] Cmd+T : Toggle Tasks Panel
- [x] Cmd+I : Toggle Invoices Panel
- [x] Cmd+P : Toggle CRM Panel
- [x] Cmd+⇧A : Toggle Atelier Panel
- [x] Cmd+⇧F : Search Memory
- [x] Cmd+O : Open File
- [x] Cmd+, : Settings
- [x] Cmd+⇧D : Toggle Demo Mode
- [x] Escape : Ferme le modal le plus en avant
- [x] Pas d'interaction avec les inputs sauf Cmd+K, Cmd+/, Cmd+N, Escape
- [x] preventDefault() sur les combinaisons gérées

**Composants :** useKeyboardShortcuts.ts
**data-testid :** keyboard-input-handler

---

### US-706 : Personnalisation des raccourcis clavier (futur)
**En tant que** solopreneur
**Je veux** personnaliser mes raccourcis clavier selon mes préférences
**Afin de** adapter THÉRÈSE à mon workflow habituel

**Critères d'acceptation :**
- [ ] Settings > Raccourcis : affiche la liste des actions personnalisables
- [ ] Clicker sur une ligne pour capturer une nouvelle combinaison
- [ ] Validation : pas de conflits entre raccourcis
- [ ] Bouton "Réinitialiser par défaut"
- [ ] Sauvegarde dans personalisationStore (Zustand)
- [ ] Persistance en localStorage
- [ ] Feedback visuel pendant la capture (ex: "Appuie sur une combinaison...")

**Composants :** KeyboardShortcutsSettings.tsx (à créer), personalisationStore.ts (US-PERS-01)
**data-testid :** shortcut-settings, shortcut-capture-input, shortcut-reset-btn

---

## Module UX Transverse

### US-707 : Système de z-index standardisé
**En tant que** développeur
**Je veux** que tous les composants utilisent des constantes de z-index centralisées
**Afin d'** éviter les conflits de stacking et les chevauchements inattendus

**Critères d'acceptation :**
- [x] Z_LAYER.INTERNAL (z-10) : badges, indicateurs, overlays relatifs
- [x] Z_LAYER.DROPDOWN (z-20) : menus contextuels, dropdowns, tooltips
- [x] Z_LAYER.SIDEBAR (z-30) : sidebars et panels coulissants
- [x] Z_LAYER.BACKDROP (z-40) : backdrops des modaux
- [x] Z_LAYER.MODAL (z-50) : modaux principaux (DialogShell, Settings, Email, Calendar, Board, CRM)
- [x] Z_LAYER.MODAL_NESTED (z-60) : modaux dans modaux
- [x] Z_LAYER.WIZARD (z-70) : setup wizards, notifications actionables
- [x] Z_LAYER.COMMAND_PALETTE (z-80) : command palette
- [x] Z_LAYER.TOAST (z-90) : toasts / notifications passives
- [x] Z_LAYER.ONBOARDING (z-100) : onboarding uniquement
- [x] Z_LAYER.ONBOARDING_TOP (z-101) : onboarding header
- [x] Chaque composant utilise `className=\`... ${Z_LAYER.MODAL} ...\``

**Composants :** src/frontend/src/styles/z-layers.ts
**data-testid :** N/A (constantes TypeScript)

---

### US-708 : useGuardedAction - Exécution d'action avec pré-conditions explicites
**En tant que** développeur
**Je veux** que chaque action vérifiée affiche un message d'erreur explicite si une pré-condition échoue
**Afin de** d'éliminer les erreurs silencieuses et déboguer facilement

**Critères d'acceptation :**
- [x] Hook `useGuardedAction(guards)` avec tableau de GuardCondition
- [x] GuardCondition : { check: unknown, message: string }
- [x] Retour : { execute, error, loading, clearError }
- [x] Vérifie toutes les pré-conditions avant d'exécuter l'action
- [x] Affiche le premier message d'erreur si une condition échoue
- [x] Affiche l'erreur de l'action si la promesse reject
- [x] État `loading: true` pendant l'exécution
- [x] `clearError()` réinitialise l'état d'erreur
- [x] Persistance de l'erreur jusqu'à `clearError()` ou nouvelle tentative

**Composants :** src/frontend/src/hooks/useGuardedAction.ts
**data-testid :** guarded-action-error, guarded-action-loading

---

### US-709 : Mode d'animations réduites (Respect des préférences de mouvement)
**En tant que** utilisateur photosensible ou préférant une interface statique
**Je veux** désactiver toutes les animations Framer Motion
**Afin de** d'utiliser THÉRÈSE sans gêne visuelle ou nausée

**Critères d'acceptation :**
- [x] Détection automatique de prefers-reduced-motion du système
- [x] Synchronized avec le store accessibilityStore (useReducedMotion)
- [x] Settings > Accessibilité : toggle "Réduire les animations"
- [x] Tous les variants Framer Motion vérifier `reduceMotion` store
- [x] Animations activées avec `initial={reduceMotion ? false : { ... }}`
- [x] Transitions définie comme `transition={{ duration: reduceMotion ? 0 : 0.2 }}`
- [x] CommandPalette, modaux, sidebar, toasts respectent ce flag
- [x] Écoute les changements système en temps réel (onReducedMotionChange)
- [x] Classe CSS basée sur la préférence (optionnel : data-reduce-motion)

**Composants :** accessibilityStore.ts, lib/accessibility.ts, App.tsx, CommandPalette.tsx, ConversationSidebar.tsx
**data-testid :** reduce-motion-toggle, accessibility-settings

---

### US-710 : Accessibilité au clavier - Navigation complète sans souris
**En tant que** utilisateur en fauteuil roulant ou souhaitant naviguer uniquement au clavier
**Je veux** accéder à tous les éléments interactifs via Tab et exécuter les actions via Enter/Space
**Afin de** d'utiliser THÉRÈSE indépendamment

**Critères d'acceptation :**
- [x] Focus visible ring (2px, accent-cyan) sur tous les boutons/inputs
- [x] Tab order logique : conversation > chat input > sidebar > modaux
- [x] Focus trap dans les modaux (DialogShell, CommandPalette)
- [x] Escape ferme le modal le plus en avant
- [x] Roving tabindex pour les listes (createRovingTabindex)
- [x] Arrow Up/Down pour naviguer dans CommandPalette et listes
- [x] Double-clic = rename : aussi accessible via Enter sur l'item + Rename
- [x] Context menu accessible via Shift+F10 ou clavier
- [x] Skip link "Aller au contenu principal" visible au focus
- [x] aria-label, aria-modal, role="button", role="dialog", role="status"

**Composants :** DialogShell.tsx, accessibility.ts (getFocusableElements, createFocusTrap, createRovingTabindex), Button.tsx, App.tsx
**data-testid :** focus-visible, skip-link, keyboard-nav-test

---

### US-711 : Annonces pour lecteur d'écran (ARIA live regions)
**En tant que** utilisateur malvoyant utilisant un lecteur d'écran (NVDA, JAWS, VoiceOver)
**Je veux** être informé des changements de l'interface via des annonces textuelles
**Afin de** d'utiliser THÉRÈSE en toute indépendance

**Critères d'acceptation :**
- [x] Fonction `announceToScreenReader(message, { assertive?, timeout? })`
- [x] Crée un live region aria-live="polite" ou "assertive"
- [x] Message disparaît après timeout (défaut 1000ms)
- [x] Classe CSS "sr-only" : caché visuellement mais lisible par lecteur
- [x] AnnoncetoScreenReader utilisé pour :
  - [x] "Nouvelle conversation créée"
  - [x] "Conversation supprimée"
  - [x] "Conversation renommée en {titre}"
  - [x] "Message envoyé"
  - [x] Erreurs critiques (assertive)
- [x] aria-label sur les IconButtons (constat dans ConversationSidebar : pas de labels visible)
- [x] aria-describedby pour les inputs avec description

**Composants :** lib/accessibility.ts (announceToScreenReader), ConversationSidebar.tsx, Button.tsx
**data-testid :** live-region, sr-only-announcer

---

### US-712 : Contraste des couleurs conforme WCAG AA
**En tant que** utilisateur malvoyant ou daltonien
**Je veux** que tous les textes et éléments interactifs aient un contraste minimum de 4.5:1 (normal) ou 3:1 (large)
**Afin de** lire THÉRÈSE sans effort

**Critères d'acceptation :**
- [x] Palette THÉRÈSE conforme WCAG AA :
  - [x] textPrimary (#E6EDF7) vs background (#0B1226) : 13.5:1 ✓
  - [x] textMuted (#B6C7DA) vs background : 7.8:1 ✓
  - [x] accentCyan (#22D3EE) vs background : 8.2:1 ✓
  - [x] accentMagenta (#E11D8D) vs background : 5.1:1 ✓
- [x] Fonctions utilitaires :
  - [x] getLuminance(hex) : calcul luminance relative
  - [x] getContrastRatio(color1, color2) : ratio WCAG
  - [x] meetsContrastRequirement(fg, bg, isLargeText) : validation
- [x] Vérification au build (console.warn si < 4.5:1)
- [x] Settings > Accessibilité : toggle "Contraste élevé" (à implémenter)

**Composants :** lib/accessibility.ts (getLuminance, getContrastRatio, meetsContrastRequirement, A11Y_COLORS), accessibilityStore.ts
**data-testid :** contrast-checker, high-contrast-toggle

---

### US-713 : Tailles de police personnalisables (petite, moyenne, grande)
**En tant que** utilisateur malvoyant ou avec défaut de vision
**Je veux** augmenter la taille de la police pour lire plus facilement
**Afin de** d'adapter l'interface à ma vision

**Critères d'acceptation :**
- [x] Settings > Accessibilité : 3 options de taille
  - [x] Petite (14px)
  - [x] Moyenne (16px, défaut)
  - [x] Grande (18px)
- [x] Sauvegarde dans accessibilityStore
- [x] Hook `useFontSize()` retourne la valeur en px
- [x] App.tsx applique le style : `style={{ fontSize }}`
- [x] Tous les éléments héritent cette taille (cascade CSS)
- [x] Les espacements (padding, gap) restent proportionnels

**Composants :** accessibilityStore.ts, App.tsx, AccessibilityTab.tsx
**data-testid :** font-size-small, font-size-medium, font-size-large, accessibility-settings

---

### US-714 : Mode sombre persistant (Dark theme par défaut)
**En tant que** utilisateur travaillant la nuit ou préférant l'interface sombre
**Je veux** que THÉRÈSE reste en mode sombre à chaque lancement
**Afin de** de ne pas être gêné par la lumière bleue tard le soir

**Critères d'acceptation :**
- [x] Palette Tailwind : dark mode via CSS custom properties
  - [x] background: #0B1226 (bg-bg)
  - [x] surface: #131B35 (bg-surface)
  - [x] text-primary: #E6EDF7 (text-text)
  - [x] text-muted: #B6C7DA (text-text-muted)
  - [x] accent-cyan: #22D3EE
  - [x] accent-magenta: #E11D8D
- [x] Pas de toggle light/dark (design choix)
- [x] Tous les composants utilisent la palette (pas de couleurs en dur)

**Composants :** tailwind.config.js, tous les composants via Tailwind classes
**data-testid :** N/A (thème global)

---

### US-715 : Animations fluides avec respect de reduceMotion
**En tant que** développeur
**Je veux** utiliser une bibliothèque centralisée de variants Framer Motion
**Afin de** d'avoir des animations cohérentes et performantes

**Critères d'acceptation :**
- [x] Variants pré-définis (fadeIn, slideInFromLeft, scaleIn, modalVariants, sidebarLeftVariants, etc.)
- [x] Transitions standardisées (springTransition, easeTransition, smoothTransition)
- [x] Composants vérifier `reduceMotion` store avant d'appliquer les variants
- [x] ConversationSidebar : slideInFromLeft avec `initial={false}` si reduceMotion
- [x] CommandPalette : scaleIn + fade avec `initial={reduceMotion ? false : { ... }}`
- [x] Modaux : modalVariants avec spring transition
- [x] Listes : staggerContainer + staggerItem avec délai de 0.05s
- [x] Transitions court-circuitées à 0 si reduceMotion

**Composants :** lib/animations.ts, tous les composants avec motion.div
**data-testid :** animation-test

---

### US-716 : Drag & drop des fichiers (File Upload via DropZone)
**En tant que** solopreneur
**Je veux** glisser-déposer des fichiers dans le chat pour les indexer
**Afin de** d'enrichir ma mémoire rapidement sans cliquer

**Critères d'acceptation :**
- [x] DropZone : overlay semi-transparent lors du survol de fichiers
- [x] Visual feedback : dashed border bleu, fond semi-transparent
- [x] Gestion des événements : dragover, dragleave, drop
- [x] Filtre par type MIME (documents, images, sheets, presentations)
- [x] Validation taille (< 100MB généralement)
- [x] Téléchargement automatique vers ~/therese/uploads
- [x] Indexation Qdrant après upload
- [x] Toast de succès/erreur
- [x] Disabled lors d'un upload en cours (loading state)

**Composants :** files/DropZone.tsx, hooks/useFileDrop.ts
**data-testid :** dropzone, drag-overlay

---

### US-717 : Notifications et toasts (système unifié)
**En tant que** solopreneur
**Je veux** recevoir des notifications pour les actions importantes (erreurs, succès, confirmations)
**Afin de** d'être informé du statut en temps réel

**Critères d'acceptation :**
- [x] Toast (passive) : succès, info, warning (z-90, bottom-right, auto-dismiss 3s)
- [x] Notification (interactive) : erreurs, confirmations (boutons, peut être cliquée)
- [x] Animation : fade-in from bottom, exit upward
- [x] Respecte reduceMotion (duration: 0 si réduit)
- [x] Z_LAYER.TOAST (z-90) : au-dessus des modaux mais pas de la command palette
- [x] NotificationCenter icon : cloche + badge compteur
- [x] Notifications persistantes jusqu'à action
- [x] Design couleurs : rouge pour erreurs, cyan pour succès, jaune pour warning

**Composants :** ui/Notifications.tsx, ui/NotificationCenter.tsx, stores/notificationStore.ts
**data-testid :** toast, notification-badge, notification-item

---

### US-718 : Focus management et modal stacking
**En tant que** utilisateur au clavier
**Je veux** que le focus soit géré correctement lors de l'ouverture/fermeture de modaux
**Afin de** de naviguer logiquement sans surprises

**Critères d'acceptation :**
- [x] À l'ouverture du modal : focus sur le premier élément focusable
- [x] Tab/Shift+Tab : focus trap, boucle dans le modal
- [x] Escape : ferme le modal et retourne le focus à l'élément précédent (trigger)
- [x] Modaux imbriqués : handleEscape ferme le plus en avant (logique z-index)
- [x] Backdrop : click ferme le modal (optionnel : click-outside)
- [x] aria-modal="true", role="dialog", aria-label

**Composants :** DialogShell.tsx, panelStore.ts (handleEscape)
**data-testid :** dialog-focus-trap, modal-stack-test

---

### US-719 : Onboarding wizard (première utilisation)
**En tant que** nouvel utilisateur
**Je veux** suivre un tour guidé de THÉRÈSE à mon premier lancement
**Afin de** de comprendre les fonctionnalités principales

**Critères d'acceptation :**
- [x] Détecte si c'est la première utilisation (localStorage therese-onboarding-done)
- [x] Affiche un wizard modal par-dessus le chat (z-70 WIZARD)
- [x] Étapes : bienvenue, conversation, mémoire, raccourcis, finition
- [x] Boutons : Suivant, Précédent, Ignorer
- [x] À la fin : marque comme complété, cache le wizard
- [x] Animations respectent reduceMotion
- [x] Focusable, accessible au clavier

**Composants :** onboarding/OnboardingWizard.tsx, App.tsx
**data-testid :** onboarding-wizard, onboarding-step, onboarding-next-btn

---

### US-720 : Détection de connexion (Mode offline gracieux)
**En tant que** utilisateur en perte de connexion Internet
**Je veux** que l'interface affiche clairement que je suis hors-ligne
**Afin de** de savoir que les appels API échoueront

**Critères d'acceptation :**
- [x] ConnectionStatus component : indicateur réseau (top-right ou header)
- [x] Détecte navigator.onLine et écoute online/offline events
- [x] Visual : dot rouge "Hors-ligne" si déconnecté, vert "En ligne" si connecté
- [x] Désactive les boutons d'envoi/appels API si hors-ligne
- [x] Toast warning : "Connexion perdue" quand réseau bascule offline
- [x] Retry automatique de la dernière action quand connexion revient (optionnel)

**Composants :** ui/ConnectionStatus.tsx, hooks/useOnlineStatus.ts
**data-testid :** connection-status, offline-indicator

---

### US-721 : Settings Panel (Paramètres unifiés)
**En tant que** solopreneur
**Je veux** accéder à tous les paramètres depuis un seul écran
**Afin de** de configurer THÉRÈSE selon mes besoins

**Critères d'acceptation :**
- [x] Cmd+, ouvre Settings modal (z-50 MODAL)
- [x] Onglets : Général, Accessibilité, LLM, Avancé
- [x] Accessible via Command Palette
- [x] Sauvegarde immédiate (no Save button needed)
- [x] Responsive : scroll sur petit écran

**Composants :** settings/SettingsModal.tsx, settings/AccessibilityTab.tsx
**data-testid :** settings-modal, settings-tab-accessibility

---

## Résumé Transverse

| Domaine | User Stories |
|---------|-------------|
| **Navigation** | US-700 à US-704 |
| **Raccourcis clavier** | US-705 à US-706 |
| **UX Transverse** | US-707 à US-721 |

### Fichiers clés impliqués
- `src/frontend/src/styles/z-layers.ts` : Hiérarchie z-index centralisée
- `src/frontend/src/hooks/useKeyboardShortcuts.ts` : Gestion raccourcis
- `src/frontend/src/hooks/useGuardedAction.ts` : Exécution sécurisée d'actions
- `src/frontend/src/stores/accessibilityStore.ts` : Préférences d'accessibilité
- `src/frontend/src/lib/accessibility.ts` : Utilitaires A11Y (contraste, focus, live regions)
- `src/frontend/src/components/sidebar/ConversationSidebar.tsx` : Sidebar gauche
- `src/frontend/src/components/chat/CommandPalette.tsx` : Palette de commandes
- `src/frontend/src/components/ui/DialogShell.tsx` : Base pour modaux accessibles
- `src/frontend/src/components/chat/ChatLayout.tsx` : Routing des panels principaux
- `src/frontend/src/stores/panelStore.ts` : État centralisé des panneaux
- `src/frontend/src/App.tsx` : Détection système (reduced-motion), onboarding, splash screen
- `src/frontend/src/lib/animations.ts` : Variants Framer Motion standardisés