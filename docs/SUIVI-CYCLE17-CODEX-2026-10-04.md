# Cycle 17 Codex, ouvert le 4 octobre 2026

Le message de Ludo « Et cycle suivant » autorise ce cycle, directement sur le Mac.
Le départ est `b517daedc45480e5191eac5e37cdc6c2bf111cc4`, sur `codex/cycle-17`.
La release distribuée 0.77.2-alpha provient de `1fb934ff7e82086f3b06d90c5abedaf5f36b7e33` ;
les sources produit de ce départ sont identiques. Son bilan reste dans
[le rapport de release](releases/v0.77.2-alpha.md).

Le cycle 16 a livré sa release par le workflow autorisé après expiration de son
budget autonome. Sa phase persistante restait HUMAN_GATE. Le démarrage du 17 a
utilisé `new-cycle`, sans inventer des transitions POST_RELEASE ou RESTART et
sans forçage. Les anciens compteurs et preuves sont conservés. Le nouveau budget
opérationnel de 48 heures commence à 16:14:30 UTC ; il ne constitue pas une durée
promise ni une autorisation de publication. Preuves locales :
`.app-loop/cycles/17/start/authorization.json` et `start/cycle16-before/`.

## Cadre et instruments

Les données, profils, ports et preuves QA sont distincts du profil réel. Aucun
UTM ni VM. Les nouvelles fonctionnalités et la release suivante conservent
leur portail humain. La calibration et les deux rondes doivent être rejouées
au cycle 17. Une préparation, un build ou une ancienne ronde ne valent pas une
nouvelle validation UI.

La cartographie différentielle relève cinq fichiers modifiés :
`src/backend/app/__init__.py`, `src/backend/app/config.py`,
`src/frontend/package.json`, `src/frontend/src-tauri/Cargo.toml` et
`src/frontend/src-tauri/tauri.conf.json`. Deux lecteurs Codex indépendants
sont chargés de leur lecture. Le mapper initial échoue sur le lien de dossier
`.venv` ; la copie corrigée déjà vérifiée au cycle 16 réussit le refresh.
Source, empreinte et retour rouge puis vert : `.app-loop/cycles/17/map/`.
Le script Claude canonique reste inchangé.

La garde de comptabilité adaptée à Codex, approuvée par Ludo le 2 octobre,
est réutilisée sans modification dans `.app-loop/cycles/17/tools/app_loop-codex.py`.
Elle conserve le refus zéro tokens, la couverture complète et les autres portes.
Le compteur historique de transitions forcées reste 23. Les rôles indépendants
emploient GPT ; aucune diversité externe ni utilisation de Claude n'est affirmée.
Les tokens saisis au budget sont des estimations explicitement nommées.

## État au démarrage

Phase MAP, zéro nouvelle ronde propre sur deux. Préparation des instruments QA
à partir des sources courantes et de dépendances isolées déjà présentes.
Aucune calibration 17, aucun bug corrigé ni aucune publication 17 n'est encore
revendiqué. Les résultats suivants seront consignés ici après observation.

## Reprise du 6 octobre

Le GO de Ludo « ok la suite? » reprend le cycle existant. Une nouvelle fenêtre
opérationnelle de 48 heures est choisie, en conservant le départ, les usages,
les preuves et les compteurs. La sauvegarde avant reprise reste sous
`.app-loop/cycles/17/reprise-2026-10-06/`. Ce GO ne publie pas une version.

Une revue indépendante a revérifié les empreintes des 2 122 fichiers de la
carte : aucune différence ni absence, couverture 100 %. Les 111 divergences
historiques ont chacune un dernier arbitrage concordant. Les huit rapports C17
n'ouvrent aucun risque haut ou critique ; les deux risques moyens sur le
fallback de configuration et la CSP loopback restent à reproduire.
La transition normale MAP vers CALIBRATE réussit, sans forçage.

L'ancien dossier temporaire QA a disparu. Les sources sont donc reconstruites
par archive Git exacte et les seules dépendances locales sont copiées dans une
racine jetable neuve. La revue native retient encore le lancement : la politique
doit refuser toute écriture directe hors QA et être éprouvée par un témoin
extérieur qui ne bénéficie pas d'une interdiction nominative. Aucun nouveau
build, lancement ou résultat de calibration n'est encore attesté à cette étape.

## Résultats observés le 6 octobre, 19:36 UTC

La phase persistante reste CALIBRATE et le compteur reste à zéro ronde propre.
Les constats ci-dessous remplacent l'état provisoire de la reprise, sans
modifier les sources produit ni les résultats des cycles précédents.

### Application native et dépendances

Une app QA reconstruite depuis le départ exact a été lancée deux fois, avec
un identifiant macOS, un HOME, un dossier de données et le port 17594 réservés
au test. Les seules adaptations de sources dans cette archive jetable portent
sur ces paramètres et la désactivation du nettoyage global des backends.
Le profil synthétique et le dossier de travail QA persistent après fermeture
puis relance. Les groupes de processus attribués et le listener sont absents
après le second arrêt. Les captures, appels API, empreintes, contrôles de garde
et la contradiction indépendante sont conservés sous
`.app-loop/cycles/17/calibration/native/qualification-native.json`, avec son
complément additif `probe-history-complement/qualification-complement.json`.

Cette qualification reste bornée : la console JavaScript native n'a pas été
collectée, les logs combinés contiennent deux mentions de force kill et aucun
arrêt intégralement gracieux n'est affirmé. Le confinement global des échanges
XPC du sélecteur macOS n'est pas démontré. Ces deux lancements ne sont pas deux
rondes de plateau. Le backend embarqué copié depuis l'app installée possède
une empreinte attestée ; cela ne prouve pas la parité de ses dépendances avec
le nouveau venv Python.

Les dépendances copiées initialement ne correspondaient pas toutes aux locks.
La copie QA frontend a été réconciliée par npm ci hors ligne : 427 paquets,
aucun écart de version. Un venv neuf a été construit avec UV et le lock figé,
sans projet éditable : 149 distributions, aucun écart, aucun .pth éditable
extérieur et contrôle frozen réussi. L'essai hors ligne incomplet est conservé
avant la récupération des roues verrouillées sur le registre officiel. Les
venvs et node_modules d'origine sont préservés.

### Portes statiques et suites exécutées

Les commandes utilisent une archive indépendante des 3 578 fichiers suivis,
au même HEAD, avec contrôle des empreintes et de l'index avant et après.

| Vérification | Résultat observé |
| --- | --- |
| Ruff, TypeScript, ESLint et build Vite 7.3.6 | Réussite |
| Vitest | 3 442 cas distincts réussis, zéro échec et zéro skip |
| Pytest général sous garde OS | 4 323 réussites, 4 skips, zéro échec sur 4 327 cas distincts |
| Complément Pytest Seatbelt | 15 cas encore non exécutés |
| Mypy | Échec, 937 diagnostics ; liste identique à la référence C16 vérifiée |

Les 7 765 réussites exécutées n'incluent ni les skips, ni les sous-tests
délégués, ni les contrôles de calibration. Mypy n'est pas déclaré vert et la
suite backend n'est pas encore complète. Preuves du lot général :
`.app-loop/cycles/17/full-suite/therese-c17-full-suite-ps_tgzy5/`.

Une sandbox macOS imbriquée échoue avant d'exercer le produit. Les 15 cas
concernés sont donc réservés à un harnais spécialisé relu, qui conserve les
vrais profils Seatbelt enfants et les assertions d'origine. Son parent Python
est audité, pas confiné par l'OS. Sa calibration du 6 octobre, 19:36 UTC, passe
15 contrôles réels, y compris le témoin libre et le profil volontairement
inefficace. Aucune source n'a changé ; aucun alias, listener ou enfant QA ne
reste actif. Le GO pour les tests dépend d'une nouvelle lecture indépendante
de ce reçu, pas de son seul code retour.

### Calibration navigateur en cours

Les essais rouges sont conservés et leurs causes distinguées des défauts
produit : versions des outils, chargement de configuration Vite, origine CORS
et attente de chargement inadaptée au polling. Le frontend QA utilise désormais
5173, une origine admise par le produit, et le backend isolé 17593. Le port réel
17293 n'est pas utilisé.

Dans le contexte exact du contrôle écran, l'app est montée à 15 secondes mais
le pont d'actions n'est prêt qu'à 30 secondes ; aucune erreur console ni
réponse CORS refusée n'est observée dans cette sonde. Les attentes QA sont
ajustées sur ces mesures et une nouvelle campagne de calibration est ouverte.
Les parcours métier, la couverture visuelle et les deux rondes indépendantes
restent à exécuter après calibration valide. Aucun bug produit nouveau,
correctif produit, plateau ou publication n'est revendiqué à cette étape.

## Passage à DISCOVER, 6 octobre, 19:47 UTC

Après lecture des contrôles bruts et inspection des deux captures par root,
les cinq axes obligatoires ont été inscrits avec leurs empreintes et une
validité de 24 heures. `calibration-status` renvoie PASS et la transition
normale CALIBRATE vers DISCOVER réussit. Les 71 fichiers probatoires de la
campagne F sont conservés sous `.app-loop/cycles/17/calibration/web-F/` ;
leur inventaire SHA a été vérifié. Le résumé agrégé de F reste rouge.

Cette distinction est importante : l'instrument additionnel `screen_coverage`
dépasse son watchdog de 180 secondes après la capture de l'accueil. Il n'est
pas inscrit comme vert et reste une condition manquante de la couverture et
du plateau. Le gate des recettes agrégées reste fermé. Une campagne ciblée
ajoute seulement des jalons et conserve les flux partiels pour mesurer cette
cause, sans réduire la liste des gestes ni modifier les assertions.

Le second passage des 15 cas Seatbelt possède un reçu interne complet : la
procédure canonique `pytest_sessionfinish` est mesurée avant son véritable
`os._exit`, avec le même code de sortie. Le premier passage sans reçu final
est conservé mais exclu du décompte qualifié. La contradiction finale et la
consolidation sans doublon avec le lot général restent à terminer. Les tests
TAP de l'instrument écran font l'objet d'un lot distinct sur HTML synthétique,
sous garde OS ; ils ne qualifient pas l'interface THÉRÈSE.

Le compteur reste à zéro ronde propre. Aucune transition forcée nouvelle,
publication ou utilisation du profil réel n'est effectuée.

## Suites consolidées et diagnostic écran

La contradiction du complément Seatbelt est terminée : 15 identités exactes,
zéro échec, erreur ou skip, finalisation canonique mesurée, sources inchangées
et aucun processus, port ou alias attribué restant. Les deux calibrations et
les deux passages sont préservés additivement ; seul le second passage complet
entre au décompte. Preuve :
`.app-loop/cycles/17/full-suite/specialized/qualification-specialized.json`.

L'union backend est bijective avec la collecte des 4 342 cas : 4 338 réussites
et les quatre skips exacts. Les 3 442 réussites frontend sont distinctes et
sans skip. Les 20 tests TAP de l'instrument sont verts, sur HTML synthétique
avec Chromium headless et garde OS, sans être une ronde de l'app.
La consolidation est dans `.app-loop/cycles/17/qualification/backend-union.json`
et `consolidation-current.json`. Les 129 sélecteurs unitaires requis sont tous
présents et verts ; leur présence ne remplace pas les liaisons d'exécutants
ni les reçus runtime manquants.

La revue root a ensuite relié les 129 obligations aux vrais appels
collaboration, bruts, logs, sources et approbations individuelles. Le contrôle
unitaire seul accepte les 129 positifs et refuse les 48 contrôles altérés
sur copies. Les 415 originaux rehashés sont inchangés. Reçu :
`.app-loop/cycles/17/qualification/unit-consumer-calibration-20261006T201246.771777Z/receipt.json`.
Ce contrôle ne qualifie ni FULL, ni l'interface, ni une ronde.

La campagne diagnostique G est rouge et arrêtée. Les flux partiels montrent
22 interactions recensées en 1,04 seconde, puis des réouvertures complètes
de 35 à 38 secondes ; le watchdog coupe au geste 7. Les réouvertures qui
suivent un changement d'état servent à l'indépendance des gestes et ne sont
pas retirées. L'archive avec empreintes est sous
`.app-loop/cycles/17/calibration/web-G/`.

La sonde H a mesuré 970 scans globaux synchrones `lsof`, pour 39,369 secondes
cumulées pendant une seule ouverture. Le chargement et l'attente du pont QA
sont presque entièrement occupés par ces scans. La cause mesurée est notre
garde-fou de test, pas un bug produit établi. La pile H est arrêtée et ses
reçus restent sous `.app-loop/cycles/17/calibration/web-H/`.

La copie QA I a vérifié un contrôle asynchrone conservant le scan global et
le refus des listeners étrangers. Seules les requêtes déjà en attente peuvent
partager un scan en cours ; aucun résultat n'est mis en cache. Les contrôles
simulés et le vrai scan avec PID attendu volontairement erroné sont verts.
L'ouverture comparable passe d'environ 44 à 9 secondes, avec 48 scans au
lieu de 970. La pile I est arrêtée ; les deux scripts interrompus pendant
les navigations restent observés et ne sont pas assimilés à une couverture
complète. Reçus sous `.app-loop/cycles/17/calibration/web-I/`.

Ce seul delta de garde est intégré dans le générateur QA pour une campagne J
fraîche. Sa calibration agrégée complète passe réellement, de 20:14 à 20:18 UTC :
les six outils détectent les témoins injectés et les témoins sains sont verts.
Le défaut visuel est absent des captures avant injection et après restauration.
Les bruts et leur inventaire vérifié restent sous
`.app-loop/cycles/17/calibration/web-J/`. Root inscrit les six calibrations
à 20:33 UTC, pour 12 heures, sans forçage. Les labels d'acteur des bruts restent
inchangés ; cette campagne de découverte ne devient pas implicitement une
ronde FULL runtime78.

Les recettes J navigation, facturation et CRM passent, avec respectivement
trois, cinq et deux assertions métier. Les captures et les bruts sont relus
par root. Aucun appel extérieur, téléchargement, popup ou accès au port réel
n'est observé dans ces recettes. La couverture complète des écrans en clair
et sombre, à 1 440 et 800 pixels, se termine avant son watchdog de 1 500
secondes : 21 écrans par combinaison, 84 captures. Seule la combinaison
1 440 pixels claire déroule les 265 gestes du protocole ; les trois autres
restent des parcours visuels statiques. Les 44 anomalies brutes se dédupliquent
en 17 candidats, dont 12 gestes introuvables, trois contenus rognés, une action
potentiellement idempotente et une erreur de chargement du calendrier.
Elles ne sont ni des bugs établis ni des faux positifs acquis. Les bruts ne
contiennent pas les échecs réseau horodatés nécessaires pour attribuer cette
erreur à une navigation ou au produit. Une QA ciblée séparée est préparée.
La pile J est arrêtée, ses deux ports QA libres ; les 209 fichiers durables
et leurs empreintes sont contrôlés, sans réécriture des anciens reçus.

Les huit variantes causales shared4 sont exécutées dans les copies jetables
avec leurs résultats attendus, sans timeout de lot. Les versions saines
passent ; les versions altérées échouent aux assertions exactes attendues.
Le contrôle négatif B1772 produit aussi l'unique trace SQLCipher attendue,
absente du témoin sain. Une comparaison du vérificateur supplémentaire est
corrigée pour respecter la sérialisation JSON tuple/list, sans relancer les
lots ni modifier les bruts. Les 159 fichiers sont préservés et revérifiés sous
`.app-loop/cycles/17/calibration/shared4/attempt-20261006T202446-5504681c/index.json`.
La revue indépendante et les liaisons du consommateur restent distinctes
des résultats d'exécution. La revue des quatre contrats est terminée sous
`qualification/shared4-independent-review.json`, avec quatre cartes séparées
dans `qualification/shared4-reviews/`. Elle conserve les limites AST/mémoire,
les sources historiques rouges et l'absence de preuve native/UI. Les 159
copies et origines sont inchangées, les 23 PID attribués absents. Root relit
le consommateur avant toute calibration positive ; un défaut de lecture de
l'attribut XML Vitest est corrigé dans l'instrument seulement, sans modifier
ni les assertions exactes ni les bruts ni les sources produit.

La nouvelle revue native relie les assertions aux captures, signatures,
sources, observations et limites réelles. Elle conserve l'absence de console
JavaScript et de code de sortie GUI. Le journal applicatif JSON réel est
préservé additivement sans relance : 129 records, aucun ERROR ni CRITICAL.
Le flux combiné rust/uvicorn reste du texte et n'est pas réinterprété comme
ce journal JSON. Index et revue sont sous `calibration/native/application-json-log/`
et `qualification/native-policy-review-assertions.json`.

Le consommateur FULL refuse encore les preuves ou approbations absentes.
La phase reste DISCOVER, zéro ronde propre, 23 forçages historiques inchangés.
Aucune correction produit ni publication n'est déclarée.

## Reprise nocturne autorisée

