# Campagne 10 personas + touche-à-tout - THÉRÈSE 0.40

Date : 16 juillet 2026. Demandé par Ludo : nouvelle interface par défaut,
10 personas qui cliquent partout sur la vraie appli, ne laisser passer aucun bug.

## Méthode

- 10 profils solopreneurs (coach, artisan, formatrice, dev, graphiste, consultante
  RH, e-commerçant, praticienne bien-être, restaurateur, juriste), chacun sur un
  espace de données vierge dédié, nouvelle interface active par défaut.
- Crawler « touche-à-tout » : sur chaque écran, énumère et clique chaque élément
  interactif (rail, en-tête, parcours, 30 capacités et leurs canevas, réglages),
  collecte toute erreur JS / requête échouée / impasse. Effets externes annulés.
- Détecteur de boutons morts : clique chaque bouton et vérifie qu'il produit un
  changement (le complément que l'automatisation seule ratait).
- Passe finale sur la vraie base de Ludo (la plus riche).

## Résultat

| Persona | Clics testés | Erreurs JS | Impasses |
|---|---|---|---|
| Les 10 (vierges) | 31 chacun | 1 (artefact) | 2 (artefact) |
| Vraie base (finale) | 39 | 0 réelle après fix | 0 réelle après fix |

Boutons morts (en-tête + rail) : **0** après les correctifs.

### Le seul « bug » restant sur les personas est un artefact de test
« Voice recording error: Not supported » : le navigateur headless du crawler n'a
pas de micro. Dans la vraie appli (Tauri ou navigateur avec micro), la dictée
fonctionne. Ce n'est pas un défaut de l'appli.

## Vrais bugs trouvés et corrigés pendant la campagne

| Bug | Cause | Fix |
|---|---|---|
| Agenda 500 sur 2 calendriers Google | `#` non encodé dans l'ID (weeknum, jours fériés) → URL tronquée → 404 Google → 500 | Encodage + filet 404 (3e6461d) |
| Agenda 400 « account_id requis » à froid | Chargement via le compte email courant (vide) au lieu du compte du calendrier | account_id dérivé du calendrier (0f19027) |
| Erreur console file-drop en navigateur | Listeners Tauri montés hors Tauri | Garde isTauri (c3c3c53) |

## Findings d'ergonomie de Ludo (œil humain, complément indispensable)

Corrigés : bouton calendrier inerte → agenda, « Vue complète » → agenda coque,
doublon avatar/roue (avatar seul), bulle Aide clarifiée, languette retirée,
bouton Menu « trois traits » redondant retiré, double + du rail.

## Conclusion

Après correctifs, la campagne automatisée ne trouve plus aucun vrai bug (seul
l'artefact micro du test subsiste). Les défauts d'ergonomie relevés par Ludo
sont tous traités. La leçon tient : le crawler trouve les plantages (les deux
bugs agenda), l'œil de Ludo trouve les boutons qui ne servent à rien.
