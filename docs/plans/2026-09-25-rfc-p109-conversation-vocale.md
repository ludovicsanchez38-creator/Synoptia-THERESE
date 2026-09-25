# RFC P-109 : une conversation vocale de bout en bout, mains libres

Rédigé le 25/09/2026. Proposition S9 de Dr_logic-3D, acceptée par Ludo le 25/09. La recommandation du portail était : « à discuter : cohérent avec la ligne vocale Grok de Synoptïa, coûteux en local ». Aucun code avant la validation de ce document.

Chemins relatifs à `src/backend/app/` (serveur) et `src/frontend/src/` (interface), sauf mention contraire.

## 1. Le besoin

Dr_logic-3D (fil Discord du 25/09) réfléchit à voix haute en conduisant, avec Perplexity en mode vocal. Il voudrait la même chose avec THÉRÈSE : parler, entendre la réponse, relancer, sans écran ni clavier. Aujourd'hui, THÉRÈSE sait dicter et lire un texte, mais pas converser.

Trois exigences en découlent :

- **une boucle continue** : détecter la fin de parole, répondre à voix haute, se remettre à écouter ;
- **l'interruption** : pouvoir couper Thérèse ;
- **aucun écran requis** pendant la conversation.

**Une réserve d'emblée.** THÉRÈSE est une application de bureau (macOS, Windows, Linux), sans client mobile. « En voiture » veut donc dire aujourd'hui un ordinateur portable allumé dans l'habitacle. Or le Code de la route interdit :

- de placer dans le champ de vision du conducteur un appareil à écran en fonctionnement qui n'aide pas à la conduite ([article R412-6-2](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025111520)) ;
- de porter à l'oreille tout dispositif susceptible d'émettre du son ([article R412-6-1](https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=LEGIARTI000030800800&cidTexte=LEGITEXT000006074228&dateTexte=20150628)).

Le son doit donc passer par les haut-parleurs du véhicule ou de l'ordinateur, écran hors de vue. La V1 vise d'abord le bureau mains libres. L'usage mobile véritable relève d'un autre chantier (question 1).

## 2. Ce qui existe déjà

### Points d'appui

- **Dictée.** `VoiceDictationButton` (`components/chat/VoiceDictationButton.tsx`) et `useVoiceRecorder` (`hooks/useVoiceRecorder.ts`) fonctionnent au clic : un clic lance l'écoute, un second l'arrête.
  - Dans l'app packagée, le greffon Tauri `mic-recorder` enregistre dans un fichier (`useVoiceRecorder.ts:143-197`).
  - Hors Tauri, `getUserMedia` est appelé avec annulation d'écho et réduction de bruit (`useVoiceRecorder.ts:212-219`).
  - Le texte est inséré dans le composeur, jamais envoyé seul (`components/prototype/ConversationCanvasPrototype.tsx:1617-1624`).
- **Routage de la transcription, local ou Groq, en trois états.** La préférence est respectée sans exception ; jamais de repli silencieux vers le cloud (`services/api/voice.ts:29-34`, `99-123`, `141-197`).
- **Consentement de la dictée.**
  - Il est demandé au clic micro, pour le fournisseur Groq, avec la catégorie « audio de la dictée » (`VoiceDictationButton.tsx:54-67`).
  - Le consentement v2 fonctionne par finalité et par fournisseur (`lib/consent.ts:26`). Le précédent de la finalité distincte `documents` est documenté (`lib/consent.ts:13-24`).
- **Moteurs vocaux côté serveur.**
  - Groq Whisper (`routers/voice.py:55-155`, modèle `whisper-large-v3-turbo` l.104).
  - Whisper local, faster-whisper en int8 sur CPU, modèle gardé en mémoire (`routers/voice.py:215-279`, `services/voice_local.py:232-258`).
  - Synthèse locale Piper (`routers/voice.py:296-334`, `services/voice_local.py:261-291`).
  - Les bibliothèques sont embarquées dans les builds officiels (`src/backend/backend.spec:128-139`) ; les modèles se téléchargent en un clic.
  - Besoins en mémoire : environ 1 Go pour Whisper base, environ 0,5 Go pour la voix Piper (`docs/VOICE-LOCAL.md`).
