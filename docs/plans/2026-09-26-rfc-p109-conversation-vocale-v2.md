# RFC P-109 V2 : une conversation vocale de bout en bout, mains libres

Rédigé le 26/09/2026. Remplace la V1 (`docs/plans/2026-09-25-rfc-p109-conversation-vocale.md`), jugée NO-GO par la revue adverse du 25/09 (`docs/plans/revues/2026-09-25-revue-rfc-p109-p125.md`, section P-109). Les décisions du 25/09 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 18, 19 et 21) sont intégrées comme des faits. Aucun code avant une nouvelle revue adverse de ce document.

Base de code relue : `main` à `900765fb` (26/09/2026). Tous les numéros de ligne sont ceux de ce commit. Chemins relatifs à `src/backend/app/` (serveur) et `src/frontend/src/` (interface), sauf mention contraire. Tête Alembic : `b8c9d0e1f2a3`.

## 0. Ce qui change depuis la V1

- **La session crée sa propre conversation** avant la première parole (décision 18), et c'est elle qui rend l'interruption fiable : `cancelGeneration` a besoin d'un identifiant.
- **Les accords sont vérifiés au démarrage, une fois**, avec une finalité nouvelle `voice_conversation` pour l'écoute en ligne et la garde du composeur factorisée pour le modèle (décision 19, constats 2 et 3) ; une révocation pendant la session l'arrête.
- **Aucune mémoire locale n'est envoyée en phase 1** : le moteur la coupe en `mode_vocal`, le champ `include_memory` n'étant lu nulle part.
- **La session a son propre verrou**, lu par la garde de navigation existante, sans toucher `isStreaming` : elle ne dépend pas du registre de P-125, qui n'a aucune ligne de code, et survit à la levée du verrou du chat que prévoit la V2 de P-125 (`docs/plans/2026-09-26-rfc-p125-reponse-en-fond-v2.md`, lot 5) ; elle rejoindra ce registre après ses lots 2 et 3 (constat 6).
- **Échap et le grand bouton seulement**, par la pile d'Échap unifiée ; Espace n'arrête rien (décision 21, constat 5).
- **Le serveur court-circuite les quatre interprètes du message** en mode vocal, pas seulement les outils (constat 10).
- **La voix est lue par Web Audio**, sans URL `blob:` ni changement de CSP ; le module de capture est un fichier servi par l'application (constat 4).
- **La synthèse ne passe plus par le disque** et une seule tourne à la fois (constat 8).
- **Les dictées WAV sont effacées** depuis B-1424 ; la purge des dictées déjà conservées reste une décision de Ludo, décrite en deux options (section 9).
- **Le lot 0 perd le correctif de la voix « fr »**, fait par B-1410 (constat 7), et l'appui `system_resources` est retiré (constat 9).

## 1. Le besoin

Dr_logic-3D (fil Discord du 25/09) réfléchit à voix haute en conduisant, avec Perplexity en mode vocal. Il voudrait la même chose avec THÉRÈSE : parler, entendre la réponse, relancer, sans regarder d'écran. Aujourd'hui THÉRÈSE sait dicter et lire un texte, mais ne converse pas.

Trois exigences en découlent : une boucle continue (fin de parole détectée, réponse dite, écoute reprise), l'interruption, et aucun écran requis pendant la conversation.

**La réserve de la V1 tient toujours.** THÉRÈSE est une application de bureau, sans client mobile ; « en voiture » veut dire un ordinateur portable allumé dans l'habitacle. Le Code de la route interdit de placer dans le champ de vision du conducteur un écran allumé qui n'aide pas à la conduite ([article R412-6-2](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025111520)) et de porter à l'oreille un dispositif qui émet du son ([article R412-6-1](https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000030800800&cidTexte=LEGITEXT000006074228&dateTexte=20150628)). La V2 vise donc le bureau mains libres ; la voiture reste un usage toléré sur portable, écran hors de vue, son par les haut-parleurs, et l'application ne le promeut pas.

## 2. Décisions tranchées

