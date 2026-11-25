# Protocoles des personas proposés au cycle 6

Ces trois fichiers reproduisent la proposition de `731338825`, en attente de la relecture de Ludo. Les protocoles à utiliser pour la candidate sont [dans `tests/protocols/app/personas/`](../../../tests/protocols/app/personas/), au contenu de `0ddefd1a3` pour A1, A2 et A3.

La comparaison des fichiers donne 61 étapes retouchées sur 153, dont 60 titres de niveau « Étape ». Le titre de l’étape A2-26 reste identique avec un corps modifié. La proposition adapte aussi les prérequis des trois fiches au banc navigateur sur le port 17394 et à sa base jetable. Elle actualise des gestes, des libellés et les preuves. Les lignes ci-dessous signalent les contrôles qui perdent une partie de leur portée.

## A1 · Sophie Martin

| Étape | Modification proposée et motif |
|---|---|
| 3 | Décrire le bouton de démarrage et le nouveau formulaire à nom complet. Les vérifications du délai, de l’animation et de la progression disparaissent. |
| 5 | Saisir un nom complet et un rôle dans les champs actuels. Le contrôle explicite de l’activation du bouton après saisie disparaît. |
| 6 | Renommer LLM en Service d’IA et constater la procédure repliée quand Claude est déjà prêt sur le banc. L’état sans clé et le bouton Passer sortent de ce contrôle. |
| 7 | Employer Configurer plus tard, le libellé du geste qui mène à Sécurité. Le parcours sans service obligatoire reste couvert. |
| 9 | Vérifier l’état sans dossier et le bouton Continuer sans dossier, qui remplacent l’ancien chemin présélectionné et les deux boutons de poursuite. |
| 10 | Lire le récapitulatif et cliquer sur Commencer, le libellé actuel. L’ouverture de l’application suffit dans la proposition. Le champ de chat prêt et le marqueur de fin ne sont plus vérifiés ici. |
| 12 | Examiner l’avertissement et le composeur désactivé sans service, comme observé sur le banc. Le scénario d’envoi suivi d’une erreur disparaît. |
| 14 | Employer Service d’IA dans Paramètres et repérer la grille et Autres, selon le sélecteur actuel. Le contrôle de chaque champ de clé disparaît. |
| 15 | Contrôler le champ d’OpenAI sans clé et les indicateurs des services déjà configurés. La vérification ne couvre plus tous les champs ni leurs exemples de format. |
| 17 | Revenir au composeur et relire l’explication affichée selon l’état du service. La persistance de la bulle d’erreur, le focus et l’animation de fermeture sortent de l’étape. |
| 24 | Ouvrir les contacts de la Mémoire depuis l’espace de travail ou sa commande et repérer le filtre documenté. La vue Projets est accessible séparément. |
| 31 | Vérifier que Jean Dupont, créé en Mémoire lors d’une étape précédente, est déjà dans Pipeline. Le scénario de Pipeline vide disparaît. |
| 32 | Créer une deuxième fiche dans Pipeline. La saisie d’un montant, désormais située dans les devis pour ce parcours, sort de l’étape. |
| 39 | Employer l’horloge du banc au lieu d’une date de mars 2026. Le mois et le jour courant restent vérifiés. L’agenda vide devient facultatif. |
| 45 | Préparer le Board et vérifier l’accord cloud puis la confirmation, qui précèdent le lancement. Le démarrage des cinq conseillers ou l’erreur après soumission sortent de l’étape. |
| 48 | Suivre la rubrique Sécurité et confidentialité et vérifier le téléchargement JSON. Les critères de contenu et le message de confirmation disparaissent de l’attendu. |

## A2 · Marc Lefèvre

