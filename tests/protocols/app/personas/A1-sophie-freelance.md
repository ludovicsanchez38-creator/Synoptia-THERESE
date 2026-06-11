# Protocole de test - Persona A1 : Sophie Martin, graphiste freelance

> Version : 1.0 | Date : 2026-03-27
> App : THERESE Desktop (Tauri 2.0, React, Python FastAPI)
> URL dev : http://localhost:1420 | Backend : http://localhost:17293
> Pré-requis : `make dev` lancé, backend healthy, base SQLite vierge

## Profil persona

| Champ | Valeur |
|-------|--------|
| Nom | Sophie Martin |
| Age | 42 ans |
| Métier | Graphiste freelance |
| OS | macOS |
| Niveau tech | Non-tech, n'a jamais configuré une clé API |
| Objectif | Gérer ses clients, créer des devis, organiser son quotidien |
| Contexte | Premier contact avec l'IA, arrive de Canva/Figma, aucune expérience CLI |

## Convention de nommage screenshots

Tous les screenshots FAIL vont dans `/tmp/therese-tests/` avec le format :
`A1-{NN}_{slug}.png` (ex: `A1-01_splashscreen.png`)

## Dossier screenshots

```bash
mkdir -p /tmp/therese-tests
```

---

## Phase 1 : Premier lancement et onboarding (étapes 1-10)

---

### Étape 1 : Lancer l'app (première fois) - SplashScreen

**Priorité** : P0
**URL** : http://localhost:1420

**Pré-conditions** :
- Base SQLite vierge (supprimer `~/.therese/therese.db` si existante)
- localStorage vidé (`localStorage.clear()`)

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420`
2. `wait_for` -> `[data-testid="app-main"]` OU SplashScreen visible (max 10s)
3. `screenshot` -> `/tmp/therese-tests/A1-01_splashscreen.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="app-main"]') !== null || document.querySelector('.splash-screen') !== null`

**Résultat attendu** : L'app affiche soit le SplashScreen (attente backend en mode Tauri prod), soit redirige directement vers l'onboarding si le backend est déjà prêt (mode dev). Aucun écran blanc, aucune erreur console.
**États testés** : loading
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-01_splashscreen.png`

---

### Étape 2 : Onboarding Welcome (step 0) - wizard visible, bouton Commencer

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `wait_for` -> `[data-testid="onboarding-wizard"]` visible (max 15s)
2. `find` -> `[data-testid="onboarding-step-0"]`
3. `find` -> `[data-testid="onboarding-next-btn"]` (bouton "Commencer")
4. `screenshot` -> `/tmp/therese-tests/A1-02_welcome.png`
5. `javascript_tool` -> vérifier que le texte contient "Bienvenue" ou "THERESE"

**Résultat attendu** : Le wizard d'onboarding est affiché en plein écran. L'étape 0 (Welcome) est active avec le titre "Bienvenue". Le bouton "Commencer" (onboarding-next-btn) est visible et cliquable. La barre de progression indique l'étape 1/6.
**États testés** : empty, loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-02_welcome.png`

---

### Étape 3 : Cliquer Commencer - transition step 1 (Profil)

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="onboarding-next-btn"]`
2. `wait_for` -> `[data-testid="onboarding-step-1"]` visible (max 3s)
3. `screenshot` -> `/tmp/therese-tests/A1-03_profil_step.png`
4. `javascript_tool` -> vérifier la présence des champs prénom, nom, activité

**Résultat attendu** : L'animation de transition se joue (slide vers la gauche). L'étape 1 (Profil) s'affiche avec les champs de saisie : prénom, nom, activité. La barre de progression avance à 2/6. Le bouton "Suivant" est visible.
**États testés** : empty (champs vides)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-03_profil_step.png`

---

### Étape 4 : Profil vide - cliquer Suivant - validation erreur

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="onboarding-next-btn"]`
2. `wait_for` -> message d'erreur ou bordure rouge sur les champs (max 2s)
3. `screenshot` -> `/tmp/therese-tests/A1-04_profil_validation_error.png`
4. `javascript_tool` -> vérifier qu'un élément `.text-red`, `.border-red`, ou `[role="alert"]` est visible
5. `find` -> `[data-testid="onboarding-step-1"]` (toujours sur l'étape Profil, pas avancé)

**Résultat attendu** : L'onboarding reste sur l'étape 1 (Profil). Un message d'erreur apparaît indiquant que les champs obligatoires (prénom, nom) ne sont pas remplis. Les champs en erreur sont mis en évidence (bordure rouge ou texte d'erreur). Sophie comprend immédiatement ce qui manque.
**États testés** : error, empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-04_profil_validation_error.png`

---

### Étape 5 : Remplir le profil - prénom, nom, activité

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> champ prénom (input[name="firstName"] ou premier input dans step-1)
2. `click` -> champ prénom
3. `type` -> "Sophie"
4. `find` -> champ nom (input[name="lastName"] ou second input)
5. `click` -> champ nom
6. `type` -> "Martin"
7. `find` -> champ activité (input[name="activity"] ou troisième champ)
8. `click` -> champ activité
9. `type` -> "Graphiste"
10. `screenshot` -> `/tmp/therese-tests/A1-05_profil_filled.png`
11. `javascript_tool` -> vérifier que le bouton Suivant est maintenant enabled

**Résultat attendu** : Les trois champs sont remplis : "Sophie", "Martin", "Graphiste". Les erreurs de validation ont disparu. Le bouton Suivant est actif (pas grisé). Les champs affichent le texte saisi correctement (accents si besoin).
**États testés** : filled, focus
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-05_profil_filled.png`

---

### Étape 6 : Passer à LLM (step 2) - liste providers

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="onboarding-next-btn"]`
2. `wait_for` -> `[data-testid="onboarding-step-2"]` visible (max 3s)
3. `screenshot` -> `/tmp/therese-tests/A1-06_llm_step.png`
4. `javascript_tool` -> vérifier la liste des providers (Anthropic, OpenAI, Gemini, etc.)
5. `find` -> `[data-testid="onboarding-skip-btn"]` (bouton Skip doit être visible)

