# Spec — Phase 1 : Refonte navigation (content-swap par vues)

**Date** : 2026-06-04 · **Branche** : `chantier-revue-produit` · **Layout validé** : zone principale / content-swap (modèle Linear/Notion).

## Problème (rappel état des lieux)
Aujourd'hui Email/Agenda/Tâches/Factures/CRM ouvrent des **fenêtres Tauri séparées** (`openPanelWindow`), Mémoire/Board sont des panneaux in-window, Settings/Atelier/Actions des modaux/tiroirs. Trois piles d'Échap concurrentes. L'utilisateur jongle entre N fenêtres et se perd entre les surfaces.

## Cible : une fenêtre, des VUES
- **État `activeView`** : `'chat' | 'memory' | 'crm' | 'email' | 'calendar' | 'tasks' | 'invoices'` (défaut `chat`).
- La **zone principale** de ChatLayout devient un **routeur de vues** : elle rend la vue active. On bascule entre vues via la sidebar, le header et ⌘K.
- **Restent des overlays** (transitoires, pas des vues) : Settings, Command Palette (⌘K), ContactModal/ProjectModal, Board (délibération ponctuelle), Atelier, Actions.
- **Surfaces devenues des vues** : CRM, Email, Agenda, Tâches, Factures (+ éventuellement Mémoire, à trancher en L6 : vue plein écran vs tiroir contextuel à côté du chat).
- **Échap / retour** : une **pile de vues** (historique) ; Échap ferme d'abord un overlay ouvert, sinon revient à la vue précédente (ou `chat`). Remplace les 3 piles d'Échap.
- **⌘K colonne vertébrale (P8)** : aller à n'importe quelle vue + lancer toute action, au clavier.

## Décomposition (lots TDD)
- **L1 — Fondation** : introduire `activeView` (navigationStore) + le routeur de vues dans la zone principale ; migrer **le CRM** de fenêtre → vue (valider le modèle de bout en bout). Header CRM → `setActiveView('crm')`. Retrait du CRM du windowManager.
- **L2-L5** : migrer Email, Agenda, Tâches, Factures en vues (même patron que L1).
- **L6** : Mémoire — décider vue plein écran vs tiroir contextuel (cohérence vs utilité du split chat+contexte).
- **L7 — Pile Échap/retour unifiée (P7)** : un seul state machine (overlays puis historique de vues), absorbe actionsStore/atelierStore.
- **L8 — ⌘K spine (P8)** : navigation + actions au clavier, découvrabilité.
- **L9 — Nettoyage** : retrait de la machinerie fenêtres-panels du windowManager + PanelWindow.tsx + variantes `standalone`.

## Principes
- Patron de migration **déjà prouvé** sur la Mémoire (Chantier B / B4) : ajouter l'état, rendre dans la zone, basculer le déclencheur, retirer du windowManager.
- TDD : tests sur le navigationStore (transitions de vues, pile de retour) + guards de régression (header utilise setActiveView, windowManager n'a plus la vue migrée).
- Vérif navigateur human-like à chaque lot significatif (comme Chantier B).

## Hors-périmètre
- Refonte visuelle fine de chaque vue (on déplace, on ne redessine pas chaque écran).
- Le tunnel de vente CRM (Phase 2), la visibilité des fonctions orphelines (Phase 3).
