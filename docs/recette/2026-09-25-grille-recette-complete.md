# Grille de la recette complète (P-146)

Rédigée le 25/09/2026 pour le cycle 13. Demande de Ludo : qu'au moins une fois
par release, **l'ensemble des fonctionnalités soit testé par un équivalent
humain**. La couverture écran de P-145 vérifie que rien ne casse ; cette
recette vérifie que chaque fonction fait ce qu'elle promet.

Source de la liste : les trente capacités du tiroir « Plus d'outils »
(`components/prototype/CapabilityCenter.tsx`, champ `features`), complétées des
écrans ajoutés au cycle 13. Une capacité non listée ici est un trou de la
grille, à signaler.

## Règles pour chaque persona de lot

- **Pile jetable seulement** : moteur 17393, Vite 1420, dossier de données
  vierge du lot. Jamais le port 17293. Service d'IA : Ollama local
  (`qwen3:8b`), aucun consentement cloud.
- **Une ligne = un geste réel dans l'application** (clic, frappe), jamais un
  appel d'API à la place du geste. L'API ne sert qu'à vérifier le résultat.
- **Coche** : `OK` (résultat observé conforme, avec la preuve : capture,
  réponse d'API ou texte lu), `KO` (attendu, observé, preuve : c'est un bug
  candidat), `N/A` (fonction impossible sur la pile, avec la raison : compte
  Google absent, clé cloud absente…). La grille est complète quand chaque
  ligne porte une coche.
- **Ne jamais confirmer un envoi vers l'extérieur** (e-mail, service tiers) :
  s'arrêter à la carte de confirmation, qui est elle-même le résultat attendu.
- **Données fictives** uniquement (Hélène Ménard, Julien Garnier, Nadia Roux,
  adresses en `example.test`).

## Lot 1 : organiser le quotidien

