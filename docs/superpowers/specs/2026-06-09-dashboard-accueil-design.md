# Spec — Vue « Accueil » de THÉRÈSE (refonte du dashboard)

Date : 2026-06-09
Branche : `feat/dashboard-accueil` (basée sur `fix/bugs-post-0.20`, intégration release 0.21.0)
Statut : design validé par Ludo (brainstorm 09/06/2026)

## Problème

Au lancement, THÉRÈSE affiche un dashboard « Ma journée » (`DashboardToday` + `GET /api/dashboard/today`) qui souffre de 4 maux :

1. **Cul-de-sac** : une fois fermé (clic sur la barre du bas), aucun moyen d'y revenir (pas de vue `home` dans `navigationStore`, pas de bouton, pas de raccourci). Pour le rouvrir : décocher « skip » dans Réglages > Avancé puis relancer l'app.
2. **Vide donc muet** : sur une instance sans agenda/factures/prospects, tout est à 0, l'agenda et les suggestions sont vides → écran perçu comme inutile.
3. **Éléments faux** : barre de recherche topbar décorative (un `<span>`), badge « Claude Opus 4.8 » codé en dur (mensonger en multi-provider), barre « Demandez à Thérèse… » qui ne saisit rien (bascule juste vers le chat).
4. **Non persistant** : disparaît dès qu'une conversation a un message.

Le concept (centre du jour) est bon et le backend `/today` tire de vraies données SQLite locales. Le travail : promouvoir cet écran en **vraie vue « Accueil »**, persistante, honnête et actionnable.

## Décisions de design (validées)

- **Forme** : hybride « lanceur + journée ». Haut = actions + reprise de conversations (toujours utile). Bas = aperçu du jour (agenda + à traiter).
- **Pas** de zone de saisie chat centrale : un **bouton « Nouvelle conversation »** (décision Ludo, sobriété).
- **État vide guidé qui se retire** : une bande « Mise en route » propose ce qui n'est pas encore branché et chaque carte disparaît une fois l'étape faite.

## Architecture

### Accès & cycle de vie
- Ajouter `'home'` au type `AppView` (`navigationStore.ts`).
- **Landing** : au démarrage, `activeView = 'home'` si la préférence le permet (réutilise `localStorage['therese-skip-dashboard']`, renommée conceptuellement « Afficher l'Accueil au lancement »). Sinon `'chat'`.
- **Header** : bouton « Accueil » (icône `Home` lucide) qui appelle `setView('home')`. Action ⌘K `home.open`.
- **Rendu** : dans `ChatLayout`, la vue `home` est rendue **sans** la barre « ← Chat » (c'est la racine, pas une sous-vue content-swap). Les autres vues gardent leur back-bar.
- Le composant `DashboardToday` est **remplacé** par `HomeView`. Le gating local `showDashboard` de `ChatLayout` est retiré au profit de la vue `home` + la préférence de lancement.

### Composants (unités à responsabilité unique)
- `HomeView.tsx` — conteneur : orchestre le fetch (`/today` + `/setup-status`), la mise en page, l'état chargement/erreur.
- `HomeHeader.tsx` — salutation + date FR ; badge « Données locales » ; badge **fournisseur réel** (lu dans la config courante).
- `QuickActions.tsx` — rangée de boutons dérivés de `actionRegistry` (Nouvelle conversation, Produire un document, Nouvelle facture, Nouveau contact).
- `RecentConversations.tsx` — 3 à 5 conversations récentes (depuis `chatStore`), clic → ouvre la conv dans le chat. Vide → « Aucune conversation pour l'instant ».
- `TodayAgenda.tsx` — RDV du jour (depuis le payload `/today`). Vide → « Rien de prévu aujourd'hui ».
- `TodayActionables.tsx` — « À traiter » : factures impayées + prospects à relancer + tâches urgentes, priorisés ; clic → vue concernée. Vide → « Aucune relance en attente ».
- `SetupChecklist.tsx` — bande « Mise en route » : cartes pour les étapes non faites (agenda / mail / profil facturation), chacune masquée une fois l'étape accomplie ; bande entièrement masquée quand tout est branché.

### Données
- **Réutilise** `GET /api/dashboard/today` (events / urgent_tasks / overdue_invoices / stale_prospects / summary) — inchangé.
- **Nouveau** `GET /api/dashboard/setup-status` → `{ has_calendar: bool, has_email: bool, billing_complete: bool }`, construit sur les signaux existants :
  - `has_calendar` : au moins un `Calendar` (ou compte calendrier) configuré.
  - `has_email` : statut d'auth email connecté (réutilise la logique de `email auth status`).
  - `billing_complete` : profil émetteur complet (réutilise `is_billing_complete` / `/api/invoices/billing/profile-status`).
- **Fournisseur réel** : lu dans la config/réglages courants (provider + modèle actifs). Si indisponible proprement, le badge est masqué plutôt que faux.
- Conversations récentes : `chatStore.conversations` triées par date, top 5.

### Honnêteté (suppression des faux)
- Barre de recherche topbar décorative → **supprimée**.
- Badge « Opus 4.8 » codé en dur → **fournisseur réellement actif** (ou masqué si indisponible).
- Barre « Demandez à Thérèse… » factice → **supprimée** (remplacée par le bouton « Nouvelle conversation »).
- Badge « Données locales » → **conservé** (honnête depuis la clarification souveraineté 0.20 : stockage local, traitement éventuellement cloud selon le provider).

## Flux

1. Lancement → `App`/`ChatLayout` : si préférence de lancement active et pas de conversation forcée, `setView('home')`.
2. `HomeView` monte → fetch parallèle `/today` + `/setup-status` ; lit `chatStore` (récentes) et la config (provider).
3. L'utilisateur clique une action rapide / une conv récente / un élément du jour → navigation vers la vue/conv concernée.
4. Bouton header « Accueil » ou ⌘K `home.open` → retour à la vue `home` à tout moment.

## Gestion d'erreur / états
- Chargement : spinner discret dans la zone du jour (l'en-tête et les actions restent visibles immédiatement).
- Échec `/today` ou `/setup-status` : la section concernée affiche un état dégradé (« Indisponible pour le moment »), le reste de l'Accueil fonctionne (les actions rapides ne dépendent d'aucun réseau).
- Aucune donnée : états vides sobres + bande « Mise en route » tant qu'il reste des étapes.

## Tests
- **Backend** : `GET /api/dashboard/setup-status` — has_calendar / has_email / billing_complete selon les fixtures (présence/absence de compte calendrier, statut email, complétude profil).
- **Frontend** :
  - `navigationStore` : la vue `home` est gérée (setView/goBack/history) ; action ⌘K `home.open` y navigue.
  - `HomeView` : rend les sections, états vides corrects, n'affiche aucun élément factice (pas de champ de recherche, pas de badge modèle codé en dur).
  - `SetupChecklist` : masque les étapes faites ; bande entièrement masquée quand tout est branché.
  - `RecentConversations` : top 5, clic ouvre la conv.

## Hors scope (YAGNI)
- Blocs configurables / réorganisables, widgets, graphiques.
- Saisie chat centrale (décision : bouton « Nouvelle conversation »).
- Personnalisation de l'ordre des sections.

## Compat & migration
- Suppression de `DashboardToday.tsx` et du gating `showDashboard` dans `ChatLayout` (remplacés par la vue `home`).
- La préférence `therese-skip-dashboard` (Réglages > Avancé) est conservée et pilote désormais « Afficher l'Accueil au lancement ».
- Le endpoint `/api/dashboard/today` reste inchangé (toujours consommé par `HomeView`).