| Étape | Modification proposée et motif |
|---|---|
| 1 | Ouvrir Ma journée avec un profil configuré et relever le résumé actuel. Le thème suit le banc. Le texte de salutation et l’inventaire précis des compteurs disparaissent. |
| 2 | Lire le brief et les actions selon les données présentes. Les compteurs à zéro, l’accès rapide au chat et les critères de lisibilité explicites sortent de l’attendu. |
| 11 | Filtrer les titres après le renommage du compte rendu avec « Durand ». Le compte rendu doit désormais apparaître. L’insensibilité à la casse n’est plus vérifiée. |
| 12 | Ouvrir Pipeline depuis l’espace de travail et suivre ses huit colonnes actuelles. Les critères sur le thème et le bouton d’ajout disparaissent de l’étape. |
| 15 | Adapter la fiche rapide aux champs présents. La saisie de l’adresse passe par Mémoire et celle des notes par le journal d’activités. |
| 16 | Vérifier Célia Durand dans Contact après sauvegarde, selon les données et le libellé actuels. La preuve est la fiche visible. |
| 17 | Passer en Proposition par Étape dans la fiche. La nouvelle colonne et l’enregistrement restent attendus. Le glisser-déposer sort de la recette. |
| 21 | Créer un brouillon via Nouveau devis ou facture et choisir Célia Durand. Le numéro est attendu après sauvegarde, en accord avec le parcours observé. |
| 25 | Exiger la conversion et sa confirmation. Le devis est Converti et la facture créée en brouillon reçoit son numéro définitif à l’émission. |
| 26 | Compléter les mentions émetteur et l’adresse du destinataire pour obtenir le PDF. Le contrôle se concentre sur le contenu local, avec une portée réduite sur les mentions légales et la restitution du fichier. |
| 29 | Utiliser un compte simulé pour ouvrir le formulaire Nouveau message sur le banc. La réception des messages récents et l’envoi sortent de la vérification. |
| 31 | Afficher les sept jours et les créneaux de la semaine calculée d’après le banc. L’hypothèse d’un agenda vide et la date de mars 2026 disparaissent. |
| 33 | Avancer d’un mois depuis la période courante et lire le rendez-vous si applicable. Le retour au mois initial et l’absence de rechargement ne sont plus demandés. |
| 38 | Modifier l’état par le formulaire ouvert depuis Liste, puis vérifier les Colonnes. La tâche témoin reste dans À faire. Le glisser-déposer sort du parcours. |
| 39 | Saisir la question et atteindre la confirmation du Board, avec accord cloud si nécessaire. La délibération et l’indicateur de progression sortent de ce contrôle sur le banc à un seul compte. |
| 43 | Simuler un refus 401 sur le transport Anthropic et lire l’erreur du chat. Le contrôle dans Paramètres et la disponibilité du fournisseur précédent disparaissent. |

## A3 · Léa

