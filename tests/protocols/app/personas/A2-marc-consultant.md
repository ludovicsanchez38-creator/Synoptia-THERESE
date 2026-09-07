# Protocole de test - Persona A2 : Marc Lefèvre, consultant RH

> Version : 1.0 | Date : 2026-03-27
> App : THERESE Desktop (Tauri 2.0, React, Python FastAPI)
> URL dev : http://localhost:1420 | Backend : http://localhost:17293
> Pré-requis : `make dev` lancé, backend healthy, onboarding déjà complété, clé API OpenAI configurée

## Profil persona

| Champ | Valeur |
|-------|--------|
| Nom | Marc Lefèvre |
| Age | 55 ans |
| Métier | Consultant RH indépendant |
| OS | macOS |
| Niveau tech | À l'aise avec Excel, pas avec la technique. Ne comprend pas les modèles LLM |
| Objectif | Rédiger des emails pro, suivre ses clients dans le CRM, facturer ses missions |
| Contexte | App déjà installée et configurée (onboarding fait, clé API OpenAI en place). Journée type de travail |

## Convention de nommage screenshots

Tous les screenshots FAIL vont dans `/tmp/therese-tests/` avec le format :
`A2-{NN}_{slug}.png` (ex: `A2-01_dashboard.png`)

## Dossier screenshots

```bash
mkdir -p /tmp/therese-tests
```

---

## Phase 1 : Lancement et Dashboard "Ma journée" (étapes 1-3)

---

### Étape 1 : Lancer l'app - Dashboard "Ma journée" visible

**Priorité** : P0
**URL** : http://localhost:1420

**Pré-conditions** :
- Onboarding déjà complété (localStorage flag présent)
- Clé API OpenAI configurée et sauvegardée
- Base SQLite existante (pas vierge)

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420`
2. `wait_for` -> `[data-testid="app-main"]` visible (max 10s)
3. `screenshot` -> `/tmp/therese-tests/A2-01_dashboard.png`
4. `javascript_tool` -> vérifier que l'onboarding wizard n'est PAS affiché (pas de `[data-testid="onboarding-wizard"]`)
5. `javascript_tool` -> vérifier la présence d'un message d'accueil contenant "Bonjour" ou "Bonsoir" (selon l'heure)

**Résultat attendu** : L'app se lance directement sur le dashboard "Ma journée" (pas d'onboarding). Un message d'accueil contextuel ("Bonjour Marc" ou "Bonsoir Marc") est visible. Le dashboard affiche les compteurs : RDV du jour, tâches urgentes, factures en retard. L'interface est en dark mode cohérent.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-01_dashboard.png`

---

### Étape 2 : Vérifier le dashboard - date du jour, compteurs, bouton chat

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier que la date du jour "27 mars 2026" (ou format FR) est affichée quelque part dans le dashboard
2. `javascript_tool` -> vérifier la présence de compteurs (tâches, RDV, factures) - éléments `.counter`, `.stat`, `.badge` ou équivalent
3. `find` -> bouton ou lien "Passer au chat" ou "Commencer" ou accès direct au chat
4. `screenshot` -> `/tmp/therese-tests/A2-02_dashboard_details.png`

**Résultat attendu** : Le dashboard affiche la date du jour, des compteurs (même à zéro) pour les tâches, RDV et factures. Un bouton ou lien permet de basculer rapidement vers le chat. L'interface est lisible pour Marc (55 ans, pas de texte trop petit).
**États testés** : loaded, empty (compteurs à zéro si DB fraîche)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-02_dashboard_details.png`

---

### Étape 3 : Passer au chat - interface chat vide (nouvelle journée)

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="chat-message-input"]` (accès direct ou via bouton dashboard)
2. `javascript_tool` -> si le chat n'est pas visible, cliquer sur le bouton "Passer au chat" trouvé à l'étape 2
3. `wait_for` -> `[data-testid="chat-message-input"]` visible (max 5s)
4. `find` -> `[data-testid="chat-message-list"]`
5. `screenshot` -> `/tmp/therese-tests/A2-03_chat_empty.png`
6. `javascript_tool` -> vérifier que l'input est vide et que le placeholder invite à écrire

**Résultat attendu** : L'interface de chat est accessible et vide (nouvelle journée, pas d'historique dans la conversation courante). L'input de saisie affiche un placeholder invitant Marc à poser sa question. L'ambiance dark mode est cohérente. Les boutons envoi, pièce jointe et micro sont visibles.
**États testés** : empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-03_chat_empty.png`

---

## Phase 2 : Chat et rédaction assistée (étapes 4-11)

> **Sidebar fermée par défaut (depuis 11/06/2026)** : la sidebar conversations
> n'est plus ouverte au lancement (l'app atterrit sur l'Accueil). Avant toute
> action sur un `[data-testid="sidebar-*"]`, l'ouvrir :
> `javascript_tool` -> `window.__therese.stores.panel.getState().togglePanel('conversationSidebar')`
> (ou raccourci ⌘B/Ctrl+B), puis `wait_for` -> `[data-testid="sidebar"]` visible.

---

### Étape 4 : Demander un email de relance - streaming réponse

**Priorité** : P0
**Pré-condition** : Clé API OpenAI valide configurée
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `click` -> `[data-testid="chat-message-input"]`
2. `type` -> "Rédige un email de relance pour le client Durand qui n'a pas signé le contrat"
3. `screenshot` -> `/tmp/therese-tests/A2-04_typing_relance.png`
4. `click` -> `[data-testid="chat-send-btn"]`
5. `wait_for` -> apparition du premier token de réponse (max 20s)
6. `screenshot` -> `/tmp/therese-tests/A2-04_streaming_start.png`
7. `wait_for` -> fin du streaming (indicateur de typing disparaît) (max 60s)
8. `screenshot` -> `/tmp/therese-tests/A2-04_streaming_complete.png`

**Résultat attendu** : Le message de Marc apparaît immédiatement (bulle droite). L'indicateur de frappe (TypingIndicator) s'affiche pendant le streaming. Les tokens arrivent progressivement. La réponse complète est un email structuré avec objet, corps, formule de politesse. Le contenu est pertinent pour une relance commerciale RH.
**États testés** : loading (streaming), filled (réponse complète)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-04_streaming_complete.png`

