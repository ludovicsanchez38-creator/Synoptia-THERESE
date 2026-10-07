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
