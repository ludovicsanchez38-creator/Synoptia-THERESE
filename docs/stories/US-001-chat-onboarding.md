Excellent! Maintenant j'ai une vision complète. Laissez-moi créer le markdown avec toutes les user stories:

# User Stories - THÉRÈSE v2 (Modules Chat & Onboarding)

## Module CHAT

### US-001 : Afficher la liste des messages de conversation
**En tant que** solopreneur/TPE  
**Je veux** voir tous les messages échangés dans la conversation courante  
**Afin de** suivre l'historique de mes échanges avec THÉRÈSE

**Critères d'acceptation :**
- [ ] Les messages s'affichent avec alternance user/assistant
- [ ] Le scroll automatique reste au bas lors de nouveaux messages
- [ ] Le mode démo masque le contenu sensible (maskText)
- [ ] Les entités détectées apparaissent sous forme de suggestions

**Composants :** MessageList.tsx, MessageBubble.tsx, TypingIndicator.tsx  
**data-testid :** chat-message-list, chat-message-item

---

### US-002 : Envoyer un message texte au chat
**En tant que** solopreneur/TPE  
**Je veux** envoyer un message texte en appuyant sur Entrée  
**Afin de** communiquer avec THÉRÈSE et obtenir des réponses

**Critères d'acceptation :**
- [ ] Entrée envoie le message, Maj+Entrée crée une nouvelle ligne
- [ ] Le message s'ajoute immédiatement à la conversation
- [ ] L'indicateur de saisie "Réflexion..." s'affiche pendant le traitement
- [ ] Le message est sauvegardé brouillon avant envoi (autosave)

**Composants :** ChatInput.tsx, ChatLayout.tsx  
**data-testid :** chat-message-input, chat-send-btn

---

### US-003 : Annuler la génération d'une réponse
**En tant que** solopreneur/TPE  
**Je veux** arrêter le traitement en cours d'une réponse  
**Afin de** relancer rapidement une autre requête ou corriger ma demande

**Critères d'acceptation :**
- [ ] Un bouton carré apparaît pendant le streaming
- [ ] Cliquer arrête immédiatement la génération (cancellation token)
- [ ] Le message incomplète est conservé en historique
- [ ] La conversation redevient prête pour une nouvelle saisie

**Composants :** ChatInput.tsx, chat.py (router backend)  
**data-testid :** chat-cancel-btn

---

### US-004 : Insérer un fichier dans le chat
**En tant que** solopreneur/TPE  
**Je veux** glisser-déposer ou sélectionner un fichier avant d'envoyer un message  
**Afin de** faire analyser des documents par THÉRÈSE avec le contexte du chat

**Critères d'acceptation :**
- [ ] Zone de drop-zone visible lors du survol
- [ ] Les fichiers s'ajoutent via drag-drop ou bouton d'ajout
- [ ] Les fichiers dupliqués ne s'ajoutent pas deux fois
- [ ] L'indexation commence automatiquement (isIndexing state)
- [ ] Les fichiers apparaissent comme "chips" avant envoi

**Composants :** ChatInput.tsx, DropZone.tsx (FileChip)  
**data-testid :** chat-attach-btn

---

### US-005 : Afficher le tableau de bord "Ma journée" au lancement
**En tant que** solopreneur/TPE  
**Je veux** voir un dashboard avec mes tâches et rendez-vous du jour au lancement  
**Afin de** commencer ma journée avec une vue d'ensemble

**Critères d'acceptation :**
- [ ] Dashboard s'affiche si la conversation est vide
- [ ] Un bouton "Continuer" lance une conversation normale
- [ ] La préférence "skip-dashboard" est mémorisée
- [ ] Le composant DashboardToday est lazy-loadé

**Composants :** ChatLayout.tsx, DashboardToday.tsx (composant home)  
**data-testid :** dashboard-dismiss-btn

---

### US-006 : Afficher l'indicateur de mode hors ligne
**En tant que** solopreneur/TPE  
**Je veux** savoir si ma connexion est perdue  
**Afin de** comprendre pourquoi les messages ne s'envoient pas

