# RFC P-125 : changer de sujet pendant une réponse longue, la réponse se termine en fond

Rédigé le 25/09/2026. Proposition acceptée par Ludo le 25/09 (« Je valide tout sauf la 141 »). Aucun code avant la validation de ce document.

## 1. Le besoin

Hugo, persona du cycle 13 (`docs/campagnes/2026-09-25-personas-c13/rapports/hugo.md`, hugo-07, étapes 2.1, 2.4 et 2.6, captures 14, 16 et 21 à 23), travaille avec un modèle local :

- ses réponses ont pris 4 min 35, 7 min 10 (pour répondre « noté »), 5 min 7 et 2 min ;
- pendant ce temps, « Nouvelle conversation », un changement de vue ou l'ouverture d'une autre conversation sont refusés : « Réponse en cours. Arrête la réponse avant de changer de vue ou de conversation. » (le tiroir le dit autrement : « Arrête la réponse en cours avant de changer de conversation. ») ;
- il n'a que deux choix : attendre, ou jeter la réponse.

Sa piste : laisser la réponse se terminer en fond et la suivre dans « Travaux », qui la liste déjà. Voisins : hugo-08 (le bandeau cachait « Arrêter », B-1369, corrigé), hugo-13 (les lignes de Travaux ne mènent nulle part), hugo-14 (l'Atelier fait l'inverse : quitter jette la trame en silence), hugo-17 (brouillon qui suivait d'une conversation à l'autre, B-1377, corrigé).

## 2. Ce qui existe

### 2.1 Le refus est une règle de l'interface

- La coque consulte `blockStreamingNavigation` (`ConversationCanvasPrototype.tsx:984-998`) avant d'ouvrir le chat (`:1104`), de créer une conversation (`:1126`), d'ouvrir une vue (`:1134`), de fermer le chat par Échap (`:1442`) ou par sa croix (`:1873`), de changer de parcours (`:1480`) ou de capacité (`:1506`), et dans `runUnifiedAction` (`:1666`, `:1674`, `:1686`).
- Le tiroir reçoit `navigationLocked={isStreaming}` (`:1858`) et refuse (`PrototypeConversationDrawer.tsx:225-252`).
- `runNavigationAction` refuse aussi (`lib/clientActions.ts:29-43`).
- Une navigation posée dans le store pendant le flux est rejouée à la fin (`ConversationCanvasPrototype.tsx:1190-1196`).

### 2.2 Le moteur sait déjà finir une réponse sans écran

- Chaque génération est un traitement `chat` rattaché à sa conversation (`routers/chat.py:1935-1942`). Son identifiant part au navigateur dans le premier événement `generation` (`:1977-1986`), que le composeur ignore aujourd'hui.
- Les registres sont tenus par conversation et protégés par le jeton de chaque génération (`:126-205`). Deux générations qui se chevauchent ne se gênent pas (`tests/test_fencing_traitement.py`, `test_deux_generations_chevauchees_ne_se_fencent_pas`). Une génération longue et vivante n'est jamais purgée (`:2055-2056`, `:2162-2180`, test p211).
- Le message de l'utilisateur est écrit avant le flux (`:1312-1313`) ; la réponse est écrite une fois, à la fin (`:2815-2816`). Une réponse arrêtée garde, une fois, sa partie produite (`:2127-2160`, `:2695-2702`, `:2803-2813`).
- Le modèle local n'a pas de délai de lecture (`services/providers/ollama.py:169-173`).
- **Contrainte structurante** : la génération vit tant que la connexion HTTP du flux vit. Une déconnexion vaut arrêt réel (`GeneratorExit` donne `cancelled`, `:2071-2078`), principe voulu depuis la 0.46. Pour qu'une réponse se termine en fond, **la lecture du flux doit survivre au changement d'écran**. C'est un chantier d'interface, pas de moteur.

### 2.3 L'interface écrit déjà au bon endroit

