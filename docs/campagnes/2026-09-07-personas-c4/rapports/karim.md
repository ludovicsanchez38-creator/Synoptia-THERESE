# Karim, consultant indépendant : trace de la campagne

> Campagne « chaque écran, chaque persona », cycle 4, 07-08/09/2026.
> Frontend `http://localhost:1420` (worktree `Synoptia-THERESE-repair`, branche `repair/c4-lot1`),
> moteur `http://127.0.0.1:17393`, `THERESE_DATA_DIR=/tmp/therese-demo-c4`.
> Viewport 1280×800, DPR 1, thème clair, locale fr-FR, fuseau Europe/Paris, souris et clavier.
> J'arrive après Jean : le profil est le sien, la base contient un contact (Camille) et rien d'autre.

## Écart d'instrument (à lire avant les constats)

Le serveur MCP Playwright annoncé (`mcp__plugin_playwright_playwright__*`) **n'est pas exposé** à cette
session. Il a été remplacé par la même méthode que Jean : **Playwright Node piloté en CDP**. Un lanceur
`chromium.launchPersistentContext` (headless, 1280×800, DPR 1, `locale: 'fr-FR'`, `colorScheme: 'light'`,
`timezoneId: 'Europe/Paris'`, `--remote-debugging-port=9222`) reste vivant pendant tout le parcours et porte
les écouteurs `console`, `pageerror`, `requestfailed`, `response >= 400` et **toute requête `/api/` non-GET**
(c'est ce dernier journal qui prouve qu'un formulaire refusé n'envoie rien). Chaque geste se connecte par
`connectOverCDP` sur le même onglet, prend la capture, puis relève `document.activeElement`, les titres
visibles et l'arbre d'accessibilité. Moteur : chromium-1208 (HeadlessChrome 145). Cet écart relève du
contexte de mesure, pas du comportement de l'application.

**Garde d'environnement, avant le premier geste** :
`({ visible: document.visibilityState, horloge: document.timeline.currentTime })`
→ `{"visible":"visible","horloge":24071.866}`. Document visible, horloge d'animation non nulle : parcours autorisé.

**Stockage NON purgé**, sur consigne de l'orchestrateur (les données du persona précédent font partie du
décor). Le profil de navigateur de Jean n'existait plus, donc le mien est neuf côté navigateur ; comme le
moteur avait déjà `onboarding-complete`, **aucun assistant de mise en route ne s'est affiché** : je suis
tombé directement sur l'accueil, et je n'ai donc eu ni à choisir ni à confirmer Ollama (le moteur répond
déjà `provider: ollama, model: gemma4-tia:latest, available: true`). Contrôle d'accord écran/moteur : le
tiroir affiche « Aucune conversation enregistrée » et `GET /api/chat/conversations` rend `[]` (capture `03` ;
le fantôme du constat jean-04 ne se reproduit pas sur un profil neuf, ce qui confirme qu'il venait bien du
stockage local du navigateur).

Aucune clé, aucune donnée réelle, aucun envoi, aucun `POST /api/shutdown`, aucune suppression. Le jeton n'a
servi qu'en lecture (`GET`). **Toutes les écritures de la session viennent de mes gestes dans l'écran**, et
les voici en entier : `POST /api/tasks`, `PUT /api/tasks/{id}`, `POST /api/memory/projects`,
`POST /api/calendar/events`, `POST /api/chat/conversations`, `POST /api/chat/send`,
`POST /api/variables/preview`. **Aucune réponse HTTP ≥ 400 sur toute la session.**

**Le dépôt a bougé pendant et après mon parcours, il faut le savoir avant de relire mon code cité.**
Mon parcours court de 00:05 à 00:20 ; les numéros de ligne que je cite valent pour l'état du dépôt à ce
moment-là. Depuis, le travail de réparation en cours a modifié une vingtaine de fichiers, dont **deux qui
portent mes constats** : `components/prototype/EmailConversationCard.tsx` et `stores/actionsStore.ts`
(horodatés 00:26). Le diff de la carte e-mail répare exactement mon karim-02, sous la référence **B-596** :
« en rédaction libre il n'y a pas de message source ; `generateDraft` sortait sans rien faire et le bouton
restait actif », et remplace le bouton par la phrase « Rédaction libre : aucune proposition à générer sans
message source. » Mon constat n'est donc pas invalidé, il est confirmé par ailleurs - mais **le bouton que
j'ai photographié n'existe peut-être déjà plus**. Le reste (karim-03, karim-04) portait sur des lignes de
la même carte non touchées par ce diff.

**Le dépôt a bougé pendant mon parcours** : `git status` montre douze fichiers de
`src/backend/app/` modifiés entre 00:18 et 00:20, plus un `tests/test_lot_c4_candidats_backend.py`
non suivi, alors que je n'ai rien écrit hors de mes captures et de cette trace (le diff de
`services/planning.py` porte la mention « B-581 » : c'est le travail de réparation en cours, pas le mien).
Aucun des fichiers touchés n'est sur les chemins de mes constats (palette, e-mail, tâches, agenda côté
écran), et le moteur n'a pas redémarré pendant la session (aucune coupure, aucun 5xx), mais le lecteur doit
savoir que l'application observée n'était pas figée.

## Mon impression

Je viens d'installer, je n'ai rien lu, et en dix secondes l'accueil me dit trois choses que je comprends
(« Bonjour Jean », « ce qui mérite ton attention », « Branche tes mails ») et deux que je ne comprends pas :
« ESSAYER UN AUTRE PARCOURS » alors que je n'en ai encore essayé aucun, et « Parcours réel · mutations du
chat confirmées », qui ressemble à une note d'ingénieur restée dans l'écran. La colonne de gauche est bonne :
six icônes, tout est atteignable, et le catalogue « Ce que Thérèse sait mobiliser » est le meilleur écran de
l'application, celui qui m'a dit où étaient mes tâches.

