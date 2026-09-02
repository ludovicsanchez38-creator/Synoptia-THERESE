# Protocole de test - Persona A3 : Léa Moreau, coach business (power user)

> Version : 1.0 | Date : 2026-03-27
> App : THERESE Desktop (Tauri 2.0, React, Python FastAPI)
> URL dev : http://localhost:1420 | Backend : http://localhost:17293
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
| Contexte | 3 clés API (Anthropic, OpenAI, Gemini), contacts en mémoire, conversations existantes, app déjà configurée |

## Convention de nommage screenshots

Tous les screenshots FAIL vont dans `/tmp/therese-tests/` avec le format :
`A3-{NN}_{slug}.png` (ex: `A3-01_dashboard.png`)

## Dossier screenshots

```bash
mkdir -p /tmp/therese-tests
```

## Pré-conditions globales (Léa = app déjà configurée)

Avant de lancer ce protocole, l'app doit contenir :
- Onboarding déjà complété (localStorage flag)
- 3 clés API configurées (Anthropic, OpenAI, Gemini) - vraies ou fausses selon le mode de test
- Au moins 3 contacts en mémoire
- Au moins 2 conversations existantes dans le chat
- Au moins 1 projet existant
- Au moins 1 facture existante (brouillon ou envoyée)
- Au moins 2 tâches existantes

Si la base est vierge, exécuter le protocole A1 d'abord ou injecter des données de seed.

---

## Phase 1 : Lancement et dashboard (étapes 1-3)

---

### Étape 1 : Lancer l'app - Dashboard "Ma journée" avec données

**Priorité** : P0
**URL** : http://localhost:1420

**Pré-conditions** :
- App déjà configurée (onboarding complété)
- Données existantes en base (contacts, tâches, factures, événements)

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420`
2. `wait_for` -> `[data-testid="app-main"]` visible (max 10s)
3. `screenshot` -> `/tmp/therese-tests/A3-01_dashboard.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="app-main"]') !== null`
5. `javascript_tool` -> vérifier que le dashboard affiche des données (pas un écran vide, pas l'onboarding)

**Résultat attendu** : L'app démarre directement sur le dashboard "Ma journée" (pas l'onboarding). Le dashboard affiche des données réelles : RDV à venir, tâches en cours, dernières factures. Léa voit immédiatement un résumé de sa journée. Aucun écran blanc, aucune erreur console.
**États testés** : loaded, filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-01_dashboard.png`

---

### Étape 2 : Dashboard - vérifier les KPIs

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier la présence de blocs KPI (nombre d'événements, tâches, factures)
2. `javascript_tool` -> vérifier que les valeurs KPI sont > 0 (données pré-existantes)
3. `screenshot` -> `/tmp/therese-tests/A3-02_dashboard_kpis.png`
4. `javascript_tool` -> vérifier que les compteurs sont des nombres (pas NaN, pas undefined)

**Résultat attendu** : Le dashboard affiche des KPIs numériques : nombre d'événements du jour, nombre de tâches en cours, nombre de factures récentes. Les valeurs sont cohérentes avec les données injectées. L'affichage est lisible et aligné.
**États testés** : filled
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

### Étape 5 : Changer de modèle LLM via le sélecteur

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> sélecteur de modèle LLM (dropdown ou bouton dans le header du chat)
2. `click` -> le sélecteur de modèle
3. `wait_for` -> liste des modèles visible (max 2s)
4. `screenshot` -> `/tmp/therese-tests/A3-05_model_selector_open.png`
5. `javascript_tool` -> vérifier que la liste contient au moins 3 providers (Anthropic, OpenAI, Gemini)
6. `find` -> option contenant "claude" ou "sonnet" dans la liste
7. `click` -> cette option
8. `wait_for` -> sélecteur fermé, modèle mis à jour (max 2s)
9. `screenshot` -> `/tmp/therese-tests/A3-05_model_changed.png`
10. `javascript_tool` -> vérifier que le modèle affiché a changé (contient "claude" ou "sonnet")

**Résultat attendu** : Le sélecteur de modèle affiche tous les modèles disponibles pour les 3 providers configurés. La sélection de claude-sonnet est immédiate. Le modèle affiché dans le header change. Pas de rechargement de page, pas de perte de contexte.
**États testés** : loaded, hover (dropdown), filled (nouveau modèle sélectionné)
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

### Étape 8 : Message avec markdown - rendu formaté

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="chat-message-input"]`
2. `type` -> "# Mon programme coaching\n\n**Objectif** : structurer l'activité\n\n- Séance 1 : Bilan\n- Séance 2 : Marché\n- Séance 3 : Business plan\n\n> La clé du succès, c'est la régularité."
3. `click` -> `[data-testid="chat-send-btn"]`
4. `wait_for` -> message affiché (max 5s)
5. `screenshot` -> `/tmp/therese-tests/A3-08_markdown_message.png`
6. `javascript_tool` -> vérifier la présence d'un `<h1>` ou `<strong>` ou `<ul>` ou `<blockquote>` dans le dernier message
7. `javascript_tool` -> vérifier que "Objectif" est en gras (dans un `<strong>` ou `<b>`)

