# Sophie, formatrice indépendante : trace de la campagne

> Campagne « chaque écran, chaque persona », cycle 6, 10/09/2026. THÉRÈSE 0.69.0 (main 0f7418a1).
> Instrument : Playwright MCP, `http://localhost:1420` (le frontend Vite n'écoute que sur `[::1]:1420`,
> `http://127.0.0.1:1420` ne répond pas), backend jetable 17393, base vierge, viewport 1280x800,
> thème clair, taille de police « grande », modèle local `qwen3:8b` (Ollama).
> **Version réellement servie** : la mission annonce `main 0f7418a1`, mais le dépôt était sur `a92534e9`
> avec quatre fichiers modifiés non commités (`modeles_catalogue.py`, `providers/openai.py`,
> `token_tracker.py`, `lib/effortOpenAI.temoins.json`, chantier P-057 en cours). Vite sert l'arbre de
> travail : le frontend testé est donc `a92534e9` + ces modifications, pas `0f7418a1` pur.
> Garde d'environnement avant le premier geste : `{ visible: "visible", horloge: 1841.13 }` puis, après purge
> de `localStorage`/`sessionStorage`/IndexedDB et rechargement, document toujours `visible`, horloge non nulle.
> Les requêtes API partent vers 17393 (101 requêtes au relevé de la mise en route), plus deux `GET /api/tags`
> vers Ollama en `localhost:11434` ; toutes en 200.

## Mon impression

Je suis entrée sans rien connaître et je suis ressortie avec deux documents structurés, exportés en
Markdown et en Word : c'est la première fois qu'un outil me laisse écrire au lieu de me faire cliquer.
La mise en route est claire, et la mention qui me dit si le modèle tient dans ma mémoire vive m'a évité
de choisir le mauvais. L'atelier documentaire est ce qui m'a le plus rassurée : quand j'annule une trame,
rien n'apparaît derrière mon dos ; quand j'ajoute ma propre section pendant que la machine travaille, elle
est toujours là à l'arrivée ; quand je quitte le document et que je reviens, le travail est toujours en cours
et je peux encore l'arrêter. Trois choses m'ont gênée. D'abord la colonne de la trame : à la taille de police
que j'ai choisie, la moitié de mes titres est coupée et je n'ai aucun moyen de les lire en entier. Ensuite
l'attente : la rédaction d'une section peut durer plusieurs minutes, l'écran me le dit honnêtement, mais le
compteur « Travaux » affiche « 0 en cours » pendant ce temps et rien ne me permet d'arrêter cette
rédaction-là, alors que je peux arrêter la trame. Enfin, la bibliothèque de prompts m'a fait perdre pied sur
deux gestes précis (voir plus bas). Rien de tout cela ne m'a fait perdre de contenu : c'est un outil dans
lequel je laisserais mes supports.

## Parcours

### Mise en route : configurer THÉRÈSE sur une base vierge, en local

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | Ouvrir `localhost:1420`, purger le stockage, recharger | Assistant de mise en route, étape 1/6 | « Bienvenue sur THÉRÈSE », fil des 6 étapes, bouton « Commencer la configuration » | 01 | conforme |
| 2 | Renseigner le profil (nom, entreprise, rôle, e-mail fictif, ville) | Champs libres, mention du stockage local | « Ces informations sont stockées localement dans /tmp/therese-demo-c6/data et ne quittent jamais ta machine » | 02, 03 | conforme |
| 3 | Choisir le service d'IA | Liste des fournisseurs, Ollama local sans clé | 16 fournisseurs, « Ollama (Local) - 100% local - Aucune clé API requise » en bas de liste | 04, 05 | conforme |
| 4 | Choisir le modèle `gemma4-tia:latest` | Indication de faisabilité | Bandeau rouge « RAM déconseillée - Environ 8,3 Gio requis, pour un plafond de 8 Gio (la moitié des 16 Gio de RAM) » (RAM machine vérifiée : 16 Gio) | 05 | conforme |
| 5 | Basculer sur `qwen3:8b` | Le bandeau suit le choix | Bandeau vert « RAM compatible - Environ 6,9 Gio requis, sous le plafond de 8 Gio » ; « Configurer plus tard » reste offert | 06 | conforme |
| 6 | Étape Sécurité | Risques expliqués, pas de consentement cloud imposé | Quatre familles de risques + « Parcours local sans consentement cloud » | 07 | conforme |
| 7 | Étape Dossier de travail | Choix ou report possible | « Aucun dossier configuré », boutons « Sélectionner un dossier » et « Passer » (non testé : dialogue natif Tauri indisponible dans le navigateur) | 08 | angle mort |
| 8 | Terminer | Résumé fidèle | « Profil : Sophie », « Service d'IA : ollama / qwen3:8b », « Dossier de travail : Non configuré » | 09 | conforme |
| 9 | Arriver dans l'application | Accueil personnalisé | « Bonjour Sophie. », brief du jour vide expliqué, mise en route proposée | 10 | conforme |
| 10 | ⌘, puis Paramètres > Accessibilité > « Grande » | Toute l'interface grossit | Police visiblement plus grande sur tous les écrans suivants | 11, 12, 13, 14 | conforme |

