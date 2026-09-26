# RFC P-125 (V2) : changer de sujet pendant une réponse longue, la réponse se termine en fond

Rédigé le 26/09/2026 sur `main` à `900765fb`. Remplace la V1 du 25/09 (`docs/plans/2026-09-25-rfc-p125-reponse-en-fond.md`), jugée NO-GO par la revue adverse B (`docs/plans/revues/2026-09-25-revue-rfc-p109-p125.md`, section P-125). Proposition acceptée par Ludo le 25/09 (« Je valide tout sauf la 141 »). Les décisions 30 à 32 du 25/09 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, section « Décisions du 25/09/2026 ») sont posées ici comme des faits. Aucun code avant la validation de ce document.

Chemins relatifs à `src/frontend/src/` (écran) et `src/backend/app/` (moteur), sauf mention. Toutes les lignes citées ont été relues à `900765fb`.

## 0. Ce qui change depuis la V1

- **Le moteur change.** La V1 disait « aucun changement obligatoire » ; la décision 31 impose que la purge et la restauration arrêtent d'office les réponses en cours, et l'inventaire montre deux écritures possibles dans une conversation disparue. Ces changements forment le lot 1, livrable seul, utile même avec le verrou actuel.
- **Plafond** de deux réponses en cours (décision 30), un seul flux local ; **pièces jointes** gardées sur la conversation d'origine (décision 32).
- **Inventaire refait** à HEAD : 13 appels de la garde (11 dans la V1), « Travaux » mène déjà aux conversations (P-140), l'écran quitté se rouvre après un rechargement (P-142), le départ du client garde le partiel (B-1461, B-1462), l'Atelier documentaire laisse désormais tourner sa trame (B-1374).
- **Deux interdits de la V1 n'existaient pas** : supprimer une conversation depuis le tiroir et changer son projet ne sont pas gardés aujourd'hui pendant une réponse. Ils sont à ajouter, pas à conserver.
- **La recherche approfondie passe au registre avant la levée du verrou.** La V1 la migrait en dernier : entre les deux lots, un flux sans propriétaire aurait survécu au changement d'écran.
- Les cinq questions de la V1, que les décisions du 25/09 ne couvrent pas, sont tranchées ici avec leur motif.

## 1. Le besoin

Hugo, persona du cycle 13 (`docs/campagnes/2026-09-25-personas-c13/rapports/hugo.md`, hugo-07, étape 2.1), travaille avec un modèle local : ses réponses prennent de 2 à 7 minutes. Pendant ce temps, « Nouvelle conversation », un changement de vue ou l'ouverture d'une autre conversation sont refusés (« Réponse en cours. Arrête la réponse avant de changer de vue ou de conversation. »). Il n'a que deux choix : attendre, ou jeter la réponse. Sa piste, acceptée : laisser la réponse se terminer en fond et la retrouver ensuite.

## 2. Décisions tranchées

| Nº | Décision | Origine | Ce qu'elle impose ici |
|---|---|---|---|
| 30 | Deux réponses de fond en même temps en ligne, file au-delà, avec mention | Ludo par délégation, 25/09 | **Lecture retenue** : deux flux de réponse ouverts au plus, la réponse affichée comprise. Motif : la réponse qu'on regarde devient une réponse de fond au premier changement de conversation ; un plafond qui ne compterait que les réponses quittées serait dépassé par ce seul geste, qu'on ne veut plus refuser. La recherche approfondie compte comme une réponse |
| 31 | La purge (« Effacer toutes mes données ») et la restauration arrêtent d'office les réponses en cours, et le disent | Ludo par délégation, 25/09 ; lié à B-1425 (`deferred`, non reproduit en deux essais) | Arrêt et attente de l'état terminal côté moteur avant toute suppression ; générations refusées pendant la purge ; le compte des réponses arrêtées part dans la réponse de la route et à l'écran |
| 32 | Les pièces jointes d'une réponse de fond qui échoue restent sur la conversation d'origine, jamais déposées ailleurs | Ludo par délégation, 25/09 | Le registre garde les pièces jointes par conversation ; le composeur affiché n'est jamais touché par l'échec d'une autre conversation |
| V1-Q1 | Avec un modèle local, une réponse à la fois : l'envoi suivant attend dans la file de sa conversation, avec mention | Tranché ici | Motif : deux réponses locales se partagent le modèle et l'une attend l'autre sans que l'écran le sache ; c'est l'interface qui sérialise, donc la mention est vraie. Un envoi en ligne n'occupe pas le modèle local et n'attend pas |
| V1-Q2 | Fin d'une réponse de fond : notification avec « Ouvrir », pastille et repère dans le tiroir | Tranché ici | Motif : les pastilles vivent dans l'établi (`components/prototype/ConversationCanvasPrototype.tsx:2083-2084`), qu'on ne voit pas depuis une vue ; la notification atteint tous les écrans |
| V1-Q3 | Une carte « action sensible à valider » venue d'une réponse de fond est visible partout, avec son origine | Tranché ici | Motif : un e-mail qui n'attendrait qu'en revenant dans la conversation serait oublié ; la carte dit « Depuis Orion » et n'est jamais validée sans clic |
| V1-Q4 | Une conversation éphémère garde le verrou actuel | Tranché ici | Motif : elle n'est pas enregistrée, il n'y a nulle part où revenir |
| V1-Q5 | La reprise après rechargement (génération détachée du navigateur) n'est pas ouverte | Tranché ici | Motif : elle renverse « déconnexion vaut arrêt réel » (0.46), exige tout le travail de ce chantier en plus, et depuis B-1461 un rechargement garde déjà la partie produite ; elle ne se rouvre que sur des signalements d'usage |
| Q-import | L'import de conversations reste permis pendant une réponse de fond | Tranché ici | Motif : il n'ajoute que des conversations absentes et saute les existantes (`routers/data.py:1812-1817`) ; il ne peut ni supprimer ni réécrire celle où le moteur écrit |

Aucune question ne reste ouverte (§ 10).

## 3. Ce qui existe à HEAD

### 3.1 Réglé depuis la V1, à ne pas reproposer

