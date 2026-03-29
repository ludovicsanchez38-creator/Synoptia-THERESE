Parfait ! J'ai maintenant toutes les informations. Créons le document des user stories :

# Récapitulatif des User Stories - THÉRÈSE Settings, MCP, Images, Voix

Basé sur mon analyse du codebase complet, voici les **user stories** reconstruites pour les modules Settings, MCP (19 presets), Images et Voix.

---

## **ONGLET PROFIL**

### US-600 : Configuration du profil utilisateur
**En tant que** solopreneur/TPE  
**Je veux** renseigner mon profil (nom, surnom, entreprise, rôle, email, localisation, adresse, SIREN, TVA) et contexte additionnel  
**Afin de** personnaliser les réponses de l'IA avec mes informations métier

**Critères d'acceptation :**
- [ ] Formulaire 2 colonnes pour nom/surnom, entreprise/rôle, email/localisation
- [ ] Champs adresse (facturation), SIREN et TVA intracommunautaire
- [ ] Zone texte contexte additionnel (offres, secteur, projets en cours)
- [ ] Vérification statut profil avec badge "Profil configuré"
- [ ] Sauvegarde en base de données + chiffrage des données sensibles

**Composants :** ProfileTab.tsx, SettingsModal.tsx  
**data-testid :** settings-profile-name, settings-profile-company, settings-profile-context  
**API :** PATCH /api/config/user-profile

---

### US-601 : Gestion du fichier THERESE.md
**En tant que** solopreneur avec contexte complexe  
**Je veux** éditer un fichier THERESE.md (markdown) dans une modale pour stocker mes instructions personnalisées  
**Afin de** que THÉRÈSE comprenne mon domaine, mes offres et ma stratégie personnalisée

**Critères d'acceptation :**
- [ ] Bouton "Voir THERESE.md" qui ouvre une modale d'édition
- [ ] Zone textarea monospace pour éditer le contenu markdown
- [ ] Bouton "Sauvegarder" avec état loading/saved/error
- [ ] Chargement du contenu depuis l'API (GET /api/config/therese-md)
- [ ] Z-index modal (Z_LAYER.MODAL)
- [ ] Fermeture avec bouton X

**Composants :** ProfileTab.tsx  
**data-testid :** profile-therese-md-modal, profile-therese-save-btn  
**API :** GET/POST /api/config/therese-md

---

### US-602 : Import du profil depuis fichier
**En tant que** utilisateur  
**Je veux** importer mon profil depuis un fichier (JSON ou THERESE.md)  
**Afin de** de migrer rapidement depuis une autre instance

**Critères d'acceptation :**
- [ ] Bouton "Importer" qui ouvre un file picker Tauri
- [ ] Lecture du fichier et parsing (JSON ou markdown frontmatter)
- [ ] Remplissage automatique du formulaire profil
- [ ] Gestion des erreurs si format invalide

**Composants :** ProfileTab.tsx  
**data-testid :** profile-import-btn  
**API :** POST /api/config/import-profile

---

### US-603 : Mode Démo (masquage des données clients)
**En tant que** consultant/formateur  
**Je veux** activer un "Mode Démo" qui remplace les noms/emails par des personas fictifs  
**Afin de** montrer THÉRÈSE à des clients sans divulguer mes données réelles

**Critères d'acceptation :**
- [ ] Toggle "Mode Démo" en bas de l'onglet Profil
- [ ] Stockage en localStorage (therese-demo-mode)
- [ ] Remplacement global des noms de contacts/projets par des personas
- [ ] Raccourci clavier ⌘⇧D (Mac) ou Ctrl+Shift+D (Windows)
- [ ] Affichage du statut dans une bannière cyan quand actif

**Composants :** ProfileTab.tsx, useDemoStore  
**data-testid :** profile-demo-toggle  
**Store :** demoStore

---

## **ONGLET IA (LLM)**

### US-604 : Sélection du fournisseur LLM
**En tant que** utilisateur technique  
**Je veux** choisir mon fournisseur d'IA parmi 10 options (Anthropic, OpenAI, Gemini, Mistral, Grok, OpenRouter, Perplexity, DeepSeek, Infomaniak, Ollama)  
**Afin de** d'utiliser le modèle qui correspond le mieux à mes besoins/budget

