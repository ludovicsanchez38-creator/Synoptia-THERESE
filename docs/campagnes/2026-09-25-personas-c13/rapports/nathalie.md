# Nathalie, gérante d'une TPE de quatre salariés : trace de la campagne

> Campagne c13, 25/09/2026 (vendredi). Instrument : Playwright MCP, viewport 1280×800, DPR 1, fr-FR, thème clair ; texte agrandi à 125 % pour la seconde moitié (parcours 4 à 6).
> Frontend http://127.0.0.1:1420, moteur jetable http://127.0.0.1:17393 (v0.75.0, `main` à eed43fe6 : correctifs B-1341 à B-1363 issus de la trace de Claire), données laissées par Claire et Hugo (quatre contacts dont Paul Exemple en périmètre projet, un devis converti et sa facture, trois projets).
> Garde d'environnement à 10:52 : `{ visible: "visible", horloge: 37594.288 }`, 1280×800, DPR 1, thème clair (`data-theme="light"`), aucun dialogue ouvert. Stockage NON purgé (consigne de l'orchestrateur : l'application est déjà configurée).
> Note d'instrument (fichiers) : le serveur Playwright n'a pas d'outil de dépôt de fichier. Pour chaque import, je clique réellement sur le bouton d'import (le sélecteur natif n'apparaît pas dans le navigateur piloté), puis j'injecte le fichier fourni dans le `input[type=file]` de la page par `DataTransfer` et un événement `change` : la suite (requête au moteur, notification, liste) est le comportement réel de l'application.
> Note d'instrument (125 %) : le zoom texte du navigateur n'est pas pilotable par le MCP ; il est simulé par `document.documentElement.style.fontSize = '20px'` (réglage « Grande » de Chrome, 125 % de 16 px), vérifié par une mesure avant et après.
> Console attendue hors Tauri, non retenue : « [API] IPC échoué, retry n/10 », « Fallback port 17393 (mode dev) ».

## Mon impression (première personne, cinq à dix lignes)

Mes prospects vivent dans Excel, et THÉRÈSE ne sait pas lire Excel : « importer » ne trouve rien, le bouton dit « .vcf », et quand j'essaie quand même on me répond « format .vcf » sans me dire comment faire. Avec le vCard, ça passe, mais une carte sans nom disparaît sans un mot, et le même bouton sur deux écrans me répond deux choses différentes, dont une sans accents.
Déplacer un prospect au clavier marche, le compteur suit, mais le score me perd : Élodie passe de 50 à 105 pour une colonne, Karim, plus avancé, a moins qu'elle, et l'explication dit seulement « plus il est haut, plus il est chaud ». L'historique me parle de « Stage: contact → discovery ».
Ma relance de jeudi, je n'ai pas réussi à la poser sur Élodie : les « relances » veulent une boîte mail, les « actions » veulent une IA. J'ai fini par écrire une tâche, que rien ne relie à Élodie et que l'Accueil ne me montrera que jeudi.
Le devis, la conversion et le paiement se font vite et avec des confirmations claires ; mais ma facture payée se dit « Envoyée » alors que je ne l'ai jamais envoyée, et à 125 % je ne lis plus que « Vitri » de ma ligne.
L'Accueil est honnête sur aujourd'hui, chaque chiffre dit d'où il vient ; il ne me dit rien de ma semaine, de mon argent ni de mon pipeline.
Mon export ressort un vCard sans mes étapes ni mes étiquettes : je ne peux pas le comparer à mon Excel.

## Parcours (un bloc par parcours)

### 1. Importer mes prospects : trouver l'import, savoir ce qui est accepté et ce qui est écarté

Préconditions : quatre contacts laissés par Claire et Hugo (Hélène, Sophie Durand `@exemple.test`, Julien, Paul en périmètre projet), Accueil affiché. Mes fichiers : `prospects.vcf` (trois cartes : Élodie Martin, Karim Benali, Sophie Durand `@exemple.fr`) et `prospects-excel.csv` (points-virgules, trois lignes : Louis Petit, Amandine Roux, Marc Leroy sans entreprise et d'étape « inconnue »).
Gestes pour atteindre un import : « Plus d'outils », recherche, carte, bouton (4 gestes) ; « importer » ne trouve rien.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1.1 | Arrivée | L'Accueil | « Bonjour Claire. », un point d'attention (séance d'Hélène), établi. Titre h1 annoncé, pas de dialogue ouvert | 01-import-arrivee-accueil.png | ok |
| 1.2 | « Plus d'outils », je tape « importer » | Une capacité d'import | « Aucune capacité trouvée. Essaie avec le résultat souhaité, par exemple « devis » ou « analyser ». » | 02-import-recherche-importer.png | proposal (nathalie-01) |
| 1.3 | Je tape « prospects » | Mes prospects | Une carte « Pipeline, Vue, Suivre prospects… » | 03-import-recherche-prospects.png | ok |
| 1.4 | Je tape « excel » | Importer mon Excel | Une seule carte : « Word, PowerPoint et Excel, Demande relue, produire un fichier Office » (produire, pas importer) | 04-import-recherche-excel.png | proposal (nathalie-01) |
| 1.5 | Carte « Pipeline » | La vue avec un import | « Pipeline, 4 contacts · 3 projets », boutons « Importer (.vcf) » et « Nouveau contact ». Sept colonnes, dont deux hors écran à 1 280 px (Actif, Archive) | 05-import-vue-pipeline.png | ok |
| 1.6 | « Importer (.vcf) » avec mon fichier Excel (CSV) | Soit il le lit, soit il me dit comment faire | Notification rouge « Erreur import, Le fichier doit être au format .vcf » ; `POST /api/crm/import/vcf` → 400. Rien sur Excel, rien sur la conversion. Le moteur sait pourtant lire un CSV, un Excel ou un JSON avec aperçu et erreurs par ligne (`POST /api/crm/import/contacts/preview` et `/import/contacts`, `src/backend/app/routers/crm.py` l. 741-811) : aucune surface ne l'appelle (`grep "import/contacts" src/frontend/src` : 0 résultat) | 06-import-csv-refuse.png | proposal (nathalie-02) |
| 1.7 | « Importer (.vcf) » avec `prospects.vcf` | Trois prospects importés, un bilan | « Import VCF, 3 contact(s) créé(s) » ; « 7 contacts · 3 projets » ; les trois dans la colonne « Contact », score 50. Réponse `{"created":3,"updated":0,"total":3}`. Sophie Durand existe désormais deux fois (autre e-mail) : règle des homonymes B-1205, non re-signalée | 07-import-vcf-resultat.png | ok |
| 1.8 | Je réimporte le même fichier | « Déjà présents » | « 0 contact(s) créé(s), 3 mis à jour » : rien n'a changé dans les fiches, mais on me dit « mis à jour » | 08-import-vcf-reimport.png | observation (nathalie-04) |
| 1.9 | Variante de démonstration : deux cartes, une sans nom (« Fournisseur Exemple », e-mail seul), plus Karim | « 1 carte écartée : pas de nom » | « 0 contact(s) créé(s), 1 mis à jour ». La réponse dit `"total":1` pour un fichier de deux cartes : la carte sans nom a disparu sans un mot, même du total | 09-import-vcf-carte-sans-nom-muette.png ; réponse réseau n° 1917 | bug_candidate (nathalie-03) |
| 1.10 | « Plus d'outils » > « Contacts » (parcours) | Mes contacts | Panneau « Contacts et contexte », « 7 contacts dans la mémoire locale », bouton « Ouvrir Contacts » en bas de carte à moitié posé sur la bordure, sous « Voir la suite » | 10-import-parcours-contacts.png | observation |
| 1.11 | « Ouvrir Contacts » | L'écran Contacts | « Contacts » : « Importer (.vcf) », « Exporter », « Nouveau contact ». Icônes collées au texte (écart mesuré 0 px ; le même bouton du Pipeline a un espace) | 11-import-ecran-contacts.png | observation |
| 1.12 | « Importer (.vcf) » de cet écran, avec mon CSV | Le même message qu'au Pipeline | « Import VCF, L'import a échoué. Vérifie le fichier et réessaie. » La raison est perdue ; la console montre que le moteur l'avait donnée (« Le fichier doit etre au format .vcf », sans accent) sur une autre route, `POST /api/memory/contacts/import` | 12-import-csv-contacts-message-generique.png ; console l. 186-189 | bug_candidate (nathalie-05) |
| 1.13 | Même écran, `prospects.vcf` | Même bilan qu'au Pipeline | « 0 contact(s) cree(s), 3 mis a jour » : sans accents. Les deux boutons de même nom appellent deux routes aux règles de doublon différentes (e-mail seul au Pipeline, e-mail puis prénom et nom ici) | 13-import-vcf-contacts-message-sans-accents.png ; `src/backend/app/routers/memory.py` l. 762-850 | bug_candidate (nathalie-05) |

Arbre d'accessibilité : focus resté sur « Importer (.vcf) » après chaque import ; les notifications sont dans `region "Notifications"` (titre + message), le bouton de fermeture est nommé « Fermer la notification : Import VCF ».
Console : deux 400 attendus (mes deux essais CSV), plus `VCF import failed: Error: Le fichier doit etre au format .vcf` (écran Contacts). Réseau : 4 × `POST /api/crm/import/vcf` (1 × 400, 3 × 200), 2 × `POST /api/memory/contacts/import` (400, 200) ; tout en 127.0.0.1.

### 2. Pipeline : déplacer deux prospects d'étape, retrouver le score et son explication

Préconditions : sept contacts, tous en « Contact » ; Élodie et Karim viennent de l'import (score 50).
Note d'instrument : le MCP n'a pas de glisser-déposer à la souris ; j'ai déplacé les cartes au clavier (focus posé sur la carte, Espace, flèche droite, Espace), chemin prévu par l'application (capteur clavier de dnd-kit, consigne lue par le lecteur d'écran : « Pour saisir un élément, appuie sur la barre d'espace… »). Le glisser à la souris n'est pas éprouvé.
Gestes : 4 par déplacement au clavier ; aucun autre moyen de changer d'étape (la fiche n'a pas de champ « Étape »).

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 2.1 | Écran Contacts, « Retour » | Revenir d'où je viens | Retour au Pipeline (vue d'avant). Le bouton s'annonce pourtant « Revenir à la conversation unifiée » | 14-pipeline-retour-depuis-contacts.png | observation |
| 2.2 | « Ouvrir la fiche » d'Élodie | Sa fiche : coordonnées, étape, score | L'onglet bascule sur « Activités » : nom, entreprise, « Prestations », « Historique ». Ni étape, ni score, ni e-mail, ni téléphone. Le champ « Intitulé » a pour exemple « FORGER, PROPULSER, diagnostic… » (offres de l'éditeur, `ListeDesPrestations.tsx` l. 128) ; « Où ça en est » propose un autre jeu d'étapes (Piste, Proposition envoyée, Signée, Perdue, En cours, Terminée) que les colonnes du pipeline | 15-pipeline-fiche-elodie.png | bug_candidate (nathalie-08), proposal (nathalie-09) |
| 2.3 | Onglet « Pipeline », focus sur la carte d'Élodie, Espace, flèche droite | La carte suit | Annonce « la carte de Élodie Martin est au-dessus de la colonne Découverte. » (sans élision) | 16-pipeline-elodie-saisie-clavier.png | observation |
| 2.4 | Espace | Élodie en Découverte | Déposée ; annonce « … a été déposé sur la colonne Découverte. » (accord manquant). `PATCH /api/crm/contacts/df1c07e7…/stage` 200, `"stage":"discovery","score":105`. Colonnes : Contact 6, Découverte 1. **Le focus tombe sur `BODY`** : pour déplacer une seconde carte il faut repartir du haut de la page | 17-pipeline-elodie-deposee-decouverte.png | bug_candidate (nathalie-07) |
| 2.5 | Karim, Espace, deux flèches, Espace | Karim en Proposition | Déposé ; Contact 5, Découverte 1, Proposition 1 ; conforme à `GET /api/crm/pipeline/stats` (`contact 5, discovery 1, proposition 1`, total 7) | 18-pipeline-karim-proposition-score-survol.png | ok |
| 2.6 | Survol du « ? » du score | Une explication du chiffre | Infobulle native (`title`) : « Score de potentiel commercial, calculé depuis les informations du contact et son étape dans le pipeline. Plus il est haut, plus le prospect est chaud. L'échelle n'est pas plafonnée. » Rien sur le détail. À l'écran : Karim, plus avancé (Proposition), 100 ; Élodie (Découverte) 105 | 18 (infobulle système non capturée) ; arbre d'accessibilité | bug_candidate (nathalie-06) |
| 2.7 | « Ouvrir la fiche » d'Élodie, Historique | Pourquoi 105 | « Score recalculé : 50 → 105, Motif : changement d'étape » (B-1353 a pris) ; dessous « Stage: contact → discovery, Changement de stage dans le pipeline commercial » : codes internes anglais. L'étape vaut 10 points (`scoring.py` l. 33-41), le reste du saut (45 points) vient de l'e-mail, du téléphone et de l'entreprise, jamais comptés à l'import | 19-pipeline-elodie-historique-score.png | bug_candidate (nathalie-06, nathalie-10) |

Arbre d'accessibilité : chaque carte est un `div` `aria-roledescription="sortable"` décrit par la consigne clavier ; les annonces passent par une région `role=status` (`DndLiveRegion`). Onglets « Pipeline » / « Activités » en `tablist` « Vues du CRM ».
Console : rien de nouveau. Réseau : 2 × `PATCH …/stage` 200.

### 3. Relances : poser une relance à jeudi, la retrouver à l'Accueil

Préconditions : vendredi 25/09/2026, « jeudi » = 01/10/2026. Aucune boîte mail branchée (`setup-status` : `has_email: false`). Élodie en Découverte.
Gestes : 3 pistes essayées avant de trouver un moyen de dater quelque chose (Relances et alertes, Actions et relances, Tâches) ; 9 gestes pour la tâche de jeudi (Plus d'outils, recherche, carte, Nouvelle tâche, 4 champs, Enregistrer).

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 3.1 | « Plus d'outils », « relance » | Poser une relance sur un prospect | Quatre cartes : « Brief du jour », « Relances et alertes », « Actions et relances », « Skills et commandes » (« relancer » au sens de relancer un processus) | 20-relance-recherche-capacite.png | observation |
| 3.2 | « Relances et alertes » | Un bouton « Nouvelle relance » avec un contact et une date | Panneau « Relances et alertes, Échéances réelles liées aux emails », filtre « À traiter » vide, un seul bouton : « Créer depuis un email ». À gauche, la liste des contacts affiche l'étape en code interne : « … · proposition », « … · discovery », « … · contact » (le Pipeline dit « Découverte ») | 21-relance-vue-relances-alertes.png ; texte DOM relevé | bug_candidate (nathalie-11, nathalie-10) |
| 3.3 | « Créer depuis un email » | Une relance | L'écran « Email » s'ouvre avec la modale « Configuration Email » (Gmail OAuth, SMTP / IMAP) : je n'ai pas de boîte à brancher pour noter un rappel | 22-relance-creer-depuis-email.png | bug_candidate (nathalie-11) |
| 3.4 | Échap | Revenir aux relances | La modale se ferme mais je reste sur l'écran « Email » vide (« Aucun compte email configuré »), focus sur le bouton d'aide du rail. Le panneau des relances a disparu | 23-relance-apres-echap.png ; `activeElement` mesuré | bug_candidate (nathalie-12) |
| 3.5 | « Retour » | Les relances | Retour au Pipeline (Activités d'Élodie), pas au panneau où j'étais | 24-relance-retour-depuis-email.png | bug_candidate (nathalie-12) |
| 3.6 | « Plus d'outils », « relance », « Actions et relances » | Poser une relance | Panneau « Actions » : « Relance clients, Identifie les clients et prospects à relancer, avec un plan d'action, 3 étapes » (tâche confiée à l'IA). Aucune date à poser | 25-relance-actions-et-relances.png | observation |
| 3.7 | Échap, « Plus d'outils », « tâche », carte « Tâches » | Une liste de tâches | « Tâches, 0 tâche », colonnes À faire / En cours / Terminé ; le rail n'a pas d'entrée Tâches | 26-relance-vue-taches.png | ok |
| 3.8 | « Nouvelle tâche » | Un formulaire qui me laisse choisir Élodie | Titre, Description, Statut, Priorité, Date limite, Tags (« Séparez les tags par des virgules » : vouvoiement). **Aucun champ contact** : la tâche ne sera pas reliée à Élodie | 27-relance-nouvelle-tache-vide.png | proposal (nathalie-13) |
| 3.9 | « Relancer Élodie Martin (Boulangerie Martin) », 01/10/2026, tags, « Enregistrer » | Enregistrée | Carte « 1 oct. » dans « À faire » ; API `due_date: 2026-10-01T00:00:00` (pas de glissement de jour). Aucune confirmation écrite, la carte apparaît | 28-relance-tache-remplie.png, 29-relance-tache-enregistree.png | ok |
| 3.10 | Rail « Accueil » | Ma relance de jeudi, ou une rubrique « cette semaine » | « Un point mérite ton attention, 1 élément » : la séance d'Hélène seule, « Sources : agenda ». `GET /api/dashboard/today` : `urgent_tasks: 0`. Règle lue : le brief ne prend que les tâches « en retard ou dues aujourd'hui » (`dashboard.py` l. 385-400) ; rien d'« à venir » | 30-relance-accueil-sans-relance-jeudi.png | proposal (nathalie-14) |
| 3.11 | Contrôle : tâche « Relancer Karim Benali », due aujourd'hui | Visible à l'Accueil | Oui : « Ton attention aujourd'hui, 2 éléments », « Relancer Karim Benali (Garage Benali), Échéance 25/09, À traiter », « Sources : agenda, tâches ». Le brief marche ; c'est l'horizon qui s'arrête à aujourd'hui | 31-relance-tache-du-jour-enregistree.png, 32-relance-accueil-tache-du-jour.png | ok |
| 3.12 | Clic sur la ligne « Relancer Karim Benali » | La tâche, ou mieux la fiche de Karim avec son téléphone | La liste générale des Tâches ; la tâche n'est ni ouverte ni mise en avant ; rien ne mène à Karim | 33-relance-clic-ligne-brief.png | proposal (nathalie-13) |

Lecture du code (pour savoir quoi chercher, pas comme preuve d'écran) : le brief sait afficher « Relancer <prospect> · relance prévue le <date> » à partir de la date `next_follow_up` d'un contact (`prototypeReadModels.ts` l. 140-160, `services/relances.py`), mais aucun formulaire ni outil ne permet de poser cette date (`grep next_follow_up src/frontend/src` : lecture seule ; `memory_tools.py` : lecture seule).
Arbre d'accessibilité : la modale « Configuration Email » a le focus à l'ouverture ; après Échap, focus sur le bouton d'aide du rail. Le formulaire de tâche a des champs nommés (Titre, Description, Statut, Priorité, Date limite, Tags).
Console : rien de nouveau. Réseau : `POST /api/tasks/` × 2 (200), `GET /api/dashboard/today` relu à chaque retour à l'Accueil.

### 4. Devis puis facture : un devis pour Élodie, le convertir, marquer la facture payée (texte à 125 %)

Préconditions : texte agrandi à 125 % (mesure : corps 14 → 17,5 px, titre 26 → 32,5 px, bouton « Facturer » 30 → 37 px de haut). Profil de facturation de Claire (SIRET, adresse, pas de numéro de TVA). Deux pièces de Claire (DEV-2026-001 converti, FACT-2026-001 brouillon).
Gestes : puce « Facturer », « Nouveau devis », client, 4 champs, « Enregistrer le brouillon », « Confirmer le brouillon » (9) ; « Ouvrir Devis et factures », ligne, « Convertir en facture », « Convertir » (4) ; ligne de la facture, « Marquer comme payée », « Confirmer le paiement » (3). 16 gestes, sans hésitation.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 4.1 | Accueil à 125 % | Lisible | Lisible ; l'établi passe sur deux lignes (« Facturer », « Décider » en dessous) | 34-facturer-accueil-125.png | ok |
| 4.2 | Puce « Facturer » | Faire un devis | Carte « Facturer un client, 2 documents enregistrés », « Nouveau devis », « Ouvrir Devis et factures » (le doublon « Préparer un devis » vu par Claire a disparu) | 35-facturer-ouvert-125.png | ok |
| 4.3 | « Nouveau devis » | Formulaire lisible | Panneau « Nouveau devis brouillon », sous-titre « Les données affichées viennent du module Facturation existant. » (phrase de développeur). À 125 %, la ligne donne 61 px à « Description », 70 à « Qté », 100 à « Prix HT », 86 à « TVA » ; « Supprimer la ligne 1 » tient dans le panneau (x 1 179-1 219 pour 1 280 : B-1355 tient) | 36-facturer-nouveau-devis-125.png ; mesures DOM | bug_candidate (nathalie-15) |
| 4.4 | Client « Élodie Martin », « Vitrine réfrigérée, fourniture et pose », 1 × 1 200 €, TVA 20 %, notes | Voir ce que je tape | La description affiche « Vitri » : 59 px visibles pour 322 px de texte. Totaux justes : HT 1 200 €, TVA 240 €, TTC 1 440 € | 37-facturer-devis-rempli-125.png, 38-facturer-ligne-description-ecrasee-125.png | bug_candidate (nathalie-15) |
| 4.5 | « Enregistrer le brouillon » | Récapitulatif | « Confirmer la création du devis brouillon, Destinataire : Élodie Martin, Montant TTC : 1440,00 €, Échéance : 25/10/2026 » | 39-facturer-devis-confirmation-125.png | ok |
| 4.6 | « Confirmer le brouillon » | Enregistré | « DEV-2026-002 enregistré comme brouillon. Aucun PDF n'a été généré et aucun email n'a été envoyé. » ; « 3 documents enregistrés » ; « Enregistrer le brouillon » désormais grisé (plus de doublon possible) | 40-facturer-devis-confirme-125.png | ok |
| 4.7 | « Ouvrir Devis et factures » | La liste | « 3 pièces ». DEV-2026-001 : « Converti en facture, Émis le 25/09/2026 » (B-1356 tient pour le devis). À 125 %, le tableau fait 1 313 px pour 1 148 visibles : les boutons « Supprimer » (x 1 265-1 394) sont hors cadre, il faut défiler à l'horizontale | 41-facturer-liste-devis-factures-125.png ; mesures DOM | bug_candidate (nathalie-15) |
| 4.8 | Clic sur DEV-2026-002 | Le devis | Dialogue « Modifier DEV-2026-002 » ; « Lignes de facturation » (le panneau disait « Lignes du devis ») ; TVA « 20% (norma » tronquée ; boutons Accepter, Refuser, Convertir en facture | 42-facturer-devis-detail-125.png | observation |
| 4.9 | « Convertir en facture » | Confirmation claire | « Convertir en facture ? … Conditions : 30 jours, virement bancaire. Mentions légales : ajoutées automatiquement » (accentué : B-1358 tient). Le focus reste sur « Convertir en facture », derrière la confirmation | 43-facturer-convertir-confirmation-125.png ; arbre d'accessibilité (`[active]`) | observation |
| 4.10 | « Convertir » | Une facture | « Devis converti en facture, Facture FACT-2026-002 créée à partir du devis DEV-2026-002 » ; 4 pièces | 44-facturer-facture-creee-125.png | ok |
| 4.11 | Clic sur FACT-2026-002 | Un moyen de dire « payée » | Dialogue « Modifier FACT-2026-002 » avec « Marquer comme payée ». Menu Statut : « Brouillon, Envoyé, Payée, En retard, Annulée » (« Envoyé » au masculin pour une facture ; le filtre dit « Envoyée ») | 45-facturer-facture-detail-125.png | observation |
| 4.12 | « Marquer comme payée » | Confirmation | « Aperçu avant action, Confirmer le paiement de la facture, … enregistrera sa date de paiement », FACT-2026-002, 1440,00 €, « Payée ». Ne demande pas la date du paiement (ce sera aujourd'hui) et ne relève pas que la facture est encore un brouillon jamais envoyé | 46-facturer-marquer-payee-clic-125.png | observation |
| 4.13 | « Confirmer le paiement » | Payée, sans rien inventer | Notification « Facture payée ». Dans la liste : Paiement « Payée le 25/09/2026 », mais Envoi « **Envoyée le 25/09/2026** » alors que je n'ai rien envoyé : le moteur rend `status: paid, sent_at: None`. Le montant est coupé (« 1 440, ») | 47-facturer-facture-payee-125.png ; `GET /api/invoices/` | bug_candidate (nathalie-16) |
| 4.14 | « PDF » de FACT-2026-002 | Une facture juste | Hors Tauri, ouverture impossible (repli attendu). PDF lu : émetteur, SIRET, cliente, ligne à 20 %, totaux, conditions accentuées et « 11,62 % » (B-1357 tient), « Statut : Payée » sans date. Aucun numéro de TVA de l'émetteur alors que la facture applique 20 % : le champ « TVA intracommunautaire » existe dans Paramètres mais est vide, et rien ne m'a prévenue | 48-facturer-pdf-facture-125.png ; texte extrait de `FACT-2026-002.pdf` | proposal (nathalie-17) |

Arbre d'accessibilité : la confirmation de conversion est un `dialog "Confirmer la conversion"` imbriqué, sans focus initial ; la liste est un vrai `table` ; « PDF » s'annonce « Générer et ouvrir le PDF ».
Console : `[INFO] PDF generated but local opening is unavailable` (attendu hors Tauri). Réseau : `POST /api/invoices` (devis, n° 2066), `POST /api/invoices/f0090efe…/convert-to-invoice` (n° 2084), `PATCH /api/invoices/1f1738ff…/mark-paid` (n° 2093), `GET …/pdf` (n° 2097), tous 200 ; tout en 127.0.0.1.

### 5. Tableau de bord : lire l'Accueil, savoir ce qui est urgent et d'où viennent les chiffres (texte à 125 %)

Préconditions : une tâche due aujourd'hui (Karim), une due jeudi (Élodie), une séance d'Hélène à 16:00, une facture payée à l'instant.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 5.1 | Rail « Accueil » | Ce qui est urgent, et mes chiffres de la semaine | « Ton attention aujourd'hui, 2 éléments » : séance d'Hélène (16:00, « Contact CRM ») et « Relancer Karim Benali, Échéance 25/09, À traiter » ; « Sources : agenda, tâches · Rafraîchi à 11:06 ». Le chiffre 2 = `events_count 1 + tasks_count 1` de `GET /api/dashboard/today` : cohérent et sourcé (« Lu dans Agenda, Tâches »). Rien sur la facture encaissée (1 440 €), rien sur le pipeline (3 nouveaux, 1 en Découverte, 1 en Proposition), rien sur la relance de jeudi | 49-accueil-125.png ; réponse du moteur relevée | proposal (nathalie-14) |
| 5.2 | « Voir la suite » | Une suite | Défilement de 25 px : le bandeau « Lu dans » était caché sous le composeur ; aucun contenu nouveau | 50-accueil-voir-la-suite-125.png | observation |
| 5.3 | « Plus d'outils » > « Brief du jour » | Un tableau plus complet | La même carte, mêmes chiffres (cohérent). Le bouton principal reste « Commencer : Séance Hélène Ménard-Lefèvre » ; ma relance du jour a le même poids visuel que la séance (étiquette neutre « À traiter ») | 51-accueil-capacite-brief-du-jour-125.png | observation |

Réponse à ma question « ce qui est urgent est-il clair ? » : oui pour aujourd'hui, et chaque chiffre dit sa source. Mais l'Accueil ne regarde qu'aujourd'hui : ni la semaine, ni l'argent, ni le pipeline.
Console : rien de nouveau. Réseau : `GET /api/dashboard/today` et `GET /api/dashboard/setup-status` à chaque retour.

### 6. Export : exporter mes contacts, rouvrir le fichier, comparer avec l'écran (texte à 125 %)

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 6.1 | ⌘M | L'écran Contacts | « Contacts », 7 fiches ; la liste n'affiche ni étape, ni score, ni téléphone | 52-export-ecran-contacts-125.png | ok |
| 6.2 | « Exporter » | Un fichier que je peux ouvrir dans Excel, avec mes étapes | Notification « Export VCF, Téléchargement du fichier VCF démarré ». `GET /api/memory/contacts/export` 200 ; fichier `therese-contacts.vcf` (1 283 octets). Le bouton ne disait pas « vCard » | 53-export-clic-125.png ; requête n° 2118 | proposal (nathalie-18) |
| 6.3 | Je rouvre le fichier | Même contenu que l'écran | 7 cartes pour 7 fiches à l'écran (Paul, périmètre projet, inclus ; les deux Sophie Durand aussi). Noms, e-mails, entreprises, téléphones, adresses, notes : conformes. **Absents** : étape du pipeline, score, et étiquettes (Hélène a `tags: ["cliente","reconversion"]` en base, aucune ligne `CATEGORIES` dans le fichier). Ordre différent de l'écran | fichier relu (extrait dans le constat nathalie-19) | bug_candidate (nathalie-19) |

Lecture du code : le moteur sait exporter en CSV, Excel ou JSON avec filtre par étape (`POST /api/crm/export/contacts`, `crm.py` l. 628-652) ; aucune surface ne l'appelle (`grep "crm/export" src/frontend/src` : 0). L'export vCard n'écrit que N, FN, ORG, EMAIL, TEL, ADR, NOTE (`memory.py` l. 862-907).
Note d'instrument : le navigateur piloté a déposé le téléchargement dans `~/.playwright-mcp/therese-contacts.vcf` (dossier de travail de l'outil, pas un geste de ma part).
Console : rien de nouveau. Réseau : 1 × `GET /api/memory/contacts/export` 200.

## Constats numérotés

**nathalie-01, proposal : la recherche de capacités ne connaît pas « importer ».**
« importer » → « Aucune capacité trouvée » ; « excel » → « Word, PowerPoint et Excel » (produire un fichier, pas en lire un) ; il faut penser à « prospects » (Pipeline) ou « contacts » pour tomber sur un bouton d'import. Piste : relier « importer », « import », « Excel », « CSV », « fichier » aux écrans qui importent. Voisin de claire-15 (synonymes). Preuve : 02, 03, 04.

**nathalie-02, proposal : aucune entrée pour importer un fichier Excel ou CSV, alors que le moteur le sait.**
Étapes : Pipeline ou Contacts, « Importer (.vcf) », fichier `prospects-excel.csv`. Observé : refus « Le fichier doit être au format .vcf » (Pipeline) ou « L'import a échoué » (Contacts), sans piste. Le moteur expose pourtant un import CSV, Excel ou JSON avec aperçu, correspondance des colonnes et erreurs par ligne (`POST /api/crm/import/contacts/preview` et `/import/contacts`, `src/backend/app/routers/crm.py` l. 741-811) ; `grep "import/contacts" src/frontend/src` ne rend rien. C'est exactement ce qu'il me faut pour savoir ce qui est écarté (ma ligne « Marc Leroy », étape « inconnue », sans entreprise). Seule autre voie : la synchronisation Google Sheets (en ligne). Preuve : 06, 12 ; requêtes n° 1903 et 1930 (400).

**nathalie-03, bug_candidate, moyenne : l'import vCard écarte des cartes sans le dire, même dans son total.**
Étapes : Pipeline, « Importer (.vcf) », fichier de deux cartes dont une sans N ni FN (entreprise et e-mail seuls). Attendu : « 1 carte écartée : pas de nom » (ma ligne rouge : un import qui dit « terminé » sans dire ce qui a été écarté). Observé : « Import VCF, 0 contact(s) créé(s), 1 mis à jour » ; réponse `{"created":0,"updated":1,"total":1,…}` pour un fichier de deux cartes. Cause lue : `src/backend/app/services/import_service.py` l. 121 (`continue  # Pas de nom, skip`) retire la carte avant tout comptage ; l. 138, une adresse e-mail jugée douteuse est vidée en silence (la fiche est créée sans e-mail, aucun signalement) ; `crm.py` l. 891-892 construit le message sans rubrique « écartées ». Preuve : 09-import-vcf-carte-sans-nom-muette.png, requête n° 1917 (corps cité).

**nathalie-04, observation : « mis à jour » pour des fiches que rien n'a changé.**
Réimporter le même fichier annonce « 0 contact(s) créé(s), 3 mis à jour » : je ne sais pas ce qui a été modifié (rien, en réalité, les valeurs étaient identiques). « 3 déjà présents, rien à changer » serait vrai. Preuve : 08.

**nathalie-05, bug_candidate, mineure : deux boutons « Importer (.vcf) » identiques, deux routes, deux règles, deux messages.**
Étapes : même fichier depuis Pipeline puis depuis Contacts. Observé : le Pipeline appelle `POST /api/crm/import/vcf` (doublon reconnu par l'e-mail seul) ; l'écran Contacts appelle `POST /api/memory/contacts/import` (doublon par e-mail, puis par prénom et nom : une homonyme y serait mise à jour au lieu d'être créée). En cas d'échec, le Pipeline montre la raison du moteur, l'écran Contacts la remplace par « L'import a échoué. Vérifie le fichier et réessaie. » (`MemoryPanel.tsx` l. 193) ; en cas de réussite, l'écran Contacts écrit « 0 contact(s) cree(s), 3 mis a jour », sans accents (`memory.py` l. 778, 793, 848, 850 : « doit etre », « Aucun contact trouve », « cree(s) », « mis a jour »). Attendu (grille, cohérence) : même bouton, même effet, même message. Preuve : 06, 12, 13 ; console l. 186-189. Les règles d'homonymie elles-mêmes relèvent de B-1205 (non re-signalé) ; le défaut ici est la divergence entre deux boutons de même nom.

**nathalie-06, bug_candidate, moyenne : le score d'un prospect importé n'est pas calculé, puis saute au premier déplacement ; son origine est illisible.**
Étapes : importer `prospects.vcf`, déplacer Élodie d'une colonne. Observé : les fiches importées affichent 50, quelle que soit leur richesse ; au premier déplacement, Élodie passe à 105 (« Score recalculé : 50 → 105, Motif : changement d'étape ») alors que l'étape Découverte vaut 10 points ; Karim, déplacé plus loin (Proposition), a 100 < 105 parce qu'il n'a pas de téléphone ; Paul et Julien, mêmes champs (e-mail, entreprise) et même étape, ont 50 et 80. L'infobulle du « ? » est une phrase générale (« calculé depuis les informations du contact et son étape… L'échelle n'est pas plafonnée »), sans le détail. Cause lue : le calcul (`services/scoring.py` l. 19-41 : base 50, e-mail 20, téléphone 15, entreprise 10, étape 0 à 50) n'est appelé à la création que par le formulaire (`memory.py` l. 738, `reason="initial_creation"`) ; les imports créent `Contact(...)` avec le défaut `score = 50` (`entities.py` l. 38). Paul, lui, n'a pas été importé : Hugo l'a créé par `/contact Paul Exemple email=… societe=Orion` dans le chat (trace d'Hugo, étape 1b.1) ; il est aussi à 50 avec e-mail et entreprise, donc la commande du chat ne calcule pas non plus. Attendu : un chiffre stable, le même pour deux fiches identiques, et une explication qui dise « +15 téléphone, +10 Découverte ». C'est ma ligne rouge : un chiffre dont je ne comprends pas l'origine. Preuve : 17, 18, 19 ; `PATCH …/stage` n° 1954 (`"score":105`) ; relevé API des sept fiches (Julien 80, Paul 50).

**nathalie-07, bug_candidate, mineure : après avoir posé une carte au clavier, le focus tombe sur la page.**
Étapes : Pipeline, focus sur une carte, Espace, flèche droite, Espace. Observé : `document.activeElement` = `BODY` ; pour déplacer la carte suivante il faut repartir du début de la page. Attendu (grille, clavier) : le focus reste sur la carte déposée. Preuve : 17 ; mesure DOM (`estBody: true`). Fichier suspecté : `src/frontend/src/components/crm/PipelineView.tsx` (la carte est rendue dans une autre colonne après le dépôt).

**nathalie-08, bug_candidate, mineure : « Ouvrir la fiche » n'ouvre pas de fiche, et propose les offres de l'éditeur en exemple.**
Étapes : Pipeline, « Ouvrir la fiche » d'Élodie. Observé : l'onglet « Activités » : nom, entreprise, « Prestations », « Historique » ; ni e-mail, ni téléphone, ni étape, ni score. Le champ « Intitulé » d'une prestation a pour exemple « FORGER, PROPULSER, diagnostic… » (`src/frontend/src/components/crm/ListeDesPrestations.tsx` l. 128), noms d'offres qui ne sont pas les miennes. Voisin de claire-19 (« Synoptïa » en exemple). Preuve : 15, 19.

**nathalie-09, proposal : deux vocabulaires d'avancement et aucun champ « Étape ».**
Les colonnes disent Contact, Découverte, Proposition, Signature, Livraison, Actif, Archive ; la prestation de la même fiche dit Piste, Proposition envoyée, Signée, Perdue, En cours, Terminée. Il n'y a pas de « Perdu » dans le pipeline, et le seul moyen de changer d'étape est de glisser la carte (aucun menu sur la carte ni sur la fiche). Pistes : un champ « Étape » sur la fiche, un vocabulaire unique. Preuve : 15, relevé des options.

**nathalie-10, bug_candidate, mineure : les codes internes des étapes s'affichent encore (B-1353 partiel).**
Observé : historique d'Élodie « Stage: contact → discovery », « Changement de stage dans le pipeline commercial » (`src/backend/app/routers/crm.py` l. 537-538 ; le correctif B-1353 de `lib/activitesCrm.ts` ne traduit que le recalcul de score) ; panneau « Contacts et mémoire » : « … · discovery », « … · proposition », « … · contact » alors que le Pipeline dit « Découverte ». Attendu (lexique) : les libellés des colonnes. Preuve : 19, 21 ; texte DOM relevé.

**nathalie-11, bug_candidate, moyenne : impossible de poser une relance datée sur un prospect.**
Étapes : « Plus d'outils », « relance », « Relances et alertes » ; puis « Actions et relances ». Attendu : la capacité promet de « faire remonter ce qui risque d'être oublié » ; l'Accueil sait afficher « Relancer <prospect> · relance prévue le <date> ». Observé : « Relances et alertes » ne propose que « Créer depuis un email », qui ouvre la configuration d'une boîte mail (Gmail OAuth ou IMAP) ; « Actions et relances » lance un plan d'action par l'IA ; la date `next_follow_up` d'un contact, que le brief lit (`prototypeReadModels.ts` l. 140-160, `services/relances.py`), n'a aucun champ dans les formulaires (`grep next_follow_up src/frontend/src` : lecture seule) ni dans les outils du chat (`memory_tools.py` : lecture seule). Vérifié aussi sur la fiche : « Ajouter une activité » ouvre « Nouvelle activité » avec Type (Email, Appel, Réunion, Note), Titre, Description, sans aucune date ; côté moteur, `CreateActivityRequest` (`schemas.py` l. 1367-1374) n'a pas de date, et une activité de type appel, e-mail ou réunion ne fait que solder une relance existante (`crm.py` l. 151-159). Sans boîte mail, la seule voie est une tâche, non reliée au contact. C'est ma ligne rouge : une relance que je ne retrouve pas. Preuve : 20, 21, 22, 25, 27, 57-relance-controle-ajouter-activite.png.

**nathalie-12, bug_candidate, mineure : je ne peux pas revenir au panneau des relances.**
Étapes : « Relances et alertes », « Créer depuis un email », Échap, puis « Retour ». Observé : Échap ferme la configuration mais me laisse sur l'écran « Email » vide (focus sur le bouton d'aide du rail) ; « Retour » m'envoie au Pipeline. Le panneau d'où je venais a disparu. Attendu (grille) : Échap et « Retour » ramènent d'où je viens. Le bouton « Retour » s'annonce en outre « Revenir à la conversation unifiée » sur tous les écrans, quelle que soit sa destination. Preuve : 22, 23, 24 ; `activeElement` mesuré.

**nathalie-13, proposal : une relance posée en tâche n'est reliée à personne.**
Le formulaire « Nouvelle tâche » n'a pas de champ contact ; dans le brief, cliquer « Relancer Karim Benali » ouvre la liste générale des tâches, ni la tâche ni la fiche de Karim (et donc pas son numéro). Pistes : un contact sur la tâche ; un clic qui ouvre la personne à rappeler. Preuve : 27, 33.

**nathalie-14, proposal : l'Accueil ne regarde qu'aujourd'hui.**
Ma relance de jeudi n'apparaîtra que jeudi (`dashboard.py` l. 385-400 : tâches « en retard ou dues aujourd'hui ») ; la facture encaissée (1 440 €) et l'état du pipeline n'y figurent pas. Ce qui s'y trouve est juste et sourcé (« 2 éléments » = 1 rendez-vous + 1 tâche, « Lu dans Agenda, Tâches »). Piste : une ligne « Cette semaine » (relances et échéances à venir) et deux chiffres (encaissé du mois, prospects par étape), chacun avec sa source. Preuve : 30, 32, 49 ; `GET /api/dashboard/today`.

**nathalie-15, bug_candidate, mineure : à 125 %, je ne lis plus ce que je facture.**
Étapes : texte agrandi à 125 % (racine 20 px), « Facturer », « Nouveau devis ». Observé : la description de la ligne a 61 px (« Vitri » visible sur « Vitrine réfrigérée, fourniture et pose », 322 px de texte), moins que le prix (100 px) ; à 100 %, 99 px. Dans « Devis et factures », le tableau fait 1 313 px pour 1 148 visibles : les boutons « Supprimer » (x 1 265-1 394) sont hors cadre, et après paiement le montant est coupé (« 1 440, »). Attendu (grille, lisibilité) : aucun texte important coupé à 125 %. B-1355 (bouton de suppression dans le panneau) tient, lui, aux deux tailles. Preuve : 36, 38, 41, 47, 54 ; mesures DOM.

**nathalie-16, bug_candidate, moyenne : une facture payée se dit « Envoyée » alors qu'elle n'a jamais été envoyée (B-1356 partiel).**
Étapes : convertir un devis brouillon, ouvrir la facture, « Marquer comme payée », « Confirmer le paiement ». Observé : colonne Envoi « Envoyée le 25/09/2026 » ; le moteur rend `status: paid`, `sent_at: None`. Cause lue : `src/frontend/src/components/invoices/presentationFacture.ts` l. 67 construit « Envoyée le <date d'émission> » sans lire `sent_at`, et les branches `paid` (l. 132), `overdue` (l. 148), `sent` (l. 156) et le repli final l'affichent ; B-1356 n'a corrigé que le devis converti (l. 100-107). C'est la même affirmation d'un envoi inventé, sur une facture, document juridique. Preuve : 47 ; `GET /api/invoices/` (FACT-2026-002 `sent_at= None`).

**nathalie-17, proposal : une facture à 20 % de TVA part sans numéro de TVA, sans avertissement.**
Le PDF de FACT-2026-002 applique 20 % et ne porte aucun numéro de TVA de l'émetteur : le champ « TVA intracommunautaire » existe (Paramètres > Profil) mais est vide, et ni le profil (« complet ») ni la facture ne le signalent. Mention qui relève d'une règle légale externe à l'application : à confirmer par Ludo. Preuve : texte extrait de `FACT-2026-002.pdf` ; `GET /api/config/profile` (`tva_intra: ""`) ; `invoice_pdf.py` l. 354-356 (n'affiche le numéro que s'il existe).

**nathalie-18, proposal : l'export ne sort qu'un vCard, sans mes étapes ; l'export tableur du moteur n'a pas de bouton.**
« Exporter » (écran Contacts) télécharge `therese-contacts.vcf`, pour un carnet d'adresses, pas pour Excel ; le bouton ne dit pas le format. Le moteur sait exporter en CSV, Excel ou JSON avec filtre d'étape (`POST /api/crm/export/contacts`, `crm.py` l. 628-652), sans aucune surface (`grep "crm/export" src/frontend/src` : 0). Preuve : 53 ; requête n° 2118.

**nathalie-19, bug_candidate, mineure : l'export perd les étiquettes des contacts.**
Étapes : écran Contacts, « Exporter », rouvrir le fichier. Observé : 7 cartes pour 7 fiches (conforme), mais aucune étiquette : Hélène a `tags: ["cliente","reconversion"]` en base, et sa carte n'a pas de ligne `CATEGORIES` (propriété vCard standard). L'export n'écrit que N, FN, ORG, EMAIL, TEL, ADR, NOTE (`memory.py` l. 862-921). Une étiquette saisie disparaît à l'aller-retour, sans le dire. Extrait du fichier : `FN:Hélène Ménard-Lefèvre` … `NOTE:Accompagnement reconversion\, 10 séances\, facturé au mois.` … `TEL;TYPE=CELL:06 00 00 00 01` (aucune `CATEGORIES`). Preuve : fichier `~/.playwright-mcp/therese-contacts.vcf` relu ; relevé API des fiches.

**nathalie-20, observation : petites fautes de langue et de cohérence relevées en chemin.**
Annonces du glisser au clavier « la carte de Élodie Martin … a été déposé » (élision, accord) ; « Séparez les tags par des virgules » (vouvoiement, l'application tutoie) ; statut de facture « Envoyé » au masculin (le filtre dit « Envoyée ») ; sous-titre du devis « Les données affichées viennent du module Facturation existant » (phrase de développeur) ; « Lignes du devis » dans le panneau, « Lignes de facturation » dans le dialogue ; icônes collées au texte des boutons de l'écran Contacts (écart 0 px) ; « Voir la suite » de l'Accueil qui ne défile que de 25 px ; à 1 280 px, les colonnes « Actif » et « Archive » du Pipeline sont hors écran (défilement horizontal nécessaire, rien ne l'indique). Preuve : 16, 17, 27, 36, 42, 45, 11, 50, 05 ; relevés DOM.

**nathalie-21, observation : on peut marquer payée une facture restée brouillon, sans date de paiement.**
La confirmation ne signale pas que FACT-2026-002 n'a jamais été émise ni envoyée, et ne demande pas la date du paiement (ce sera le jour du clic) ; le PDF affiche « Statut : Payée » sans date. Je ne sais pas si c'est voulu. Preuve : 46, 47, texte du PDF.

Écartés faute de preuve (2) : le bouton « Voir la suite » qui semblait recouvrir la ligne DEV-2026-001 à 125 % (mesure `elementFromPoint` non concluante) ; le bouton « Ouvrir Contacts » posé à cheval sur la bordure de la carte « Contacts et mémoire » (vu sur la capture 10, non mesuré).

## Transitions couvertes et angles morts

**Transitions couvertes** (57 captures, relues à l'image pour 37 d'entre elles, les autres vérifiées au même instant par l'arbre d'accessibilité ou une mesure DOM) :
- Accueil → « Plus d'outils » → recherches « importer », « prospects », « excel », « contacts » → Pipeline → import CSV (refus) → import vCard (succès) → réimport (doublons) → variante sans nom (écart muet).
- Accueil → Contacts (parcours) → « Ouvrir Contacts » → import CSV (refus générique) → import vCard (bilan sans accents) → « Retour » (Pipeline).
- Pipeline → « Ouvrir la fiche » (Activités) → onglet Pipeline → deux déplacements au clavier (Espace, flèches, Espace) → infobulle du score → historique.
- « Plus d'outils » → Relances et alertes → « Créer depuis un email » → Échap → « Retour » ; → Actions et relances → Échap ; → Tâches → deux tâches (jeudi, aujourd'hui) → Accueil (absente, puis présente) → clic sur la ligne du brief.
- Texte à 125 % : Accueil → Facturer → Nouveau devis → Enregistrer → Confirmer → Devis et factures → devis → Convertir → facture → Marquer comme payée → Confirmer → PDF.
- Accueil à 125 % → « Voir la suite » → Brief du jour ; ⌘M → Contacts → Exporter → fichier rouvert.
- Contrôle à 100 % de la ligne de devis ; Paramètres → Accessibilité → Sombre ; viewport 1440×900.
- Contrôle après relecture (1440×900, sombre) : Pipeline → Activités d'Élodie → « Ajouter une activité » (aucun champ de date) → Annuler → Accueil.

**Correctifs revérifiés au passage** : B-1355 (bouton de suppression dans le panneau, à 100 % et 125 %) tient ; B-1356 tient pour le devis converti, pas pour la facture payée (nathalie-16) ; B-1357 (PDF accentué, « 11,62 % ») tient ; B-1358 (confirmation de conversion accentuée) tient ; B-1353 tient pour le score, pas pour le changement d'étape (nathalie-10). « Enregistrer le brouillon » est grisé après confirmation (le doublon que Claire n'avait pas essayé n'est plus possible).

**Angles morts** :
- Instrument : pas de dépôt de fichier ni de glisser-déposer à la souris dans le MCP. Fichiers injectés par `DataTransfer` après un clic réel sur le bouton ; cartes déplacées au clavier. Le sélecteur de fichier natif (et son filtre `.vcf`, qui griserait peut-être mon CSV sur macOS) n'est pas vu.
- 125 % simulé par la taille de la racine (20 px), pas par le zoom du navigateur ; l'application a son propre réglage de taille de texte (`therese-accessibility.fontSize`), non essayé.
- Horloge : je ne peux pas avancer au jeudi 1er octobre ; la présence de la tâche de jeudi à l'Accueil ce jour-là est déduite de la règle lue et du contrôle par une tâche du jour.
- Tauri absent : ouverture du PDF et enregistrement de l'export dans Téléchargements non testables (repli navigateur constaté).
- Non essayés : synchronisation Google Sheets (en ligne), chat (lent en local, et aucun de mes gestes n'en avait besoin), vue « Liste » du Pipeline et des Tâches, glisser à la souris, filtres de statut des factures.
- Console : 24 erreurs (« ERR_CONNECTION_REFUSED » sur `/api/auth/token`, `/health`, `/api/config/stats`) et 24 avertissements (« Could not load auth token », « Tentative n/5 échouée », « Health check failed ») datent d'avant mon premier geste (relance du moteur par l'orchestrateur) ; pendant mon parcours, seules mes deux tentatives CSV (400) et `VCF import failed` apparaissent, plus l'information attendue sur le PDF hors Tauri.

**Données laissées en place pour Zoé** : contacts Élodie Martin (Découverte, score 105), Karim Benali (Proposition, 100), Sophie Durand `@exemple.fr` (Contact, 50) en plus des quatre d'avant ; tâches « Relancer Élodie Martin (Boulangerie Martin) » (01/10) et « Relancer Karim Benali (Garage Benali) » (25/09) ; DEV-2026-002 (converti) et FACT-2026-002 (payée, 1 440 €) pour Élodie. État final mesuré à 11:14, sur l'Accueil : document visible, 1440×900, thème `dark`, racine 16 px (mon style retiré), aucun dialogue, `HTMLInputElement.prototype.click` rendu natif.

**Bilan** : 21 constats numérotés avec preuve : 11 bug_candidate (4 moyennes : nathalie-03, 06, 11, 16 ; 7 mineures), 7 proposal, 3 observation. 2 constats écartés faute de preuve.

## Tokens consommés (si connus)

Environ 400 000 tokens (compteur de session : 15 000 000 au départ, environ 14 603 000 à la fin de la trace).
