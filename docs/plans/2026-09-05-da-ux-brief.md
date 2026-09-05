# Brief DA et UX de THÉRÈSE, 5 septembre 2026

> Écrit par Claude Code (CLAUCLAU) pour le rituel coco-et-clauclau : COCO le
> démonte avant toute maquette. Ludo veut des propositions qualitatives de
> direction artistique et d'expérience, écran par écran, déposées sur DreamQuest
> à côté de la refonte DA de synoptia.fr, pour trancher oui / non / plus tard.

## 1. Ce qui existe et fait foi

- **DA validée en mai 2026, relue le 30/08** : `docs/audits/2026-08-30-planche-da.html` (+ `.png`).
  Mode clair « Équilibre » par défaut, mode sombre « Signature ». Geste principal =
  pilule de remplissage cyan `#22D3EE` avec encre `#06121F`, rayon 14 px. Titres en
  Plus Jakarta Sans (26/800, 19/700, 16/700), corps en Inter 14 (600 pour une action,
  400 pour le courant), métadonnées Inter 12/500 atténué. Plancher : rien d'important
  sous 14 px. Quatre couleurs de domaine (agenda cyan, tâches ambre, factures magenta,
  prospects violet) avec leur teinte. Deux rayons (8 px champs et puces, 14 px boutons,
  cartes, panneaux) plus le plein pour les étiquettes.
- **Jetons réels** : `src/frontend/src/styles/globals.css` (bloc `@theme` clair,
  `[data-theme="dark"]`, `[data-high-contrast="true"]`). Fond clair `#F3F6FC`, surface
  `#FFFFFF`, texte `#101C36`, atténué `#526178`, accent texte `#0E7490`, anneau `#0F8FB3`,
  sémantiques assombris pour AA. Polices embarquées (hors ligne) : Inter, Plus Jakarta
  Sans, JetBrains Mono.
- **`docs/rules/RULES-DESIGN.md` est périmé** : il décrit encore le « Dark Glassmorphism »
  de janvier (fond `#0B1226` par défaut, boutons `#2451FF`, police système). L'application
  est claire par défaut depuis la 0.60. Sa section 13 (lexique des surfaces) reste valable.
  Le brief propose sa réécriture.
- **Tests de charte qui ferment la porte** (`src/frontend/src/styles/*.test.ts`) : contraste
  4,5:1 de chaque jeton texte sur sa propre teinte composée à 30 % ; encre d'accent
  10,43:1 sur le remplissage cyan ; rayons limités à `sm`, `md`, `full` ; Inter, Jakarta
  et mono déclarés en dépendances ; aucune opacité sur du texte ; anneau de focus 3:1 au
  moins ; tailles typographiques par jetons ; couleurs du splash alignées. Toute
  proposition doit passer ces tests avant d'atteindre DreamQuest.
- **Règles UX déjà décidées, à ne pas rejuger** : plan du 27/08 (`docs/plans/2026-08-27-*`) :
  noms des surfaces (Agenda, Devis et factures, Décision, Améliorer THÉRÈSE ; canevas
  « Préparer un rendez-vous », « Facturer un client » ; boutons « Voir tout mon agenda »
  au lieu de « Ouvrir Agenda ») ; retour déterministe ; cartes du tiroir qui ouvrent leur
  destination ; suppression confirmée ; états indisponibles distincts des états vides.
  Propositions acceptées par Ludo en attente d'implémentation : P-001 (contraste du bleu
  d'agent), P-002 (adresses et badges de la vue Mémoire lisibles), P-009, P-011, P-015,
  P-027, P-030 (formulations et traces). Dette assumée : 257 champs stylés à la main face
  à 4 primitives de formulaire jamais importées ; 73 % du texte nommé en 12 px ; 29
  éléments interactifs visibles par défaut sur l'accueil ; 90 puces de jargon.
- **Matière visuelle** : 92 captures de la 0.66 dans
  `docs/presentation/_build/shots-web/` (1300 px, JPEG), une par écran et par état,
  dont quatre en thème sombre (30 à 33). Le guide de présentation (31 pages) les
  commente : `docs/presentation/THERESE-0.66-guide-de-presentation.pdf`.

## 2. La refonte DA de synoptia.fr, en cours sur DreamQuest

