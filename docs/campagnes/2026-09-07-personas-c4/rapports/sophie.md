# Sophie, formatrice indépendante : trace de la campagne

> Campagne « chaque écran, chaque persona », cycle 4, 08/09/2026 (nuit du 07 au 08).
> Frontend `http://localhost:1420` (worktree `Synoptia-THERESE-repair`, branche `repair/c4-lot1`),
> moteur `http://127.0.0.1:17393`, `THERESE_DATA_DIR=/tmp/therese-demo-c4`.
> Viewport 1280×800, DPR 1, thème clair, locale fr-FR, fuseau Europe/Paris, souris et clavier,
> **taille de police « grande »** posée en préalable et remise à « moyenne » à la fin.
> J'arrive après Jean et Karim : le profil est celui de Jean, il y a un projet
> (« Refonte du site Démo »), un contact, une tâche, un événement, une conversation. **Aucun document
> d'atelier n'existait** : l'état vide est photographié (capture `07`, `GET /api/documents` → `[]`)
> avant que je crée le mien.

## L'application n'était pas figée

Pendant mon parcours, **un autre agent modifiait du code backend et des tests dans le même dépôt**
(pas les sources de l'interface). Les extraits de code que je cite ont été lus au moment indiqué et
peuvent avoir bougé depuis. Le moteur, lui, n'a pas été redémarré pendant la session : le processus
qui a servi mes requêtes est celui lancé à 23:33.

## Écart d'instrument (à lire avant les constats)

Le serveur MCP Playwright annoncé (`mcp__plugin_playwright_playwright__*`) **n'est pas exposé** à
cette session. Même méthode que Jean et Karim : **Playwright Node piloté en CDP**. Un lanceur
`chromium.launchPersistentContext` (headless, 1280×800, DPR 1, `locale: 'fr-FR'`,
`colorScheme: 'light'`, `timezoneId: 'Europe/Paris'`, `--remote-debugging-port=9222`) reste vivant
pendant tout le parcours et porte les écouteurs `console`, `pageerror`, `requestfailed`,
`response >= 400`, `download` et **toute requête `/api/` non-GET**. Chaque geste se connecte par
`connectOverCDP` sur le même onglet, prend la capture, écrit l'arbre d'accessibilité complet dans un
fichier annexe et relève `document.activeElement` ainsi que les titres visibles. Playwright 1.58.2,
chromium-1208. Cet écart relève du contexte de mesure, pas du comportement de l'application.

**Garde d'environnement, avant le premier geste** :
`({ visible: document.visibilityState, horloge: document.timeline.currentTime })`
→ `{"visible":"visible","horloge":18943.3,"w":1280,"h":800,"dpr":1,"lang":"fr-FR"}`.
Document visible, horloge d'animation non nulle : parcours autorisé.

**Stockage NON purgé**, sur consigne de l'orchestrateur. Contrôle d'entrée écran/moteur fait
(capture `01`) ; ma propre vérification par `fetch` a rendu un 401 parce que j'ai lu le jeton depuis
la mauvaise clé de `localStorage` : **c'est mon erreur d'instrument, pas un défaut de l'application**,
et c'est le seul 401 du journal. Le décor a ensuite été confirmé par lecture directe du moteur
(`/api/documents`, `/api/memory/projects`, `/api/config/llm`, `/api/prompts/library`) avec l'en-tête
`X-Therese-Token`.

Aucune clé, aucune donnée réelle, aucun envoi, aucun `POST /api/shutdown`, aucune suppression.
**Toutes les écritures de la session viennent de mes gestes dans l'écran**, et les voici en entier :
`POST /api/documents`, `POST /api/documents/{id}/outline`, `POST /api/documents/sections/{id}/draft`,
`PATCH /api/documents/pistes/{id}`, `POST /api/variables/preview`. Aucune écriture par l'API.

## Mon impression

J'écris pour vivre, et l'atelier m'a donné une vraie bonne surprise : la trame est propre, hiérarchisée,
en français correct, et la section rédigée est publiable telle quelle. Les deux exports existent
réellement sur le disque, avec les accents, les guillemets français et la mise en forme des titres.
Ça, c'est du travail sérieux.

Ce qui m'a coûté, c'est l'attente. Trois minutes vingt pour la trame, trois minutes vingt-quatre pour
une seule section, et pendant tout ce temps l'écran me dit « Aucune section pour l'instant » ou me
montre une page blanche avec un curseur qui clignote. Rien ne me dit que ça travaille, rien ne me dit
combien de temps ça va prendre, rien ne me dit que le modèle local est lent. J'ai cru deux fois que
c'était planté. On m'avait promis une rédaction qui s'écrit sous mes yeux ; j'ai eu un écran vide puis
un texte qui tombe d'un coup.

Ensuite, deux petites choses qui font perdre confiance. J'ai cliqué « Explorer » sur une piste : elle
a disparu dans « Pistes traitées », et rien d'autre. J'ai dû fouiller pour comprendre que le texte de
la piste avait été déposé dans un champ situé sous la ligne de flottaison, large de cent quarante
pixels pour un texte qui en fait quatre cent soixante-neuf. Et quand j'insère un modèle de prompt, on
me dit « 0 variable résolue, inconnues : {nom_client}, {nombre_jours}… » sans me proposer nulle part
de les renseigner. J'ai fini par réécrire mes valeurs à la main dans le message, ce que le modèle
était censé m'éviter.

Enfin, l'écran « Livrables et suivi client » me propose cinq filtres par statut pour des livrables
que je ne peux créer nulle part. Le panneau est honnête, il annonce « sans modifier les données » ;
c'est l'ensemble qui ne l'est pas, puisqu'aucun autre écran ne le permet non plus.

## Parcours

### Accessibilité : passer la police en « grande » avant tout le reste

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 01 | Contrôle d'entrée sur l'accueil | écran cohérent avec le moteur | « Bonjour Jean. », brief à 0 élément, établi à 4 verbes ; focus sur `BODY` | `01` | ok |
| 02 | Ouvrir les Paramètres (roue crantée du rail) | panneau Paramètres | Paramètres, focus donné à « Fermer les paramètres », six onglets | `02` | ok |
| 03 | Onglet « Accessibilité » | réglages de confort | Apparence, Réduire les animations, Taille de police, Contraste élevé, raccourcis | `03` | ok |
| 04 | Clic « Grande » | tout grossit | `font-size` racine 16 px → 18 px, `--therese-root-font-size: 18px`, `therese-accessibility.fontSize = "large"` | `04` | ok |
| 05 | Fermer, revenir à l'accueil | effet visible partout | effet confirmé sur l'accueil entier | `05` | ok |
| 41 | En fin de parcours, clic « Moyenne » | retour à l'état initial | `font-size` 18 px → 16 px, `fontSize: "medium"` | `41` | ok |

Arbre d'accessibilité, étape 04 : le focus reste sur « Fermer les paramètres » ; la liste des tailles
est annoncée comme trois boutons, sans état sélectionné annoncé (pas de `aria-pressed` relevé).

### Atelier documentaire : de la trame vide au fichier Word

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 06 | ⌘K puis « atelier » | trouver l'atelier | 2 résultats ; la surface s'appelle **« Documents »**, pas « Atelier » | `06` | observation |
| 07 | « Ouvrir les Documents » | écran vide expliqué | « 0 document », phrase d'accueil, deux boutons « Nouveau document » ; `GET /api/documents` → `[]` | `07` | ok, état vide photographié |
| 08 | « Nouveau document » | formulaire | Titre obligatoire, Brief, « Projet lié (optionnel) » avec « Refonte du site Démo » | `08` | ok |
| 09 | Saisie titre accentué + brief + projet lié | champs conservés | conservés, guillemets français et apostrophe typographique acceptés | `09` | ok |
| 10 | « Créer » | document ouvert, trame lancée | document ouvert, `POST /api/documents` puis `POST …/outline` à 00:34:17 ; le panneau affiche « **Aucune section pour l'instant.** » et un bouton « Générer la trame » grisé | `10` | **sophie-01** |
| 11 | Attendre 20 s | savoir que ça travaille | toujours « Aucune section pour l'instant. » ; seule trace d'activité : un glyphe gris dans le bouton désactivé | `11` | **sophie-01** |
| 12 | Attendre 50 s | idem | idem, rien de neuf | `12` (attente à 50 s) | **sophie-01** |
| 13 | Attendre encore | trame | trame arrivée à **00:37:37,92** (date de création des 15 sections en base), soit **3 min 20,8 s** après le clic : 15 sections hiérarchisées, toutes « VIDE » ; `sections_total` 0 → 15 | `13` | ok (contenu), voir sophie-01 |
| 14 | « Exporter .md » sur un document sans contenu | refus lisible | 400, message « Document vide : rien à exporter. » affiché dans la colonne Trame, à 440 px du bouton cliqué | `14` | ok (refus juste), voir sophie-05 |
| 15 | Ouvrir la section « Introduction et objectifs pédagogiques » | éditeur de section | éditeur, consigne préremplie, barre « Rédiger / Retoucher / Valider » ; **le message d'erreur d'export s'affiche une deuxième fois** ici | `15` | **sophie-05**, **sophie-04** |
| 16 | « Rédiger », attendre 20 s | texte qui s'écrit | rien : corps vide, un curseur cyan, tous les contrôles désactivés, badge encore « VIDE » | `16` | **sophie-02** |
| 17 | Attendre 90 s | au moins un tiers du texte | toujours rien ; l'arbre d'accessibilité contient un `- status` **vide** | `17` | **sophie-02** |
| 18 | Attendre la fin | texte complet | texte complet d'un coup à **3 min 24 s** (00:38:53 → 00:42:17), badge « BROUILLON », 2 pistes apparues | `18` | ok (contenu), voir sophie-02 |
| 19 | Lire le volet Pistes | pistes utiles | 2 pistes pertinentes, chacune avec « Explorer » et « Ignorer » | `19` | ok |
| 20 | « Explorer » la première piste | comprendre ce qui se passe | la piste passe en « Pistes traitées (1) », `PATCH …/pistes/{id}` → `status: "exploree"` ; **aucun autre effet visible** | `20` | **sophie-03** |
| 21 | Défiler jusqu'en bas de l'éditeur | retrouver l'effet | le texte de la piste a été déposé dans « Instruction de retouche », qui était à `y = 1247` dans une fenêtre de 800 px ; champ de 139 px pour 469 px de contenu | `21` | **sophie-03**, **sophie-04** |
| 22 | « Exporter .md » | fichier réel | téléchargement déclenché **et** fichier écrit côté moteur : `/tmp/therese-demo-c4/outputs/Programme de formation _ Rédiger avec l_IA __ef4a218a.md`, 2 215 o | `22` | ok, voir sophie-P1 |
| 23 | « Exporter .docx » | fichier réel | idem : `…__65ec6f0d.docx`, 38 510 o, OOXML valide, 27 passages de texte, titre et accents intacts | `23` | ok, voir sophie-P1 |

Contrôle du contenu exporté (hors écran, lecture disque) : le `.md` commence par
`# Programme de formation « Rédiger avec l’IA »` puis `## Introduction et objectifs pédagogiques` ;
le `.docx` contient le même titre, les intertitres et les puces en gras. Les quatorze sections restées
vides sont omises, ce qui est cohérent avec le refus d'exporter un document entièrement vide.

### Bibliothèque de prompts : insérer un modèle à variables et le remplir

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 24 | ⌘K puis « prompt » | trouver la bibliothèque | 2 résultats, dont « Bibliothèque de prompts » | `24` | ok |
| 25 | Ouvrir | catalogue | « 34 prompts prêts à l'emploi », classés par catégorie, focus donné au champ de recherche | `25` | ok |
| 26 | Chercher « formation » | des modèles pour mon métier | « 0 résultats pour "formation" », état vide expliqué avec un conseil | `26` | **sophie-10** (proposal) |
| 27 | Chercher « relance » | résultats | 3 résultats, dont « Relance client en attente » | `27` | ok |
| 28 | « Utiliser » | prompt dans le composeur | prompt inséré dans une nouvelle conversation ; bandeau « **0 variable résolue — inconnues : {nom_client}, {nombre_jours}, {sujet}, {prenom}, {nom_entreprise}** » | `28` | **sophie-06** |
| 29 | Cliquer le bandeau | un moyen de renseigner les variables | rien : c'est un `DIV` sans rôle, sans titre, `cursor: auto` | `29` | **sophie-06** |
| 30 | Réécrire les valeurs à la main dans le message | bandeau qui suit | le bandeau disparaît dès qu'il ne reste plus de `{…}` ; `POST /api/variables/preview` | `30` | ok |

### Livrables et suivi client : créer un livrable lié au projet, changer son statut

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 31 | ⌘K puis « livrable » | trouver l'écran | 1 résultat : « Livrables et suivi client - Relier ce qui a été promis, livré, facturé et reste à faire. » | `31` | ok |
| 32 | Ouvrir | écran des livrables | bandeau « LECTURE LOCALE UNIFIÉE », sous-titre « …**sans modifier les données** », projet suivi « Refonte du site Démo », compteurs à 0 | `32` | ok (honnêteté du panneau) |
| 33 | Chercher comment créer un livrable | un bouton de création | **aucun** : les seuls contrôles sont le sélecteur de projet, cinq filtres de statut (« Tous / À faire / En cours / Révision / Validés ») et deux liens « Ouvrir Projets » / « Ouvrir Devis et factures » | `33` | **sophie-07** |
| 34 | « Ouvrir Projets » | fiche projet avec ses livrables | tableau Kanban des projets ; aucune notion de livrable | `34` | **sophie-07** |
| 35 | Cliquer la carte « Refonte du site Démo » | fiche détaillée | aucun détail ne s'ouvre au clic sur la carte | `35` | observation |

### Commande utilisateur au nom accentué

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 36 | Nouvelle conversation, bloc « Produire » | liste des commandes | 9 commandes en pastilles + « Créer une commande » | `36` | ok |
| 37 | « Créer une commande » | assistant | assistant en trois étapes : Réfléchir / Faire / Capturer, champ « Décris ta commande idéale... » | `37` | ok |
| 38 | Cliquer directement l'étape « Capturer » | atteindre la nomination | sans effet : les étapes ne sont pas des raccourcis | `38` | observation |
| 39 | Saisir le brief (« …Nom souhaité : Résumé de réunion. ») | brief pris en compte | texte saisi dans le composeur de l'assistant | `39` | ok |
| 40 | « Passer à Faire » | étape suivante | **bouton désactivé**, sans explication ; l'écran empile deux composeurs (celui de l'assistant et celui du chat) avec deux boutons d'envoi, et l'en-tête d'étapes est sorti de l'écran | `40` | **sophie-09** ; transition non couverte |