**Résultat attendu** : Le markdown est rendu correctement : titre H1 "Mon programme coaching" en grand, "Objectif" en gras, liste à puces avec les 3 séances, citation en retrait. L'affichage est cohérent avec le dark mode. Les éléments HTML sont sémantiques.
**États testés** : filled (rendu markdown)
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

### Étape 10 : Command Palette - sélectionner un résultat pour naviguer

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> premier résultat dans la palette contenant "facture" ou "invoice"
2. `click` -> ce résultat
3. `wait_for` -> palette fermée ET navigation vers le panel factures (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A3-10_palette_navigate_invoices.png`
5. `javascript_tool` -> `document.querySelector('[data-testid="invoices-panel"]') !== null || window.location.href.includes('invoices')`

**Résultat attendu** : Le clic sur le résultat "Factures" ferme la palette et navigue vers le panel Factures. La transition est fluide. Le panel Factures s'affiche avec les factures existantes de Léa. Aucun double-clic nécessaire.
**États testés** : loaded, filled (panel factures avec données)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-10_palette_navigate_invoices.png`

---

## Phase 4 : Settings complets - 8 onglets (étapes 11-19)

---

### Étape 11 : Raccourci Ctrl+, (ou bouton) - ouvrir Settings

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> `const mod = navigator.platform.toUpperCase().indexOf('MAC') >= 0 ? 'metaKey' : 'ctrlKey'; document.dispatchEvent(new KeyboardEvent('keydown', {key: ',', [mod]: true, bubbles: true}))`  <!-- Cmd sur macOS, Ctrl ailleurs : useKeyboardShortcuts.ts:40 lit `event.metaKey` des que navigator.platform contient MAC -->
2. `wait_for` -> `[data-testid="settings-modal"]` visible (max 3s)
3. `screenshot` -> `/tmp/therese-tests/A3-11_settings_open.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="settings-modal"]') !== null`

**Résultat attendu** : Le raccourci Ctrl+, ouvre le modal Settings. Si le raccourci ne fonctionne pas, fallback : cliquer sur `[data-testid="settings-btn"]`. Le modal s'ouvre avec animation. L'onglet par défaut (Profil) est sélectionné.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-11_settings_open.png`

---

### Étape 12 : Settings - naviguer les 8 onglets un par un

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="settings-tab-profile"]`
2. `click` -> `[data-testid="settings-tab-profile"]`
3. `screenshot` -> `/tmp/therese-tests/A3-12_tab_profile.png`
4. `find` -> `[data-testid="settings-tab-ai"]`
5. `click` -> `[data-testid="settings-tab-ai"]`
6. `screenshot` -> `/tmp/therese-tests/A3-12_tab_ai.png`
7. `find` -> `[data-testid="settings-tab-services"]`
8. `click` -> `[data-testid="settings-tab-services"]`
9. `screenshot` -> `/tmp/therese-tests/A3-12_tab_services.png`
10. `find` -> `[data-testid="settings-tab-tools"]`
11. `click` -> `[data-testid="settings-tab-tools"]`
12. `screenshot` -> `/tmp/therese-tests/A3-12_tab_tools.png`
13. `find` -> `[data-testid="settings-tab-agents"]`
14. `click` -> `[data-testid="settings-tab-agents"]`
15. `screenshot` -> `/tmp/therese-tests/A3-12_tab_agents.png`
16. `find` -> `[data-testid="settings-tab-privacy"]`
17. `click` -> `[data-testid="settings-tab-privacy"]`
18. `screenshot` -> `/tmp/therese-tests/A3-12_tab_privacy.png`
19. `find` -> `[data-testid="settings-tab-advanced"]`
20. `click` -> `[data-testid="settings-tab-advanced"]`
21. `screenshot` -> `/tmp/therese-tests/A3-12_tab_advanced.png`
22. `find` -> `[data-testid="settings-tab-about"]`
23. `click` -> `[data-testid="settings-tab-about"]`
24. `screenshot` -> `/tmp/therese-tests/A3-12_tab_about.png`

**Résultat attendu** : Les 8 onglets sont cliquables et chacun affiche un contenu distinct : Profil (nom, activité), AI (providers, modèles), Services (Brave Search, etc.), Tools (MCP presets), Agents (config agents), Privacy (RGPD), Advanced (skip dashboard, etc.), About (version, crédits). Aucun onglet ne provoque d'erreur ou d'écran vide. La navigation entre onglets est fluide (pas de rechargement).
**États testés** : loaded (x8)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-12_tab_about.png`

---

### Étape 13 : Settings > AI - vérifier les 3 providers configurés

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="settings-tab-ai"]`
2. `wait_for` -> contenu onglet AI visible (max 2s)
3. `screenshot` -> `/tmp/therese-tests/A3-13_ai_providers.png`
4. `javascript_tool` -> vérifier que les 3 providers (Anthropic, OpenAI, Gemini) ont un champ de clé API non vide ou un indicateur "configuré"
5. `javascript_tool` -> compter le nombre de providers avec une clé configurée (doit être >= 3)

**Résultat attendu** : L'onglet AI affiche les 3 providers configurés par Léa. Chaque provider montre un indicateur visuel "actif" ou "configuré" (coche verte, badge, ou champ masqué non vide). Les modèles disponibles pour chaque provider sont listés. Le provider par défaut est clairement identifié.
**États testés** : filled (3 providers actifs)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-13_ai_providers.png`

---

### Étape 14 : Settings > AI - changer le modèle par défaut

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> sélecteur de modèle par défaut dans l'onglet AI
2. `javascript_tool` -> noter le modèle actuellement sélectionné
3. `click` -> le sélecteur
4. `wait_for` -> liste des modèles visible (max 2s)
5. `find` -> un modèle différent du modèle actuel
6. `click` -> ce modèle
7. `screenshot` -> `/tmp/therese-tests/A3-14_model_default_changed.png`
8. `javascript_tool` -> vérifier que le modèle par défaut a changé

**Résultat attendu** : Le sélecteur de modèle par défaut affiche tous les modèles des 3 providers. Le changement est immédiat (pas de page reload). Le nouveau modèle sera utilisé pour les prochaines conversations.
**États testés** : filled, hover (dropdown)
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

### Étape 17 : Settings > Advanced - toggle "Skip dashboard"

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="settings-tab-advanced"]`
2. `wait_for` -> contenu onglet Advanced visible (max 2s)
3. `screenshot` -> `/tmp/therese-tests/A3-17_advanced_before.png`
4. `find` -> toggle ou checkbox "Skip dashboard" ou "Passer le dashboard"
5. `javascript_tool` -> noter l'état actuel du toggle (on/off)
6. `click` -> le toggle
7. `screenshot` -> `/tmp/therese-tests/A3-17_advanced_toggled.png`
8. `javascript_tool` -> vérifier que l'état du toggle a changé

**Résultat attendu** : L'onglet Advanced contient un toggle "Skip dashboard" (ou équivalent). Le toggle change d'état visuellement au clic (on <-> off). Le changement sera effectif au prochain lancement de l'app. D'autres options avancées sont potentiellement visibles (mode debug, logs, etc.).
**États testés** : filled, toggle
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

### Étape 19 : Sauvegarder et fermer Settings

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="settings-save-btn"]`
2. `click` -> `[data-testid="settings-save-btn"]`
3. `wait_for` -> toast ou notification de confirmation (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A3-19_settings_saved.png`
5. `find` -> `[data-testid="settings-close-btn"]`
6. `click` -> `[data-testid="settings-close-btn"]`
7. `wait_for` -> `[data-testid="settings-modal"]` disparaît (max 2s)
8. `screenshot` -> `/tmp/therese-tests/A3-19_settings_closed.png`

