# Nadia, testeuse aguerrie de l'alpha : trace de la campagne

> **L'application n'était pas figée pendant mon parcours.** Le dernier commit du dépôt au
> moment où j'ai commencé (01:05:47) était `ff170d73 2026-09-08 01:03:16 fix(interface):
> constats des personas Jean et Karim (B-607 à B-626)`, soit **deux minutes avant mon
> premier geste**, et il touche **28 fichiers de `src/frontend/`** (dont `CommandPalette.tsx`,
> `AccessibilityTab.tsx`, `classerCommandes.ts`). Contrairement à ce qui m'était annoncé,
> l'interface a donc bougé juste avant, et Vite servait déjà le code corrigé. Trois fichiers
> backend étaient modifiés non commités (`documents.py`, `llm.py`, `token_tracker.py`).
>
> Pendant mon parcours, un autre agent a commité (`9b764743`, 01:12) mais **aucune source
> d'interface** n'a bougé entre mon premier et mon dernier geste (`git diff ff170d73 HEAD --
> src/frontend/src`, hors fichiers de test : vide). Seuls des fichiers de test sont apparus.
>
> Poste : **1024×768**, thème **sombre** (`data-theme=dark`, fond mesuré `rgb(11,18,38)`),
> clavier d'abord. Instrument : serveur MCP Playwright, document visible.
> Garde d'environnement avant le premier geste : `{visible:"visible", horloge:5194753.024}` — OK.
> Stockage local **non purgé** (consigne de l'orchestrateur).
> Parcours de 01:05 à 01:27 (heure locale), 24 captures.

## Mon impression

Je connais cette application depuis la 0.40, et ce soir j'ai eu deux sensations opposées.
Le panneau Actions m'a impressionnée : je lance « Relance clients », je vois « En cours »,
un pourcentage, trois étapes, un bouton « Annuler » rouge. Je clique, ça passe à « Arrêt
demandé… », puis « Arrêt en cours », puis « Annulé ». C'est une machine qui parle.

Le Board, lui, m'a laissée dans le noir complet. J'ai rempli ma question, choisi le mode
souverain, confirmé, et l'écran n'a **rien** fait. Pas de sablier, pas de conseiller qui
arrive, rien : le formulaire est resté là, avec son bouton « Confirmer et lancer » toujours
actif. J'ai cliqué une deuxième fois, comme n'importe qui l'aurait fait. Derrière, le moteur
avait lancé **deux** délibérations et trois conseillers avaient déjà répondu. Deux minutes
et demie de mon processeur, 1 949 jetons de sortie, et pas un pixel pour le dire. En fermant
la fenêtre j'ai tout perdu : l'historique est vide, aucune décision enregistrée.

Le reste tient bien la petite fenêtre : pas de débordement horizontal, rien sous 12 px, le
sombre est cohérent partout. Ce qui coince est ailleurs : un panneau qui recouvre des boutons
encore atteignables au Tab, une palette dont une tabulation sur trois part sur le corps du
document, un Atelier qui me propose cinq modèles locaux dont aucun n'est installé chez moi,
et le même Atelier écrit sans accents alors que toute l'application en met.

## Parcours

### Raccourcis clavier : ouvrir l'aide, essayer chacun d'eux

Aide ouverte par ⌘+/ : dialogue « Raccourcis clavier », **20 raccourcis annoncés**, pas de
défilement (le dialogue tient en 645 px de haut à 768). Chaque raccourci a été frappé pour
de vrai, et l'effet mesuré par une sonde posée sur `keydown` (élément focalisé, dialogues
présents, titres de la vue) 500 ms après la frappe.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 01 | Contrôle d'entrée | accueil configuré | **assistant de mise en route affiché par-dessus l'accueil** alors que le moteur répond `{"completed":true,"completed_at":"2026-09-07T21:44:48"}` ; DOM contenant à la fois « Bonjour. » et « Configuration initiale de Thérèse » | `01` | observation |
| 02 | Rechargement de la page | accueil | « Bonjour Jean. », brief 0 élément, mise en route ; l'assistant a disparu | `02` | observation |
| 03 | ⌘+/ | aide des raccourcis | dialogue « Raccourcis clavier », 20 entrées, focus sur un BUTTON | `03` | ok |
| 04 | Échap | ferme l'aide | fermée, focus rendu à `BODY` (il y était avant, non concluant) | — | ok |
| 05 | ⌘+N | nouvelle conversation | titre « Nouvelle conversation / Comment puis-je t'aider ? » | — | ok |
| 06 | ⌘+B | liste des conversations | tiroir ouvert, focus sur `DIV Historique des conversations` ; la région du tiroir est **`role="region"` sans `aria-label`** | — | ok (réserve a11y) |
| 07 | ⌘+M | Contacts | vue Contacts, focus sur `H2 Contacts` | — | ok |
| 08 | ⌘+D | Décision | dialogue « Décision » ouvert | `04` | ok |
| 09 | ⌘+E, ⌘+T, ⌘+I, ⌘+P, ⌘+O **avec la Décision ouverte** | soit rien (surface modale), soit la Décision se ferme | la Décision **reste à l'écran** et les vues défilent derrière : `Email/Décision/Configuration Email`, `Tâches/Décision`, `Devis et factures/Décision`, `Pipeline/Décision`, `Fichiers/Décision` | `04` | **nadia-02** |
| 10 | Échap | ferme la Décision | fermée ; on atterrit sur **Fichiers**, une vue jamais demandée à l'écran | — | preuve de nadia-02 |
| 11 | ⌘+E seul | Email | vue Email + dialogue « Configuration Email », focus sur « Fermer » | `05` | ok |
| 12 | Échap | ferme le dialogue | fermé, focus sur `H2 Email` | — | ok |
| 13 | ⌘+⇧+C | Agenda | vue Agenda, focus `H2 Agenda` | — | ok |
| 14 | ⌘+⇧+F | « Rechercher dans les Contacts » | vue Contacts ouverte, focus sur le **titre**, pas sur le champ de recherche | — | proposal |
| 15 | ⌘+⇧+A | « Améliorer THÉRÈSE » | panneau **Atelier** ouvert (Chat / Agents) | `22` | ok |
| 16 | ⌘+⇧+K | « Katia - nouvelle tâche » | **même panneau Atelier**, onglet Chat, focus resté sur `BODY` : aucun champ de nouvelle tâche mis au clavier | — | **nadia-06** |
| 17 | ⌘+, | Paramètres | dialogue « Paramètres », onglets Profil/IA/Services/Accessibilité/Confidentialité/À propos | `06` | ok |

Raccourcis non essayés : ↵ et ⇧+↵ du composeur (couverts par Karim), ⌘+⇧+D (mode
démonstration : je ne voulais pas modifier l'état de données que les personas suivants
liraient).

### Thème sombre : bascule et contrôle

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 18 | Paramètres > Accessibilité > radio « Sombre » | thème sombre réel | `data-theme="dark"`, `body` `rgb(11,18,38)` sur `rgb(230,237,247)` — la charte. Pas de confusion avec « Contraste élevé » (interrupteur laissé sur off) | `06` | ok |

### Palette de commandes au clavier (⌘K)

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 19 | ⌘+K | palette | dialogue « Rechercher dans Thérèse », focus dans le champ. **2 éléments réellement tabulables** (le champ, le bouton « Fermer ») : les 17 destinations portent `tabindex="-1"` | — | ok |
| 20 | Six tabulations d'affilée | « Tab reste dans la palette » | cycle de période **3** : 1 `BUTTON Fermer` (dedans) → 2 `DIV Résultats` (dedans) → **3 `BODY` (dehors)** → 4 `INPUT Rechercher` (dedans) → 5 `Fermer` → 6 `Résultats`. Une tabulation sur trois sort | `07` | **nadia-03** |
| 21 | Taper « Conversations » | Conversations en premier | 2 résultats : **1. Tâches** (« Créer, prioriser et terminer les actions… »), sélectionné (`aria-selected=true`, donc Entrée l'ouvrirait), **2. Conversations** | `08` | **nadia-01** |
| 22 | Échap | ferme et rend le focus | palette fermée | — | ok |

### Décision (Board) en mode souverain

Précondition manquante : `GET /api/board/decisions` renvoie `[]`. **Aucune décision
enregistrée** n'existait, je n'ai donc pas pu « lire la décision existante » de ma fiche.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 23 | ⌘+D, bouton « Souverain » | mode local | bascule OK, les cinq conseillers reçoivent un sélecteur de modèle listant **les modèles réellement installés** (`qwen3:8b (4,9 Go)`, `gemma4-tia:latest (6,3 Go)`) avec un code couleur RAM. Libellé tronqué dans le sélecteur (« qwen3:8b (4.9 ») | `09` | ok (réserve) |
| 24 | Question « Dois-je facturer mes déplacements ? » puis « Préparer la délibération souveraine » | bloc de confirmation | « Confirmer le lancement / Mode : souverain via Ollama local. » suivi d'un paragraphe qui parle **du mode cloud** et de crédits API, sous un lancement souverain | `10` | **nadia-07** |
| 25 | « Confirmer et lancer » (01:14:22) | état de délibération, cinq avis qui arrivent | **rien ne change à l'écran** : formulaire intact, bouton toujours actif, aucun `role="status"`/`aria-live`. Le panneau ne bouge pas d'un pixel | `11` | **nadia-04** |
| 26 | Deuxième clic (01:15:03), faute du moindre retour | — | **deuxième délibération lancée**. Réseau : deux `POST /api/board/deliberate` en `text/event-stream`. Journal moteur : deux lignes « Board en mode souverain (Ollama séquentiel) » | `12` | preuve de nadia-04 |
| 27 | Attente de 2 min 30 (modèle local, jusqu'à 2 min par avis : c'est normal et attendu) | au moins un avis affiché | à 01:16:49 le dialogue fait **960 caractères** et se termine toujours par « Annuler / Confirmer et lancer ». Pendant ce temps le moteur a enregistré **trois réponses de conseillers** (`[TOKEN] Recorded` à 01:15:37, 01:16:13, 01:16:50 — 629, 642 et 678 jetons de sortie, `qwen3:8b`) | `13` | preuve de nadia-04 |
| 28 | Échap | fermer | la Décision se ferme **sans un mot** sur la délibération en cours ; aucune reprise possible. Après 01:16:50 le journal moteur s'arrête net, et `GET /api/board/decisions` renvoie toujours `[]` à 01:22 | — | **nadia-05** |

### Automatisation et actions

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 29 | ⌘+K, « action » | trouver le panneau | deux entrées pour la même chose : « **Actions et relances** » (capacité) et « **Actions** » (destination) | — | proposal |
| 30 | Ouvrir « Actions » | catalogue | panneau latéral, 5 automatisations classées Organisation / Commercial / Finance, avec nombre d'étapes | `14` | ok |
| 31 | Clic sur « Relance clients » | fiche puis lancement | **lancement immédiat au premier clic**, sans écran de confirmation : « En cours… », 0 %, « Scan du CRM » en cours, deux étapes en attente, bouton « Annuler » | `15` | ok (réserve : un clic suffit à lancer un agent) |
| 32 | « Annuler » à 01:18:04 | arrêt | +14 s : « **Arrêt demandé… / Arrêt en cours** » | `16` | ok |
| 33 | Attente | état final | +58 s : toujours « Arrêt en cours ». **+97 s : « Annulé »** — l'état final arrive bien. La lenteur s'explique : Ollama traitait encore mes deux délibérations, l'appel en cours devait finir | — | ok |
| 34 | Lecture du résultat | cohérence | état « Annulé » mais **barre de progression à 100 %**, en cyan, avec l'étape 1 cochée en vert et les étapes 2 et 3 restées en attente | `17` | **nadia-08** |

### Thème sombre et petites fenêtres

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 35 | Mesure à 1024×768, panneau Actions ouvert | pas de recouvrement piégeux | `document.scrollWidth = 1024` (aucun débordement horizontal), **aucun texte sous 12 px**, un seul texte tronqué (le lien d'évitement, masqué par conception). Mais le panneau occupe x=644→1024 **sans voile**, et recouvre **10 éléments interactifs** de la colonne principale | `14`, `15` | **nadia-09** |
| 36 | `focus()` sur « Nouveau contact » (x=846, y=116, sous le panneau) | inerte ou hors tabulation | `inert` absent, **le bouton prend le focus**, alors que `elementFromPoint` à ses coordonnées rend « Scan du CRM » (le panneau) | — | preuve de nadia-09 |
| 37 | ⌘+B avec le panneau Actions ouvert | tiroir + panneau | les deux cohabitent ; le tiroir, lui, **pose bien un voile** sur la colonne centrale | `18` | ok |
| 38 | Échap (1er) | ferme la surface active | ferme le **panneau Actions**, alors que le focus était dans le tiroir (`DIV Historique des conversations`), ouvert en dernier | — | **nadia-10** |
| 39 | Échap (2e) | ferme le tiroir | tiroir fermé, retour à Contacts | — | ok |
| 40 | Redimensionnement 900×700, Agenda | lisible | mois de septembre complet, dense mais lisible, événement tronqué dans sa case (attendu) | `19` (agenda) | ok |
| 41 | ⌘+I, Devis et factures | état vide utile | « 0 document » et pourtant « **Aucun document ne correspond à ce filtre.** » avec « Réinitialiser les filtres », alors que les filtres sont sur leurs valeurs par défaut (Type = Tout, Statut = Toutes) | `20` | **nadia-11** |
| 42 | Accueil | lisible | la ligne « Sources réelles » du brief (boîte 505→521) passe **sous le composeur** (qui commence à 520) et n'est peinte qu'à moitié | `21` | **nadia-12** |

### Connecteurs, agents, atelier de code

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 43 | ⌘+⇧+A | Atelier | panneau « Atelier », onglets Chat / Agents, étiquettes « Katia: claude-sonnet-4-6 » et « Zézette: claude-sonnet-4-6 » — **deux modèles cloud annoncés sur une installation sans aucune clé cloud**, sans mention d'indisponibilité | `22` | **nadia-13** |
| 44 | Onglet « Agents » | agents locaux disponibles | 5 modèles proposés : `qwen3.5:9b` (présélectionné), `qwen3-coder:30b`, `ministral3:8b`, `devstral:24b`, `gpt-oss:20b`. **Aucun n'est installé** : `GET localhost:11434/api/tags` rend `['gemma4-tia:latest','qwen3:8b']` | `23` | **nadia-14** |
| 45 | Lecture des textes du même panneau | français accentué | « Chaque agent est **specialise** dans un domaine. **Selectionne** celui qui correspond a ta **tache**. », « **synthetise** les **resultats** », « **Redige** des textes professionnels **adaptes** a ton **activite** », « Analyse des **donnees** », « **cree** des plans d'action » | `23` | **nadia-15** |

Je n'ai rien lancé dans l'atelier de code, conformément à ma fiche.

### Console et réseau

- Console : **0 erreur, 0 avertissement** sur tout le parcours réel (19 messages, tous
  informatifs). Les 2 seules erreurs sont **les miennes**, produites par mon test de route
  inexistante : `Failed to load resource: 404 @ /api/route-qui-nexiste-pas` et
  `ApiError: Not Found at Module.request (src/services/api/core.ts:171)`.
- Réseau : aucune requête applicative en échec. Deux `POST /api/board/deliberate` en 200,
  flux `text/event-stream` (voir nadia-04).
- Réserve d'instrument : le relevé réseau montre un **très grand nombre** de
  `GET /api/processing-tasks?limit=30`, souvent par paires rapprochées. Je n'ai pas mesuré
  la fréquence sur une fenêtre bornée, donc je ne le classe pas ; c'est un angle mort.

## Constats numérotés

- **nadia-01 - P2 - Taper « Conversations » dans la palette sélectionne « Tâches », et le correctif du jour a été posé sur une palette qui n'est pas celle affichée**
  - Préconditions : accueil, thème sombre, 1024×768.
  - Étapes : ⌘+K ; taper `Conversations` ; lire l'ordre des résultats.
  - Attendu : « Conversations » en premier (Entrée doit ouvrir ce qu'on a écrit).
  - Observé : `1. Tâches…` (`aria-selected="true"`), `2. Conversations…`. Capture `08`.
  - Pourquoi ça compte au-delà du rejeu de karim-01 : le correctif B-613 **existe et est
    juste** — `src/frontend/src/lib/classerCommandes.ts` est importé par
    `src/frontend/src/components/chat/CommandPalette.tsx` (ligne 33, `filteredCommands`
    ligne 119), et je l'ai **exécuté dans la page** (`await import('/src/lib/classerCommandes.ts')`
    → rend bien `['Conversations','Tâches']`). Mais la palette réellement affichée est
    celle de **`src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx`**
    (`aria-label="Rechercher dans Thérèse"` ligne ~506), qui filtre **deux listes séparées
    sans aucun classement** : `visibleCapabilities` (lignes 428-448, `includes` sur
    titre+description+features+keywords) puis `visibleActions` (lignes 449-469). « Tâches »
    est une capacité, « Conversations » une destination : la première liste passe toujours
    devant. Le correctif ne peut donc pas se voir.
  - Preuve : capture `08`, relevé DOM de l'ordre des boutons, exécution du module dans la page.

- **nadia-02 - P2 - Les raccourcis globaux naviguent derrière une fenêtre modale ouverte**
  - Préconditions : accueil.
  - Étapes : ⌘+D (la Décision s'ouvre) ; ⌘+E ; ⌘+T ; ⌘+I ; ⌘+P ; ⌘+O ; puis Échap.
  - Attendu : soit la modale absorbe les raccourcis, soit elle se ferme en changeant de vue.
  - Observé : la Décision reste au premier plan pendant que la vue défile derrière —
    sonde : `Email/Décision/Configuration Email`, puis `Tâches/Décision`, `Devis et
    factures/Décision`, `Pipeline/Décision`, `Fichiers/Décision`. À l'Échap, on se retrouve
    dans **Fichiers** sans l'avoir jamais vue s'ouvrir. Avec ⌘+E on obtient même **deux
    dialogues empilés**.
  - Preuve : capture `04` (Décision au premier plan, vue Fichiers derrière) + journal de sonde.

- **nadia-03 - P3 - Dans la palette, une tabulation sur trois pose le focus sur le corps du document**
  - Préconditions : palette ouverte (⌘K), rien de tapé.
  - Étapes : six tabulations d'affilée, focus relevé après chacune.
  - Attendu : « Tab reste dans la palette » (promesse de la surface).
  - Observé, dans l'ordre : **1** `BUTTON Fermer` (dans la palette) · **2** `DIV Résultats`
    (dans la palette) · **3** `BODY`, **hors de la palette** · **4** `INPUT Rechercher`
    (dans la palette) · **5** `BUTTON Fermer` · **6** `DIV Résultats`. Le cycle a une
    période de 3 et la sortie tombe au **troisième** arrêt, pas au quatrième.
  - Le piège rattrape le focus au coup d'après (il ne l'empêche pas de partir).
  - Preuve : capture `07`, drapeau `dansPalette` mesuré par `activeElement.closest('[role=dialog]')`.
  - Note : le deuxième arrêt (`DIV Résultats`) est le conteneur défilant, que Chrome rend
    focalisable de lui-même ; il n'a pas de `tabindex` dans le DOM.

- **nadia-04 - P1 - Le Board souverain délibère sans rien montrer, et invite à relancer**
  - Préconditions : mode souverain, Ollama local, aucune clé cloud.
  - Étapes : ⌘+D ; « Souverain » ; question courte ; « Préparer la délibération souveraine » ;
    « Confirmer et lancer ».
  - Attendu : un état de délibération (au minimum un indicateur), puis les cinq avis.
  - Observé : **aucun changement d'écran**. Le formulaire reste, le bouton « Confirmer et
    lancer » reste actif, aucun élément `role="status"` ni `aria-live` n'existe dans le
    dialogue. Faute de retour, j'ai cliqué une seconde fois : **une seconde délibération est
    partie**. Preuves croisées : deux `POST /api/board/deliberate` (200,
    `content-type: text/event-stream`), journal moteur « Board en mode souverain (Ollama
    séquentiel) » à 01:14:22 **et** 01:15:03, et trois réponses de conseillers enregistrées
    (`[TOKEN] Recorded 311/629`, `296/642`, `294/678`, `qwen3:8b`) à 01:15:37, 01:16:13 et
    01:16:50 — pendant que le dialogue restait à 960 caractères de formulaire.
  - **Ce n'est pas la lenteur du modèle local** : les avis arrivaient bien, en 35 à 40 s
    chacun. C'est l'écran qui ne les montre pas.
  - Preuve : captures `11`, `12`, `13` ; `/tmp/therese-demo-c4/backend.out` ; relevé réseau.

- **nadia-05 - P1 - Fermer la Décision jette la délibération en cours, sans avertissement ni trace**
  - Préconditions : délibération souveraine en cours (nadia-04).
  - Étapes : Échap sur le dialogue Décision ; puis `GET /api/board/decisions`.
  - Attendu : un avertissement (« une délibération est en cours »), ou une reprise, ou au
    moins la décision partielle enregistrée dans l'Historique.
  - Observé : fermeture immédiate et muette. Le journal moteur s'arrête à 01:16:50 (dernier
    avis) et ne reprend jamais. À 01:22:40, `GET /api/board/decisions` rend toujours `[]`.
    Trois avis calculés, 1 949 jetons de sortie et ~2 min 30 de machine perdus, et le bouton
    « Historique » du Board n'a rien à montrer.
  - Preuve : journal moteur, deux appels API horodatés, capture `13`.

- **nadia-06 - P3 - ⌘+⇧+K est annoncé « Katia - nouvelle tâche » et ouvre seulement l'Atelier**
  - Étapes : ⌘+⇧+K depuis l'accueil.
  - Attendu : l'Atelier en mode Katia avec le champ de nouvelle tâche au clavier (c'est le
    libellé de l'aide).
  - Observé : le panneau Atelier s'ouvre sur l'onglet Chat, **focus resté sur `BODY`** :
    aucun champ n'est prêt. C'est exactement le même effet que ⌘+⇧+A. Deux raccourcis
    annoncés différemment pour un seul comportement.
  - Preuve : capture `22` (état obtenu), sonde de focus.
  - Fichier suspecté : `hooks/useKeyboardShortcuts.ts` (`onOpenKatiaNewTask`) câblé sur
    `openAtelierPanel` dans `ConversationCanvasPrototype.tsx` ligne 1199, la même fonction
    que `onToggleAtelierPanel` ligne 1198.

- **nadia-07 - P3 - Le bloc de confirmation d'un lancement souverain explique les frais du mode cloud**
  - Étapes : Board > Souverain > « Préparer la délibération souveraine ».
  - Observé : « Mode : souverain via Ollama local. » immédiatement suivi de « Le mode cloud
    transmet la question, le contexte, le profil local utile et les résultats web aux
    fournisseurs configurés. Jusqu'à six appels LLM peuvent consommer des crédits API. »
    Sous un lancement local, ce paragraphe fait douter de ce qui va partir.
  - Preuve : capture `10`, texte relevé dans le DOM.

- **nadia-08 - P3 - Une action annulée affiche 100 % de progression**
  - Étapes : Actions > Relance clients > Annuler > attendre l'état final.
  - Attendu : une barre qui reflète ce qui a été fait (1 étape sur 3).
  - Observé : état « Annulé » et barre **pleine à 100 %**, en cyan, avec l'étape 1 cochée
    verte et les étapes 2 et 3 restées en attente. Les deux informations se contredisent.
  - Preuve : capture `17`, relevé de texte `Relance clients | Annulé | 100% | …`.

- **nadia-09 - P2 - À 1024 px, le panneau Actions recouvre dix commandes qui restent focalisables**
  - Préconditions : 1024×768, vue Contacts, panneau Actions ouvert.
  - Étapes : ouvrir le panneau ; mesurer les boîtes ; `focus()` sur « Nouveau contact ».
  - Attendu : sous le seuil de 1280 px, un panneau couvrant isole ce qu'il cache (c'est la
    règle posée en 0.48.1 : `usePanneauCouvrant` + `VoilePanneau`).
  - Observé : le panneau occupe x=644→1024. **Aucun voile** (aucun élément `position:fixed`
    de plus de 900×700 avec un fond non transparent). **Dix éléments interactifs** de la
    colonne principale sont dessous, dont « Nouveau contact » (x=846, y=116), « Importer »,
    « Exporter », « Rechercher ⌘K », « Travaux (0 en cours) ». « Nouveau contact » n'est
    **pas `inert`**, **prend le focus** au clavier, et un clic à ses coordonnées atteint
    « Scan du CRM » (le panneau). Un utilisateur au clavier atterrit sur un bouton invisible.
  - Fichier suspecté : `src/frontend/src/components/actions/ActionPanel.tsx` — il
    n'importe ni `usePanneauCouvrant`, ni `VoilePanneau`, ni `inert`, contrairement aux six
    panneaux de `components/prototype/`.
  - Preuve : captures `14`, `15` ; mesures de boîtes et `elementFromPoint`.

- **nadia-10 - P3 - Échap ferme le panneau qui n'a pas le focus avant celui qui l'a**
  - Préconditions : panneau Actions ouvert, puis tiroir des conversations ouvert par ⌘+B
    (donc en dernier, et il détient le focus).
  - Étapes : Échap, puis Échap.
  - Attendu : la surface active (celle qui a le focus, ouverte en dernier) se ferme d'abord.
  - Observé : le **premier** Échap ferme le panneau Actions et laisse le tiroir ouvert avec
    son focus ; le second ferme le tiroir. La cascade finit juste, l'ordre est contre-intuitif.
  - Preuve : capture `18`, sondes de focus avant/après.

- **nadia-11 - P3 - « Devis et factures » vide accuse un filtre qui n'est pas posé**
  - Préconditions : 900×700, aucune facture (`0 document` affiché par l'écran lui-même).
  - Étapes : ⌘+I.
  - Attendu : un état vide qui dit « rien encore » et propose de créer.
  - Observé : « **Aucun document ne correspond à ce filtre.** » avec pour seule action
    « Réinitialiser les filtres », alors que Type = Tout et Statut = Toutes, c'est-à-dire
    les valeurs par défaut. L'action proposée ne peut rien changer.
  - Preuve : capture `20`.

- **nadia-12 - P3 - À 900×700, le pied du brief passe sous le composeur**
  - Étapes : 900×700, accueil.
  - Observé : la mention « Sources réelles » occupe y=505→521 tandis que le composeur
    commence à y=520 ; à l'écran, la ligne n'est peinte qu'à moitié.
  - Preuve : capture `21` et mesure des deux boîtes englobantes.

- **nadia-13 - P2 - L'Atelier annonce deux modèles cloud sur une installation sans clé cloud**
  - Préconditions : aucune clé cloud (`/api/config/llm` → `provider: ollama`), mode souverain.
  - Étapes : ⌘+⇧+A.
  - Observé : deux étiquettes en haut du panneau, « Katia: claude-sonnet-4-6 » et
    « Zézette: claude-sonnet-4-6 », sans aucune mention d'indisponibilité ni de prérequis.
    Le Board, lui, sait dire « Cloud » / « Souverain » et lister les modèles installés.
  - Preuve : capture `22`, `GET /api/config/llm`.

- **nadia-14 - P2 - L'onglet Agents propose cinq modèles locaux dont aucun n'est installé**
  - Étapes : ⌘+⇧+A puis onglet « Agents » ; lire le sélecteur.
  - Attendu : les modèles réellement disponibles, comme le fait le Board.
  - Observé : liste figée de 5 entrées — `qwen3.5:9b` (**présélectionnée**),
    `qwen3-coder:30b`, `ministral3:8b`, `devstral:24b`, `gpt-oss:20b`. Or Ollama ne sert
    que `gemma4-tia:latest` et `qwen3:8b` (`GET http://localhost:11434/api/tags`, et
    `GET /api/config/llm` → `available_models: ["gemma4-tia:latest","qwen3:8b"]`).
    L'agent par défaut ne peut pas tourner, et rien ne le dit avant de lancer.
  - Preuve : capture `23`, les deux appels API.

