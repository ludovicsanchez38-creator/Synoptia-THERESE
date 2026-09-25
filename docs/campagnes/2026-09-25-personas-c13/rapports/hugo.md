# Hugo, développeur freelance : trace de la campagne

> Campagne c13, 25/09/2026. Instrument : Playwright MCP, viewport 1440×900, DPR 1, fr-FR, thème sombre (réglé par Hugo au premier geste).
> Frontend http://127.0.0.1:1420, moteur jetable http://127.0.0.1:17393, données laissées par Claire (profil « Claire Exemple Coaching », trois contacts, deux séances, un devis et une facture, une conversation).
> Garde d'environnement à 10:05 : `{ visible: "visible", horloge: 699472 }`, viewport initial 1280×800 passé à 1440×900. Stockage NON purgé (consigne de l'orchestrateur : on arrive sur l'application configurée par Claire).
> Captures : `captures/hugo/NN-<capacite>-<etape>.png`. Chemin des fichiers Playwright : racine `~`, chemins absolus utilisés.

## Mon impression (première personne, cinq à dix lignes)

Je change de sujet toutes les heures, et c'est là que THÉRÈSE me coûte. Créer mes trois projets a été rapide, mais Entrée ne valide aucun formulaire, et « ouvrir » un projet me donne un formulaire de modification où je ne retrouve ni mes conversations ni mon document.
Le même objet s'appelle projet, dossier ou « documents généraux » selon l'écran, et « Documents » veut dire cinq choses différentes.
Pendant qu'une réponse locale tourne (cinq à sept minutes), je ne peux aller nulle part ; dans l'atelier, au contraire, partir jette ma trame sans un mot.
Mon dossier Orion est « Terminé » dans les travaux alors qu'aucun fichier n'a été lu, et le chat m'assure, « confiance haute », que specifications.md n'existe pas.
Le lendemain, ma conversation Orion s'appelle « Nouvelle conversation » : ni le tiroir ni ⌘K ne la retrouvent. Et mon brouillon Orion m'a suivi dans la conversation Veille, prêt à partir dans le mauvais projet.
Ce qui tient : les contacts ne fuient pas d'un projet à l'autre, Échap rend presque toujours le focus, ⌘K et ⌘B marchent hors du champ de message, et le thème sombre est propre.

## Parcours (un bloc par parcours)

Blocs numérotés d'après ma fiche, rangés dans l'ordre où je les ai vécus.

### 0. Réglage : passer en thème sombre, au clavier

Préconditions : arrivée sur « Devis et factures » laissé par Claire, thème clair.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 0.1 | Arrivée | Un écran connu | « Devis et factures » ouvert (état laissé par Claire), thème clair | 01-arrivee-accueil.png | ok |
| 0.2 | Échap | Revenir d'où l'on vient | Retour à la vue « Facturer un client », focus rendu sur « Ouvrir Devis et factures » | (mesure DOM, pas de capture distincte) | ok |
| 0.3 | ⌘, | Les réglages | Paramètres s'ouvre, focus sur « Fermer les paramètres » | 02-reglage-theme-sombre.png | ok |
| 0.4 | « Accessibilité et affichage » > « Sombre » | Thème sombre appliqué | Appliqué à chaud ; l'encadré annonce quatre raccourcis : ⌘K palette, ⌘B conversations, ⌘M mémoire, ⌘D décision | 02-reglage-theme-sombre.png | ok |
| 0.5 | Échap | Fermer, focus rendu | Fermé, focus rendu sur « Ouvrir Devis et factures » | 03-reglage-accueil-sombre.png | ok |

Arbre d'accessibilité : dialogue « Paramètres », `tablist` « Rubriques des paramètres », groupe radio « Thème de l'interface » ; focus initial sur le bouton de fermeture.

### 1. Trois projets : les créer, en ouvrir un, rattacher une conversation à chacun