La finale retenue par le jury du 05/09 (page `syn/finale.html` de la prévisualisation)
pose : papier `#FAFAF7`, encre `#0F172A`, encre secondaire `#475569`, filet `#E2E4E9`,
navy `#0B1226` avec lueur `#E6EDF7` pour les blocs sombres, bleu `#2451FF`, cyan
`#22D3EE` (encre cyan `#0891B2`), magenta `#DB2777`, violet `#7C3AED`, vert `#059669`,
ambre `#D97706`, un dégradé « couture » bleu, cyan, vert, ambre, magenta, violet.
Typographie : Instrument Serif pour les titres (400, interlettrage -0,012 em), Inter
pour le corps, IBM Plex Mono pour les données. Structure « deux mondes » : colonne
humaine sur papier, colonne assistant sur navy.

THÉRÈSE partage déjà la palette d'accents (cyan, magenta, violet, navy) mais pas le
registre : fond bleuté `#F3F6FC` au lieu du papier, Jakarta au lieu d'un serif, aucun
dégradé de marque à l'écran.

## 3. La question stratégique que les directions doivent trancher

Une application de travail quotidien peut-elle adopter le registre éditorial du site
(papier, serif, couture) sans perdre en lisibilité et en densité ? Trois directions,
volontairement distinctes pour que Ludo juge une différence délibérée :

1. **Continuité** : THÉRÈSE parle la langue du site. Papier `#FAFAF7`, encre `#0F172A`,
   Instrument Serif sur les titres de page et de carte seulement, Inter partout ailleurs,
   couture en filet de 3 px sur la barre de titre et les cartes actives, colonne
   assistant sur navy dans la conversation. Risque : serif à 16 px sur écran, densité
   des listes, contraste des accents sur papier (à calculer).
2. **Application affinée** : la DA de mai poussée au bout, sans emprunt au site. Jakarta
   et Inter, fond `#F3F6FC`, pilule cyan, quatre domaines. Ce qui change : hiérarchie
   (14 px plancher réel, titres plus grands), respiration (grille 8 px, marges 24 et 32),
   états vides dessinés, un seul geste principal par écran, tiroir et rail unifiés,
   micro-interactions sobres (spring 300/30, 150 ms). Risque : ne pas assez marquer la
   marque ; Ludo trouve l'app « comme Claude et ChatGPT ».
3. **Hybride « deux mondes »** : l'app garde ses jetons et ses polices, mais la
   conversation adopte la structure du site : ce que dit l'humain sur papier, ce que
   fait THÉRÈSE sur navy avec lueur, couture verticale de 4 px entre les deux ; les vues
   d'administration (contacts, devis, agenda) restent claires et denses. Instrument
   Serif réservé au « Bonjour Marie » et aux titres de section de l'atelier
   documentaire. Risque : deux registres dans une même fenêtre, transitions clair/navy.

