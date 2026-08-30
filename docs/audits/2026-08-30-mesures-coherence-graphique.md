# Cohérence graphique de THÉRÈSE - les mesures

> 30 août 2026. Matériau brut pour l'audit. **Des chiffres, pas des avis.**
> Périmètre : `src/frontend/src`, 174 composants, 48 818 lignes de TSX.

## Ce qui existe déjà

Un système de jetons **réel** : 94 variables `--color-*` dans `globals.css`,
avec des jetons sémantiques (`success`, `warning`, `error`, `info`), des jetons
de surface (`surface`, `surface-2`, `surface-elevated`, `border`) et les
accents de la charte (`accent-cyan`, `accent-magenta`, `accent-violet`).

Leur adoption est massive : `text-text-muted` 1245 fois, `text-text` 845,
`border-border` 796, `bg-surface` 436.

Il existe aussi un historique de migration documenté dans le `CLAUDE.md` du
dépôt, avec des exceptions **assumées et écrites** (catégories neutres
e-mail/appel/rendez-vous, statuts `refused` et `converted` sans jeton
équivalent).

**Ce n'est donc pas un chantier vierge.** C'est un système à environ deux tiers
d'adoption, avec une dette partiellement documentée.

## Ce qui diverge

### Couleurs

| Mesure | Valeur |
|---|---|
| Classes Tailwind de couleur brute (`text-green-400`…) | **389** |
| Couleurs hexadécimales écrites en dur dans du TSX | **121** |
| Dominantes | `text-green-400` (42), `bg-purple-500` (35), `text-purple-400` (33), `bg-green-500` (25) |
| Concentration | `atelier` (9 fichiers), `email` (9 avec le wizard), `guided` (4), `crm` (4) |

**Le bleu primaire de la marque est presque absent.** Sur les quatre couleurs
de la charte Synoptïa :

| Couleur | Rôle | Occurrences |
|---|---|---|
| `#22D3EE` | cyan | 30 |
| `#E11D8D` | magenta | 10 |
| `#2451FF` | **primaire** | **4** |
| `#0B1226` | fond | **3** |

### Typographie

| Taille | Occurrences |
|---|---|
| `text-xs` | 969 |
| `text-sm` | 868 |
| `text-lg` | 70 |
| `text-base` | 29 |
| tailles arbitraires (`text-[10px]`, `[11px]`, `[9px]`) | **52** |

Deux tailles portent **96 %** du texte, et la plus petite domine. `text-xs`
est la taille des métadonnées ; elle est ici la taille du contenu.

### Composants partagés contre écriture à la main

| Primitive | Fichiers qui l'importent | Écrit à la main |
|---|---|---|
| `Button` | 58 | **463** `<button>` |
| `Input` | **1** | **180** `<input>`, 48 `<select>` |
| `Spinner` | 68 | 30 `animate-spin`, 27 `animate-pulse` |

La primitive de champ existe et n'est utilisée nulle part.

### Formes

| Mesure | Valeur |
|---|---|
| `rounded-lg` | 491 |
| `rounded-full` | 156 |
| rayons arbitraires (`[9px]`, `[10px]`, `[8px]`, `[6px]`…) | **388** |
| ombres arbitraires `shadow-[…]` | 61 |
| espacements arbitraires en px | **0** (l'échelle d'espacement, elle, est tenue) |

### Langue

**183 formulations distinctes** d'état vide (« Aucun… », « Pas de… »,
« Rien… »). 577 occurrences de « chargement » / « loading ».

## Ce que ces chiffres ne disent pas

- Le **contraste réel** en thème clair et sombre. Les 389 couleurs brutes ne
  sont pas toutes fautives : certaines sont des catégories neutres assumées.
- Ce que l'écran donne à **voir**. Aucune capture n'a été prise pour ce
  document.
- L'**accessibilité** : ordre de tabulation, focus visible, lecteur d'écran.
- La cohérence des **espacements verticaux** entre écrans, invisible au grep.


---

## Corrections apportées par l'audit (30/08, soir)

Mes comptages étaient légèrement faux. Les valeurs retenues :

| Mesure | Ce que j'avais écrit | Valeur corrigée |
|---|---|---|
| Couleurs Tailwind brutes | 389 | **400** |
| Rayons arbitraires | 388 | **492** |
| Hexadécimaux dans du TSX | 121 | **119**, dont 105 hors tests |
| `<select>` à la main | 48 | **47** |

Le diagnostic ne change pas, mais la leçon tient : **figer un script de mesure
avec ses exclusions avant d'en faire un indicateur.** Sans ça, deux passages
donnent deux chiffres et le suivi ne veut rien dire.

## Mes mesures de contraste étaient fausses, et je les retire

J'ai tenté un script maison. Il ne compose pas les fonds semi-transparents
(`rgba(…, 0.12)` lui donnait 1,0) et ne sait pas lire `oklab()` (il a rendu
267 967 178). J'ai aussi cru voir un bouton illisible en thème sombre : mesuré
correctement, il est à 15,79.

**Aucun chiffre de contraste de ce document ne vient de moi.** Ceux qui suivent
viennent de l'audit, calculés sur le code des deux thèmes.

## Les défauts de contraste mesurés

| Association | Clair | Sombre |
|---|---|---|
| Cyan `#22D3EE` sur fond principal | **1,67:1** | 10,29:1 |
| Bordure sur fond principal | **1,14:1** | **1,53:1** |
| Anneau de focus cyan | **1,67:1** | 10,29:1 |
| Magenta `#E11D8D` sur fond principal | **4,07:1** | **4,22:1** |
| `error` sur sa propre teinte | 5,89:1 | **4,02:1** |
| Badge « Bientôt » (9 px, cyan 60 %) | **1,35:1** | |
| Boutons cyan à texte blanc | **1,81:1** | |
| Pipeline CRM : 6 colonnes sur 7 | jaune **1,91:1**, vert 2,22, gris 2,60, orange 2,89 | |

Le cyan est utilisé **242 fois** comme couleur de texte (`text-accent-cyan`) :
montants, liens, dates, scores. Ce n'est pas une couleur décorative isolée.

## Le test d'accessibilité donne une assurance fausse

`src/frontend/src/test/a11y.test.tsx` passe au vert. Il ne teste que
`success / warning / error / info` sur fond simple : **aucune occurrence de
`accent`, `cyan` ou `magenta`**. Il ne regarde pas là où ça casse, et son
analyseur n'extrait même pas les teintes sombres en `rgba()`.

## Infractions directes à la charte

Cinq fichiers contiennent des emoji dans l'interface, alors que la règle est
« jamais d'emoji, des SVG à la place » : `EmailPriorityBadge.tsx` (🔴🟠🟢),
`AgentSession.tsx` (🤖 👤), `RFCCapture.tsx` (📧 en placeholder),
`MemoryPanel.tsx` (⚠).

En revanche la règle « aucun dégradé sur un bouton » **est respectée** : les
dégradés trouvés sont sur des titres, des barres de progression et des fonds.