Arbre d'accessibilité (étape 10) : focus sur le bouton « Grande », dialogue annoncé `role="dialog"`,
`aria-modal="true"`, nom accessible « Paramètres ».
Console : aucun avertissement ni erreur. Réseau : 102 requêtes API, toutes en 200, toutes vers 17393.

### Atelier documentaire : produire un programme de formation, de la trame à l'export

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | Chercher la capacité (« Plus d'outils » > « document ») | Trouver l'atelier | « Rédiger un document - Construire propositions, dossiers et rapports structurés » | 16, 17 | conforme |
| 2 | Ouvrir | Écran Documents, état vide expliqué | « 0 document », « Crée ton premier document… » + bouton | 18 | conforme |
| 3 | Créer le document 1 (titre + brief) | Document créé | La génération de trame démarre seule, « Annuler la génération » offert | 19, 20 | conforme |
| 4 | Ouvrir « Travaux » pendant la génération | Le traitement y est | « Trame : Programme de formation - Bur… / En cours », bouton « Arrêter » | 21 | conforme |
| 5 | Annuler la génération | Aucune section ne doit apparaître | « Génération de la trame annulée. », « Aucune section pour l'instant. » ; API : `sections = 0`, traitement `state=cancelled` | 22 | conforme |
| 6 | Revenir à la liste | Statut honnête | Badge « SANS TRAME », « Trame non générée » | 23 | conforme |
| 7 | Créer le document 2 et le laisser aboutir | Trame complète | 12 sections hiérarchisées, badges « VIDE » (≈ 3 min avec le modèle local) | 24, 27, 28 | conforme |
| 8 | Quitter le document pendant la génération et le rouvrir | L'état de travail est retrouvé | « Génération de la trame en cours… » + « Annuler la génération » toujours là | 25, 26 | conforme |
| 9 | Ouvrir une section, cliquer « Rédiger » | Attente annoncée puis texte en flux | « Rédaction lancée : le modèle prépare le texte, aucun mot reçu pour l'instant. » puis flux mot à mot, badge « BROUILLON » | 29, 30, 31 | conforme |
| 10 | Pendant la rédaction, lire le compteur « Travaux » | Le travail en cours est compté | Bouton annoncé « Travaux (0 en cours) », API `processing-tasks` sans entrée de rédaction, aucun bouton pour arrêter | 30 | bug_candidate (sophie-01) |
| 11 | Lire les pistes | Pistes proposées après rédaction | 3 pistes avec « Explorer » et « Ignorer » | 32 | conforme |
| 12 | Explorer une piste | Effet annoncé | La piste passe dans « Pistes traitées (1) » et son texte est déposé dans le champ d'instruction de retouche | 33 | conforme |
| 13 | Exporter en .md | Fichier fidèle | `Support de cours - Prise de parole_43f98d7f.md`, 1 426 o, titres et contenu conformes | 34 | conforme |
| 14 | Exporter en .docx | Fichier fidèle | `.docx` de 38 083 o, 18 entrées OOXML, texte vérifié | 35 | conforme |
| 15 | Créer le document 3 et ajouter une section à la main pendant la génération | La section survit à l'arrivée de la trame | Section « Mes règles de sécurité en salle » créée pendant la génération, toujours présente après l'arrivée des 16 autres (API et écran) | 36, 37, 38, 39 | conforme |
| 16 | Double-clic sur « Générer la trame » | Un seul traitement, bouton d'annulation conservé | Une seule tâche créée (10:46:13), le second appel refusé en 409, « Annuler la génération » toujours affiché, annulation effective | 40 | conforme |
| 17 | Relancer une trame après une annulation | La génération repart | Nouvelle tâche créée et annulable (pas de blocage `cancel_requested`) | 40 | conforme |

Arbre d'accessibilité (étape 9) : focus sur le bouton « Rédiger », zone de texte de la section annoncée,
badge d'état « BROUILLON » lu à côté du titre.
Console (parcours entier) : 2 erreurs, toutes deux `409 (Conflict)` sur
`POST /api/documents/b910ee43…/outline` — la première à la création du document 1, la seconde au second
clic du double-clic. Aucune n'a de conséquence visible (voir sophie-11).
Réseau : `POST /api/documents/{id}/outline` 200 pour les documents 2 et 3, 409 pour les deux appels
redondants du document 1 ; exports en 200.

### Bibliothèque de prompts : retrouver un modèle, le copier, l'insérer

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | « Plus d'outils » > « prompt » > « Modèles et variables » | Bibliothèque | « Bibliothèque de prompts - 34 prompts prêts à l'emploi », 6 catégories | 41, 42 | conforme |
| 2 | Replier la catégorie « Email » | La catégorie se ferme | Les 6 catégories apparaissent repliées, avec leur compte | 43 | conforme |
| 3 | Chercher « relance » | Voir les résultats | En-tête « 3 résultats pour "relance" » mais **aucun résultat affiché** : trois catégories repliées (1, 1, 1) | 44 | bug_candidate (sophie-02) |
| 4 | Déplier « Email » | Le résultat apparaît | « Relance client en attente » s'affiche enfin | 45 | conforme |
| 5 | Copier un prompt (copie réelle) | Coche « copié » | Icône remplacée par une coche pendant exactement 2 s (relevé par observateur de mutations : 1 coche à t=1 920 059 ms, 0 à t=1 922 062 ms) | 46, 48, 49 | conforme |
| 6 | Copier avec `navigator.clipboard.writeText` mis en échec (injection au runtime) | Pas de coche, ou un message d'échec | La coche s'affiche quand même 2 s (journal : 1 à t=1 936 651, 0 à t=1 938 655), aucun message ; console : « Write permission denied. » | 50 | bug_candidate (sophie-03) |
| 7 | « Utiliser » sur « Relance client en attente » | Le prompt arrive dans le composeur | Texte inséré, barre de variables : « 0 variable résolue - inconnues : {nom_client}, {nombre_jours}, {sujet}, {prenom}, {nom_entreprise} · à remplacer dans le message avant l'envoi » | 51 | conforme |
| 8 | « Renseigner les variables » | Formulaire des cinq variables | Cinq champs, explication « Ces valeurs deviennent des variables réutilisables ; le message garde ses jetons et le moteur les remplace à l'envoi », « Enregistrer comme variables » désactivé tant que rien n'est saisi | 52 | conforme |
| 9 | Remplir puis « Enregistrer comme variables » | Variables enregistrées | « 5 variables résolues », le message garde ses jetons | 53, 54 | conforme |
| 10 | Écrire un message avec `{mauvais-nom}` et `{2eme sujet}` | Savoir ce qui est reconnu | « 1 variable résolue » ; les deux jetons mal formés ne sont ni reconnus ni signalés | 55 | proposal (sophie-06) |
| 11 | Paramètres > Services > Variables : créer `nom_client` (nom déjà pris) | Refus lisible, saisies conservées | Refus, saisies conservées, mais le message est l'enveloppe brute : `{"code":"HTTP_ERROR","message":"La variable « nom_client » existe déjà…"}` (HTTP 409) | 58, 59 | bug_candidate (sophie-05) |
| 12 | Créer `mauvais-nom` (nom invalide) | Idem | Même enveloppe brute : `{"code":"HTTP_ERROR","message":"Nom de variable invalide : « mauvais-nom »…"}` (HTTP 422), saisies conservées | 60 | bug_candidate (sophie-05) |
| 13 | ⌘, depuis le composeur | Ouvrir les Paramètres | Rien ne s'ouvre tant que le curseur est dans le champ de message ; le même raccourci fonctionne dès que le focus est ailleurs | 56 | bug_candidate (sophie-07) |

Arbre d'accessibilité (étape 11) : focus sur le champ « Nom », le refus s'affiche dans une notification
« Création refusée » en bas à droite ; aucune région `aria-live` n'est associée aux boutons de copie
(étape 5), la coche est purement visuelle.
Console (parcours entier) : `409 (Conflict)` puis `422 (Unprocessable Content)` sur `/api/variables`
(refus attendus), « Write permission denied. » (injection volontaire), et un rechargement complet de la
page à la première ouverture de la bibliothèque — dû à la re-optimisation des dépendances du serveur
Vite en mode développement (`node_modules/.vite/deps/…?v=…`), donc un artefact d'instrument, pas un
défaut du produit ; le réglage « police grande » a survécu au rechargement.

### Livrables et suivi client : promettre, livrer, revenir en arrière

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | Ouvrir « Projets » (rail) | Liste des projets | « 0 projet », carte vide « Aucun projet » sans explication ni action (le bouton est en haut de l'écran) | 61 | proposal (sophie-10) |
| 2 | Créer un projet | Projet créé | « Formation Bureautique - Boulangerie Démo » en colonne « Actif » | 62, 63 | conforme |
| 3 | Cliquer la carte du projet | Ouvrir le projet | Ouvre « Modifier le projet » (formulaire d'édition), pas le contenu du projet | 64 | observation |
| 4 | « Plus d'outils » > « livrable » > « Livrables et suivi client » | Écran de suivi | Panneau « Livrables et suivi client », projet présélectionné, « Aucun livrable n'est rattaché à ce projet : ajoute le premier. » | 65, 66 | conforme |
| 5 | « Ajouter un livrable » puis laisser le titre vide | Refus | Le bouton « Ajouter » reste désactivé (aucun message, mais aucune création) | 67, 68 | conforme |
| 6 | Titre + échéance 25/09/2026, « Ajouter » | Livrable créé | « Support PDF remis aux stagiaires · Échéance · 25 sept. 2026 », compteur Livrables 1, confirmation « Livrable « … » ajouté. » | 69, 70 | conforme |
| 7 | Passer le statut à « Validé » en ligne | Statut et compteurs suivent | « Validé · 10 sept. 2026 », compteur Validés 1, barre de progression pleine | 71 | conforme |
| 8 | Revenir à « À faire » | L'état de validation disparaît | Compteur Validés 0, la date de validation disparaît | 72 | conforme |
| 9 | Créer un second projet, revenir au panneau | Le sélecteur connaît les deux | Les deux projets sont listés, le second est sélectionné par défaut | 73 | conforme |
| 10 | Revenir au premier projet | Le livrable est retrouvé tel quel | Livrable, échéance et statut « À faire » intacts | 74 | conforme |

Arbre d'accessibilité (étape 6) : focus sur le champ « Titre », le statut est un `select` étiqueté,
la confirmation est un texte simple sous le bouton (pas de région annoncée).

### Tiroir des conversations : un brouillon ne doit pas disparaître

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | ⌘N (focus hors champ) | Nouvelle conversation | Écran « Comment puis-je t'aider ? », composeur vide, modèle « qwen3:8b · local » | 75 | conforme |
| 2 | Taper un brouillon sans l'envoyer, attendre 7 s | Brouillon conservé | Mention « Sauvegardé il y a 15s » sous le composeur | 76 | conforme |
| 3 | Ouvrir le tiroir « Conversations » | La conversation au brouillon est listée | « Nouvelle conversation - 10 sept., 13:55 - Brouillon en attente · non enregistrée » | 77 | conforme |
| 4 | Cliquer « Nouvelle conversation » puis rouvrir le tiroir | Le brouillon reste listé | Toujours listé, une seule entrée, le texte est resté dans le composeur (rien n'est perdu) | 78 | conforme |
| 5 | Comparer avec l'API | Le tiroir ne ment pas | `GET /api/chat/conversations` rend `[]` et le tiroir dit explicitement « non enregistrée » | — | conforme |

### Studio Images : essayer sans clé

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | « Plus d'outils » > « image » > « Images » | Studio Images | « Studio Images - Génération réelle, aperçu local et historique conservé », trois moteurs marqués « non configuré », « Historique réel : 0 image chargée sur 50 maximum » | 79, 80, 81 | conforme |
| 2 | Décrire un visuel puis « Préparer la génération » | Refus lisible, rien n'est envoyé | « Le moteur GPT Image 2 n'est pas configuré. » ; encart « La demande sera transmise au moteur choisi. Rien ne part avant confirmation. » ; aucune requête sortante | 82 | conforme |
| 3 | Chercher comment configurer depuis ce refus | Un chemin vers le réglage | Aucun lien ni bouton : il faut savoir aller dans Paramètres > Services | 82 | proposal (sophie-08) |

### Voix et transcription : ce qui est local, ce qui ne l'est pas

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | Ouvrir « Voix et transcription » | Distinction claire local / cloud | Colonne gauche : « Groq Whisper cloud · le fichier sera envoyé à Groq après ta confirmation » ; colonne droite : « Synthèse locale Piper. Aucun texte n'est envoyé vers un service externe. » | 84 | conforme |
| 2 | Lire la consigne d'activation | Savoir où activer | « La voix locale doit être activée dans Paramètres → Confidentialité avant d'utiliser la synthèse. » | 84 | conforme |
| 3 | Aller dans Paramètres > Confidentialité | Trouver l'activation | Section « Voix locale souveraine » : « La voix locale n'est pas embarquée dans cette version de THÉRÈSE. Mets l'application à jour pour en profiter. » Aucun réglage à activer | 85, 86 | bug_candidate (sophie-04) |

### Calculateurs : un seuil de rentabilité vérifiable

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | Ouvrir « Calculateurs » | Outils de calcul | « Calculateurs vérifiables - Les valeurs sont envoyées au moteur de calcul local, jamais estimées par le modèle », onglets ROI / ICE / RICE / VAN / Seuil | 87, 88 | conforme |
| 2 | Onglet « Seuil » | Formule affichée | « Seuil de rentabilité : coûts fixes ÷ (prix − coût variable) », trois champs | 89 | conforme |
| 3 | 12 000 € de coûts fixes, 150 € de coût variable, 490 € de prix, « Calculer avec le moteur local » | Résultat juste et lisible | « 36 unités minimum - Seuil théorique : 35,29 · Chiffre d'affaires au minimum entier : 17 640,00 € » (vérifié à la main : 12 000 ÷ 340 = 35,294 ; 36 × 490 = 17 640) | 90 | conforme |

Console et réseau de la fin de campagne : 930 requêtes en 200, plus quatre refus attendus
(deux `409` sur `/outline`, un `409` et un `422` sur `/api/variables`). Aucune requête en échec réseau.

## Constats numérotés

### sophie-01 - `bug_candidate` - P3 - la rédaction d'une section n'est ni comptée ni arrêtable
- **Préconditions** : document avec une trame, section ouverte, modèle local.
- **Étapes** : ouvrir une section > « Rédiger » > pendant que le texte arrive, lire le bouton « Travaux » de l'en-tête.
- **Attendu** : le compteur « Travaux » reflète le travail en cours, comme il le fait pour la trame, et la rédaction peut être arrêtée comme la trame peut l'être.
- **Observé** : le bouton est annoncé « Travaux (0 en cours) » alors que l'écran affiche « Rédaction lancée : le modèle prépare le texte… cela peut prendre plusieurs minutes » ; `GET /api/processing-tasks` ne contient que les deux trames (`document_outline`), aucune entrée de rédaction ; aucun bouton pour arrêter.
- **Preuve** : capture `30-doc2-redaction-en-cours.png` ; `aria-label` relevé : `Travaux (0 en cours)` ; sortie API : `document_outline | Trame : Support de cours… | done` et `… | cancelled`, rien d'autre.
- **Fichier suspecté** : `src/frontend/src/components/traitements/TraitementsIndicator.tsx:33` pour le libellé ; l'enregistrement du traitement se fait côté backend (routes de rédaction de section), non couvert par le registre.

### sophie-02 - `bug_candidate` - P2 - la bibliothèque annonce des résultats qu'elle n'affiche pas
- **Préconditions** : bibliothèque de prompts ouverte, catégorie « Email » repliée par un clic.
- **Étapes** : replier « Email » > taper « relance » dans la recherche.
- **Attendu** : les résultats s'affichent (une recherche montre ce qu'elle a trouvé).
- **Observé** : l'en-tête indique « 3 résultats pour "relance" » et l'écran ne montre que trois bandeaux de catégorie repliés ; il faut déplier chaque catégorie à la main pour voir le moindre prompt.
- **Preuve** : captures `43-bibliotheque-categorie-repliee.png`, `44-bibliotheque-recherche-relance.png` (« 3 résultats », zéro prompt visible), `45-bibliotheque-resultat-deplie.png` (le résultat existe bien).
- **Fichier suspecté** : `src/frontend/src/components/prompts/PromptLibrary.tsx` - l'intention est écrite ligne 454 (`defaultOpen={searchResults !== null || index === 0}`) mais l'accordéon fige la valeur au montage (ligne 208, `useState(defaultOpen)`) : le repli décidé par l'utilisateur l'emporte sur la recherche.

### sophie-03 - `bug_candidate` - P2 - la coche « copié » s'affiche même quand la copie a échoué
- **Préconditions** : bibliothèque ouverte.
- **Étapes** : neutraliser `navigator.clipboard.writeText` pour qu'il rejette (`NotAllowedError`, injection au runtime depuis la console) > cliquer l'icône « Copier le prompt ».
- **Attendu** : pas de coche, ou un message disant que la copie n'a pas eu lieu.
- **Observé** : la coche s'affiche 2 s exactement, aucun message ; la console porte « Write permission denied. ».
- **Preuve** : journal d'un observateur de mutations posé sur la modale - copie réelle `[[1920059,1],[1922062,0]]`, copie mise en échec `[[1936651,1],[1938655,0]]` (comportement identique) ; capture `50-bibliotheque-copie-sabotee-aucune-erreur.png` ; ligne de console citée ci-dessus.
- **Fichier suspecté** : `src/frontend/src/components/prompts/PromptLibrary.tsx:105-114` - `navigator.clipboard.writeText(prompt.prompt);` n'est ni attendu ni rattrapé, `setCopied(true)` suit inconditionnellement.

### sophie-04 - `bug_candidate` - P3 - la voix locale renvoie vers un réglage qui n'existe pas
- **Préconditions** : aucune.
- **Étapes** : « Plus d'outils » > « Voix et transcription » > lire la consigne > Paramètres > Confidentialité > chercher la voix locale.
- **Attendu** : trouver l'activation annoncée, ou lire au même endroit que la fonction n'est pas disponible.
- **Observé** : l'écran Voix dit « La voix locale doit être activée dans Paramètres → Confidentialité avant d'utiliser la synthèse » ; la section « Voix locale souveraine » des Paramètres dit « La voix locale n'est pas embarquée dans cette version de THÉRÈSE. Mets l'application à jour pour en profiter. » et n'offre aucun réglage.
- **Preuve** : captures `84-voix-transcription.png` et `86-voix-locale-non-embarquee.png`.
- **Réserve** : la pile testée est le frontend Vite branché sur un backend lancé depuis les sources ; il se peut que la synthèse Piper soit embarquée dans l'application empaquetée. La contradiction entre les deux écrans, elle, ne dépend pas de l'empaquetage : l'écran Voix devrait dire ce que dit celui des Paramètres.

### sophie-05 - `bug_candidate` - P2 - un refus de variable montre l'enveloppe JSON du serveur
- **Préconditions** : au moins une variable enregistrée (`nom_client`).
- **Étapes** : Paramètres > Services > Variables > créer `nom_client` (déjà pris), puis `mauvais-nom` (nom invalide).
- **Attendu** : la phrase d'explication, sans structure technique.
- **Observé** : la notification « Création refusée » affiche `{"code":"HTTP_ERROR","message":"La variable « nom_client » existe déjà. Utilise « remplacer » pour changer sa valeur (l'écrasement silencieux est refusé)."}` puis `{"code":"HTTP_ERROR","message":"Nom de variable invalide : « mauvais-nom ». Attendu : minuscules, chiffres et _ (32 caractères maximum)."}`. Les saisies restent affichées (attendu tenu sur ce point).
- **Preuve** : captures `59-variables-doublon-refus.png` et `60-variables-nom-invalide-refus.png` ; console : `409 (Conflict)` puis `422 (Unprocessable Content)` sur `http://127.0.0.1:17393/api/variables`.
- **Fichier suspecté** : `src/frontend/src/components/settings/VariablesSection.tsx:78` - `notify('error', 'Création refusée', err instanceof Error ? err.message : undefined)` : le message d'erreur transporte le corps brut de la réponse.

### sophie-06 - `proposal` - un jeton mal formé n'est ni reconnu ni signalé
- **Attendu** : savoir, avant d'envoyer, que `{mauvais-nom}` et `{2eme sujet}` ne seront pas remplacés.
- **Étapes** : écrire dans le composeur `Note interne pour {nom_client} et {mauvais-nom} et {2eme sujet}.`
- **Observé** : la barre annonce « 1 variable résolue » ; les deux autres jetons ne sont ni listés en « inconnues » ni signalés comme mal nommés, alors qu'ils ressemblent à des variables et partiront tels quels dans le message.
- **Preuve** : capture `55-variables-noms-invalides.png`. Console/réseau : rien de notable (aucune requête déclenchée).
- **Pour le portail humain** : signaler les jetons qui ressemblent à une variable sans en respecter la forme (« minuscules, chiffres et _ »).

### sophie-07 - `bug_candidate` - P3 - ⌘, ne fonctionne pas quand j'écris
- **Étapes** : cliquer dans le champ de message, presser ⌘, ; puis rendre le focus au document et presser ⌘, à nouveau.
- **Attendu** : la fin de la mise en route promet « Tu peux à tout moment modifier ces paramètres dans les Paramètres (raccourci Cmd+,) ».
- **Observé** : aucune ouverture tant que le curseur est dans le composeur (`document.activeElement` = `TEXTAREA`, aucun `[role="dialog"]` après la frappe) ; le même raccourci ouvre bien « Paramètres » dès que le focus est ailleurs.
- **Preuve** : captures `09-mise-en-route-termine.png` (la promesse) et `56-parametres-etat.png` (rien ne s'ouvre) ; relevés `{"apresRaccourciDansTextarea": false}` puis `{"apresRaccourciHorsChamp": true, "titre": "Paramètres"}`. Console/réseau : rien de notable.
- **Fichier suspecté** : `src/frontend/src/hooks/useKeyboardShortcuts.ts` - la garde générique `if (isInput) return;` (ligne 94) est posée AVANT le traitement de ⌘, (ligne 177) ; ⌘N, lui, est explicitement exempté juste au-dessus (ligne 87, commentaire « fonctionne meme si le focus est dans le textarea »). Le comportement ne vient donc pas du navigateur : aucun accélérateur natif ⌘, n'existe côté Tauri (`Comma`, `accelerator`, `Menu::` absents de `src-tauri/src/` et de `tauri.conf.json`), l'application empaquetée se comportera de même.

### sophie-08 - `proposal` - le refus du Studio Images ne dit pas où configurer
- **Attendu** : un refus qui dit quoi faire (la grille du protocole : « erreur lisible qui dit quoi faire »).
- **Observé** : « Le moteur GPT Image 2 n'est pas configuré. » sans lien vers Paramètres > Services ni bouton d'action.
- **Preuve** : capture `82-images-sans-cle.png`. Console/réseau : rien de notable, et surtout aucune requête sortante (le refus est posé avant tout envoi).

### sophie-09 - `proposal` - les titres de la trame sont coupés sans moyen de les lire
- **Attendu** : pouvoir lire le titre entier d'une section, au moins au survol, surtout avec la police « grande ».
- **Observé** : dans la colonne « Trame », la moitié des titres est tronquée (« Fixer l'objectif et les … », « Comportement et dis… », « Comprendre le… » une fois le badge « BROUILLON » posé) ; aucune infobulle ne rend le titre complet. Le réglage d'accessibilité « police grande » aggrave le phénomène, la colonne ne s'élargissant pas.
- **Preuve** : captures `28-doc2-trame-arrivee.png`, `31-doc2-redaction-flux.png`, `39-doc3-bas-de-trame-section-manuelle.png`. Console/réseau : rien de notable.
- **Fichier suspecté** : `src/frontend/src/components/documents/OutlineTree.tsx:312` - `<span className="… truncate …">{section.title}</span>`, sans attribut `title`.

### sophie-10 - `proposal` - l'état vide de « Projets » n'explique rien
- **Attendu** : un vide expliqué avec une action, comme le fait « Documents ».
- **Observé** : « Aucun projet », sans phrase d'explication ni action dans la carte, là où « Documents » propose « Crée ton premier document pour démarrer une proposition, un dossier ou un rapport structuré » avec son bouton.
- **Preuve** : captures `61-projets-vide.png` et `18-atelier-liste-vide.png`. Console/réseau : rien de notable.

### sophie-11 - `observation` - une erreur 409 en console à la création du premier document
- **Observé** : à la création du document 1, `POST /api/documents/{id}/outline` répond `409 Conflict` (une génération avait déjà été lancée par la création) ; l'écran reste juste (« Génération de la trame en cours… »), mais la console porte une erreur. Le même 409 protège correctement le second clic du double-clic.
- **Preuve** : journal réseau `1030. [POST] …/outline => [409] Conflict`, console `Failed to load resource: … 409 (Conflict)`.

### sophie-12 - `observation` - la liste des documents ne montre pas qu'une trame est en cours
- **Attendu** : que la liste distingue « pas encore de trame » d'« une trame est en train d'arriver ».
- **Observé** : pendant la génération, la carte du document porte « SANS TRAME » et « Trame non générée » ; seul le compteur « Travaux » de l'en-tête signale le travail.
- **Preuve** : capture `25-liste-pendant-generation-doc2.png` (badge « SANS TRAME » et pastille « 1 » sur Travaux au même instant). Console/réseau : `GET /api/documents` en 200, `sections_total: 0` à cet instant.

## Constats écartés faute de preuve

- **Paramètres qui se referment seuls** : après la mise en route, la fenêtre Paramètres ouverte par ⌘, avait disparu au relevé suivant (capture `11-parametres-ouverts.png` puis arbre d'accessibilité sans dialogue). Non reproductible : trois tentatives ensuite (⌘, et bouton du rail) laissent la fenêtre ouverte au-delà de 15 s. Écarté.
- **Capacité « Images » qui ouvrirait « Projets »** : un premier clic sur la description de la carte a laissé l'écran « Projets » (capture `80-studio-images.png`). Deux reproductions ensuite, dont une sur le texte descriptif lui-même, ouvrent bien le Studio Images ; la description est bien à l'intérieur du bouton (vérifié par `elementFromPoint`). Écarté : le premier clic a vraisemblablement atteint le fond de la boîte de dialogue.
- **Rechargement complet de la page à la première ouverture de la bibliothèque** : artefact du serveur de développement Vite (nouvelle optimisation de dépendances, `?v=` modifié), pas un défaut du produit. Écarté.

## Transitions couvertes et angles morts

**Couvert** : mise en route complète sur base vierge (six étapes, modèle local, RAM compatible/déconseillée, « Configurer plus tard » photographié sans être choisi) ; réglage d'accessibilité « police grande » appliqué et tenu sur tous les écrans suivants, y compris après un rechargement ; atelier documentaire de bout en bout (création, génération automatique de trame, présence dans « Travaux », annulation avec vérification par l'API qu'aucune section n'apparaît, aboutissement d'une seconde trame, ajout d'une section à la main pendant la génération et survie à l'arrivée de la trame, double-clic sur « Générer la trame », sortie et retour dans le document pendant la génération, relance après annulation, rédaction d'une section en flux, pistes et exploration d'une piste, exports .md et .docx vérifiés fichier en main) ; bibliothèque de prompts (repli, recherche, copie réussie et copie mise en échec, insertion) ; variables (formulaire, enregistrement, refus sur nom déjà pris et sur nom invalide, conservation des saisies) ; livrables (création, titre vide refusé, changement de statut en ligne, retour arrière, bascule entre deux projets) ; tiroir des conversations avec brouillon en attente confronté à l'API ; Studio Images sans clé ; Voix et transcription (local contre cloud) ; calculateur de seuil de rentabilité vérifié à la main.

**Angles morts** :
- Dialogues natifs de Tauri : « Sélectionner un dossier » à la mise en route et l'enregistrement des exports passent par le navigateur (téléchargement direct), pas par la boîte de dialogue de l'application empaquetée. Le comportement de l'export en application installée n'est pas couvert, et aucune confirmation à l'écran n'a pu être observée après un export.
- « Retoucher » une section à partir d'une piste : la piste explorée dépose bien son texte dans le champ d'instruction, mais la retouche elle-même n'a pas été lancée (temps de modèle local).
- Réordonner la trame par glisser-déposer, supprimer une section, « Valider » une section : non tentés.
- Voix locale et dictée : rien n'a été téléchargé ni enregistré (aucun micro, et la voix locale est déclarée non embarquée).
- Le mode « Contributeur » (fonctions avancées : Outils, Agents, Avancé) n'a pas été activé.
- **Aucun message n'a été envoyé au modèle depuis le chat** : la seule conversation existante était une coquille jamais enregistrée (`GET /api/chat/conversations` rend `[]`). Le geste « changer de conversation » du parcours du tiroir est donc dégénéré : il ramène sur la même coquille. Un vrai passage d'une conversation enregistrée à une autre, brouillon en attente, reste à couvrir.
- **Arbre d'accessibilité** : résumé une fois par parcours (mise en route, atelier, bibliothèque, livrables) et non à chaque étape comme le protocole le demande ; pas de relevé pour le tiroir, le Studio Images, la Voix et les Calculateurs. Les captures, elles, couvrent chaque étape.
- Thème sombre et petits écrans : hors périmètre de cette fiche (1280x800, thème clair).

## Tokens consommés

Environ 772 000 tokens de la fenêtre de contexte (15 000 000 au départ, 14 228 000 restants après les relectures de fin), dont une part importante perdue sur un appel `navigator.clipboard.readText()` resté bloqué 30 minutes avant abandon par l'outil : à ne jamais rejouer, la lecture du presse-papiers n'est pas résoluble dans ce navigateur piloté.