Deux choses m'ont fait perdre confiance. J'ai tapé le mot exact « Conversations » dans la barre de recherche,
j'ai appuyé sur Entrée, et je suis arrivé sur **Tâches** : le premier résultat n'était pas celui dont je
venais d'écrire le nom. Et surtout, l'écran « Écrire » m'annonce en haut à droite **EMAIL CONNECTÉ** pendant
qu'il m'écrit à gauche **« Aucun compte email connecté »**. J'ai quand même cliqué « Générer une proposition » :
rien. Pas d'erreur, pas de roue qui tourne, rien. J'ai recliqué : rien. J'ai écrit mon message à la main, on
m'a demandé de confirmer avec une phrase que j'ai trouvée juste (« Cette action crée un brouillon. Elle
n'envoie rien. »), puis on m'a répondu que le fournisseur n'avait pas voulu, alors que je n'ai aucun
fournisseur. Trois messages sur le même écran, trois versions de la vérité.

Ce qui m'a plu, en revanche, mérite d'être dit : refuser une tâche sans titre avec « Ajoute un titre » sans
rien envoyer au serveur, la double confirmation avant d'écrire un rendez-vous, et surtout la fiche de
préparation qui écrit noir sur blanc, pour chacun de mes deux invités, « Pas de correspondance CRM exacte »
et « Aucun contexte absent n'est inventé ». C'est exactement ce que j'attends d'un outil qui touche à mes
clients. Compte des gestes : une tâche créée en 4 clics, terminée en 3 de plus, un rendez-vous complet en
5 clics, et le tiroir des conversations en 1.

## Parcours

### Découvrir : comprendre l'accueil, le tiroir, le catalogue, trouver mes tâches

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | Garde d'environnement, page chargée | document visible, horloge non nulle | `visible`, horloge `24071.866` ; accueil directement, sans assistant | `01` | ok |
| 2 | Je lis l'accueil (10 s) | savoir où je suis et quoi faire | « Bonjour Jean. » ; « J'ai regroupé ce qui mérite ton attention » ; « Aucune priorité détectée / 0 élément issu de tes données » ; puis « ESSAYER UN AUTRE PARCOURS » et « Parcours réel · mutations du chat confirmées » | `02` | voir karim-08 et karim-09 |
| 3 | Clic sur « Conversations » (rail gauche), 1 clic | le tiroir s'ouvre | tiroir 306×744, focus porté sur le champ « Rechercher une conversation », contenu « Aucune conversation enregistrée / Commence une conversation pour la retrouver ici. » - conforme à `GET /api/chat/conversations` = `[]` | `03` | ok |
| 4 | Second clic sur « Conversations » | le tiroir se referme (c'est le même bouton) | le tiroir reste ouvert, mêmes dimensions 306×744, `visibility: visible`, `display: flex` ; aucun effet visible | `04` | voir karim-06 |
| 5 | ⌘K | la palette s'ouvre | dialogue « Rechercher dans Thérèse », focus sur le combobox, « 17 résultats », 5 parcours puis « Capacités fréquentes » | `05` | ok |
| 6 | Quatre Tab dans la palette | le focus reste dans la palette | Tab 1 → « Fermer » (dans la palette), Tab 2 → liste « Résultats » (dans la palette), **Tab 3 → `BODY`, hors de la palette**, Tab 4 → retour au champ de recherche | `06` | voir karim-07 |
| 7 | Échap | la palette se ferme et rend le focus | palette fermée, focus rendu **au bouton « Conversations »**, exactement l'élément qui l'avait avant l'ouverture | `07` | ok |
| 8 | ⌘K, je tape « Conversations », Entrée | ouvrir les conversations | **la vue « Tâches » s'ouvre** : le premier résultat sélectionné est la capacité « Tâches », dont la description contient le mot « conversations » | `08` | voir karim-01 |
| 9 | Je recommence à l'identique | même chose | même résultat, reproductible | `09` | voir karim-01 |
| 10 | ⌘K, « Conversations », je regarde sans valider | l'entrée exacte en tête | « 2 résultats » : groupe **Capacités** → « Tâches » `aria-selected=true` ; groupe **Commandes de l'application** → « Conversations · Ouvrir la liste des conversations · ⌘B », non sélectionné | `10` | preuve de karim-01 |
| 11 | Flèche bas puis Entrée (la bonne entrée) | le tiroir bascule | tiroir **fermé** : `0` élément `prototype-conversation-drawer` dans le DOM | `11` | ok |
| 12 | ⌘K, « Conversations », flèche bas, Entrée | le tiroir se rouvre, un seul | **1 seul** tiroir, 306×744, focus sur « Historique des conversations » | `12` | ok, transition (b) conforme |
| 13 | Échap | le tiroir se ferme, la vue reste | tiroir à 0, vue « Tâches » : « 0 tâche », colonnes « À faire / En cours / Terminé », « Aucune tâche » dans chacune | `13` | ok |
| 34 | Clic sur « Plus d'outils » | catalogue des capacités | « Ce que Thérèse sait mobiliser · 30 capacités » ; 6 familles ; « Tâches - Créer, prioriser et terminer les actions issues des conversations » ; focus sur « Rechercher une capacité » | `34` | ok |

**Où sont mes tâches ?** Deux chemins existent et aucun n'est le rail : le catalogue « Plus d'outils »
(famille « Organiser mon quotidien ») et la palette. Le rail gauche n'affiche ni Tâches ni Agenda ni Contacts.

### Projets et tâches : créer, refuser, terminer, colonnes puis liste, filtrer

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 14 | « Nouvelle tâche » | un formulaire | « Titre * », Description, Statut, Priorité, Date limite, Tags ; le champ titre n'a ni `required` ni `aria-required` ; le focus reste sur le bouton | `14` | ok (réserve karim-10) |
| 15 | « Enregistrer » avec un titre vide | refus lisible, rien d'envoyé | **« Ajoute un titre »** en `role="alert"` ; formulaire conservé ; **aucune requête `/api/` non-GET dans le journal** | `15` | ok |
| 16 | Titre « Relancer le devis de démonstration » puis Enregistrer | tâche créée | « 1 tâche », carte dans « À faire » ; `POST /api/tasks {"title":"…","status":"todo","priority":"medium"}` | `16` | ok |
| 17 | Clic sur la carte | ouvrir la tâche | « Modifier la tâche » ; la carte porte `role="button"` et `tabindex=0` (atteignable au clavier) | `17` | ok |
| 18 | Statut → « Terminé », Enregistrer | la tâche passe en Terminé | colonne « Terminé (1) » ; `PUT /api/tasks/{id} {"status":"done"}` | `18` | ok |
| 19 | Bouton « Afficher les tâches en liste » | vue liste | liste ; la tâche terminée est barrée (`text-decoration: line-through`) avec une coche verte ; **le bouton de bascule n'a aucun nom accessible** (SVG seul) | `19` | voir karim-11 |
| 20 | Bouton « Filtrer les tâches » | filtres statut et priorité | deux listes ; la première propose « Tous les statuts / **A faire** / En cours / Terminé / Annulé » - sans accent, alors que la colonne du kanban écrit « À faire » | `20` | voir karim-05 |
| 21 | Rail → « Projets » | vue Projets | « 0 projet », « Aucun projet », un seul bouton « Nouveau projet » | `21` | ok (réserve karim-12) |
| 22 | « Nouveau projet » | formulaire | « Nom du projet * », Description, Statut, **Contact associé (Aucun contact / Camille)**, Budget (€), Notes, Tags | `22` | ok |
| 23 | Nom « Refonte du site Démo » puis « Créer » | projet créé | « 1 projet » ; colonnes **ACTIF / EN ATTENTE / TERMINÉ / ANNULÉ** avec « Glisser ici » ; `POST /api/memory/projects` | `23` | ok (réserve karim-12) |

### Écrire : brouillon d'un e-mail de suivi

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 24 | Accueil puis « Écrire » | le parcours d'écriture | à gauche « Aucun compte email connecté / Configure Gmail ou IMAP dans la vue Email complète » ; **à droite l'en-tête « EMAIL CONNECTÉ »** puis « Rédaction » et « Ton brouillon reste ici : rien ne part tant que tu ne l'envoies pas depuis ta messagerie » | `24` | voir karim-03 |
| 25 | Je mesure les deux mentions | une seule vérité | « Aucun compte email connecté » en (259, 235), 14 px ; « Email connecté » rendu en capitales en (778, 72), 12 px ; `GET /api/dashboard/setup-status` → `"has_email": false` | `25` | preuve de karim-03 |
| 26 | Je remplis « À » et « Objet » | champs nommés | `#email-recipient` (label « À », `aria-label` « Destinataire du brouillon ») et `#email-subject` - correctement étiquetés | `26` | ok |
| 27 | « Générer une proposition » | une proposition, ou une attente, ou une erreur | **rien** : pas de roue, pas de message, pas de requête réseau ; le bouton n'est pas désactivé (`disabled: false`, `opacity: 1`) | `27` | voir karim-02 |
| 28 | J'attends 8 s | quelque chose | brouillon toujours vide, aucun `role="alert"`, aucune requête | `28` | voir karim-02 |
| 29 | Je reclique (2ᵉ geste) | quelque chose | rien de nouveau après 5 s. J'arrête : c'est mon troisième geste sur ce bouton | `29` | voir karim-02 |
| 30 | « Enregistrer comme brouillon » avec un corps vide | refus lisible | **« Le brouillon est vide. »** en `role="alert"`, et le focus est déplacé sur `#email-draft` | `30` | ok |
| 31 | Première tentative de saisie du corps | le texte arrive dans le brouillon | **raté d'instrument** : ma commande a visé le mauvais des deux `textarea` de la page, le brouillon est resté vide et « Le brouillon est vide. » s'affiche toujours. Capture conservée pour la trace, elle ne prouve rien sur l'application | `31` | (instrument) |
| 32 | J'écris le message dans `#email-draft` puis « Enregistrer comme brouillon » | confirmation | étape de confirmation : « Confirmer l'enregistrement chez le fournisseur email - Destinataire : camille@exemple.test - Objet : Suivi de notre échange - **Cette action crée un brouillon. Elle n'envoie rien.** » + Annuler / Confirmer | `32` | ok |
| 33 | « Confirmer le brouillon » | succès, ou une erreur qui dit quoi faire | **« Impossible d'enregistrer le brouillon chez le fournisseur email. »** ; **aucune requête réseau n'est partie** | `33` | voir karim-04 |

### Préparer un rendez-vous : un participant inconnu et un « connu »

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 35 | Échap puis « Préparer » | le parcours rendez-vous | « 0 événement sur 90 jours » ; « Aucun rendez-vous à venir / L'agenda est disponible. Tu peux y préparer un nouvel événement. » ; bandeau Sources « 0 calendrier · **1 contacts consultables** · Écriture confirmée » | `35` | voir karim-05 |
| 36 | « Préparer un événement » | formulaire | Titre, Début, Fin, Calendrier (« Mon calendrier »), Lieu ou lien, « Participants, séparés par une virgule » (`contact@exemple.fr`), Description ; « Aucune donnée n'est écrite avant la confirmation finale » ; **Sources passe de « 0 calendrier » à « 1 calendrier »** (calendrier local provisionné au geste) | `36` | ok |
| 37 | Titre + créneau + `bertrand.inconnu@exemple.test, camille@exemple.test`, puis « Vérifier avant création » | un récapitulatif qui me dit qui est qui | « Créer « Point de suivi Démo » le 10/09/2026 **10:00:00** dans « Mon calendrier » (local), avec **2 participants**. Fuseau : Europe/Paris. » + Annuler / Modifier / Confirmer la création. Ni les noms, ni l'heure de fin, ni le fait qu'aucun des deux n'est connu | `37` | voir karim-13 |
| 38 | « Confirmer la création » | l'événement, et le contexte | événement créé (`POST /api/calendar/events`) puis fiche : « PARTICIPANTS ET CONTACTS RELIÉS - bertrand.inconnu@exemple.test : **Pas de correspondance CRM exacte** ; camille@exemple.test : **Pas de correspondance CRM exacte** » ; « POINTS À VÉRIFIER : objectif non renseigné, lieu non renseigné, **aucun participant ne correspond exactement à un contact local** » ; « Les contacts sont reliés uniquement par adresse email exacte. **Aucun contexte absent n'est inventé.** » | `38` | ok, transition (d) conforme |

### Chat : poser une question simple au modèle local

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 39-40 | Je tape « Quelles sont mes tâches ? » dans le composeur de l'accueil et j'appuie sur Entrée | la question part | la vue bascule sur « Nouvelle conversation », **rien n'est envoyé** (aucune requête), et le texte reste dans le composeur | `39`, `40` | voir karim-15 |
| 39b | **Rejeu contrôlé du même geste** : Accueil, clic dans le composeur, vidage vérifié (`value === ""`), frappe touche par touche, mesure du focus **avant** Entrée | soit l'envoi, soit la preuve que c'est mon instrument | focus avant Entrée = `TEXTAREA aria-label="Message à Thérèse"` contenant « Quelles sont mes tâches ? ». Après Entrée : **0 message, aucune requête**, vue « Nouvelle conversation », texte reporté dans `#chat-input`, **focus rendu à `BODY`** | `39b` | preuve de karim-15 |
| 41 | Je retape la question dans le composeur du chat et j'envoie | la question part | envoyée - mais le composeur avait **gardé** le premier texte, si bien que le message parti est « Quelles sont mes tâches ?Quelles sont mes tâches ? », et le titre de la conversation aussi. `POST /api/chat/conversations` puis `POST /api/chat/send` | `41` | conséquence de karim-15 |
| 42 | J'attends | une attente visible | indicateur d'attente présent, bulle de réponse vide, composeur rendu au focus | `42` | ok |
| 43 | J'attends la fin | une réponse à ma question | **45 secondes**, puis : « Voici votre prochain rendez-vous : Point de suivi Démo : le 10 septembre à 10h00 (durée 30 min). » avec la mention « Local » et « 12544 tokens ». Ce n'est pas la réponse à ma question : j'ai une tâche en base | `43` | observation (qualité du modèle local, pas une règle de l'application) |
| 44 | Nouvelle conversation puis « Prompts » | bibliothèque | « Bibliothèque de prompts · 34 prompts prêts à l'emploi », familles Email (6)… ; focus sur « Rechercher un prompt » | `44` | ok |
| 45 | « Utiliser » sur un prompt | le texte arrive dans le composeur | il arrive : « Rédige une réponse professionnelle à l'email suivant : "{contenu_email_recu}"… », le panneau se ferme, le focus va au composeur, `POST /api/variables/preview` pour l'aperçu des variables. **Mais le bouton « Utiliser » a `opacity: 0` au repos et `opacity: 1` au survol** : je ne le vois pas tant que je ne passe pas dessus | `45` | voir karim-14 |

## Constats numérotés

> Quinze constats, tous avec preuve : quatre en P2 (karim-01 à karim-04), onze en P3.
> Deux observations ont été écartées faute de preuve suffisante, elles sont nommées dans les angles morts.

### karim-01 - La palette place « Tâches » devant « Conversations » quand je tape le mot « Conversations » (P2)

- **Préconditions** : n'importe quel écran.
- **Étapes** : ⌘K → taper `Conversations` → Entrée.
- **Attendu** : la commande dont le titre est exactement le mot tapé arrive en tête.
- **Observé** : la vue **Tâches** s'ouvre. La liste rend « 2 résultats » : d'abord le groupe *Capacités* avec
  « Tâches - Créer, prioriser et terminer les actions issues des **conversations**. » portant
  `aria-selected="true"`, ensuite le groupe *Commandes de l'application* avec « Conversations - Ouvrir la
  liste des conversations - ⌘B ». Le classement met la correspondance sur la **description** devant la
  correspondance sur le **titre**.
- **Preuve** : captures `08`, `09` (deux fois de suite, reproductible), `10` (la palette ouverte avec la
  sélection visible) ; relevé d'accessibilité : `option "Tâches …" [selected]` puis `option "Conversations …"`.
- **Sévérité** : P2. C'est le geste clavier le plus vendu de l'application (« Rechercher ⌘K » dans l'en-tête),
  et il m'emmène ailleurs sans que rien ne me prévienne.

### karim-02 - « Générer une proposition » ne fait rien, sans le dire, dans une rédaction nouvelle (P2)

- **Préconditions** : accueil → parcours « Écrire » (rédaction nouvelle, sans message d'origine).
- **Étapes** : remplir « À » et « Objet » → cliquer « Générer une proposition » → attendre → recliquer.
- **Attendu** : une proposition, ou une attente, ou une erreur qui dit quoi faire.
- **Observé** : rien du tout. Bouton actif (`disabled: false`, `opacity: 1`, `pointer-events: auto`), aucun
  `role="alert"` ni `role="status"`, corps du brouillon inchangé, **aucune requête réseau** après 8 s puis
  encore 5 s.
- **Preuve** : captures `27`, `28`, `29` ; journal réseau vide sur toute la séquence.
- **Fichier suspecté** (lu) : `src/frontend/src/components/prototype/EmailConversationCard.tsx:263-264` -
  `async function generateDraft(replacing) { if (resource?.status !== 'ready') return; … }`. En rédaction
  nouvelle il n'y a pas de message source, donc `resource` n'est pas `ready` et la fonction **sort en
  silence**, avant même le `try` qui sait afficher une cause (lignes 274-290, l'acquis de BUG-171).
- **Sévérité** : P2. Le bouton est proposé dans un état où il ne peut rien faire, et son échec est muet.

### karim-03 - L'écran « Écrire » affiche « EMAIL CONNECTÉ » alors qu'aucun compte ne l'est (P2)

- **Préconditions** : aucun compte email configuré (`GET /api/dashboard/setup-status` → `"has_email": false`).
- **Étapes** : accueil → « Écrire ».
- **Attendu** : l'écran dit la même chose partout sur l'état de ma boîte.
- **Observé** : la colonne de gauche affiche « **Aucun compte email connecté** - Configure Gmail ou IMAP dans
  la vue Email complète » (14 px, en 259/235) ; l'en-tête du panneau de droite affiche « **EMAIL CONNECTÉ** »
  (12 px, en 778/72, texte source « Email connecté » rendu en capitales).
- **Preuve** : captures `24` et `25` ; relevé DOM des deux nœuds de texte avec leurs boîtes ;
  `setup-status` renvoyant `has_email: false`.
- **Fichier suspecté** (lu) : `EmailConversationCard.tsx:354-357` - l'intitulé est écrit en dur dans l'en-tête,
  sans aucune condition sur l'existence d'un compte.
- **Sévérité** : P2. Une affirmation d'état fausse, contredite par le même écran.

### karim-04 - L'échec d'enregistrement du brouillon accuse le fournisseur alors que la cause est connue (P2)

- **Préconditions** : aucun compte email ; brouillon rempli à la main.
- **Étapes** : « Enregistrer comme brouillon » → « Confirmer le brouillon ».
- **Attendu** : une erreur qui dit ce qui s'est passé et quoi faire (« aucun compte email : branche Gmail ou
  IMAP »), au plus tard ici et de préférence avant.
- **Observé** : « **Impossible d'enregistrer le brouillon chez le fournisseur email.** » - alors qu'aucune
  requête n'est partie (journal réseau vide sur l'étape) et qu'il n'existe aucun fournisseur à accuser.
- **Preuve** : capture `33` ; journal réseau : zéro requête entre le clic et le message.
- **Fichiers suspectés** (lus) : `usePrototypeEmailData.ts:132-134` lève `new Error('Aucun compte email
  actif.')` ; `EmailConversationCard.tsx:345-347` intercepte et remplace **toute** erreur par la phrase
  générique - exactement le motif que la même classe corrige pourtant sur le chemin de génération
  (lignes 285-290, où la cause du serveur est affichée telle quelle).
- **Sévérité** : P2. Avec karim-03, l'utilisateur est conduit jusqu'à une confirmation pour un geste que
  l'application savait impossible dès l'ouverture de l'écran.

### karim-05 - Deux mots français fautifs dans des écrans courants (P3)

- **a) « A faire » sans accent** dans le filtre de statut des tâches, à côté de la colonne « **À** faire » du
  même écran. Étapes : Tâches → « Filtrer les tâches » → dérouler le statut. Preuve : capture `20`, options
  relevées `["Tous les statuts","A faire","En cours","Terminé","Annulé"]`.
- **b) « 1 contacts consultables »** dans le bandeau Sources du parcours « Préparer ». Étapes : accueil →
  « Préparer ». Preuve : capture `35`, texte relevé « 0 calendrier · 1 contacts consultables ».