## Console et réseau, sur toute la session

- **Zéro `pageerror`.**
- **Deux réponses HTTP ≥ 400** : le 401 de mon `fetch` mal authentifié (instrument) et le 400 attendu
  de l'export d'un document vide.
- **Une erreur console applicative** : à 00:48:42, `Cannot update a component (HomeCommands) while
  rendering a different component (CommandExecutor). To locate the bad setState() call inside
  HomeCommands, follow the stack trace…` déclenchée en ouvrant le bloc « Produire ».
- Les dix `[API] IPC échoué, retry n/10…` du démarrage sont reproduits à l'identique : déjà fichés par
  Jean sous **jean-P6**, je ne les refiche pas.
- Deux `download` déclenchés par les exports ; l'échec de `saveAs` côté Playwright vient de mon
  lanceur, pas de l'application (le fichier existe côté moteur).

## Constats numérotés

- **sophie-01 - P2 - la génération de la trame se cache derrière l'état vide (bug_candidate).**
  Préconditions : un document venant d'être créé. Étapes : Documents → Nouveau document → remplir →
  Créer. Attendu : un état de chargement nommé, court ou annoncé comme long. Observé : pendant
  **3 min 20,8 s** (`POST …/outline` à 00:34:17,09 ; les 15 sections portent `created_at`
  00:37:37,92), la colonne Trame affiche
  « Aucune section pour l'instant. » avec un bouton « Générer la trame » désactivé portant un glyphe
  gris de 16 px, et le volet central affiche « Sélectionne une section dans la trame pour la rédiger. »
  Aucun texte ne dit qu'un travail est en cours, aucune durée n'est annoncée, aucun moyen d'annuler.
  Preuve : captures `10` (3 s), `11` (20 s), `12` (50 s, fichier
  `12-atelier-trame-attente-50s.png`), `13` (fin) ; journal réseau ;
  `GET /api/documents` `sections_total` 0 puis 15. C'est la règle « chargement visible et court, ou
  expliqué » du protocole qui n'est pas tenue, et l'état vide qui ment sur ce qui se passe.

