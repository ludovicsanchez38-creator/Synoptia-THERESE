# Couverture fonctionnelle des 30 capacités

Cette matrice relie le catalogue visuel du prototype au code existant. « Existant »
signifie qu’un composant, une API ou un service correspondant a été identifié dans
le dépôt. Cela ne vaut pas validation complète du parcours 0.40.

Légende des phases : L = lecture réelle, B = brouillon/édition, E = effet externe,
S = stabilisation.

## Raccordements 0.40 déjà réalisés localement

| Capacité | Raccordement vérifié | Limite encore ouverte |
|---|---|---|
| Brief du jour | `/api/dashboard/today`, tri des urgences, états chargement/vide/erreur et accès à Agenda, Tâches, Factures, CRM ou Relances | les règles de priorité restent celles du backend, sans reclassement inventé par la coque |
| Contacts et mémoire | `contactsStore`, fiches réelles en lecture seule, recherche locale, notes, tags et repli vers la Mémoire complète | recherche sémantique et édition encore portées par la vue classique |
| Email | comptes Gmail/IMAP réels, liste et détail normalisés, génération de réponse, texte modifiable et création de brouillon confirmée | aucun envoi depuis la 0.40 ; résumé, signatures, labels et gestion des comptes restent dans la vue classique |
| Rendez-vous et Agenda | calendriers local, Google et CalDAV agrégés sans création implicite, événements à 90 jours, participants, contacts reliés par email exact et activités CRM ; création d’événement et note CRM en deux étapes | aucun email n’est utilisé comme source ; modification, suppression, sync détaillée et ICS restent dans la vue classique |
| Devis et factures | liste et détail réels, contacts et devise réels, profil émetteur explicite, création confirmée d’un devis brouillon, PDF local et protection contre le double clic | conversion, paiement, suppression et envoi restent hors du canevas ; l’action d’envoi est masquée tant que le backend retourne 501 |
| Board de décision | historique et détail réels, formulaire confirmé, progression SSE, conseillers, synthèse et sauvegarde relue ; Ollama strict en souverain ; sources web, provider, modèle et usage persistés | pas de reprise en arrière-plan, d’export PDF ni de transformation en plan d’action |
| Atelier d’agents | historique `AgentTask`, préflight dépôt/modèles/permissions, SSE Katia-Zézette, plan, phases, sorties agents, tests, explication, branche, commit et diff persistés ; annulation backend et revue confirmée | coût de mission non mesuré ; OpenClaw et Action Agents restent hors du canevas initial |
| Livrables et suivi client | index des projets puis chargement ciblé du contact, des livrables, tâches ouvertes et facturation ; filtre par statut, échéances, réponses obsolètes ignorées et états partiels séparés | la facture est reliée au contact du projet, pas au livrable ; limites visibles à 200 projets, 100 documents et 1 000 tâches ; aucune mutation depuis ce canevas |
| Centre des capacités | inventaire exact de 30 entrées ; chaque carte ouvre un canevas réel, une vue classique, une action, un réglage, une reprise explicite dans le chat ou les calculateurs | plusieurs fonctions restent portées par la vue classique, mais aucune carte n’est sans débouché ni remplacée par un faux résultat |
| Calculateurs | canevas réel pour ROI, ICE, RICE, VAN et seuil de rentabilité ; formule et hypothèses visibles, validation locale et backend, résultat fini exigé, aucune persistance ni appel LLM | devise EUR fixe dans cette première surface ; pas d’historique ni de comparaison multi-scénarios |
| Images | statut provider, historique, aperçu, téléchargement et génération réelle en deux étapes | l’édition par image de référence n’est pas exposée dans ce premier studio |
| Relances et alertes | file réelle des relances email, filtres, modification d’échéance et note, clôture, réouverture et suppression confirmée | création depuis le détail d’un email ; pas de moteur autonome de relance |
| Voix et transcription | import de fichier audio, moteur local/cloud indiqué, confirmation, transcription éditable, reprise dans le chat et synthèse locale Piper | la capture micro historique reste dans le chat ; disponibilité des modèles locaux dépend de l’installation |
| Données et RGPD | export global exhaustif sans secrets, suppression globale confirmée, création, liste, restauration et suppression des sauvegardes | les journaux d’audit et sauvegardes sont conservés lors de la purge et ce périmètre est annoncé |