- **nadia-15 - P3 - L'onglet Agents est écrit sans accents, seul endroit de l'application dans ce cas**
  - Étapes : ⌘+⇧+A > Agents ; lire les descriptions.
  - Observé : « Chaque agent est **specialise** dans un domaine. **Selectionne** celui qui
    correspond a ta **tache**. » ; « Recherche sur le web et **synthetise** les
    **resultats** » ; « **Redige** des textes professionnels **adaptes** a ton
    **activite** » ; « Analyse des **donnees**, du code ou des documents » ; « Organise tes
    projets, **cree** des plans d'action ». Tout le reste de l'application est accentué.
  - Preuve : capture `23`, textes relevés dans le DOM.

## Ce que je signale au portail humain, sans le compter comme défaut

- **Deux entrées de palette pour une seule chose** : « Actions et relances » (capacité) et
  « Actions » (destination) mènent au même panneau (étape 29).
- **Un clic suffit à lancer un agent** : « Relance clients » démarre au premier clic depuis
  le catalogue, sans fiche préalable ni confirmation (étape 31). Ici c'est sans effet
  externe ; le jour où une automatisation enverra des e-mails, ce geste sera coûteux.
- **⌘+⇧+F « Rechercher dans les Contacts »** ouvre bien Contacts mais ne met pas le focus
  dans le champ de recherche (étape 14).