- **Sévérité** : P3, mais visibles au premier écran par un utilisateur qui vient d'installer.

### karim-06 - Le mot « Conversations » désigne deux comportements différents selon l'endroit (P3)

- **Préconditions** : tiroir des conversations ouvert.
- **Étapes** : cliquer une seconde fois sur « Conversations » dans le rail gauche.
- **Attendu** : le même mot fait la même chose partout (la commande homonyme de la palette, elle, bascule).
- **Observé** : le rail **ouvre seulement** ; le second clic n'a aucun effet visible (tiroir toujours
  306×744, `visibility: visible`). La commande « Conversations » de la palette, elle, **bascule** bien
  (fermé à l'étape 11, rouvert à l'étape 12). Le bouton du rail ne porte ni `aria-expanded` ni état enfoncé.
- **Preuve** : captures `04` (second clic sans effet), `11` et `12` (bascule par la palette).
- **Fichier suspecté** (lu) : `ConversationCanvasPrototype.tsx:1559` -
  `<IconButton label="Conversations" onClick={() => openConversationDrawer('search')}>` là où
  `toggleConversationDrawer` existe à la ligne 895 et sert la palette (ligne 1447).
- **Sévérité** : P3.

### karim-07 - Dans la palette, une tabulation sur quatre pose le focus sur le corps du document (P3)

