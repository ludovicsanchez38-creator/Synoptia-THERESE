# Constructeur physique FULL A/B proposé

Auteur : `/root/shared4_execution`. Préparation seulement. Aucun checkout,
root A/B, admission, GO, Session, browser ou workload n'a été construit/lancé
par ce lot. Les anciens gels et le dépôt sont inchangés.

Le HEAD documentaire courant transmis par MAIN est
`d1486c2ad1d1879b1c10196fe269e16b35b85e6e`. Il n'est pas une valeur par défaut
du constructeur et aucune source QA actuelle n'est revendiquée ici. HEAD2d69
des définitions WRAPPER et HEAD19979 de la précédente source A/B restent des
origines historiques, jamais une admission sur ce HEAD courant.

## Entrées et commande future

`build_full_round.py` n'importe ni G1 ni produit. Il ne lance pas Git, Node,
codesign, Popen, libproc, socket ou Chrome. Ses deux modes relisent d'abord les
preuves root avant toute allocation. Sans autorisation physique externe exacte,
il refuse. Sans `--construct`, il n'émet aucune racine.

```text
<Python-stdlib-pinné> -I -B build_full_round.py
  --request-ref '{"path":"<request-root-physique>","sha256":"<SHA64>","bytes":<int>}'
  --authority-ref '{"path":"<Q/décision-construct-root>","sha256":"<SHA64>","bytes":<int>}'
  [--construct]
```

Cet appel n'a pas été exécuté. La requête réelle doit avoir le schéma
`c17-full-ab-construction-request-v1` et les champs suivants :

| Champ | Contrôle |
| --- | --- |
| `root`, `campaign`, `actor` | `/private/tmp/therese-c17-direct-round-[ab]-12hex`, absent, campagne concordante, acteur canonique réel autorisé |
| `other_round` | `{root,actor,campaign,expected_head}`, autre campagne, autre root et autre acteur ; aucun override déclaratif |
| `expected_head`, `qa_source` | HEAD40 explicite, source physique `therese-c17-direct-source-*/source` ; pas de HEAD vivant inventé |
| `ports` | Objet exact `{backend:17593,frontend:5173,cdp:17594}` ; toute autre valeur refusée |
| `git_head_ref`, `git_commit_ref`, `git_tree_ref`, `git_manifest_ref` | Refs exactes `{path,sha256,bytes}`, raw root concordants ; commit SHA1, tree reconstruit, blobs/modes/liens et corps sources rehashés ; aucun hardlink source |
| `python_audit_ref`, `node_audit_ref` | Audits physiques du même source/HEAD, locks/package metadata/pth/graph ; ensemble `.pth` exact |
| `copied_chrome`, `chrome_tree_ref`, `chrome_signature_ref` | Copie QA explicite, 1339 entrées physiques exactes, octets/modes/UID/GID/dev/inode/liens ; codesign réel root rc0 avec refs et âge ≤120 s ; aucun lancement par le constructeur |
| `profiles` | Trois refs `web/sql/chrome` revues root ; octets copiés sans dérivation ni compilation |
| `session_contract_ref` | Définition ABI Session physique et relue avec `features` ; pin `module` dérivé vers la copie, sans admission implicite |
| `rpc_contract_ref` | Contrat exact du composite déjà pinné par assets ; seul son pin lecteur est dérivé, les 16 exigences restent inchangées |

L'autorisation `c17-runtime78-successor-admission-v1`, phase `construct`, reste
externe sous Q. Elle doit joindre les pins effectifs `constructor`,
`definition_assets`, `construction_request`, `identity_registry`, les origines
réelles des deux acteurs, `root_review_origin`, `reviewed_profiles`,
`source_proofs`, `issued_at` et `expires_at` (TTL ≤3600 s). Le module ne l'émet
jamais. Les chaînes JSON ne prouvent ni autorisation humaine ni auteur OS :
MAIN doit vérifier les vraies origines/outils hors de ce code.

## Rendu physique futur

Le rendu fermé réutilise 88 sources exactes de définitions : composite A/B,
wrappers RPC corrigés, port CDP/Git/listener et table78. Les différences de
chaque définition finale sont enregistrées avec préimage byte-exacte et diff.
Les résultats/calibrations historiques ne sont jamais copiés comme preuves.
Les dix espèces B1760 sont des définitions filtrées, pas les anciens exports.