Le 6 octobre, Ludo demande la poursuite pendant la nuit. Une reprise planifiée
horaire est créée dans ce même chat, jusqu'au 7 octobre à 8 heures Europe/Paris :
`th-r-se-cycle-17-reprise-nocturne`. Sa configuration canonique est dans
`/Users/synoptia/.codex/automations/th-r-se-cycle-17-reprise-nocturne/automation.toml`.
Elle commence par vérifier les travaux déjà actifs pour éviter une seconde
boucle concurrente. Elle ne publie pas et s'arrête à une porte humaine ou si
une autorité nouvelle est nécessaire. Ce mécanisme exige que le Mac et l'app
restent disponibles ; sa création ne prouve pas l'exécution d'une future ronde.

Au passage de relais, les agents actifs terminent la couverture J, la revue
sémantique shared4 et le consommateur hors ligne. Les origines collaboration
réelles, y compris shared4, sont dans
`qualification/root-identity-extension-20261006T203259.814224Z/` ; l'ancienne
calibration unitaire et son registre restent inchangés. Les nouvelles liaisons
shared4 restent non approuvées dans `qualification/shared-bindings-draft/`.
Ce relais ne constitue ni un GO de consommateur ni une qualification FULL.

## Travail nocturne, 6 octobre après 20:40 UTC

Root relit les quatre cartes et vérifie 220 fichiers distincts, les 159
origines et les limites normatives. Reçu :
`qualification/root-shared4-readonly-20261006T205040.311392Z.json`.
Les huit portes complètes ont un assemblage dérivé contrôlé, sous
`qualification/complete-gates-assembly-20261006T205511.888666Z/`.
Les 937 diagnostics Mypy restent une observation rouge, jamais un PASS ;
une absence de SHA du lanceur dans un brut reste explicitement non attestée.

Après relecture intégrale des instruments courants, root crée quatre
approbations exactes hors ligne, sous
`qualification/root-shared-approval-20261006T210409.990959Z/`.
Le contrôle shared passe réellement : quatre positifs, quatre prérequis
unitaires liés et 30 refus ciblés, sans application, test produit, FULL ou
ronde. Reçu : `qualification/shared-consumer-calibration-20261006T210447.016990Z/receipt.json`.
Root relit les 30 paires et leurs motifs exacts, inspecte les copies altérées
et rehashe 426 originaux du dépôt et 155 originaux privés, sans écart.
Le garde d'admission de cette calibration passe, sous
`qualification/shared-consumer-qualification-20261006T210736.643519Z/qualification.json`.

Le diagnostic K est rouge sur un locator absent avant les mesures Mémoire,
CRM et facture. Il a néanmoins observé HTTP 200 sur les événements Agenda
et le retour septembre vers octobre. L'erreur calendrier de J n'a pas été
reproduite ; cela ne suffit pas à la classer. K est arrêté, les ports QA sont
libres. Les 120 fichiers sont préservés byte-exact sous `calibration/web-K/`,
y compris les canaris rouges et corrigés. Le premier canari SIGTERM a révélé
que `InterruptedError` pouvait être absorbée par Python pendant `communicate` ;
une exception dédiée est ensuite contrôlée dans ce même chemin, avec arrêt
des seuls processus attribués. Aucun correctif produit n'en est déduit.

L termine ses neuf observations ciblées, sans étape absente et sans erreur
du diagnostic. Les onze captures sont inspectées par root et les 133 fichiers
préservés ont un inventaire byte-exact vérifié. À 1 440 et 800 pixels, le
défilement du pipeline atteint réellement la dernière colonne ; la table de
factures à 800 pixels affiche montant et actions à sa borne droite. Le client
figé de la facture passe du placeholder au bon contact synthétique après
chargement. Aujourd'hui conserve octobre puis revient de septembre à octobre.
Six requêtes événements retournent 200, aucune n'est observée en échec. Les
six ERR_ABORTED concernent des modules Vite ou l'atlas pendant la navigation ;
l'erreur événements de J reste non reproduite et non attribuée. Revue root :
`calibration/web-L-root-observation-review.json`. La pile L est arrêtée.

L révèle surtout un défaut d'instrument : six des neuf boutons Expliquer le
score sont relocalisés vers une autre carte CRM après remontage par les IDs
React aria-controls réattribués. L ne clique pas ces faux matchs. Root inscrit
screen_coverage en FAIL à 21:15 UTC, sans effacer le PASS J. Les contrôles sont
présents dans le DOM ; aucun défaut produit n'en est déduit. Le PASS renvoyé
par calibration-status ne porte que sur les cinq axes requis ; le consommateur
FULL exige bien six calibrations fraîches, dont la couverture écran encore
suspendue. La phase DISCOVER et zéro ronde propre restent inchangés.

La revue statique de la calibration native trouve d'abord
une ancienne empreinte d'instrument non préservée et des sources produit
appelées avec un périmètre de preuve C17 incorrect. Les anciennes cartes
et reçus sont conservés, sans les réécrire pour masquer ces refus.
L'ancien instrument est ensuite récupéré byte-exact depuis les vrais patches
de la session, avec aller-retour et empreinte d'origine confirmés. Il reste
une définition historique, interdite comme preuve produit ou preuve d'aspect.
Les dix sources actuelles sont admises seulement par leurs paires path/SHA
exactes du contrat ; aucune preuve historique arbitraire n'est admise.
La nouvelle revue statique indépendante est sous
`qualification/native-consumer-preparation/SHARED4-REFERENCE-FIX-ADDENDUM.md`.

Après une décision root exacte, le contrôle natif hors ligne passe réellement
un positif et quinze refus de la frontière d'approbation immuable. Les erreurs
d'instrument ne comptent pas comme des refus attendus. Les originaux, y compris
les deux sources QA patchées, les deux binaires et le journal QA effectivement
relus, sont inchangés. Reçu :
`qualification/native-consumer-calibration-20261006T210951.483053Z/receipt.json`.
La relecture indépendante de ce premier résultat est terminée. Elle vérifie
les 125 originaux mais relève deux limites : quatre copies et quatre origines
de complément, ainsi que le lecteur root, n'étaient pas inscrits au registre
temporel ; le négatif historique retirait le builder, pas une sonde API.
Le brut initial demeure intact avec ces limites, dans la revue
`qualification/native-consumer-preparation/SHARED4-NATIVE-CALIBRATION-ACTUAL-REVIEW.md`.

Après correction de l'instrument et revue statique indépendante, une nouvelle
approbation root et un nouveau contrôle passent réellement un positif et
quinze refus. Les 134 originaux, dont les huit compléments et le lecteur root,
restent identiques avant/après. Le négatif historique retire cette fois la
vraie première sonde API223503. Reçu exact :
`qualification/native-consumer-calibration-20261006T212043.758789Z/receipt.json`.
Sa revue indépendante est terminée, sans écart sur les 134 empreintes et
les quinze copies/motifs. Addendum :
`qualification/native-consumer-preparation/SHARED4-NATIVE-CALIBRATION-SECOND-ADDENDUM.md`.
Aucune GUI ni API n'est relancée et ce
contrôle n'établit ni quinze parsers internes, ni une nouvelle ronde native,
ni FULL. Console et code de sortie GUI restent inconnus.

Le constructeur des deux futures rondes runtime78 est relu en entier. Il
reste une préparation statique, avec lanceur fermé ; contrôleur de services
persistants, gardes OS et preuves fraîches restent nécessaires avant exécution.
J, K et L ne deviennent pas les deux rondes FULL par changement d'étiquette.
Le contrôleur runtime78 possède une préparation séparée, référencée par
`qualification/RUNTIME78-CONTROLLER-C17.md`. La revue indépendante ferme son
exécution avant correction du nettoyage après ambiguïté et des contrôles
d'identité/survie des services après interruption. Aucun canari ni runtime78
n'est encore exécuté. Les préimages et limites de polling sont conservées.

Le candidat écran M retire les identifiants React et `aria-controls` du
ciblage. Dans le CRM, la carte porte l'UUID réel du contact ; ce contexte doit
être unique avant toute sélection par attribut direct. Hors de ce contexte,
les homonymes sans identité stable restent refusés. Les vingt tests HTML
synthétiques passent, sans constituer une validation produit. La revue
statique indépendante est dans
`/private/tmp/therese-c17-identity-m-7go8uh/shared4-static-review/REVIEW-M-V2.md`.
Après lecture root, le contrôle de nettoyage M passe trois sondes réelles :
timeout, SIGTERM pendant communicate et identité volontairement erronée
refusée sans signal. Les familles attribuées sont absentes à la fin. Le
premier passage rouge pour refus sandbox de ps reste conservé, avec son arrêt
ciblé. Reçu courant :
`/private/tmp/therese-c17-web-m-ixm37utn/canary-owned-family-escalated/controls.json`.
La campagne M est maintenant terminée. Après lecture des quatre contrôles
bruts, des XML, des journaux et des captures, root qualifie les six calibrations
dans leur portée. Les six inscriptions au registre passent, avec validité
de douze heures ; la phase reste DISCOVER et zéro ronde propre. Le diagnostic
retrouve les 18 boutons CRM sur le même UUID métier, sans mauvais ciblage ;
les neuf boutons RGPD homonymes restent refusés. Aucun de ces 27 boutons n'est
cliqué par cette sonde. L'acteur brut `codex-environment-routes`, son round et
son statut `completed_unqualified` restent intacts, sans devenir runtime78.
Les quatre captures du diagnostic et les captures de calibration sont
inspectées individuellement. Les 119 fichiers de l'archive sont rehashés par
root, sans écart. Les services sont arrêtés et une vérification root fraîche
ne trouve ni les deux PID attribués ni les listeners 17593/5173. Preuve bornée :
`calibration/root-M-qualification-20261006T214400Z.json`, avec références exactes
à `calibration/web-M/`. Ce lot ne qualifie pas les 21 écrans, FULL ou un plateau.

La relecture indépendante de la révision 03 du contrôleur relève deux courses
de publication JSON de la barrière, un champ de stabilité des logs trop large
en présence d'un descendant non attribué et un défaut de fermeture des FD
si le préflight sandbox refuse avant enregistrement. Les chemins restent
fail-closed, sans preuve d'un défaut produit. La révision 04 et son complément
errno ferment ces réserves statiquement. Le relecteur indépendant et root
revérifient les 62 fichiers gelés et les six instruments. Les refus EPERM et
EACCES d'une identité connue ne sont plus assimilés à un processus absent.
Les quatre faux retours errno sont des tests purs, pas des appels noyau.

Après un GO root limité aux canaris, le premier essai réel échoue au parser
Seatbelt : `host must be * or localhost in network address`, exit 65 sur
l'adresse littérale 127.0.0.1 du profil web. Aucun service ou témoin OS ne
démarre. Le reçu rouge et ses dix fichiers sont archivés byte-exact sous
`qualification/controller-canaries-initial-red-vqcjnilt/`, avec la lecture
root dans `qualification/controller-canaries-initial-red-review.json`.
La birth attribuée est absente après arrêt, sans signal ; les ports restent
libres. Une correction syntaxique bornée vers localhost, sans wildcard ni
nouveau port, est préparée avec ses préimages. Le bord d'ouverture partielle
des deux FD est fermé dans la révision 05 statique relue indépendamment et
par root, avec 104 références exactes. Un nouveau GO root et un second essai
réel passent le parser mais échouent avant workload, exit 71 sur execvp Python.
Le journal kernel du seul PID attribué identifie le refus `file-read-metadata`
sur l'alias UV 3.13 qui pointe vers le Python physique 3.13.5 déjà épinglé.
Le reçu et les dix bruts sont copiés byte-exact sous
`qualification/controller-canaries-second-red-bydwjf5_/` ; la lecture root et
la sortie native du journal sont conservées à côté. Aucun signal, survivant,
ambiguïté ou listener QA n'est constaté. Une révision 06 prépare uniquement
l'accès metadata à ce lien exact, sans lecture de contenu ou dossier ajouté.
La révision 06 est relue, ses 146 références rehashées, puis réellement
éprouvée sous nouveau GO root. L'interpréteur quitte cette fois sur SIGABRT,
avant workload et sans stdout/stderr. Le journal kernel de sa seule birth
signale `file-read-data /` ; la suffisance de ce refus comme cause n'est pas
encore démontrée. Les dix bruts byte-exacts, la ligne kernel et la lecture
root restent sous `qualification/controller-canaries-third-red-*`.
Une révision 07 propose uniquement l'énumération du répertoire racine par
literal, sans lecture des contenus descendants ni subpath. Auto-review refuse
effectivement l'ajout faute d'autorisation humaine explicite. Le changement
n'est pas appliqué : les profils restent en révision 06 et aucun index 07
ne prétend le contraire. Préservation et motif exact sont dans
`/private/tmp/therese-c17-runtime78-controller-wZcNwTl5/revision-07/BLOCAGE.md`.
Une question asynchrone demande à Ludo ce droit précis ; sa réponse n'est pas
présumée. Le rapport de crash natif du propre PID est lu : frames dyld avant
Python, sans démontrer qu'une autre commande ou un autre cwd résoudrait le
refus. Les ports et births attribuées restent absents, zéro signal de secours.
La préparation des modules G1/G5 et du successeur continue, mais toute
exécution reste fermée. Aucun canari, produit, ronde ou FULL n'est qualifié.

Le plan d'intégration runtime78 est relu en entier : 27 étapes futures, huit
journaux, cinq contextes, six calibrations et revues indépendantes des 84
captures, dix PDF et 78 contrats. Le port statique d'un successeur reste
distinct des anciennes définitions et son exécution fermée. Référence :
`/private/tmp/therese-c17-full-suite-ps_tgzy5/proofs/runtime78-constructor/shared4-integration-plan/INTEGRATION-PLAN.json`.
Les anciens résultats ne sont jamais importés comme preuves de ces rondes.

Les métadonnées GitHub des deux dernières releases sont revérifiées le
6 octobre : v0.77.1-alpha et v0.77.2-alpha sont publiques, avec dix artefacts
uploadés chacune. Ce contrôle de métadonnées n'est pas un nouveau contrôle
des téléchargements, signatures ou installations. Rapports canoniques :
`docs/releases/v0.77.1-alpha.md` et `docs/releases/v0.77.2-alpha.md`.
La fin du rapport 0.77.1 conserve un ancien checkpoint d'interruption ; la
clôture ultérieure est attestée séparément dans
`.app-loop/cycles/15/reprise/release-go/final-sync-root/receipt.json` et son
état archivé. Ce texte ancien ne signifie pas que la release est encore
ouverte. Un pointeur de réconciliation est ajouté au rapport local, sans
réécrire ses observations historiques ni publier ou modifier main.

## Porte humaine, nuit du 6 au 7 octobre

La reprise horaire `th-r-se-cycle-17-reprise-nocturne` est effectivement mise
en pause par l'outil d'automatisation après le refus de permission système.
Sa programmation et son prompt sont conservés ; aucune réponse de Ludo à
la question précise sur le répertoire racine n'est présumée. Le goal n'est
pas déclaré achevé et l'état applicatif reste DISCOVER, zéro ronde propre,
23 forçages historiques. Cette suspension concerne l'automatisation, pas
une transition fictive de la boucle.

Le cœur G1 séparé et le port G5 sont relus statiquement par root et croisés
indépendamment. G1 conserve son admission physique fermée avant libproc,
mkdir et Popen, les quatre capacités runtime absentes et les profils r06
stricts. Un handle dont Popen a échoué peut encore être classé stable par
le prototype : il ne constitue pas une preuve de lancement ou d'arrêt de
services. Cette réserve bloquante, les capacités manquantes, la dépendance
à un superviseur réel et les limites de capture d'un enfant court sont
gardées explicites. La préparation de G5 corrige le lecteur hardlink et
conserve les préimages ; aucun de ces outils n'est admis ni exécuté.

Le lot root est dans
`qualification/static-night-20261006T220500Z/root-static-review.json`.
Les 21 fichiers indexés du cœur, son index et des préimages non qualifiées
sont copiés byte-exact dans `g1-core/`. Les références d'origine ne sont pas
réécrites pour faire passer cette copie pour une exécution ou une admission.
Les sources produit, scripts et tests restent identiques à HEAD ; un contrôle
frais ne trouve ni les cinq PID QA attribués ni les listeners 17593, 5173 et
17594. Il ne vise pas le port réel 17293 et ne signale aucun processus.

Pour reprendre, il faut d'abord la décision humaine sur le droit système
précis. Même un accord ne vaudra pas qualification : nouvelle révision
gelée, relecture indépendante, canaris OS réels puis liaison G1/G5 et deux
rondes indépendantes resteraient nécessaires. Aucune nouvelle version,
publication, notification Discord ou modification de main n'est faite.