**Critères d'acceptation :**
- [ ] 10 cartes radio avec provider, description, badge "Recommandé"/"Stable"/"Rapide"
- [ ] Ollama affiche "Non disponible" si pas de connexion locale
- [ ] Icône Check/Key/XCircle indiquant le statut de la clé API
- [ ] Clic sélectionne le provider et affiche la section clé API correspondante

**Composants :** LLMTab.tsx  
**data-testid :** llm-provider-select, llm-provider-anthropic  
**API :** PATCH /api/config/llm

---

### US-605 : Configuration de la clé API LLM
**En tant que** utilisateur  
**Je veux** saisir ma clé API pour le provider sélectionné avec visibilité toggle  
**Afin de** que THÉRÈSE accède au modèle d'IA choisi

**Critères d'acceptation :**
- [ ] Input password avec bouton œil pour afficher/masquer
- [ ] Placeholder contextuel (sk-ant-... pour Anthropic, sk-... pour OpenAI, etc.)
- [ ] Lien "Obtenir ta clé" vers la console du provider
- [ ] Bouton "Sauver" qui chiffre la clé (Fernet) avant stockage en DB
- [ ] États loading/success/error avec icônes
- [ ] Détection de clés corrompues avec badge rouge

**Composants :** LLMTab.tsx, SettingsModal.tsx  
**data-testid :** settings-api-key, llm-api-key-save-btn  
**API :** POST /api/config/api-key, GET /api/config/ (vérification encryption)  
**Security :** Fernet encryption, clé depuis Keychain macOS

---

### US-606 : Sélection du modèle LLM
**En tant que** utilisateur  
**Je veux** choisir le modèle (Claude Opus/Sonnet/Haiku, GPT-5/4o, Gemini 3.1/2.5, etc.) selon le provider  
**Afin de** d'équilibrer qualité, latence et coût

**Critères d'acceptation :**
- [ ] Select dropdown avec optgroup par provider
- [ ] Badges "Flagship"/"Recommandé"/"Rapide"/"Reasoning"/"Économique"
- [ ] Modèles listés après sélection du provider
- [ ] Pour Ollama : liste dynamique depuis /api/config/ollama/models

**Composants :** LLMTab.tsx  
**data-testid :** llm-model-select  
**API :** GET /api/config/ollama/models

---

### US-607 : Statut Ollama et re-test
**En tant que** utilisateur Ollama local  
**Je veux** vérifier l'état de connexion Ollama et pouvoir la re-tester sans recharger  
**Afin de** de savoir rapidement si mon instance locale est accessible

**Critères d'acceptation :**
- [ ] Badge "Ollama connecté (http://localhost:11434)" en vert si dispo
- [ ] Badge "Ollama non disponible" en rouge sinon
- [ ] Bouton refresh (RefreshCw) qui re-teste la connexion
- [ ] Spinner en rotation pendant le test
- [ ] Affichage du nombre de modèles disponibles

**Composants :** LLMTab.tsx  
**data-testid :** llm-ollama-status, llm-ollama-retest-btn  
**API :** GET /api/config/ollama/status, POST /api/config/ollama/retest  
**Ref :** BUG-049 (re-test Ollama à la demande)

---

## **ONGLET SERVICES**

### US-608 : Configuration génération d'images
**En tant que** utilisateur créatif  
**Je veux** sélectionner et configurer un provider de génération d'images (GPT Image 1.5, Nano Banana 2, Fal Flux Pro)  
**Afin de** générer des images via différents services

**Critères d'acceptation :**
- [ ] 3 cartes radio pour les providers images
- [ ] Chaque provider a sa clé API dédiée (openai_image, gemini_image, fal)
- [ ] Input password + bouton save par provider
- [ ] Lien vers la console du provider
- [ ] Badge "Clé OK" (vert) ou "Clé requise" (jaune)

**Composants :** ServicesTab.tsx  
**data-testid :** services-image-provider-select, services-image-key-save-btn  
**API :** PATCH /api/config/image-keys

---

### US-609 : Configuration Groq pour transcription vocale
**En tant que** utilisateur qui dicte  
**Je veux** configurer ma clé API Groq pour activer la transcription vocale Whisper  
**Afin de** de transcrire mes enregistrements audio en texte

**Critères d'acceptation :**
- [ ] Section "Transcription vocale" avec description "Groq whisper-large-v3-turbo"
- [ ] Input password pour clé API gsk_...
- [ ] Badge "Dictée vocale active" (vert) ou "Dictée vocale désactivée" (jaune)
- [ ] Lien vers console.groq.com
- [ ] API call stocke la clé chiffrée

