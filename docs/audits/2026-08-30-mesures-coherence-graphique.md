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