- **Le tiroir des conversations est une `role="region"` sans `aria-label`** (étape 06).
- **Une conversation fantôme** « Nouvelle conversation · 0 message · non enregistrée »
  reste listée dans le tiroir après un simple ⌘+N (capture `18`), à côté du titre doublé
  « Quelles sont mes tâches ?Quelles sont mes tâches ? » déjà signalé par Karim.
- **L'assistant de mise en route réaffiché** (étape 01) : je le laisse en observation. Il
  s'est produit **après une mise à jour à chaud de Vite**, le moteur répondait pourtant
  `completed: true`, et un simple rechargement l'a fait disparaître. Aucun utilisateur
  d'application installée n'est dans ces conditions ; je ne transforme pas un artefact
  d'instrument en défaut.

## Transitions couvertes et angles morts

| Transition demandée | Résultat |
|---|---|
| **(a)** Palette au clavier : Tab reste dedans, Échap ferme et rend le focus, « Conversations » d'abord | **couverte.** Tab : sortie mesurée au **3e** arrêt (et non au 4e), liste ordonnée des six arrêts dans nadia-03. Échap : ferme bien. « Conversations » : karim-01 se reproduit, et j'en donne la cause (nadia-01, deux palettes distinctes). |
| **(b)** Aide des raccourcis, chaque raccourci essayé réellement | **couverte à 17 sur 20.** Non essayés : ↵ et ⇧+↵ du composeur, et ⌘+⇧+D (mode démonstration, écarté pour ne pas modifier l'état de données de la pile partagée). Résultats : 15 conformes, ⌘+⇧+K non tenu (nadia-06), ⌘+⇧+F partiel. |
| **(c)** Board souverain : cinq avis, panneau de résultat, annulation | **couverte, et c'est le gros trou de la soirée.** Zéro avis affiché sur cinq (nadia-04), aucun panneau de résultat, **aucune annulation proposée** pendant la délibération : le seul geste disponible est de fermer, ce qui perd tout (nadia-05). |
| **(d)** Panneau Actions : lancer, annuler, « Arrêt en cours » → état final | **couverte - conforme.** L'état final arrive (« Annulé » à +97 s), la séquence « Arrêt demandé… » → « Arrêt en cours » → « Annulé » est lisible. Réserve : 100 % affiché sur un travail annulé (nadia-08). |
| **(e)** Thème sombre à 1024×768 | **couverte.** Aucun débordement horizontal, rien sous 12 px, un seul texte tronqué (le lien d'évitement, masqué par conception), palette conforme à la charte. Défauts trouvés ailleurs : recouvrement sans voile ni isolation (nadia-09), pied du brief sous le composeur à 900×700 (nadia-12). |

**Angles morts assumés :**

- **Bandeau d'erreur sur une route inexistante** : je n'ai trouvé **aucun geste métier** qui
  provoque un 404 dans l'application. Mon appel synthétique (import du client `api` depuis
  la page, `GET /api/route-qui-nexiste-pas`) a bien produit un 404 et une `ApiError` en
  console, mais aucun composant n'écoutait cet appel : l'absence de bandeau ne prouve rien.
  Non classé.
- **Fréquence de sondage de `/api/processing-tasks`** : le relevé réseau en montre des
  centaines, souvent par paires. Je n'ai pas mesuré sur une fenêtre bornée, donc pas de
  constat.
- **Mode démonstration (⌘+⇧+D)** : volontairement non essayé.
- **Décision enregistrée existante** : impossible à lire, il n'y en avait aucune (`[]`).
- **Contraste mesuré au ratio** : je me suis limitée à l'inspection visuelle et aux tailles
  de police ; aucun calcul de rapport de contraste (l'outil dédié, B-420, est un outil humain).
- **Chaque avis du Board photographié** : impossible, aucun n'a jamais été affiché.
- **Réserve d'ordonnancement** : les deux délibérations que j'ai lancées occupaient Ollama
  pendant l'annulation de « Relance clients ». Les 97 s d'arrêt sont donc **majorées par mon
  propre parcours** et ne doivent pas être lues comme une mesure de performance.
- **Application non figée** : commit d'interface `ff170d73` deux minutes avant mon départ ;
  ce que j'ai vu de la palette, de l'accessibilité et de l'onboarding porte sur ce code-là.

## Tokens consommés

Environ **270 000 jetons** (différence entre le budget de session annoncé au départ et le
solde restant à la remise de la trace : 15 000 000 → 14 732 000).
