# RFC P-039 - Diagrammes PERT, Gantt et prévision de planning

Statut : validé - lot A implémenté

Date : 4 septembre 2026

Source produit : suggestion Discord « Diagrammes & prédiction », triée en P-039

Portée validée : prototype local en lecture seule

## Décision proposée

Construire d'abord un moteur de planning déterministe, séparé du LLM, puis une
vue projet en lecture seule qui affiche :

- un Gantt calculé à partir des tâches, dépendances, durées et contraintes ;
- un réseau PERT avec chemin critique et marges ;
- les données manquantes et conflits qui empêchent un calcul fiable ;
- une estimation de date avec son niveau de confiance, sans inventer les
  valeurs absentes.

Le LLM et le pont MCP pourront lire et expliquer ce résultat. Ils ne pourront
pas modifier le planning dans la première version.

## Problème

THÉRÈSE connaît déjà les projets et leurs tâches. Une tâche porte aujourd'hui
un titre, un état, une priorité, une échéance éventuelle et un rattachement au
projet. Il manque les données nécessaires à un vrai planning : durée,
dépendances, contraintes de date, ressources, jalons et incertitude.

Dessiner des barres à partir des seules échéances donnerait une fausse
précision. Demander au LLM de calculer le chemin critique ou d'inventer les
dates rendrait le résultat non reproductible. Le calcul doit donc appartenir à
un service métier testable ; l'IA ne sert qu'à collecter les informations,
appeler ce service et expliquer ses sorties.

## Objectifs

1. Produire le même planning pour les mêmes entrées.
2. Expliquer chaque date calculée et chaque alerte.
3. Signaler explicitement les données absentes, cycles et surcharges.
4. Préserver les tâches actuelles et leurs API.
5. Fournir une représentation accessible en liste en plus des diagrammes.
6. Préparer un contrat MCP lisible sans autoriser de mutation implicite.

## Hors périmètre du premier lot

- nivellement automatique des ressources ;
- modification du planning par le LLM ;
- synchronisation bidirectionnelle avec Microsoft Project, Asana ou Jira ;
- facturation déclenchée automatiquement par un jalon ;
- promesse d'une date fiable lorsque les estimations sont incomplètes ;
- apprentissage statistique à partir de données insuffisantes.

## Modèle de données proposé

Les données de planification vivent dans des tables séparées, reliées aux
tâches existantes. Ce choix évite d'alourdir l'API de tâches pour les projets
qui n'utilisent pas le planning.

### `task_schedules`

Une ligne au plus par tâche :

| Champ | Type | Règle |
| --- | --- | --- |
| `task_id` | UUID | référence une tâche existante |
| `duration_optimistic_minutes` | entier nullable | strictement positif |
| `duration_likely_minutes` | entier nullable | supérieur ou égal à l'optimiste |
| `duration_pessimistic_minutes` | entier nullable | supérieur ou égal au probable |
| `constraint_type` | enum nullable | `start_no_earlier`, `finish_no_later`, `fixed_start`, `fixed_finish` |
| `constraint_at` | datetime nullable | obligatoire avec une contrainte |
| `progress_percent` | entier | de 0 à 100 |
| `is_milestone` | booléen | impose une durée nulle |
| `billing_milestone` | booléen | information seulement en V1 |

### `task_dependencies`

| Champ | Type | Règle |
| --- | --- | --- |
| `predecessor_task_id` | UUID | même projet que le successeur |
| `successor_task_id` | UUID | différent du prédécesseur |
| `kind` | enum | `finish_start` par défaut, puis `start_start`, `finish_finish`, `start_finish` |
| `lag_minutes` | entier | positif ou négatif, borné |

Une contrainte unique empêche le doublon d'une liaison. Un cycle rend le
planning invalide et doit nommer les tâches qui le forment.

### `planning_resources` et `task_allocations`

Une ressource porte un nom, un type, une capacité et un calendrier. Une
allocation relie une tâche à une ressource avec un taux d'occupation. En V1,
le moteur détecte les surcharges mais ne déplace pas les tâches pour les
résoudre.

### `planning_snapshots`

Chaque calcul conserve : version du moteur, empreinte des entrées, date de
calcul, état `complete`, `incomplete` ou `invalid`, avertissements et résultat
sérialisé. Le cache n'est réutilisé que si l'empreinte des entrées est
identique.

## Règles de calcul

### Validation

Le moteur refuse de présenter un chemin critique si :

- une dépendance forme un cycle ;
- une tâche liée appartient à un autre projet ;
- une durée est négative ou les trois estimations ne sont pas ordonnées ;
- deux contraintes fixes sont incompatibles.

Une durée ou une contrainte absente ne reçoit jamais une valeur inventée. Le
résultat reste consultable avec l'état `incomplete` et la liste précise des
champs manquants.

### PERT et chemin critique

Quand les trois estimations sont présentes :

```text
durée attendue = (optimiste + 4 × probable + pessimiste) / 6
variance = ((pessimiste - optimiste) / 6)²
```

Le moteur effectue ensuite les passes avant et arrière du CPM pour calculer
début au plus tôt, fin au plus tôt, début au plus tard, fin au plus tard et
marge totale. Une tâche est critique quand sa marge est nulle dans la précision
retenue.

