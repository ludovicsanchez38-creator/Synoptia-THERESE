# Décisions et arbitrages 0.40

## Décisions déjà posées

| Sujet | Décision | Motif |
|---|---|---|
| Migration | progressive et réversible | préserver les usages et isoler les régressions |
| Interface par défaut aujourd’hui | classique | le prototype utilise encore des données simulées |
| Source métier | backend et stores existants | éviter deux vérités concurrentes |
| Navigation | une coque, des canevas contextuels | réduire le morcellement sans perdre la profondeur |
| Actions sensibles | aperçu puis confirmation | garder la maîtrise des effets externes |
| Board | canevas de décision | rendre les divergences et la synthèse lisibles |
| Atelier | canevas de mission | rendre plan, exécution et revue contrôlables |
| Données | aucune migration de schéma pour la coque | réduire le risque initial |
| Version | pas de bump pendant la préparation | ne pas confondre chantier et release |
| Diffusion | local uniquement | la bêta commencera après signature et GO explicite |

## Arbitrages à prendre avant la release

| Question | Options | Moment limite |
|---|---|---|
| Mode par défaut de la 0.40 | nouvelle interface avec repli, ou bêta opt-in | avant la RC 0.39 |
| Nom visible du centre | Capacités, Outils, ou « Ce que Thérèse sait faire » | avant tests utilisateurs |
| Usage des portraits | tous les conseillers, Board seulement, ou Board et Atelier | avant stabilisation visuelle |
| Historique des canevas | dans la conversation, dans chaque module, ou les deux avec liens | avant branchement des données |
| Télémétrie | aucune, journaux locaux, ou métriques opt-in | avant bêta élargie |

## Registre des décisions à ajouter

Toute décision qui modifie les données, les permissions, le comportement par
défaut ou le protocole de retour arrière doit être ajoutée ici avec sa date, son
auteur et la preuve de validation.