**Composants :** ServicesTab.tsx  
**data-testid :** services-groq-key-input, services-groq-save-btn  
**API :** PATCH /api/config/groq-key  
**Backend :** src/backend/app/routers/voice.py

---

### US-610 : Configuration Brave Search pour recherche web
**En tant que** utilisateur web-aware  
**Je veux** activer la recherche web avec Brave Search et configurer ma clé API  
**Afin de** que les LLMs puissent chercher sur internet en temps réel

**Critères d'acceptation :**
- [ ] Toggle "Recherche Web" dans la section Services
- [ ] Input password (optionnel) pour clé Brave Search (BSA...)
- [ ] Badge "Clé OK" si configurée
- [ ] Lien "Obtenir une clé API" vers brave.com/search/api/
- [ ] Toggle loading pendant la sauvegarde

**Composants :** ServicesTab.tsx  
**data-testid :** services-websearch-toggle, services-brave-key-input  
**API :** PATCH /api/config/brave-search

---

### US-611 : Extraction automatique (contacts/projets)
**En tant que** utilisateur avec beaucoup de conversations  
**Je veux** activer l'extraction automatique de contacts et projets dans le contexte  
**Afin de** que THÉRÈSE enrichisse automatiquement ma base de données

**Critères d'acceptation :**
- [ ] Toggle "Extraction automatique" en bas de l'onglet Services
- [ ] Décrivant "Extraire contacts et projets des conversations"
- [ ] État persisté en base de données (Preference key: auto_extract_entities)

**Composants :** ServicesTab.tsx  
**data-testid :** services-auto-extract-toggle  
**API :** PATCH /api/config/extraction-settings

---

## **ONGLET OUTILS (MCP)**

### US-612 : Installation de presets MCP
**En tant que** utilisateur voulant étendre THÉRÈSE  
**Je veux** installer l'un des 19 presets MCP avec un clic  
**Afin de** d'ajouter des capacités (Filesystem, Notion, HubSpot, Stripe, etc.)

**Critères d'acceptation :**
- [ ] Affichage des 19 presets groupés par catégorie (Essentiels, Productivité, Recherche, Marketing, CRM, Finance, Communication, Avancé)
- [ ] Chaque preset affiche : nom, description, icône (popular ⭐, risk level 🛡️)
- [ ] Clic install → modale EnvVarModal si env_required, sinon installation directe
- [ ] État "Installé mais inactif" si le serveur est installé mais arrêté
- [ ] Auto-démarrage après installation réussie
- [ ] Badge "Clé requise" affichant les variables d'environnement manquantes

**Composants :** ToolsPanel.tsx, PresetCategory component  
**data-testid :** tools-preset-install-btn, tools-preset-card  
**API :** POST /api/mcp/presets/{preset_id}/install  
**19 Presets :** 
1. Filesystem (essentiels)
2. Fetch (essentiels)
3. Time (essentiels)
4. Google Workspace (productivité)
5. Notion (productivité, populaire)
6. Airtable (productivité)
7. Todoist (productivité, populaire)
8. Trello (productivité)
9. Brave Search (recherche, populaire)
10. Perplexity (recherche)
11. Brevo (marketing, populaire)
12. HubSpot CRM (CRM, populaire)
13. Pipedrive (CRM)
14. Stripe (finance, populaire, risque élevé)
15. WhatsApp Business (communication, risque moyen)
16. Sequential Thinking (avancé)
17. Slack (avancé)
18. Playwright (avancé, risque élevé)
19. (Un dernier - vérifier dans code)

---

### US-613 : Configuration des variables d'environnement MCP
**En tant que** utilisateur installant Stripe ou Notion  
**Je veux** saisir les clés API requises dans une modale avant installation  
**Afin de** que le preset MCP soit fonctionnel immédiatement

**Critères d'acceptation :**
- [ ] Modale EnvVarModal affiche les champs requis (STRIPE_API_KEY, NOTION_API_KEY, etc.)
- [ ] Inputs password avec toggle eye pour masquer/afficher
- [ ] Bouton Cancel et Confirm
- [ ] Validation : au moins un champ requis non vide
- [ ] Les clés sont chiffrées avant stockage en mcp_servers.json

