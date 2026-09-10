# Cadrage : intégrer la DA « Application affinée » (direction 2)

Date : 10/09/2026. Décision de Ludo : « la DA application affinée est
superbe. je valide » (10/09), avec une réserve : « il n'y a pas toutes les
pages. il faudra que chaque page de l'appli soit traitée (je pense au mail et
sans doute à d'autres trucs) ». Ordre demandé : cycle 6, release 0.70.0, puis
la DA. Ce document est le plan à valider AVANT de coder.

Source de la proposition : `http://192.168.1.56:8098/therese/` (DQ SYN,
LAN), dossier `~/.local/share/synoptia-site-preview-20260904/public/therese/`
(copie locale de travail dans le scratchpad de la session). Neuf pages :
socle, accueil, tiroir, contacts, devis, projets, decision, agenda,
parametres ; `ecrans.json` décrit les états maquettés ; `maquettes/da/`
contient `base.css` (le socle), `tokens.css` (jetons RÉELS extraits de
`src/frontend/src/styles/globals.css`) et `d2.css` (vide : « le socle base.css
tel quel, avec les jetons réels. Rien à redéfinir »).

## Ce que la direction 2 est, concrètement

La direction 2 ne change ni la palette ni les jetons : elle consomme ceux de
l'application (fonds, encres, accent, domaines, rayons, ombres, polices Inter
et Plus Jakarta Sans déjà déclarées dans `globals.css`). Ce qu'elle tranche,
c'est la FORME : une coque (barre de 3,25 rem avec marque, état, « Contrôle des
données », recherche ⌘K ; rail de 3,5 rem à icônes, avatar en bas ; colonne de
contenu à 56 rem ; composeur flottant qui porte l'établi des cinq verbes et ne
recouvre rien), une typographie de registre (h1 800 / h2 700 / h3 700 en
Plus Jakarta Sans, `.editorial` pour les titres de brief, `.meta` 12 px pour
les métadonnées), des composants (boutons primaire en pilule cyan, secondaire,
discret, danger, icône ; cartes ; lignes 2 rem-1fr-auto ; étiquettes
sémantiques et de domaine ; segments ; champs ; tableau ; états vide, alerte,
chargement ; messages THÉRÈSE et humain).

Une partie est déjà dans le code (rayons 14 px « valeur de la DA », classes
`btn-da` du bouton, rail de navigation `w-16`, jetons de domaine). La leçon
de la 0.60 vaut encore : la DA de mai « était déjà dans le code sans être
consommée ». Le travail est de la consommer partout, pas de la redéclarer.

## Inventaire : ce que la DA couvre, ce qui manque