**Résultat attendu** : L'étape 2 (LLM) s'affiche avec la liste des fournisseurs d'IA. Sophie voit les logos/noms des providers mais les champs clé API sont vides. Le bouton "Passer" (Skip) est visible et accessible. L'explication est compréhensible pour une non-tech.
**États testés** : empty (aucune clé configurée)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-06_llm_step.png`

---

### Étape 7 : Cliquer Skip (ne sait pas ce qu'est une clé API)

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="onboarding-skip-btn"]`
2. `wait_for` -> `[data-testid="onboarding-step-3"]` visible (max 3s)
3. `screenshot` -> `/tmp/therese-tests/A1-07_security_step.png`

**Résultat attendu** : L'onboarding avance à l'étape 3 (Sécurité) sans bloquer. Sophie n'est pas obligée de configurer une clé API pour continuer. Aucune erreur, aucun avertissement bloquant. Le skip est silencieux et bienveillant.
**États testés** : empty (skip volontaire)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-07_security_step.png`

---

### Étape 8 : Security (step 3) - lire et cliquer Suivant

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="onboarding-step-3"]`
2. `javascript_tool` -> vérifier que le contenu mentionne "chiffrement", "local", "données" ou "sécurité"
3. `screenshot` -> `/tmp/therese-tests/A1-08_security_read.png`
4. `click` -> `[data-testid="onboarding-next-btn"]`
5. `wait_for` -> `[data-testid="onboarding-step-4"]` visible (max 3s)

**Résultat attendu** : L'étape Sécurité affiche un résumé clair des mesures de protection des données (chiffrement Fernet, données locales, pas de cloud). Le texte est compréhensible pour Sophie (pas de jargon technique excessif). Le clic sur Suivant mène à l'étape 4.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-08_security_read.png`

---

### Étape 9 : Working Dir (step 4) - garder défaut ~/.therese/

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="onboarding-step-4"]`
2. `javascript_tool` -> vérifier que le chemin par défaut `~/.therese/` ou un équivalent est affiché
3. `screenshot` -> `/tmp/therese-tests/A1-09_workingdir.png`
4. `click` -> `[data-testid="onboarding-next-btn"]`
5. `wait_for` -> `[data-testid="onboarding-step-5"]` visible (max 3s)

**Résultat attendu** : Le répertoire de travail par défaut (`~/.therese/`) est pré-rempli. Sophie n'a pas besoin de le modifier. Le bouton Suivant est actif. Le bouton Skip est aussi disponible. Le clic sur Suivant mène à l'étape finale.
**États testés** : filled (valeur par défaut)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-09_workingdir.png`

---

### Étape 10 : Complete (step 5) - Terminer - redirect chat

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="onboarding-step-5"]`
2. `find` -> `[data-testid="onboarding-complete-btn"]`
3. `screenshot` -> `/tmp/therese-tests/A1-10_complete_step.png`
4. `click` -> `[data-testid="onboarding-complete-btn"]`
5. `wait_for` -> `[data-testid="chat-message-input"]` visible (max 5s)
6. `screenshot` -> `/tmp/therese-tests/A1-10_chat_redirect.png`

**Résultat attendu** : L'étape finale affiche un résumé et un bouton "Terminer". Après le clic, l'onboarding se ferme et Sophie est redirigée vers l'interface de chat principale. Le wizard disparaît complètement. L'input de chat est visible et prêt à l'emploi. localStorage contient le flag onboarding complété.
**États testés** : loaded -> transition -> empty (chat vide)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-10_complete_step.png`

---

## Phase 2 : Découverte du chat et configuration LLM (étapes 11-20)

---

### Étape 11 : Chat vide - placeholder visible, pas de messages

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="chat-message-list"]`
2. `find` -> `[data-testid="chat-message-input"]`
3. `javascript_tool` -> `document.querySelectorAll('[data-testid="chat-message-item"]').length === 0`
4. `javascript_tool` -> vérifier que le placeholder de l'input contient un texte d'invitation (ex: "Posez votre question...")
5. `screenshot` -> `/tmp/therese-tests/A1-11_chat_empty.png`

**Résultat attendu** : L'interface de chat est vide : aucun message dans la liste. L'input de saisie affiche un placeholder invitant Sophie à écrire. Les boutons d'envoi, pièce jointe et micro sont visibles mais l'envoi est désactivé (input vide). L'ambiance dark mode est cohérente.
**États testés** : empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-11_chat_empty.png`

---

### Étape 12 : Taper "Bonjour" sans clé API - message erreur

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="chat-message-input"]`
2. `type` -> "Bonjour"
3. `screenshot` -> `/tmp/therese-tests/A1-12_typing.png`
4. `click` -> `[data-testid="chat-send-btn"]`
5. `wait_for` -> message d'erreur ou notification (max 5s)
6. `screenshot` -> `/tmp/therese-tests/A1-12_no_api_key_error.png`
7. `javascript_tool` -> vérifier qu'une notification, un toast, ou un message d'erreur mentionne "clé API", "API key", ou "configurer"

**Résultat attendu** : Le message "Bonjour" de Sophie apparaît dans la liste (bulle utilisateur). L'app tente d'appeler le LLM mais échoue car aucune clé API n'est configurée. Un message d'erreur clair apparaît (toast ou message système dans le chat) expliquant qu'il faut configurer une clé API. Le message n'est pas technique/cryptique.
**États testés** : error
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-12_no_api_key_error.png`

---

### Étape 13 : Ouvrir Settings (bouton engrenage)

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="settings-btn"]`
2. `click` -> `[data-testid="settings-btn"]`
3. `wait_for` -> `[data-testid="settings-modal"]` visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A1-13_settings_open.png`

**Résultat attendu** : Le modal des paramètres s'ouvre avec une animation fluide. Les onglets sont visibles sur la gauche (Profil, IA/LLM, Services, Données, etc.). L'onglet par défaut est sélectionné. Le bouton de fermeture (X) est visible en haut à droite.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-13_settings_open.png`