- **sophie-02 - P2 - la rédaction annoncée « en streaming » n'affiche rien pendant 3 min 24 s
  (bug_candidate).** Préconditions : une section vide sélectionnée. Étapes : ouvrir une section →
  « Rédiger ». Attendu : le texte s'écrit au fil de l'eau. C'est la promesse
  écrite du produit (`CLAUDE.md`, Modules fonctionnels : « Atelier documentaire (trame, rédaction
  guidée par section **en streaming**, pistes, export md/docx) ») et le contrat documenté du
  `documentStore` (« le contenu est mis à jour AU FIL DE L'EAU, chunk par chunk »). Observé : à 20 s
  et à 90 s, le corps de l'éditeur est **vide** avec un unique curseur clignotant ; le badge de la
  section reste « VIDE » ; tous les contrôles sont désactivés ; l'arbre d'accessibilité contient un
  nœud `- status` **sans texte**, donc rien n'est annoncé à une synthèse vocale. Le texte complet
  (environ 500 mots) apparaît d'un seul coup à 3 min 24 s (`POST …/draft` à 00:38:53, pistes créées à
  00:42:17). Preuve : captures `16`, `17`, `18`, extrait de l'arbre d'accessibilité de l'étape 17.
  Je ne conclus pas sur la cause (modèle local qui produit une phase non transmise, ou absence de
  transmission des fragments) ; je constate qu'aucun caractère n'atteint l'écran avant la fin et que
  rien n'occupe l'utilisateur pendant ce temps.

