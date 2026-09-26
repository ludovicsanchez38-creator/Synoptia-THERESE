# RFC P-109 V3 : une conversation vocale de bout en bout, mains libres

Rédigé le 26/09/2026. Remplace la V2 (`docs/plans/2026-09-26-rfc-p109-conversation-vocale-v2.md`), refusée par la revue adverse du 26/09 (constats 1 à 14 ; fichier de travail de l'orchestrateur, hors dépôt : `revue-v2-p109-p110.md`). Les décisions 18, 19 et 21 du 25/09 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`) restent des faits ; la question 20 reste à Ludo. Règle de délégation du 25/09 appliquée : chaque choix de conception est tranché ici avec sa raison, sauf effacement définitif de données d'utilisateurs, annonces publiques et marque. Aucun code avant une nouvelle revue adverse de ce document.

Base de code relue : `main` à `a3c98b74` (26/09/2026). La reprise a commencé à `66b78788` ; `main` a reçu pendant ce temps dix-huit correctifs de l'orchestrateur (B-1483 à B-1505), dont deux touchent cette RFC : B-1495 (`include_memory` honoré) et B-1494 (aucune réponse écrite dans une conversation supprimée). Tous les numéros de ligne ont été revérifiés à `a3c98b74`, lus par `git show a3c98b74:`. Chemins relatifs à `src/backend/app/` (serveur) et `src/frontend/src/` (interface), sauf mention. Aucune migration : la tête Alembic n'est pas touchée par cette RFC.

## Réponse à la revue de la V2, en tête

Chaque constat a été relu au code avant d'être accepté. Aucun n'est faux. Deux vont plus loin une fois relus : le constat 4 manquait un sixième interprète du message, et le constat 10 cachait un débordement sur disque propre au décodeur de formulaires.

| # | Gravité | Constat | Verdict | Traitement | Où |
|---|---|---|---|---|---|
| 1 | P2 | L'accord du modèle n'est vérifié qu'au démarrage, alors que le fournisseur peut changer en cours de session, et le disjoncteur bascule vers un autre fournisseur en ligne | Accepté : `get_llm_service()` relit la configuration globale à chaque tour (`routers/chat.py:2379`), singleton à bascule autorisée (`services/llm.py:1210-1216`, `:824`, `:849-856`) | Accord vérifié avant chaque tour ; destination figée au démarrage et comparée par le serveur (`fournisseur_attendu`, `modele_attendu`, 409 sinon) ; service du tour construit sans bascule ; destination de l'écoute figée elle aussi ; arrêt dit sur changement de modèle | 4.1, 4.2, 4.5, lots 2 et 5 |
| 2 | P2 | L'arrêt sur « Effacer toutes mes données » ne protège pas l'effacement : la coupure fait écrire le partiel en concurrence avec la purge | Accepté à la base de la V2. Depuis, B-1494 (commit `6f927313`, arrivé pendant cette reprise) fait passer toute réponse, partiel compris, par `_ecrire_reponse` (`routers/chat.py:2162-2181`), qui vérifie l'existence de la conversation sous le verrou d'écriture de SQLite ; la purge efface tout en une transaction (`routers/data.py:632-700`). Reste ouvert : le message de l'utilisateur, écrit hors de ce point (`routers/chat.py:1307-1318`), et la génération qui continue après la purge | Dépendance au lot 1 de P-125 gardée pour ce qui reste (409 pendant une purge, arrêt d'office) ; test moteur en `mode_vocal` | 4.1, lot 5, section 1 bis |
| 3 | P2 | Le gestionnaire d'Échap de la session passe avant Paramètres, le Board, la palette et les centres | Accepté (`components/prototype/ConversationCanvasPrototype.tsx:851-862`, `:1609-1612`) | Plus de gestionnaire dans la pile : la session s'insère dans la cascade juste avant `voiceOpen` ; toute surface ouverte se ferme d'abord | 4.1, lot 5 |
| 4 | P2 | `/fichier` et `/analyse` lisent un fichier local et le joignent au contexte | Accepté, et étendu : la syntaxe `{{action: …}}` résout aussi un skill et déclenche l'auto-exécution (`routers/chat.py:2345-2366`, `:2900-2944`) | Sept interprètes recensés depuis le code et coupés en `mode_vocal` ; tests par interprète | 4.5, lot 2 |
| 5 | P3 | Le test « dossier temporaire vide » est vert sur `main` | Accepté : la tâche de fond de `FileResponse` s'exécute dans l'appel ASGI (`starlette/responses.py:382-383`, starlette 1.2.1), que le client de test attend | Tests par espions (`NamedTemporaryFile` jamais appelé, `wave.open` sur un `BytesIO`, réponse d'octets) ; sabotage de la fonction qui produit le WAV en mémoire | 4.6, lot 0 |
| 6 | P3 | `include_memory` n'est lu nulle part | Accepté à la base de la V2 ; défaut fiché à part (B-1495) et corrigé par l'orchestrateur pendant cette reprise (commit `d80d4406`) : le champ est honoré sur les deux chemins (`routers/chat.py:1738-1741`, `:2396-2399`) | B-1495, prérequis du lot 2, est satisfait ; `mode_vocal` force l'exclusion par cette branche | 1 bis, 4.5 |
| 7 | P3 | Le prompt système emporte le profil et jusqu'à 10 000 caractères de THERESE.md | Accepté (`services/llm.py:506-517`, `:551`, `:890`) | Profil et consignes personnelles nommés sur la carte ; mesure au lot 1 avec un THERESE.md réel | 4.2, 4.9, lot 1 |
| 8 | P3 | Une extraction d'entités part en fond à chaque tour | Accepté (`routers/chat.py:2979-2986`) | Aucune extraction en `mode_vocal` ; test par espion | 4.5, lot 2 |
| 9 | P3 | Sans outil, Gemini ajoute l'ancrage Google Search | Accepté (`services/providers/gemini.py:263-283`) | `enable_grounding=False` en `mode_vocal` (paramètre existant, `services/llm.py:961`) ; test sur le corps de la requête | 4.5, lot 2 |
| 10 | P3 | Chaque segment transcrit passe par un fichier temporaire du moteur | Accepté (`routers/voice.py:87-99`, `:150-155`, `:260-277`), et étendu : au-delà de 1 Mio, le décodeur de formulaires de Starlette déborde lui aussi sur disque (`starlette/formparsers.py:126`) | Transcription depuis la mémoire sur les deux routes ; segments de 30 s au plus en WAV 16 kHz mono, sous le seuil de débordement ; phrase fautive corrigée | 4.3, 4.4, 4.10, lot 0 |
| 11 | P3 | Deux tests nommés ne rougiront pas sur `main` | Accepté | Test B-1071 étiqueté non-régression ; test Whisper avec constructeur doublé lent et barrière entre deux fils | lots 0 et 2 |
| 12 | P3 | Le module du worklet peut être inliné en `data:` par Vite | Accepté (aucun `assetsInlineLimit`, `src/frontend/vite.config.ts`) | Worklet dans `public/`, chargé par une URL absolue du même domaine, sans passer par Vite ; le lot 1 éprouve exactement ce chargement | 4.3, lot 1 |
| 13 | P3 | La conversation créée par l'API n'entre pas dans le store ; « Ouvrir la conversation » suppose le lot 6 de P-125 ; la clause vocale n'est pas dans la V2 de P-125 | Accepté | La session ajoute elle-même sa conversation au store et l'ouvre ; la clause vocale devient un contrat à reporter dans P-125 avant de coder l'une ou l'autre | 1 bis, 4.1, lot 5 |
| 14 | P3 | `cancelGeneration` sans attente : une annulation tardive arrêterait le tour suivant | Accepté (`routers/chat.py:1001-1042` résout la génération active la plus récente de la conversation) | Annulation **par génération** (`annulerTraitement`, identifiant reçu par l'événement `generation`), attendue avant de rouvrir l'écoute ; plus jamais `cancelGeneration(conversation)` | 4.1, lot 5 |

## 0. Ce qui change depuis la V2

- **La destination est figée au démarrage et le serveur la vérifie à chaque tour** ; aucun tour ne peut partir chez un fournisseur que la carte n'a pas nommé, ni par un changement de réglage, ni par le disjoncteur.
- **Sept interprètes du message** sont coupés en `mode_vocal`, recensés depuis le code et non plus quatre.
- **Échap passe par la cascade de la coque**, pas par la pile : la surface au premier plan se ferme toujours d'abord.
- **L'interruption vise une génération**, jamais « la génération courante d'une conversation ».
- **Aucun fichier audio nommé** n'est écrit par la session, transcription comprise, et les segments restent sous le seuil où Starlette déborderait sur disque.
- **La purge pendant une réponse vocale** s'appuie sur B-1494, arrivé pendant cette reprise, pour les réponses, et sur le lot 1 de P-125, écrit comme dépendance, pour le reste.
- **La conversation vocale entre au store** par la session elle-même ; « Ouvrir la conversation » ne dépend plus de P-125.

## 1. Le besoin

Dr_logic-3D (fil Discord du 25/09) réfléchit à voix haute en conduisant, avec Perplexity en mode vocal. Il voudrait la même chose avec THÉRÈSE : parler, entendre la réponse, relancer, sans regarder d'écran. Aujourd'hui THÉRÈSE sait dicter et lire un texte, mais ne converse pas. Trois exigences en découlent : une boucle continue (fin de parole détectée, réponse dite, écoute reprise), l'interruption, et aucun écran requis pendant la conversation.

**La réserve de la V1 tient toujours.** THÉRÈSE est une application de bureau ; « en voiture » veut dire un ordinateur portable allumé dans l'habitacle. Le Code de la route interdit de placer dans le champ de vision du conducteur un écran allumé qui n'aide pas à la conduite ([article R412-6-2](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025111520)) et de porter à l'oreille un dispositif qui émet du son ([article R412-6-1](https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000030800800&cidTexte=LEGITEXT000006074228&dateTexte=20150628)). La cible est le bureau mains libres ; la voiture reste un usage toléré sur portable, écran hors de vue, son par les haut-parleurs, et l'application ne le promeut pas.

## 1 bis. Prérequis et dépendances

| Élément | Nature | Ce qui en dépend | Pourquoi |
|---|---|---|---|
| **B-1495** : `include_memory` honoré, corrigé à part par l'orchestrateur | Prérequis, **satisfait** (commit `d80d4406`, `routers/chat.py:2396-2399`) | Lot 2 | `mode_vocal` force l'exclusion de la mémoire par cette branche au lieu d'ouvrir un second chemin |
| **B-1494** : aucune réponse écrite dans une conversation disparue | Fait acquis (commit `6f927313`, `routers/chat.py:2162-2181`) | Lot 5 | Le partiel qu'une coupure fait écrire pendant une purge est soit effacé par elle, soit refusé : la purge efface tout en une transaction (`routers/data.py:632-700`), et `_ecrire_reponse` vérifie la conversation sous le verrou d'écriture |
| **Lot 1 de P-125** (`docs/plans/2026-09-26-rfc-p125-reponse-en-fond-v2.md`, § 5.1 et lot 1) | Dépendance | Lot 5 | Ce que B-1494 ne couvre pas : le message de l'utilisateur, écrit par `send_message` hors de `_ecrire_reponse` (`routers/chat.py:1307-1318`) après une vérification de la conversation (`:1266-1268`) qu'une purge peut devancer, et la génération qui continue de produire après l'effacement. Le lot 1 de P-125 refuse tout envoi pendant une purge (409) et arrête d'office les générations en attendant leur état terminal ; la session, seule, ne le peut pas (constat 2) |
| **Clause vocale dans le lot 5 de P-125** | Contrat à reporter | Lot 5 | La V2 de P-125 écrit : « La garde ne retient plus que la saisie modifiée (B-978) et les interdits du § 5.7 » (sa ligne 245). Cette V3 ne peut pas modifier P-125 : le report de la clause `sessionVocaleBloqueLaNavigation()` dans le lot 5 de P-125 est une condition pour coder l'une ou l'autre, à porter par l'orchestrateur |
| Lot 6 de P-125 | Plus requis | Rien | La session ajoute elle-même sa conversation au store et l'ouvre (section 4.1). Si le lot 6 arrive, il peut reprendre la même fonction |

## 2. Décisions tranchées

| Sujet | Décision | Source |
|---|---|---|
| Conversation | Neuve à chaque session : aucun document ni projet embarqué sans le voir | Décision 18 du 25/09 |
| Accord pour le modèle en ligne | Demandé une fois, au démarrage, avant la première parole ; revérifié avant chaque tour sans nouvelle question | Décision 19 du 25/09, précisée ici (constat 1) |
| Arrêt au clavier | Échap et le grand bouton seulement | Décision 21 du 25/09 |
| Destination du modèle et de l'écoute | Figées au démarrage ; tout changement arrête la session en le disant ; le serveur refuse un tour dont la destination diffère | Tranché ici (constat 1) : une révocation n'est pas le seul chemin par lequel la destination change |
| Disjoncteur | Aucune bascule vers un autre fournisseur en `mode_vocal`, comme le Board | Tranché ici (constat 1) |
| Cible | Le bureau mains libres ; la voiture reste tolérée, jamais promue | Tranché en V2, gardé |
| Moteurs par défaut | Écoute locale si la voix locale est prête, sinon Groq avec accord ; modèle configuré ; voix Piper toujours locale | Tranché en V2, gardé |
| Outils | Phase 1 sans aucun outil ; phase 2 en lecture seule, après usage réel | Tranché en V2, gardé |
| Interruption en parlant | Phase 2, après un essai d'annulation d'écho | Tranché en V2, gardé |
| Accord de l'écoute en ligne | Finalité nouvelle `voice_conversation` | Tranché en V2, gardé |
| Mémoire locale | Exclue en phase 1, par `mode_vocal`, sur la branche de B-1495 | Tranché ici (constat 6) |
| Profil et THERESE.md | Gardés dans le prompt, nommés sur la carte, mesurés au lot 1 | Tranché ici (constat 7) : ils font que la réponse est celle de l'utilisatrice |
| Propriété du flux | Verrou propre à la session, lu par la garde de navigation ; `isStreaming` n'est pas touché | Tranché en V2, gardé ; contrat avec P-125 écrit (section 1 bis) |
| Interruption | Par identifiant de génération, attendue | Tranché ici (constat 14) |
| Échap | Dans la cascade de la coque, juste avant la fermeture de l'espace Voix | Tranché ici (constat 3) |
| Segments | 30 s au plus, WAV 16 kHz mono 16 bits, transcrits par tranches pour une parole plus longue | Tranché ici (constat 10) |
| Lecture audio | Web Audio (`decodeAudioData`), aucune URL `blob:`, CSP inchangée | Tranché en V2, gardé |
| Dictées déjà conservées | **Laissé à Ludo** (section 10) | Réservé le 25/09 |

## 3. Ce qui existe à `a3c98b74`

### 3.1 Faits réglés avant cette RFC

- **B-1410** : la route de synthèse accepte `voice: "fr"` (`services/voice_local.py:99`), test `tests/test_b1410_voix_fr_acceptee.py`.
- **B-1424, volet dictée** : le WAV du greffon est effacé dès qu'il a été lu (`hooks/useVoiceRecorder.ts:105-116`, appelé à `:204-205`).
- **B-1424, volet purge** : « Effacer toutes mes données » vide le dossier `tauri-plugin-mic-recorder` après la purge du moteur (`services/api/data.ts:123-135`, appelé à `:144`).
- **Ce que B-1424 ne couvre pas** : le greffon crée le fichier au démarrage de l'enregistrement et le chemin n'est connu qu'à l'arrêt ; une application fermée pendant une dictée laisse un WAV. Les dictées accumulées avant la correction restent aussi en place (question 20, section 10).

### 3.2 Points d'appui

- **Dictée au clic.** Chemin navigateur : `getUserMedia` avec annulation d'écho et réduction de bruit (`hooks/useVoiceRecorder.ts:226-233`).
- **Routage de la transcription.** Préférence respectée sans repli silencieux (`services/api/voice.ts:84-123`) ; `transcribeAudio` refuse l'envoi à Groq sans accord, contrôlé en dur sur la finalité `voice` (`:131`, `:155`).
- **Consentement par finalité et par fournisseur.** `CloudPurpose` (`lib/consent.ts:26`), clé `finalité:fournisseur` (`:40-42`), `hasCloudConsent` (`:82-88`), révocation qui émet `CLOUD_CONSENT_REVOKED_EVENT` (`:95-104`). Libellés et révocation dans les réglages (`components/settings/PrivacyTab.tsx:56-61`, `:106`).
- **Garde d'accord du composeur.** Finalité `documents` ou `llm`, adressée à la destination réelle (`components/chat/ChatInput.tsx:558-589`, `lib/ollamaCloud.ts:19-23`) ; catégories annoncées : message, contexte de conversation, mémoire locale (`ChatInput.tsx:576-579`). Le composeur recharge la configuration sur `therese:llm-config-changed` (`:240`), émis par les Paramètres (`components/settings/SettingsModal.tsx:398`, `:545`, `:566`), la mise en route (`components/onboarding/CompleteStep.tsx:72`) et le sélecteur du composeur (`ChatInput.tsx:253`).
- **Service du modèle.** `get_llm_service()` rend un singleton à bascule autorisée (`services/llm.py:1210-1216`) ; `get_llm_service_for_provider(…, bascule_circuit=…)` sert le Board (`:1224-1229`) ; sans bascule, le fournisseur d'origine est tenté même disjoncteur ouvert (`:824`) ; un fournisseur local n'en cherche aucun (B-1071, `:832-841`) ; un fournisseur en ligne bascule vers le premier autre disponible (`:849-856`). Le prompt système porte le profil et jusqu'à 10 000 caractères de THERESE.md (`:506-517`, `:551`), repris par `prepare_context` (`:890`).
- **Moteur du chat.** `ChatRequest` (`models/schemas.py:105-119`). `_do_stream_response` (`routers/chat.py:2271`) relit le service à chaque tour (`:2379`), appelle `_get_memory_context` sauf si `include_memory` est faux (B-1495, `:2396-2399`), transmet les outils à `stream_response_with_tools` sans `enable_grounding` (`:2661`), puis lance l'extraction d'entités en fond (`:2979-2986`). L'annulation par conversation vise la génération active la plus récente (`:1001-1042`) ; le flux émet d'abord un événement `generation` portant l'identifiant du traitement (`:1985-1994`), que l'interface connaît (`services/api/chat.ts:67-72`) ; l'arrêt d'un traitement par son identifiant existe (`routers/processing_tasks.py:23`, `services/api/processingTasks.ts:44-47`). La déconnexion du client arrête la génération (`routers/chat.py:2080-2087`) et garde une fois le partiel (`_persister_message_partiel`, `:2184-2215`), écrit comme toute réponse par `_ecrire_reponse`, qui ne l'écrit que si la conversation existe encore (B-1494, `:2162-2181`).
- **Moteurs vocaux.** Groq écrit un fichier temporaire avant l'envoi (`routers/voice.py:87-99`) et l'efface en `finally` (`:150-155`) ; la voix locale fait de même (`:260-277`). Whisper local gardé dans un dictionnaire sans verrou (`services/voice_local.py:239-265`) ; Piper rechargé à chaque synthèse (`:292`) et écrit dans un fichier (`routers/voice.py:313-327`) effacé par la tâche de fond de `FileResponse`, qui s'exécute dans l'appel ASGI (`.venv/lib/python3.13/site-packages/starlette/responses.py:382-383`). Au-delà de 1 Mio, un fichier envoyé déborde du tampon mémoire du décodeur de formulaires (`starlette/formparsers.py:126`). Versions verrouillées : faster-whisper 1.2.1, piper-tts 1.4.2 (`uv.lock`).
- **Espace Voix de la coque.** Ouvert à `ConversationCanvasPrototype.tsx:2497-2507`, fermé par `collapseToolPanel` (`:1526-1533`) ; lecture actuelle par `<audio src={blob:…}>` (`components/prototype/VoiceWorkspaceCanvas.tsx:134-136`, `:192`).
- **Verrou et navigation.** `isStreaming` (`stores/chatStore.ts:82`, `:344`) ; `blockStreamingNavigation` refuse toute navigation pendant une réponse (`ConversationCanvasPrototype.tsx:1076-1090`), appelé notamment par `openChat` (`:1196`).
- **Échap.** `consommeEchapUnifie` exécute la pile avant Paramètres, contact, projet, Board, raccourcis, bibliothèque, Atelier et Actions (`ConversationCanvasPrototype.tsx:851-862`) ; la cascade examine ensuite palette, centres, tiroir, chat, vues, panneaux d'outils, puis l'espace Voix (`:1609-1622`). Paramètres laissent Échap à la cascade (`components/settings/SettingsModal.tsx:102-105`) ; la pile ne consulte que son gestionnaire du dessus (`lib/escapeStack.ts:33-37`).
- **Store du chat.** `setConversations`, `loadConversation`, `setConversationMessages` (`stores/chatStore.ts:114`, `:96`, `:116`) ; conversions depuis l'API (`hooks/useConversationSync.ts:28`, `:105`) ; `getConversation` et `getConversationMessages` (`services/api/chat.ts:272`, `:309`).
- **Ligne d'état de P-118.** `phrasesDeLEtat` (`components/prototype/CapabilityCenter.tsx:497-513`).
- **Fichiers servis tels quels.** `src/frontend/public/` sert déjà `demarrage-filet.js` ; la CSP n'a pas de `script-src` et retombe sur `default-src 'self'` (`src/frontend/src-tauri/tauri.conf.json:31`).

### 3.3 Manques

- Pas de capture continue ni de détection de fin de parole ; pas de lecture de la réponse phrase par phrase ; aucun style parlé.
- La lecture `<audio src=blob:>` de l'espace Voix n'a jamais été observée dans l'app packagée ; `default-src 'self'` ne couvre pas `blob:`. À vérifier au lot 1.
- Les confirmations d'outil vivent en mémoire (`services/tool_confirmations.py:10-12`, `:19`), ce qui compte pour la phase 2.

## 4. Conception

### 4.1 La session et son cycle de vie

**États.** Prêt, écoute, transcription, réflexion, parole, puis retour à l'écoute ; plus fin, et erreur (dite puis fin).

**Démarrage, par un geste unique** sur « Démarrer la conversation » du mode Conversation de l'espace Voix :

1. Refus si une réponse écrite est en cours (`useChatStore.getState().isStreaming`) : « Une réponse est en cours dans le chat. Arrête-la ou attends sa fin. »
2. Lecture de la configuration réelle (`getLLMConfig`, préférence de voix locale), puis **figement des deux destinations** de la session : `{ fournisseur, modele }` du modèle et moteur d'écoute (`local` ou `groq`). Vérification des accords (section 4.2) ; s'il en manque, une seule carte les liste ; rien ne démarre avant l'acceptation.
3. Fermeture du chat s'il est ouvert (`fermerLeChat`).
4. Création de la conversation neuve par `createConversation("Conversation vocale du 26/09 à 14 h 02")` (`services/api/chat.ts:276-281`). Elle existe avant la première parole : tous les tours y écrivent, et la purge comme la suppression se détectent par un 404.
5. Prise du verrou : un petit store `sessionVocale` passe à `active`. `blockStreamingNavigation` reçoit une clause distincte, `sessionVocaleBloqueLaNavigation()`, qui refuse avec « Conversation vocale en cours » et le bouton « Arrêter la conversation vocale ». `isStreaming` et l'emplacement d'arrêt du composeur ne sont pas touchés. La clause est une fonction à part pour que le lot 5 de P-125, qui réécrit la condition de flux, la garde telle quelle (section 1 bis).
6. Annonce à voix haute des moteurs (section 4.7), puis écoute.

**Interruption, au clavier ou au bouton.** Un seul grand bouton, dont le libellé suit l'état : « Couper Thérèse » pendant la réflexion ou la parole, « Terminer la conversation » pendant l'écoute. Espace n'est jamais écouté (décision 21).

**Échap, dans la cascade** (constat 3). La session ne pousse **aucun** gestionnaire dans la pile d'Échap. La cascade de la coque (`ConversationCanvasPrototype.tsx:1592-1624`) change sa branche de l'espace Voix (`:1622`) : `else if (voiceOpen) { if (!echapPourLaSessionVocale()) collapseToolPanel('voice'); }`, où `echapPourLaSessionVocale()` lit le store `sessionVocale` et, s'il est actif, coupe ou termine selon l'état puis rend `true`. Par construction, tout ce que la cascade examine avant, pile d'Échap, tiroir focalisé, Paramètres, contact, projet, Board, raccourcis, bibliothèque, Atelier, Actions, palette, centres, chat, vues et autres panneaux d'outils, se ferme d'abord : Échap dans Paramètres ferme Paramètres, et la session continue. Le tableau de dépendances de l'effet (`:1626`) gagne l'accès au store. Pourquoi pas un gestionnaire qui décline quand une surface est ouverte : les drapeaux de la palette et des centres sont des états locaux de la coque, invisibles depuis l'espace Voix, et la liste se périmerait au premier écran ajouté.

**Couper Thérèse** (constat 14), dans cet ordre et une seule fois : abandonner la lecture du flux (son `AbortController`) ; si l'événement `generation` de ce tour a été reçu, appeler `annulerTraitement(generationId)` (`services/api/processingTasks.ts:44-47`) et **attendre** sa réponse, au plus 3 s ; abandonner les synthèses en vol ; arrêter la source audio ; vider la file de lecture ; puis seulement revenir à l'écoute. L'annulation désigne ce tour et lui seul : une réponse tardive ne peut pas arrêter le tour suivant, ce que `cancelGeneration(conversation)` permettait en résolvant « la génération active la plus récente » (`routers/chat.py:1017-1027`). Si l'événement n'est pas encore arrivé, l'abandon du flux suffit : la déconnexion arrête la génération (`:2080-2087`). La session n'appelle jamais `cancelGeneration`.

**Fin de session.** Par le bouton ou Échap pendant l'écoute, par la commande « fin de session », après 3 minutes sans parole (annoncé), au bout de 60 minutes, ou sur l'un des arrêts de la section suivante. La fin arrête les pistes du micro, rend le verrou, **ajoute la conversation au store** et affiche « Ouvrir la conversation ».

**La conversation au store** (constat 13). `ajouterConversationServeurAuStore(id)` (`lib/conversationVocale.ts`) : `getConversation(id)` puis `formatConversationFromResponse` (`hooks/useConversationSync.ts:105`), fusionnée dans la liste par `setConversations` (`stores/chatStore.ts:114`) sans doublon ; puis `getConversationMessages(id)`, `formatMessageFromResponse` (`useConversationSync.ts:28`) et `setConversationMessages` (`chatStore.ts:116`). « Ouvrir la conversation » appelle cette fonction puis `loadConversation(id)` (`chatStore.ts:96`) et ouvre le chat. L'ajout se fait à la fin, et non au démarrage, pour que le tiroir ne propose pas de supprimer une conversation en cours ; une synchronisation serveur qui la ferait apparaître plus tôt reste couverte par le filet du 404.

**Fermeture de l'espace Voix.** La session vit dans un hook du mode Conversation ; son nettoyage au démontage fait la fin complète. Fermer le panneau l'arrête donc par construction : aucune piste micro ne survit au panneau.

**Arrêts venus d'ailleurs**, tous dits en une phrase, sans envoyer le segment en cours :

- **Travaux** : une génération de la session y apparaît comme un traitement `chat` ; arrêtée là, le flux rend `cancelled` ; la session dit « Réponse arrêtée. » et revient à l'écoute.
- **Révocation d'un accord** qu'elle utilise (`CLOUD_CONSENT_REVOKED_EVENT`, `lib/consent.ts:95-104`) : arrêt, « Tu as retiré l'accord pour Groq, j'arrête la conversation. »
- **Changement de modèle** (`therese:llm-config-changed`) : la session relit la configuration ; si `{ fournisseur, modele }` diffère de la destination figée, arrêt, « Le modèle a changé dans les réglages, j'arrête la conversation vocale. » Le serveur fait la même comparaison à chaque tour (section 4.5), si bien qu'un changement passé par un autre chemin que l'événement est refusé quand même.
- **Changement du moteur d'écoute** : `transcribeAudio` reçoit le moteur figé et refuse de transcrire si le routage courant en désigne un autre (section 4.4) ; arrêt, « Le réglage de la voix a changé, j'arrête. »
- **Purge ou restauration** : `deleteAllData` (`services/api/data.ts:137-146`) et la restauration émettent `therese:purge-demandee` avant l'appel au moteur, et la session s'arrête dès qu'elle le reçoit. **Ce signal est une politesse, pas la garantie** (constat 2) : la coupure qu'il provoque fait écrire le partiel par le moteur (`routers/chat.py:2184-2215`), en concurrence avec la purge, qui ne suspend que les créations du chat (`routers/data.py:586-588`). Pour les réponses, la garantie est désormais B-1494 : le partiel passe par `_ecrire_reponse` (`routers/chat.py:2162-2181`), et la purge efface tout en une transaction (`routers/data.py:632-700`), si bien qu'il est effacé avec le reste ou refusé. Pour le reste, elle vient du lot 1 de P-125 (section 1 bis) : 409 sur un envoi pendant la purge (« Une opération sur tes données est en cours, j'arrête. »), qui protège le message de l'utilisateur, et arrêt d'office de chaque génération.
- **Conversation effacée** : un 404 sur sa conversation (`routers/chat.py:1266-1268`) termine la session : « La conversation a été effacée, j'arrête. »

### 4.2 Les accords

- **Écoute en ligne (Groq)** : finalité nouvelle `voice_conversation`, ajoutée à `CloudPurpose` (`lib/consent.ts:26`) et à `PURPOSE_LABELS` (`PrivacyTab.tsx:56-61`, typage `Record<CloudPurpose, string>`). `transcribeAudio` et `needsVoiceCloudConsent` reçoivent la finalité en paramètre (défaut `voice`) au lieu du `'voice'` écrit en dur (`services/api/voice.ts:131`, `:155`).
- **Modèle en ligne** : finalité `llm`, adressée à `fournisseurDAccord(fournisseur, modele)` (`lib/ollamaCloud.ts:19-23`). La garde du composeur (`ChatInput.tsx:558-589`) est extraite dans une fonction pure `accordRequisPourUnMessage({ fournisseur, modele, porteDesDocuments, piecesJointes })`, appelée par le composeur et par la session. **La session l'appelle au démarrage, puis avant chaque `streamMessage`**, sur la destination figée : un accord retiré entre deux tours sans que l'événement soit reçu arrête quand même la session, sans nouvelle question (décision 19).
- **Documents** : jamais requis. La conversation est neuve, la phase 1 n'a aucun outil, les commandes de fichier sont coupées et le serveur refuse `file_paths` en `mode_vocal` (section 4.5).
- **Catégories annoncées sur la carte** (constat 7) : ce que tu dis, transcrit ; le contexte de la conversation vocale ; **ton profil et tes consignes personnelles (THERESE.md)**, qui partent avec chaque message ; sans la mémoire locale. Pour Groq : l'audio de tes phrases.

### 4.3 Capture et fin de parole

- `getUserMedia` avec les options de la dictée (`hooks/useVoiceRecorder.ts:226-233`), puis un `AudioWorklet`. L'audio vit en mémoire, par segment.
- **Le module du worklet** (constat 12) est un fichier JavaScript simple, `src/frontend/public/capteurMicro.worklet.js`, chargé par `audioContext.audioWorklet.addModule('/capteurMicro.worklet.js')`. Un fichier de `public/` est copié tel quel, sans passer par Vite, donc jamais inliné en `data:` ; `demarrage-filet.js` suit déjà ce chemin. Le worklet ne fait que copier les trames et les poster ; toute la logique vit dans un module TypeScript pur, testé par vitest. Si l'essai du lot 1 échoue sur un système, repli sur `ScriptProcessorNode` pour ce système.
- **Détecteur d'énergie à hystérésis**, module pur sur trames PCM : la parole commence après 250 ms au-dessus du seuil et finit après 800 ms de silence ; seuil calibré sur une seconde de bruit au démarrage.
- **Segments de 30 s au plus, en WAV 16 kHz mono 16 bits** (constat 10). Le micro livre le plus souvent 48 kHz : la capture ouvre son contexte audio par `new AudioContext({ sampleRate: 16000 })`, les moteurs de Chromium et de WebKit rééchantillonnant eux-mêmes le flux du micro ; si l'essai du lot 1 montre une webview qui ignore l'option, le module pur rééchantillonne. À 16 kHz : 32 000 octets par seconde, soit 960 044 octets pour 30 s, sous le seuil de 1 Mio (1 048 576 octets) au-delà duquel le décodeur de formulaires de Starlette déborde dans un fichier temporaire (`starlette/formparsers.py:126`). Une parole plus longue est découpée en tranches de 30 s, transcrites l'une après l'autre ; le tour ne part au modèle qu'à la fin de parole, avec les tranches réunies.
- **À l'alternat en phase 1.** Pendant la parole de Thérèse, les trames ne nourrissent pas le détecteur, et 300 ms de marge suivent la fin de la lecture.
- **Pendant la réflexion**, seuls les segments de moins de 1,5 s sont transcrits, et seules les commandes y comptent ; tout autre segment est ignoré avec un son court « non pris ».
- **Silero** n'entre pas en phase 1 ; le lot 1 vérifie seulement la présence de son modèle dans le bundle.

### 4.4 Transcription

Chaque segment part vers `transcribeAudio(segment, 'segment.wav', signal, { finalite: 'voice_conversation', moteurAttendu })`. Le paramètre `moteurAttendu` (`local` ou `groq`) est le moteur figé au démarrage : si `resolveUseLocalForTranscription()` (`services/api/voice.ts:99-123`) désigne l'autre, `transcribeAudio` lève une erreur dédiée sans rien envoyer. Un segment ou une transcription vide ramène à l'écoute ; une erreur de transcription est dite, puis la session s'arrête.

**Côté moteur, aucun fichier nommé** (constat 10) : la route Groq passe les octets reçus directement au client HTTP (`files={"file": (nom, octets, type)}`) au lieu d'écrire un fichier (`routers/voice.py:87-99`) ; la route locale passe à `transcribe_local` un objet binaire en mémoire au lieu d'un chemin (`:260-277`). faster-whisper accepte, d'après sa documentation, un chemin, un objet binaire ou un tableau d'échantillons ; la version verrouillée (1.2.1) n'est pas installée dans l'environnement de développement, si bien que le lot 0 le prouve par un test rouge d'abord ; repli sûr si l'objet binaire était refusé : décoder le WAV 16 kHz par `wave` et passer un tableau `float32`. La dictée du composeur, qui utilise les mêmes routes, en profite.

**Commandes vocales**, reconnues côté interface avant tout envoi, sur la phrase entière, casse et accents repliés, ponctuation retirée : « stop » ou « arrête » (couper), « répète » (relire la dernière réponse depuis les sons déjà synthétisés), « plus court » (nouveau tour : « Redis ta dernière réponse en une phrase. »), « fin de session » ou « termine ». Un « stop » au milieu d'une phrase n'est pas une commande.

### 4.5 Le serveur : `mode_vocal`

`ChatRequest` (`models/schemas.py:105-119`) reçoit `mode_vocal: bool = False`, `fournisseur_attendu: str | None = None` et `modele_attendu: str | None = None`. Quand `mode_vocal` est vrai :

1. **Refus explicites, avant toute écriture** : `file_paths` non vide, `skill_id` présent, `stream=false`, ou `fournisseur_attendu` / `modele_attendu` absents donnent 422.
2. **Destination vérifiée** (constat 1) : `send_message` compare `fournisseur_attendu` et `modele_attendu` à `get_llm_service().config` avant de créer le moindre message ; s'ils diffèrent, 409 « Le modèle a changé depuis le début de la conversation vocale : rien n'a été envoyé. »
3. **Aucune bascule** (constat 1) : le tour est servi par `LLMService(get_llm_service().config, bascule_circuit=False)`, transmis à `_do_stream_response` au lieu de la relecture `routers/chat.py:2379`, sur le patron du Board (`services/llm.py:1224-1229`). Disjoncteur ouvert, le fournisseur d'origine est tenté et son échec remonte (`:824`) ; aucun autre fournisseur n'est appelé.
4. **Le message est du texte, rien d'autre** (constat 4). Les sept interprètes recensés dans le code sont court-circuités :

   | Interprète | Où | Effet évité |
   |---|---|---|
   | `parse_action_message` | `routers/chat.py:1324` | Actions déterministes (ouvrir une vue, produire un document) |
   | `resolve_message`, branche « produire » | `:1344-1347` | Substitution de variables dans le sujet produit |
   | `parse_slash_command` | `:1459` | Commandes `/contact`, `/projet`, `/rdv` |
   | `parse_inline_commands` | `:1543` | Directives `[contact: …]` exécutées avant le modèle |
   | `resolve_message`, variables | `:1636-1644` | `{nom}` remplacé par sa valeur |
   | `resolve_skill_from_message` et `parse_action_syntax` | `:2345-2366`, puis auto-exécution `:2900-2944` | `{{action: docx-pro}}` résout un skill et produit un fichier |
   | `_parse_file_commands` | `:2420`, via `allow_file_commands` | `/fichier` et `/analyse` lisent un fichier local et le joignent au contexte |

   Une transcription « /analyse ~/x.pdf », « [contact: X] » ou « {{action: docx-pro}} » part telle quelle au modèle ; rien n'est lu, créé ni produit. Le rejeu des pièces jointes des tours précédents (`_pieces_jointes_recentes`, `:2457`) ne trouve rien dans une conversation où `file_paths` est refusé ; il est tout de même sauté en `mode_vocal`.
5. **Aucun outil**, quelle que soit la valeur de `disable_tools` (branche actuelle à `:2528-2531`).
6. **Aucun ancrage Google Search** (constat 9) : `stream_response_with_tools(context, None, enable_grounding=False)` à la place de l'appel `:2661`. Sans cela, Gemini ajoute `{"google_search": {}}` dès que la recherche web est autorisée et qu'aucun outil n'est déclaré (`services/providers/gemini.py:282-283`).
7. **Aucune mémoire** (constat 6) : le moteur traite la requête comme `include_memory=False`, par la branche de B-1495 (`routers/chat.py:2396-2399`, section 1 bis) ; la session envoie aussi `include_memory: false`, et un client qui combinerait `mode_vocal=true` et `include_memory=true` n'obtient pas la mémoire.
8. **Aucune extraction d'entités** (constat 8) : la tâche de fond `routers/chat.py:2979-2986` n'est pas lancée. Son résultat n'est que journalisé (`routers/chat.py:975-983`), et en local elle disputerait le processeur au tour suivant.
9. **Style parlé.** Un bloc s'ajoute à `context.system_prompt` : deux à quatre phrases, ni liste, ni markdown, ni lien, ni emoji ; il dit expressément qu'il remplace, pour cette conversation, les consignes de mise en forme du prompt général (qui demandent des listes à puces dans les récapitulatifs) ; une question de relance quand elle aide ; « à vérifier » plutôt qu'une affirmation sèche.
10. **Local en panne** : l'erreur remonte, jamais de repli en ligne (B-1071).

La réponse reste écrite dans la conversation : le brainstorm se relit au retour.

### 4.6 La parole, phrase par phrase

- **Découpeur** de phrases sur le flux : ne coupe ni « M. Durand », ni « etc. », ni « 3,5 » ou « 12.5 », gère les points de suspension et les guillemets, garde une phrase coupée entre deux morceaux.
- **Nettoyeur** : retire listes et markdown, remplace un lien par « lien dans la conversation » et un bloc de code par « le code est dans la conversation », retire les emoji.
- **File de lecture, une synthèse à la fois**, chaque requête portant un `AbortController` abandonné à l'interruption.
- **Lecture par Web Audio** : `decodeAudioData`, une `AudioBufferSourceNode` par phrase, arrêtée par `stop()`. Aucune URL `blob:`, CSP inchangée.
- **Côté serveur** : la voix Piper est chargée une fois et gardée dans un cache protégé par un verrou ; les synthèses passent l'une après l'autre ; le chargement du modèle Whisper prend un verrou (`services/voice_local.py:239-265`). **Le WAV est produit en mémoire** (`wave.open` sur un `io.BytesIO`, dans une fonction `synthese_wav_en_memoire`) et rendu par une réponse d'octets : la route n'appelle plus `tempfile.NamedTemporaryFile` ni `FileResponse` (`routers/voice.py:313-327`).
- Une synthèse déjà lancée dans son fil n'est pas annulable ; son résultat est jeté.

### 4.7 Aucun écran requis

- **Sons d'état** synthétisés par un oscillateur Web Audio : écoute, réflexion, erreur, non pris, fin. Au-delà de 2 s de réflexion, un son discret ; au-delà de 8 s, « Je cherche encore. »
- **Erreurs dites** en une phrase actionnable, puis arrêt propre. Jamais une erreur seulement affichée.
- **Moteurs dits au démarrage**, d'après la configuration lue : la phrase du modèle est extraite de `phrasesDeLEtat` (`CapabilityCenter.tsx:497-513`) dans une fonction partagée avec la ligne d'état de P-118.
- **Accessibilité** : annonces `aria-live` limitées aux changements d'état.
- **Emplacement** : un mode « Conversation » dans l'espace Voix ; le bouton de dictée du composeur ne change pas.

### 4.8 Ce qui ne se fait pas à la voix

- **Phase 1 : aucun outil ni aucun effet.** Si on demande d'envoyer un mail, Thérèse répond qu'elle ne peut pas agir à la voix et que l'idée reste dans la conversation.
- **Phase 2, après usage réel : lecture seule**, filtrée par `classe_de(nom) == LECTURE_SEULE` (`services/contexte_execution.py:26-47`), moins la recherche web, le navigateur et les outils MCP ; lecture des mails à voix haute désactivée par défaut.
- **Jamais à la voix** : toute mutation. Un « oui » oral ne vaut pas confirmation ; la phase 2 devra rendre durables les confirmations en attente, en lien avec P-096.

### 4.9 Latence et mémoire

Cibles, entre la fin de parole et la première syllabe : moins de 3 s en hybride, moins de 6 s en local sur la machine de référence. Le lot 1 mesure chaque étage sur un Mac récent et un PC modeste, avec Ollama et Piper actifs en même temps, **et avec un THERESE.md réel proche de 10 000 caractères** (constat 7), puisque le prompt système l'emporte à chaque tour. Si la cible locale n'est pas tenue, le rapport du lot 1 dit quelle part revient au prompt, et un complément de RFC décidera d'un THERESE.md abrégé en `mode_vocal` ; la V3 n'en décide pas sans mesure. Aucun contrôle de mémoire libre n'est promis ; si le premier tour dépasse la cible locale, l'écran le dit une fois et propose l'hybride.

### 4.10 L'audio et le disque

**Ce que la session promet** (constat 10, qui rend fausse la phrase de la V2) : aucun fichier audio nommé n'est écrit par la session. La capture vit en mémoire ; les deux routes de transcription et la route de synthèse travaillent en mémoire (sections 4.4 et 4.6) ; les segments restent sous le seuil où Starlette déborderait dans un fichier temporaire. Si ce seuil était un jour franchi, le débordement irait dans un `TemporaryFile`, sans nom sous macOS et Linux, supprimé à la fermeture sous Windows, arrêt brutal compris.

Le greffon d'enregistrement n'est utilisé que par le repli « alternat à la touche », sur un système où `getUserMedia` échouerait ; il hérite alors de B-1424. Les dictées accumulées avant B-1424 et le fichier laissé par une application fermée pendant une dictée relèvent de la question 20 (section 10).

## 5. Défauts existants, hors de toute RFC, à reproduire

Relus au code en traitant les constats ; aucun n'est corrigé par cette RFC sauf mention.

| Réf. | Défaut supposé | Preuve dans le code | Reproduction proposée |
|---|---|---|---|
| R-109-1 | La carte d'accord du composeur annonce message, contexte et mémoire locale, mais pas le profil ni les consignes personnelles, qui partent pourtant avec chaque message vers un fournisseur en ligne | Catégories : `components/chat/ChatInput.tsx:576-579` ; profil et THERESE.md dans le prompt : `services/llm.py:506-517`, `:551`, `:890` | Configurer un modèle en ligne, remplir le profil et THERESE.md, retirer l'accord `llm`, envoyer un message, lire la carte, puis relever le prompt envoyé (fournisseur doublé) |
| R-109-2 | « Arrêter » avec un message en file : la file part 50 ms après la fin du flux, dans la même conversation, pendant que `cancelGeneration(conversation)`, lancé sans être attendu, peut encore arriver au serveur et arrêter la génération du message en file | Arrêt : `ChatInput.tsx:1030-1048` ; départ de la file : `:1019-1028` ; résolution de la génération la plus récente : `routers/chat.py:1017-1027` | Test d'interface avec un `cancelGeneration` retardé et un message en file, puis test moteur où l'annulation arrive après l'inscription du second traitement |
| R-109-3 | Les routes de transcription (Groq et locale) et la synthèse écrivent un fichier nommé effacé en `finally` ou par une tâche de fond ; un arrêt brutal du moteur laisse l'audio de l'utilisatrice dans le dossier temporaire du système, que Windows ne purge pas | `routers/voice.py:87-99`, `:150-155`, `:260-277`, `:313-327` | Tuer le moteur pendant une transcription locale longue, relever le dossier temporaire. Corrigé par le lot 0 de P-109 s'il est codé ; corrigeable seul sinon |
| R-109-4 | `include_memory_context` des préférences de personnalisation n'est lu par aucun code, sans réglage visible | `models/schemas_personalisation.py:71` ; `stores/personalisationStore.ts:46`, `:55` | Sans effet visible aujourd'hui : à rattacher à B-1495 ou à une fiche sœur, par l'orchestrateur |

B-1495 (`include_memory` ignoré) et B-1494 (réponse écrite dans une conversation supprimée) sont corrigés à `a3c98b74` ; B-1425 (purge pendant une réponse) reste fiché et couvert par le lot 1 de P-125. Ils sont cités, pas redoublés.

## 6. Ce que la V3 retire ou reporte, et pourquoi

- **Le gestionnaire d'Échap dans la pile** : retiré, remplacé par une branche de la cascade (constat 3).
- **`cancelGeneration(idDeLaConversationVocale)`** : retiré, remplacé par l'annulation par génération (constat 14). La justification de la V2 (« la session crée sa conversation parce que `cancelGeneration` a besoin d'un identifiant ») tombe ; la création au démarrage reste, pour la décision 18 et la détection du 404.
- **« Les quatre interprètes »** : remplacé par une liste de sept, recensée depuis le code (constat 4).
- **« La session n'écrit aucun audio sur disque »** : remplacé par une promesse exacte, rendue vraie par la transcription en mémoire et le plafond de 30 s (constat 10).
- **Le plafond de segment à 60 s** : ramené à 30 s, avec des tranches pour une parole plus longue.
- **`new URL('./capteurMicro.worklet.js', import.meta.url)`** : remplacé par un fichier de `public/` (constat 12).
- **« La session n'attend pas le mécanisme de B-1425 »** : retiré ; le lot 5 attend le lot 1 de P-125, B-1494 couvrant déjà les réponses (constat 2). Le signal `therese:purge-demandee` reste, comme politesse.
- **« Ce contrat est à reporter dans la V2 de P-125 à sa prochaine reprise »** : durci en condition préalable au code des deux RFC (constat 13).
- **Le test « dossier temporaire vide »** : remplacé par des espions (constat 5).
- **Reporté** : un THERESE.md abrégé en `mode_vocal`, qui attend la mesure du lot 1 ; l'inscription de la session au registre de P-125, qui attend ses lots 2 et 3.

