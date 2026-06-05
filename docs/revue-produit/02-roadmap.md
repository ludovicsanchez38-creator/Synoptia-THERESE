# Revue produit Thérèse Desktop — Roadmap

**Validée le 2026-06-04.** Exécution sur branche `chantier-revue-produit`, jamais `main`. Chaque chantier : brainstorm ciblé → plan → TDD, validation à chaque étape. On ne lance qu'une phase à la fois.

## Phase 0 — Fondations : confiance + données unifiées  ← EN COURS (cadrage)
*Tout le reste repose là-dessus.*
- **Chantier A — Confiance** : P1 vérité d'exécution · P2 erreurs honnêtes.
- **Chantier B — Donnée unifiée** : P3 une Mémoire · **P4 un Contact (Mémoire=CRM, verrou)** · P5 recherche sémantique.
- A et B en parallèle ; P4 est la clé de voûte.
- *Résultat user* : « Thérèse fait ce qu'elle dit, et mes contacts sont au même endroit partout. »

## Phase 1 — Refonte de la navigation
*Dépend de la Phase 0 (surfaces refondées sur une donnée unifiée).*
- **Chantier C** : P6 règle unique de surfaces · P7 pile Échap unique · P8 ⌘K colonne vertébrale.
- *Résultat user* : « Je ne me perds plus entre dix fenêtres, je vais partout au clavier. »

## Phase 2 — Relier les parcours de bout en bout
*Dépend de A + B, profite de C.*
- **Chantier D** : P11 parcours signature chat→…→facture · P9 Board→chat · P10 Actions→résultat · P12 agenda hors Google.
- *Résultat user* : « De la première mention d'un prospect jusqu'à la facture, un seul fil continu. »

## Phase 3 — Visibilité, clarté, providers
- **Chantier E** : P13 fonctions orphelines · P14 mémoire visible · P15 écriture · P16 onboarding.
- **Chantier F** : P17 provider par usage + fallback + libellés honnêtes · P18 réglages + MCP.

## Respirations (quick wins à glisser dès qu'on a 1h)
P9, P10, P15, P16 : peu coûteux, très visibles, bons pour le moral et les testeurs.

## État d'avancement
- [x] Étape 0 périmètre · [x] Étape 1 état des lieux · [x] Étape 2 pistes · [x] Étape 3 roadmap validée
- [x] Phase 0 — cadrage Chantier B (brainstorm + spec + plan)
- [x] **Phase 0 — Chantier B (Donnée unifiée) IMPLÉMENTÉ + VALIDÉ PAR LES 2 REGARDS** (P3+P4+P5+B6). **1er regard (Claude, navigateur)** : P3/P4/P5 déroulés. **2e regard (Syn, Tauri réel)** : Boot, P3 in-window, P4, **vue croisée CRM**, pas-de-faux-succès = OK ; **P5 jugé KO** (taper le nom cachait le contact). **Correctif P5** (`ee61fae`) : recherche **hybride** (filtre local nom + sémantique), re-vérifiée navigateur (Revue/Browser trouvés, requête non-matchante → vide). Chantier B **clos, les deux regards verts**. Voir `B-rapport-implementation.md`.
- [x] **Phase 0 — Chantier A (Confiance) DURCI** : constat = l'essentiel (déduplication des créations + erreurs honnêtes des outils) était déjà en place depuis les retours de Dr_logic. Ajouté en défense en profondeur : `enforce_create_cap` (cap créations par tour) + `summarize_executions` (résumé déterministe), câblés dans chat.py, + garde-fous de régression. 448 tests backend verts.
- [~] **Phase 1 — refonte navigation** (content-swap par vues) : layout validé (zone principale, Linear/Notion), spec (`phase1-navigation-spec.md`), `navigationStore`. **FAITS** : L1 (CRM en vue, vérifié navigateur), **L2-L5 (Email/Agenda/Tâches/Factures en vues, `b365131`)**, **L9 (machinerie fenêtres-panels supprimée : windowManager + PanelWindow, `c4ed628`)**. **RESTE** :
  - **L6 — Mémoire : vue plein écran** → **FAIT + vérifié navigateur** (panel UX/UI `L6-decision-ux-panel.md`, reco appliquée). Mémoire = vue content-swap (`ee91e04`/`066a10e`), dette toggle soldée (`109b522`), fin du faux ami ⌘K. Débordement = 0 à 1280 px. **Reste de la reco** : pastille de glance inline (Lot 9), fusion Contacts→CRM + sortie Fichiers→vue (Lot 10, post-L6), virtualisation liste.
  - **L7 — pile Échap/retour unifiée** (un seul state machine overlays + historique de vues) : spec claire, TDD-able, dépend un peu de L6.
  - **L8 — ⌘K colonne vertébrale** (navigation + actions au clavier) : feature.
- [ ] Phase 2 (parcours), Phase 3 (visibilité/providers)