| Fiche | Ce qui est fait | Où |
|---|---|---|
| B-1461 | Le départ du client pendant une réponse (rechargement, fermeture) donne un arrêt, pas un échec, et le partiel survit : nettoyage abrité par `anyio.move_on_after(5, shield=True)` | `routers/chat.py:2076-2091`, `:2103-2137` ; `tests/test_b1461_depart_du_client_pendant_la_reponse.py` |
| B-1462 | Même motif pour la recherche approfondie | `routers/chat.py:1213-1222` |
| B-1478 | Même motif pour une mission de l'Atelier | `routers/agents.py:398-402` ; `tests/test_b1478_mission_client_parti.py` |
| B-1469, B-1470 | La restauration ferme Qdrant et rouvre la base avant de rendre la main | `routers/data.py:1587-1595`, `:1442-1453`, `:1660-1665` |
| B-1284 | La restauration suspend les créations du chat ; le mode maintenance ne suit plus une réponse en flux après ses en-têtes | `routers/data.py:1570-1577` ; `main.py:718-734` |
| P-140 | Une ligne chat ou recherche approfondie de « Travaux » ouvre sa conversation | `lib/destinationDuTravail.ts:29-31` ; `components/traitements/TraitementsPanel.tsx:85`, `:95-110` |
| P-142 | Après un rechargement, l'écran quitté se rouvre (sauf le chat, qui suit la conversation courante) | `lib/vueQuittee.ts` |
| B-1374 | Quitter l'atelier ne jette plus la trame : elle continue en fond, arrêtable dans « Travaux » (hugo-14, que la V1 renvoyait hors périmètre) | `stores/documentStore.ts:253-264` |
| B-1369 | Le refus « Réponse en cours » porte le bouton « Arrêter la réponse » | `lib/arretDeLaReponse.ts` ; `ConversationCanvasPrototype.tsx:1084-1088` |
| B-1377 | Le brouillon du composeur appartient à sa conversation | `components/chat/ChatInput.tsx:1127-1155` ; `hooks/useAutosave.ts:155-177` |

### 3.2 Le refus est une règle de l'interface

`blockStreamingNavigation` (`ConversationCanvasPrototype.tsx:1076-1090`) mêle deux gardes : sans flux, elle rend `sortieRetenueParUneSaisie()` (une saisie modifiée retient la sortie, B-978, `:1082`) ; avec un flux, elle notifie et refuse. Elle est appelée 13 fois :

