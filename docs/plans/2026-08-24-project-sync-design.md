# project.sync (0.45) - synchroniser un dossier local avec l'index d'un projet

> **Design V2 du 24/08/2026** - après le challenge de Soso sur la V1
> (14 findings, verdict « à reprendre », tous intégrés ; liste des changements
> en fin de document). À re-challenger avant le code.

## Le besoin

Dr_logic (testeur alpha, passé co-concepteur) synchronise ses dossiers de
travail par rsync et veut que THÉRÈSE réindexe ce qui a changé, avec une trace
de ce qui a été fait. Périmètre arbitré (UltraJury du 24/08) : **une racine
exclusive par projet, mode plan puis apply, jamais de reclassement silencieux,
zéro LLM, journal local, reprise après échec.**

## Contrat produit

1. Un projet peut déclarer **une** racine locale. Exclusive : jamais partagée,
   jamais imbriquée dans celle d'un autre projet.
2. **Le rattachement établit l'état de référence** : scan complet, empreinte
   SHA-256 de chaque fichier indexable, indexation initiale par un premier
   plan. Sans référence, aucune détection n'est possible (`content_hash`
   n'était alimenté nulle part - V1 l'avait supposé à tort).
3. **`plan`** est en lecture seule et **fail-closed** : racine absente,
   identité de volume changée, erreur de parcours ou de permission → le plan
   ÉCHOUE sans produire la moindre opération de retrait. Jamais de « tout a
   disparu » déduit d'un montage débranché.
4. **`apply`** exécute LE DERNIER plan uniquement (un plan plus récent rend
   les précédents caducs), item par item, sous verrou, avec revalidation :
   on n'indexe jamais une version différente de celle montrée. Une dérive
   entre plan et apply marque l'opération `obsolete` - un nouveau plan la
   reprendra.
