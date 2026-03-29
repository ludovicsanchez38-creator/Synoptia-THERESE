Parfait ! J'ai maintenant tous les éléments. Voici le rapport complet avec les user stories :

---

## USER STORIES - THÉRÈSE v2
### Modules Calendrier et Tâches

Basées sur l'analyse complète du code source des composants frontend/backend, stores et API services.

---

### US-200 : Afficher et naviguer dans le calendrier Google
**En tant que** solopreneur/TPE
**Je veux** consulter mon calendrier Google en différentes vues (mois/semaine/jour/liste)
**Afin de** visualiser rapidement mes événements

**Critères d'acceptation :**
- [ ] Charger les calendriers depuis le compte Google (via OAuth)
- [ ] Auto-sélectionner le calendrier primaire à l'ouverture
- [ ] Afficher les événements du mois sélectionné en grille 7x6 (calendrier classique)
- [ ] Afficher la semaine avec colonne horaire (8h-20h) et ligne "heure actuelle" rouge
- [ ] Afficher le jour avec détail horaire (6h-22h, résolution 30min)
- [ ] Afficher liste chronologique des événements groupés par date
- [ ] Gérer les événements "Toute la journée" dans une section dédiée
- [ ] Navigation mois/semaine/jour et bouton "Aujourd'hui"
- [ ] Scroll auto vers "maintenant" en semaine/jour

**Composants :** CalendarPanel.tsx, CalendarView.tsx (MonthView, WeekView, DayView, ListView)
**data-testid :** calendar-panel, calendar-view, event-card

---

### US-201 : Créer un nouvel événement calendrier
**En tant que** solopreneur/TPE
**Je veux** créer rapidement un événement avec titre, date/heure, lieu, participants
**Afin de** planifier mes rendez-vous

**Critères d'acceptation :**
- [ ] Ouvrir formulaire "Nouvel événement" via bouton + ou doublon date
- [ ] Valider: titre obligatoire, dates cohérentes (fin > début)
- [ ] Toggle "Toute la journée" masque les champs heure
- [ ] Parser automatiquement les emails en participants (virgule-séparés)
- [ ] Afficher spinner "Enregistrement..." pendant POST
- [ ] Créer l'événement au backend (POST /api/calendar/events)
- [ ] Ajouter l'événement au store local immédiatement
- [ ] Fermer le formulaire et afficher l'événement en détail
- [ ] Erreur explicite si compte email ou calendrier absent (BUG-100)

**Composants :** EventForm.tsx, EventFormModal
**Hooks:** useGuardedAction
**data-testid :** event-form, event-form-submit, form-error-no-account

---

### US-202 : Éditer un événement calendrier
**En tant que** solopreneur/TPE
**Je veux** modifier titre, dates, participants d'un événement existant
**Afin de** ajuster mes plannings

**Critères d'acceptation :**
- [ ] Cliquer sur un événement → affiche EventDetail
- [ ] Bouton "Éditer" → ouvre EventForm pré-remplie avec les données
- [ ] Charger datetime en format ISO, splitter "T" pour date/heure
- [ ] Validation idem création (titre, dates)
- [ ] Envoyer PUT /api/calendar/events/{eventId} avec modifications
- [ ] Mettre à jour l'événement dans le store
- [ ] Retourner à l'affichage détail (read-only)

**Composants :** EventDetail.tsx, EventForm.tsx
**data-testid :** event-detail, event-edit-button, event-form-edit

---

### US-203 : Supprimer un événement calendrier
**En tant que** solopreneur/TPE
**Je veux** supprimer un événement que j'ai créé
**Afin de** nettoyer mon calendrier

**Critères d'acceptation :**
- [ ] Afficher bouton trash dans EventDetail
- [ ] Confirmation: "Supprimer cet événement ?"
- [ ] Envoyer DELETE /api/calendar/events/{eventId}
- [ ] Retirer l'événement du store local
- [ ] Revenir au calendrier (currentEventId = null)
- [ ] Gérer erreur: "Échec de la suppression" en toast

**Composants :** EventDetail.tsx
**data-testid :** event-delete-button, delete-confirmation

---

### US-204 : Synchroniser le calendrier Google
**En tant que** solopreneur/TPE
**Je veux** rafraîchir mon calendrier pour récupérer les derniers changements
**Afin de** rester à jour avec les modifications Google Calendar

**Critères d'acceptation :**
- [ ] Bouton Refresh en haut du CalendarPanel
- [ ] Appeler POST /api/calendar/sync?account_id=X
- [ ] Afficher spinner RefreshCw pendant sync
- [ ] Recharger les calendriers et événements du mois
- [ ] Afficher timestamp "Dernière synchro: XX:XX" dans store
- [ ] Gestion erreur: bannière jaune + message "Synchronisation échouée"
- [ ] Token expiré: afficher "Connexion Google expirée" + bouton "Reconnecter"

