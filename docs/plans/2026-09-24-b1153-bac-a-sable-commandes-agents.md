# B-1153 : confiner les commandes des agents (design V4)

Statut : **V4, après trois revues adverses** (V1, V2 et V3 : NO-GO ; rapports
hors dépôt, scratchpad de la session du 24/09). Arbitrage de principe :
`docs/plans/2026-09-24-arbitrages-par-delegation.md`. Aucun code avant un GO
de revue.

## Ce que les revues ont corrigé

| Version | Affirmait | Le code ou la mesure dit |
|---|---|---|
| V1 | `run_command` tourne aussi sur `/spawn` | faux : `_PROFILE_DISABLED_MUTATION_TOOLS` (`routers/agents.py:69`, `:500`, `:602`) et le refus hors schéma (`runtime.py:187-192`) le coupent ; seule la mission Atelier l'exécute, dans un worktree jetable (`swarm.py:218-249`) |
| V1 | refuser la lecture de `~/.ssh` protège les clés | la commande signe par le socket de `ssh-agent`, joignable sous Seatbelt comme sous Landlock (mesuré) |
| V2 | le réseau peut rester ouvert (R2) | faux : le moteur écoute sur `127.0.0.1:17293` et `/api/auth/token` rend le jeton à tout appel sans `Origin` (`main.py:686-701`, exemption `:748-756`). Une commande confinée pilotait toute l'API, données déchiffrées comprises. **Le réseau est coupé en V3** |
| V2 | purge de l'environnement par liste noire | laisse passer `THERESE_DB_KEY` (clé SQLCipher de la base, `encryption.py:454-462`) ; B-250 avait déjà abandonné la liste noire pour le bac à sable des skills. **Liste blanche en V3** |
| V2 | `core.hooksPath=/dev/null` suffit pour git | les filtres (`filter.*.clean`) et `diff.*.textconv` de la configuration globale s'exécutent encore sur un `.gitattributes` écrit par l'agent |
| V2 | prototypes « validés » | ils utilisaient `assert` (supprimé sous `-O`, donc fail-open) et ne bloquaient ni `io_uring` ni les appels x32. Corrigé et remesuré en V3 |
| V3 | la commande est coupée des autres processus | les signaux n'étaient restreints nulle part : sous Seatbelt, une commande confinée a tué un processus extérieur (mesuré par la revue). La revue craignait aussi la lecture de `/proc/<moteur>/environ` et `ptrace` sous Linux ; **mesuré le 24/09 : Landlock les refuse déjà** (un processus confiné ne peut pas exercer d'accès de type ptrace hors de son domaine), le témoin non confiné lisant bien le secret. **Signaux restreints en V4**, `ptrace` refusé aussi par seccomp |
| V3 | cinq dossiers d'identifiants refusés en lecture (macOS) | `~/.netrc`, `~/.npmrc`, `~/.config/gh`, `~/.docker`, cookies de navigateurs restaient lisibles. **Liste étendue en V4** ; R1 requalifié |

## Le constat

La garde P-100 borne la ligne de commande, pas le code que la commande
exécute : `pytest.ini`, `conftest.py`, `package.json`, `vitest.config.ts`,
`Makefile` sont écrits par l'agent puis lus par `run_command`. C'est une
exécution de code choisie par le modèle ; l'avocat du diable de l'audit 0.75
l'a prouvé (un `--basetemp` hors du dépôt a vidé ce dossier).

Deuxième voie, **antérieure et hors `run_command`** : en fin de mission,
THÉRÈSE lance `git add -A`, `git commit` puis des `git diff` dans le worktree
(`swarm.py:311-334`, `git_service.py:197-251`), hors de tout confinement.
Les hooks du dépôt de l'utilisateur (`pre-commit` lit une configuration que
l'agent peut réécrire) et les pilotes de la configuration git globale
s'exécutent alors.

## Périmètre

- **Dedans** : `run_command` de la mission Atelier ; les commandes `git` que
  THÉRÈSE lance dans le worktree de mission.
- **Dehors, inchangé** : `/spawn` reste sans `write_file` ni `run_command`
  (test existant conservé) ; la fusion approuvée (`approve_task`), sur un diff
  relu par l'utilisateur, voir R6.

