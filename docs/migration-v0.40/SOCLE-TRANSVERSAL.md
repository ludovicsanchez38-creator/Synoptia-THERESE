# Socle transversal à préserver

Les 30 capacités décrivent ce que THÉRÈSE sait faire. Elles ne suffisent pas à
garantir la parité de l’application. Cette matrice couvre les comportements qui
traversent plusieurs capacités et risqueraient de disparaître pendant la refonte.

Une capacité n’est considérée comme migrée que si elle respecte aussi les lignes
transversales qui la concernent.

## Conversation et continuité

| Fonction à préserver | Preuve actuelle | Contrat 0.40 |
|---|---|---|
| Création et historique | `chatStore`, `ConversationSidebar` | créer, retrouver, renommer et supprimer sans changer les identifiants backend |
| Recherche et export | recherche sidebar, export MD/DOCX frontend et backend | retrouver puis exporter la conversation courante dans les deux formats |
| Renommage | `chatStore.renameConversation` local | empêcher que la synchronisation backend écrase le nouveau titre |
| Conversation éphémère | `chatStore.ephemeral` | indiquer clairement la non-persistance et ne pas la resynchroniser |
| Synchronisation | `useConversationSync` | retrouver les conversations après relance sans doublon |
| Streaming | `ChatInput`, `MessageBubble`, SSE chat | conserver l’affichage progressif et l’état réel de génération |
| Interruption | `AbortController` dans `ChatInput` | arrêter chat et recherche approfondie, puis marquer le résultat interrompu |
| Reprise après erreur | gestion `ApiError`, health check | garder la demande et proposer une nouvelle tentative sûre |
| Brouillon de saisie | `useAutosave` | ne pas perdre le texte lors d’un changement de canevas |
| Suggestion de saisie | `useGhostText` | rester facultative et ne jamais partir comme demande sans validation |
| Choix du modèle | sélecteur dans `ChatInput`, configuration LLM | afficher le modèle demandé et celui réellement utilisé |
| Usage et incertitude | métadonnées `MessageUsage` et `MessageUncertainty` | rattacher coût, usage et incertitude au bon message |

## Entrées, fichiers et résultats

| Fonction à préserver | Preuve actuelle | Contrat 0.40 |
|---|---|---|
| Pièces jointes multiples | `useFileDrop`, `DropZone`, `ChatInput` | joindre, dédupliquer, retirer et indexer plusieurs fichiers |
| Sélecteur natif | dialogue Tauri dans `ChatInput` | conserver le choix de fichiers et les erreurs de permissions |
| Gestion des fichiers | API `files`, FileBrowser et fichiers de projet | lister, lire, indexer, supprimer et rattacher avec statut réel |
| Fichiers produits | `MessageSkillFile`, `MessageBubble` | afficher chaque fichier réellement créé et permettre son ouverture |
| Rendu de réponse | Markdown et coloration syntaxique | préserver tableaux, code, liens et contenu long |
| Recherche approfondie | `streamDeepResearch` | distinguer recherche normale, approfondie et interruption |
| Entités détectées | `EntitySuggestion`, `contactsStore` | proposer avant sauvegarde et rattacher au bon scope mémoire |
| Résultat d’action | `actionsStore.insertResultInChat` | insérer le résultat backend, y compris partiel ou en erreur |

## Commandes et navigation

| Fonction à préserver | Preuve actuelle | Contrat 0.40 |
|---|---|---|
| Palette de commandes | `CommandPalette`, `actionRegistry` | mêmes actions disponibles au clavier et depuis la conversation |
| Commandes slash | `SlashCommandsMenu` | recherche, navigation clavier et commandes utilisateur conservées |
| Commandes personnalisées | API `commands`, `commands_v3`, composants RFC | création, édition et exécution depuis un point d’entrée explicite |
| Bibliothèque de prompts | `PromptLibrary` | accessible depuis tout canevas, avec insertion sans exécution automatique |
| Raccourcis clavier | `useKeyboardShortcuts`, `ShortcutsModal` | parité macOS/Windows, focus et conflits documentés |
| Retour et Échap | `escapeStack`, `resolveEscape`, historique de navigation | fermer le bon niveau sans perdre le travail en cours |
| Accès aux vues historiques | `actionRegistry`, `navigationStore` | repli vers l’objet ou la vue classique tant que le canevas manque |

## Confiance, sécurité et résilience

| Fonction à préserver | Preuve actuelle | Contrat 0.40 |
|---|---|---|
| Confirmation d’outil | `ToolConfirmationCard`, `toolConfirmationStore` | aucun effet externe avant confirmation explicite |
| Actions gardées | `useGuardedAction` | vérifier préconditions et afficher une erreur exploitable |
| Consentement cloud | `lib/consent`, étape Sécurité de l’onboarding | consentement horodaté et versionné avant transfert |
| État de connexion | `useOnlineStatus`, `useHealthCheck`, `ConnectionStatus` | distinguer réseau, backend et service externe indisponibles |
| Vérité d’exécution | backend `execution_truth` | ne pas annoncer un succès avant confirmation du backend |
| Assainissement | `sanitizeError`, `sanitizeEmailHtml`, sécurité des prompts et chemins | ne pas réinjecter HTML, erreur sensible ou chemin non autorisé |
| Erreur globale | `GlobalErrorBoundary`, notifications | récupérer sans écran blanc et conserver un diagnostic local |
| Authentification locale | initialisation du token dans `App.tsx`, contrôles backend | conserver le démarrage authentifié avant les appels métier |