**Composants :** CalendarPanel.tsx
**data-testid :** sync-button, reauth-banner, reauth-button

---

### US-205 : Gérer l'authentification Google expirée (BUG-100)
**En tant que** solopreneur/TPE
**Je veux** être notifié quand mon token Google expire et pouvoir me réconnecter
**Afin de** continuer à utiliser le calendrier sans interruption

**Critères d'acceptation :**
- [ ] Détecter 401/403 "expired" lors du chargement calendriers/événements
- [ ] Afficher bannière jaune: "Connexion Google expirée. Reconnecte-toi..."
- [ ] Bouton "Reconnecter" → ouvre flow OAuth dans navigateur (Tauri ou fallback window.open)
- [ ] Poller status toutes les 3s jusqu'à 100 tentatives
- [ ] Une fois token valide: fermer bannière, recharger calendriers
- [ ] Afficher message explicite si aucun compte configuré: "Aucun compte email configuré. Ajoute un compte dans les paramètres."
- [ ] useGuardedAction blockage: "Aucun compte configuré" / "Aucun calendrier sélectionné"

**Composants :** CalendarPanel.tsx, EventForm.tsx
**Hooks:** useGuardedAction
**data-testid :** reauth-banner, reauth-button, no-account-error

---

### US-206 : Importer des événements au format ICS
**En tant que** solopreneur/TPE
**Je veux** importer des événements depuis un fichier .ics
**Afin de** migrer mes calendriers locaux ou d'intégrer des événements d'une tierce app

**Critères d'acceptation :**
- [ ] Bouton Upload (icône) en haut CalendarPanel
- [ ] File input caché type="file" accept=".ics"
- [ ] Parser fichier ICS et POST /api/calendar/import-ics
- [ ] Afficher notification: "Import ICS - 15 événement(s) importé(s)"
- [ ] Recharger calendriers et événements du mois
- [ ] Reset file input.value = '' pour permettre réimport même nom
- [ ] Erreur: "Erreur import - Format ICS invalide"

**Composants :** CalendarPanel.tsx
**data-testid :** ics-upload-button, ics-input, import-success-notification

---

### US-207 : Filtrer les événements calendrier
**En tant que** solopreneur/TPE
**Je veux** afficher/masquer les événements annulés et chercher par titre
**Afin de** se concentrer sur les événements importants

**Critères d'acceptation :**
- [ ] Toggle "Afficher annulés" (checkbox dans CalendarView ou toggle)
- [ ] Filtrer events: status !== 'cancelled' quand désactivé
- [ ] Champ recherche: filtre par summary / description / location
- [ ] Regex case-insensitive sur les 3 champs
- [ ] Persistance des filtres dans le store (partialize: ['showCancelled', 'searchQuery'])
- [ ] Visuel "Aucun événement" si filtrés vides

**Composants :** CalendarView.tsx, CalendarPanel.tsx
**data-testid :** show-cancelled-toggle, search-input, empty-state

---

### US-208 : Afficher le détail d'un événement
**En tant que** solopreneur/TPE
**Je veux** voir tous les détails d'un événement (date, lieu, participants, récurrence, description)
**Afin de** me préparer pour mon rendez-vous

**Critères d'acceptation :**
- [ ] Cliquer sur un événement → slide/modal EventDetail
- [ ] Afficher: titre, date (formatée FR), heure (si pas all-day), lieu, participants
- [ ] Afficher récurrence (si présente) en format RRULE lisible
- [ ] Afficher description complète (mode pre-wrap)
- [ ] Badge "Annulé" (rouge) / "Provisoire" (jaune) si status !== confirmed
- [ ] Boutons Éditer et Supprimer en haut
- [ ] Bouton retour (chevron) pour fermer

**Composants :** EventDetail.tsx
**data-testid :** event-detail, event-summary, event-attendees-list, event-status-badge

---

### US-209 : Créer une nouvelle tâche
**En tant que** solopreneur/TPE
**Je veux** créer rapidement une tâche avec titre, priorité, date limite
**Afin de** tracker ma to-do list

**Critères d'acceptation :**
- [ ] Bouton "+ Nouvelle tâche" en haut TasksPanel
- [ ] Ouvrir TaskForm avec champs: titre, description, statut, priorité, date limite, tags
- [ ] Valider: titre obligatoire
- [ ] Status par défaut: "À faire", priorité par défaut: "Moyenne"
- [ ] Parser tags comma-separated
- [ ] Envoyer POST /api/tasks avec les données
- [ ] Ajouter au store local immédiatement
- [ ] Fermer formulaire, afficher tâche dans la vue actuelle (Kanban/List)