Les trois agents terminent leur lot sans exécution runtime. Les définitions
G1, son extension fermée, G5 v3 préservée puis v4 et le successeur sont copiés
dans le même dossier privé ; chaque fichier sélectionné par leur index est
rehashé par root sans écart. G5 v4 durcit le lecteur d'ack, mais ne prouve
toujours pas une Session vivante avant Popen. Le successeur corrige sa
proposition A/B vers deux exécutants distincts, sans joindre encore les ABI.
Clôture et limites exactes :
`qualification/static-night-20261006T220500Z/root-close-review.json`.
Le manager comptabilise 48 lots logiques GPT et 1 490 000 tokens estimés,
distincts de tout compteur API. Aucun temps de travail parallèle n'est ajouté.
Budget et registre de calibration renvoient PASS ; ce dernier ne constitue
pas une qualification runtime/FULL. Le commit/push reste différé tant que le
lot est bloqué et que les préparations exigent ce HEAD exact ; les changements
préexistants sont conservés.

## Reprise bornée du 7 octobre : accord sur le répertoire racine

Ludo répond « ok » dans cette conversation à la question exacte qui demandait
d'autoriser Python QA à lister le seul répertoire `/`, sans ajout de lecture
sur ses descendants. Root constate directement cette réponse humaine ; le
relais du préparateur n'est pas sa source d'autorité. Cet accord ne porte
sur aucun autre accès système, les données réelles ou une publication.

La révision 07 ajoute uniquement `(allow file-read-data (literal "/"))`
aux deux profils du contrôleur canari. Root relit les deux diffs : 37 octets
ajoutés à chaque profil, aucune règle `subpath` ou permission réseau ajoutée,
quatre instruments Python inchangés. Les préimages, trois échecs réels et
`BLOCAGE.md` historiques restent intacts.

L'index gelé est
`/private/tmp/therese-c17-runtime78-controller-wZcNwTl5/revision-07/index.json`,
SHA-256 `db20b2272c71b0cdc6db292280b67a86e53fba4551fbd9cd8588ef3ed8fbe196`.
Root rehashe effectivement ses 188 fichiers et le pointeur canonique sans
écart. Ce contrôle est statique : aucun démarrage ni confinement OS n'est
encore qualifié, aucune ronde/FULL et aucune nouvelle release ne sont acquis.
Le prochain essai exige encore une contradiction indépendante et une décision
root limitée aux canaris synthétiques. Les portes runtime G1/G5 restent fermées.

## Canaris r07 réellement concluants, puis relecture indépendante

Le checkpoint ci-dessus est suivi d'un GO root limité aux canaris synthétiques,
`qualification/root-controller-r07-canaries-go-20261007T034438Z.json`.
L'essai est réellement exécuté par root et termine avec code zéro entre
03:45:05 et 03:45:19 UTC le 7 octobre. Le reçu conserve les 14 familles de
sondes attendues, six étapes, un arrêt propre et les ports 17593/5173 vides.
Les timeout et interruption sont des cas attendus du canari, jamais des
résultats produit verts. Les deux services sont des témoins Python, pas
le backend ni Vite de THÉRÈSE.

Root vérifie 39 références imbriquées sans écart. Le relecteur indépendant
`shared4_execution` vérifie 55 références, les six reçus adjacents et les
jointures birth/parent/rôle des signaux. Il ne relance aucun instrument.
Un contrôle root supplémentaire ne retrouve aucun des douze PID attribués,
ni listener sur 17593, 5173 et 17594 ; aucun signal n'est envoyé par ces
diagnostics. Le port réel 17293 n'est pas visé.

Les 59 fichiers bruts et 42 fichiers de définition/relecture sont copiés et
comparés byte-exact dans
`qualification/controller-canaries-r07-green-14tk78me/`. Les références
absolues originales restent intactes et les copies ne prétendent pas garder
l'identité inode/hardlink des publications originales. Le reçu réel a pour
SHA-256 `c0475e52217843f61d84df25d251f133d2157daec8164348955ad75c3ef858d0`.
La conclusion et ses limites sont dans `root-review.json` de ce dossier.

Cette réussite débloque le démarrage canari r07 dans les cas exercés. Elle ne
qualifie ni G1/G5, ni Chrome, les données réelles ou une ronde/FULL. Le réseau
exercé est IPv4 TCP ; le polling ne prouve pas une attribution exhaustive
d'enfants hostiles. La déclaration de périmètre des profils réels n'est pas
un audit universel des fichiers ouverts. L'automatisation reste en pause et
aucune publication, notification Discord ou modification de main n'est faite.

Le raccord du moteur de tests se poursuit dans des copies QA séparées. Une
première copie de correction de clôture G1 reste préservée après découverte
statique d'un test appelant son double au lieu de la méthode réelle. Les
tests purs et les contrôles runtime de ce nouveau module restent distincts
du succès r07 ; aucun compteur de ronde propre n'est augmenté.

La reprise native horaire est inspectée via son outil et sa configuration.
Une tentative de réactivation avec le prompt, le périmètre et l'échéance
préservés est refusée par auto-review : l'accord humain présent porte seulement
sur le listing de `/`, pas sur une automatisation persistante incluant commit
et push. La configuration est relue ensuite et reste effectivement `PAUSED`.
Aucun contournement ou édition directe de sa configuration n'est tenté.
Une question distincte demande cet accord à Ludo ; les vérifications QA du
tour courant continuent sans présumer sa réponse. Le goal natif est encore
`blocked` lors de sa lecture, distinct de la phase applicative DISCOVER.

La première copie closure G1 est ensuite éprouvée uniquement par ses tests
purs, sous GO root exact et Python `-I -B`. Le résultat réel est code 1,
11 méthodes exécutées : dix vertes, une rouge. Le test de restauration
confirme exactement le défaut du double : liste des appels vide au lieu de
SIGINT/SIGTERM. Les neuf mutations synthétiques restent incluses dans une
seule méthode verte, pas neuf tests produit supplémentaires. Source, test
et index restent identiques avant/après. Sortie native combinée et reçu :
`qualification/G1-closure-v1-pure-red/`. Aucune opération réelle de ledger,
Popen, FD, signal ou réseau n'est exercée par ces doubles. Les trois autres
réserves de la revue restent statiques à ce stade ; ce rouge ne les qualifie
pas et ne dit rien d'un bug produit ou d'une ronde/FULL.

La copie closure G1 V2 est relue par root, ses 14 références et huit préimages
comparées sans écart, puis réellement testée sous GO pur exact. Résultat :
code zéro et 19 méthodes vertes, neuf mutations dans une méthode incluses.
Unittest rapporte 0,003 seconde, distinct de la durée du travail agentique.
Source, test et index sont rehashés inchangés après l'essai. Le test de
restauration appelle désormais la vraie méthode, avec API de signal mockée.
Les cas de refus de sink, d'enregistrement, de référence tardive, de reçu et
de signal pré-Popen sont vérifiés uniquement avec des doubles.

Le gel final est `f217733915373aa89ac68b7a0db603a6ecfc89c79b2f8320702fd12d0b15a9bb`.
Un gel V2 intermédiaire, annoncé avant correction d'un test de référence de
services, reste conservé byte-exact et jamais exécuté ; son delta est explicite.
Sortie native combinée et reçu final de tests :
`qualification/G1-closure-v2-pure-green/`. Ces sorties sont celles retournées
par l'outil d'exécution, pas des captures directes séparées stdout/stderr.

La revue indépendante constate les corrections des quatre points sur cette portée pure,
sans ouvrir l'admission. Les tests stop/retry gardent un double de restauration ;
ils ne prouvent pas une installation réelle des handlers. Une exception dans
`finish` avant incrément de `close_attempts` impose encore l'abandon par
l'appelant ; le taint demeure rouge, sans faux FULL déduit. Les profils G1
restent r06 et les quatre capacités runtime absentes. Les contrôles OS réels,
le raccord final G5/successeur et les deux rondes complètes restent à produire.

Les définitions closure V1/V2 et leurs revues sont archivées byte-exact sous
`qualification/G1-closure-pure-red-green-definitions/` : 43 fichiers de
définition/préimage/revue V1 et quatre fichiers de revue V2. Root lit la revue
V2 et son addendum en entier ; le relecteur rapproche les 19 noms de méthodes
du vrai texte retourné et rehashe 33 originaux inchangés. L'index de cette
relecture est `907ba37af5eab7631a87dc5780808bdf2053d4a6188666d49ad6f75a6273b843`.

Le contrôle récurrent des copies est regroupé dans `verify-byte-copies.mjs`
de ce dossier, en lecture seule et sans import d'instrument. Ses contrôles
positifs vérifient réellement les 43 copies puis les quatre copies de revue.
Une paire de fichiers synthétiques différents est explicitement refusée
avec code 1 ; cette erreur attendue du vérificateur n'est pas un bug produit.
Le script compare les fichiers sélectionnés, pas l'absence de fichiers
supplémentaires, ni l'identité inode/hardlink des copies. Ses index et
`verifier-negative-returned-output.log` conservent cette portée.

Le raccord ABI concret est préparé par un autre agent dans une nouvelle copie
fermée, puis archivé sous `qualification/successor-ABI-closed-ud9LYaSh/`.
Root lit le README, rehashe les 75 fichiers de l'index et compare les 31
préimages déclarées sans écart ; les 76 fichiers de la copie entière sont
comparés byte-exact. Index :
`b319daa0d7799149f3813848b055d451fbbb9f79d57c32a3431d0ad5d4a47998`.
Ce lot reste à relire dans son code et à tester : les 42 cas synthétiques
déclarés par son auteur ne sont pas exécutés. Aucun GO runtime n'est acquis.
Les bindings tardifs de contrats/revues ne prétendent pas prévoir un SHA
futur ; trois phases SQL sont encore fermées faute de worker borné. Les
capacités G1 manquantes et les admissions restent des refus, jamais des
valeurs vertes ajoutées dans un adaptateur. Les sept délais ne sont pas
adoptés et le contrat de 45 requêtes density demeure inchangé.

Le lot courant est comptabilisé une fois par le gestionnaire : 52 lots
logiques GPT et 1 620 000 tokens estimés, pas un compteur API. Le temps
parallèle n'est pas additionné. Une première invocation avec le Python
système 3.9 refuse `datetime.UTC` avant toute mutation ; l'interpréteur QA
3.13 compatible est ensuite utilisé sans modifier le script. Budget : PASS.
`next-action` propose DISCOVER, mais son texte générique « rien n'attend
l'humain » n'annule ni la question d'autorisation de reprise native, ni les
portes runtime fermées. Zéro ronde/FULL est ajouté ; 23 forçages historiques
restent inchangés. Le goal natif et la reprise horaire ne sont pas présentés
comme relancés. Aucun commit/push, nouveau tag ou publication n'est effectué ;
le lot de campagne reste à qualifier et les préparations pinent ce HEAD exact.

## Reprise du 7 octobre après « oui termine »

Ludo autorise explicitement la poursuite QA et le commit/push sur la seule
branche Codex, sans publication ni données réelles. Lors de la vérification,
l'échéance de reprise nocturne, 8 h Europe/Paris le 7 octobre, est déjà passée.
La configuration reste `PAUSED` et aucun horaire supplémentaire n'est inventé.
Le tour courant poursuit les vérifications autorisées ; le goal natif est
encore `blocked` lors de sa lecture, et n'est pas présenté comme réactivé.

Root relit le bridge ABI, ses tests et les sept diffs, puis le coordinateur
et le module G1 V2 complets. Les 75 références de l'index ABI `b319daa0…`
sont réellement rehashées sans écart avant et après le test. Le GO root est
strictement pur, distinct d'une admission runtime. Exécution native : code 0,
42 cas collectés et réussis, résumé pytest 0,02 seconde, durée de retour outil
0,159507167 seconde. La version observée est Python 3.13.5 / pytest 9.0.2.
Les plugins automatiques et le cache pytest sont désactivés, l'environnement
et HOME/TMPDIR sont QA, avec Python `-I -B`.

Les cinq fichiers de GO/runner/reçu/sorties sont archivés et comparés byte-exact
dans `qualification/successor-ABI-pure-42-green-ZgjNPq/`. Cette fois stdout
et stderr sont des sinks directs séparés ; stderr est réellement vide.
Le reçu a pour SHA-256
`b7e10088514d714b9e99e9dd907777c90f133436659844c3d723c8d97749b2c0`.
Ces 42 cas éprouvent seulement des jointures sur fixtures synthétiques, sans
import de G1, libproc, processus, signal, réseau ou code produit. Ils ne
qualifient aucune ronde/FULL et ne modifient aucun compteur.

La gestion réelle des processus et les trois workers SQL sont poursuivis
dans deux nouvelles copies QA séparées, sans modifier les gels existants.
Une troisième relecture indépendante porte le raccord et la sortie réelle.
Les admissions runtime restent fermées tant que les capacités et canaris
propres à la nouvelle définition ne sont pas effectivement prouvés.

La relecture indépendante ABI est ensuite close et lue par root en entier.
Ses trois fichiers sont archivés byte-exact dans le sous-dossier
`independent-review/` du lot pur ci-dessus. Index SHA-256
`40917cdb8f1a317b4f0d580bb9b16d8a373ce85f674b9d7a2b032936d9ad31ac`.
Elle constate 31 paires de préimages exactes et sept diffs reconstitués, puis
les 42 lignes PASSED du vrai stdout. Il s'agit d'une relecture, pas d'une
seconde exécution. Les manques runtime précédents restent explicitement refusés.

### Essai G1 réel, arrêt sur confinement et clôture du protocole SQL

La nouvelle définition canari G1 est figée dans l'index `662d463a…`.
Root lit ses modifications, le runner, le workload et les tests. Les 24
tests purs réussissent réellement : code 0, 0,005 seconde selon unittest.
Ils restent limités aux fixtures. Les preuves et la définition sont conservées
dans `qualification/G1-canary-pure-24-and-OS-red-CX1rRI/` et
`qualification/G1-canary-closed-zOs7Ib/`.

Le premier canari positif OS est réellement lancé sur une racine QA fraîche.
Il échoue avec code 1. Son stderr direct montre `Path.resolve(strict=True)`
refusé sur `/private` avec `PermissionError`. Ce résultat est un échec du
canari de confinement, pas un bug causal THÉRÈSE. Le reçu réel demeure rouge :
`c16d6a417defb836844b7bb013483da1533594c9380eb0c48627d09a7135be0d`.
L'instrument rapporte 0,11814704199787229 seconde ; aucun succès de workload
ni de ronde n'est déduit du nettoyage réussi.

Les reçus de stage et d'arrêt indiquent zéro signal, restant attribué,
ambiguïté ou erreur de nettoyage, avec restauration des gestionnaires.
Les diagnostics externes `lsof` sur les seuls ports QA 17593 et 5173, puis
`ps` sur les seuls PID attribués 63712 et 63720, ne retournent aucune ligne.
Ils ne qualifient pas la capacité G1 d'absence des ports. Les journaux et
reçus sont conservés dans `qualification/G1-canary-positive-OS-red-jgjxq8w7/`.
Le timeout n'est pas lancé après ce refus prévisible.

Une proposition r08 ajoute uniquement `file-read-metadata` sur les deux
littéraux `/private` et `/private/tmp`, une ligne par profil. Elle ne donne
aucune lecture de contenu ou de descendants, ni écriture, réseau ou signal.
Root lit les deux diffs et la revue. La question humaine précise est posée
et reste sans réponse à ce checkpoint. Les copies proposées sont archivées
dans `qualification/G1-r08-profiles-proposed-only-Lk8GNY/`. Elles ne sont pas
activées. Les profils r07, les assertions de chemin et les preuves rouges
restent intacts. Aucun élargissement automatique n'est effectué.

Les trois workers SQL sont préparés dans une copie distincte fermée. Root
lit leurs trois nouveaux modules, les six diffs et les tests. Une relecture
indépendante ciblée est lue et conservée, index `2450a4fa…`. Le parent prévoit
les copies QA exactes des seules références réellement consommées ; le
worker conserve les fonctions et assertions métier, sans fallback SQL dans
le parent. Ces comportements sont préparés, pas encore exécutés.

Les 36 tests purs de `sql_protocol` réussissent réellement, code 0 : pytest
0,02 seconde, retour outil 0,435135459 seconde. Les 78 références de l'index
`0ae270ff…` sont rehashées avant et après sans écart. Le reçu root a pour SHA
`06173ee654c49de52f58be68e42124caf0360090b7fdafc64f84bb31eb0d10ed`.
Le lot est conservé dans `qualification/SQL-workers-closed-fvAEbpNh/`,
`qualification/SQL-protocol-pure-36-green-ZNjyhpN9/` et
`qualification/SQL-workers-independent-review-VPYv3f/`. Les tests n'importent
ni worker, ni vue de copies, ni core, G1 ou produit. Ils ne prouvent donc pas
les fonctions métier, les copies en contexte réel ou un démarrage OS.

La conservation de ces sept dossiers est contrôlée par le vérificateur
existant : 143 fichiers source comparés byte-exact, 1 550 898 octets, sans
rebasing des références ni affirmation sur les inodes ou les fichiers
supplémentaires. Un premier contrôle échoue parce que sa redirection crée
son propre fichier dans la source déjà copiée. Ce défaut de procédure est
conservé, puis corrigé en plaçant la sortie hors des arbres comparés. Aucun
code du vérificateur ou assertion n'est abaissé. Le contrôle final réussit,
SHA `7bc60a6b1895a9a21aa4d406315eb9f949575b1ae2cf5760876fa5f530416757`,
dans `qualification/root-copy-check-BhrL305O/`.