| Ligne | Geste |
|---|---|
| `:1196` | `openChat` |
| `:1218` | `startConversation` (« Nouvelle conversation », ⌘N) |
| `:1226` | `openEmbeddedView` (toute vue) |
| `:1398` | ouvrir un résultat de la palette (P-016) |
| `:1413` | ouvrir une ligne de « Travaux » (P-140) |
| `:1615` | Échap qui fermerait le chat |
| `:1653` | `chooseScenario` (parcours de l'établi) |
| `:1679` | `chooseCapability` |
| `:1732` | ouvrir une séance depuis l'Agenda (P-117) |
| `:1858` | action unifiée qui ouvre une vue |
| `:1866` | « Accueil » |
| `:1878` | `chat.clear` (vider la conversation) |
| `:2066` | croix du chat |

Ailleurs : le tiroir reçoit `navigationLocked={isStreaming}` (`:2051`) et refuse d'ouvrir ou de créer une conversation (`components/prototype/PrototypeConversationDrawer.tsx:258-285`) ; `runNavigationAction` refuse aussi (`lib/clientActions.ts:29-42`) ; une vue posée dans le store pendant le flux est rejouée à la fin (`ConversationCanvasPrototype.tsx:1284-1288`).

### 3.3 Le moteur sait déjà finir une réponse sans écran

- Chaque génération est un traitement `chat` rattaché à sa conversation (`routers/chat.py:1942-1946`), dont l'identifiant part dans le premier événement `generation` (`:1983-1991`) ; la recherche approfondie fait de même en `deep-research` (`:1104-1108`, `:1129-1137`). L'écran connaît ces deux événements (`services/api/chat.ts:67`) mais le composeur n'a de branche ni pour `generation` ni pour `cancelled` (`components/chat/ChatInput.tsx:730-813`).
- Les contextes de génération sont tenus par conversation et protégés par l'identité de chaque génération (`routers/chat.py:124-205`) ; deux générations qui se chevauchent ne se gênent pas (`tests/test_fencing_traitement.py:89`) ; une génération vivante n'est jamais purgée comme orpheline (`routers/chat.py:2057-2061`, `:2193-2210`). La recherche approfondie, elle, ne s'inscrit pas dans ce registre : elle s'arrête par son traitement (`:1111-1115`, `:1152-1158`).
- `/cancel/{conversation_id}` retrouve la génération active de la conversation par son traitement et lui demande l'arrêt (`:1000-1042`).
- Le message de l'utilisateur est écrit avant le flux (`:1307-1317`) ; la réponse est écrite une fois, à la fin (`:2846-2847`) ; une réponse arrêtée garde sa partie produite, une fois (`:2158-2190`, `:2726-2733`, `:2833-2844`).
- Le modèle local n'a pas de délai de lecture (`services/providers/ollama.py:173`).
- **Contrainte structurante** : la génération vit tant que la connexion HTTP du flux vit ; une déconnexion vaut arrêt réel (`routers/chat.py:2076-2091`). Pour qu'une réponse se termine en fond, **la lecture du flux doit survivre au changement d'écran**.

### 3.4 L'interface écrit déjà au bon endroit, en partie

- Rien ne coupe le flux quand le composeur disparaît : l'arrêt n'a lieu que dans `stopStreaming` (`ChatInput.tsx:1031-1048`).
- La bulle de réponse est créée avant tout `await` (`:613-639`), donc dans la conversation affichée au moment de l'envoi. `updateMessage`, `setMessageEntities`, `setMessageMetadata` et `setMessageSkillFile` cherchent le message dans toutes les conversations (`stores/chatStore.ts:248-282`, `:299-342`).
- La conversation non éphémère est enregistrée avant le départ (`ChatInput.tsx:677-690`), et l'adoption d'une identité serveur reste possible pendant le flux (`:715-728`, règle de `lib/identiteConversation.ts`).
- La synchronisation n'écrase pas une conversation qui a des messages locaux (`hooks/useConversationSync.ts:137-145`) ; elle ne charge les messages que d'une conversation présente dans le store et vide (`:201-211`).

### 3.5 Ce qui pense encore « la conversation affichée »

Si l'on retirait seulement la garde :

| État ou geste | Où | Effet si Hugo passe d'Orion à Veille |
|---|---|---|
| `isStreaming`, un booléen pour toute l'application | `stores/chatStore.ts:82`, `:344` ; lu par `components/chat/MessageList.tsx:54`, `:92`, `:153-154`, par le composeur (`ChatInput.tsx:543`, `:1021`, `:1239`, `:1509`, `:1538-1571`), par la coque (`ConversationCanvasPrototype.tsx:1046`, `:1082`) et par `lib/clientActions.ts:32` | « Réflexion », le repère « modèle local » et « Arrêter » s'affichent dans Veille ; son premier envoi part en file |
| Arrêt du composeur | `abortRef` (`ChatInput.tsx:156`) ; `cancelGeneration` sur la conversation **affichée** (`:1036-1043`) | « Arrêter » dans Veille coupe la lecture d'Orion et demande l'arrêt de Veille au moteur |
| Arrêt joignable hors du composeur | un seul emplacement, retiré au démontage (`lib/arretDeLaReponse.ts:10-20`, `ChatInput.tsx:1063`) | hors du chat, plus aucun arrêt sauf par « Travaux » |
| File d'attente d'une place, globale | `chatStore.ts:85` ; auto-envoi (`ChatInput.tsx:1020-1028`) ; transport de l'accueil, B-626 (`ConversationCanvasPrototype.tsx:1799-1805`) | un message mis en file dans Orion part dans la conversation affichée |
| Navigation reçue du moteur | mise de côté puis exécutée à la fin (`ChatInput.tsx:778-785`, `:874-876`) | une vue s'ouvre sous les yeux de Hugo pendant qu'il travaille ailleurs |
| Carte « action sensible à valider » | `ChatInput.tsx:795-798` ; `PendingConfirmation` n'a pas la conversation (`stores/toolConfirmationStore.ts:17-21`), alors que l'événement la porte (`routers/chat.py:1490`, `:1586`, `:2279`, `:3165`) et que le moteur la garde (`services/tool_confirmations.py:89-91`) | « Envoyer cet e-mail ? » surgit sans dire d'où |
| Échec du flux : texte | `setInput`, `saveDraft` (`ChatInput.tsx:835`, `:841`) ; `saveDraft` et `clearDraft` prennent la conversation du rendu (`hooks/useAutosave.ts:56`, `:136`) | le message raté d'Orion atterrit dans le champ de Veille |
| Échec du flux : pièces jointes | `setAttachedFiles(sentFiles)` (`ChatInput.tsx:836-840`) | les documents d'Orion rejoignent le composeur de Veille, et l'envoi suivant les ferait partir dans une autre conversation, voire un autre projet (constat 3 de la revue) |
| Conversation fantôme (404) | `deleteConversation(currentConversationId)` (`ChatInput.tsx:848-856`) | c'est Veille qui serait retirée du store |
| Entités détectées | `clearMessageEntities` ne cherche que dans la conversation affichée (`chatStore.ts:284-297`) | écarter une entité d'Orion depuis Veille ne ferait rien (constat 4) |
| Activité et fournisseur | `setActivity` (`stores/statusStore.ts:61-62`, appelé en `ChatInput.tsx:632`, `:734`, `:869`) ; `fournisseurCourant` (`chatStore.ts:84`) | la fin d'Orion remet l'indicateur « au repos » pendant que Veille réfléchit |
| Arrêt venu de « Travaux » | le lecteur rend la main sur `done` ou `error` seulement (`services/api/chat.ts:189-191`) ; aucune branche `cancelled` | la bulle se fige vide, sans « interrompu » |
| Recherche approfondie | même structure, second chemin (`ChatInput.tsx:882-991`) | mêmes effets |

### 3.6 Supprimer, vider, déplacer, effacer, restaurer pendant un flux

| Geste | Aujourd'hui | Risque si la réponse court |
|---|---|---|
| Supprimer une conversation depuis le tiroir | **non gardé** : `confirmDelete` ne consulte pas `navigationLocked` (`PrototypeConversationDrawer.tsx:301-310`) ; le moteur supprime sans regarder les générations (`routers/chat.py:3859-3881`) | déjà possible aujourd'hui pour la conversation affichée : le partiel ou la réponse finale s'écrivent ensuite dans une conversation disparue, sans erreur, puisque SQLite n'applique pas les clés étrangères (aucun `PRAGMA foreign_keys` sous `src/backend/app`) |
| Vider (`chat.clear`) | gardé (`ConversationCanvasPrototype.tsx:1878`) | aucun tant que la garde tient |
| Changer le projet | **non gardé** : le sélecteur n'est désactivé que pendant son propre enregistrement (`components/chat/ConversationProjectPicker.tsx:58`, `:161`) | une réponse nourrie des documents d'un projet s'écrit dans une conversation rangée sous un autre : la cloison ment |
| Effacer toutes mes données | `_arreter_les_travaux_de_fond` attend créations et indexations, pas les générations (`routers/data.py:602-629`) ; la suspension ne vise que les créations de fiches (`services/memory_tools.py:1251-1292`) ; la route `/api/chat/send` n'est pas suspendue | B-1425 : une réponse écrite après l'effacement (non reproduit en deux essais, décision 31 comme garde de conception) ; un envoi parti pendant la purge écrirait son message après elle |
| Restaurer une sauvegarde | mode maintenance : les nouvelles requêtes sont refusées (`services/maintenance.py:30-49`), mais une réponse en flux est relâchée après ses en-têtes (`main.py:731-734`) ; `_arreter_les_travaux_de_fond` précède la fermeture de la base (`routers/data.py:1583-1587`) | la réponse s'écrit dans la base restaurée, ou échoue sur une base fermée |
| Importer des conversations | additif, saute les existantes (`routers/data.py:1812-1817`) | aucun (décision Q-import) |

### 3.7 « Travaux »

Les lignes de chat et de recherche approfondie mènent à leur conversation (P-140), mais le chemin passe par la garde (`ConversationCanvasPrototype.tsx:1412-1413`) : pendant un flux, il est refusé comme le reste. Et `ouvrirConversation` (`:1417-1420`) ne fait que `loadConversation(id)` : une conversation absente du store (liste plafonnée, identité pas encore adoptée) s'ouvre vide, puisque la synchronisation n'agit que sur une conversation présente (`hooks/useConversationSync.ts:201-211`).

### 3.8 Connexions

Chaque flux tient une connexion HTTP ouverte des minutes durant, lue par `getReader` : chat et recherche (`services/api/chat.ts:165`, `:226`), Board (`services/api/board.ts:112`), Atelier (`services/api/agents.ts:169`, `:431`), trame documentaire (`services/api/documents.ts:278`). Toute autre requête a un délai de 30 s (`services/api/core.ts:122`, `:250`). Chromium, donc WebView2 sous Windows, ouvre six connexions HTTP/1.1 par hôte ; le plafond de WKWebView et de WebKitGTK n'est pas lisible dans le code et se mesure en recette. Sans plafond de réponses, flux de fond, Board, Atelier et trame peuvent occuper ce pool, et l'Agenda tomberait au délai.

## 4. Options et recommandation

Les trois options de la V1 restent les bonnes : A (le flux quitte le composeur pour un registre par conversation), B (génération détachée côté moteur, avec reprise après rechargement), C (garder le verrou, l'adoucir). C ne répond pas au besoin accepté ; B est écartée par la décision V1-Q5.

**Recommandation : A**, complétée par un lot moteur que la V1 omettait. Le moteur sait déjà finir une réponse, l'annuler par conversation et garder un partiel ; le verrou protège surtout l'interface contre ses propres états globaux. On protège d'abord les données (lot 1), on donne ensuite au flux un propriétaire qui survit aux changements d'écran (lots 2 à 4), puis on lève le verrou (lot 5).

## 5. Conception

### 5.1 Moteur (lot 1)

1. **Arrêt d'office des réponses avant une purge ou une restauration (décision 31).** Une fonction `arreter_les_generations_en_cours()` demande l'arrêt de chaque traitement `chat` et `deep-research` actif (chemin de `/cancel`, `routers/chat.py:1016-1027` : `demander_arret`, `services/traitements.py:200`), pose aussi le jeton de chaque contexte encore inscrit sans traitement (`_active_generations`, repli du suivi en panne, `routers/chat.py:1960-1975`), puis **attend l'état terminal** de chacun. Elle est appelée en tête de `_arreter_les_travaux_de_fond` (`routers/data.py:602-629`), donc par la purge (`:633`) comme par la restauration (`:1583`, avant `close_db` à `:1587`), sous le plafond existant (`DELAI_MAX_TRAVAUX_DE_FOND_S`, `:595`) : au-delà, rien n'est touché et la route répond 503, comme aujourd'hui. Pourquoi attendre l'état terminal et pas seulement demander : le partiel s'écrit pendant la fermeture du producteur (`:2726-2733`), avant que le traitement ne passe à « Arrêté » (`:2132-2137`) ; attendre cet état garantit que la dernière écriture de la génération précède l'effacement, qui l'emporte alors. La réponse de la route porte `reponses_arretees`.
2. **Aucune génération ne démarre pendant une purge.** `/api/chat/send` et `/api/chat/deep-research` consultent la suspension des créations (`services/memory_tools.py:1251-1278`) avant d'écrire le message de l'utilisateur (`routers/chat.py:1307-1317`) et répondent 409 : « Une opération sur tes données est en cours (effacement ou restauration) : rien n'a été envoyé. » La restauration refuse déjà tout par le mode maintenance.
3. **Jamais d'écriture dans une conversation disparue.** `_persister_message_partiel` (`routers/chat.py:2158-2190`) et l'écriture finale (`:2846-2847`) relisent la conversation et n'écrivent rien si elle n'existe plus (journal, pas d'erreur à l'écran : la conversation n'est plus là pour l'afficher).
4. **Supprimer une conversation dont la réponse court est refusé** : `delete_conversation` (`:3859-3881`) répond 409 tant qu'un traitement `chat` ou `deep-research` actif lui est rattaché, avec un détail qui propose d'arrêter la réponse. L'écran pose la même règle (§ 5.7) ; le moteur la tient pour tous les appelants.
5. **Banc SQLite** (constat 8 de la revue) : sur une vraie base en fichier (le banc de tests place les données dans un dossier temporaire, `tests/conftest.py:38` ; le test vérifie que l'URL du moteur désigne un fichier), deux réponses de deux conversations finissent en même temps pendant qu'une écriture utilisateur a lieu ; chacune est écrite une fois, aucune « database is locked » (WAL et `busy_timeout` de 5 s, `models/database.py:1050-1051`).

Aucune colonne ne change : la tête Alembic reste `b8c9d0e1f2a3` (`models/database.py:619`).

### 5.2 Un registre des réponses en cours (lot 2)

- `lib/reponsesEnCours.ts`, avec un petit store Zustand : une entrée par conversation, clé = identifiant serveur (la conversation est enregistrée avant le départ, `ChatInput.tsx:677-690`). L'entrée porte : la bulle, l'`AbortController`, l'identifiant de génération (événement `generation`), le fournisseur et le modèle, le caractère local (`fournisseurDAccord(fournisseur, modele) === null`, `lib/ollamaCloud.ts:19-23`), l'heure de départ, le texte envoyé et les pièces jointes envoyées.
- La clé suit l'adoption d'identité (`chatStore.ts:444-452`) : l'entrée est renommée, jamais dupliquée.
- La boucle de lecture et la fin du flux (`ChatInput.tsx:693-878`), pour le chat **et** pour la recherche approfondie (`:921-990`), deviennent des fonctions du module, avec la conversation d'origine en paramètre explicite ; le flux ne relit jamais `currentConversationId` après son départ. Le composeur garde la préparation (accord cloud, variables, pièces jointes, bulles, persistance), puis confie le flux.
- `arreter(conversationId)` coupe la lecture de cette réponse et appelle `cancelGeneration` sur sa conversation, ce qui vise la bonne génération puisqu'une conversation n'a jamais deux réponses (§ 5.7). « Arrêter » du composeur, le bandeau B-1369 et « Travaux » passent tous par là ; `lib/arretDeLaReponse.ts` devient une façade du registre, et `arreterLaReponse()` sans argument garde son sens actuel : la réponse de la conversation affichée.
- L'événement `cancelled` fige la bulle comme un arrêt du composeur (`ChatInput.tsx:825-831` : le texte reçu, ou « (interrompu) »).
- Sur un 404 « Conversation not found », c'est la conversation d'origine qui est retirée du store.
- `saveDraft` et `clearDraft` reçoivent la clé de la conversation d'origine au lieu de celle du rendu.

### 5.3 Des états par conversation (lot 3)

- `isStreaming` devient le sélecteur `reponseEnCours(conversationId)`. L'indicateur « Réflexion », le repère « modèle local » (`MessageList.tsx:79`, avec le fournisseur de l'entrée), le suivi du bas du fil, « Arrêter », le texte du champ et les suggestions ne regardent que la conversation affichée.
- L'activité globale (`setActivity`) suit la conversation affichée : une réponse de fond n'y touche pas, et changer de conversation rend l'activité de celle qu'on ouvre.
- `clearMessageEntities` cherche dans toutes les conversations.

### 5.4 Une file par conversation et un plafond (lot 4)

- `filesDAttente[conversationId]` : une place par conversation, comme aujourd'hui (`chatStore.ts:85`).
- **Un envoi part tout de suite** si sa conversation n'a pas de réponse en cours, si moins de deux flux de réponse sont ouverts (décision 30), et, pour un envoi local, si aucun flux local ne l'est (décision V1-Q1). Sinon il entre dans la file de sa conversation, avec la mention qui dit la vraie raison :
  - réponse de la même conversation : comme aujourd'hui (« Un message en file d'attente ») ;
  - plafond : « En file : partira dès qu'une des deux réponses en cours sera finie. » ;
  - modèle local : « En file : partira à la fin de la réponse d'Orion. Le modèle local peut aussi servir d'autres travaux, que « Travaux » montre. » La seconde phrase répond au constat 7 de la revue : la décision de départ ne regarde que les réponses du chat, seules connues de l'interface (un traitement ne dit pas s'il est local, `services/api/processingTasks.ts:6-29`), et la mention ne tait pas le reste.
