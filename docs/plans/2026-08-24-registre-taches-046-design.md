# Traitements longs (0.46) - voir, suivre et arrêter, sans mentir

> **Design V2.1 du 24/08/2026** - V1 challengée (10 findings, « à
> reprendre »), V2 contre-challengée (VIABLE, 5 corrections intégrées
> ci-dessous). Le code peut démarrer.

## Le vocabulaire d'abord (finding 1)

« Tâches » est PRIS : `/api/tasks`, `taskStore`, `TasksPanel` sont les todos
métier. Ce chantier parle de **traitements** :
route `/api/processing-tasks`, store `useProcessingTasksStore`, panneau
`TraitementsPanel`. Aucune collision.

## État des lieux exact (finding 2, corrigé)

Le Stop du chat est DÉJÀ profond (J1b, 31/07) : surveillant d'annulation en
concurrence avec `__anext__()` du producteur, fermeture du générateur,
métriques finalisées, garde avant chaque outil et avant la première écriture
durable, nettoyage en `finally`. Sémantique du drapeau :
`_active_generations[id] = True` signifie « annulation demandée ».

Les VRAIS trous :
- pas de garde APRÈS l'outil ; un outil lancé (thread, MCP) peut poursuivre
  ses effets après l'annulation de la coroutine ;
- le message partiel n'est pas persisté en base sur annulation ;
- le registre est indexé par `conversation_id`, pas par GÉNÉRATION unique ;
- `deep-research` est un long flux chat séparé (chat.py:840) : il est INCLUS
  dans ce chantier (même mécanique, type `deep-research`).

`task_registry` : complet côté runtime mais **zéro producteur en
production** (seuls les tests appellent `inscrire()`). project.sync est
producteur DURABLE seulement - et il est mal fini : pas de try/finally
autour du run, une exception hors boucle laisse la ligne `running` jusqu'au
redémarrage (finding 5). `statusStore.progress` n'est lu par personne :
suppression sûre, en nettoyage séparé.

## La promesse réaliste (finding 9)

Aucun système ne fait cesser instantanément le calcul d'un fournisseur
cloud. La promesse tenable, et tenue : **THÉRÈSE cesse d'attendre, ferme le
transport quand c'est possible, et interdit tout effet local ultérieur.**
L'interface distingue « Arrêter » de « Arrêt demandé - fin de l'étape en
cours ». Précision V2.1 sur les outils : la garantie MVP est « aucune
NOUVELLE étape lancée ; une étape non interruptible déjà en cours (thread,
MCP) peut finir » - le fencing avant commit des outils mutateurs est un
chantier 0.47, pas une promesse implicite.

## Architecture

### `TraitementHandle` - explicite, jamais magique (finding 7)

Les familles n'ont ni leur session DB, ni leur identifiant métier, ni la
même signification de `CancelledError` au même moment. Pas de context
manager qui infère l'état terminal :

```python
handle = await creer_traitement(type, label, project_id=..., conversation_id=...)
handle.lier_adaptateur(adaptateur)      # inscrit au registre runtime
await handle.progresser(step=..., progress=...)
await handle.terminer(etat, error=...)  # SEUL le producteur décide l'état
# + un mini context manager optionnel qui garantit UNIQUEMENT le retrait
# runtime (pas l'état terminal)
```

### Annulation - l'autorité est au producteur (finding 4)