Bilan de ce tour : 42 + 24 + 36 = 102 tests purs réussis, distincts des
preuves OS. Le gestionnaire compte le lot une fois : 53 lots GPT et
1 680 000 tokens estimés, pas une mesure API. Le temps parallèle n'est pas
additionné. Zéro ronde/FULL est ajouté. Les deux rondes complètes et la
release restent à faire. La reprise horaire reste en pause après son échéance
de 8 h ; aucun nouveau créneau, tag ou déploiement n'est autorisé par ce
checkpoint. La prochaine action OS nécessite d'abord la réponse humaine
aux deux métadonnées, puis une nouvelle définition et de vrais essais frais.

Ce lot documentaire peut être sauvegardé sur `codex/cycle-17` après les
vérifications ci-dessus, sans inclure les modifications antérieures de la
carte ou de la fiche release. Ses preuves conservent leur HEAD exact testé
`b517daed…` ; un commit de documentation ne les retargete pas. Avant toute
exécution future exigeant le HEAD courant, reconstruire et relire le gel
approprié, sans réutiliser un reçu ancien comme résultat d'une nouvelle ronde.

## Reprise après l'accord limité aux métadonnées, 7 octobre

Le « ok » humain répond à la question exacte sur `file-read-metadata` des
deux littéraux `/private` et `/private/tmp`. Il n'autorise ni contenu,
descendants, permissions globales, publication ou prolongation de la reprise
nocturne. Le reçu de périmètre est conservé dans le contrôleur QA
`/private/tmp/therese-c17-r08-root-9S4sNn9t/` ; SHA-256
`352607dbda8a748abf845935269b05cd7931c5278162c4e5a7f82439de573203`.

Deux définitions nouvelles sont lues et rehashées sans modifier les gels r07.
Le canari direct r08 porte l'index `d97f12e9…` et 29 références ; la copie
conjointe SQL r08 porte l'index `a7624cb8…` et 25 références. Le seul changement
fonctionnel de profil est la ligne de 73 octets autorisée. Aucun accès réseau,
écriture, signal ou contenu supplémentaire n'est ajouté. Les états de
préparation inscrits dans les INDEX restent historiques ; les résultats
effectivement exécutés sont séparés.

Les 27 tests purs du protocole conjoint sont réellement exécutés avant les
canaris : 27 PASSED, code outil 0, pytest 0,01 seconde. Les 23 références de
leur définition sont identiques avant/après. Leur stdout a pour SHA-256
`c9a7bade531c966416d5b6e497aa60d103a12b1f6375eeb750ff14c4beef2fa8`.
Ce sont des fixtures synthétiques, pas une qualification OS ou produit.

### Deux canaris directs r08 effectivement observés

Le positif s'exécute sur la racine fraîche
`/private/tmp/therese-c17-g1-canary-positive-mjq74g5e/` : code 0, workload
inerte sorti normalement, 0,08553458399546798 seconde selon le reçu. Nettoyage
stage 0,00422662500932347 seconde et arrêt 0,00421558300149627 seconde,
tous deux sous 8 secondes, sans signal, résidu, ambiguïté ou erreur.
Les bruts sont stables et les gestionnaires restaurés. Reçu SHA-256
`dba5c94169670cca0455c2ac3ebea83e40d0bdd8dfd5ba7cb7dd59fb6f52969b`.

Le timeout s'exécute séparément sur
`/private/tmp/therese-c17-g1-canary-timeout-fdq03ajd/` : code outil 0 car le
résultat attendu est bien observé, mais workload arrêté avec exit -15 et
timeout d'instrument, jamais succès produit. Durée reçue
3,0326072919997387 secondes ; nettoyage stage 0,013324500003363937 seconde
et arrêt 0,007531750001362525 seconde. Les cinq signaux réels ciblent seulement
la birth canonique du workload : trois SIGSTOP, SIGTERM, SIGCONT. Les taints
attendus sont conservés ; aucune stabilité de logs après timeout n'est
affirmée. Reçu SHA-256
`402237ecf45e8c618d932b9ad77787014f20214d63dccfd2424f481af290a3c0`.

Root vérifie les deux bruts, leurs SHA, les bornes stage/stop, les taints
exacts et les identités, sans s'appuyer sur le seul exit 0 du runner.
Le premier vérificateur échoue en tentant de parser un stderr vide comme
JSON ; son code et ses sorties rouges sont conservés. Une copie V2 lit les
flux comme octets, sans abaisser les assertions. Elle réussit, ainsi que
huit mutations explicitement synthétiques en mémoire. Ces mutations ne sont
ni de nouvelles exécutions OS, ni des tests produit.

### Premier raccord imbriqué r08 : rouge d'instrument préservé

Le vrai canari conjoint positif échoue avant le grant de lancement imbriqué :
`ValueError: joint exact request environment_sha256`. Racine fraîche
`/private/tmp/therese-c17-g1-canary-positive-9ozdv1tk/`, reçu SHA-256
`e8670cbd2a956903e94e1b1511a16afa6877270f648367bd812daa36ac48542b`.
Aucun enfant imbriqué n'est lancé. L'abort ferme seulement le helper attribué,
nettoyage 0,030613458002335392 seconde, sans résidu, ambiguïté ou erreur.
Le timeout conjoint n'est pas relancé avec la même cause déterministe.

La reconstruction pure à partir de l'environnement et de la demande physiques
donne l'attendu `11960e1f…`. L'ajout unique
`__CF_USER_TEXT_ENCODING=0x1F5:0:0` reproduit exactement le hash demandé
`9ea3a1ea…`, sans retirer de clé ou modifier d'autre valeur. Cela isole le
delta de jointure ; l'injecteur système exact n'est pas prouvé. Le correctif
est préparé dans une nouvelle copie : fournir explicitement cette valeur
liée à l'UID dans l'environnement admis, en conservant l'empreinte complète.
Aucun filtre silencieux ou changement de permission n'est accepté.

Les diagnostics externes des seuls PID attribués 73627, 73630, 73707,
73708, 74269 et 74270, puis des seuls ports QA 17593/5173, ne retournent
aucune ligne. Ces diagnostics ne qualifient pas l'API G1 d'absence des ports.
Les cinq arbres source/reçus sont conservés dans les dossiers
`qualification/G1-r08-*` et `qualification/G1-G5-r08-*` nommés par leurs
identifiants ci-dessus. Comparaison byte-exacte : 96 fichiers, 1 099 138
octets, SHA manifeste `a07ca70b…`, sans rebasing ni preuve d'inode des copies.

La nouvelle lecture native du goal le trouve `active`, contrairement au
checkpoint précédent. Il s'agit du retour réel du produit, pas d'une
mutation de statut par le code QA. Cela ne prolonge pas le heartbeat expiré
et ne valide pas de ronde. Les admissions FULL, quatre capacités G1 et les
deux rondes produit restent non qualifiées à cette étape.

### Correctif de jointure et deux essais imbriqués effectivement qualifiés

La nouvelle copie porte l'index `604dd16b…`, 39 références rehashées exactes.
Le delta G1 est limité à la constante obligatoire
`__CF_USER_TEXT_ENCODING=f"0x{os.getuid():X}:0:0"`. Le runner durcit également
les bornes de nettoyage stage/stop et les booléens de taint ; son prédicat
est extrait pour des tests purs. Les gates, protocole, owner, helper,
capture imbriquée, fixture et profil SQL r08 sont inchangés. Aucun flag de
capacité ou admission n'est ouvert.

Les 52 tests purs sont réellement exécutés : 27 cas précédents et 25 nouveaux,
pytest 0,09 seconde, code 0, stderr vide, sources avant/après identiques.
L'ancien rouge est reproduit ; les contrôles de hash complet ET l'allowlist
réelle sélectionnée par AST refusent une clé absente, une valeur différente
ou une clé supplémentaire. Reçu SHA-256
`0070f59d023fe30dcc95b47f6dcb98c434a3f0fb8e40b86b04dc8abb9ed32fc7`.
Ce deuxième passage de 27 cas n'est pas compté comme 27 tests distincts en plus.

Après lecture root et revue indépendante, un nouveau GO exact est établi
pour chaque variante et le gel corrigé. Le positif réel est exécuté dans
`/private/tmp/therese-c17-g1-canary-positive-18ixt1ew/` : reçu
`7da050cbd2be28669bc45511dce91069f9c1727d1d9d0ce7c3baf6b63fad43df`,
durée 0,3621015829994576 seconde. La birth enfant est capturée avant release,
le helper reste vivant jusqu'à l'ACK, les flux sont effectivement stables.
Nettoyage imbriqué 0,05675712499942165 seconde, stage
0,006847083001048304 seconde et arrêt 0,006174207999720238 seconde. Zéro signal,
taint, résidu, ambiguïté ou erreur ; handlers restaurés.

Le timeout réel suit seulement après validation physique du positif, dans
`/private/tmp/therese-c17-g1-canary-timeout-yuqq9tok/` : reçu
`66fb59426ab4fa2fe5d01d163a216c2448fd3122a562a5d832b5760a7cf3c1b9`,
durée 2,380147208008566 secondes. La limite imbriquée de 2 secondes est observée,
pas le watchdog externe. STOP trois fois, TERM et CONT ciblent exclusivement
l'enfant birth `77531/1791357590/212770`, UID 501, PGID 77530 ; le helper
77530 reste vivant avant ACK et sort ensuite avec exit 86. Nettoyage imbriqué
0,06567416701000184 seconde, stage 0,008596166997449473 seconde et arrêt
0,007137916007195599 seconde, tous sous 8 secondes. Les taints exacts et la
classification timeout d'instrument sont conservés ; aucun vert produit.

Le vérificateur root V2 contrôle les SHA/taille, contextes, environnement
intégral, grants, birth réservée, ACK, bruts, taints et bornes, puis rejette
14 mutations explicitement synthétiques en mémoire. Son premier mode à un
seul positif ne prétend pas vérifier une paire ; le passage final vérifie
bien deux racines et deux variantes distinctes. Une seconde relecture
indépendante confirme les reçus et 12 publications hardlink physiques,
incluant les deux child-gates. Elle ne rejoue aucun OS. Les audits de
processus non attribués ne sont pas présentés comme confinement hostile
exhaustif ou absence de course Darwin lecture/signal.

Les six PID attribués et les deux ports QA sont de nouveau absents au
diagnostic externe, sans signal. Les trois nouvelles copies sont conservées
dans `qualification/G1-G5-env-fix-*` ; comparaison byte-exacte de 96 fichiers,
1 119 319 octets, manifeste `20367c3a…`. Le rouge précédent reste intact.

Le raccord mesuré est volontairement un canari inerte à un seul enfant.
Il ne devient pas par copie un renderer produit multi-enfants. L'observation
des listeners/absence des ports, le relais root des bindings, l'environnement
du successeur, les bornes manquantes et le raccord G5 multi-enfants restent
à intégrer et à vérifier avant une ronde complète. Zéro ronde/FULL est ajouté,
aucun build, tag ou release produit n'est déclaré livré.

### Comptabilisation : plancher natif distinct des estimations

Le compteur natif du goal est effectivement lu à 7 528 002 tokens pendant
ce lot, avec statut `active`. Le goal a commencé après le cycle 17 ; il ne
prouve pas une mesure complète du cycle, ni une facturation API. Le budget
local ne comptait jusque-là que 1 680 000 tokens estimés. Pour que son
coupe-circuit ne dépende plus uniquement de cette sous-estimation, le CLI
enregistre une correction positive de 5 848 002 tokens et un seul lot logique.
Retour réel : 54 lots, 7 528 002 tokens comptabilisés comme plancher
conservateur. Ce n'est pas 54 appels fournisseur. Les anciens événements
estimés restent intacts, le temps parallèle n'est pas cumulé et aucun plafond
n'est relevé. Les préparations listener/relais encore en cours seront suivies
séparément. Aucun forçage de phase, plateau ou ronde n'est ajouté.

### Listeners QA : rouge physique conservé puis positif V4

La lecture root et une revue indépendante trouvent trois refus déterministes
dans la préparation initiale : le gate ne reconnaît pas la racine listener,
le runner omet `bytes` dans les références comparées au GO, et la métrique
`finish` ne couvre pas les scans de ports ultérieurs. Les gels V1/V2 restent
historiques. La nouvelle V3 distingue la branche canari, vérifie les références
physiques complètes et publie des durées de phase séparées. Aucun profil
Seatbelt ni droit supplémentaire n'est ajouté.

Le diagnostic lsof utilise sa propre barrière : birth libproc attribuée au
ledger avant exec, deux flux distincts, timeout rouge et nettoyage par les
seules births admises. La commande est `-F p`, sans `-t`, qui supprimerait
les avertissements. Cette observation sous les droits courants ne prouve pas
une visibilité exhaustive. Les PIPE diagnostiques ne sont pas présentés
comme les sinks exclusifs de stages G1.

V3, index `486a2eb0…`, est rehashée 29/29 ; root exécute effectivement ses
13 tests purs, code 0, 0,004 seconde. Son canari réel échoue dans la racine
`/private/tmp/therese-c17-listener-canary-mv7yrcOi/` : lsof retourne code 0,
stderr vide et stdout exact `p6126\nf3\n`. Le parseur n'accepte que les
champs `p`. Le manuel lsof installé indique que `f`, descripteur de fichier,
est toujours sélectionné. Le rouge est donc un défaut d'instrument, pas un
bug produit ni la présence d'un processus étranger. Reçu SHA-256
`adf4b4ea8898993192aa07f5820b357275af64249063929b20ab9a41ada1a4d5`.

La fermeture du rouge est relue sur ses vrais bruts : sonde puis deux témoins
attribués uniquement, zéro résidu, ambiguïté ou erreur d'attribution, handlers
restaurés. `finish` mesure 0,007299750010133721 seconde pour la sonde,
0,007233541997266002 pour les services et 0,0058972090046154335 pour la
fermeture finale. Les taints et le faux `log_stability_proved` sont conservés.
Les deux reçus de fin observent chacun quatre scans de ports vides.

Une V4 neuve, index `f8b7eb48…`, corrige seulement le parseur exécutable :
grammaire bornée `(pPID fFD+)+`, sans filtrage silencieux. Les sorties
malformées, groupes incomplets, doublons, champs inconnus, NUL/CR et plusieurs
listeners restent refusés. Les 36 références sont exactes ; les 15 tests
purs passent réellement, 0,004 seconde, code 0. Ils incluent les cas V3,
donc les deux passages ne sont pas additionnés en 28 tests distincts.

Après lecture root, revue indépendante et nouveau GO exact, le positif V4
s'exécute dans `/private/tmp/therese-c17-listener-canary-bEQ2Oh8z/` : code 0,
durée reçue 0,8516174999967916 seconde, SHA-256
`2f8d8a9884ec67be35e2f18b97689f4cb60e6edda79017f4ec731d31222c23eb`.
Deux scripts inertes, pas THÉRÈSE/Vite, écoutent uniquement les deux ports QA.
La sonde demande effectivement deux observations au parent vivant ; chacune
porte deux scans concordants et la birth exacte du service attendu. Les
réponses RPC sont liées aux demandes et aux SHA des observations.

Births : backend `7485/1791397178/158574`, vite `7488/1791397178/192175`,
sonde `7489/1791397178/244162`, owner `7476/1791397177/924051`, UID 501.
La sonde termine normalement, stderr vide. Les signaux ne ciblent que les
deux témoins admis, jamais l'owner ou les diagnostics. Zéro taint, résidu,
ambiguïté ou erreur ; handlers restaurés. `finish` mesure respectivement
0,006344084002193995, 0,007866291998652741 et 0,006217207992449403 seconde.
Les phases services/final, scans inclus avant publication finale, mesurent
0,15713737499027047 et 0,15497508300177287 seconde. Le watchdog coopératif de
90 secondes ne se déclenche pas ; aucune garantie hard realtime n'est affirmée.

Le vérificateur root et une seconde relecture indépendante valident les bruts.
La revue indépendante rehash 71 références et contrôle dix publications
hardlink physiques. Le premier vérificateur root échoue sur des noms de
champs de scans incorrects ; une copie V2, conservant ce rouge, lit le vrai
schéma `scans` et vérifie effectivement les deux résultats. Les PID attribués
et les deux ports ne retournent ensuite aucune ligne au contrôle root.
Le premier `ps` est refusé par le sandbox ; le contrôle escaladé, limité aux
huit PID déjà attribués, retourne code 1 et aucun flux. Aucun signal externe.

Limite de provenance : les reçus d'étape conservent encore le libellé hérité
`execution_scope=g1_g5_joint_inert_canary_only`. Le résultat et l'admission
portent la bonne portée listener. Les bruts ne sont pas relabellés : ce
canari ne devient ni une ronde produit, ni une capacité FULL.

### Relais root/stage : tests purs réussis, intégration encore fermée