- **sophie-03 - P2 - « Explorer » une piste dépose son texte hors de l'écran (bug_candidate).**
  Préconditions : une section rédigée, donc assez longue pour remplir le volet. Étapes : volet Pistes
  → « Explorer » sur une piste. Attendu : un effet visible. Observé : la piste bascule dans « Pistes
  traitées », `PATCH …/pistes/{id}` → `status: "exploree"`, et le seul autre effet est le
  préremplissage du champ « Instruction de retouche », mesuré à `y = 1247` dans une fenêtre de 800 px
  de haut (`dansEcran: false`). Rien ne défile jusqu'à lui, rien ne le signale. Preuve : captures `20`
  et `21`, mesure de la boîte englobante, arbre d'accessibilité de l'étape 20 (`textbox "Instruction
  de retouche" … text: Création d'une charte d'utilisation interne après la formation`).
  Fichier suspecté (lu) : `src/frontend/src/components/documents/DocumentWorkspace.tsx` et
  `SectionEditor.tsx` (`instructionPrefill`) : le comportement est conforme à l'intention documentée,
  c'est sa visibilité qui manque.

- **sophie-04 - P2 - le champ « Instruction de retouche » cache 70 % de son contenu (bug_candidate).**
  Étapes : ouvrir une section, regarder la barre d'action. Observé : champ de **139 px** de largeur
  utile pour un `scrollWidth` de **469 px** ; le libellé lui-même est amputé à l'affichage
  (« Instruction de re »), alors que le placeholder complet vaut « Instruction de retouche (ex. plus
  concis, ajouter un exemple...) ». En police « grande » (15,75 px de corps), une consigne de retouche
  d'une ligne n'est jamais lisible en entier. Preuve : captures `15` et `21`, mesures
  `clientWidth`/`scrollWidth`.

