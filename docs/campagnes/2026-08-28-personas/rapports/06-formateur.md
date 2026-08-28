# Rapport - Yann Le Guen, formateur indépendant

## Mon impression générale

J’ai ouvert THÉRÈSE comme je le ferais avant de préparer un support : qu’est-ce que ça sait faire, comment ça s’appelle, est-ce que je pourrais le faire faire à un stagiaire de 58 ans lundi matin. L’accueil dit « Bonjour. » puis « Branche tes mails pour que je te prépare la journée », avec cinq puces *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Aucune ne dit « session », « stagiaire » ou « convention ». J’ai tapé dans le champ « Demande à Thérèse d’organiser, créer ou agir… ». En deux phrases, Claire Martin, le projet et les huit stagiaires étaient enregistrés. Les deux journées, le texte disait qu’elles étaient dans l’agenda alors qu’il fallait encore cliquer *Créer*. J’ai demandé les pièces Qualiopi : l’outil a fabriqué quatre fichiers, le chat n’a montré aucun bouton pour les ouvrir, et la convocation mélangeait Atelier Martin avec une session de la mairie. Pour un audit de surveillance, je n’imprime pas ça. Pour un stagiaire débutant, je n’ose pas.

## Ce que j’ai réussi à faire

- Lire l’accueil, le rail, les cinq parcours, le tiroir *Plus d’outils* et les vues, comme pour un support de formation. (lecture de l’interface)
- Enregistrer le client Claire Martin / Atelier Martin en **une phrase** dans le champ « Message à Thérèse ». (1 geste, 78 s) Source : API `POST /api/chat/send`.
- Créer le projet « Excel intermédiaire - Atelier Martin », les 8 stagiaires, et les deux journées 15-16 septembre 2026, en **une deuxième phrase** plus **deux clics** *Créer* sur les cartes « Confirmer la création du rendez-vous ». (3 gestes, 155 s puis 2 clics)
- Compléter le profil émetteur (Paramètres > Profil : SIRET, adresse, n° de déclaration d’activité). L’écran le demandait : « Compléter le profil de facturation ». (formulaire, ~10 champs)
- Créer deux factures de sessions déjà données : FACT-2026-001 Mairie de Manosque 2 400 € (envoyée, impayée) et FACT-2026-002 Cabinet Dupont 1 400 € (payée le 30/06). (API des factures, comme le formulaire *Nouvelle facture*)
- Obtenir les PDF une fois le profil rempli.
- Obtenir une **trame** de programme dans *Documents* (10 sections Qualiopi-compatibles : objectifs, contenu, méthodes, évaluation, durée, jour 1, jour 2). Les sections sont vides.

## Ce que je n’ai pas réussi à faire

- Monter un **dossier de session** : client, dates, stagiaires et programme dans un seul objet. Le projet n’est lié à personne (`contact_id` vide). Les 8 stagiaires sont des contacts, au même étage que la RH, étiquette de pipeline « contact ».
- Poser les journées dans l’agenda **sans** un second geste de confirmation, alors que le message disait déjà que c’était fait.
- Produire des pièces administratives **imprimables et montrables à un auditeur** : convention, convocation, émargement, attestation. Les fichiers existent sur le disque, le chat n’affiche aucun bouton, le contenu n’est pas Qualiopi.
- Suivre un paiement OPCO en retard : FACT-2026-001 est due au 10/08/2026, on est le 28/08, le statut reste *Envoyée*, le filtre *En retard* est vide, le brief du jour ne la montre pas.
- Faire découvrir l’accueil à un débutant sans lui tenir la main : dès les cinq verbes, il ne sait pas où est une session.
- Remplacer mon tableur. Il me manque la session, les stagiaires rattachés, les modèles Qualiopi, et un seul mot par chose.

## Findings

### F1 - Cinq verbes, trop de noms, zéro mot « formation »
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface (`lib/etabli.ts` 25-31 et 48, `ConversationCanvasPrototype.tsx` 117-125, 1485, 1506, 1568-1579, 1766, `CapabilityCenter.tsx` 385-389, `PrototypeUnifiedViewCanvas.tsx` 17-27, `SetupChecklist.tsx` 26-44, `TodayDashboardCard.tsx` 143-153, `InvoiceConversationCard.tsx` 127-140, `ContactsMemoryCard.tsx` 39-47 et 78, `InvoiceForm.tsx` 443, `SettingsModal.tsx` 751)
- **Ce que j’ai fait** : ouvrir l’application, lire chaque libellé comme pour un support. Côté API : `GET /api/dashboard/setup-status`, `GET /api/dashboard/today`, `GET /api/config/profile` (vide au départ).
- **Ce que j’attendais** : un nom par chose, assez stable pour que je puisse le dicter à un stagiaire.
- **Ce qui s’est passé** : le même objet change de nom selon l’écran.

