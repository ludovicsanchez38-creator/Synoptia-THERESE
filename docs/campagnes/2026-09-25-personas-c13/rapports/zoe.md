# Zoé, la contradictrice (testeuse d'ergonomie) : trace de la campagne

> Campagne « parcours et ergonomie », cycle 13, 25/09/2026. Frontend `http://127.0.0.1:1420` servi depuis `main` 02286c46 (le HEAD 0151d413 n'ajoute que la trace de Nathalie), moteur jetable `http://127.0.0.1:17393` (0.75.0), modèle `ollama / gemma4-tia:latest`. Instrument : Playwright MCP, document visible.
>
> Garde d'environnement au premier geste (11:17) : `{ visible: "visible", horloge: 33477.966 }`, viewport 1440×900, thème `dark`, racine 16 px. Sur consigne de l'orchestrateur, le stockage du navigateur n'a PAS été purgé au démarrage (les données de Claire, Hugo et Nathalie sont le terrain de l'attaque). Les 24 erreurs console présentes à l'arrivée sont des `ERR_CONNECTION_REFUSED` sur `/health`, `/api/auth/token` et `/api/config/stats`, émises pendant le redémarrage du moteur avant mon arrivée : bruit hérité, pas un constat.
>
> Gravité : la fiche ordonne perte de données > action en double > blocage > gêne ; je l'écris avec le vocabulaire des trois autres traces : **haute** (perte de données), **moyenne** (action en double, blocage ou montant faux sans alerte), **mineure** (gêne).

## Mon impression (première personne, cinq à dix lignes)

Je suis venue pour casser, et l'application a mieux tenu que je ne l'espérais sur le geste le plus bête : j'ai double-cliqué et triple-cliqué sur six écrans de création, je n'ai obtenu aucun doublon. Ce qui casse, c'est tout ce qui se passe entre deux gestes. Deux onglets ouverts sur la même fiche, et le second enregistrement efface le premier sans un mot, chaque onglet persuadé d'avoir gagné. Échap ou un clic à côté, et mon contact, mon devis ou mon projet à moitié tapés disparaissent, alors que la tâche et le rendez-vous, eux, me demandent si je veux vraiment abandonner : deux règles dans la même application. Un rechargement au mauvais moment, et l'Atelier me dit qu'il n'y a rien pendant que la trame s'écrit en coulisse, ou le chat me laisse une réponse de Thérèse qui dit « network error ». Dans un devis, taper « -2 » sur une quantité sélectionnée m'a donné 12 et un total à 14 407 € : c'est celui-là qui me fait peur, parce qu'il ne se voit pas. Au clavier, rien ne suit une seule règle : Entrée valide le devis mais pas le contact, et le focus arrive tantôt sur le titre, tantôt nulle part. À 200 %, l'Atelier garde ses trois colonnes et l'éditeur tient dans 131 pixels. Le contraste élevé est net, sauf qu'on ne sait plus quel filtre est choisi.

## Parcours (un bloc par attaque)

### Attaque 1. Impatience : double-clic et triple-clic sur chaque bouton de création (six écrans)