- L'auto-envoi ne part que dans la conversation affichée, une fois sa propre réponse finie et le plafond libre ; il est réévalué à chaque fin d'entrée du registre.
- **Quitter une conversation dont un message attend en file** : ce message devient le brouillon de cette conversation (clé B-1377), avec « Ton message attend dans Orion : il est gardé en brouillon. » Il ne part jamais ailleurs, ni plus tard sans geste.
- Le transport de l'accueil (B-626) met le texte dans la file de la conversation qu'`openChat` va afficher, créée d'abord s'il n'y en a pas.

### 5.5 La fin d'une réponse qu'on ne regarde plus (lot 4)

- **Succès** : notification « Réponse prête dans Orion » avec « Ouvrir » (même forme d'action que le bandeau B-1369, `ConversationCanvasPrototype.tsx:1084-1088`), repère sur la ligne du tiroir jusqu'à l'ouverture.
- **Navigation reçue** : exécutée à la fin seulement si la conversation est toujours affichée et que l'utilisatrice n'a pas changé d'écran entre-temps ; sinon, jamais exécutée, et la notification la propose (« La réponse d'Orion propose d'ouvrir l'Agenda »).
- **Carte d'action sensible** : `PendingConfirmation` porte `conversation_id`, pris dans l'événement ; la carte dit « Depuis Orion » et propose « Ouvrir la conversation ». Elle reste visible partout et n'est jamais validée sans clic.
- **Échec** : le texte rejoint le brouillon d'Orion sous sa clé ; les pièces jointes restent dans l'entrée d'Orion et reviennent dans le composeur quand Orion est rouverte (décision 32). Le composeur affiché n'est pas touché. Ce rattachement vit en mémoire : un rechargement arrête de toute façon la réponse, et le message de l'utilisateur, déjà écrit en base avec ses pièces jointes (`routers/chat.py:1311-1317`, BUG-160), les garde dans la conversation.
- **Arrêt venu de « Travaux » ou d'une purge** : la bulle se fige avec son texte ou « (interrompu) » ; la file de cette conversation n'est pas relancée par cet arrêt.

