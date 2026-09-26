# RFC P-125 (V3) : changer de sujet pendant une réponse longue, la réponse se termine en fond

Rédigé le 26/09/2026 ; lignes relues sur `main` à `feac6303`, revérifiées à `a3c98b74` (les commits intermédiaires, B-1503 à B-1505, ne déplacent que les lignes de la restauration dans `routers/data.py`, recalées ici). Remplace la V2 du même jour (`docs/plans/2026-09-26-rfc-p125-reponse-en-fond-v2.md`), refusée par la revue adverse du 26/09 (constats 9 à 22, dont un P1, verdict NO-GO). Proposition acceptée par Ludo le 25/09 (« Je valide tout sauf la 141 »). Les décisions 31 et 32 du 25/09 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:108-112`, `:187-189`) sont posées comme des faits ; la lecture de la décision 30 est soumise à Ludo (§ 12). Aucun code avant la validation de ce document.

Chemins relatifs à `src/frontend/src/` (écran) et `src/backend/app/` (moteur), sauf mention. Toutes les lignes citées ont été lues à `feac6303` par `git show HEAD:` : la rédaction a commencé à `66b78788`, quinze commits sont arrivés pendant (dont B-1494, prérequis, fermé), et toutes les citations ont été recalées puis revérifiées ; l'arbre de travail portait des modifications non commitées, qui ne sont pas la base. Entre `900765fb` (base de la V2) et `feac6303`, `routers/chat.py` (au-delà de `:1699`) et `routers/data.py` (au-delà de `:1033`) ont bougé : les numéros de la V2 dans ces zones sont décalés, et la V3 cite les nouveaux ; ailleurs, ceux de la V2 restent justes.

## 0. Les constats de la revue et leur traitement

| Nº | Constat | Verdict et preuve relue à HEAD | Traitement | Où |
|---|---|---|---|---|
| 9 (P1) | Le brouillon d'une conversation est effacé à la fin de sa propre réponse : un message mis en file, devenu brouillon d'Orion, disparaît quand la réponse à A se termine ; en échec, `saveDraft(A)` écrase B | **Accepté, et il existe déjà sans RFC.** `components/chat/ChatInput.tsx:820` (`clearDraft()` après un flux réussi), `:841` (`saveDraft(trimmed)` en échec) ; `hooks/useAutosave.ts:136-153` (effacement sans comparer), `:161-177` (écriture sous la clé quittée). Variantes actuelles, verrou compris : R-125-1 à R-125-3 (§ 10) | Un seul effacement, au moment où le texte quitte le champ (envoi ou mise en file), minuteur abandonné ; plus rien à la fin du flux ; en échec, A n'est rendu au brouillon d'origine que s'il est vide ; un échec ne relance pas la file | § 7.2, § 7.4, lots 2 et 4 |
| 10 | L'arrêt d'office et le refus de suppression comptent les lignes `running` en base, orphelines comprises : purge en 503 à répétition, conversation insupprimable | **Accepté.** `services/traitements.py:304-326` (une ligne sans adaptateur est orpheline), `:248-261` (sans adaptateur, rien n'est conclu) ; `services/task_registry.py:162-187` (le récupérateur ne traite que l'exécution précédente) ; `routers/chat.py:2112`, `:2136-2141` (état terminal écrit sous `suppress`, dans un nettoyage borné à 5 s) | Un registre moteur des envois en cours, en mémoire du processus : ni l'attente ni le refus ne lisent la base, une ligne orpheline ne retient donc rien | § 7.1, lot 1 |
| 11 | « Aucune génération ne démarre pendant une purge » est un test suivi d'une écriture : un envoi qui a passé le test écrit après la purge | **Accepté.** `routers/chat.py:1307-1318` (message écrit), `:1945-1949` (traitement créé plus tard, dans le flux) ; `routers/data.py:633` puis `:700` ; `services/memory_tools.py:1255-1261` (B-1276, même classe) | L'envoi s'inscrit au registre moteur dès l'entrée de `/send` et `/deep-research`, avant le test de suspension et sans attente entre les deux ; la purge attend sa sortie | § 7.1, lot 1 |
| 12 | Le test « rien n'est écrit, ni dans l'ancienne base ni dans la restaurée » contredit le mécanisme : le partiel s'écrit dans l'ancienne base, archivée ensuite | **Accepté.** `routers/data.py:1628` (arrêt des travaux), `:1632` (`close_db`), `:1643` (archive de sécurité) ; `routers/chat.py:2752-2759` (partiel écrit à l'annulation) | Tranché : le partiel s'écrit dans l'ancienne base, donc dans l'archive de sécurité, et n'est pas dans la base restaurée (V3-2) | § 7.1, lot 1 |
| 13 | Les pièces jointes du composeur ne sont rattachées à aucune conversation ; un message en file ne garde que son texte | **Accepté, et il existe déjà sans RFC.** `ChatInput.tsx:126` (état local), `:543-548` (file : texte seul), `:1127-1155` (la bascule ne restaure que le texte) ; `components/prototype/PrototypeChatSurface.tsx:91` (`<ChatInput` sans `key`). Aujourd'hui déjà, sans flux, une pièce jointe ajoutée dans Orion reste au composeur quand on ouvre Veille (R-125-4) | Pièces jointes rangées par conversation dans un store ; la file porte texte et pièces jointes | § 7.2, § 7.4, lots 2 et 4 |
| 14 | « Jamais d'écriture dans une conversation disparue » oublie les deux messages d'erreur, et une relecture n'est pas atomique avec l'insertion | **Accepté ; traité pour l'essentiel par B-1494, fermé pendant la rédaction** (commit `6f927313`). Le point d'écriture unique `_ecrire_reponse` (`routers/chat.py:2162-2182`) insère d'abord, ce qui prend le verrou d'écriture de SQLite, vérifie ensuite que la conversation existe, sinon revient en arrière ; il couvre le partiel (`:2207-2213`), les deux messages d'erreur (`:2747`, `:2788`) et la réponse finale (`:2871-2873`). Restent hors de ce point la synthèse de la recherche approfondie (`:1196-1204`), atteignable depuis l'écran, et le chemin non diffusé (`:1886-1896`), réservé à l'API, que B-1494 laisse à P-125 (R-125-5). Les tests de B-1494 suppriment la conversation avant l'écriture (`tests/test_b1494_conversation_supprimee_pendant_la_reponse.py:48`) : aucun ne met les deux en concurrence réelle | Le lot 1 fait passer les deux écritures restantes par `_ecrire_reponse` et ajoute un test de concurrence répété ; l'atomicité se prouve, elle n'est pas affirmée | § 3, § 7.1, lot 1 |
| 15 | Au-delà du plafond, le 503 dirait « rien n'a été modifié » alors que des réponses ont été coupées | **Accepté.** `routers/data.py:596-599`, `:621-628` (B-1283, même mensonge corrigé pour les fiches) | Message propre à ce cas, avec le compte | § 7.1, lot 1 |
| 16 | La décision 31 est ramenée au chat et à la recherche sans le dire ; Board et Atelier écrivent après la purge | **Accepté, et il existe déjà sans RFC.** `routers/board.py:199-203`, `services/board.py:853-875` (décision écrite en fin de délibération), `routers/agents.py:291` ; `routers/data.py:602-629` n'attend ni l'un ni l'autre. Il y a plus que ces deux : `routers/documents.py:775` (trame), `routers/files.py:88`, `services/action_agents.py:638`, `services/project_sync_service.py:415` | L'arrêt d'office vise les **réponses** (chat et recherche), comme la décision 31 le dit ; le lot 1 est renommé en conséquence ; les autres écrivains sont fichés (R-125-6), et le registre moteur leur est réutilisable | § 7.1, § 7.9, § 10 |
| 17 | `ChatInput.annulation` et d'autres tests posent l'état global que le lot 3 remplace : « à garder verts sans modification » est impossible | **Accepté.** `ChatInput.annulation.test.tsx:60`, `:224` ; `MessageList.c9.test.tsx:21` ; `MessageList.attenteLocale.c10.test.tsx:40` ; `ChatInput.ollamaCloudLocal.b1174.test.tsx:114` | Listés au lot 3 comme à migrer, intention conservée, sabotage pour vérifier qu'ils rougissent encore | lot 3, § 9 |
| 18 | L'appui de l'écran désigne la restauration ; la purge recharge la fenêtre aussitôt, le compte n'est lisible qu'un instant ; la confirmation s'appuie sur le registre du lot 2 | **Accepté.** `components/settings/PrivacyTab.tsx:163-171` (restauration), `:182-199` (purge), `:197` (rechargement) | Appuis corrigés ; le compte est annoncé dans la confirmation, avant l'effacement ; au lot 1 par `isStreaming` (une réponse au plus sous verrou), par le registre ensuite | § 7.7, lot 1 |
| 19 | L'appui « deux générations qui se chevauchent ne se gênent pas » vise le fencing d'une même conversation | **Accepté.** `tests/test_fencing_traitement.py:88-99` (une seule clé, `conv-chevauchement`) | Ce test reste l'appui du fencing seulement ; la sûreté de deux conversations en flux se prouve au lot 0, et la V3 ne l'affirme pas avant | § 6, § 11, lot 0 |
| 20 | Refuser le changement de projet pendant la réponse ne protège pas la cloison, qui peut changer une seconde après | **Accepté ; la vraie raison est vérifiée.** `components/chat/ConversationProjectPicker.tsx:161` (`disabled={enCours}` seulement), `components/prototype/PrototypeChatSurface.tsx:59` ; `routers/memory.py:400-408`. Le périmètre est lu au départ (`routers/chat.py:1745`, `:2403`) **et relu à chaque appel d'outil de mémoire** (`:3299-3301`, `:3610-3612`) : changer le projet pendant une réponse fait lire deux périmètres à une même réponse. Existe sans RFC (R-125-7) | Refus gardé pour ce motif ; la cloison d'une conversation qui a déjà des réponses est hors périmètre, proposée à part | § 7.7, § 7.9 |
| 21 | La décision 30 est relue « deux flux au total, affichée comprise », présentée comme un fait ; Board, Atelier et trame tiennent aussi une connexion | **Accepté.** `docs/plans/2026-09-25-questions-rfc-pour-ludo.md:106-107` et `:187-188` ; flux longs `services/api/board.ts:112`, `agents.ts:169`, `:431`, `documents.ts:278` | Question 1 du § 12, avec l'arithmétique ; le plafond devient une constante et une fonction de comptage, pour que l'une ou l'autre lecture soit un changement d'une ligne ; recette du pire cas | § 5, § 7.4, § 12, lot 6 |
| 22 | Un contexte inscrit sans traitement n'a pas d'état terminal : on ne sait pas ce qu'on attend | **Accepté.** `routers/chat.py:1963-1978` (repli `generation = None`), `:2133-2135` (retrait du contexte après la fermeture du producteur) | L'attente porte sur la sortie de l'envoi du registre moteur, qui existe avec ou sans traitement ; test « suivi en panne » | § 7.1, lot 1 |

Aucun constat n'est réfuté. Cinq décrivent aussi un défaut qui existe déjà, verrou compris : ils sont fichés à reproduire (§ 10).

## 1. Ce que la V3 garde de la V2

- Le besoin (Hugo, `docs/campagnes/2026-09-25-personas-c13/rapports/hugo.md`, hugo-07) et la recommandation : option A, le flux quitte le composeur pour un registre par conversation ; le verrou n'est levé qu'au lot 5.
- L'inventaire de la V2 (§ 3.1 à § 3.8), relu à `feac6303` : les treize appels de `blockStreamingNavigation`, ce qui pense encore « la conversation affichée », les gestes destructeurs pendant un flux, « Travaux », les connexions. Les corrections de la V3 sont au § 6.
- Les décisions V1-Q1 à V1-Q5 et Q-import, avec leur motif (V2 § 2).
- La recherche approfondie migrée au registre avant la levée du verrou.
- Les fins hors écran (notification « Réponse prête », navigation reçue jamais exécutée hors de sa conversation, carte d'action sensible « Depuis Orion »), « Travaux » sans garde de flux, pastille et repère du tiroir (V2 § 5.5 et § 5.6).
- La conversion d'un message en file en brouillon quand on quitte sa conversation (V2 § 5.4). Elle n'était dangereuse que par l'effacement de fin de flux, que la V3 retire ; elle ne peut entrer en conflit avec aucun autre texte, puisque le champ est désactivé tant qu'un message attend (`ChatInput.tsx:202`, `hasQueuedPrompt`).

## 2. Ce que la V3 retire ou reporte, et pourquoi

- **Retiré : « `saveDraft` et `clearDraft` reçoivent la clé de la conversation d'origine »** (V2 `:156`) et le test « brouillon effacé sous la clé d'origine » (V2 `:232`). C'est la moitié du P1 (constat 9). Remplacés par un effacement au départ du texte (§ 7.2).
- **Retiré : l'arrêt d'office fondé sur « tout traitement actif » en base** (V2 `:140`, `:143`). Les lignes orphelines l'auraient bloqué (constat 10) et un contexte sans traitement n'avait rien à attendre (constat 22). Remplacé par le registre moteur (§ 7.1).
- **Retiré : le test « la réponse n'est écrite ni dans l'ancienne base ni dans la restaurée »** (V2 `:228`). Il ne pouvait pas passer (constat 12).
- **Retiré : « au-delà, rien n'est touché et la route répond 503, comme aujourd'hui »** (V2 `:140`, `:267`) (constat 15).
- **Retiré : l'appui du fencing comme preuve de la sûreté de deux conversations** (V2 `:78`, `:265`) (constat 19).
- **Retiré : la « lecture retenue » de la décision 30 présentée comme un fait** (V2 `:24`). Elle devient une question à Ludo, et la conception tient les deux lectures (constat 21).
- **Retiré : « à garder verts sans modification »** pour `ChatInput.annulation` au-delà du lot 2 (V2 `:233`, `:259`) (constat 17).
- **Retiré : l'intitulé « Le moteur protège les données »** du lot 1 (constat 16) : il protège les données des réponses, et le dit.
- **Reporté, fiché : l'arrêt d'office des autres écrivains de fond** (Board, Atelier, trame, actions, indexation de fichiers, synchronisation de dossier) pendant une purge ou une restauration (R-125-6). Motif : la décision 31 porte sur les réponses ; ces écrivains ont chacun leur propre cycle, et les arrêter touche leurs routes, hors de ce chantier. Le registre moteur du lot 1 leur est réutilisable tel quel.
- **Reporté : la cloison d'une conversation qui a déjà des réponses et change de projet** (constat 20). Elle existe sans flux ; la V3 garde seulement le refus pendant la réponse, pour son vrai motif.
- **Inchangé, dit : un message en file est perdu par un rechargement**, comme aujourd'hui (`stores/chatStore.ts:460-473` ne persiste pas `queuedPrompt`).

## 3. Prérequis, corrigé hors RFC par l'orchestrateur

- **B-1494**, fermé pendant la rédaction (commit `6f927313`) : une conversation supprimée pendant sa réponse ne reçoit plus de message orphelin. Son point d'écriture unique (`routers/chat.py:2162-2182`) couvre les quatre écritures du chemin diffusé ; son message de commit laisse à P-125 le chemin non diffusé. Le lot 1 y ajoute ce chemin et la synthèse de la recherche approfondie, qui n'y passe pas non plus (R-125-5).

## 4. Le besoin

Hugo travaille avec un modèle local : ses réponses prennent de 2 à 7 minutes. Pendant ce temps, « Nouvelle conversation », un changement de vue ou l'ouverture d'une autre conversation sont refusés. Il n'a que deux choix : attendre, ou jeter la réponse. Sa piste, acceptée : laisser la réponse se terminer en fond et la retrouver ensuite.

## 5. Décisions

| Nº | Décision | Origine | Ce qu'elle impose ici |
|---|---|---|---|
| 30 | Deux réponses de fond en même temps en ligne, file au-delà, avec mention | Ludo par délégation, 25/09 | **Lecture soumise à Ludo** (§ 12, question 1). La conception ne dépend que d'une constante et d'une fonction de comptage (§ 7.4) |
| 31 | La purge et la restauration arrêtent d'office les réponses en cours, et le disent | Ludo par délégation, 25/09 ; lié à B-1425 | Registre moteur, arrêt et attente de la sortie de chaque envoi avant toute suppression ; envois refusés pendant la purge ; le compte est annoncé avant et rendu après |
| 32 | Les pièces jointes d'une réponse de fond qui échoue restent sur la conversation d'origine, jamais déposées ailleurs | Ludo par délégation, 25/09 | Pièces jointes rangées par conversation, y compris avant l'envoi (constat 13) |
| V1-Q1 à V1-Q5, Q-import | Inchangées (V2 `:27-32`) | Tranchées en V2 | Un flux local à la fois ; notification de fin ; carte d'action visible partout ; conversation éphémère verrouillée ; pas de reprise après rechargement ; import permis |
| V3-1 | Le moteur tient en mémoire la liste des envois en cours (`/send`, `/deep-research`) ; c'est elle, et jamais la base, que lisent l'arrêt d'office et le refus de suppression | Tranché ici | Motif : constats 10, 11 et 22 ; une liste en mémoire du processus ne peut pas contenir d'orphelin d'une exécution précédente, et elle existe avant le traitement |
| V3-2 | Une restauration pendant une réponse : le partiel s'écrit dans l'ancienne base, donc dans l'archive de sécurité ; il n'est pas dans la base restaurée | Tranché ici (délégation : aucun effacement de plus, rien d'annoncé, pas de marque) | Motif : l'archive de sécurité est « l'état d'avant » ; elle doit contenir tout ce qui a été écrit avant, sans quoi revenir en arrière perdrait ce partiel ; et la base restaurée doit être exactement la sauvegarde choisie |
| V3-3 | Un brouillon n'est effacé qu'au moment où son texte quitte le champ (envoi ou mise en file) | Tranché ici | Motif : constat 9 ; à la fin d'un flux, le brouillon peut être un autre texte |
| V3-4 | Un échec ne relance pas la file de sa conversation ; A revient au brouillon seulement s'il est vide | Tranché ici | Motif : le message en file supposait la réponse qui a échoué ; aujourd'hui il part quand même et remplace A dans le champ (R-125-8) |
| V3-5 | Changer le projet d'une conversation pendant sa réponse est refusé | Tranché ici | Motif : les outils de mémoire relisent le périmètre à chaque appel (constat 20) |

## 6. Ce qui existe à HEAD : corrections de l'inventaire de la V2

- **Sûreté de deux flux** : `tests/test_fencing_traitement.py:88-99` prouve le fencing de deux générations d'une même conversation, rien de plus (constat 19). La sûreté de deux conversations en flux simultané n'est pas prouvée à HEAD ; c'est l'objet du lot 0.
- **Changer le projet** (V2 § 3.6) : le risque n'est pas que « la cloison ment » à la fin, c'est qu'une même réponse lise deux périmètres (§ 0, constat 20).
- **Effacer toutes mes données** (V2 § 3.6) : outre les réponses, la purge n'attend ni le Board, ni l'Atelier, ni la trame, ni les actions, ni l'indexation de fichiers, ni la synchronisation de dossier (constat 16, R-125-6).
- **Purge à l'écran** : la route est appelée par `handleDeleteAll` (`PrivacyTab.tsx:182-199`), qui recharge la fenêtre aussitôt le message posé (`:197`) ; la restauration est `handleRestoreBackup` (`:163-171`).
- **Recherche approfondie au suivi en panne** (`routers/chat.py:1138-1140`) : la V2 la disait inarrêtable par la purge ; avec le registre moteur, elle l'est, par son drapeau (`:1102`, `:1152`).
- **Toutes les sorties de `/send`** : la route rend un flux à cinq endroits (`routers/chat.py:1438`, `:1507`, `:1603`, `:1671`, `:1689` : commandes déterministes, actions en ligne, réponse du modèle) ; chacune écrit en base. L'inscription au registre moteur doit toutes les couvrir.

## 7. Conception

### 7.1 Moteur (lot 1) : protéger les données des réponses

**Le registre moteur des envois** (`services/envois_en_cours.py`, V3-1). Un `Envoi` porte : la conversation (celle de la requête dès l'entrée, avant tout `await`, ou celle que la route crée, `routers/chat.py:1262-1272`), un drapeau `arret_demande`, la fonction d'arrêt de sa génération une fois liée, et un événement `fini`. Quatre opérations :

- `ouvrir_envoi()` : synchrone, première instruction de `send_message` (`:1251`) et de `deep_research_endpoint` (`:1054`). Juste après, sans aucun `await` entre les deux, la route consulte la suspension des créations (`services/memory_tools.py:1251-1278`) ; suspendue, elle ferme l'envoi et répond 409 : « Une opération sur tes données est en cours (effacement ou restauration) : rien n'a été envoyé. » En asyncio, rien ne s'intercale entre deux instructions sans `await` : soit l'envoi a passé le test avant que la purge ne suspende, et il est dans la liste quand elle la relève ; soit il le passe après, et il est refusé (constat 11).
- `envoi.lier_arret(fonction)` : la génération lie son arrêt dès qu'elle existe (le contexte de `_register_generation`, `routers/chat.py:1943` ; le drapeau de la recherche, `routers/chat.py:1102`). Si l'arrêt était déjà demandé, la fonction est appelée aussitôt, et la génération rend `cancelled` avant de produire.
- `fermer(envoi)` : pose `fini` et retire l'envoi. Appelée dans le `finally` le plus extérieur du producteur, **après** le bloc de nettoyage borné (`routers/chat.py:2112-2141`) et l'état terminal, pour le chat ; après `terminer` (`:1227-1232`) pour la recherche ; dans le `finally` de la route pour une sortie sans flux. Toutes les réponses en flux de `send_message` (§ 6) passent par un même enveloppeur, `_flux_suivi(envoi, flux)`, qui ferme l'envoi dans son `finally`. Invariant : après `fermer`, plus aucune écriture de cet envoi ne peut avoir lieu (le partiel est écrit, ou son écriture a été annulée par la borne de 5 s).
- `arreter_et_attendre() -> int` : relève la liste, demande l'arrêt de chaque envoi, attend tous les `fini`, rend le nombre d'envois arrêtés. Appelée en tête de `_attendre` dans `_arreter_les_travaux_de_fond` (`routers/data.py:616-619`), donc par la purge (`:633`) comme par la restauration (`:1628`), sous le plafond existant (`:595`, `:622`).

Ce registre répond aux trois constats d'un coup. Une ligne `running` orpheline n'y figure pas : elle ne retient ni la purge ni la suppression (constat 10). Un envoi qui n'a pas encore créé son traitement, ou dont le suivi est en panne (`generation = None`, `routers/chat.py:1963-1978`), y figure et est attendu (constats 11 et 22).

**Arrêt d'office (décision 31).** La réponse de la purge porte `reponses_arretees`. Au-delà du plafond, la route répond 503 ; si des réponses ont été arrêtées, le détail le dit : « 1 réponse en cours a été arrêtée ; l'effacement n'a pas eu lieu. Réessaie dans un instant. » (constat 15), sur le modèle de B-1283 (`routers/data.py:623-628`). Sans réponse arrêtée, le message actuel (`routers/data.py:596-599`) reste juste.

**Restauration (V3-2).** Même chemin : les réponses sont arrêtées et leurs partiels écrits dans l'ancienne base avant `close_db` (`routers/data.py:1632`), donc avant l'archive de sécurité (`routers/data.py:1643`), qui les contient ; la base restaurée ne les contient pas.

**Écritures dans une conversation disparue (constat 14).** B-1494 a posé le point d'écriture unique, `_ecrire_reponse` (`routers/chat.py:2162-2182`) : l'insertion part d'abord et prend le verrou d'écriture, la vérification de la conversation suit, un retour arrière annule tout si elle a disparu. Il couvre la réponse finale (`:2871-2873`), le partiel (`:2207-2213`) et les deux messages d'erreur (`:2747`, `:2788`). Le lot 1 y fait passer les deux écritures restantes : la synthèse de la recherche approfondie (`:1196-1204`) et la réponse du chemin non diffusé (`:1886-1896`). Il ajoute le test qui manque : suppression et insertion lancées en parallèle, répétées, jamais de message orphelin. La suppression est elle-même une transaction unique (`:3915-3916`). Si ce test rougit (par exemple si la session d'écriture tient déjà un instantané de lecture plus ancien), le lot passe à une insertion conditionnelle en une seule instruction (`INSERT INTO messages (...) SELECT ... WHERE EXISTS (SELECT 1 FROM conversations WHERE id = :conversation_id)`). L'atomicité n'est pas affirmée ici : elle se prouve.

**Supprimer une conversation dont la réponse court** : `delete_conversation` (`:3901-3923`) répond 409 quand le registre moteur a un envoi pour elle, avec un détail qui propose d'arrêter la réponse. Le registre, pas la base : une ligne orpheline ne rend plus rien insupprimable. Comme l'envoi porte sa conversation dès l'entrée, la suppression est refusée aussi dans la fenêtre où `send_message` a vérifié la conversation (`:1262-1268`) sans avoir encore écrit le message de l'utilisateur (`:1307-1318`), que le point d'écriture de B-1494 ne couvre pas.

**Banc SQLite** : au lot 0 (§ 8).

**Ce que l'arrêt d'office ne couvre pas** (constat 16) : les autres écrivains de fond (§ 7.9, R-125-6).

Aucune colonne ne change ; la tête Alembic reste `b8c9d0e1f2a3`.

### 7.2 Le registre de l'écran, les brouillons et les pièces jointes (lot 2)

**Le registre** (`lib/reponsesEnCours.ts`, petit store Zustand) : repris de la V2 (§ 5.2). Une entrée par conversation, clé = identifiant serveur, renommée à l'adoption d'identité (`stores/chatStore.ts:444-452`) ; la boucle de lecture et la fin du flux, pour le chat et pour la recherche approfondie, deviennent des fonctions du module, avec la conversation d'origine en paramètre ; `arreter(conversationId)` coupe cette lecture et appelle `cancelGeneration` sur cette conversation ; `lib/arretDeLaReponse.ts` en devient la façade ; l'événement `cancelled` fige la bulle ; un 404 « Conversation not found » retire la conversation d'origine ; `clearMessageEntities` cherche dans toutes les conversations.

**Les brouillons (constat 9, V3-3, V3-4).** Trois règles, et rien d'autre ne touche un brouillon :

1. **Le texte quitte le champ** (envoi, ou mise en file) : le minuteur de sauvegarde en attente est abandonné, puis le brouillon de la conversation affichée est effacé. C'est le seul effacement. `clearDraft` (`hooks/useAutosave.ts:136-153`) abandonne désormais aussi le minuteur ; il est appelé au départ du texte (`ChatInput.tsx:621` pour l'envoi, `:544-545` pour la file), et plus à la fin du flux (`:820` disparaît). La conversation affichée est bien celle d'origine à ce moment-là : c'est son champ que le texte quitte.
2. **Fin réussie d'une réponse** : aucun geste sur les brouillons.
3. **Échec** : A est rendu à la conversation d'origine par `rendreAuBrouillonSiVide(conversationId, texte)` (`lib/brouillons.ts`, clé explicite) seulement si son brouillon est vide, et, si elle est affichée, son champ aussi. Sinon A n'est pas réécrit : il reste dans le fil, en bulle de l'utilisatrice (`ChatInput.tsx:613-617`) et en base (`routers/chat.py:1307-1318`). `saveDraft(trimmed)` (`ChatInput.tsx:841`) disparaît. Un échec ne relance pas la file (V3-4) : le message en file reste affiché, avec « Retirer » (`ChatInput.tsx:1374-1390`) et un nouveau bouton « Envoyer maintenant ».

`useAutosave` garde sa forme publique (`saveDraft`, `restoreDraft`, `clearDraft`, `retrySave`) : les dix-huit fichiers de tests qui la simulent (par exemple `ChatInput.annulation.test.tsx:40`) restent valides ; `rendreAuBrouillonSiVide` vit dans `lib/brouillons.ts`, que ces simulations ne touchent pas.

**Les pièces jointes (constat 13, décision 32).** `attachedFiles` quitte l'état local du composeur (`ChatInput.tsx:126`) pour un store, `piecesJointesParConversation`, renommé à l'adoption d'identité. Le composeur affiche et modifie la liste de la conversation affichée ; changer de conversation change de liste, sans rien transporter. L'indexation d'une pièce jointe garde la conversation relevée à l'ajout (`:302-308`) et met à jour la liste de celle-ci, même si l'on est ailleurs. En échec, les pièces jointes envoyées reviennent dans la liste d'origine si elle est vide ; sinon elles restent consignées sur le message en base (BUG-160, `routers/chat.py:1316`). Ce lot corrige R-125-4 dès maintenant, verrou compris.

### 7.3 Des états par conversation (lot 3)

Repris de la V2 (§ 5.3) : `isStreaming` devient le sélecteur `reponseEnCours(conversationId)` pour tout ce qui s'affiche (indicateur, repère local, suivi du bas du fil, « Arrêter », suggestions) ; l'activité globale suit la conversation affichée. Pour les lecteurs qui demandent « une réponse court-elle quelque part ? », le registre expose `uneReponseEstEnCours()` : `lib/clientActions.ts:33` jusqu'au lot 5, et l'étape 1 de P-109 (§ 7.8).

### 7.4 Une file par conversation et un plafond (lot 4)

- `filesDAttente[conversationId]` : une place par conversation, texte **et pièces jointes** (constat 13).
- **Un envoi part tout de suite** si sa conversation n'a pas de réponse en cours, si `compterLesFluxQuiComptent() < PLAFOND_REPONSES_EN_LIGNE`, et, pour un envoi local, si aucun flux local n'est ouvert (V1-Q1). La constante vaut 2 ; la fonction de comptage est le seul endroit où vit la lecture de la décision 30 (§ 12). Sinon, file de la conversation, avec la mention qui dit la vraie raison (formulations de la V2 `:168-170`).
- L'auto-envoi ne part que dans la conversation affichée, une fois sa propre réponse finie **avec succès** (V3-4) et le plafond libre ; il est réévalué à chaque fin d'entrée du registre.
- **Quitter une conversation dont un message attend** : ce message devient son brouillon, ses pièces jointes rejoignent sa liste, avec « Ton message attend dans Orion : il est gardé en brouillon. » Le brouillon était vide (règle 1 du § 7.2, champ désactivé tant qu'un message attend) : aucun texte n'est écrasé. Il ne part jamais ailleurs, ni plus tard sans geste.
- Le transport de l'accueil (B-626) met le texte dans la file de la conversation qu'`openChat` va afficher.

### 7.5 La fin d'une réponse qu'on ne regarde plus (lot 4)

Repris de la V2 (§ 5.5) pour le succès, la navigation reçue, la carte d'action sensible et l'arrêt venu de « Travaux » ou d'une purge. L'échec suit le § 7.2 : aucun brouillon écrasé, pièces jointes rendues à leur conversation si sa liste est vide, file non relancée.

### 7.6 Suivre et revenir (lot 6)

Repris de la V2 (§ 5.6) : « Travaux » ouvre sa conversation sans garde de flux, en la chargeant par l'API si elle manque au store ; pastille « Réponse en arrière-plan · Orion » ; repère du tiroir.

### 7.7 Ce qui reste interdit

1. **Deux réponses dans la même conversation** : le second message reste en file (V2 `:191`).
2. **Supprimer, vider ou changer le projet** d'une conversation dont la réponse court : refusé avec « Arrêter la réponse » (B-1369). La suppression est aussi refusée par le moteur (§ 7.1). Le projet l'est parce que les outils relisent le périmètre en cours de réponse (V3-5) ; le sélecteur (`ConversationProjectPicker.tsx:161`) est désactivé tant que sa conversation a une réponse en cours, et le dit.
3. **Exécuter en fond** une navigation ou une action sensible sans clic.
4. **Une conversation éphémère** garde le verrou actuel (V1-Q4).
5. **Recharger ou fermer THÉRÈSE** arrête les réponses en cours (B-1461, B-1462, P-142).
6. **Effacer ou restaurer** arrête d'office les réponses et le dit : la confirmation annonce « La réponse en cours sera arrêtée » (lot 1, `isStreaming`) puis « N réponses en cours seront arrêtées » (dès le lot 2, registre), **avant** l'effacement ; le message qui suit la route reprend `reponses_arretees`, même si la fenêtre se recharge aussitôt (`PrivacyTab.tsx:197`).
7. **Une session vocale** garde son propre verrou (§ 7.8).

### 7.8 Contrat avec P-109 (conversation vocale)

La V2 de P-109 (`docs/plans/2026-09-26-rfc-p109-conversation-vocale-v2.md:89-92`, `:297`) exige ce qui suit ; la V3 le reprend comme règle de ses lots.

1. **Le lot 5 garde la clause vocale de `blockStreamingNavigation`** : si une session vocale est active, la garde refuse avec « Conversation vocale en cours » et « Arrêter la conversation vocale », avant toute autre clause. Si P-109 est livré avant ce lot, son test « `openChat` refusé pendant une session » figure dans la liste des tests à garder verts sans modification ; s'il est livré après, P-109 ajoute sa clause à la fonction réécrite.
2. **Le verrou du tiroir et celui de `runNavigationAction`** ne tombent pas avec le verrou du chat : au lot 5, `navigationLocked` (`components/prototype/ConversationCanvasPrototype.tsx:2051`) et la garde de `lib/clientActions.ts:33` deviennent « conversation éphémère en flux, **ou** session vocale active ». Sans cela, le tiroir changerait `currentConversationId` pendant une session.
3. **L'étape 1 de P-109** (refus si une réponse écrite est en cours, `rfc-p109-v2:85`) lit aujourd'hui `isStreaming` global ; à partir du lot 3, elle lit `uneReponseEstEnCours()` (§ 7.3). Le lot 3 migre ce lecteur si P-109 est déjà fusionné.
4. **Après les lots 2 et 3**, la session inscrit ses générations au registre de l'écran sous l'identifiant de sa conversation (engagement de P-109). Côté moteur, ses générations passent par `/send` : le registre moteur du lot 1 les arrête d'office à la purge sans rien de plus.
5. **Ce que la V3 de P-109, rédigée en parallèle** (`docs/plans/2026-09-26-rfc-p109-conversation-vocale-v3.md`), attend en plus du lot 1 d'ici : que le message de l'utilisateur, écrit hors du point d'écriture de B-1494, ne survive pas à une purge ou à une suppression, et que la génération s'arrête d'office. Le registre moteur du § 7.1 couvre les deux (inscription avant la suspension, conversation portée dès l'entrée, arrêt et attente). Elle nomme la clause vocale `sessionVocaleBloqueLaNavigation()` : c'est ce nom que le lot 5 garde en tête de la garde.
6. **Plafond** : une session ne démarre que si aucune réponse ne court, et verrouille la navigation pendant sa durée ; elle ne coexiste donc avec aucune réponse de fond, et le plafond n'a pas à la compter.

### 7.9 Hors périmètre, nommé

- La reprise après rechargement (V1-Q5).
- La rédaction d'une section de l'Atelier documentaire, encore coupée quand on ferme le document (`stores/documentStore.ts:257`).
- **Les autres écrivains de fond pendant une purge ou une restauration** : délibération du Board (`routers/board.py:199-203`, décision écrite `services/board.py:853-875`), mission de l'Atelier (`routers/agents.py:291`), trame documentaire (`routers/documents.py:775`), actions (`services/action_agents.py:638`), indexation de fichiers (`routers/files.py:88`), synchronisation de dossier (`services/project_sync_service.py:415`). Fiché R-125-6.
- La cloison d'une conversation qui a déjà des réponses et change de projet (constat 20) : à proposer au portail (avertir au changement), sans lien avec le flux.
- La persistance d'un message en file après un rechargement (inchangée).

## 8. Livraison en lots TDD

Chaque lot : tests écrits d'abord et vus rouges pour la bonne raison (sauf les caractérisations du lot 0) ; un commit par lot ; sabotage ciblé par fonction, jamais par chaîne globale (règle du 27/08) ; les six portes du dépôt ; revue adverse du diff. Le verrou reste en place jusqu'au lot 5. B-1494, prérequis, est fermé (`6f927313`).

**Lot 0. Caractérisation (aucun code applicatif).**
Moteur, verts attendus : deux conversations en flux simultané écrivent chacune leur réponse une seule fois, et `/cancel/{conversation_id}` arrête la bonne (c'est l'appui de la sûreté, constat 19) ; une conversation relue pendant son flux ne montre la réponse qu'une fois, à la fin ; banc SQLite sur une vraie base en fichier (le test vérifie que l'URL du moteur désigne un fichier) : deux commits de fin concurrents et une écriture utilisateur au même moment, chacun écrit une fois, aucune « database is locked » (WAL et `busy_timeout`, `models/database.py:1050-1051`). Écran : les tests « à garder verts » du § 9 sont relevés tels quels.
Critère observable : `pytest` et `vitest` verts, aucun fichier applicatif touché.

**Lot 1. Le moteur protège les données des réponses (livrable seul).**
Rouges d'abord, avec un fournisseur factice lent :
- purge pendant un flux de chat, puis pendant une recherche approfondie : aucune ligne `messages` après, `reponses_arretees` vaut 1 ;
- envoi en vol quand la purge commence (l'envoi est retenu, par un point d'arrêt injecté, juste après le test de suspension et avant l'écriture de son message) : après la purge, aucune ligne `messages`, `conversations` ni `processing_tasks` (constat 11) ;
- `send` et `deep-research` après le début de la purge : 409, aucun message écrit ;
- toutes les sorties de `send_message` (commande déterministe, action en ligne, réponse du modèle, erreur avant le flux) : le registre moteur est vide à la fin (un envoi jamais fermé bloquerait chaque purge jusqu'au plafond) ;
- ligne `running` de type `chat` sans producteur, insérée à la main : la purge ne l'attend pas, la suppression de sa conversation passe (constat 10) ;
- suivi en panne (`creer_traitement` qui lève) : purge pendant le flux, le partiel est écrit avant l'effacement, donc effacé (constat 22) ;
- plafond dépassé (plafond réduit par le test, fournisseur qui ignore l'arrêt) : 503, détail « 1 réponse en cours a été arrêtée ; l'effacement n'a pas eu lieu… », aucune table vidée (constat 15) ;
- restauration pendant un flux : le partiel est écrit avant `close_db` (ordre relevé par espion), absent de la base restaurée (constat 12) ;
- conversation supprimée pendant une recherche approfondie : aucune synthèse écrite ; même chose par le chemin non diffusé ; test de concurrence suppression et insertion répété, jamais de message orphelin (constat 14 ; les quatre écritures du chemin diffusé sont couvertes par les tests de B-1494) ;
- `DELETE /api/chat/conversations/{id}` pendant une génération : 409 ; après sa fin : 200 ; demandé pendant qu'un envoi est retenu (point d'arrêt injecté) entre la vérification de la conversation et l'écriture du message de l'utilisateur : 409, aucun message orphelin.
Écran, rouges d'abord : le tiroir refuse de supprimer la conversation affichée dont la réponse court (`isStreaming`, verrou en place) et propose « Arrêter la réponse » ; la confirmation de « Effacer toutes mes données » et celle d'une restauration annoncent « La réponse en cours sera arrêtée » quand `isStreaming` est vrai.
Critère observable : dans l'app, une réponse en cours, Paramètres, « Effacer toutes mes données » : la confirmation annonce l'arrêt ; après le redémarrage, aucune conversation ne réapparaît.

**Lot 2. Le registre, les brouillons, les pièces jointes, verrou inchangé.**
Rouges d'abord :
- registre : départ, fin, arrêt ciblé, renommage de clé à l'adoption, deux entrées indépendantes, `cancelled` qui fige la bulle ; `clearMessageEntities` sur une conversation non affichée ; 404 fantôme qui retire la conversation d'origine ;
- brouillons, sur les parcours d'aujourd'hui (R-125-1 à R-125-3) : B tapé pendant la réponse à A et enregistré, A réussit, puis changement de conversation et retour : B est là ; A échoue alors que B est dans le champ : le brouillon enregistré reste B ; A échoue, champ vide : A revient dans le champ et le brouillon ; message envoyé moins de 5 s après la dernière frappe, réponse finie avant ces 5 s (horloge factice) : aucun brouillon au retour ;
- pièces jointes (R-125-4) : une pièce jointe ajoutée dans Orion sans envoi, bascule vers Veille sans flux : Veille n'en a aucune, Orion la retrouve ; chat fermé puis rouvert sur Orion : elle est là ; l'indexation commencée dans Orion se termine sur la liste d'Orion.
À garder verts sans modification : `ChatInput.annulation`, `ChatInput.fluxCoupe.b1395`, `ChatInput.rattachement`, `ChatInput.brouillonParConversation.b1377`, `ChatInput.cycle6` (« après Arrêter, aucun brouillon n'est réécrit »), `hooks/useAutosave.test.ts`, `lib/arretDeLaReponse.test.ts`.
Critère observable : aucun changement visible du verrou ; une réponse arrêtée depuis « Travaux » se fige avec « (interrompu) » ; une pièce jointe ne suit plus un changement de conversation.

**Lot 3. Des états par conversation.**
Rouges d'abord, en pilotant le store (Orion en flux, Veille affichée) : « Arrêter », indicateur et repère local absents de Veille ; activité au repos dans Veille, rendue en revenant dans Orion ; la fin d'Orion écrit dans Orion ; `uneReponseEstEnCours()` vrai pendant le flux d'Orion quelle que soit la conversation affichée.
Tests à migrer, intention conservée (constat 17) : `ChatInput.annulation.test.tsx` (`:60`, `:224`), `MessageList.c9.test.tsx` (`:21`), `MessageList.attenteLocale.c10.test.tsx` (`:40`), `ChatInput.ollamaCloudLocal.b1174.test.tsx` (`:114`) : le flux est posé dans le registre au lieu de `isStreaming`. Chacun est saboté après migration (retrait ciblé de la branche qu'il protège) pour vérifier qu'il rougit encore ; en particulier `MessageList.c9` ne doit pas devenir vert par construction.
Critère observable : verrou en place, aucun changement visible ; une capture du chat pendant une réponse, avant et après le lot, est identique.

**Lot 4. Files, plafond et fins hors écran.**
Rouges d'abord : un message en file n'est consommé qu'une fois et jamais dans une autre conversation ; il porte ses pièces jointes ; B en file, Orion quittée, A réussit : B intact dans le brouillon d'Orion, ses pièces jointes dans la liste d'Orion ; A échoue avec B en file : B ne part pas, reste en file avec « Envoyer maintenant » et « Retirer », A revient dans le champ (R-125-8) ; troisième envoi en ligne au plafond : en file avec la mention du plafond, parti à la première fin ; changer la valeur de la constante ou la fonction de comptage change le seuil sans autre modification ; envoi local pendant une réponse locale : en file avec la mention locale ; envoi en ligne pendant une réponse locale : part ; échec d'Orion affichant Veille : champ et pièces jointes de Veille intacts ; navigation reçue par Orion quittée : non exécutée, proposée par notification ; carte d'action portant « Depuis Orion ».
Critère observable : verrou en place ; un message tapé pendant une réponse part encore à sa fin dans la même conversation ; une carte « Envoyer cet e-mail ? » dit de quelle conversation elle vient.

**Lot 5. Levée du verrou.**
La garde ne retient plus que la session vocale (§ 7.8, en premier), la saisie modifiée (B-978, avec les surfaces de P-121 si son lot 5 est passé) et les interdits du § 7.7 ; le tiroir et `runNavigationAction` suivent (« éphémère en flux, ou session vocale ») ; le sélecteur de projet est désactivé pendant la réponse de sa conversation ; la vue demandée pendant un flux s'ouvre tout de suite (`ConversationCanvasPrototype.tsx:1284-1288`). Un test énumère les treize appelants de la garde et vérifie qu'un flux dans une autre conversation ne les retient plus, et qu'une session vocale les retient tous.
Tests à inverser, intention d'origine gardée là où elle vaut encore (conversation éphémère, suppression, vidage, projet) : `lib/clientActions.test.ts:88`, `components/prototype/ConversationCanvasPrototype.parite.test.tsx:286` et `:363`, `components/prototype/PrototypeConversationDrawer.test.tsx:138`, `lib/arretDeLaReponse.test.ts:33`.
Coordination : le lot 5 de P-121 (`docs/plans/2026-09-26-rfc-p121-un-formulaire-de-devis-v3.md`, § 6.4) réécrit aussi `blockStreamingNavigation` ; le second à passer se rebase, les tests des deux restent verts.
Critère observable : dans l'app, pendant une réponse d'Orion, « Nouvelle conversation », l'Agenda et le tiroir s'ouvrent sans bandeau ; supprimer Orion, la vider ou changer son projet est refusé avec « Arrêter la réponse ».

**Lot 6. Suivre et revenir, puis recette.**
Rouges d'abord : une ligne de « Travaux » ouvre sa conversation pendant un flux ; une conversation absente du store est chargée puis ouverte ; pastille et repère du tiroir ; notification « Réponse prête » et son « Ouvrir ».
Recette navigateur (pile jetable 17393 et 1420, jamais 17293 ; modèle local réel, ou flux ralenti par `page.route`) : le parcours de Hugo (V2 `:251`), puis **le pire cas des connexions** (constat 21), dans chacune des trois webviews : le nombre de réponses que le plafond permet selon la lecture tranchée par Ludo, plus une délibération du Board, une mission d'Atelier et une trame documentaire en cours, puis ouvrir l'Agenda ; relever le temps de chargement et le nombre de connexions ouvertes vers le moteur. Captures à chaque étape, console et réseau relevés.
Critère observable : le parcours de Hugo se déroule sans refus ; Orion compte en base une seule réponse ; dans le pire cas, l'Agenda s'affiche en moins de 30 s sous WebView2. Sinon, la constante baisse d'un cran, sans autre changement.

## 9. Plan de tests, en résumé

- **Unitaires** : le registre de l'écran ; `lib/brouillons.ts` ; la règle de départ (plafond, local) ; `envois_en_cours` côté moteur (ouverture, lien d'arrêt tardif, fermeture, attente).
- **Composants et stores** : Orion en flux, Veille ouverte par le tiroir, avec les attendus des lots 2 à 4.
- **Moteur** : lot 0 (hypothèse de sûreté, banc SQLite), lot 1 (purge, restauration, envoi en vol, sorties de `/send`, orphelin, suivi en panne, plafond, écritures orphelines, suppression).
- **À garder verts sans modification** : `ChatInput.fluxCoupe.b1395`, `ChatInput.rattachement`, `ChatInput.brouillonParConversation.b1377`, `ChatInput.cycle6`, `hooks/useAutosave.test.ts`, `hooks/useConversationSync.test.ts`, `tests/test_chat_annulation_reelle.py`, `tests/test_chat_traitement.py`, `tests/test_fencing_traitement.py`, `tests/test_traitements_fondation.py`, `tests/test_b1461_depart_du_client_pendant_la_reponse.py`, et le test vocal de P-109 s'il est déjà fusionné.
- **À migrer** : les quatre du lot 3. **À inverser** : les cinq du lot 5.
- **Recette** : lot 6.

## 10. À reproduire : défauts qui existent sans aucune RFC

Chacun se reproduit à HEAD, verrou compris ; l'orchestrateur les fiche avant le lot qui les corrige.

- **R-125-1. Un texte tapé pendant une réponse est effacé à la fin de celle-ci.** Hugo tape B pendant la réponse à A, sans l'envoyer ; B est enregistré au bout de 5 s (`hooks/useAutosave.ts:84-86`) ; la réponse finit, `clearDraft()` (`ChatInput.tsx:820`) retire la clé et vide la valeur retenue (`useAutosave.ts:136-148`) ; B reste affiché, mais si Hugo change de conversation sans retaper, le nettoyage n'écrit rien (`:161-176`, contenu retenu vide) et B est perdu au retour. Corrigé au lot 2.
- **R-125-2. Un échec réécrit le brouillon avec le message raté.** Le champ garde B (`ChatInput.tsx:835`), mais `saveDraft(trimmed)` (`:841`) programme l'écriture de A sous la même clé ; au changement de conversation, A remplace B. Corrigé au lot 2.
- **R-125-3. Un message envoyé peut revenir en brouillon.** L'envoi vide le champ sans passer par `saveDraft` (`ChatInput.tsx:621` ; `saveDraft` n'est appelé qu'à la frappe, `:462`) ; `clearDraft` n'abandonne pas le minuteur (`useAutosave.ts:136-153`), qui a capturé le texte (`:84-86`). Si la réponse finit moins de 5 s après la dernière frappe, le minuteur réécrit le message déjà parti, qui revient dans le champ au prochain retour dans la conversation. Corrigé au lot 2.
- **R-125-4. Une pièce jointe suit le changement de conversation.** Sans aucun flux, une pièce jointe ajoutée dans Orion (indexée sous le périmètre d'Orion, `ChatInput.tsx:302-308`) reste dans le composeur quand on ouvre Veille (`:126`, aucune remise à zéro hors envoi, `:622` ; composeur non recréé, `PrototypeChatSurface.tsx:91`) et part avec le message suivant de Veille. Corrigé au lot 2.
- **R-125-5. La synthèse d'une recherche approfondie s'écrit dans une conversation supprimée.** Supprimer depuis le tiroir la conversation affichée pendant sa recherche n'est pas gardé (`components/prototype/PrototypeConversationDrawer.tsx:301-310`) ; la synthèse s'écrit ensuite par sa propre session, hors du point d'écriture de B-1494 (`routers/chat.py:1196-1204`). Même défaut sur le chemin non diffusé (`:1886-1896`), réservé à l'API. B-1494 couvre les quatre écritures du chemin diffusé (partiel, deux erreurs, réponse finale), et son message de commit laisse le chemin non diffusé à P-125. Fiche sœur de B-1494. Corrigé au lot 1.
- **R-125-6. Des écrivains de fond écrivent après « Effacer toutes mes données ».** `_arreter_les_travaux_de_fond` (`routers/data.py:602-629`) n'attend ni une délibération du Board (qui écrit `BoardDecisionDB`, question comprise, en fin de délibération, `services/board.py:853-875`), ni une mission d'Atelier, ni une trame documentaire, ni une action, ni une indexation de fichier, ni une synchronisation de dossier. Reproduction proposée : lancer une délibération du Board en arrière-plan, effacer toutes les données pendant la délibération, relire `board_decisions` après la fin. Hors de ce chantier (§ 7.9).
- **R-125-7. Changer le projet d'une conversation pendant sa réponse fait lire deux périmètres à une même réponse.** Le sélecteur n'est désactivé que pendant son propre enregistrement (`ConversationProjectPicker.tsx:161`) ; le contexte initial est lu au départ (`routers/chat.py:1745`, `:2403`) et chaque outil de mémoire relit le périmètre (`:3299-3301`, `:3610-3612`). Corrigé au lot 5 par le refus (V3-5) ; à reproduire avant, puisque le défaut existe verrou compris.
- **R-125-8. Un échec relance quand même la file.** Quand A échoue avec B en file, `setInput` rend A au champ (`ChatInput.tsx:835`), puis `setStreaming(false)` (`:868`) déclenche l'auto-envoi (`:1020-1028`), qui remplace A par B dans le champ et envoie B. Corrigé au lot 4 (V3-4).

## 11. Risques et régressions à protéger

- **Un envoi jamais fermé** bloquerait chaque purge jusqu'au plafond puis la ferait échouer : toutes les sorties de `/send` passent par `_flux_suivi` ou par le `finally` de la route, et un test du lot 1 vérifie le registre vide après chacune.
- **Ordre inscription puis suspension** : l'absence d'`await` entre les deux est l'invariant qui ferme le constat 11 ; un test l'exerce, et un commentaire le dit à l'endroit exact.
- **Concurrence de deux flux** : prouvée au lot 0, pas avant ; côté modèle local, la file est dite à l'écran.
- **Messages en file** : jamais envoyés dans une autre conversation, jamais deux fois, jamais après un échec sans geste.
- **Brouillons** : un seul effacement, au départ du texte ; aucune écriture de brouillon ne vise une conversation sans clé explicite.
- **Purge et restauration** : une recherche approfondie ne s'arrête qu'entre deux étapes (`routers/chat.py:1152`) ; si l'attente dépasse le plafond, le 503 dit le compte des réponses arrêtées.
- **Identité adoptée (B-1377)** : clés du registre, de la file et des pièces jointes renommées à l'adoption, jamais dupliquées.
- **BUG-139, B-1369, B-1395, B-1461** : inchangés depuis la V2 (§ 9).
- **Connexions** : le plafond est un choix, pas une mesure ; la recette du lot 6 le confronte au pire cas.
- **P-109** : la clause vocale et le verrou vocal du tiroir sont testés au lot 5 (§ 7.8).
- **P-121** : même fonction de garde réécrite par les deux lots 5 ; rebase explicite.

## 12. Questions pour Ludo

**Question 1 (décision 30, relue).** La décision 30, prise sur ta délégation le 25/09, dit : « deux réponses de fond en même temps en ligne, file au-delà ». La V2 l'a relue sans te le demander ; la revue l'a relevé (constat 21). Deux lectures sont possibles, et elles n'ont pas le même coût. Une ligne de toi suffit : « A » ou « B ».

- **Lecture A** : deux réponses en ligne ouvertes au plus, **celle qu'on regarde comprise**. Au troisième envoi, file avec mention.
- **Lecture B** : deux réponses **de fond**, plus celle qu'on regarde, soit trois.

L'arithmétique : chaque flux long tient une connexion au moteur pendant des minutes (chat et recherche, `services/api/chat.ts:165`, `:226` ; Board, `board.ts:112` ; Atelier, `agents.ts:169`, `:431` ; trame, `documents.ts:278`), et WebView2 (Windows) n'en ouvre que six par hôte ; toute autre requête abandonne au bout de 30 s (`services/api/core.ts:122`). Le plafond ne compte que les réponses du chat. Pire cas en lecture A : deux réponses, un Board, une mission d'Atelier et une trame, cinq connexions ; l'Agenda prend la sixième. En lecture B : six connexions occupées avant l'Agenda, qui attend et peut tomber au délai.

**Recommandation : la lecture A.** Elle garde une connexion libre dans le pire cas ; la recette du lot 6 le vérifie dans les trois webviews. Dans les deux cas, ta réponse ne change qu'une constante et une fonction de comptage (§ 7.4).

Aucune autre question : la purge arrête des réponses mais n'efface rien de plus que ce que l'utilisatrice a demandé d'effacer ; rien n'est annoncé publiquement ; la marque n'est pas en jeu.

## Annexe : appuis dans le code (à `feac6303`)

- Coque : `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx` : garde `:1076-1091`, appels `:1196`, `:1218`, `:1226`, `:1398`, `:1413`, `:1615`, `:1653`, `:1679`, `:1732`, `:1858`, `:1866`, `:1878`, `:2066` ; rejeu `:1284-1288` ; tiroir `:2051` ; pastilles `:2083-2084`.
- Tiroir : `src/frontend/src/components/prototype/PrototypeConversationDrawer.tsx:258-285`, `:301-310`. Projet : `src/frontend/src/components/chat/ConversationProjectPicker.tsx:58`, `:161` ; `src/frontend/src/components/prototype/PrototypeChatSurface.tsx:59`, `:91`.
- Composeur : `src/frontend/src/components/chat/ChatInput.tsx` : pièces jointes `:126`, indexation `:287-332`, `abortRef` `:156`, brouillon `:182`, champ désactivé `:202`, frappe `:457-470`, file `:543-548`, envoi `:596-639`, persistance `:677-690`, fin `:816-878`, auto-envoi `:1020-1028`, arrêt `:1031-1048`, `:1063`, brouillon par conversation `:1127-1155`, bandeau de file `:1374-1390`.
- Brouillons : `src/frontend/src/hooks/useAutosave.ts:56-87`, `:136-153`, `:161-177`.
- Stores : `src/frontend/src/stores/chatStore.ts:78-87`, `:248-297`, `:344-347`, `:444-452`, `:460-473`.
- Navigation : `src/frontend/src/lib/clientActions.ts:29-42`. Réglages : `src/frontend/src/components/settings/PrivacyTab.tsx:163-171`, `:182-199`.
- API écran : `src/frontend/src/services/api/core.ts:122`, `:250` ; `src/frontend/src/services/api/chat.ts:165`, `:226` ; `board.ts:112`, `agents.ts:169`, `:431`, `documents.ts:278`.
- Moteur, chat : `src/backend/app/routers/chat.py` : registre des générations `:124-205`, annulation `:1000-1042`, recherche approfondie `:1053-1232`, envoi `:1250-1318`, sorties en flux `:1438`, `:1507`, `:1603`, `:1671`, `:1689`, périmètre `:1745`, `:2403`, génération `:1939-1994`, nettoyage `:2096-2141`, partiel `:2184-2215`, erreurs `:2727-2791`, fin `:2858-2873`, outils de mémoire `:3299-3306`, `:3609-3618`, suppression `:3901-3923`.
- Moteur, traitements : `src/backend/app/services/traitements.py:121-165`, `:200-261`, `:304-326` ; `src/backend/app/services/task_registry.py:129-187`.
- Moteur, données : `src/backend/app/routers/data.py` : purge `:565-589`, plafond `:595-599`, travaux de fond `:602-629`, suppression `:632-700`, restauration `:1604-1648` ; `src/backend/app/services/memory_tools.py:1251-1300` ; `src/backend/app/main.py:715-734` ; `src/backend/app/models/database.py:1044-1066`.
- Autres écrivains de fond : `src/backend/app/routers/board.py:199-203`, `src/backend/app/services/board.py:853-875`, `src/backend/app/routers/agents.py:291`, `src/backend/app/routers/documents.py:775`, `src/backend/app/routers/files.py:88`, `src/backend/app/services/action_agents.py:638`, `src/backend/app/services/project_sync_service.py:415`.
- Projet supprimé : `src/backend/app/routers/memory.py:400-408`.