| Fonction | Geste | Résultat qui la valide |
|---|---|---|
| Accueil, brief du jour | Ouvrir l'application avec une tâche due aujourd'hui | Le point apparaît, sa source est nommée (« Lu dans Tâches ») |
| Point du brief | Cliquer « Relancer … » (tâche reliée) | La fiche de la personne s'ouvre (P-134, B-1417) |
| Cette semaine | Poser une relance à J+3 | Elle apparaît sous « Cette semaine », avec son jour |
| Chiffres de l'Accueil | Marquer une facture payée ce mois | « Encaissé » la compte, source dite |
| Mise en route | Carte « Compléter le profil de facturation » | Ouvre la facturation ; disparaît une fois complétée |
| Tâches : créer | Nouvelle tâche avec échéance, priorité, contact | Elle apparaît, reliée à la personne |
| Tâches : compléter | Cocher une tâche | Elle passe « Terminée », sort du brief |
| Tâches : filtrer | Filtre projet, filtre tag | La liste se restreint, « réinitialiser » la rend |
| Agenda : créer | Nouveau rendez-vous local avec un participant | Il apparaît dans l'Agenda et dans les séances de la fiche (P-116) |
| Agenda : ajout rapide | Saisie en langage naturel dans la conversation (seul point d'entrée pour un agenda local) | Carte de confirmation, rendez-vous créé, message accentué (B-1431) |
| Agenda : import/export ICS | Exporter puis réimporter | Le fichier se range dans Téléchargements, l'import ne duplique pas |
| Préparer un rendez-vous | Choisir la séance | Participants reliés, points à vérifier, note de séance |
| Note de séance | Ajouter la note au contact | Elle se lit dans l'historique de la fiche (P-120) |
| Relances et alertes | Créer une relance | Elle apparaît à sa date, se complète |
| Écrire un e-mail | Rédiger un brouillon sans boîte branchée | L'écran dit ce qui manque, rien ne part |
| Palette ⌘K | Chercher un nom de client | Le contact, le projet, la conversation (P-016) |
| Navigation | Rail, Retour, Échap depuis chaque vue | On revient d'un geste à l'écran précédent |
| Reprise | Recharger sur une vue | La vue quittée se rouvre (P-142) |
| Agenda : vues et périodes | Jour, Semaine, Mois, Liste ; période suivante puis précédente, y compris à cheval sur deux mois | Chaque rendez-vous reste à sa place, dernier jour du mois compris (B-1429) |
| Préparer : nouvel événement | « Nouvel événement » depuis Préparer | Formulaire « Vérifier avant création », rendez-vous créé |
| Poursuivre dans le chat | Depuis l'Accueil, saisir puis « Poursuivre dans le chat » | Nouvelle conversation avec la saisie, non envoyée |
| Tâches : colonnes et liste | Basculer Colonnes et Liste, glisser une carte entre colonnes | Le statut suit la colonne |
| Relance de fiche : la compléter | Relance posée sur la fiche, puis la déclarer faite | Elle sort du brief et de « Cette semaine » |

## Lot 2 : développer l'activité (clients)

| Fonction | Geste | Résultat qui la valide |
|---|---|---|
| Contacts : créer | Nouveau contact complet | Il apparaît, cherchable par prénom (B-1350) |
| Contacts : modifier | Changer le téléphone | La fiche relue porte la nouvelle valeur |
| Contacts : relance datée | Prochaine relance sur la fiche | Elle remonte au brief à sa date (P-133) |
| Contacts : périmètres | Filtre Global, Projet, Conversation | L'aide dit d'où vient chacun (P-115) |
| Contacts : import vCard | Importer un .vcf | « créé », « déjà à jour » au second import |
| Contacts : import tableur | CSV avec « Étape » accentuée | Aperçu : colonnes reconnues, ignorées, lignes signalées (P-130, B-1418) |
| Contacts : export | vCard, puis tableur | Deux fichiers dans Téléchargements, étapes dans le tableur (P-137) |
| Contacts : RGPD | Exporter (Art. 20), anonymiser (Art. 17) | Export JSON ; fiche anonymisée, pièces émises gardées |
| Pipeline : déplacer | Glisser une carte d'étape | L'étape change, une activité est tracée |
| Pipeline : fiche | « Ouvrir la fiche » | Coordonnées, étape modifiable, score expliqué (P-144, P-132) |
| Pipeline : score | Changer d'étape | Le score se recalcule |
| Projets : créer | Nouveau projet avec tags | Tags visibles sur la carte (P-123) |
| Projets : filtrer | Filtre par nom et par tag | La liste se restreint (P-123) |
| Projets : Kanban | Déplacer un projet de statut | Le statut change |
| Livrables | Ajouter un livrable au projet | Il apparaît avec son statut |
| Conversations : projet | Rattacher une conversation à un projet | Le tiroir nomme le projet, le filtre et la recherche le trouvent (P-126, P-127) |

## Lot 3 : produire (factures et documents)

| Fonction | Geste | Résultat qui la valide |
|---|---|---|
| Profil de facturation | Adresse, SIRET, régime de TVA | Enregistré, confirmé au pied (B-1347) |
| Devis | Créer un devis à deux lignes | Totaux justes au centime (B-1411) |
| Facture | Convertir le devis en facture | Numéro continu, lignes reprises |
| Avoir | Émettre un avoir | Il se distingue de la facture |
| PDF | Télécharger le PDF d'une facture à 0 % en franchise | « TVA non applicable, art. 293 B du code général des impôts » (P-119) |
| PDF formation | Régime « exonéré formation » | La mention de l'art. 261, 4, 4° a |
| Paiement | Marquer payée | Statut, date de paiement, encaissé de l'Accueil |
| Devises | Facture en CHF | Montant et mentions hors euro |
| Rédiger un document | Nouveau document, générer la trame (modèle local) | Sections créées ; la ligne des Travaux ouvre le document (P-140) |
| Sections | Rédiger, valider, réordonner | Statut et ordre conservés au rechargement |
| Pistes | Ajouter une piste | Elle se garde |
| Export | Markdown, puis Word | Deux fichiers lisibles |
| Office | Demander un DOCX, un XLSX, un PPTX dans le chat | Chaque fichier se télécharge et s'ouvre |
| Fichiers | Indexer un dossier, poser une question | La réponse cite le fichier |

## Lot 4 : comprendre et décider (conversation)

| Fonction | Geste | Résultat qui la valide |
|---|---|---|
| Conversation | Question simple au modèle local | Réponse en streaming, arrêt possible (B-1369) |
| Outils | « Crée le contact … » dans le chat | Carte de confirmation, fiche créée après accord |
| Recherche web | Question d'actualité, recherche active | Sources citées ; coupée, elle ne sort pas |
| Recherche approfondie | Lancer, suivre dans Travaux | Ligne ouvrable, résultat cité |
| Décision | Soumettre une décision au Board | Cinq avis, synthèse, divergences |
| Calculateurs | ROI, seuil de rentabilité | Résultat chiffré cohérent |
| Références juridiques | Question sur une mention légale | Référence citée, relecture humaine rappelée |
| Images | Générer (moteur choisi) | Confirmation avant, historique après |
| Voix | Dictée (locale si disponible) | Texte transcrit dans le composeur |
| Modèles et variables | Insérer un prompt, une variable `{nom}` | Substitution visible avant envoi |
| Commandes | `/contact`, `/rdv`, `{action: aide}` | Exécution déterministe, sans modèle |

## Lot 5 : automatiser et maîtriser

| Fonction | Geste | Résultat qui la valide |
|---|---|---|
| Actions et relances | Lancer une action guidée | Suivi d'exécution, résultat vérifiable |
| Améliorer THÉRÈSE | Lancer une mission sur un dépôt témoin | Plan, diff relu, fusion par l'utilisateur |
| Connecteurs | Installer un préréglage MCP | Outils listés, carte de confirmation à l'usage |
| Skills et commandes | Créer une commande personnalisée | Elle s'exécute |
| Services d'IA | Changer de service, de modèle, d'effort | Le choix tient, l'en-tête le dit |
| Centre de confiance | Ouvrir « Contrôle des données » | Ligne d'état vraie (local, recherche web) (P-118) |
| Données et RGPD | Export global, purge (sur dossier jetable) | Archive produite ; purge confirmée et effective |
| Sauvegarde | Créer puis restaurer une sauvegarde | Données identiques après restauration |
| Sécurité locale | Clés : origine dite (coffre ou environnement) | Aucune clé affichée en clair |
| Coûts et limites | Statistiques après quelques réponses | Consommation mesurée, unité juste |
| Profil | Importer THÉRÈSE.md | Facturation et régime gardés (B-1299, P-119) |
| Personnalisation | Mode contributeur, contraste élevé, réduction des mouvements | Effet visible, gardé au rechargement |
| Mode démo | Activer, parcourir Accueil, palette, Retrouver, Pipeline | Aucun vrai nom nulle part (B-1080, B-1414, B-1419) |
| Mise en route | Dossier vierge : les six étapes | Ollama proposé d'abord (P-111), volet facturation (P-112), sans jargon (P-113) |
| Raccourcis | Chaque raccourci annoncé, depuis un champ et hors champ | Il fait ce que dit la liste (B-1376) |