Préconditions : aucun projet (`GET /api/memory/projects` = `[]`).
Gestes comptés pour le premier projet au clavier : rail « Projets » (1 clic), Tab, Entrée, saisie du nom, Entrée (sans effet), saisie description, 10 Tab jusqu'à « Créer » (ou tags puis 2 Tab), Entrée.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1.1 | Rail « Projets » | La liste, vide | « Aucun projet. Crée ton premier projet pour rassembler les contacts, documents et tâches d'une même affaire. » + « Nouveau projet » (deux fois) ; focus sur le titre « Projets » | 04-projets-ouvert-vide.png | ok |
| 1.2 | Tab puis Entrée | Le formulaire | Tab atteint « Nouveau projet » (anneau visible), Entrée ouvre « Nouveau projet », focus dans « Nom du projet » | 05-projets-formulaire-vide.png | ok |
| 1.3 | Je tape « Site association » puis Entrée | Le projet est créé (le nom est le seul champ obligatoire) | Rien : le dialogue reste ouvert, `GET /api/memory/projects` = `[]`. La modale n'a pas de `<form>` (`ProjectModal.tsx`, `handleSave` seulement sur le clic), alors que la modale d'agenda en a un | 06-projets-site-association-entree.png | bug_candidate (hugo-01) |
| 1.4 | Description, tags « asso, web », Tab Tab, Entrée sur « Créer » | Créé | Créé, dialogue fermé, focus rendu sur « Nouveau projet » ; aucun message, la carte apparaît sous « Actif » | 07-projets-site-association-cree.png | ok |
| 1.5 | « API client Orion » et « Veille IA » de la même façon | Trois projets | Trois cartes sous « Actif », conformes à l'API (trois projets `scope: global`). Les tags saisis n'apparaissent nulle part sur les cartes ; aucun champ pour filtrer la liste | 08-projets-trois-crees.png | proposal (hugo-02) |
| 1.6 | Clic sur « API client Orion » | Ouvrir le projet : ses conversations, documents, tâches, contacts (ce que promettait l'état vide) | Un dialogue « Modifier le projet » : nom, description, statut, un seul « Contact associé », budget, notes, « Dossier synchronisé », « Fichiers du projet », tags. Aucune conversation, aucune tâche, aucun document de l'atelier | 09-projets-orion-ouvert.png, 10-projets-orion-bas-du-formulaire.png | bug_candidate (hugo-03) |
| 1.7 | Échap | Fermer, focus rendu | Fermé, focus rendu sur la carte « API client Orion » | (mesure DOM) | ok |
| 1.8 | Rail « Nouvelle conversation » | Une conversation neuve, focus dans le message | Écran « Nouvelle conversation ». Le projet se choisit dans un sélecteur en haut à droite nommé « Dossier de cette conversation : fichiers rattachés, carnet partagé », options « Documents généraux », les trois projets, « Tous les projets ». Focus resté sur le bouton du rail (rien dans le champ de message) | 11-rattacher-nouvelle-conversation.png | bug_candidate (hugo-04), observation (focus) |
| 1.9 | Je choisis « API client Orion » | Conversation rattachée | L'API crée aussitôt une conversation vide « Nouvelle conversation » avec `project_id` d'Orion et `memory_scope: project` | 12-rattacher-orion-choisi.png | ok |
| 1.10 | Message « Orion : on a retenu la variante B… » + Entrée | Envoi, réponse locale | Envoyé ; titre de la conversation = les 50 premiers caractères ; « Avec un modèle local, cela peut prendre plusieurs minutes. » Journal : outils fournis à 10:08:42, `search_files` appelé à 10:10:01 | 13-rattacher-orion-envoye.png | ok |

| 1.11 | Réponse | Une réponse | 4 min 35 s plus tard (journal : `Stream complete: 2109 tokens in 274781ms`), après `search_files` × 2 et `search_emails` : « Je n'ai pas trouvé d'informations spécifiques concernant la variante B… » (normal : aucun fichier encore). Vouvoiement et compteur « 30058 tokens » déjà signalés par Claire | 18-rattacher-orion-reponse.png | ok |
| 1.12 | Côté moteur, la conversation Orion | Le titre que je vois à l'écran | L'écran et le tiroir disent « Orion : on a retenu la variante B (fonctions) le 2… » ; `GET /api/chat/conversations/b1bf840a…` rend `"title": "Nouvelle conversation"`, `message_count: 2`, `updated_at` égal à la création (08:08:20). Cause lue : `src/backend/app/routers/chat.py` l. 1253-1263, le titre n'est tiré du premier message que si la conversation n'existe pas ; choisir le projet d'abord la crée sous le titre par défaut | (réponse API citée) | bug_candidate (hugo-06), effet vérifié au parcours 5 |
| 1.13 | Nouvelle conversation, choix « Veille IA », message | Conversation rattachée à Veille IA | Mon outil a raté le sélecteur (deux `select` dans la page, erreur d'instrument) : le message est parti en « Documents généraux ». J'ai rattaché après coup, pendant la génération : le sélecteur reste actif, `PATCH …/project` 200, l'API rend `project_id` de Veille IA et `memory_scope: project`. Cette conversation-là prend bien son titre du message | 19-rattacher-veille-envoye.png, 20-rattacher-veille-apres-coup.png | ok |

Arbre d'accessibilité : liste des projets = pour chaque carte un `div role="button"` « sortable » sans nom (poignée de glisser), le bouton du projet, « Supprimer <projet> » : trois arrêts de tabulation par projet. Le sélecteur de projet de la conversation est un `combobox` nommé « Dossier de cette conversation : fichiers rattachés, carnet partagé ».

### 2. Changer de sujet : passer d'un projet à l'autre, compter les gestes, retrouver où j'en étais

Préconditions : conversation Orion en cours de génération (modèle local, 4 à 5 minutes par réponse).

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 2.1 | Pendant la réponse Orion, rail « Nouvelle conversation » | Ouvrir un autre sujet ; la réponse Orion continue et m'attend | Refusé : toast « Réponse en cours. Arrête la réponse avant de changer de vue ou de conversation. » Avec un modèle local, cela veut dire 4 à 5 minutes bloqué sur un sujet, ou jeter la réponse | 14-changer-nouvelle-pendant-generation.png | proposal (hugo-07) |
| 2.2 | Même toast, je cherche le bouton d'arrêt | Le bouton « Arrêter la réponse » accessible | Le toast (x 1040-1424, y 785-884) recouvre le bouton « Arrêter la réponse » (x 1315-1359, y 792-836) : `document.elementFromPoint` au centre du bouton rend le `<p>` du toast. Le message me demande d'arrêter et cache le bouton pour le faire | 17-changer-toast-couvre-arreter.png | bug_candidate (hugo-08) |
| 2.3 | Rail « Conversations » pendant la réponse | Le tiroir | Le tiroir s'ouvre (autorisé). Aucune ligne ne dit à quel projet appartient la conversation | 15-changer-tiroir-pendant-generation.png | proposal (hugo-09) |
| 2.4 | « Nouvelle conversation » en bas du tiroir | Idem 2.1 | Refus affiché dans le tiroir, avec une autre phrase : « Arrête la réponse en cours avant de changer de conversation. » | 16-changer-refus-nouvelle-conversation.png | observation (deux formulations) |
| 2.5 | Hors génération, rail « Nouvelle conversation » | Focus dans le champ de message | Le focus reste sur le bouton du rail ; 18 arrêts de tabulation jusqu'au champ (Conversations, Projets, Paramètres, Plus d'outils, profil, sélecteur de projet, Fermer, 4 cartes, 4 actions rapides, modèle, Joindre) | 11-rattacher-nouvelle-conversation.png (état), mesure DOM | proposal (hugo-05) |
| 2.6 | Réponse « Veille » (« Réponds juste noté ») | Quelques secondes pour un mot | 7 min 10 s : journal `Ollama (gemma4-tia:latest): réponse vide, aucun contenu reçu` à 10:20:01 (l'écran n'en dit rien, bulle vide et curseur), puis `First token latency: 430204ms`, « noté » à 10:21:13. Sept minutes pendant lesquelles je ne peux changer ni de vue ni de conversation (2.1) | 21-rattacher-veille-attente-5min.png, 22-rattacher-veille-reponse-vide.png, 23-rattacher-veille-reponse-7min.png | observation (lenteur du modèle local sur cette machine ; l'avertissement « réponse vide » reste invisible à l'écran) |
| 2.7 | Depuis Projets : ⌘B | Le tiroir, prêt à naviguer | Le raccourci annoncé marche : tiroir ouvert, focus sur le conteneur « Historique des conversations » (`tabindex=-1`) | 30-changer-cmd-b-tiroir.png | ok |
| 2.8 | Flèche bas | Descendre dans la liste | Rien : il faut Tab. Tab × 3 (chaque conversation a un second arrêt « Actions pour … ») pour atteindre Orion, anneau de focus visible (3 px) | 31-changer-focus-orion-tiroir.png | observation |
| 2.9 | Entrée sur Orion | La conversation Orion, focus dans la conversation ou le champ de message | Conversation ouverte (2 messages, sélecteur « API client Orion »), mais le focus atterrit sur le bouton « Projets » du rail, l'écran que je quittais ; 12 Tab jusqu'au champ de message. Même chose en 1.8 : quitter Projets rend le focus à « Projets » | 32-changer-orion-rouvert-focus-projets.png, mesure DOM | bug_candidate (hugo-10) |

Console des parcours 1 et 2 : aucune erreur (la seule de la session est le 409 du parcours 3). Réseau : `PATCH /api/chat/conversations/b1bf840a…/project` (n° 1041) et `…/1612f518…/project` (n° 1154) en 200, `POST /api/chat/send` (n° 1046, 1151) en 200 ; aucune requête hors 127.0.0.1.

Gestes comptés pour passer de « Projets » à la conversation Orion au clavier : ⌘B, Tab × 3, Entrée, puis Tab × 12 pour écrire : 17 touches. À la souris : 2 clics (rail « Conversations », ligne), puis un clic dans le champ.

### 4. Un dossier de travail : relier `dossier-orion` au projet, synchroniser, suivre l'indexation, interroger le chat

Préconditions : projet « API client Orion » sans dossier ; `/tmp/therese-demo-c13/dossier-orion` contient `README.md` (174 o), `docs/notes-reunion.txt` (102 o), `docs/specifications.md`.
Gestes : rail « Projets », carte Orion, défilement du dialogue, saisie du chemin, « Attacher », « Préparer la synchronisation », « Appliquer » : 7 gestes.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 4.1 | Projets > Orion, je tape le chemin dans « Chemin du dossier à synchroniser » puis Entrée | Attacher | Entrée ne fait rien (même cause que hugo-01) ; il faut cliquer « Attacher ». L'exemple grisé « /Users/toi/Documents/mon-projet » ressemble à une valeur | 24-dossier-chemin-saisi.png | observation |
| 4.2 | « Attacher » | Dossier attaché | Attaché aussitôt (`racine: /private/tmp/…`, `generation: 1`), sans « Mettre à jour », alors que les autres champs du même dialogue attendent ce bouton | 25-dossier-attache.png | observation (deux règles d'enregistrement dans un même dialogue) |
| 4.3 | « Préparer la synchronisation » | Un plan lisible | « 3 à indexer, 0 à réindexer, 0 à retirer, 0 inchangés », fichiers listés sous l'étiquette « INDEXER » | 26-dossier-plan-prepare.png | ok |
| 4.4 | « Appliquer » | Trois fichiers lus | « Synchronisation en cours… » puis, pour les trois fichiers : « (obsolete - Fichier enregistre mais AUCUN chunk indexe : il n'apparaitra pas dans les recherches. Format non extractible, fichier vide ou protege ?) » et « Dernière synchronisation : partielle (des éléments restent à traiter) ». Journal : `file_parser` « Unsupported file type: » (extension vide) puis « No text extracted for README.md » (idem pour les deux autres). API : trois fichiers en périmètre projet, `chunk_count: 0`, plan `applique_partiel` | 27-dossier-applique.png, 28-dossier-echec-aucun-chunk.png | bug_candidate (hugo-11) |
| 4.5 | Je lis le motif | Comprendre et savoir quoi faire | Motif tronqué par des points de suspension dans le dialogue ; sans accents ; « chunk », « obsolete », « INDEXER » ; aucune action proposée. « Fichiers du projet », juste en dessous, ne liste pas les trois fichiers enregistrés | 28-dossier-echec-aucun-chunk.png | bug_candidate (hugo-12) |
| 4.6 | En-tête « Travaux » | Suivre l'indexation | Panneau « Travaux récents » (nommé « Travaux en cours » pour l'accessibilité) : « Synchronisation de dossier-orion, Terminé, Début 10:22 · Fin 10:22 ». Le moteur rend `run.etat: done` et `dernier_plan.etat: applique_partiel` : l'échec total devient « Terminé ». Tout en 12 px, lignes non cliquables | 29-dossier-travaux-recents.png | bug_candidate (hugo-13) |
| 4.7 | ⌘B, Tab × 3, Entrée sur Orion ; « Que dit le fichier specifications.md du dossier Orion sur l'authentification et sur le budget ? Cite le fichier. » | La réponse tirée du fichier (jeton de 30 minutes, 12 400 € HT) | 5 min 7 s, trois `search_files` : « Je n'ai trouvé aucun fichier nommé specifications.md dans le projet API client Orion ou dans vos autres dossiers indexés… Pourriez-vous vérifier s'il est bien présent… », avec la mention « Confiance haute ». Or `GET /api/memory/projects/<Orion>/files` liste bien `specifications.md` dans le projet. `search_files` et `read_file` ne retiennent que `chunk_count > 0` (`src/backend/app/services/memory_tools.py` l. 1431 et 1534) : conséquence directe de hugo-11 | 33-dossier-question-fichier-envoyee.png, 34-dossier-reponse-fichier.png | bug_candidate (hugo-11, conséquence) ; observation (« Confiance haute » sur une absence) |

Console du parcours : aucune erreur. Réseau : `PUT …/sync/racine`, `POST …/sync/plan`, `POST …/sync/apply`, tous en 200 ; l'échec n'est visible que dans le corps (`applique_partiel`) et le journal.

### 1 bis. Étanchéité entre projets : une conversation de « Site association » ne voit pas un contact d'« API client Orion »

Préconditions : conversation Orion rattachée ; aucun contact de projet.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1b.1 | Dans la conversation Orion : `/contact Paul Exemple email=paul@orion-exemple.fr societe=Orion` | Contact créé dans le projet Orion | Réponse immédiate « Contact Paul Exemple créé en mémoire. » ; API : `scope: project`, `scope_id` d'Orion | 35-etancheite-contact-paul-orion.png | ok |
| 1b.2 | Rail « Nouvelle conversation », projet « Site association », « quel est l'e-mail de Paul Exemple ? » | Ne pas le trouver | 2 min : `read_contact` appelé, réponse « Je ne trouve aucun contact pour Paul Exemple dans vos dossiers. » L'étanchéité tient pour les contacts | 36-etancheite-question-site-association.png, 38-etancheite-reponse-site-association.png | ok |

Étanchéité des documents non testable par le chat : aucun fichier du dossier Orion n'est lisible (hugo-11). Le bouton « Ajouter un fichier » de « Fichiers du projet » ouvre un sélecteur natif que mon instrument ne sait pas remplir.

### 3. Documentation : créer un document de l'atelier (trame, deux sections), le retrouver depuis le projet

Préconditions : aucun document (`GET /api/documents` = `[]`).
Gestes : ⌘K, « atelier », Entrée (3) ; Tab, Entrée (2) ; titre, brief, projet lié, « Créer » (4) ; deux sections à 3 gestes chacune (« Ajouter une section », titre, « Créer ») : 15 gestes.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 3.1 | ⌘K, je tape « atelier », puis « documentation », « document », « trame » | Trouver l'atelier documentaire | « atelier » : « Ouvrir les Documents », « Nouveau document ». « documentation » : rien. « document » : six entrées, dont « Rédiger un document », « Produire un document » (DOCX, PPTX, XLSX), « Fichiers » (documents locaux) et « Facturer un client » (documents commerciaux). Le même mot désigne quatre objets différents, et « Documents généraux » en désigne un cinquième dans le sélecteur de conversation | 39-documentation-palette-atelier.png | bug_candidate (hugo-04) |
| 3.2 | Entrée sur « Ouvrir les Documents » | L'atelier | Écran « Documents », 0 document, état vide avec action ; focus sur le titre | 40-documentation-ouvert.png | ok |
| 3.3 | Tab, Entrée : « Nouveau document » | Un formulaire | Titre, Brief, « Projet lié (optionnel) » dont l'absence s'appelle « Aucun projet » (ailleurs « Documents généraux ») | 41-documentation-formulaire.png | bug_candidate (hugo-04) |
| 3.4 | Je remplis, projet « API client Orion », Entrée dans le titre | Créer | Entrée sans effet (focus resté dans le titre, dialogue ouvert) ; clic « Créer » | 41-documentation-formulaire.png | bug_candidate (hugo-01) |
| 3.5 | « Créer » | Le document, sa trame | Espace du document ouvert, « Génération de la trame en cours… Avec un modèle local, cela peut prendre plusieurs minutes. », bouton « Annuler la génération ». Deux boutons de retour superposés (« Retour » vers la « conversation unifiée », « Retour aux documents »). Focus posé sur « Replier le volet Pistes », à l'autre bout de l'écran | 42-documentation-cree.png | observation |
| 3.6 | Sans attendre, rail « Projets », carte Orion | Retrouver mon document depuis le projet, la trame continue en fond | Le dialogue du projet ne mentionne aucun document. Et en quittant l'atelier, la trame a été annulée : `POST /api/documents/<id>/outline` → 409 `{"code":"outline_cancelled","message":"Génération de la trame annulée."}` (console : « Failed to load resource: 409 (Conflict) »). Aucun avertissement avant de partir, aucun message après. Le chat, lui, m'empêche de partir pendant une réponse (2.1) : deux règles opposées pour le même geste. Cause lue : `closeDocument()` annule la trame au démontage (`src/frontend/src/stores/documentStore.ts` l. 238-249, B-919) | 43-documentation-projet-sans-document.png, requête réseau 1529 | bug_candidate (hugo-14), bug_candidate (hugo-03) |
| 3.7 | ⌘K « Ouvrir les Documents » | Retrouver où j'en étais | Liste : « Documentation technique API Orion · Sans trame · Trame non générée ». Rien ne dit que la génération a été annulée ; le projet lié n'est pas affiché ; pas de filtre par projet | 44-documentation-liste-retour.png | bug_candidate (hugo-14) |
| 3.8 | Ouvrir le document, « Ajouter une section » × 2 | Deux sections | Un champ en ligne prend le focus ; Entrée n'y crée pas la section (clic « Créer » nécessaire) ; deux sections « Vide » créées, conformes à l'API (`sections_total: 2`). Le second titre est tronqué (« Réservation : points d'e… ») | 45-documentation-rouvert-sans-trame.png, 46-documentation-ajouter-section.png, 47-documentation-section-1.png, 48-documentation-deux-sections.png | bug_candidate (hugo-01) |
| 3.9 | ⌘K « Documentation technique » | Mon document | « 0 résultat » | 49-documentation-palette-titre-introuvable.png | bug_candidate (hugo-15) |

Console du parcours : une erreur, le 409 de 3.6. Réseau : `POST /api/documents` 200, `POST …/outline` 409, `POST …/sections` 200 × 2.

### 2 bis. Changer de sujet, suite : le brouillon et les raccourcis depuis le champ de message

Préconditions : conversations Orion (6 messages) et Veille IA (2 messages), aucune génération en cours.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 2b.1 | Dans Orion, je commence un message sans l'envoyer : « Brouillon Orion : penser au quota de l'hébergeur avant la démo » | Le brouillon reste dans Orion | Saisi | 50-changer-brouillon-orion.png | ok |
| 2b.2 | ⌘B depuis le champ de message, deux fois | Le tiroir | Rien (vérifié sur 1 s, deux essais). ⌘K, au même endroit, ouvre la palette. Cause lue : `src/frontend/src/hooks/useKeyboardShortcuts.ts` l. 101 « Skip other shortcuts when in inputs » : ⌘B, ⌘M, ⌘D sont ignorés dans un champ, alors que ⌘K, ⌘N, ⌘, et ⌘/ y marchent. La liste des Paramètres annonce ⌘B sans cette réserve, et n'annonce ni ⌘N ni ⌘/ | 51-changer-cmd-b-depuis-champ.png | bug_candidate (hugo-16) |
| 2b.3 | Rail « Conversations », ligne « Veille » | La conversation Veille, avec son propre champ vide | Veille s'ouvre (sélecteur « Veille IA ») mais son champ contient mon brouillon Orion. Un Entrée de trop, et ma note Orion part dans le projet Veille IA | 52-changer-brouillon-orion-dans-veille.png | bug_candidate (hugo-17) |
| 2b.4 | Retour dans Orion | Mon brouillon | Il y est aussi : un seul brouillon pour toutes les conversations. État local `useState('')` du champ (`src/frontend/src/components/chat/ChatInput.tsx` l. 107), non rattaché à la conversation. Je l'efface | (mesure DOM) | bug_candidate (hugo-17) |

### 5. Retrouver : « qu'avais-je dit sur Orion hier ? » par le tiroir et par ⌘K

Préconditions : quatre conversations, dont Orion (titre local « Orion : on a retenu la variante B… », titre en base « Nouvelle conversation », hugo-06).

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 5.1 | ⌘K (pendant une réponse), « Orion » | Ma conversation, mon projet | Dialogue « Rechercher dans Thérèse » : « 0 résultat · Aucune capacité trouvée », « 30 capacités indexées ». « variante », « API client Orion » : 0. « projet » : trois capacités, aucun projet. La palette ne cherche que parmi les capacités. Échap rend le focus au champ de message | 37-retrouver-palette-orion.png | bug_candidate (hugo-15) |
| 5.2 | Rail « Conversations » (focus dans la recherche), « Orion », le jour même | La conversation | Une ligne, trouvée par son titre local ; aucune requête réseau (recherche côté client) | 53-retrouver-tiroir-orion-avant-rechargement.png | ok |
| 5.3 | « Le lendemain » : rechargement de la page (garde rejouée : `visible`, horloge 3568, thème sombre conservé), rail « Conversations » | Mes conversations avec leurs titres | Orion et Site association s'appellent toutes deux « Nouvelle conversation » ; Orion affiche 10:08 alors que son dernier message date de 10:30, et se range sous Veille | 54-retrouver-tiroir-apres-rechargement.png | bug_candidate (hugo-06) |
| 5.4 | « Orion » dans la recherche du tiroir | La conversation | « Aucune conversation trouvée ». « variante », « quota », « API client », « Paul » : rien non plus, alors que l'aperçu affiché sous une ligne contient « Paul » (voisin de claire-25) | 55-retrouver-tiroir-orion-apres-rechargement.png | bug_candidate (hugo-06), proposal (hugo-18) |

Gestes : par le tiroir, 2 (rail, saisie) et zéro résultat le lendemain ; par ⌘K, 2 et zéro résultat ; par le projet, impossible (il ne liste pas ses conversations, hugo-03). Il ne reste qu'à ouvrir une à une les « Nouvelle conversation ».
Console depuis le rechargement : aucune erreur, aucun avertissement. Réseau : 59 requêtes, toutes en 200, toutes vers 127.0.0.1 (`captures/hugo/reseau-apres-rechargement.txt`).

### 5 bis. Les quatre raccourcis annoncés dans Paramètres (⌘K, ⌘B, ⌘M, ⌘D)

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 5b.1 | ⌘K hors champ et dans le champ | Palette | Marche dans les deux cas | 37-retrouver-palette-orion.png | ok |
| 5b.2 | ⌘B hors champ | Conversations | Marche (2.7) ; pas depuis le champ (2b.2) | 30-changer-cmd-b-tiroir.png | bug_candidate (hugo-16) |
| 5b.3 | ⌘M hors champ (focus sur le rail) | « Mémoire », comme annoncé | Ouvre l'écran « Contacts » : l'annonce et l'écran ne portent pas le même nom | 56-raccourcis-cmd-m-memoire.png | bug_candidate (hugo-16) |
| 5b.4 | ⌘D depuis Contacts, puis Échap | « Décision » | Dialogue « Décision » ouvert ; Échap le ferme et rend le focus au titre « Contacts » | 57-raccourcis-cmd-d-decision.png | ok |
| 5b.5 | ⌘/ depuis le champ de message (en fin de session) | La liste des raccourcis | Fenêtre « Raccourcis clavier » : ⌘N « Nouvelle conversation », ⌘K « Palette de commandes », ⌘B « Liste des conversations », ⌘M « Contacts », ⌘D « Décision », ⌘E, ⌘T, ⌘I, ⌘P, ⌘O, ⌘⇧A/K/C/F/D. Seconde liste, plus complète que celle de Paramètres, et qui nomme ⌘M autrement | 63-raccourcis-fenetre-cmd-slash.png | bug_candidate (hugo-16) |

### 6. Capacités : ouvrir le centre, comprendre parcours, vues et actions

Préconditions : aucune.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 6.1 | Rail « Plus d'outils » | Comprendre ce que chaque carte fera | Dialogue « Capacités, 30 capacités », six intentions en onglets, focus dans « Chercher une capacité, un résultat ou un outil… ». Trois types sur les cartes : 7 « Parcours », 19 « Vue », 4 « Demande relue » ; la seule explication est en pied de dialogue : « Parcours et Vue s'ouvrent au clic. Une Demande relue pose une phrase dans le composeur, que tu relis avant l'envoi. » Rien ne dit ce qui distingue un Parcours d'une Vue | 58-capacites-ouvert.png | proposal (hugo-20) |
| 6.2 | Carte « Agenda » (Parcours) | L'agenda | L'Accueil en mode « Préparer un rendez-vous », avec le panneau « Préparation du rendez-vous » ; l'agenda demande un clic de plus (« Ouvrir Agenda »). La carte dit « Agenda », l'écran dit « Préparer ». Focus retombé sur « Conversations » du rail | 59-capacites-parcours-agenda.png | proposal (hugo-20), bug_candidate (hugo-10) |
| 6.3 | Carte « Tâches » (Vue) | L'écran Tâches | Ouvert directement, focus sur le titre « Tâches » : une Vue, c'est un écran | 60-capacites-vue-taches.png | ok |
| 6.4 | « Comprendre et décider » > « Recherche web » (Demande relue) | Une phrase à relire, le curseur dedans | Phrase « Fais une recherche actuelle et cite précisément les sources utilisées. » posée dans le composeur de l'Accueil, étiquette « Capacité : Recherche web ». La puce « Préparer » reste enfoncée au-dessus (vestige de 6.2). Focus resté sur « Plus d'outils » : pour relire, il faut revenir au champ | 61-capacites-demande-relue.png | bug_candidate (hugo-10) |
| 6.5 | « Retirer la capacité » (×) | Retirer la demande | L'étiquette part, la phrase reste dans le champ, et le focus tombe sur `BODY` : au clavier, je ne sais plus où je suis. J'ai vidé le champ à la main | 62-capacites-retirer-focus-perdu.png | bug_candidate (hugo-19) |

Arbre d'accessibilité : dialogue nommé par `aria-labelledby="capability-center-title"` (« Capacités »), `tablist` « Intentions », `searchbox` « Rechercher une capacité », statut « 5 capacités affichées ». Le nom « Plus d'outils » du rail pour un dialogue « Capacités » est déjà relevé par Claire (2.1), non repris.
Console : aucune erreur. Réseau : rien de neuf hors 200.

## Constats numérotés

**hugo-01, bug_candidate, mineure : Entrée ne valide aucun des formulaires de mes parcours.**
Étapes : Projets > « Nouveau projet », taper un nom, Entrée ; projet > « Chemin du dossier à synchroniser », Entrée ; Documents > « Nouveau document », titre, Entrée ; document > « Ajouter une section », titre, Entrée. Attendu (grille, clavier) : Entrée valide un formulaire dont le seul champ obligatoire est rempli. Observé : rien dans les quatre cas (dialogue resté ouvert, `GET /api/memory/projects` = `[]` après 1.3). Il faut 10 Tab depuis la description pour atteindre « Créer » dans la modale projet. Fichier lu : `src/frontend/src/components/memory/ProjectModal.tsx`, aucun `<form>`, `handleSave` seulement sur le clic ; la modale d'agenda (`calendar/EventForm.tsx`) en a un. Preuve : 06, 24, 41, 47.

**hugo-02, proposal : la liste des projets ne montre pas les tags et ne se filtre pas.**
Trois projets créés avec des tags (« asso, web », « orion, api », « veille ») : aucune carte ne les affiche, aucun champ de filtre. Avec trois projets ça passe ; avec quinze, c'est ma ligne rouge « une liste qui ne se filtre pas ». Preuve : 08.

**hugo-03, bug_candidate, moyenne : ouvrir un projet ne montre pas ce qu'il rassemble.**
Étapes : Projets, clic sur « API client Orion » après y avoir rattaché trois conversations (Orion), un contact (Paul Exemple, périmètre projet), un document (« Documentation technique API Orion », `project_id` d'Orion) et un dossier. Attendu : la promesse de l'état vide, « rassembler les contacts, documents et tâches d'une même affaire ». Observé : un dialogue « Modifier le projet » (nom, statut, un seul « Contact associé », budget, notes, dossier, fichiers, tags) ; aucune conversation, aucun document de l'atelier, aucune tâche, Paul Exemple absent. Depuis le projet, je ne peux ni ouvrir ma conversation Orion ni mon document. Preuve : 04 (promesse), 09, 10, 43 ; API : `GET /api/documents/bfd005f5…` rend `project_id: 0c7ee991…`.

**hugo-04, bug_candidate, mineure : un même objet sous plusieurs noms, un même nom pour plusieurs objets.**
Le projet s'appelle « Projets » dans le rail, « Dossier de cette conversation : fichiers rattachés, carnet partagé » dans la conversation ; l'absence de projet s'appelle « Documents généraux » dans la conversation et « Aucun projet » dans le formulaire de document ; « Dossier synchronisé » désigne un dossier du disque dans le même écran de projet. « Documents » désigne l'atelier (« Ouvrir les Documents »), la génération Office (« Produire un document »), les fichiers indexés (« Fichiers », « Indexer et interroger les documents locaux »), les devis (« Facturer un client », « documents commerciaux ») et le périmètre général (« Documents généraux »). Attendu (grille, cohérence et lexique : Projets) : un mot par objet. Preuve : 11, 12, 39, 41, 09.

**hugo-05, proposal : « Nouvelle conversation » ne place pas le curseur dans le message.**
Rail « Nouvelle conversation » : le focus reste sur le bouton du rail ; 18 arrêts de tabulation jusqu'au champ (rail, sélecteur de projet, quatre cartes, quatre actions rapides, modèle, pièce jointe). ⌘N existe (`useKeyboardShortcuts.ts` l. 86) ; il figure dans la fenêtre « Raccourcis clavier » (⌘/) mais pas dans la liste de Paramètres > Accessibilité, la seule que l'on m'a montrée. Preuve : 11, 63, mesure DOM de l'ordre de tabulation.

**hugo-06, bug_candidate, moyenne : choisir le projet avant d'écrire laisse la conversation s'appeler « Nouvelle conversation » en base, et le lendemain je ne la retrouve plus.**
Étapes : rail « Nouvelle conversation », choisir un projet dans le sélecteur (la conversation est créée à ce moment, 0 message), écrire, envoyer ; recharger la page. Attendu : le titre tiré du premier message, comme pour une conversation sans projet. Observé : à l'écran, le titre local « Orion : on a retenu la variante B… » ; en base, `"title": "Nouvelle conversation"`, `message_count: 2` puis 6, `updated_at` figé à la création (08:08:20) ; après rechargement, deux « Nouvelle conversation » dans le tiroir, Orion daté 10:08 et rangé sous une conversation plus ancienne, et la recherche « Orion » rend « Aucune conversation trouvée ». La conversation Veille, créée par le premier message puis rattachée, garde son titre : c'est l'ordre des gestes qui décide. Fichier lu : `src/backend/app/routers/chat.py` l. 1253-1263, le titre n'est posé que si la conversation n'existe pas. Preuve : 13, 32, 54, 55 ; `GET /api/chat/conversations/b1bf840a…`.

**hugo-07, proposal : avec un modèle local, je ne peux pas changer de sujet pendant cinq à sept minutes.**
Pendant une réponse, rail et tiroir refusent de changer de conversation ou de vue (« Arrête la réponse avant de changer de vue ou de conversation. »). C'est un choix de conception, mais mes réponses ont pris 4 min 35 s, 7 min 10 s (pour « noté »), 5 min 7 s et 2 min : c'est tout mon rythme de travail qui s'arrête. Pistes : laisser la réponse finir en fond et la signaler dans « Travaux » (qui la liste déjà), ou prévenir avant l'envoi. Preuve : 14, 16, 21-23 ; journal `[PERF] Stream complete`.

**hugo-08, bug_candidate, mineure : le toast qui me demande d'arrêter la réponse cache le bouton « Arrêter la réponse ».**
Étapes : réponse en cours, rail « Nouvelle conversation ». Observé : toast x 1040-1424, y 785-884 ; bouton x 1315-1359, y 792-836 ; `document.elementFromPoint` au centre du bouton rend le `<p>` du toast. Attendu : l'action demandée reste accessible. Preuve : 17, mesure DOM.

**hugo-09, proposal : le tiroir ne dit pas à quel projet appartient une conversation.**
Aucune ligne n'affiche son projet, aucun filtre par projet ; avec trois clients et plusieurs conversations chacun, je ne sais pas où je clique. Preuve : 15, 54.

**hugo-10, bug_candidate, mineure : après un changement d'écran, le focus atterrit sur un bouton qui n'a rien à voir.**
Quatre cas mesurés (`document.activeElement`) : ouvrir une conversation depuis le tiroir alors que j'étais dans Projets → focus sur « Projets » du rail (12 Tab jusqu'au message) ; idem en 1.8 ; carte « Agenda » des capacités → focus sur « Conversations » du rail ; « Demande relue » → focus resté sur « Plus d'outils » au lieu du champ où la phrase attend d'être relue ; ouverture d'un document → focus sur « Replier le volet Pistes », à l'autre bout de l'écran. Attendu (grille, focus) : le focus va sur le titre ou le champ de l'écran ouvert, comme le font déjà Projets, Documents, Tâches et Contacts. Preuve : 32, 42, 45, 59, 61.

**hugo-11, bug_candidate, haute : la synchronisation de dossier ne peut indexer aucun fichier, quel que soit son format, et le chat ne voit donc rien du dossier.**
Étapes : projet « API client Orion », attacher `/tmp/therese-demo-c13/dossier-orion`, « Préparer la synchronisation » (3 à indexer), « Appliquer ». Observé : les trois fichiers (`.md`, `.txt`, `.md`, 102 à 174 octets) finissent en « AUCUN chunk indexe » ; journal : `Unsupported file type: ` (extension vide) puis `No text extracted for README.md` (idem pour les deux autres) ; API : `chunk_count: 0` pour les trois, plan `applique_partiel`. Ensuite, dans la conversation Orion, « Que dit specifications.md… » : « Je n'ai trouvé aucun fichier nommé specifications.md dans le projet » (avec « Confiance haute »), car `search_files` et `read_file` ne retiennent que `chunk_count > 0` (`services/memory_tools.py` l. 1431 et 1534). Cause lue : `src/backend/app/services/indexation.py` l. 399-418, `_copier_si_conforme` copie le fichier dans `tempfile.mkstemp(prefix="therese-sync-")` sans suffixe ; l. 381-392, cette copie devient `source_extraction` ; `file_parser.extract_text` aiguille sur `file_path.suffix` (vide). Seul le chemin de synchronisation passe `sha256_attendu` (`project_sync_service.py` l. 543) : l'indexation directe ne devrait pas être touchée (déduit du code, non éprouvé, pour ne pas écrire un fichier global dans la base partagée). Présent depuis `05165c10` (0.45). Preuve : 26, 27, 28, 34 ; journal 10:22:05.

**hugo-12, bug_candidate, mineure : le motif d'échec de la synchronisation est illisible et ne dit pas quoi faire.**
Dans le dialogue du projet : « INDEXER specifications.md (obsolete - Fichier enregistre mais AUCUN chunk indexe : il n'apparaitra pas dans les recherches. Format non extractible, fichier vide ou protege ?) », tronqué par des points de suspension à la largeur du dialogue, sans accents, avec « chunk » et « obsolete » ; « Dernière synchronisation : partielle (des éléments restent à traiter) » sans bouton ni conseil. « Fichiers du projet », juste en dessous, ne liste pas les trois fichiers enregistrés. Attendu (grille, états) : une erreur lisible qui dit quoi faire. Preuve : 28.

**hugo-13, bug_candidate, moyenne : « Travaux » annonce « Terminé » pour une synchronisation qui n'a rien lu.**
Étapes : suite de hugo-11, en-tête « Travaux ». Observé : « Synchronisation de dossier-orion · Terminé · Début 10:22 · Fin 10:22 », alors que le moteur rend `run.etat: done` et `dernier_plan.etat: applique_partiel` avec 0 fragment. Tout le panneau est en 12 px (grille : rien d'important sous 14 px), les lignes ne mènent nulle part, et le dialogue s'appelle « Travaux en cours » pour un titre visible « Travaux récents ». Preuve : 29 ; `GET /api/projects/<Orion>/sync`.

**hugo-14, bug_candidate, moyenne : quitter l'atelier jette la trame en cours, sans prévenir ni l'expliquer ensuite.**
Étapes : « Nouveau document » lié à Orion, « Créer » (génération de la trame lancée), rail « Projets ». Observé : `POST /api/documents/<id>/outline` → 409 `{"code":"outline_cancelled","message":"Génération de la trame annulée."}` ; aucun avertissement avant de partir ; au retour, la liste dit « Sans trame · Trame non générée » sans mentionner l'annulation, le document n'a aucune section. Le chat applique la règle inverse (il m'empêche de partir, hugo-07) : le même geste, deux conséquences. Fichier lu : `src/frontend/src/stores/documentStore.ts` l. 238-249, `closeDocument()` annule la trame au démontage (choix B-919 : sans cela le suivi restait bloqué). Attendu : ne pas perdre un travail en cours en silence (avertir, ou laisser tourner en fond comme les autres travaux). Preuve : 42, 43, 44, 45 ; console « 409 (Conflict) ».

**hugo-15, bug_candidate, mineure : ⌘K s'appelle « Rechercher » et « Rechercher dans Thérèse » mais ne cherche que parmi 30 capacités.**
Étapes : ⌘K, « Orion », « variante », « API client Orion », « Documentation technique ». Observé : 0 résultat à chaque fois ; seuls des noms de capacités sortent. Le même raccourci s'appelle « Rechercher » (en-tête), « commandes » (pied du composeur), « Palette de commandes » (Paramètres), « Rechercher une commande, un parcours ou une capacité » (champ). Attendu (grille, prévisibilité et cohérence) : le titre dit ce que fait l'outil, un nom par outil. Voisin de claire-20 (« Hélène » → 0 résultat), vu ici sous l'angle des projets, conversations et documents. Preuve : 37, 49, 02.

**hugo-16, bug_candidate, mineure : les raccourcis annoncés ne marchent pas partout, et l'un porte un autre nom que l'écran qu'il ouvre.**
Paramètres > Accessibilité annonce ⌘B, ⌘M, ⌘D sans réserve. Depuis le champ de message, où je passe l'essentiel de mon temps, ⌘B ne fait rien (deux essais) ; ⌘K y marche. Cause lue : `src/frontend/src/hooks/useKeyboardShortcuts.ts` l. 101. ⌘M s'appelle « Mémoire » dans Paramètres et « Contacts » dans la fenêtre « Raccourcis clavier » (⌘/), et ouvre l'écran « Contacts » : deux listes de raccourcis, deux noms pour la même touche. ⌘N et ⌘/ ne figurent que dans la fenêtre ⌘/, pas dans Paramètres ; ⌘/ marche depuis le champ de message, ⌘B non. Aucune des deux listes ne dit que certains raccourcis se taisent dans un champ. Ligne rouge de ma fiche : « un raccourci annoncé qui ne marche pas ». Preuve : 02, 51, 56, 63.

**hugo-17, bug_candidate, moyenne : le brouillon d'une conversation me suit dans une autre, d'un projet à l'autre.**
Étapes : conversation Orion, taper sans envoyer ; ouvrir la conversation Veille (projet Veille IA) par le tiroir. Observé : le brouillon Orion est dans le champ de Veille ; revenu dans Orion, il y est aussi. Attendu : un brouillon par conversation, ou au moins aucun texte d'un projet dans le champ d'un autre (c'est exactement le cloisonnement que les projets promettent). Fichier suspecté : `src/frontend/src/components/chat/ChatInput.tsx` l. 107, `const [input, setInput] = useState('')`, non rattaché à la conversation. Preuve : 50, 52, mesures DOM (`textarea.value`).

**hugo-18, proposal : la recherche du tiroir ne connaît que les titres.**
« variante », « quota », « API client » (nom du projet), « Paul » : rien, même quand l'aperçu affiché contient le mot. Pour un freelance qui retrouve un sujet par un mot du fond ou par le client, il faut chercher dans le contenu et dans le nom du projet. Voisin de claire-25 (aperçu non indexé). Preuve : 55.

**hugo-19, bug_candidate, mineure : « Retirer la capacité » laisse sa phrase dans le champ et perd le focus.**
Étapes : « Plus d'outils » > « Comprendre et décider » > « Recherche web », puis × « Retirer la capacité ». Observé : l'étiquette disparaît, la phrase « Fais une recherche actuelle… » reste, `document.activeElement` = `BODY`. Attendu : retirer la demande entière, focus rendu au champ. Preuve : 61, 62.

**hugo-20, proposal : les types de capacités ne s'expliquent qu'en pied de dialogue, et une carte ne mène pas à ce qu'elle nomme.**
7 « Parcours », 19 « Vue », 4 « Demande relue » ; seule explication, une phrase en pied. En essayant, je comprends : une Vue ouvre un écran (Tâches), un Parcours ouvre un mode de l'Accueil (la carte « Agenda » ouvre « Préparer un rendez-vous », et l'agenda demande un clic de plus), une Demande relue pose une phrase. Piste : nommer la carte d'après ce qu'elle ouvre, et une infobulle par type. Preuve : 58, 59, 60, 61.

**hugo-21, observation : les signaux de la réponse locale ne me disent pas ce qui se passe.**
Le moteur journalise « Ollama (gemma4-tia:latest): réponse vide, aucun contenu reçu » à 10:20:01 ; l'écran montre une bulle vide jusqu'à 10:21:13, sans rien signaler. « Confiance haute » accompagne une réponse fausse par absence (hugo-11). Lenteur propre à cette machine (Claire signalait déjà un modèle « RAM déconseillée »), donc preuve insuffisante pour un défaut de l'application. Preuve : 22, 23, 34 ; journal.

## Transitions couvertes et angles morts

**Transitions couvertes** (63 captures : 31 relues à l'image, les autres vérifiées au même instant par l'arbre d'accessibilité ou une mesure DOM) :
- Devis et factures → Échap → Accueil → ⌘, → Paramètres (thème sombre) → Échap.
- Rail Projets → création × 3 (clavier puis souris) → ouverture d'un projet → Échap (focus rendu).
- Rail Nouvelle conversation → sélecteur de projet → message → changement refusé pendant la réponse (rail, tiroir) → tiroir → réponse ; rattachement après coup pendant une réponse.
- Projets → dossier attaché → plan → application → Travaux.
- ⌘B → tiroir → Tab × 3 → Entrée → conversation → question sur un fichier.
- `/contact` dans un projet → nouvelle conversation d'un autre projet → question sur ce contact (étanchéité des contacts).
- ⌘K → Documents → Nouveau document → départ pendant la trame → Projets → retour → deux sections.
- Brouillon Orion → Veille → Orion ; ⌘B depuis le champ.
- ⌘K (projets, conversations, documents) ; tiroir avant et après rechargement (« le lendemain », garde rejouée).
- ⌘M, ⌘D ; Plus d'outils → Parcours, Vue, Demande relue → Retirer.

**Angles morts** :
- Étanchéité des documents entre projets non testable par le chat : aucun fichier du dossier n'est lisible (hugo-11). « Ajouter un fichier » de « Fichiers du projet » ouvre un sélecteur natif que l'instrument ne remplit pas.
- Tauri absent : sélecteur de dossier natif (le chemin a été saisi à la main).
- Génération de trame par le modèle non attendue jusqu'au bout (annulée par mon départ, puis sections posées à la main pour tenir le temps) ; rédaction d'une section non essayée.
- Glisser-déposer des cartes de projet et de sections, « Contact associé », budget, statut : non éprouvés.
- ⌘N non pressé (risque d'ouvrir une fenêtre du navigateur) : constaté dans le code et dans la fenêtre ⌘/, pas éprouvé.
- `main` a avancé pendant la session (`cedae831` à 10:20) ; le frontend Vite a pu se recharger à chaud. Aucun changement de comportement observé en cours de route, mais les constats valent pour l'état du 25/09 entre 10:05 et 10:41.
- Lenteur du modèle local : propre à cette machine, non imputée à l'application (hugo-21).

**Données laissées en place pour Nathalie et Zoé** : projets « Site association », « API client Orion » (dossier `dossier-orion` attaché, trois fichiers enregistrés à 0 fragment), « Veille IA » ; conversations Orion (6 messages, titre en base « Nouvelle conversation »), Veille IA (2), Site association (2, titre en base « Nouvelle conversation ») ; contact Paul Exemple (périmètre projet Orion) ; document « Documentation technique API Orion » (deux sections vides, sans trame générée). Composeurs vidés. Thème rendu clair et viewport rendu à 1280×800 en fin de session (préférence d'affichage de Nathalie), voir la dernière ligne.

**Bilan** : 21 constats numérotés avec preuve : 14 bug_candidate (1 haute, 5 moyennes, 8 mineures), 6 proposal, 1 observation (hugo-21). Aucun constat écarté faute de preuve. Deux ratés d'instrument écartés : le sélecteur `main select` ambigu (1.13, message parti hors projet puis rattaché) et une référence d'élément périmée au premier clic sur « Projets » (capture 03 renommée en conséquence).

## Tokens consommés (si connus)

Environ 400 000 tokens (compteur de session : 15 000 000 au départ, 14 597 747 à la fin de la trace).

État final à 10:46, après la vérification ⌘/ : thème `light`, viewport 1280×800, aucun dialogue ouvert, composeur vide (mesure DOM).
