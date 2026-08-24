# Traitements longs, complément (0.47) - Board, actions, indexation, fencing

> Design V1 du 24/08/2026 (soir), À CHALLENGER par Soso avant toute ligne de
> code. Solde la dette actée du jalon 0.46 : les trois producteurs reportés
> et la promesse complète sur les outils.

## Ce qui existe et fait foi

Le patron 0.46 est prouvé sur quatre producteurs : `TraitementHandle`
(CAS durables, état terminal au producteur, `AnnuleAvantDemarrage` = zéro
production, échec post-création = `failed` explicite), panneau Traitements,
annulation canonique par `/api/processing-tasks/{id}/cancel`. Chaque
enrôlement 0.47 suit EXACTEMENT ce patron - y compris ses deux pièges
d'initialisation fermés en passe 2/3 de revue.

## 1. Board - le producteur résistant

État réel : `generate_stream` lance les advisors en tâches parallèles + un
moniteur ; le `finally` du flux annule déjà tout à la fermeture (panneau
fermé = déconnexion SSE) ; `decision_id` ne naît qu'à la SAUVEGARDE finale.

Enrôlement (recommandation du challenge 0.46) :
- le handle naît AVANT le premier événement SSE (type `board`, label =
  question tronquée), `generation_id` émis au frontend en premier événement ;
- `entity_id` renseigné avec le `decision_id` APRÈS la sauvegarde (le
  handle gagne une méthode `rattacher_entite(entity_id)` - UPDATE simple) ;
- adaptateur : `AnnulationParTacheAsyncio` sur la tâche du flux - l'arrêt
  canonique emprunte le MÊME chemin que la fermeture du panneau (le finally
  existant annule les advisors) ; « fermer le panneau annule » reste vrai ;
- états : `done` après sauvegarde, `cancelled` sur fermeture/annulation
  (partiel NON persisté : une décision à moitié délibérée ne se sauve pas,
  c'est le contrat Board existant), `failed` avec cause.

## 2. ActionRunner - corriger le mensonge AVEC l'enrôlement

État réel : `cancel_task` pose l'évènement ET marque immédiatement
`CANCELLED` + `completed_at` pendant que le flux LLM de l'étape continue -
le mensonge historique documenté partout.

- `cancel_task` ne pose QUE l'évènement (plus jamais l'état) ; le statut
  `CANCELLED` n'est posé que par la boucle `run()` quand elle constate
  l'évènement (chemin existant lignes ~594-609, qui devient le SEUL) ;
- le TaskState gagne `CANCEL_REQUESTED` pour l'affichage de son propre
  panneau historique - même distinction que ProcessingTask ;
- enrôlement : un ProcessingTask type `action` par run (label = agent),
  adaptateur `AnnulationCooperative(poser_drapeau=_cancel_event.set)`,
  progression = étapes (i+1)/n via `handle.progresser(step=label)`,
  mapping final COMPLETED→done, FAILED→failed, CANCELLED→cancelled ;
- la route historique d'annulation d'action passe par le service canonique
  (résolution par entity_id = task_id du runner), repli direct sinon -
  même bascule que l'Atelier en 0.46.

## 3. Indexation - une tâche par fichier

État réel : `index_payload` porte `est_abandonnee` (coopératif, consulté
aux étapes sûres) ; l'extraction threadée va à son terme (arrêt différé
ASSUMÉ, documenté depuis 0.41.3).

- la route `/api/files/index` crée un handle type `indexation` (label =
  nom du fichier), et `est_abandonnee` devient : déconnexion OU
  `handle.annulation_demandee()` - le panneau peut donc abandonner une
  indexation exactement comme la déconnexion le fait déjà ;
- `remplacer_puis_indexer` (upload de projet) : même enveloppe ;
- le trombone du chat n'a PAS de tâche propre : il vit dans la génération
  de chat qui le porte (déjà annulable par elle) ;
- états : done (chunk_count consigné), cancelled (abandon constaté - l'état
  précédent de l'index reste la vérité, invariant N1 existant), failed ;
- project.sync appelle `index_payload` DANS son apply : pas de double
  tâche - `index_payload` n'enrôle RIEN lui-même, ce sont ses APPELANTS
  de surface (route, upload) qui enrôlent. Règle écrite : un traitement =
  un geste UTILISATEUR, pas une fonction interne.

## 4. Fencing des outils mutateurs - la promesse complète

Promesse 0.46 : « aucune NOUVELLE étape lancée ». Reste le trou documenté :
un outil DÉJÀ lancé (thread, MCP) commite son effet après l'annulation.

- un helper `annulation_en_vol(conversation_id) -> bool` (lecture du
  drapeau existant) exposé par le module chat aux outils ;
- les outils mutateurs LOCAUX (workspace : création de contact/projet/tâche,
  écriture de document, mutations agenda locales) appellent le fence JUSTE
  AVANT leur commit : annulation en vol = l'outil retourne « interrompu
  avant écriture » comme résultat d'outil, AUCUN commit ;
- les outils MCP externes et le web restent HORS fencing (on ne peut pas
  dé-lancer une requête externe) - la promesse écrite reste « aucun effet
  LOCAL ultérieur », les effets externes déjà partis sont assumés ;
- inventaire des outils mutateurs à figer par un test de complétude : tout
  outil du dispatcher qui écrit en base ou sur disque doit référencer le
  fence (test par inspection du module, même esprit que les tests de
  parité du manifeste).

## 5. Dette interne soldée au passage

- déduplication du message partiel LIÉE à la génération : le Message
  partiel porte `{"generation_id": ...}` dans `extra_data`, la dédup se
  fait dessus - deux réponses identiques légitimes ne sont plus confondues ;
- avertissements React `act()` des tests à faux timers : nettoyés ;
- `docs/releases` et CLAUDE.md mis à jour en fin de jalon.

## Séquencement

1. ActionRunner (le mensonge est le plus ancien défaut documenté) ;
2. Indexation (enveloppe de route, la plus mécanique) ;
3. Board (le résistant, avec `rattacher_entite`) ;
4. Fencing (transversal, test de complétude) ;
5. dette interne + revue de jalon.

## Hors périmètre (explicite)

Reprise `resumable`, watchers, llm_usage/temps par projet, remplacement des
Loader2, SSE dédié aux traitements, barrière de restauration.

## Questions ouvertes pour le challenge

1. Board : l'adaptateur sur la tâche du flux SSE annule le TRANSPORT - le
   même chemin que la déconnexion. Y a-t-il un cas où le flux survit au
   transport (buffering Starlette) qui rendrait l'arrêt mensonger ?
2. ActionRunner : son panneau historique (TaskState) reste-t-il exposé
   quelque part côté frontend, ou le panneau Traitements le remplace-t-il
   de fait (deux listes pour la même chose = divergence garantie) ?
3. Le fence par conversation_id : les outils reçoivent-ils tous le
   conversation_id aujourd'hui, ou faut-il le faire circuler ?
4. Indexation en MASSE (déposer 30 fichiers = 30 requêtes = 30 tâches) :
   le panneau devient-il illisible ? Seuil de visibilité à étendre au type
   `indexation` (< 2 s masquées) ?
