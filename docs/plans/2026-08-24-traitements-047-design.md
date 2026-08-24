# Traitements longs, complément (0.47) - Board, actions, indexation, fencing

> **Design V2.1 du 24/08/2026 (nuit)** - V1 challengée (10 findings), V2
> contre-challengée (VIABLE, 5 corrections intégrées ci-dessous). Le code
> peut démarrer.

## Le socle qui fait foi

Patron 0.46 prouvé : `TraitementHandle` (CAS durables, état terminal au
producteur, `AnnuleAvantDemarrage` = zéro production, échec post-création =
`failed`), panneau Traitements, annulation canonique. Chaque enrôlement суit
ce patron, pièges d'initialisation compris.

## 1. Board

Constats exacts (challenge) : le `finally` du flux n'est qu'un nettoyage
LOCAL de la branche cloud parallèle - il ne couvre ni la recherche web, ni
le mode souverain, ni la synthèse, ni la persistance. La garantie d'arrêt
global vient de l'annulation de la TÂCHE PORTEUSE du flux. Avec la pile
verrouillée (Starlette 1.2.1 + Uvicorn 0.40, listener de déconnexion ASGI),
pas de trou de buffering connu.

- **`decision_id` PRÉALLOUÉ** avant la création du handle et passé au
  service (l'UUID naissait à la sauvegarde sans nécessité) - `entity_id`
  posé dès la création, pas de `rattacher_entite` ;
- handle type `board` créé avant le premier événement SSE, `generation_id`
  émis en premier ;
- adaptateur `AnnulationParTacheAsyncio` sur la tâche porteuse du flux ;
- **fence avant le commit** de la décision ; après commit confirmé, `done`
  GAGNE même si une demande d'arrêt arrive trop tard (le producteur résout
  le cancel_requested tardif en done - contrat 0.46) ;
- états : done après commit, cancelled sur annulation/déconnexion (pas de
  partiel : une décision à moitié délibérée ne se sauve pas), failed ;
- **contrats UI distincts** : le Board classique ferme = annule (existant) ;
  le nouveau canevas MASQUE sans annuler (contrat testé) - les boutons
  Annuler des DEUX passent par l'endpoint canonique avec le generation_id
  PUIS ferment le transport ; masquer ne touche à rien ;
- matrice de tests par phase : annulation pendant recherche web, pendant
  advisors cloud, en mode souverain séquentiel, pendant la synthèse, avant
  le commit, après le commit (done gagne) - au niveau StreamingResponse,
  pas seulement sur le générateur du service.

## 2. ActionRunner - corriger le mensonge sans casser son panneau

Constats exacts : le panneau Actions est VIVANT (lancement + progression
par étapes, `TaskState` consommé par actions.ts et ActionPanel.tsx) - il
reste ; Traitements est la vue globale. Les deux seules écritures de
`CANCELLED` sont cancel_task (le mensonge) et le chemin final de la boucle.
L'enum d'échec s'appelle `ERROR` (pas FAILED). `_execute` a des zones hors
try (contexte local, callbacks) qui peuvent le tuer en laissant tout
`running`.

- `cancel_task` pose l'évènement + `TaskStatus.CANCEL_REQUESTED` (nouvel
  état TaskState), SANS `completed_at` ; seul le chemin de boucle pose
  `CANCELLED` ;
- `_execute` ne réécrit pas `RUNNING` si l'annulation a gagné avant son
  démarrage (course testée) ;
- **enveloppe terminale autour de TOUT `_execute`** (contexte local et
  callbacks compris) : correspondance COMPLETED→done, ERROR→failed,
  CANCELLED→cancelled - plus aucun chemin qui laisse TaskState ET
  ProcessingTask `running` ;
- enrôlement : un ProcessingTask type `action` par run ; l'adaptateur
  canonique appelle une PRIMITIVE UNIQUE `demander_arret_action(task_id)`
  qui pose l'évènement ET `TaskStatus.CANCEL_REQUESTED` (V2.1 : un simple
  event.set laissait le panneau Actions afficher running) ; progression =
  étapes via `handle.progresser(step=label, progress=(i+1)/n)` ;
- frontend Actions : `cancel_requested` ajouté à l'union TS, libellés,
  couleurs, états ACTIFS (le polling continue, le spinner devient « arrêt
  demandé »), nettoyage mémoire ;
- la route d'annulation d'action passe par le service canonique (résolution
  entity_id), repli direct sinon - bascule identique à l'Atelier 0.46.

## 3. Indexation - deux niveaux formalisés

Constats exacts : le trombone appelle `/api/files/index` DIRECTEMENT à
l'attachement (avant tout message, avec son AbortController) - c'est un
traitement AUTONOME ; le fallback interne de chat.py (~197) a encore son
propre pipeline sans fence ; `index_payload` saute l'écriture sur abandon
puis retourne un FileResponse NORMAL - l'enveloppe ne peut pas distinguer
done de cancelled.