Le gel `root-stage-relay-pure-XVKXbS`, index `eb0e59d7…`, contient les trois
méthodes de livraison root/binding tardif. Root lit les quatre diffs, le
contrat pur, les bornes et les tests ; les 34 références sont exactes.
Les 37 tests purs sont effectivement exécutés, code 0, 0,02 seconde, sans
import de Session complète, libproc ou processus produit. La revue indépendante
confirme l'environnement propre, les bornes et les liens de livraison.

Le plafond de ronde calculé, 12 884 secondes, reste une proposition non
mesurée et non admise. Le watchdog global, les profils/API complets,
le raccord listener et le G5 multi-enfants manquent encore. Deux refus
contractuels supplémentaires sont repérés : le consommateur exige
`launched_services` et `unlaunched_handles`, que G1 n'émet pas ; le libellé
de portée doit aussi distinguer une vraie ronde du canari. Un correctif
séparé est préparé, sans modifier ce gel ni ouvrir ses flags.

Les six arbres de ce lot sont conservés sous `qualification/G1-listener-*`,
`qualification/root-stage-relay-pure-XVKXbS` et
`qualification/listener-root-closed-ZLM4Dg5R`. Comparaison byte-exacte :
186 fichiers, 2 290 498 octets, manifeste SHA-256
`48146bb8ef85cfbecf1590e738c9c6962d7094b10a5b29ad1b21c7f206accf0c`.
Les références originales ne sont pas rebasées ; les inodes des copies
ne sont pas présentés comme qualifiés. Le checkpoint détaillé est dans le
contrôleur fermé, `checkpoint.json`.

Comptabilisation réelle CLI : 55 lots logiques, 8 713 694 tokens au plancher
natif conservateur. La correction positive est 1 185 692 par rapport au
plancher précédent, sans relever de plafond ni additionner le temps parallèle.
Il ne s'agit toujours pas d'une mesure API ou d'une facture.

L'état effectivement relu reste `active`, `DISCOVER`, zéro ronde et 23
transitions forcées historiques. Les calibrations test/UI/captures/réseau/logs
sont expirées ; ces canaris ne les renouvellent pas. HEAD documentaire
`96371340…`, source historique `b517daed…`, sans diff `src/tests/scripts`.
Les modifications antérieures de la carte et de la fiche release restent
hors de ce lot. Ni tag, build produit, release, installation, publication,
heartbeat prolongé ou donnée réelle ne sont modifiés.

### Raccord de portée et résumé des lancements, gel pur suivant

Copie neuve `root-stage-scope-pure-RLhd2r`, index `8608ed00…`, 35 références
rehashées. Deux sources changent seulement : Session dérive les champs
`launched_services` et `unlaunched_handles` des handles réellement enregistrés,
avec birth libérée et reçu de démarrage ; le consommateur exige désormais
la portée et la ronde exactes. Une liste de handles non lancés vide ne prouve
pas la présence de toutes les étapes du plan.

La portée est dérivée après relecture de l'admission initiale. Les modes
canari ne sont jamais acceptés comme A/B. Le vrai `finish` tente le nettoyage
avant ce contrôle : admission refusée ou mutée produit une portée non vérifiée,
une erreur et un taint avant tout reçu vert. Cette copie ne contient pas encore
le loader listener V4 ; son étiquette disponible ne l'admet pas.

L'auteur exécute 43 tests purs puis root les rejoue séparément, code 0,
pytest 0,26 seconde côté root, stderr vide, sources avant/après identiques.
Les trois cas du vrai `finish` vide passent : admission valide, refusée, mutée.
Stdout root SHA-256
`9f9543cc1aa7e6121251c77d4356209dcb37ea7f10026236941f6b7dcaa80019`.
Il s'agit des mêmes 43 cas sur deux exécutions, pas de 86 tests distincts.
La revue indépendante est favorable au delta fermé, sans qualification OS.
Les anciens 37 tests de relais sont copiés, pas relancés dans ce lot.

Les deux arbres source/preuves root sont conservés ; comparaison byte-exacte
41 fichiers, 444 568 octets, manifeste SHA-256
`f2d2c5c3be27fbe6c73e144fc1d9bd1e42e9c47b144759122b6c91e1f2ce67aa`.
Checkpoint : `qualification/scope-root-closed-FtuXAG7m/checkpoint.json`.
Les vieux gels et bruts sont inchangés. Budget CLI : 56 lots logiques,
8 967 975 tokens au plancher conservateur ; plafond GPT effectivement relu
à 10 000 000, inchangé. Ce plafond n'est ni une cible à consommer, ni une mesure
de facturation.

La lecture ciblée G5 confirme pourquoi le raccord réel reste nécessaire :
`g5_capture_port.py` porte cinq appels, mais son helper renderer lance directement
l'enfant sans capture préalable G1. Le `JointOwner` mesuré, lui, utilise une
fixture, une birth et des slots uniques. Le prochain port doit conserver son
rendez-vous pré-lancement et sa barrière de birth, puis indexer les demandes
par étape/nonce et traiter les marqueurs normaux et timeout avec leur ACK exact.
Une bascule de flags ou la copie du renderer ne qualifie pas ce mécanisme.

Aucune nouvelle ronde, calibration, capacité, release ou publication.
HEAD documentaire à cette revue : `390d2ec4…` ; les pins historiques source
`b517daed…` ne sont pas retargetés. L'admission, les quatre capacités, les profils
complets, le raccord listener/multi-enfants et le watchdog global restent à
qualifier avant les deux rondes réelles. Le goal natif reste actif ; ce suivi
ne prolonge pas le heartbeat expiré.

### G5 séquentiel : trois enfants inertes réellement mesurés

Lot du 7 octobre, clôture des preuves vers 19 h 25 UTC. Branche documentaire
`codex/cycle-17`, HEAD avant ce lot `bb56eb47…`, push précédent réellement
terminé et référence distante concordante. Le GO humain sur les métadonnées
de `/private` et `/private/tmp` ne vaut ni nouveau périmètre ni publication.
La QA native isolée reste dans le périmètre du précédent « termine ».

La copie neuve `G5-sequential-source-3yaUMY`, index SHA-256
`2dc83d82aa1f6efd8751899dca4268d8abb1e06d0af70534f22508b957a97a0d`,
11 504 octets, ferme exactement trois fixtures Python directes. G1, gate
initial, SQL r08 et fixture restent byte-exacts au gel mono précédent.
Les sept deltas, préimages et défauts pré-revue sont conservés. Aucun ancien
reçu n'est relabellé, rebasé ou présenté comme mesure de cette copie.

Quatre incohérences de l'instrument sont corrigées avant le canari OS :
bootstrap de la clé contrat absente, audit du namespace par noms exacts,
rehash final des ACK même après sortie immédiate du helper, puis inclusion
du gate physique dans les sept références de chaque enfant. Elles ne sont
pas classées comme bugs THÉRÈSE. Root lit les sources/deltas, et deux agents
relisent le gel sans import G1 complet ni exécution OS.

L'auteur mesure 72 tests purs puis root rejoue séparément les mêmes cas :
code 0, 13 pins avant/après inchangés. Root relit les deux flux et rehash
29 références du reçu pur ; stdout indique `FULL_G1_IMPORTED False`.
Stderr contient le rapport unittest avec 72 noms `ok`, pas un flux vide.
Reçu root SHA-256
`4e1fc13093ee20b70923c5686370e3a975d8bf78a9e4bccf51eac735ab402bf2`.
Ce sont 72 cas distincts, pas 144 ; les anciens tests mono ne sont pas rejoués.
Les doubles et extractions AST ne deviennent pas des observations du kernel.

La table parent ferme index, nonce, argv, cwd, environnement intégral,
bornes et sinks distincts avant le premier enfant. Chaque lancement exige
un grant de la vraie Session, puis capture de birth et réservation du rôle
avant release du workload. Le helper consomme l'ACK exact avant la demande
suivante, qui rejoint cet ACK. Outer 30 s et cleanup 8 s restent inchangés ;
un budget frais insuffisant refuse un enfant, sans promesse de faire rentrer
les trois pires cas dans ces 30 secondes.

Après les revues et deux GO root exacts séparés, deux canaris OS sont mesurés :

- Positif, `G5-sequential-positive-8_f07gq4` : trois terminaisons normales,
  aucun signal enfant, helper exit 0, pas de taint, stage et Session fermés.
  Durée du reçu 0,985864959002356 seconde ; SHA-256
  `07b3d31b9cce03cc0a5bacefeb5fec79a88f1451a9663f15bf6c4d1a70fe4b85`.
- Timeout, `G5-sequential-timeout-_8ixi59t` : deux enfants normaux puis le
  troisième borné à 2 s, cleanup 0,07013858400750905 seconde. Les cinq signaux
  SIGSTOP/SIGTERM/SIGCONT ciblent seulement sa birth
  `20924/1791400872/81091`, jamais le helper `20921`, vivant avant l'ACK.
  Helper exit 86, taint monotone, stage `raw_stable=false`, erreur d'instrument
  conservée. Aucun quatrième enfant observé, aucune assertion métier verte.
  Durée du reçu 2,9849783749959897 secondes ; SHA-256
  `09cd43ba4fa002a0ba5a24abdefd510c26cfa349fbbb36dbcec90b47e09627c7`.

Les deux wrappers sortent 0, sans événement watchdog coopératif de 90 s ;
stdout/stderr exclusifs sont conservés, stderr OS vide. Le code du wrapper
ne remplace pas le contrôle des bruts. Root vérifie physiquement 105
références et 38 hardlinks : tableaux, GO, grants, gates, releases, markers,
cleanups, ACK, flux et stages/stops. Les ACK consommés sont chaînés et les
six births/rôles/sinks sont distincts. Rapport SHA-256 `4909b203…`.
Une seconde relecture indépendante lit tables, demandes, flux helper,
cleanups et fermeture, sans relancer ce vérificateur ni prétendre recompter
ses 105 références. Aucun défaut concret dans cette portée limitée.

Le contrôle root `ps` sur les seuls dix PID déjà attribués retourne code 1,
aucune ligne ni erreur. Aucun signal externe, aucun profil réel ni port réel
inspecté ou modifié. La comparaison produit `git diff --quiet b517daed… --
src tests scripts` retourne 0. Les pins historiques restent historiques.

Sources et trois arbres de preuves sont copiés dans quatre destinations
neuves sous `qualification/G5-sequential-*`. Comparaison byte-exacte :
179 fichiers, 1 591 397 octets ; manifeste `G5-sequential-copy-manifest-20261007.json`,
SHA-256 `a132a4c3acc71188a06dc5596d8040229e7af6f37e1cabe9bd063c7ea1a6e2fd`.
Les inodes/hardlinks des copies ne sont pas qualifiés et les références
originales ne sont pas rebasées. Contrôleur fermé et détail des preuves :
`qualification/G5-sequential-root-closed-lGxqUtsK/checkpoint.json`.

### Deux releases existantes vérifiées en lecture seule

Le skill Codex `release-therese`, sa commande canonique Claude et sa checklist
sont lus pour la vérification. Aucun lock de publication, merge, bump, tag,
build, installation ou message Discord n'est lancé. Les rapports canoniques
restent `docs/releases/v0.77.2-alpha.md` et `docs/releases/v0.77.1-alpha.md` ;
les changements préexistants de ce dernier sont préservés.

Les API GitHub effectivement consultées confirment les deux dernières releases
publiées : `v0.77.2-alpha` le 4 octobre à 15:47:27 UTC et `v0.77.1-alpha` le
2 octobre à 07:59:38 UTC, dix assets chacune, non brouillons et préreleases.
Les deux workflows existants sont `completed/success`, sur les commits
indiqués par leurs métadonnées ; aucune CI n'est relancée.

Le GET public de l'updater sert 0.77.2, sept plateformes, URLs du bon tag.
Ses 5 260 octets et SHA-256 `5794240f…` concordent avec le digest de l'asset
GitHub. Le GET de la landing contient `Alpha v0.77.2` et trois liens du même
tag. Cette vérification HTTP n'est ni une recette visuelle, ni un nouveau
contrôle des binaires/signatures ou de l'installation. Relevé réel dans
`qualification/G5-sequential-root-closed-lGxqUtsK/release-readonly-checkpoint.json`.
Aucune nouvelle release préparée ou publiée.

### Limites et point de reprise

Le prochain port doit encore traiter les helpers indirects, Node/Vitest et
les sorties métier normales non nulles, puis raccorder les cinq appels réels.
Le gate actuel est Python seulement et le helper doit être enfant direct
de G1. Ce canari ne qualifie ni petits-enfants, ni fork hostile exhaustif,
ni héritage des FD, ni primitive atomique birth/signal ou hard realtime.
Les quatre caps, l'admission FULL, les profils/API complets, le loader listener
et le watchdog global restent fermés. Il manque aussi un gel du HEAD courant,
cinq calibrations fraîches et les deux rondes réelles indépendantes A/B.

Budget CLI effectivement relu après correction positive de 713 707 tokens :
57 lots logiques, 9 681 682 tokens au plancher natif conservateur, pas une
facture API. Plafond GPT 10 000 000 inchangé, contrôle `Budget: PASS` ; le
plancher laisse 318 318 tokens à cet instant, avant la fin documentaire.
Ce reste ne garantit pas l'achèvement des rondes/release. Aucun plafond
n'est relevé ni temps parallèle ajouté. L'état reste `active`, `DISCOVER`,
zéro ronde, 23 transitions forcées historiques. Aucun canari ne renouvelle
les calibrations expirées. Goal natif actif, heartbeat non prolongé, pas de
publication ou d'action sur les données réelles.

## Lot 58 : vrais appelants G5, politique de sortie et coupe-circuit

Le renderer G5 et les cinq sources originales sont relus, avec trois avis
distincts terminés. Les appels ne sont pas des fixtures interchangeables :
pytest/Vitest attendent 1/0/1/0 et des XML exacts ; le témoin réseau Node attend
un code non nul et son oracle JSON ; le mutant SQL doit retourner 1 avec la
bonne assertion avant que son wrapper puisse conclure. Les bornes et les
environnements métier doivent rester distincts du contexte des helpers.
Les cinq remplacements ne couvrent pas Git, Chrome Playwright et `lsof`.

Arbitrage technique : un lancement centralisé dans la Session root paraît
viable, sous nouveau contrat causal et transport non bloquant pendant
`Session.wait`. Le parent OS observé et la chaîne logique demandeur/enfant
ne doivent pas être confondus. Le relais root/stage existant ne fournit pas
ce transport. Aucun RPC de lancement n'est implémenté ou mesuré dans ce lot,
aucun reçu ancien n'est requalifié. Détails et conditions de reprise dans
`qualification/G5-real-port-policy-E3PqfI/REPRISE-RPC.md`.

Root exécute six tests purs du corps AST réel de `Session.wait`, avec doubles
de processus, ledger et fermeture. Codes métier 0/1/2 conservés ; timeout,
taint et cleanup incomplet refusés. Code 0, six cas distincts verts, sans
import G1 complet, processus OS ni produit. Root rehash 74 références du reçu
et constate les 35 pins source avant/après inchangés. Ce n'est ni un test du
transport proposé, ni un canari réel, ni une calibration ou une ronde.
Reçu `de067fde007570967cd507666e8764f86eda9b8babffda86f1ea1cedb8d74662`,
15 878 octets, conservé avec les six stages explicitement synthétiques.

Le nouveau dossier fermé est archivé sous `G5-real-port-policy-E3PqfI`.
Copie byte-exacte effectivement contrôlée : 13 fichiers, 31 559 octets.
Manifeste `G5-real-port-policy-copy-20261007.json`, SHA-256
`365e93456862ddb42058a7ec44a036d9cca0bad2d0bf6522ebc318feed8584d5`.
Ni inodes de la copie qualifiés, ni références originales rebasées.
Les anciens gels, le produit et les modifications préexistantes sont préservés.

La lecture native du goal donne 10 019 552 tokens conservateurs. Correction
positive effectivement enregistrée : 337 870 tokens, un lot logique, durée 0
pour ne pas additionner le temps parallèle. Usage local : 58 lots et
10 019 552 tokens, plafond GPT 10 000 000 inchangé. Ce compteur n'est pas une
facture API. `record-usage` et `budget-check` sortent 75 ; le second indique
`Budget: STOP`. `next-action` retourne `[arret] DISCOVER` pour dépassement.
Aucune nouvelle exécution ou implémentation n'est lancée après ce constat.
La clôture, la documentation et leur sauvegarde sont seules poursuivies.

Le relèvement exact de 10 à 12 millions est demandé à Ludo et reste sans
réponse humaine dans ce lot. Pas de `new-cycle`, de hausse implicite ou de
transition forcée pour contourner ce coupe-circuit. Le goal reste actif et
non accompli : transport réel, attribution complète, HEAD frais, cinq
calibrations et deux rondes indépendantes manquent toujours. Aucune nouvelle
release, publication, installation ou prolongation du heartbeat.

## Reprise du 8 octobre : suppression humaine des plafonds de tokens