Dans chaque direction, le thème sombre « Signature » doit exister au même niveau
(les captures 30 à 33 montrent l'existant) et le mode contraste élevé doit rester
possible.

## 4. Les huit écrans à traiter (capture de référence)

| Écran | Capture 0.66 | Ce que l'écran doit réussir |
|---|---|---|
| Accueil conversationnel, brief du jour | 07, 51 | dire en une seconde ce qui attend Marie aujourd'hui, un seul geste principal, composeur qui ne recouvre rien |
| Tiroir des conversations et catalogue | 92, 11 | retrouver, relancer, comprendre les 30 capacités sans lire 90 puces |
| Contacts et pipeline | 36, 15, 16 | lire une fiche, faire glisser une étape, voir la prochaine relance |
| Devis et factures, nouveau devis | 18, 80, 79 | statut lisible, montants alignés, PDF conforme, thème sombre 30 |
| Projets et tâches | 10, 57, 58 | colonnes et liste, échéances civiles, une tâche se crée en trois secondes |
| Décision (Board) | 41, 90, 89 | cinq avis lisibles, synthèse mise en avant, Markdown rendu |
| Agenda | 86, 87, 88 | mois et semaine, ligne de l'heure, création sans modale imbriquée |
| Paramètres | 21, 22, 29 | neuf rubriques, clé de service visible sans la dévoiler, coûts |

Chaque écran sera livré en HTML et CSS réels (pas des images), aux jetons proposés,
clair et sombre, à 1280 px et à 1024 px, navigable au clavier, avec les états vide et
erreur pour au moins l'accueil et les devis.

## 5. Ce que l'on attend de la passe COCO

1. Démonter la question stratégique : laquelle des trois directions est intenable, et
   pourquoi, en s'appuyant sur les jetons et les tests réels.
2. Calculer ou faire calculer les contrastes que le brief affirme ou suppose (encre
   cyan sur papier, magenta sur papier, lueur sur navy, texte sur teintes de domaine
   à 30 %).
3. Dire ce qu'un directeur artistique ambitieux pousserait dans les limites des tests :
   mouvement, couture, typographie, matière (grain, ombres), transitions clair/navy.
4. Lister ce que le brief oublie : accessibilité (réduction de mouvement, tailles
   utilisateur small/medium/large, contraste élevé), Windows et Linux (polices, ClearType,
   DPR 1), fenêtre 1024 px, densité des listes longues, impression PDF.
5. Verdict sur la méthode de dépôt : une page par écran, avant à gauche et après à
   droite, trois directions en onglets, décisions oui / non / plus tard par écran.

## 6. Réponse à la passe COCO (05/09, 12:10) : ce qui change

Verdict `docs/plans/2026-09-05-da-ux-brief-verdict-coco.md` (GO avec réserves, 13 findings,
tous vérifiés contre le code cité). Décisions prises :

1. **Direction 2 « Application affinée » devient le socle** de toutes les maquettes ; les
   directions 1 et 3 sont des variantes explorées sur trois écrans discriminants (accueil,
   devis, décision) avant toute extension.
2. **Les encres de THÉRÈSE restent** : `#0E7490` et `#BE1A72` (les encres du site donnent
   3,52:1 et 4,40:1 sur papier). Le papier `#FAFAF7` est admissible comme fond ; le violet
   `#7C3AED` passe sur papier mais pas sur navy, donc jamais constant entre thèmes.
3. **Instrument Serif** n'entre que par un jeton distinct (`--font-family-editorial`),
   embarqué localement, réservé aux grands titres éditoriaux (« Bonjour Marie », titres de
   section de l'atelier) ; Jakarta reste en tête de `--font-family-display`.
4. **Les maquettes partagent les jetons réels** : `maquettes/da/tokens.css` est extrait de
   `globals.css` (clair, sombre, contraste élevé) par script, et chaque proposition déclare
   ses paires texte/fond, contrôlées par calcul avant dépôt (4,5:1, 7:1 en contraste élevé,
   3:1 pour focus et sélection).
5. **Conditions de comparaison** imposées à chaque maquette : trois tailles racine (14, 16,
   18 px), deux thèmes, contraste élevé, réduction de mouvement, largeurs 1280, 1024 et
   800×600, noms longs et listes de plusieurs centaines d'éléments sur les vues de liste.
6. **Deux rythmes** dans le même système : lecture confortable pour une synthèse, densité
   maîtrisée pour les listes ; « un geste principal » = priorité visuelle, sans disparition
   des autres actions ni des confirmations.
7. **Critères par écran** repris du finding 9 (contacts hors pipeline accessibles, Jour et
   Liste de l'agenda, statuts d'envoi / paiement / échéance distincts, synthèse du Board
   présentée tôt, clé masquée / invalide / service indisponible distingués).
8. **Méthode de dépôt** : bascule avant / après à l'échelle 1:1 (côte à côte seulement si la
   largeur le permet), sélecteur de largeur, décision « socle commun » (polices, couleurs,
   rail, boutons, tiroir) avant les décisions par écran, chaque décision datée avec direction
   et réserve ; « plus tard » conserve l'existant.
9. **Coût annoncé par direction** (estimation COCO, hors PDF ReportLab) : affinée 10 à 18
   jours, continuité corrigée 18 à 30, deux mondes 20 à 35.
10. **`docs/rules/RULES-DESIGN.md` sera réécrit** sur la DA de mai et les jetons réels, avec
    les trois mentions « observé sur capture », « présent dans le code », « vérifié au rendu ».