| Sujet | Décision | Source |
|---|---|---|
| Conversation | Neuve à chaque session : aucun document ni projet embarqué sans le voir | Décision 18 du 25/09 |
| Accord pour le modèle en ligne | Demandé une fois, au démarrage, avant la première parole | Décision 19 du 25/09 |
| Arrêt au clavier | Échap et le grand bouton seulement ; Espace active déjà les boutons | Décision 21 du 25/09 |
| Cible de la V1 | Le bureau mains libres ; la voiture reste tolérée, jamais promue | Tranché ici (question 1 de la V1) : le produit n'a pas de client mobile |
| Moteurs par défaut | Écoute locale si la voix locale est prête, sinon Groq avec accord ; modèle configuré ; voix Piper toujours locale | Tranché ici (question 2 de la V1) : même routage que la dictée (`services/api/voice.ts:84-123`) et même esprit que P-111 (commit `64d98e79`, le choix local proposé d'abord à la mise en route) |
| Outils | Phase 1 sans aucun outil ; phase 2 en lecture seule, après usage réel | Tranché ici (question 3 de la V1) : la voix ne sait pas montrer une carte à valider |
| Interruption en parlant | Phase 2, après un essai d'annulation d'écho sur haut-parleurs | Tranché ici (question 4 de la V1) : sans essai, Thérèse s'interromprait en s'entendant |
| Accord de l'écoute en ligne | Finalité nouvelle `voice_conversation`, distincte de la dictée | Tranché ici (question 5 de la V1, constat 3) |
| API parole-à-parole en ligne (option C de la V1) | Refusée pour cette RFC ; à reconsidérer seulement si la recette montre que l'hybride ne tient pas sa cible | Tranché ici (question 6 de la V1) : nouveau tiers, audio et mémoire chez lui, outils et cloisons à recâbler |
| Usage mobile (option D de la V1) | Hors périmètre : un client mobile serait un produit à part | Tranché ici (question 7 de la V1) |
| Mémoire locale | Pas de contexte mémoire en phase 1, décidé par le moteur | Tranché ici : latence (prompt plus court, décisif en local), esprit de la décision 18 (rien d'embarqué sans le voir), phase 1 dédiée à la réflexion ; le champ `include_memory` n'est lu nulle part (section 4.5) |
| Propriété du flux | Verrou propre à la session, lu par `blockStreamingNavigation` ; `isStreaming` n'est pas touché ; inscription au registre de P-125 après ses lots 2 et 3 | Tranché ici (constat 6) : P-125 n'a aucune ligne de code ; sa V2 (`docs/plans/2026-09-26-rfc-p125-reponse-en-fond-v2.md`) lèvera le verrou du chat à son lot 5 et renvoie P-109 à son registre (§ 5.8) |
| Lecture audio | Web Audio (`decodeAudioData`), aucune URL `blob:`, CSP inchangée | Tranché ici (constat 4) |
| Dictées déjà conservées chez les testeurs | **Laissé à Ludo** (section 9) : c'est un effacement définitif sur leurs machines | Réservé le 25/09 |

## 3. Ce qui existe à `900765fb`

### 3.1 Faits réglés depuis la revue

- **B-1410** (commit `2d70c92d`) : la route de synthèse accepte `voice: "fr"`. La liste blanche traduit la langue seule en voix par défaut (`services/voice_local.py:99`, `_VOIX_PAR_LANGUE = {"fr": DEFAULT_PIPER_VOICE}`), test `tests/test_b1410_voix_fr_acceptee.py`. Le préalable du lot 0 de la V1 disparaît.
- **B-1424, volet dictée** (commit `a1c6737a`) : le WAV que le greffon écrit est effacé dès qu'il a été lu, que la transcription réussisse ou non (`hooks/useVoiceRecorder.ts:105-116` pour `effacerLEnregistrement`, appelé dans le `finally` à `:204-205`). Test `hooks/useVoiceRecorder.wavEfface.test.ts`. La permission existe : `fs:allow-remove` sur `$APPDATA/**` (`src/frontend/src-tauri/capabilities/default.json:138-144`).
- **B-1424, volet purge** (commit `1c8a1af8`) : « Effacer toutes mes données » vide le dossier `tauri-plugin-mic-recorder` après la purge du moteur (`services/api/data.ts:123-135`, appelé à `:144`). Test `services/api/data.purgeDictees.b1424.test.ts`.
- **Ce que B-1424 ne couvre pas**, et qui compte pour la section 4.10 : le greffon crée le fichier au **démarrage** de l'enregistrement (`WavWriter::create`, `~/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/tauri-plugin-mic-recorder-2.0.0/src/commands.rs:136-139`), et le chemin n'est connu de l'interface qu'à l'arrêt (`:208`). Une application fermée pendant une dictée, ou un arrêt qui échoue, laisse donc un WAV que rien n'efface. Les dictées accumulées avant la correction restent aussi en place.

### 3.2 Points d'appui

- **Dictée au clic.** Chemin Tauri : `hooks/useVoiceRecorder.ts:156-211`. Chemin navigateur : `getUserMedia` avec annulation d'écho et réduction de bruit (`:226-233`), sans fichier sur disque. Le texte est inséré dans le composeur, jamais envoyé seul (`components/prototype/ConversationCanvasPrototype.tsx:1809-1816`).
- **Routage de la transcription.** Préférence respectée sans exception, jamais de repli silencieux vers le cloud (`services/api/voice.ts:84-123`, `:141-197`). L'accord Groq est contrôlé en dur sur la finalité `voice` (`:131` et `:155`).
- **Consentement par finalité et par fournisseur.** `CloudPurpose` ne connaît que `llm`, `voice`, `images` et `documents` (`lib/consent.ts:26`). La clé est `finalité:fournisseur` (`:40-42`) et `dataCategories` n'est jamais testé (`:82-88`). Les réglages nomment chaque finalité (`components/settings/PrivacyTab.tsx:56-61`) et révoquent n'importe quel accord (`:106`, liste à `:439-443`). Le bouton de dictée demande l'accord Groq au clic (`components/chat/VoiceDictationButton.tsx:52-67`).
- **Garde d'accord du composeur.** Finalité `documents` dès que la conversation porte un document, sinon `llm`, adressée à la destination réelle (`components/chat/ChatInput.tsx:558-589`, `lib/ollamaCloud.ts:19-23`). C'est la seule garde du modèle en ligne : le serveur ne la refait pas.
- **Moteurs vocaux serveur.** Groq Whisper (`routers/voice.py:55-155`, modèle `whisper-large-v3-turbo` à `:104`, fichier temporaire effacé à `:150-155`). Whisper local, modèle gardé en mémoire dans un dictionnaire sans verrou (`services/voice_local.py:239-265`). Synthèse Piper, voix rechargée à chaque appel (`:292`), écrite dans un fichier temporaire (`routers/voice.py:313-322`) effacé par une tâche de fond après l'envoi. Bibliothèques embarquées par `collect_all` quand l'extra `voice-local` est présent au build (`src/backend/backend.spec:126-141`). Besoins en mémoire : environ 2 Go libres pour Whisper `base` et une voix Piper (`docs/VOICE-LOCAL.md:36-55`).
- **Espace Voix de la coque.** Transcrit un fichier, lit un texte, dit quel moteur sert et si l'audio quitte la machine (`components/prototype/VoiceWorkspaceCanvas.tsx:174`). Ouvert à `ConversationCanvasPrototype.tsx:2497-2507`, fermé par `collapseToolPanel` (`:1526-1533`).
- **Chat.** `streamMessage` (`services/api/chat.ts:147`), `createConversation` (`:276-281`), `cancelGeneration` (`:400-404`), événement `cancelled` connu du type des morceaux (`:67`). Route d'annulation par conversation (`routers/chat.py:1000`). `ChatRequest.disable_tools` (`models/schemas.py:114`). Classes d'effet des outils (`services/contexte_execution.py:26-47`). Un fournisseur local en panne ne bascule jamais en ligne (B-1071, `services/llm.py:832`).
- **Verrou de réponse et arrêt.** Un seul `isStreaming` (`stores/chatStore.ts:82`, `:344`), non persisté (`:460-468`). `blockStreamingNavigation` refuse toute navigation pendant une réponse et propose l'arrêt (`ConversationCanvasPrototype.tsx:1076-1090`), appelé notamment par `openChat` (`:1196`). Un emplacement unique d'arrêt joignable hors du composeur (`lib/arretDeLaReponse.ts:10-33`), que le composeur occupe tant qu'il est monté (`ChatInput.tsx:1063`).
- **Pile d'Échap.** `pushEscapeHandler` (`lib/escapeStack.ts:24-30`) ; un gestionnaire qui renvoie `false` décline et la cascade continue (`:33-37`). La cascade de la coque la consulte en premier (`ConversationCanvasPrototype.tsx:851-852`) et ferme l'espace Voix en dernier recours (`:1622`).
- **Ligne d'état de P-118.** `phrasesDeLEtat` dit, d'après la configuration lue, si les messages quittent la machine (`components/prototype/CapabilityCenter.tsx:497-513`).

### 3.3 Manques

- Pas de capture continue ni de détection de fin de parole.
- Pas de lecture de la réponse du chat, phrase par phrase.
- La lecture actuelle de l'espace Voix passe par `<audio src={blob:...}>` (`VoiceWorkspaceCanvas.tsx:134-136`, `:192`). La CSP n'a pas de `media-src` et retombe sur `default-src 'self'` (`src/frontend/src-tauri/tauri.conf.json:31`), qui ne couvre pas `blob:`. Personne ne l'a observé dans l'app packagée : la synthèse échouait en amont jusqu'à B-1410. À vérifier au lot 1.
- Aucun style parlé : les réponses sont écrites pour l'écran.
- Les confirmations d'outil vivent en mémoire (`services/tool_confirmations.py:10-12`, `:19`), ce qui compte pour la phase 2.

## 4. Conception

### 4.1 La session et son cycle de vie

**États.** Prêt, écoute, transcription, réflexion, parole, puis retour à l'écoute ; plus fin, et erreur (dite puis fin).

**Démarrage, par un geste unique** sur le bouton « Démarrer la conversation » du mode Conversation de l'espace Voix :

1. Refus si une réponse écrite est en cours (`useChatStore.getState().isStreaming`), dit et écrit : « Une réponse est en cours dans le chat. Arrête-la ou attends sa fin. »
2. Lecture de la configuration réelle (modèle, voix locale), puis vérification des accords (section 4.2). S'il en manque, une seule carte les liste ; rien ne démarre avant l'acceptation.
3. Fermeture du chat s'il est ouvert (`fermerLeChat`), pour qu'aucun composeur ne puisse viser une autre conversation pendant la session.
4. Création de la conversation neuve par `createConversation("Conversation vocale du 26/09 à 14 h 02")` (`services/api/chat.ts:276-281`). L'identifiant existe avant la première parole ; `send_message` n'a jamais à la créer (`routers/chat.py:1269-1272`), et l'interruption a toujours sa cible.
5. Prise du verrou : un petit store `sessionVocale` passe à `active` pour toute la durée de la session. `blockStreamingNavigation`, déjà appelé à treize endroits, reçoit une clause de plus : si une session vocale est active, il refuse avec « Conversation vocale en cours » et le bouton « Arrêter la conversation vocale », qui la termine. `isStreaming` et l'emplacement d'arrêt du composeur (`lib/arretDeLaReponse.ts`) ne sont pas touchés : la session n'a rien à voir avec une réponse du composeur, et c'est `isStreaming` que P-125 va transformer.
6. Annonce à voix haute des moteurs (section 4.7), puis écoute.

**Pourquoi un verrou propre plutôt que le registre de P-125.** La revue demandait de choisir (constat 6). Le registre de P-125 n'existe pas encore ; en dépendre bloquerait P-109 sans date. La garde de navigation existe et est déjà câblée partout où l'on change d'écran ; lui ajouter une clause vocale suffit. Poser `isStreaming` aurait été plus court, mais deux défauts l'écartent : un composeur visible afficherait « Arrêter » et viserait sa propre conversation (`ChatInput.tsx:1031-1048`), et la V2 de P-125 fait de `isStreaming` un état par conversation puis lève le verrou du chat à son lot 5 (`docs/plans/2026-09-26-rfc-p125-reponse-en-fond-v2.md`). **Contrat entre les deux RFC** : le lot 5 de P-125 garde la clause vocale de `blockStreamingNavigation` ; quand le registre de P-125 existera (ses lots 2 et 3), la session y inscrira ses générations sous l'identifiant de sa conversation, pour que la purge et « Travaux » l'arrêtent comme une autre réponse. Aucune autre ligne de cette RFC ne changera.

**Interruption, au clavier ou au bouton.** Un seul grand bouton, dont le libellé suit l'état : « Couper Thérèse » pendant la réflexion ou la parole, « Terminer la conversation » pendant l'écoute. Échap fait la même chose : la session pousse un gestionnaire dans la pile d'Échap (`lib/escapeStack.ts:24`) qui agit et renvoie `true` tant qu'elle vit, puis décline (`false`) quand elle est finie ; le prochain Échap ferme l'espace Voix par la cascade existante (`ConversationCanvasPrototype.tsx:1622`). Espace n'est jamais écouté (décision 21).

Couper Thérèse, c'est, dans cet ordre et une seule fois : abandonner la lecture du flux (son `AbortController`), appeler `cancelGeneration(idDeLaConversationVocale)`, abandonner les synthèses en vol, arrêter la source audio en cours, vider la file de lecture, puis revenir à l'écoute. Le moteur traite la déconnexion comme un arrêt réel (`routers/chat.py:2077-2082`) et garde une fois la partie déjà produite (`_persister_message_partiel`, `:2158-2161`), comme pour une réponse écrite arrêtée.

**Fin de session.** Par le bouton ou Échap pendant l'écoute, par la commande « fin de session », après 3 minutes sans parole (annoncé : « Je n'entends plus rien, j'arrête la conversation. »), ou au bout de 60 minutes. La fin arrête les pistes du micro, rend le verrou (`sessionVocale` inactive) et affiche « Ouvrir la conversation ».

**Fermeture de l'espace Voix.** La session vit dans un hook du composant du mode Conversation ; son nettoyage au démontage fait la fin complète ci-dessus. Fermer le panneau (croix, `collapseToolPanel('voice')`, second Échap) arrête donc la session par construction : aucune piste micro ne survit au panneau.

**Arrêt venu de Travaux.** Une génération de la session est un traitement `chat` comme une autre (`routers/chat.py:1943`) et apparaît dans Travaux au-delà de 2 s (`services/traitements.py:37-38`). Si on l'y arrête, le flux rend `cancelled` ; la session le dit (« Réponse arrêtée. ») et revient à l'écoute.

**Paramètres restent ouvrables pendant la session** : le bouton n'a pas de garde (`ConversationCanvasPrototype.tsx:2005`). Deux gestes y touchent la session, et tous deux l'arrêtent en le disant. Une révocation d'accord est traitée en section 4.2. « Effacer toutes mes données » et la restauration arrêtent d'office les réponses en cours (décision 31 du 25/09, défaut B-1425 en cours de reproduction). La session n'attend pas le mécanisme de B-1425 : `deleteAllData` (`services/api/data.ts:137`) et la restauration émettent un événement `therese:purge-demandee` avant l'appel au moteur, et la session s'arrête dès qu'elle le reçoit, sans envoyer le segment en cours. Filets, si elle le manquait : un `cancelled`, une erreur, ou un 404 sur sa conversation effacée (`routers/chat.py:1266-1268`) la terminent aussi : « La conversation a été effacée, j'arrête. »

### 4.2 Les accords, vérifiés une fois au démarrage

- **Écoute en ligne (Groq)** : finalité nouvelle `voice_conversation`, ajoutée à `CloudPurpose` (`lib/consent.ts:26`). Le libellé « Audio de la conversation vocale » s'ajoute à `PURPOSE_LABELS` (`PrivacyTab.tsx:56-61`), que le typage `Record<CloudPurpose, string>` rend obligatoire ; la révocation est déjà générique (`:106`). `transcribeAudio` et `needsVoiceCloudConsent` reçoivent la finalité en paramètre (défaut `voice`), au lieu du `'voice'` écrit en dur (`services/api/voice.ts:131`, `:155`). L'accord de la dictée ne vaut pas pour une écoute qui peut durer une heure.
- **Modèle en ligne** : finalité `llm`, adressée à `fournisseurDAccord(fournisseur, modèle)` (`lib/ollamaCloud.ts:19-23`) sur la configuration relue au démarrage. La garde du composeur (`ChatInput.tsx:558-589`) est extraite dans une fonction pure `accordRequisPourUnMessage({ fournisseur, modele, porteDesDocuments, piecesJointes })`, que le composeur et la session appellent tous deux. Un accord `llm` déjà donné pour ce fournisseur vaut : la finalité est la même (des messages envoyés à l'assistante), et la session le dit au démarrage.
- **Documents** : jamais requis. La conversation est neuve (décision 18) et la phase 1 n'a aucun outil ; aucun document ne peut y entrer. Le serveur refuse d'ailleurs `file_paths` en mode vocal (section 4.5).
- **Catégories annoncées** sur la carte : ce que tu dis (transcrit) et le contexte de la conversation vocale pour le modèle, sans la mémoire locale (section 4.5) ; l'audio de tes phrases pour Groq.
- **Révocation en cours de session.** `revokeCloudConsent` émet `CLOUD_CONSENT_REVOKED_EVENT` (`lib/consent.ts:95-104`), que le composeur écoute déjà (`ChatInput.tsx:234-235`). La session l'écoute aussi : si l'accord retiré est l'un de ceux qu'elle utilise (`voice_conversation:Groq`, ou `llm` pour son fournisseur), elle s'arrête sur-le-champ, sans envoyer le segment en cours : « Tu as retiré l'accord pour Groq, j'arrête la conversation. »

### 4.3 Capture et fin de parole

- `getUserMedia` avec les options de la dictée (`hooks/useVoiceRecorder.ts:226-233`), puis un `AudioWorklet`. Aucun fichier sur disque : l'audio vit en mémoire, par segment.
- **Le module du worklet est un fichier statique** livré avec l'application et chargé par une URL du même domaine (`new URL('./capteurMicro.worklet.js', import.meta.url)`). Jamais une URL `blob:` : `script-src` retombe sur `default-src 'self'` (`tauri.conf.json:31`). Si l'essai du lot 1 échoue sur un système, repli sur `ScriptProcessorNode` pour ce système.
- **Détecteur d'énergie à hystérésis**, module pur sur trames PCM : la parole commence après 250 ms au-dessus du seuil et finit après 800 ms de silence ; seuil calibré sur une seconde de bruit au démarrage ; segment plafonné à 60 s.
- **À l'alternat en phase 1.** Pendant la parole de Thérèse, les trames ne nourrissent pas le détecteur, et 300 ms de marge suivent la fin de la lecture, pour qu'elle ne s'entende pas dans les haut-parleurs.
- **Pendant la réflexion**, le micro écoute, mais seuls les segments de moins de 1,5 s sont transcrits, et seules les commandes y comptent (« stop », « fin de session »). Tout autre segment est ignoré, avec un son court « non pris ». Cela évite une file cachée et une transcription longue qui disputerait le processeur au modèle.
- **Silero** (`vad_filter` de faster-whisper) n'entre pas en phase 1. `collect_all("faster_whisper")` embarque les données du paquet (`backend.spec:132-136`) ; le lot 1 vérifie seulement la présence de son modèle dans le bundle, pour la phase 2.

### 4.4 Transcription

Chaque segment part vers `transcribeAudio(segment, 'segment.wav', signal, 'voice_conversation')`, dont le routage local ou en ligne reste celui de la dictée. Un segment ou une transcription vide ramène à l'écoute sans rien envoyer au modèle. Une erreur de transcription est dite, puis la session s'arrête.

**Commandes vocales**, reconnues côté interface avant tout envoi, sur la phrase entière, casse et accents repliés, ponctuation retirée : « stop » ou « arrête » (couper), « répète » (relire la dernière réponse depuis les sons déjà synthétisés, sans nouvel appel), « plus court » (nouveau tour : « Redis ta dernière réponse en une phrase. »), « fin de session » ou « termine ». Un « stop » au milieu d'une phrase n'est pas une commande.

### 4.5 Le serveur : `mode_vocal`

`ChatRequest` reçoit `mode_vocal: bool = False` (`models/schemas.py:105-119`). Quand il est vrai :

1. **Le message est du texte, rien d'autre.** Les quatre interprètes sont court-circuités : `parse_action_message` (`routers/chat.py:1324`), `parse_slash_command` (`:1459`), `parse_inline_commands` (`:1543`) et la substitution des variables `resolve_message` (`:1640-1643`, et `:1344-1347` dans la branche « produire »). Une transcription « /contact nom=X » ou « [contact: X] » ne crée rien ; elle part telle quelle au modèle.
2. **Aucun outil en phase 1, par construction.** Dans `_do_stream_response` (`:2246`), la liste d'outils est vide dès que `mode_vocal` est vrai, quelle que soit la valeur de `disable_tools` envoyée (la branche actuelle est à `:2501-2504`). Un client qui enverrait `mode_vocal=true, disable_tools=false` n'obtient toujours aucun outil.
3. **Pas de contexte mémoire en phase 1, par construction.** `_get_memory_context` (`routers/chat.py:2369-2372`) n'est pas appelé en `mode_vocal`. Le champ `include_memory` de la requête (`models/schemas.py:110`) n'est lu nulle part dans le moteur (recherche du 26/09) : la V2 ne s'appuie pas sur lui, c'est `mode_vocal` qui décide.
4. **Style parlé.** Un bloc s'ajoute à `context.system_prompt` après les blocs actuels (`:2581-2594`) : deux à quatre phrases, ni liste, ni markdown, ni lien, ni emoji ; une question de relance quand elle aide ; « à vérifier » plutôt qu'une affirmation sèche, puisque l'oral ne montre pas de sources.
5. **Refus explicites** : `file_paths` non vide ou `skill_id` présent donnent 422 ; `mode_vocal` exige `stream=true` (422 sinon), la session n'utilisant que le flux.
6. **Local en panne** : l'erreur remonte, jamais de repli en ligne (B-1071, `services/llm.py:832`).

La réponse reste écrite dans la conversation : le brainstorm se relit au retour.

### 4.6 La parole, phrase par phrase

- **Découpeur** de phrases sur le flux : ne coupe ni « M. Durand », ni « etc. », ni « 3,5 » ou « 12.5 », gère les points de suspension et les guillemets, garde une phrase coupée entre deux morceaux.
- **Nettoyeur** : retire listes et markdown, remplace un lien par « lien dans la conversation » et un bloc de code par « le code est dans la conversation », retire les emoji.
- **File de lecture, une synthèse à la fois.** La phrase suivante n'est demandée à `POST /api/voice/tts` qu'une fois la précédente reçue ; chaque requête porte un `AbortController`, abandonné à l'interruption. La première phrase est dite pendant que le modèle écrit la suite.
- **Lecture par Web Audio** : `decodeAudioData` sur les octets reçus, puis une `AudioBufferSourceNode` par phrase, que l'interruption arrête par `stop()`. Aucune URL `blob:`, aucune modification de la CSP ; le même lecteur remplace l'`<audio>` de l'espace Voix si l'essai du lot 1 confirme qu'il est bloqué.
- **Côté serveur** : la voix Piper est chargée une fois et gardée dans un cache protégé par un verrou ; les synthèses passent l'une après l'autre (un second verrou autour de `synthesize_wav`) ; le chargement du modèle Whisper prend aussi un verrou (`services/voice_local.py:239-262`). **Le WAV est produit en mémoire** (`wave.open` sur un `io.BytesIO`) et rendu par une réponse d'octets : plus aucun fichier de synthèse sur disque. C'est la parade par construction au constat 8 : la tâche de fond de `FileResponse` ne s'exécute qu'après l'envoi (`.venv/lib/python3.13/site-packages/starlette/responses.py:384-385`, starlette 1.2.1), si bien qu'un abandon client pouvait laisser un fichier.
- Une synthèse déjà lancée dans son fil n'est pas annulable ; son résultat est simplement jeté.

### 4.7 Aucun écran requis

- **Sons d'état** synthétisés par un oscillateur Web Audio, sans fichier : écoute, réflexion, erreur, non pris, fin. Au-delà de 2 s de réflexion, un son discret ; au-delà de 8 s, « Je cherche encore. »
- **Erreurs dites** en une phrase actionnable, puis arrêt propre : « Le micro ne répond plus, j'arrête la conversation. » Jamais une erreur seulement affichée.
- **Moteurs dits au démarrage**, d'après la configuration lue et jamais supposée, avec la logique de P-118 : la phrase du modèle est extraite de `phrasesDeLEtat` (`CapabilityCenter.tsx:497-513`) dans une fonction partagée, pour que la ligne d'état et la session disent la même chose. Exemple : « J'écoute en local, je réponds avec Mistral en ligne, je parle en local. »
- **Accessibilité** : annonces `aria-live` sobres (changement d'état seulement), pour ne pas couvrir la voix de Thérèse par le lecteur d'écran.
- **Emplacement** : un mode « Conversation » dans l'espace Voix, grand état lisible, grand bouton, moteurs affichés. Le bouton de dictée du composeur ne change pas.

### 4.8 Ce qui ne se fait pas à la voix

- **Phase 1 : aucun outil.** Si on demande d'envoyer un mail, Thérèse répond qu'elle ne peut pas agir à la voix et que l'idée reste dans la conversation.
- **Phase 2, après usage réel : lecture seule**, filtrée par `classe_de(nom) == LECTURE_SEULE` (`services/contexte_execution.py:26-47`), moins la recherche web (la requête part chez Brave), le navigateur et les outils MCP. Le réglage « lire le contenu des mails à voix haute » est désactivé par défaut, à cause des passagers.
- **Jamais à la voix** : toute mutation, locale ou externe. Un « oui » oral ne vaut pas confirmation : la transcription se trompe, un passager ou la radio parlent. Les actions restent des propositions à valider devant l'écran ; la phase 2 devra rendre durables les confirmations en attente (`services/tool_confirmations.py:10-12`), en lien avec P-096.

### 4.9 Latence et mémoire

Cibles, entre la fin de parole et la première syllabe : moins de 3 s en hybride, moins de 6 s en local sur la machine de référence. Le lot 1 mesure chaque étage sur un Mac récent et un PC modeste, **avec Ollama et Piper actifs en même temps**, puisqu'ils se disputent le processeur pendant la première phrase.

L'appui `services/system_resources.py` de la V1 est retiré : ce module ne lit que la RAM totale (`:76-102`) pour dimensionner le contexte Ollama, et son seul appelant est `routers/config.py:35`. La V2 ne promet aucun contrôle de mémoire libre. Le conseil repose sur la mesure : si le premier tour dépasse la cible locale, l'écran le dit une fois et propose l'hybride.

### 4.10 Les dictées sur disque

La session n'utilise jamais le greffon : `getUserMedia` garde l'audio en mémoire. Le greffon ne sert qu'au repli « alternat à la touche », sur un système où `getUserMedia` échouerait (lot 1) ; il hérite alors de B-1424 (WAV effacé après lecture). Deux résidus restent : les dictées accumulées avant B-1424, et le fichier laissé par une application fermée pendant un enregistrement (section 3.1). Tous deux relèvent de la question 20, laissée à Ludo (section 9) ; aucun lot de cette RFC n'en dépend.

## 5. Réponse à la revue

Les quatre questions posées à Ludo par la revue sont devenues les décisions 18 à 21 : 18, 19 et 21 sont tranchées et appliquées ; 20 lui reste réservée.

| # | Gravité | Constat | Réponse | Où |
|---|---|---|---|---|
| 1 | P1 | Chaque dictée laisse un WAV sur disque, hors de toute purge | Traité par B-1424 (`a1c6737a`, `1c8a1af8`) : effacement après lecture et purge RGPD, deux tests. La phrase fautive de la V1 est retirée. La session n'écrit aucun audio sur disque. Les dictées déjà conservées et le résidu d'arrêt brutal relèvent de la question 20 | 3.1, 4.3, 4.10, section 9 |
| 2 | P2 | L'accord du modèle en ligne n'est contrôlé que dans le composeur ; la session le contournerait | Garde factorisée dans `accordRequisPourUnMessage`, appelée par le composeur et par la session au démarrage, avant la première parole (décision 19) ; révocation en cours de session qui l'arrête ; mémoire locale coupée par le moteur en phase 1 ; tests « modèle en ligne sans accord : rien n'est envoyé » et « révocation : arrêt immédiat » | 4.1, 4.2, 4.5, lots 2 et 5 |
| 3 | P2 | Une « catégorie » sous `voice` serait satisfaite par l'accord de la dictée | Finalité `voice_conversation` dans `CloudPurpose`, `PURPOSE_LABELS`, la révocation, et passée en paramètre à `transcribeAudio` et `needsVoiceCloudConsent` | 4.2, lot 5 |
| 4 | P2 | Lecture par URL `blob:` non couverte par la CSP ; worklet non vérifié | Lecture par Web Audio, CSP inchangée ; worklet en fichier statique du même domaine, repli `ScriptProcessorNode` ; essai sur les trois systèmes au lot 1, avec vérification de l'`<audio>` actuel de l'espace Voix | 4.3, 4.6, lot 1, lot 4 |
| 5 | P2 | Cycle de vie face à la coque non défini ; Échap déjà consommé ; conflit avec Espace | Gestionnaire dans la pile d'Échap (premier Échap : couper ou terminer ; suivant : fermer), arrêt complet au démontage du panneau, Espace jamais écouté (décision 21) ; test « panneau fermé : aucune piste micro active » | 4.1, lot 5 |
| 6 | P2 | Flux hors composeur sans relation à `isStreaming`, au verrou, à l'identité de conversation, ni à P-125 | La session crée sa conversation (décision 18), refuse de démarrer pendant une réponse écrite, ferme le chat, tient un verrou propre lu par `blockStreamingNavigation` sans toucher `isStreaming` ; contrat écrit avec la V2 de P-125 (clause vocale gardée à son lot 5, inscription à son registre après ses lots 2 et 3) | 4.1, lot 5 |
| 7 | P3 | Le préalable « voix fr » est déjà corrigé | Retiré du lot 0, B-1410 cité avec son test | 3.1, 0 |
| 8 | P3 | Synthèses concurrentes sur une instance partagée, cache Whisper sans verrou, synthèses en vol non annulées, CPU disputé | Une synthèse à la fois (file côté client et verrou serveur), verrous de chargement, abandon des requêtes en vol, WAV en mémoire, mesure avec Ollama et Piper en parallèle | 4.6, 4.9, lots 0, 1, 4 |
| 9 | P3 | Le garde-fou de mémoire est surestimé | Appui retiré ; conseil fondé sur la latence mesurée | 4.9 |
| 10 | P3 | Commandes `/`, directives `[...]` et actions s'exécutent avant `disable_tools` | En `mode_vocal`, les quatre interprètes sont court-circuités et les outils coupés par construction ; test « transcription /contact nom=X : rien n'est créé » | 4.5, lot 2 |
| 11 | P3 | Références décalées ; lien avec P-118 et P-111 absent | Toutes les références rebasées sur `900765fb` ; phrase des moteurs partagée avec P-118 ; moteurs par défaut alignés sur P-111 (commit `64d98e79`, local proposé d'abord) | 3, 4.7, annexe |

## 6. Lots, dans l'ordre, en TDD

Règles communes à chaque lot : les tests nommés sont écrits d'abord et rougissent sur `main` ; un commit par lot, en français ; sabotage ciblé **par fonction** (découper le source entre deux `def` ou deux `function`, jamais un remplacement de chaîne globale, règle du `CLAUDE.md` du dépôt), chaque test doit rougir sous le sabotage de sa fonction ; revue adverse du diff avant fusion ; les six portes du `CLAUDE.md` sur `main` fusionné.

**Données.** La phase 1 n'a besoin d'aucune migration : la session écrit dans les tables `conversations` et `messages` existantes, les accords vivent dans le stockage local. La tête Alembic reste `b8c9d0e1f2a3`.

### Lot 0 : moteur vocal serveur (voix gardée, une synthèse à la fois, aucun fichier)

- Tests d'abord (pytest) :
  - `PiperVoice.load` n'est appelé qu'une fois pour deux synthèses (compteur sur un double) ;
  - deux synthèses lancées depuis deux fils ne chargent la voix qu'une fois et ne se chevauchent pas (horodatages d'entrée et de sortie de `synthesize_wav`) ;
  - deux transcriptions concurrentes ne chargent le modèle Whisper qu'une fois ;
  - `POST /api/voice/tts` avec `tempfile.tempdir` pointé sur un dossier de test laisse ce dossier vide, et rend un WAV valide (en-tête `RIFF`) ;
  - `voice: "fr"` reste accepté (non-régression de B-1410).
- Critère observable : dix synthèses de suite ne créent aucun fichier dans le dossier temporaire du système.
- Sabotage : retirer le cache de `synthesize_local`, retirer le verrou de chargement Whisper.

### Lot 1 : essais dans l'app packagée, trois systèmes (aucun code livré)

Une branche d'essai jetable, et un rapport `docs/qualite/2026-09-xx-p109-essais-voix.md` avec un verdict par système (macOS, Windows, Linux) :

- `getUserMedia` dans la webview packagée : accordé, refusé, absent ;
- `audioWorklet.addModule` depuis un fichier du bundle ;
- lecture par `decodeAudioData` d'un WAV de `/api/voice/tts` ;
- lecture actuelle `<audio src=blob:>` de l'espace Voix : si elle est bloquée, défaut à ficher, corrigé au lot 4 par le lecteur Web Audio ;
- présence du modèle Silero dans le bundle ;
- tableau de latence rempli (fin de parole, transcription d'une phrase, premier morceau de réponse, première phrase dite), local et hybride, Ollama et Piper actifs ensemble.

Sortie : pour chaque système, « session continue » ou « alternat à la touche avec le greffon ». Aucun lot suivant ne commence sans ce rapport.

### Lot 2 : serveur, `mode_vocal`

- Tests d'abord (pytest) :
  - en `mode_vocal`, le bloc de style est dans le prompt système ; hors `mode_vocal`, il n'y est pas ;
  - aucun outil n'est transmis au fournisseur, même avec `disable_tools=false` ; réintroduire les outils fait rougir le test ;
  - transcription « /contact nom=Durand » : aucune fiche créée, aucun message marqué déterministe, le texte part au modèle ;
  - « [contact: Durand] » et « {action: ouvrir crm} » : rien n'est créé, aucune `client_action` ;
  - `{nom}` n'est pas substitué ;
  - en `mode_vocal`, `_get_memory_context` n'est pas appelé (espion), même avec `include_memory=true` ; hors `mode_vocal`, il l'est ;
  - `file_paths` non vide, `skill_id` présent ou `stream=false` avec `mode_vocal` : 422 ;
  - fournisseur local indisponible : une erreur, aucun appel en ligne.
- Critère observable : une conversation vocale rejouée par l'API ne contient que des messages utilisateur et assistante, aucun effet de bord en base.
- Sabotage : la fonction qui décide de court-circuiter les interprètes ; la fonction qui construit la liste d'outils.

### Lot 3 : interface, détecteur de fin de parole et capture

- Tests d'abord (vitest), sur trames synthétiques : silence, bruit constant de roulage, salves de parole, parole plus longue que le plafond, calibrage du seuil, trames ignorées pendant la parole de Thérèse et pendant la marge de 300 ms.
- La capture est un module qui expose un flux de trames, doublé en test ; le worklet réel n'est exercé qu'au lot 7.
- Critère observable : sur un WAV témoin de trois phrases séparées de silences, trois segments exactement.
- Sabotage : la fonction de décision du détecteur.

### Lot 4 : interface, parole phrase par phrase

- Tests d'abord (vitest) :
  - découpeur : « M. Durand », « etc. », « 3,5 », « 12.5 », points de suspension, guillemets, phrase coupée entre deux morceaux ;
  - nettoyeur : listes, gras, liens, blocs de code, emoji ;
  - file : jamais deux requêtes de synthèse en vol ; après interruption, aucune phrase lue, requêtes en vol abandonnées, file vide ; retirer le vidage fait rougir le test ;
  - lecteur : `decodeAudioData` appelé sur les octets reçus, `stop()` sur la source à l'interruption ; aucune URL `blob:` créée (espion sur `URL.createObjectURL`).
- L'espace Voix actuel passe sur ce lecteur si le lot 1 a confirmé le blocage de l'`<audio>`.
- Sabotage : `decouperPhrases`, `nettoyerPourLaVoix`, la fonction de vidage de la file.

### Lot 5 : interface, la session

- Tests d'abord (vitest, minuteurs simulés) :
  - chaque transition de la machine à états ; transcription vide qui revient à l'écoute ; erreur dite puis arrêt ; 3 minutes sans parole ; 60 minutes ;
  - démarrage refusé si `isStreaming` est déjà vrai ;
  - `createConversation` appelé une fois, avant la première transcription ; tous les `streamMessage` portent son identifiant et `mode_vocal: true` ;
  - accords : modèle en ligne sans accord `llm` : la carte s'affiche et aucun `streamMessage` ne part ; écoute Groq sans accord `voice_conversation` : même chose, et l'accord de la dictée ne suffit pas ; accord `llm` déjà donné pour ce fournisseur : aucune carte ;
  - le composeur appelle la même `accordRequisPourUnMessage` (test du composeur existant rebranché ; saboter la fonction fait rougir les deux) ;
  - interruption : `cancelGeneration` appelé une seule fois, avec l'identifiant de la conversation vocale ;
  - verrou : `sessionVocale.active` vrai pendant toute la session et faux après ; `isStreaming` jamais modifié par la session ; `openChat` pendant la session est refusé avec « Conversation vocale en cours », et le bouton du bandeau termine la session ;
  - Échap : premier appui pendant la parole, retour à l'écoute ; pendant l'écoute, fin ; après la fin, le gestionnaire décline et la cascade ferme le panneau ;
  - panneau fermé : aucune piste micro active (`track.stop` appelé sur chaque piste), `sessionVocale.active` faux ;
  - événement `cancelled` reçu (arrêt venu de Travaux) : « Réponse arrêtée. », retour à l'écoute ;
  - révocation de `voice_conversation:Groq` ou de `llm` pour le fournisseur de la session : arrêt immédiat, aucun `transcribeAudio` ni `streamMessage` après l'événement ; révocation d'un accord sans rapport : la session continue ;
  - événement `therese:purge-demandee` pendant l'écoute : arrêt immédiat, aucun `transcribeAudio` ni `streamMessage` ensuite ; `deleteAllData` émet l'événement avant son appel au moteur ;
  - `streamMessage` rend 404 sur la conversation vocale : « La conversation a été effacée, j'arrête. », fin propre ;
  - commandes vocales : variantes, accents, casse ; « stop » au milieu d'une phrase ne compte pas ; segments de plus de 1,5 s ignorés pendant la réflexion.
- Sabotage : `accordRequisPourUnMessage`, la fonction de nettoyage de la session, la fonction de reconnaissance des commandes.

### Lot 6 : surface

- Mode « Conversation » de l'espace Voix : grand état, grand bouton au libellé suivant l'état, moteurs affichés et dits, sons d'état, libellé `voice_conversation` dans les réglages.
- Tests d'abord (vitest) : les moteurs affichés et dits sont ceux du routage réel (préférence locale, configuration du modèle) ; la phrase du modèle est la même que celle de la ligne d'état de P-118 ; annonces `aria-live` limitées aux changements d'état.
- Recette Playwright (Chromium, serveur jetable 17393) : micro simulé par un WAV (`--use-fake-device-for-media-stream`, `--use-file-for-fake-audio-capture`), transcription et modèle doublés ; un tour complet, puis une interruption, puis Échap deux fois.

### Lot 7 : recette humaine

App packagée sur les trois systèmes, avec un casque Bluetooth ; voiture à l'arrêt, puis en roulant avec un passager aux commandes ; bruit de route ; PC modeste ; tableau de latence du lot 1 refait sur la version finale.

### Phase 2, non planifiée

Lecture seule filtrée par classe d'effet, interruption en parlant après un essai d'annulation d'écho, confirmations durables (P-096), réglage des mails lus à voix haute. Elle fera l'objet d'un complément de RFC après usage réel.

## 7. Risques restants

- **Latence locale.** Plusieurs secondes par tour sur un portable, défavorable face à Perplexity. Parades : phrase par phrase, sons d'attente, hybride proposé sur mesure.
- **Webview.** Si `getUserMedia` manque sur un système, ce système n'aura que l'alternat à la touche, qui demande un geste : l'usage mains libres n'y existera pas. Le lot 1 le dira avant tout code d'interface.
- **Écho et faux déclenchements** (haut-parleurs, radio, passagers). L'alternat et le seuil calibré les réduisent, sans les supprimer.
- **Mémoire vive** : Whisper, Piper et un modèle local ensemble. Aucun contrôle de mémoire libre n'est promis.
- **Confidentialité** : audio continu chez Groq en hybride, sous un accord distinct ; contenus entendus par les passagers en phase 2.
- **Sécurité routière** : la session n'exige ni regard ni geste, mais l'application tourne sur un ordinateur ; l'usage au volant ne doit pas être promu (section 9).
- **Assurance orale** : une erreur dite avec aplomb, sans sources visibles. Parades : style « à vérifier » et conversation relisible.
- **Verrou long** : pendant une session, tout changement d'écran est refusé. C'est voulu ; le bandeau dit pourquoi et propose l'arrêt.
- **Contrat avec P-125** : si le lot 5 de sa V2 (`docs/plans/2026-09-26-rfc-p125-reponse-en-fond-v2.md`) retirait la clause vocale de `blockStreamingNavigation`, la session perdrait sa protection contre un changement d'écran. Le test « `openChat` refusé pendant une session » du lot 5 d'ici le rendrait rouge ; ce contrat est à reporter dans la V2 de P-125 à sa prochaine reprise.
- **Dictées déjà conservées** chez les testeurs, tant que Ludo n'a pas tranché la question 20.

## 8. Plan de tests, récapitulatif

Serveur : lots 0 et 2 (pytest). Interface : lots 3 à 6 (vitest). Bout en bout : lot 6 (Playwright, micro simulé). Recette humaine : lots 1 et 7. Chaque fonction de garde (accords, court-circuit des interprètes, liste d'outils, nettoyage de session, vidage de file) a un test qui rougit sous son sabotage.

## 9. Laissé à Ludo

**Question 20 : les dictées déjà conservées chez les testeurs.** B-1424 empêche toute nouvelle accumulation ; restent les WAV antérieurs, parfois lourds (un fichier de 1,5 Go relevé par la revue sur le Mac de Ludo), et le fichier laissé par une application fermée pendant une dictée. Deux options :

- **Option A, purge à la mise à jour** (recommandation du 25/09) : au premier démarrage de la version corrigée, THÉRÈSE efface tout le dossier `tauri-plugin-mic-recorder`, puis le vide à chaque démarrage (ce qui couvre aussi l'arrêt brutal). Annonce dans les notes de version et sur Discord. Test : dossier peuplé de trois WAV, démarrage, dossier vide.
- **Option B, rien d'effacé d'office** : les réglages de confidentialité affichent « N dictées conservées par une ancienne version, X Mo » avec un bouton « Effacer » ; au démarrage, seuls les fichiers dont l'horodatage du nom (`AAAAMMJJHHMMSS.wav`) est postérieur au premier lancement de la version corrigée sont effacés, ce qui couvre l'arrêt brutal sans toucher aux anciens. Test : un ancien et un récent, démarrage, seul le récent disparaît.

Aucun lot de cette RFC n'attend cette réponse ; le lot qui la met en œuvre s'ajoutera après.

**Annonces publiques.** Le texte des notes de version et du message Discord qui présenteront la conversation vocale, en particulier la phrase sur l'usage en voiture, relève de Ludo. La recommandation technique est de ne jamais la présenter comme un usage au volant.

## Annexe : appuis dans le code (`900765fb`)

| Sujet | Référence |
|---|---|
| Effacement du WAV de dictée (B-1424) | `hooks/useVoiceRecorder.ts:105-116`, `:204-205` |
| Purge des dictées (B-1424) | `services/api/data.ts:123-135`, `:144` |
| Création du WAV au démarrage par le greffon | `~/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/tauri-plugin-mic-recorder-2.0.0/src/commands.rs:136-139`, `:208` |
| Permission d'effacement | `src/frontend/src-tauri/capabilities/default.json:138-144` |
| Voix « fr » acceptée (B-1410) | `services/voice_local.py:99`, `tests/test_b1410_voix_fr_acceptee.py` |
| Finalités d'accord | `lib/consent.ts:26`, `:40-42`, `:82-88` |
| Finalité `voice` en dur | `services/api/voice.ts:131`, `:155` |
| Libellés et révocation | `components/settings/PrivacyTab.tsx:56-61`, `:106`, `:439-443` |
| Garde d'accord du composeur | `components/chat/ChatInput.tsx:558-589`, `lib/ollamaCloud.ts:19-23` |
| Arrêt du composeur | `components/chat/ChatInput.tsx:1031-1048`, `:1063` |
| Emplacement d'arrêt | `lib/arretDeLaReponse.ts:10-33` |
| Verrou de réponse | `stores/chatStore.ts:82`, `:344` ; `components/prototype/ConversationCanvasPrototype.tsx:1076-1090`, `:1196` |
| Pile et cascade d'Échap | `lib/escapeStack.ts:24-37` ; `ConversationCanvasPrototype.tsx:851-852`, `:1591-1628` |
| Espace Voix | `components/prototype/VoiceWorkspaceCanvas.tsx:134-136`, `:174`, `:192` ; `ConversationCanvasPrototype.tsx:1526-1533`, `:2497-2507` |
| CSP | `src/frontend/src-tauri/tauri.conf.json:31` |
| Ligne d'état P-118 | `components/prototype/CapabilityCenter.tsx:497-513` |
| API du chat | `services/api/chat.ts:67`, `:147`, `:276-281`, `:400-404` |
| Requête de chat | `models/schemas.py:105-119` |
| Création implicite de conversation | `routers/chat.py:1269-1272` |
| Interprètes du message | `routers/chat.py:1324`, `:1344-1347`, `:1459`, `:1543`, `:1640-1643` |
| Outils et prompt système | `routers/chat.py:2246`, `:2483`, `:2501-2504`, `:2581-2594` |
| Annulation serveur | `routers/chat.py:1000` |
| Classes d'effet | `services/contexte_execution.py:26-47` |
| Confirmations en mémoire | `services/tool_confirmations.py:10-12`, `:19` |
| Pas de bascule en ligne (B-1071) | `services/llm.py:832` |
| Moteurs vocaux | `routers/voice.py:55-155`, `:215-279`, `:296-334` ; `services/voice_local.py:239-298` |
| Tâche de fond de `FileResponse` | `.venv/lib/python3.13/site-packages/starlette/responses.py:384-385` (starlette 1.2.1) |
| Embarquement de la voix locale | `src/backend/backend.spec:126-141` |
| RAM totale seulement | `services/system_resources.py:76-102`, `routers/config.py:35` |