- Rien ne coupe le flux quand le composeur disparaît : l'arrêt n'a lieu que dans `stopStreaming` (`ChatInput.tsx:1020-1037`).
- La bulle de réponse est créée avant tout départ possible (`ChatInput.tsx:602-628`). `updateMessage`, `setMessageEntities`, `setMessageMetadata` et `setMessageSkillFile` cherchent le message dans **toutes** les conversations (`stores/chatStore.ts:244-338`, avec un commentaire US-010 qui prévoyait ce cas).
- La synchronisation n'écrase pas une conversation qui a des messages locaux (`hooks/useConversationSync.ts:137-145`, `:201-211`).

### 2.4 Mais plusieurs états pensent « la conversation affichée »

Voici ce qui se passerait si l'on retirait seulement la garde :

| État ou geste | Où | Effet si Hugo change de conversation |
|---|---|---|
| `isStreaming`, un seul booléen pour toute l'application | `chatStore.ts:81`, `:340` ; lu par `MessageList.tsx:54-86`, `:92`, `:153` et par le composeur (`ChatInput.tsx:1459-1523`) | L'indicateur « Réflexion », le repère « modèle local » et « Arrêter » s'affichent dans la nouvelle conversation ; son premier envoi part en file au lieu de partir |
| Arrêt du composeur | `abortRef` (`ChatInput.tsx:148`), `cancelGeneration(currentConversationId)` (`:1025`) | « Arrêter » dans Veille coupe la lecture d'Orion côté navigateur et demande l'arrêt de Veille au moteur : l'arrêt frappe à côté |
| Arrêt joignable hors du composeur | un seul emplacement, retiré au démontage (`lib/arretDeLaReponse.ts:10-20`, `ChatInput.tsx:1052`) | Hors du chat, plus aucun arrêt, sauf par Travaux |
| File d'attente d'une place, globale | `chatStore.ts:84` ; auto-envoi dans le composeur monté (`ChatInput.tsx:1008-1017`) ; transport depuis l'accueil (`ConversationCanvasPrototype.tsx:1609-1614`) | Un message mis en file dans Orion part dans la conversation affichée à la fin |
| Navigation reçue du moteur | mise de côté puis exécutée à la fin (`ChatInput.tsx:767-774`, `:855-867`) | Une vue s'ouvre sous les yeux de Hugo pendant qu'il travaille ailleurs |
| Carte « action sensible à valider » | `ChatInput.tsx:784-787` ; `PendingConfirmation` ne porte pas la conversation (`stores/toolConfirmationStore.ts:17-21`), alors que le moteur l'envoie (`chat.py:1485`, `:1581`, `:2248`, `:3134`) | « Envoyer cet e-mail ? » surgit au-dessus d'une autre conversation, sans dire d'où |
| Échec du flux | `setInput(trimmed)` et `saveDraft` (`ChatInput.tsx:824-830`) | Le message raté d'Orion atterrit dans le champ de Veille : le défaut B-1377 par un autre chemin |
| Brouillon effacé au succès | `clearDraft` (`:809`), clé prise au rendu | À rendre explicite (clé de la conversation d'origine) |
| Activité et fournisseur | `statusStore.ts:61-62`, `fournisseurCourant` | La fin d'Orion remet l'indicateur « au repos » pendant que Veille réfléchit |
| Arrêt venu de Travaux | l'événement `cancelled` n'a pas de branche (`ChatInput.tsx:719-802`) | La bulle se fige sans dire « interrompu » |
| Supprimer, vider | tiroir (`PrototypeConversationDrawer.tsx:270-271`), `chat.clear` (`ConversationCanvasPrototype.tsx:1685-1689`) | Orion supprimée pendant que le moteur y écrit |
| Recherche approfondie | même structure, second chemin d'envoi (`ChatInput.tsx:871-980`) | Mêmes effets |

### 2.5 Travaux

- Le panneau liste déjà les générations de plus de 2 s (`services/traitements.py:37-38`, `:329-373`), sous le libellé du message (`chat.py:1939`). Son « Arrêter » fonctionne (état `cancel_requested`, puis événement `cancelled`).
- Ses lignes ne mènent nulle part (`components/traitements/TraitementsPanel.tsx:80-139`, hugo-13).
- Précédent à réutiliser : les pastilles « Board en arrière-plan » et « Atelier en arrière-plan » (`ConversationCanvasPrototype.tsx:1888-1891`).

## 3. Trois options

| | A. Le flux quitte le composeur | B. Génération détachée côté moteur | C. Garder le verrou, l'adoucir |
|---|---|---|---|
| Idée | Un registre des réponses en cours, hors de React et par conversation, tient la connexion, l'arrêt et la fin ; l'interface passe de « un flux » à « un flux par conversation » | La génération devient une tâche du moteur, indépendante de la requête, avec un tampon d'événements et une route de réabonnement | Prévenir avant d'envoyer à un modèle local lent ; proposer « Arrêter et garder le début » dans le refus |
| Pour | Tout le moteur sert tel quel (suivi, annulation, persistance, cloisons) ; le risque reste dans l'interface | Survit à un rechargement de la fenêtre | Petit |
| Contre | Recharger ou fermer THÉRÈSE arrête encore la réponse (partie produite conservée, « Arrêté » dans Travaux) ; une dizaine de consommateurs à rattacher à leur conversation | Renverse le principe « déconnexion = arrêt réel » (0.46, J1b) ; la session de la requête (`chat.py:1684-1700`) ne peut plus servir ; tampon, reprise et nettoyage à écrire dans le code le plus revu du dépôt ; une interface plantée laisserait tourner, et facturer, une génération en ligne sans témoin ; demande **en plus** tout le travail de A | Ne répond pas au besoin accepté : Hugo reste bloqué 5 à 7 minutes |
| Effort | Moyen (sept lots) | Large | Petit |

## 4. Recommandation : l'option A

Le moteur fait déjà ce qu'il faut ; le verrou protège l'interface contre ses propres états globaux. On rattache ces états à leur conversation, on donne au flux un propriétaire qui survit aux changements d'écran, puis on lève le verrou. L'option B ne sera ouverte que si l'usage montre un besoin de reprise après rechargement.

### 4.1 Un registre des réponses en cours

- `src/frontend/src/lib/reponsesEnCours.ts`, avec son état dans un petit store Zustand : une entrée par conversation. La clé est l'identifiant serveur, puisque la conversation est enregistrée avant le départ (`ChatInput.tsx:666-679`). L'entrée porte la bulle, l'`AbortController`, l'identifiant de génération (événement `generation`), le fournisseur et l'heure de départ.
- La clé suit l'adoption d'identité (`chatStore.ts:440-448`, règle de `lib/identiteConversation.ts`) : si la conversation change d'identifiant pendant le flux, l'entrée est renommée, jamais dupliquée.
- `arreter(conversationId)` coupe la lecture de **cette** réponse et appelle `cancelGeneration` avec **son** identifiant. « Arrêter » du composeur, le bandeau B-1369 et Travaux passent tous par là.
- La boucle de lecture (`ChatInput.tsx:702-803`) et la fin du flux (`:805-867`) deviennent une fonction du module, avec la conversation d'origine en paramètre explicite. Le composeur garde la préparation (accord cloud, variables, pièces jointes, bulles, persistance), puis confie le flux.

### 4.2 Des états par conversation

- `isStreaming` devient `reponseEnCours(conversationId)`. L'indicateur, le repère « modèle local », le suivi du bas du fil, « Arrêter » et la file ne regardent que la conversation affichée.
- L'activité (« Réflexion en cours », « En train d'écrire ») ne suit que la conversation affichée ; une réponse de fond ne touche pas à l'indicateur global.
- Le flux ne relit jamais `currentConversationId` après son départ.

