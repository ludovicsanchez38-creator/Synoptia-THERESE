# Protocole de test - Persona A3 : Léa Moreau, coach business (power user)

> **Recette de la bêta 0.85, 25/11/2026.** Le banc navigateur utilise un moteur de test sur `127.0.0.1:17394` et une base jetable. Les étapes natives demandent une installation de test sur le système visé. Les écrans et les actions décrits ci-dessous suivent la recette du cycle 6.

> Version : 1.0 | Date : 2026-03-27
> App : THERESE Desktop (Tauri 2.0, React, Python FastAPI)
> URL dev : http://localhost:1420 | Moteur du banc : http://127.0.0.1:17394
> Pré-requis : `make dev` lancé, backend healthy, base SQLite **avec données existantes**

## Profil persona

| Champ | Valeur |
|-------|--------|
| Nom | Léa Moreau |
| Age | 34 ans |
| Métier | Coach business indépendante |
| OS | macOS |
| Niveau tech | Power user, à l'aise avec les clés API, les raccourcis clavier, la config avancée |
| Objectif | Exploiter 100% de l'app : Board IA quotidien, multi-LLM, CRM, facturation, Skills Office |
| Contexte | Profil configuré, contact et tâche fictifs, compte Anthropic sur le banc |

## Convention de nommage screenshots

Tous les screenshots FAIL vont dans `/tmp/therese-tests/` avec le format :
`A3-{NN}_{slug}.png` (ex: `A3-01_dashboard.png`)

## Dossier screenshots

```bash
mkdir -p /tmp/therese-tests
```

## Pré-conditions globales (Léa = app déjà configurée)

Le banc prépare un profil Léa avec la mise en route validée, un contact fictif et une tâche. La clé Anthropic permet le chat et les deux modèles utilisés par la recette. La délibération à cinq exige les comptes des cinq conseillers.

---

## Phase 1 : Lancement et dashboard (étapes 1-3)

---

### Étape 1 : Lire le brief avec un profil configuré

**Priorité** : P0
**URL** : http://localhost:1420

**Pré-conditions** :
- App déjà configurée (onboarding complété)
- Données existantes en base (contacts, tâches, factures, événements)

**Actions Chrome MCP** :
1. Démarre avec le profil Léa, un contact fictif et une tâche fictive.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : L’accueil affiche le profil, la date et le résumé permis par les données présentes.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-01_dashboard.png`

---

### Étape 2 : Lire la date et les signaux du brief

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Vérifie la date, le résumé et les actions prioritaires.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Les données chargées et les sources éventuellement indisponibles se distinguent.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-02_dashboard_kpis.png`

---

### Étape 3 : Dashboard - naviguer vers le chat

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> lien ou bouton de navigation vers le chat dans le dashboard ou la sidebar
2. `click` -> ce lien/bouton
3. `wait_for` -> `[data-testid="chat-message-input"]` visible (max 5s)
4. `screenshot` -> `/tmp/therese-tests/A3-03_navigate_chat.png`

**Résultat attendu** : Léa quitte le dashboard et arrive sur l'interface de chat. Les conversations existantes sont visibles dans la sidebar. L'input de chat est prêt à l'emploi. La transition est fluide.
**États testés** : loaded, filled (conversations existantes)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-03_navigate_chat.png`

---

## Phase 2 : Chat avancé et raccourcis (étapes 4-8)

> **Sidebar fermée par défaut (depuis 11/06/2026)** : la sidebar conversations
> n'est plus ouverte au lancement (l'app atterrit sur l'Accueil). Avant toute
> action sur un `[data-testid="sidebar-*"]`, l'ouvrir :
> `javascript_tool` -> `window.__therese.stores.panel.getState().togglePanel('conversationSidebar')`
> (ou raccourci ⌘B/Ctrl+B), puis `wait_for` -> `[data-testid="sidebar"]` visible.

---

### Étape 4 : Raccourci Ctrl+N - nouvelle conversation

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> `document.querySelectorAll('[data-testid="sidebar-conversation-item"]').length` (compter les conversations avant)
2. `javascript_tool` -> `const mod = navigator.platform.toUpperCase().indexOf('MAC') >= 0 ? 'metaKey' : 'ctrlKey'; document.dispatchEvent(new KeyboardEvent('keydown', {key: 'n', [mod]: true, bubbles: true}))`  <!-- Cmd sur macOS, Ctrl ailleurs : useKeyboardShortcuts.ts:40 lit `event.metaKey` des que navigator.platform contient MAC -->
3. `wait_for` -> nouvelle conversation créée (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A3-04_ctrl_n_new_conv.png`
5. `javascript_tool` -> vérifier que l'input chat est vide et focusé
6. `javascript_tool` -> vérifier que la liste des conversations dans la sidebar a augmenté de 1

**Résultat attendu** : Le raccourci Ctrl+N crée instantanément une nouvelle conversation. L'input de chat est vide et prêt à l'emploi (auto-focus). La sidebar montre la nouvelle conversation en haut de la liste (sélectionnée). Les anciennes conversations restent accessibles.
**États testés** : empty (nouvelle conv), filled (sidebar avec historique)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-04_ctrl_n_new_conv.png`

---

### Étape 5 : Changer de modèle depuis le composeur

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Ouvre Modèle de conversation.
2. Choisis Claude Haiku 5.5. Lis la puce, puis remets Sonnet 5.5 pour la suite.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le sélecteur affiche les modèles du service actif. La puce affiche le nouveau modèle. Le choix est enregistré sans rechargement.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-05_model_changed.png`

---

### Étape 6 : Message long (500+ caractères) - pas de troncature

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="chat-message-input"]`
2. `type` -> "Je suis en train de préparer un programme de coaching business pour des entrepreneurs qui veulent structurer leur activité. Le programme comprend 6 séances individuelles sur 3 mois, avec des livrables à chaque étape : bilan de compétences, étude de marché, business plan simplifié, stratégie de pricing, plan de communication, et plan d'action sur 90 jours. J'ai besoin que tu me fasses une proposition détaillée pour chaque séance avec les objectifs pédagogiques, les exercices pratiques, et les livrables attendus. Le tarif global est de 2 400 euros HT. Mes clients sont principalement des consultants, freelances et thérapeutes qui ont entre 1 et 5 ans d'activité."
3. `screenshot` -> `/tmp/therese-tests/A3-06_long_message_typed.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="chat-message-input"]').value.length >= 500`
5. `click` -> `[data-testid="chat-send-btn"]`
6. `wait_for` -> message utilisateur affiché dans la liste (max 3s)
7. `screenshot` -> `/tmp/therese-tests/A3-06_long_message_sent.png`
8. `javascript_tool` -> vérifier que le dernier `[data-testid="chat-message-item"]` contient le texte complet (au moins "plan d'action sur 90 jours")