---

### Étape 14 : Naviguer onglet AI/LLM

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="settings-tab-llm"]`
2. `click` -> `[data-testid="settings-tab-llm"]`
3. `wait_for` -> contenu de l'onglet LLM visible (max 2s)
4. `screenshot` -> `/tmp/therese-tests/A1-14_settings_llm_tab.png`

**Résultat attendu** : L'onglet AI/LLM est sélectionné (highlight visuel). Le contenu affiche la liste des providers (Anthropic, OpenAI, Gemini, Mistral, Grok, OpenRouter, Ollama). Chaque provider a un champ pour sa clé API. Le layout est clair et non surchargé.
**États testés** : loaded, empty (clés vides)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-14_settings_llm_tab.png`

---

### Étape 15 : Voir les champs clé API vides

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> compter le nombre d'inputs de type password ou text dans l'onglet LLM
2. `javascript_tool` -> vérifier que tous les champs clé API sont vides (value === "")
3. `screenshot` -> `/tmp/therese-tests/A1-15_api_keys_empty.png`

**Résultat attendu** : Tous les champs de clé API sont vides. Les placeholders indiquent le format attendu (ex: "sk-..."). Aucune clé n'est pré-remplie. Les labels sont explicites pour chaque provider.
**États testés** : empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-15_api_keys_empty.png`

---

### Étape 16 : Entrer une fausse clé - sauvegarder - toast feedback

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> premier champ clé API (Anthropic ou OpenAI)
2. `click` -> ce champ
3. `type` -> "sk-fake-key-12345678"
4. `screenshot` -> `/tmp/therese-tests/A1-16_fake_key_typed.png`
5. `find` -> `[data-testid="settings-save-btn"]`
6. `click` -> `[data-testid="settings-save-btn"]`
7. `wait_for` -> toast/notification de confirmation (max 3s)
8. `screenshot` -> `/tmp/therese-tests/A1-16_save_feedback.png`

**Résultat attendu** : La clé est saisie dans le champ (affichée masquée ou en clair selon le type d'input). Le clic sur Sauvegarder déclenche une sauvegarde avec retour visuel (toast "Paramètres sauvegardés" ou équivalent). La clé est stockée chiffrée via Fernet. Le toast disparaît après quelques secondes.
**États testés** : filled, loading (pendant sauvegarde), success
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-16_save_feedback.png`

---

### Étape 17 : Fermer Settings

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="settings-close-btn"]`
2. `click` -> `[data-testid="settings-close-btn"]`
3. `wait_for` -> `[data-testid="settings-modal"]` disparaît (max 2s)
4. `find` -> `[data-testid="chat-message-input"]` (retour au chat)
5. `screenshot` -> `/tmp/therese-tests/A1-17_settings_closed.png`

**Résultat attendu** : Le modal se ferme avec une animation. L'interface de chat est à nouveau visible et interactive. Le message d'erreur précédent est toujours visible dans l'historique. L'input de chat est focusable.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-17_settings_closed.png`

---

### Étape 18 : Retenter un message - erreur ou réponse selon la clé

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="chat-message-input"]`
2. `type` -> "Est-ce que tu fonctionnes maintenant ?"
3. `click` -> `[data-testid="chat-send-btn"]`
4. `wait_for` -> réponse ou erreur (max 15s)
5. `screenshot` -> `/tmp/therese-tests/A1-18_retry_message.png`
6. `javascript_tool` -> compter les `[data-testid="chat-message-item"]` (doit être >= 3 : Bonjour + erreur/réponse + nouveau message)

**Résultat attendu** : Avec une fausse clé : un nouveau message d'erreur apparaît (401/403 du provider). Avec une vraie clé : une réponse en streaming apparaît. Dans les deux cas, le message de Sophie est ajouté à l'historique. L'app ne plante pas. Le comportement est prévisible.
**États testés** : error (fausse clé) OU loading + filled (vraie clé)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-18_retry_message.png`

---

### Étape 19 : (Si clé valide) Envoyer une demande - streaming réponse

**Priorité** : P1
**Pré-condition** : Clé API valide configurée (sinon skip cette étape)
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="chat-message-input"]`
2. `type` -> "Aide-moi à rédiger un email pour un client qui veut un logo"
3. `click` -> `[data-testid="chat-send-btn"]`
4. `wait_for` -> apparition du premier token de réponse (max 20s)
5. `screenshot` -> `/tmp/therese-tests/A1-19_streaming_start.png`
6. `wait_for` -> fin du streaming (indicateur de typing disparaît) (max 60s)
7. `screenshot` -> `/tmp/therese-tests/A1-19_streaming_complete.png`

**Résultat attendu** : Le message de Sophie apparaît immédiatement (bulle droite). L'indicateur de frappe (TypingIndicator) s'affiche pendant le streaming. Les tokens arrivent progressivement (effet de streaming visible). La réponse complète est formatée en Markdown (gras, listes, etc.). Le contenu est pertinent (email professionnel).
**États testés** : loading (streaming), filled (réponse complète)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-19_streaming_complete.png`

---

### Étape 20 : Vérifier le message dans la liste (user + assistant)

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> `document.querySelectorAll('[data-testid="chat-message-item"]').length`
2. `javascript_tool` -> vérifier qu'il y a au moins un message "user" et un message "assistant"
3. `screenshot` -> `/tmp/therese-tests/A1-20_messages_list.png`
4. `javascript_tool` -> vérifier le scroll automatique (dernier message visible dans le viewport)