- **Espace Voix de la coque** (`components/prototype/VoiceWorkspaceCanvas.tsx`).
  - Il transcrit un fichier et lit un texte.
  - Il affiche déjà le moteur utilisé et ce qui sort ou non de la machine (l.93-96 et l.173-175).
  - Il est ouvert depuis `ConversationCanvasPrototype.tsx:2285-2294`.
- **Chat.**
  - Flux et annulation : `streamMessage` et `cancelGeneration` (`services/api/chat.ts:147` et `397`).
  - `ChatRequest.disable_tools` (`models/schemas.py:114`).
  - Classes d'effet des outils : lecture seule, mutation locale, mutation externe (`services/contexte_execution.py:26-60`).
  - Un fournisseur local en panne ne bascule jamais en ligne (B-1071, `services/llm.py:832-840`).

### Manques

- **Pas de capture continue.** Le greffon Tauri n'expose que deux commandes, démarrer et arrêter vers un fichier (`docs/application-map/risques.md:2009`). Le fonctionnement de `getUserMedia` dans les webviews packagées n'a jamais été vérifié sur les trois systèmes.
- **Pas de détection de fin de parole.**
- **Pas de lecture de la réponse du chat.** La synthèse porte sur un bloc entier, pas phrase par phrase.
- **La voix Piper est rechargée à chaque synthèse** (`services/voice_local.py:285`), contrairement au modèle Whisper, gardé en mémoire (l.247-255).
- **Aucun style parlé.** Les réponses sont écrites pour l'écran : listes, liens, markdown.
- **Les confirmations en attente vivent en mémoire** et se perdent au redémarrage (`services/tool_confirmations.py:10-20`).

### Préalable découvert en lisant le code

**La synthèse de l'espace Voix échouerait à chaque fois.**

- `synthesizeSpeech` envoie `voice: "fr"` par défaut (`services/api/voice.ts:200` et `204`).
- La route garde cette valeur (`routers/voice.py:317`, `payload.voice or DEFAULT_PIPER_VOICE`).
- La liste blanche ne connaît que `fr_FR-siwis-medium` (`services/voice_local.py:98-109`, appelée l.271).
- Réponse attendue : 503 « Voix Piper inconnue : fr ».

Aucun test ne le voit : la fonction est simulée côté interface (`components/prototype/VoiceWorkspaceCanvas.test.tsx:21-28`), et les tests serveur envoient une requête sans `voice` (`tests/test_routers_voice.py:323`). À reproduire dans l'app packagée, puis à ficher. C'est le lot 0.

## 3. Quatre options