**Critères d'acceptation :**
- [ ] Une banneau jaune s'affiche en haut du chat quand offline
- [ ] Le message indique "Mode hors ligne - données sauvegardées localement"
- [ ] Les boutons d'envoi restent grisés (isDisabled)
- [ ] L'indicateur disparaît dès que la connexion revient

**Composants :** ChatLayout.tsx, ConnectionStatus.tsx  
**data-testid :** offline-banner

---

### US-007 : Sauvegarder automatiquement le brouillon de message
**En tant que** solopreneur/TPE  
**Je veux** que mon texte en cours soit sauvegardé automatiquement  
**Afin de** ne pas perdre mon contenu si THÉRÈSE se ferme accidentellement

**Critères d'acceptation :**
- [ ] Le brouillon s'enregistre toutes les 5 secondes (autosave)
- [ ] Un label "Sauvegardé" ou "Sauvegardé il y a 30s" s'affiche
- [ ] Le brouillon se restaure au rechargement de la conversation
- [ ] Le brouillon est spécifique à chaque conversation

**Composants :** ChatInput.tsx (SavedIndicator, useAutosave hook)  
**data-testid :** saved-indicator

---

### US-008 : Enregistrer une réponse comme commande slash personnalisée
**En tant que** solopreneur/TPE  
**Je veux** sauvegarder une réponse utile de THÉRÈSE comme commande `/moncommande`  
**Afin de** la réutiliser rapidement par la suite

**Critères d'acceptation :**
- [ ] Un bouton "Enregistrer" apparaît sur les messages assistant non-streaming
- [ ] Une modale s'ouvre pour nommer et configurer la commande
- [ ] La commande devient disponible dans le menu `/`
- [ ] L'icône et la catégorie sont mémorisées

**Composants :** MessageBubble.tsx, CreateCommandForm.tsx  
**data-testid :** save-as-command-btn

---

### US-009 : Copier le contenu d'un bloc de code
**En tant que** solopreneur/TPE  
**Je veux** copier le code proposé par THÉRÈSE en un clic  
**Afin de** l'utiliser directement dans mon IDE ou terminal

**Critères d'acceptation :**
- [ ] Un bouton "Copier" s'affiche en haut à droite du bloc
- [ ] Le texte complet du code est copié dans le presse-papiers
- [ ] Le bouton change en "Copié" pendant 2 secondes
- [ ] La syntaxe colorée s'affiche correctement (hljs Light)

**Composants :** MessageBubble.tsx (CodeBlock component)  
**data-testid :** code-copy-btn

---

### US-010 : Afficher les suggestions d'entités détectées
**En tant que** solopreneur/TPE  
**Je veux** voir les contacts ou projets automatiquement détectés dans la réponse  
**Afin de** les sauvegarder rapidement en mémoire

**Critères d'acceptation :**
- [ ] Les suggestions apparaissent après chaque message assistant
- [ ] Chaque entité montre le type (contact/projet), le nom et un % de confiance
- [ ] Un bouton permet de sauvegarder ou ignorer chaque entité
- [ ] Les entités disparaissent après action (save ou ignore)

**Composants :** EntitySuggestion.tsx, MessageList.tsx  
**data-testid :** entity-save-btn, entity-ignore-btn

---

### US-011 : Afficher l'indicateur de saisie (typing indicator)
**En tant que** solopreneur/TPE  
**Je veux** voir un animation pendant que THÉRÈSE réfléchit  
**Afin de** savoir que le traitement est en cours

**Critères d'acceptation :**
- [ ] Les 3 points bleus montent et descendent en boucle
- [ ] L'icône Bot + "Réflexion..." s'affiche avant le texte
- [ ] L'animation s'arrête dès que le texte arrive
- [ ] Respecte les préférences accessibilité (reduceMotion)

**Composants :** TypingIndicator.tsx, MessageList.tsx  
**data-testid :** typing-indicator

---

### US-012 : Annoncer les nouveaux messages au lecteur d'écran
**En tant que** solopreneur/TPE malvoyant  
**Je veux** qu'un lecteur d'écran annonce les nouveaux messages  
**Afin de** suivre la conversation sans voir l'écran

