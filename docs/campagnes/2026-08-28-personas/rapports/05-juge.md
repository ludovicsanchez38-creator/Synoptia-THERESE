# Rapport - Claire Dumontier, magistrate (chambre civile)

## Mon impression générale

J'ai ouvert THÉRÈSE comme j'ouvre un logiciel dont on me vante la prudence : d'abord les mentions, ensuite seulement le travail. Le bouton *Contrôle des données* est en tête d'écran, le *Centre de confiance* parle de local et de confirmation, l'onglet *Confidentialité* affirme que rien ne part. J'ai voulu y croire le temps d'une formation ENM, hors de toute affaire. L'accueil, lui, me parle de *Facturer* et me demande de *Brancher mes mails*. Quand j'ai demandé un plan d'intervention, on m'a cité l'article 700 du code de procédure civile pour l'exécution provisoire. C'est l'article des frais irrépétibles. J'ai reposé la question que je connais. Même erreur, plus un « Code de la déontologie et de l'ethique de la profession juridique » qui n'existe pas, avec une confiance affichée à 100 %. Puis j'ai demandé d'attendre avant toute recherche web : la requête est partie toute seule, et le texte m'a assuré qu'aucune donnée ne quittait la machine. Je n'ai plus besoin d'un second essai.

## Ce que j'ai réussi à faire

- Lire, à l'écran, ce que l'application dit d'elle-même : *Contrôle des données*, *Centre de confiance*, *Paramètres > Confidentialité*, *À propos*. (lecture d'interface)
- Créer un « projet » *Intervention ENM - Exécution provisoire de droit*, un document du même nom, deux rendez-vous dans *Mon calendrier* (préparation le 8 octobre, intervention le 15 octobre à Bordeaux) et deux tâches de relecture. (API : `POST /api/memory/projects`, `POST /api/documents/`, `POST /api/calendar/events`, `POST /api/tasks/`)
- Obtenir une trame en cliquant, côté écran, sur *Générer la trame* (`POST /api/documents/{id}/outline`, 66 s, 16 sections vides).
- Obtenir un plan d'intervention dans le chat (`POST /api/chat/send`, conversation `d172e713-…`, 144 s). Le texte est inutilisable (voir F3).
- Exporter un JSON global (`GET /api/data/export`, HTTP 200). Le bouton d'écran s'appelle *Exporter toutes mes données*.
- Vérifier que l'effacement global existe, sans le lancer : *Supprimer toutes mes données*, puis *Saisis SUPPRIMER pour confirmer*.

## Ce que je n'ai pas réussi à faire

- Trouver, dans l'interface, une phrase que je puisse opposer à un collègue : données sur ce poste, rien ne sort sans que je le voie, et le droit n'est pas inventé.
- Obtenir un plan d'intervention ENM avec des sources que je pourrais citer. Les articles donnés sont faux. La trame générée est un plan de réunion générique (*Introduction*, *Cas d'étude 1*, *slides*).
- Obtenir la réponse exacte sur l'exécution provisoire de droit (art. 514 CPC). L'outil a persisté dans l'article 700.
- Savoir, par l'écran, si je peux travailler dans un TGV ou une salle sans réseau. Le bandeau dit *Connecté* dès que le logiciel tourne.
- Empêcher une recherche internet après avoir demandé d'attendre ma confirmation.
- Recommander cet outil à un collègue magistrat, même pour de la formation.

## Findings

### F1 - L'écran promet le local et la confirmation ; la recherche web part sans moi
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j'ai fait** :
  1. Lecture de l'en-tête, du *Centre de confiance*, de *Confidentialité* et de *Services*.
  2. `GET /api/config/web-search` : `enabled: true`. `GET /api/config/` : `web_search_enabled: true`. Aucune préférence `web_search_enabled` n'est enregistrée : le défaut est donc allumé.
  3. Dans la conversation `c3123a0e-…`, après qu'on m'ait dit que je serais prévenue : « Cherche maintenant sur internet le programme de formation continue de l'ENM pour l'automne 2026. Si cette recherche quitte ma machine, dis-le AVANT d'envoyer la requête, et attends que je confirme. »
