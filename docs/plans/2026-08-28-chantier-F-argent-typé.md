# Chantier F — L'argent comme type, pas comme nombre

> Ouvert le 28/08/2026, à l'issue de la release 0.54.0-alpha.
> Point de départ : une recherche que j'aurais dû faire avant d'écrire le lot B3.

## Le constat

`invoice_totals` a été repris huit fois avant publication. Six des défauts
trouvés sont des « jumeaux » : une règle posée sur un champ et non balayée sur
les autres. Trois sont nés directement de mes propres correctifs.

La cause n'est pas la difficulté du calcul. C'est que **l'argent est représenté
par un `float` et une chaîne de caractères posée à côté**, et que rien dans le
type n'interdit les gestes faux.

État actuel, vérifié :

```
src/backend/app/models/entities.py
  subtotal_ht: float = 0.0
  total_ttc: float = 0.0
  unit_price_ht: float
  total_ht: float
  currency: str          # NOT NULL sur base neuve, nullable sur base migrée
```

Aucune bibliothèque monétaire installée. Chaque `round(x, 2)` est posé à la main.

## Ce que le domaine fait à la place

| Problème rencontré | Ce que le domaine emploie |
|---|---|
| `0.10 + 0.20` sort `0.30000000000000004` | `Decimal`, ou un **entier en plus petite unité** (1940 centimes, pas 19,40 €) |
| 1 000 EUR + 1 000 USD sort `2000` | un type `Money` qui **lève** au lieu d'additionner |
| Une devise choisie au hasard pour étiqueter le total | conversion explicite ou refus, jamais une priorité implicite |
| La somme du détail ne colle pas au total | `allocate()` du motif Money de Fowler, qui distribue le reliquat |
| Deux champs du même résultat arrondis différemment | une seule valeur typée, arrondie une seule fois à la frontière |

Le point décisif n'est pas la précision, c'est **l'impossibilité**. Un type qui
refuse `Money(100, EUR) + Money(100, USD)` transforme le défaut de la passe 1 en
exception au premier test, au lieu d'un mensonge à découvrir en production.

Sources : [py-moneyed](https://py-moneyed.readthedocs.io/en/latest/usage.html),
[money (carlospalol)](https://github.com/carlospalol/money),
[motif Money de Fowler](https://gist.github.com/cryptocompress/7097498),
[travailler en centimes](https://dev.to/aloukissas/you-better-work-in-cents-not-dollars-ngo).

## Périmètre réel de la migration

Ce n'est pas un correctif local. Les montants traversent :

1. le modèle SQLModel (`entities.py`) et la base des testeurs, déjà peuplée ;
2. les schémas Pydantic d'entrée et de sortie ;
3. la génération de PDF ;
4. `invoice_totals`, `search_invoices`, le tableau de bord, le brief ;
5. le type `Invoice` du frontend et tous les affichages ;
6. les tests, qui écrivent des `float` littéraux partout.

**Une migration de base est nécessaire** si l'on passe aux entiers de centimes.
Elle doit être réversible et testée sur une copie d'une vraie base de testeur,
pas seulement sur une base neuve — l'erreur de la passe 2 était exactement de
conclure depuis une base neuve.

## Comment le traiter

La campagne recommandait de traiter F « en posant, à chaque correctif, un test
de cohérence entre couches plutôt qu'un correctif local ». Appliqué ici :

1. **D'abord un test de cohérence, sans rien migrer.** Un test qui prend une
   facture réelle et vérifie que le montant lu est identique à travers les six
   couches. S'il est vert, la dette est théorique ; s'il est rouge, il nomme
   précisément où ça diverge.
2. **Puis le type, en interne seulement.** Introduire `Money` dans le service de
   calcul, en convertissant aux frontières. `invoice_totals` devient le premier
   consommateur. Aucune migration de base à ce stade — le bénéfice principal
   (l'impossibilité d'additionner deux devises) est déjà acquis.
3. **Enfin, et seulement si l'étape 2 le justifie**, la représentation en base.

Faire l'étape 2 avant l'étape 3 permet d'arrêter après 2 si le rapport n'y est
pas.

## Ce que ce chantier ne fait pas

- Il ne touche pas au cap produit : c'est D.
- Il ne ferme pas la dette « une capacité redéclarée à sept endroits et honorée
  à trois ». L'argent en est le cas le plus coûteux, pas le seul.