**Critères d'acceptation :**
- [ ] Un message "Nouveau message de Therese" est annoncé via aria-live
- [ ] Seuls les messages assistant terminés sont annoncés
- [ ] L'annonce respecte la préférence `announceMessages` dans le store
- [ ] Les messages interactifs sont balisés aria-label

**Composants :** MessageList.tsx, accessibility utilities  
**data-testid :** N/A (aria-live)

---

### US-013 : Afficher la Palette de Commandes
**En tant que** solopreneur/TPE  
**Je veux** appuyer sur Cmd+K pour ouvrir une palette de commandes  
**Afin de** naviguer rapidement sans utiliser la souris

**Critères d'acceptation :**
- [ ] Cmd+K ouvre une modale modale avec liste de commandes
- [ ] Les commandes sont catégorisées (chat, memory, panels, settings)
- [ ] Tapez pour filtrer les commandes
- [ ] Les flèches et Entrée naviguent et exécutent
- [ ] Échap ferme la palette

**Composants :** CommandPalette.tsx, ChatLayout.tsx  
**data-testid :** command-palette

---

### US-014 : Afficher les raccourcis clavier
**En tant que** solopreneur/TPE  
**Je veux** voir tous les raccourcis disponibles avec Cmd+/  
**Afin de** apprendre les touches rapides

**Critères d'acceptation :**
- [ ] Une modale groupée par catégories affiche les raccourcis
- [ ] Les raccourcis Mac/Windows s'adaptent automatiquement
- [ ] Les touches sont lisibles (symboles ⌘, ⇧, ↵, etc.)
- [ ] Fermeture avec Échap

**Composants :** ShortcutsModal.tsx, ChatLayout.tsx  
**data-testid :** shortcuts-modal

---

### US-015 : Ouvrir le menu des commandes slash
**En tant que** solopreneur/TPE  
**Je veux** taper "/" pour voir les commandes disponibles  
**Afin de** exécuter rapidement une action sans mémoriser la syntaxe

**Critères d'acceptation :**
- [ ] Un menu apparaît après taper "/" avec les commandes filtrées
- [ ] Les commandes intégrées et customisées sont listées
- [ ] Chaque commande affiche icône + description
- [ ] Les flèches et Entrée sélectionnent et insèrent le préfixe
- [ ] Le menu se ferme quand le "/" est supprimé

**Composants :** SlashCommandsMenu.tsx, ChatInput.tsx  
**data-testid :** slash-commands-menu

---

### US-016 : Gérer l'affichage des panneaux latéraux
**En tant que** solopreneur/TPE  
**Je veux** ouvrir/fermer les panneaux (Mémoire, Settings, Board) avec des raccourcis  
**Afin de** maximiser l'espace du chat quand j'en ai besoin

**Critères d'acceptation :**
- [ ] Cmd+M bascule le panneau Mémoire
- [ ] Cmd+D bascule le Board
- [ ] Cmd+B bascule la sidebar des conversations
- [ ] Les panneaux se ferment indépendamment
- [ ] L'état des panneaux est mémorisé

**Composants :** ChatLayout.tsx, PanelContainer.tsx, panelStore  
**data-testid :** memory-panel-toggle, board-panel-toggle

---

### US-017 : Afficher l'en-tête du chat avec titre de conversation
**En tant que** solopreneur/TPE  
**Je veux** voir le titre de la conversation courante dans la barre top  
**Afin de** savoir sur quelle conversation je travaille

**Critères d'acceptation :**
- [ ] Le logo THÉRÈSE s'affiche à gauche (cliquable = nouvelle conv)
- [ ] Le titre de la conversation s'affiche à côté du logo
- [ ] Les boutons d'accès rapides (Mail, Calendrier, etc.) sont dans la barre
- [ ] Les contrôles Windows (min/max/close) s'affichent sur Windows/Linux

**Composants :** ChatHeader.tsx  
**data-testid :** settings-btn

---

### US-018 : Créer une nouvelle conversation
**En tant que** solopreneur/TPE  
**Je veux** cliquer sur le logo ou appuyer Cmd+N pour démarrer une conversation vide  
**Afin de** commencer un nouvel échange sans garder l'historique