**Composants :** EnvVarModal.tsx, ToolsPanel.tsx  
**data-testid :** env-var-modal, env-var-input, env-var-confirm-btn  
**API :** POST /api/mcp/presets/{id}/install avec corps {env_vars}

---

### US-614 : Gestion des serveurs MCP ajoutés manuellement
**En tant que** utilisateur avancé  
**Je veux** ajouter, éditer, démarrer, arrêter et supprimer des serveurs MCP manuels  
**Afin de** d'utiliser des serveurs personnalisés ou pas (encore) dans les presets

**Critères d'acceptation :**
- [ ] Liste des serveurs MCP avec statut (stopped/starting/running/error)
- [ ] Bouton "Ajouter un serveur" qui ouvre un formulaire (name, command, args)
- [ ] Boutons Démarrer/Arrêter/Redémarrer/Supprimer par serveur
- [ ] Expansion de chaque serveur pour voir les outils exposés
- [ ] Modale de confirmation avant suppression
- [ ] Polling automatique toutes les 3s si un serveur est en état "starting"

**Composants :** ToolsPanel.tsx  
**data-testid :** tools-server-list, tools-add-server-btn, tools-server-start-btn  
**API :** POST /api/mcp/servers, PUT /api/mcp/servers/{id}, DELETE /api/mcp/servers/{id}  
**Service :** src/backend/app/services/mcp_service.py

---

### US-615 : Affichage du statut MCP global
**En tant que** utilisateur  
**Je veux** voir un résumé du nombre de serveurs MCP actifs et d'outils disponibles  
**Afin de** de comprendre rapidement ce qui est installé et fonctionnel

**Critères d'acceptation :**
- [ ] En-tête montrant : "X serveurs totaux (Y actifs)" et "Z outils"
- [ ] Refresh automatique de l'état après démarrage/arrêt d'un serveur
- [ ] Statut par serveur : nom, état (couleurs), nombre d'outils

**Composants :** ToolsPanel.tsx  
**data-testid :** tools-status-header  
**API :** GET /api/mcp/status

---

## **ONGLET AGENTS (Katia & Zézette)**

### US-616 : Sélection du modèle par agent IA embarqué
**En tant que** utilisateur voulant personnaliser ses agents  
**Je veux** choisir le modèle LLM utilisé par Katia (PM/Guide) et Zézette (Dev)  
**Afin de** d'optimiser leurs performances selon la tâche

**Critères d'acceptation :**
- [ ] Deux selects indépendants : "Katia (PM/Guide)" et "Zézette (Dev)"
- [ ] Options groupées par provider (Anthropic, OpenAI, Google, etc.)
- [ ] Modèles avec badge "recommandé"
- [ ] Stockage en base de données (Preference)
- [ ] Bouton "Sauvegarder la configuration"

**Composants :** AgentsTab.tsx  
**data-testid :** agents-katia-model-select, agents-zezette-model-select  
**API :** PATCH /api/config/agent-config

---

### US-617 : Affichage du statut des agents
**En tant que** utilisateur  
**Je veux** voir le statut de Git, dépôt THÉRÈSE, Katia et Zézette  
**Afin de** de vérifier que les agents sont disponibles

**Critères d'acceptation :**
- [ ] Tableau de status : Git (OK/KO), Dépôt (OK/KO), Katia (OK/KO), Zézette (OK/KO)
- [ ] Affichage de la branche actuelle
- [ ] Bouton refresh (RefreshCw) pour re-checker
- [ ] Icônes CheckCircle/XCircle/AlertCircle

**Composants :** AgentsTab.tsx  
**data-testid :** agents-status-table, agents-refresh-btn  
**API :** GET /api/config/agent-status

---

### US-618 : Configuration du chemin source THÉRÈSE
**En tant que** développeur/contributeur THÉRÈSE  
**Je veux** spécifier le chemin vers mon clone/fork du repo  
**Afin de** que Katia et Zézette puissent améliorer l'app directement

**Critères d'acceptation :**
- [ ] Input text pour "/chemin/vers/Synoptia-THERESE"
- [ ] Sauvegarde en base de données (Preference key: agent_source_path)
- [ ] Synchronisation avec Zustand atelierStore

**Composants :** AgentsTab.tsx  
**data-testid :** agents-source-path-input  
**API :** PATCH /api/config/agent-source-path

---

## **ONGLET CONFIDENTIALITÉ**

