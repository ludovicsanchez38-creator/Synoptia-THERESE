# RFC P-125 (V4) : changer de sujet pendant une réponse longue, la réponse se termine en fond

Rédigé le 26/09/2026. **Base relue : `main` à `7baf1793`.** Toutes les lignes citées ont été lues à ce commit ; la rédaction a commencé à `e49a679a`, une vingtaine de commits sont arrivés pendant (B-1522 à B-1535, P-132 lots 1 à 4), et chaque citation a été recalée puis vérifiée mécaniquement (existence de chaque ligne, première ligne relue). Depuis `a3c98b74`, base de la V3, ont bougé, parmi les fichiers cités : `routers/chat.py` (B-1513, une ligne de plus après `routers/chat.py:1203`), `routers/data.py` (B-1504 à B-1507, B-1522 à B-1524 ; les lignes de la purge et de la restauration citées ici sont inchangées), `main.py` (le mode maintenance est désormais à `main.py:729-752`), `components/chat/ChatInput.tsx` (B-1508 à B-1510, B-1514, B-1521, B-1525, B-1530), `hooks/useAutosave.ts` (B-1508), `services/memory_tools.py` (B-1533 : la suspension des créations descend d'une trentaine de lignes). La coque, le tiroir, les stores et les services de traitement n'ont pas bougé.

Remplace la V3 du même jour (`docs/plans/2026-09-26-rfc-p125-reponse-en-fond-v3.md`), refusée par la revue adverse du 26/09 (constats 8 à 20, dont six P2, verdict NO-GO). Proposition acceptée par Ludo le 25/09. Les décisions 31 et 32 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:108-112`) sont des faits ; la décision 30 est réservée à Ludo (§ 12). **Cette V4 est la dernière version avant implémentation** : pas de nouvelle revue de document ; chaque lot a sa revue de conception au moment du code, puis la revue adverse de son diff.

Chemins relatifs à `src/frontend/src/` (écran) et `src/backend/app/` (moteur), sauf mention.

## 0. Les constats de la revue et leur traitement

| Nº | Constat | Verdict, relu à `7baf1793` | Traitement | Où | Fermé au code, ou traité en design |
|---|---|---|---|---|---|
| 8 (P2) | Un envoi ouvert dans la route n'est jamais fermé si le client part avant le premier octet | **Accepté.** Sous uvicorn 0.40 (`"spec_version": "2.3"`, `.venv/lib/python3.13/site-packages/uvicorn/protocols/http/httptools_impl.py:227`), Starlette 1.2.1 lance la réponse et l'écoute de la déconnexion dans un groupe de tâches ; `stream_response` envoie l'en-tête avant tout `async for` (`.venv/lib/python3.13/site-packages/starlette/responses.py:248-254`), et le groupe est annulé à la déconnexion (`.venv/lib/python3.13/site-packages/starlette/responses.py:272-281`). Un générateur jamais démarré n'exécute pas son `finally` | L'envoi se ferme au niveau de l'appel ASGI de la réponse (`ReponseSuivie`), après la fermeture explicite du générateur (V4-1) | § 7.1, lot 1a | design ; test `test_client_parti_avant_le_premier_octet` au lot 1a |
| 9 (P2) | Pièces jointes indexées par chemin seul ; démontage qui abandonne l'indexation sans état | **Accepté.** `components/chat/ChatInput.tsx:127`, `components/chat/ChatInput.tsx:341` (dédoublonnage par chemin), `components/chat/ChatInput.tsx:274` (un contrôleur par chemin), `components/chat/ChatInput.tsx:284-290` (tout est annulé au démontage), `components/chat/ChatInput.tsx:322` (abandon : sortie sans statut). Aujourd'hui ce n'est pas un défaut (une seule liste, perdue au démontage) : c'est une contrainte de conception pour B-1512 | Store par conversation : dédoublonnage et indexation par (conversation, chemin), conduits hors du composant ; le démontage du composeur n'annule rien (V4-5) | § 7.3, lot 2 | design ; tests au lot 2 |
| 10 (P2) | Le transport de l'accueil (B-626) écrase ou envoie le brouillon de la cible | **Accepté, fiché B-1526** (différé à cette V4). Au montage du composeur, l'auto-envoi pose T (`components/chat/ChatInput.tsx:1062-1074`), puis la restauration, déclarée après, pose D (`components/chat/ChatInput.tsx:1188-1209`) ; l'envoi part 50 ms plus tard avec D | Le transport suit la règle de l'échec : file seulement si la cible n'a ni brouillon ni réponse en cours, sinon T rejoint le brouillon et rien ne part (V4-7) | § 7.3, lot 2 | design ; test au lot 2 |
| 11 (P2) | La question sur la décision 30 ne dit pas ce que chaque lecture retire ; la constante est baissée sans Ludo | **Accepté.** V3 § 7.4 et critère du lot 6 | Question reformulée avec la conséquence de chaque lecture, dont « B, flux longs comptés ensemble » ; la recette du lot 6 constate et rapporte, elle ne change rien | § 12, lots 4 et 6 | question à Ludo |
| 12 | `arreter(conversationId)` rappelle `cancelGeneration`, que B-1514 vient de retirer | **Accepté.** `components/chat/ChatInput.tsx:1077-1114` : arrêt par `annulerTraitement(generationId)` (`components/chat/ChatInput.tsx:1095`), repli seulement avant l'événement `generation` ; `routers/chat.py:1022` résout « la plus récente » | Le registre de l'écran garde l'identifiant de génération et arrête par lui ; test de B-1514 gardé vert | § 7.3, lot 2 | design ; B-1514 fermé (`ee3244f7`), non-régression au lot 2 |
| 13 | `ChatInput.cycle6` n'observe que l'espion `saveDraft` | **Accepté.** `components/chat/ChatInput.cycle6.test.tsx:18-20` | Le test lit le stockage (`therese-draft-<id>`, `hooks/useAutosave.ts:5-8`), sabotage prévu | lot 2 | design ; test réécrit au lot 2 |
| 14 | La recherche approfondie et le chemin `{{action}}` vident le champ sans effacer le brouillon | **Accepté, fermé pendant la rédaction** : B-1525 (`6b41942a`) ajoute l'effacement sur la recherche approfondie (`components/chat/ChatInput.tsx:947`), l'action (`components/chat/ChatInput.tsx:523`) et la commande de navigation (`components/chat/ChatInput.tsx:1126`) | Le lot 2 regroupe les cinq chemins dans une seule fonction | § 7.3, lot 2 | **fermé au code** (`6b41942a`, tests de `ChatInput.brouillonEtReponse.b1509`) |
| 15 | Contrat P-109 non réciproque ; sort d'`isStreaming` non écrit ; confirmation qui tait la réponse vocale | **Accepté.** `docs/plans/2026-09-26-rfc-p109-conversation-vocale-v3.md:116` (démarrage refusé sur `isStreaming`), `docs/plans/2026-09-26-rfc-p109-conversation-vocale-v3.md:352` (inscription au registre en phase 2) | `isStreaming` devient au lot 3 un miroir écrit par le seul registre, et plus aucun code applicatif ne le lit (V4-8) ; P-109 lit `uneReponseEstEnCours()` quel que soit l'ordre ; le compte annoncé vient du moteur, qui voit les générations vocales (V4-9) | § 6, § 7.4, § 7.9 | design ; tests aux lots 1a et 3 |
| 16 | La suppression ne ferme la course que dans un sens : message de l'utilisateur orphelin | **Accepté, fiché B-1527** (différé à cette V4). `routers/chat.py:3902-3917` (lecture, `delete`, `commit`), `routers/chat.py:1318-1319` (message de l'utilisateur hors du point d'écriture de B-1494) | Suppression et envoi se réservent la conversation, chacun par une vérification synchrone (V4-3) | § 7.1, lot 1a | design ; test en concurrence forcée au lot 1a |
| 17 | Le chemin non diffusé n'a aucun arrêt lié | **Accepté.** `routers/chat.py:1857` (boucle sans drapeau), `routers/chat.py:1896-1897` (écriture hors de `_ecrire_reponse`) | Lecture du modèle dans une tâche que l'arrêt annule ; écriture par `_ecrire_reponse` (V4-4) | § 7.1, lot 1a | design ; test au lot 1a |
| 18 | En échec, les pièces jointes ne restent pas « consignées sur le message » si le moteur ne l'a jamais écrit | **Accepté.** `routers/chat.py:1269` (404 avant écriture), `main.py:729-752` (503 de maintenance avant la route) ; `components/chat/ChatInput.tsx:876-880` (liste d'origine non vide : les envoyées sont jetées) | Fusion dans la liste d'origine, sans doublon de chemin (V4-6) | § 7.3, lot 2 | design ; test au lot 2 |
| 19 | Main a appliqué une partie de la V3 ; citations décalées ; « vide » non défini | **Accepté.** B-1508 à B-1510 ferment R-125-1 à R-125-3, B-1513 la moitié de R-125-5, B-1525 le constat 14 ; `components/chat/ChatInput.tsx:871` (B-1510 ne lit que le champ, juste sous le verrou seulement) | Citations recalées à `7baf1793` ; tests correspondants étiquetés « non-régression » avec sabotage ; « vide » défini (§ 7.3) | § 3, § 7.3 | design ; test « C tapé depuis 2 s » au lot 2 |
| 20 | Aucune V3 ne fixe la signature de la garde ni l'ordre de ses clauses | **Accepté.** 13 appelants (`components/prototype/ConversationCanvasPrototype.tsx:1196` à `components/prototype/ConversationCanvasPrototype.tsx:2066`) | Section commune (§ 6), citée par P-121 V4 ; un test par clause, indépendant du nombre d'appelants | § 6 | design ; tests au premier des lots 5 qui passe |
| 3 (P-121, partagé) | La clause vocale n'est nommée nulle part dans la réécriture | **Accepté** | § 6, clause 1 | § 6 | design |
| B-1520 | Travaux de fond qui écrivent après la purge ; tentative échouée | **Cause de l'échec isolée** (§ 3) : le harnais, pas l'application | Les travaux de fond entrent dans l'arrêt d'office (V4-2) | § 7.2, lot 1b | design ; test d'intégration au lot 1b |
| B-1511, B-1512 | Échec qui relance la file ; pièce jointe qui suit la bascule | Ouverts à `7baf1793` | Lots 4 et 2 | § 7.3, § 7.5 | design |

Aucun constat n'est réfuté. Le constat 14 est fermé au code pendant la rédaction.

## 1. Ce que la V4 garde de la V3

- Le besoin (Hugo, hugo-07), la recommandation (option A : le flux quitte le composeur pour un registre par conversation, verrou levé au lot 5 seulement) et les décisions V1-Q1 à V1-Q5 et Q-import.
- Le registre moteur des envois en mémoire (V3-1) : ni l'arrêt d'office ni le refus de suppression ne lisent la base, une ligne `running` orpheline ne retient donc rien (constat 10 de la revue V2).
- L'ordre « inscription, puis test de suspension, sans `await` entre les deux » (constat 11 de la revue V2), la restauration qui écrit le partiel dans l'ancienne base (V3-2), le message 503 qui dit le compte (B-1283).
- La règle des brouillons (V3-3) : un brouillon ne s'efface qu'au départ de son texte. Elle est désormais au code (B-1509, B-1525).
- V3-4 (un échec ne relance pas la file) et V3-5 (projet refusé pendant la réponse), les fins hors écran, « Travaux » sans garde de flux, les interdits, les tests à migrer du lot 3 et à inverser du lot 5.

## 2. Ce que la V4 retire, réintègre ou reporte, et pourquoi

- **Réintégré, et non plus reporté : l'arrêt d'office des autres travaux de fond** (Board, Atelier, trame, indexation, actions, synchronisation de dossier). La V3 le fichait (R-125-6) et le repoussait ; il est confirmé (B-1520), la cause de l'échec de la tentative est isolée, et le mécanisme tient dans `services/traitements.py`. Lot 1b.
- **Retiré : la fermeture de l'envoi dans le `finally` de l'enveloppeur `_flux_suivi`** (V3 § 7.1). Un générateur jamais démarré ne l'exécute pas (constat 8). Remplacé par `ReponseSuivie` (V4-1).
- **Retiré : `arreter(conversationId)` qui appelle `cancelGeneration`** (V3 § 7.2). B-1514 arrête par l'identifiant de génération (constat 12).
- **Retiré : `ChatInput.cycle6` comme protection de « aucun brouillon réécrit après Arrêter »** tant qu'il n'observe qu'un espion (constat 13).
- **Retiré : « un test énumère les treize appelants de la garde »** (V3 lot 5). Il dépendait du nombre d'appelants, que P-121 change (constat 20). Remplacé par un test par clause (§ 6).
- **Retiré : « la constante baisse d'un cran » au critère du lot 6** (constat 11). La recette mesure, Ludo décide.
- **Retiré : « sinon elles restent consignées sur le message en base »** (décision 32, V3 § 7.2), faux quand le moteur n'a rien écrit (constat 18).
- **Retiré : « l'engagement de P-109 » d'inscrire ses générations au registre de l'écran** (V3 § 7.8, point 4). P-109 V3 le range en phase 2 (`docs/plans/2026-09-26-rfc-p109-conversation-vocale-v3.md:352`). La V4 n'en a plus besoin : le compte vient du moteur (V4-9).
- **Retiré : les tests « rouges d'abord » de R-125-1 à R-125-3 et de la moitié de R-125-5**. Fermés au code ; leurs tests sont « non-régression » (§ 3).
- **Reporté, inchangé** : la reprise après rechargement (V1-Q5), la rédaction d'une section de l'Atelier documentaire coupée à la fermeture du document, la cloison d'une conversation qui a déjà des réponses et change de projet, la persistance d'un message en file.

## 3. Ce qui a changé sur `main` depuis la V3, et la cause de B-1520

**Fermés au code, étiquetés « non-régression » dans les lots :**

- B-1508 (`6a7e8388`) : `clearDraft` abandonne le minuteur (`hooks/useAutosave.ts:136-150`). Ferme R-125-3.
- B-1509 et B-1510 (`1fd6a079`) : le brouillon s'efface au départ du texte (`components/chat/ChatInput.tsx:553`, `components/chat/ChatInput.tsx:651`), plus à la fin du flux ; un échec ne réécrit le brouillon que si le champ est vide (`components/chat/ChatInput.tsx:871-875`). Ferment R-125-1 et R-125-2. Test `components/chat/ChatInput.brouillonEtReponse.b1509.test.tsx`.
- B-1513 (`d86575af`) : la synthèse de la recherche approfondie passe par `_ecrire_reponse` (`routers/chat.py:1205`). Ferme la moitié de R-125-5.
- B-1514 (`ee3244f7`) : « Arrêter » vise la génération par son identifiant, et la file attend l'arrêt (`components/chat/ChatInput.tsx:1062-1074`, `components/chat/ChatInput.tsx:1086-1099`). Test `components/chat/ChatInput.arretEtFile.b1514.test.tsx`.
- B-1525 (`6b41942a`) : même règle sur la recherche approfondie, l'action et la commande de navigation (constat 14).
- B-1521 et B-1530 : accord « documents » pour `/fichier`, y compris porté par une variable ; tests `components/chat/ChatInput.commandeFichier.b1521.test.tsx`, à garder verts.

**Ouverts à `7baf1793` et couverts ici** : B-1511 (lot 4), B-1512 (lot 2), B-1520 (lot 1b), B-1526 (lot 2), B-1527 (lot 1a).

**B-1520 : la cause de l'échec de la tentative est isolée.** La fiche dit : l'écrivain reste bloqué jusqu'au plafond pendant la purge, cause non isolée. Elle l'est : c'est le harnais. Le test de la tentative lançait l'écrivain par `asyncio.create_task` sur la boucle de pytest, puis appelait la purge par `client.delete(...)`, qui est l'appel **synchrone** du `TestClient` (`tests/conftest.py:128-129`) : il bloque la boucle de pytest pendant toute la purge, qui tourne sur la boucle du portail du `TestClient`. L'écrivain ne pouvait donc pas avancer tant que la purge l'attendait. Les tests de concurrence qui marchent lancent le travail concurrent sur la boucle de l'application (par un fil qui appelle le `TestClient`, `tests/test_b1260_purge_attend_les_creations_du_chat.py:37-44`). Expérience du 26/09, dans le scratchpad, sur la boucle de l'application (`client._tc.portal.start_task_soon`), écrivain « non interruptible » qui écrit 0,5 s après son démarrage :

- sans attente (à `e49a679a` puis à `04a8e8ee`, même résultat) : la purge répond 200 en 0,02 s, l'écrivain écrit après elle, sa ligne survit. **Le défaut se reproduit** ;
- avec la demande d'arrêt de chaque traitement vivant puis l'attente de sa sortie du registre (le mécanisme de la tentative) : la purge répond 200 en 0,53 à 0,54 s, l'écriture a lieu à 0,50 ou 0,51 s, avant la fin de l'attente (0,52 s), et la ligne est absente après.

Le principe de la tentative est donc sain. Le § 7.2 dit ce qu'il laissait passer (trois trous, lus au code), et le lot 1b prescrit le harnais.

## 4. Le besoin

Hugo travaille avec un modèle local : ses réponses prennent de 2 à 7 minutes. Pendant ce temps, « Nouvelle conversation », un changement de vue ou l'ouverture d'une autre conversation sont refusés. Il n'a que deux choix : attendre, ou jeter la réponse. Sa piste, acceptée : laisser la réponse se terminer en fond et la retrouver ensuite.

## 5. Décisions

| Nº | Décision | Origine | Ce qu'elle impose ici |
|---|---|---|---|
| 30 | Deux réponses de fond en même temps en ligne, file au-delà | Ludo par délégation, 25/09 | **Lecture réservée à Ludo** (§ 12). La conception ne dépend que d'une constante et d'une fonction de comptage |
| 31 | Purge et restauration arrêtent d'office les réponses en cours, et le disent | Ludo par délégation, 25/09 | Lots 1a (réponses) et 1b (autres travaux de fond, B-1520) |
| 32 | Les pièces jointes d'une réponse de fond qui échoue restent sur la conversation d'origine | Ludo par délégation, 25/09 | Store par conversation, fusion en échec (V4-5, V4-6) |
| V1-Q1 à V1-Q5, Q-import, V3-1 à V3-5 | Inchangées | V2, V3 | § 1 |
| V4-1 | Un envoi se ferme dans l'appel ASGI de sa réponse, après la fermeture explicite de son générateur | Tranché ici | Motif : constat 8 ; c'est le seul point par lequel passe toute réponse, démarrée ou non |
| V4-2 | Un traitement de fond entre dans l'arrêt d'office ; il sort de la table en mémoire à `terminer()`, jamais à la fin de sa tâche porteuse | Tranché ici | Motif : B-1520 ; la fin de la porteuse du Board précède sa persistance protégée (§ 7.2) |
| V4-3 | Suppression d'une conversation et envoi se la réservent l'un contre l'autre, par une vérification synchrone de chaque côté | Tranché ici | Motif : constat 16, B-1527 ; l'un des deux gagne toujours, sans lecture de base |
| V4-4 | Le chemin non diffusé lit le modèle dans une tâche que l'arrêt annule | Tranché ici | Motif : constat 17 ; un drapeau lu entre deux morceaux attendrait le morceau suivant, et un modèle local peut rester muet des minutes |
| V4-5 | Les pièces jointes vivent dans un store par conversation ; dédoublonnage et indexation par (conversation, chemin), hors du composant | Tranché ici | Motif : constat 9, B-1512 |
| V4-6 | En échec, les pièces jointes envoyées rejoignent la liste d'origine, fusionnées sans doublon de chemin | Tranché ici (délégation : aucun effacement) | Motif : constat 18 ; ne rien jeter, ne rien dédoubler |
| V4-7 | Le transport depuis l'accueil n'entre en file que si la cible n'a ni brouillon ni réponse en cours ; sinon il s'ajoute au brouillon et rien ne part sans geste | Tranché ici | Motif : constat 10, B-1526 |
| V4-8 | Au lot 3, `isStreaming` reste dans le store du chat comme miroir écrit par le seul registre (vrai si une réponse court quelque part) ; chaque lecteur applicatif passe à `reponseEnCours(conversationId)` ou à `uneReponseEstEnCours()`, et une garde de source interdit ensuite de lire le miroir | Tranché ici | Motif : constat 15. Une cinquantaine de fichiers de test posent `isStreaming: false` pour remettre le store à zéro : retirer le champ les ferait tous réécrire sans rien protéger. Le seul risque réel est un lecteur qui voudrait dire « la conversation affichée » et lirait « quelque part » ; la garde de source l'attrape, `tsc` ne le ferait pas mieux |
| V4-9 | Le compte annoncé avant une purge ou une restauration vient du moteur | Tranché ici | Motif : constat 15 ; le moteur voit toutes les générations, vocales comprises, et les autres travaux de fond |
| V4-10 | La garde de navigation commune, sa signature et l'ordre de ses clauses (§ 6) | Tranché ici | Motif : constats 3 et 20 |

## 6. Section commune : la garde de navigation (P-109, P-121, P-125)

Trois lots réécrivent la même fonction : le lot 5 de P-121 (les sorties du devis consultent des surfaces), le lot 5 de P-125 (le flux ne retient plus la navigation) et le lot 5 de P-109 (la session vocale la retient). Cette section fixe la forme commune ; P-121 V4 la cite, et P-109 V3 y trouve sa clause.

**Où.** `lib/gardeDeNavigation.ts`, nouveau module. La coque garde son nom local, réduit à une délégation : `const blockStreamingNavigation = useCallback((sortie?: Sortie) => sortieRefusee(sortie), [])`. Ses treize appelants (`components/prototype/ConversationCanvasPrototype.tsx:1196`, `:1218`, `:1226`, `:1398`, `:1413`, `:1615`, `:1653`, `:1679`, `:1732`, `:1858`, `:1866`, `:1878`, `:2066`) gardent leur forme ; ceux de la table des sorties de P-121 passent leurs surfaces. Le premier des trois lots qui passe crée le module avec les quatre clauses dans l'ordre ci-dessous, une clause encore sans objet valant `false` ; les suivants remplacent le corps de leur prédicat, jamais l'ordre ni la signature.

**Signature.**

```ts
export type Surface = 'vue' | 'panneau';
export interface Sortie {
  /** Ce que la sortie démonte. Défaut ['vue'], le seul cas qui existe avant P-121. */
  surfaces?: readonly Surface[];
  /** Geste interdit pendant la réponse de la conversation affichée (P-125, lot 5). */
  geste?: 'vider';
}
/** La garde complète : vrai si la sortie est refusée (un bandeau ou une question a été posé). */
export function sortieRefusee(sortie?: Sortie): boolean;
/** Clauses 1 et 2 seulement, sans effet : le verrou de navigation. */
export function navigationVerrouillee(): boolean;
/** La même, réactive, pour le tiroir. */
export function useNavigationVerrouillee(): boolean;
```

**Ordre des clauses.** La première qui refuse arrête l'évaluation.

1. **Vocale** : `sessionVocaleBloqueLaNavigation()` (P-109, `docs/plans/2026-09-26-rfc-p109-conversation-vocale-v3.md:120`) ; bandeau « Conversation vocale en cours » et « Arrêter la conversation vocale ». Avant P-109 : `false`.
2. **Flux** : `fluxRetientLaNavigation()`. Jusqu'au lot 5 de P-125 : une réponse court quelque part (`useChatStore.getState().isStreaming` aujourd'hui, `uneReponseEstEnCours()` dès le lot 3). Après le lot 5 : une conversation éphémère a une réponse en cours (V1-Q4). Bandeau « Réponse en cours » et « Arrêter la réponse » (B-1369).
3. **Interdits** : `interditPendantLaReponse(sortie.geste)`. `vider` pendant la réponse de la conversation affichée est refusé, avec « Arrêter la réponse ». Avant le lot 5 de P-125, la clause 2 couvre déjà ce cas ; supprimer et changer le projet ne sont pas des sorties de navigation et gardent leurs propres refus (§ 7.8).
4. **Saisie** : `sortieRetenueParUneSaisie(sortie.surfaces ?? ['vue'])` (P-121) ; le formulaire modifié le plus récent parmi ces surfaces pose sa question, et un seul (B-994).

**Pourquoi cet ordre.** Le brief énumérait « vocale, flux, saisie, interdits » ; la V4 place les interdits avant la saisie. Seule la clause 4 a un effet au-delà d'un bandeau : elle pose une question qui peut mener à abandonner la saisie. Poser cette question pour un geste que la clause suivante refuserait ferait abandonner une saisie pour rien. Toutes les clauses qui refusent sans rien toucher passent donc avant la seule qui interroge. La clause vocale passe en tête, comme P-109 V3 l'exige.

**Qui suit quoi.**
- Les treize appelants de la coque : `sortieRefusee(sortie)`, avec les surfaces de la table de P-121 V4 (§ 6.4) et `{ geste: 'vider' }` à `components/prototype/ConversationCanvasPrototype.tsx:1878` (lot 5 de P-125).
- `runNavigationAction` (`lib/clientActions.ts:33`) : `navigationVerrouillee()`. La saisie est consultée par la coque quand elle exécute l'action revendiquée.
- Le tiroir : `navigationLocked={useNavigationVerrouillee()}` (aujourd'hui `isStreaming`, `components/prototype/ConversationCanvasPrototype.tsx:2051`), puis sa consultation de la saisie avant toute mutation (B-991, `components/prototype/PrototypeConversationDrawer.tsx:258-271`), avec les surfaces qu'`openChat` démontera (P-121 V4). Même ordre : verrou, puis saisie.
- `TasksPanel`, `CalendarPanel`, `lib/actionRegistry.ts:117` et le retour B-994 de l'effet de navigation (`components/prototype/ConversationCanvasPrototype.tsx:1293`) appellent `sortieRetenueParUneSaisie()` directement, avec la valeur par défaut : inchangés.

**Tests** (`lib/gardeDeNavigation.test.ts`), un par clause ; chaque sabotage vise le seul prédicat de sa clause et ne rougit que son test :
- `clause vocale : session active, sortie refusée, flux et saisie jamais consultés` (espions) ;
- `clause flux : réponse en cours, refus avec « Arrêter la réponse », aucune question posée` (une garde de saisie modifiée est inscrite ; son `demander` n'est jamais appelé) ;
- `clause interdits : vider pendant la réponse de la conversation affichée est refusé ; naviguer ne l'est pas` (à partir du lot 5 de P-125) ;
- `clause saisie : ['vue'] ignore une garde 'panneau' ; ['vue', 'panneau'] pose la question de la plus récente, une seule` ;
- `ordre : session vocale et réponse en cours ensemble, un seul bandeau, celui de la voix` ;
- `navigationVerrouillee ne consulte jamais la saisie`.

Au niveau de la coque, le fil reste le test de P-109 « `openChat` refusé pendant une session » (`docs/plans/2026-09-26-rfc-p109-conversation-vocale-v3.md:326`), et `components/prototype/ConversationCanvasPrototype.parite.test.tsx` vérifie que chaque appelant passe par la délégation.

## 7. Conception

### 7.1 Moteur, lot 1a : le registre des envois

**Le registre** (`services/envois_en_cours.py`, V3-1). Un `Envoi` porte : sa conversation (celle de la requête dès l'entrée, ou celle que la route crée), un drapeau `arret_demande`, la fonction d'arrêt liée, un booléen `arret_invoque` et un événement `fini`.

- `ouvrir_envoi(conversation_id: str | None) -> Envoi` : **synchrone**, première instruction de `send_message` (`routers/chat.py:1251`) et de `deep_research_endpoint` (`routers/chat.py:1053`). Elle lève `OperationSurLesDonneesEnCours` si les créations sont suspendues (le compteur de `services/memory_tools.py:1283-1310`, exposé par une fonction `creations_suspendues()`), et `ConversationEnSuppression` si la conversation est réservée par une suppression (V4-3) ; sinon elle inscrit l'envoi. La vérification et l'inscription sont dans la même fonction synchrone : en asyncio, rien ne s'intercale. Les routes traduisent en 409 : « Une opération sur tes données est en cours (effacement ou restauration) : rien n'a été envoyé. » et « Cette conversation est en cours de suppression : rien n'a été envoyé. »
- `envoi.poser_conversation(id)` : quand la route crée la conversation (`routers/chat.py:1271-1273`, `routers/chat.py:1077-1079`).
- `envoi.lier_arret(fonction)` : si l'arrêt est déjà demandé, la fonction est appelée aussitôt. Chat : `contexte_execution.demander_arret`, juste après `_register_generation` (`routers/chat.py:1944`), avant `creer_traitement`. Recherche : le drapeau `arret_demande` (`routers/chat.py:1102`). Chemin non diffusé : l'annulation de la tâche de lecture (V4-4).
- `fermer(envoi)` : pose `fini`, retire l'envoi. Appelée par `ReponseSuivie` pour une réponse en flux, sinon par le `finally` de la route (réponse JSON, 404, 409, exception) ; un drapeau `transmis` évite la double fermeture.
- `arreter_et_attendre() -> int` : jusqu'à ce que la table soit vide, demande l'arrêt de chaque envoi et attend tous les `fini` ; rend le nombre d'envois dont l'arrêt a été réellement invoqué (une commande déterministe qui finit seule n'est pas comptée).

**`ReponseSuivie` (V4-1, constat 8)**, dans `services/envois_en_cours.py` :

```python
class ReponseSuivie(StreamingResponse):
    """Réponse en flux dont la fin est garantie, que son générateur ait démarré ou non."""

    def __init__(self, flux, *, envoi=None, clore_si_jamais_demarre=None, **kw):
        self._flux = flux
        self._demarre = False
        self._envoi = envoi                        # lot 1a : /send, /deep-research
        self._clore = clore_si_jamais_demarre      # lot 1b : un traitement créé dans la route (Board)
        super().__init__(self._suivre(), **kw)

    async def _suivre(self):
        self._demarre = True                       # le flux démarre dans le même pas, rien ne s'intercale
        async for morceau in self._flux:
            yield morceau

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            try:
                with anyio.move_on_after(DELAI_DE_FERMETURE_S, shield=True):  # 6 s, au-delà de la borne de 5 s
                    await self._flux.aclose()
                    await self.body_iterator.aclose()
                    if not self._demarre and self._clore is not None:
                        await self._clore()
            finally:
                if self._envoi is not None:
                    fermer(self._envoi)            # synchrone, toujours atteint, après aclose() quand il aboutit
```

Quand `super().__call__` rend la main, la tâche qui lisait le flux est finie (le groupe de tâches l'attend). Trois cas : flux jamais démarré, `aclose()` le ferme sans exécuter son corps ; flux suspendu à un `yield` (annulation reçue pendant `send`), `aclose()` y lève `GeneratorExit` et son nettoyage s'exécute maintenant, au lieu d'attendre le ramasse-miettes ; flux fini, rien. **Tout ce qui attend est protégé** : sous Starlette, l'annulation de la déconnexion est relivrée à chaque `await` de la portée annulée (B-1461), un `await` hors du bloc protégé serait coupé. **La fermeture de l'envoi est synchrone et dans un `finally`** : aucun point d'attente ne peut l'empêcher, et elle suit `aclose()` quand celui-ci aboutit, ce qui tient l'invariant : **après `fermer`, plus aucune écriture de cet envoi**. Si `aclose()` dépasse 6 s (le nettoyage du producteur est lui-même borné à 5 s, `routers/chat.py:2113`), l'envoi est fermé quand même : c'est le résiduel de la borne (§ 10). Le drapeau `_demarre` remplace `inspect.getasyncgenstate`, absent de Python 3.11, que le projet supporte encore (`requires-python`, `pyproject.toml:6`). Les cinq réponses en flux de `send_message` (`routers/chat.py:1439`, `routers/chat.py:1508`, `routers/chat.py:1604`, `routers/chat.py:1672`, `routers/chat.py:1690`) et celle de la recherche (`routers/chat.py:1236`) deviennent des `ReponseSuivie`.

**Arrêt d'office (décision 31).** `_attendre()` (`routers/data.py:616-619`) commence par `bilan = await arreter_les_ecritures_de_fond()`, qui appelle `arreter_et_attendre()` (lot 1a), puis l'arrêt des traitements (lot 1b), et recommence tant que l'une des deux tables n'est pas vide. La purge (`routers/data.py:588`) et la restauration (`routers/data.py:1694`, avant `close_db` à `routers/data.py:1698` et l'archive de sécurité à `routers/data.py:1709`) en héritent. La réponse porte `ecritures_arretees` ; au plafond (`routers/data.py:595`, `routers/data.py:622-628`), le 503 dit le compte : « 1 réponse en cours a été arrêtée ; l'effacement n'a pas eu lieu. Réessaie dans un instant. » Sans rien d'arrêté, le message actuel (`routers/data.py:596-599`) reste juste.

**Chemin non diffusé (V4-4, constat 17).** La lecture du modèle (`routers/chat.py:1857-1858`) passe dans une tâche ; `envoi.lier_arret(tache.cancel)`. Annulée, la route écrit le partiel s'il y en a un, puis rend la réponse. L'écriture finale (`routers/chat.py:1896-1897`) et celle du partiel passent par `_ecrire_reponse` (`routers/chat.py:2163-2182`) : c'est la moitié de R-125-5 que B-1513 laissait.

**Suppression (V4-3, constat 16, B-1527).** `delete_conversation` (`routers/chat.py:3902-3926`) commence, avant tout `await`, par `reserver_suppression(conversation_id)` : synchrone, elle lève `ReponseEnCours` si un envoi porte cette conversation (409 : « Une réponse est en cours dans cette conversation : arrête-la avant de la supprimer. »), sinon elle réserve la conversation jusqu'à la fin de la route (`finally`). `ouvrir_envoi` refuse une conversation réservée. Chaque côté vérifie et s'inscrit sans `await` : l'un des deux gagne toujours. Le message de l'utilisateur (`routers/chat.py:1318-1319`) n'a donc plus de fenêtre où une suppression le devance.

**Restauration (V3-2, inchangée).** Le mode maintenance refuse déjà les nouvelles requêtes (`main.py:729-752`) ; les envois admis avant sont arrêtés et leurs partiels écrits dans l'ancienne base avant `close_db`, donc dans l'archive de sécurité ; la base restaurée ne les contient pas.

**Le compte annoncé (V4-9).** `GET /api/data/ecritures-en-cours` rend `{ reponses, travaux }` à partir des deux tables. La confirmation de « Effacer toutes mes données » et celle d'une restauration (`components/settings/PrivacyTab.tsx:163-171`, `components/settings/PrivacyTab.tsx:182-199`) l'appellent à l'ouverture et annoncent « 1 réponse en cours sera arrêtée » (lot 1b : « et 1 délibération du Board ») ; le message qui suit la route reprend `ecritures_arretees`, même si la fenêtre se recharge aussitôt (`components/settings/PrivacyTab.tsx:197`). Une génération vocale passe par `/send` : elle est comptée sans rien demander à P-109.

Aucune colonne ne change ; la tête Alembic est celle de `main` à la base (`c9d0e1f2a3b4`, arrivée avec P-132), et ce chantier n'en ajoute pas.

### 7.2 Moteur, lot 1b : les autres travaux de fond (B-1520)

**Ce que la tentative laissait passer**, lu au code. Son principe (demander l'arrêt, puis attendre la sortie du registre) est sain sur une seule boucle (§ 3), mais le registre qu'elle attendait, `services/task_registry.py`, a trois trous :

- **un traitement pas encore lié n'y figure pas.** Le Board crée sa ligne dans le corps de la route (`routers/board.py:199-205`) et ne lie son adaptateur que dans le générateur (`routers/board.py:255-259`) ; une purge qui passe entre les deux ne l'attend pas ;
- **il en sort trop tôt.** `inscrire` retire l'entrée quand la tâche porteuse finit (`services/task_registry.py:141-143`). Or la décision du Board est écrite par une persistance lancée sous `shield` (`services/board.py:816-820`) : la porteuse annulée finit, l'entrée sort, et la persistance peut encore commiter. La route l'attend avant de trancher (`routers/board.py:287-294`), mais le registre est déjà vide ;
- **rien ne refuse un traitement créé pendant l'attente.**

**Le mécanisme (V4-2).** `services/traitements.py` gagne une table en mémoire `_en_cours: dict[str, TraitementHandle]`.

- `creer_traitement` (`services/traitements.py:168`) commence, sans `await`, par lever `OperationSurLesDonneesEnCours` si les créations sont suspendues, puis inscrit le traitement dans `_en_cours`, puis écrit sa ligne. Si l'écriture échoue, l'entrée est retirée et l'exception remonte comme aujourd'hui.
- `terminer()` (`services/traitements.py:145-166`) retire l'entrée et pose l'événement `termine` dans son `finally`, après l'écriture protégée de l'état terminal. La sortie est le dernier mot du producteur (« SEUL le producteur pose l'état terminal, après son nettoyage réel ») : pour le Board, après l'attente de la persistance.
- `arreter_les_traitements_et_attendre() -> dict[str, int]` : demande l'arrêt de chaque traitement de la table (`demander_arret`, `services/traitements.py:200`, qui rejoue la demande à la liaison si l'adaptateur n'est pas encore lié, `services/traitements.py:88-101`), attend les `termine`, recommence jusqu'à table vide ; rend le compte par type.
- **Les six sites de création** laissent passer le refus au lieu de l'avaler dans leur repli « suivi indisponible » : Board (`routers/board.py:199-205`), Atelier (`routers/agents.py:291`), trame (`routers/documents.py:775`), indexation (`routers/files.py:88`), actions (`services/action_agents.py:638`), synchronisation de dossier (`services/project_sync_service.py:415`). Chacun rend 409 avec la phrase commune, ou, pour un service sans route propre, remonte le refus à la route qui l'appelle.
- **Le Board** rend une `ReponseSuivie(..., clore_si_jamais_demarre=...)` : **seulement si son flux n'a jamais démarré** (drapeau `_demarre`, § 7.1), elle termine le traitement en `cancelled` (« interrompu avant de commencer ») ; un client parti avant le premier octet ne laisse plus une ligne `queued` (R-125-10), ni une entrée dans `_en_cours`. S'il a démarré, rien : son propre nettoyage, ou la clôture détachée qu'il lance à la déconnexion (`routers/board.py:330-349`), pose l'état terminal après la persistance, et c'est ce `terminer()` que la purge attend.
- **Le chat** : son traitement, créé par le générateur après la liaison de l'arrêt de l'envoi, peut être refusé pendant une purge ; le repli existant (`routers/chat.py:1973`, `routers/chat.py:1979`) produit alors sans suivi, mais le drapeau est déjà posé et la génération rend `cancelled` avant de produire.

**Résiduel nommé.** Un travail dont la ligne n'a pas pu être écrite (base occupée plus de 5 s à sa création, hors purge) tourne sans entrée, comme aujourd'hui : le suivi reste un témoin (commentaire de `routers/files.py`, « le suivi est un TÉMOIN, jamais un acteur »). Fenêtre étroite, hors de ce lot.

### 7.3 Écran, lot 2 : registre, brouillons, pièces jointes, transport (verrou inchangé)

**Le registre de l'écran** (`lib/reponsesEnCours.ts`, petit store Zustand), repris de la V3 avec l'arrêt de B-1514 (constat 12) : une entrée par conversation, clé renommée à l'adoption d'identité (`stores/chatStore.ts:444-452`) ; l'entrée garde l'identifiant reçu par l'événement `generation` ; `arreter(conversationId)` coupe la lecture, puis appelle `annulerTraitement(id)` si l'identifiant est connu, `cancelGeneration(conversationId)` seulement avant l'événement ; la promesse d'annulation en vol vit dans l'entrée, et la file de cette conversation l'attend (la règle de `components/chat/ChatInput.tsx:1067-1072`). `lib/arretDeLaReponse.ts` en devient la façade. Le module exporte aussi `uneReponseEstEnCours()` ; si P-109 passe avant ce lot, la façade existe déjà (§ 7.9) et ce lot change son corps.

**Les brouillons.** La règle est au code (B-1509, B-1525) ; le lot la rend structurelle et la complète en échec.

1. **Le texte quitte le champ.** Les cinq chemins (envoi `components/chat/ChatInput.tsx:648-651`, file `components/chat/ChatInput.tsx:550-553`, action `components/chat/ChatInput.tsx:522-523`, recherche approfondie `components/chat/ChatInput.tsx:946-947`, commande de navigation `components/chat/ChatInput.tsx:1125-1126`) appellent une seule fonction, `leTexteQuitteLeChamp()`, qui vide le champ et appelle `clearDraft` (minuteur abandonné, `hooks/useAutosave.ts:142`). Un sixième chemin qui l'oublierait est attrapé par un test qui parcourt les chemins.
2. **Fin réussie** : aucun geste sur les brouillons.
3. **Échec** : `rendreAuBrouillonSiVide(conversationId, texte)` (`lib/brouillons.ts`, clé explicite) remplace le code de B-1510 (`components/chat/ChatInput.tsx:871-875`), juste sous le verrou seulement. **Vide** se définit ainsi (constat 19) : pour la conversation affichée, le champ fait foi (le stockage peut avoir 5 s de retard sur lui, un texte tapé depuis moins de 5 s n'existe qu'au champ) ; pour une autre conversation, le stockage fait foi (la bascule a écrit sous la clé quittée le texte en attente, `hooks/useAutosave.ts:167-178`). Vide : A est écrit sous la clé d'origine et, si elle est affichée, dans le champ. Sinon A n'est pas réécrit : il reste dans le fil, en bulle, et en base.

**Les pièces jointes (V4-5, V4-6, B-1512).** `stores/piecesJointesStore.ts` : `parConversation[conversationId]`, renommé à l'adoption, vidé à la suppression d'une conversation et par la purge locale. Dédoublonnage par (conversation, chemin) : joindre dans Veille le document déjà joint dans Orion l'ajoute à Veille. Les contrôleurs d'indexation sont tenus par le store, clé (conversation, chemin) ; le démontage du composeur n'annule rien : fermer le chat pendant une indexation la laisse aller à son terme, et la pièce jointe est prête au retour. Le retrait d'une pièce jointe, la suppression de sa conversation ou la purge annulent son indexation (BUG-155 inchangé). L'indexation garde la conversation relevée à l'ajout, et son état `synced` est lu sur cette conversation-là, pas sur l'affichée (BUG-165). En échec d'envoi, les pièces jointes envoyées rejoignent la liste d'origine, fusionnées sans doublon de chemin, au lieu d'être jetées quand elle n'est pas vide (`components/chat/ChatInput.tsx:876-880`). Limite du moteur, inchangée et dite : un fichier indexé est unique par chemin (`FileMetadata.path`, `models/entities.py:225`) ; le joindre dans deux conversations le range sous le périmètre de la dernière. À relever au code au lot 2 ; s'il en résulte une perte d'accès pour la première, c'est une fiche à part.

**Le transport de l'accueil (V4-7, B-1526).** `submitComposer` (`components/prototype/ConversationCanvasPrototype.tsx:1799-1804`) : la conversation cible est celle qu'`openChat` affichera. Si son brouillon stocké est vide et qu'aucune réponse n'y court, T entre dans la file (B-626 inchangé) ; au montage, la restauration n'a rien à poser. Sinon, T est ajouté au brouillon de la cible, séparé d'une ligne vide, et écrit sous sa clé avant `openChat` ; rien ne part ; un statut dit « Ton message a été ajouté au brouillon de cette conversation : relis-le avant de l'envoyer. »

### 7.4 Écran, lot 3 : des états par conversation, et le sort d'`isStreaming`

Repris de la V3 : l'indicateur, le repère local, le suivi du bas du fil, « Arrêter » et les suggestions lisent `reponseEnCours(conversationId)` ; l'activité globale suit la conversation affichée. **`isStreaming` devient un miroir** (V4-8, champ `stores/chatStore.ts:82`, action `stores/chatStore.ts:344`) : le registre l'écrit (vrai si une réponse court quelque part), le composeur n'appelle plus `setStreaming`. Les lecteurs applicatifs du store du chat (`components/chat/ChatInput.tsx:172`, `components/chat/MessageList.tsx:54`, `components/chat/MessageList.tsx:92`, `components/prototype/ConversationCanvasPrototype.tsx:1046`, `lib/clientActions.ts:33`) choisissent chacun explicitement `reponseEnCours(conversationId)` (ce qui s'affiche) ou `uneReponseEstEnCours()` (une réponse court-elle quelque part : la clause 2 de la garde jusqu'au lot 5, l'étape 1 de P-109). Garde de source `lib/miroirIsStreaming.test.ts` : aucun fichier applicatif ne lit `isStreaming` du store du chat (sabotage : une lecture ajoutée dans `components/chat/MessageList.tsx`). Les tests qui simulent un flux en posant `isStreaming: true` ou `setStreaming(true)` (cinq fichiers à `7baf1793` : `components/chat/MessageList.c9.test.tsx`, `components/prototype/ConversationCanvasPrototype.parite.test.tsx`, `lib/arretDeLaReponse.test.ts`, `lib/clientActions.test.ts`, `stores/chatStore.test.ts`) passent par le registre, intention conservée ; ceux qui posent `isStreaming: false` pour remettre le store à zéro ne changent pas. Ceux que la V3 nommait (`components/chat/ChatInput.annulation.test.tsx`, `components/chat/MessageList.c9.test.tsx`, `components/chat/MessageList.attenteLocale.c10.test.tsx`, `components/chat/ChatInput.ollamaCloudLocal.b1174.test.tsx`) sont sabotés après migration pour vérifier qu'ils rougissent encore.

### 7.5 Écran, lot 4 : files, plafond, fins hors écran (B-1511)

- `filesDAttente[conversationId]` : une place par conversation, texte **et** pièces jointes.
- Un envoi part tout de suite si sa conversation n'a pas de réponse en cours, si `compterLesFluxQuiComptent() < PLAFOND_REPONSES_EN_LIGNE`, et, pour un envoi local, si aucun flux local n'est ouvert (V1-Q1). La constante et la fonction de comptage sont le seul endroit où vit la lecture de la décision 30 (§ 12). Sinon, file, avec la mention qui dit la vraie raison.
- **B-1511 (V3-4)** : un échec ne relance pas la file. Le message en file reste affiché avec « Retirer » (`components/chat/ChatInput.tsx:1429-1445`) et un nouveau bouton « Envoyer maintenant » ; sans lui, le champ désactivé tant qu'un message attend (`components/chat/ChatInput.tsx:207`) le bloquerait, motif du report inscrit dans la fiche.
- L'auto-envoi ne part que dans la conversation affichée, après le succès de sa propre réponse, plafond libre.
- Quitter une conversation dont un message attend : il passe par `rendreAuBrouillonSiVide` ; si le brouillon n'est pas vide (ce qui ne devrait pas arriver, le champ étant désactivé), il y est ajouté, jamais écrasé. Ses pièces jointes rejoignent la liste de la conversation. « Ton message attend dans Orion : il est gardé en brouillon. »

### 7.6 La fin d'une réponse qu'on ne regarde plus (lot 4)

Repris de la V3 : notification « Réponse prête » ; navigation reçue jamais exécutée hors de sa conversation, proposée par la notification ; carte d'action sensible « Depuis Orion » ; l'échec suit le § 7.3.

### 7.7 Suivre et revenir (lot 6)

Repris de la V3 : « Travaux » ouvre sa conversation sans garde de flux, en la chargeant par l'API si elle manque au store ; pastille « Réponse en arrière-plan · Orion » ; repère du tiroir.

### 7.8 Ce qui reste interdit

1. Deux réponses dans la même conversation : le second message reste en file.
2. Supprimer, vider ou changer le projet d'une conversation dont la réponse court : refusé avec « Arrêter la réponse ». Supprimer : par le tiroir et par le moteur (§ 7.1). Vider : clause 3 de la garde. Projet : le sélecteur (`components/chat/ConversationProjectPicker.tsx:161`) est désactivé tant que sa conversation a une réponse, parce que les outils de mémoire relisent le périmètre en cours de réponse (V3-5).
3. Exécuter en fond une navigation ou une action sensible sans clic.
4. Une conversation éphémère garde le verrou (clause 2 après le lot 5).
5. Recharger ou fermer THÉRÈSE arrête les réponses (B-1461, B-1462, P-142).
6. Effacer ou restaurer arrête d'office réponses et travaux de fond, et le dit avant et après (§ 7.1).
7. Une session vocale garde son verrou (clause 1).

### 7.9 Contrat avec P-109, réciproque

1. **Clause vocale** : clause 1 de la garde commune (§ 6), quel que soit l'ordre des lots.
2. **Tiroir et `runNavigationAction`** : `navigationVerrouillee()` (clauses 1 et 2) ; le verrou vocal ne tombe pas avec le verrou du chat.
3. **Exigence envers P-109, quel que soit l'ordre** : le démarrage d'une session lit `uneReponseEstEnCours()`, jamais `isStreaming` (P-109 V3 l'écrit sur `isStreaming`, `docs/plans/2026-09-26-rfc-p109-conversation-vocale-v3.md:116`, `docs/plans/2026-09-26-rfc-p109-conversation-vocale-v3.md:320`). Si P-109 passe avant le lot 2 d'ici, il crée la façade `lib/reponsesEnCours.ts` avec un corps d'une ligne (`return useChatStore.getState().isStreaming`) ; le lot 2 en change le corps. Si P-109 lisait encore `isStreaming`, la garde de source du lot 3 le rougirait, qu'il soit fusionné avant ou après.
4. **Purge et restauration** : les générations vocales passent par `/send`, le registre des envois les arrête et les compte (§ 7.1). L'inscription de la session au registre de l'écran reste la phase 2 de P-109, non planifiée ; ce contrat n'en dépend plus.
5. **Ce que P-109 attend du lot 1a** : que le message de l'utilisateur ne survive ni à une purge (suspension, arrêt, attente) ni à une suppression (V4-3), et que la génération s'arrête d'office. Tenu.
6. **Plafond** : une session ne démarre que si aucune réponse ne court et verrouille la navigation ; elle ne coexiste avec aucune réponse de fond, le plafond n'a pas à la compter.

### 7.10 Hors périmètre, nommé

La reprise après rechargement (V1-Q5) ; la rédaction d'une section de l'Atelier documentaire, coupée à la fermeture du document (`stores/documentStore.ts:257`) ; la cloison d'une conversation qui a déjà des réponses et change de projet ; la persistance d'un message en file ; un travail de fond dont la ligne de suivi n'a pas pu être écrite (§ 7.2).

## 8. Livraison en lots TDD

Chaque lot : tests écrits d'abord et vus rouges pour la bonne raison, sauf les caractérisations et les non-régressions (celles-ci sabotées pour prouver qu'elles mordent) ; un commit par lot ; sabotage ciblé par fonction, jamais par chaîne globale (règle du 27/08) ; les six portes du dépôt ; revue de conception au début du lot, revue adverse du diff à la fin ; recette navigateur sur la pile jetable (17393 et 1420, jamais 17293) quand le lot touche l'affichage. Le verrou reste en place jusqu'au lot 5. **Règle de harnais pour tout test de concurrence moteur** : le travail concurrent tourne sur la boucle de l'application (`client._tc.portal.start_task_soon`, ou un fil qui appelle le `TestClient`, comme `tests/test_b1260_purge_attend_les_creations_du_chat.py:37-44`), jamais sur la boucle de pytest, que l'appel synchrone du `TestClient` bloque (§ 3).

**Lot 0. Caractérisation et harnais (aucun code applicatif).**
- `tests/concurrence.py` (aide de test) : `lancer_sur_la_boucle_de_l_app(client, coro)`, `appel_asgi(client, methode, chemin, corps, deconnexion_immediate=True)` (portée `spec_version` 2.3, `receive` qui rend le corps puis `http.disconnect`, appel de l'`app` réelle, middlewares compris), `premier_delete(engine)` (espion `before_cursor_execute` qui date la première instruction `DELETE`).
- `tests/test_p125_lot0_deux_flux.py`, verts attendus : `test_deux_conversations_en_flux_ecrivent_chacune_une_fois`, `test_annuler_une_conversation_n_arrete_pas_l_autre` (`/cancel/{conversation_id}`), `test_relue_pendant_son_flux_la_reponse_n_apparait_qu_a_la_fin`, `test_banc_sqlite_deux_fins_et_une_ecriture_sans_verrou` (vraie base en fichier ; WAL et `busy_timeout`, `models/database.py:1050-1051`).
- `tests/test_p125_lot0_harnais.py` : `test_b1520_aucune_ecriture_apres_la_purge_sur_la_boucle_de_l_app` (l'expérience du § 3, écrivain lancé sur la boucle de l'application). Il affirme le comportement voulu, ligne absente après la purge ; il est donc rouge à HEAD, pour la bonne raison (la ligne survit), et `xfail(strict=True)` le garde rouge sans casser la suite jusqu'au lot 1b, qui retire le marqueur.
Critère observable : `pytest` et `vitest` verts, aucun fichier applicatif touché.

**Lot 1a. Registre des envois (livrable seul).**
Rouges d'abord, `tests/test_p125_lot1a_registre_des_envois.py`, fournisseur factice lent :
- `test_purge_pendant_un_flux_de_chat` : aucune ligne `messages` après, `ecritures_arretees.reponses == 1` ;
- `test_purge_pendant_une_recherche_approfondie` : même attendu ;
- `test_envoi_retenu_entre_suspension_et_ecriture` : envoi retenu par un point d'arrêt injecté juste après `ouvrir_envoi` ; après la purge, aucune ligne `messages`, `conversations` ni `processing_tasks` ;
- `test_send_et_deep_research_refuses_pendant_la_purge` : 409, phrase commune, rien écrit ;
- `test_toutes_les_sorties_de_send_ferment_l_envoi` (paramétré : commande déterministe, action en ligne, réponse du modèle, 404, erreur avant le flux, chemin non diffusé) : table vide à la fin ;
- `test_client_parti_avant_le_premier_octet` (par `appel_asgi`, `/send` puis `/deep-research`) : table vide ; purge 200 en moins de 2 s ; suppression de la conversation 200 (constat 8) ;
- `test_client_parti_pendant_la_reponse_le_nettoyage_precede_la_fermeture` (annulation reçue pendant `send`, flux suspendu à un `yield`) : le partiel est écrit, puis l'envoi est fermé (ordre relevé par espion) ;
- `test_fermeture_atteinte_meme_si_le_nettoyage_depasse_le_delai` (flux dont le nettoyage attend 10 s, délai réduit par le test) : l'envoi est fermé ; sabotage : sortir `fermer` du `finally`, rouge ;
- `test_ligne_running_orpheline_ne_retient_rien` : purge et suppression passent ;
- `test_suivi_en_panne_le_partiel_precede_l_effacement` (`creer_traitement` qui lève) : écriture du partiel datée avant `premier_delete` ;
- `test_plafond_depasse_503_dit_le_compte` (plafond réduit, fournisseur qui ignore l'arrêt) : 503, détail avec le compte, aucune table vidée ;
- `test_restauration_le_partiel_va_dans_l_archive` : partiel écrit avant `close_db` (ordre relevé par espion), présent dans l'archive de sécurité, absent de la base restaurée ;
- `test_chemin_non_diffuse_arrete_par_la_purge` (fournisseur muet 30 s) : purge 200 en moins de 2 s, compte 1 (constat 17) ;
- `test_chemin_non_diffuse_n_ecrit_rien_dans_une_conversation_supprimee` (moitié restante de R-125-5) ;
- `test_suppression_refusee_pendant_une_generation` : 409 ; 200 après la fin ;
- `test_suppression_et_envoi_en_concurrence` (paramétré, deux ordres forcés par barrière : suppression réservée puis envoi, envoi ouvert puis suppression) : un 409 d'un côté, aucun message orphelin (B-1527) ;
- `test_ecritures_en_cours_compte_les_envois` (`GET /api/data/ecritures-en-cours`).
Non-régression, verts sans modification : `tests/test_b1494_conversation_supprimee_pendant_la_reponse.py`, `tests/test_b1513_synthese_conversation_supprimee.py`, `tests/test_b1461_depart_du_client_pendant_la_reponse.py`, `tests/test_b1260_purge_attend_les_creations_du_chat.py`, `tests/test_b1276_purge_suspend_les_creations_du_chat.py`, `tests/test_chat_annulation_reelle.py`, `tests/test_chat_traitement.py`, `tests/test_fencing_traitement.py`, `tests/test_traitements_fondation.py`.
Écran, rouges d'abord : `components/settings/PrivacyTab.ecrituresEnCours.test.tsx` (la confirmation annonce le compte lu au moteur ; le message suivant reprend `ecritures_arretees`) ; `components/prototype/PrototypeConversationDrawer.suppressionPendantLaReponse.test.tsx` (409 du moteur : la conversation reste, « Arrêter la réponse » est proposé).
Critère observable : une réponse en cours, Paramètres, « Effacer toutes mes données » : la confirmation annonce l'arrêt ; après le redémarrage, aucune conversation ne réapparaît.

**Lot 1b. Travaux de fond (B-1520).**
Rouges d'abord, `tests/test_p125_lot1b_travaux_de_fond.py` :
- **`test_b1520_la_derniere_ecriture_precede_l_effacement`** (le test d'intégration demandé) : délibération du Board par la vraie route `/api/board/deliberate`, fournisseur factice lent, persistance de la décision ralentie de 0,3 s sous `shield`, lancée sur la boucle de l'application ; purge par le `TestClient` pendant la persistance. Attendus : purge 200 ; commit de la décision daté avant `premier_delete` ; aucune `BoardDecisionDB` après ; `ecritures_arretees.travaux.board == 1`. Sabotage : faire sortir le traitement de `_en_cours` à la fin de la porteuse au lieu de `terminer()` : rouge ;
- `test_b1520_aucune_ecriture_apres_la_purge_sur_la_boucle_de_l_app` du lot 0 : marqueur `xfail` retiré, vert ;
- `test_pendant_une_purge_aucun_travail_ne_demarre` (paramétré : board, atelier, trame, indexation, action, synchronisation) : refus dit, aucune ligne ;
- `test_chaque_travail_sort_de_la_table_apres_sa_derniere_ecriture` (même paramètre, espion d'ordre) ;
- `test_board_client_parti_avant_le_premier_octet` (par `appel_asgi`) : table vide, ligne `cancelled`, jamais `queued` (R-125-10) ; `test_board_client_parti_pendant_la_deliberation` : la clôture détachée pose l'état terminal après la persistance, `ReponseSuivie` ne le touche pas ;
- `test_bilan_nomme_les_travaux` : « 1 réponse et 1 délibération du Board ont été arrêtées. »
Critère observable : une délibération du Board en cours, « Effacer toutes mes données » : la confirmation la nomme ; après le redémarrage, la décision n'existe pas.

**Lot 2. Registre de l'écran, brouillons, pièces jointes, transport ; verrou inchangé.**
Rouges d'abord :
- `lib/reponsesEnCours.test.ts` : départ, fin, deux entrées indépendantes, renommage à l'adoption, `cancelled` qui fige la bulle, 404 fantôme qui retire la conversation d'origine, `clearMessageEntities` sur une conversation non affichée ; `arrêt après l'événement generation : annulerTraitement(id), jamais cancelGeneration` ; `arrêt avant l'événement : cancelGeneration(conversationId)` ;
- `lib/brouillons.test.ts` : `rendreAuBrouillonSiVide` selon la définition de « vide » (affichée : champ ; autre : stockage) ;
- `components/chat/ChatInput.echecEtBrouillon.test.tsx` : `C tapé depuis 2 s dans le champ d'Orion affichée, A échoue : C intact, A non réécrit` ; `A échoue, Orion quittée, brouillon d'Orion vide : A sous la clé d'Orion` ; `A échoue, Orion quittée, brouillon d'Orion B : B intact` ;
- `components/chat/ChatInput.texteQuitteLeChamp.test.tsx` : les cinq chemins, frappe à t, geste à t + 2 s, horloge + 10 s : aucun brouillon (non-régression de B-1509 et B-1525, étendue au test qui parcourt les chemins) ;
- `stores/piecesJointesStore.test.ts` : `même fichier joint dans Orion puis dans Veille : deux entrées` ; `bascule Orion vers Veille sans flux : Veille n'en a aucune, Orion la retrouve` (B-1512) ; `chat fermé pendant l'indexation, rouvert : la pièce jointe est prête, l'envoi n'est pas bloqué` ; `retrait : indexation annulée` ; `échec 409, liste d'origine non vide : les deux pièces jointes présentes, sans doublon` ;
- `components/prototype/ConversationCanvasPrototype.transportAccueil.test.tsx` : `brouillon D enregistré, T transporté depuis l'accueil : D puis T au champ, streamMessage jamais appelé` (B-1526) ; `brouillon vide : T part une fois` (non-régression B-626).
Test réécrit : `components/chat/ChatInput.cycle6.test.tsx` lit `localStorage['therese-draft-conv-locale']` au lieu de l'espion (constat 13) ; sabotage : réécrire le brouillon dans le chemin d'arrêt, rouge.
À garder verts sans modification : `components/chat/ChatInput.arretEtFile.b1514.test.tsx`, `components/chat/ChatInput.brouillonEtReponse.b1509.test.tsx`, `components/chat/ChatInput.brouillonParConversation.b1377.test.tsx`, `components/chat/ChatInput.fluxCoupe.b1395.test.tsx`, `components/chat/ChatInput.rattachement.test.tsx`, `components/chat/ChatInput.commandeFichier.b1521.test.tsx`, `components/chat/ChatInput.annulation.test.tsx`, `hooks/useAutosave.test.ts`, `lib/arretDeLaReponse.test.ts`.
Critère observable : aucun changement visible du verrou ; une pièce jointe ne suit plus un changement de conversation ; fermer le chat pendant une indexation ne la perd plus.

**Lot 3. États par conversation ; `isStreaming` devient un miroir.**
Rouges d'abord (Orion en flux, Veille affichée, en pilotant le registre) : `« Arrêter », indicateur et repère local absents de Veille` ; `activité au repos dans Veille, rendue en revenant dans Orion` ; `la fin d'Orion écrit dans Orion` ; `uneReponseEstEnCours() vrai pendant le flux d'Orion, quelle que soit la conversation affichée`.
Garde de source : `lib/miroirIsStreaming.test.ts`. À migrer, intention conservée : les cinq fichiers qui simulent un flux par `isStreaming: true` ou `setStreaming(true)`, et les quatre que la V3 nommait ; chacun saboté après migration. Si P-109 est fusionné, son test de démarrage refusé passe sur `uneReponseEstEnCours()`.
Critère observable : verrou en place ; une capture du chat pendant une réponse, avant et après le lot, est identique.

**Lot 4. Files, plafond et fins hors écran.**
Rouges d'abord : `un message en file n'est consommé qu'une fois et jamais dans une autre conversation` ; `il porte ses pièces jointes` ; `B en file, Orion quittée, A réussit : B intact dans le brouillon d'Orion, ses pièces jointes dans sa liste` ; `A échoue avec B en file : B ne part pas, « Envoyer maintenant » et « Retirer » offerts, A revient au champ` (B-1511) ; `troisième envoi au plafond : en file avec la mention du plafond, parti à la première fin` ; `changer la constante ou la fonction de comptage change le seuil sans autre modification` ; `envoi local pendant une réponse locale : en file avec la mention locale` ; `envoi en ligne pendant une réponse locale : part` ; `échec d'Orion affichant Veille : champ et pièces jointes de Veille intacts` ; `navigation reçue par Orion quittée : non exécutée, proposée par notification` ; `carte d'action « Depuis Orion »`.
Critère observable : verrou en place ; un message tapé pendant une réponse part encore à sa fin dans la même conversation.

**Lot 5. Levée du verrou.**
La clause 2 de la garde commune passe à « conversation éphémère en flux » ; la clause 3 entre (`vider`) ; le tiroir et `runNavigationAction` suivent `navigationVerrouillee()` ; le sélecteur de projet est désactivé pendant la réponse de sa conversation ; la vue demandée pendant un flux s'ouvre tout de suite (`components/prototype/ConversationCanvasPrototype.tsx:1288`). Si ce lot crée le module, il écrit les tests du § 6 ; sinon il ajoute ceux des clauses 2 et 3 dans leur nouvelle forme.
Tests à inverser, intention d'origine gardée là où elle vaut encore (éphémère, suppression, vidage, projet) : `lib/clientActions.test.ts`, `components/prototype/ConversationCanvasPrototype.parite.test.tsx`, `components/prototype/PrototypeConversationDrawer.test.tsx`, `lib/arretDeLaReponse.test.ts`. Vert sans modification : le test vocal de P-109 s'il est fusionné.
Critère observable : pendant une réponse d'Orion, « Nouvelle conversation », l'Agenda et le tiroir s'ouvrent sans bandeau ; supprimer Orion, la vider ou changer son projet est refusé avec « Arrêter la réponse ».

**Lot 6. Suivre et revenir, puis recette.**
Rouges d'abord : `une ligne de « Travaux » ouvre sa conversation pendant un flux` ; `une conversation absente du store est chargée puis ouverte` ; pastille et repère du tiroir ; notification « Réponse prête » et son « Ouvrir ».
Recette navigateur (modèle local réel, ou flux ralenti par `page.route`) : le parcours de Hugo, puis le pire cas des connexions dans chacune des trois webviews, selon la lecture tranchée par Ludo, avec une délibération du Board, une mission d'Atelier et une trame en cours, puis ouvrir l'Agenda ; temps de chargement et connexions ouvertes relevés, captures, console et réseau.
Critère observable : le parcours de Hugo se déroule sans refus ; Orion compte en base une seule réponse. **Le pire cas est mesuré et rapporté** ; si l'Agenda dépasse 30 s sous WebView2, le constat revient à Ludo avec la mesure et une proposition, et rien ne change sans sa réponse.

## 9. Défauts qui existent sans aucune RFC

- **Fermés depuis la V3** : R-125-1 à R-125-3 (B-1508 à B-1510), la moitié de R-125-5 (B-1513), le constat 14 (B-1525).
- **Ouverts, couverts ici** : B-1511 (R-125-8, lot 4), B-1512 (R-125-4, lot 2), B-1520 (R-125-6, lot 1b, cause de l'échec isolée au § 3), B-1526 (transport, lot 2), B-1527 (message orphelin, lot 1a), la moitié restante de R-125-5 (chemin non diffusé, lot 1a).
- **R-125-7, à ficher** : changer le projet d'une conversation pendant sa réponse fait lire deux périmètres à une même réponse (`components/chat/ConversationProjectPicker.tsx:161`, `routers/chat.py:1746`, `routers/chat.py:3300`). Corrigé au lot 5.
- **R-125-10, nouveau, à reproduire (lu au code)** : une délibération du Board dont le client part avant le premier octet laisse sa ligne de suivi `queued` jusqu'au redémarrage. La ligne est créée dans le corps de la route (`routers/board.py:199-205`) ; le générateur qui la démarre et la termine (`routers/board.py:222`) ne s'exécute jamais si la réponse est annulée avant son premier pas (mécanisme du constat 8). Reproduction proposée : `appel_asgi` sur `/api/board/deliberate` avec déconnexion immédiate, puis `GET /api/processing-tasks` : la délibération y figure, en attente, jusqu'au redémarrage. Corrigé au lot 1b.

## 10. Risques et régressions à protéger

- **Un envoi ou un traitement jamais fermé** retiendrait chaque purge jusqu'au plafond : `ReponseSuivie` pour toute réponse en flux, `finally` de route sinon, `terminer()` pour les traitements ; les tests « toutes les sorties » des lots 1a et 1b vérifient les tables vides.
- **Ordre inscription puis suspension** : invariant sans `await`, commenté à l'endroit exact, exercé par les tests d'envoi retenu.
- **Borne de 5 s du nettoyage** (`routers/chat.py:2113`) : une écriture coupée par elle peut encore aboutir dans le fil d'aiosqlite ; si c'est avant le premier `DELETE`, elle est effacée, sinon elle survit. De même, `ReponseSuivie` ferme l'envoi au-delà de 6 s même si `aclose()` n'a pas fini. Fenêtre étroite (base occupée 5 s), nommée, non couverte.
- **Harnais** : un test de concurrence écrit sur la boucle de pytest ne mesure rien (§ 3) ; la règle est en tête du § 8.
- **Brouillons** : un seul effacement, au départ du texte ; aucune écriture de brouillon sans clé explicite ; jamais d'écrasement.
- **Pièces jointes** : le store ne persiste rien, comme aujourd'hui ; un rechargement les perd.
- **Identité adoptée (B-1377)** : clés du registre, de la file et des pièces jointes renommées, jamais dupliquées.
- **Connexions** : le plafond est un choix, la recette le confronte au pire cas, Ludo décide.
- **P-109 et P-121** : garde commune (§ 6), tests par clause.
- **BUG-139, B-1369, B-1395, B-1461, B-1514** : tests gardés verts.

## 11. Plan de tests, en résumé

- **Moteur** : `tests/test_p125_lot0_deux_flux.py`, `tests/test_p125_lot0_harnais.py`, `tests/test_p125_lot1a_registre_des_envois.py`, `tests/test_p125_lot1b_travaux_de_fond.py`, aide `tests/concurrence.py`.
- **Écran** : `lib/gardeDeNavigation.test.ts`, `lib/reponsesEnCours.test.ts`, `lib/miroirIsStreaming.test.ts`, `lib/brouillons.test.ts`, `stores/piecesJointesStore.test.ts`, `components/chat/ChatInput.echecEtBrouillon.test.tsx`, `components/chat/ChatInput.texteQuitteLeChamp.test.tsx`, `components/prototype/ConversationCanvasPrototype.transportAccueil.test.tsx`, `components/settings/PrivacyTab.ecrituresEnCours.test.tsx`, `components/prototype/PrototypeConversationDrawer.suppressionPendantLaReponse.test.tsx`, plus ceux des lots 3 à 6.
- **À migrer** : lot 3. **À inverser** : lot 5. **Recette** : lot 6.

## 12. Questions réservées à Ludo

**Question 1 : la décision 30, relue avec ses conséquences.** Le 25/09, sur ta délégation, j'ai retenu « deux réponses de fond en même temps en ligne, file au-delà ». Trois lectures sont possibles ; elles ne retirent pas la même chose. Ta réponse ne change qu'une constante et une fonction de comptage. Une ligne suffit : « A », « B » ou « B+ ».

Le contexte technique : chaque flux long (une réponse du chat, une recherche approfondie, une délibération du Board, une mission d'Atelier, une trame) tient une connexion au moteur pendant des minutes ; Chromium, donc WebView2 sous Windows, n'en ouvre que six par hôte ; toute autre requête qui attend plus de 30 s abandonne avec un message d'erreur (`services/api/core.ts:122`). Pour un modèle local, rien ne change : une seule réponse locale à la fois (V1-Q1).

- **Lecture A : deux réponses du chat au total, celle que tu regardes comprise.** Conséquence : pendant qu'Orion te répond, tu ne peux lancer qu'une seule autre conversation ; la troisième attend, avec la mention « deux réponses sont déjà en cours ». Ce n'est plus « deux de fond ». Pire cas avec un Board, un Atelier et une trame en cours : cinq connexions, l'Agenda a la sixième.
- **Lecture B : deux réponses de fond plus celle que tu regardes, trois au total.** Conséquence : la décision telle qu'elle est écrite. Pire cas : trois réponses, un Board, un Atelier et une trame occupent les six connexions ; l'écran que tu ouvres ensuite (l'Agenda) attend qu'une se libère, et affiche une erreur de délai au bout de 30 s si aucune ne se libère.
- **Lecture B+ : B, mais les flux longs se comptent ensemble, cinq au plus pour qu'un message du chat parte.** Conséquence : trois réponses du chat tant que rien d'autre ne tourne ; si le Board délibère, une place de fond en moins, et la mention le dit (« une délibération du Board est en cours : ton message part dès qu'une place se libère »). Le Board, l'Atelier et la trame n'ont pas de file et ne sont jamais retenus : si tu les lances alors que cinq flux tournent, le sixième passe, et c'est seulement dans ce cas que l'écran suivant peut attendre.

**Ma recommandation : B+.** Elle tient la décision telle que tu l'as prise (deux de fond) et garde une connexion libre dans tous les cas où c'est le chat qui ouvre le cinquième flux. A est plus simple mais retire une réponse de fond sur deux dès que tu regardes une conversation qui répond ; B est la plus généreuse mais peut faire tomber un écran au délai.

**Et dans tous les cas** : la recette du lot 6 mesure le pire cas dans les trois webviews ; si l'Agenda dépasse 30 s, je reviens vers toi avec la mesure. Aucune baisse de la constante sans ta réponse.

Aucune autre question : l'arrêt d'office n'efface rien de plus que ce que l'utilisatrice a demandé d'effacer, rien n'est annoncé publiquement, la marque n'est pas en jeu.

## Annexe : appuis dans le code (à `7baf1793`)

- Garde et coque : `components/prototype/ConversationCanvasPrototype.tsx` : garde `:1076-1091`, `openChat` `:1195-1216`, effet de navigation `:1280-1326`, `fermerLeChat` `:1514-1525`, rétrécissement `:1587-1589`, Échap `:1591-1628`, actions `:1856-1881`, transport B-626 `:1799-1804`, tiroir `:2051`, surface du chat `:2054-2055`. Tiroir : `components/prototype/PrototypeConversationDrawer.tsx:258-285`. Navigation : `lib/clientActions.ts:29-42`. Arrêt : `lib/arretDeLaReponse.ts:10-32`. Registre des saisies : `lib/saisieEnCours.ts:12-31`.
- Composeur : `components/chat/ChatInput.tsx` : pièces jointes `:126-127`, champ désactivé `:207`, contrôleurs `:274-290`, indexation `:292-337`, dépôt `:339-360`, envoi `:506-509`, file `:549-555`, départ `:648-653`, échec `:854-904`, auto-envoi `:1062-1074`, arrêt `:1077-1114`, inscription de l'arrêt `:1117`, restauration `:1188-1209`, bandeau de file `:1429-1445`.
- Brouillons : `hooks/useAutosave.ts:5-8`, `:136-150`, `:167-178`. Store : `stores/chatStore.ts:82-85`, `:344-347`, `:444-452`, `:460-473`.
- Moteur, chat : `routers/chat.py` : annulation `:1000-1043`, recherche `:1053-1245`, envoi `:1251-1319`, réponses en flux `:1439`, `:1508`, `:1604`, `:1672`, `:1690`, chemin non diffusé `:1857-1897`, génération `:1913-1995`, nettoyage `:2081-2143`, point d'écriture `:2163-2182`, suppression `:3902-3926`.
- Moteur, données : `routers/data.py` : purge `:566-588`, plafond `:595-599`, attente `:602-629`, suppression `:632-647`, restauration `:1547`, `:1671`, `:1688`, `:1694`, `:1698`, `:1709` ; `services/memory_tools.py:1283-1337` ; `main.py:729-752` ; `services/maintenance.py:1-71`.
- Traitements : `services/traitements.py:61-166`, `:168`, `:200` ; `services/task_registry.py:58-86`, `:129-160` ; Board `routers/board.py:164-205`, `:222-306`, `services/board.py:816-820`.
- Starlette et uvicorn (`.venv`) : `.venv/lib/python3.13/site-packages/starlette/responses.py:248-281`, `.venv/lib/python3.13/site-packages/uvicorn/protocols/http/httptools_impl.py:227`.
- Harnais : `tests/conftest.py:106-129`, `:245-258` ; `tests/test_b1260_purge_attend_les_creations_du_chat.py:37-44`.