---

### Étape 5 : Vérifier la qualité de la réponse (email structuré)

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> récupérer le texte du dernier `[data-testid="chat-message-item"]` (rôle assistant)
2. `javascript_tool` -> vérifier que la réponse contient "Objet" ou "Subject" (ligne d'objet email)
3. `javascript_tool` -> vérifier que la réponse contient une formule de politesse ("Cordialement", "Bien cordialement", "Sincères salutations")
4. `screenshot` -> `/tmp/therese-tests/A2-05_email_quality.png`

**Résultat attendu** : La réponse contient un email professionnel structuré : un objet clair, un corps avec contexte de relance, une formule de politesse. Le formatage Markdown est rendu correctement (gras, sauts de ligne). Marc peut copier-coller directement cet email.
**États testés** : filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-05_email_quality.png`

---

### Étape 6 : Copier la réponse (sélection texte)

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> sélectionner le texte du dernier message assistant : `const el = document.querySelectorAll('[data-testid="chat-message-item"]'); const last = el[el.length-1]; const range = document.createRange(); range.selectNodeContents(last); window.getSelection().removeAllRanges(); window.getSelection().addRange(range);`
2. `screenshot` -> `/tmp/therese-tests/A2-06_text_selected.png`
3. `javascript_tool` -> vérifier que `window.getSelection().toString().length > 50` (texte sélectionné non vide)

**Résultat attendu** : Le texte de la réponse est sélectionnable. Marc peut utiliser Ctrl+C (ou Cmd+C sur Mac) pour copier le contenu. Le texte sélectionné est visuellement mis en surbrillance. Aucun élément de l'UI ne bloque la sélection.
**États testés** : filled, focus
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-06_text_selected.png`

---

### Étape 7 : Nouvelle conversation - compte-rendu de réunion

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="sidebar-new-conversation-btn"]`
2. `click` -> `[data-testid="sidebar-new-conversation-btn"]`
3. `wait_for` -> l'input de chat est vidé et la liste de messages est vide (max 3s)
4. `javascript_tool` -> `document.querySelectorAll('[data-testid="chat-message-item"]').length === 0`
5. `click` -> `[data-testid="chat-message-input"]`
6. `type` -> "Prépare un compte-rendu de réunion RH du 27 mars"
7. `click` -> `[data-testid="chat-send-btn"]`
8. `wait_for` -> fin du streaming (max 60s)
9. `screenshot` -> `/tmp/therese-tests/A2-07_cr_reunion.png`

**Résultat attendu** : Une nouvelle conversation est créée (historique vidé). Le message de Marc est envoyé et la réponse contient un modèle de compte-rendu structuré (date, participants, ordre du jour, décisions, actions). La conversation précédente (relance Durand) est sauvegardée dans la sidebar.
**États testés** : empty -> loading -> filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-07_cr_reunion.png`

---

### Étape 8 : Vérifier les 2 conversations dans la sidebar

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="sidebar"]`
2. `find` -> `[data-testid="sidebar-conversation-list"]`
3. `javascript_tool` -> `document.querySelectorAll('[data-testid="sidebar-conversation-item"]').length >= 2`
4. `screenshot` -> `/tmp/therese-tests/A2-08_sidebar_two_convs.png`

**Résultat attendu** : La sidebar affiche au moins 2 conversations. Les titres sont pertinents (générés automatiquement à partir du contenu ou du premier message). Marc peut distinguer la conversation "relance Durand" de la conversation "compte-rendu RH". Les conversations sont ordonnées par date (la plus récente en haut).
**États testés** : filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-08_sidebar_two_convs.png`

---

### Étape 9 : Renommer une conversation (menu contextuel)

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> premier `[data-testid="sidebar-conversation-item"]`
2. `javascript_tool` -> déclencher un clic droit (contextmenu) sur le premier item : `document.querySelector('[data-testid="sidebar-conversation-item"]').dispatchEvent(new MouseEvent('contextmenu', {bubbles: true, clientX: 100, clientY: 100}))`
3. `wait_for` -> menu contextuel visible (max 2s)
4. `screenshot` -> `/tmp/therese-tests/A2-09_context_menu.png`
5. `javascript_tool` -> chercher un bouton/lien "Renommer" dans le menu contextuel visible
6. `click` -> option "Renommer" (si trouvée)
7. `screenshot` -> `/tmp/therese-tests/A2-09_rename.png`

**Résultat attendu** : Un clic droit sur une conversation ouvre un menu contextuel avec les options : Renommer, Supprimer (au minimum). L'option Renommer rend le titre éditable (input inline ou modal). Marc peut taper un nouveau nom. Si le menu contextuel n'existe pas, une icône "..." ou un bouton d'édition est disponible sur hover.
**États testés** : loaded, focus
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-09_context_menu.png`

---

### Étape 10 : Ouvrir la sidebar si fermée

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier si `[data-testid="sidebar"]` est visible (offsetWidth > 0 et pas display:none)
2. `javascript_tool` -> si la sidebar est fermée, chercher un bouton toggle (hamburger, icône sidebar) et cliquer dessus
3. `wait_for` -> `[data-testid="sidebar"]` visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A2-10_sidebar_open.png`
5. `find` -> `[data-testid="sidebar-conversation-list"]`

**Résultat attendu** : La sidebar est visible et affiche la liste des conversations. Si elle était fermée, le bouton toggle l'ouvre avec une animation fluide (slide-in). La sidebar ne recouvre pas le contenu principal sur desktop (layout flex).
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-10_sidebar_open.png`

---

### Étape 11 : Rechercher "Durand" dans la sidebar

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="sidebar-search-input"]`
2. `click` -> `[data-testid="sidebar-search-input"]`
3. `type` -> "Durand"
4. `wait_for` -> filtrage de la liste (max 2s)
5. `screenshot` -> `/tmp/therese-tests/A2-11_sidebar_search_durand.png`
6. `javascript_tool` -> vérifier que la liste filtrée contient au moins la conversation avec "Durand"
7. `javascript_tool` -> `document.querySelectorAll('[data-testid="sidebar-conversation-item"]').length >= 1`