Le calendrier par défaut proposé est Europe/Paris, du lundi au vendredi,
09:00-12:00 et 14:00-18:00. Il doit rester configurable par projet.

### Prévision

La première version affiche la date PERT attendue et une fourchette issue des
variances du chemin critique, qualifiée comme estimation. Une seconde phase
pourra exécuter une simulation Monte-Carlo avec graine dérivée de l'empreinte
des entrées afin que le résultat reste reproductible. Elle devra montrer la
graine, le nombre d'itérations et les percentiles P50, P80 et P90.

## API locale proposée

```text
GET  /api/projects/{project_id}/schedule
POST /api/projects/{project_id}/schedule/calculate
GET  /api/projects/{project_id}/schedule/snapshots/{snapshot_id}
PUT  /api/tasks/{task_id}/schedule
POST /api/projects/{project_id}/dependencies
DELETE /api/projects/{project_id}/dependencies/{dependency_id}
```

`GET schedule` et `calculate` restent sans effet métier externe. Les routes de
mutation valident les rattachements, enregistrent une trace d'audit et
invalident le snapshot courant.

## Contrat MCP proposé

Deux outils de lecture dans le premier lot :

### `get_project_schedule`

Entrée : `project_id`, vue optionnelle `summary`, `gantt` ou `pert`.

Sortie : version de calcul, état, tâches calculées, chemin critique,
avertissements, données manquantes, empreinte et date de calcul.

### `explain_project_schedule`

Entrée : `project_id` et question facultative.

Sortie structurée : facteurs de retard, tâches critiques, conflits de
ressources et preuves de calcul. L'explication textuelle du LLM doit toujours
s'appuyer sur ces champs.

Les futurs outils `set_task_estimate`, `link_tasks` et `move_milestone` seront
classés comme mutations et resteront désactivés tant qu'une confirmation
humaine explicite n'est pas disponible dans le pont MCP.

## Interface proposée

Ajouter un onglet `Planning` dans la fiche projet :

1. bandeau de qualité des données ;
2. sélecteur `Liste`, `Gantt`, `PERT` ;
3. ligne de temps zoomable sans dégradé ;
4. chemin critique en magenta, dépendances normales en cyan ;
5. jalons sous forme de losanges SVG ;
6. panneau latéral expliquant dates, marges et alertes ;
7. tableau accessible reprenant toutes les informations du diagramme.

Un planning incomplet ne montre pas une date finale comme certaine. Le bandeau
indique par exemple : « 4 tâches sur 11 n'ont pas d'estimation de durée ».

## Découpage recommandé

### Lot A - Socle calculable (implémenté)

- migrations et schémas ;
- validation du graphe ;
- moteur PERT/CPM pur, sans accès base ;
- tests unitaires par tables de cas ;
- API de calcul.

### Lot B - Prototype en lecture seule

- écran Liste et Gantt ;
- réseau PERT ;
- états incomplet et invalide ;
- tests clavier, lecteur d'écran et rendu visuel.

### Lot C - MCP de lecture

- deux outils proposés ;
- contrat borné et versionné ;
- tests route, service et outil ;
- aucune mutation.

### Lot D - Prévision avancée

- simulation reproductible ;
- conflits de ressources ;
- comparaison de scénarios, toujours sans appliquer automatiquement un plan.

## Critères d'acceptation du prototype

- un même jeu d'entrées produit le même snapshot sur macOS, Windows et Linux ;
- un graphe avec cycle est refusé avec la chaîne du cycle ;
- un projet incomplet nomme chaque champ manquant ;
- le chemin critique et les marges sont vérifiés sur au moins cinq graphes de
  référence, dont dépendances parallèles et décalages ;
- le Gantt, le PERT et le tableau accessible racontent les mêmes dates ;
- l'outil MCP ne peut ni créer ni modifier une tâche ;
- aucune date absente n'est complétée par le LLM ;
- le calcul de 1 000 tâches et 5 000 dépendances reste inférieur à une seconde
  sur la machine de référence, hors rendu.

## Arbitrages validés

Ludo a validé les cinq choix le 4 septembre 2026 :

1. prototype en lecture seule avant toute écriture par l'IA ;
2. calendrier Europe/Paris, lundi-vendredi, 09:00-12:00 et 14:00-18:00 ;
3. jalons de facturation informatifs en V1, sans déclenchement ;
4. nivellement automatique des ressources reporté après le prototype ;
5. prévision Monte-Carlo autorisée uniquement dans le lot D.

## Résultat du lot A

- cinq tables dédiées avec contraintes et migration Alembic ;
- moteur pur `pert-cpm-1`, sans accès base ni LLM ;
- quatre types de dépendances, décalages, jalons et contraintes fixes ;
- états `complete`, `incomplete` et `invalid`, avec champs ou cycles nommés ;
- cache immuable par empreinte SHA-256 des entrées ;
- routes de calcul, dernier snapshot et snapshot précis ;
- aucune route de mutation de planning exposée dans ce lot.

## Références internes

- `.app-loop/proposals.json`, P-039 ;
- `src/backend/app/models/entities.py`, modèles `Project` et `Task` ;
- `src/backend/app/routers/tasks.py`, API de tâches existante ;
- `src/backend/app/services/mcp_therese_server.py`, registre MCP actuel ;
- `docs/rules/RULES-DESIGN.md` et `docs/rules/RULES-DONNEES.md`.