Ces raccordements ne disposent d’aucune donnée de démonstration de secours. Une
source indisponible produit un état d’erreur explicite et une possibilité de
réessayer ou d’ouvrir la vue classique.

## Niveaux de raccordement audités

Les lignes non mentionnées ci-dessous possèdent un socle UI et API identifié,
mais leur parité 0.40 reste à tester. Ces exceptions doivent être visibles dans
l’interface tant qu’elles ne sont pas résolues :

| Capacité | État actuel vérifié | Règle de migration |
|---|---|---|
| Relances et alertes | canevas CRUD raccordé aux relances email réelles | ne pas présenter cette file comme une automatisation autonome |
| Devis et factures | consultation, brouillon et PDF raccordés ; envoi HTTP 501 | masquer l’envoi et conserver les autres mutations dans la vue dédiée |
| Images | studio raccordé à la génération, l’historique et au téléchargement | ne pas annoncer l’édition par référence tant qu’elle n’est pas exposée |
| Voix et transcription | import, transcription local/cloud et synthèse locale raccordés | afficher le moteur et confirmer avant toute transmission cloud |
| Calculateurs | API et canevas déterministe raccordés ; cinq moteurs testés | conserver les formules visibles et refuser tout résultat numérique non fini |
| Références juridiques | injection d’un corpus par mots-clés, sans canevas autonome | parler de corpus vérifié, pas d’un RAG autonome |
| Actions guidées | expérimental | auditer contexte, persistance et vérité d’exécution |
| Données et RGPD | export, purge et sauvegardes globaux raccordés ; RGPD contact conservé dans le CRM | garder les deux périmètres distincts et explicites |

## Organiser mon quotidien

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Brief du jour | `dashboard`, `notifications`, `follow_ups` | synthèse quotidienne dans conversation et canevas | L | agréger sans inventer de priorité |
| Email | composants Email, API `email` | liste et lecture raccordées ; brouillon généré ou manuel, modifiable et confirmé | L/B | aucun envoi exposé dans la 0.40 ; distinguer brouillon et message envoyé |
| Agenda | composants et API `calendar` | liste réelle, préparation factuelle, proposition confirmée et note CRM confirmée | L/B/E | destination, provider, compte, fuseau et invités visibles ; aucune mutation à l’ouverture |
| Tâches | composants, store et API `tasks` | liste contextuelle, création et complétion | L/B/E | éviter les doublons issus du chat |
| Relances et alertes | API `follow_ups`, `notifications` | file d’attention explicable | L/B/E | afficher la règle et l’échéance source |

## Développer mon activité

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Contacts et mémoire | composants Memory, API `memory`, contexte et recherche | fiche liée à la conversation | L/B | conserver scopes et suppression confirmée |
| Pipeline commercial | composants CRM, API `crm` | pipeline synthétique et fiche opportunité | L/B/E | source Sheets ou locale clairement indiquée |
| Projets | ProjectsPanel/Kanban, mémoire | canevas projet avec contacts, tâches et budget | L/B | mêmes identifiants que la vue classique |
| Devis et factures | composants, store, API `invoices` | liste et détail raccordés ; devis brouillon structuré, calculé et confirmé ; PDF ouvert localement | L/B | envoi HTTP 501 masqué ; conversion, paiement et suppression gardés hors du canevas initial |
| Livrables et suivi client | `DeliverablesWorkspaceCanvas`, CRM étendu, projets, tâches et facturation | lecture unifiée par projet : promesse, livraison, reste à faire et facturation du contact | L | la facture n’a pas de `project_id` ni de `deliverable_id` ; ne pas présenter l’association au contact comme une liaison au livrable |