## Données, sauvegardes et traçabilité

| Fonction à préserver | Preuve actuelle | Contrat 0.40 |
|---|---|---|
| Export global | endpoints `data/export` | proposer un fichier réel et documenter son contenu |
| Import | import conversations et contacts dans `routers/data.py` | aperçu, validation et compte rendu des éléments importés |
| Sauvegardes | création, liste et statut des backups backend | rendre l’état et la date de la dernière sauvegarde visibles |
| Restauration | restauration avec sauvegarde de sécurité et rollback | avertissement, confirmation et vérification après restauration |
| Suppression globale | routes data/RGPD | périmètre exact et irréversibilité avant confirmation |
| Journal et historique | audit et historique d’actions backend | conserver la traçabilité sans la confondre avec les notifications |

Ces fonctions backend ne sont pas toutes raccordées à l’interface actuelle. La
0.40 ne doit donc pas les présenter comme accessibles avant création et recette
du parcours utilisateur.

## Réglages et personnalisation

| Fonction à préserver | Preuve actuelle | Contrat 0.40 |
|---|---|---|
| Premier démarrage | `OnboardingWizard` | profil, provider, sécurité et dossier de travail restent configurables |
| Clés et providers | `LLMTab`, configuration, détection de clés corrompues | ne jamais afficher la clé et signaler les configurations invalides |
| Services connectés | `ServicesTab`, assistants Email, Agenda et CRM | état réel de connexion, reconnexion et déconnexion accessibles |
| Outils et agents | `ToolsPanel`, `AgentsTab` | permissions, statut et limites visibles en mode contributeur |
| Profil métier | `ProfileTab`, `billingProfileStore`, import de profil | conserver les champs sans inventer les valeurs manquantes |
| Dossier de travail | réglages et dialogue Tauri | vérifier existence, droits et portée des fichiers |
| Personnalisation | `personalisationStore` | visibilité des fonctions, comportement IA et accueil partagés entre UI |
| Modes standard/contributeur | `useUXMode`, onglets conditionnels | ne pas masquer une fonction indispensable lors de la migration |
| Mode démonstration | `demoStore`, `useDemoMask` | masquer les données sensibles de façon cohérente sur les nouveaux canevas |

## Accessibilité et application desktop

| Fonction à préserver | Preuve actuelle | Contrat 0.40 |
|---|---|---|
| Thèmes | `accessibilityStore` | clair et sombre cohérents sur coque, cartes et canevas |
| Taille et contraste | `accessibilityStore` | zoom fonctionnel, contraste suffisant et aucun contenu tronqué |
| Mouvement réduit | `MotionConfig`, hooks d’accessibilité | respecter le système et le réglage utilisateur |
| Focus | `useDialogFocusTrap`, skip link | navigation complète au clavier et restitution du focus |
| Démarrage desktop | `SplashScreen`, sidecar Tauri | attendre le backend sans lancer un faux onboarding |
| Fenêtre desktop | plugin window-state, commandes Tauri | restaurer taille, position, maximisation et focus |
| Arrêt propre | gestion du child et nettoyage des processus | arrêter le sidecar et éviter les processus zombies |
| Permissions et CSP | capabilities Tauri et `tauri.conf.json` | préserver le moindre privilège et tester les nouveaux médias/connexions |
| Mise à jour | `UpdateBanner`, plugin updater | vérification, téléchargement, installation et relance hors prototype local |
| Toasts temporaires | `statusStore`, composant Notifications | retour immédiat sans persistance |
| Notifications persistantes | `notificationStore`, `NotificationCenter`, API | lecture/non-lu et lien vers le bon objet |
| Version et À propos | `AboutTab`, configuration Tauri et backend | même version affichée partout |

## Portabilité des services connectés

La recette ne doit pas résumer un domaine à « connecté ». Elle vérifie séparément :

- Email : OAuth, IMAP/SMTP, reconnexion, déconnexion, dossiers, labels,
  signatures, brouillons et classification ;
- Agenda : Google et CalDAV, synchronisation, reconnexion, import/export ICS ;
- Contacts : import/export CSV, JSON et VCF lorsque le parcours correspondant
  est présent ;
- CRM : import, export et synchronisation Google Sheets, avec source de vérité
  indiquée ;
- MCP et navigateur : permissions, secrets, état du service et fermeture propre.

## Éléments à classer avant branchement

Ces surfaces existent dans le dépôt mais leur place exacte dans le catalogue doit
être décidée avant migration :

- automatisation du navigateur via l’API `browser` ;
- intégration OpenClaw dans l’Atelier ;
- construction guidée de commandes via les composants `rfc` ;
- escalade, limites, estimation de coût et incertitude via l’API `escalation` ;
- import et export de profil, synchronisation CRM et renouvellement du
  consentement RGPD.

Elles ne doivent pas être supprimées sous prétexte qu’elles ne correspondent pas
à une carte autonome.