- **Préconditions** : palette ouverte (⌘K).
- **Étapes** : Tab, Tab, Tab, Tab, en relevant `document.activeElement` après chaque frappe.
- **Attendu** : « Tab reste dans la palette ».
- **Observé** : `button Fermer` (dans la palette) → `div Résultats` (dans la palette) → **`BODY`, hors de la
  palette** → retour au champ de recherche. Le piège rattrape bien le focus au coup suivant, mais il existe
  un arrêt où plus rien n'est mis en évidence à l'écran.
- **Preuve** : capture `06` et le relevé par frappe, avec le drapeau `dansPalette` mesuré par
  `dialog.contains(document.activeElement)` : `true, true, false, true`.
- **Réserve d'instrument** : mesuré en navigateur sans interface (headless). Dans une fenêtre réelle, cet
  arrêt pourrait être capté par la barre d'adresse plutôt que par le corps du document ; le fait que le focus
  sorte du dialogue, lui, ne change pas.
- **Sévérité** : P3. Le contrat « Échap ferme et rend le focus » est, lui, parfaitement tenu (étape 7 :
  focus rendu au bouton exact qui l'avait avant l'ouverture).

### karim-08 - « ESSAYER UN AUTRE PARCOURS » propose un « autre » parcours avant le premier (P3)