Les dérivations fonctionnelles proposées sont bornées : import `uuid` de G1,
HEAD/QA/Chrome explicites, profils exacts paramétrés, sept ancres identité v2,
Vite canonique du checkout QA, préparation du manifeste sans legacy start/stop,
pins lecteurs ABI sur les octets rendus et ajout Git Node après le port A/B CDP.
Les scénarios, oracles, codes métier, timeouts et types de contrôle existants
sont conservés. Les pures rendent les vrais textes et la vraie blueprint.

Le constructeur émettrait config/frozen-inputs, source-files/source-checkout,
raw Git déjà observés par root, scripts/transport/G1/profils, manifest `prepared`,
quatorze contextes Chrome sans birth, et les canaux `session-events` et
`session-rpc`. Les allocations/sinks restent exclusifs. Un échec d'émission
laisse les fichiers partiels intacts, sans overwrite ni reprise automatique.

Les quinze descriptors ne sont pas fabriqués avec un owner futur : les vrais
bindings/plan/enveloppes et le peer doivent être scellés par le bootstrap ROOT
vivant après les contrôles/admissions nécessaires. Les trois parents SQL
restent tardifs, après vraie revue du contrat courant. Le helper
`requester_spec` vérifie leur argv/env complet avant revue/binding. Aucun PID,
deadline monotonic futur, running/stopped/ACK ou scan ne sort de ce constructeur.

## Mesures pures et limites

Mesure finale : 51 tests PASS, zéro failure/error/skip, sources avant/après
égales. Reçu `proofs/pure-qc5aaeit/receipt.json`, sinks directs stdout/stderr.
Les fixtures Git/Chrome/signature/enrollment sont explicitement synthétiques.
Le vrai `calibrate-all` est parcouru contre un transport double ; aucune des
15 feuilles réelles n'est lancée. Les tests ne qualifient pas Chrome, G1,
confinement OS, identité peer, A/B, runtime78 ou FULL.

Trois essais préalables rouges sont conservés :

1. `abd8b8`, code5, zéro test exécuté : le source écran portait encore les sept
   anciennes ancres. Le port v2 exact a été ajouté, source avant conservée.
2. `b9cde6`, code5, zéro test exécuté : fixture sans `chrome_tree_ref`.
3. `4f7dc5`, code1, zéro test exécuté : fixture sans `python_audit_ref` ; reçu
   et sinks directs `proofs/pure-3osto88c` conservés.

Les deux premiers logs sont copies du texte réellement retourné par l'outil,
pas des sinks directs rétroactivement créés. Les passages 40/49 antérieurs
restent séparés de la suite finale51. Aucune donnée manquante n'est complétée.

Conditions encore bloquantes avant runtime : nouvelle source QA/dépendances
et raw Git réellement capturés au HEAD choisi, profils et Chrome explicitement
revus/qualifiés, vraie autorisation externe de construction, ABI Session
complète et admission G1 A/B courante, table/plan15/bindings14/enrollments issus
du root vivant, origin/auth peer réel, trois revues SQL tardives/Q post-STOP.
G1/core gardent RUNTIME/OS/caps false et tables d'admission vides. Il faudra un
nouveau gel/admission root explicite pour ouvrir leur exécution, pas modifier
une copie fermée par un simple booléen de l'auteur.

Les rechecks dépendances sont metadata/locks/pth/versions/graph, pas une
comparaison de chaque corps des 149/427 paquets. Le scan Chrome physique ne
remplace pas la signature réelle ni le reçu lifecycle avant ACK. Les polling
et le watchdog coopératif ne prouvent pas une préemption hard-realtime ou une
attribution atomique de tous les forks/PID reuse.

Le package conserve ses 78 obligations, 84 captures inspectées, 10 PDF réels,
six calibrations courantes, cinq contextes métier et huit logs. Deux vraies
rondes par des acteurs distincts et les autres gates FULL restent requises.
`FULL=False`, `release=False`, zéro ronde comptée dans ce lot.