**Résultat attendu** : Le message de 500+ caractères est saisi intégralement dans l'input (textarea auto-resize). Après envoi, le message complet apparaît dans la bulle utilisateur sans troncature. Tout le texte est lisible. L'input se vide après envoi.
**États testés** : filled (input), loaded (message affiché)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-06_long_message_sent.png`

---

### Étape 7 : Message avec code - rendu syntax highlighting

**Priorité** : P1
**URL** : http://localhost:1420

**Pré-condition** : Clé API valide configurée (sinon attendre la réponse d'erreur et vérifier le rendu du message utilisateur uniquement)

**Actions Chrome MCP** :
1. `click` -> `[data-testid="chat-message-input"]`
2. `type` -> "Voici mon script de calcul de TVA :\n```python\ndef calcul_tva(montant_ht, taux=20):\n    tva = montant_ht * taux / 100\n    ttc = montant_ht + tva\n    return {'ht': montant_ht, 'tva': tva, 'ttc': ttc}\n\nprint(calcul_tva(2400))\n```\nEst-ce correct ?"
3. `click` -> `[data-testid="chat-send-btn"]`
4. `wait_for` -> message affiché dans la liste (max 5s)
5. `screenshot` -> `/tmp/therese-tests/A3-07_code_message.png`
6. `javascript_tool` -> vérifier la présence d'un élément `<pre>` ou `<code>` ou `.hljs` dans le dernier message
7. `javascript_tool` -> vérifier que le texte "calcul_tva" est visible dans un bloc de code

**Résultat attendu** : Le bloc de code Python est rendu avec syntax highlighting (coloration syntaxique). Les mots-clés (`def`, `return`, `print`) sont colorés différemment des variables. Le texte hors code ("Voici mon script" et "Est-ce correct ?") est affiché normalement. Le bloc de code est visuellement distinct (fond différent, police monospace).
**États testés** : filled (rendu markdown)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-07_code_message.png`

---

### Étape 8 : Vérifier le rendu Markdown

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Demande une liste de trois tâches de préparation, avec le titre de chaque tâche en gras.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : La réponse affiche trois éléments en liste et leurs titres en gras.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-08_markdown_message.png`

---

## Phase 3 : Command Palette et navigation rapide (étapes 9-10)

---

### Étape 9 : Raccourci Ctrl+K - Command Palette - rechercher "facture"

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> `const mod = navigator.platform.toUpperCase().indexOf('MAC') >= 0 ? 'metaKey' : 'ctrlKey'; document.dispatchEvent(new KeyboardEvent('keydown', {key: 'k', [mod]: true, bubbles: true}))`  <!-- Cmd sur macOS, Ctrl ailleurs : useKeyboardShortcuts.ts:40 lit `event.metaKey` des que navigator.platform contient MAC -->
2. `wait_for` -> Command Palette visible (max 2s)
3. `screenshot` -> `/tmp/therese-tests/A3-09_command_palette_open.png`
4. `javascript_tool` -> vérifier que la palette contient des commandes listées
5. `find` -> champ de recherche dans la palette
6. `type` -> "facture"
7. `wait_for` -> filtrage des commandes (max 1s)
8. `screenshot` -> `/tmp/therese-tests/A3-09_palette_search_facture.png`
9. `javascript_tool` -> vérifier qu'au moins 1 résultat contient "facture" ou "invoice"

**Résultat attendu** : Le raccourci Ctrl+K ouvre instantanément la Command Palette. La palette est un modal centré avec un champ de recherche en haut. La saisie de "facture" filtre les commandes en temps réel. Au moins une commande liée aux factures apparaît (ex: "Ouvrir Factures", "Nouvelle facture").
**États testés** : loaded, filled (filtrée)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-09_palette_search_facture.png`

---

### Étape 10 : Ouvrir Devis et factures depuis la recherche

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Dans la recherche de facture, choisis Ouvrir les Devis et factures dans Commandes de l’application.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : La palette se ferme et le panneau Devis et factures s’ouvre. Le résultat distinct Facturer un client mène à la capacité métier.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-10_palette_navigate_invoices.png`

---

## Phase 4 : Réglages, neuf rubriques (étapes 11-19)

---

### Étape 11 : Raccourci Ctrl+, (ou bouton) - ouvrir Settings

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> `const mod = navigator.platform.toUpperCase().indexOf('MAC') >= 0 ? 'metaKey' : 'ctrlKey'; document.dispatchEvent(new KeyboardEvent('keydown', {key: ',', [mod]: true, bubbles: true}))`  <!-- Cmd sur macOS, Ctrl ailleurs : useKeyboardShortcuts.ts:40 lit `event.metaKey` des que navigator.platform contient MAC -->
2. `wait_for` -> `[data-testid="settings-modal"]` visible (max 3s)
3. `screenshot` -> `/tmp/therese-tests/A3-11_settings_open.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="settings-modal"]') !== null`

**Résultat attendu** : Le raccourci Ctrl+, ouvre le modal Settings. Si le raccourci ne fonctionne pas, fallback : cliquer sur `button[aria-label="Paramètres"]`. Le modal s'ouvre avec animation. L'onglet par défaut (Profil) est sélectionné.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-11_settings_open.png`

---

### Étape 12 : Parcourir les neuf rubriques des réglages

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Ouvre Paramètres et active le Mode Contributeur pour voir les rubriques avancées.
2. Ouvre successivement Profil, Service d’IA, Services et connecteurs, Accessibilité et affichage, Outils, Agents, Sécurité et confidentialité, Avancé et À propos et mise à jour.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Les neuf rubriques sont accessibles et présentent chacune leur contenu.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-12_tab_about.png`

---

### Étape 13 : Identifier Claude dans Service d’IA

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Ouvre Paramètres > Service d’IA. Repère le service configuré et son modèle.
2. Lis l’état des autres services de ce banc à un seul compte.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Claude porte les indications Actif et Clé enregistrée. Les autres services sans compte sont signalés comme tels. Le modèle appartient au service choisi.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-13_ai_providers.png`

---

### Étape 14 : Modifier le modèle dans Service d’IA

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Choisis Claude Haiku 5.5 et vérifie la persistance.
2. Reviens à Sonnet 5.5. Règle l’effort sur Faible et envoie un message de recette.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le modèle et l’effort enregistrés sont utilisés par le prochain tour. Les réglages s’appliquent depuis cette rubrique.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-14_model_default_changed.png`