**Critères d'acceptation :**
- [ ] Une nouvelle conversation est créée dans le store
- [ ] La conversation précédente est sauvegardée
- [ ] Le chat vide affiche les "HomeCommands" (guided prompts)
- [ ] L'ID de conversation est unique

**Composants :** ChatHeader.tsx, ChatLayout.tsx, chatStore.ts  
**data-testid :** new-conversation-btn

---

### US-019 : Sélectionner rapidement le modèle LLM actif
**En tant que** solopreneur/TPE  
**Je veux** voir et changer le modèle LLM courant dans le chat  
**Afin de** tester rapidement différents modèles sans aller en Settings

**Critères d'acceptation :**
- [ ] Un dropdown affiche le provider et modèle courant
- [ ] Les modèles disponibles sont listés (depuis availableModels)
- [ ] Changer le modèle met à jour la config immédiatement
- [ ] Un événement `therese:llm-config-changed` est envoyé

**Composants :** ChatInput.tsx (handleModelChange)  
**data-testid :** model-selector

---

### US-020 : Afficher le ghost text prédictif
**En tant que** solopreneur/TPE  
**Je veux** voir une suggestion grisée du texte à taper  
**Afin de** compléter mes messages plus rapidement (style Copilot)

**Critères d'acceptation :**
- [ ] Une suggestion s'affiche en gris dans le textarea
- [ ] Appuyer Tab ou Entrée accepte la suggestion
- [ ] La suggestion disparaît si je commencer à taper
- [ ] Basé sur l'historique de la conversation

**Composants :** ChatInput.tsx (useGhostText hook)  
**data-testid :** ghost-text

---

### US-021 : Enregistrer un message audio via le micro
**En tant que** solopreneur/TPE  
**Je veux** appuyer sur un bouton micro pour dicter mes messages  
**Afin de** communiquer naturellement sans écrire

**Critères d'acceptation :**
- [ ] Clic sur l'icône microphone lance l'enregistrement
- [ ] Pendant l'enregistrement, le bouton devient un carré rouge "Stop"
- [ ] L'audio est envoyé pour transcription (Groq Whisper)
- [ ] Le texte transcrit s'insère dans le textarea
- [ ] Un message d'erreur s'affiche en cas d'échec micro

**Composants :** ChatInput.tsx, useVoiceRecorder hook  
**data-testid :** chat-voice-btn

---

### US-022 : Afficher le statut de connexion au serveur
**En tant que** solopreneur/TPE  
**Je veux** voir un indicateur dans le coin bas-droit montrant l'état de connexion  
**Afin de** diagnostiquer les problèmes de réseau

**Critères d'acceptation :**
- [ ] Un petit point vert = connecté
- [ ] Un point rouge ou orange = en cours de reconnexion
- [ ] Survol affiche le statut exact (connected, connecting, disconnected)
- [ ] L'indicateur se met à jour en temps réel

**Composants :** ConnectionStatus.tsx, ChatLayout.tsx  
**data-testid :** connection-status

---

### US-023 : Afficher la barre latérale des conversations
**En tant que** solopreneur/TPE  
**Je veux** voir toutes mes conversations antérieures dans une sidebar  
**Afin de** naviguer rapidement entre les discussions

**Critères d'acceptation :**
- [ ] La sidebar s'affiche à gauche (toggle avec Cmd+B)
- [ ] Chaque conversation affiche titre + date
- [ ] Cliquer charge la conversation
- [ ] Un bouton "+" crée une nouvelle conversation
- [ ] Un menu contextuel permet supprimer une conversation

**Composants :** ConversationSidebar.tsx, ChatLayout.tsx  
**data-testid :** conversation-sidebar

---

### US-024 : Afficher les sideToggle pour réduire la barre latérale
**En tant que** solopreneur/TPE  
**Je veux** réduire les panneaux latéraux pour maximiser le chat  
**Afin de** avoir plus d'espace pour les messages

**Critères d'acceptation :**
- [ ] Deux petits chevrons "< >" apparaissent sur les côtés
- [ ] Cliquer les cache/affiche les panneaux
- [ ] L'état est mémorisé
- [ ] Les tooltips montrent le raccourci (Cmd+B, Cmd+M)

