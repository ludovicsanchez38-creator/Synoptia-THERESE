# Constructeur physique FULL A/B v3 proposé, préparation seulement

Auteur du gel v1 : `/root/shared4_execution` ; corrections v2/v3 :
`/root/environment_routes`. Préparation seulement. Aucun checkout,
root A/B, admission, GO, Session, browser ou workload n'a été construit/lancé
par ce lot. Les anciens gels et le dépôt sont inchangés.

Préimages v1 et v2 exactes sous `preimages-v1/` et `preimages-v2/` ; gels
originaux `/private/tmp/therese-c17-full-physical-builder-LVOOtP/INDEX.json`
et `/private/tmp/therese-c17-full-physical-builder-v2-dxGPne/INDEX.json`.
Les huit fichiers de diff direct/inverse de v2 restent historiques ; les
nouveaux diffs v3 sont sous `diffs-v3/`. Les reçus sous `proofs/` antérieurs
au v3 sont des copies historiques et ne lui sont pas réattribués. Le rouge
v2 `proofs/pure-huatyyse/` demeure conservé.

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
| `profiles` | Trois refs `web/sql/chrome` revues root ; octets copiés sans dérivation ni compilation. Chrome doit contenir exactement un `(param "AUXILIARY_PARENT")`. |
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
chaque définition finale ordinaire sont enregistrées avec préimage byte-exacte
et diff. Exception volontaire : le B1760 brut C16 contient
`four_historical_runs` ; la racine A/B reçoit seulement sa projection de
définition, ni préimage ni diff brut. La source C16 reste hors de la ronde,
référencée par SHA/bytes dans `assets.json` et `full-construction-origin.json`.
Les résultats/calibrations historiques ne sont pas copiés comme preuves.
Les dix espèces B1760 sont des définitions filtrées, pas les anciens exports.

Les dérivations fonctionnelles proposées sont bornées : import `uuid` de G1,
HEAD/QA/Chrome explicites, parent `root/auxiliary` injecté uniquement dans la
branche Chrome avec ancre réversible, profils exacts paramétrés, sept ancres identité v2,
Vite canonique du checkout QA, préparation du manifeste sans legacy start/stop,
pins lecteurs ABI sur les octets rendus et ajout Git Node après le port A/B CDP.
V3 porte séparément le seul delta WRAPPER14 `MAC_CHROMIUM_TMPDIR` au contrat A/B :
garde `validate_environment` pour `mode=chrome`, racine canonique
`/private/tmp/therese-c17-direct-round-[ab]-12hex` et les 14 noms exacts de
`ab_aux.NAMES.values()` ; valeur obligatoire identique à `TMPDIR` et à
`root/auxiliary/<nom>/tmp`, répertoire canonique existant. Aucun ajout aux
ensembles globaux d'environnement ni aux services, parents, feuilles ou
WRAPPER historiques. Le constructeur futur crée les 14 répertoires privés ;
`authorization/auxiliary-definition-table.json` émet leurs 14 paires de clés
requises, mais pas des descriptors ou un owner futur. Le binding root réel doit
ensuite émettre l'environnement complet et G1 le compare avant FD/Popen.
L'origine du port est le gel WRAPPER14 `INDEX.json` SHA
`e135223b023a771e3080f7ecb280ad350098783afbeeb5133d3221b6880ed7e6`.
Ses cinq stages et sa racine littérale ne sont pas relabellés A/B ; le corps
du garde est une adaptation distincte.
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

Mesure v3 finale : 59 tests PASS, zéro failure/error/skip, sources avant/après
égales. Reçu `proofs/pure-2wzrd2kw/receipt.json` SHA
`9f05193bfb8d037c5dc0d6062fd8c44afb344c771c3604779e18dcf73d31f5d0` ;
les trois passages v3 antérieurs restent historiques dans `proofs/pure-j9kr70rk`,
`proofs/pure-00ppkkdo` et `proofs/pure-kjg8ip5s`.
Les sinks stdout/stderr sont directs. V2 a séparément 55 tests PASS, reçus historiques
`proofs/pure-093gk8e_/receipt.json` et root `proofs/pure-d7jzy2lq/receipt.json`.
L'acteur `/root/environment_routes` a été explicitement passé à `run_pure.py --actor`.
Ce champ est une déclaration CLI et ne prouve ni autorité root ni acteur OS.
Rejeu futur de la même suite : `python3 -I -B run_pure.py --actor /root` depuis
ce dossier, avec nouveau reçu et sources avant/après ; ne pas réétiqueter
le reçu auteur ni celui de cette revue.
Les fixtures Git/Chrome/signature/enrollment sont explicitement synthétiques.
Le vrai `calibrate-all` est parcouru contre un transport double ; aucune des
15 feuilles réelles n'est lancée. Les tests ne qualifient pas Chrome, G1,
confinement OS, identité peer, A/B, runtime78 ou FULL.

Trois essais v1 préalables rouges sont conservés comme historique copié :

1. `abd8b8`, code5, zéro test exécuté : le source écran portait encore les sept
   anciennes ancres. Le port v2 exact a été ajouté, source avant conservée.
2. `b9cde6`, code5, zéro test exécuté : fixture sans `chrome_tree_ref`.
3. `4f7dc5`, code1, zéro test exécuté : fixture sans `python_audit_ref` ; reçu
   et sinks directs `proofs/pure-3osto88c` conservés.

Le v2 conserve aussi `proofs/pure-huatyyse/receipt.json` : zéro test exécuté,
ancre Chrome initialement ambiguë avec la boucle Q. L'ancre a été resserrée
sur l'`else` Chrome exact avant le PASS 55. Les deux premiers logs v1 sont
copies du texte réellement retourné par l'outil,
pas des sinks directs rétroactivement créés. Les passages 40/49 antérieurs
restent séparés de la suite finale51. Aucune donnée manquante n'est complétée.

Conditions encore bloquantes avant runtime : nouvelle source QA/dépendances
et raw Git réellement capturés au HEAD choisi, profils et Chrome explicitement
revus/qualifiés, vraie autorisation externe de construction, ABI Session
complète et admission G1 A/B courante, table/plan15/bindings14/enrollments issus
du root vivant, origin/auth peer réel, trois revues SQL tardives/Q post-STOP.
Le diagnostic ROOT13 sur `MAC_CHROMIUM_TMPDIR` est un raccord d'environnement
encore à éprouver séparément ; v3 prépare seulement sa transmission A/B et ne
présente pas le profil Chrome ni le canari WRAPPER14 comme qualifiés pour A/B.
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