---

### Étape 15 : Settings > Services - vérifier Brave Search

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="settings-tab-services"]`
2. `wait_for` -> contenu onglet Services visible (max 2s)
3. `screenshot` -> `/tmp/therese-tests/A3-15_services_brave.png`
4. `javascript_tool` -> vérifier la présence d'un élément mentionnant "Brave" ou "Search"
5. `javascript_tool` -> vérifier si un toggle ou indicateur de statut est présent pour Brave Search

**Résultat attendu** : L'onglet Services affiche Brave Search parmi les services configurables. Le statut (actif/inactif) est clairement visible. La clé API Brave est configurable depuis cet onglet. Les explications sont claires sur ce que permet le service (recherche web en temps réel).
**États testés** : loaded, filled (si Brave configuré)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-15_services_brave.png`

---

### Étape 16 : Settings > Privacy - voir les options RGPD

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="settings-tab-privacy"]`
2. `wait_for` -> contenu onglet Privacy visible (max 2s)
3. `screenshot` -> `/tmp/therese-tests/A3-16_privacy_rgpd.png`
4. `javascript_tool` -> vérifier la présence de texte mentionnant "RGPD", "données", "export", "anonymisation" ou "suppression"
5. `javascript_tool` -> vérifier la présence de boutons d'action (export, supprimer, anonymiser)

**Résultat attendu** : L'onglet Privacy affiche les options RGPD : export des données, anonymisation, suppression. Les textes explicatifs sont en français. Les boutons d'action sont clairement libellés. Les actions destructives (suppression) ont un avertissement visuel (rouge, confirmation requise).
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-16_privacy_rgpd.png`

---

### Étape 17 : Changer le comportement au lancement

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Dans Paramètres, active le Mode Contributeur.
2. Ouvre Avancé > Comportement au lancement, puis bascule Ouvrir sur le chat directement.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : L’interrupteur change d’état. Le choix détermine la surface initiale au prochain lancement.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-17_advanced_toggled.png`

---

### Étape 18 : Settings > About - vérifier la version

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="settings-tab-about"]`
2. `wait_for` -> contenu onglet About visible (max 2s)
3. `screenshot` -> `/tmp/therese-tests/A3-18_about_version.png`
4. `javascript_tool` -> vérifier la présence d'un numéro de version (format X.Y.Z, ex: "0.9.0" ou "0.8.0")
5. `javascript_tool` -> vérifier la présence du texte "THERESE" ou "Thérèse"

**Résultat attendu** : L'onglet About affiche le nom de l'application (THERESE), la version actuelle (format semver), et potentiellement les crédits, le lien GitHub, et les licences. Le numéro de version est lisible et correspond à la version déployée.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-18_about_version.png`

---

### Étape 19 : Fermer les réglages

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Après enregistrement du modèle et sélection du comportement, clique sur Fermer.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : L’interface du paramètre concerné confirme la modification. La fenêtre principale redevient accessible.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-19_settings_closed.png`

---

## Phase 5 : Mémoire - contacts et projets (étapes 20-25)

---

### Étape 20 : Ouvrir les contacts de la Mémoire

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Ouvre Mémoire depuis l’espace de travail.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le contact fictif du profil s’affiche. Le champ de recherche et le bouton Nouveau contact sont disponibles.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-20_memory_panel.png`

---

### Étape 21 : Mémoire - rechercher un contact existant

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="memory-search-input"]`
2. `click` -> `[data-testid="memory-search-input"]`
3. `type` -> nom d'un contact existant (ex: "Dupont" ou premier contact visible)
4. `wait_for` -> résultats filtrés (max 2s)
5. `screenshot` -> `/tmp/therese-tests/A3-21_memory_search.png`
6. `javascript_tool` -> vérifier que les résultats contiennent le terme recherché
7. `javascript_tool` -> vérifier que les contacts non pertinents sont masqués

**Résultat attendu** : La recherche filtre les contacts en temps réel. Le contact recherché apparaît dans les résultats. Les contacts ne correspondant pas au terme sont masqués. Le filtrage est instantané (pas de délai perceptible).
**États testés** : filled (résultats filtrés)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-21_memory_search.png`

---

### Étape 22 : Éditer un contact - modifier le téléphone

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> le contact trouvé dans la recherche
2. `click` -> ce contact (ouvrir la fiche)
3. `wait_for` -> fiche du contact visible (max 2s)
4. `screenshot` -> `/tmp/therese-tests/A3-22_contact_fiche.png`
5. `find` -> bouton "Éditer" ou "Modifier" ou icône crayon
6. `click` -> bouton Éditer
7. `find` -> champ téléphone
8. `click` -> champ téléphone
9. `javascript_tool` -> vider le champ téléphone
10. `type` -> "06 12 34 56 78"
11. `screenshot` -> `/tmp/therese-tests/A3-22_contact_phone_edited.png`

**Résultat attendu** : La fiche du contact s'ouvre avec toutes les informations. Le mode édition est activé. Le champ téléphone est modifiable. Le nouveau numéro "06 12 34 56 78" est saisi. Les autres champs restent inchangés.
**États testés** : filled, focus (édition)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-22_contact_phone_edited.png`

---