## Garanties de la V4

1. **Écriture confinée** au worktree de la mission, à un dossier temporaire
   neuf propre à la commande (`mkdtemp(prefix="therese-cmd-")`, retiré à la
   fin), et aux pseudo-fichiers `/dev/null`, `/dev/zero`, `/dev/urandom`,
   `/dev/fd/*` (pas `/dev/tty`, qui ouvrirait le terminal du moteur) ; sous Linux, aussi `/dev/shm` (sémaphores de
   `multiprocessing`, voir R9). `TMPDIR`, `TMP`, `TEMP`, `XDG_CACHE_HOME`,
   `XDG_DATA_HOME`, `UV_CACHE_DIR` et `npm_config_cache` pointent dans le
   dossier temporaire. Liens physiques, symboliques, renommages hors de ces
   dossiers : refusés (vérifié par la revue V2 sous Seatbelt).
2. **Aucun réseau.** Ni TCP, ni UDP, ni socket Unix, localhost compris : la
   commande ne joint ni Internet, ni l'API du moteur, ni `ssh-agent`, ni
   `docker.sock`. macOS : Seatbelt `(deny network*)`. Linux : seccomp refuse
   `socket()` pour toutes les familles (EPERM), `io_uring_setup` (EPERM, sinon
   `IORING_OP_SOCKET` contournerait le filtre) et tout appel x32 (bit
   `0x40000000`, EPERM). `socketpair` reste permis (tubes internes de Python
   et Node, `multiprocessing`).
3. **Environnement en liste blanche**, comme le bac à sable des skills
   (B-250) : `PATH`, `HOME`, `USER`, `LOGNAME`, `LANG`, `LANGUAGE`, `TZ`,
   `TERM`, `LC_*`, puis les variables de dossiers temporaires ci-dessus et
   `PYTHONDONTWRITEBYTECODE=1`. Rien d'autre : `THERESE_DB_KEY`, clés de
   fournisseurs, `SSH_AUTH_SOCK`, `PYTHONPATH` du moteur packagé n'y sont pas.
4. **Aucune prise sur les autres processus.** Signaux : la commande ne peut
   signaler qu'elle-même et ses descendants (macOS : `(deny signal)` puis
   `(allow signal (target self))` et `(target children)`, mesuré : enfant tué,
   processus extérieur refusé ; Linux : `LANDLOCK_SCOPE_SIGNAL` à partir de
   l'ABI 6, mesuré sur ABI 8). Lecture de l'environnement ou de la mémoire du
   moteur, `ptrace` : Landlock refuse tout accès de type ptrace hors du domaine
   (mesuré : `/proc/<moteur>/environ` EACCES, attache EPERM, le témoin non
   confiné lisant bien le secret) ; seccomp refuse en plus `ptrace`,
   `process_vm_readv`, `process_vm_writev` et `pidfd_getfd`. Sous macOS,
   `KERN_PROCARGS2` ne rend pas l'environnement d'un autre processus (mesuré
   par la revue V3).
5. **Descripteurs** : `close_fds=True` explicite ; le relais n'ouvre que des
   descripteurs non héritables (`O_CLOEXEC`) et les ferme avant `execvp`.
   Aucun socket déjà connecté du moteur n'est transmis.
6. **Git sans exécution de code du worktree ni de la configuration globale.**
   Toute commande `git` de THÉRÈSE dans le worktree de mission :
   - `GIT_DIR` et `GIT_WORK_TREE` explicites, le premier relevé par
     `git rev-parse --absolute-git-dir` à la création du worktree, avant que
     l'agent n'agisse (un `.git` réécrit est ignoré) ;
   - `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`, et l'identité
     relue à la création du worktree **avec l'environnement complet** (avant
     toute neutralisation : l'identité vit souvent dans `~/.gitconfig`), puis
     repassée par `-c` ; sans identité, la cause remonte comme aujourd'hui
     (B-376) ;
   - `-c core.hooksPath=/dev/null -c core.fsmonitor=false` ;
   - `diff` avec `--no-textconv --no-ext-diff`.