- **Règle écrite** : le cœur (`index_payload`, `remplacer_puis_indexer`)
  n'enrôle JAMAIS ; seules les enveloppes de SURFACE (route `/index`,
  route `/upload`) créent un traitement. Un geste utilisateur = un
  traitement. Test : un apply project.sync avec plusieurs indexations =
  exactement UN ProcessingTask ;
- **issue d'abandon explicite** : le cœur lève `IndexationAbandonnee` au
  point exact où l'abandon est observé (au lieu du FileResponse normal).
  Branchements PRÉCIS (V2.1 - seul `/files/index` passait est_abandonnee
  jusqu'ici) : `/index` et `/upload` → traitement `cancelled` ; le fallback
  chat CESSE d'absorber aveuglément et laisse remonter l'abandon (la
  génération porte l'état) ; project.sync → l'exception INTERROMPT l'apply
  sans marquer l'opération `echec` (elle reste `a_faire`, l'apply constate
  l'annulation - chemin cancelled existant) ;
- adaptateur runtime : évènement local + `TravailNonInterruptible(event.set)`
  (l'extraction threadée va au bout - arrêt différé assumé), callback
  combiné `await request.is_disconnected() OR event.is_set()` ;
- le fallback interne de chat.py est raccordé au même cœur et au même
  signal (il vit dans la génération de chat qui le porte) ;
- type `indexation` ajouté au seuil de visibilité serveur (< 2 s masquées) ;
- une tâche PAR fichier (annulation individuelle) ; le regroupement visuel
  des lots attendra.

## 4. Fencing - un contexte d'exécution, pas un drapeau partagé

Constats exacts : le drapeau réel est indexé par conversation - deux
générations chevauchées peuvent fencer la mauvaise ; les outils workspace
ne reçoivent pas le conversation_id ; le chemin de confirmation perd tout ;
les mutateurs locaux immédiats réels sont `create_contact`,
`create_project`, `generate_document` (calendrier = geste confirmé séparé,
HORS périmètre ; email/web/MCP = externes).

- **`ContexteExecution`** explicite : `generation_id` + token d'annulation,
  construit par le chat au lancement de la génération, passé au dispatcher
  puis aux handlers - AUCUN service n'importe `routers.chat`. V2.1 : le
  contexte REMPLACE le drapeau partagé comme AUTORITÉ - un unique token par
  génération alimente le wrapper du flux, l'adaptateur canonique, le
  fallback d'indexation et les outils ; `_active_generations` devient une
  simple table conversation→token courant (compat lecture), jamais une
  seconde mécanique ;
- **registre déclaratif des outils** : chaque outil du dispatcher est classé
  `read_only | local_mutation | external_mutation` - test de complétude sur
  le registre (un outil non classé = rouge) ;
- les trois mutateurs locaux appellent le fence JUSTE AVANT leur premier
  effet durable - et pour contact/projet, AVANT `session.add()`/`flush()`
  (V2.1 : un « interrompu » après un add laisserait une écriture pendante
  commitée plus tard par la session du chat), Qdrant compris : annulation
  observée = résultat « interrompu avant écriture », zéro effet ;
- **tests COMPORTEMENTAUX avec barrières** : lancer l'outil, annuler avant
  le premier effet durable, relâcher, vérifier SQLite + Qdrant + disque -
  l'inspection statique ne prouve rien (generate_document écrit via le
  registre de skills) ;
- promesse écrite : « aucun nouvel effet MÉTIER local après observation de
  l'annulation » - la consignation du traitement et le message partiel sont
  explicitement exclus.

## 5. Divers

- index sur `ProcessingTask.entity_id` : RETIRÉ du MVP (V2.1 - attendre une
  preuve de lenteur).

## Retirés du MVP (challenge)

`rattacher_entite` générique, fencing du calendrier confirmé, regroupement
des lots d'indexation, nettoyage des warnings React (lot séparé), dédup du
partiel par generation_id (lot séparé non bloquant).

## Séquencement

1. ActionRunner (mensonge + enveloppe terminale + frontend Actions) ;
2. Indexation (issue d'abandon + enveloppes + trombone/fallback) ;
3. Board (préallocation + adaptateur + matrice de phases) ;
4. Fencing (contexte + registre déclaratif + tests à barrières) ;
5. index entity_id + revue de jalon.

## Révision V2 - ce que le challenge a corrigé

1. Board : finally = nettoyage local cloud seulement ; decision_id
   préalloué au lieu de rattacher_entite ; masquer ≠ annuler (deux
   contrats UI distincts) ; matrice de phases exigée.
2. ActionRunner : le panneau Actions est vivant et reste ; CANCEL_REQUESTED
   écrit dans TaskState (sinon inobservable) ; enveloppe terminale totale ;
   l'enum s'appelle ERROR.
3. Indexation : le trombone est un traitement autonome (il appelle la
   route) ; IndexationAbandonnee au lieu du FileResponse ambigu ; fallback
   chat.py raccordé ; adaptateur TravailNonInterruptible.
4. Fencing : ContexteExecution par generation_id (le drapeau par
   conversation fençait potentiellement la mauvaise génération) ; registre
   déclaratif + tests comportementaux ; inventaire corrigé (3 mutateurs).