**Résultat attendu** : La sauvegarde déclenche un toast "Paramètres sauvegardés". La fermeture du modal est fluide. L'interface principale est à nouveau visible et interactive. Les modifications (modèle par défaut, toggle skip dashboard) sont persistées.
**États testés** : loading (sauvegarde), success, loaded (retour UI)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-19_settings_closed.png`

---

## Phase 5 : Mémoire - contacts et projets (étapes 20-25)

---

### Étape 20 : Ouvrir Mémoire via header

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> bouton ou lien "Mémoire" dans le header ou la sidebar
2. `click` -> ce bouton
3. `wait_for` -> `[data-testid="memory-panel"]` visible (max 5s)
4. `screenshot` -> `/tmp/therese-tests/A3-20_memory_panel.png`
5. `javascript_tool` -> `document.querySelector('[data-testid="memory-panel"]') !== null`

**Résultat attendu** : Le panneau Mémoire s'ouvre avec les contacts existants de Léa. La liste des contacts est peuplée (au moins 3 contacts). Le champ de recherche est visible. Le bouton "Ajouter un contact" est accessible.
**États testés** : loaded, filled (contacts existants)
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

### Étape 24 : Créer un projet "Lancement coaching Q2"

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> onglet ou section "Projets" dans le panneau Mémoire
2. `click` -> onglet Projets
3. `find` -> bouton "Nouveau projet" ou "+"
4. `click` -> bouton Nouveau projet
5. `wait_for` -> formulaire de création de projet (max 3s)
6. `find` -> champ nom du projet
7. `click` -> champ nom
8. `type` -> "Lancement coaching Q2"
9. `find` -> champ description (si existant)
10. `click` -> champ description
11. `type` -> "Programme coaching business - Q2 2026 - 6 séances individuelles"
12. `screenshot` -> `/tmp/therese-tests/A3-24_project_form.png`
13. `find` -> bouton Sauvegarder
14. `click` -> bouton Sauvegarder
15. `wait_for` -> projet créé (max 3s)
16. `screenshot` -> `/tmp/therese-tests/A3-24_project_created.png`

**Résultat attendu** : Le formulaire de création de projet est accessible. Le projet "Lancement coaching Q2" est créé avec sa description. Le projet apparaît dans la liste des projets. Un toast de confirmation s'affiche.
**États testés** : empty (formulaire), filled (données saisies), success (projet créé)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-24_project_created.png`