7. **Fail-closed de bout en bout.**
   - Aucune `assert` : chaque étape du confinement vérifie son code de retour
     et, en cas d'échec, écrit `THERESE-CONFINEMENT-ECHEC: <étape>` sur
     stderr puis `os._exit(97)`, avant `execvp`. Mesuré : dossier autorisé
     inexistant → code 97, commande non lancée.
   - `run_command` traduit le code 97 et ce marqueur en refus explicite.
   - **Sonde avec jumeau** au premier `run_command` du processus : la même
     commande témoin tourne une fois sans confinement (elle doit réussir à
     écrire son fichier témoin, à ouvrir un socket et à signaler un processus
     témoin extérieur) et une fois confinée (elle doit échouer sur les trois,
     avec EPERM ou EACCES ; sous Linux avant l'ABI 6, l'échec du signal n'est
     pas exigé et R11 est journalisé). Toute autre
     issue refuse `run_command` pour la vie du processus. La sonde ne prouve
     que ces trois points ; les autres garanties ont leurs tests.
   - Toute exception de préparation (mkdtemp, résolution, profil) refuse.
8. **Refus explicite** là où le confinement n'existe pas : Windows ; Linux
   sans Landlock (noyau < 5.13 ou désactivé), sans seccomp, ou hors x86_64 et
   aarch64 ; macOS sans `/usr/bin/sandbox-exec` ou dont la sonde échoue.
   Message : « Erreur : les commandes des agents sont désactivées sur ce
   système, faute de pouvoir les confiner (<raison>). L'agent peut toujours
   lire et modifier les fichiers de la mission. »

Défense en profondeur, macOS : lecture refusée du dossier de données de
THÉRÈSE et des identifiants usuels (`~/.ssh`, `~/.aws`, `~/.gnupg`,
`~/.docker`, `~/.kube`, `~/.config/gh`, `~/.config/gcloud`, `~/.netrc`,
`~/.npmrc`, `~/.git-credentials`, `~/Library/Keychains`, `~/Library/Cookies`,
`~/Library/Safari`, profils Chrome et Firefox) ; `(deny appleevent-send)` ; `(deny mach-lookup (global-name
"com.apple.pasteboard.1"))`, le presse-papiers (mesuré : `pbpaste` échoue).

## Mécanismes

**macOS, profil Seatbelt** (chemins passés par `-D`, jamais interpolés, et
résolus : `/tmp` y est `/private/tmp`) :

```scheme
(version 1)
(allow default)
(deny file-write* (subpath "/"))
(allow file-write* (subpath (param "DEPOT")) (subpath (param "TMP"))
       (literal "/dev/null") (literal "/dev/zero") (literal "/dev/urandom")
       (regex #"^/dev/fd/"))
(deny network*)
(deny appleevent-send)
(deny mach-lookup (global-name "com.apple.pasteboard.1"))
(deny signal)
(allow signal (target self))
(allow signal (target children))
(deny file-read* (subpath (param "DONNEES"))
       (subpath (string-append (param "HOME") "/.ssh"))
       ;; … même forme pour la liste de la garantie de défense en profondeur
       (literal (string-append (param "HOME") "/.netrc")))
```

Mesuré le 24/09 : `127.0.0.1:17293` et `1.1.1.1:53` refusés (EPERM),
`socketpair` intact, `pbpaste` en échec, identifiants et cookies refusés,
fichiers ordinaires du dossier personnel lisibles, `/dev/tty` refusé. Piège
appris : `(target pgrp)` laisse signaler tout le groupe du terminal ;
`(target others)` ne refuse rien sous `(allow default)`.