- **sophie-05 - P3 - l'erreur d'export s'affiche deux fois, et loin du geste (bug_candidate).**
  Étapes : document sans contenu → « Exporter .md ». Observé : « Document vide : rien à exporter. »
  apparaît **à la fois** en tête de la colonne Trame et dans l'éditeur de section, avec un bouton
  « Reprendre » qui laisse croire à un échec de rédaction. Le bouton cliqué est en haut à droite, le
  message en haut à gauche. Preuve : captures `14` et `15`. Correspond à la dette déjà écrite dans
  `CLAUDE.md` (« `error` du documentStore est mono-slot… rendue à la fois dans `OutlineTree` ET
  `SectionEditor` ») : constatée ici à l'écran, avec en plus le libellé « Reprendre » qui ne
  correspond pas à l'échec réel.

- **sophie-06 - P2 - « inconnues : {nom_client}… » nomme un manque sans donner le moyen de le combler
  (bug_candidate).** Préconditions : bibliothèque de prompts ouverte. Étapes : chercher « relance » →
  « Utiliser » sur « Relance client en attente ». Observé : bandeau « 0 variable résolue - inconnues :
  {nom_client}, {nombre_jours}, {sujet}, {prenom}, {nom_entreprise} », qui est un `DIV` sans `role`,
  sans `title`, `cursor: auto`, donc non cliquable ; aucun bouton, aucun lien, aucune mention de
  l'endroit où définir ces variables. Le bouton d'envoi reste actif : rien n'empêche d'expédier un message contenant cinq `{…}` non
  résolus (je ne l'ai pas envoyé, je constate seulement que rien ne s'y oppose). Preuve :
  captures `28` et `29`, inspection du nœud. La grille du protocole demande une erreur « qui dit quoi
  faire » ; ici le diagnostic est juste et l'action absente.