| Surface de l'application | Maquette DA | États maquettés |
|---|---|---|
| Accueil (brief du jour, cinq verbes) | oui (`accueil`) | quatre éléments, relance préparée, relance envoyée, journée dégagée, agenda indisponible |
| Tiroir des conversations, catalogue des capacités | oui (`tiroir`) | conversations, catalogue, vide |
| Contacts et Pipeline (fiche, déplacement clavier) | oui (`contacts`) | pipeline, fiche en déplacement, fiche contact |
| Devis et factures (liste, nouveau devis, filtre vide) | oui (`devis`) | liste, filtre vide, nouveau devis avec erreur de ligne |
| Projets et Tâches (colonnes, liste, nouvelle tâche) | oui (`projets`) | colonnes, liste, nouvelle tâche sans titre |
| Décision (Board) | oui (`decision`) | enregistrée, en cours, un conseiller muet |
| Agenda (semaine, mois, nouveau, rafraîchissement raté) | oui (`agenda`) | semaine, mois, nouveau rendez-vous, erreur |
| Paramètres (neuf rubriques) | oui (`parametres`) | service d'IA, profil, clé refusée |
| **Email** : liste, lecture, composition, assistant de connexion (Gmail, IMAP/SMTP), signature, réponse générée | **non** | à maquetter |
| **Documents** : liste, création, atelier de rédaction (trame, sections, pistes) | **non** | à maquetter |
| **Fichiers** : indexation locale | **non** | à maquetter |
| **Atelier des agents** : catalogue, session, revue de code, mission | **non** | à maquetter |
| **Mise en route** : six étapes, récapitulatif | **non** | à maquetter |
| **Canevas conversationnels** : rendez-vous, facturer, livrables, images, voix, calcul, relances, tableau du jour | **non** (le composeur et les cartes du socle s'appliquent) | à maquetter par famille |
| **Couches** : palette ⌘K, raccourcis, notifications, bannières (mise à jour, sidecar), modales contact / projet / commande, confirmations en ligne, Travaux, Actions, Centre de confiance | **non** | à maquetter par famille |
| Thème sombre, contraste élevé, grande police, 1024 et 800 px | partiels (captures sombres pour cinq écrans) | à généraliser |

## Ordre proposé

1. **Socle** (un lot, sans changement d'écran) : `globals.css` et les
   primitives `components/ui` (Button, Input, Select, Textarea, FormField,
   DialogShell, Spinner, étiquettes) alignés sur `base.css` ; classes
   utilitaires nommées comme la DA (`.carte`, `.ligne`, `.etiquette`,
   `.segments`, `.champ`, `.tableau`, `.vide`, `.alerte`) exposées en
   composants React, pas en CSS global copié. Coque : barre, rail, colonne,
   composeur avec établi. Gardes : `typographie.test.ts` (plancher 14 px),
   tests de contraste existants, un test de véracité « chaque primitive
   consomme un jeton, aucune couleur en dur ».
2. **Écrans maquettés**, dans l'ordre de la DA et un écran par lot : accueil,
   tiroir, contacts et pipeline, devis et factures, projets et tâches,
   décision, agenda, paramètres. Pour chacun : critères de recette de la page
   DA (« Ce que l'écran doit réussir »), « déjà décidé côté UX, pas à rejuger »,
   états maquettés reproduits, captures avant/après en clair, sombre, contraste
   élevé, aux trois largeurs.
3. **Écrans sans maquette** : Syn produit d'abord la maquette avec le même
   générateur (`build.py`, fragments, `ecrans.json`) pour Email (le plus gros,
   cité par Ludo), Documents, Fichiers, Atelier, Mise en route, puis les
   familles de canevas et de couches ; Ludo tranche page par page sur la
   prévisualisation, comme pour les huit premières ; intégration ensuite.
4. **Recette** : campagne de personas sur la pile jetable, audit visuel des
   rondes (balayage DOM, console, réseau), Grok en contradicteur du design
   AVANT le code de chaque lot (rituel « design avant code »), puis revue du
   diff avant la release.

## Ce que ce plan ne fait pas

- Il ne change aucun comportement : les tests de comportement (3 392 pytest,
  1 994 vitest, 99 parcours e2e) restent la vérité ; un lot DA qui en rougit
  un est un lot à refaire.
- Il ne rejuge pas ce que les pages DA marquent « déjà décidé côté UX ».
- Il ne touche pas aux propositions P-058 à P-065, qui attendent la décision
  de Ludo au portail humain.

## Estimation

| Lot | Taille | Risque |
|---|---|---|
| Socle + coque | grand (deux à trois jours de boucle) | régressions de mise en page sur toutes les vues ; à mesurer par les rondes visuelles |
| Huit écrans maquettés | moyen chacun | états multiples ; le Board et l'Agenda ont des tests de comportement denses |
| Maquettes manquantes (Syn) puis intégration | grand (Email seul vaut un écran maquetté et demi) | dépend des décisions de Ludo page par page |

## Décisions attendues de Ludo

1. L'ordre ci-dessus (socle d'abord, puis les huit écrans, puis les maquettes
   manquantes) ou un écran prioritaire (Email ?) avant le socle.
2. Les maquettes manquantes sont produites par Syn sur DQ SYN avec le même
   générateur, et validées sur la prévisualisation, avant intégration.
3. Une release par lot d'écrans (0.71, 0.72…) ou une seule release DA.