## 7. Lots, dans l'ordre, en TDD

Règles communes : les tests nommés sont écrits d'abord et rougissent sur `main`, sauf ceux étiquetés « non-régression », qui protègent un comportement déjà juste ; un commit par lot, en français ; sabotage ciblé **par fonction** (découper le source entre deux `def` ou deux `function`, jamais un remplacement de chaîne globale, règle du `CLAUDE.md` du dépôt), chaque test doit rougir sous le sabotage de sa fonction ; revue adverse du diff avant fusion ; les six portes du `CLAUDE.md` sur `main` fusionné.

### Lot 0 : moteur vocal serveur (voix gardée, une synthèse à la fois, aucun fichier)

- Tests d'abord (pytest) :
  - `PiperVoice.load` n'est appelé qu'une fois pour deux synthèses (compteur sur un double) ;
  - deux synthèses lancées depuis deux fils ne se chevauchent pas (horodatages d'entrée et de sortie de `synthesize_wav`) ;
  - **Whisper** (constat 11) : constructeur `WhisperModel` doublé, lent (0,2 s), deux fils synchronisés par une `threading.Barrier(2)` appellent `transcribe_local` ; le constructeur n'est appelé qu'une fois. Rouge sur `main`, dont le cache n'a pas de verrou ;
  - **synthèse sans fichier** (constat 5) : pendant `POST /api/voice/tts`, un espion sur `tempfile.NamedTemporaryFile` du module `app.routers.voice` n'est jamais appelé, `wave.open` reçoit un `io.BytesIO` et jamais un chemin, la réponse n'est pas une `FileResponse` et son corps commence par `RIFF`. Rouge sur `main`, qui appelle `NamedTemporaryFile` (`routers/voice.py:313-314`) ;
  - **transcription sans fichier** (constat 10) : même espion sur `NamedTemporaryFile` pendant `/api/voice/transcribe` (client HTTP doublé, qui reçoit des octets) et `/api/voice/local/transcribe` (`transcribe_local` reçoit un objet binaire, ou le tableau du repli) ;
  - `voice: "fr"` reste accepté (non-régression de B-1410).
- Critère observable : dix synthèses et dix transcriptions de suite ne créent aucun fichier dans le dossier temporaire du système, relevé pendant les requêtes et non après.
- Sabotage : retirer le cache de `synthesize_local` ; retirer le verrou de chargement Whisper ; faire écrire `synthese_wav_en_memoire` dans un fichier.

### Lot 1 : essais dans l'app packagée, trois systèmes (aucun code livré)

Une branche d'essai jetable et un rapport `docs/qualite/2026-09-xx-p109-essais-voix.md`, avec un verdict par système (macOS, Windows, Linux) :

- `getUserMedia` dans la webview packagée : accordé, refusé, absent ;
- `audioWorklet.addModule('/capteurMicro.worklet.js')` depuis `public/`, **exactement le chargement retenu** (constat 12), et relevé de l'URL réellement chargée dans l'outil réseau ;
- lecture par `decodeAudioData` d'un WAV de `/api/voice/tts` ;
- lecture actuelle `<audio src=blob:>` de l'espace Voix : si elle est bloquée, défaut à ficher, corrigé au lot 4 ;
- présence du modèle Silero dans le bundle ;
- fréquence réelle du contexte audio créé avec `sampleRate: 16000` (lue sur `audioContext.sampleRate`) ; taille d'un segment de 30 s encodé : sous 1 048 576 octets ;
- tableau de latence (fin de parole, transcription d'une phrase, premier morceau de réponse, première phrase dite), local et hybride, Ollama et Piper actifs ensemble, **avec un THERESE.md réel proche de 10 000 caractères, puis sans**, pour mesurer sa part.

Sortie : pour chaque système, « session continue » ou « alternat à la touche avec le greffon ». Aucun lot d'interface ne commence sans ce rapport.

### Lot 2 : serveur, `mode_vocal` (B-1495 livré)

- Tests d'abord (pytest) :
  - style parlé présent en `mode_vocal`, absent sinon ;
  - aucun outil transmis au fournisseur, même avec `disable_tools=false` ;
  - **un test par interprète** : « /contact nom=Durand » (rien créé, aucun message marqué déterministe) ; « [contact: Durand] » et « {action: ouvrir crm} » (aucune `client_action`) ; « {nom} » non substitué ; **« /analyse ~/x.pdf » : `_get_file_context` jamais appelé, rien joint au contexte** ; **« {{action: docx-pro}} » : aucun skill résolu, aucun événement `skill_file`, `registry.execute` jamais appelé** ; le texte de chacun arrive intact au fournisseur doublé ;
  - **Gemini, recherche web autorisée** : le corps de la requête ne porte aucune clé `tools` (constat 9) ;
  - **mémoire** : `_get_memory_context` n'est pas appelé en `mode_vocal`, même avec `include_memory=true` ; hors `mode_vocal`, il suit `include_memory` (**non-régression** de B-1495, déjà couvert par `tests/test_b1495_include_memory.py`) ;
  - **extraction** : `_extract_entities_background` n'est pas planifiée en `mode_vocal` (espion sur `asyncio.create_task` ou sur la fonction) ;
  - **destination** : `fournisseur_attendu` ou `modele_attendu` différent de la configuration : 409, aucun message écrit, fournisseur jamais appelé ; absents : 422 ;
  - **disjoncteur** : fournisseur en ligne au circuit ouvert, un second fournisseur configuré et disponible : seul le premier est appelé, l'erreur remonte ;
  - `file_paths` non vide, `skill_id` présent, `stream=false` : 422 ;
  - fournisseur local indisponible : une erreur, aucun appel en ligne (**non-régression** de B-1071, vert sur `main` par construction).
- Critère observable : une conversation vocale rejouée par l'API ne contient que des messages utilisateur et assistante, aucun effet de bord en base ni sur disque.
- Sabotage : la fonction qui décide de court-circuiter les interprètes ; la fonction qui construit la liste d'outils ; la fonction qui compare la destination ; la construction du service sans bascule.

### Lot 3 : interface, détecteur de fin de parole et capture

- Tests d'abord (vitest), sur trames synthétiques : silence, bruit constant de roulage, salves de parole, parole plus longue que 30 s (deux tranches, un seul tour), calibrage du seuil, trames ignorées pendant la parole de Thérèse et pendant la marge de 300 ms ; encodeur WAV : 30 s à 16 kHz mono donnent 960 044 octets.
- La capture est un module qui expose un flux de trames, doublé en test ; le worklet réel n'est exercé qu'aux lots 1 et 7.
- Critère observable : sur un WAV témoin de trois phrases séparées de silences, trois segments exactement.
- Sabotage : la fonction de décision du détecteur ; la fonction de découpe en tranches.

### Lot 4 : interface, parole phrase par phrase

- Tests d'abord (vitest) : découpeur (« M. Durand », « etc. », « 3,5 », « 12.5 », points de suspension, guillemets, phrase coupée entre deux morceaux) ; nettoyeur (listes, gras, liens, blocs de code, emoji) ; file (jamais deux synthèses en vol, rien lu après interruption, requêtes abandonnées, file vide) ; lecteur (`decodeAudioData` sur les octets reçus, `stop()` à l'interruption, aucune URL `blob:` créée, espion sur `URL.createObjectURL`).
- L'espace Voix actuel passe sur ce lecteur si le lot 1 a confirmé le blocage de l'`<audio>`.
- Sabotage : `decouperPhrases`, `nettoyerPourLaVoix`, la fonction de vidage de la file.

### Lot 5 : interface, la session (après le lot 1 de P-125 et le report de la clause vocale dans P-125)

- Tests d'abord (vitest, minuteurs simulés) :
  - transitions de la machine à états ; transcription vide ; erreur dite puis arrêt ; 3 minutes sans parole ; 60 minutes ;
  - démarrage refusé si `isStreaming` est vrai ;
  - `createConversation` appelé une fois, avant la première transcription ; tous les `streamMessage` portent son identifiant, `mode_vocal: true`, `include_memory: false`, `fournisseur_attendu` et `modele_attendu` figés ;
  - **accords** : modèle en ligne sans accord `llm`, carte et aucun `streamMessage` ; écoute Groq sans accord `voice_conversation`, même chose, l'accord de la dictée ne suffisant pas ; **accord retiré du stockage entre deux tours sans événement : aucun `streamMessage` au tour suivant, arrêt dit** ; le composeur appelle la même `accordRequisPourUnMessage` (saboter la fonction fait rougir les deux) ;
  - **changement de modèle** : `therese:llm-config-changed` avec une autre destination, arrêt dit, aucun `streamMessage` ensuite ; avec la même destination, la session continue ; réponse 409 du serveur, arrêt dit ;
  - **moteur d'écoute** : préférence de voix basculée pendant la session, aucun `transcribeAudio` envoyé à l'autre moteur, arrêt dit ;
  - **interruption** (constat 14) : après l'événement `generation`, `annulerTraitement` appelé une fois avec cet identifiant, `cancelGeneration` jamais appelé ; l'écoute ne rouvre qu'après la résolution d'`annulerTraitement` (ou son délai de 3 s) ; avant l'événement, seul l'abandon du flux ;
  - **verrou** : `sessionVocale.active` vrai pendant la session, faux après ; `isStreaming` jamais modifié ; `openChat` refusé avec « Conversation vocale en cours », et le bouton du bandeau termine la session. Ce test est le fil qui rougira si le lot 5 de P-125 retirait la clause ;
  - **Échap** (constat 3) : Paramètres ouverts pendant la session, Échap ferme Paramètres et la session continue ; même chose avec la palette, le Board et le centre de confiance ; sans autre surface, premier Échap pendant la parole, retour à l'écoute ; pendant l'écoute, fin ; après la fin, Échap ferme l'espace Voix ;
  - panneau fermé : `track.stop` appelé sur chaque piste, `sessionVocale.active` faux ;
  - événement `cancelled` (arrêt venu de Travaux) : « Réponse arrêtée. », retour à l'écoute ;
  - révocation de `voice_conversation:Groq` ou de `llm` pour le fournisseur de la session : arrêt immédiat, aucun `transcribeAudio` ni `streamMessage` après l'événement ; révocation sans rapport : la session continue ;
  - `therese:purge-demandee` pendant l'écoute : arrêt immédiat ; `deleteAllData` émet l'événement avant son appel au moteur ; réponse 409 « opération sur tes données » : arrêt dit ;
  - 404 sur la conversation vocale : « La conversation a été effacée, j'arrête. » ;
  - **fin** : la conversation apparaît au store avec ses messages, sans doublon ; « Ouvrir la conversation » l'ouvre dans le chat ;
  - commandes vocales : variantes, accents, casse ; « stop » au milieu d'une phrase ne compte pas ; segments de plus de 1,5 s ignorés pendant la réflexion.
- Tests moteur (pytest) :
  - purge puis restauration pendant une réponse en `mode_vocal` : aucune ligne `messages` après, réponse comme message de l'utilisateur (**non-régression** de B-1494 et du lot 1 de P-125 appliqués au mode vocal) ;
  - arrêt du traitement A d'une conversation pendant que son traitement B a démarré : B continue (**non-régression** de `demander_arret` ciblé, `routers/processing_tasks.py:23`).
- Sabotage : `accordRequisPourUnMessage`, `echapPourLaSessionVocale`, la fonction de nettoyage de la session, la fonction d'interruption, la reconnaissance des commandes, `ajouterConversationServeurAuStore`.

### Lot 6 : surface

- Mode « Conversation » de l'espace Voix : grand état, grand bouton au libellé suivant l'état, moteurs affichés et dits, sons d'état, libellé `voice_conversation` dans les réglages, carte d'accords avec le profil et THERESE.md nommés.
- Tests d'abord (vitest) : moteurs affichés et dits conformes au routage réel ; phrase du modèle identique à celle de la ligne d'état de P-118 ; catégories de la carte ; annonces `aria-live` limitées aux changements d'état.
- Recette Playwright (Chromium, serveur jetable 17393, jamais 17293) : micro simulé par un WAV (`--use-fake-device-for-media-stream`, `--use-file-for-fake-audio-capture`), transcription et modèle doublés ; un tour complet, une interruption, Paramètres ouverts puis Échap (Paramètres se ferment, la session continue), puis Échap deux fois.

### Lot 7 : recette humaine

App packagée sur les trois systèmes, avec un casque Bluetooth ; voiture à l'arrêt, puis en roulant avec un passager aux commandes ; bruit de route ; PC modeste ; tableau de latence du lot 1 refait sur la version finale ; dossier temporaire du système relevé avant et après une session d'une heure.

### Phase 2, non planifiée

Lecture seule filtrée par classe d'effet, interruption en parlant après un essai d'annulation d'écho, confirmations durables (P-096), réglage des mails lus à voix haute, inscription au registre de P-125 après ses lots 2 et 3. Un complément de RFC après usage réel.

## 8. Risques restants

- **Latence locale** : plusieurs secondes par tour sur un portable ; parades : phrase par phrase, sons d'attente, hybride proposé sur mesure, part de THERESE.md mesurée.
- **Webview** : un système sans `getUserMedia` n'aura que l'alternat à la touche ; le lot 1 le dira avant tout code d'interface.
- **Écho et faux déclenchements** : l'alternat et le seuil calibré les réduisent sans les supprimer.
- **Mémoire vive** : Whisper, Piper et un modèle local ensemble ; aucun contrôle de mémoire libre n'est promis.
- **Confidentialité** : audio continu chez Groq en hybride, sous un accord distinct ; profil et THERESE.md chez le fournisseur en ligne, désormais annoncés.
- **Dépendances** : le lot 5 attend le lot 1 de P-125 et le report de la clause vocale dans son lot 5 ; si l'un tarde, la session attend.
- **Ordre des messages après une coupure précoce** : couper Thérèse avant l'arrivée de l'événement `generation` laisse le moteur écrire le partiel pendant son nettoyage, borné à 5 s ; si l'utilisatrice relance plus vite, le partiel peut s'inscrire après sa nouvelle question. Aucune perte, un ordre inexact dans la conversation relue ; accepté, l'attente de 3 s couvrant le cas courant.
- **faster-whisper en mémoire** : si l'objet binaire était refusé par la version embarquée, le repli par tableau d'échantillons ajoute un décodage ; le lot 0 le dira.
- **Sécurité routière** : l'usage au volant ne doit pas être promu (section 10).
- **Assurance orale** : une erreur dite avec aplomb, sans sources visibles ; parades : style « à vérifier » et conversation relisible.
- **Verrou long** : pendant une session, tout changement d'écran est refusé ; c'est voulu, et le bandeau dit pourquoi.
- **Dictées déjà conservées** chez les testeurs, tant que la question 20 n'est pas tranchée.

## 9. Plan de tests, récapitulatif

Serveur : lots 0 et 2, plus les deux tests moteur du lot 5 (pytest). Interface : lots 3 à 6 (vitest). Bout en bout : lot 6 (Playwright, micro simulé). Recette humaine : lots 1 et 7. Chaque fonction de garde (accords, destination, court-circuit des interprètes, liste d'outils, service sans bascule, interruption, Échap, nettoyage de session, vidage de file, synthèse en mémoire) a un test qui rougit sous son sabotage.

## 10. Laissé à Ludo

**Question 20 : les dictées déjà conservées chez les testeurs.** B-1424 empêche toute nouvelle accumulation ; restent les WAV antérieurs, parfois lourds (un fichier de 1,5 Go relevé sur le Mac de Ludo), et le fichier laissé par une application fermée pendant une dictée. Deux options :

- **Option A, purge à la mise à jour** (recommandation du 25/09) : au premier démarrage de la version corrigée, THÉRÈSE efface tout le dossier `tauri-plugin-mic-recorder`, puis le vide à chaque démarrage. Annonce dans les notes de version et sur Discord. Test : dossier peuplé de trois WAV, démarrage, dossier vide.
- **Option B, rien d'effacé d'office** : les réglages affichent « N dictées conservées par une ancienne version, X Mo » avec « Effacer » ; au démarrage, seuls les fichiers postérieurs au premier lancement de la version corrigée sont effacés. Test : un ancien et un récent, démarrage, seul le récent disparaît.

Aucun lot de cette RFC n'attend cette réponse.

**Annonces publiques.** Le texte des notes de version et du message Discord qui présenteront la conversation vocale, en particulier la phrase sur l'usage en voiture, relève de Ludo. La recommandation technique est de ne jamais la présenter comme un usage au volant.

## Annexe : appuis dans le code (`a3c98b74`)

| Sujet | Référence |
|---|---|
| Effacement du WAV de dictée et purge des dictées (B-1424) | `hooks/useVoiceRecorder.ts:105-116`, `:204-205` ; `services/api/data.ts:123-135`, `:137-146` |
| Options du micro | `hooks/useVoiceRecorder.ts:226-233` |
| Voix « fr » (B-1410) | `services/voice_local.py:99` |
| Finalités d'accord et révocation | `lib/consent.ts:26`, `:40-42`, `:82-88`, `:95-104` ; `components/settings/PrivacyTab.tsx:56-61`, `:106` |
| Routage et accord de la transcription | `services/api/voice.ts:84-123`, `:131`, `:155` |
| Garde d'accord et catégories du composeur | `components/chat/ChatInput.tsx:558-589`, `:576-579` ; `lib/ollamaCloud.ts:19-23` |
| Changement de modèle | `components/chat/ChatInput.tsx:240`, `:253` ; `components/settings/SettingsModal.tsx:398`, `:545`, `:566` ; `components/onboarding/CompleteStep.tsx:72` |
| Arrêt du composeur et file | `components/chat/ChatInput.tsx:1019-1028`, `:1030-1048` |
| Service du modèle et bascule | `services/llm.py:824`, `:832-841`, `:849-856`, `:961`, `:1210-1216`, `:1224-1229` |
| Prompt système | `services/llm.py:506-517`, `:551`, `:890` |
| Requête de chat | `models/schemas.py:105-119`, `:110` |
| Interprètes du message | `routers/chat.py:1324`, `:1344-1347`, `:1459`, `:1543`, `:1636-1644`, `:2345-2366`, `:2420`, `:2457`, `:2900-2944` |
| Flux, outils, mémoire, ancrage, extraction | `routers/chat.py:2271`, `:2379`, `:2396-2399`, `:1738-1741`, `:2528-2531`, `:2661`, `:2979-2986`, `:975-983` |
| Annulation et génération | `routers/chat.py:1001-1042`, `:1017-1027`, `:1985-1994`, `:2080-2087`, `:2162-2181`, `:2184-2215`, `:1266-1268`, `:1307-1318` ; `services/api/chat.ts:67-72`, `:276-281` ; `routers/processing_tasks.py:23` ; `services/api/processingTasks.ts:44-47` |
| Purge | `routers/data.py:586-588`, `:632-700` |
| Ancrage Gemini | `services/providers/gemini.py:263-283` |
| Moteurs vocaux | `routers/voice.py:87-99`, `:150-155`, `:260-277`, `:313-327` ; `services/voice_local.py:239-265`, `:292` |
| Starlette 1.2.1 | `.venv/lib/python3.13/site-packages/starlette/responses.py:382-383` ; `.venv/lib/python3.13/site-packages/starlette/formparsers.py:126` |
| Espace Voix | `components/prototype/VoiceWorkspaceCanvas.tsx:134-136`, `:192` ; `components/prototype/ConversationCanvasPrototype.tsx:1526-1533`, `:2497-2507` |
| Verrou et navigation | `stores/chatStore.ts:82`, `:344` ; `components/prototype/ConversationCanvasPrototype.tsx:1076-1090`, `:1196` |
| Échap | `components/prototype/ConversationCanvasPrototype.tsx:843-849`, `:851-862`, `:1592-1626` ; `lib/escapeStack.ts:33-37` ; `components/settings/SettingsModal.tsx:102-105` |
| Store du chat | `stores/chatStore.ts:96`, `:114`, `:116` ; `hooks/useConversationSync.ts:28`, `:105` ; `services/api/chat.ts:272`, `:309` |
| Ligne d'état P-118 | `components/prototype/CapabilityCenter.tsx:497-513` |
| CSP | `src/frontend/src-tauri/tauri.conf.json:31` |
| Classes d'effet et confirmations | `services/contexte_execution.py:26-47` ; `services/tool_confirmations.py:10-12`, `:19` |
| Mémoire morte des préférences | `models/schemas_personalisation.py:71` ; `stores/personalisationStore.ts:46`, `:55` |
