# Registre de tâches (0.46) - voir, suivre et arrêter les traitements longs

> Design V1 du 24/08/2026, À CHALLENGER par Soso avant toute ligne de code.
> Reprend le socle A du plan 0.42 (suggestions 1, 2, 12), corrigé par ce qui
> existe DÉJÀ : `ProcessingTask` + `task_registry` (31/07), le Stop du chat
> câblé frontend→backend (J1b, 31/07), project.sync enrôlé (0.45).

## Le manque, constaté dans le code au 24/08

| Existant | Trou |
|---|---|
| `POST /api/chat/cancel` câblé depuis l'interface (J1b) | le drapeau n'est consulté qu'ENTRE deux chunks (`chat.py`) : ni dans la boucle fournisseur, ni autour des outils ; une sortie anticipée saute la finalisation des métriques |
| `ProcessingTask` (durable) + `task_registry` (runtime, 4 adaptateurs définis) | UN seul producteur (project.sync) ; personne d'autre n'appelle `inscrire()` ; aucune route ne LISTE les tâches ; rien à montrer |
| `agent_tasks` (Atelier, cycle de vie persisté) | pas de lien avec `processing_tasks` ; `ActionRunner` marque `CANCELLED` alors que le flux LLM continue (mensonge à ne pas généraliser) |
| `statusStore.progress` (frontend) | slot déclaré, JAMAIS alimenté |
| 4 registres mémoire séparés (`_active_generations`, `_running_agent_tasks`, `ActionRunner._tasks`, flux Board) | aucune vue d'ensemble, annulations hétérogènes |

## Contrat produit (MVP 0.46)

1. **Une surface Traitements** : un indicateur discret dans la coque (badge
   n tâches actives) ouvre un panneau listant les traitements actifs et les
   N derniers terminés - label lisible, étape, progression quand elle est
   mesurable, bouton Arrêter quand un adaptateur vivant existe.
2. **Arrêter dit la vérité** : `cancel_requested` tant que l'arrêt n'est pas
   CONFIRMÉ par l'adaptateur ; `cancelled` seulement quand le travail est
   réellement coupé. La sémantique mensongère d'ActionRunner est CORRIGÉE,
   pas généralisée.
3. **Le Stop du chat arrête le compteur** : le drapeau est consulté dans la
   boucle de consommation du flux fournisseur ET avant chaque exécution
   d'outil ; la sortie anticipée finalise les métriques et l'état durable
   APRÈS le nettoyage runtime.
4. **Cinq producteurs enrôlés** : chat, indexation de fichiers, missions
   Atelier, décisions Board, actions `{action: ...}` - chacun via
   l'adaptateur de SA famille (jamais une mécanique inventée). project.sync
   l'est déjà.
5. **Récupération au redémarrage** : déjà en place (`interrupted`) - les
   nouveaux producteurs en héritent gratuitement.

## Architecture

### Durable - `ProcessingTask` (table existante, AUCUNE colonne ajoutée)
Les types s'étendent par convention de chaîne : `chat`, `indexation`,
`atelier`, `board`, `action`, `project_sync` (existant). `entity_id` porte
l'identifiant métier (conversation, fichier, mission, décision).

### Runtime - `task_registry` (existant)
`inscrire(task_id, adaptateur)` à l'entrée du traitement, `retirer()` en
finally. Adaptateurs par famille, DÉJÀ définis dans le module :
- chat → `AnnulationParDrapeauCooperatif` (pose `_active_generations[id] = False`) ;
- indexation → drapeau coopératif (le `est_abandonnee` existant) ;
- Atelier → `AnnulationParTacheAsyncio` (le `.cancel()` déjà éprouvé d'`agents.py`) ;
- Board → fermeture de flux ;
- actions → drapeau coopératif de l'`ActionRunner`, MAIS l'état durable ne
  passe `cancelled` qu'à la sortie effective de la boucle.

### Cycle de vie type d'un producteur
```
row = creer_processing_task(type, label, ...)   # queued -> running
task_registry.inscrire(row.id, adaptateur)
try:    ... travail, MAJ progress/step par transactions courtes ...
finally:
    task_registry.retirer(row.id)
    finaliser(row.id, done|failed|cancelled)     # l'état durable EN DERNIER
```
Un helper unique `app/services/traitements.py` porte ce squelette
(`ouvrir_traitement()` context manager async) pour que les cinq producteurs
n'aient pas cinq variantes.

### API
- `GET /api/tasks?actives=true|false&limit=` → tâches triées récentes
  d'abord (état, label, step, progress, type, created/started/finished).
- `POST /api/tasks/{id}/cancel` → 404 inconnu ; si adaptateur vivant :
  `demander_annulation()` → confirmé = `cancelled`, non confirmé =
  `cancel_requested` (200 avec l'état résultant) ; si plus vivant et état
  actif → `interrupted` (le processus est mort) ; si terminal → 409.

### Frontend
- `tasksStore` (zustand) : liste + polling léger (3 s quand le panneau est
  ouvert OU qu'une tâche active existe, sinon rien).
- `TasksIndicator` dans la coque (badge) + `TasksPanel` (liste, Arrêter).
- `statusStore.progress` : SUPPRIMÉ (slot jamais alimenté) - le panneau est
  la seule vérité. Les 65 `Loader2` ad hoc restent en place (hors MVP).

## Profondeur du Stop chat (le point technique dur)

État : le flag n'est consulté qu'entre deux chunks émis au client. Cibles :
1. consulter AVANT chaque exécution d'outil et juste APRÈS (un outil peut
   durer des secondes) ;
2. dans la boucle de consommation du flux fournisseur, à chaque événement
   reçu (pas seulement à chaque chunk retransmis) ;
3. sur sortie anticipée : fermer le flux fournisseur (`aclose`), finaliser
   métriques et message partiel en base, PUIS l'état durable `cancelled` ;
4. test rouge exigé (plan 0.42) : fournisseur bloqué → le producteur reçoit
   l'arrêt, aucune écriture tardive, registre runtime nettoyé, état durable
   terminal après nettoyage. Le test existant ne vérifie que le booléen.

## Atelier : lien, pas absorption
`agent_tasks` garde branche/diff/événements. La mission crée AUSSI un
`ProcessingTask` (type `atelier`, `entity_id` = agent_task.id) et l'annulation
passe par le panneau comme par la route existante - même adaptateur.

## Hors périmètre 0.46 (explicite)
`llm_usage`/temps par projet (J5), remplacement des 65 Loader2, barrière de
restauration (la restauration reste le cas spécial documenté), reprise
`resumable` (seul `interrupted` + réessayer manuel), watchers.

## Questions ouvertes pour le challenge
1. Le polling 3 s suffit-il, ou le flux SSE existant du chat doit-il pousser
   les changements de tâches (coût/complexité) ?
2. `ouvrir_traitement()` context manager : quelle signature pour couvrir les
   cinq familles sans devenir un fourre-tout ?
3. Board : la « tâche » est-elle le flux SSE (annulé à la fermeture du
   panneau ?) ou la décision en cours de génération ?
4. Le chat crée-t-il une ProcessingTask PAR message (volume !) ou seulement
   au-delà d'un seuil de durée ? Un row par message = des centaines de
   lignes/jour ; proposition : créer la row à la volée seulement si la
   génération dépasse 2 s, sinon rien.
5. L'indexation en masse (dépôt de 30 fichiers) : une tâche par fichier ou
   une tâche agrégée ?