**Résultat attendu** : La liste de messages contient les échanges de Sophie (bulles utilisateur à droite) et les réponses de l'IA (bulles assistant à gauche). Les messages sont ordonnés chronologiquement. Le scroll est automatiquement positionné sur le dernier message. Le rendu Markdown est correct.
**États testés** : filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-20_messages_list.png`

---

## Phase 3 : Gestion des conversations (étapes 21-23)

> **Sidebar fermée par défaut (depuis 11/06/2026)** : la sidebar conversations
> n'est plus ouverte au lancement (l'app atterrit sur l'Accueil). Avant toute
> action sur un `[data-testid="sidebar-*"]`, l'ouvrir :
> `javascript_tool` -> `window.__therese.stores.panel.getState().togglePanel('conversationSidebar')`
> (ou raccourci ⌘B/Ctrl+B), puis `wait_for` -> `[data-testid="sidebar"]` visible.

---

### Étape 21 : Nouvelle conversation (bouton +)

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="sidebar-new-conversation-btn"]`
2. `click` -> `[data-testid="sidebar-new-conversation-btn"]`
3. `wait_for` -> l'input de chat est vidé et la liste de messages est vide (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A1-21_new_conversation.png`
5. `javascript_tool` -> `document.querySelectorAll('[data-testid="chat-message-item"]').length === 0`