- **sophie-07 - P2 - des filtres par statut pour des livrables qu'aucun écran ne permet de créer
  (bug_candidate).** Étapes : ⌘K « livrable » → « Livrables et suivi client ». Observé : l'écran
  affiche cinq filtres (« Tous / À faire / En cours / Révision / Validés »), trois compteurs à 0 et
  « Aucun livrable réel n'est encore rattaché à ce projet », sans aucun bouton de création ni de
  changement de statut ; le panneau assume sa lecture seule (« sans modifier les données »,
  « Lecture seule depuis Projets, CRM, Tâches et Facturation »). « Ouvrir Projets » mène à un Kanban
  qui ignore la notion de livrable. Preuve : captures `32`, `33`, `34`, relevé exhaustif des
  contrôles visibles. Corroboration par le code lu : `createDeliverable` et `updateDeliverable` sont
  exportés par `src/frontend/src/services/api/crm-extended.ts` et réexportés par `services/api/index.ts`,
  mais **aucun fichier de `components/` ni de `stores/` ne les importe** ; `DeliverablesList.tsx`
  n'affiche que des lignes. La capacité annoncée dans la palette (« Relier ce qui a été promis,
  livré, facturé et reste à faire ») ne peut donc jamais commencer.

- **sophie-08 - P3 - erreur React à l'ouverture du bloc « Produire » (bug_candidate).** Étapes :
  nouvelle conversation → « Produire ». Observé, console : `Cannot update a component (HomeCommands)
  while rendering a different component (CommandExecutor). To locate the bad setState() call inside
  HomeCommands, follow the stack trace…`, à 00:48:42. Sans conséquence visible pour moi, mais c'est un
  `setState` pendant le rendu, donc un rendu non déterministe possible. Preuve : journal console.