## Créer et produire

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Atelier documentaire | `DocumentWorkspace`, API `documents` | trame et sections éditables dans un canevas | L/B | préserver versions et ordre des sections |
| Word, PowerPoint et Excel | `skills`, `workspace_tools` | demande, aperçu et fichiers produits | B/E | afficher tous les fichiers réellement créés |
| Images | API `images`, `image_generator`, `ImagesWorkspaceCanvas` | galerie, génération confirmée, aperçu et téléchargement | L/B/E | référence image non exposée |
| Voix et transcription | API et composants `voice`, `VoiceWorkspaceCanvas` | dictée historique, import audio, transcription exploitable et Piper local | B | moteur visible et confirmation avant transfert cloud |
| Modèles et variables | PromptLibrary, API `prompts`, `variables` | recherche, insertion et édition de modèle | L/B | aperçu des variables avant exécution |

## Comprendre et décider

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Recherche web | `web_search`, `deep_research`, navigateur | résultats et sources dans le canevas | L | citations vérifiables et date visible |
| Fichiers et connaissances | FileBrowser, API `files`, Qdrant | sources locales, extraits et contexte RAG | L/B | distinguer indexé, lu et simplement repéré |
| Board de décision | composants et API `board` | historique, question confirmée, progression, regards, divergences et synthèse raccordés | L/B/E | succès après relecture locale ; aucun repli cloud en souverain ; pas de reprise en arrière-plan |
| Calculateurs | API, service `calculators` et `CalculatorWorkspaceCanvas` | cinq formulaires déterministes avec formule, hypothèses et résultat vérifiable | L/B | aucune estimation LLM ; validation des bornes, protection double clic et refus des résultats non finis |
| Références juridiques | corpus déterministe injecté dans le chat | sources et incertitudes dans le canevas | L/S | pas de RAG ni de parcours autonome à ce stade |

## Automatiser et déléguer

| Capacité | Socle identifié | Cible 0.40 | Phase | Point de contrôle |
|---|---|---|---|---|
| Actions et relances | ActionPanel et API `actions`, plus canevas CRUD des relances email | relances raccordées ; actions autonomes encore expérimentales | L/B/E | ne pas confondre échéance email et exécution autonome |
| Atelier d’agents | API `agents`, `action_agents` | swarm de code raccordé : mission, historique reconstructible, plan SSE, agents, tests, explication, artefacts Git et revue ; autres moteurs différés | L/B/E | worktree isolé, dépôt propre, seconde confirmation et relecture backend avant succès |
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
| Personnalisation | mode UX, réglages avancés et accessibilité persistants | accès direct au mode standard/contributeur, au démarrage et à l’accessibilité réellement consommés | L/B | ne pas exposer les préférences backend `llm_behavior` et `feature_visibility` tant que l’application ne les consomme pas |

## Priorité d’intégration

Le premier incrément utile doit connecter quatre capacités représentatives :

1. Contacts et mémoire pour une lecture locale.
2. Email pour un brouillon puis un effet externe confirmé.
3. Devis et factures pour un objet métier structuré.
4. Board pour un canevas long et asynchrone.

Ce quatuor teste les principaux contrats sans attendre la migration des 30
capacités. Les autres gardent un repli vers la vue classique tant que leur
adaptateur n’est pas validé.

État local : la lecture « Contacts et mémoire », le brief du jour, Email,
Rendez-vous, « Devis et factures », le Board, le swarm de code de l’Atelier et
les cinq calculateurs sont raccordés. Les parcours sensibles exigent une
confirmation explicite. Le centre des capacités route les autres entrées vers
leur surface existante sans exécution automatique et sans donnée sensible dans
l’URL. Les 30 cartes ont désormais un débouché déterministe ; cette couverture
de navigation ne signifie pas que chaque fonction historique possède déjà son
propre canevas 0.40.
