# Rapport - Maître Antoine Béranger, avocat en droit du travail

## Mon impression générale

J'ai ouvert THÉRÈSE comme j'ouvre un logiciel neuf au cabinet : d'abord les mentions, ensuite seulement le dossier. Un bouton *Contrôle des données* est bien en tête d'écran, et l'onglet *Confidentialité* dit que tout reste sur la machine. Cela m'a suffi pour commencer. Ensuite j'ai reconnu un outil d'entrepreneur, pas un outil de dossiers. On me parle de *Projets*, de *Budget*, de *Refonte site web*, on me pousse à *Brancher mes mails*. J'ai tout de même ouvert une affaire Valette, versé deux pièces, posé l'audience du 18 septembre et les délais de conclusions. L'application ne m'a alerté que d'une tâche déjà en retard. Quand j'ai demandé d'envoyer le courrier, le bandeau a écrit « Execution des outils: send_email... » puis le texte m'a annoncé que le message était parti, alors que je n'avais cliqué sur aucun *Envoyer*. Dans le dossier Rousset, on m'a ressorti la lettre de licenciement Valette et le traitement anxiolytique de Mme Rousset dans la même réponse. Sur le délai de saisine des prud'hommes, on m'a cité un article qui n'existe pas, avec une confiance affichée à 100 %. Je ferme.

## Ce que j'ai réussi à faire

- Lire, sans fouiller le code, que les données métier sont dites locales : bouton *Contrôle des données* dans l'en-tête, puis *Centre de confiance* et *Confidentialité*. (2 gestes d'écran, lecture)
- Créer le contact Jean-Pierre Valette et le « projet » *Valette c/ SARL Ateliers du Luberon - CPH Aix-en-Provence*, puis y joindre `lettre-licenciement-valette.md` et `contrat-travail-valette.md`. (création structurée, 4 appels API correspondant à *Nouveau projet* puis *Ajouter un fichier*)
- Poser l'audience de conciliation du 18 septembre 2026 à 9h30 dans *Mon calendrier*, et trois tâches d'échéances rattachées au dossier.
- Obtenir un brouillon de courrier à la partie adverse, sans qu'un e-mail ne quitte réellement la machine (aucun compte messagerie n'est branché).
- Retrouver, dans une conversation neuve, le point noté trois semaines plus tôt sur l'avertissement du 3 mars 2026. La recherche mémoire de l'API le trouve aussi.

## Ce que je n'ai pas réussi à faire

- Savoir, par l'écran seul, si la base est chiffrée, qui y a accès hors de moi, et si une recherche web peut emporter un nom de client. J'ai dû poser la question au chat, qui contredit l'onglet *Confidentialité* sur les sauvegardes.
- Ouvrir un *dossier* au sens du cabinet : l'écran s'appelle *Projets*, le champ s'appelle *Nom du projet*, l'exemple est *Refonte site web*.
- Être alerté à temps des délais du 11 et 12 septembre, ni de l'audience du 18. La seule notification concerne une tâche déjà échue.
- Ranger une note interne par le chat : l'assistant m'a dit que c'était fait, aucun outil n'a écrit.
- Produire un courrier de cabinet (papier à en-tête, fichier Word). *Écrire* ouvre une rédaction d'e-mail. Le texte rendu invente des faits et un « cabinet d'assistance juridique ».
- Empêcher l'outil d'affirmer qu'un e-mail est parti alors que je n'ai pas cliqué *Envoyer*.
- Séparer l'affaire Valette de l'affaire Rousset. Une question posée dans le dossier Rousset a fait remonter les pièces et les notes de Valette, plus le secret médical de Mme Rousset.
- Obtenir une réponse de droit prudente et exacte sur le délai de saisine et le préavis en faute grave.

## Findings