**Résultat attendu** : La recherche "Durand" filtre les conversations et affiche celle contenant ce mot (la relance email). La conversation "compte-rendu RH" n'apparaît pas (ne contient pas "Durand"). Le filtre est insensible à la casse.
**États testés** : filled (résultats filtrés)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-11_sidebar_search_durand.png`

---

## Phase 3 : CRM et gestion de pipeline (étapes 12-19)

---

### Étape 12 : Ouvrir le CRM

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=crm`
2. `wait_for` -> `[data-testid="crm-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A2-12_crm_panel.png`

**Résultat attendu** : Le panneau CRM s'ouvre et affiche l'interface de gestion commerciale. Les colonnes du pipeline sont visibles (Prospect, Qualifié, Proposition, Gagné, Perdu). L'interface est en dark mode cohérent. Un bouton d'ajout de contact est visible.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-12_crm_panel.png`

---

### Étape 13 : Voir le pipeline (colonnes visibles)

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier la présence de colonnes de pipeline (éléments contenant "Prospect", "Qualifié", "Proposition", "Gagné", "Perdu")
2. `javascript_tool` -> compter le nombre de colonnes visibles (au moins 3)
3. `screenshot` -> `/tmp/therese-tests/A2-13_pipeline_columns.png`

**Résultat attendu** : Le pipeline affiche ses colonnes avec des titres clairs. Chaque colonne est visuellement distincte (fond, bordure, ou header coloré). Les colonnes sont vides (aucun contact CRM créé encore). Le layout est en grille horizontale scrollable ou en flex.
**États testés** : loaded, empty (colonnes sans cartes)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-13_pipeline_columns.png`

---

### Étape 14 : Créer un contact "Société Durand"

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> bouton "Ajouter" ou "+" ou "Nouveau contact" dans le CRM
2. `click` -> ce bouton
3. `wait_for` -> formulaire de création contact visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A2-14_crm_form_open.png`
5. `find` -> champ nom / entreprise
6. `click` -> champ nom
7. `type` -> "Société Durand"

**Résultat attendu** : Un formulaire de création de contact CRM s'ouvre (modal ou panneau latéral). Les champs sont vides et prêts à être remplis. Marc commence par saisir le nom de l'entreprise.
**États testés** : empty (formulaire vide)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-14_crm_form_open.png`

---