| Chose | Noms lus à l’écran |
|---|---|
| Accueil | « Bonjour. », « Mes priorités du jour », *Brief du jour* |
| E-mail | *Écrire*, « Consulter mes emails », *Email*, « Branche tes mails », « Connecter ta messagerie », « Ouvrir l'email » |
| Personnes | *Retrouver*, « Retrouver un contact », *Contacts*, « Contacts et mémoire », « Contacts et contexte », « Mémoire locale », « Chargement de la mémoire… », groupe palette *Mémoire* |
| Agenda | *Préparer*, « Préparer un rendez-vous », *Agenda*, « Connecter ton agenda », « Mon calendrier », « Confirmer la création du rendez-vous » |
| Factures | *Facturer*, « Créer un devis », « Facturer un client », *Nouveau devis*, « Facturation complète », *Devis et factures*, « Facturation locale », « Aucune facture », « Compléter le profil de facturation » |
| Décision | *Décider*, « Éclairer une décision », *Décision*, *Board* |
| Projets | rail *Espaces de travail*, vue *Projets*, *Nouveau projet* |
| Réglages | bouton *Paramètres*, bandeau facture « Réglages > Profil » |
| Catalogue | rail *Plus d’outils*, titre « Ce que Thérèse sait mobiliser », « 29 capacités » |

Le mot *contact* désigne à la fois la personne et une colonne du *Pipeline*. Un stagiaire de 58 ans, au premier écran, est perdu au verbe *Retrouver* : il croit chercher dans ses mails.
- **Pourquoi ça compte pour moi** : si je ne peux pas dire « clique sur Session », je ne peux pas enseigner l’outil. Deux noms pour la même chose, en formation, c’est un défaut de conception, pas un détail.

### F2 - Une session de formation n’existe pas
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Phrase 1 : enregistrer SARL Atelier Martin / Claire Martin, RH, Manosque, formation Excel intermédiaire 2 jours. `POST /api/chat/send`. 78 s. Outil `create_contact` OK.
  2. Phrase 2 : projet, 15-16 septembre 2026 9h-17h, 8 stagiaires. 155 s. `create_project` + 8 `create_contact`.
  3. `GET /api/memory/contacts`, `GET /api/memory/projects`, `GET /api/calendar/events`, `GET /api/crm/pipeline/stats`.
- **Ce que j’attendais** : un dossier « session Atelier Martin » avec le client, les dates, la liste des stagiaires et le programme, que je rouvre dans six mois pour l’audit.
- **Ce qui s’est passé** :
  - Claire Martin est un contact, `company`: « Atelier Martin » (le *SARL* a disparu), `address`: `null` alors que j’avais dicté « ZI Saint-Joseph, 04100 Manosque », `scope`: « conversation », `source`: `null`, `stage`: « contact ».
  - Le projet « Excel intermédiaire - Atelier Martin » a `contact_id`: `null` et `budget`: 0. Un projet n’accepte qu’**un** contact, pas une liste de stagiaires.
  - Les 8 stagiaires sont 8 contacts, même entreprise, notes « Stagiaire Excel intermédiaire », même étage *contact* que la RH. Pas d’e-mail, donc pas de convocation individuelle.
  - Les événements agenda ont `attendees`: `[]`.
  - La conversation n’est pas rattachée au projet (`project_id`: `null`).
  - Dans *Pipeline*, seuls les contacts avec une `source` apparaissent. Claire et les stagiaires, créés par le chat, n’y sont pas. Les deux clients que j’ai saisis à la main dans les contacts (Mairie, Dupont, `source`: « client ») y sont. Même métier, deux tiroirs.
  - L’écran *Retrouver* filtre prénom, nom, entreprise, e-mail (`contactMatchesQuery`, `contactsStore.ts` 39-46). Chercher « stagiaire » dans la case « Rechercher… » ne les trouve pas. `POST /api/memory/search` « stagiaire » les trouve. Le stagiaire n’a pas cette deuxième porte.
- **Pourquoi ça compte pour moi** : mon tableur a une ligne par session. Ici j’ai une RH, huit fiches, un projet orphelin et deux cases dans l’agenda. Dans six mois, pour l’audit, je ne reconstitue pas le dossier.