**Composants :** SideToggle.tsx, ChatLayout.tsx  
**data-testid :** side-toggle-left, side-toggle-right

---

### US-025 : Afficher la notification du mode démo
**En tant que** solopreneur/TPE  
**Je veux** voir une badge "Mode Démo" quand la démo est activée  
**Afin de** savoir que le contenu est masqué

**Critères d'acceptation :**
- [ ] Un petit badge cyan apparaît dans le header quand demoEnabled est vrai
- [ ] Le texte "Mode Démo" est visible
- [ ] Le badge pulse pour l'attention
- [ ] Cmd+Shift+D bascule le mode démo

**Composants :** ChatHeader.tsx  
**data-testid :** demo-mode-badge

---

## Module ONBOARDING

### US-026 : Afficher l'assistant onboarding au premier lancement
**En tant que** nouveau utilisateur  
**Je veux** être guidé à travers un wizard de configuration  
**Afin de** configurer THÉRÈSE correctement dès le début

**Critères d'acceptation :**
- [ ] Un full-screen modal s'affiche au premier lancement
- [ ] 6 étapes sont parcourues de façon guidée (Welcome → Complete)
- [ ] Les boutons Previous/Next permettent la navigation
- [ ] L'onboarding ne s'affiche plus une fois terminé

**Composants :** OnboardingWizard.tsx, App.tsx  
**data-testid :** onboarding-wizard

---

### US-027 : Afficher l'étape de bienvenue
**En tant que** nouveau utilisateur  
**Je veux** voir une présentation attrayante de THÉRÈSE  
**Afin de** comprendre ce que je m'apprête à utiliser

**Critères d'acceptation :**
- [ ] Le logo THÉRÈSE s'affiche avec une animation
- [ ] Les 3 features clés (Mémoire, Données locales, Multi-LLM) sont décrites
- [ ] Un bouton "Commencer la configuration" lance l'étape suivante
- [ ] Le texte est en français

**Composants :** WelcomeStep.tsx, OnboardingWizard.tsx  
**data-testid :** onboarding-step-0, onboarding-next-btn

---

### US-028 : Configurer le profil utilisateur
**En tant que** nouveau utilisateur  
**Je veux** saisir mon nom, entreprise, email et contexte professionnel  
**Afin de** que THÉRÈSE me connaisse et adapte ses réponses

**Critères d'acceptation :**
- [ ] Champs : nom (obligatoire), prénom, entreprise, rôle, email, localisation, contexte
- [ ] Un bouton "Importer depuis CLAUDE.md" charge un fichier markdown
- [ ] Les données sont sauvegardées via `setProfile()`
- [ ] Un bouton "Passer" permet de continuer sans remplir

**Composants :** ProfileStep.tsx, OnboardingWizard.tsx  
**data-testid :** onboarding-step-1, profile-name-input

---

### US-029 : Sélectionner le provider LLM et la clé API
**En tant que** nouveau utilisateur  
**Je veux** choisir mon fournisseur IA (Claude, GPT, Gemini, Mistral, etc.)  
**Afin de** utiliser le modèle de mon choix

**Critères d'acceptation :**
- [ ] 7 providers sont affichés (Anthropic, OpenAI, Gemini, Mistral, Grok, OpenRouter, Perplexity)
- [ ] Chaque provider liste ses modèles disponibles
- [ ] Une zone de saisie pour la clé API (masquée par défaut)
- [ ] Un lien "Obtenir une clé" redirige vers la console du provider
- [ ] Les données sont sauvegardées et chiffrées via `setLLMConfig()`

**Composants :** LLMStep.tsx, OnboardingWizard.tsx  
**data-testid :** onboarding-step-2, llm-provider-select

---

### US-030 : Afficher les avertissements de sécurité
**En tant que** nouveau utilisateur  
**Je veux** comprendre les risques liés à l'utilisation de THÉRÈSE  
**Afin de** prendre des décisions informées sur la configuration