**Composants :** TaskForm.tsx, TasksPanel.tsx
**data-testid :** task-form, task-form-submit, new-task-button

---

### US-210 : Éditer une tâche existante
**En tant que** solopreneur/TPE
**Je veux** modifier titre, description, priorité, date limite d'une tâche
**Afin de** mettre à jour mes actions

**Critères d'acceptation :**
- [ ] Cliquer sur une tâche → ouvre TaskForm pré-remplie
- [ ] Charger: titre, description, statut, priorité, due_date (format date), tags
- [ ] Parser due_date ISO → format input date (YYYY-MM-DD)
- [ ] Validation: titre obligatoire
- [ ] Envoyer PUT /api/tasks/{taskId}
- [ ] Mettre à jour le store
- [ ] Fermer le formulaire

**Composants :** TaskForm.tsx, TaskList.tsx, TaskKanban.tsx
**data-testid :** task-form-edit, task-edit-button

---

### US-211 : Marquer une tâche comme terminée
**En tant que** solopreneur/TPE
**Je veux** cocher une tâche pour indiquer qu'elle est faite
**Afin de** tracker ma progression

**Critères d'acceptation :**
- [ ] Checkbox dans TaskList (circle → checkmark vert)
- [ ] Actions rapides en hover TaskKanban (bouton checkmark vert)
- [ ] Click: PATCH /api/tasks/{taskId}/complete (si status !== done)
- [ ] Statut → "done", completed_at → maintenant
- [ ] Mise à jour du store
- [ ] Visuel: strikethrough + opacity réduite
- [ ] Toggle: click de nouveau pour "uncomplete" (PATCH /uncomplete)

**Composants :** TaskList.tsx, TaskKanban.tsx (TaskCard)
**data-testid :** task-checkbox, task-complete-button

---

### US-212 : Supprimer une tâche
**En tant que** solopreneur/TPE
**Je veux** supprimer une tâche que je ne veux plus tracker
**Afin de** garder ma liste propre

**Critères d'acceptation :**
- [ ] Bouton trash en fin de ligne (TaskList) ou via actions (TaskKanban)
- [ ] Confirmation: "Supprimer cette tâche ?"
- [ ] Envoyer DELETE /api/tasks/{taskId}
- [ ] Retirer du store local
- [ ] Fermer formulaire si ouvert
- [ ] Visuel: disparition animée (Framer Motion)

**Composants :** TaskList.tsx, TaskKanban.tsx
**data-testid :** task-delete-button, delete-confirmation

---

### US-213 : Afficher les tâches en vue Kanban (Drag & Drop)
**En tant que** solopreneur/TPE
**Je veux** voir mes tâches en colonnes À faire / En cours / Terminé et les glisser
**Afin de** gérer mon workflow visuellement

**Critères d'acceptation :**
- [ ] 3 colonnes: Todo (grey), In Progress (blue), Done (green)
- [ ] Drag & Drop via @dnd-kit/core + @dnd-kit/sortable
- [ ] Grip handle (≡) visible au hover
- [ ] Dropped sur colonne → PATCH /api/tasks/{taskId} status=target_status
- [ ] Card highlight cyan/5 quand over
- [ ] DragOverlay: card en drag affiche shadow + ring cyan
- [ ] Compteur de tâches par colonne
- [ ] Pas de reorder parmi les statuts (juste le statut change)
- [ ] "Aucune tâche" si colonne vide

**Composants :** TaskKanban.tsx (DroppableColumn, SortableTaskCard, TaskCard)
**data-testid :** kanban-column-todo, kanban-column-in-progress, kanban-column-done, task-card-drag

---

### US-214 : Afficher les tâches en vue Liste
**En tant que** solopreneur/TPE
**Je veux** voir mes tâches dans une liste scrollable avec tous les détails
**Afin de** avoir une vue d'ensemble

**Critères d'acceptation :**
- [ ] Chaque tâche: checkbox + titre + priorité + description + due date + tags
- [ ] Ordre: todo/in_progress avant done/cancelled, puis par priorité, puis due_date
- [ ] Checkbox pour marquer done/uncomplete
- [ ] Priority badge: couleur selon urgence (red urgent, orange high, blue medium, gray low)
- [ ] Due date rouges si dépassée et status !== done
- [ ] Tags affichés en pills cyan
- [ ] Hover: affiche bouton trash
- [ ] Click ligne → ouvre TaskForm pour éditer
- [ ] Strikethrough + opacity 60% si done
- [ ] "Aucune tâche" si liste vide