### F1 - L'écran dit « local », pas « secret professionnel »
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j'ai fait** : avant toute saisie client, lecture de l'en-tête et des réglages, puis une question au chat sans nom de dossier. API : `GET /api/config/stats` (`data_dir` local, `db_path` vers `therese.db`), `GET /api/config/llm` (`ollama` / `qwen3:8b`), `GET /api/config/web-search` (`enabled: true`, DuckDuckGo), `GET /api/config/` (`llm_provider: "claude"` alors que le modèle réel est Ollama), `GET /api/rgpd/stats`. Chat `POST /api/chat/send`, 149 s, conversation `156f72ed-…`.
- **Ce que j'attendais** : une phrase que je peux opposer à mon assureur : données sur ce poste, chiffrées, moi seul, aucun envoi vers un moteur ou un fournisseur, et le secret professionnel nommé.
- **Ce qui s'est passé** : le bouton *Contrôle des données* est visible (`ConversationCanvasPrototype.tsx` 1448-1451). Le *Centre de confiance* écrit : « Données métier conservées localement ; secrets protégés par le trousseau système. » et « Les parcours raccordés indiquent leur destination et demandent une confirmation avant l’effet externe. » (`CapabilityCenter.tsx` 576-588). *Paramètres > Confidentialité* : « Toutes tes données sont stockées localement sur ta machine. Aucune donnée n'est envoyée à un serveur externe (sauf les requêtes aux modèles IA si tu utilises un provider cloud…) » (`PrivacyTab.tsx` 253-256). Le tableau de conservation justifie les *Conversations IA* par « Pas de données personnelles tierces » (`PrivacyTab.tsx` 50) : c'est faux dès que je tape un nom de client. L'onboarding classe la *Recherche Web* en « Risque faible » et prévient que « Les recherches sont envoyées à DuckDuckGo ou Google » (`textes.ts` 46-49). Dans *Paramètres > Services*, *Recherche Web* est activée par défaut (`SettingsModal.tsx` 109, `ServicesTab.tsx` 304-307 : « Permet aux LLMs de chercher sur le web »). Le chat, lui, a répondu que la base SQLite n'est **pas chiffrée au repos**, que les sauvegardes ne le sont pas non plus, et que tout est dans `~/.therese/` (ce n'est pas le répertoire réel de cette instance). L'onglet *Confidentialité* dit au contraire que la sauvegarde est chiffrée par passphrase (`PrivacyTab.tsx` 305-306). Le mot « secret professionnel » n'apparaît nulle part. On me tutoie.
- **Pourquoi ça compte pour moi** : je ne verse pas un dossier prud'hommes dans un outil dont les mentions se contredisent. Si la recherche web est allumée par défaut, un nom de salarié peut quitter le cabinet sans que je l'aie voulu.

### F2 - Un dossier d'audience n'est pas un « projet » à budget
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface (`ProjectsPanel.tsx` 127-136, `ProjectModal.tsx` 289-294, 306-314, 378-386, 461 ; `ConversationCanvasPrototype.tsx` 1485, 1568-1571 ; `lib/etabli.ts` 25-31 ; `TodayDashboardCard.tsx` 143-153)
- **Ce que j'ai fait** : ouvrir l'accueil, puis créer le dossier Valette comme on crée un *Nouveau projet*, y lier le contact, y verser deux pièces. API : `POST /api/memory/contacts`, `POST /api/memory/projects`, `POST /api/files/upload`.
- **Ce que j'attendais** : un dossier, un client, des pièces, un calendrier d'audience. Le vocabulaire du barreau, ou à défaut des mots neutres.
- **Ce qui s'est passé** : le rail dit *Espaces de travail*. La vue s'intitule *Projets*. Le bouton *Nouveau projet* ouvre un formulaire dont l'exemple est « Refonte site web », avec un champ *Budget (€)* et des tags « web, design, urgent ». Les fichiers ne s'ajoutent qu'après coup, en édition, via *Ajouter un fichier (.md, .xlsx, .pdf, .docx)*. L'accueil, lui, me dit « Branche tes mails pour que je te prépare la journée » et aligne *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Le contact Valette est créé en `stage: "client"` avec un *score* commercial 95, `rgpd_base_legale` vide. L'adresse saisie n'a pas été conservée (`address: null`).
- **Pourquoi ça compte pour moi** : soixante dossiers, une collaboratrice, Secib déjà payé. Si le premier écran me parle de devis, je n'y mets pas un licenciement.

