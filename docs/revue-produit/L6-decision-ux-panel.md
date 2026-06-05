# L6 (Mémoire : vue vs tiroir) — Verdict du panel UX/UI

**Date** : 2026-06-05 · **Méthode** : panel de 6 experts UX/UI à angles distincts + 2 critiques adversariales + synthèse (workflow `ux-panel-memoire-L6`, 10 agents). **Statut** : recommandation, en attente d'arbitrage Ludo.

## Vote brut du panel
- **hybride_split : 4** (Archi info, Coût d'interaction, Fidélité vision, Patterns d'apps de référence)
- **vue_plein_ecran : 2** (Cohérence/Nielsen — confiance forte ; Responsive/a11y — confiance moyenne)
- tiroir_lateral pur : 0

## Le retournement (les critiques ont ouvert le code)
Les 6 experts ont raisonné sur le brief, pas sur le code. Les 2 critiques adversariales ont vérifié dans les fichiers et démonté l'hybride majoritaire sur des **faits** :

1. **L'hybride répare un faux bug.** Le « débordement du tiroir 420 px sous ~1550 px » sert de preuve à 3 experts que « la gestion étouffe, donc plein écran ». Or un panneau `position: fixed right-0` (MemoryPanel.tsx l.244) **ne peut pas** déborder hors viewport ; le brief le marquait déjà « non bisecté ». La vraie cause est très probablement un **enfant flex sans `min-w-0`**, corrigeable en une ligne, **sans rien décider d'architectural**.
2. **Le « contexte à côté du chat » du tiroir est déjà illusoire.** Le tiroir pose un backdrop `fixed inset-0 bg-black/40 backdrop-blur-sm` (l.233) qui **masque le chat**. On ne sacrifie donc aucun côte-à-côte existant en passant en vue (confirmé par observation navigateur : le dashboard était grisé en fond).
3. **Diag A (« Mémoire ≠ CRM ») est déjà résolu côté donnée.** CRM et Mémoire lisent le **même `useContactsStore`** (P4). Ce qui reste, ce sont des surfaces redondantes. Ajouter un peek = une **3e surface du même store** = l'inverse du « calme » visé.
4. **Pour un solo en alpha, l'hybride est l'option la plus chère** (2 UI + mécanisme de promotion + 2 piles d'Échap) pour un usage « glance » **supposé, non mesuré**. Linear/Notion (cités par les pro-hybride) sont des équipes de 50+, pas un mainteneur unique.

La 2e critique va plus loin : **« Mémoire » n'est pas un objet, c'est un agrégat de 3 choses de natures différentes** :
- **Contacts** = déjà le CRM (même store, filtré sur `source`) → à fusionner avec la vue CRM, pas une surface de plus.
- **Fichiers** = `FileBrowser`, un **indexeur de système de fichiers OS Tauri** (`readDir`/`homeDir`/`@tauri-apps/plugin-fs`), **aucun lien donnée avec les contacts** → sa place est une vue « Indexation/Fichiers » à part.
- **Le glance contextuel** (« qui est ce contact pendant que je discute ») = le **seul** morceau qui justifie le pattern « mémoire visible » du benchmark, et il ne pèse rien (lecture seule).

## Statut d'implémentation (2026-06-05)
**Reco appliquée : la Mémoire est désormais une vue content-swap.** Lots livrés sur `chantier-revue-produit` :
- `ee91e04` — `MemoryPanel` accepte `standalone` (vue pleine, sans backdrop ni tiroir fixe).
- `066a10e` — câblage en vue : routeur `ChatLayout` (`activeView === 'memory'`), ⌘M / SideToggle / header / ⌘K-Mémoire → `handleToggleMemory` (toggle) ; `onSearch` ne pointe plus vers le tiroir (fin du faux ami).
- `109b522` — dette soldée : retrait du code mort `showMemoryPanel`/`toggleMemoryPanel`/`closeMemoryPanel` de `panelStore`.

**Vérification (TDD + navigateur via DOM)** : 132 tests front, `tsc` 0, régression `TestL6_MemoryAsView`. Navigateur sur backend isolé, **fenêtre 1280 px** (la largeur où le tiroir clippait) : vue `relative h-full` pleine largeur, **débordement horizontal = 0** (panneau ET document) → le bug de la piste L6 disparaît mécaniquement comme prévu. Création de contact (callback `onNewContact` OK dans la vue), recherche par nom trouvée (P5 OK), requête sans match → « Aucun contact », bouton « ← Chat » démonte la vue. **Note honnête** : la cause-racine du débordement du *tiroir* n'a pas été bisectée (le tiroir est supprimé) ; ce qui est prouvé, c'est l'absence de débordement de la *vue* à la largeur problématique.

**Reste de la reco (à suivre)** : signal de glance inline dans le chat (« pastille » contexte, Lot 9), fusion onglet Contacts → vue CRM + sortie onglet Fichiers → vue Indexation (Lot 10, post-L6), virtualisation de la liste contacts (scalabilité).

## Recommandation finale (certitude : forte)
**Mémoire = vue plein écran content-swap**, comme les 5 autres surfaces. Pas de tiroir, pas d'hybride peek+vue. Le besoin de glance se sert par un **signal contextuel léger en lecture seule** injecté dans le fil de chat (« N contacts liés à cette conversation », chip cliquable → ouvre la vue Mémoire scope conversation), **pas** par un panneau concurrent. La présence (« Thérèse te connaît ») se prouve par ce que Thérèse **répond** (RAG/mémoire sémantique), pas par un panneau de gestion toujours ouvert.

**Pourquoi c'est aussi le moins cher** : `AppView` contient déjà `'memory'`, `navigationStore` expose déjà `goBack`/`history`, `CRMPanel` a déjà le prop `standalone` à copier. Il manque surtout le branchement dans le routeur de `ChatLayout`. Et ça supprime mécaniquement les 3 incohérences que la phase Tauri mono-fenêtre veut tuer (double point d'entrée, double pile d'Échap, focus-trap d'overlay).