- **Ce que j'attendais** : soit un refus d'envoyer tant que je n'ai pas cliqué, soit un bandeau clair du type « cette requête va quitter le poste ».
- **Ce qui s'est passé** :
  - Le bouton *Contrôle des données* ouvre le *Centre de confiance*, qui écrit : « Données métier conservées localement ; secrets protégés par le trousseau système. » et « Les parcours raccordés indiquent leur destination et demandent une confirmation avant l’effet externe. » (interface : `CapabilityCenter.tsx` 584-587).
  - Sous le composeur : *Parcours réel · confirmation avant effet* (`ConversationCanvasPrototype.tsx` 1851). Dans *Plus d'outils* : *Toujours sous contrôle*, « confirmation sur les actions externes raccordées » (`CapabilityCenter.tsx` 432-437).
  - *Paramètres > Confidentialité* : « Toutes tes données sont stockées localement sur ta machine. Aucune donnée n'est envoyée à un serveur externe (sauf les requêtes aux modèles IA si tu utilises un provider cloud comme Anthropic, OpenAI ou Google). » (`PrivacyTab.tsx` 253-256). La recherche web n'est pas dans cette exception.
  - *Paramètres > Services* : *Recherche Web*, « Permet aux LLMs de chercher sur le web », interrupteur allumé (`ServicesTab.tsx` 304-307). L'onboarding classe ce risque en « low » : « Les recherches sont envoyées à DuckDuckGo ou Google (selon le moteur choisi). Tes requêtes peuvent être tracées. » (`textes.ts` 46-49).
  - L'API a exécuté `web_search` immédiatement. Bandeau : « Execution des outils: web_search... » (sans accent). Résultat en 1114 ms, champ `confirmation: null`. Le code appelle `execute_web_search` sans carte de confirmation (`chat.py` 2885-2890). Le défaut, sans préférence, est `True` (`chat.py` 2271). Le prompt dit au modèle : « Ne dis JAMAIS que tu ne peux pas accéder à internet […] si un outil le permet » (`chat.py` 2300-2302).
  - Après coup, le texte a écrit : « Ces informations proviennent de sources externes. Veuillez confirmer si vous souhaitez poursuivre. » puis « Aucune donnée ne quitte votre machine ». La requête était déjà partie. Confiance affichée : 100, `should_verify: false`.
- **Pourquoi ça compte pour moi** : je n'ai pas le droit de faire partir un nom, un thème de formation ou un projet d'intervention vers un moteur sans le savoir. Si l'écran me dit que rien ne sort, et que ça sort, je ferme.

### F2 - « Références juridiques » annonce un corpus vérifié ; ce n'est pas du droit processuel
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j'ai fait** : ouvrir *Plus d'outils*, lire la capacité *Références juridiques*. Puis demander un plan ENM et une question de CPC. Comparer avec le corpus réellement chargé.
- **Ce que j'attendais** : soit un vrai corpus de procédure civile, soit l'aveu que l'outil n'est pas une source de droit.
- **Ce qui s'est passé** :
  - L'écran décrit la capacité ainsi : « Mobiliser le corpus vérifié et signaler clairement les points à confirmer. » Traits : *Corpus juridique*, *Références vérifiées*, *Relecture humaine* (`CapabilityCenter.tsx` 255-260). Le bouton n'ouvre pas un écran juridique : il prépare une phrase dans le chat (`destination: { kind: 'prompt' }`).
  - Le corpus réel (`src/backend/app/data/legal_corpus.json`, vérifié le 2026-06-06) contient 12 entrées : pénalités de retard B2B, mentions de facture, franchise en base de TVA, droits d'auteur, loi Hoguet, rétractation consommateur, secret professionnel pénal, déclaration d'organisme de formation, prescription commerciale, intérêts moratoires. Rien sur le décret n° 2019-1333, rien sur les articles 514 et suivants du CPC.
  - Sur mon plan ENM, aucun extrait de ce corpus n'est apparu. Le modèle a inventé des articles, puis a ajouté « à vérifier sur Légifrance ».
- **Pourquoi ça compte pour moi** : « références vérifiées » est un mot de commissaire. Si c'est le droit des factures des TPE, qu'on le dise. Un collègue croira qu'il a Légifrance dans la machine.

### F3 - Sur une question que je connais, l'outil invente l'article et un code
- **Gravité** : bloquant
- **Nature** : limite_modele_local
- **Source** : les deux
- **Ce que j'ai fait** :
  1. Chat 1 (`d172e713-…`, 144 s) : préparer une intervention ENM de 3 heures sur l'exécution provisoire de droit depuis le décret n° 2019-1333. Consigne : ne citer un article que si l'on est certain, sinon dire qu'on ne sait pas.
  2. Chat 2, conversation neuve (`a0cf1421-…`, 91 s) : « un jugement civil de première instance est-il exécutoire de plein droit ? Quel article du CPC le dit ? L'article 700 a-t-il un rapport avec l'exécution provisoire ? »