---

### Étape 25 : Lier le projet à un contact

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> le projet "Lancement coaching Q2" dans la liste
2. `click` -> ce projet (ouvrir la fiche)
3. `find` -> section "Contacts liés" ou bouton "Lier un contact"
4. `click` -> bouton Lier
5. `wait_for` -> sélecteur de contacts (max 2s)
6. `find` -> un contact dans la liste de sélection
7. `click` -> ce contact
8. `screenshot` -> `/tmp/therese-tests/A3-25_project_linked.png`
9. `javascript_tool` -> vérifier que le contact est affiché dans la fiche du projet

**Résultat attendu** : Le projet peut être lié à un contact existant. Le contact apparaît dans la section "Contacts liés" du projet. La relation est bidirectionnelle (le projet apparaît aussi dans la fiche du contact). La liaison est persistée en base.
**États testés** : filled (liaison créée)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-25_project_linked.png`

---

## Phase 6 : CRM (étapes 26-30)

---

### Étape 26 : Ouvrir CRM

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=crm`
2. `wait_for` -> `[data-testid="crm-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A3-26_crm_panel.png`
4. `javascript_tool` -> `document.querySelector('[data-testid="crm-panel"]') !== null`

**Résultat attendu** : Le panneau CRM s'affiche avec le pipeline de leads. Les colonnes du pipeline sont visibles (Prospect, Qualifié, Proposition, Négociation, Gagné, Perdu). Des leads existants peuvent être présents. L'interface est de type Kanban.
**États testés** : loaded, filled (si leads existants)
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