Ludo demande de continuer jusqu'à la fin puis précise : « pas de plafond en
token ». Cette dernière instruction remplace la proposition de relèvement
à 12 millions ; elle ne supprime aucun gate de QA, de plateau ou de release.

Le code actuel de `budget_reasons` interprète `0` comme limite désactivée.
Root met donc uniquement `limits.max_tokens.{claude,grok,gpt}` et
`limits.max_total_tokens` à 0 dans le budget local, sous le verrou canonique
et par écriture atomique. L'historique complet, les cycles, les limites
d'appels 300/38/150 et la limite murale 5 798 minutes restent inchangés.
Les fichiers globaux du skill Claude ne sont pas modifiés. Le comptage
d'usage continue ; il ne s'agit pas d'une mesure de facturation API.

La sauvegarde d'avant mutation, le script exact et le reçu sont archivés
dans `qualification/TOKENS-SANS-PLAFOND-20261008-gObOf0ef`. Les trois `cmp`
source/copie sortent 0. SHA-256 budget avant :
`54769026dcdf9d79a6e2b5a60efa0bc92c78fbb916da87995676c3437aa87017` ;
juste après mutation :
`285c705e3789baf4b30e13fe96ab63d52f408f83f847d014f126656c3ff6478e`.
Ces empreintes décrivent ce changement, pas les futurs ajouts d'usage.

Le contrôle effectif retourne `Budget: PASS`, code 0, et `next-action`
`[continuer] DISCOVER`. Les cinq calibrations restent expirées ; les travaux
reprennent par la réparation de l'instrument RPC, sans qualifier une chasse
ou une ronde à partir de ces instruments. Trois agents distincts reprennent
transport, adaptation de Session et tests des cinq vrais wrappers, sous un
dossier neuf. Ni transition forcée, ni nouvelle release dans cette reprise.

## Lot 60 : transport RPC implémenté, premier canari Mac rouge

La transition normale `DISCOVER → CALIBRATE` est effectivement enregistrée
le 8 octobre à 07:47:30 UTC. Le cycle reste actif ; aucun gate ou plafond de
temps/appels n'est contourné. Les cinq calibrations expirées ne sont pas
renouvelées par les travaux qui suivent.

Le nouveau transport possède quinze commandes fermées, des contextes
préémis sans PID futur et une empreinte de plan extérieure au contexte.
La vraie birth est enrôlée après le gate et avant sa libération. Le peer
Unix est observé hors payload ; les codes bruts non nuls restent conservés.
Root corrige aussi une course Darwin : garder la connexion après l'ACK
jusqu'à fermeture du client permet sa dernière vérification `LOCAL_PEERPID`.
Les capacités produit/FULL restent toutes fermées.

Après gel et relecture distincte, root rejoue six suites pures :
15 + 47 + 17 + 68 + 27 + 2 = 176 cas distincts, zéro erreur/échec/saut.
Les 24 pins communs sont identiques avant/après chaque suite et rehashés
ensuite, ainsi que les six reçus et leurs douze sorties brutes. Les mêmes
47 corps de wrappers sont également rejoués par un autre agent ; ils ne
comptent pas comme 47 cas supplémentaires. Les essais intermédiaires
restent historiques. Aucun de ces tests purs ne qualifie G1/kernel/Seatbelt.

Le premier lancement natif root est réellement exécuté dans
`/private/tmp/therese-c17-rpc-canary-positive-7gdu85a5`, avec seize sources
copiées byte-exactes et un profil jetable. Résultat final : code 86,
`unqualified_instrument_or_lifecycle`. Les deux parents inertes retournent
86 avant toute requête RPC : leur contrôle confondait création d'une socket
IP et accès réseau. Le second socket Unix vivant est bien refusé, errno 1 ;
la création TCP est permise, sans qu'une connexion TCP ait été tentée.
Ce refus de qualification n'est ni une fuite démontrée, ni un bug produit.

Les deux births lancées sont terminées, sans handle attribué restant,
ambiguïté, erreur ou signal de nettoyage. Le reçu d'arrêt indique
`session_closed=true`, `clean=true`, borne respectée, 0,006509875 s.
Les seize sources sont rehashées inchangées après l'essai. Aucun enfant
RPC/Node n'a encore été lancé ; l'identité Unix du transport et son timeout
ne sont donc pas qualifiés. Une nouvelle copie séparée prépare des témoins
connect/send vers des counterparts loopback vivants, sans élargir le profil.

Le gel précédent, ses préimages, les 176 cas, les lectures publiques et ce
canari rouge sont sauvegardés dans l'archive locale ignorée
`qualification/RPC-G5-lot60-20261008-gObOf0ef/PROOFS.tar.gz`, 11 277 107 octets,
SHA-256 `cea6b4d5faf559fb55a47c86edbb952dd9ff5cf4969f28f755a3d576aff73516`.
Copie `cmp` réellement égale. Les sockets et caches Python sont exclus ;
les références/inodes originaux ne sont pas réécrits ou requalifiés.
L'index root archivé est `ROOT-FREEZE-20261008.json`, SHA-256
`2a1159a621747d69288bcde870b4122359a3df820b6f471921de8b76c2f2997d`.
Les faits du contrôle des deux releases publiques sont dans le snapshot
archivé `public-releases-20261008.json`, avec les réponses landing/updater.
Ce contrôle n'a modifié aucune publication et ne revérifie pas les binaires.

Usage consigné : 60 lots logiques, plancher natif conservateur 11 926 892
tokens, correction positive de 1 514 242 ; durée ajoutée 0 pour ne pas
additionner le travail parallèle. Ce n'est pas une facture API. Le contrôle
effectif retourne `Budget: PASS`, code 0. L'objectif natif reste actif et
inaccompli : HEAD frais, cinq calibrations et deux rondes indépendantes
restent requis avant le processus de release.

## Lot 61 : canaris RPC natifs positif et timeout fermés

Le témoin réseau corrigé tente connect TCP et sendto UDP vers trois
contreparties root-owned locales vivantes, et non la seule création de
socket. Le profil SQL reste byte-exact. Le nouveau gel Nv1rIK possède
25 pins communs ; sept suites pures rejouées par root donnent
15 + 47 + 17 + 68 + 27 + 2 + 2 = 178 cas distincts, sans erreur/échec/saut.
Les mêmes 47 corps rejoués par un autre agent ne sont pas des cas nouveaux.
Ces pures ne qualifient pas le kernel ou les vrais parcours métier.

Le positif réel, racine `therese-c17-rpc-canary-positive-jd1peu7_`,
sort 0 : deux parents 0 reçoivent fidèlement Python 1 et Node 2.
Les sorties sont distinctes, les peers réels rejoignent les births demandeurs,
les ACK rejoignent les demandes, reçus et nettoyages. EPERM est observé pour
les trois tentatives Unix/TCP/UDP précises ; aucune lisibilité n'est observée
sur les contreparties pendant les snapshots. Cela ne démontre pas une
interdiction exhaustive de tout réseau. Stop fermé, clean/stabilité vrais,
aucun signal ou résidu attribué ; cleanup stop 0,006830208 s.
Résultat SHA-256 `d111b5f4c1cbff310c17c2b2db14c03af5ab9d70bf40d588ae553fa6810b03a5`.

Le négatif réel, racine `therese-c17-rpc-canary-timeout-ih9vq0d0`,
conserve la borne enfant 240 s. L'enfant retourne -15 après nettoyage
0,056500958 s ; cinq signaux ciblent exclusivement sa birth connue.
Le parent retourne 86 avec erreur instrument. Audit attendu
`expected_timeout_red_observed`, jamais réussite métier. Stop fermé,
handlers restaurés, aucun handle/restant/ambiguïté/erreur de cleanup ;
sa durée vaut 0,008491416 s. Le champ stop clean reste faux et la stabilité
fausse par taint monotone, malgré cleanup.clean vrai et zéro résidu.
Résultat SHA-256 `2ffee72281b3a0bc7436b6deef39d286288ecaf37cb7fb12327dbc07cb2ea115`.

Root rehash 60 puis 41 références physiques, les 16 copies source de
chaque essai et leurs originaux. Une relecture distincte des bruts par
l'auteur du transport, non exécuteur des canaris, vérifie aussi les joins,
enveloppes, digests et paires hardlink. Rapport `REVIEW.md` SHA-256
`95007f76da59939bcb6f7065f8b38c9eb87e34003e15e2a0967315210f4f9a81`.
La vérification répétée des refs est regroupée dans
`root-close-verifier/verify-closed-rpc-proofs.mjs`, lecture seule sans
processus enfant ni réseau. Le premier canari rouge reste inchangé.

Archive locale ignorée byte-exacte, 3 708 186 octets :
`qualification/RPC-G5-lot61-20261008-Nv1rIK/PROOFS.tar.gz`, SHA-256
`22cd2188db9a47c18fe723eb55b980b86a56d5f2efd1dd7ba5b5aa5def0f895a`.
Les références et inodes originaux ne sont ni rebasés ni requalifiés.
Les bindings conservent leur HEAD documentaire 542cc6f7 ; le gel distingue
le HEAD repo observé 6cb01029. Aucune ronde actuelle n'en est déduite.

Le prochain raccord est préparé séparément : constructeur des onze sorties
RPC et table15, G1/listener/web instrument-only puis Git/Chrome/lsof indirects.
Il ne nécessite pas encore les recettes/density/package78, mais les cinq
axes de boucle et le sixième axe screen_coverage du consommateur FULL
devront être recalibrés sur une vraie pile QA fraîche et le HEAD gelé.
Toutes les admissions FULL restent fermées ; zéro ronde ou release nouvelle.

Usage consigné : 61 lots logiques, plancher natif conservateur 12 817 563
tokens ; ajout 890 671, durée 0, pas une facture API. Contrôle effectif
`Budget: PASS`, code 0, phase CALIBRATE active. Les plafonds de tokens
restent désactivés ; ceux de temps/appels et les gates restent inchangés.

## Lot 62 : raccord des wrappers réels, quatre essais clos

Le constructeur prépare désormais la vraie table des quinze enfants et les
cinq contextes Chrome sans PID futur. La copie produit QA est un checkout
détaché sur `2d69e30c`, avec 3 579 blobs Git, modes et octets vérifiés.
Les profils, données et ports QA restent distincts du profil réel de Ludo.
Les onze sorties de base restent byte-exactes ; l'admission est WRAPPER
seulement. Les capacités FULL, les 78 obligations et les rondes A/B restent
fermées. Aucun fichier produit, version ou publication n'est modifié.

Quatre essais natifs root sont réellement exécutés et terminent avec code
86. Aucun n'est relabellé comme une réussite produit :

- RED1 : Vite ne peut pas lire les métadonnées du parent du checkout QA ;
  aucune readiness et zéro RPC.
- RED2 : le parent `session-events` manquait ; la readiness est réelle,
  mais Vite refuse aussi `stat /`. Zéro RPC. Ces deux défauts de construction
  sont corrigés dans des racines neuves, sans relancer les racines closes.
- RED3 : sept demandes/ACK, six feuilles réellement lancées. Pytest échoue
  à la collecte du mauvais rootdir ; Vitest échoue sur DNS localhost ;
  Chrome s'arrête sur l'exception NSBundle. Le témoin logs passe.
- RED4 : rootdir pytest et host IPv4 Vitest sont bornés exactement.
  Les quatre témoins ont désormais les vrais XML : codes 1/0/1/0,
  un testcase chacun, le défaut injecté produit une assertion causale,
  sans erreur de collecte ni saut. Les deux parents test-runner/logs
  retournent 0. Chrome retourne -6 sans timeout : ses bruts montrent un
  refus Crashpad distinct et son rapport SIGABRT la pile
  `_RegisterApplication`/AppKit. Sept ACK sur quinze, aucun faux complet.

Le dernier constructeur passe 27 tests purs root, dont 16 hérités non
recomptés comme nouveaux cas ; le correctif des frontières test-runner
passe 17 tests purs. Ces pures ne qualifient pas le kernel ou FULL.
ROOT4 porte 76 références source, soit les 63 initiales conservées,
sept copies de preuves et six diffs. La préparation root rehash 4 202
références transitives courantes ; trois snapshots intermédiaires de
tests G1 restent des observations historiques du reçu, jamais des bindings
courants sur des chemins modifiés. La revue indépendante de préparation
vérifie séparément 3 777 chemins physiques et les blobs/modes du checkout.

L'arrêt physique est prouvé pour les identités attribuées des quatre essais.
Pour RED4, root vérifie 515 refs et 30 joins de signaux dans son jeu de
reçus sélectionné. La relecture indépendante vérifie 177 chemins,
37 publications hardlink et 45 occurrences de signaux, soit 15 événements
uniques sur les births backend/Vite/descendant. Aucun signal sur l'owner
ou Chrome. Les deux scans finaux de chacun des trois ports QA sont vides.
Nettoyages services puis close : 1,210509166 s et 0,939976208 s, bornes
respectées, handlers restaurés, aucun résidu/ambiguïté/erreur attribué.
Les champs originaux clean/stabilité faux, taint vrai et
`owned_shutdown_proved=false` de RED2/3/4 restent inchangés.
Ces preuves sont finies : elles ne garantissent pas l'exhaustivité de
descendants très courts. Crashpad11321 est dans le rapport macOS avec
PPID1, mais n'a pas de birth capturée dans le ledger Chrome.

Les quatre archives locales ignorées sont sous
`qualification/RPC-WRAPPER-lot62-20261008/` :

- `RED1.tar.gz` : 768 635 octets, SHA-256
  `71418861c2edb3e15eee1d3c98f28f72edf341adc5895ca8b5f2c8a2d99cb3a4`.
- `RED2.tar.gz` : 1 812 161 octets, SHA-256
  `b757566c55de9c1268bc86eba80d446399f5154bececc7a17a60b160fa9fa71a`.
- `RED3.tar.gz` : 1 931 641 octets, SHA-256
  `1934135e85944f679e3009065b7af33adbaaf56f0de433d3efd50025b9f75ff0`.
- `RED4.tar.gz` : 2 010 932 octets, SHA-256
  `91651dc7bda4b35077ce372bb0b220c9107b5dbaf4b320adc0eace189940934e`.

`PREPARATIONS.tar.gz`, 69 001 octets, SHA-256
`28699c7b8c08d84710f4358c6be0963209c3f2f06452786a7a82e282f69d469e`,
conserve séparément le builder des six calibrations closes (55 pures root),
le producteur Git A/B et sa demande après vrai stop (19 pures root),
et le candidat Chrome à deux lookups UI exacts (six pures root).
Les copies sont réellement égales par `cmp`, intégrité gzip contrôlée ;
sockets/caches exclus, références et inodes originaux non rebasés.
Ces préparations n'ont émis aucune calibration A/B réelle. Le prochain
essai Chrome doit encore valider les deux lookups issus de ses diagnostics,
sans permission globale Mach/presse-papiers/TCC/profil personnel/Internet.
Le raccord FULL, notamment ses bindings tardifs et la lecture bornée des
trois décisions externes par le builder, reste à qualifier séparément.

Usage consigné : 62 lots logiques, plancher natif conservateur 18 024 955
tokens ; ajout 5 207 392, durée ajoutée 0 pour le parallèle. Ce n'est pas
une facture API. Le contrôle effectif retourne `Budget: PASS`, code 0.
Les plafonds de tokens restent désactivés conformément à Ludo ; les
limites de temps/appels et les gates restent appliquées. Phase CALIBRATE
active, zéro ronde de plateau actuelle et aucune release nouvelle.

## Demande pour la prochaine boucle : actualiser les modèles

Ajout de Ludo le 8 octobre 2026 : intégrer les derniers modèles disponibles,
en particulier Sonnet 5.5, Haiku 5.5, GPT-6.1 Sol, et examiner Grok 4.7 et
Mistral Large 4. Cette demande vise la prochaine boucle, pas un élargissement
du cycle 17 ni de la release actuellement en qualification.

Le triage documentaire du 8 octobre confirme les cinq noms sur des pages
officielles ouvertes par root et un relecteur indépendant. Ce relevé sera
revérifié au moment de l'intégration. Il ne prouve ni l'accès des comptes
de Ludo ni la compatibilité réelle des providers actuels.