| | A. Tout local, à l'alternat | B. Chaîne hybride, étage par étage | C. API parole-à-parole en ligne | D. Compagnon mobile |
|---|---|---|---|---|
| Idée | Micro continu, fin de parole détectée, Whisper local, modèle configuré (Ollama s'il est local), Piper phrase par phrase | Même chaîne ; chaque étage passe en ligne avec son accord : Groq pour l'écoute, le modèle en ligne déjà configuré pour la réponse, Piper toujours local pour la voix | Un fournisseur temps réel (type OpenAI Realtime, Gemini Live, Grok Voice) reçoit l'audio et répond en audio | Un téléphone converse avec une instance de THÉRÈSE |
| Pour | Rien ne quitte la machine ; réutilise la dictée, la voix locale et le chat | Latence réduite sans nouveau tiers : Groq et le fournisseur du modèle ont déjà leurs accords | Latence la plus basse, interruption native, voix naturelle | Le vrai usage en voiture |
| Contre | Plusieurs secondes par tour sur un portable ; mémoire (Whisper, Piper, modèle local) ; interruption vocale difficile | Audio continu chez Groq, bien plus que « l'audio de la dictée » ; dépend du réseau | Nouveau fournisseur ; audio et contexte mémoire chez un tiers ; outils et cloisons à recâbler ; tarif à la minute à relever aux sources ; à rebours de la ligne souveraine | Sécurité réseau et synchronisation (P-108) |
| Effort | Moyen à large | Petit, en plus de A | Large | Très large, hors périmètre |

## 4. Recommandation : A et B comme une seule chaîne à moteurs interchangeables, en deux phases

### 4.1 La boucle (phase 1)

**États.** Prêt, écoute, fin de parole, transcription, commande éventuelle, réflexion, parole, puis retour à l'écoute.

**Fin de parole, côté interface.**

- `getUserMedia` avec les options déjà utilisées par la dictée, et un `AudioWorklet`. Aucune nouvelle dépendance.
- Détecteur d'énergie à hystérésis :
  - la parole commence après 250 ms au-dessus du seuil, elle finit après 800 ms de silence (réglable) ;
  - le seuil est calibré sur une seconde de bruit ambiant au démarrage ;
  - un segment dure 60 s au plus.
- Si ce détecteur ne suffit pas en voiture : le filtre de voix de faster-whisper (`vad_filter`, Silero) en second passage côté serveur. Sa présence dans la version embarquée est à confirmer.

**Transcription.**

- Le segment est envoyé à `transcribeAudio`, dont le routage local ou en ligne reste inchangé.
- Segment ou transcription vide : retour à l'écoute, rien n'est envoyé au modèle.

**Réponse.**

- L'envoi passe par `streamMessage`, sur une conversation normale : historique, badge local ou en ligne, cloison de projet.
- L'audio n'est jamais conservé ; les fichiers temporaires sont effacés comme aujourd'hui.

**Lecture phrase par phrase.**

- Un découpeur de phrases lit le flux.
- Un nettoyeur retire listes et markdown, remplace les liens par « lien dans la conversation » et le code par « le code est dans la conversation ».
- Chaque phrase passe par `POST /api/voice/tts`, puis entre dans une file de lecture. La première phrase est dite pendant que le modèle écrit la suite.

**À l'alternat en phase 1.** Le micro est coupé pendant que Thérèse parle, pour qu'elle ne s'entende pas dans les haut-parleurs d'une voiture. L'écoute reprend seule à la fin de la lecture.

**Interruption en phase 1.**

- Moyens : touche Espace ou Échap, grand bouton « Stop », ou commande vocale « stop » pendant la réflexion.
- Effet : `cancelGeneration`, file audio vidée, lecture coupée, retour à l'écoute.

**Commandes vocales.** « stop », « répète », « plus court », « fin de session ». Elles sont reconnues avant le modèle, sur la phrase entière, accents repliés, sans aucun appel au modèle, comme les actions déterministes du chat.

**Fin de session.** Par la commande, après 3 minutes sans parole (annoncé à voix haute), ou au bout de 60 minutes.

### 4.2 Aucun écran requis

- **Sons d'état.** Chaque état a un son court (écoute, réflexion, erreur, fin), joué localement. Au-delà de 2 s de réflexion, un son discret le signale ; au-delà de 8 s, Thérèse dit « je cherche encore ».
- **Erreurs dites.** Toute erreur est dite à voix haute en une phrase actionnable, puis la session s'arrête proprement : « Le micro ne répond plus, j'arrête la conversation. » Jamais une erreur seulement affichée.
- **Aucune carte à valider** pendant la session (voir 4.4).
- **Démarrage** par un geste unique, avant de partir (bouton ou raccourci). Pas de mot d'éveil en V1 : il supposerait une écoute permanente, coûteuse et intrusive.
- **Accessibilité.** Le mode sert aussi à ceux qui ne peuvent pas taper. Les annonces `aria-live` restent sobres, pour ne pas couvrir la voix de Thérèse par celle du lecteur d'écran.
- **Emplacement.** Le mode « Conversation » vit dans l'espace Voix : grand état lisible, gros bouton « Stop », moteurs affichés. Le bouton de dictée du composeur ne change pas.

### 4.3 Le style parlé (serveur)

- `ChatRequest` reçoit `mode_vocal`, à côté de `disable_tools`.
- En mode vocal, un bloc de prompt demande :
  - deux à quatre phrases ;
  - ni liste, ni markdown, ni lien, ni emoji ;
  - une question de relance quand elle aide ;
  - « à vérifier » plutôt qu'une affirmation sèche, puisque l'oral ne montre pas de sources.
- Les réponses restent écrites dans la conversation : le brainstorm se relit au retour.

### 4.4 Ce qui ne peut pas se faire à la voix

- **Phase 1 : aucun outil** (`disable_tools=True`). Le mode vocal sert à réfléchir. Si on lui demande d'envoyer un mail, Thérèse répond qu'elle ne peut pas agir à la voix et que l'idée reste dans la conversation.
- **Phase 2 : lecture seule**, filtrée par classe d'effet : agenda, fiches, factures, fichiers, recherche de mails. Le réglage « lire le contenu des mails à voix haute » est désactivé par défaut, à cause des passagers.
- **Jamais à la voix.**
  - Toute mutation externe : `send_email`, création d'événement dans un agenda en ligne, recherche web (la requête part chez Brave), navigateur, outils MCP.
  - Toute mutation locale soumise à une carte.
- **Pourquoi un « oui » oral ne vaut pas confirmation.** La transcription peut se tromper, et un passager ou la radio peut parler.
- **Devenir de ces actions.** Elles restent des propositions à valider devant l'écran. La phase 2 devra rendre les cartes en attente durables, en lien avec P-096.

### 4.5 Local d'abord, en ligne avec accord

- **Au démarrage**, les trois moteurs sont affichés et dits : « J'écoute en local, je réponds avec Mistral en ligne, je parle en local. »
- **Par défaut** : écoute locale si la voix locale est prête, modèle configuré, voix Piper locale.
- **Écoute en ligne (Groq) : accord distinct**, catégorie « audio de la conversation vocale », sur le précédent de `documents`. L'accord de la dictée ne couvre pas une écoute qui peut durer une heure.
- **Moteur local qui tombe** en cours de session : Thérèse le dit et s'arrête, sans aucun basculement en ligne (B-1071).
- **Option C** : pas en V1. Une expérience séparée plus tard, si Ludo la veut (question 6), avec son propre accord par fournisseur.

### 4.6 Latence : la mesurer, puis la dire

Mesures du lot 0, sur un Mac récent et sur un PC modeste :

| Étage | Local | Hybride |
|---|---|---|
| Fin de parole | 0,8 s (réglage) | 0,8 s |
| Transcription d'une phrase | Whisper base sur CPU : à mesurer | Groq : à mesurer |
| Premier morceau de réponse | Ollama : à mesurer | fournisseur en ligne : à mesurer |
| Première phrase dite | Piper, voix en mémoire : à mesurer | idem |

Cibles proposées, entre la fin de parole et la première syllabe : moins de 3 s en hybride, moins de 6 s en local sur la machine de référence. Si la machine ne peut pas tenir la cible, l'écran déconseille le tout local et propose l'hybride. Le garde-fou de mémoire existe déjà (`services/system_resources.py`).

## 5. Livraison proposée (après validation), en TDD

0. Préalables et essai.
   - Correctif de la voix `fr`, avec un test rouge du contrat réel.
   - Voix Piper gardée en mémoire.
   - Essai de `getUserMedia` dans l'app packagée sur macOS, Windows et Linux, avec un verdict par système. Repli : l'alternat à la touche, avec le greffon actuel.
   - Vérification de `vad_filter`, mesure de latence.
   - Design court et revue adverse du design.
1. Détecteur de fin de parole (module pur sur trames PCM) et capture continue.
2. Machine à états de la session, annulation.
3. Serveur : `mode_vocal` (style parlé, outils coupés).
4. Parole phrase par phrase : découpeur, nettoyeur, file de lecture.
5. Surface : mode « Conversation » de l'espace Voix, sons d'état, moteurs affichés, accord Groq distinct, commandes vocales.
6. Recette sur les trois systèmes : casque Bluetooth, voiture (profil mains libres), bruit, machine modeste, tableau de latence rempli.

Phase 2, après usage réel : lecture seule, interruption en parlant (après un essai d'annulation d'écho sur haut-parleurs), propositions d'action durables, réglage des mails lus à voix haute.

Chaque lot fait l'objet d'un commit, avec sabotage des tests (ciblé par fonction) et revue adverse du diff.

## 6. Plan de tests

**Serveur (pytest).**

- `POST /api/voice/tts` avec `voice: "fr"`, ce qu'envoie l'interface, rend un WAV. Test rouge avant le correctif.
- La voix Piper n'est chargée qu'une fois pour deux synthèses (compteur sur `PiperVoice.load`).
- `mode_vocal` : le bloc de style est présent en mode vocal, absent sinon. Aucun outil n'est transmis au fournisseur en phase 1 ; réintroduire `send_email` fait rougir le test. En phase 2, seules les lectures classées passent.
- Fournisseur local indisponible en mode vocal : une erreur, aucun repli en ligne.

**Interface (vitest).**

- Détecteur sur trames synthétiques : silence, bruit constant de roulage, salves de parole, parole plus longue que le plafond, calibrage du seuil.
- Machine à états (minuteurs simulés) : chaque transition ; transcription vide qui revient à l'écoute ; erreur dite puis arrêt ; inactivité de 3 minutes ; durée maximale.
- Interruption : après « Stop », plus aucune phrase lue, `cancelGeneration` appelé une seule fois, file vide. Retirer le vidage de la file fait rougir le test.
- Découpeur : « M. Durand », « etc. », « 3,5 », « 12.5 », points de suspension, guillemets, phrase coupée entre deux morceaux du flux.
- Nettoyeur : listes, gras, liens, blocs de code, emoji.
- Commandes vocales : variantes, accents, casse. Un « stop » au milieu d'une phrase ne compte pas.
- Accord : une première écoute en ligne sans accord « conversation » déclenche la demande, et rien n'est envoyé. L'accord de la dictée ne suffit pas.
- Les moteurs affichés sont bien ceux du routage réel.

**Bout en bout (Playwright, Chromium, serveur jetable 17393).** Le micro est simulé par un fichier WAV (`--use-fake-device-for-media-stream`, `--use-file-for-fake-audio-capture`), transcription et modèle doublés. On joue un tour complet, puis une interruption.

**Recette humaine.**

- App packagée sur les trois systèmes, avec un casque Bluetooth.
- Voiture à l'arrêt, puis en roulant avec un passager aux commandes.
- Bruit de route, PC modeste, tableau de latence rempli.

## 7. Risques

- **Latence locale.** Plusieurs secondes par tour sur un portable : la comparaison avec Perplexity sera défavorable. Parades : phrase par phrase, sons d'attente, hybride en option, mesure dite.
- **Webview.** Si `getUserMedia` manque dans une webview packagée, ce système n'aura pas de fin de parole automatique. Repli : l'alternat à la touche.
- **Écho et faux déclenchements** : haut-parleurs, radio, passagers. Parades : l'alternat en phase 1 et le seuil calibré.
- **Mémoire vive.** Whisper, Piper et un modèle local tournent ensemble. Parades : le garde-fou existant, et l'hybride conseillé sur les petites machines.
- **Confidentialité.** Audio continu chez Groq en hybride ; contenus privés entendus par les passagers en phase 2.
- **Sécurité routière** (section 1). Ne jamais exiger un regard ni un geste pendant la conduite, et ne pas promouvoir l'usage au volant tant que le produit n'est pas mobile.
- **Assurance orale.** Une erreur dite avec aplomb, sans sources visibles. Parades : le style « à vérifier » et la transcription relisible.
- **Batterie et chaleur.** La détection côté interface limite la transcription aux seuls segments de parole.

## 8. Décisions attendues de Ludo

1. **Cible de la V1** : le bureau mains libres, la voiture restant un usage toléré sur portable ? Recommandation : oui.
2. **Moteurs par défaut** : local s'il est prêt, hybride en option avec accord ? Recommandation : oui.
3. **Outils** : phase 1 sans aucun outil, pour la réflexion pure ? Recommandation : oui.
4. **Interruption en parlant** : en phase 2, après l'essai d'annulation d'écho ? Recommandation : oui.
5. **Accord distinct** pour l'écoute continue chez Groq ? Recommandation : oui.
6. **API parole-à-parole en ligne** (option C) : une expérience plus tard, ou un refus ?
7. **Usage mobile** (option D) : le rattacher à P-108, ou à Thérèse Server ?