- **Étapes** : ouvrir l'accueil sans rien faire.
- **Observé** : le groupe des cinq verbes (Écrire, Retrouver, Préparer, Décider, « Voir la suite ») est
  intitulé « ESSAYER UN AUTRE PARCOURS » alors que je n'en ai encore essayé aucun.
- **Preuve** : capture `02`.
- **Sévérité** : P3, prévisibilité.

### karim-09 - Une phrase d'ingénieur en pied d'accueil (P3)

- **Observé** : « **Parcours réel · mutations du chat confirmées** - Thérèse affiche les sources reçues et
  confirme les effets externes effectivement raccordés. » Le mot « mutations » n'appartient pas au vocabulaire
  d'un consultant ; « effets externes effectivement raccordés » non plus.
- **Preuve** : captures `02`, `24`, `35` (la phrase suit tous les parcours).
- **Sévérité** : P3, lisibilité. À rapprocher du lexique verrouillé par `lexiqueTitres.test.ts`, qui porte sur
  les titres et pas sur ces mentions.

### karim-10 - « Titre * » n'est obligatoire que pour l'œil (P3)

- **Observé** : dans le formulaire de tâche, le champ porte l'étoile dans son étiquette mais l'élément n'a ni
  `required` ni `aria-required`, et aucun `aria-label`. Le refus fonctionne (« Ajoute un titre »,
  `role="alert"`, rien d'envoyé), mais l'obligation n'est annoncée qu'en typographie.
- **Preuve** : capture `14` (relevé des champs : `{tag: INPUT, ph: "Titre de la tâche", req: false, lab: null}`)
  et capture `15`.
- **Sévérité** : P3, accessibilité.

### karim-11 - Boutons sans nom accessible dans la vue Tâches (P3)

- **Observé** : dans la vue liste, le bouton qui bascule une tâche en terminé est un `<button>` ne contenant
  qu'un SVG, sans `aria-label` ni `title` - invisible pour un lecteur d'écran. (Les quatre boutons de la
  barre d'outils, eux, sont correctement nommés : « Afficher les tâches en kanban », « … en liste »,
  « Filtrer les tâches », « Rafraîchir les tâches ».)
- **Preuve** : capture `19` et l'extrait DOM de la ligne :
  `<button class="mt-0.5 shrink-0 …"><svg class="lucide lucide-circle-check …"></svg></button>`.
- **Sévérité** : P3.

### karim-12 - Deux tableaux de colonnes qui ne se ressemblent pas (P3)

- **Observé** : les colonnes des Tâches s'écrivent « À faire / En cours / Terminé » en casse normale, avec un
  compteur nu ; celles des Projets s'écrivent « ACTIF / EN ATTENTE / TERMINÉ / ANNULÉ » en capitales avec le
  compteur entre parenthèses et une zone « Glisser ici ». La vue Tâches offre une bascule kanban/liste, la
  vue Projets n'en a pas. L'état vide des Projets se réduit à « Aucun projet », sans phrase ni action, là où
  les autres écrans expliquent (« Commence une conversation pour la retrouver ici »).
- **Preuve** : captures `13`, `19`, `21`, `23`.
- **Sévérité** : P3, cohérence.

### karim-13 - Le récapitulatif d'un rendez-vous ne nomme pas les participants ni l'heure de fin (P3)

- **Observé** : avant d'écrire quoi que ce soit, l'écran résume « Créer « Point de suivi Démo » le
  10/09/2026 **10:00:00** dans « Mon calendrier » (local), avec **2 participants**. Fuseau : Europe/Paris. »
  Les adresses ne sont pas citées, l'heure de fin (10:30, que j'ai saisie) n'apparaît pas, et les secondes
  sont affichées. Le fait qu'aucun des deux invités ne corresponde à un contact n'est dit qu'**après**
  la création.