### 4.3 Une file par conversation

- `filesDAttente[conversationId]` : une place par conversation, comme aujourd'hui. L'auto-envoi ne part que dans la conversation affichée, une fois sa propre réponse finie.
- Quitter une conversation qui a un message en file : ce message devient le brouillon de cette conversation (clé de B-1377), avec le bandeau « Ton message attend dans Orion : il est gardé en brouillon. » Il ne part jamais ailleurs, ni plus tard sans geste.
- Le transport de l'accueil (B-626) vise la conversation que `openChat` va afficher.

### 4.4 La fin d'une réponse qu'on ne regarde plus

- **Succès** : notification « Réponse prête dans Orion » avec « Ouvrir » ; repère sur la ligne du tiroir jusqu'à l'ouverture.
- **Navigation reçue** : non exécutée ; la notification la propose (« La réponse d'Orion propose d'ouvrir l'Agenda »).
- **Carte d'action sensible** : `PendingConfirmation` porte la conversation, que le moteur envoie déjà. La carte dit « Depuis Orion » et propose d'ouvrir la conversation ; elle n'est jamais validée sans clic.
- **Échec** : le message rejoint le brouillon d'Orion sous sa clé ; le champ affiché n'est pas touché.
- **Arrêt venu de Travaux** : l'événement `cancelled` fige la bulle avec « (interrompu) », comme un arrêt du composeur.

### 4.5 Suivre et revenir

- **Travaux** : une ligne de chat ou de recherche approfondie rattachée à une conversation gagne « Ouvrir la conversation », avec le titre de la conversation en seconde ligne (lu dans le store). Si la conversation n'est pas dans le store (identité non adoptée, cas de `doitAdopterIdentiteServeur`), ses messages sont chargés avant de l'ouvrir.
- **Pastille** « Réponse en arrière-plan · Orion », à côté de celles du Board et de l'Atelier, qui ouvre la conversation.
- **Tiroir** : repère « réponse en cours » sur la ligne.

### 4.6 Deux réponses locales en même temps

Aucun verrou ne met les générations en série : deux réponses locales se partagent le modèle, et l'une attend l'autre sans que l'écran le sache. Recommandation pour la phase 1 : avec un fournisseur local, un envoi dans une autre conversation pendant une réponse locale se met dans **sa** file, avec la mention « Partira à la fin de la réponse d'Orion ». La mention est vraie, puisque c'est l'interface qui attend. En ligne, les réponses partent en parallèle.

### 4.7 Moteur

Aucun changement n'est obligatoire. Un test d'intégration fige l'hypothèse dont tout dépend : deux conversations en flux simultané écrivent chacune leur réponse une seule fois, et `/cancel/{conversation_id}` arrête la bonne.

## 5. Ce qui reste interdit

1. **Deux réponses dans la même conversation** : le second message reste en file. Le moteur n'écrit la réponse qu'à la fin (`chat.py:2815`) : un second tour partirait avec un historique qui ne la contient pas, et le registre par conversation (`:133-143`) ferait de la seconde génération la « courante ».
2. **Supprimer, vider ou changer le projet** d'une conversation dont la réponse court : le périmètre a été résolu au départ, la cloison doit rester vraie. Le refus propose « Arrêter la réponse » (B-1369).
3. **Exécuter en fond** une navigation ou une action sensible sans clic.
4. **Une conversation éphémère** garde le verrou actuel : elle n'est pas enregistrée, il n'y a pas d'endroit où revenir.
5. **Recharger ou fermer THÉRÈSE** arrête les réponses en cours (partie produite conservée, « Arrêté » dans Travaux, B-1395). La pastille et Travaux le disent ; la fenêtre ne l'intercepte pas (règle Tauri : pas d'`onCloseRequested`).