| Candidat | Identifiant API documenté | Fiche officielle |
| --- | --- | --- |
| Sonnet 5.5 | `claude-sonnet-5-5` | [Anthropic](https://platform.claude.com/docs/en/models/sonnet-5-5/overview) |
| Haiku 5.5 | `claude-haiku-5-5` | [Anthropic](https://platform.claude.com/docs/en/models/haiku-5-5/overview) |
| GPT-6.1 Sol | `gpt-6.1-sol` | [OpenAI](https://developers.openai.com/api/docs/models/gpt-6.1-sol) |
| Grok 4.7 | `grok-4.7` | [xAI](https://docs.x.ai/developers/grok-4-7) |
| Mistral Large 4 | `mistral-large-4` | [Mistral, Public Preview](https://docs.mistral.ai/models/mistral-large) |

Points à ne pas réduire à un ajout de libellé : GPT-6.1 Sol exige Responses
pour les appels d'outils ; Sonnet 5.5 documente des ruptures de compatibilité
sur les outils et les blocs de réflexion. La variante Grok 4.7 Fast n'est
pas disponible sur l'API publique selon sa fiche. Aucun second identifiant
Mistral masqué par « +1 » n'est inventé.

Travail prévu : mettre à jour la source unique
`src/backend/app/services/modeles_catalogue.py`, les adaptateurs strictement
nécessaires et leurs tests ; vérifier streaming, outils, raisonnement,
limites de contexte/sortie et sélection persistée dans l'interface.
Préserver les réglages existants et les modèles encore supportés ; ne pas
changer de modèle par défaut ni retirer une génération sans décision
explicite. Les tests de disponibilité réels devront être bornés, sans
données personnelles, avant toute annonce de compatibilité.

## Lot 63 : deux nouveaux essais rouges clos, lecture Q bornée

Les essais ROOT5 et ROOT6 sont réellement exécutés par root dans deux
racines QA neuves. Ils retournent 86, avec sept demandes/ACK sur quinze
et aucune qualification FULL ou ronde A/B. Les champs originaux faux de
réussite, stabilité et owned shutdown ne sont pas réécrits après nettoyage.
Le checkout produit détaché reste `2d69e30c`, différent du HEAD documentaire
`c2acd0da` observé au lancement : il sert seulement au canari WRAPPER.
Une future ronde complète exigera un nouveau checkout au HEAD courant.

ROOT5 dépasse le précédent blocage AppKit, puis Chrome retourne 21.
Ses bruts montrent le refus de bind du `SingletonSocket` sous le TMP QA
et un refus Crashpad Mach distinct. Le candidat suivant ajoute seulement
le domaine de socket Unix et le bind sous `TMP_ROOT`, sans port IP,
lookup Mach ou écriture hors QA supplémentaires. Cinq tests purs root
vérifient ce delta ; ils ne prouvent pas son comportement kernel.

ROOT6 utilise ce profil exact de 1 698 octets, SHA-256
`9c6d17def6fa847f0740bb2398d52a8ef6dfc3a8279563dd1bda815d7892e872`.
Le constructeur V5 passe les 34 tests purs root et une revue indépendante.
La préparation rehash 4 565 refs transitives courantes, vérifie les 3 579
blobs/modes du checkout et les 36 sources SQL ; les relations B1753/B1760
restent identiques. L'autorité SQL fraîche est externe au contrat,
dont `root_reviewed=false` reste intact. Aucun succès historique n'est
réutilisé comme calibration courante.

Dans ROOT6, les quatre XML témoins pytest/Vitest ont leurs codes causaux
1/0/1/0 et les deux contrôles logs passent réellement. Chrome25577 retourne
-11 sans timeout ni interruption. Ses 600 octets stderr conservent le
refus Crashpad25605 et deux avertissements CFURL ; le rapport macOS exact
du PID25577 montre SIGSEGV à 0x10 dans IONotificationPortGetRunLoopSource.
Ces observations seules ne prouvent pas une cause unique. Le descendant
25622 est attribué dans le ledger ; Crashpad25605 ne possède pas de birth
capturée, donc aucune exhaustivité de descendants très courts n'est annoncée.
Résultat ROOT6 SHA-256
`d1afb85175ed28facf8cc82fb9015a666a795efbc13bca9f6b3fe62729ac5cd1`.

Les arrêts physiques des identités attribuées sont vérifiés. ROOT5 :
services 1,035203375 s, close 0,954089792 s ; ROOT6 : 1,276678833 s et
1,045646250 s. Les bornes de huit secondes sont respectées, les handlers
restaurés et les ports 17593/5173/17594 absents. Zéro résidu, ambiguïté ou
erreur de cleanup attribué. Root relit 943 refs pour ROOT5 et 1 058 pour
ROOT6, avec 30 joins de signaux dans chaque jeu sélectionné. Pour ROOT6,
la revue indépendante rehash 3 880 chemins, vérifie 50 liens de parenté,
37 publications hardlink et 15 événements uniques de signaux ciblant
seulement backend/Vite. Le résultat original reste rouge et FULL fermé.

La lecture Seatbelt Q est testée séparément. V1 conserve son échec natif :
le lanceur Apple Python appelle xcode-select et est refusé avant le témoin.
V2 utilise le binaire Python QA physique déjà conforme, sans ajouter de
droit au profil. Le canari natif lit trois fichiers synthétiques hors des
cinq sous-arbres larges ; le quatrième fichier, existant mais non passé
en paramètre, est refusé avec EPERM. Les deux processus sont reapés, sans
signal, interruption ou erreur de cleanup. Root rehash 28 refs et une
revue indépendante confirme les argv et les bruts. Ce succès qualifie
uniquement les fixtures synthétiques, pas les trois décisions réelles du
builder, G1, FULL ou une ronde A/B.

Les préparations restent distinctes et fermées : contrat FULL31 et son
rejeu root31 ; Q18 et root18 ; raccord HEAD/checkouts/bindings tardifs
FULL25 et root25 ; candidat auxiliaire A/B14 v2 et root9. Les 14 éléments
désignent des invocations Chrome, pas 14 obligations réussies. Ses contrôles
sont lexicaux ; `activate()` refuse toujours. Le lecteur SQL/RPC en cours
dans un autre gel n'est ni intégré ni inclus dans les archives de ce lot.

Quatre archives locales ignorées, copies exactes et gzip/tar vérifiés,
sont indexées sous `qualification/RPC-lot63-20261008/INDEX.json` :

- `ROOT5-closed.tar.gz`, 5 701 575 octets, SHA-256
  `f6fb08178057e2a18fb94c4518bf10bfa516bbb65554b23fab499a1233f52a57`.
- `Q.tar.gz`, 39 453 octets, SHA-256
  `86fbbe856f2b6feb041fe4d4e18a5dd1ca00bd2b7494b7ca43cfaaab90cdd3dd`.
- `PREPARATIONS.tar.gz`, 443 107 octets, SHA-256
  `bcf2d248d3ad8260b8171db6c64ac7a4aa5a4b7bc400d4406f4500531639d6b8`.
- `ROOT6-closed-and-preparations.tar.gz`, 5 829 491 octets, SHA-256
  `9479adf77613fd3bf948d314c8c64863891092f21d091a071bc5093791ac4caf`.

Les références/inodes originaux restent historiques, non rebasés sur une
extraction ; sockets et caches sont exclus. Les AppleDouble sont des
métadonnées, pas des preuves. Les neuf documents déjà modifiés sont
comparés à leurs hashes de départ et restent inchangés. Aucun changement
produit, main, version, tag, installation, landing, updater ou Discord.

Usage effectivement consigné : 63 lots logiques, plancher natif conservateur
20 360 520 tokens, ajout 2 335 565, durée ajoutée 0 pour le parallèle.
Ce n'est pas une facture API. Le contrôle retourne `Budget: PASS`, code 0.
Tokens sans plafond ; limites de temps/appels et gates inchangées.
CALIBRATE reste active, zéro ronde actuelle et aucune release nouvelle.

## Lot 64 : diagnostic IOKit, copie Chrome stricte et lecteur SQL/RPC

Le diagnostic kernel ROOT6 est collecté en lecture seule sur la fenêtre
du PID25577 et de son descendant25622. Ses 88 événements sont conservés
intégralement. Le refus de `iokit-open-user-client RootDomainUserClient`
est joint au même PID et au thread4420066 du rapport macOS, juste avant
le crash. Cette jonction motive un essai ; elle ne prouve pas encore une
cause unique ni une correction runtime.

Le candidat Chrome ajoute uniquement cette classe IOKit exacte, soit
216 octets. Ce droit possède une surface système réelle, au-delà des seules
notifications d'alimentation ; il n'est pas présenté comme inoffensif.
Les cinq tests purs root passent. Le constructeur V6 conserve les autres
commandes, sources, SQL, environnements et bornes ; ses 37 tests purs root
passent avec une revue indépendante favorable pour préparation seulement.
Le profil reste non qualifié et aucun nouveau canari n'est lancé dans ce lot.

Le contrôle strict initial de Chrome installé est rouge. L'audit hors
sandbox précise le refus : FinderInfo sur des dossiers du bundle.
La vérification profonde ordinaire et le strict du framework passent ;
la signature Google/Apple est réellement vérifiée, sans transformer
le strict rouge du bundle original en réussite.

Une copie Chrome indépendante est préparée sous
`/private/tmp/therese-c17-chrome-qa-copy-RoZmwsja/Google Chrome.app`.
Les 1 339 entrées conservent octets, modes, UID/GID et liens ; aucun fichier
n'est hardlinké à l'original. Seul FinderInfo est retiré de 69 chemins
canoniques de la copie, avec les valeurs originales archivées. Chrome
installé et ses attributs restent inchangés.

L'écart de copie est explicite : 1 339 valeurs de `com.apple.provenance`
diffèrent déjà avant le retrait FinderInfo. Elles ne sont pas réécrites et
aucune cause système n'est affirmée. Tous les autres attributs de la baseline
de copie restent identiques après le retrait ciblé. Les deux premiers
retours rouges du collecteur sont conservés : format hexdump non reconnu,
puis comparaison des attributs source/copie refusée avant tout retrait.
Le successeur v3 exige ces limites exactes et passe réellement
`codesign --verify --deep --strict`, code 0. Reçu SHA-256
`f97793cb43454051da734685185cb5d4e5b5ffbabc516580287195ef3d32993c`.
La copie n'est pas lancée. Le constructeur doit encore lier cette cible
aux cinq argv, à G1, au profil et à un nouveau GO externe avant tout essai.
Cette vérification Google ne signe aucune release THÉRÈSE.

Une relecture indépendante rehash 26 refs et les 1 339 entrées physiques
sans écart. La quarantaine est absente des inventaires source et copie :
« préservée » signifie ici absence inchangée, pas présence attestée.

La tranche lecteur RPC/SQL est fermée et revue indépendamment : 20 préimages
byte-exactes, huit diffs reconstruits, 49 AST valides. Root rejoue réellement
48 tests : 30 nouvelles jointures et 18 cas Q repris, sans erreur ni saut,
avec références inchangées et garde anti-processus/socket/import complet G1.
Les corps AST sont testés sur des fixtures synthétiques, pas sur une ronde.
La demande SQL lie checkout/HEAD/binding/env ; ReadView est installée avant
configure. Les six records de calibration ne sont construits qu'après le
vrai stop prévu par le coordinateur. Aucun record A/B réel n'est émis ici.
Reçu root SHA-256
`aeac9be48cc34ed78f79520d821aeb52bee566d52a7fb9395f84998b88a0a111`.

Deux archives locales ignorées sont copiées à l'identique et contrôlées
gzip/CRC, headers et fin tar sous `qualification/RPC-lot64-20261008` :

- `DIAGNOSTICS-CHROME.tar.gz`, 347 893 octets, SHA-256
  `56c21015db62c1675dcece5e3b2c8238fc9cce504adb37efa431f1b0a22d5945`.
- `SQL48-closed.tar.gz`, 362 532 octets, SHA-256
  `39717feea557f62961a1e744d052680320a493a25a277152e8b039d1f227e524`.

La copie binaire Chrome est exclue de l'archive, qui conserve ses manifests,
scripts et bruts. Les références originales ne sont pas rebasées sur une
extraction. V7, raccord A/B14 et bootstrap encore en travail ne sont pas
archivés ni admis. Les neuf documents préexistants restent inchangés.
Aucun changement produit, main, version, tag, app installée, landing,
updater ou Discord. La demande modèles reste celle de la prochaine boucle.

Usage effectivement consigné : 64 lots logiques, plancher natif conservateur
21 634 059 tokens, ajout 1 273 539, durée ajoutée 0 pour le parallèle.
Ce n'est pas une facture API. Le contrôle effectif retourne `Budget: PASS`,
code 0. Plafonds de tokens désactivés ; limites temps/appels et gates
inchangées. CALIBRATE reste active, zéro ronde actuelle, aucune release.

## Lot 65 : V8 cohérent, pures rejoués et ROOT7 rouge physiquement fermé

Le constructeur V8 ferme la jonction helper/descripteurs/argv/defaults/G1 vers
la seule copie Chrome QA. INDEX `278e5a8a…`, builder `57223365…`, helper
`7922a13b…` ; profil `c9101b2a…` inchangé, sources 76, core 17 et six deltas.
Scan frais complet avant/après préparation : 1 339 entrées, types 697/635/7,
octets/modes/UID/GID/liens/inodes exacts, aucun hardlink vers Chrome installé.
Revue Shared4 favorable à la préparation, pas au runtime.

Rejeux root réels, tous sources inchangées et processus/socket/G1 interdits :

- V8 : 62 tests, outil `1b7c8b` exit 0, reçu `fea5b4f…`.
- A/B : 80 tests, outil `fe29c1` exit 0, reçu `ae3b80b5…` ; lecteur stop
  exige deux passes ordonnées sur les trois ports. Le premier rejeu rouge
  provient du harnais root sur mkdir existant, pas des sources ; 120 fixtures
  résiduelles déplacées en quarantaine récupérable, aucune suppression.
- Watchdog : 47 tests, outil `b41c89` exit 0, reçu `30258634…` ; tick léger,
  rehash complet aux frontières, pas de relèvement des bornes. Les revues
  indépendantes A/B et watchdog sont favorables aux gels fermés seulement.

ROOT7 construit par `46ae84` puis `7c03de`, exit 0 : construction
`5ac1b80d…`, root-GO `db72766e…`, contrat SQL `f4865f12…` intégralement lu.
Contrôle root `7fa3e1` : 4 666 refs, 3 579 blobs/modes Git et 36 sources SQL.
Revue physique Environment favorable, 3 788 refs. HEAD produit historique
`2d69…`, jamais présenté comme FULL du HEAD courant `ee437969…`.
Chrome fraîchement vérifié strict/deep : `73248b` exit 0, reçu `0e1b86b3…`
à 13:54:37 UTC. Aucun xattr actuel ni Gatekeeper prétendu par ce contrôle.

L'essai natif unique `b037a9` puis `c924e6` termine exit 86. Résultat
`bbf48bc1…` : sept ACK sur quinze, six témoins causaux conformes, refus avant
la feuille Node de capture navigateur. Chrome QA PID 44147 reste vivant,
sans sortie ni profil créé, puis est arrêté par les signaux attribués ;
code -15, aucun SIGSEGV inventé. La cause initiale est perdue dans l'ACK
générique de refus, ce qui reste une limite d'observabilité.

Sources inchangées et transport fermé ; cleanup physique Chrome 0,942 s,
services 1,028 s, Session 0,852 s, zéro résidu/erreur/ambiguïté et deux passes
sur 17593/5173/17594 archivées. La taint antérieure demeure vraie et les
reçus globaux restent rouges. Clôture root `419e7a` : 1 208 refs et 35
jointures signaux/birth, reçu `67ac7b0b…`. Shared4 confirme indépendamment
193 chemins, 2 078 refs, 76 sources et 36 publications hardlink.

Journaux système exacts : reçu `73e025e8…` puis `8b1c4bfd…`. Le refus ASP
de chargement du framework survient trois microsecondes après l'interruption
du wait au nettoyage ; sa causalité autonome n'est pas démontrée. Assessment
standard de la copie QA `4c4b63`, spctl code 0, reçu `92dbaaed…` à 14:04:22
UTC : accepted, Notarized Developer ID, Google LLC. Aucun disable, resign,
xattr ou Chrome installé modifié par ces scripts ; effets du cache de
politique système non mesurés. Aucun délai ni permission élargi.

Archives canoniques sous `.app-loop/cycles/17/qualification/RPC-lot65-20261008` :

- `CANDIDATS-PURS-closed.tar.gz`, 1 233 961 octets, SHA
  `fe58a30866864034b322187832e1a3a6dd76e1c9e504283e8e6b0be1d3336835`.
- `ROOT7-closed-v2.tar.gz`, 1 927 954 octets, SHA
  `9c3650d5481be4b0b4f46c47ef756b3c94544925326ae907f86bca8ad812018a`.
- `CLOTURE-ROOT7.tar.gz`, 63 538 octets, SHA
  `f97dc7df711fee6945cebe086e01fc35746b3c0ff3fdc3e93511aa685cbde8e9`.

Gzip/tar et copies vérifiés ; binaire Chrome, cache Vite et socket Unix
exclus. Les premières erreurs de routage du lecteur root sont conservées,
sans changement des bruts natifs. Le rapport de raccord FULL `e70d4fc7…`
est archivé : collisions start/stop, relais/pin et lecteur/pin identifiées,
assemblage futur encore fermé, préflight A/B et HEAD actuels non qualifiés.

Usage consigné : 65 lots logiques, plancher natif conservateur 23 564 140
tokens, ajout 1 930 081, durée parallèle ajoutée 0 ; pas une facture API.
Contrôle effectif `Budget: PASS`, code 0. Aucun produit, main, version,
tag, installation, publication ou release modifié. Zéro ronde actuelle ;
la demande nouveaux modèles reste dédiée à la prochaine boucle.

## Lot 66 : ROOT8 rouge, diagnostic précis et clôture physique

ROOT8 neuf `2cf6bb68…`, préparé à partir de V8 fermé sur le HEAD documentaire
observé `727578fe…`, sources produit historiques `2d69…` explicitement WRAPPER
seulement. Construction `b7699841…`, root-GO `a3b485f1…`, SQL `918b1027…`
intégralement lu. Contrôle principal : 4 671 refs, 76 sources, 3 579 blobs et
modes Git, 36 sources SQL. Revue Environment favorable aux sources fermées.
Signature stricte/deep de la copie Chrome recontrôlée à 14:15:10 UTC, reçu
`2e483318…`, aucun changement de la copie ou de Chrome installé.

Essai natif unique `948edd` puis `056f6a`, exit 86. Résultat original
`278e6737…`, sept ACK sur quinze, six témoins conformes, refus avant la feuille
Node. L'assessment Gatekeeper préalable n'a pas suffi. Chrome PID 48739,
birth 1791469046/912722, termine réellement à -6, sans signal de cleanup :
SIGABRT distinct du -15 de ROOT7. stderr `cc9970e5…`, 987 octets, exception
`-[NSBundle initWithURL:]: non-file URL argument`. Le rapport exact du PID a
été lu ; il ne révèle ni l'URL fautive ni sa provenance. Aucune causalité
interne n'est affirmée et aucun rapport machine brut n'est ajouté au dépôt.

Diagnostic kernel exact, reçu `ca8b417a…`, onze événements physiques. Trois
refus de lecture de répertoires, même thread 4586453, précèdent l'exception :
metadata du parent exact de la copie Chrome QA, read-data du QA_ROOT exact et
de `/private/tmp`. Hypothèse bornée proposée pour V9 : trois ajouts littéraux
de lecture uniquement, pas de subpath supplémentaire, écriture, réseau,
Mach/IOKit ni relèvement des bornes. Les refus dtracehelper, logd,
notification_center et les événements AMFI d'abort ne justifient pas de
permissions supplémentaires. V9 encore en préparation fermée à ce lot.

Clôture principale `34d707` : 1 213 refs, 30 jointures signaux/birth, reçu
`438574cc…`. Revue Shared4 : 1 456 occurrences sur 180 chemins, 76 sources,
36 publications hardlink et dix jointures gate/birth/release, aucun écart.
Quatre XML réels 1/0/1/0 conformes, logs corrélés, deux parents code 0.
Nettoyage Chrome/services/Session : 0,845453 / 1,119227 / 0,895330 s ; aucun
résidu, erreur ou ambiguïté, deux scans sur les trois ports, handlers
restaurés et transport fermé. Les indicateurs globaux demeurent rouges :
`clean=false`, taint vraie, `owned_shutdown_proved=false`, aucune admission.

Archive canonique `.app-loop/cycles/17/qualification/RPC-lot66-20261008/ROOT8-closed-v2.tar.gz` :
2 020 000 octets, SHA
`9410af66ccd1e6eec711f9663df4797e092021643d393eb1572b5e0216a2838a`.
Copie, gzip/tar et 1 538 membres vérifiés par `3311a5` ; cache Vite, binaire
Chrome et socket Unix exclus. La première archive TMP a signalé le socket,
elle est conservée sans remplacement ; v2 l'exclut explicitement. Les neuf
documents préexistants et les sources produit sont inchangés.

Usage : 66 lots logiques, plancher natif conservateur 24 164 450 tokens,
ajout 600 310, durée parallèle ajoutée zéro, pas une facture API. Budget
effectivement contrôlé PASS, limites et deadline inchangées. Aucune version,
release, publication, installation, ronde A/B ou FULL validée par ce lot.

## Lot 67 : V9 et composite relus, ROOT9 clos rouge

V9 fermé `1G4jE1`, INDEX `c217e93a…`, ajoute uniquement trois lectures
ciblées au profil V8. Revue Shared favorable aux dérivations, trente et une
autres fonctions builder AST exactes. Rejeu principal `23519e`, 67 PASS,
zéro échec/erreur/saut, reçu `9b6de42a…`, 7,165 s ; sources inchangées,
aucun import G1 complet, processus, socket ou mesure native.

Composite FULL fermé `9I2loX52`, INDEX `0f7b28ca…`, relu intégralement et
revue Environment favorable aux axes composés SQL48/A-B80/watchdog47.
Quatre sources dérivées, six modules RPC matériels, reader `fd5256f0…`
et relais `9b271297…`. Rejeu principal `cb5a6f`, 71 PASS, reçu `e36231ba…`,
1,597 s : les 47 mêmes assertions watchdog et 24 raccords, aucun nouveau
dénominateur runtime. Chrome original/profil A-B restent non qualifiés.
Le constructeur physique, les API/contexts workers et les consommateurs
FULL actuels restent des travaux séparés ; un import uuid manquant a été
repéré ensuite, sans modifier le composite fermé ni ROOT9.

ROOT9 neuf `42f8fa9d…`, HEAD documentaire observé `9bbee124…`, QA produit
historique `2d69…` explicitement WRAPPER. Construction `e4596471…`, GO
`556f0475…`, SQL `206c301f…` lu entièrement. Contrôle principal `5a5bb5` :
4 706 refs, 76 sources, 3 579 blobs/modes, SQL36. Préflight Shared favorable :
4 036 occurrences, 3 769 chemins, core17 et six dérivations/sept diffs exacts,
Chrome5/options/sinks cohérents. Signature stricte/deep QA recontrôlée à
14:40:00 UTC, reçu `54e114c5…`, aucun changement de Chrome installé ou QA.
La readiness WRAPPER n'appelle pas l'export listener affecté par uuid.

Natif unique `4531c3`, clôture `fb5fb4` exit86 : résultat original `c094078b…`,
sept ACK sur quinze, six témoins initiaux conformes, septième refus avant
la feuille Node, pas de birth inventée. Chrome PID56446,
birth1791471012/453073, owner56102 birth1791470968/512200 ; exit -9 après
STOP trois fois/TERM/CONT/KILL de nettoyage exact. stderr `a45faf9d…`,
3 027 octets, sans exception NSBundle visible. Diagnostic système borné
`d23453`, reçu `67e6524e…`, 141 événements dans treize secondes : refus
Mach/IOKit/fichiers observés, cause non démontrée, aucune permission ajoutée.
La chaîne de causes RPC perdue exige un successeur diagnostique distinct.

Clôture principale `315e15` : 1 248 refs, 36 jointures, reçu `95ad8101…`.
Premier lecteur refusé sur INDEX V6/V7 historiques copiés ; pins et sources
inchangés, correction limitée à leur statut de données historiques. Revue
Shared : 3 484 occurrences, 186 chemins, 37 hardlinks, dix jointures
gate/birth/release, 21 actions de signaux distinctes sur quatre births.
Chrome/services/Session nettoyés en 3,947269 / 1,033187 / 0,895535 s,
aucun résidu/erreur/ambiguïté, deux scans sur trois ports, handlers restaurés,
transport fermé. `clean=false`, taint vraie et owned_shutdown false conservés.

Archives canoniques sous `.app-loop/cycles/17/qualification/RPC-lot67-20261008/` :
ROOT9-closed-v3.tar.gz, 2 049 201 octets, SHA `c51e6ce33a4feb7778898e95fcb816b97968eb8af356396469d80a53664eb7b7` ;
V9-closed-root67.tar.gz, 218 816 octets, SHA `f61a95581c130e910c6a4eb720388764798610662e63e4f044114c5dda5aa516` ;
FULL-composite-closed-root71.tar.gz, 487 147 octets, SHA `12721a02927015174aa3acf3b74ab590211865f82e4fd9792f23246807d272ca`.
Contrôle `c6ee89` : copie/gzip/tar et 1 584/84/320 membres conformes, neuf
documents préexistants identiques. Première archive TMP refusée sur un socket
Chrome ; v2 refusée sur son lien SingletonSocket, déplacée vers TMP et
conservée. Seule v3, sans sockets/liens SingletonSocket, est canonique.

Usage `59d271` : 67 lots logiques, plancher natif 25 454 455 tokens,
ajout 1 290 005, durée parallèle zéro, pas une facture API. Budget PASS,
deadline/limites inchangées. Sources produit inchangées (`f49b41`). Aucun
tag, version, main, installation, publication, release, FULL ou ronde A/B.
Les nouveaux modèles restent dédiés à la prochaine boucle, lot62.

## Lot 68 : raccords purs, ROOT10 clos rouge et hypothèse graphique bornée

Les contrôles isolés réellement exécutés ont passé : préallocation7,
contexte worker40, diagnostics RPC34, constructeur V10 71, CDP Python19
et Node35, Git Python47 et Node35, listener Python6 et Node6. Les comptes
ne s'additionnent pas en couverture native ; Python46 reste historique.
Le premier préallocateur et les deux premiers contrôles V10 rouges sont
conservés, ainsi que le premier Node CDP abort134, sans tests exécutés.
Les corrections de fixtures et de profils sont distinctes des résultats.

Composition Git/listener fermée `4VBlvfDx`, INDEX `9b18f54b…` : helper
`f302e0fd…`, contexte `9960ba63…`, trois textes listener, neuf autres
textes inchangés et table quatorze sites (9 directs/5 RPC). Les dix tests
principaux `3e92c7` passent, reçu `7b4bb288…`, 37 pins locaux stables ;
guard Python interdisant OS/processus/socket/ctypes et écritures hors preuve.
Aucune admission native ou qualification de transport réel n'en découle.

Source QA fraîche `F4KirwuR`, HEAD `19979e8a…`, 3 586 blobs/modes vérifiés.
Préflight A `a8ad20` seul, reçu `f4b8b6d…` : entrées exactes, plan préparé,
racine future absente. Ni ronde A, ni B, ni Session, ni FULL. La copie de
dépendances QA et le verrou UV ont été contrôlés séparément ; cinq fichiers
source littéraux seulement, plus dix-neuf preuves, sont archivés. Après
le prochain commit, ce HEAD devient historique et demande un nouveau gel.

ROOT10 neuf `b90937db…`, QA WRAPPER historique `2d69…`, GO `59cc2fe7…`,
SQL36 `5fd2cfc1…`. Signature Chrome QA strict/deep verte hors sandbox outils
`77c5fd49…`, manifeste inchangé ; son contrôle rouge dans la sandbox outils
est aussi conservé. Aucun Chrome installé ou QA resigné/modifié.
Contrôle statique corrigé par comparaison stricte des trois champs de ref,
six permutations positives et quinze cas négatifs ; aucune autorité créée.

Natif unique `7b3ec8`, clôture `e96370` exit86, résultat `49b98038…` :
7 ACK sur 15. Le septième conserve désormais la chaîne réelle du refus :
Chrome absent/changé ou admission CDP hors délai5s, avant feuille Node.
Chrome70792/birth1791474774/727823, owner70354/birth1791474736/659266,
terminé -9 par le nettoyage borné ; pas de nouvelle cause OS inventée.

Clôture principale `32835a`, reçu `315c9c8d…` : 1 318 refs, 79 sources,
34 paires hardlink et 36 jointures signaux/birth. Revue Shared favorable.
Quatre XML1/0/1/0, chaînes ACK/stderr exactes, transport fermé, aucun résidu,
erreur ou ambiguïté et deux scans sur les trois ports, handlers restaurés.
Chrome/services/Session nettoyés en 3,899 / 1,017178 / 0,904120 s.
Nettoyage physique prouvé, mais taint vraie, clean/logstability/ownedshutdown
false et résultat natif rouge intégralement conservés. CALIBRATE reste0/2.

Diagnostic système fermé `a45bbd` après recharge, reçu `abed48bd…`, brut
`6593b92a…` : 139 événements/61 messages distincts, intervalle17s exact.
La première demande d'exécution refusée faute de crédits n'avait rien lancé.
Les refus CARenderServer, IOSurfaceRootUserClient et AGXDeviceUserClient
justifient une hypothèse ciblée, pas une cause démontrée. Profil proposé
`bee3c2e7…`, INDEX `499ed6c8…`, préimage2067 +308 octets exacts, seuls
trois droits nommés ajoutés ; quatorze tests statiques verts, revue indépendante
Environment favorable. Ni compilation Apple, ni installation, ni lancement
de ce profil ; clipboard, AppleEvents, HID et wildcards toujours exclus.
Chrome normal ouvert par Ludo le08/10 : contrôle CUA et page visible vérifiés.
Ce test utilisateur n'est pas adopté comme mesure QA isolée, A/B ou FULL.

Archives canoniques sous `.app-loop/cycles/17/qualification/RPC-lot68-20261008/` :
primary22, reçu `bf4d34a4…`, 307 membres, 1 836 662 octets compressés ;
supplement12, reçu `eb117f84…`, 111 membres, 314 037 octets ;
native3, reçu `1bf99dc2…`, 2 700 membres, 6 112 312 octets.
Contrôles MAIN `3c40d3`, `b43bf9`, `59e81f` puis relecture indépendante Gate :
USTAR, SHA/octets/modes/UID/GID, types et bornes64MiB/4096 conformes.
Contrôleur initial refusé avant destination sur fixtures/.git ; v2 n'exclut
que quatre fixtures synthétiques top-level avec ancres/statuts validés.
Natif : quatre liens Singleton et deux sockets exacts exclus sans suivi,
metadata conservée et revérifiée. L'extraction n'est jamais une preuve live
d'inode, hardlink ou ownership. Copie MAIN `e89f88` : 110 fichiers,
9 674 112 octets, manifeste `79184222…`, reçus bruts byte-exacts.
Le hook Git refuse ensuite l'archive35 de6 032 202 octets (limite3Mo),
sans commit créé. Fragmentation mécanique `aa7886`, trois fragments≤2MiB,
reconstruction SHA `2074bb9f…` exacte. Original complet préservé en TMP,
manifeste initial conservé, manifeste dérivé `148c99f1…` : 112 pins exacts,
37 archives logiques, aucun ALLOW_BIG ni modification d'un reçu brut.

Usage : 68 lots logiques, plancher natif 29 577 727 tokens, ajout4 123 272,
durée parallèle zéro, pas une facture API. Budget réel PASS, plafond tokens
désactivé, autres limites et deadline inchangées. Neuf documents préexistants
inchangés (`9e52e7`). Aucun produit, version, main, tag, release, installation,
landing, updater, Discord, mail, VPS ou DNS modifié ; publication toujours fermée.

## Lot 69 : WRAPPER11 préparé, contrôle statique encore rouge

Le constructeur `ecca6ab6…`, PLAN-INDEX `d159911e…`, conserve V10 hors
constantes profil et vérificateur exact du suffixe. Profil `bee3c2e7…`, trois
règles nommées, bornes 5/50/8 et 79 sources inchangées. Dix-sept tests purs
réels consignés, revue Gate favorable à la préparation seule, sans causalité.

HEAD documentaire observé `5f89164c…`, QA WRAPPER historique `2d69…`, ni
A/B ni produit courant qualifiés. Script de préparation `35688cc9…`, INDEX
`ef5b39a1…`, 22 refs rehashées MAIN `0d32b8`. Registre réel MAIN observé,
note de revue MAIN distincte ; invocation `f9d1f4` crée seulement les deux
JSON exclusifs : autorité `17382f10…`, registre `670890d3…`.

Construction mécanique `f2ace6`, clôture `187f22` code0 : ROOT11 `eff7b4e4…`,
reçu `d638ebb7…`, GO préparatoire `eccbc5bb…`, SQL36 `f53d7e71…` lu
entièrement par MAIN (`a80c53`). Aucun G1, Chrome, Session ou profil lancé.
Premier contrôleur : oracle HEAD19979 erroné, refus statique conservé ;
successeur v2 `e8ea3ec9…`, INDEX `1b4ba999…`, seul oracle corrigé vers5f891.

Contrôle v2 MAIN réel `fa326c` puis `e6e3d3` code1 : refus de propriétaire
sur le profil Apple primaire GameOverlayUI, UID0, alors que ref exige UID501.
Les trois sources système sont régulières, canoniques, UID/GID0, mode644,
nlink1 et SHA/taille exacts (`8b97aa`). Il ne s'agit pas d'un essai natif.
Un v3 non exécuté est préparé sous `hK9Iql`, INDEX `ab62bbb3…`, script
`218074ae…` : exception strictement limitée aux trois fichiers système
épinglés, à relire indépendamment avant usage ; autres refs restent UID501.

Copie canonique `f7c34e`, lot69 : 159 fichiers, 3 585 122 octets, manifeste
`62dfc30f…`. Préparation et rouge v2 préservés, aucun reçu requalifié ; les
copies ne donnent pas une preuve live d'inode ou d'ownership. Usage `a44439` :
69 lots, plancher30 201 597 tokens, ajout623 870, durée parallèle zéro,
pas une facture API. Dernier budget réel PASS `786fad`. Deadline16:52:30 UTC
inchangée ; prolongation de deux heures demandée, non accordée à ce lot.
CALIBRATE0/2, FULL, A/B et release restent fermés, aucune publication.
