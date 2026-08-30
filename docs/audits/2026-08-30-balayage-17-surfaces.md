# Balayage des 17 surfaces, deux thèmes — 30/08/2026

Mesure faite dans l'application **lancée** (dev, port 1420), pas sur le code.
Outil : `scripts/audit-visuel.js`. Navigation par `window.__therese.runAction()`.

Méthode : pour chaque nœud de texte visible, la couleur du texte et la pile de
fonds au-dessus sont composées par le **navigateur** (canvas 1×1), puis le
rapport de contraste est calculé sur le RGB obtenu. Les tailles, rayons,
familles de police et cibles de clic sont relevés au passage.

## Résultat

**34 mesures (17 surfaces × 2 thèmes) : 0 texte sous le seuil, 0 élément
cliquable sous 14 px.**

| Surface | clair | sombre | rayons observés | tailles observées |
|---|---|---|---|---|
| Accueil | 0 | 0 | 14 / 8 / plein | 14, 12, 16, 24 |
| Pipeline (CRM) | 0 | 0 | 14 / 14-14-0-0 / 0-0-14-14 / 8 / plein | 14, 16, 12, 18 |
| E-mail | 0 | 0 | 14 / 8 / plein | 14, 12, 18, 20 |
| Agenda | 0 | 0 | 14 / 8 / plein | 14, 12, 18 |
| Tâches | 0 | 0 | 8 / 14 / plein | 14, 12, 18 |
| Devis et factures | 0 | 0 | 14 / 8 / plein | 14, 12, 16, 18 |
| Projets | 0 | 0 | 14 / 8 / plein | 14, 12, 18 |
| Fichiers | 0 | 0 | 14 / 8 / plein | 14, 12 |
| Documents | 0 | 0 | 14 / 8 / plein | 14, 12, 18 |
| Contacts | 0 | 0 | 8 / 14 / plein | 14, 12, 18 |
| Décision (Board) | 0 | 0 | 14 / 8-0-0 / 8 / plein | 14, 12, 16, 18, 24 |
| Actions | 0 | 0 | 14 / 8 / plein | 12, 14, 16, 20, 24 |
| Paramètres | 0 | 0 | 14 / 8 / plein | 14, 12, 16, 18, 24 |
| Raccourcis clavier | 0 | 0 | 8 / 14 / plein | 12, 14, 16, 18, 24 |
| Bibliothèque de prompts | 0 | 0 | 8 / 14 / plein | 12, 14, 16, 18, 24 |
| Produire un document | 0 | 0 | 14 / 8 / plein | 12, 14, 20 |
| Conversations | 0 | 0 | 14 / 8 / plein | 14, 12, 16, 24 |

Les rayons composés (`14px 14px 0px 0px`) sont des coins hauts de colonne de
kanban, pas des valeurs supplémentaires.

Polices relevées : **Inter**, **Plus Jakarta Sans**, **ui-monospace** (avant
l'embarquement de JetBrains Mono, corrigé le jour même).

## Ce que ce balayage a trouvé, que les tests statiques ne voyaient pas

1. **Les cinq conseillers du Board** portaient leur couleur en style inline
   depuis un objet JS : `#22D3EE` à **1,81:1** sur fond blanc, `#F59E0B` à
   2,15:1, `#EF4444` à 3,76:1. Visibles sur quatre écrans.
2. **`bg-accent-cyan/20` sous une encre d'accent** : 4,36:1 sur `surface-2`,
   4,68:1 sur blanc. La même classe passe ou échoue selon la couche du
   dessous. 44 occurrences.
3. **Toutes les teintes du thème sombre étaient translucides** (accent,
   sémantiques, domaines) : même défaut, contraste imprévisible. Deux encres
   sous AA sur leur propre teinte une fois opacifiées (`#EF4444` à 4,02,
   `#F0509F` à 4,43).
4. **La police monospace** était déclarée et jamais chargée, exactement comme
   Inter avant le lot 0. 44 nœuds en `ui-monospace` du système.
5. **Le fil d'Ariane des Fichiers** restait cliquable à 12 px.

## Deux pièges de mesure, tombés dedans avant de les écrire

- **`oklab()`** : un parseur naïf lit `oklab(0.999994 …)` comme du RVB et
  annonce du noir. Cinquante faux positifs sur le panneau des raccourcis avant
  de passer par le canvas.
- **Onglet en arrière-plan** : le navigateur gèle les transitions d'un
  document `hidden`. Le fond du `body` reste indéfiniment celui du thème de
  départ pendant que `--color-bg` est déjà celui d'arrivée. Onze faux défauts,
  et j'ai failli conclure que le `body` ne suivait pas le thème. Couper les
  transitions avant de basculer.

## Ce qui reste, non corrigé et assumé

- **Cibles de clic sous 24 px** : 4 à 9 par écran. Les entrées du rail font
  44×20 (hauteur 20). Sous le confort tactile, au-dessus de rien : c'est une
  application de bureau, pilotée à la souris. À trancher.
- **La densité en 12 px** reste forte sur trois surfaces : Raccourcis (84
  nœuds à 12 px contre 31 à 14), Bibliothèque de prompts (52 contre 18),
  Actions (25 contre 11). Le plancher est respecté, la proportion non.