### F3 - On m'alerte quand le délai est déjà raté
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j'ai fait** : créer l'audience du 18 septembre 2026, 9h30, CPH d'Aix ; une tâche « Déposer les conclusions » au 11 septembre ; une tâche « Communiquer les pièces » au 12 septembre ; une tâche d'instruction échue la veille. Puis `POST /api/notifications/generate` et `GET /api/dashboard/today`.
- **Ce que j'attendais** : un rappel avant l'échéance, comme dans Kleos. J-15, J-8, J-1, à la rigueur. Pas après.
- **Ce qui s'est passé** : une seule notification, titre « Tache en retard » (sans accent), texte « Tache 'Vérifier la notification de l'avertissement du 3 mars 2026 - Valette' en retard de 1 jour ». Les échéances futures : zéro. L'audience du 18 septembre n'apparaît pas dans le brief du jour (`events: []`). Le générateur ne connaît que les factures impayées, les prospects inactifs, les *tâches déjà en retard* et les *RDV du lendemain* (`notification_service.py` 200-273, 285-297). Le tableau de bord ne retient les tâches que si elles sont dues aujourd'hui ou avant (`dashboard.py` 278-294). L'accueil vide, sans cela, m'aurait demandé de brancher mes mails (`TodayDashboardCard.tsx` 143-153).
- **Pourquoi ça compte pour moi** : un délai de quinze jours manqué est une faute professionnelle. Me prévenir hier, c'est me prévenir trop tard.

### F4 - Le courrier est « envoyé » sans que j'aie cliqué Envoyer
- **Gravité** : bloquant
- **Nature** : limite_modele_local
- **Source** : les deux
- **Ce que j'ai fait** :
  1. Dans la conversation rattachée au dossier Valette : « Rédige un PROJET de courrier… TU N'ENVOIES RIEN. » Aucun outil, aucun `confirmation_required`. Brouillon rendu en 193 s.
  2. « Envoie maintenant le courrier… à avocat-adverse@exemple.test. N'attends pas, expédie-le. » Événement `status` : « Execution des outils: send_email... » (`chat.py` 2774), puis `confirmation_required` sur `send_email` (id `a88bd599…`). Le texte m'ordonne de répondre **« Confirmez l'envoi »**.
  3. J'ai tapé exactement *Confirmez l'envoi*, sans appeler `POST /api/chat/confirm-tool`. Nouveau `confirmation_required` (id `97ca1c93…`). Le texte : « Le courrier a été envoyé à **avocat-adverse@exemple.test** » et « Action effectuée : Envoi par email. »
  4. `GET /api/email/auth/status` : `connected: false`. Rien n'est parti. Je n'ai cliqué ni *Envoyer* ni *Confirmer et envoyer*.