**Résultat attendu** : Une nouvelle conversation est créée. L'historique de chat est vidé. L'input est vide et prêt pour un nouveau message. La conversation précédente est sauvegardée et apparaît dans la sidebar. Le titre de la nouvelle conversation est générique ("Nouvelle conversation" ou vide).
**États testés** : empty (nouvelle conversation)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-21_new_conversation.png`

---

### Étape 22 : Vérifier que l'ancienne apparaît dans la sidebar

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="sidebar"]`
2. `find` -> `[data-testid="sidebar-conversation-list"]`
3. `javascript_tool` -> `document.querySelectorAll('[data-testid="sidebar-conversation-item"]').length >= 1`
4. `screenshot` -> `/tmp/therese-tests/A1-22_sidebar_previous.png`
5. `click` -> premier `[data-testid="sidebar-conversation-item"]` (l'ancienne conversation)
6. `wait_for` -> les messages de l'ancienne conversation réapparaissent (max 3s)
7. `screenshot` -> `/tmp/therese-tests/A1-22_restore_conversation.png`

**Résultat attendu** : La sidebar contient au moins une conversation précédente. Le titre est pertinent (soit généré automatiquement, soit le premier message). Le clic sur une conversation restaure son historique complet. Les messages sont intacts (contenu, ordre, formatage).
**États testés** : filled (sidebar), loaded (restauration)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-22_sidebar_previous.png`

---

### Étape 23 : Rechercher dans la sidebar

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="sidebar-search-input"]`
2. `click` -> `[data-testid="sidebar-search-input"]`
3. `type` -> "Bonjour"
4. `wait_for` -> filtrage de la liste (max 2s)
5. `screenshot` -> `/tmp/therese-tests/A1-23_sidebar_search.png`
6. `javascript_tool` -> vérifier que la liste filtrée contient au moins la conversation avec "Bonjour"
7. `find` -> `[data-testid="sidebar-search-input"]`
8. `javascript_tool` -> vider le champ de recherche (triple clic + delete)
9. `type` -> "zzzznonexistent"
10. `wait_for` -> liste vide ou message "aucun résultat" (max 2s)
11. `screenshot` -> `/tmp/therese-tests/A1-23_sidebar_search_empty.png`

**Résultat attendu** : La recherche filtre les conversations en temps réel. "Bonjour" affiche la conversation contenant ce mot. Un terme inexistant affiche une liste vide ou un message explicite. Le filtre est insensible à la casse. La suppression du terme restaure la liste complète.
**États testés** : filled (résultats), empty (aucun résultat), focus
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-23_sidebar_search.png`

---

## Phase 4 : Mémoire et contacts (étapes 24-29)

---

### Étape 24 : Ouvrir le panneau Mémoire (via bouton header)

**Priorité** : P0
**URL** : http://localhost:1420/?panel=memory

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=memory`
2. `wait_for` -> `[data-testid="memory-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A1-24_memory_panel.png`

**Résultat attendu** : Le panneau Mémoire s'ouvre et affiche l'interface de gestion des contacts et projets. La recherche sémantique est visible. Le panneau est structuré avec des sections claires (Contacts, Projets, Recherche).
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-24_memory_panel.png`

---

### Étape 25 : Mémoire vide - recherche vide, pas de contacts

**Priorité** : P1
**URL** : http://localhost:1420/?panel=memory

**Actions Chrome MCP** :
1. `find` -> `[data-testid="memory-search-input"]`
2. `javascript_tool` -> vérifier que la liste de contacts est vide (pas d'éléments .contact-item ou équivalent)
3. `screenshot` -> `/tmp/therese-tests/A1-25_memory_empty.png`
4. `click` -> `[data-testid="memory-search-input"]`
5. `type` -> "test"
6. `wait_for` -> résultat vide ou message "aucun résultat" (max 3s)
7. `screenshot` -> `/tmp/therese-tests/A1-25_memory_search_empty.png`

**Résultat attendu** : La mémoire est vide au premier lancement. La recherche sur un terme ne retourne rien. Un état vide explicite est affiché (illustration, texte "Aucun contact" ou équivalent). L'interface invite à ajouter un premier contact.
**États testés** : empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-25_memory_empty.png`

---

### Étape 26 : Ajouter un contact "Jean Dupont" (bouton + contact)

**Priorité** : P0
**URL** : http://localhost:1420/?panel=memory

**Actions Chrome MCP** :
1. `find` -> `[data-testid="memory-add-contact-btn"]`
2. `click` -> `[data-testid="memory-add-contact-btn"]`
3. `wait_for` -> modal ou formulaire de contact visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A1-26_contact_modal.png`

**Résultat attendu** : Un modal ou formulaire d'ajout de contact s'ouvre. Les champs sont vides et prêts à être remplis : nom, email, téléphone, entreprise, notes. Le formulaire est accessible (labels, tabulation).
**États testés** : empty (formulaire vide)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-26_contact_modal.png`

---

### Étape 27 : Remplir nom, email, téléphone, sauvegarder

**Priorité** : P0
**URL** : http://localhost:1420/?panel=memory

**Actions Chrome MCP** :
1. `find` -> champ nom du contact
2. `click` -> champ nom
3. `type` -> "Jean Dupont"
4. `find` -> champ email
5. `click` -> champ email
6. `type` -> "jean.dupont@example.com"
7. `find` -> champ téléphone
8. `click` -> champ téléphone
9. `type` -> "06 12 34 56 78"
10. `screenshot` -> `/tmp/therese-tests/A1-27_contact_filled.png`
11. `find` -> bouton Sauvegarder/Ajouter dans le modal
12. `click` -> bouton Sauvegarder
13. `wait_for` -> le modal se ferme et le contact apparaît dans la liste (max 3s)
14. `screenshot` -> `/tmp/therese-tests/A1-27_contact_saved.png`

**Résultat attendu** : Les champs sont remplis correctement. Le clic sur Sauvegarder persiste le contact en base SQLite. Le modal se ferme. Le contact "Jean Dupont" apparaît dans la liste des contacts de la mémoire. Un toast de confirmation peut apparaître.
**États testés** : filled, loading (sauvegarde), success
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-27_contact_saved.png`

---

### Étape 28 : Vérifier le contact dans la liste

**Priorité** : P1
**URL** : http://localhost:1420/?panel=memory

**Actions Chrome MCP** :
1. `javascript_tool` -> rechercher un élément contenant le texte "Jean Dupont" dans le panneau mémoire
2. `javascript_tool` -> vérifier que l'email "jean.dupont@example.com" est affiché ou accessible
3. `screenshot` -> `/tmp/therese-tests/A1-28_contact_in_list.png`

**Résultat attendu** : Le contact "Jean Dupont" est visible dans la liste des contacts. Les informations essentielles (nom, email) sont affichées. Le contact est cliquable pour voir les détails. Le compteur de contacts a été incrémenté (de 0 à 1).
**États testés** : filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-28_contact_in_list.png`

---

### Étape 29 : Rechercher "Jean" dans la mémoire

**Priorité** : P1
**URL** : http://localhost:1420/?panel=memory

**Actions Chrome MCP** :
1. `find` -> `[data-testid="memory-search-input"]`
2. `click` -> `[data-testid="memory-search-input"]`
3. `javascript_tool` -> vider le champ (sélectionner tout + supprimer)
4. `type` -> "Jean"
5. `wait_for` -> résultat de recherche contenant "Jean Dupont" (max 3s)
6. `screenshot` -> `/tmp/therese-tests/A1-29_memory_search_jean.png`
7. `javascript_tool` -> vérifier qu'au moins un résultat contient "Jean Dupont"

**Résultat attendu** : La recherche "Jean" retourne le contact "Jean Dupont" dans les résultats. La recherche fonctionne sur le prénom partiel. Les résultats sont mis en surbrillance ou filtrés. La recherche sémantique via Qdrant enrichit les résultats si des embeddings existent.
**États testés** : filled (résultats trouvés)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-29_memory_search_jean.png`

---

## Phase 5 : CRM et pipeline (étapes 30-32)

---

### Étape 30 : Ouvrir CRM via header

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=crm`
2. `wait_for` -> `[data-testid="crm-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A1-30_crm_panel.png`

**Résultat attendu** : Le panneau CRM s'ouvre et affiche l'interface de gestion commerciale. Les colonnes du pipeline sont visibles (Prospect, Contact, Proposition, Gagné, Perdu ou équivalent). L'interface est en dark mode cohérent avec le reste de l'app.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-30_crm_panel.png`

---

### Étape 31 : CRM vide - pas de pipeline, pas de leads

**Priorité** : P1
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier que le pipeline ne contient aucun lead/contact (colonnes vides)
2. `screenshot` -> `/tmp/therese-tests/A1-31_crm_empty.png`
3. `javascript_tool` -> vérifier qu'un état vide est affiché (texte ou illustration)

**Résultat attendu** : Le CRM est vide au premier lancement. Les colonnes du pipeline sont présentes mais sans cartes. Un message ou une illustration invite Sophie à ajouter son premier lead. L'interface est claire sur la marche à suivre.
**États testés** : empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-31_crm_empty.png`

---

### Étape 32 : Créer un lead/contact dans le CRM

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> bouton "Ajouter" ou "+" dans le CRM
2. `click` -> ce bouton
3. `wait_for` -> formulaire de création lead visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A1-32_crm_add_lead.png`
5. `find` -> champ nom du lead
6. `type` -> "Jean Dupont - Logo"
7. `find` -> champ montant ou valeur (si présent)
8. `type` -> "500"
9. `find` -> bouton Sauvegarder
10. `click` -> bouton Sauvegarder
11. `wait_for` -> le lead apparaît dans le pipeline (max 3s)
12. `screenshot` -> `/tmp/therese-tests/A1-32_crm_lead_created.png`

**Résultat attendu** : Un formulaire de création de lead s'ouvre. Sophie remplit le nom et le montant. Après sauvegarde, le lead apparaît dans la première colonne du pipeline (Prospect ou Lead). La carte affiche le nom "Jean Dupont - Logo" et le montant "500". Le CRM n'est plus vide.
**États testés** : empty -> filled -> success
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-32_crm_lead_created.png`

---

## Phase 6 : Facturation et devis (étapes 33-37)

---

### Étape 33 : Ouvrir Factures via header

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=invoices`
2. `wait_for` -> `[data-testid="invoices-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A1-33_invoices_panel.png`

**Résultat attendu** : Le panneau Factures s'ouvre. L'interface affiche la liste des documents (devis, factures, avoirs). Les filtres par type et statut sont visibles. Un bouton "Nouveau" ou "+" permet de créer un document.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-33_invoices_panel.png`

---

### Étape 34 : Factures vide - pas de devis

**Priorité** : P1
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier que la liste de documents est vide
2. `screenshot` -> `/tmp/therese-tests/A1-34_invoices_empty.png`
3. `javascript_tool` -> vérifier qu'un état vide explicite est affiché

**Résultat attendu** : Aucun devis ni facture n'existe. Un état vide est affiché (texte "Aucun document" ou illustration). Le bouton de création est bien mis en avant pour inviter Sophie à créer son premier devis.
**États testés** : empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-34_invoices_empty.png`

---

### Étape 35 : Créer un devis - client "Jean Dupont", ligne "Logo design 500EUR"

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> bouton "Nouveau" ou "Créer" dans le panneau factures
2. `click` -> ce bouton
3. `wait_for` -> formulaire InvoiceForm visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A1-35_invoice_form_open.png`
5. `find` -> sélecteur type de document (devis/facture/avoir)
6. `javascript_tool` -> sélectionner "devis" dans le select
7. `find` -> sélecteur client/contact
8. `javascript_tool` -> sélectionner "Jean Dupont" dans la liste des contacts
9. `find` -> champ description de la première ligne
10. `click` -> champ description
11. `type` -> "Logo design"
12. `find` -> champ quantité
13. `click` -> champ quantité
14. `javascript_tool` -> vider et taper "1"
15. `find` -> champ prix unitaire
16. `click` -> champ prix unitaire
17. `type` -> "500"
18. `screenshot` -> `/tmp/therese-tests/A1-35_devis_filled.png`

**Résultat attendu** : Le formulaire de création de devis est ouvert. Le type "devis" est sélectionné. Le client "Jean Dupont" est sélectionné depuis la liste des contacts existants. Une ligne de devis est créée avec "Logo design", quantité 1, prix 500EUR. Le total HT et TTC sont calculés automatiquement.
**États testés** : empty -> filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-35_devis_filled.png`

---

### Étape 36 : Sauvegarder le devis - statut brouillon

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> bouton Sauvegarder dans le formulaire
2. `click` -> bouton Sauvegarder
3. `wait_for` -> le formulaire se ferme et le devis apparaît dans la liste (max 5s)
4. `screenshot` -> `/tmp/therese-tests/A1-36_devis_saved.png`
5. `javascript_tool` -> vérifier que le devis a le statut "brouillon" ou "draft"
6. `javascript_tool` -> vérifier que le montant affiché est 500EUR (ou avec TVA selon config)

**Résultat attendu** : Le devis est sauvegardé en base SQLite. Le formulaire se ferme. Le devis apparaît dans la liste avec le statut "Brouillon". Le numéro de devis est généré automatiquement (ex: DEV-2026-001). Le montant est correct. Sophie peut le retrouver facilement.
**États testés** : loading (sauvegarde), success, filled (liste avec 1 devis)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-36_devis_saved.png`

---

### Étape 37 : Générer le PDF du devis

**Priorité** : P1
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> le devis dans la liste
2. `click` -> le devis (pour ouvrir les options)
3. `find` -> bouton "PDF" ou "Télécharger" ou icône PDF
4. `click` -> bouton PDF
5. `wait_for` -> téléchargement ou aperçu PDF (max 10s)
6. `screenshot` -> `/tmp/therese-tests/A1-37_devis_pdf.png`
7. `javascript_tool` -> vérifier qu'un fichier a été téléchargé ou qu'un aperçu est affiché

**Résultat attendu** : Le PDF du devis est généré avec les informations correctes : coordonnées de Sophie Martin (graphiste), client Jean Dupont, ligne "Logo design 500EUR", numéro de devis, date. Le PDF est conforme aux obligations légales françaises (mentions obligatoires). Le fichier est téléchargé ou affiché dans un viewer.
**États testés** : loading (génération), success (PDF disponible)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-37_devis_pdf.png`

---

## Phase 7 : Calendrier et événements (étapes 38-40)

---

### Étape 38 : Ouvrir Calendrier

**Priorité** : P0
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=calendar`
2. `wait_for` -> `[data-testid="calendar-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A1-38_calendar_panel.png`

**Résultat attendu** : Le panneau Calendrier s'ouvre en vue mois par défaut. La grille du mois courant est affichée. Les jours de la semaine sont indiqués. La navigation mois précédent/suivant est disponible.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-38_calendar_panel.png`

---

### Étape 39 : Calendrier - vue mois, date du jour surlignée

**Priorité** : P1
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier que la date du jour est mise en évidence (classe CSS `today`, `current`, highlight, ou équivalent)
2. `javascript_tool` -> `new Date().getDate()` puis vérifier que ce numéro est surligné dans la grille
3. `screenshot` -> `/tmp/therese-tests/A1-39_calendar_today.png`
4. `javascript_tool` -> vérifier que le titre du mois correspond au mois courant

**Résultat attendu** : La date du jour (27 mars 2026) est visuellement distincte (couleur, bordure, fond). Le mois affiché est "Mars 2026". La grille est correcte (jours de la semaine alignés). Le calendrier est vide (aucun événement encore créé).
**États testés** : loaded, empty (pas d'événements)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-39_calendar_today.png`

---

### Étape 40 : Créer événement "RDV Jean Dupont" demain 14h

**Priorité** : P0
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `find` -> bouton "Ajouter" ou "+" ou cliquer sur la case du lendemain
2. `click` -> ce bouton ou la case du 28 mars
3. `wait_for` -> formulaire EventForm visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A1-40_event_form.png`
5. `find` -> champ titre de l'événement
6. `click` -> champ titre
7. `type` -> "RDV Jean Dupont"
8. `find` -> champ date (si pas pré-rempli)
9. `javascript_tool` -> définir la date au lendemain
10. `find` -> champ heure de début
11. `javascript_tool` -> définir l'heure à "14:00"
12. `find` -> bouton Sauvegarder
13. `click` -> bouton Sauvegarder
14. `wait_for` -> l'événement apparaît dans le calendrier (max 3s)
15. `screenshot` -> `/tmp/therese-tests/A1-40_event_created.png`

**Résultat attendu** : Le formulaire de création d'événement s'ouvre. Sophie remplit le titre "RDV Jean Dupont" et configure la date du lendemain à 14h. Après sauvegarde, l'événement apparaît sur la case du 28 mars dans la grille du calendrier. Le titre est visible ou tronqué avec tooltip.
**États testés** : empty -> filled -> success
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-40_event_created.png`

---

## Phase 8 : Gestion des tâches (étapes 41-43)

---

### Étape 41 : Ouvrir Tâches

**Priorité** : P0
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=tasks`
2. `wait_for` -> `[data-testid="tasks-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A1-41_tasks_panel.png`

**Résultat attendu** : Le panneau Tâches s'ouvre. L'interface affiche soit une vue liste (TaskList) soit un kanban (TaskKanban). Un bouton d'ajout de tâche est visible. L'interface est vide au premier lancement.
**États testés** : loaded, empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-41_tasks_panel.png`

---

### Étape 42 : Créer tâche "Envoyer maquettes Jean" deadline vendredi

**Priorité** : P0
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `find` -> bouton "Ajouter" ou "+" dans le panneau tâches
2. `click` -> ce bouton
3. `wait_for` -> formulaire TaskForm visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A1-42_task_form.png`
5. `find` -> champ titre de la tâche
6. `click` -> champ titre
7. `type` -> "Envoyer maquettes Jean"
8. `find` -> champ date limite (deadline/due_date)
9. `javascript_tool` -> calculer le vendredi de la semaine courante et le définir
10. `find` -> bouton Sauvegarder
11. `click` -> bouton Sauvegarder
12. `wait_for` -> la tâche apparaît dans la liste (max 3s)
13. `screenshot` -> `/tmp/therese-tests/A1-42_task_created.png`
14. `javascript_tool` -> vérifier que le texte "Envoyer maquettes Jean" est présent dans le DOM

**Résultat attendu** : La tâche est créée avec le titre "Envoyer maquettes Jean" et une deadline au vendredi. La tâche apparaît dans la liste/kanban avec le statut "A faire" ou "todo". La deadline est affichée de manière lisible. L'interface montre 1 tâche active.
**États testés** : empty -> filled -> success
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-42_task_created.png`

---

### Étape 43 : Marquer la tâche comme terminée

**Priorité** : P0
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `find` -> la tâche "Envoyer maquettes Jean" dans la liste
2. `find` -> checkbox ou bouton "Terminer" sur cette tâche
3. `click` -> checkbox/bouton terminer
4. `wait_for` -> la tâche change de statut (max 2s)
5. `screenshot` -> `/tmp/therese-tests/A1-43_task_completed.png`
6. `javascript_tool` -> vérifier que la tâche a un attribut checked, completed, done, ou qu'elle a changé de colonne (kanban)

**Résultat attendu** : La tâche est marquée comme terminée. L'affichage change : barré, grisé, déplacé dans une colonne "Fait", ou checkbox cochée. L'animation de complétion est fluide. La tâche reste visible (pas supprimée immédiatement). Sophie a la satisfaction de voir son travail terminé.
**États testés** : filled -> disabled (terminé)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-43_task_completed.png`

---

## Phase 9 : Board IA - délibération (étapes 44-46)

---

### Étape 44 : Ouvrir Board IA - bouton Board dans le header

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420`
2. `wait_for` -> page principale chargée (max 5s)
3. `find` -> bouton Board dans le header (icône Gavel ou texte "Board")
4. `click` -> bouton Board
5. `wait_for` -> `[data-testid="board-panel"]` visible (max 5s)
6. `screenshot` -> `/tmp/therese-tests/A1-44_board_panel.png`

**Résultat attendu** : Le panneau Board IA s'ouvre. L'interface affiche un champ de saisie pour poser une question aux conseillers IA. Le mode de délibération est sélectionnable (rapide, approfondi, etc.). Les 5 conseillers sont présentés ou décrits. L'ambiance est "conseil d'administration privé".
**États testés** : loaded, empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-44_board_panel.png`

---

### Étape 45 : Poser une question "Dois-je augmenter mes tarifs ?"

**Priorité** : P0
**Pré-condition** : Clé API valide configurée (sinon tester uniquement l'envoi et l'erreur)
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> champ de saisie dans le board (textarea ou input)
2. `click` -> champ de saisie
3. `type` -> "Dois-je augmenter mes tarifs de graphiste freelance ?"
4. `screenshot` -> `/tmp/therese-tests/A1-45_board_question.png`
5. `find` -> `[data-testid="board-submit-btn"]`
6. `click` -> `[data-testid="board-submit-btn"]`
7. `wait_for` -> début de la délibération ou erreur (max 15s)
8. `screenshot` -> `/tmp/therese-tests/A1-45_board_deliberating.png`

**Résultat attendu** : La question est saisie dans le champ. Le clic sur le bouton de soumission lance la délibération. Avec une clé valide : les 5 conseillers commencent à répondre (streaming). Sans clé : un message d'erreur explicite apparaît. L'interface montre l'état "en cours de délibération".
**États testés** : filled, loading
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-45_board_deliberating.png`

---

### Étape 46 : Voir la délibération des 5 conseillers

**Priorité** : P1
**Pré-condition** : Clé API valide et délibération en cours/terminée
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `wait_for` -> `[data-testid="board-result"]` visible (max 120s - la délibération peut être longue)
2. `screenshot` -> `/tmp/therese-tests/A1-46_board_result.png`
3. `javascript_tool` -> vérifier la présence des cartes des conseillers (AdvisorCard) - au moins 3 visibles
4. `javascript_tool` -> vérifier qu'une synthèse (SynthesisCard) est affichée
5. `screenshot` -> `/tmp/therese-tests/A1-46_board_synthesis.png`

**Résultat attendu** : Les 5 conseillers ont répondu. Chaque conseiller a sa carte (AdvisorCard) avec son rôle, son avis, ses arguments. La disposition en arc (AdvisorArcLayout) est élégante. Une synthèse (SynthesisCard) résume les positions. Sophie obtient des perspectives variées sur sa question tarifaire. Le rendu est professionnel et lisible.
**États testés** : filled (résultats complets)
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-46_board_result.png`

---

## Phase 10 : Fonctionnalités transverses (étapes 47-48)

---

### Étape 47 : Raccourci Ctrl+K - Command Palette

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420`
2. `wait_for` -> `[data-testid="chat-message-input"]` visible (max 5s)
3. `javascript_tool` -> `document.dispatchEvent(new KeyboardEvent('keydown', {key: 'k', ctrlKey: true, bubbles: true}))`
4. `wait_for` -> Command Palette visible (max 2s)
5. `screenshot` -> `/tmp/therese-tests/A1-47_command_palette.png`
6. `javascript_tool` -> vérifier que la palette contient des commandes (Nouvelle conversation, Paramètres, Board, Email, etc.)
7. `find` -> champ de recherche dans la palette
8. `type` -> "nouveau"
9. `wait_for` -> filtrage des commandes (max 1s)
10. `screenshot` -> `/tmp/therese-tests/A1-47_palette_filtered.png`
11. `javascript_tool` -> `document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}))`
12. `wait_for` -> palette fermée (max 1s)

**Résultat attendu** : Le raccourci Ctrl+K ouvre la Command Palette (modal de commandes rapides). La palette liste les actions disponibles : Nouvelle conversation, Ouvrir paramètres, Board, Email, Calendrier, Tâches, CRM, Factures. La recherche filtre en temps réel. Escape ferme la palette. Nota : en mode Vitest jsdom, utiliser `ctrlKey` (pas `metaKey`).
**États testés** : loaded, filled (filtré), hover
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-47_command_palette.png`

---

### Étape 48 : Export RGPD données - settings > data > exporter

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="settings-btn"]`
2. `click` -> `[data-testid="settings-btn"]`
3. `wait_for` -> `[data-testid="settings-modal"]` visible (max 3s)
4. `find` -> `[data-testid="settings-tab-data"]`
5. `click` -> `[data-testid="settings-tab-data"]`
6. `wait_for` -> contenu onglet Data visible (max 2s)
7. `screenshot` -> `/tmp/therese-tests/A1-48_settings_data_tab.png`
8. `find` -> bouton "Exporter" ou "Export RGPD" ou "Télécharger mes données"
9. `click` -> bouton Export
10. `wait_for` -> téléchargement ou confirmation (max 10s)
11. `screenshot` -> `/tmp/therese-tests/A1-48_rgpd_export.png`
12. `javascript_tool` -> vérifier qu'un fichier a été téléchargé ou qu'un message de confirmation apparaît

**Résultat attendu** : L'onglet Data des paramètres est accessible. Le bouton d'export RGPD est visible et clairement libellé. Le clic déclenche l'export de toutes les données de Sophie (contacts, conversations, tâches, factures, etc.) au format JSON ou ZIP. Un toast de confirmation apparaît. Le fichier est conforme RGPD (données personnelles incluses, format lisible).
**États testés** : loaded, loading (export en cours), success
**Si FAIL** : Screenshot `/tmp/therese-tests/A1-48_rgpd_export.png`

---

## Récapitulatif des priorités

| Priorité | Étapes | Count |
|----------|--------|-------|
| P0 | 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 16, 18, 21, 24, 26, 27, 30, 32, 33, 35, 36, 38, 40, 41, 42, 43, 44, 45, 48 | 31 |
| P1 | 8, 9, 15, 17, 19, 20, 22, 23, 25, 28, 29, 31, 34, 37, 39, 46, 47 | 17 |
| P2 | - | 0 |

## Matrice de couverture

| Module | Étapes | État vide | État rempli | État erreur | État loading |
|--------|--------|-----------|-------------|-------------|--------------|
| SplashScreen | 1 | - | - | - | oui |
| Onboarding | 2-10 | oui | oui | oui | - |
| Chat | 11-12, 18-20 | oui | oui | oui | oui |
| Settings | 13-17, 48 | oui | oui | - | oui |
| Sidebar | 21-23 | oui | oui | - | - |
| Mémoire | 24-29 | oui | oui | - | - |
| CRM | 30-32 | oui | oui | - | - |
| Factures | 33-37 | oui | oui | - | oui |
| Calendrier | 38-40 | oui | oui | - | - |
| Tâches | 41-43 | oui | oui | - | - |
| Board IA | 44-46 | oui | oui | oui | oui |
| Command Palette | 47 | - | oui | - | - |
| RGPD | 48 | - | - | - | oui |

## data-testid référencés

```
app-main
onboarding-wizard
onboarding-step-0 .. onboarding-step-5
onboarding-next-btn
onboarding-skip-btn
onboarding-prev-btn
onboarding-complete-btn
chat-message-input
chat-send-btn
chat-message-list
chat-message-item
chat-attach-btn
chat-voice-btn
sidebar
sidebar-new-conversation-btn
sidebar-search-input
sidebar-conversation-list
sidebar-conversation-item
settings-btn
settings-modal
settings-tab-llm
settings-tab-data
settings-close-btn
settings-save-btn
memory-panel
memory-search-input
memory-add-contact-btn
board-panel
board-submit-btn
board-result
tasks-panel
crm-panel
invoices-panel
calendar-panel
update-banner
```

## Pré-requis d'exécution

1. `make dev` lancé (backend :17293 + frontend :1420)
2. Base SQLite vierge (`rm ~/.therese/therese.db` avant le test)
3. localStorage vidé (ouvrir la console, `localStorage.clear()`)
4. Chrome avec extension Claude-in-Chrome ou Chrome DevTools MCP actif
5. Dossier screenshots créé : `mkdir -p /tmp/therese-tests`
6. (Optionnel) Clé API valide pour les étapes 19, 45, 46

## Durée estimée

- Parcours complet (48 étapes) : ~25-35 minutes
- P0 uniquement (31 étapes) : ~15-20 minutes
- Sans clé API (skip 19, 45, 46) : retrancher ~5 minutes
