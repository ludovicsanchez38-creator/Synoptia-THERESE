# Cycle 15 : décisions déléguées et cadrage

Le 1er octobre 2026, Ludo autorise Codex à décider P160, P161 et P162 selon la logique d’usage et la législation. Les trois propositions sont acceptées via le CLI canonique. Les textes officiels ci-dessous ont été relus le même jour. Les choix de produit sont distingués des obligations des textes.

## P160 : série commune pour les prochaines émissions

L’[article 242 nonies A, I-7°](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000050811276) demande une numérotation unique, chronologique et continue. Les séries distinctes nécessitent une justification liée aux conditions d’activité. Le [BOFiP, §§70 à 100](https://bofip.impots.gouv.fr/bofip/140-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-10-20131018) précise ces conditions et donne des exemples. Les passages lus n’établissent pas que la distinction facture/avoir constitue à elle seule cette justification.

Choix retenu : poursuivre la série existante `FACT-AAAA-NNN` pour les prochaines factures **et** les prochains avoirs. Le type du document reste porté par `document_type` et son titre. Le préfixe FACT est une convention du produit. Les prochaines émissions ne prolongent plus AV. DEV reste une série de devis.

### Transition et critères

- Aucun numéro, date ou contenu d’une pièce déjà émise ne change, y compris les anciens AV et les pièces émises puis annulées par une ancienne version.
- Un brouillon PROV reçoit son numéro à sa première émission. Sa suppression ne consomme aucun rang.
- Un brouillon hérité AV, d’une ancienne année ou d’une autre convention reçoit un numéro de la série courante à sa première émission.
- Un brouillon portant un FACT de l’année courante peut conserver ce numéro s’il suit la forme canonique (trois chiffres minimum, sans zéros surnuméraires), de rang positif et encore le dernier de sa série. Un import FACT-7 ne conserve pas le rang d’un FACT-007 déjà émis. Sinon il reçoit le prochain FACT.
- Le maximum FACT considère toutes les pièces qui occupent réellement un numéro, quel que soit leur type. Le maximum AV historique ne fait pas sauter des rangs dans FACT.
- Le suffixe se compare numériquement, y compris après 999. La contrainte d’unicité SQL, la réservation d’écriture avant lecture et les SAVEPOINT restent en place.
- Le numéro et la date imprimée doivent utiliser le même instant d’émission. Un test autour du changement d’année vérifie cette cohérence sur PUT et paiement initial.
- Des émissions simultanées de facture et d’avoir reçoivent deux FACT successifs ; relire ou payer une pièce émise conserve son numéro et ses premières dates.

Il n’y a pas de migration réécrivant les documents existants. La transition agit à la première émission d’un brouillon. Les preuves rouges, vertes, sabotages et recettes de ce lot sont conservées sous `.app-loop/cycles/15/reprise/p160-serie-commune/`.

## P161 : cadrer la rectification d’un avoir émis

Livrable accepté : le présent cadrage, avant le développement d’un parcours rectificatif. L’[article 289, I-4, I-5 et V](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000048827413) encadre conservation, intégrité et référence du document modificatif à l’original. Le [BOFiP, V §§210, 220, 240 et 260](https://bofip.impots.gouv.fr/bofip/142-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-20-20220119) décrit la facture de remplacement et la note d’avoir, avec leurs références. Les passages lus ne désignent pas un type logiciel universel de compensation d’un avoir.

### Contrat du futur parcours

1. Conserver l’avoir émis, son numéro, sa date et son contenu.
2. Produire une nouvelle pièce avec identité, numéro et date propres.
3. Relier la rectification à l’avoir corrigé **et** à la facture initiale. Ce double lien est un choix de traçabilité du produit.
4. Conserver motif, auteur, instant, références et variation HT/TVA/TTC. Présenter la chaîne complète à l’écran et dans les PDF.
5. Empêcher les liens circulaires, les références ambiguës et les doubles validations concurrentes. Une saisie abandonnée ou refusée n’a aucun effet financier.
6. Définir et éprouver les effets sur les montants, l’encours et les états avant de proposer une validation réelle.

| Situation | Critère à définir et vérifier |
| --- | --- |
| Description ou référence incorrecte | Correction documentée, sans changement automatique de montant. |
| Avoir insuffisant | Réduction complémentaire identifiée et justifiée. |
| Avoir excessif ou doublon | Pièce de compensation et effet explicites, original conservé. |
| TVA incorrecte | Base, taux, régime et variation documentés ; aucun recalcul aveugle au taux courant. |
| Plusieurs factures ou remise globale | Périmètre distinct du lien simple actuel, à spécifier séparément. |

Le modèle actuel utilise `converted_from_id` pour relier un avoir à une facture. Un lien dédié vers la pièce rectifiée sera nécessaire ; détourner ce champ rendrait la référence ambiguë. Une variation financière doit être visible avant confirmation et les traitements simultanés doivent rester atomiques.

Changer un statut en « Annulée » ne constitue pas, à lui seul, une pièce rectificative. Formulation produit retenue pour le futur parcours : « Pour annuler l’effet d’un avoir émis, établis un document rectificatif. L’avoir d’origine reste conservé. » Le formulaire actuel ne crée pas encore cette pièce. Ce cadrage n’annonce ni calcul fiscal universel ni validation comptable déjà obtenue.

## P162 : rendre le défilement des factures découvrable

À 800 px, la recette réelle a montré les colonnes Envoi, Paiement et Échéance lisibles après défilement de 392 px. Le montant et les actions restent collés au bord. Le besoin porte sur l’indication du contenu hors cadre.

Choix retenu : un indice textuel discret **avant** le tableau, qui indique gauche, droite ou les deux selon sa position. Il disparaît si tout tient, ainsi qu’en chargement, erreur ou état vide. La vraie région horizontale est nommée et focalisable, avec focus visible ; molette et flèches restent des gestes natifs. Aucun bouton supplémentaire ni décompte trompeur de colonnes.

Critères : mesure après chargement, changement de filtre et redimensionnement ; textes exacts selon début/milieu/bord ; aucune cellule couverte ; aucune régression du sticky ni déplacement forcé du focus. La recette Chromium portera sur 800/1440 px et clair/sombre, avec GET seuls et comparaison des fixtures avant/après.

## Exécution et preuves

Une proposition de code est traitée à la fois : P160, puis stabilisation et boucle de contrôle ; P162 vient ensuite. P161 est livré ici comme cadrage documentaire. Les décisions, preuves officielles et lectures contradictoires sont indexées dans `.app-loop/cycles/15/reprise/decision-deleguee/`. Le changelog et le suivi distingueront décision, cadrage, implémentation et validation réelle.