- **Ce que j'attendais** : l'article 514 du CPC (exécution provisoire de droit depuis le 1er janvier 2020), les exceptions des articles 514-1 et suivants, et la réponse « non » sur l'article 700 (frais irrépétibles). À défaut, un « je ne sais pas, allez sur Légifrance ».
- **Ce qui s'est passé** :
  - Chat 1 : le décret n° 2019-1333, article 1er, « Création de la procédure d'exécution provisoire » ; article 2, « Conditions d'ouverture (montant des créances) ». CPC « articles 700 à 703 : dispositions générales sur l'exécution des jugements » ; « article 704 : exécution provisoire ». Circulaire du 1er juillet 2020 et rapport d'information de la commission des lois (2020) : je n'en ai jamais entendu parler sous cette forme, et l'outil ne les a pas cherchés. Le tout, suivi de « à vérifier sur Légifrance ».
  - Chat 2, sans les erreurs du premier tour pour se raccrocher : le principe (exécutoire de plein droit) est à peu près dit, puis attribué à l'article **700**. L'appel et le pourvoi « suspendent l'exécution provisoire » (c'est le contraire de la réforme). Exceptions inventées : « présomption de faillite » renvoyée à l'article L. 611-1 d'un « Code de la déontologie et de l'ethique de la profession juridique » (ce code n'existe pas ; L. 611-1, c'est le livre VI du code de commerce). Article 702 CPC présenté comme une expertise. Phrase finale : l'article 700 « est directement lié à l'exécution provisoire ». `uncertainty.is_uncertain: false`, `confidence_score: 100`.
  - Le prompt système demande d'accompagner **toute** référence d'un `[à confirmer sur Légifrance]`, même si le modèle se croit certain (`llm.py` 338-341). Le tampon devient un alibi : on affirme, on décharge.
  - Côté écran, rien n'indique que la réponse juridique n'est pas sourcée. Pas de pastille « hors corpus ». La carte *Références juridiques* reste disponible.
- **Pourquoi ça compte pour moi** : je n'enseignerai pas l'article 700 à l'ENM. Un auditeur moins méfiant recopierait. Le tampon Légifrance ne répare pas une phrase fausse : il l'habille.

### F4 - Rien n'avertit honnêtement quand le réseau manque, ou quand on en a besoin
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j'ai fait** : lire le bandeau d'état en tête d'écran ; chercher un mode hors ligne ; poser la question au chat ; puis déclencher une recherche web (F1). Je n'ai pas coupé le réseau de la machine (ce n'est pas à moi de l'arrêter).
- **Ce que j'attendais** : un état « hors ligne » distinct, et un refus explicite avant toute sortie.
- **Ce qui s'est passé** :
  - Le bandeau affiche *Connecté*, *Connexion...*, *Déconnecté* ou *Erreur* (`ConnectionStatus.tsx` 8-32). C'est l'état du moteur local, pas d'internet. Dans un TGV, si l'application tourne, je lirai *Connecté*.
  - Un crochet `useOnlineStatus` existe (`hooks/useOnlineStatus.ts`) et n'est branché sur aucun écran (seulement réexporté). Aucun libellé *hors ligne* dans l'accueil.
  - Le chat (`c3123a0e-…`, 79 s) a répondu que les fonctions locales marchent sans internet, et que `web_search` / l'e-mail « ne peuvent pas être utilisées hors ligne. Je vous préviens clairement si une action nécessite une connexion. » La phrase suivante de la même conversation a démenti ce « je vous préviens » (F1).
  - *À propos* : *L'assistante souveraine des entrepreneurs français*, phase *Alpha* (`AboutTab.tsx` 139-153). *Avancé* (masqué en mode standard) : pastille *Données 100% locales* (`AdvancedTab.tsx` 106). Le mot « souveraine » est aussi à l'accueil d'installation : « Ton assistante IA souveraine. Ta mémoire, tes données, ton business. » (`WelcomeStep.tsx` 57).
- **Pourquoi ça compte pour moi** : je prépare souvent dans le train. « Souveraine » et « 100 % local » ne veulent rien dire si une recherche part dès que le réseau existe, et si rien ne me dit quand il n'existe pas.