Méthode : double-clic Playwright réel (`dblclick`) ou triple-clic par script, trois `click()` espacés de 40 ms, chacun dans sa propre tâche JS (le rythme d'un triple-clic humain rapide ; React a le temps de se redessiner entre deux clics). Preuve : compte des POST dans `browser_network_requests` et relevé de l'API. État de référence relevé à 11:19 : 7 contacts, 3 projets, 2 tâches, 4 pièces (devis et factures), 1 document, 4 conversations, 2 rendez-vous.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1.1 | Contacts > « Nouveau contact », Zoé Doubleclic, double-clic « Créer » | un seul contact | 1 POST `/api/memory/contacts`, la fiche apparaît en tête, une seule fois | 02, 03 | conforme |
| 1.2 | Tâches > « Nouvelle tâche », titre, triple-clic « Enregistrer » | une seule tâche | 1 POST `/api/tasks` ; bouton `disabled` dès le 2e clic | 04 | conforme |
| 1.3 | Agenda > « Nouveau rendez-vous », titre, triple-clic « Enregistrer » | une seule confirmation, un seul rendez-vous | une seule fenêtre « Confirmer la création de l'événement », focus sur « Annuler » ; double-clic « Confirmer la création » : 1 POST `/api/calendar/events`. Le bouton « Enregistrer » n'est jamais désactivé (3 clics sur un bouton actif), mais la confirmation absorbe les doublons | 05, 06 | conforme |
| 1.4 | Projets > « Nouveau projet », triple-clic « Créer » | un seul projet | 1 POST `/api/memory/projects`, bouton `disabled` dès le 2e clic | 07 | conforme |
| 1.5 | Devis et factures > « Nouveau devis ou facture », type Devis, client Zoé, 1 ligne à 500 €, triple-clic « Créer » | un seul devis | 1 POST `/api/invoices` (DEV-2026-003) | 08, 09 | conforme |
| 1.6 | Fiche DEV-2026-003, double-clic « Convertir en facture » | la confirmation s'ouvre | **rien ne se passe à l'écran**, aucune requête : le 1er clic ouvre « Confirmer la conversion », le 2e tombe sur son voile, qui la referme | 10 | bug_candidate (zoe-01) |
| 1.7 | Même bouton, clic simple, puis double-clic « Convertir » dans la confirmation | une seule facture | la confirmation s'ouvre (focus resté derrière, sur « Convertir en facture ») ; 1 POST `convert-to-invoice` | 11, 12 | conforme (focus : zoe-09) |
| 1.8 | Documents > « Nouveau document », triple-clic « Créer » | un seul document | 1 POST `/api/documents`, puis la trame part toute seule (POST `/outline`) | 13 | conforme |
| 1.9 | Accueil, message tapé, double-clic « Poursuivre dans le chat » puis double-clic « Envoyer le message » | un seul envoi | le 1er bouton transfère le texte au chat sans l'envoyer ; le second : 1 POST `/api/chat/conversations`, 1 POST `/api/chat/send` | 18, 19 | conforme |

Verdict de l'attaque : aucun doublon sur six écrans ; le correctif du cycle tient. Seule cassure : le double-clic avale la confirmation de conversion.

### Attaque 2. Interruption : recharger, fermer, revenir en arrière

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 2.1 | Document « Zoé document triple-clic » juste créé, trame en génération (« Génération de la trame en cours… », « Annuler la génération »), rechargement de la page (`page.goto` de la même adresse, équivalent F5) à 11:25:05 | revenir où j'étais, ou au moins retrouver la génération | retour à l'Accueil (l'application n'a pas d'adresse par écran) ; « Travaux » garde son badge 1 et liste « Trame : Zoé document triple-clic, En cours, Arrêter » | 14, 15 | observation (l'écran quitté n'est pas restauré) |
| 2.2 | Documents > rouvrir le document | « génération en cours », avec « Annuler » | **« Aucune section pour l'instant. Génère une trame… » et un bouton « Générer la trame »** ; plus de bouton d'annulation dans l'Atelier | 16 | bug_candidate (zoe-02) |
| 2.3 | Cliquer « Générer la trame » | ne pas me le proposer | POST `/outline` → **409** ; le message « Une génération de trame est déjà en cours pour ce document. » est coupé à « …en cours pou » dans la barre du document (conteneur de 320 px en `overflow: hidden`, texte de 446 px, sans points de suspension ni infobulle) ; l'état vide reste affiché | 17 | bug_candidate (zoe-02) |
| 2.4 | Chat : « Zoé : réponds juste OK. » envoyé à 11:26:45, rechargement à 11:27:03 pendant l'attente de la réponse | la question reste, la réponse dit qu'elle a été interrompue, ou reprend | Travaux : « Zoé : réponds juste OK., **En échec** ». Le tiroir : « 2 messages » et l'aperçu **« network error »** ; la conversation rouverte montre une bulle de Thérèse « network error » (anglais, brut) ; la base (`GET /api/chat/conversations/4235f827…/messages`) n'a **qu'un** message, celui de l'utilisateur. Le magasin local `therese-chat` a enregistré `{role: "assistant", content: "network error"}` | 20 | bug_candidate (zoe-03) |

| 2.5 | Contacts > « Nouveau contact », Prénom « Zoé », Nom « Echap », Notes (une ligne de découverte), puis Échap | une demande « abandonner la saisie ? » | le formulaire se ferme sans rien dire ; rouvert, il est vide (`prenom: "", notes: ""`) ; focus rendu à « Nouveau contact » | 21, 22 | bug_candidate (zoe-04) |
| 2.6 | Même formulaire, saisie, clic sur le fond grisé au point (200, 450), hors du panneau (séquence `pointerdown/mousedown/pointerup/mouseup/click` déclenchée au point exact : le clic Playwright vise le centre du fond, qui est sous le panneau) | rien, ou une demande | le formulaire se ferme et la saisie est perdue ; code : `ContactModal.tsx:177-178`, `onClick={onClose}` sur le fond | (état mesuré au DOM) | bug_candidate (zoe-04) |
| 2.6 bis | Même formulaire, prénom et note, clic sur la croix « Fermer » (11:50) | une demande | fermé sans rien dire, aucune alerte | 63 | bug_candidate (zoe-04) |
| 2.7 | Devis et factures > « Nouveau devis ou facture », une ligne « Mission complète de trois jours… » à 1 800 €, Échap | une demande | fermé sans rien dire ; rouvert : description vide, prix « 0 » | 23 | bug_candidate (zoe-04) |
| 2.8 | Projets > « Nouveau projet », nom saisi, Échap | une demande | fermé sans rien dire, saisie perdue | (état mesuré au DOM) | bug_candidate (zoe-04) |
| 2.9 | Tâches > « Nouvelle tâche », titre et description, Échap | une demande | **« Abandonner les modifications ? » avec « Continuer la saisie » (focus) et « Abandonner »** | 24 | conforme, et c'est la règle que les autres formulaires ne suivent pas |
| 2.10 | Agenda > « Nouveau rendez-vous », titre et description, Échap | une demande | même protection que les tâches | (arbre : `alert "Abandonner les modifications ?"`) | conforme |
| 2.11 | Retour arrière du navigateur depuis Projets (`history.length` = 2, `history.state` nul) | rester dans l'application | la page quitte l'application pour `about:blank` | 25 | observation (l'application livrée est une fenêtre Tauri sans bouton « Précédent » ; le geste n'y est pas atteignable, je le note sans le classer en défaut) |

Bilan de l'attaque : la trame survit au rechargement côté moteur (terminée à 11:30 avec 11 sections), mais l'Atelier rouvert après le rechargement ne le sait pas ; la réponse du chat, elle, meurt et laisse une fausse bulle ; et trois formulaires sur cinq (contact, devis, projet) jettent la saisie à Échap, à la croix ou au clic sur le fond, quand les deux autres (tâche, rendez-vous) demandent confirmation.

### Attaque 3. Clavier seul : un contact, une tâche, un devis au Tab, Entrée et Échap

Méthode : touches réelles (`keyboard.press`) ; à chaque arrêt, l'élément actif et son indicateur de focus sont lus par `getComputedStyle` (contour ou ombre non transparente), **en place et 300 ms après l'arrêt**. Un premier journal pris au moment du `focusin` notait « sans indicateur » sur « Annuler » et « Créer » : c'était la transition CSS de 0,15 s en cours, pas un défaut ; remesurés en place, les deux ont l'anneau cyan (capture 26). Je n'ai retenu aucun défaut d'indicateur mesuré au vol.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 3.1 | Accueil, ⌘M | Contacts, focus sur le titre | Contacts, focus sur le titre « Contacts » (`H2`, `:focus-visible`) | (mesure DOM) | conforme |
| 3.2 | 3 Tab (« Importer (.vcf) », « Exporter », « Nouveau contact »), Entrée | le formulaire, focus dans « Prénom » | conforme, anneau à chaque arrêt | (mesure DOM) | conforme |
| 3.3 | Prénom, Tab, Nom « Clavier », **Entrée dans le champ Nom** | le contact est créé | rien : aucun POST, le formulaire reste ouvert | (réseau) | bug_candidate (zoe-05, revu après hugo-01) |
| 3.4 | 8 Tab (Entreprise, Email, Téléphone, Adresse, Notes, Tags, Annuler, Créer), Entrée | création, focus rendu | contact « Zoé Clavier » créé, focus rendu à « Nouveau contact » ; 14 frappes hors saisie pour un contact à deux champs | 26 | conforme (coût : zoe-05) |
| 3.5 | Depuis Contacts, ⌘T | Tâches, focus dans la vue | Tâches affichées, **focus sur `BODY`** (⌘M le posait sur le titre) | (mesure DOM) | bug_candidate (zoe-06, revu après hugo-10) |
| 3.6 | Tab jusqu'à « Nouvelle tâche », Entrée | le formulaire, focus dans « Titre » | le formulaire s'ouvre, **le focus reste sur « Nouvelle tâche »** ; il faut 3 Tab (« Retour », « Enregistrer », puis « Titre ») : le bouton d'enregistrement passe avant le premier champ | (journal de focus) | bug_candidate (zoe-06) |
| 3.7 | Titre « Zoé tâche clavier », **Entrée dans le champ** | la tâche est enregistrée | rien (aucun POST `/api/tasks`) ; Maj+Tab vers « Enregistrer », Entrée : enregistrée, focus rendu à « Nouvelle tâche » | 27 | bug_candidate (zoe-05) |
| 3.8 | Depuis Tâches, ⌘I | Devis et factures, focus dans la vue | **focus sur `BODY`** | (mesure DOM) | bug_candidate (zoe-06) |
| 3.9 | Tab, Entrée sur « Nouveau devis ou facture » | focus dans le premier champ utile | **focus sur « Fermer »** (la croix) ; l'ordre de tabulation compte 18 arrêts avant les dates natives (chaque date ajoute 3 à 4 arrêts : jour, mois, année, calendrier) | 28, 29 | observation (le focus initial sur la croix est un choix discutable, pas une règle écrite) |
| 3.10 | Tab « Devis », Entrée ; Tab ×3 jusqu'à « Client », touche « z » | Devis, client choisi | « Nouveau devis », client « Zoé Clavier » choisi au clavier | 29 | conforme |
| 3.11 | Description, Tab ×2, Prix « 300 », **Entrée dans le champ Prix** | cohérent avec les autres formulaires | **le devis est créé** (1 POST `/api/invoices`), focus rendu à « Nouveau devis ou facture » ; c'est le seul des trois formulaires où Entrée valide | (réseau) | bug_candidate (zoe-05) |
| 3.12 | Projets, focus clavier sur « Supprimer Veille IA » | le bouton visible au focus | visible (aucun ancêtre en opacité < 1 au focus) | (mesure DOM) | conforme |
| 3.13 | Même carte : structure de focus | un arrêt par action nommée | la carte est un `div role="button" tabindex="0" aria-roledescription="sortable"` **sans nom**, qui contient deux vrais `button` (« ouvrir » et « Supprimer ») : trois arrêts par carte dont un muet, et des contrôles imbriqués dans un bouton | (attributs relevés au DOM, arbre : `button [ref=f8e703]` sans nom) | bug_candidate (zoe-07) |

Bilan : le focus est visible partout où je l'ai mesuré en place, mais le clavier ne suit pas une seule règle. Entrée valide le devis, pas le contact ni la tâche ; le focus d'arrivée est le titre (⌘M), le corps de page (⌘T, ⌘I), le bouton d'ouverture (tâche) ou la croix (devis).

### Attaque 5. Saisies hostiles : vide, espaces, 5 000 caractères, émojis, balises, montants à la française, collage de tableau

Méthode : saisies par `fill` (une seule valeur d'un coup, comme un collage), par frappe lettre à lettre (`pressSequentially`), ou, pour les textes de 300 et 5 000 caractères, par le mutateur natif de `value` suivi d'un évènement `input` (React le voit comme une frappe). La preuve est ce que l'API a stocké, relu après enregistrement.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 5.1 | Nouveau contact, Prénom = cinq espaces, « Créer » | refus lisible | « Le prénom ou le nom est requis » | 30 | conforme |
| 5.2 | Prénom 300 caractères sans espace, entreprise `<b>Gras</b> 🚀👩🏽‍💻 "guillemets" & 'apostrophe' ; DROP TABLE contacts;--`, e-mail « pas-un-email », téléphone « +33 6 ☎️ abc », notes 5 000 caractères | refus de l'e-mail, puis limite annoncée | « Format email invalide », affiché en bas du formulaire, sans marquer le champ (`aria-invalid` absent) | 31, 32 | conforme (message à distance du champ : observation) |
| 5.3 | E-mail corrigé, « Créer » | la limite du prénom dite, sur le champ | **422** ; l'écran dit seulement « Données invalides dans la requête ». La réponse du moteur précise pourtant `{"field":"first_name","message":"String should have at most 200 characters"}` ; aucun champ ne porte `maxLength` (les huit valent -1) | 33 | bug_candidate (zoe-08) |
| 5.4 | Prénom ramené à 150 caractères, « Créer » | stockage fidèle, affichage échappé | stocké tel quel (150 caractères, balises et guillemets intacts, téléphone « +33 6 ☎️ abc » accepté) ; affiché échappé dans la liste, le nom long passe à la ligne sans casser la rangée ; notes : 4 954 points de code côté moteur pour 5 000 unités UTF-16 côté navigateur, soit les 46 fusées comptées deux fois par JavaScript, **rien de perdu** | 34 | conforme |
| 5.5 | Nouveau devis, Prix HT : « 1 000,50 € » collé d'un bloc | 1 000,50, ou un refus dit | **le champ reste à « 0 »**, sans message | (mesure DOM) | bug_candidate (zoe-10) |
| 5.6 | Même champ, « 1 000,50 € » tapé lettre à lettre | 1 000,50 | espace et « € » filtrés en silence, valeur « 1000,50 », total 1 200,60 € TTC, juste | 35 | conforme |
| 5.7 | Quantité « 1 » sélectionnée (Cmd+A, sélection 0-1), puis frappe de « -2 » | -2 refusé, ou 2 | le « - » est refusé et **la sélection s'effondre** (0-1 devient 1-1), puis « 2 » s'ajoute : **quantité 12**, total **14 407,20 € TTC** au lieu de 1 200,60 €, sans alerte | 35 | bug_candidate (zoe-09) |
| 5.8 | Description : collage d'un tableau Excel (trois lignes séparées par des tabulations ; évènement `paste` puis `insertText`) | les lignes réparties, ou au moins le texte | tout aplati en une seule description (« Désignation⇥Qté⇥PU HT Audit ergonomie⇥1⇥500 Formation… », 66 caractères), quantité et prix inchangés | 36 | proposal (zoe-P2) |
| 5.9 | Agenda, rendez-vous du 30/09 au 28/09 | refus lisible | « La date et l'heure de fin doivent être postérieures au début. » | 37 | conforme |
| 5.10 | Pendant la question « Abandonner les modifications ? » du rendez-vous, clic sur « Projets » dans le rail | rester, la question ouverte | la vue reste sur l'Agenda (la coque retient la sortie, B-978) ; la surbrillance de « Projets » dans la capture est le survol de la souris | 37 | conforme |
| 5.11 | Nouveau projet, Budget « -5000 » (le champ déclare `min="0"`), « Créer » | refus | **projet créé, budget -5000.0 en base** ; aucun message ; le budget ne s'affiche pas dans la liste | 38 | connu : B-1244 (règle des budgets en attente de Ludo), non re-signalé |

### Attaque 7. Enchaînements absurdes : aide, palette, Paramètres, puis Échap trois fois

Méthode : après chaque geste, relevé de toutes les couches visibles (`[role=dialog]`, régions nommées) avec leur `z-index` effectif (premier ancêtre positionné) et du focus.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 7.1 | ⌘K, « aide » | l'aide | « 0 résultat » ; l'aide du rail est l'icône « ? », nommée « Plus d'outils » | (arbre) | observation |
| 7.2 | « ? » (Plus d'outils) > « Brief du jour » | un panneau | ramène à l'Accueil, rien ne s'ouvre | 39 | observation |
| 7.3 | « ? » > « Email » | un panneau | l'Accueil passe en mode « Écrire » (carte « Messages reçus, aucune messagerie branchée ») et le panneau « Nouveau message / Rédaction » s'ouvre à droite ; couches : `region "Écrire un message" z=20` | 40 | conforme |
| 7.4 | ⌘K par-dessus, « Paramètres », Entrée | Paramètres au-dessus | `dialog "Paramètres" z=50`, focus « Fermer les paramètres » | 41 | conforme |
| 7.5 | Échap ×3 | refermer dans l'ordre inverse, revenir d'où je viens | Échap 1 : Paramètres fermé ; Échap 2 : panneau « Rédaction » fermé, focus rendu à « Plus d'outils » ; **Échap 3 : rien**, l'Accueil reste en mode « Écrire » avec sa carte « Messages reçus » | 42 | observation (je ne reviens pas à l'Accueil d'où je suis partie, mais aucune règle écrite ne dit qu'Échap quitte un mode de l'établi) |
| 7.6 | Paramètres ouverts (⌘,), puis ⌘K | rien, ou la palette au-dessus | rien : la palette ne s'ouvre pas sous une fenêtre modale | (mesure DOM) | conforme |
| 7.7 | Tiroir Conversations, puis « Travaux », puis « Contrôle des données » | une fenêtre d'en-tête à la fois, ou empilées lisiblement | trois couches : `region "Conversations" z=30`, `dialog "Travaux en cours" z=50`, `dialog "Centre de confiance" z=65` ; **Travaux reste ouvert sous le Centre de confiance, au même coin** : son titre coupé (« Tr ») et sa frise dépassent sur le bord gauche du Centre | 43, 44 | bug_candidate (zoe-12) |
| 7.8 | Échap ×3 | ordre inverse | Centre, puis Travaux, puis Conversations : ordre juste ; après le 2e Échap le focus reste sur « Contrôle des données » (la fenêtre fermée était Travaux) | (mesure DOM) | conforme |
| 7.9 | ⌘M (Contacts), ⌘T (Tâches), clic « Retour » | le bouton dit où il mène | il ramène à **Contacts** (juste) mais son nom accessible est « Revenir à la conversation unifiée » sur toutes les vues (`PrototypeUnifiedViewCanvas.tsx:52`, libellé fixe) | 45 | bug_candidate (zoe-13) |

Bilan : la pile d'Échap ne ment pas ; ce sont les noms qui mentent (« Retour » annoncé vers la conversation), et deux fenêtres d'en-tête qui se recouvrent au lieu de se remplacer.

### Attaque 6. Deux onglets : la même fiche modifiée des deux côtés

Méthode : deux onglets Playwright du même navigateur. Toute action et toute lecture se font dans l'onglet au premier plan, garde `visibilityState` relancée à chaque bascule (visible, horloge active les deux fois). Preuve : relecture de l'API après chaque enregistrement et corps de la requête.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 6.1 | Onglet A : Contacts > « Zoé Doubleclic » (formulaire « Modifier le contact », entreprise « Contradiction SARL ») laissé ouvert | | | (arbre) | |
| 6.2 | Onglet B (nouvel onglet, 11:42) : même fiche, Entreprise → « Version onglet B », « Mettre à jour » | enregistré | API : `company: "Version onglet B"`, `updated_at 09:42:17` | 46 | conforme |
| 6.3 | Retour à l'onglet A (visible, horloge 693 054 ms) | le formulaire rafraîchi, ou un avertissement | le formulaire montre toujours « Contradiction SARL », aucun bandeau | 47 | (voir 6.4) |
| 6.4 | Onglet A : Notes → « Note saisie dans l'onglet A », « Mettre à jour » | ma note ajoutée, l'entreprise de B conservée, ou un conflit signalé | **l'entreprise de B est effacée** : API `company: "Contradiction SARL"`, `notes: "Note saisie dans l'onglet A"`. Le `PATCH` renvoie tous les champs du formulaire, périmés compris : `{"first_name":"Zoé","last_name":"Doubleclic","company":"Contradiction SARL","email":null,…,"notes":"Note saisie dans l'onglet A","tags":null}`. Aucun message, ni dans A ni dans B | 48 | bug_candidate (zoe-14) |
| 6.5 | Retour à l'onglet B | la valeur réelle | la liste affiche encore « Version onglet B » : chaque onglet croit avoir gagné | 49 | bug_candidate (zoe-14) |

Angle mort : je n'ai pas testé la course des magasins locaux (`localStorage` partagé, `therese-chat`, `task-storage`…) entre les deux onglets ; le conflit serveur suffisait à prouver la perte.

### Attaque 4. Petite fenêtre : 1024×700, 800×600, puis zoom 200 %

Méthode : `setViewportSize`. Le zoom navigateur n'est pas pilotable par Playwright MCP (les raccourcis clavier vont à la page, pas au navigateur) : je l'ai émulé par une fenêtre de **720×450**, qui est exactement la largeur et la hauteur CSS que voit la page à 1440×900 zoomée à 200 % (les points de rupture CSS se déclenchent comme au vrai zoom, contrairement à `style.zoom`). À chaque écran, une mesure DOM relève les contrôles dont la boîte sort de la fenêtre et les textes coupés sans points de suspension.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 4.1 | 1024×700, Contacts | chaque rangée lisible | la rangée du contact au prénom de 150 caractères sans espace (créé en 5.4) déborde jusqu'à 1 312 px : le nom passe **sous le badge « RGPD ? » et les icônes**, et une barre de défilement horizontale apparaît sous la liste. À 1440 px le même nom passait à la ligne | 50 | bug_candidate (zoe-15) |
| 4.2 | 1024×700, Agenda semaine | lisible | aucun débordement ; titres d'évènements tronqués avec points de suspension | 51 | conforme |
| 4.3 | 800×600, Agenda | lisible | aucun débordement ; les commandes passent sur trois lignes et occupent 270 px, la grille ne montre plus que 10 h à 13 h 30 | 52 | observation |
| 4.4 | 800×600, Devis et factures > « Nouveau devis ou facture » | formulaire utilisable | tient dans la fenêtre, corps défilant, « Créer » visible | 53 | conforme |
| 4.5 | 800×600, liste des devis et factures | voir le montant et les actions | le tableau fait **1 176 px dans un cadre de 686** : Échéance, **Montant TTC**, « PDF » et « Supprimer » (1 070 à 1 241 px) sont hors vue ; la barre de défilement horizontale est au bas du tableau, sous la ligne de flottaison | 54 | bug_candidate (zoe-16, même effet que nathalie-15 à 125 %, revu ici par la largeur) |
| 4.6 | 720×450 (zoom 200 %), Accueil | lire « Ton attention aujourd'hui » | le composeur (175 px) recouvre la carte ; **« Voir la suite » est posé sur le titre** de la carte (boîtes mesurées : bouton 215-245 px, titre 228-251 px, chevauchement vrai) | 55 | bug_candidate (zoe-17) |
| 4.7 | Même taille, en-tête | pouvoir chercher à la souris | le bouton « Rechercher ⌘K » **n'existe plus dans le DOM** (le nom de l'espace de travail est en `display: none`) ; seul le raccourci clavier reste | 55 | bug_candidate (zoe-17) |
| 4.8 | 720×450, Contacts > « Nouveau contact » | formulaire utilisable | tient (383 px de haut), corps défilant (219 px visibles sur 638), « Créer » visible | 56 | conforme |
| 4.9 | 720×450, Atelier, document « Zoé document triple-clic » | pouvoir rédiger | les trois colonnes restent côte à côte : **l'éditeur central fait 131 px**, le volet Pistes sort à droite (« Aucune piste pour l'instan… »), et son bouton **« Replier le volet Pistes » est à 715-751 px** : 5 px visibles, aucun conteneur ne défile pour l'atteindre (il reste joignable au clavier) | 57 | bug_candidate (zoe-18) |

### Attaque 8. Thème sombre et contraste élevé, rejoués sur Paramètres, Devis et factures et Contacts

Méthode : le réglage existe (Paramètres > Accessibilité et affichage > « Contraste élevé »), je n'ai donc pas eu besoin d'émuler `prefers-contrast`. Ratios WCAG calculés par script sur le texte et le fond effectif (couches semi-transparentes composées). Le réglage a été remis à son état d'origine en fin d'attaque (`therese-accessibility` : `highContrast: false`, `theme: "dark"`, relu dans `localStorage`).

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 8.1 | Sombre normal, Paramètres > Accessibilité | textes lisibles | ratio le plus faible 7,39:1 (cyan sur fond), textes atténués #B6C7DA à 9,85:1 | (mesure DOM) | conforme |
| 8.2 | Activer « Contraste élevé » | effet immédiat, sans enregistrer | immédiat : `data-high-contrast="true"`, texte atténué #E0E0E0, bordures #FFFFFF ; une phrase jaune explique que le contraste élevé prend le pas sur le thème | 58 | conforme |
| 8.3 | Échap pour fermer Paramètres | fermé | la première fois, Paramètres est resté ouvert (le ⌘I suivant n'a rien fait) ; un second Échap l'a fermé. **Rejoué une fois : fermé du premier coup.** Je ne sais pas prouver la cause | 59 | écarté faute de preuve |
| 8.4 | Contraste élevé, Devis et factures | lisible | ratio le plus faible 7,13:1 (« Supprimer », rouge #FF6B6B) ; statuts en couleurs pleines (bleu 9,33:1, vert 14,43:1) | 60 | conforme |
| 8.5 | Même écran, filtres « Type » et « Statut » | voir lequel est sélectionné | le filtre sélectionné (« Tout », « Toutes ») ne se distingue plus : texte #FFFFFF contre #E0E0E0 (1,32:1 entre les deux états), fond #0A0A0A contre transparent sur noir (1,06:1), même graisse, et l'ombre qui marque la sélection vaut `rgba(16, 28, 54, 0.05)`, invisible sur noir | 60 | bug_candidate (zoe-19) |
| 8.6 | Contraste élevé, Contacts : filtres « Tout / Global / Projet / Conv. » | idem | même mesure, même effacement de l'état sélectionné | 62 | bug_candidate (zoe-19) |
| 8.7 | Survol de « Supprimer Karim Benali » en contraste élevé | l'icône reste lisible | rouge #FF6B6B sur noir, 7,57:1 | 62 | conforme |
| 8.8 | Retour en sombre normal, mêmes filtres | | sélectionné : fond #131B35, texte #E6EDF7 ; non sélectionné : transparent, #B6C7DA ; la différence existe mais repose sur la même ombre à 5 % | (mesure DOM) | observation |

## Constats numérotés

Captures : `docs/campagnes/2026-09-25-personas-c13/captures/zoe/NN-…png`. Gravité : haute = perte de données, moyenne = action en double, blocage ou montant faux sans alerte, mineure = gêne.

**zoe-14, bug_candidate, haute : deux onglets sur la même fiche, le second enregistrement efface le premier sans rien dire.**
Écran : Contacts > fiche « Modifier le contact ». Étapes : (1) onglet A, ouvrir la fiche « Zoé Doubleclic » et la laisser ouverte ; (2) onglet B, même fiche, Entreprise → « Version onglet B », « Mettre à jour » ; (3) onglet A, Notes → « Note saisie dans l'onglet A », « Mettre à jour ». Attendu : la note ajoutée et l'entreprise de B conservée, ou un conflit annoncé. Observé : `company` revient à « Contradiction SARL » en base, la valeur de B est perdue ; l'onglet B continue d'afficher « Version onglet B ». Preuve : captures 46 à 49, API relue après chaque enregistrement, corps du `PATCH /api/memory/contacts/8564daa3…` : `{"first_name":"Zoé","last_name":"Doubleclic","company":"Contradiction SARL","email":null,"phone":null,"address":null,"notes":"Note saisie dans l'onglet A","tags":null}` (le formulaire renvoie tous ses champs, périmés compris, sans version ni date de référence). Même risque pour qui garde une fiche ouverte pendant que Thérèse modifie le contact depuis le chat (non testé).

**zoe-04, bug_candidate, moyenne : Échap ou un clic sur le fond jette la saisie de trois formulaires sur cinq, sans demander.**
Écrans : « Nouveau contact », « Nouveau devis ou facture », « Nouveau projet ». Étapes : ouvrir le formulaire, remplir (prénom et notes ; une ligne de devis à 1 800 € ; un nom de projet), appuyer sur Échap, ou cliquer sur la croix « Fermer » ou sur le fond grisé hors du panneau (contact). Attendu : la question « Abandonner les modifications ? » que posent déjà les formulaires Tâche et Rendez-vous. Observé : fermeture immédiate, formulaire vide à la réouverture. Preuve : captures 21, 22, 23, 24, 63 ; `ContactModal.tsx:177-178` (`onClick={onClose}` sur le fond) ; la règle existe (`hooks/useAbandonDeSaisie.ts`, B-973, B-974, B-978) mais n'est branchée que sur `TaskForm.tsx` et `EventForm.tsx`. Le fond cliquable contredit aussi l'arbitrage de BUG-156 (Paramètres ne se ferment plus au clic sur le fond).

**zoe-09, bug_candidate, moyenne : dans un devis, une touche refusée efface la sélection, et la frappe suivante multiplie la quantité.**
Écran : « Nouveau devis », ligne 1. Étapes : quantité « 1 », Cmd+A (sélection 0-1), taper « -2 ». Attendu : -2 refusé avec un mot, ou la quantité remplacée par 2. Observé : le « - » est refusé, la sélection passe de (0,1) à (1,1), puis « 2 » s'ajoute : quantité **12**, total **14 407,20 € TTC** au lieu de 1 200,60 €, sans alerte. Preuve : mesures `selectionStart/End` et total à chaque frappe (étape 5.7), capture 35 ; `InvoiceForm.tsx:241-244` (`updateDecimalLineInput` sort sans rien faire quand `isValidDecimalDraft` refuse, le champ contrôlé est redessiné et le navigateur place le curseur en fin). Même mécanisme pour une espace ou « € » tapés sur une sélection.

**zoe-02, bug_candidate, moyenne : après un rechargement, l'Atelier dit « aucune section » pendant que la trame se génère, et propose de la relancer.**
Écran : Atelier, document neuf. Étapes : créer un document (la trame part seule), recharger la page, rouvrir le document. Attendu : « Génération de la trame en cours… » et « Annuler la génération ». Observé : état vide « Aucune section pour l'instant » et bouton « Générer la trame » ; le clic renvoie **409**, dont le message est coupé à « …en cours pou » ; l'annulation n'est plus possible que depuis « Travaux ». La trame s'est bien terminée côté moteur (11 sections relues en base à 11:30) ; je n'ai pas laissé l'Atelier ouvert pendant ce temps, je ne sais donc pas s'il se serait rafraîchi seul. Preuve : captures 13 à 17 ; Travaux « Trame : Zoé document triple-clic, En cours » ; mesure du message (conteneur 320 px, `overflow: hidden`, texte de 446 px, pas de points de suspension) ; `OutlineTree.tsx:199-215` ne connaît que l'état local `isLoading`, perdu au rechargement.

**zoe-03, bug_candidate, moyenne : recharger pendant une réponse laisse une fausse réponse « network error » de Thérèse.**
Écran : chat. Étapes : envoyer « Zoé : réponds juste OK. », recharger pendant l'attente, ouvrir le tiroir puis la conversation. Attendu : ma question, et une mention « réponse interrompue » ou la reprise. Observé : tiroir « 2 messages » avec l'aperçu « network error », bulle de Thérèse « network error » (anglais, brut) ; en base un seul message ; Travaux « En échec ». Preuve : capture 20, `GET …/4235f827…/messages` (1 message), `localStorage["therese-chat"]` (`{role:"assistant", content:"network error"}`), tiroir encore faux à la capture 44 ; `ChatInput.tsx:843-851` écrit `error.message` tel quel dans la bulle, et la conversation rouverte n'est pas relue depuis la base.

**zoe-18, bug_candidate, moyenne : à 200 %, l'Atelier devient inutilisable pour écrire.**
Écran : Atelier, 720×450 (équivalent CSS du zoom 200 % sur 1440×900). Étapes : ouvrir un document. Attendu : colonnes empilées ou volets repliés. Observé : trois colonnes côte à côte, **éditeur de 131 px**, volet Pistes coupé à droite, bouton « Replier le volet Pistes » à 715-751 px (5 px visibles, aucun défilement horizontal pour l'atteindre ; joignable au clavier seulement). Preuve : capture 57, boîtes mesurées au DOM.

**zoe-01, bug_candidate, mineure : un double-clic sur « Convertir en facture » ne fait rien.**
Écran : fiche d'un devis. Étapes : double-clic sur « Convertir en facture ». Attendu : la confirmation. Observé : rien, aucune requête ; le premier clic ouvre « Confirmer la conversion », le second tombe sur son voile (`absolute inset-0`, `onClick={() => setShowConvertDialog(false)}`) qui la referme. Au clic simple, la confirmation s'ouvre mais le focus reste derrière, sur « Convertir en facture ». Preuve : captures 10 et 11, réseau, `InvoiceForm.tsx:853-858`.

**zoe-05, bug_candidate, mineure : Entrée valide le devis mais ni le contact ni la tâche (revu après hugo-01).**
Étapes : taper dans « Nom » d'un nouveau contact puis Entrée ; dans « Titre » d'une nouvelle tâche puis Entrée ; dans « Prix HT » d'un nouveau devis puis Entrée. Observé : contact et tâche, rien (aucun POST) ; devis, créé (1 POST `/api/invoices`). Un contact à deux champs coûte 14 frappes hors saisie. Preuve : réseau aux étapes 3.3, 3.7, 3.11 ; captures 26 à 29.

**zoe-06, bug_candidate, mineure : le focus d'arrivée change d'un écran à l'autre (revu après hugo-10).**
Observé : ⌘M depuis l'Accueil pose le focus sur le titre « Contacts » ; ⌘T depuis Contacts et ⌘I depuis Tâches le laissent sur `BODY` ; « Nouvelle tâche » ouvre le formulaire en gardant le focus sur le bouton, et « Enregistrer » passe avant le premier champ (3 Tab pour atteindre « Titre ») ; « Nouveau devis ou facture » pose le focus sur la croix « Fermer ». Preuve : mesures `document.activeElement` aux étapes 3.1 à 3.9. Hypothèse, non prouvée : `PrototypeUnifiedViewCanvas` reste monté d'une vue à l'autre, et son focus initial sur le titre (`data-dialog-autofocus`) ne rejoue qu'au montage.

**zoe-07, bug_candidate, mineure : chaque carte de projet est un bouton sans nom qui contient deux autres boutons.**
Écran : Projets. Preuve : attributs relevés (`div role="button" tabindex="0" aria-roledescription="sortable" aria-describedby="DndDescribedBy-4"`, sans `aria-label`), qui contient un `button` d'ouverture et le `button "Supprimer Veille IA"` ; l'arbre d'accessibilité montre `button [ref=f8e703]` sans nom. Trois arrêts de tabulation par carte, dont un muet ; contrôles interactifs imbriqués.

**zoe-08, bug_candidate, mineure : « Données invalides dans la requête » ne dit ni quel champ ni quelle limite.**
Écran : « Nouveau contact ». Étapes : prénom de 300 caractères, « Créer ». Observé : 422 et ce seul message, alors que le moteur répond `{"field":"first_name","message":"String should have at most 200 characters"}` ; aucun champ ne porte `maxLength`. Preuve : capture 33, corps de la réponse 422.

**zoe-10, bug_candidate, mineure : coller « 1 000,50 € » dans un prix ne fait rien.**
Écran : « Nouveau devis », Prix HT. Observé : collé d'un bloc, la valeur reste « 0 », sans message ; tapé lettre à lettre, « 1000,50 » (juste). Preuve : étapes 5.5 et 5.6, `InvoiceForm.tsx:241-244`.

**zoe-11, retiré** : le budget de projet négatif accepté (étape 5.11, capture 38, `budget: -5000.0` en base malgré `min="0"`) relève de B-1244, règle des budgets en attente de Ludo ; vérifié dans `.app-loop/state.json` (« le chat refuse un négatif, la route et le tableur l'acceptent »). Non re-signalé, numéro laissé vide.

**zoe-12, bug_candidate, mineure : deux fenêtres d'en-tête se recouvrent au même coin.**
Étapes : ouvrir « Travaux », puis « Contrôle des données ». Observé : `dialog "Travaux en cours" z=50` reste ouvert sous `dialog "Centre de confiance" z=65` ; son titre coupé (« Tr ») et sa frise dépassent sur le bord du Centre. Preuve : captures 43 et 44, relevé des couches.

**zoe-13, bug_candidate, mineure : « Retour » annonce la conversation et ramène à l'écran précédent.**
Étapes : ⌘M, ⌘T, « Retour ». Observé : retour à Contacts (juste), mais le nom accessible du bouton est « Revenir à la conversation unifiée » sur toutes les vues. Preuve : capture 45, `PrototypeUnifiedViewCanvas.tsx:52`.

**zoe-15, bug_candidate, mineure : un nom sans espace passe sous les actions de la rangée.**
Écran : Contacts, 1024×700. Observé : le prénom de 150 caractères (étape 5.4) s'étend jusqu'à 1 312 px, passe sous « RGPD ? » et les icônes, et fait apparaître une barre de défilement horizontale. Un e-mail ou une adresse web longs feraient pareil. Preuve : capture 50, mesure DOM.

**zoe-16, bug_candidate, mineure : à 800 px, la liste des devis et factures cache le montant et les actions (même effet que nathalie-15).**
Observé : tableau de 1 176 px dans un cadre de 686 ; Échéance, Montant TTC, « PDF », « Supprimer » hors vue ; la barre de défilement horizontale est au bas du tableau, sous la ligne de flottaison. Preuve : capture 54, mesure DOM.

**zoe-17, bug_candidate, mineure : à 200 %, l'Accueil superpose et retire.**
Écran : Accueil, 720×450. Observé : « Voir la suite » chevauche le titre « Ton attention aujourd'hui » (boîtes mesurées) ; le composeur recouvre la carte ; le bouton « Rechercher ⌘K » n'est plus dans le DOM (seul le raccourci reste). Preuve : capture 55, mesures.

**zoe-19, bug_candidate, mineure : en contraste élevé, on ne voit plus quel filtre est sélectionné.**
Écrans : Devis et factures, Contacts, contraste élevé actif. Observé : sélectionné contre non sélectionné, texte #FFFFFF contre #E0E0E0 (1,32:1), fond #0A0A0A contre noir (1,06:1), même graisse, ombre `rgba(16, 28, 54, 0.05)` invisible sur noir ; très en dessous des 3:1 attendus pour l'état d'un composant (WCAG 1.4.11). Preuve : captures 60 et 62, styles calculés.

**zoe-20, bug_candidate, mineure : la génération de trame ne rafraîchit pas la date du document.**
Écran : Atelier, liste des documents (triée par `updated_at` décroissant). Étapes : créer un document, laisser la trame se générer (11 sections, terminée vers 11:30). Attendu : `updated_at` avance, comme le promet la note « `Document.updated_at` figé : CORRIGÉ » du `CLAUDE.md` du dépôt (`_touch_document` appelé par `create_section`… « un document qui vit remonte dans la liste triée par `updated_at desc` »). Observé : `created_at 2026-09-25T09:24:45.331372`, `updated_at 2026-09-25T09:24:45.331408`, `sections_total 11`, relu à 11:48 par `GET /api/documents`. Invisible aujourd'hui (le document était déjà le plus récent), mais une trame régénérée sur un vieux document le laisserait en bas de la liste.

### Propositions pour le portail humain

- **zoe-P1** : dans « Travaux », chaque ligne pourrait ouvrir l'objet qu'elle nomme (la trame en cours mène à son document) ; aujourd'hui ce sont des textes inertes (`generic`), et c'est le seul endroit qui savait que la trame tournait (étape 2.1).
- **zoe-P2** : coller un tableau (tabulations et sauts de ligne) dans une ligne de devis pourrait créer les lignes ; aujourd'hui tout est aplati dans une seule description (étape 5.8).
- **zoe-P3** : après un rechargement, rouvrir l'écran quitté (l'application revient toujours à l'Accueil ; étape 2.1).
- **zoe-P4** : « aide » dans ⌘K rend « 0 résultat », et l'icône « ? » du rail s'appelle « Plus d'outils » (étape 7.1 ; voisin de hugo-15).

### Observations (preuve insuffisante pour un défaut, ou pas de règle écrite)

- Retour arrière du navigateur : quitte l'application vers `about:blank` (capture 25) ; non atteignable dans la fenêtre Tauri livrée.
- Échap ne quitte pas le mode « Écrire » de l'Accueil ouvert depuis « Plus d'outils > Email » (étape 7.5).
- À 800×600, l'Agenda ne montre plus que trois heures et demie de grille (capture 52).
- « Format email invalide » s'affiche en bas du formulaire, sans marquer le champ (`aria-invalid` absent, capture 32) ; le téléphone accepte « +33 6 ☎️ abc ».

### Écartés faute de preuve

- Paramètres resté ouvert après un premier Échap (étape 8.3) : non reproduit au second essai.
- « Sans indicateur de focus » sur « Annuler » et « Créer » au premier journal clavier : artefact de mesure (transition CSS de 0,15 s en cours), démenti par la mesure en place.

## Transitions couvertes et angles morts

**Transitions couvertes** (62 captures numérotées de 01 à 63, la 61 manquante après une capture d'élément refusée par l'instrument ; 28 relues à l'image, les autres vérifiées au même instant par l'arbre d'accessibilité ou une mesure DOM) : création de contact, tâche, rendez-vous (avec confirmation), projet, devis, conversion devis vers facture, document, envoi de message, chacune au double ou au triple clic ; rechargement pendant une trame et pendant une réponse du chat, réouverture du document et de la conversation, Travaux avant et après ; Échap sur cinq formulaires, croix et clic sur le fond sur le formulaire de contact ; retour arrière du navigateur ; parcours complets au clavier (contact, tâche, devis) ; 1024×700, 800×600 et 720×450 sur Accueil, Contacts, Agenda, Devis et factures (liste et formulaire), Atelier ; saisies hostiles sur contact, devis, rendez-vous, projet ; deux onglets sur une fiche contact ; trois enchaînements de couches (aide puis ⌘K puis Paramètres, Paramètres puis ⌘K, Conversations puis Travaux puis Centre de confiance) et le bouton « Retour » ; contraste élevé sur Paramètres, Devis et factures, Contacts, avec un survol.

**Angles morts** :
- Zoom navigateur réel non pilotable : émulé par la taille CSS équivalente (720×450).
- Collage réel depuis le presse-papiers non disponible : émulé par l'évènement `paste` suivi d'`insertText`, ou par `fill` (une seule valeur d'un coup).
- Course des magasins locaux (`localStorage`) entre deux onglets : non testée.
- Une seule génération du modèle local dans toute la campagne (la trame) et une réponse de chat interrompue exprès ; je n'ai pas vu de réponse complète.
- Pas de lecteur d'écran réel : les noms accessibles viennent de l'arbre Playwright et des attributs.
- `prefers-reduced-motion` et le thème clair non rejoués.

**Données laissées en place** (état relu à 11:48 par l'API) : contacts « Zoé Doubleclic » (entreprise « Contradiction SARL », note de l'onglet A), « Zoé Clavier », « Zoé…x Hostile » (150 caractères, entreprise à balises et émojis, notes de 5 000 caractères) ; tâches « Zoé tâche triple-clic », « Zoé tâche clavier » ; rendez-vous « Zoé rdv triple-clic » (25/09, 11:21) ; projets « Zoé projet triple-clic » et « Zoé projet budget négatif » (-5000) ; DEV-2026-003 (converti) et FACT-2026-003 (brouillon, 600 €) pour Zoé Doubleclic, DEV-2026-004 (brouillon, 360 €) pour Zoé Clavier ; document « Zoé document triple-clic » (11 sections générées) ; conversation « Zoé : réponds juste OK. » (1 message en base, fausse bulle « network error » dans le magasin local). Rien supprimé. Totaux : 10 contacts, 5 projets, 4 tâches, 7 pièces, 2 documents, 5 conversations, 3 rendez-vous.

**État final mesuré à 11:50:16** (après le test de la croix), sur l'Accueil : document visible, horloge active, 1440×900, thème `dark`, contraste élevé désactivé (`therese-accessibility` identique à l'état d'arrivée), racine 16 px (taille « Moyenne »), aucun dialogue ouvert, un seul onglet. Console : les seules erreurs de ma session sont le 409 de la trame (2.3) et le 422 du prénom trop long (5.3), provoqués exprès ; aucune requête en échec en dehors d'eux.

**Bilan** : 19 constats numérotés avec preuve (zoe-01 à zoe-20, zoe-11 retiré car connu sous B-1244) : 19 bug_candidate (1 haute, 5 moyennes, 13 mineures), plus 4 propositions et 4 observations ; 2 points écartés faute de preuve ; 1 point connu non re-signalé (B-1244).

## Tokens consommés (si connus)

Environ 477 000 tokens, lus sur le compteur de session (15 000 000 au départ, environ 14 523 000 à la fin de la rédaction).