### 5.6 Suivre et revenir (lot 6)

- **« Travaux »** : la ligne ouvre sa conversation sans passer par la garde de flux ; une conversation absente du store est chargée par l'API avant d'être ouverte.
- **Pastille** « Réponse en arrière-plan · Orion », à côté de celles du Board et de l'Atelier (`ConversationCanvasPrototype.tsx:2083-2084`), qui ouvre la conversation.
- **Tiroir** : repère « réponse en cours » sur la ligne, puis « réponse prête » jusqu'à l'ouverture.

### 5.7 Ce qui reste interdit

1. **Deux réponses dans la même conversation** : le second message reste en file. Le moteur n'écrit la réponse qu'à la fin (`routers/chat.py:2846-2847`) : un second tour partirait avec un historique qui ne la contient pas, et le registre par conversation (`:134-143`) ferait de la seconde génération la courante.
2. **Supprimer, vider ou changer le projet** d'une conversation dont la réponse court : refusé avec « Arrêter la réponse » (B-1369). Vider l'est déjà ; supprimer et changer le projet ne le sont pas aujourd'hui (§ 3.6) et le deviennent, la suppression aussi côté moteur (§ 5.1, point 4).
3. **Exécuter en fond** une navigation ou une action sensible sans clic.
4. **Une conversation éphémère** garde le verrou actuel (décision V1-Q4).
5. **Recharger ou fermer THÉRÈSE** arrête les réponses en cours : partie produite conservée (B-1461, B-1462), « Arrêté » dans « Travaux », écran quitté rouvert (P-142). La fenêtre ne l'intercepte pas (règle Tauri : pas d'`onCloseRequested`).
6. **Effacer ou restaurer** arrête d'office les réponses en cours et le dit (décision 31) : la confirmation annonce « N réponses en cours seront arrêtées » quand le registre n'est pas vide, et le message final reprend le compte rendu par le moteur (`components/settings/PrivacyTab.tsx:163-197`).