### Étape 28 : CRM - créer un lead avec tous les champs

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> bouton "Nouveau lead" ou "+" dans le CRM
2. `click` -> bouton Nouveau lead
3. `wait_for` -> formulaire de création visible (max 3s)
4. `find` -> champ nom/contact
5. `click` -> champ nom
6. `type` -> "Marie Lefèvre - Coaching premium"
7. `find` -> champ montant estimé
8. `click` -> champ montant
9. `type` -> "4800"
10. `find` -> champ email ou contact
11. `click` -> champ email
12. `type` -> "marie.lefevre@example.com"
13. `find` -> sélecteur d'étape/stage
14. `javascript_tool` -> sélectionner "Qualifié" ou la deuxième étape
15. `screenshot` -> `/tmp/therese-tests/A3-28_crm_lead_form.png`
16. `find` -> bouton Sauvegarder
17. `click` -> bouton Sauvegarder
18. `wait_for` -> lead créé dans le pipeline (max 3s)
19. `screenshot` -> `/tmp/therese-tests/A3-28_crm_lead_created.png`

**Résultat attendu** : Le formulaire permet de remplir tous les champs d'un lead. Le lead "Marie Lefèvre - Coaching premium" est créé avec un montant de 4 800 EUR et positionné dans la colonne "Qualifié". La carte apparaît dans le pipeline immédiatement.
**États testés** : empty (formulaire), filled, success
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-28_crm_lead_created.png`

---

### Étape 29 : CRM - déplacer un lead dans le pipeline (stage)

**Priorité** : P1
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> le lead "Marie Lefèvre" dans le pipeline
2. `click` -> le lead (ouvrir les détails ou le menu)
3. `find` -> option pour changer de stage (dropdown, bouton "Déplacer", ou drag handle)
4. `javascript_tool` -> changer le stage du lead (ex: "Qualifié" -> "Proposition")
5. `wait_for` -> le lead se déplace dans la colonne "Proposition" (max 3s)
6. `screenshot` -> `/tmp/therese-tests/A3-29_crm_lead_moved.png`
7. `javascript_tool` -> vérifier que le lead est maintenant dans la colonne "Proposition"

**Résultat attendu** : Le lead est déplacé de "Qualifié" à "Proposition". Le pipeline se met à jour visuellement (la carte change de colonne). La modification est sauvegardée en base. Le nombre de leads par colonne est mis à jour.
**États testés** : filled, transition
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-29_crm_lead_moved.png`

---

### Étape 30 : CRM - ajouter un scoring/priorité

**Priorité** : P1
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> le lead "Marie Lefèvre" dans le pipeline
2. `click` -> le lead (ouvrir les détails)
3. `find` -> champ scoring, priorité, ou étoiles
4. `javascript_tool` -> attribuer un score ou une priorité haute
5. `screenshot` -> `/tmp/therese-tests/A3-30_crm_lead_scoring.png`
6. `find` -> bouton Sauvegarder (si mode édition)
7. `click` -> bouton Sauvegarder
8. `wait_for` -> confirmation (max 3s)
9. `screenshot` -> `/tmp/therese-tests/A3-30_crm_lead_scored.png`

**Résultat attendu** : Le lead a un score ou une priorité attribuée. L'indicateur visuel est visible sur la carte du lead dans le pipeline. La modification est persistée. Les leads peuvent être triés par score/priorité.
**États testés** : filled, success
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

### Étape 32 : Créer une facture (pas un devis) directement

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> bouton "Nouveau" ou "Créer"
2. `click` -> bouton Nouveau
3. `wait_for` -> formulaire InvoiceForm visible (max 3s)
4. `find` -> sélecteur type (devis/facture/avoir)
5. `javascript_tool` -> sélectionner "facture" dans le select
6. `screenshot` -> `/tmp/therese-tests/A3-32_invoice_type_facture.png`
7. `javascript_tool` -> vérifier que le type sélectionné est "facture" (pas "devis")