- **sophie-09 - P3 - l'assistant de création de commande empile deux composeurs et bloque sans dire
  pourquoi (bug_candidate).** Étapes : « Produire » → « Créer une commande » → saisir un brief →
  « Passer à Faire ». Observé : deux zones de saisie superposées avec chacune son bouton d'envoi
  (celle de l'assistant, celle du chat), l'en-tête d'étapes « Réfléchir / Faire / Capturer » sorti de
  l'écran une fois le brief saisi, et un bouton « Passer à Faire » **désactivé** sans message
  expliquant qu'il faut d'abord envoyer le brief. Preuve : captures `37`, `39`, `40`.

- **sophie-11 - P2 - les deux générations de l'Atelier ne sont comptées nulle part (bug_candidate).**
  Préconditions : moteur en `THERESE_DATA_DIR=/tmp/therese-demo-c4`. Étapes : créer un document (trame
  générée automatiquement) puis « Rédiger » une section. Attendu : les jetons consommés apparaissent
  dans le suivi de consommation, comme pour le chat. Observé : après mes deux appels au modèle
  (200,8 s et 204 s), `token_usage.json` est resté **inchangé depuis 00:16**, avec les seules valeurs
  laissées par la conversation de Karim (`today_input: 12409, today_output: 135`), et le journal du
  moteur ne contient **aucune** ligne `[TOKEN] Recorded` ni `[PERF] Stream complete` pour l'Atelier -
  la seule ligne du fichier est celle du chat de Karim. Un utilisateur qui rédige un dossier entier
  verrait donc un compteur à zéro. Preuve : `cat /tmp/therese-demo-c4/token_usage.json`,
  horodatage du fichier (00:16), `grep -E "PERF|TOKEN" backend.out`. Recoupe l'observation de Jean
  (« les compteurs de Limites & Consommation sont restés à 0 »), mais ici avec deux appels réels au
  modèle derrière.

- **sophie-10 - proposal - une bibliothèque de 34 prompts sans rien pour la formation.** « formation »
  rend 0 résultat ; l'état vide est correct et conseille d'autres mots-clés. Pour une formatrice,
  c'est le premier mot tapé. Preuve : capture `26`. Pour le portail humain, pas un défaut.

- **sophie-P1 - proposal - un export réussi ne dit ni où ni combien.** Les deux exports produisent un
  téléchargement navigateur **et** un fichier côté moteur dans `outputs/`, sans que l'écran indique le
  chemin, la taille ou le nombre de sections retenues. Rejoint **jean-P5** et **jean-P2** (aucun chemin
  absolu du dossier de données nulle part). Preuve : captures `22`, `23`, listage du dossier `outputs/`.

- **sophie-P2 - proposal - le nom de la surface.** La fiche métier et le vocabulaire de l'équipe disent
  « Atelier documentaire » ; l'application dit « Documents » partout (palette, titre, fil d'Ariane).
  Ce n'est pas une violation du lexique verrouillé, c'est un écart entre la documentation interne et
  l'écran, à trancher dans un sens ou dans l'autre. Preuve : captures `06`, `07`.

## Ce que j'ai trouvé juste, et qui mérite d'être protégé

- **La trame produite est réellement exploitable** : quinze sections hiérarchisées sur deux niveaux,
  intitulés en français correct, cohérentes avec le brief que j'avais écrit (capture `13`).
- **Les deux exports existent pour de bon**, et pas seulement à l'écran : `.md` de 2 215 o et `.docx`
  de 38 510 o vérifiés sur le disque, OOXML valide, titre `« Rédiger avec l’IA »` avec ses guillemets
  français et son apostrophe typographique intacts, intertitres et puces mis en forme.
- **Le refus d'exporter un document vide est juste et lisible** (« Document vide : rien à exporter. »),
  au lieu de produire un fichier creux.
- **Les pistes sont pertinentes et rattachées à leur section d'origine** ; « Explorer » et « Ignorer »
  sont deux gestes distincts, et « Pistes traitées » garde la trace de ce qui a été vu.
- **Le bandeau des variables dit la vérité**, et il se met à jour correctement dès que le message ne
  contient plus de `{…}` (capture `30`).
- **Le panneau des livrables n'invente pas ses données** : il annonce sa lecture seule, dit d'où vient
  ce qu'il montre, et refuse de chercher une facturation pour un projet sans contact.
- **La taille de police « grande » agit sur toute l'application** par une variable de racine, pas sur
  une poignée d'écrans (captures `04`, `05`).

## Transitions couvertes et angles morts