**Composants :** TaskList.tsx
**data-testid :** task-list-item, task-priority-badge, task-due-date, task-tags

---

### US-215 : Filtrer les tâches par statut et priorité
**En tant que** solopreneur/TPE
**Je veux** filtrer les tâches par statut et priorité
**Afin de** me concentrer sur les actions urgentes

**Critères d'acceptation :**
- [ ] Dropdown "Tous les statuts" → todo, in_progress, done, cancelled
- [ ] Dropdown "Toutes les priorités" → urgent, high, medium, low
- [ ] Filtre en live: recharger tâches avec query params ?status=X&priority=Y
- [ ] Bouton "Réinitialiser" visible si filtres actifs
- [ ] Persistance: filterStatus, filterPriority dans store.partialize
- [ ] Affichage paniers: "X tâche(s)"

**Composants :** TasksPanel.tsx
**data-testid :** filter-status-select, filter-priority-select, filter-reset-button

---

### US-216 : Rechercher des tâches
**En tant que** solopreneur/TPE
**Je veux** rechercher une tâche par titre ou description
**Afin de** retrouver rapidement mes actions

**Critères d'acceptation :**
- [ ] Champ recherche dans TasksPanel ou CalendarPanel
- [ ] Filtre en live: cherche dans title + description (case-insensitive)
- [ ] Regex pattern matching
- [ ] Persistance: searchQuery dans store
- [ ] Tous les statuts filtrés ci-dessus + recherche = AND logic
- [ ] "Aucune tâche" si recherche vide

**Composants :** TasksPanel.tsx
**data-testid :** search-input, search-results

---

### US-217 : Basculer entre vues Kanban et Liste (Tâches)
**En tant que** solopreneur/TPE
**Je veux** switcher rapidement entre Kanban et Liste
**Afin de** choisir la vue qui me convient

**Critères d'acceptation :**
- [ ] 2 boutons radio en haut TasksPanel: LayoutGrid (Kanban) / ListTodo (Liste)
- [ ] Highlight cyan si actif
- [ ] Persistance: viewMode dans store.partialize
- [ ] Affichage instantané sans recharge des données
- [ ] Animation transition (Framer Motion opacity)

**Composants :** TasksPanel.tsx
**data-testid :** view-mode-kanban-button, view-mode-list-button

---

### US-218 : Rafraîchir les tâches
**En tant que** solopreneur/TPE
**Je veux** rechargé les tâches manuellement
**Afin de** voir les derniers changements

**Critères d'acceptation :**
- [ ] Bouton Refresh RefreshCw en haut TasksPanel
- [ ] Click: GET /api/tasks?[filters appliqués]
- [ ] Afficher spinner pendant chargement
- [ ] Mettre à jour le store
- [ ] Garder les filtres/searchQuery appliqués

**Composants :** TasksPanel.tsx
**data-testid :** refresh-button

---

### US-219 : Afficher les erreurs explicites pour configuration manquante
**En tant que** solopreneur/TPE
**Je veux** voir des messages clairs si mon compte ou calendrier ne sont pas configurés
**Afin de** savoir exactement quoi faire (FIX BUG-100)