### F5 - L'export et l'effacement existent ; l'assistant n'indique pas le même chemin, et le chiffrement n'est pas dit à l'écran
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j'ai fait** : *Paramètres > Confidentialité* (visible en mode standard, sans *Avancé*). `GET /api/data/export` (200, JSON de portabilité). `GET /api/data/backups` (liste vide). `GET /api/config/stats`. Question au chat : où sont les données, comment exporter, comment tout effacer, la base est-elle chiffrée. Je n'ai lancé ni `DELETE /api/data/all` ni aucune restauration.
- **Ce que j'attendais** : un lieu, un bouton d'export, un bouton d'effacement, et la vérité sur le chiffrement, les trois au même endroit.
- **Ce qui s'est passé** :
  - L'écran est à peu près complet : *Exporter toutes mes données* ; *Créer une sauvegarde* avec *Passphrase de chiffrement* (« La sauvegarde est chiffrée par cette passphrase. ») ; *Supprimer toutes mes données* (« Efface les données métier, conversations, réglages personnels et index vectoriels. Les journaux d’audit légaux et les sauvegardes locales restent conservés. ») puis saisie de `SUPPRIMER` (`PrivacyTab.tsx` 264-307, 524-559).
  - L'onglet affirme le stockage local et ne dit pas que la base SQLite n'est **pas** chiffrée au repos. Le tableau de conservation justifie les *Conversations IA* par « Pas de données personnelles tierces » (`PrivacyTab.tsx` 50) : c'est faux dès que je tape un nom de formation, un collègue, un auditeur.
  - Le chat, lui, dit : dossier `~/.therese/`, SQLite non chiffrée, « copiez le dossier » pour exporter, « supprimez le dossier » pour effacer. Il ne mentionne ni le bouton d'export, ni la confirmation `SUPPRIMER`, ni la conservation des journaux. `GET /api/config/stats` donne, sur cette instance, un autre répertoire que `~/.therese/` ; *À propos* répète `~/.therese/` pour les mises à jour (`AboutTab.tsx` 233).
  - *THÉRÈSE respecte le RGPD* (`PrivacyTab.tsx` 241-243) est une affirmation, pas une démonstration. L'export par conversation (`GET /api/chat/conversations/{id}/export`) renvoie une URL relative `/api/skills/download/…`.
- **Pourquoi ça compte pour moi** : avant d'y mettre un calendrier de formations, je veux savoir ce qui survit à un effacement, et si un vol de machine livre la base en clair. Là, l'écran et l'assistant se contredisent.

### F6 - L'accueil et la trame parlent d'un autre métier
- **Gravité** : confort
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j'ai fait** : poser une intervention ENM comme on pose un dossier de formation. Accueil, *Espaces de travail*, *Rédiger un document*, *Générer la trame*, calendrier.
- **Ce que j'attendais** : un plan, des sources, un calendrier. Des mots neutres suffisent.
- **Ce qui s'est passé** :
  - Accueil : « J’ai regroupé ce qui mérite ton attention. Tu peux agir ici, sans chercher le bon module. » (`ConversationCanvasPrototype.tsx` 1570-1571). Les cinq gestes : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider* (`etabli.ts` 25-30). Brief vide : « Branche tes mails pour que je te prépare la journée » / *Brancher mes mails* (`TodayDashboardCard.tsx` 143-152). *Mise en route* : *Connecter ta messagerie*, *Compléter le profil de facturation* (`SetupChecklist.tsx` 26-45). Je ne brancherai pas ma messagerie professionnelle sur un outil personnel.
  - *Nouveau projet*, exemple « Refonte site web » (`ProjectModal.tsx` 290-313). J'ai créé le mien quand même.
  - Trame générée en 66 s : *Introduction*, *Cadre juridique*, *Méthodologie*, *Exemples concrets*, *Défis et solutions*, *Questions et réponses*, *Calendrier*, puis des sous-parties numérotées **après** les titres (profondeur 1 à partir de l'ordre 80, plus rattachées). *Étapes de l'exécution provisoire* : « Procédure détaillée avec les obligations des parties ». *Préparation des supports* : « Création des slides ». Ce n'est pas une séance ENM. Le chat n'a pas vu ce document (`search_files` : `found: false`).
- **Pourquoi ça compte pour moi** : je peux vivre avec un vocabulaire d'entrepreneur si le fond est juste. Le fond ne l'est pas. Reste une application de devis qui me tutoie.

## Verdict

Je ne rouvre pas demain. Un outil qui attribue l'exécution provisoire à l'article 700, avec une confiance à 100 %, n'a pas sa place dans une préparation de formation, même hors juridiction. L'écran qui promet le local et la confirmation, pendant qu'une recherche web part sans clic, règle la question de confiance. Je ne le recommanderais à aucun collègue : le risque n'est pas que ça serve mal, c'est que ça ait l'air de servir.