`POST /api/processing-tasks/{id}/cancel` (corrections V2.1) :
- `queued` → CAS atomique direct vers `cancelled` (un producteur ne peut
  plus la faire passer `running` ensuite : le démarrage vérifie l'état) -
  sans cela une tâche jamais démarrée resterait `cancel_requested` pour
  toujours ;
- `running` → transition atomique vers `cancel_requested` + transmission à
  l'adaptateur s'il est vivant ; `lier_adaptateur()` REJOUE une demande
  arrivée avant l'enrôlement (fenêtre de course fermée) ;
- `can_cancel` devient FAUX dès la demande posée (plus « adaptateur
  vivant » seul) ;
- il n'écrit JAMAIS `cancelled` sur une running, ni `interrupted` :
- `cancelled` : posé par le producteur, après son nettoyage réel ;
- `interrupted` : réservé au redémarrage (existant) ;
- l'absence d'adaptateur ne prouve rien (fenêtre d'enregistrement,
  traitement non annulable, nettoyage en cours) - la réponse dit juste
  `transmise: true|false` ;
- résultat d'adaptateur STRUCTURÉ : `accepted | stopped | unavailable`
  (le booléen actuel est ambigu) ;
- un `cancel_requested` arrivé trop tard est résolu par le producteur :
  il termine `done` si le travail était déjà fini (et le dit).

### API

- `GET /api/processing-tasks?actives=true|false&limit=` - DTO : id, type,
  label, state, step, progress, `can_cancel` (adaptateur vivant),
  horodatages, error. Index sur `created_at` + rétention (purge des
  terminées > 30 jours, au démarrage).
- `POST /api/processing-tasks/{id}/cancel` - 404 inconnue, 409 terminale,
  200 `{state, transmise}`.

### Chat : une ligne PAR GÉNÉRATION LLM (finding 8.4, convergence V2.1)

- **`ProcessingTask.id` EST le `generation_id`** ; le SSE émet
  `conversation_id` + `generation_id` dès le premier événement ;
- `/api/chat/cancel/{conversation_id}` reste une FAÇADE compatible (le
  frontend J1b déployé envoie un conversation_id) : elle résout la
  génération active de la conversation puis appelle le service canonique ;
- la ligne est créée IMMÉDIATEMENT (des centaines de petites lignes ne
  gênent pas SQLite) ; les commandes déterministes `{action: ...}` n'en
  créent JAMAIS (ce sont des navigations instantanées, pas des traitements) ;
- le seuil de 2 s est un seuil de VISIBILITÉ filtré CÔTÉ SERVEUR, avant
  `limit`, UNIQUEMENT pour les types `chat` et `deep-research` : actives
  masquées si `now - created_at < 2 s`, succès masqués si
  `finished_at - created_at < 2 s` ; échecs et annulations TOUJOURS
  visibles. JAMAIS de création différée (courses fin/annulation) ;
- sur annulation : persister le message partiel en base, puis `cancelled`.

### Frontend

- `useProcessingTasksStore` : polling 3 s quand le panneau est ouvert OU
  qu'une tâche active est connue ; 10-15 s sinon quand l'app est visible
  (pas d'angle mort au démarrage) ;
- `TraitementsIndicator` (badge) + `TraitementsPanel` : label, étape,
  progression, bouton Arrêter si `can_cancel`, état « Arrêt demandé - fin
  de l'étape en cours » après le clic ;
- les boutons Stop du chat et de l'Atelier passent par le service
  d'annulation canonique ; celui du Board GARDE son mécanisme existant
  (fermeture de flux) jusqu'à son enrôlement en 0.47 - pas de façade
  précipitée sur le producteur le plus résistant.

## Séquencement - prouver le cycle avant de généraliser (finding 9)

Le MVP enrôle TROIS producteurs, du plus simple au plus dur, et s'arrête là :

1. **Fondation** : `TraitementHandle` + routes + rétention + DTO `can_cancel`
   + résultat d'adaptateur structuré. TDD sur un producteur factice.
2. **project.sync réparé** (finding 5) : try/finally autour du run,
   enrôlement runtime (annulation d'un apply depuis le panneau), état
   terminal posé sur TOUS les chemins. C'est le banc d'essai du patron.
3. **Atelier** (le plus facile : `asyncio.Task` + finally existants) :
   ProcessingTask lié à `agent_tasks` (`entity_id` = agent_task.id), même
   adaptateur pour le panneau et la route existante. Tests exigés :
   annulation par le panneau ET par la route historique, déconnexion du
   client pendant la mission, cohérence des états `AgentTask` /
   `ProcessingTask` sur tous les chemins de sortie.
4. **Chat** (le plus dur sémantiquement) : generation_id, ligne par
   génération, garde après outil, message partiel persisté, deep-research
   inclus, tests d'absence d'écriture tardive (fournisseur bloqué, outil
   lent).
5. **Surface frontend** + bascule des boutons Stop existants.

**Reportés à 0.47** (après preuve du cycle) : Board (le plus résistant :
pas d'ID avant la sauvegarde, annulation couplée au panneau - il faudra un
ProcessingTask.id créé avant le premier événement SSE), ActionRunner
(corriger le mensonge CANCELLED en même temps que son enrôlement),
indexation de fichiers (une tâche PAR fichier, arrêt différé assumé).

## Hors périmètre (explicite)

Remplacement des 65 Loader2, llm_usage/temps par projet, reprise
`resumable`, watchers, barrière de restauration, SSE dédié aux traitements
(le polling suffit au MVP).

## Tests exigés

- annulation pendant chaque phase du chat (avant outil, pendant outil lent,
  entre chunks, après dernier chunk) → aucune écriture locale tardive,
  message partiel persisté, état `cancelled` posé par le producteur ;
- cancel sur tâche sans adaptateur → `cancel_requested` + `transmise: false`,
  PAS `interrupted` ;
- producteur qui finit pendant un `cancel_requested` → `done`, pas
  d'écrasement ;
- project.sync : exception hors boucle → ligne `failed`, jamais `running`
  fantôme ; annulation d'un apply depuis le panneau → `cancelled` + reprise
  possible par nouveau plan ;
- rétention : les terminées > 30 j sont purgées, les actives jamais.

## Révision V2 - ce que le challenge a changé

1. Renommage complet (« traitements ») : `/api/tasks` et TasksPanel sont les
   todos (collision bloquante).
2. État des lieux du chat corrigé : J1b a déjà fait le travail profond, les
   trous réels sont la garde post-outil, les effets threadés/MCP, le message
   partiel et l'identité par génération - et la sémantique du drapeau était
   INVERSÉE dans la V1.
3. L'endpoint cancel ne pose plus jamais d'état terminal (l'autorité est au
   producteur) ; `interrupted` réservé au redémarrage.
4. `TraitementHandle` explicite au lieu du context manager magique.
5. project.sync réparé EN PREMIER (try/finally manquant constaté).
6. MVP resserré : 3 producteurs prouvés (project.sync, Atelier, chat) ;
   Board, ActionRunner et indexation reportés à 0.47.
7. Chat : ligne par génération immédiate + seuil de VISIBILITÉ (jamais de
   création différée) ; `{action:...}` déterministes exclus ; deep-research
   inclus.
8. Résultat d'adaptateur structuré, `can_cancel` au DTO, « Arrêt demandé »
   distinct dans l'interface, promesse réaliste écrite noir sur blanc.