**Critères d'acceptation :**
- [ ] Hook useGuardedAction vérifie: currentAccountId, currentCalendarId
- [ ] Message 1: "Aucun compte configuré. Ajoute un compte email dans les paramètres."
- [ ] Message 2: "Aucun calendrier sélectionné. Choisis un calendrier dans le menu déroulant."
- [ ] CalendarPanel.loadCalendars(): détecte token expiré → bannière reauth
- [ ] EventForm.handleSave(): execute() attend guards OK avant POST
- [ ] TasksPanel: si erreur chargement (n'affiche que si pas de cache)
- [ ] Tous les messages utilisateur en FR, spécifiques et actionnables

**Composants :** EventForm.tsx, CalendarPanel.tsx, TaskForm.tsx
**Hooks:** useGuardedAction
**data-testid :** no-account-error, no-calendar-error, reauth-banner

---

### US-220 : Gérer le mode standalone vs modal du Calendrier
**En tant que** développeur
**Je veux** réutiliser CalendarPanel en pleine page ou en modal
**Afin de** intégrer le calendrier dans différents contextes

**Critères d'acceptation :**
- [ ] Prop standalone: boolean (défaut false)
- [ ] standalone=true: pleine page (h-full flex flex-col)
- [ ] standalone=false: modal centré avec backdrop blur + AnimatePresence
- [ ] Modal: click backdrop ferme le panel (onClose callback)
- [ ] Header: bouton X seulement en mode modal
- [ ] Chargement des comptes email en standalone mode si absent
- [ ] Z_LAYER.MODAL pour stacking correct
- [ ] data-testid="calendar-panel" sur les deux modes

**Composants :** CalendarPanel.tsx
**data-testid :** calendar-panel

---

### US-221 : Gérer le mode standalone vs modal des Tâches
**En tant que** développeur
**Je veux** réutiliser TasksPanel en pleine page ou en modal
**Afin de** intégrer les tâches dans différents contextes

**Critères d'acceptation :**
- [ ] Prop standalone: boolean (défaut false)
- [ ] standalone=true: pleine page
- [ ] standalone=false: modal centré (Z_LAYER.MODAL)
- [ ] Click backdrop ferme (onClose callback)
- [ ] Bouton X seulement en modal
- [ ] Chargement popul mask demo (useDemoMask) en standalone+demoEnabled
- [ ] AnimatePresence pour animations
- [ ] data-testid="tasks-panel" sur les deux modes

**Composants :** TasksPanel.tsx
**data-testid :** tasks-panel

---

### US-222 : Afficher les tags et priorités des tâches
**En tant que** solopreneur/TPE
**Je veux** voir les tags et priorités codifiées par couleur
**Afin de** identifier rapidement les actions importantes

**Critères d'acceptation :**
- [ ] Tags: pillules cyan/10 avec texte accent-cyan
- [ ] Priorité badges:
  - Urgent: bg-red-500/10 text-red-400
  - High: bg-orange-500/10 text-orange-400
  - Medium: bg-blue-500/10 text-blue-400
  - Low: bg-gray-500/10 text-gray-400
- [ ] TaskList: priorité visuelle en fin de ligne
- [ ] TaskKanban: priorité badge en haut card
- [ ] Icône AlertCircle rouge si overdue (due_date < now && status !== done)
- [ ] Icône Clock bleu si in_progress

**Composants :** TaskList.tsx, TaskKanban.tsx (TaskCard)
**data-testid :** task-priority-badge, task-tags, overdue-indicator

---

### US-223 : Masquer les informations sensibles en mode demo (Demo Mask)
**En tant que** testeur/démo
**Je veux** que les contacts, projets et tâches soient masqués par des placeholders
**Afin de** faire des démos sans exposer les données réelles

**Critères d'acceptation :**
- [ ] Hook useDemoMask() retourne maskText(text) si demoEnabled
- [ ] TaskList/TaskKanban: title + description passent par maskText()
- [ ] Contacts/Projets remplacés par UUID générés pseudo-aléatoires
- [ ] Mapping persistant: même ID → même placeholder dans la démo
- [ ] TasksPanel: charger contacts + projets si demoEnabled ET effectiveOpen
- [ ] Aucun changement visible au non-démo

**Composants :** TaskList.tsx, TaskKanban.tsx
**Hooks:** useDemoMask
**data-testid :** masked-task-title, masked-task-description

---

### US-224 : Charger les données du calendrier en étapes (calendriers puis événements)
**En tant que** développeur
**Je veux** charger les calendriers avant les événements
**Afin de** éviter les races conditions et améliorer la perf

**Critères d'acceptation :**
- [ ] useEffect 1: effectiveOpen + currentAccountId → loadCalendars()
- [ ] useEffect 2: calendarsReady + currentCalendarId → loadEvents()
- [ ] calendarsReady flag devient true une fois calendriers chargés
- [ ] Si pas de calendriers en cache: afficher loader
- [ ] Si calendriers en cache: showLoader reste false, loadEvents directement
- [ ] selectedDate change → recharger events (pas calendriers)

**Composants :** CalendarPanel.tsx
**data-testid :** calendar-loading, events-loading

---

### US-225 : Persister et récupérer l'état du stockage (Zustand persist)
**En tant que** utilisateur
**Je veux** que mes préférences et mes événements soient sauvegardés
**Afin de** retrouver mon état à la réouverture

**Critères d'acceptation :**
- [ ] calendarStore.persist: calendars, currentCalendarId, events, viewMode, showCancelled, lastSyncAt
- [ ] taskStore.persist: tasks, viewMode, filterStatus, filterPriority
- [ ] Clé localStorage: "calendar-storage" et "task-storage"
- [ ] Hydratation automatique à la réouverture
- [ ] Champs non persistés: UI transient (isEventFormOpen, selectedDate, searchQuery)

**Composants :** calendarStore.ts, taskStore.ts
**data-testid :** n/a (test localStorage)

---

**Fin du document. Numérotation complète US-200 → US-225 (26 user stories).**