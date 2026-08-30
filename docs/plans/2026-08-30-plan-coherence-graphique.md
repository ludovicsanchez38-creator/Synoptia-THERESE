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

## Les lots

### Lot 1 - Le trou de contraste (le seul à faire en premier)

Périmètre serré, dans cet ordre :

1. Assombrir `--color-accent` en clair, au moins au niveau de `--agent-cyan`
   (`#0E7490`), qui est déjà dans le fichier.
2. `text-accent-cyan` devient **décoratif et sombre uniquement**. En clair, le
   texte et les liens passent par `text-accent`.
3. Anneau de focus et `::selection` : une couleur qui contraste en clair.
4. **Retirer les `color: "#E6EDF7"` de l'Atelier.** Le thème clair n'est pas
   optionnel, et 1,18:1 est le pire chiffre du dossier.
5. **Étendre le test d'accessibilité** aux paires accent / teinte / ring, dans
   **les deux** thèmes. Sans ça, le chantier reviendra.

Vérification : « Contrôle des données » et le badge « Recommandé » à 4,5:1 en
clair, l'anneau de focus à 3:1, mesurés dans les deux thèmes.

### Lot 2 - Une seule langue d'action

Choisir entre la pilule encre de la coque et le bouton brutaliste de
`Button.tsx`, puis l'appliquer aux deux. C'est le lot où **l'écran change**.

Il dépend d'un arbitrage produit qui n'est pas technique (voir plus bas).

### Lot 3 - Le plancher typographique

Écran par écran, pas au script : un `sed` de `text-xs` vers `text-sm`
casserait la densité des listes.

- Corps et boutons d'action : **14 px plancher**.
- Titres de carte et de panneau : **16 px**.
- `text-xs` : légendes, badges, puces de source seulement.
- Interdire `text-[9px]`, `[10px]`, `[11px]` hors un cas nommé.

Note : les tailles arbitraires en pixels **neutralisent le réglage de police**
de l'application, qui agit sur la racine en `rem`.

### Lot 4 - Les couleurs brutes, là où elles s'affichent

Pas les 400. Celles qui se voient en thème clair : l'assistant e-mail, le CRM,
les tâches, l'Atelier. `guided/` (34 occurrences) **n'est plus monté** : le
compter gonfle le problème.

### Correctifs courts, à caler entre les lots

- **Cinq fichiers contiennent des emoji** alors que la charte l'interdit :
  `EmailPriorityBadge.tsx` (🔴🟠🟢), `AgentSession.tsx` (🤖 👤),
  `RFCCapture.tsx` (📧), `MemoryPanel.tsx` (⚠).
- **Inter est déclaré et jamais chargé** : aucune `@font-face`, aucun lien.
  La police réelle est celle du système. Décider : la charger, ou cesser de
  l'annoncer.
- L'écran de démarrage et sa palette à lui.

## Ce qui sort

- **La migration des 180 champs vers `Input`.** Zéro pixel pour l'utilisateur,
  et la primitive porte elle-même un focus trop faible : la migrer maintenant
  propagerait le défaut.
- **Les 492 rayons arbitraires.** Une différence entre 8, 9 et 10 px ne se voit
  pas. Ce qui se voit, c'est la coexistence pilule / carte douce / bouton carré.
- **Les 183 formulations d'état vide** comme telles. Le vrai défaut est
  ailleurs : le même gabarit répété jusqu'à **trois fois sur un écran**, et
  l'absence de distinction entre « vide », « pas chargé », « filtre sans
  résultat » et « indisponible ».
- Les 577 « chargement » : `Spinner` a déjà absorbé le sujet.
- L'échelle d'espacement : elle est tenue, zéro arbitraire. Ce n'est pas le
  chantier.

## L'arbitrage qui reste, et qui bloque le lot 2

**Quelle langue THÉRÈSE parle-t-elle, la sienne ?**

Deux boutons d'action primaire coexistent d'un écran à l'autre : la pilule
encre de la coque et le bouton brutaliste de `Button.tsx`. Il faut en choisir
un et l'appliquer partout. C'est un choix de goût, pas de technique, et il
appartient à Ludo.

Le thème par défaut (clair) et le thème sombre restent tous deux à supporter :
ce n'est plus une question d'identité de marque, mais l'Atelier prouve que le
clair est aujourd'hui traité comme optionnel, et il ne l'est pas.

Le lot 1 n'attend pas cette décision.