### Étape 23 : Sauvegarder le contact modifié

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> bouton "Sauvegarder" ou "Enregistrer"
2. `click` -> bouton Sauvegarder
3. `wait_for` -> confirmation de sauvegarde (toast ou retour en mode lecture) (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A3-23_contact_saved.png`
5. `javascript_tool` -> vérifier que le numéro "06 12 34 56 78" est affiché dans la fiche (mode lecture)

**Résultat attendu** : La modification est sauvegardée. Un toast de confirmation apparaît ou le mode lecture est réactivé. Le téléphone "06 12 34 56 78" est visible dans la fiche. La modification est persistée en base SQLite.
**États testés** : loading (sauvegarde), success, filled (mode lecture)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-23_contact_saved.png`

---

### Étape 24 : Ouvrir la création d’un projet

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Ouvre Nouveau projet, puis saisis « Lancement coaching Q2 ».
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le titre et le champ Contact associé sont disponibles avant l’enregistrement.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-24_project_created.png`

---

### Étape 25 : Associer le contact au projet

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Sélectionne Éva Pilote dans Contact associé, puis clique sur Créer.
2. Vérifie que le projet est enregistré avec ce contact.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le projet est sauvegardé et la relation avec le contact sélectionné est conservée.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-25_project_linked.png`

---

## Phase 6 : CRM (étapes 26-30)

---

### Étape 26 : Ouvrir Pipeline

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. Ouvre Pipeline depuis l’espace de travail.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Les colonnes Contact, Découverte, Proposition, Signature, Livraison, Actif, Perdu et Archive affichent leurs compteurs.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-26_crm_panel.png`

---

### Étape 27 : CRM - voir le pipeline avec des leads existants

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier la présence de colonnes pipeline (au moins 3 colonnes)
2. `javascript_tool` -> compter le nombre de leads (cartes) dans le pipeline
3. `screenshot` -> `/tmp/therese-tests/A3-27_crm_pipeline.png`
4. `javascript_tool` -> vérifier que chaque colonne a un titre visible

**Résultat attendu** : Le pipeline Kanban est structuré en colonnes avec des titres explicites. Les leads existants sont positionnés dans les bonnes colonnes. Chaque carte de lead affiche le nom du contact, le montant estimé, et le statut. L'interface est visuellement claire.
**États testés** : filled (pipeline avec leads)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-27_crm_pipeline.png`

---

### Étape 28 : Créer un contact commercial

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. Dans Nouveau contact, renseigne Julie Exemple, Atelier Test, e-mail et téléphone fictifs.
2. Enregistre la fiche. Pour une prestation chiffrée, utilise Nouvelle prestation dans sa fiche.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le contact apparaît dans le Pipeline. Les renseignements d’un contact et ceux d’une prestation ont des formulaires distincts.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-28_crm_lead_created.png`

---

### Étape 29 : Passer le contact en Proposition

**Priorité** : P1
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. Ouvre Julie Exemple et choisis Proposition dans Étape.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : La fiche quitte Contact et figure dans Proposition.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-29_crm_lead_moved.png`

---

### Étape 30 : Lire le score du contact

**Priorité** : P1
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. Lis l’indicateur Score dans le Pipeline et ouvre la fiche.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le CRM affiche le score calculé. La priorité ou le score ne se saisissent pas dans la fiche.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-30_crm_lead_scored.png`

---

## Phase 7 : Facturation multi-lignes (étapes 31-36)

---

### Étape 31 : Ouvrir Factures

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=invoices`
2. `wait_for` -> `[data-testid="invoices-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A3-31_invoices_panel.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="invoices-panel"]') !== null`
5. `javascript_tool` -> vérifier qu'au moins 1 facture/devis existant est affiché

**Résultat attendu** : Le panneau Factures s'affiche avec les documents existants de Léa. La liste montre les factures/devis avec leur statut (brouillon, envoyée, payée). Le bouton de création est visible.
**États testés** : loaded, filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-31_invoices_panel.png`

---

### Étape 32 : Créer une facture directe

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. Ouvre Nouveau devis ou facture, puis sélectionne Facture.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le formulaire de facture s’ouvre. Le client et les lignes sont éditables. Le numéro définitif vient à l’émission.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-32_invoice_type_facture.png`

---

### Étape 33 : Ajouter trois prestations

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. Saisis une séance de cadrage à 250 €, un coaching d’équipe à 400 € et une restitution à 180 €, quantité 1.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Les trois lignes conservent leurs champs indépendants de description, quantité et prix HT.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-33_invoice_3_lines.png`

---

### Étape 34 : Vérifier les totaux de la facture

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. Lis le HT, la TVA et le TTC avant d’enregistrer le brouillon.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Pour 830 € HT et 20 % de TVA, le formulaire affiche 166 € de TVA et 996 € TTC.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-34_invoice_totals.png`

---

### Étape 35 : Facture - générer PDF

**Priorité** : P1
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> bouton Sauvegarder dans le formulaire
2. `click` -> bouton Sauvegarder
3. `wait_for` -> facture sauvegardée (max 5s)
4. `find` -> la facture dans la liste
5. `click` -> la facture
6. `find` -> bouton "PDF" ou "Télécharger" ou icône PDF
7. `click` -> bouton PDF
8. `wait_for` -> téléchargement ou aperçu PDF (max 10s)
9. `screenshot` -> `/tmp/therese-tests/A3-35_invoice_pdf.png`

**Résultat attendu** : Le PDF de la facture est généré avec les 3 lignes, les totaux HT/TVA/TTC corrects, les coordonnées de Léa Moreau (coach business), et les mentions légales obligatoires. Le fichier est téléchargé ou affiché dans un viewer. Le format est professionnel.
**États testés** : loading (génération), success (PDF)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-35_invoice_pdf.png`

---

### Étape 36 : Enregistrer le passage du brouillon en Envoyée

**Priorité** : P1
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. Ouvre la ligne « Brouillon, numéro à l’émission » et choisis Envoyée dans Statut.
2. Utilise Mettre à jour, puis vérifie le numéro et le statut.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : La facture porte un numéro définitif et le statut enregistré. La manipulation simule le suivi de l’envoi sans envoyer de message.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-36_invoice_status_sent.png`

---

## Phase 8 : Calendrier multi-événements (étapes 37-40)

---

### Étape 37 : Ouvrir Calendrier

**Priorité** : P0
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=calendar`
2. `wait_for` -> `[data-testid="calendar-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A3-37_calendar_panel.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="calendar-panel"]') !== null`

**Résultat attendu** : Le panneau Calendrier s'affiche. La vue par défaut est le mois courant. La grille est correctement alignée. La date du jour est mise en évidence.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-37_calendar_panel.png`

---

### Étape 38 : Calendrier - passer en vue semaine

**Priorité** : P1
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `find` -> bouton "Semaine" ou "Week" dans les contrôles du calendrier
2. `click` -> bouton Semaine
3. `wait_for` -> vue semaine affichée (max 2s)
4. `screenshot` -> `/tmp/therese-tests/A3-38_calendar_week_view.png`
5. `javascript_tool` -> vérifier que la vue affiche 7 jours (lundi-dimanche ou dimanche-samedi)

**Résultat attendu** : La vue semaine s'affiche avec les 7 jours de la semaine courante. Les créneaux horaires sont visibles (grille horaire). La journée d'aujourd'hui est mise en évidence. La transition mois -> semaine est fluide.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-38_calendar_week_view.png`

---

### Étape 39 : Calendrier - créer 3 événements dans la même semaine

**Priorité** : P0
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `find` -> bouton "Nouveau" ou "+" ou clic sur un créneau
2. `click` -> bouton Nouveau
3. `wait_for` -> formulaire d'événement (max 3s)
4. `find` -> champ titre
5. `type` -> "Coaching Marie L. - Séance 1"
6. `find` -> champ date/heure début
7. `javascript_tool` -> définir date = lundi prochain 10h00
8. `find` -> champ durée ou heure fin
9. `javascript_tool` -> définir durée = 1h30
10. `find` -> bouton Sauvegarder
11. `click` -> Sauvegarder
12. `wait_for` -> événement créé (max 3s)
13. `screenshot` -> `/tmp/therese-tests/A3-39_event_1_created.png`
14. `click` -> bouton Nouveau (2ème événement)
15. `find` -> champ titre
16. `type` -> "Webinaire Pricing"
17. `javascript_tool` -> définir date = mercredi prochain 14h00, durée 2h
18. `find` -> bouton Sauvegarder
19. `click` -> Sauvegarder
20. `wait_for` -> événement créé (max 3s)
21. `click` -> bouton Nouveau (3ème événement)
22. `find` -> champ titre
23. `type` -> "Call prospect - Sophie D."
24. `javascript_tool` -> définir date = vendredi prochain 16h00, durée 30min
25. `find` -> bouton Sauvegarder
26. `click` -> Sauvegarder
27. `wait_for` -> événement créé (max 3s)
28. `screenshot` -> `/tmp/therese-tests/A3-39_three_events.png`

**Résultat attendu** : Les 3 événements sont créés et visibles dans la vue semaine : "Coaching Marie L." (lundi 10h), "Webinaire Pricing" (mercredi 14h), "Call prospect" (vendredi 16h). Chaque événement occupe le bon créneau horaire. Les événements ne se chevauchent pas visuellement.
**États testés** : empty (formulaire) x3, filled x3, success x3
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-39_three_events.png`

---

### Étape 40 : Calendrier - naviguer entre vues mois/semaine/jour

**Priorité** : P1
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `find` -> bouton "Mois" ou "Month"
2. `click` -> bouton Mois
3. `wait_for` -> vue mois (max 2s)
4. `screenshot` -> `/tmp/therese-tests/A3-40_view_month.png`
5. `find` -> bouton "Semaine" ou "Week"
6. `click` -> bouton Semaine
7. `wait_for` -> vue semaine (max 2s)
8. `screenshot` -> `/tmp/therese-tests/A3-40_view_week.png`
9. `find` -> bouton "Jour" ou "Day"
10. `click` -> bouton Jour
11. `wait_for` -> vue jour (max 2s)
12. `screenshot` -> `/tmp/therese-tests/A3-40_view_day.png`
13. `javascript_tool` -> vérifier que la vue jour affiche les événements du jour sélectionné

**Résultat attendu** : Les 3 vues sont accessibles et fonctionnelles. La vue mois montre la grille mensuelle avec les points/badges d'événements. La vue semaine montre la grille horaire sur 7 jours. La vue jour montre le planning détaillé d'une journée. Les transitions sont fluides. Les événements créés sont visibles dans chaque vue.
**États testés** : loaded (x3), filled (événements visibles)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-40_view_day.png`

---

## Phase 9 : Tâches multi-priorités (étapes 41-44)

---

### Étape 41 : Ouvrir Tâches

**Priorité** : P0
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=tasks`
2. `wait_for` -> `[data-testid="tasks-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A3-41_tasks_panel.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="tasks-panel"]') !== null`
5. `javascript_tool` -> vérifier la présence de tâches existantes (au moins 2)

**Résultat attendu** : Le panneau Tâches s'affiche avec les tâches existantes de Léa. La liste montre les tâches avec leur statut (à faire, en cours, terminée) et leur priorité. Le bouton de création est visible.
**États testés** : loaded, filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-41_tasks_panel.png`

---

### Étape 42 : Créer 5 tâches avec priorités différentes

**Priorité** : P0
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `find` -> bouton "Nouvelle tâche" ou "+"
2. `click` -> bouton Nouvelle tâche
3. `find` -> champ titre
4. `type` -> "Préparer support coaching Q2"
5. `find` -> sélecteur priorité
6. `javascript_tool` -> sélectionner "Haute" ou "High"
7. `find` -> champ deadline
8. `javascript_tool` -> définir deadline = dans 3 jours
9. `find` -> bouton Sauvegarder
10. `click` -> Sauvegarder
11. `wait_for` -> tâche créée (max 2s)
12. `click` -> bouton Nouvelle tâche
13. `find` -> champ titre
14. `type` -> "Envoyer facture Marie L."
15. `javascript_tool` -> sélectionner priorité "Urgente" ou "Critical"
16. `javascript_tool` -> définir deadline = demain
17. `click` -> Sauvegarder
18. `wait_for` -> tâche créée (max 2s)
19. `click` -> bouton Nouvelle tâche
20. `find` -> champ titre
21. `type` -> "Mettre à jour site web"
22. `javascript_tool` -> sélectionner priorité "Moyenne" ou "Medium"
23. `javascript_tool` -> définir deadline = dans 7 jours
24. `click` -> Sauvegarder
25. `wait_for` -> tâche créée (max 2s)
26. `click` -> bouton Nouvelle tâche
27. `find` -> champ titre
28. `type` -> "Répondre aux DMs Instagram"
29. `javascript_tool` -> sélectionner priorité "Basse" ou "Low"
30. `click` -> Sauvegarder
31. `wait_for` -> tâche créée (max 2s)
32. `click` -> bouton Nouvelle tâche
33. `find` -> champ titre
34. `type` -> "Planifier retraite été"
35. `javascript_tool` -> sélectionner priorité "Moyenne" ou "Medium"
36. `javascript_tool` -> définir deadline = dans 14 jours
37. `click` -> Sauvegarder
38. `wait_for` -> tâche créée (max 2s)
39. `screenshot` -> `/tmp/therese-tests/A3-42_five_tasks.png`
40. `javascript_tool` -> compter le nombre de tâches dans la liste (au moins 5 nouvelles + les existantes)

**Résultat attendu** : Les 5 tâches sont créées avec des priorités différentes : "Préparer support" (Haute), "Envoyer facture" (Urgente), "MAJ site" (Moyenne), "DMs Instagram" (Basse), "Retraite été" (Moyenne). Chaque tâche a un indicateur visuel de priorité (couleur, icône). Les deadlines sont configurées.
**États testés** : empty (formulaire) x5, filled x5, success x5
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-42_five_tasks.png`

---

### Étape 43 : Filtrer les tâches par priorité

**Priorité** : P1
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `find` -> sélecteur de filtre par priorité
2. `click` -> sélecteur de filtre
3. `javascript_tool` -> sélectionner "Haute" ou "Urgente"
4. `wait_for` -> liste filtrée (max 2s)
5. `screenshot` -> `/tmp/therese-tests/A3-43_tasks_filtered_high.png`
6. `javascript_tool` -> vérifier que seules les tâches haute/urgente priorité sont visibles
7. `javascript_tool` -> sélectionner "Toutes" pour reset
8. `wait_for` -> toutes les tâches réaffichées (max 1s)
9. `screenshot` -> `/tmp/therese-tests/A3-43_tasks_filter_reset.png`

**Résultat attendu** : Le filtre par priorité fonctionne correctement. La sélection "Haute/Urgente" n'affiche que les tâches correspondantes. Le reset "Toutes" réaffiche toutes les tâches. Le filtre est instantané (pas de rechargement).
**États testés** : filled (filtrée), filled (toutes)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-43_tasks_filter_reset.png`

---

### Étape 44 : Consulter les échéances en vue Liste

**Priorité** : P1
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. Ouvre Liste et relève les échéances affichées dans chaque ligne.
2. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Les dates sont lisibles. La liste ne propose pas de commande de tri par échéance.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-44_tasks_sorted_deadline.png`

---

## Phase 10 : Board IA (étapes 45-48)

---

### Étape 45 : Préparer la question stratégique

**Priorité** : P0
**URL** : http://localhost:1420/?panel=board

**Pré-condition** : Clé API valide configurée (au moins 1 provider)

**Actions Chrome MCP** :
1. Autorise le Board cloud dans Sécurité et confidentialité si nécessaire.
2. Saisis la question de tarification, puis clique sur Préparer le Board.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : La confirmation précise ce qui sera partagé. Le lancement effectif dépend des cinq services accessibles.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-45_board_question_sent.png`

---

### Étape 46 : Board - attendre les 5 conseillers

**Priorité** : P0
**URL** : http://localhost:1420/?panel=board

**Pré-condition** : Clé API valide, question envoyée à l'étape 45

**Actions Chrome MCP** :
1. `wait_for` -> `[data-testid="board-result"]` visible (max 120s)
2. `screenshot` -> `/tmp/therese-tests/A3-46_board_results_loading.png`
3. `javascript_tool` -> compter le nombre de réponses de conseillers affichées
4. `wait_for` -> 5 réponses de conseillers (max 180s total)
5. `screenshot` -> `/tmp/therese-tests/A3-46_board_5_advisors.png`
6. `javascript_tool` -> vérifier que chaque conseiller a un nom/rôle distinct
7. `javascript_tool` -> vérifier que chaque réponse contient du texte substantiel (> 50 caractères)

**Résultat attendu** : Les 5 conseillers IA répondent progressivement. Chaque conseiller a un rôle distinct (ex: Stratège, Financier, Marketing, RH, Juridique). Chaque avis contient une analyse pertinente de la question de pricing. Les réponses sont formatées (markdown). Le temps de chargement est signalé par des indicateurs de progression.
**États testés** : loading (progressif), filled (5 avis)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-46_board_5_advisors.png`

---

### Étape 47 : Board - voir la synthèse

**Priorité** : P1
**URL** : http://localhost:1420/?panel=board

**Actions Chrome MCP** :
1. `find` -> section "Synthèse" ou "Résumé" ou "Conclusion" dans le board
2. `screenshot` -> `/tmp/therese-tests/A3-47_board_synthesis.png`
3. `javascript_tool` -> vérifier la présence d'un bloc de synthèse (résumé des 5 avis)
4. `javascript_tool` -> vérifier que la synthèse contient un montant ou une fourchette de prix recommandée

**Résultat attendu** : Après les 5 avis individuels, une synthèse globale est générée. La synthèse résume les points de convergence et de divergence entre les conseillers. Une recommandation de tarif (fourchette ou montant) est proposée. Le format est clair et actionnable pour Léa.
**États testés** : filled (synthèse)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-47_board_synthesis.png`

---

### Étape 48 : Lire la disponibilité de l’export du Board

**Priorité** : P2
**URL** : http://localhost:1420/?panel=board

**Actions Chrome MCP** :
1. Ouvre Historique sur le Board.
2. Repère le bouton PDF.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le bouton « PDF Bientôt » est visible et désactivé. L’export PDF sera vérifié quand il sera disponible.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-48_board_exported.png`

---

## Phase 11 : Skills Office (étapes 49-50)

---

### Étape 49 : Générer le document Word des tâches

**Priorité** : P1
**URL** : http://localhost:1420

**Pré-condition** : Clé API valide, tâches existantes en mémoire

**Actions Chrome MCP** :
1. Demande toutes les tâches fictives à faire et en cours. Demande un Word avec titre, priorité, échéance et la mention non renseigné si une valeur manque.
2. Vérifie le format et le contenu dans « Confirmer la création du document ». Confirme, puis utilise la commande de téléchargement du fichier local.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le moteur génère un DOCX contenant les tâches. La carte propose Télécharger. Le dialogue d’enregistrement se vérifie dans une installation Tauri.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-49_skill_docx.png`

---

### Étape 50 : Générer le tableur Excel des factures

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Demande les factures d’Éva Pilote, brouillons compris, et les colonnes Client, Description, HT, TVA, TTC et Statut.
2. Vérifie le format dans « Confirmer la création du document », puis confirme et utilise le téléchargement.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : Le moteur génère un XLSX avec les colonnes et les valeurs disponibles. La carte propose Télécharger. Le dialogue d’enregistrement se vérifie dans une installation Tauri.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-50_skill_xlsx.png`

---

## Phase 12 : Navigation directe entre surfaces (étapes 51-53)

> B-074 (02/09/2026) : ces trois étapes dispatchaient Ctrl+1, Ctrl+2 et
> Ctrl+3. `useKeyboardShortcuts.ts` ne traite ces touches sur AUCUNE
> plateforme (il énumère k, n, `/`, `,`, m, b, d, e, t, i, p, o et les
> combos Shift, lignes 56-183) : l'étape exigeait une fonctionnalité
> absente et ne pouvait donc pas échouer pour la bonne raison. Le geste
> réellement câblé est le lien profond (`lib/deepLinks.ts`). Si un jour
> Ctrl+1/2/3 est implémenté, ces étapes redeviendront des raccourcis.

---

### Étape 51 : Retour direct au chat depuis un autre panneau

**Priorité** : P0
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=tasks`
2. `wait_for` -> `[data-testid="tasks-panel"]` visible (max 5s)
3. `navigate` -> `http://localhost:1420/?view=chat`
4. `wait_for` -> `[data-testid="chat-message-input"]` visible (max 3s)
5. `screenshot` -> `/tmp/therese-tests/A3-51_ctrl_1_chat.png`
6. `javascript_tool` -> vérifier que le panel actif est le chat (input visible, tasks masqué)

**Résultat attendu** : Depuis n'importe quel panneau, le lien profond `?view=chat` ramène au chat. L'input de chat est visible. Le panneau précédent (Tâches) ne l'est plus.
**États testés** : loaded (chat via raccourci)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-51_ctrl_1_chat.png`

---

### Étape 52 : Ouverture directe du panneau Mémoire

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?view=memory`
2. `wait_for` -> `[data-testid="memory-panel"]` visible (max 3s)
3. `screenshot` -> `/tmp/therese-tests/A3-52_ctrl_2_memory.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="memory-panel"]') !== null`

**Résultat attendu** : Le lien profond `?view=memory` ouvre le panneau Mémoire. Les contacts existants sont visibles. Le champ de recherche est prêt. La transition depuis le chat est fluide.
**États testés** : loaded, filled (contacts)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-52_ctrl_2_memory.png`

---

### Étape 53 : Ouverture directe du panneau Board

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=board`
2. `wait_for` -> `[data-testid="board-panel"]` visible (max 3s)
3. `screenshot` -> `/tmp/therese-tests/A3-53_ctrl_3_board.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="board-panel"]') !== null`

**Résultat attendu** : Le lien profond `?panel=board` ouvre le panneau Board IA. Les résultats précédents (question pricing) sont potentiellement visibles.
**États testés** : loaded (board via raccourci)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-53_ctrl_3_board.png`

---

## Phase 13 : Sécurité et RGPD (étapes 54-55)

---

### Étape 54 : XSS test - injection dans le chat

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?view=chat` (retour chat)
2. `wait_for` -> `[data-testid="chat-message-input"]` visible (max 3s)
3. `click` -> `[data-testid="chat-message-input"]`
4. `javascript_tool` -> armer le témoin AVANT l'injection, sinon le contrôle 9 ne peut pas échouer : `window.__xss_triggered = undefined; window.alert = () => { window.__xss_triggered = true; };`
5. `type` -> `<img src=x onerror=alert(1)>`
6. `click` -> `[data-testid="chat-send-btn"]`
7. `wait_for` -> message affiché dans la liste (max 5s)
8. `screenshot` -> `/tmp/therese-tests/A3-54_xss_test.png`
9. `javascript_tool` -> vérifier qu'aucun `alert` n'a été déclenché : `window.__xss_triggered === undefined` (le témoin posé à l'action 4 devient `true` dès qu'`alert` est appelé : sans lui, ce contrôle était toujours vrai)
10. `javascript_tool` -> vérifier que le message est affiché en texte brut (échappé) et non interprété comme HTML
11. `javascript_tool` -> `document.querySelectorAll('img[src="x"]').length === 0` (pas d'image injectée)
12. `type` -> `<script>document.title='HACKED'</script>`
13. `click` -> `[data-testid="chat-send-btn"]`
14. `wait_for` -> message affiché (max 5s)
15. `screenshot` -> `/tmp/therese-tests/A3-54_xss_script_test.png`
16. `javascript_tool` -> `document.title !== 'HACKED'` (le script n'a pas été exécuté)

**Résultat attendu** : Les deux tentatives XSS sont neutralisées. Le `<img src=x onerror=alert(1)>` est affiché en texte brut (échappé en `&lt;img...&gt;`) et non interprété comme HTML. Aucune alert() n'est déclenchée. Le `<script>` est aussi échappé. Le titre de la page reste inchangé. L'anti-injection est fonctionnel.
**États testés** : filled (message échappé), security
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-54_xss_script_test.png`

---

### Étape 55 : Exporter les données de Léa

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Ouvre Paramètres > Sécurité et confidentialité, puis Exporter toutes mes données.
2. Ouvre le fichier exporté hors réseau.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : L’export local s’enregistre et reste lisible.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-55_rgpd_export_done.png`

---

## Phase 14 : États d'erreur (étapes 56-60)

> **Ajoutée le 07/09/2026 (B-386).** La matrice de couverture ne portait aucun
> « État erreur » : en 55 étapes, le protocole ne faisait jamais échouer un
> appel, ne coupait jamais le moteur, ne fournissait jamais une clé invalide.
> Or la moitié des correctifs consignés dans le CLAUDE.md portent sur des
> erreurs mal présentées à l'écran. Ces cinq étapes visent des témoins qui
> existent dans le code (`data-testid` ou `role="alert"`) ; un témoin absent
> est un FAIL, pas une étape « sans objet ».

---

### Étape 56 : Lire l’erreur de clé refusée dans le chat

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Simule un HTTP 401 sur le transport d’Anthropic.
2. Envoie un message fictif et lis le résultat.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : L’erreur indique qu’une clé Anthropic est invalide ou expirée. Aucun texte de succès ne tient lieu de réponse.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-56_cle_invalide.png`

---

### Étape 57 : Aucun modèle actif - le composeur l'explique et bloque l'envoi

**Priorité** : P0
**URL** : http://localhost:1420

**Pré-condition** : aucune clé cloud valide et Ollama arrêté (ou le fournisseur courant pointé sur un modèle absent).

**Actions Chrome MCP** :
1. `javascript_tool` -> `window.__therese.runAction('chat.new')`
2. `wait_for` -> `[data-testid="chat-model-unavailable"]` visible (max 10s)
3. `screenshot` -> `/tmp/therese-tests/A3-57_sans_modele.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="chat-message-input"]').disabled === true`
5. `javascript_tool` -> `document.querySelector('[data-testid="chat-send-btn"]').disabled === true`
6. `javascript_tool` -> `document.querySelector('[data-testid="chat-model-unavailable"]').textContent`

**Résultat attendu** : Le bandeau « Choisis d'abord un modèle » est visible, avec un bouton vers les réglages IA (ou, si les réglages sont déjà ouverts, l'indication d'y choisir un modèle). L'envoi est impossible : champ et bouton désactivés. Aucune requête n'est envoyée au moteur.
**États testés** : error (aucun modèle)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-57_sans_modele.png`

---

### Étape 58 : Moteur arrêté - l'état est dit, rien ne passe pour « vide »

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. arrêter le backend de développement (Ctrl+C dans le terminal `make dev-backend`, ou `kill` du processus uvicorn :17293 - JAMAIS une instance installée)
2. `wait_for` -> l'indicateur de connexion affiche « Moteur arrêté » ou « Erreur du moteur » (max 20s)
3. `screenshot` -> `/tmp/therese-tests/A3-58_moteur_arrete.png`
4. `javascript_tool` -> `window.__therese.runAction('memory.open')`
5. `wait_for` -> `[data-testid="contacts-memory-error"]` ou un `[role="alert"]` visible (max 10s)
6. `screenshot` -> `/tmp/therese-tests/A3-58_contacts_erreur.png`
7. `javascript_tool` -> `[...document.querySelectorAll('[role="alert"]')].map(n => n.textContent).join(' | ')`
8. relancer le backend (`make dev-backend`)
9. `wait_for` -> l'indicateur affiche « Moteur actif » (max 30s)
10. `screenshot` -> `/tmp/therese-tests/A3-58_moteur_revenu.png`

**Résultat attendu** : L'arrêt du moteur est annoncé par l'indicateur de connexion. Les surfaces qui lisent le serveur affichent une erreur explicite (« Impossible de contacter le serveur » ou équivalent), jamais un état vide qui ferait croire à l'absence de données. Au retour du moteur, l'indicateur repasse à « Moteur actif » et les surfaces se rechargent sans redémarrer l'application.
**États testés** : error (moteur arrêté), recovery (moteur revenu)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-58_moteur_arrete.png`

---

### Étape 59 : Conserver l’agenda lors d’un échec de rafraîchissement

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Vérifie que Séance A est visible avant de simuler un échec.
2. Clique sur Synchroniser l’agenda. Lis l’état puis cherche à nouveau Séance A.
3. Enregistre une capture de l’état observé et relève le résultat.

**Résultat attendu** : L’écran signale un échec de synchronisation et conserve le rendez-vous déjà chargé.
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-59_agenda_conserve.png`

---

### Étape 60 : Tableau de bord - panne annoncée, pas « rien à faire »

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. arrêter le backend (comme à l'étape 58)
2. `javascript_tool` -> `window.__therese.runAction('home.open')`
3. `wait_for` -> `[data-testid="today-dashboard-error"]` visible (max 10s)
4. `screenshot` -> `/tmp/therese-tests/A3-60_dashboard_erreur.png`
5. `javascript_tool` -> `document.querySelector('[data-testid="today-dashboard-error"]').getAttribute('role') === 'alert'`
6. relancer le backend, `wait_for` -> le brief du jour se recharge (max 30s)
7. `screenshot` -> `/tmp/therese-tests/A3-60_dashboard_revenu.png`

**Résultat attendu** : Le brief du jour affiche une erreur explicite tant que le moteur ne répond pas ; il n'affiche jamais « rien à faire aujourd'hui » à la place d'une panne. Si une seule source est en panne (agenda, e-mail) alors que le reste répond, le témoin `today-dashboard-indisponible` nomme la source manquante. Au retour du moteur, le brief se recharge.
**États testés** : error (moteur arrêté), partial (source indisponible), recovery
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-60_dashboard_erreur.png`

---

## Récapitulatif des priorités

| Priorité | Étapes | Count |
|----------|--------|-------|
| P0 | 1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 19, 20, 24, 26, 27, 28, 31, 32, 33, 34, 37, 39, 41, 42, 45, 46, 51, 52, 54, 55, 56, 57, 58 | 33 |
| P1 | 2, 7, 8, 14, 15, 16, 17, 18, 21, 22, 23, 25, 29, 30, 35, 36, 38, 40, 43, 44, 47, 49, 50, 53, 59, 60 | 26 |
| P2 | 48 | 1 |

## Matrice de couverture

| Module | Étapes | État vide | État rempli | État erreur | État loading |
|--------|--------|-----------|-------------|-------------|--------------|
| Dashboard | 1-3, 60 | - | oui | oui (60) | - |
| Chat | 4, 6-8, 54, 57 | oui | oui | oui (57) | - |
| Chat (LLM) | 6 | - | oui | - | oui |
| Command Palette | 9-10 | - | oui | - | - |
| Settings (8 tabs) | 11-19, 56 | - | oui | oui (56) | oui |
| Mémoire | 20-25, 58 | oui | oui | oui (58) | - |
| CRM | 26-30 | oui | oui | - | - |
| Factures | 31-36 | oui | oui | - | oui |
| Calendrier | 37-40, 59 | oui | oui | oui (59) | - |
| Tâches | 41-44 | oui | oui | - | - |
| Board IA | 45-48 | oui | oui | - | oui |
| Skills Office | 49-50 | - | oui | - | oui |
| Raccourcis | 4, 9, 11, 51-53 | - | oui | - | - |
| Sécurité XSS | 54 | - | oui | - | - |
| RGPD | 55 | - | - | - | oui |
| Moteur (connexion) | 58 | - | - | oui (58) | oui (retour) |

## data-testid référencés

```
app-main
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
settings-modal
settings-tab-profile
settings-tab-ai
settings-tab-services
settings-tab-tools
settings-tab-agents
settings-tab-privacy
settings-tab-advanced
settings-tab-about
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
email-panel
calendar-panel
update-banner
```

## Pré-requis d'exécution

1. `make dev` lancé (backend :17293 + frontend :1420)
2. Base SQLite **pré-peuplée** (contacts, conversations, tâches, factures, projets)
3. 3 clés API configurées (Anthropic, OpenAI, Gemini) - vraies pour étapes 45-50, fausses pour le reste
4. localStorage avec flag onboarding complété
5. Chrome avec extension Claude-in-Chrome ou Chrome DevTools MCP actif
6. Dossier screenshots créé : `mkdir -p /tmp/therese-tests`

## Durée estimée

- Parcours complet (55 étapes) : ~40-55 minutes
- P0 uniquement (30 étapes) : ~20-30 minutes
- Sans Board IA (skip 45-48) : retrancher ~10 minutes
- Sans Skills Office (skip 49-50) : retrancher ~5 minutes
- Sans clé API valide (skip 45-50) : retrancher ~15 minutes