**Résultat attendu** : Le formulaire de création s'ouvre. Le type "facture" est sélectionnable directement (pas obligé de créer un devis d'abord). Le numéro de facture est pré-généré (ex: FAC-2026-001). Les champs client et lignes sont vides et prêts à remplir.
**États testés** : empty (formulaire), filled (type sélectionné)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-32_invoice_type_facture.png`

---

### Étape 33 : Facture - ajouter 3 lignes de produits/services

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> champ description ligne 1
2. `click` -> champ description
3. `type` -> "Coaching individuel - séance 1"
4. `find` -> champ quantité ligne 1
5. `click` -> champ quantité
6. `javascript_tool` -> vider et taper "1"
7. `find` -> champ prix unitaire ligne 1
8. `click` -> champ prix unitaire
9. `type` -> "400"
10. `find` -> bouton "Ajouter une ligne" ou "+"
11. `click` -> bouton Ajouter ligne
12. `find` -> champ description ligne 2
13. `click` -> champ description
14. `type` -> "Coaching individuel - séance 2"
15. `find` -> champ quantité ligne 2
16. `click` -> champ quantité
17. `javascript_tool` -> vider et taper "1"
18. `find` -> champ prix unitaire ligne 2
19. `click` -> champ prix unitaire
20. `type` -> "400"
21. `click` -> bouton Ajouter ligne
22. `find` -> champ description ligne 3
23. `click` -> champ description
24. `type` -> "Support de formation personnalisé"
25. `find` -> champ quantité ligne 3
26. `click` -> champ quantité
27. `javascript_tool` -> vider et taper "2"
28. `find` -> champ prix unitaire ligne 3
29. `click` -> champ prix unitaire
30. `type` -> "150"
31. `screenshot` -> `/tmp/therese-tests/A3-33_invoice_3_lines.png`

**Résultat attendu** : La facture contient 3 lignes : "Coaching séance 1" (1x400), "Coaching séance 2" (1x400), "Support formation" (2x150). Le bouton "Ajouter une ligne" fonctionne pour chaque ajout. Chaque ligne a ses propres champs description, quantité, prix unitaire.
**États testés** : filled (3 lignes)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-33_invoice_3_lines.png`

---

### Étape 34 : Facture - vérifier le calcul HT/TVA/TTC

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `javascript_tool` -> récupérer le montant HT affiché (attendu : 400 + 400 + 300 = 1 100 EUR)
2. `javascript_tool` -> récupérer le montant TVA affiché (attendu : 1 100 x 20% = 220 EUR)
3. `javascript_tool` -> récupérer le montant TTC affiché (attendu : 1 100 + 220 = 1 320 EUR)
4. `screenshot` -> `/tmp/therese-tests/A3-34_invoice_totals.png`
5. `javascript_tool` -> vérifier la cohérence : HT + TVA === TTC

**Résultat attendu** : Les totaux sont calculés automatiquement : HT = 1 100 EUR, TVA (20%) = 220 EUR, TTC = 1 320 EUR. Le calcul est correct et mis à jour en temps réel à chaque modification de ligne. Les montants sont formatés avec 2 décimales et le symbole EUR.
**États testés** : filled (calculs automatiques)
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

### Étape 36 : Facture - modifier le statut (brouillon -> envoyée)

**Priorité** : P1
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> la facture dans la liste
2. `click` -> la facture (ouvrir détails)
3. `find` -> sélecteur de statut ou bouton "Marquer comme envoyée"
4. `javascript_tool` -> vérifier le statut actuel ("brouillon" ou "draft")
5. `click` -> bouton ou option pour passer à "envoyée"
6. `wait_for` -> confirmation de changement de statut (max 3s)
7. `screenshot` -> `/tmp/therese-tests/A3-36_invoice_status_sent.png`
8. `javascript_tool` -> vérifier que le statut est maintenant "envoyée" ou "sent"

**Résultat attendu** : Le statut de la facture passe de "Brouillon" à "Envoyée". Le badge de statut change de couleur (gris -> bleu/vert). La date d'envoi est enregistrée. La facture ne peut plus être modifiée librement (verrouillage partiel). Le changement est persisté.
**États testés** : filled, transition (changement de statut)
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

### Étape 44 : Trier les tâches par deadline

