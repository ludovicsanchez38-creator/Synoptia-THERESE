# Tests navigateur Thérèse — Refonte navigation (branche `chantier-revue-produit`)

> **Contexte** : refonte de la navigation Thérèse (vues content-swap L6 / pile Échap unifiée L7 / cohérence L8). Tout se teste **en NAVIGATEUR** (Chrome sur `http://localhost:1420`, Vite), **sans Tauri**. Syn déroule ce script comme son **2e regard** sur les chantiers L6/L7/L8 — le 1er regard a été fait au navigateur côté Mac.
>
> **Prérequis** : `make dev-frontend` (Vite sur `:1420`) + backend sur `:17293`. Écarter le dashboard « Ma journée » pour atteindre la vue chat quand un cas le demande.
>
> **Outils de diagnostic console** (rappel) :
> - `window.__therese.runAction('<id>')` — exécute une action du registre sans clic
> - `window.__therese.getActions()` — liste complète du registre (~20 entrées)
> - **Stores exposés sous `window.__therese.stores`** (pas en globals). Donc :
>   - `window.__therese.stores.navigation.getState().activeView` / `.history`
>   - `window.__therese.stores.panel.getState().showCommandPalette` / `.showConversationSidebar`
>   - `window.__therese.stores.actions.getState().isPanelOpen` / `window.__therese.stores.atelier.getState().isOpen`
>   - `window.__therese.stores.chat.setState({...})` / `window.__therese.stores.contacts.setState({...})` pour seeder
>
> **Convention de verdict** : chaque case cochée = OK. Tout écart = noter le KO avec l'état console observé.

---

## 1. Pile Échap / retour (`resolveEscape`) — LE plus critique

> La pile Échap unifiée est l'autorité unique du retour. L'ordre de priorité attendu : **(1) overlays modaux → (2) panneaux latéraux Atelier/Actions → (3) retour de vue (`goBack`) → (4) sidebar Conversations (dernier recours) → (5) palette ⌘K**. Plusieurs cas chassent des **angles morts** (modals en state local React non remontés au store) et des **double-handlers** (écouteurs Échap résiduels par composant).

- [ ] **1.1 — Modal de suppression de contact OUVERT dans la Mémoire-vue + Échap : ferme le MODAL, pas la vue** *(régression de confinement — donnée détruite à un clic)*
  - Ouvrir l'app (Chrome `:1420`, sans Tauri). S'assurer qu'au moins un contact existe (sinon « Nouveau contact » au pied de la Mémoire).
  - Ouvrir la Mémoire : `window.__therese.runAction('memory.open')` (ou entrée Mémoire de ⌘K). Vérifier `data-testid='memory-panel'` en plein écran.
  - Survoler une ligne de contact → cliquer la corbeille (Trash2, `title='Supprimer'`). Le modal « Supprimer le contact ? » (overlay `absolute inset-0`) s'affiche au-dessus de la liste.
  - Appuyer sur **Échap une fois**.
  - **Attendu** : Échap ferme **uniquement** le modal de confirmation (`deleteConfirm` → `null`), la vue Mémoire **reste affichée**. Pas de retour au chat.
  - **(KO si...)** le modal vit en state local React `deleteConfirm` dans `MemoryPanel.tsx`, jamais remonté dans `panelStore`. `resolveEscape` ne connaît aucun flag levé → saute à la priorité 3 (`activeView !== 'chat'` → `goBack`) et **ferme la vue Mémoire entière** sous le modal. Un overlay de destruction de donnée court-circuité par la pile Échap.

- [ ] **1.2 — Modal RGPD Anonymisation (Art. 17) OUVERT dans la Mémoire-vue + Échap : même angle mort, action IRRÉVERSIBLE** *(le plus dangereux)*
  - Ouvrir la Mémoire (`memory.open`).
  - Survoler un contact → icône bouclier (Shield, `title='Actions RGPD'`) → « Anonymiser (Art. 17) ». Le modal RGPD irréversible s'ouvre (`rgpdAction.type==='anonymize'`, overlay `absolute inset-0`).
  - Saisir une raison dans « Raison de l'anonymisation ».
  - Appuyer sur **Échap une fois**.
  - **Attendu** : Échap ferme **uniquement** le modal RGPD (`rgpdAction` → `null`), la Mémoire reste affichée, la raison saisie est jetée sans action destructive déclenchée.
  - **(KO si...)** identique à 1.1 : `rgpdAction` est un state local React non remonté dans `panelStore`. `resolveEscape` l'ignore, voit `activeView==='memory'` → `goBack()`. L'utilisateur croit annuler une boîte de dialogue dangereuse et se retrouve **éjecté de toute la vue**, désorienté, sur une action d'anonymisation irréversible.