- **Preuve** : captures `37` (récapitulatif) et `38` (fiche d'après, qui, elle, dit tout, et bien).
- **Sévérité** : P3. C'est un manque de la confirmation, pas une erreur : classé comme tel.

### karim-14 - L'action d'une carte de la bibliothèque de prompts est invisible au repos (P3)

- **Observé** : le bouton « Utiliser » de chaque carte a `opacity: 0` mesurée au repos et `opacity: 1` au
  survol (classes `opacity-0 group-hover:opacity-100 group-focus-within:opacity-100`). À la souris, rien
  n'indique que ces cartes sont actionnables tant qu'on ne passe pas dessus. Une fois cliqué, tout est juste :
  le texte arrive dans le composeur, le panneau se ferme, le focus suit.
- **Preuve** : capture `45`, mesures `opaciteAuRepos: "0"` / `opaciteAuSurvol: "1"`.
- **Sévérité** : P3, découvrabilité.

### karim-15 - Entrée dans le composeur de l'accueil n'envoie rien et lâche le focus sur le corps du document (P3)

- **Préconditions** : accueil, composeur « Message à Thérèse » vide.
- **Étapes** : cliquer dans le composeur, taper « Quelles sont mes tâches ? », appuyer sur Entrée.
- **Attendu** : soit la question part, soit je reste dans un champ où je peux la renvoyer.
- **Observé** : la vue bascule sur « Nouvelle conversation », le texte est bien **reporté** dans le composeur
  du chat (`#chat-input`), **aucune requête ne part** (`0` message, journal réseau vide), et le focus est
  rendu à `BODY`. Il faut donc reprendre la souris pour renvoyer. **Rejeu contrôlé** : le focus mesuré juste
  avant la frappe d'Entrée était bien sur le `textarea` de l'accueil, avec la bonne valeur ; ce n'est pas mon
  instrument. Effet de bord constaté dans la foulée : le texte non envoyé reste dans le composeur, si bien
  qu'une seconde saisie s'ajoute à la première (mon message est parti en double, et le titre de la
  conversation avec).
- **Preuve** : captures `39`, `39b`, `40`, `41` ; relevés `focusAvantEntree = {tag: "TEXTAREA", aria: "Message
  à Thérèse", valeur: "Quelles sont mes tâches ?"}` puis `messages: 0`, `composeurs[0].v = "Quelles sont mes
  tâches ?"`, focus final `BODY`.
- **Nuance honnête** : le composeur de l'accueil n'annonce nulle part qu'Entrée envoie (l'indice
  « ⇧+↵ nouvelle ligne » n'apparaît que dans la vue chat, contrôlé après coup), donc le passage à la
  conversation peut être voulu. Ce qui reste un défaut, c'est la **perte du focus** : le geste suivant exige
  la souris.
- **Sévérité** : P3.

## Propositions pour le portail humain (pas des défauts)

- **P-K1** : dans la vue liste des tâches, terminer une tâche coûte **un** clic (la coche) ; dans la vue
  kanban, il en faut **trois** (ouvrir la carte, changer le statut, enregistrer) ou un glisser-déposer.
  Offrir la même coche sur la carte du kanban.
- **P-K2** : le rail gauche ne mène ni aux Tâches, ni à l'Agenda, ni aux Contacts. Un nouvel arrivant les
  trouve par le catalogue ou par la palette. Une entrée « Tâches » dans le rail éviterait le détour.
- **P-K3** : signaler l'invité non reconnu **avant** la création, et proposer « Créer le contact » depuis la
  fiche de préparation, qui sait déjà dire « Pas de correspondance CRM exacte ».
- **P-K4** : au premier chargement, la console affiche « Tentative 1/5 échouée: ApiError: Impossible de
  contacter le serveur » (`App.tsx`, `initAndCheckOnboarding`) avec un `net::ERR_ABORTED` sur
  `/api/config/onboarding-complete`. La reprise est immédiate et invisible à l'écran, mais c'est le seul
  bruit d'erreur de toute la session ; il mérite d'être regardé à froid.

## Ce que j'ai trouvé juste, et qui mérite d'être protégé

- La fiche de préparation d'un rendez-vous : « Pas de correspondance CRM exacte » pour chaque invité,
  « POINTS À VÉRIFIER », et « Aucun contexte absent n'est inventé ». C'est la meilleure page de l'application.
- La confirmation d'enregistrement du brouillon : « Cette action crée un brouillon. Elle n'envoie rien. »
- Le refus d'une tâche sans titre : message court, `role="alert"`, **et rien n'est envoyé au serveur**.
- Échap : ferme la palette et rend le focus à l'élément exact qui l'avait avant.
- Le catalogue « Ce que Thérèse sait mobiliser », classé par intention (« JE VEUX… »).
- Aucune réponse HTTP ≥ 400 sur les 45 étapes, aucune erreur JavaScript après le démarrage.

## Transitions couvertes et angles morts

| Transition demandée | Résultat |
|---|---|
| **(a)** Tableau de bord : « et N autres non affichés » quand il y a beaucoup de tâches | **NON couverte - angle mort assumé.** La mention n'apparaît que si un total dépasse le nombre rendu : `nombreNonAffiche()` additionne `tasks_total - tasks_count`, `follow_ups_total - follow_ups_count` et `invoices_total - invoices_count` (`prototypeReadModels.ts:199-205`), et le moteur plafonne chaque liste à **50** (`PLAFOND_BRIEF = 50`, `routers/dashboard.py:258`, appliqué lignes 401, 428, 474). Il faut donc **plus de 50** tâches, relances ou factures ; en créer autant à la souris dépasse le budget de 45 étapes, et mon jeton est en lecture seule. À ne pas confondre avec le variateur « Aujourd'hui, montre-moi », qui replie la carte (`seuil`) sans rien dire de « non affiché » - et qui ne s'affiche qu'à partir de plusieurs éléments (`motsOfferts.length > 1`), donc pas avec la seule tâche que j'avais. **Reproduction possible** : semer 51 tâches par l'API puis ouvrir l'accueil. |
| **(b)** Commande « Conversations » depuis ⌘K, puis à nouveau : ouvre puis ferme, jamais deux tiroirs | **couverte - conforme.** Premier appel : `0` élément `prototype-conversation-drawer` dans le DOM (capture `11`). Second appel : **exactement 1**, 306×744 (capture `12`). Jamais deux. Réserve distincte : la même commande tapée au clavier n'est pas celle que la palette sélectionne (karim-01), et le bouton homonyme du rail, lui, ne bascule pas (karim-06). |
| **(c)** Écrire : brouillon d'e-mail, la carte de message apparaît ; « Insérer dans le chat » depuis une autre vue crée une notification « Voir » sans déplacer | **couverte à moitié.** La carte de message apparaît et le brouillon se prépare de bout en bout (captures `24` à `33`), avec trois défauts en chemin (karim-02, karim-03, karim-04). L'insertion d'un prompt dans le chat est couverte par la bibliothèque (capture `45`) : le texte arrive dans le composeur, le panneau se ferme, le focus suit. **La notification « Voir », elle, n'est PAS couverte** : elle n'est émise que par le retour d'une **action d'agent** terminée pendant qu'on est ailleurs - `actionsStore.ts:78-85`, `if (navigation.activeView === 'chat') return;` puis `action: { label: 'Voir', … }`. Il aurait fallu lancer un agent et changer de vue pendant son exécution ; je ne l'ai pas fait, faute de budget, et je ne déclare donc ce chemin ni bon ni mauvais. |
| **(d)** Préparer un rendez-vous avec un participant inconnu : ce que l'écran propose | **couverte - conforme, avec une réserve de moment.** Après création, l'écran nomme chaque invité et écrit « Pas de correspondance CRM exacte », ajoute « Aucun participant ne correspond exactement à un contact local » aux points à vérifier, et pose la règle : « Les contacts sont reliés uniquement par adresse email exacte. Aucun contexte absent n'est inventé » (capture `38`). Il ne **propose** rien (pas de « créer ce contact ») et ne dit rien **avant** la confirmation (karim-13, P-K3). NB : mon invité « connu » ne l'était pas - le contact Camille laissé par Jean n'a pas d'adresse email en base (`GET /api/memory/contacts` → `"email": null`), donc les deux participants étaient inconnus au sens de l'application. La branche « participant reconnu » reste un angle mort. |
| **(e)** Projets : tâche sans titre (validation), avec titre, terminée, colonnes puis liste | **couverte - conforme.** Refus « Ajoute un titre » sans aucune requête (capture `15`) ; création (`16`) ; passage en Terminé (`18`) ; kanban puis liste (`13`, `19`) ; filtres statut et priorité (`20`). Projet créé au passage (`21` à `23`). Réserves : karim-05a (accent), karim-11 (bouton sans nom), karim-12 (les deux kanbans ne se ressemblent pas). |
| **(f)** Palette au clavier : Tab reste dans la palette, Échap ferme et rend le focus | **couverte - un demi-écart.** Échap : conforme et net, le focus revient au bouton exact qui l'avait (capture `07`). Tab : trois arrêts sur quatre restent dans la palette, le troisième pose le focus sur `BODY` (karim-07, capture `06`). |

**Autres angles morts de cette session** :

- **Le premier envoi de chat n'est pas parti** (étape 39) : **rejoué et tranché**, ce n'est pas mon
  instrument, c'est karim-15.
- **La réponse du modèle local ne répondait pas à ma question** (rendez-vous au lieu des tâches, 45 s). Le
  message parti était doublé (« Quelles sont mes tâches ?Quelles sont mes tâches ? ») par ma faute. Classé
  `observation` : c'est du comportement de `gemma4-tia:latest`, pas une règle de l'application.
- **Pas de mise en route** : le moteur était déjà configuré, donc rien de l'assistant n'a été revu (Jean l'a
  photographié en entier).
- **Objectif 5 de ma fiche (« ouvrir Contacts, Agenda, Paramètres au clavier ; Échap à chaque niveau ;
  vérifier que Retour ramène d'où je viens ») n'est couvert qu'à moitié** : seules les transitions (b) et (f)
  l'ont été, c'est-à-dire la palette elle-même, sa navigation au Tab et son Échap. **Je n'ai ouvert aucune des
  trois destinations par la palette**, et **je n'ai jamais éprouvé « Retour »** : je l'ai seulement relevé dans
  l'arbre d'accessibilité de la vue Tâches (`button` « Retour », `aria-label` « Revenir à la conversation
  unifiée »). Échap n'a été éprouvé qu'à deux niveaux, la palette (étape 7) et le tiroir (étape 13), plus le
  catalogue (étape 35).
- **Non ouverts, faute de budget** : Paramètres, Contacts, Devis et factures, Décider (Board), Agenda complet,
  Email complet, Contrôle des données, le glisser-déposer des deux kanbans, et le thème sombre.
- **Le tiroir a été mesuré par sa boîte englobante** (largeur et hauteur), pas seulement par sa présence dans
  le DOM : c'est ce qui permet d'affirmer qu'un second clic sur le rail ne le referme pas.
- **46 fichiers de captures** : 45 étapes numérotées plus `39b-chat-rejeu-envoi-depuis-accueil.png`, ajouté
  après coup pour trancher l'étape 39 (même usage que le `37b` de Jean). Deux clichés intermédiaires de
  l'étape 45 (tentatives bloquées par l'en-tête collant puis par l'opacité nulle) ont été mis à la corbeille
  au profit du cliché concluant.

## Tokens consommés

Côté application, un seul appel de modèle : **12 544 tokens** affichés sous la réponse locale (capture `43`),
sans coût puisque le modèle est `gemma4-tia:latest` en local. Côté session d'agent, environ **250 000 tokens**
consommés, sans mesure exacte disponible.