### Étape 15 : Remplir le contact complet (nom, email, téléphone, adresse, notes)

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> champ contact / personne (si séparé de l'entreprise)
2. `javascript_tool` -> si champ "contact" ou "nom du contact" existe, cliquer et taper "Marie Durand"
3. `find` -> champ rôle / poste
4. `javascript_tool` -> si le champ existe, taper "DRH"
5. `find` -> champ email
6. `click` -> champ email
7. `type` -> "m.durand@societedurand.fr"
8. `find` -> champ téléphone
9. `click` -> champ téléphone
10. `type` -> "01 23 45 67 89"
11. `find` -> champ adresse (si présent)
12. `javascript_tool` -> si le champ existe, taper "12 rue des Lilas, 75001 Paris"
13. `find` -> champ notes (si présent)
14. `javascript_tool` -> si le champ existe, taper "Prospect via recommandation. Besoin audit RH."
15. `screenshot` -> `/tmp/therese-tests/A2-15_crm_contact_filled.png`

**Résultat attendu** : Le formulaire est rempli avec les informations de la Société Durand. Les champs obligatoires sont remplis (nom, email). Les champs optionnels (téléphone, adresse, notes) sont remplis si disponibles. Marc voit les données saisies avant de sauvegarder.
**États testés** : filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-15_crm_contact_filled.png`

---

### Étape 16 : Sauvegarder le contact - visible dans la liste

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> bouton Sauvegarder / Créer dans le formulaire CRM
2. `click` -> bouton Sauvegarder
3. `wait_for` -> le formulaire se ferme et le contact apparaît dans le pipeline (max 5s)
4. `screenshot` -> `/tmp/therese-tests/A2-16_crm_contact_saved.png`
5. `javascript_tool` -> vérifier qu'un élément contenant "Société Durand" ou "Durand" est visible dans le pipeline

**Résultat attendu** : Le contact est sauvegardé en base SQLite. Le formulaire se ferme. Le contact "Société Durand" apparaît dans la première colonne du pipeline (Prospect). Un toast de confirmation peut apparaître. Le CRM n'est plus vide.
**États testés** : loading (sauvegarde), success, filled (pipeline avec 1 carte)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-16_crm_contact_saved.png`

---

### Étape 17 : Déplacer le contact dans la colonne "Proposition"

**Priorité** : P0
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> carte "Société Durand" dans la colonne Prospect
2. `javascript_tool` -> tenter un drag & drop de la carte vers la colonne "Proposition" : `const card = document.querySelector('[data-testid="crm-panel"]').querySelector(':scope *:has(> *)')` (adapter au sélecteur réel)
3. `screenshot` -> `/tmp/therese-tests/A2-17_crm_drag_attempt.png`
4. `javascript_tool` -> si drag & drop échoue, chercher un sélecteur de statut (select, dropdown) sur la carte et changer vers "Proposition"
5. `wait_for` -> le contact change de colonne ou de statut (max 3s)
6. `screenshot` -> `/tmp/therese-tests/A2-17_crm_moved.png`

**Résultat attendu** : Le contact "Société Durand" passe de la colonne "Prospect" à la colonne "Proposition" via drag & drop ou via un sélecteur de statut. La carte est visuellement dans la bonne colonne. La modification est persistée en base. Marc voit son pipeline avancer.
**États testés** : filled -> filled (changement de colonne)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-17_crm_moved.png`

---

### Étape 18 : Ajouter une activité/note sur le contact

**Priorité** : P1
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> carte "Société Durand" dans le pipeline
2. `click` -> carte "Société Durand" (ouvrir le détail)
3. `wait_for` -> panneau de détail ou modal du contact visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A2-18_crm_detail.png`
5. `find` -> bouton "Ajouter une note" ou "Nouvelle activité" ou champ notes
6. `click` -> ce bouton ou champ
7. `type` -> "Relance envoyée le 28/03"
8. `find` -> bouton Sauvegarder la note (si présent)
9. `click` -> bouton Sauvegarder (si présent)
10. `screenshot` -> `/tmp/therese-tests/A2-18_crm_note_added.png`

**Résultat attendu** : Le détail du contact s'ouvre avec les informations saisies précédemment. Un champ ou un bouton permet d'ajouter une note/activité. La note "Relance envoyée le 28/03" est ajoutée et sauvegardée. L'historique des activités est visible sur le contact.
**États testés** : loaded, filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-18_crm_note_added.png`

---

### Étape 19 : Rechercher "Durand" dans le CRM

**Priorité** : P1
**URL** : http://localhost:1420/?panel=crm

**Actions Chrome MCP** :
1. `find` -> champ de recherche dans le CRM (input type search ou text)
2. `click` -> champ de recherche
3. `type` -> "Durand"
4. `wait_for` -> résultats filtrés (max 3s)
5. `screenshot` -> `/tmp/therese-tests/A2-19_crm_search_durand.png`
6. `javascript_tool` -> vérifier qu'au moins un résultat contient "Durand"

**Résultat attendu** : La recherche "Durand" filtre les contacts du CRM et affiche la carte "Société Durand". Le filtrage est en temps réel. Les contacts ne correspondant pas sont masqués. Marc retrouve rapidement son client.
**États testés** : filled (résultats trouvés)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-19_crm_search_durand.png`

---

## Phase 4 : Facturation et devis (étapes 20-26)

---

### Étape 20 : Ouvrir Factures

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=invoices`
2. `wait_for` -> `[data-testid="invoices-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A2-20_invoices_panel.png`

**Résultat attendu** : Le panneau Factures s'ouvre. L'interface affiche la liste des documents (devis, factures, avoirs). Les filtres par type et statut sont visibles. Un bouton "Nouveau" ou "+" permet de créer un document.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-20_invoices_panel.png`

---

### Étape 21 : Créer un devis pour Société Durand

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> bouton "Nouveau" ou "Créer" dans le panneau factures
2. `click` -> ce bouton
3. `wait_for` -> formulaire InvoiceForm visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A2-21_invoice_form_open.png`
5. `find` -> sélecteur type de document (devis/facture/avoir)
6. `javascript_tool` -> sélectionner "devis" dans le select
7. `find` -> sélecteur client/contact
8. `javascript_tool` -> sélectionner "Société Durand" dans la liste des contacts (ou taper le nom)

**Résultat attendu** : Le formulaire de création s'ouvre. Le type "devis" est sélectionné. Le client "Société Durand" est sélectionnable depuis la liste des contacts existants (lien avec le CRM). Le numéro de devis est pré-généré automatiquement.
**États testés** : empty -> filled (partiel)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-21_invoice_form_open.png`

---

### Étape 22 : Ajouter une ligne "Audit RH - 3 jours" à 800EUR/jour

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> champ description de la première ligne
2. `click` -> champ description
3. `type` -> "Audit RH - diagnostic complet"
4. `find` -> champ quantité
5. `click` -> champ quantité
6. `javascript_tool` -> vider le champ (triple clic + backspace) puis taper "3"
7. `find` -> champ prix unitaire
8. `click` -> champ prix unitaire
9. `javascript_tool` -> vider le champ puis taper "800"
10. `screenshot` -> `/tmp/therese-tests/A2-22_devis_line.png`
11. `javascript_tool` -> vérifier que le total HT affiché est 2400 (3 x 800)

**Résultat attendu** : La ligne de devis est remplie : description "Audit RH - diagnostic complet", quantité 3, prix unitaire 800 EUR. Le total HT de la ligne (2 400 EUR) est calculé automatiquement. Marc n'a pas besoin de faire le calcul lui-même (habitué à Excel, il s'attend à un calcul auto).
**États testés** : filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-22_devis_line.png`

---

### Étape 23 : Ajouter TVA 20%

**Priorité** : P1
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> champ ou sélecteur TVA (taux de TVA, select, ou input %)
2. `javascript_tool` -> si c'est un select, sélectionner "20%" ; si c'est un input, taper "20"
3. `screenshot` -> `/tmp/therese-tests/A2-23_tva.png`
4. `javascript_tool` -> vérifier que le montant TTC affiché est 2880 (2400 + 20% = 2880)

**Résultat attendu** : Le taux de TVA 20% est appliqué. Le total TTC est recalculé automatiquement : 2 400 EUR HT + 480 EUR TVA = 2 880 EUR TTC. Les montants HT, TVA et TTC sont clairement affichés et distincts. Marc comprend immédiatement la décomposition.
**États testés** : filled
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-23_tva.png`

---

### Étape 24 : Sauvegarder le devis - statut brouillon

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> bouton Sauvegarder dans le formulaire
2. `click` -> bouton Sauvegarder
3. `wait_for` -> le formulaire se ferme et le devis apparaît dans la liste (max 5s)
4. `screenshot` -> `/tmp/therese-tests/A2-24_devis_saved.png`
5. `javascript_tool` -> vérifier que le devis a le statut "brouillon" ou "draft"
6. `javascript_tool` -> vérifier que le montant affiché correspond (2400 HT ou 2880 TTC)

**Résultat attendu** : Le devis est sauvegardé en base SQLite. Le formulaire se ferme. Le devis apparaît dans la liste avec le statut "Brouillon". Le numéro de devis est généré automatiquement (ex: DEV-2026-001). Le montant est correct (2 400 EUR HT). Marc peut le retrouver facilement.
**États testés** : loading (sauvegarde), success, filled (liste avec 1 devis)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-24_devis_saved.png`

---

### Étape 25 : Convertir le devis en facture (si disponible)

**Priorité** : P1
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> le devis dans la liste
2. `click` -> le devis (pour ouvrir les options)
3. `find` -> bouton "Convertir en facture" ou "Facturer" ou icône de conversion
4. `screenshot` -> `/tmp/therese-tests/A2-25_convert_btn.png`
5. `javascript_tool` -> si le bouton existe, cliquer dessus
6. `wait_for` -> confirmation ou nouveau document facture (max 5s)
7. `screenshot` -> `/tmp/therese-tests/A2-25_converted.png`

**Résultat attendu** : Si la fonctionnalité existe : le devis est converti en facture avec les mêmes informations (client, lignes, montants). Le numéro change (FAC-2026-001). Le statut passe à "Émise" ou "En attente". Si la fonctionnalité n'existe pas : documenter l'absence et passer à l'étape suivante.
**États testés** : loaded -> success (si conversion disponible)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-25_convert_btn.png`

---

### Étape 26 : Générer le PDF du devis

**Priorité** : P0
**URL** : http://localhost:1420/?panel=invoices

**Actions Chrome MCP** :
1. `find` -> le devis (ou facture) dans la liste
2. `click` -> le document (pour ouvrir les options)
3. `find` -> bouton "PDF" ou "Télécharger" ou icône PDF
4. `click` -> bouton PDF
5. `wait_for` -> téléchargement ou aperçu PDF (max 10s)
6. `screenshot` -> `/tmp/therese-tests/A2-26_pdf_generated.png`
7. `javascript_tool` -> vérifier qu'un fichier a été téléchargé ou qu'un aperçu est affiché

**Résultat attendu** : Le PDF du devis est généré avec les informations correctes : coordonnées de Marc Lefèvre (consultant RH), client Société Durand, ligne "Audit RH - 3 jours x 800 EUR = 2 400 EUR HT", TVA 20%, total TTC 2 880 EUR. Le PDF est conforme aux obligations légales françaises (mentions obligatoires, numéro, date, conditions de règlement). Le fichier est téléchargé ou affiché dans un viewer.
**États testés** : loading (génération), success (PDF disponible)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-26_pdf_generated.png`

---

## Phase 5 : Email (étapes 27-29)

---

### Étape 27 : Ouvrir le panneau Email

**Priorité** : P0
**URL** : http://localhost:1420/?panel=email

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=email`
2. `wait_for` -> `[data-testid="email-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A2-27_email_panel.png`

**Résultat attendu** : Le panneau Email s'ouvre. L'interface affiche soit la boîte de réception (si configuré), soit le wizard de configuration (si email non configuré). La transition est fluide depuis le panneau précédent.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-27_email_panel.png`

---

### Étape 28 : Email non configuré - wizard setup visible

**Priorité** : P1
**URL** : http://localhost:1420/?panel=email

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier si un wizard de configuration email est affiché (texte "Configurer", "Setup", "Connecter" ou formulaire IMAP/SMTP)
2. `screenshot` -> `/tmp/therese-tests/A2-28_email_setup_wizard.png`
3. `javascript_tool` -> vérifier qu'il n'y a pas d'erreur bloquante (écran blanc, erreur JS)

**Résultat attendu** : Si l'email n'est pas configuré : un wizard de setup est affiché avec des instructions claires pour connecter un compte (Gmail OAuth ou IMAP/SMTP). Le texte est compréhensible pour Marc (pas de jargon technique). Si l'email est déjà configuré : la boîte de réception est visible avec un bouton "Nouveau message" ou "Composer".
**États testés** : empty (pas configuré) OU loaded (configuré)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-28_email_setup_wizard.png`

---

### Étape 29 : Email configuré - liste emails et bouton composer

**Priorité** : P1
**Pré-condition** : Email configuré (sinon skip)
**URL** : http://localhost:1420/?panel=email

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier si une liste d'emails est visible (éléments .email-item, .message-row ou équivalent)
2. `find` -> bouton "Nouveau message" ou "Composer" ou icône crayon
3. `screenshot` -> `/tmp/therese-tests/A2-29_email_inbox.png`
4. `javascript_tool` -> si le bouton composer existe, cliquer dessus
5. `wait_for` -> formulaire de composition visible (max 3s)
6. `screenshot` -> `/tmp/therese-tests/A2-29_email_compose.png`

**Résultat attendu** : La boîte de réception affiche les emails récents. Un bouton "Composer" permet d'ouvrir un formulaire de nouveau message (destinataire, objet, corps). Marc peut envoyer un email directement depuis l'app sans ouvrir un autre logiciel. L'interface est similaire à ce qu'il connaît (Gmail, Outlook).
**États testés** : loaded (inbox), empty (composition)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-29_email_inbox.png`

---

## Phase 6 : Calendrier (étapes 30-33)

---

### Étape 30 : Ouvrir le Calendrier

**Priorité** : P0
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=calendar`
2. `wait_for` -> `[data-testid="calendar-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A2-30_calendar_panel.png`

**Résultat attendu** : Le panneau Calendrier s'ouvre. La vue par défaut est la semaine ou le mois courant. Les jours de la semaine sont indiqués. La navigation (précédent/suivant) est disponible.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-30_calendar_panel.png`

---

### Étape 31 : Vue semaine - voir les jours

**Priorité** : P1
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `javascript_tool` -> chercher un bouton "Semaine" ou "Week" pour basculer en vue semaine (si pas par défaut)
2. `javascript_tool` -> cliquer sur le bouton vue semaine si trouvé
3. `screenshot` -> `/tmp/therese-tests/A2-31_calendar_week.png`
4. `javascript_tool` -> vérifier que les 7 jours de la semaine sont affichés (lundi à dimanche)
5. `javascript_tool` -> vérifier que la date du jour est mise en évidence

**Résultat attendu** : La vue semaine affiche les 7 jours de la semaine courante. Le jour actuel (27 mars 2026) est visuellement distinct (couleur, bordure). Les créneaux horaires sont visibles. Le calendrier est vide (aucun événement encore créé).
**États testés** : loaded, empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-31_calendar_week.png`

---

### Étape 32 : Créer un RDV "Réunion Durand" mardi prochain 10h

**Priorité** : P0
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `find` -> bouton "Ajouter" ou "+" ou cliquer sur le créneau du mardi
2. `click` -> ce bouton ou la case du mardi prochain
3. `wait_for` -> formulaire EventForm visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A2-32_event_form.png`
5. `find` -> champ titre de l'événement
6. `click` -> champ titre
7. `type` -> "Réunion Durand"
8. `find` -> champ date
9. `javascript_tool` -> calculer le mardi prochain et le définir dans le champ date
10. `find` -> champ heure de début
11. `javascript_tool` -> définir l'heure à "10:00"
12. `find` -> bouton Sauvegarder
13. `click` -> bouton Sauvegarder
14. `wait_for` -> l'événement apparaît dans le calendrier (max 3s)
15. `screenshot` -> `/tmp/therese-tests/A2-32_event_created.png`

**Résultat attendu** : Le formulaire de création d'événement s'ouvre. Marc remplit le titre "Réunion Durand" et configure la date du mardi prochain à 10h. Après sauvegarde, l'événement apparaît dans la grille du calendrier au bon créneau. Le titre est visible ou tronqué avec tooltip. Marc voit son planning se remplir.
**États testés** : empty -> filled -> success
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-32_event_created.png`

---

### Étape 33 : Naviguer au mois suivant

**Priorité** : P1
**URL** : http://localhost:1420/?panel=calendar

**Actions Chrome MCP** :
1. `find` -> bouton "Suivant" ou ">" ou flèche droite pour naviguer au mois suivant
2. `click` -> bouton suivant
3. `wait_for` -> changement de mois visible (max 2s)
4. `screenshot` -> `/tmp/therese-tests/A2-33_calendar_next_month.png`
5. `javascript_tool` -> vérifier que le titre du calendrier affiche "Avril 2026" (ou le mois suivant)
6. `find` -> bouton "Précédent" ou "<" pour revenir
7. `click` -> bouton précédent
8. `wait_for` -> retour au mois de mars (max 2s)
9. `screenshot` -> `/tmp/therese-tests/A2-33_calendar_back.png`

**Résultat attendu** : La navigation mois suivant fonctionne (Mars -> Avril 2026). Le titre du calendrier change. La grille se met à jour. Le bouton retour ramène au mois de mars. La navigation est fluide et sans rechargement de page.
**États testés** : loaded (transitions)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-33_calendar_next_month.png`

---

## Phase 7 : Tâches et kanban (étapes 34-38)

---

### Étape 34 : Ouvrir Tâches

**Priorité** : P0
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420/?panel=tasks`
2. `wait_for` -> `[data-testid="tasks-panel"]` visible (max 5s)
3. `screenshot` -> `/tmp/therese-tests/A2-34_tasks_panel.png`

**Résultat attendu** : Le panneau Tâches s'ouvre. L'interface affiche soit une vue liste (TaskList) soit un kanban (TaskKanban) avec les colonnes "À faire", "En cours", "Terminé". Un bouton d'ajout de tâche est visible. L'interface est vide au premier lancement.
**États testés** : loaded, empty
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-34_tasks_panel.png`

---

### Étape 35 : Créer tâche "Préparer proposition Durand" deadline vendredi, priorité haute

**Priorité** : P0
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `find` -> bouton "Ajouter" ou "+" dans le panneau tâches
2. `click` -> ce bouton
3. `wait_for` -> formulaire TaskForm visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A2-35_task_form.png`
5. `find` -> champ titre de la tâche
6. `click` -> champ titre
7. `type` -> "Préparer proposition Durand"
8. `find` -> champ date limite (deadline/due_date)
9. `javascript_tool` -> calculer le vendredi de la semaine courante et le définir
10. `find` -> sélecteur priorité (si présent)
11. `javascript_tool` -> si le sélecteur existe, choisir "Haute" ou "High"
12. `find` -> bouton Sauvegarder
13. `click` -> bouton Sauvegarder
14. `wait_for` -> la tâche apparaît dans la liste/kanban (max 3s)
15. `screenshot` -> `/tmp/therese-tests/A2-35_task_created.png`
16. `javascript_tool` -> vérifier que le texte "Préparer proposition Durand" est présent dans le DOM

**Résultat attendu** : La tâche est créée avec le titre "Préparer proposition Durand", une deadline au vendredi, et une priorité haute (si le champ existe). La tâche apparaît dans la colonne "À faire". La deadline et la priorité sont visuellement affichées (badge, couleur, icône).
**États testés** : empty -> filled -> success
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-35_task_created.png`

---

### Étape 36 : Créer tâche "Relancer Martin" deadline lundi

**Priorité** : P1
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `find` -> bouton "Ajouter" ou "+"
2. `click` -> ce bouton
3. `wait_for` -> formulaire TaskForm visible (max 3s)
4. `find` -> champ titre
5. `click` -> champ titre
6. `type` -> "Relancer Martin"
7. `find` -> champ date limite
8. `javascript_tool` -> calculer le lundi suivant et le définir
9. `find` -> bouton Sauvegarder
10. `click` -> bouton Sauvegarder
11. `wait_for` -> la tâche apparaît dans la liste (max 3s)
12. `screenshot` -> `/tmp/therese-tests/A2-36_task_relancer.png`
13. `javascript_tool` -> vérifier que 2 tâches sont affichées dans le panneau

**Résultat attendu** : La deuxième tâche "Relancer Martin" est créée avec une deadline au lundi suivant. Le panneau affiche maintenant 2 tâches. Les deux sont dans la colonne "À faire". Marc voit sa charge de travail se structurer.
**États testés** : filled (2 tâches)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-36_task_relancer.png`

---

### Étape 37 : Voir le kanban (À faire, En cours, Terminé)

**Priorité** : P1
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `javascript_tool` -> vérifier la présence de colonnes kanban (texte "À faire", "En cours", "Terminé" ou "Todo", "In Progress", "Done")
2. `javascript_tool` -> compter les colonnes (au moins 3)
3. `screenshot` -> `/tmp/therese-tests/A2-37_kanban_view.png`
4. `javascript_tool` -> vérifier que les 2 tâches sont dans la colonne "À faire"

**Résultat attendu** : Le kanban affiche 3 colonnes minimum : "À faire", "En cours", "Terminé". Les 2 tâches de Marc sont dans la colonne "À faire". Les colonnes "En cours" et "Terminé" sont vides. Le layout est en grille horizontale claire.
**États testés** : filled (colonne À faire), empty (autres colonnes)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-37_kanban_view.png`

---

### Étape 38 : Déplacer une tâche en "En cours"

**Priorité** : P0
**URL** : http://localhost:1420/?panel=tasks

**Actions Chrome MCP** :
1. `find` -> tâche "Préparer proposition Durand"
2. `javascript_tool` -> tenter un drag & drop vers la colonne "En cours"
3. `screenshot` -> `/tmp/therese-tests/A2-38_task_drag.png`
4. `javascript_tool` -> si drag & drop échoue, chercher un sélecteur de statut sur la tâche et changer vers "En cours"
5. `wait_for` -> la tâche change de colonne (max 3s)
6. `screenshot` -> `/tmp/therese-tests/A2-38_task_in_progress.png`
7. `javascript_tool` -> vérifier que la colonne "En cours" contient 1 tâche et la colonne "À faire" contient 1 tâche

**Résultat attendu** : La tâche "Préparer proposition Durand" passe de "À faire" à "En cours" via drag & drop ou sélecteur. La colonne "En cours" contient maintenant 1 tâche. La colonne "À faire" en contient 1 ("Relancer Martin"). La modification est persistée.
**États testés** : filled -> filled (changement de colonne)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-38_task_in_progress.png`

---

## Phase 8 : Board IA - délibération business (étapes 39-40)

---

### Étape 39 : Ouvrir Board IA - question business

**Priorité** : P0
**Pré-condition** : Clé API valide configurée
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `navigate` -> `http://localhost:1420`
2. `wait_for` -> page principale chargée (max 5s)
3. `find` -> bouton Board dans le header (icône Gavel ou texte "Board")
4. `click` -> bouton Board
5. `wait_for` -> `[data-testid="board-panel"]` visible (max 5s)
6. `screenshot` -> `/tmp/therese-tests/A2-39_board_panel.png`
7. `find` -> champ de saisie dans le board (textarea ou input)
8. `click` -> champ de saisie
9. `type` -> "Dois-je accepter une mission à 600 euros/jour pour un grand compte ?"
10. `screenshot` -> `/tmp/therese-tests/A2-39_board_question.png`
11. `find` -> `[data-testid="board-submit-btn"]`
12. `click` -> `[data-testid="board-submit-btn"]`
13. `wait_for` -> début de la délibération (max 15s)
14. `screenshot` -> `/tmp/therese-tests/A2-39_board_deliberating.png`

**Résultat attendu** : Le Board IA s'ouvre. Marc pose une question business stratégique. Le clic sur le bouton de soumission lance la délibération des 5 conseillers. L'interface montre l'état "en cours de délibération" avec un indicateur de progression.
**États testés** : loaded, filled, loading
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-39_board_deliberating.png`

---

### Étape 40 : Voir la délibération - résultat avec pros/cons

**Priorité** : P1
**Pré-condition** : Clé API valide et délibération en cours/terminée
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `wait_for` -> `[data-testid="board-result"]` visible (max 120s)
2. `screenshot` -> `/tmp/therese-tests/A2-40_board_result.png`
3. `javascript_tool` -> vérifier la présence des cartes des conseillers (au moins 3 visibles)
4. `javascript_tool` -> vérifier qu'une synthèse (SynthesisCard) est affichée
5. `javascript_tool` -> vérifier que le contenu mentionne des arguments pour et contre (avantages/inconvénients)
6. `screenshot` -> `/tmp/therese-tests/A2-40_board_synthesis.png`

**Résultat attendu** : Les 5 conseillers ont répondu. Chaque conseiller a sa carte avec son rôle, son avis et ses arguments. La synthèse résume les positions avec des pros/cons clairs. Marc obtient des perspectives variées sur sa question tarifaire (rentabilité, charge de travail, positionnement, risques). Le rendu est professionnel et lisible.
**États testés** : filled (résultats complets)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-40_board_result.png`

---

## Phase 9 : Settings et fin de journée (étapes 41-42)

---

### Étape 41 : Ouvrir Settings - vérifier son profil

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="settings-btn"]`
2. `click` -> `[data-testid="settings-btn"]`
3. `wait_for` -> `[data-testid="settings-modal"]` visible (max 3s)
4. `screenshot` -> `/tmp/therese-tests/A2-41_settings_open.png`
5. `find` -> `[data-testid="settings-tab-profile"]` (ou premier onglet Profil)
6. `javascript_tool` -> si l'onglet profil n'est pas sélectionné, cliquer dessus
7. `screenshot` -> `/tmp/therese-tests/A2-41_settings_profile.png`
8. `javascript_tool` -> vérifier que le profil contient des champs prénom, nom, activité (remplis lors de l'onboarding)

**Résultat attendu** : Le modal des paramètres s'ouvre. L'onglet Profil affiche les informations saisies lors de l'onboarding (prénom, nom, activité). Marc peut vérifier et modifier ses informations. Les champs sont éditables. Un bouton Sauvegarder est visible.
**États testés** : loaded, filled (profil existant)
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-41_settings_profile.png`

---

### Étape 42 : Fermer settings - fin de journée

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `find` -> `[data-testid="settings-close-btn"]`
2. `click` -> `[data-testid="settings-close-btn"]`
3. `wait_for` -> `[data-testid="settings-modal"]` disparaît (max 2s)
4. `find` -> `[data-testid="app-main"]` (retour à l'interface principale)
5. `screenshot` -> `/tmp/therese-tests/A2-42_end_of_day.png`
6. `javascript_tool` -> vérifier que l'app est dans un état stable (pas d'erreur console, pas d'écran blanc)

**Résultat attendu** : Le modal se ferme avec une animation fluide. L'interface principale est à nouveau visible et interactive. Toutes les données créées pendant la session sont persistées (conversations, contacts CRM, devis, tâches, événement calendrier). L'app est stable et prête pour la prochaine session de Marc.
**États testés** : loaded
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-42_end_of_day.png`

---

## Récapitulatif des priorités

| Priorité | Étapes | Count |
|----------|--------|-------|
| P0 | 1, 2, 3, 4, 7, 12, 13, 14, 15, 16, 17, 20, 21, 22, 24, 26, 27, 30, 32, 34, 35, 38, 39 | 23 |
| P1 | 5, 6, 8, 9, 10, 11, 18, 19, 23, 25, 28, 29, 31, 33, 36, 37, 40, 41, 42 | 19 |
| P2 | - | 0 |

## Phase 11 : États d'erreur (étapes 43-45)

> **Ajoutée le 08/09/2026 (B-600).** La matrice de couverture ne portait aucun
> « État erreur » pour les dix modules. Trois étapes visent des témoins qui
> existent dans le code ; un témoin absent est un FAIL, pas une étape « sans objet ».
>
> **Liste de messages virtualisée (B-599)** : la liste du chat passe par
> react-virtuoso, seuls les messages de la fenêtre de rendu portent
> `[data-testid="chat-message-item"]`. Un comptage DOM à zéro prouve le vide ;
> un comptage DOM ne prouve JAMAIS un total. Pour un total, lire le store :
> `javascript_tool` -> `window.__therese?.stores?.chat?.getState().messages.length`
> si ce pont est exposé, sinon `GET /api/chat/conversations/{id}/messages`
> avec le jeton de session. « Le dernier message » = le dernier élément
> rendu après un défilement en bas de liste.

---

### Étape 43 : Clé API invalide - l'erreur est nommée, aucun faux succès

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. `javascript_tool` -> `window.__therese.runAction('settings.open')`
2. `wait_for` -> `[data-testid="settings-modal"]` visible (max 3s)
3. `click` -> `[data-testid="settings-tab-ai"]`
4. choisir un fournisseur cloud, saisir la clé `sk-invalide-A2-43`, valider
5. `wait_for` -> `[data-testid="settings-modal"] [role="alert"]` visible (max 15s)
6. `screenshot` -> `/tmp/therese-tests/A2-43_cle_invalide.png`
7. `javascript_tool` -> `[...document.querySelectorAll('[role="status"]')].map(n => n.textContent).join(' | ')` (aucune notification de succès)

**Résultat attendu** : un message d'erreur lisible dans la modale, aucun toast de succès, le fournisseur précédent reste utilisable.
**États testés** : error
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-43_cle_invalide.png`

---

### Étape 44 : Moteur arrêté - les listes disent « indisponible », pas « vide »

**Priorité** : P0
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. arrêter le backend de développement (Ctrl+C dans `make dev-backend`, JAMAIS une instance installée)
2. `wait_for` -> l'indicateur de connexion affiche « Moteur arrêté » ou « Erreur du moteur » (max 20s)
3. `javascript_tool` -> `window.__therese.runAction('crm.open')`
4. `wait_for` -> un `[role="alert"]` visible (max 10s)
5. `screenshot` -> `/tmp/therese-tests/A2-44_crm_moteur_arrete.png`
6. relancer le backend ; `wait_for` -> « Moteur actif » (max 30s) ; `screenshot` -> `/tmp/therese-tests/A2-44_moteur_revenu.png`

**Résultat attendu** : le CRM affiche une erreur explicite, jamais un pipeline vide qui ferait croire à l'absence de contacts. Au retour du moteur, les données reviennent sans redémarrer l'application.
**États testés** : error, recovery
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-44_crm_moteur_arrete.png`

---

### Étape 45 : Facture - PDF impossible sans profil émetteur complet

**Priorité** : P1
**URL** : http://localhost:1420

**Actions Chrome MCP** :
1. Paramètres > Profil : vider le SIRET, enregistrer
2. ouvrir « Devis et factures », ouvrir une facture existante, demander le PDF
3. `wait_for` -> un message d'erreur qui nomme le champ manquant (max 10s)
4. `screenshot` -> `/tmp/therese-tests/A2-45_pdf_profil_incomplet.png`
5. remettre le SIRET, enregistrer, redemander le PDF -> succès

**Résultat attendu** : le refus nomme précisément ce qui manque (« SIRET ») et où le renseigner ; aucun PDF non conforme n'est produit. Après correction, le PDF est généré.
**États testés** : error, success
**Si FAIL** : Screenshot `/tmp/therese-tests/A2-45_pdf_profil_incomplet.png`

---

## Matrice de couverture

| Module | Étapes | État vide | État rempli | État erreur | État loading |
|--------|--------|-----------|-------------|-------------|--------------|
| Dashboard | 1-2 | oui | oui | - | - |
| Chat | 3-7 | oui | oui | - (moteur : 44) | oui |
| Sidebar | 8-11 | - | oui | - | - |
| CRM | 12-19, 44 | oui | oui | oui (44) | oui |
| Factures | 20-26, 45 | oui | oui | oui (45) | oui |
| Email | 27-29 | oui | oui | - | - |
| Calendrier | 30-33 | oui | oui | - | - |
| Tâches | 34-38 | oui | oui | - | - |
| Board IA | 39-40 | oui | oui | - | oui |
| Settings | 41-43 | - | oui | oui (43) | - |

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
2. Base SQLite **existante** (onboarding déjà complété)
3. Clé API OpenAI configurée et sauvegardée dans les settings
4. localStorage contient le flag onboarding complété
5. Chrome avec extension Claude-in-Chrome ou Chrome DevTools MCP actif
6. Dossier screenshots créé : `mkdir -p /tmp/therese-tests`

## Différences clés avec A1 (Sophie)

| Aspect | A1 - Sophie | A2 - Marc |
|--------|-------------|-----------|
| Onboarding | Testé (étapes 1-10) | Skippé (déjà fait) |
| Clé API | Non configurée au départ | Déjà configurée (OpenAI) |
| Dashboard | Non testé | Testé (étapes 1-2) |
| CRM | Survol (1 lead) | Approfondi (contact complet, pipeline, notes, recherche) |
| Facturation | 1 devis simple | Devis détaillé (3 jours, TVA), conversion facture, PDF |
| Email | Non testé | Testé (setup wizard ou inbox) |
| Board IA | Question freelance | Question business (tarif grand compte) |
| Tâches | 1 tâche | 2 tâches, kanban, déplacement |
| Calendrier | 1 événement | 1 événement + navigation mois |

## Durée estimée

- Parcours complet (45 étapes) : ~30-40 minutes
- P0 uniquement (23 étapes) : ~15-20 minutes
- Sans clé API (skip 4-7, 39-40) : retrancher ~10 minutes