### 5.8 Hors périmètre, nommé

- La reprise après rechargement (option B, décision V1-Q5).
- La rédaction d'une section de l'Atelier documentaire, encore coupée quand on ferme le document (`stores/documentStore.ts:257`), alors que la trame continue depuis B-1374.
- La conversation vocale (P-109) : sa revue (constat 6) demande qu'elle passe par ce registre ; elle le fera après les lots 2 et 3 d'ici.

## 6. Réponse à la revue

| Nº | Gravité | Constat de la revue | Réponse | Où |
|---|---|---|---|---|
| 1 | P2 | Réponses de fond en ligne non plafonnées, alors que chaque flux tient une connexion et que le webview plafonne les connexions par hôte ; délai client de 30 s | Décision 30 : deux flux de réponse ouverts au plus, affichée comprise, un seul local ; au-delà, file de la conversation avec mention. Plafond Chromium connu, WebKit à mesurer ; recette sous Windows « deux réponses et une délibération du Board ouvertes, l'Agenda se charge encore » | § 2, § 3.8, § 5.4, lots 4 et 6 |
| 2 | P2 | Purge, restauration et import oubliés : une réponse peut s'écrire après l'effacement ou dans la base restaurée | Décision 31 : arrêt et attente de l'état terminal avant toute suppression, pour la purge et la restauration ; générations refusées pendant la purge ; aucune écriture dans une conversation disparue. Import : additif, laissé permis (décision Q-import). Test moteur « purge pendant un flux : aucune ligne `messages` après », qui fait aussi office de reproduction de B-1425 | § 3.6, § 5.1, lot 1 |
| 3 | P2 | Un échec remet aussi les pièces jointes dans le composeur affiché | Décision 32 : les pièces jointes restent sur l'entrée de la conversation d'origine et reviennent quand elle est rouverte ; test « échec d'Orion : Veille n'a aucune pièce jointe, Orion les retrouve » | § 3.5, § 5.5, lot 4 |
| 4 | P3 | `clearMessageEntities` ne cherche que dans la conversation courante | Ajouté à l'inventaire ; corrigé au lot 2 avec son test | § 3.5, § 5.3, lot 2 |
| 5 | P3 | « Travaux » mène déjà à la conversation (P-140), l'écran quitté se rouvre (P-142) : § 2.5 et lot 5 périmés | Inventaire rebasé ; il reste à ne plus passer par la garde de flux et à charger une conversation absente du store ; l'étape 7 de la recette compose avec P-142 | § 3.1, § 3.7, § 5.6, lot 6 |
| 6 | P3 | Inventaire des gardes décalé et incomplet (13 appels, pas 11) | Les 13 appels listés par geste ; le lot 5 est conduit par la fonction et par un test qui énumère ses appelants, pas par une liste de lignes | § 3.2, lot 5 |
| 7 | P3 | La mise en série locale ne regarde que le chat ; la mention tait les autres occupants du modèle | La décision de départ ne regarde que les réponses du chat, seules connues de l'interface ; la mention dit aussi que d'autres travaux peuvent occuper le modèle local et renvoie à « Travaux » | § 5.4, lot 4 |
| 8 | P3 | Le test moteur ne prouve l'absence de « database is locked » que sur une vraie base en fichier, avec deux fins simultanées | Banc précisé : base en fichier vérifiée, deux commits finaux concurrents et une écriture utilisateur au même moment | § 5.1 point 5, lot 0 |

Les trois questions que la revue adressait à Ludo sont les décisions 30 à 32.

## 7. Livraison en lots TDD

Chaque lot : tests écrits d'abord et vus rouges pour la bonne raison (sauf les caractérisations du lot 0, vertes par définition) ; un commit par lot ; sabotage ciblé par fonction, jamais par chaîne globale (règle du 27/08) ; les six portes du dépôt ; revue adverse du diff. Le verrou reste en place jusqu'au lot 5 : chaque lot avant lui se livre sans changement visible pour Hugo, sauf le lot 1, qui protège les données.

**Lot 0. Caractérisation (aucun code applicatif).**
Verts attendus, ils protègent l'hypothèse dont tout dépend : deux conversations en flux simultané écrivent chacune leur réponse une seule fois, et `/cancel/{conversation_id}` arrête la bonne ; une conversation relue par `GET /api/chat/conversations/{id}/messages` pendant son flux ne montre la réponse qu'une fois, à la fin ; banc SQLite du § 5.1 point 5. Côté écran, les tests « à garder verts » du § 8 sont relevés tels quels.
Critère observable : `pytest` et `vitest` verts, aucun fichier applicatif touché.

**Lot 1. Le moteur protège les données (livrable seul).**
Rouges d'abord, avec un fournisseur factice lent : purge pendant un flux de chat, puis pendant une recherche approfondie : aucune ligne `messages` après, les traitements finissent « Arrêté », la réponse de la route porte `reponses_arretees` ; restauration pendant un flux : la réponse n'est écrite ni dans l'ancienne base ni dans la restaurée ; `send` et `deep-research` pendant une purge : 409, aucun message écrit ; conversation supprimée pendant une génération simulée : aucune écriture orpheline ; `DELETE /api/chat/conversations/{id}` pendant une génération : 409. Écran : le tiroir refuse de supprimer la conversation dont la réponse court et propose « Arrêter la réponse » ; `PrivacyTab` annonce l'arrêt et en dit le compte.
Critère observable : dans l'app, lancer une réponse, ouvrir Paramètres, « Effacer toutes mes données » : le message dit qu'une réponse a été arrêtée, et après le redémarrage aucune conversation ne réapparaît.