| Transition demandée | Résultat |
|---|---|
| **(a)** Atelier : trame, rédaction d'une section en streaming avec le modèle local, pistes, export Markdown puis Word, fichier vérifié sur le disque | **couverte en entier.** État vide photographié (`07`), création (`08`-`10`), trame après 3 min 20,8 s (`13`), section rédigée après 3 min 24 s (`18`), pistes lues et une piste explorée (`19`-`21`), exports `.md` et `.docx` **vérifiés sur le disque** dans `/tmp/therese-demo-c4/outputs/` (`22`, `23`) et contrôlés en contenu. Attente et échec d'export photographiés (`11`, `12`, `14`, `16`, `17`). Défauts : sophie-01 à sophie-05 et sophie-11. |
| **(b)** Bibliothèque de prompts : insertion d'un prompt à variables et remplissage | **couverte, avec une réserve.** Ouverture (`25`), recherche à vide puis fructueuse (`26`, `27`), insertion d'un prompt à cinq variables dans le composeur (`28`), remplissage **à la main** faute d'autre chemin (`30`). Le remplissage guidé n'existe pas : c'est sophie-06. |
| **(c)** Livrables : création liée au projet existant, changement de statut | **partiellement couverte - la création est impossible.** Écran ouvert, lu et photographié (`32`, `33`), projet « Refonte du site Démo » bien reconnu comme périmètre, chemin alternatif « Ouvrir Projets » exploré (`34`, `35`). Aucun livrable n'a pu être créé, donc aucun statut changé. Constat sophie-07, corroboré par le code (`createDeliverable` sans appelant). |
| **(d)** Commande utilisateur « Résumé de réunion » : slug affiché ni vide ni amputé | **NON couverte - angle mort assumé.** L'assistant a été atteint et photographié (`37`, `39`, `40`), le brief saisi porte bien le nom accentué souhaité, mais l'étape de nomination est derrière deux échanges avec le modèle local, à environ trois minutes chacun d'après mes deux mesures du jour ; mon budget de temps était épuisé. **Reproduction** : « Produire » → « Créer une commande » → écrire le brief → **envoyer le message** (le bouton « Passer à Faire » reste désactivé tant que l'assistant n'a pas répondu) → « Faire » → « Capturer », puis relever le champ Nom à l'écran et comparer à `GET /api/commands/user`. Ce que j'ai pu lire du code sans l'exécuter, à titre d'**observation** et non de constat : `valider_nom_de_commande` (`src/backend/app/models/schemas_commands.py`) ne retire ni les accents ni les espaces, il refuse seulement `/`, `\`, les caractères de contrôle et le point initial, et `CreateCommandRequest.name` est borné à 50 caractères ; le nom vient soit de la saisie, soit du modèle à qui `commands_v3.py:141` demande un « name (slug court) ». Le risque d'amputation, s'il existe, se joue donc dans ce que produit le modèle et dans l'affichage, pas dans la validation du moteur. Je ne l'ai pas vu, je ne l'affirme pas. |

**Autres angles morts de cette session** :

- **Studio Images** (objectif 4 de ma fiche) : non ouvert, budget de temps.
- **Voix et transcription** (objectif 5) : non ouvert. L'avertissement de téléchargement du modèle
  local n'a donc pas été photographié.
- **Calculateurs** (objectif 6) : non ouvert, aucun calcul de seuil de rentabilité effectué.
- **Rédaction d'une deuxième section, retouche, validation** : non faites ; le bouton « Valider » n'a
  jamais été actionné, donc le passage « BROUILLON » → « Validé » n'est pas couvert.
- **Réorganisation de la trame par glisser-déposer** : les poignées existent, je ne les ai pas
  utilisées.
- **Comportement en arrière-plan** : non testé, le document est resté visible en permanence, comme
  l'exige la garde d'instrument.
- **Le titre en double d'une conversation de Karim** (« Quelles sont mes tâches ?Quelles sont mes
  tâches ? », vu dans `localStorage.therese-chat`) n'a pas été rejoué à l'écran : je le signale sans
  le ficher, la preuve serait celle d'un autre parcours que le mien.
- **41 captures** pour 41 étapes numérotées, toutes relues. Aucune écriture hors de
  `captures/sophie/` et de ce fichier. Aucun commit.

## Tokens consommés

Côté application, l'atelier a fait travailler le modèle local **deux fois** (génération de la trame,
rédaction d'une section) ; je n'ai envoyé aucun message de chat, et `POST /api/chat/send` n'apparaît
pas dans mon journal d'écritures. Ces deux appels ne sont comptés nulle part : voir sophie-11. La
seule mesure de débit disponible dans le journal du moteur est celle laissée par Karim,
`[PERF] Stream complete: 135 tokens in 69549ms (1.9 tok/s)` sur `gemma4-tia:latest`. Côté session
d'agent, environ **230 000 tokens** consommés, sans mesure exacte disponible.
