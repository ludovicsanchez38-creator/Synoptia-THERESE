# Couverture fonctionnelle des 30 capacités

Cette matrice relie le catalogue visuel du prototype au code existant. « Existant »
signifie qu’un composant, une API ou un service correspondant a été identifié dans
le dépôt. Cela ne vaut pas validation complète du parcours 0.40.

Légende des phases : L = lecture réelle, B = brouillon/édition, E = effet externe,
S = stabilisation.

## Raccordements 0.40 déjà réalisés localement

| Capacité | Raccordement vérifié | Limite encore ouverte |
|---|---|---|
| Brief du jour | `/api/dashboard/today`, tri des urgences, états chargement/vide/erreur et repli vers Agenda, Tâches, Factures, CRM ou Accueil | notifications et relances détaillées encore accessibles par les vues classiques |
| Contacts et mémoire | `contactsStore`, fiches réelles en lecture seule, recherche locale, notes, tags et repli vers la Mémoire complète | recherche sémantique et édition encore portées par la vue classique |
| Email | comptes Gmail/IMAP réels, liste et détail normalisés, génération de réponse, texte modifiable et création de brouillon confirmée | aucun envoi depuis la 0.40 ; résumé, signatures, labels et gestion des comptes restent dans la vue classique |

Ces raccordements ne disposent d’aucune donnée de démonstration de secours. Une
source indisponible produit un état d’erreur explicite et une possibilité de
réessayer ou d’ouvrir la vue classique.

## Niveaux de raccordement audités

Les lignes non mentionnées ci-dessous possèdent un socle UI et API identifié,
mais leur parité 0.40 reste à tester. Ces exceptions doivent être visibles dans
l’interface tant qu’elles ne sont pas résolues :

| Capacité | État actuel vérifié | Règle de migration |
|---|---|---|
| Relances et alertes | partiel : synthèse Accueil + backend, sans client CRUD dédié | lecture ou repli, aucune promesse d’édition complète |
| Devis et factures | partiel : ouverture PDF à terminer, envoi HTTP 501 | masquer l’envoi et garder le téléchargement manuel |
| Images | partiel : génération et API d’historique, sans galerie raccordée | ne pas annoncer l’historique comme accessible |
| Voix et transcription | UI + API pour transcription, synthèse vocale backend seulement | ne migrer que la transcription validée |
| Calculateurs | API uniquement | créer un canevas ou déclencher par chat avant de déclarer la parité |
| Références juridiques | injection d’un corpus par mots-clés, sans canevas autonome | parler de corpus vérifié, pas d’un RAG autonome |
| Actions et relances | expérimental | auditer contexte, persistance et vérité d’exécution |
| Données et RGPD | partiel : RGPD contact raccordé, sauvegardes globales surtout backend | séparer RGPD contact et sauvegarde de l’application |

## Organiser mon quotidien

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Brief du jour | `dashboard`, `notifications`, `follow_ups` | synthèse quotidienne dans conversation et canevas | L | agréger sans inventer de priorité |
| Email | composants Email, API `email` | liste et lecture raccordées ; brouillon généré ou manuel, modifiable et confirmé | L/B | aucun envoi exposé dans la 0.40 ; distinguer brouillon et message envoyé |
| Agenda | composants et API `calendar` | prochain rendez-vous, détail et proposition d’événement | L/B/E | confirmer calendrier, date et invités |
| Tâches | composants, store et API `tasks` | liste contextuelle, création et complétion | L/B/E | éviter les doublons issus du chat |
| Relances et alertes | API `follow_ups`, `notifications` | file d’attention explicable | L/B/E | afficher la règle et l’échéance source |

## Développer mon activité

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Contacts et mémoire | composants Memory, API `memory`, contexte et recherche | fiche liée à la conversation | L/B | conserver scopes et suppression confirmée |
| Pipeline commercial | composants CRM, API `crm` | pipeline synthétique et fiche opportunité | L/B/E | source Sheets ou locale clairement indiquée |
| Projets | ProjectsPanel/Kanban, mémoire | canevas projet avec contacts, tâches et budget | L/B | mêmes identifiants que la vue classique |
| Devis et factures | composants, store, API `invoices` | formulaire, aperçu PDF, statut et actions | L/B/E | envoi indisponible et ouverture PDF à terminer |
| Livrables et suivi client | `DeliverablesList`, CRM étendu | promesse, livraison, facture et reste à faire | L/B/E | statut réel, pas d’inférence présentée comme fait |