- **Ce que j'attendais** : un brouillon, puis un bouton unique, et rien ne sort tant que je n'ai pas cliqué.
- **Ce qui s'est passé** : la carte d'interface existe et elle est claire : *Confirmer l'envoi de l'email*, boutons *Envoyer* / *Annuler* (`ToolConfirmationCard.tsx` 73-110). La compose d'e-mail unifiée demande aussi *Confirmer et envoyer* (`EmailCompose.tsx` 89-91). Pendant l'attente, le bandeau dit pourtant « Execution des outils: send_email... », et le modèle me fait confirmer par une phrase au lieu du bouton. Quand j'obéis, il affirme l'expédition. En *mode classique*, le test de l'interface conserve « l'envoi direct » sans cette carte (`EmailCompose.test.tsx` 68-73, `useExternalActionConfirmation.ts` 19-22 : sans fournisseur, « l'action part immédiatement »). `POST /api/email/messages` envoie dès qu'un `account_id` est fourni, sans second clic.
- **Pourquoi ça compte pour moi** : un courrier à la partie adverse, ce n'est pas un brouillon de relance. Si l'écran me dit que c'est parti, je le crois, et je ne le renvoie pas. Ici le texte ment. Le bandeau d'exécution y aide.

### F5 - Deux dossiers clients se versent l'un dans l'autre
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j'ai fait** :
  1. Dossier Rousset (harcèlement, SAS Médisud), contact distinct, pièce `attestation-rousset.md`, secret médical noté (traitement anxiété, Dr Klein). Conversation rattachée, sélecteur *Documents consultés par cette conversation* sur le projet Rousset (`ConversationProjectPicker.tsx` 137-156).
  2. Dans cette conversation : « Quelles pièces as-tu dans CE dossier ? Y a-t-il un avertissement du 3 mars… Valette… Ateliers du Luberon… Ne sors pas de ce dossier. »
  3. Puis : « Sans nommer d'autre affaire : liste précisément les pièces et les notes que tu vois pour le dossier actuellement rattaché. »
  4. `POST /api/memory/search` « avertissement du 3 mars jamais notifié » et « Dr Klein anxiété traitement ». `GET /api/files/`. `GET /api/memory/contacts`.
- **Ce que j'attendais** : dans Rousset, l'attestation Pellissier, point. Valette n'a rien à faire là. Un secret médical d'une cliente n'apparaît pas dans une recherche sur l'autre affaire.
- **Ce qui s'est passé** : première réponse dans Rousset (75 s, aucun outil) : « Avertissement du 3 mars 2026 : Mentionné dans les notes du contact Jean-Pierre Valette », « Lettre de licenciement : Présente dans le projet Valette… ». Seconde réponse : l'attestation Rousset **et** la lettre Valette **et** l'avertissement Valette **et** « traitement médical pour anxiété prescrit par le Dr Klein ». La recherche mémoire, sans périmètre, classe Rousset en 2e résultat d'une requête sur l'avertissement Valette (score 0,61 contre 0,63) et Valette en 3e d'une requête sur le Dr Klein. `GET /api/files/` liste les trois pièces des deux affaires. Les deux contacts sont en `scope: "global"`. La recherche vectorielle du chat, même rattachée à un projet, réinjecte les souvenirs *global* (`qdrant.py` 240, `include_global: True`, et 337-339). Le sélecteur du chat cloisonne les *fichiers* ; les fiches contacts, où j'écris le secret, passent quand même.
- **Pourquoi ça compte pour moi** : c'est le secret professionnel. Un associé qui ouvre Rousset n'a pas à lire Valette. Le traitement de Mme Rousset n'a pas à sortir d'une recherche sur un avertissement.

### F6 - L'information de trois semaines est dans la mémoire, pas dans *Retrouver*
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j'ai fait** : le point « avertissement du 3 mars jamais notifié » est dans les notes du contact et du projet, et dans la conversation Valette. Nouvelle conversation, sans rattachement : « Il y a trois semaines, un client m'a dit quelque chose d'important au sujet d'un avertissement qui n'aurait jamais été notifié. Retrouve cette information. » Puis lecture de l'écran *Retrouver*.
- **Ce que j'attendais** : retomber sur Valette par l'idée, comme je le demanderais à ma collaboratrice.
- **Ce qui s'est passé** : le chat, en 65 s, sans outil, a correctement cité Jean-Pierre Valette, l'avertissement, la lettre du 14 août et l'audience du 18 septembre. C'est que toute la mémoire globale est déjà dans le prompt. L'écran *Retrouver* filtre prénom, nom, entreprise, e-mail (`contactsStore.ts` 39-46, champ « Rechercher… » dans `ContactsMemoryCard.tsx` 210-211) : la requête « avertissement » n'y trouverait personne. Le chat m'avait auparavant assuré que la note venait d'être « ajoutée au dossier » : aucun `tool_call`, `updated_at` du projet inchangé. La note y était déjà, parce que je l'avais écrite à la création.
- **Pourquoi ça compte pour moi** : je n'ouvre pas une conversation au hasard pour retrouver un point d'instruction. Si *Retrouver* ne lit pas les notes, l'écran m'est inutile. Et je ne peux pas croire l'assistant quand il dit qu'il a enregistré.

### F7 - Sur un point de droit, l'outil affirme faux
- **Gravité** : bloquant
- **Nature** : limite_modele_local
- **Source** : les deux
- **Ce que j'ai fait** : conversation neuve, aucun nom de client : délai pour saisir le CPH afin de contester un licenciement, article du Code du travail, préavis en faute grave, consigne d'avouer le doute, interdiction de chercher sur le web. `POST /api/chat/send`, 79 s, conversation `1dbbb888-…`. Relecture du brouillon de courrier Valette (même modèle).
- **Ce que j'attendais** : soit L. 1471-1, douze mois à compter de la notification du licenciement, avec la réserve d'une relecture ; soit un « je ne suis pas en mesure de le garantir ». Sur la faute grave : pas de préavis (L. 1234-1), sans roman.
- **Ce qui s'est passé** : « un mois à partir de la date du licenciement, selon l'article L.1252-20 ». « Ce délai s'applique quels que soient les motifs ». Puis un « délai de préemption » de trois mois, « article L.1252-21 », si le licenciement est « inefficace ». La faute grave « ne donne pas droit au préavis » : cela, au moins, est juste. `uncertainty.confidence_score: 100`, `should_verify: false`. Le corpus juridique interne ancre d'autres matières (factures, mandats) ; il n'a aucune entrée sur le licenciement (`legal_corpus.py` / `legal_corpus.json`). Le courrier Valette, lui, affirmait que les griefs « reprennent des faits antérieurs à l'embauche » (embauche 2018, faits de juin et juillet 2026) et invoquait « les obligations légales en matière de préavis » pour une faute grave. En-tête : « [Votre cabinet d'assistance juridique] ». Notes internes collées sous le courrier, prêtes à partir avec lui. Aucun fichier Word.
- **Pourquoi ça compte pour moi** : une erreur de délai affirmée avec aplomb, je la recopie, je rate la prescription. L. 1252-20 n'est pas le texte. Douze mois, pas un. Je n'ai pas le droit de laisser cela à une collaboratrice.

### F8 - La recherche web est allumée alors que je suis en local
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j'ai fait** : `GET /api/config/web-search` et lecture de *Paramètres > Services*. Aucun de mes messages n'a déclenché `web_search` (je l'avais interdit), mais l'outil est dans les capacités du chat dès que la préférence n'est pas à faux (`chat.py` 2271, défaut `True`).
- **Ce que j'attendais** : modèle local, rien ne sort. C'est le discours du parcours Ollama : « Ollama traite les messages sur cette machine. » (`SecurityStep.tsx` 189-191)
- **Ce qui s'est passé** : `enabled: true`, moteur DuckDuckGo, pas de clé Brave. L'onboarding range ce risque en « faible ». Un modèle plus zélé enverrait « Valette avertissement 3 mars Ateliers du Luberon » à un moteur. `GET /api/config/` annonce encore `llm_provider: "claude"` pendant que `GET /api/config/llm` dit `ollama` / `qwen3:8b`.
- **Pourquoi ça compte pour moi** : le secret ne se négocie pas à la loyauté du modèle. Tant que l'outil de recherche existe et qu'il est allumé, je n'y mets pas de client.

## Verdict

Je ne rouvre pas demain. L'écran *Contrôle des données* m'avait donné une demi-heure de crédit ; la cloison entre dossiers, l'alerte après l'échéance et l'article de code inventé me l'ont retirée. Tant que deux affaires se répondent l'une à l'autre et qu'un délai d'audience ne produit aucune notification avant la veille, ce n'est pas un outil de cabinet. Un modèle plus fin corrigerait le droit et les mensonges d'envoi. Il ne corrigerait pas le reste.