**Linux, relais Landlock + seccomp**, sans dépendance (appels système par
`ctypes`). Ordre, chaque étape vérifiée, sortie 97 sinon :
`PR_SET_NO_NEW_PRIVS` ; Landlock sur les droits d'écriture (ABI ≥ 1 ; `REFER`
si ≥ 2, `TRUNCATE` si ≥ 3 ; droits de fichier seulement pour les
pseudo-fichiers, sinon `EINVAL` ; `scoped = LANDLOCK_SCOPE_SIGNAL` si ≥ 6) ;
seccomp (`socket`, `io_uring_setup`, `ptrace`, `process_vm_readv`,
`process_vm_writev`, `pidfd_getfd`, appels x32) ; `execvp`. Prototype mesuré sur
DQ SYN (Ubuntu 24.04.4 LTS, noyau HWE `7.0.0-30-generic`, Landlock ABI 8,
`yama.ptrace_scope = 1`) : `socket` AF_UNIX, AF_INET et
AF_INET6 refusés (EPERM), `io_uring_setup` refusé (EPERM), `socketpair` et
`multiprocessing` intacts, écriture dans `~` et dans `/tmp` refusée (EACCES),
écriture dans le dépôt acceptée. Non exercé faute de noyau x32 : le refus du
bit x32 (inféré, par construction du filtre).

Le relais est un mode du moteur reconnu **par position** dans `main.py`
avant `argparse` : `argv[1] == "--therese-confiner"`, DEPOT, TMP, `--`, puis
la commande, jamais relue comme drapeau ; exclusif du relais
`multiprocessing` existant (`main.py:90-110`). En développement, le même
module (bibliothèque standard seule) est lancé par `python -I -c`.