| Étape | Modification proposée et motif |
|---|---|
| 1 | Démarrer avec le profil, un contact et une tâche fictifs, puis lire le brief. Le contrôle des rendez-vous, des factures et de l’absence d’erreur console disparaît. |
| 2 | Lire la date, le résumé et la disponibilité des sources dans le brief actuel. Le contrôle des valeurs exactes des indicateurs numériques disparaît. |
| 5 | Changer de modèle via la puce du composeur avec les modèles du service actif. La couverture passe de trois services à un. La conservation du contexte ne figure plus dans l’attendu. |
| 8 | Provoquer une liste de trois titres en gras pour rendre la recette jouable au premier échange. La couverture Markdown perd le titre de niveau 1, la citation et les vérifications sémantiques et de thème. |
| 10 | Ouvrir Devis et factures par la commande de recherche actuelle et distinguer Facturer un client. Les contrôles de transition, de double-clic et de présence des factures sortent de l’étape. |
| 12 | Parcourir les neuf rubriques actuelles, dont Accessibilité et affichage, en mode Contributeur. L’accessibilité et le contenu distinct restent attendus. La fluidité sans rechargement n’est plus vérifiée. |
| 13 | Relever Claude actif avec sa clé et lire les états des autres services, selon le banc à un compte. La configuration simultanée de trois fournisseurs n’est plus vérifiée. |
| 14 | Choisir Haiku, revenir à Sonnet et envoyer un tour avec l’effort Faible. Le contrôle s’étend à l’effort et à l’usage effectif, tout en passant de trois fournisseurs à un. |
| 17 | Employer le chemin Avancé > Comportement au lancement en mode Contributeur et le libellé actuel de l’interrupteur. Son effet au prochain lancement reste attendu. |
| 19 | Fermer après enregistrement dans les rubriques, qui gèrent leurs propres confirmations. Le toast global et la vérification conjointe des deux préférences disparaissent. |
| 20 | Ouvrir les contacts de Mémoire depuis l’espace de travail avec un contact fictif. Le minimum de trois contacts sort de l’attendu. |
| 24 | Ouvrir Nouveau projet et saisir le titre. La création effective est déplacée à l’étape 25. Description, présence dans la liste et toast disparaissent de l’étape 24. |
| 25 | Associer un contact pendant la création, selon le formulaire actuel. La relation sauvegardée reste attendue. La présence inverse du projet dans la fiche contact n’est plus vérifiée. |
| 26 | Employer Pipeline et les huit colonnes actuelles avec leurs compteurs. Les anciens noms de colonnes disparaissent. |
| 28 | Créer une fiche commerciale puis passer par Nouvelle prestation pour le montant. Le scénario d’un lead avec montant et étape déjà attribués disparaît. |
| 29 | Passer de Contact à Proposition par le champ Étape. Le changement de colonne reste visible. La mise à jour des compteurs et la persistance ne sont plus des critères explicites. |
| 30 | Lire le score calculé affiché sur la carte, selon l’écran observé. L’attribution d’un score ou d’une priorité, sa persistance et le tri disparaissent. |
| 32 | Ouvrir une facture directement via le formulaire actuel. Le numéro définitif est attendu à l’émission et non au stade du formulaire. |
| 33 | Utiliser trois prestations fictives adaptées à la recette et vérifier les champs indépendants. Les trois quantités valent un, ce qui réduit le contrôle du calcul sur une quantité supérieure. |
| 34 | Contrôler 830 € HT, 166 € de TVA et 996 € TTC avec le nouveau jeu d’essai. La mise à jour à chaque modification et le format à deux décimales sortent de l’attendu. |
| 36 | Enregistrer Envoyée et vérifier le numéro attribué et le statut. La date d’envoi, la couleur du badge et le verrouillage partiel ne sont plus vérifiés. |
| 44 | Lire les échéances en vue Liste parce que le banc ne présente aucune commande de tri. L’ordre croissant, l’indicateur et le rang des tâches sans date sortent de la vérification. |
| 45 | Atteindre la confirmation après accord cloud et lire ce qui sera partagé. Les cinq départs et leurs indicateurs de progression sortent du contrôle. |
| 48 | Relever « PDF Bientôt » désactivé dans Historique, selon l’état actuel. Le geste d’export ou de copie est remplacé par un constat de disponibilité. |
| 49 | Demander un DOCX au contenu précisé, confirmer sa création et vérifier la carte Télécharger. Le dialogue d’enregistrement est déplacé à la recette native Tauri. |
| 50 | Demander un XLSX pour un client avec brouillons et statut, confirmer et vérifier la carte Télécharger. Le dialogue d’enregistrement est déplacé à la recette native Tauri. |
| 55 | Télécharger l’export depuis Sécurité et confidentialité et l’ouvrir hors réseau. Le contrôle de complétude par catégorie et le toast de confirmation disparaissent. |
| 56 | Simuler le refus 401 et lire l’erreur dans le chat. Le test de rejet lors de la vérification de la clé dans Paramètres, le coffre et le maintien du fournisseur précédent sortent de la recette. |
| 59 | Simuler l’échec de synchronisation et vérifier que Séance A reste visible. Le libellé précis de l’avertissement, son horodatage et sa disparition après le retour du service ne sont plus vérifiés. |