### US-619 : Affichage de la politique de stockage RGPD
**En tant que** utilisateur soucieux de confidentialité  
**Je veux** voir comment mes données sont stockées et gérées  
**Afin de** de comprendre que THÉRÈSE respecte le RGPD

**Critères d'acceptation :**
- [ ] Section "Stockage" : "Toutes tes données sont locales (SQLite + Qdrant)"
- [ ] Section "Tes données" : liste des types (Contacts, Emails, Factures, Conversations, etc.)
- [ ] Table "Durées de conservation" avec justification légale
- [ ] Section "Tes droits" : Exporter / Anonymiser / Supprimer
- [ ] Z-index modal (Z_LAYER.MODAL)

**Composants :** PrivacyTab.tsx  
**data-testid :** privacy-storage-section, privacy-rights-section  
**API :** Lecture seule (contenu statique)

---

### US-620 : Purge automatique avec notification 30j
**En tant que** utilisateur  
**Je veux** configurer une purge automatique des contacts inactifs après X mois  
**Afin de** de respecter les durées de conservation légales

**Critères d'acceptation :**
- [ ] Toggle "Purge automatique" (activée par défaut)
- [ ] Slider 12-60 mois avec points clés (12, 36, 60)
- [ ] Notification 30j avant anonymisation des contacts exclus de la purge
- [ ] Contacts marqués "Exclure de la purge" ne sont jamais anonymisés automatiquement
- [ ] Bouton "Enregistrer"

**Composants :** PrivacyTab.tsx  
**data-testid :** privacy-purge-toggle, privacy-purge-slider, privacy-purge-save-btn  
**API :** GET/POST /api/rgpd/purge-settings

---

## **ONGLET AVANCÉ**

### US-621 : Comportement au lancement (skip dashboard)
**En tant que** utilisateur pressé  
**Je veux** ouvrir THÉRÈSE directement sur le chat au lieu du tableau de bord  
**Afin de** de gagner du temps au démarrage

**Critères d'acceptation :**
- [ ] Toggle "Ouvrir sur le chat directement"
- [ ] Stockage en localStorage (therese-skip-dashboard)
- [ ] Au lancement : si true, affiche /chat, sinon affiche /dashboard

**Composants :** AdvancedTab.tsx, StartupBehavior component  
**data-testid :** advanced-skip-dashboard-toggle  
**Store :** localStorage

---

### US-622 : Affichage des statistiques de stockage
**En tant que** utilisateur  
**Je veux** voir combien de conversations, messages, contacts, projets sont stockés  
**Afin de** de comprendre la taille de ma base de données

**Critères d'acceptation :**
- [ ] 4 cartes affichant : Conversations, Messages, Contacts, Projets
- [ ] Nombres formatés en français (1 234 au lieu de 1234)
- [ ] Badge "Données 100% locales" en vert

**Composants :** AdvancedTab.tsx, StatCard component  
**data-testid :** advanced-stats-card  
**API :** GET /api/config/ (field: stats)

---

### US-623 : Sélection du dossier de travail
**En tant que** utilisateur  
**Je veux** choisir où THÉRÈSE stocke les fichiers et la base de données  
**Afin de** de contrôler l'espace disque utilisé

**Critères d'acceptation :**
- [ ] Affichage du chemin actuel (ou "Non configuré")
- [ ] Bouton "Parcourir" qui ouvre le file picker Tauri (folder selection)
- [ ] Confirmation du changement en base de données (Preference: working_directory)
- [ ] Défaut : ~/.therese/

**Composants :** AdvancedTab.tsx  
**data-testid :** advanced-working-dir-input, advanced-browse-btn  
**API :** PATCH /api/config/working-directory

---

### US-624 : Onglets dépliables Accessibilité, Performance, Limites
**En tant que** utilisateur avec besoins d'accessibilité  
**Je veux** configurer le contraste, la réduction de mouvement, la taille de police  
**Afin de** d'améliorer mon confort d'utilisation

**Critères d'acceptation :**
- [ ] CollapsibleSection "Accessibilité" contenant AccessibilityTab
- [ ] CollapsibleSection "Performance" contenant PerformanceTab
- [ ] CollapsibleSection "Limites & Consommation" contenant LimitsTab
- [ ] CollapsibleSection "Synchronisation CRM" contenant CRMSyncPanel
- [ ] État ouvert/fermé persisté localement