Écartés : `preexec_fn` (non sûr avec des fils d'exécution), `bubblewrap`
(absent hors Ubuntu, restreint par AppArmor sur Ubuntu 24.04).

**Windows : refus.**

## Ce qui ne change pas

Garde P-100 (refus tôt et lisible), `_validate_path` de `write_file` (qui
refuse `.git`), délai de 120 s, arrêt du groupe de processus, sortie tronquée
à 5 000 caractères.

## Mesure de référence : la suite de THÉRÈSE confinée (macOS, profils V3 et V4)

Arbre jetable à 57304c07, environnement réduit à `PATH`, `HOME`, `LANG` et
aux variables de dossiers temporaires, réseau coupé :

| Suite | Résultat |
|---|---|
| pytest (hors e2e) | 3 497 tests, 1 échec, 4 sautés (V3 comme V4) |
| Vitest | 2 729 tests, 0 échec (V3 comme V4) |

Le profil V4 ajoute la restriction des signaux, retire `/dev/tty` et étend la
lecture refusée : même résultat, aucune régression.

Le seul échec lisait le vrai `~/.therese` de la personne qui lance les tests :
défaut du test, corrigé depuis (3a890e98, `HOME` jetable). La mesure Linux
des deux suites sous le relais fait partie des tests (cas 11).

## Tests (TDD)

Rouges d'abord, sabotage qui les refait rougir. Cas 1 à 10 sur la CI Linux et
macOS, sautés ailleurs ; cas 12 sur les trois systèmes.

1. **Le cas de l'audit** : `pytest.ini` avec `--basetemp` hors worktree,
   `run_command("pytest -q")` : le témoin existe toujours.
2. **`conftest.py` qui écrit dans `/tmp/<nom>` et dans `$HOME`** : refusé.
3. **Témoin positif** : la même commande écrit dans le worktree et son
   dossier temporaire, et réussit.
4. **Environnement** : `THERESE_DB_KEY`, `FAUX_API_KEY` et `SSH_AUTH_SOCK`
   posés dans le moteur sont absents de l'environnement de la commande.
5. **Réseau** : un serveur témoin écoute sur `127.0.0.1` (port libre) et un
   socket Unix témoin hors worktree ; la commande n'ouvre ni l'un ni l'autre.
6. **Git** : la commande réécrit `<worktree>/.git` vers un faux dépôt complet
   (hook `pre-commit` qui crée un témoin), pose un `.pre-commit-config.yaml`
   et un `.gitattributes` qui route un fichier vers un pilote `filter` et un
   `textconv` définis dans un faux `~/.gitconfig` (qui créent un témoin) ;
   puis `commit` et `diff_files` : aucun témoin, commit sur la vraie branche,
   avec l'identité de l'utilisateur.
7. **Relais en échec** (Linux) : DEPOT inexistant → code 97, commande non
   lancée, refus lisible ; même chose sous `PYTHONOPTIMIZE=2`.
8. **Sonde** : confinement simulé inefficace (profil vide injecté par le
   test) → `run_command` refusé ; témoin qui échoue pour une autre raison que
   le confinement (dossier absent) → refusé aussi (jumeau non confiné).
9. **Dossier temporaire** retiré après la commande, délai dépassé et
   annulation compris.
10. **Descripteurs** : un socket connecté ouvert dans le moteur n'apparaît
    pas dans `/proc/self/fd` (Linux) ou `lsof -p` (macOS) de la commande.
10b. **Autres processus** : la commande ne tue pas un processus témoin
    extérieur, tue son propre enfant ; sous Linux, `/proc/<moteur>/environ`
    (moteur lancé avec un faux `THERESE_DB_KEY`) et `ptrace` sont refusés,
    avec un témoin non confiné qui, lui, lit le secret.
10c. **Identité git seulement globale** : sous `GIT_CONFIG_GLOBAL=/dev/null`,
    le commit de mission réussit avec l'identité relue à la création.
11. **Dogfooding** : les suites pytest et Vitest de THÉRÈSE passent sous le
    confinement, sur macOS (mesure ci-dessus) et sur Linux (DQ SYN).
12. **Refus** sur plateforme sans confinement : rien lancé, message exact.
13. Gardes textuelles : `run_command` ne crée un processus qu'à travers le
    confinement ; `GitService` en mode mission passe toujours `GIT_DIR`,
    `GIT_CONFIG_GLOBAL` et `core.hooksPath`.

## Risques résiduels, numérotés

- **R1, lecture** : sous Linux (aucun refus de lecture), et sous macOS hors
  de la liste refusée, la commande lit les fichiers de l'utilisateur, y
  compris un identifiant rangé ailleurs, et peut les recopier dans sa sortie
  (5 000 caractères au plus), qui revient au modèle. Sans réseau, c'est la
  seule sortie ; elle existe aujourd'hui aussi par `read_file`.
- **R2, tests qui ont besoin du réseau** : ils échouent sous confinement.
  La suite de THÉRÈSE n'en a pas (mesuré). Assumé.
- **R3, Seatbelt obsolète** : s'il disparaît, la sonde échoue et
  `run_command` se refuse.
- **R4, Windows** : plus de commandes d'agent. Perte assumée (arbitrage).
- **R5, processus détachés** : un démon lancé par la commande survit à
  l'arrêt du groupe s'il change de session ; il reste confiné (héritage).
- **R6, fusion approuvée** : la fusion dans le dépôt de l'utilisateur exécute
  ses hooks sur le contenu de la mission. C'est un diff relu ; l'écran
  d'approbation devrait signaler un changement de configuration d'outil
  (`.pre-commit-config.yaml`, `Makefile`, `package.json`, `pytest.ini`,
  `.gitattributes`). Proposition à part.
- **R7, pilotes git de la configuration du dépôt** : `GIT_CONFIG_GLOBAL` et
  `NOSYSTEM` écartent les configurations globale et système ; celle du dépôt
  de l'utilisateur reste lue (git-lfs, par exemple). L'agent ne peut pas
  l'écrire (hors worktree), il peut seulement y router un fichier.
- **R8, services mach sous macOS** : `mach-lookup` reste ouvert, sauf le
  presse-papiers. La revue a tenté trois évasions par un autre processus
  (AppleEvent, `launchctl submit`, `open`) : toutes bloquées.
- **R9, `/dev/shm` sous Linux** : écrivable pour `multiprocessing` ; une
  commande pourrait y effacer les segments de mémoire partagée d'un autre
  programme (plantage de ce programme, pas de perte de document).
- **R11, signaux sous Linux avant l'ABI 6** (noyaux antérieurs à 6.12) :
  sans `LANDLOCK_SCOPE_SIGNAL`, la commande peut tuer les processus de
  l'utilisateur, moteur compris (perte de la session, pas de document). La
  sonde le détecte et le journal le dit ; pas de refus, qui exclurait la
  plupart des distributions stables.
- **R10, l'API du moteur sans confinement** : hors de ce chantier, tout
  processus local qui ne passe pas par le bac à sable obtient le jeton par
  `/api/auth/token` (choix documenté en `main.py:688`). Le bac à sable
  coupe cette voie pour les commandes d'agents ; la question générale est
  notée à part.