**Priorité** : P1
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `find` -> bouton ou header de colonne "Deadline" ou "Échéance" pour trier
2. `click` -> bouton tri par deadline
3. `wait_for` -> liste triée (max 1s)
4. `screenshot` -> `/tmp/therese-tests/A3-44_tasks_sorted_deadline.png`
5. `javascript_tool` -> vérifier que "Envoyer facture Marie L." (deadline demain) est en haut
6. `javascript_tool` -> vérifier l'ordre croissant des deadlines

**Résultat attendu** : Les tâches sont triées par deadline croissante : "Envoyer facture" (demain) en premier, puis "Préparer support" (3 jours), etc. Le tri est visuel et immédiat. L'indicateur de tri (flèche) est visible. Les tâches sans deadline sont en fin de liste.
**États testés** : filled (triée)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-44_tasks_sorted_deadline.png`

---

## Phase 10 : Board IA (étapes 45-48)

---

### Étape 45 : Board IA - question stratégique

**Priorité** : P0
**URL** : http://localhost:1420/?panel=board

**Pré-condition** : Clé API valide configurée (au moins 1 provider)

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=board`
2. `wait_for` -> `[data-testid="board-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A3-45_board_panel.png`
4. `find` -> champ de saisie de la question (textarea ou input dans le board)
5. `click` -> champ de saisie
6. `type` -> "Quel tarif pour mon nouveau programme coaching business de 6 séances sur 3 mois ? Mon positionnement est premium, ma cible sont des consultants et freelances avec 1-5 ans d'activité."
7. `find` -> `[data-testid="board-submit-btn"]`
8. `click` -> `[data-testid="board-submit-btn"]`
9. `wait_for` -> début des réponses des conseillers (max 20s)
10. `screenshot` -> `/tmp/therese-tests/A3-45_board_question_sent.png`

**Résultat attendu** : Le Board IA s'affiche avec un champ de saisie pour la question. La question de Léa est envoyée et le Board lance les 5 conseillers en parallèle. Des indicateurs de chargement apparaissent pour chaque conseiller. L'interface montre que le traitement est en cours.
**États testés** : empty (board vierge), filled (question), loading (attente réponses)
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

### Étape 48 : Board - exporter le résultat (si disponible)

**Priorité** : P2
**URL** : http://localhost:1420/?panel=board

**Actions Chrome MCP** :
1. `find` -> bouton "Exporter" ou "Télécharger" ou "Copier" dans le board
2. `screenshot` -> `/tmp/therese-tests/A3-48_board_export_btn.png`
3. `click` -> bouton Export (si existant)
4. `wait_for` -> téléchargement ou copie dans le presse-papiers (max 5s)
5. `screenshot` -> `/tmp/therese-tests/A3-48_board_exported.png`

**Résultat attendu** : Si un bouton d'export existe, il permet de télécharger les résultats du Board en format PDF, Markdown ou DOCX. Si seul un bouton "Copier" existe, le contenu est copié dans le presse-papiers. Si aucun bouton d'export n'est présent, noter comme fonctionnalité manquante (P2).
**États testés** : loaded (bouton visible ou non)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-48_board_exported.png`

---

## Phase 11 : Skills Office (étapes 49-50)

---

### Étape 49 : Skills - demander un document Word récapitulatif des tâches

**Priorité** : P1
**URL** : http://localhost:1420

**Pré-condition** : Clé API valide, tâches existantes en mémoire

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420`
2. `wait_for` -> `[data-testid="chat-message-input"]` visible (max 5s)
3. `click` -> `[data-testid="chat-message-input"]`
4. `type` -> "Génère un document Word récapitulatif de mes tâches en cours avec leur priorité et deadline"
5. `click` -> `[data-testid="chat-send-btn"]`
6. `wait_for` -> réponse avec lien ou aperçu du document (max 30s)
7. `screenshot` -> `/tmp/therese-tests/A3-49_skill_docx.png`
8. `javascript_tool` -> vérifier la présence d'un lien de téléchargement (.docx) ou d'un message confirmant la génération