5. **Aucun reclassement silencieux** : un chemin déjà possédé par un autre
   périmètre (global, autre projet, conversation) devient un **conflit
   visible**, jamais une opération `fait` (le scope d'`index_payload` est
   volontairement ignoré pour un fichier au périmètre voulu - V1 l'ignorait).
6. **Zéro LLM** : extraction et embeddings locaux, aucune complétion.
7. **Reprise at-least-once** : une opération reste `a_faire` jusqu'au succès
   COMPLET (vecteurs écrits + métadonnée à jour), puis un commit court la
   marque `fait`. Tous les gestes sont idempotents ; au redémarrage, un apply
   orphelin est repris là où il en était.
8. **Journal MVP réduit et honnête** : un `ProcessingTask` par run d'apply,
   `attempt_count`/`last_attempt_at`/dernier résultat par opération. Pas
   d'historique par tentative. Le journal n'est PAS une preuve de facturation
   (à dire à Dr_logic).

## Modèle de données - quatre tables nouvelles, zéro colonne ajoutée

`create_all()` crée les tables manquantes au démarrage packagé et n'ajoute
aucune colonne ; les FK SQLite ne sont pas activées par les PRAGMA actuels.
Donc : tables nouvelles, ménage explicite, et le parcours Alembic complet
(nouvelle révision idempotente - `create_all` peut être passé avant -,
MAJ `ALEMBIC_HEAD_REVISION` et de sa preuve de schéma, test de mise à niveau
d'une base 0.44 réelle).

- **`project_sync_roots`** : `project_id` (unique), `racine` (chemin
  canonique, contrainte UNIQUE), `volume_id` (st_dev au rattachement),
  `created_at`. Affectation sous **verrou global** : unicité + non-imbrication
  + `samefile()` vérifiés dans la même section critique (la V1 laissait une
  course entre deux requêtes). `delete_project` nettoie explicitement.
- **`project_sync_entries`** - l'état de référence par fichier : `project_id`,
  chemin canonique (unique par projet), `file_id`, `taille`, `mtime_ns`
  (entier epoch, jamais une date locale), `sha256` validé, horodatages,
  `generation_racine`. Distingue les fichiers gérés par la sync des pièces
  jointes et indexations manuelles. **Autorité formalisée (V2.1)** : cette
  table fait foi sur le DERNIER SNAPSHOT APPLIQUÉ ; `files` fait foi sur
  l'identité et le périmètre réellement indexés. Une entrée n'est JAMAIS
  écrite par le rattachement seul : seule une opération d'apply réussie
  l'établit. Après un crash, la divergence transitoire est réparée par la
  reprise (l'opération non `fait` se rejoue, idempotente). Changer ou
  retirer la racine incrémente `generation_racine`, invalide les plans et
  nettoie les entrées de l'ancienne génération.
- **`sync_plans`** : id, project_id, `generation_racine`, created_at, état
  (`propose | en_cours | applique | applique_partiel | caduc`), compteurs.
  (`abandonne` retiré : aucun geste utilisateur ne le déclenchait.)
- **`sync_operations`** : id, plan_id, type (`indexer | reindexer | retirer |
  conflit`), chemin, `file_id_prevu`, empreinte_prevue, empreinte_reelle,
  état (`a_faire | fait | echec | obsolete`), erreur, `attempt_count`,
  `last_attempt_at`.
- Index : `sync_operations(plan_id, etat)`, `sync_plans(project_id)`,
  `project_sync_entries(project_id)`.

## Deux services extraits AVANT le chantier sync (fondation)

Le challenge a montré que le routeur ne peut pas rester le seul détenteur des
verrous :

1. **Service d'indexation central** (`services/indexation.py`) : sortir
   `index_payload` + son verrou par chemin + le sémaphore du routeur, et faire
   passer TOUS les producteurs par lui (route index, `upload_file` - qui a
   aujourd'hui son propre pipeline non verrouillé -, chemin de secours du
   trombone dans chat.py, et la sync). La lecture des métadonnées passe SOUS
   le verrou (elle pouvait être périmée après une attente). V2.1 : vérifier le
   scope AU RETOUR est trop tard - le service accepte les ATTENDUS
   (`file_id`, scope, SHA-256), les vérifie sous verrou AVANT toute écriture
   (mismatch = conflit, zéro écriture), et extrait depuis une **copie
   stable** du fichier - le verrou interne ne protège pas contre rsync.
2. **Service de retrait** (`services/retrait_index.py`) idempotent et
   fail-closed : verrou du chemin, vérification du `file_id` attendu,
   suppression Qdrant **complète** (par filtre ou pagination - l'existant
   `delete_by_entity` plafonne à 1000 points et `delete_file` avale les
   erreurs Qdrant puis supprime quand même la ligne SQLite), PUIS suppression
   SQLite + entrée de référence. Entité déjà absente = succès (reprise).

V2.1 - « comportement constant » précisé : la route et l'upload fragmentent
en 1000/200, le trombone indexe seulement si nécessaire en 500/50, et
l'upload remplace le fichier AVANT le verrou actuel. D'où : **tests de
caractérisation d'abord** (ils gèlent le comportement observable de chaque
appelant), des **adaptateurs distincts** par famille d'appelant, et le
remplacement de fichier de l'upload ramené sous le même verrou. Le retrait
fail-closed est une CORRECTION volontaire du comportement sur erreur
(l'existant avalait les erreurs Qdrant), documentée comme telle.

## Détection des changements

Référentiel = `project_sync_entries` (pas `files` seul).

- **nouveau** : sur disque, absent du référentiel ;
- **candidat modifié** : SHA-256 systématique de chaque fichier scanné (stat
  avant/après le hash : s'il a bougé pendant la lecture, il est marqué
  **instable** et exclu du plan) ; hash égal au référentiel → inchangé.
  V2.1 : le préfiltre taille+mtime et son mode « vérification intégrale »
  sont retirés - hasher tout simplifie le produit et supprime une branche
  d'API, d'interface et de tests ; taille et mtime_ns restent STOCKÉS
  (diagnostic et évolution future) ;
- **disparu** : au référentiel, absent du disque ;
- **conflit** : sur disque mais possédé par un autre périmètre dans `files` ;
- scan et hachage **hors boucle asyncio** (`asyncio.to_thread`), erreurs de
  parcours REMONTÉES (jamais ignorées), extensions indexables et limites de
  taille du pipeline existant, liens symboliques sortant de la racine ignorés
  et journalisés.

## Exécution d'apply

- **Un `ProcessingTask` par run**, lié explicitement au plan
  (`plan_id` dans son payload). V2.1 : `recuperer_taches_orphelines()` ne
  fait que marquer `interrupted` - un **récupérateur sync spécifique**,
  lancé APRÈS l'initialisation de Qdrant, retrouve les plans `en_cours`
  orphelins et crée un **nouveau run de reprise** sur le même plan.
  Référence forte dans `app.state`, arrêt coopératif au shutdown (le
  lifespan ferme SQLite et Qdrant : l'apply s'interrompt proprement AVANT).
- **Verrou par projet étendu** (V2.1) : il couvre `apply`, `plan` ET la
  modification de racine. Un plan ne peut pas devenir caduc pendant qu'un
  apply court sur lui - créer un plan pendant un apply répond 409. Hors
  apply, seul le DERNIER plan `propose` est applicable.
- Boucle séquentielle sur `a_faire` : revalidation (stat + empreinte) sous le
  verrou du service central → dérive = `obsolete` ; indexation via le service
  central (attendus vérifiés avant écriture) ou retrait via le service de
  retrait ; succès COMPLET puis commit court `fait` + MAJ
  `project_sync_entries` ; échec → `echec`, `attempt_count += 1`, on
  continue. V2.1 : la reprise reparcourt `a_faire` **et** `echec` - un
  `echec` est réessayable dans le même plan, sinon l'at-least-once promis
  n'existait pas.
- Progression : compteurs du plan + état du ProcessingTask.

## API

- `PUT /api/projects/{id}/sync/racine` `{chemin}` / `DELETE` (ne retire rien
  de l'index).
- `POST /api/projects/{id}/sync/plan` → 200 plan + opérations (les plans
  `propose` antérieurs passent `caduc`). Fail-closed (422 avec cause lisible
  si racine absente/volume changé/scan en erreur).
- `POST /api/projects/{id}/sync/apply` `{plan_id}` → 202 ; 409 apply en
  cours ; 409 plan non-dernier ou caduc.
- `GET /api/projects/{id}/sync` → racine, dernier plan, compteurs, run.
- `GET /api/projects/{id}/sync/journal?page=` → opérations, récentes d'abord.
- Frontend : ces appels utilisent des **timeouts adaptés** (le défaut apiFetch
  de 30 s tuerait un plan sur un gros dossier) et l'apply se suit par polling.

## Interface (MVP)

Fiche projet, section « Dossier synchronisé » : choisir/retirer la racine ;
« Préparer la synchronisation » → plan (n nouveaux, n modifiés, n disparus,
n conflits, liste dépliable) ; « Appliquer » → progression ; journal.

## Séquencement de construction (validé au challenge V2)

1. Tests de caractérisation des appelants existants (route index, upload,
   trombone) ; 2. extraction des deux services ; 3. modèles + imports +
   Alembic (avec test de **bootstrap neuf** : `alembic/env.py` n'importe
   aujourd'hui ni `processing` ni les futurs modèles sync) ; 4. scanner/diff
   pur ; 5. persistance des plans ; 6. apply + reprise (indissociables) ;
   7. API puis interface.

## Tests exigés (au-delà du TDD usuel)

- crash simulé à CHAQUE frontière SQLite/Qdrant d'une opération → reprise
  restaure la cohérence sans doublon ni orphelin ;
- second plan sans changement = zéro opération ;
- fichier disparu au plan, revenu avant l'apply → `obsolete`, jamais retiré ;
- fichier > 1000 fragments → retrait complet (le plafond actuel) ;
- racine débranchée / permission refusée → plan en échec, zéro retrait ;
- chemin possédé par un autre périmètre → `conflit`, scope inchangé ;
- upgrade d'une base 0.44 réelle (Alembic + create_all déjà passés).

## Hors périmètre (explicite)

Watchers, multi-racines, racines partagées, fichiers hors racine, export de
trame, LLM, corbeille logique des métadonnées, historique par tentative,
application d'un plan ancien.

## Révision V2 - ce que le challenge a changé

1. Table d'état `project_sync_entries` ajoutée : `content_hash` n'était
   alimenté nulle part, aucun mtime persisté - le référentiel supposé
   n'existait pas (bloquant).
2. Services d'indexation et de retrait extraits en fondation : le verrou du
   routeur ne couvrait ni `upload_file` ni le trombone ; `delete_by_entity`
   plafonne à 1000 points et `delete_file` avale les erreurs Qdrant
   (bloquants).
3. Scope vérifié au retour d'`index_payload` : les paramètres sont ignorés
   pour un fichier déjà possédé → conflit visible.
4. Apply = ProcessingTask + task_registry existants (découverts au challenge),
   plus un simple asyncio.Task à référence forte.
5. Fail-closed partout : plan en erreur = zéro retrait, volume_id stocké,
   erreurs de parcours remontées, stat avant/après hash, revalidation à
   l'apply, seul le dernier plan est applicable.
6. Parcours Alembic complet + test d'upgrade sur base 0.44 réelle ; index et
   ménage delete_project explicites (FK non activées).
7. Journal réduit honnêtement (ProcessingTask + compteurs par opération),
   états `abandonne`/corbeille logique retirés, `caduc`/`obsolete`/`conflit`
   ajoutés.
