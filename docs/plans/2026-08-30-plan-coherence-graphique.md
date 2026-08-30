# Cohérence graphique et direction artistique - plan

> 30 août 2026. Deux audits indépendants (Soso sur le code, Grok sur le code
> **et** l'application qui tourne), plus des mesures de comptage. L'hypothèse
> de Ludo — « des vestiges de l'ancienne interface » — n'a été soufflée à
> aucun des deux.

## Ce sur quoi les deux tombent d'accord

**Le premier chantier n'est pas de remplacer les 400 classes de couleur
brutes.** C'est de réparer un trou de contraste qui est sur chaque écran. Une
migration mécanique propagerait les mauvaises couleurs en croyant ranger.

Ils convergent aussi, sans se parler, sur le diagnostic de Ludo : **plusieurs
langages graphiques coexistent** et cette coexistence « paraît inachevée ».

## Le trou, mesuré

Les jetons sémantiques (`success`, `warning`, `error`, `info`) tiennent : ils
sont protégés par un test. **Les accents, non — et le test ne les regarde pas.**

| Paire, thème clair (le défaut) | Ratio | Où |
|---|---|---|
| Atelier : `color: "#E6EDF7"` forcé sur fond blanc | **1,18:1** | `AgentChat.tsx` (×2), `AgentSession.tsx` |
| Cyan de marque `#22D3EE` comme texte | **1,67:1** | **242 usages** de `text-accent-cyan` |
| Anneau de focus (même cyan) | **1,67:1** | tous les écrans, seuil UI 3:1 manqué |
| `::selection` | **1,67:1** | sélection de texte quasi invisible |
| `--color-accent` `#0F8FB3` sur sa teinte | **3,29:1** | bouton « Contrôle des données », partout |
| Pipeline CRM, 6 colonnes sur 7 | jaune **1,91:1** | 7 couleurs brutes en dur |
| Magenta de marque `#E11D8D` | 4,07 clair / **4,22 sombre** | échoue dans les deux thèmes |
| Badge « Bientôt » (9 px, cyan 60 %) | **1,35:1** | |

**La valeur qui répare existe déjà dans le fichier** : `--agent-cyan: #0E7490`
passe à 4,95:1 sur le fond et 4,70:1 sur la teinte.

Note de cadrage : `#2451FF` passerait AA en texte sur le thème clair
(5,25:1). Ce n'est plus un argument d'identité (voir l'arbitrage ci-dessous),
mais ça reste une valeur disponible si on cherche une couleur d'action lisible.

## Ce que le test d'accessibilité ne voit pas

`src/frontend/src/test/a11y.test.tsx` passe au vert. Il ne teste que
`success / warning / error / info` sur fond simple : **aucune occurrence de
`accent`, `cyan`, `magenta` ou du ring**, et son analyseur n'extrait pas les
teintes sombres en `rgba()`. Il donne une assurance en ne regardant pas là où
ça casse.

## Arbitrage de Ludo, 30/08 : THÉRÈSE ne porte PAS la charte Synoptïa

**Décision produit, actée.** THÉRÈSE est un produit avec son identité propre.
La charte Synoptïa (navy `#0B1226`, primaire `#2451FF`, cyan, magenta) sert la
marque de l'entreprise et ses documents, pas cette application.

Ce que ça retire du plan :

- L'absence de `#2451FF` **n'est pas un défaut**. Le compter comme tel était
  une erreur de cadrage de ma part.
- Le navy absent du thème clair, le magenta par éclats : **pas des défauts**.
- La question « est-ce reconnaissable comme du Synoptïa sans logo ? » **ne se
  pose pas**.

Ce que ça ne retire pas, et c'est l'essentiel :

- **Les contrastes qui échouent restent des bugs.** 1,18:1 est illisible quelle
  que soit la marque.
- **Deux langages d'action concurrents restent une incohérence interne**, même
  sans référence externe.
- Un test qui donne une assurance fausse reste un test qui ment.

La question du lot 2 se reformule : non plus « quelle couleur de marque »,
mais **« quelle langue, la sienne, THÉRÈSE parle-t-elle »**.

## Quatre documents décrivent quatre produits

1. `RULES-DESIGN.md` : « Dark Glassmorphism », boutons primaires `#2451FF`.
2. `globals.css` : thème **clair** par défaut, sombre en second.
3. `Button.tsx` : `.btn-brutal`, ombre dure, bordure 2 px, fill cyan. Utilisé
   par Paramètres et Projets, **pas** par la coque.
4. `index.html` (l'écran de démarrage) : `#0f0f13`, `#00d4ff`, `#ff00aa` —
   une **quatrième** palette, dans la toute première image du produit.

Conséquence visible : deux boutons d'action primaire d'un écran à l'autre.
L'accueil met une pilule encre, les Paramètres un bouton brutaliste cyan.

## Ce que la DA de mai a réellement laissé dans le code (constat du 30/08)

La refonte DA commandée en mai 2026 (`~/Desktop/Dev Synoptia/therese-da-refonte/`)
propose trois directions. **« Équilibre » (clair) et « Signature » (sombre)** ont
été retenues. Vérification faite sur `globals.css` :

| Jeton de la DA | Valeur | Présent dans `globals.css` ? |
|---|---|---|
| `--bg` clair | `#F3F6FC` | oui, `--color-bg` |
| `--border` | `#E2E8F3` | oui, `--color-border` |
| `--ink` | `#101C36` | oui, `--color-text` |
| `--accent` | `#0F8FB3` | oui, `--color-accent` |
| `--accent-fill` | `#22D3EE` | oui, `--color-accent-fill` |
| `--accent-tint` | `#DEF4F9` | oui, `--color-accent-tint` |
| `--radius` | `14px` | **non** |

**La palette a atterri. Les composants ne la consomment pas.** Mesuré :

- `accent-fill` (l'accent d'action) : **5 fichiers** le consomment.
- `bg-text` (la pilule encre `#101C36`) : **68 occurrences**.
- Rayons écrits à la main : **451** (`9px` ×127, `10px` ×94, `8px` ×91,
  `6px` ×83, `13px` ×40, `7px` ×16), contre des jetons existants à
  6/8/12/16 px. La plupart sont **à un pixel du jeton**.

Autre constat, non vu par les deux auditeurs : `globals.css:67` déclare
`--font-family-sans: 'Inter', system-ui…` mais **aucune police n'est chargée**.
Zéro `@font-face`, zéro fichier `.woff2`, zéro lien Google Fonts, zéro paquet
`@fontsource`. THÉRÈSE emprunte donc la police du système : SF Pro sur macOS,
Segoe UI sur Windows. C'est la police de Claude Desktop et de ChatGPT.

## L'exigence de Ludo, 30/08

> « Thème clair par défaut. On veut une signature graphique et un peu de
> couleur. Aujourd'hui quand on lance Claude ou ChatGPT on ne voit pas trop la
> différence, confusion possible. On ne doit pas confondre THÉRÈSE. »

Cette signature n'est pas à inventer. Elle est déjà validée et déjà à moitié
posée. Ce qui manque tient en trois gestes : **l'accent cyan sur les actions**,
**un rayon unique**, **une police à soi**.

Planche de référence rendue le 30/08 :
`docs/audits/2026-08-30-planche-da.png` (source `planche-da.html`).

## Les lots

### Lot 0 - Une police à soi (le geste le plus visible, le moins risqué)

Embarquer **Plus Jakarta Sans** (titres) et **Inter** (texte) en local, via
`@fontsource`, sans appel réseau : THÉRÈSE est une application de bureau qui
doit fonctionner hors ligne. Corriger aussi l'écran de démarrage
(`index.html:50` et `:75`), qui déclare `-apple-system` en dur et donne donc la
toute première image du produit en police système.

Garantie mécanique : un test qui échoue si `font-family` résout vers
`system-ui` sur le `body`.

### Lot 1 - Le trou de contraste

Inchangé, périmètre serré. Reste le premier correctif fonctionnel : un texte
illisible est un bug, indépendamment de toute question de marque.

### Lot 2 - L'accent d'action (remplace « choisir une langue d'action »)

L'arbitrage n'est plus à rendre : la DA le tranche et les jetons existent.

- Le bouton d'action primaire porte `--color-accent-fill` (`#22D3EE`) avec
  `--color-accent-ink` (`#06121F`), pas `bg-text`.
- `Button.tsx` perd `.btn-brutal` : la quatrième direction disparaît.
- L'anneau de focus est `--color-accent-fill` partout, visible au clavier.
- Les 68 `bg-text` sont triés : ceux qui sont des **actions** basculent, ceux
  qui sont des **surfaces** restent.

Le tri est le vrai travail, pas la bascule. Une substitution en masse
transformerait des fonds en boutons.

### Lot 3 - Un rayon unique

Trois valeurs, pas six : **8 px** (champs, puces), **14 px** (boutons, cartes),
**plein** (étiquettes). Les 451 valeurs manuelles convergent vers ces trois.

Point à trancher : la DA donne 14 px en clair et 12 px en sombre. Garder 14 des
deux côtés est plus simple à tenir. **Décision attendue de Ludo.**

### Lot 4 - Le plancher typographique

Inchangé : 14 px devient le plancher du texte utile, 12 px reste réservé aux
métadonnées. C'est le lot le plus long et le plus intrusif ; il vient après.

### Lot 5 - Les couleurs brutes de domaine

Les quatre couleurs `k1`–`k4` de la DA (agenda, tâches, factures, prospects)
deviennent des jetons et remplacent les couleurs Tailwind brutes, dont les
102 `text-red-400` qui ignorent le thème.

Correction due : le violet `#7C3AED` signalé comme intrus par l'audit est la
**couleur de domaine prévue** pour les prospects. Il reste.

La DA ne définit pas de rôle « danger ». Proposition à valider : `#B42318` sur
`#FBE6E4` en clair, `#F87171` sur `rgba(248,113,113,.13)` en sombre.

## Ce qui sort du plan

- Toute question « est-ce du Synoptïa ? » : arbitrée le 30/08, THÉRÈSE porte
  son identité propre.
- Le glassmorphism de `RULES-DESIGN.md` : document mort, à archiver.
- Une refonte d'écrans. Aucun lot ne déplace un composant ; ils changent ce
  que les composants consomment.

## Vérification

Chaque lot suit le rituel complet : test rouge d'abord, sabotage vérifié
(la commande de sabotage doit être **constatée appliquée**), les six portes,
puis revue Grok et Soso sur le diff. Recette visuelle dans l'application
packagée avant de clore un lot qui touche un écran.