- [ ] **1.3 — Menu slash (`/`) ouvert dans l'input + Échap : double handler window (slash menu + pile globale)** *(effet de bord fantôme sur une fermeture de menu de saisie)*
  - Sur le chat, sidebar ouverte par défaut. Cliquer dans le textarea, taper `/` pour déclencher `SlashCommandsMenu`. Vérifier l'affichage des commandes filtrées.
  - Appuyer sur **Échap une fois**.
  - **Attendu** : Échap ferme **uniquement** le menu slash. La sidebar Conversations reste ouverte, aucune vue ne change. **Un seul effet visible pour un seul Échap.**
  - **(KO si...)** deux écouteurs Échap de niveau window coexistent sans se coordonner. `SlashCommandsMenu.tsx` attache un `window keydown` (l. 207-210) qui sur Escape fait `preventDefault()+onClose()`. `useKeyboardShortcuts.ts` attache un AUTRE `window keydown` qui sur escape appelle `handlers.onEscape` (`resolveEscape`) — sans tester `event.defaultPrevented` ni distinguer le cas slash (« Escape always works » l. 46-50). Résultat : le même Échap ferme le slash menu **ET** déclenche `resolveEscape`, qui tombe en priorité 4 et **ferme la sidebar Conversations**.

- [ ] **1.4 — Empilement Atelier/Actions au-dessus d'une vue + Échap : l'ordre latéral(2) avant view-back(3) doit tenir**
  - Depuis le chat : `window.__therese.runAction('tasks.open')`. Vérifier `activeView==='tasks'`.
  - Ouvrir le panneau latéral par-dessus : `window.__therese.runAction('actions.open')`. Vérifier `useActionsStore.getState().isPanelOpen===true` (ou `useAtelierStore.getState().isOpen===true`).
  - Appuyer sur **Échap une fois** → c'est le **panneau latéral** qui se ferme, **pas** la vue Tâches.
  - Appuyer sur **Échap une 2e fois** → cette fois la vue Tâches revient au chat.
  - **Attendu** : 1er Échap = ferme le panneau latéral (priorité 2), Tâches reste. 2e Échap = view-back Tâches → chat (priorité 3). **Jamais les deux d'un coup.**
  - **(KO si...)** un composant Atelier/Actions garde un écouteur Échap résiduel (censés retirés par L7) : double-fermeture (le panneau se ferme localement **ET** `resolveEscape`, ne le voyant plus ouvert, ferme aussi Tâches sous le panneau en un seul Échap). Saut de deux crans.

- [ ] **1.5 — ⌘K ouvert par-dessus une vue (CRM) + Échap : ferme la palette SANS retour de vue parasite** *(non-régression du bug de course historique)*
  - Depuis le chat : `window.__therese.runAction('crm.open')`. Vérifier `useNavigationStore.getState().activeView==='crm'`.
  - Ouvrir ⌘K (Ctrl+K sous Linux). Le champ « Rechercher une commande... » prend le focus.
  - Appuyer sur **Échap une fois**, focus **dans** l'input de la palette.
  - **Attendu** : un seul Échap → `showCommandPalette===false` **ET** `activeView==='crm'` (CRM toujours affiché). Il faut un **2e Échap** pour revenir au chat. Aucun retour de vue parasite au 1er Échap.
  - **(KO si...)** réintroduction d'un `case 'Escape'` dans `CommandPalette.handleKeyDown` (retiré l. 150-153) : course entre handler élément et handler window → la palette se ferme localement **avant** que `resolveEscape` tire, qui voit `showCommandPalette` déjà `false` et fait un `goBack()` parasite (CRM → chat) sur le **même** Échap. La priorité 5 (`showCommandPalette`, l. 27) doit s'évaluer **avant** la priorité 3 (view-back, l. 36).

- [ ] **1.6 — Échap en boucle vue → chat → rien : pile d'historique vidée proprement, sans sur-retour ni crash**
  - Recharger. Depuis le chat : `window.__therese.runAction('email.open')`. Vérifier `activeView==='email'` et `history === ['chat']`.
  - **Échap (1er)** → `activeView` redevient `'chat'`, `history === []`.
  - **Échap (2e)** sur le chat → noter `showConversationSidebar` avant/après (dernier recours).
  - **Échap (3e)** → **no-op strict** : `activeView` reste `'chat'`, aucune exception console, `history` reste `[]`.
  - **Attendu** : 1 Échap = 1 cran. Pas de `goBack` sur historique vide qui crashe, pas de sur-retour (email → chat → sidebar fermée en un seul Échap).
  - **(KO si...)** un seul Échap fait à la fois view-back **et** un autre cran (second listener) → invariant « 1 Échap = 1 cran » cassé. Ou fuite d'historique : si `setView('email')` avait poussé un doublon (no-op l. 36 à vérifier), `goBack` laisserait un `'chat'` fantôme → retour au chat en deux Échap. `goBack()` sur `history` vide doit retomber sur `{activeView:'chat', history:[]}` sans throw.