**Critères d'acceptation :**
- [ ] 5 risques sont listés : LLMs Cloud, Serveurs MCP, Accès fichiers, Recherche Web, Transcription vocale
- [ ] Chaque risque a un niveau de sévérité (haut/moyen/faible) avec couleur
- [ ] Cliquer sur un risque l'expands pour plus de détails
- [ ] Une case "J'ai compris" doit être cochée pour continuer
- [ ] Les données ne changent pas, c'est de la sensibilisation

**Composants :** SecurityStep.tsx, OnboardingWizard.tsx  
**data-testid :** onboarding-step-3, security-acknowledge-checkbox

---

### US-031 : Sélectionner le dossier de travail
**En tant que** nouveau utilisateur  
**Je veux** choisir le dossier où THÉRÈSE cherchera mes fichiers  
**Afin de** lui permettre d'accéder à mon contexte de travail

**Critères d'acceptation :**
- [ ] Un bouton "Sélectionner un dossier" ouvre un file picker
- [ ] Le chemin sélectionné s'affiche en gras
- [ ] Les données sont sauvegardées via `setWorkingDirectory()`
- [ ] Un bouton "Passer" permet de continuer sans sélectionner

**Composants :** WorkingDirStep.tsx, OnboardingWizard.tsx  
**data-testid :** onboarding-step-4, working-dir-select-btn

---

### US-032 : Afficher le résumé d'onboarding
**En tant que** nouveau utilisateur  
**Je veux** voir un résumé de ma configuration avant de terminer  
**Afin de** vérifier que tout est correct

**Critères d'acceptation :**
- [ ] 3 éléments sont affichés : Profil, LLM, Dossier de travail
- [ ] Chaque élément montre l'icône, le titre et la valeur configurée
- [ ] Une coche verte indique si l'élément est configuré
- [ ] Un bouton "Lancer THÉRÈSE" finalize l'onboarding
- [ ] Un message de félicitations (confetti ?) s'affiche

**Composants :** CompleteStep.tsx, OnboardingWizard.tsx  
**data-testid :** onboarding-step-5, onboarding-complete-btn

---

### US-033 : Navigation dans le wizard d'onboarding
**En tant que** nouveau utilisateur  
**Je veux** naviguer entre les étapes avec Previous/Next ou clavier  
**Afin de** configurer THÉRÈSE à mon rythme

**Critères d'acceptation :**
- [ ] Boutons Previous/Next naviguent entre étapes
- [ ] Le boutton Previous est désactivé à la première étape
- [ ] Le bouton Next est désactivé si des champs obligatoires manquent
- [ ] La barre de progression montre les étapes parcourues

**Composants :** OnboardingWizard.tsx  
**data-testid :** onboarding-prev-btn, onboarding-next-btn

---

### US-034 : Importer la configuration depuis CLAUDE.md
**En tant que** nouveau utilisateur expérimenté  
**Je veux** importer mon profil depuis un fichier CLAUDE.md existant  
**Afin de** configurer THÉRÈSE rapidement sans ressaisir mes infos

**Critères d'acceptation :**
- [ ] Un bouton "Importer depuis CLAUDE.md" ouvre un file picker
- [ ] Le fichier markdown est parsé pour extraire name, company, context, etc.
- [ ] Les champs du formulaire se remplissent automatiquement
- [ ] En cas d'erreur de parsing, un message d'erreur s'affiche

**Composants :** ProfileStep.tsx  
**data-testid :** import-claude-md-btn

---

### US-035 : Afficher les contrôles de fenêtre dans l'onboarding
**En tant que** utilisateur Windows/macOS  
**Je veux** pouvoir réduire/agrandir/fermer la fenêtre pendant l'onboarding  
**Afin de** gérer la fenêtre de l'app

**Critères d'acceptation :**
- [ ] macOS : les 3 traffic lights (rouge/jaune/vert) s'affichent en haut à gauche
- [ ] Windows/Linux : les 3 boutons std (-, [], X) s'affichent en haut à droite
- [ ] Les clics exécutent minimize(), toggleMaximize(), close()
- [ ] La zone draggable n'interfère pas avec les boutons

**Composants :** OnboardingWizard.tsx  
**data-testid :** window-close-btn

---