Hors périmètre : l'Atelier documentaire, qui annule la trame quand on le quitte (hugo-14, `stores/documentStore.ts:238-249`). La même règle devrait s'y appliquer un jour ; ce n'est pas ce chantier.

## 6. Livraison en lots TDD

Chaque lot : tests rouges d'abord ; un commit ; sabotage ciblé par fonction ; six portes ; revue adverse du diff.

0. **Caractérisation.** Scénarios rouges du § 2.4 : arrêt qui frappe à côté, message en file envoyé ailleurs, message raté dans le mauvais champ, navigation surprise, carte sans origine, indicateur dans la mauvaise conversation. Côté moteur, le test d'intégration du § 4.7 (vert attendu : il protège).
1. **Registre et boucle hors du composeur**, verrou inchangé. `ChatInput.annulation`, `ChatInput.fluxCoupe.b1395` et `ChatInput.rattachement` passent sans modification. Tests du registre : renommage de clé à l'adoption, arrêt ciblé, fin, `cancelled`.
2. **États par conversation** : `MessageList`, composeur, activité, arrêt ciblé.
3. **File par conversation et fins hors écran** : navigation, carte étiquetée, échec vers le brouillon d'origine, `clearDraft` à clé explicite, mise en série des réponses locales (§ 4.6).
4. **Levée du verrou** : la garde ne retient plus que les interdits du § 5 ; le tiroir et `runNavigationAction` suivent ; tests inversés (§ 7).
5. **Suivre et revenir** : Travaux, pastille, notification, repère du tiroir ; recette navigateur.
6. **Recherche approfondie** par le même registre (second chemin d'envoi, même traitement).

## 7. Plan de tests

**Unitaires** : le registre (départ, fin, arrêt ciblé, renommage, deux entrées indépendantes) ; le sélecteur `reponseEnCours` ; la file (une place, consommée une seule fois, reconvertie en brouillon quand on quitte la conversation).

**Composants et stores** : Orion en flux, puis ouverture de Veille par le tiroir. Vérifier que :

- « Arrêter » n'est pas proposé dans Veille ;
- Veille envoie tout de suite (en ligne) ou met en file avec la mention (local) ;
- la fin d'Orion écrit dans Orion et notifie ;
- un échec d'Orion laisse le champ de Veille intact ;
- une navigation reçue n'est pas exécutée ;
- une carte d'action porte « Depuis Orion » ;
- la suppression et le vidage d'Orion sont refusés pendant la réponse.

**Tests à inverser explicitement** : `lib/clientActions.test.ts` (F6, refus pendant un flux), `ConversationCanvasPrototype.parite.test.tsx` (« une navigation refusée pendant un flux n'est pas perdue », refus B-1369), `PrototypeConversationDrawer.test.tsx` (« conserve la conversation courante pendant une réponse en cours »), `lib/arretDeLaReponse.test.ts` (un seul emplacement d'arrêt). Chaque inversion garde l'intention d'origine là où elle vaut encore (conversation éphémère, suppression).

**À garder verts sans modification** : `ChatInput.annulation`, `ChatInput.brouillonParConversation.b1377`, `ChatInput.fluxCoupe.b1395`, `ChatInput.rattachement`, `hooks/useConversationSync.test.ts`, `tests/test_chat_annulation_reelle.py`, `tests/test_chat_traitement.py`, `tests/test_fencing_traitement.py`, `tests/test_traitements_fondation.py`.

**Moteur** : le test du § 4.7. Vérifier aussi qu'une conversation en flux, relue par `GET /api/chat/conversations/{id}/messages`, ne montre la réponse qu'une fois, à la fin.

**Recette navigateur** (pile jetable 17393 et 1420 ; modèle local réel, ou flux ralenti par `page.route`), le parcours de Hugo :

1. lancer une réponse dans Orion ;
2. « Nouvelle conversation », puis écrire dans Veille ;
3. ouvrir l'Agenda ;
4. revenir par Travaux, puis par la pastille ;
5. compter les messages d'Orion en base ;
6. arrêter une réponse depuis Travaux ;
7. recharger pendant une réponse de fond et lire la partie conservée.

Captures à chaque étape, console et réseau relevés.

## 8. Risques et régressions à protéger

- **Concurrence de deux flux** : sûre côté moteur (un jeton par génération) ; côté modèle local, la file est dite à l'écran (§ 4.6).
- **Messages en file** : jamais envoyés dans une autre conversation, jamais envoyés deux fois.
- **Persistance** : le navigateur n'écrit aucun message en base ; le moteur écrit une seule fois. Le seul risque de double écriture est un second envoi du même message (file consommée deux fois) : il est testé.
- **Identité adoptée du serveur (B-1377)** : la clé du registre est renommée à l'adoption. Travaux peut désigner une conversation absente du store, à charger avant de l'ouvrir.
- **Brouillons (B-1377)** : aucune écriture dans le champ d'une autre conversation ; clés explicites.
- **Arrêt** : toujours celui de la réponse visée, jamais celui de la conversation affichée.
- **BUG-139** : la navigation reçue reste différée à la fin, et n'est plus exécutée hors de sa conversation.
- **B-1369** : les refus qui subsistent (suppression) proposent encore « Arrêter la réponse ».
- **B-1395** : un rechargement pendant une réponse de fond laisse une bulle relisible, pas « network error ».
- **Charge du fil** : plusieurs flux écrivent dans le store ; l'écriture locale est déjà regroupée (`chatStore.ts:452-455`).

## 9. Questions pour Ludo

1. Deux réponses locales : l'une après l'autre avec la mention (recommandé), ou en parallèle ?
2. Fin d'une réponse de fond : notification et pastille (recommandé), ou pastille seule ?
3. Une carte « envoyer cet e-mail ? » venue d'une réponse de fond : visible partout avec son origine (recommandé), ou seulement en revenant dans la conversation ?
4. Conversation éphémère : garder le verrou (recommandé) ?
5. Reprise après rechargement (option B) : à n'ouvrir que si l'usage la réclame ?

## Annexe : appuis dans le code

- Garde : `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx:954`, `:984-998`, `:1103-1134`, `:1190-1234`, `:1442`, `:1479-1506`, `:1660-1690`, `:1858`, `:1873` ; pastilles `:1888-1891` ; transport de l'accueil `:1609-1614` ; Travaux `:1789`.
- Tiroir : `src/frontend/src/components/prototype/PrototypeConversationDrawer.tsx:225-252`, `:270-271`.
- Navigation : `src/frontend/src/lib/clientActions.ts:29-60` ; arrêt : `src/frontend/src/lib/arretDeLaReponse.ts`.
- Composeur : `src/frontend/src/components/chat/ChatInput.tsx:148`, `:531-537`, `:602-867`, `:871-980`, `:1008-1052`, `:1111-1139`.
- Stores : `src/frontend/src/stores/chatStore.ts:77-117`, `:187-338`, `:340-343`, `:440-466` ; `src/frontend/src/stores/toolConfirmationStore.ts:17-21` ; affichage : `src/frontend/src/components/chat/MessageList.tsx:53-86`, `:92`, `:153`.
- Travaux : `src/frontend/src/services/api/processingTasks.ts`, `src/frontend/src/stores/processingTasksStore.ts`, `src/frontend/src/components/traitements/TraitementsPanel.tsx:80-139`.
- Moteur : `src/backend/app/routers/chat.py:126-205`, `:999-1037`, `:1246-1313`, `:1905-2126`, `:2127-2180`, `:2695-2702`, `:2755-2816` ; `src/backend/app/services/traitements.py:37-38`, `:168-198`, `:276-373` ; `src/backend/app/models/processing.py:49-81`.