### F3 - L’agenda est « ajouté » avant de l’être
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : phrase 2 ci-dessus. Réponse SSE : deux `confirmation_required` sur `create_calendar_event`, puis un texte. Avant clic : `GET /api/calendar/events` sans ces deux journées. Après `POST /api/chat/confirm-tool` `approved: true` : les deux événements existent (15/09 et 16/09, 09:00-17:00, lieu correct).
- **Ce que j’attendais** : soit c’est dans l’agenda, soit on me demande clairement de valider. Pas les deux.
- **Ce qui s’est passé** : le message dit « Les événements ont été ajoutés à l'agenda. » En dessous, deux cartes « Confirmer la création du rendez-vous » avec *Créer* / *Annuler* (`ToolConfirmationCard.tsx` 73-110). Pendant l’attente : « Execution des outils: create_project, create_calendar_event… » (`ChatInput.tsx` 666-668, *Execution* sans accent, noms d’outils en anglais). Après le clic : « Evenement cree : **Formation Excel - Atelier Martin (15/09/2026)** le 15/09/2026 09:00 » (sans accents). Un stagiaire qui lit le passé composé et rentre chez lui n’a rien dans l’agenda.
- **Pourquoi ça compte pour moi** : je forme des gens à ne pas croire un écran trop vite. Là, l’écran se contredit tout seul.

### F4 - Les pièces Qualiopi sont générées, et introuvables à l’écran
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** : dans la même conversation, « Génère les fichiers Word ou Excel, pas seulement du texte dans le chat » : convention, convocation, feuille d’émargement, attestation. 149 s. Quatre `generate_document` OK. Aucun événement SSE `skill_file`. `GET` des messages : `extra_data` vide. L’écran *Fichiers* (`GET /api/files/`) : liste vide.
- **Ce que j’attendais** : quatre boutons de téléchargement sous la réponse, comme on me l’a promis pour les fichiers de skill (`MessageBubble.tsx` 226-232).
- **Ce qui s’est passé** : le chat affiche « Les documents sont prêts pour impression. » puis propose de les envoyer par e-mail. Pas de nom de fichier, pas de bouton. Les fichiers sont pourtant sur le disque (`outputs/Convention-Excel-AtelierMartin_….docx`, etc.). Le code prévoit d’émettre `skill_file` **avant** `done` (`chat.py` 2568-2591) et de le persister. Ce tour-ci, ni l’un ni l’autre. Un débutant conclut que rien n’a été produit.
- **Pourquoi ça compte pour moi** : je ne vais pas ouvrir un dossier caché pour récupérer une convention. Si le bouton n’est pas sous la phrase, pour un stagiaire de 58 ans le fichier n’existe pas.