### US-036 : Complèter l'onboarding
**En tant que** nouveau utilisateur  
**Je veux** finaliser l'onboarding et accéder au chat  
**Afin de** commencer à utiliser THÉRÈSE

**Critères d'acceptation :**
- [ ] Cliquer "Lancer THÉRÈSE" appelle `completeOnboarding()` en backend
- [ ] Le wizard se ferme
- [ ] Le chat devient disponible et affiche le dashboard "Ma journée"
- [ ] Un événement `therese:llm-config-changed` est envoyé

**Composants :** CompleteStep.tsx, OnboardingWizard.tsx  
**data-testid :** onboarding-complete-btn

---

## FONCTIONNALITÉS TRANSVERSES (Hooks & Stores)

### US-037 : Gérer les raccourcis clavier globaux
**En tant que** solopreneur/TPE  
**Je veux** que tous les raccourcis (Cmd+K, Cmd+M, Cmd+N, etc.) fonctionnent partout  
**Afin de** travailler rapidement sans souris

**Critères d'acceptation :**
- [ ] `useKeyboardShortcuts` déclenche les callbacks appropriés
- [ ] Cmd+N fonctionne même si le focus est dans le textarea
- [ ] Cmd+K ouvre la palette de commandes de n'importe où
- [ ] Les raccourcis s'adaptent automatiquement Mac/Windows

**Composants :** useKeyboardShortcuts.ts, ChatLayout.tsx  
**data-testid :** N/A

---

### US-038 : Enregistrer et restaurer l'audio transcrit
**En tant que** solopreneur/TPE  
**Je veux** que l'enregistrement vocal soit transcrit et inséré dans le chat  
**Afin de** dicter mes messages naturellement

**Critères d'acceptation :**
- [ ] `useVoiceRecorder` démarre l'enregistrement via Tauri ou Web API
- [ ] L'audio est envoyé à Groq Whisper pour transcription
- [ ] Le texte transcrit est retourné via callback `onTranscript`
- [ ] Les erreurs microphone sont gérées gracieusement

**Composants :** useVoiceRecorder.ts, ChatInput.tsx  
**data-testid :** N/A

---

### US-039 : Gérer l'état des conversations dans le store
**En tant que** solopreneur/TPE  
**Je veux** que mes conversations soient persistées et synchronisées  
**Afin de** reprendre ma discussion d'une session à l'autre

**Critères d'acceptation :**
- [ ] `chatStore` persiste les conversations (Zustand persist)
- [ ] Les messages ont id, role, content, timestamp, usage, uncertainty, entities
- [ ] Les conversations sont triées par date la plus récente
- [ ] La conversation courante peut être changée via `loadConversation(id)`

**Composants :** chatStore.ts  
**data-testid :** N/A

---

### US-040 : Backend - Router Chat
**En tant que** backend  
**Je veux** que l'API expose les endpoints de chat  
**Afin de** que le frontend puisse envoyer des messages et recevoir des réponses

**Critères d'acceptation :**
- [ ] `POST /chat/conversations` crée une conversation
- [ ] `POST /chat/stream` stream une réponse (async generator)
- [ ] `GET /chat/conversations/{id}` récupère une conversation
- [ ] `DELETE /chat/conversations/{id}` supprime une conversation

**Composants :** src/backend/app/routers/chat.py  
**data-testid :** N/A

---

### US-041 : Backend - LLM Service (Orchestrateur)
**En tant que** backend  
**Je veux** que le service LLM orchestre les appels multimodaux (text, voice, images)  
**Afin de** supporter Claude, GPT, Gemini, Mistral, Grok, OpenRouter, Perplexity

**Critères d'acceptation :**
- [ ] `LLMService` détermine le provider et le modèle
- [ ] Les clés API sont récupérées chiffrées depuis la DB
- [ ] Le contexte (memory, fichiers) est injecté dans le prompt système
- [ ] Les tokens et coûts sont trackés

**Composants :** src/backend/app/services/llm.py  
**data-testid :** N/A

---

---

**Total : 41 User Stories**  
**Modules couverts : Chat (25 US), Onboarding (11 US), Transverses (5 US)**