**Résultat attendu** : L'IA reconnaît la demande comme un skill Office (DOCX). Le document Word est généré avec la liste des tâches de Léa, les priorités et les deadlines. Un lien de téléchargement est affiché dans le chat. Le document est conforme (python-docx).
**États testés** : loading (génération), success (lien téléchargement)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-49_skill_docx.png`

---

### Étape 50 : Skills - demander un tableur Excel de suivi financier

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="chat-message-input"]`
2. `type` -> "Crée un tableur Excel de suivi financier avec mes factures en cours, le montant HT, la TVA et le TTC pour chaque client"
3. `click` -> `[data-testid="chat-send-btn"]`
4. `wait_for` -> réponse avec lien ou aperçu du tableur (max 30s)
5. `screenshot` -> `/tmp/therese-tests/A3-50_skill_xlsx.png`
6. `javascript_tool` -> vérifier la présence d'un lien de téléchargement (.xlsx) ou d'un message confirmant la génération

**Résultat attendu** : L'IA génère un tableur Excel avec les données financières de Léa. Le fichier contient les colonnes : Client, Description, HT, TVA, TTC, Statut. Les données proviennent des factures existantes. Le lien de téléchargement est affiché dans le chat.
**États testés** : loading (génération), success (lien téléchargement)
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

### Étape 55 : Export RGPD - settings > data > exporter tout

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="settings-btn"]`
2. `click` -> `[data-testid="settings-btn"]`
3. `wait_for` -> `[data-testid="settings-modal"]` visible (max 3s)
4. `find` -> `[data-testid="settings-tab-privacy"]`
5. `click` -> `[data-testid="settings-tab-privacy"]`
6. `wait_for` -> contenu onglet Privacy visible (max 2s)
7. `screenshot` -> `/tmp/therese-tests/A3-55_privacy_export.png`
8. `find` -> bouton "Exporter toutes mes données" ou "Export RGPD" ou "Télécharger mes données"
9. `click` -> bouton Export
10. `wait_for` -> téléchargement ou confirmation (max 15s)
11. `screenshot` -> `/tmp/therese-tests/A3-55_rgpd_export_done.png`
12. `javascript_tool` -> vérifier qu'un fichier a été téléchargé ou qu'un message de confirmation apparaît
13. `javascript_tool` -> si possible, vérifier que le fichier exporté contient : contacts, conversations, tâches, factures, projets

**Résultat attendu** : L'export RGPD génère un fichier JSON ou ZIP contenant toutes les données de Léa : profil, contacts (dont le numéro modifié), conversations, tâches (les 5 créées), factures (avec les 3 lignes), projets ("Lancement coaching Q2"), événements calendrier. Le fichier est complet et lisible. Un toast de confirmation s'affiche. Le format est conforme au droit à la portabilité RGPD.
**États testés** : loading (export en cours), success (fichier téléchargé)
**Si FAIL** : Screenshot `/tmp/therese-tests/A3-55_rgpd_export_done.png`

---

## Récapitulatif des priorités

| Priorité | Étapes | Count |
|----------|--------|-------|
| P0 | 1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 19, 20, 24, 26, 27, 28, 31, 32, 33, 34, 37, 39, 41, 42, 45, 46, 51, 52, 54, 55 | 30 |
| P1 | 2, 7, 8, 14, 15, 16, 17, 18, 21, 22, 23, 25, 29, 30, 35, 36, 38, 40, 43, 44, 47, 49, 50, 53 | 24 |
| P2 | 48 | 1 |

## Matrice de couverture

| Module | Étapes | État vide | État rempli | État erreur | État loading |
|--------|--------|-----------|-------------|-------------|--------------|
| Dashboard | 1-3 | - | oui | - | - |
| Chat | 4, 6-8, 54 | oui | oui | - | - |
| Chat (LLM) | 6 | - | oui | - | oui |
| Command Palette | 9-10 | - | oui | - | - |
| Settings (8 tabs) | 11-19 | - | oui | - | oui |
| Mémoire | 20-25 | oui | oui | - | - |
| CRM | 26-30 | oui | oui | - | - |
| Factures | 31-36 | oui | oui | - | oui |
| Calendrier | 37-40 | oui | oui | - | - |
| Tâches | 41-44 | oui | oui | - | - |
| Board IA | 45-48 | oui | oui | - | oui |
| Skills Office | 49-50 | - | oui | - | oui |
| Raccourcis | 4, 9, 11, 51-53 | - | oui | - | - |
| Sécurité XSS | 54 | - | oui | - | - |
| RGPD | 55 | - | - | - | oui |

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
settings-btn
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