**Composants :** AdvancedTab.tsx, AccessibilityTab.tsx, PerformanceTab.tsx, LimitsTab.tsx, CRMSyncPanel.tsx  
**data-testid :** advanced-collapsible-accessibility, advanced-collapsible-performance

---

## **ONGLET À PROPOS**

### US-625 : Affichage de la version actuelle
**En tant que** utilisateur  
**Je veux** connaître la version de THÉRÈSE que j'utilise  
**Afin de** de savoir si je suis à jour

**Critères d'acceptation :**
- [ ] Affichage "THÉRÈSE v0.4.0" (depuis le health check backend)
- [ ] Logo (T en dégradé cyan/magenta)
- [ ] Phase "Alpha"
- [ ] Texte "Assistante souveraine des entrepreneurs français"

**Composants :** AboutTab.tsx  
**data-testid :** about-version-display  
**API :** GET /api/health (field: version)

---

### US-626 : Vérification des mises à jour automatiques
**En tant que** utilisateur  
**Je veux** vérifier s'il existe une nouvelle version et télécharger la mise à jour  
**Afin de** de bénéficier des nouvelles fonctionnalités et corrections

**Critères d'acceptation :**
- [ ] Bouton "Vérifier les mises à jour" qui fait un fetch GitHub API
- [ ] Affichage "THÉRÈSE est à jour" (badge vert) si pas de mise à jour
- [ ] Affichage "Nouvelle version disponible : v0.4.1" avec notes de version
- [ ] Bouton "Télécharger" pour la plateforme détectée (DMG/MSI/AppImage)
- [ ] Bouton "Voir toutes les versions sur GitHub"
- [ ] Gestion des erreurs (GitHub API indisponible)

**Composants :** AboutTab.tsx  
**data-testid :** about-check-updates-btn, about-download-update-btn  
**API :** https://api.github.com/repos/ludovicsanchez38-creator/Synoptia-THERESE/releases

---

## **NOTIFICATIONS & MISE À JOUR**

### US-627 : Bandeau de mise à jour avec téléchargement en arrière-plan
**En tant que** utilisateur  
**Je veux** que le téléchargement d'une mise à jour se fasse en arrière-plan sans bloquer l'app  
**Afin de** de continuer à utiliser THÉRÈSE pendant le téléchargement

**Critères d'acceptation :**
- [ ] Check automatique au lancement (5s de délai)
- [ ] Check automatique toutes les 6 heures
- [ ] Affichage d'un bandeau en haut si mise à jour disponible
- [ ] Téléchargement silencieux en arrière-plan avec barre de progression
- [ ] État "Prêt à installer" une fois téléchargé
- [ ] Bouton "Redémarrer pour installer"
- [ ] BUG-099 : arrêt du backend sidecar AVANT l'installation (évite verrou backend.exe sur Windows)
- [ ] Health check poll : attendre que le backend soit vraiment mort

**Composants :** UpdateBanner.tsx  
**data-testid :** update-banner, update-install-btn, update-restart-btn  
**API :** Tauri updater plugin (@tauri-apps/plugin-updater)  
**Ref :** BUG-099 (shutdown backend + health check poll)

---

### US-628 : Centre de notifications in-app
**En tant que** utilisateur  
**Je veux** recevoir des notifications push (cloche) pour les événements importants  
**Afin de** de rester informé des actions du système (syncs, alertes, reminders)

**Critères d'acceptation :**
- [ ] Icône cloche dans le header avec badge compteur (nombre de notifications non lues)
- [ ] Dropdown panel avec list des notifications (récentes en haut)
- [ ] Notifications colorées par type : warning (orange), action (magenta), reminder (cyan), info (bleu)
- [ ] Chaque notif affiche : titre, message, source (badge), temps relatif, action optionnelle
- [ ] Clic sur notif = marque comme lue + annoncement au lecteur d'écran
- [ ] Z-index wizard (Z_LAYER.WIZARD) pour éviter les conflits avec modals
- [ ] Réduction de mouvement respectée (reduceMotion store)

**Composants :** NotificationCenter.tsx  
**data-testid :** notification-bell, notification-list, notification-item  
**Store :** notificationStore, accessibilityStore  
**API :** GET /api/notifications (stateless, data from WebSocket ou polling)

---

## **Z-INDEX STANDARDISATION**