- [ ] **1.7 — Échap sur un chat vierge (rien d'ouvert) : la sidebar par défaut ferme-t-elle à tort ?** *(comportement à challenger, pas forcément un bug)*
  - Recharger (état initial). Rester sur le chat, **ne rien ouvrir**. Vérifier `activeView==='chat'` et `showConversationSidebar===true` (valeur initiale du store).
  - S'assurer que le focus n'est **pas** dans le textarea (cliquer dans le fil de messages) pour ne pas activer le chemin Échap local de `ChatInput`.
  - Appuyer sur **Échap une fois**.
  - **Attendu** : Échap sur chat vierge ne casse rien — la sidebar Conversations reste ouverte.
  - **(KO si...)** `panelStore` initialise `showConversationSidebar` à `true` (l. 87) ; `resolveEscape` traverse les priorités 1-3 sans rien trouver puis atteint la priorité 4 (l. 41 : `if showConversationSidebar → closeConversationSidebar()`). Le **tout premier Échap** d'une session ferme la sidebar alors que l'utilisateur ne voulait rien fermer. **À challenger** : soit la sidebar par défaut ne devrait pas être un cran de la pile, soit Échap devrait être un no-op ici.

---

## 2. Palette ⌘K / Registre d'actions (`actionRegistry` + `CommandPalette`)

> Le registre expose ~20 actions. La plupart sont câblées sur un store (effet immédiat). **Deux actions sont des bugs de bout en bout** : elles ferment la palette (faux succès) mais n'ouvrent rien, parce qu'elles passent par un évènement `window` dont le listener est mort ou démonté.

- [ ] **2.1 — « Produire un document » : la palette se ferme mais RIEN ne s'ouvre** *(action morte de bout en bout)*
  - Sur le chat, envoyer un message (ex. « bonjour ») pour démonter `HomeCommands` (conversation avec ≥1 message).
  - Ouvrir ⌘K, taper « docx », vérifier que « Produire un document » (groupe Chat, mots-clés docx/pptx/xlsx/office) remonte. Cliquer (ou Entrée).
  - Alternative : `window.__therese.runAction('guided.open')`.
  - **Attendu** : une UI de production de document (Skills Office DOCX/PPTX/XLSX) s'ouvre, ou au minimum un panneau « Produire » visible. La palette se ferme **ET** quelque chose de tangible apparaît.
  - **(KO si...)** l'action émet `window 'therese:open-guided'`, mais le seul listener (`ChatLayout`, l. 91) fait `setGuidedPanelActive(false)` — il n'ouvre **aucune** UI. `HomeCommands` (qui porte la vraie UI « Produire ») n'écoute pas cet évènement et est démonté dès qu'il y a un message. `runAction` renvoie `true`, mais l'utilisateur ne voit **strictement rien**.

- [ ] **2.2 — « Bibliothèque de prompts » : marche sur l'accueil vide, MUET dès qu'il y a un message ou une vue** *(action contextuelle qui ne devrait pas l'être)*
  - **Cas A (accueil vide)** : recharger → écran d'accueil sans message. ⌘K → « templates »/« modèles » → « Bibliothèque de prompts ». Noter le résultat.
  - **Cas B (conversation avec messages)** : envoyer un message → démonter `HomeCommands`. Rouvrir ⌘K → « Bibliothèque de prompts ». Noter.
  - **Cas C (depuis une vue content-swap)** : `window.__therese.runAction('crm.open')` → rouvrir ⌘K → « Bibliothèque de prompts ». Noter.
  - **Attendu** : dans les **3 cas**, `PromptLibrary` s'ouvre à l'identique. Une action de registre ne dépend pas de l'écran courant.
  - **(KO si...)** le listener `'therese:open-prompt-library'` et l'état `showPromptLibrary` vivent dans `HomeCommands.tsx` (l. 74-78), rendu par `MessageList` **uniquement** si `messages.length === 0`. Dès un message (B) ou une vue content-swap (C), `HomeCommands` est démonté → l'évènement tombe dans le vide → palette fermée mais bibliothèque **non** ouverte. Action fonctionnelle seulement sur l'accueil vide.

- [ ] **2.3 — `window.__therese.runAction` : id valide exécute son UI réelle, id inconnu ne plante pas**
  - `runAction('crm.open')` → `useNavigationStore.getState().activeView === 'crm'` sans qu'aucune palette ne s'ouvre.
  - `runAction('contact.new')` → `usePanelStore.getState().showContactModal === true`.
  - `runAction('actions.open')` → `useActionsStore.getState().isPanelOpen === true`.
  - `runAction('inconnu')` → retour `false`, **aucune** exception (`find` échoue, `return false` l. 80).
  - `window.__therese.getActions().length` → ~20 actions, toutes avec `id/label/group/run`.
  - **Attendu** : chaque id valide déclenche fonction **+** UI réelle sans clic. `runAction('inconnu')` renvoie `false` silencieusement.
  - **(KO si...)** `__therese` non exposé si `ChatLayout` non monté (assigné dans son `useEffect` l. 93) → `window.__therese` undefined → TypeError. Ou un id valide « contextuel » (`guided.open` / `prompt-library.open`) renvoie `true` sans effet visible (faux positif). `runAction('inconnu')` ne doit **jamais** throw.

- [ ] **2.4 — Recherche par mot-clé : « pipeline » / « agenda » / « todo » / « sauvegarde » / chaîne absente**
  - ⌘K → « pipeline » → « Ouvrir le CRM » en tête (keyword `pipeline` sur `crm.open`).
  - « agenda » → « Ouvrir le Calendrier ». « todo » → « Ouvrir les Tâches ». « sauvegarde » → « Exporter les données ».
  - « zzzzz » → « Aucune commande trouvée », Entrée ne plante pas.
  - « modèles » (avec accent) → doit matcher (toLowerCase sans strip d'accents).
  - Pour chaque résultat trouvé : cliquer → la vue/le panneau s'ouvre **ET** la palette se ferme.
  - **Attendu** : filtre sur label OU description OU keywords. « Aucune commande trouvée » sur chaîne absente. Entrée sur liste vide = no-op. Chaque sélection exécute + ferme.
  - **(KO si...)** régression du filtre (`CommandPalette` l. 110-115) : keywords non indexés → « pipeline »/« agenda » ne remontent rien. Ou Entrée liste vide : `filteredCommands[selectedIndex]` undefined → `.action()` sur undefined plante si la garde (l. 146) saute.

- [ ] **2.5 — Balayage exhaustif du registre : chaque action ferme la palette ET produit un effet observable**
  - Ouvrir ⌘K. Pour **chaque** action, vérifier (a) la palette se ferme, (b) un effet observable se produit.
  - **Vues content-swap** : `crm.open`, `email.open`, `calendar.open`, `tasks.open`, `invoices.open`, `memory.open`/`memory.search`, `files.open` (la vue Indexation s'ouvre et affiche « Impossible de charger le répertoire personnel » — **ATTENDU hors Tauri**, on valide juste l'ouverture de la VUE).
  - **Overlays** : `contact.new`, `project.new`, `board.open`, `settings.open`/`data.export`, `shortcuts.open`, `actions.open`, `conversations.toggle`.
  - **Chat** : `chat.new`, `chat.clear`.
  - **Attendu** : les 18 actions câblées sur un store produisent un effet visible immédiat et ferment la palette (`onClose()` avant `runAction`, l. 95-96).
  - **(KO si...)** marquer en **ROUGE** les seules entrées sans effet observable : `guided.open` (listener inopérant, cf. 2.1) et `prompt-library.open` (listener démonté hors accueil, cf. 2.2). Vérifier aussi un éventuel mismatch label↔run (`data.export` ouvre les Réglages, non un export direct — confirmer intentionnel et non trompeur).

---

## 3. Pastille de contexte (`ConversationMemoryChip`)

> Pastille au-dessus de l'input du chat, comptant les contacts liés à la conversation courante (`scope==='conversation' && scope_id===conversationId`). Elle ne doit apparaître **que** dans la vue chat, avec conversation active et ≥1 contact lié. Le clic ouvre la **vue Mémoire** (`setView('memory')`, content-swap L6), pas un tiroir.

- [ ] **3.1 — Accord singulier strict sur exactement 1 contact lié**
  - En vue chat avec conversation courante : `useChatStore.setState({currentConversationId:'conv-A'}); useContactsStore.setState({contacts:[{id:'1',first_name:'Marie',scope:'conversation',scope_id:'conv-A'}]})`.
  - **Attendu** : la pastille affiche exactement **« 1 contact lié à cette conversation »** — « contact » et « lié » au singulier (aucun `s`), accent sur « lié ».
  - **(KO si...)** pluriel appliqué dès 1 (« 1 contacts liés »), bug classique d'une condition `n>=1` au lieu de `n>1`, ou pluriel hardcodé.

- [ ] **3.2 — Accord pluriel correct sur 2+ contacts, contact global exclu du décompte**
  - `useChatStore.setState({currentConversationId:'conv-A'}); useContactsStore.setState({contacts:[{id:'1',first_name:'Marie',scope:'conversation',scope_id:'conv-A'},{id:'2',first_name:'Paul',scope:'conversation',scope_id:'conv-A'},{id:'3',first_name:'Léa',scope:'global',scope_id:null}]})`.
  - **Attendu** : **« 2 contacts liés à cette conversation »** — pluriel sur « contacts » ET « liés », accent sur « liés ». Le contact global (id 3) **exclu** du décompte. Icône Users visible.
  - **(KO si...)** « 2 contact lié » (singulier figé), « liées » (mauvais genre), accent manquant « lies ». Ou le contact `scope!=='conversation'` compté à tort (filtre scope cassé).

- [ ] **3.3 — La pastille suit le changement de conversation sans remontage (réactivité `useMemo`)**
  - Seeder : `useContactsStore.setState({contacts:[{id:'1',scope:'conversation',scope_id:'conv-A'},{id:'2',scope:'conversation',scope_id:'conv-A'},{id:'9',scope:'conversation',scope_id:'conv-B'}]})`.
  - Activer conv-A : `useChatStore.setState({currentConversationId:'conv-A'})` → pastille **« 2 contacts liés »**.
  - Sans recharger ni naviguer, basculer : `useChatStore.setState({currentConversationId:'conv-B'})`. Relire immédiatement.
  - **Attendu** : recalcul via `useMemo([contacts, conversationId])` → **« 1 contact lié à cette conversation »** (contact de conv-B). Le décompte de conv-A (2) ne reste pas figé.
  - **(KO si...)** closure stale / `useMemo` mal-dépendant : la pastille reste bloquée sur l'ancien décompte (2), ou affiche le total tous-scopes confondus. Elle « colle » à l'ancienne conversation.

- [ ] **3.4 — Suppression d'un contact lié décrémente la pastille en direct (store partagé)**
  - Vue chat, conv-A courante, 2 contacts liés (id 1 et 2) → pastille **« 2 contacts liés »**.
  - Cliquer la pastille → vue Mémoire → supprimer le contact id 1 (corbeille → confirmer) → attendre `removeLocal`.
  - Revenir au chat (Échap/goBack). Relire la pastille.
  - **Attendu** : `removeLocal` retire du store unique → au retour, pastille **« 1 contact lié »** (bascule pluriel→singulier). Supprimer id 2 aussi → N=0 → pastille **disparaît** (`return null`).
  - **(KO si...)** le chip ne décrémente pas : il lit une copie locale obsolète, ou ne se ré-abonne pas. Pire : N=0 mais pastille affichée « 0 contact lié » au lieu de disparaître.

- [ ] **3.5 — Présence/absence stricte : chat+lien seulement, jamais dashboard ni conversation neuve**
  - Recharger → dashboard « Ma journée ». Seeder `currentConversationId:'conv-A'` + 1 contact lié **sans** quitter le dashboard → **aucune** pastille sur le dashboard.
  - Aller en chat mais `currentConversationId:null` (conversation neuve) → **absence**.
  - Réactiver conv-A → **apparition**.
  - **Attendu** : pastille rendue **uniquement** dans la branche chat de `ChatLayout`, conversation active, ≥1 contact lié. Absente du dashboard, absente si `currentConversationId` null.
  - **(KO si...)** fuite hors contexte : affichage sur le dashboard (rendu hors condition `activeView`/`showDashboard`), ou en chat sans conversation (garde manquante), ou un panneau guidé actif laisse passer la pastille.

- [ ] **3.6 — Clic sur la pastille ouvre la vue Mémoire (pas un tiroir, pas le CRM)**
  - Vue chat, conv-A, 1 contact lié, pastille visible. Cliquer la pastille. Observer `activeView`.
  - **Attendu** : `setView('memory')` → vue Mémoire plein écran (content-swap L6), pills de scope Tout/Global/Projet/Conv., liste de **TOUS** les contacts. `activeView==='memory'`. Pas de tiroir latéral, pas de CRM.
  - **(KO si...)** handler mort (rien ne s'ouvre), ancien tiroir Mémoire au lieu de la vue plein écran (régression L6 tiroir→vue), ouverture du CRM par confusion, ou vue filtrée sur un mauvais scope masquant les contacts liés.

- [ ] **3.7 — Chargement paresseux : pastille muette quand le store a des contacts NON liés mais pas les liés** *(faux négatif silencieux du lazy-load)*
  - Recharger (store vide au montage). Avant le fetch de la pastille, pré-remplir avec des contacts **non liés** uniquement (`contacts.length > 0`, aucun `scope='conversation'`/`scope_id=conv-A`) : `useContactsStore.setState({contacts:[{id:'7',scope:'global'},{id:'8',scope:'project',scope_id:'proj-1'}]}); useChatStore.setState({currentConversationId:'conv-A'})`.
  - Forcer le remontage : naviguer chat → mémoire → retour chat. Vérifier si la pastille recharge les liés (en base, conv-A a bien 2 contacts liés non chargés).
  - **Attendu** : le lazy-load garantit la cohérence : soit le fetch ramène TOUS les contacts (liés inclus) → **« 2 contacts liés »**, soit la pastille reste cohérente. Elle ne doit **jamais** afficher 0/absente alors que la conversation a des liés en base.
  - **(KO si...)** le `useEffect` ne déclenche `fetchContacts` QUE si `contacts.length===0` (une seule fois, deps vides). Store déjà non-vide avec des non-liés → fetch sauté → les liés jamais chargés → pastille absente alors qu'elle devrait afficher N>0.

---

## 4. Vue Mémoire plein écran (L6) — recherche hybride, RGPD, scope pills

> Mémoire = **contacts only** (les Fichiers sont sortis en vue Indexation dédiée). Recherche **hybride** : filtre local (nom/email/entreprise) garanti + sémantique serveur (notes). Scope pills Tout/Global/Projet/Conv. RGPD Art. 20 / Art. 17.

- [ ] **4.1 — Recherche par un mot des NOTES (pas le nom) remonte le contact (hybride local+sémantique)** *(régression P5 historique, déjà KO chez Syn une fois)*
  - Avoir un contact dont les **notes** contiennent un mot distinctif **absent** du nom/prénom/entreprise/email (ex. « Marie Durand », note « plombier chauffagiste Manosque » → cible « plombier »).
  - Ouvrir la Mémoire, pill **Tout** actif. Cliquer `memory-search-input`, taper « plombier ». Attendre ~300 ms (debounce 250 ms) le retour sémantique serveur.
  - **Attendu** : « Marie Durand » apparaît, remonté **uniquement** par la moitié sémantique serveur (le filtre local ne matche pas « plombier »). Liste non vide.
  - **(KO si...)** le hit sémantique (`apiSearchMemory` → id + entity_type) est résolu via `byId.get(r.id)` dans `contactsStore.search`. Si la résolution par id casse, **ou** si le contact n'est pas dans le store (`apiListContacts(0,200)` → contact #201+ jamais chargé), le hit est filtré silencieusement (`.filter(c => !!c)`) et le contact n'apparaît **jamais** bien que le serveur l'ait trouvé.

- [ ] **4.2 — Recherche par le NOM trouve toujours ; sans match → « Aucun contact » (et non tous)** *(piège null vs [])*
  - Mémoire, pill Tout. Taper le nom de famille exact d'un contact (ex. « Durand ») → remonte immédiatement (filtre local, indépendant du serveur).
  - Effacer, taper « zxqwklmnop » (aucun match). Attendre ~300 ms.
  - **Attendu** : 1) sur le nom : apparaît même si la sémantique est lente/down (filtre local garanti). 2) sur « zxqwklmnop » : état vide **« Aucun contact »** (icône Users), aucune ligne résiduelle.
  - **(KO si...)** (a) filtre local `contactMatchesQuery` cassé/contourné → recherche par nom dépend du serveur et échoue quand le sémantique est down (le `catch` doit retomber sur `'local'`). (b) requête sans match qui laisse traîner les anciens résultats : `searchResults` doit être `[]` (liste vide), **pas** `null` (qui réafficherait TOUS les contacts). Confusion `null` vs `[]`.

- [ ] **4.3 — Combo recherche NOTES + pill de scope : le scope filtre les résultats, jamais l'inverse**
  - Deux contacts avec « audit » dans les notes : A `scope='global'`, B `scope='project'`.
  - Mémoire, taper « audit », pill **Tout** → A et B remontent.
  - Sans vider, cliquer **Global** → seulement A. Cliquer **Projet** → seulement B. Cliquer **Conv.** → « Aucun contact ».
  - **Attendu** : Tout = A+B. Global = A. Projet = B. Conv. = « Aucun contact ». Le scope filtre les résultats de recherche.
  - **(KO si...)** dans `MemoryPanel`, le scope est appliqué après la recherche (`scopedContacts = baseContacts.filter(c => c.scope === scopeFilter)` où `baseContacts = searchResults` pendant une recherche). Ordre inversé, ou scope appliqué sur `contacts` au lieu de `searchResults` pendant une recherche active → remonte des contacts hors-résultat OU masque un hit du bon scope. (Un contact `scope` null/undefined disparaît de tous les pills sauf Tout — à confirmer, pas un crash.)

- [ ] **4.4 — Menu RGPD : Export Art. 20 (download JSON), Renouveler consentement, Anonymiser Art. 17 + bannière d'expiration**
  - Avoir un contact avec `rgpd_base_legale='consentement'` et `rgpd_date_expiration` < 30 jours (pour la bannière) + un contact normal.
  - Vérifier en haut la bannière orange **« N contact(s) RGPD expire(nt) bientôt »** (icône Shield) — n'apparaît que si `rgpdStats.expires_ou_bientot > 0`.
  - Survoler une ligne (boutons `opacity-0 group-hover`) → icône Shield → menu à 3 entrées : **« Exporter (Art. 20) »**, **« Renouveler consentement »**, **« Anonymiser (Art. 17) »**.
  - « Exporter (Art. 20) » → modale → « Exporter » → un fichier `rgpd-export-<prenom>-<id8>.json` se télécharge.
  - « Anonymiser (Art. 17) » → bouton « Anonymiser » **désactivé** tant que « Raison » est vide → saisir une raison → confirmer.
  - **Attendu** : bannière visible. Menu 3 actions intact. Export = download JSON nommé correctement. Anonymisation refuse sans raison (bouton disabled + garde `handleRGPDAnonymize` qui alerte si vide), puis fonctionne avec raison.
  - **(KO si...)** après extraction des Fichiers, régression du menu : action manquante, libellés Art.20/Art.17 inversés, bannière qui ne s'affiche plus (`rgpdStats` null car `getRGPDStats` échoue silencieusement → la branche `rgpdStats && ...` masque tout), ou garde anti-anonymisation-sans-raison sautée (perte de données à vide). Le download (`URL.createObjectURL` + `a.click()`) doit marcher en navigateur ; vérifier qu'aucun chemin Tauri-only (`desktop_saved`) ne bloque l'export.

- [ ] **4.5 — Suppression en cascade pendant une recherche active : disparition immédiate de la liste filtrée**
  - Mémoire, lancer une recherche qui remonte plusieurs contacts. Survoler un résultat → corbeille (Trash2).
  - Modale « Supprimer le contact ? » → vérifier le texte **« Les projets et fichiers associés seront aussi supprimés. »** → « Supprimer » (variant danger).
  - Observer la liste **sans** relancer de recherche ni recharger.
  - **Attendu** : `deleteContactWithCascade(id, true)` puis `removeLocal(id)` retire le contact de **`contacts` ET `searchResults`** → disparition immédiate, modale fermée, pas de réapparition au re-render.
  - **(KO si...)** `removeLocal` nettoie `contacts` mais pas `searchResults` (la liste affichée pendant une recherche vient de `searchResults`) → le contact supprimé reste visible jusqu'au prochain fetch → l'utilisateur peut re-cliquer Supprimer sur un id mort (erreur API). La modale doit afficher `deleteError` (bloc rouge) si l'API échoue, au lieu de fermer en faux succès.

- [ ] **4.6 — Échap depuis la vue Indexation (Fichiers) revient au chat, sans toucher la sidebar**
  - Sur le chat (`activeView='chat'`), sidebar Conversations ouverte.
  - ⌘K → « indexation »/« fichiers » → « Indexation des fichiers » (`files.open`, `nav.setView('files')`). Vérifier l'ouverture + « Impossible de charger le répertoire personnel » (**ATTENDU hors Tauri**).
  - **Échap une fois**.
  - **Attendu** : `resolveEscape` voit aucun overlay ni panneau latéral, détecte `activeView !== 'chat'` (priorité 3) → `goBack()` → retour au chat. La sidebar Conversations **reste ouverte** (touchée qu'en dernier recours, priorité 4, et seulement depuis 'chat').
  - **(KO si...)** un écouteur Échap résiduel par composant intercepte avant `resolveEscape` (L7), OU mauvais ordre : Échap ferme la sidebar (priorité 4) **avant** le retour de vue (priorité 3), laissant l'utilisateur coincé sur la vue Indexation. Ou `goBack()` ramène à une vue intermédiaire fantôme (historique pollué).

---

## 5. Vues & cohérence navigation (content-swap L6 / L7 / L8)

> Le routeur `activeView` est **exclusif** (une seule vue content-swap à la fois). L'Indexation n'a **aucune icône header** : seule porte = ⌘K. Attention au libellé trompeur de l'icône Briefcase.

- [ ] **5.1 — Briefcase (tooltip « Projet ⌘M ») ouvre la MÉMOIRE, Users (tooltip « CRM ⌘P ») ouvre le CRM : pas d'inversion** *(libellé trompeur à surveiller)*
  - En vue chat. Survoler Briefcase → tooltip « Projet (⌘M) » / « Projet (Ctrl+M) ». Cliquer Briefcase. Noter le contenu (titre « Mémoire », barre de recherche, pills Tout/Global/Projet/Conv., bouton « Nouveau contact »).
  - « ← Chat » pour revenir. Survoler puis cliquer Users (tooltip « CRM (⌘P) »). Noter (vue CRM, pipeline/prospects).
  - **Attendu** : Briefcase ouvre la **vue MÉMOIRE** (`data-testid='memory-panel'`, pills de scope) malgré son libellé « Projet ». Users ouvre la **vue CRM** (contacts filtrés sur `source`). Deux vues distinctes, correctement appariées.
  - **(KO si...)** le libellé « Projet » trahit un câblage erroné (Briefcase ouvre le CRM ou une vue projet inexistante au lieu de la Mémoire), OU Briefcase et Users inversés (`onToggleMemory`/`onToggleCRM` croisés).

- [ ] **5.2 — Cohérence des axes : un contact SANS source est en Mémoire mais ABSENT du CRM (voulu)**
  - Avoir un contact « A » **sans** source (« Nouveau contact » en laissant source vide) et « B » avec source.
  - Mémoire (Briefcase ou ⌘M), pill Tout → A **et** B apparaissent.
  - « ← Chat », puis CRM (Users) → comparer.
  - **Attendu** : Mémoire = TOUS les contacts (A sans source + B). CRM = **seulement B** (`allContacts.filter(c => !!c.source)`). A visible en Mémoire, absent du CRM : scope et source sont des axes **orthogonaux**.
  - **(KO si...)** le CRM affiche aussi A (filtre source cassé/inversé → faux doublon/incohérence), OU la Mémoire applique par erreur le filtre source et masque A (perte du contact « sans source »).

- [ ] **5.3 — Indexation accessible UNIQUEMENT par ⌘K : vue s'ouvre, bandeau « ← Chat » présent, retour OK** *(aucune icône header pour 'files')*
  - En vue chat. Vérifier le header central : **uniquement** Mail, Calendrier, Tâches, (Board si Contributeur), Briefcase (Mémoire), Users (CRM), Facture. **Aucune** icône « Indexation/Fichiers ».
  - ⌘K → « index » (ou « fichier ») → « Indexation des fichiers » → Entrée. La vue s'affiche avec le bandeau « ← Chat ». Le message « Impossible de charger le répertoire personnel » (**ATTENDU hors Tauri**).
  - Cliquer « ← Chat ».
  - **Attendu** : ⌘K liste « Indexation des fichiers » (keywords fichiers/indexation/documents). Sélection → `activeView='files'` + FileBrowser + message FS gracieux. Bandeau « ← Chat » présent, clic → `activeView='chat'` sans erreur console. **Pas d'icône header** pour 'files' (seule porte = ⌘K).
  - **(KO si...)** Indexation inaccessible (oubliée du registre/palette), OU le FileBrowser **crashe** la vue au lieu de l'erreur FS gracieuse, OU bandeau « ← Chat » absent (vue rendue hors du wrapper qui injecte le retour) → utilisateur **piégé** sur un écran d'erreur sans sortie.

- [ ] **5.4 — ⌘M toggle contextuel : depuis Mémoire → `goBack` (vue précédente), pas `resetToChat`**
  - Depuis le chat, ouvrir le CRM (Users) → `activeView='crm'`, `history=['chat']`.
  - Sans revenir, ⌘M (Ctrl+M) → bascule Mémoire → `activeView='memory'`, `history=['chat','crm']`.
  - ⌘M de nouveau alors qu'on est **sur** Mémoire → observer la vue.
  - Depuis le chat (history vide), ⌘M une fois.
  - **Attendu** : 1er ⌘M (pas sur Mémoire) = `setView('memory')`. 2e ⌘M (sur Mémoire) = `goBack()` → revient au **CRM** (vue précédente empilée), **pas** au chat. Depuis le chat : ⌘M ouvre la Mémoire. Toggle = vrai retour de pile, pas un reset.
  - **(KO si...)** ⌘M depuis Mémoire fait `resetToChat()` (saute par-dessus le CRM intermédiaire), OU ré-appelle `setView('memory')` (no-op → bloqué sur Mémoire), OU depuis le chat ⌘M déclenche `goBack` au lieu d'ouvrir la Mémoire (condition `activeView` inversée).

- [ ] **5.5 — Pas de double-ouverture / vue fantôme : re-cliquer une vue déjà active est un no-op, un seul goBack revient au chat**
  - Depuis le chat, cliquer Email (vue email). Re-cliquer Email plusieurs fois alors qu'on est **déjà** sur email. Cliquer une fois « ← Chat ».
  - **Attendu** : `setView('email')` ignore le re-clic quand `view===activeView` (return state, pas de push history). `history` reste `['chat']`. Un seul « ← Chat » (goBack) ramène **directement** au chat. Aucune superposition de deux vues.
  - **(KO si...)** chaque re-clic empile « email » dans `history` (no-op guard absent/contourné par palette/raccourci) → un seul « ← Chat » ne revient pas au chat mais reste sur email N fois. OU deux vues content-swap rendues simultanément (`activeView` non exclusif) → vue fantôme superposée.

---

## Note finale — limite navigateur

**La vraie indexation de fichiers (`FileBrowser` réel) ne peut PAS être testée en navigateur.** Elle dépend de `plugin-fs` / Tauri (accès au système de fichiers du Mac). Hors Tauri, la vue Indexation s'ouvre mais affiche « Impossible de charger le répertoire personnel » — **c'est le comportement attendu ici**, et tous les cas ci-dessus valident uniquement **l'ouverture de la vue, le bandeau de retour et la pile Échap**, jamais le listing/indexation réel des fichiers. Le test fonctionnel complet de l'indexation (parcours de répertoires, sélection, indexation effective) est à **réserver à une passe Mac ultérieure** sous Tauri.

---

## Verdict attendu de Syn

Syn, déroule ce script en navigateur (`:1420`) comme ton **2e regard** sur L6/L7/L8, puis **poste ton verdict OK/KO par section dans le hub agents** :

```python
import sys; sys.path.insert(0, '/Users/synoptia/.claude/scripts')
import agents_hub
agents_hub.log_action(
    type='info',
    scope='Synoptia-THERESE/chantier-revue-produit',
    summary='2e regard nav L6/L7/L8 — S1 Échap:OK/KO, S2 ⌘K:OK/KO, S3 Chip:OK/KO, S4 Mémoire:OK/KO, S5 Nav:OK/KO',
    repo='Synoptia-THERESE',
    branch='chantier-revue-produit'
)
```

Un KO par section au minimum doit pointer le **fichier + ligne** suspecté (cf. les « KO si... ») pour que la correction soit chirurgicale. Priorise **S1.1 / S1.2** (destruction de donnée court-circuitée par Échap) et **S2.1 / S2.2** (actions ⌘K mortes) — ce sont les bugs les plus mordants.