**Lot 2. Le registre, pour le chat et la recherche approfondie, verrou inchangé.**
Rouges d'abord : tests du registre (départ, fin, arrêt ciblé, renommage de clé à l'adoption, deux entrées indépendantes, `cancelled` qui fige la bulle) ; `clearMessageEntities` sur une conversation non affichée ; 404 fantôme qui retire la conversation d'origine ; brouillon effacé sous la clé d'origine.
À garder verts **sans modification** : `ChatInput.annulation`, `ChatInput.fluxCoupe.b1395`, `ChatInput.rattachement`, `ChatInput.brouillonParConversation.b1377`, `lib/arretDeLaReponse.test.ts` (la façade sans argument garde son sens actuel).
Critère observable : aucun changement visible ; les tests ci-dessus verts sans modification, et une réponse arrêtée depuis « Travaux » se fige avec « (interrompu) » au lieu d'une bulle vide.

**Lot 3. Des états par conversation.**
Rouges d'abord, en pilotant le store (deux entrées, Orion en flux, Veille affichée) : « Arrêter » absent dans Veille ; indicateur et repère local absents de Veille ; activité au repos dans Veille, rendue quand on revient dans Orion ; la fin d'Orion écrit dans Orion.
Critère observable : verrou toujours en place, aucun changement visible ; `vitest` vert, et une capture du chat pendant une réponse, prise avant et après le lot, est identique.

**Lot 4. Files, plafond et fins hors écran.**
Rouges d'abord : un message en file n'est consommé qu'une fois et jamais dans une autre conversation ; quitter Orion avec un message en file en fait son brouillon ; troisième envoi en ligne avec deux flux ouverts : en file avec la mention du plafond, parti à la première fin ; envoi local pendant une réponse locale : en file avec la mention locale ; envoi en ligne pendant une réponse locale : part tout de suite ; échec d'Orion : champ et pièces jointes de Veille intacts, pièces jointes retrouvées dans Orion ; navigation reçue par Orion quittée : non exécutée, proposée par notification ; carte d'action portant « Depuis Orion ».
Critère observable : verrou toujours en place ; dans l'app, un message tapé pendant une réponse part encore à sa fin dans la même conversation, et une carte « Envoyer cet e-mail ? » dit de quelle conversation elle vient.