## Dette révélée à solder dans le même lot (sinon L6 aggrave ce qu'il prétend régler)
- **Double toggle** `togglePanel('memory')` / `toggleMemoryPanel()` (panelStore l.111/167, même booléen) → un seul point d'entrée.
- **`CommandPalette.onSearch`** (ChatLayout l.142) ouvre aujourd'hui le tiroir Mémoire (faux ami) → recâbler vers la vue ou une vraie recherche (à trancher avec L8/⌘K).
- **Aucune virtualisation** de la liste contacts (`.map` brut + `searchResults` non capé) : c'est le **vrai mur de scalabilité**, indépendant du contenant.

## Plan d'implémentation proposé (lots TDD)
1. **Repro + bisection du bug d'overflow AVANT toute bascule** (Playwright 1280/1440/1550 px) — ne pas clore sur supposition.
2. Prop `standalone` sur `MemoryPanel` (calqué `CRMPanel`) : pas de backdrop, `flex-1 min-w-0` + `max-w-[1100px] mx-auto`.
3. Brancher `activeView === 'memory'` dans le routeur `ChatLayout` (lazy+Suspense + bouton Retour).
4. Recâbler `⌘M` → `setView('memory')` ; retirer le rendu tiroir de `PanelContainer`.
5. Solder la dette toggle + `CommandPalette.onSearch`.
6. Grille responsive (<800 / 800-1200 / >1200) + menu d'actions contact en popover collision-safe (plus de `absolute right-0`).
7. A11y + reduced-motion (`role=region`/`tablist`, badges RGPD `sr-only`, focus-trap local aux modaux internes).
8. Virtualisation `ContactsList` + cap `searchResults`.
9. Signal de glance inline dans le chat (lecture seule, route vers la vue).
10. (Post-L6, spec séparée) fusion onglet Contacts → vue CRM ; sortie onglet Fichiers → vue Indexation.

## Risques résiduels
- Cause réelle de l'overflow non confirmée : la vue masque le symptôme ; si la cause est un conteneur parent partagé, le bug ressurgira ailleurs (CRM/Email). Lot 1 obligatoire.
- Régression du glance si le signal inline (Lot 9) n'est pas livré dans le même chantier.
- Migration `usePanelStore` → `navigationStore` à faire dans **un seul commit** (sinon double instance temporaire).
- Désaccord produit possible : `benchmark-ux` liste « Split View Contacts | Chat » comme différenciateur ; la vue peut se lire comme un renoncement → à expliciter (le différenciateur vit dans les réponses, pas dans un panneau ouvert).