### US-629 : Standardisation des Z-layers dans l'UI
**En tant que** développeur  
**Je veux** utiliser des constantes Z_LAYER au lieu de valeurs en dur  
**Afin de** d'éviter les conflits d'empilement et maintenir une hiérarchie cohérente

**Critères d'acceptation :**
- [ ] Z_LAYER.INTERNAL (z-10) : badges, overlays relatifs
- [ ] Z_LAYER.DROPDOWN (z-20) : menus contextuels, dropdowns
- [ ] Z_LAYER.SIDEBAR (z-30) : sidebars coulissants
- [ ] Z_LAYER.BACKDROP (z-40) : overlays sombre des modals
- [ ] Z_LAYER.MODAL (z-50) : modals principaux (Settings, Email, Calendar, Board, CRM, THERESE.md)
- [ ] Z_LAYER.MODAL_NESTED (z-60) : modals secondaires
- [ ] Z_LAYER.WIZARD (z-70) : wizards, notifications actionables (NotificationCenter)
- [ ] Z_LAYER.COMMAND_PALETTE (z-80) : palette de commandes
- [ ] Z_LAYER.TOAST (z-90) : toasts passifs
- [ ] Z_LAYER.ONBOARDING (z-100) : onboarding seulement
- [ ] Z_LAYER.ONBOARDING_TOP (z-101) : header onboarding

**Composants :** z-layers.ts (constantes), tous les composants UI  
**data-testid :** (intégré aux composants)  
**Ref :** US-004 (NotificationCenter fixe Z_LAYER.WIZARD pour éviter chevaucher les modals)

---

## **RÉSUMÉ FONCTIONNEL**

| Onglet | US | Titre | Statut |
|--------|----|----|--------|
| Profil | 600 | Configuration profil utilisateur | ✅ |
| Profil | 601 | Gestion THERESE.md | ✅ |
| Profil | 602 | Import profil | ✅ |
| Profil | 603 | Mode Démo | ✅ |
| IA | 604 | Sélection provider LLM | ✅ |
| IA | 605 | Configuration clé API | ✅ |
| IA | 606 | Sélection modèle | ✅ |
| IA | 607 | Statut Ollama + retest | ✅ (BUG-049) |
| Services | 608 | Config images | ✅ |
| Services | 609 | Groq transcription vocale | ✅ |
| Services | 610 | Brave Search web | ✅ |
| Services | 611 | Extraction automatique | ✅ |
| Outils | 612 | 19 presets MCP | ✅ |
| Outils | 613 | Env vars MCP | ✅ |
| Outils | 614 | Serveurs MCP manuels | ✅ |
| Outils | 615 | Statut MCP global | ✅ |
| Agents | 616 | Modèle par agent (Katia/Zézette) | ✅ |
| Agents | 617 | Statut agents | ✅ |
| Agents | 618 | Chemin source THÉRÈSE | ✅ |
| Confidentialité | 619 | Politique RGPD | ✅ |
| Confidentialité | 620 | Purge automatique | ✅ |
| Avancé | 621 | Skip dashboard | ✅ |
| Avancé | 622 | Statistiques stockage | ✅ |
| Avancé | 623 | Dossier de travail | ✅ |
| Avancé | 624 | Onglets dépliables | ✅ |
| À propos | 625 | Version actuelle | ✅ |
| À propos | 626 | Vérification mises à jour | ✅ |
| Mise à jour | 627 | Bandeau auto-update | ✅ (BUG-099) |
| Notifications | 628 | Centre notifications | ✅ |
| Z-index | 629 | Z-layer standardisation | ✅ |

---

## **NOTES IMPORTANTES**

- **19 Presets MCP** : Filesystem, Fetch, Time, Google Workspace, Notion, Airtable, Todoist, Trello, Brave Search, Perplexity, Brevo, HubSpot, Pipedrive, Stripe, WhatsApp Business, Sequential Thinking, Slack, Playwright + 1 autre (18 visibles, vérifier le dernier)
- **BUG-099** : Arrêt du backend sidecar AVANT installation mise à jour + health check poll (évite verrou backend.exe Windows)
- **BUG-049** : Re-test Ollama sans recharger les paramètres
- **Z_LAYER.WIZARD** : Fix notifications pour éviter chevaucher les modals (z-70 > z-50)
- **Chiffrage Fernet** : Toutes les clés API sont chiffrées avec Keychain macOS
- **Stockage local** : SQLite + Qdrant dans ~/.therese/ (100% données utilisateur)