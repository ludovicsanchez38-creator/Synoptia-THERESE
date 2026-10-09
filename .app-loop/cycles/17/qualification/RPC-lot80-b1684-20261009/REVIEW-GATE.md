# Revue indépendante B-1684

Acteur : `/root/cycle17_gate_review`. Revue filesystem et source uniquement, close le 2026-10-09T06:51:57Z. Le reçu détaillé et les douze références physiques sont dans [REVIEW.json](REVIEW.json).

Avis favorable au correctif local, aucun bloqueur source relevé. B-1684 reste différé en attente de qualification. CALIBRATE, FULL et release ne sont pas admis.

## Changement réellement vérifié

La seule modification exécutable ajoute `return False` au handler `Exception` de `_is_purge_enabled`. Une lecture en échec ne peut donc plus autoriser la campagne. Le défaut activé quand le réglage est réellement absent ou vide reste inchangé.

La reconstruction en octets depuis la préimage conservée est exacte. L'AST entier du module est inchangé hors docstring et ajout de ce retour. Le mutant privé est exactement le corrigé avec ce seul retour remis à `True`. Le produit n'a pas été saboté par cette copie privée.

Le garde initial de `auto_purge_expired_contacts` arrête alors la campagne avant la rétention et les opérations ultérieures. Ce corps n'est pas modifié par le correctif.

## Preuves lues, non rejouées

Les outputs complets du reçu MAIN concordent avec les quatre résultats locaux :

| Invocation MAIN | Code | Méthodes | Échecs | Erreurs |
| --- | ---: | ---: | ---: | ---: |
| Rouge initial `91463a` | 1 | 14 | 11 | 0 |
| Corrigé `cfcbb8` | 0 | 14 | 0 | 0 |
| Mutant privé `250dec` | 1 | 14 | 11 | 0 |
| Dernier vert `a49ae8` | 0 | 14 | 0 | 0 |

Les onze échecs rouges comprennent cinq sous-tests de campagne, cinq assertions individuelles et une valeur illisible. Les deux verts rejouent les mêmes quatorze méthodes.

Les tests utilisent les deux vrais corps AST entiers, avec préférence et session en mémoire. Ils couvrent les erreurs de construction, entrée, requête, résultat et sortie, y compris une sortie échouée après lecture de `true`. Le témoin positif atteint réellement la sentinelle de suite ; le réglage désactivé et les pannes l'évitent. L'annulation n'est pas convertie en activation.

## Limites et conservation

Les douze fichiers choisis sont réguliers, canoniques, UID 501 et nlink 1. SHA, taille et métadonnées contrôlées sont identiques avant et après cette revue. Les copies canoniques de préimage et mutant sont identiques aux copies privées. Produit courant : `c5fdf5c4ee1fbbf6eb854e7a7e631818cd94a97160127f80fe9a506e0dea2892`. Test : `c755e7e1abebce3b569ca69f80a5d297da21b56989488965a830cf221f50c70b`. Reçu MAIN : `a92b6282215b673e9b144d8bd5a0637416762745daa6f8f930acf605ea910f0d`.

Le chemin du rouge était ensuite corrigé : la préimage demeure une observation historique distincte du produit actuel. Ruff et diffcheck sont rapportés verts par MAIN, pas rejoués ici.

Cette preuve ne porte pas sur une DB, Qdrant, une purge réelle, l'UI, la calibration complète ou la conformité réglementaire. Aucun test ni produit importé, aucun runtime QA, Chrome, G1 ou réseau lancé par le relecteur. Aucune mutation du dépôt, de l'état, du budget ou des rouges.