**Lot 5. Levée du verrou.**
La garde ne retient plus que la saisie modifiée (B-978) et les interdits du § 5.7 ; le tiroir, `runNavigationAction` et le sélecteur de projet suivent ; la vue demandée pendant un flux s'ouvre tout de suite au lieu d'être rejouée à la fin (`ConversationCanvasPrototype.tsx:1284-1288`). Un test énumère les appelants de la garde (les 13 du § 3.2) et vérifie, pour chacun, qu'un flux dans une autre conversation ne les retient plus.
Tests à inverser explicitement, intention d'origine gardée là où elle vaut encore (conversation éphémère, suppression, vidage, projet) : `lib/clientActions.test.ts:88` (« refuse la navigation directe pendant un streaming ») ; `components/prototype/ConversationCanvasPrototype.parite.test.tsx:286` (« une navigation refusée pendant un flux n'est pas perdue ») et `:363` (refus B-1369) ; `components/prototype/PrototypeConversationDrawer.test.tsx:138` (« conserve la conversation courante pendant une réponse en cours ») ; `lib/arretDeLaReponse.test.ts:33` (refus de navigation qui propose l'arrêt), qui ne vaut plus que pour une conversation éphémère.
Critère observable : dans l'app, pendant une réponse d'Orion, « Nouvelle conversation », l'Agenda et le tiroir s'ouvrent sans bandeau « Réponse en cours » ; supprimer Orion, la vider ou changer son projet est refusé avec « Arrêter la réponse ».

**Lot 6. Suivre et revenir, puis recette.**
Rouges d'abord : une ligne de « Travaux » ouvre sa conversation pendant un flux ; une conversation absente du store est chargée puis ouverte ; pastille et repère du tiroir ; notification « Réponse prête » et son « Ouvrir ».
Recette navigateur (pile jetable 17393 et 1420, jamais 17293 ; modèle local réel, ou flux ralenti par `page.route`), le parcours de Hugo : lancer une réponse dans Orion ; « Nouvelle conversation », écrire dans Veille ; ouvrir l'Agenda ; revenir par « Travaux », puis par la pastille ; compter les messages d'Orion en base ; arrêter une réponse depuis « Travaux » ; recharger pendant une réponse de fond, lire la partie conservée et vérifier que l'écran quitté se rouvre (P-142). Sous Windows (WebView2) : deux réponses en ligne et une délibération du Board ouvertes, l'Agenda se charge en moins de 30 s ; relever le nombre de connexions ouvertes par hôte dans les trois webviews. Captures à chaque étape, console et réseau relevés.
Critère observable : le parcours de Hugo se déroule sans refus ; Orion compte en base une seule réponse ; l'Agenda s'affiche sous Windows avec trois flux ouverts.

## 8. Plan de tests, en résumé

- **Unitaires** : le registre (départ, fin, arrêt ciblé, renommage, deux entrées, `cancelled`) ; le sélecteur `reponseEnCours` ; la file (une place, consommée une fois, reconvertie en brouillon) ; la règle de départ (plafond, local).
- **Composants et stores** : Orion en flux, Veille ouverte par le tiroir, avec les attendus des lots 3 et 4.
- **Moteur** : lot 0 (hypothèse et banc SQLite), lot 1 (purge, restauration, envoi pendant la purge, suppression, écriture orpheline).
- **À garder verts sans modification** : `ChatInput.annulation`, `ChatInput.brouillonParConversation.b1377`, `ChatInput.fluxCoupe.b1395`, `ChatInput.rattachement`, `hooks/useConversationSync.test.ts`, `tests/test_chat_annulation_reelle.py`, `tests/test_chat_traitement.py`, `tests/test_fencing_traitement.py`, `tests/test_traitements_fondation.py`, `tests/test_b1461_depart_du_client_pendant_la_reponse.py`.
- **À inverser** : les cinq du lot 5.
- **Recette** : lot 6.

## 9. Risques et régressions à protéger

- **Concurrence de deux flux** : sûre côté moteur (une identité par génération, `tests/test_fencing_traitement.py:89`) ; côté modèle local, la file est dite à l'écran.
- **Messages en file** : jamais envoyés dans une autre conversation, jamais deux fois ; seul un double envoi pourrait écrire deux fois, et il est testé.
- **Purge et restauration** : une recherche approfondie ne s'arrête qu'entre deux étapes (`routers/chat.py:1152`) ; si l'attente dépasse le plafond, la route répond 503 et ne touche à rien, comme pour les autres travaux de fond. Une recherche dont le suivi est en panne (`:1138-1140`) n'a pas de traitement et ne peut pas être arrêtée par ce chemin : cas déjà dégradé, relevé dans le journal.
- **Identité adoptée (B-1377)** : la clé du registre est renommée à l'adoption ; « Travaux » peut désigner une conversation absente du store, chargée avant d'être ouverte.
- **Brouillons et pièces jointes** : aucune écriture dans le champ d'une autre conversation ; clés explicites.
- **Arrêt** : toujours celui de la réponse visée, jamais celui de la conversation affichée.
- **BUG-139** : la navigation reçue reste différée à la fin, et n'est plus exécutée hors de sa conversation.
- **B-1369** : les refus qui subsistent proposent encore « Arrêter la réponse ».
- **B-1395, B-1461** : un rechargement pendant une réponse de fond laisse une bulle relisible, pas « network error ».
- **Charge du fil** : plusieurs flux écrivent dans le store, dont l'écriture locale est déjà regroupée (`stores/chatStore.ts:456-459`).
- **Connexions** : le plafond de deux flux de réponse est un choix, pas une mesure ; la recette Windows peut le faire baisser à un, sans changer la conception.

## 10. Questions pour l'humain

Aucune. La purge arrête des réponses mais n'efface rien de plus que ce que l'utilisatrice a demandé d'effacer ; rien n'est annoncé publiquement ; la marque n'est pas en jeu. Les choix qui restaient ouverts sont tranchés au § 2, chacun avec son motif.

## Annexe : appuis dans le code (à `900765fb`)

- Coque : `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx` : `isStreaming` `:1046`, garde `:1076-1090`, appels `:1196`, `:1218`, `:1226`, `:1398`, `:1413`, `:1615`, `:1653`, `:1679`, `:1732`, `:1858`, `:1866`, `:1878`, `:2066` ; rejeu `:1284-1288` ; « Travaux » `:1409-1430` ; transport de l'accueil `:1799-1805` ; tiroir `:2051` ; pastilles `:2083-2084`.
- Tiroir : `src/frontend/src/components/prototype/PrototypeConversationDrawer.tsx:258-285`, `:301-310`. Projet : `src/frontend/src/components/chat/ConversationProjectPicker.tsx:58`, `:161`.
- Composeur : `src/frontend/src/components/chat/ChatInput.tsx` : pièces jointes `:126`, `abortRef` `:156`, brouillon `:182`, file `:543-548`, accord `:558-589`, envoi `:596-639`, persistance `:677-690`, flux `:693-813`, fin `:816-878`, recherche `:882-991`, auto-envoi `:1020-1028`, arrêt `:1031-1048`, `:1063`, brouillon par conversation `:1127-1155`, affichage `:1239`, `:1509`, `:1538-1571`.
- Stores : `src/frontend/src/stores/chatStore.ts:82-85`, `:174-186`, `:188-342`, `:344`, `:349-357`, `:444-452`, `:456-473` ; `src/frontend/src/stores/toolConfirmationStore.ts:17-21` ; `src/frontend/src/stores/statusStore.ts:61-62` ; affichage `src/frontend/src/components/chat/MessageList.tsx:53-86`, `:92`, `:153-154`.
- Brouillons : `src/frontend/src/hooks/useAutosave.ts:5-8`, `:56`, `:136-153`, `:155-177`. Local ou en ligne : `src/frontend/src/lib/ollamaCloud.ts:19-23`.
- Navigation et arrêt : `src/frontend/src/lib/clientActions.ts:29-53` ; `src/frontend/src/lib/arretDeLaReponse.ts:10-32`.
- « Travaux » : `src/frontend/src/lib/destinationDuTravail.ts:29-31` ; `src/frontend/src/components/traitements/TraitementsPanel.tsx:85-123` ; `src/frontend/src/services/api/processingTasks.ts:6-29`.
- API écran : `src/frontend/src/services/api/core.ts:122`, `:250` ; `src/frontend/src/services/api/chat.ts:66-67`, `:147-199`, `:208-260`, `:400-404` ; flux longs `board.ts:112`, `agents.ts:169`, `:431`, `documents.ts:278`.
- Purge et restauration à l'écran : `src/frontend/src/components/settings/PrivacyTab.tsx:163-197`.
- Moteur, chat : `src/backend/app/routers/chat.py` : registre `:124-205`, annulation `:1000-1042`, recherche approfondie `:1053-1230`, message utilisateur `:1307-1317`, flux `:1688-1700`, génération `:1910-2137`, partiel `:2158-2190`, attente d'annulation `:2193-2210`, écritures `:2726-2733`, `:2833-2847`, suppression `:3859-3881`.
- Moteur, données : `src/backend/app/routers/data.py` : purge `:565-589`, plafond `:595`, travaux de fond `:602-629`, restauration `:1442-1453`, `:1456`, `:1560-1595`, `:1660-1667`, import `:1763-1817` ; `src/backend/app/services/memory_tools.py:1251-1292` ; `src/backend/app/services/maintenance.py:30-65` ; `src/backend/app/main.py:718-734` ; `src/backend/app/services/traitements.py:168`, `:200`, `:329` ; `src/backend/app/services/tool_confirmations.py:89-91` ; `src/backend/app/models/database.py:619`, `:1050-1051`.