## Créer et produire

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Atelier documentaire | `DocumentWorkspace`, API `documents` | trame et sections éditables dans un canevas | L/B | préserver versions et ordre des sections |
| Word, PowerPoint et Excel | `skills`, `workspace_tools` | demande, aperçu et fichiers produits | B/E | afficher tous les fichiers réellement créés |
| Images | API `images`, `image_generator` | galerie, référence, génération et résultat | L/B/E | historique API non raccordé à une galerie |
| Voix et transcription | API et composants `voice` | dictée, import audio, transcription exploitable | B | consentement micro et état d’enregistrement |
| Modèles et variables | PromptLibrary, API `prompts`, `variables` | recherche, insertion et édition de modèle | L/B | aperçu des variables avant exécution |

## Comprendre et décider

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Recherche web | `web_search`, `deep_research`, navigateur | résultats et sources dans le canevas | L | citations vérifiables et date visible |
| Fichiers et connaissances | FileBrowser, API `files`, Qdrant | sources locales, extraits et contexte RAG | L/B | distinguer indexé, lu et simplement repéré |
| Board de décision | composants et API `board` | question, regards, divergences, synthèse, historique | L/B/E | progression et réponses réellement reçues |
| Calculateurs | API et service `calculators`, sans UI dédiée | hypothèses, formule, résultat modifiable | L/B | créer un parcours avant de déclarer la capacité accessible |
| Références juridiques | corpus déterministe injecté dans le chat | sources et incertitudes dans le canevas | L/S | pas de RAG ni de parcours autonome à ce stade |

## Automatiser et déléguer

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Actions et relances | ActionPanel et API `actions`, état expérimental | cadrage, validation, progression, résultat | L/B/E | auditer contexte, persistance et résultat avant migration |
| Atelier d’agents | API `agents`, `action_agents` | mission, plan, agents, artefacts et revue | L/B/E | aucune application implicite des changements |
| Connecteurs MCP | ToolsPanel, API et service `mcp` | catalogue, permissions et outils disponibles | L/B/E | permissions et secrets avant connexion |
| Skills et commandes | API `skills`, `commands`, `commands_v3` | découverte, paramétrage et lancement | L/B/E | origine et portée de la commande visibles |

## Maîtriser THÉRÈSE

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Modèles et providers | LLMTab, config LLM | choix, résolution et repli expliqués | L/B | modèle réellement utilisé, pas seulement préféré |
| Données et RGPD | DataTab, PrivacyTab, API `data` et `rgpd` | inventaire, export et suppression guidée | L/B/E | périmètre et irréversibilité avant confirmation |
| Sécurité locale | SecurityStep, chiffrement et sécurité des chemins | vue claire du stockage et des transmissions | L/S | claims techniques validés avant affichage public |
| Coûts, limites et performance | LimitsTab, PerformanceTab, token tracker | consommation et limites par usage | L/B | préciser ce qui est mesuré ou seulement estimé |
| Profil et espace de travail | ProfileTab, onboarding, `user_profile` | identité, dossier de travail et contexte | L/B | aucune valeur métier inventée |
| Personnalisation | réglages, API `personalisation`, accessibilité | comportement, apparence et capacités activées | L/B | réglages partagés entre les deux interfaces |

## Priorité d’intégration

Le premier incrément utile doit connecter quatre capacités représentatives :

1. Contacts et mémoire pour une lecture locale.
2. Email pour un brouillon puis un effet externe confirmé.
3. Devis et factures pour un objet métier structuré.
4. Board pour un canevas long et asynchrone.

Ce quatuor teste les principaux contrats sans attendre la migration des 30
capacités. Les autres gardent un repli vers la vue classique tant que leur
adaptateur n’est pas validé.

État local : la lecture « Contacts et mémoire », le brief du jour et le parcours
Email sont raccordés. Email couvre la liste, le détail, la génération, l’édition
et la création confirmée d’un brouillon sans exposer l’envoi. Le prochain contrat
représentatif à traiter est « Devis et factures ».