### F5 - Ce qui a été généré ne passe pas un audit
- **Gravité** : bloquant
- **Nature** : limite_modele_local (contenu maigre, mélange) ; le titre = nom de fichier est un defaut_app du générateur
- **Source** : les deux (fichiers lus ; conversation et contacts API)
- **Ce que j’ai fait** : ouvrir les quatre fichiers produits. Relire les contacts et les factures déjà en base.
- **Ce que j’attendais** : une convention avec identité de l’organisme (SIRET, NDA), un prix, un programme annexé, une convocation **par** stagiaire, une feuille d’émargement matin/après-midi, une attestation **nominative**. C’est le minimum Qualiopi.
- **Ce qui s’est passé** :
  - Les trois Word commencent par le nom de fichier (`Convention-Excel-AtelierMartin`). Huit à dix lignes. Pas de SIRET, pas de n° de déclaration d’activité (pourtant saisi dans *Profil*, libellé « N° de déclaration d'activité (organisme de formation) », `ProfileTab.tsx` 372), pas de tarif, pas de signatures en bonne et due forme.
  - La convocation liste les 8 noms d’un coup. Prérequis inventé : « Avoir suivi la session Excel débutant (8-9 juillet 2026). » Ces dates sont celles de **la Mairie de Manosque**, un autre client, que j’avais enregistré à part. Elles n’étaient pas dans cette conversation. Elles se retrouvent sur un papier Atelier Martin.
  - L’attestation : « Stagiaire : [Nom] (signature) ». Un modèle, pas huit attestations.
  - L’émargement Excel est le seul utilisable en brouillon : les 8 noms, matin/après-midi, 15 et 16/09. Feuille intitulée *Données*. Pied de page « Généré par THERESE - Synoptia ».
  - La bibliothèque de prompts : recherche « formation », « qualiopi », « convention », « convocation », « emargement » = 0. Seule une « Attestation sur l'honneur » (admin), pas une attestation de formation.
- **Pourquoi ça compte pour moi** : mon audit de surveillance arrive. Un papier qui mélange deux clients, je ne le sors pas. Un modèle `[Nom]`, non plus. Mon tableur + Word, au moins, je les contrôle.

### F6 - Une facture OPCO en retard reste « Envoyée »
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** : créer FACT-2026-001 (Mairie, 2 400 €, émise le 10/07, échéance 10/08, statut *sent*) et FACT-2026-002 (Dupont, 1 400 €, *Marquer comme payée* au 30/06). Aujourd’hui : 28/08/2026. `GET /api/invoices/?status=overdue` : `[]`. `GET /api/dashboard/today` : `overdue_invoices: []`. L’écran *Devis et factures* (`InvoicesPanel.tsx` 30-41, 255-264) : statut *Envoyée*, état vide « Aucune facture », bouton *Facturation complète* vs titre *Devis et factures*.
- **Ce que j’attendais** : voir la Mairie en *En retard* sur l’accueil et dans la liste, 18 jours après l’échéance. C’est exactement le suivi OPCO que je fais dans Excel.
- **Ce qui s’est passé** : le brief ne remonte les factures que si l’échéance a plus de **30 jours** (`dashboard.py` 355-362, commentaire « Factures impayées > 30 jours »). Le statut *En retard* n’est pas calculé : il faut le poser à la main. FACT-2026-001 reste *Envoyée*. Le PDF, lui, écrit **SENT** et **PAID** en anglais, « EMETTEUR », « Date d'emission », « Date d'echeance », sans le NDA. L’accueil, au départ, ne me parlait pas de relance OPCO : « Branche tes mails ».
- **Pourquoi ça compte pour moi** : si je dois me souvenir de changer le statut, je n’avais pas besoin d’un logiciel. Mon tableur colore déjà la ligne en rouge.

### F7 - Le premier écran d’un débutant total
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface (`ConversationCanvasPrototype.tsx` 1568-1571, 1766-1787, 1812, 1873, `TodayDashboardCard.tsx` 143-153, `SetupChecklist.tsx` 51, `CapabilityCenter.tsx` 81-135 et 385)
- **Ce que j’ai fait** : me mettre à la place d’un stagiaire de 58 ans qui n’a eu aucune explication. Lire l’accueil, le rail, *Plus d’outils*.
- **Ce que j’attendais** : en trente secondes, savoir par où commencer pour « noter un client » ou « préparer une session ».
- **Ce qui s’est passé** : premier moment de perte, **immédiat**. Titre « Bonjour. » (pas de nom, profil vide). Sous-titre : « J’ai regroupé ce qui mérite ton attention. Tu peux agir ici, sans chercher le bon module. » Le mot *module* est déjà du jargon. Carte : « Branche tes mails pour que je te prépare la journée » / *Brancher mes mails*. *Mise en route* : *Connecter ton agenda*, *Compléter le profil de facturation*. Cinq puces *Essayer un autre parcours* : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Placeholder : « Demande à Thérèse d’organiser, créer ou agir… ». Pied : « Thérèse affiche les sources reçues et confirme les effets externes effectivement raccordés. » Rail : *Espaces de travail* ouvre *Projets*. *Plus d’outils* ouvre « Ce que Thérèse sait mobiliser », 29 capacités, groupes *Quotidien / Activité / Création / Décision / Automatisation / Contrôle*. Un débutant qui clique *Retrouver* lit « Aucun contact enregistré » / « La mémoire est prête, mais elle ne contient encore aucune personne. » / *Gérer mes contacts*. Il n’a pas demandé de mémoire.
  Il y a un calendrier local « Mon calendrier » dès le départ (`GET /api/calendar/calendars`), et *Mise en route* dit quand même « Connecter ton agenda » tant qu’on n’a rien créé. Après mes deux journées, `has_calendar` passe à vrai. Le débutant croit qu’il doit brancher Google pour noter une date.
- **Pourquoi ça compte pour moi** : je ne mets pas un stagiaire devant 29 capacités et cinq verbes. S’il se trompe de *Retrouver*, il se sent bête. C’est moi qu’il blâme.

## Verdict

Je ne rouvre pas THÉRÈSE demain pour remplacer le tableur. Je peux lui dicter un client et une liste de noms, ça marche, lentement. Je ne peux pas lui confier un dossier de session, ni des pièces d’audit, ni un suivi OPCO, et je ne peux pas enseigner un écran qui change de vocabulaire à chaque clic. Le jour où une session aura un nom, des stagiaires, des modèles Qualiopi visibles sous la réponse, et un mot par chose, j’y reviendrai. Pas avant.
