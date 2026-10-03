# Cycle 16 Codex — ouvert le 2 octobre 2026

Cycle distinct ouvert normalement à 12:07:46 UTC, depuis le commit documentaire
`8bc700115794dea9909777e69d275e62c26b2db2` sur la branche `codex/cycle-16`.
Le cycle 15 est clôturé normalement ; son reçu final est
`.app-loop/cycles/15/reprise/release-go/final-sync-root/receipt.json`.
Ses preuves historiques, ses 34 corrections et ses 7 754 tests distincts restent
rattachés à leurs versions. Les quatre messages Discord ne sont pas republiés.

Ludo a autorisé le temps nécessaire au cycle 16 le 2 octobre à 11:54:21 UTC
(message `Sentinel_ba1d5c1be3788191b1d26f9890bbbb6d`). Le budget opérationnel
séparé est de 48 heures, avec les plafonds de modèles documentés dans
`.app-loop/cycles/16/budget-opening-receipt.json`. Les compteurs d'usage Codex
sont des estimations explicitement nommées ; aucun token Claude n'est inventé.

## Instrument et accès

L'adaptation locale approuvée à 12:21:38 UTC
(`Sentinel_ae44438e89e48191b98d3bae78bad1c4`) reconnaît le compteur du modèle
réel pour quitter MAP. Couverture complète, contrôle zéro tokens et toutes les
autres portes restent conservés. Le script Claude canonique est inchangé.
Source, diff, dix comparaisons synthétiques et autorisation sont conservés sous
`.app-loop/cycles/16/proposition-compatibilite-codex` et `outils`.
Le compteur historique est resté à 23 ; aucun nouveau forçage.
Claude est à quota épuisé, Grok indisponible ; les rôles indépendants utilisent
GPT. Le registre conserve les identités réellement appelées. Cette diversité
dégradée ne devient pas une diversité de modèles.

La pile qualifiée est la révision v3 au commit produit
`c62312eb397d934bcd8a5171c4260aef218c2df9`. Son HOME et ses données sont
sous `/private/tmp/therese-c16-codex-runtime-gqx5tmht`, avec backend17493 et
frontend5173. Les deux profils précédents et leurs journaux sont conservés.
Le moteur de cette pile UI est une factory hors ligne avec SQLite en clair et
services annexes omis : elle ne qualifie pas le moteur natif complet ni SQLCipher.
Le backend et le frontend possédés ont été arrêtés normalement le 2 octobre
à 16:28:47 UTC ; ports 17493 et 5173 fermés, journaux et profil conservés.
Reçu : `reprise/runtime-v3/stop-receipt-root.json`. Le manifeste initial reste
historique et n'est pas réécrit pour lui attribuer cet arrêt. Aucun accès au
profil réel ni au port 17293 n'appartient à ce cycle.

Les cinq instruments de base et la couverture écran ont leurs témoins sains,
défaillants puis restaurés propres à v3. La capture est réellement montée,
avec géométrie et durée observées ; un rectangle nul est rejeté. Reçus :
`.app-loop/cycles/16/calibration-accepted-v3.json` et
`reprise/runtime-v3/all-20261002T140959.771452Z/calibration-summary.json`.
La calibration expire après24h et doit être reprise après changement visuel.
Le TAP de l'instrument compte20contrôles distincts, séparés des suites produit.

Le navigateur du Mac est **Google Chrome**. Des gestes réels ont été observés
sur la pile précédente ; ils ne sont pas recyclés en rondesv3. Les sélections
Chrome des deux acteursv3 ont bloqué l'outil et ont été interrompues :
3268,7s pour interface,130,2s pour contradiction. Ces deux appels n'ont fourni
ni état, ni accessibilité, ni capture, ni geste. Les campagnes automatiques
utilisent **Chromium145 / Playwright1.58.2**, ce qui ne satisfait pas cette
condition distincte de vérification avec le Chrome du Mac.

## Défauts reproduits et correctifs ciblés

| Fiche | Déclencheur et résultat du correctif | Preuve avant / après |
| --- | --- | --- |
| B-1769 | La réponse tardive de A composait à B le texte de A. Compte, message, ouverture et appel courant gardent désormais le résultat utilisable ; erreurs/finally obsolètes sont ignorés. Aucun envoi exercé. | `lecteur-interface/contamination-rouge.xml`, `reparation-interface/production-cibles.xml` |
| B-1770 | Une réponse de sauvegarde remettait de-DE malgré une saisie it-IT admise pendant l'attente. Les nouvelles saisies restent affichées et à enregistrer ; reset/import concurrents sont retenus. | `lecteur-interface/export-rouge.xml`, `reparation-interface/production-cibles.xml` |
| B-1771 | Trois noms de callbacks du test modal ne correspondaient pas au hook. Le test corrigé est vert sur le hook sain et rouge sur une copie laissant t/p/o traverser le dialogue. | `lecteur-interface/shortcut-pouvoir-echec.xml`, `reparation-interface/shortcut-power-receipt.json` |
| B-1772 | Après remplacement de la base et de sa clé par B, le cache gardait A. L'instance existante est invalidée sans IO avant réouverture, y compris après retour arrière. | `reproduction-securite/receipt.json`, `reparation-cle/ast-c62312eb-source-courante/receipt.json`, `reparation-cle/vert-voisins.xml` |
| B-1773 | DELETE réussi puis GET rejeté produisait une notification de charte restaurée avec l'ancienne valeur. La relecture rend désormais son résultat ; l'échec est expliqué à l'écran. | `lecteur-interface/relecture-correctifs/complement.xml`, `reparation-interface/production-cibles.xml` |
| B-1686 (historique repris) | Une annulation sautait les nettoyages et la finalisation tardive de l'archive de sécurité. La finalisation d'une archive existante précède les await, sans doubler celle des handlers ; une tentative annulée avant création garde les précédentes sauvegardes. Le finally protège les trois nettoyages et l'annulation remonte. | `reproduction-annulation/rouge.stdout`, `reproduction-annulation/safety-memory/rouge.stdout`, `reparation-annulation/existence-final-regression/receipt.json` |

Les chemins du tableau sont relatifs à `.app-loop/cycles/16/`. Les contrôles ciblés et leurs répétitions ne sont pas additionnés aux suites
complètes. B-1769,1770,1772,1773 et1686 sont cinq défauts produit ; B-1771
corrige l'oracle d'un test. Les relectures indépendantes ont également contrôlé
les chemins d'erreur, l'annulation et l'absence d'archive avant purge.

## Portes produit et critères de sortie

Les portes complètes portent sur **c62312eb**, avec archives, index Git et
checkout privés. Le reçu consolidé est
`.app-loop/cycles/16/reprise/gates/final-gates-c62312eb.json`.

| Porte | Résultat distinct | Limite |
| --- | --- | --- |
| Backend |4 338 succès,4 skips,0 échec/erreur ; Ruff vert |4 342 cas JUnit au total |
| Frontend |3 442 succès,0 skip/échec/erreur ; TypeScript, ESLint, build verts |26 avertissements ESLint existants |
| mypy |937 diagnostics, baseline 937 respectée |Pas une affirmation zéro diagnostic |
| Total unitaires |**7 780 succès distincts**,4 skips backend |Aucun ciblé, sabotage, export répété ou contrôle d'instrument additionné |
| Carte produit |2 122/2 122 fichiers revus,1 804 rapports analysés,100% |111 divergences historiques arbitrées, pas réutilisation d'une carte15 comme carte16 |

JUnit backend SHA256
`000b9fa9586b53c642121db8e21c353ae3c7d47e45beb7cbf68039a0204981bf` ;
frontend `54343e2f8feb4e13eeffe5b102d1e1eba7eec310afcca0e6c925597e7328264f`.
Les copies anciennes sabotées échouent sur les comportements concernés ; les
sources du produit courant restent intactes pendant ces contrôles.

Le périmètre de sortie est borné : **122 contrats critiques** (116 historiques,
6 fiches du cycle 16), deux acteurs réels et indépendants, six calibrations valides,
portes actuelles, carte complète, journaux relus et toutes les anomalies écran
arbitrées. La matrice conserve129 obligations unitaires,82 runtime et1 native.
Les 49 replays Chrome ajoutés par une heuristique du premier générateur ont été
retirés explicitement ; leurs définitions restent conservées et aucune des 122
identités n'est supprimée. Les vrais contrôles Chrome Mac restent exigés.
Un audit indépendant a vérifié les 129 preuves unitaires partagées de root,
leurs 259 sources et419 références ; elles ne deviennent pas des exécutions des
lecteurs. Les anciennes valeurs HEAD/UUID/géométrie sont des définitions à
normaliser explicitement, jamais des résultats actuels.

Les trois fragilités du premier consommateur de reçus — acteur fictif,
relecteur fictif et fichier leurre à pointeur divergent — sont conservées comme
rouges et corrigées dans le consommateurv2. Ses 32 témoins de calibration
passent, dont les trois refus explicites. Cela qualifie un outil de preuves,
pas un bug produit ni une ronde. Reçu root :
`transitions/qualificateur-v2-verifie-root.json`.

## Campagnes et qualification restante

Deux campagnes automatiques ont exécuté chacune trois recettes et 21 écrans
sur 1440/800, clair/sombre, soit 84 captures originales par acteur. Les 265 gestes
interface et 330 gestes contradiction concernent 1440 clair ; les trois autres
combinaisons sont visuelles. Chaque contexte navigateur et son stockage sont
neufs ; les fixtures du backendv3 sont partagées et ne sont pas présentées
comme une nouvelle base à chaque campagne. La première campagne a 16 candidats,
la deuxième 26 ; un refus de relocalisation ou un débordement local ne suffit
pas à confirmer un défaut. Les lectures neutres conservent ces limites.
B-1558 (« null » dans un libellé facturation) correspond à une dette historique
différée ; aucune nouvelle identité de bug ni résolution n'est inventée.

Les lectures neutres ont réellement inspecté 94 originaux de chaque campagne
(84 écrans et 10 images de recettes). Le second lot a été relu par
`/root/lecteur16_securite` ; le lecteur interface interrompu n'est pas crédité
de cette relecture. Rapports et 26 statuts individualisés :
`lecteur-securite/revue-neutre-ronde2-20261002T161500Z/`.
Les appels de transport sans retour sont conservés : certains fichiers ont été
créés avant blocage de l'accusé d'exécution ; root a vérifié leurs octets sans
inventer une fin d'outil réussie. Les préparations bloquées B1753/B1760 des
lecteurs ne deviennent pas des exécutions.

Sept compléments ont ensuite été **exécutés par root seulement**. Les parcours
UI datent de 16:23 à 16:27 UTC, avant l'arrêt de v3 ; les dernières répétitions
des harnesses offline datent de 16:47 UTC, après cet arrêt. Reçu consolidé : `complements-root/consolidation-root.json`.

- P157 : 45 contacts synthétiques, noms longs, huit étapes, largeurs 800 et
  1440 en clair. Cartes contenues, pas de chevauchement, hauts/ premières cartes
  visibles, focus conservé, bords droits 1308/668 puis retour à gauche 0 ;
  empreinte des contacts inchangée. L'oracle initial lisait le bouton droit
  après retour gauche. Son rouge est conservé ; la copie corrigée le mesure
  au bord droit, avant retour. Le produit n'a pas changé.
- P162 : gestes réels dans les quatre combinaisons largeur/thème. Envoi,
  Paiement et Échéance sont accessibles au bord droit 389 à 800 ; montant et
  actions restent visibles. Aucune mutation de facture dans cette recette.
- B1713 : deux observations BODY après Enter, puis focus visible sur « Écrire
  un e-mail » après Tab. Ce témoin ne démontre pas un focus continu ni une
  nouvelle correction.
- B1755 : trois variantes « Générer » refusées sans clic et un bouton sain
  cliqué, dans un document HTML synthétique distinct du runtime produit.
- B1753 : témoin du traitement DELETE durable puis frontière suivante ; les
  deux cas sont verts et les registres de tâches sont vides aux frontières.
- B1760 : 19 cas répétés en SQLCipher neuf, en-tête chiffré observé, dix espèces
  actuelles de PDF rattachées aux nodeids exacts. Ce lot root n'est pas un lot
  exécuté par chacun des deux lecteurs et ne s'ajoute pas aux 7 780 succès.

Le premier harness quittait le processus dans `pytest_sessionfinish` avant le
rapport post-`pytest.main`. Le variant de mesure écrit ce reçu dans un hook
prioritaire, sans changer les tests ou le produit. Les répétitions diagnostiques
16:47 enregistrent une tentative `bind AF_INET6 ::1:0` **refusée**, provenant
de la sonde d'import `_has_ipv6` d'urllib3. L'adresse, la stack et la source
primaire sont conservées ; le garde IP reste intact. Les premiers reçus n'avaient
pas cette provenance, elle n'est pas ajoutée rétroactivement. Aucun « zéro
essai réseau » n'est annoncé. Les stderr externes contiennent cinq warnings
Git sur `DARWIN_USER_TEMP_DIR` ; les stderr internes de tests sont vides.

Le complément candidats root observe Octobre → Septembre → Octobre, huit UUID
CRM (score, fiche et Activités), et l'ouverture/fermeture du menu RGPD d'une
rangée précise. Il ne prouve ni toutes les rangées homonymes, ni un export,
anonymisation ou consentement RGPD. Ces refus d'identité de l'instrument restent
une limite de couverture, sans être transformés en bugs produit confirmés.
La relecture indépendante après compléments décrit 14 observations bornées
et 12 limites de localisation restantes ; aucune acceptation globale des
26 candidats. Voir `lecteur-securite/revue-complements-root-20261002T163800Z/`
et son addendum, distinct des rapports originaux.
La recette P160 observe notices/champs chargés ; les refus 409 et la concurrence
appartiennent aux preuves unitaires exactes, sans devenir des gestes navigateur.
Les 17 relations runtime complémentaires et leurs 178 références relues sont
préparées explicitement dans `transitions/relations-runtime17-c62312eb/` ; une
relation préparée ne vaut pas une transition exécutée.

Le build natif privé est neuf et vérifié statiquement. Il comporte deux deltas
explicites dans sa copie : port17494 et identifier`fr.synoptia.therese.c16`.
GUI SHA256 `311a033a84bda149512a8e46b7be022325d7aa66402fe0d889b96edcb8b75081` ;
sidecar `efd6465060c9a6ebd888385a6c04fd97cbcdadb6ddd292ceed65d44fb3d74662`.
Les signatures ad hoc/deep/strict sont valides ; le build seul ne prouve pas
le démarrage. Les 78 empreintes du ledger et8 sources primaires locales WebKit
ont été relues et vérifiées root. Rapport :
`transitions/native-build-c62312eb-axswdp44/LIRE-RESULTAT.md`.

Le GUI natif reste **bloqué techniquement** : le choix actuel Wry utilise le
store WebKit par défaut. Le helper Foundation prouve certains refus synthétiques,
mais ne prouve pas le confinement des écritures déléguées des processus
WebContent/NetworkProcess avant leur lancement. HOME privé, identifier différent
et comparaison de fichiers après fermeture sont insuffisants. Aucun lancement
GUI, assouplissement des gardes, transaction sur stores réels ou contournement
incognito n'a été effectué.

Une fenêtre **moteur autonome** a réellement réussi de 16:50:13 à 16:50:33 UTC
le 2 octobre par `/root/preuves16_transitions` : sept témoins de confinement positifs/négatifs, port privé 63895
attribué au groupe possédé avant HTTP, version exacte, DB et Qdrant disponibles
avec services non omis. Arrêt et nettoyage observés dans le log, groupe vide après nettoyage ; bundle,
sceaux et instrument identiques. Le Python du calibrateur a été copié offline
sous QA_ROOT, avec 2 815 entrées vérifiées et un venv privé sans site-packages
système ; le garde `/Users`, réseau et Mach n'a pas été ouvert. Le journal
contient le warning OMP #179 sur un fichier `/tmp`, conservé sans cause inférée.
Reçus : `transitions/moteur-prive-verifie-root-v3.json` et
`/private/tmp/therese-c16-native-c623-axswdp44/proofs-engine-fenetre-1/receipt.json`
(SHA256 `11aaf52fd45e2a79ad4399eaedc82f72cd77afcd30161d57213309fecdb1236c`).
Le postvol vérifie 3 577 sources, cinq membres du bundle, aucun PID/listener
possédé restant et le sceau deep/strict. Le code final du sidecar et un éventuel
recours SIGKILL ne sont pas sérialisés ; exit 0 désigne le contrôleur seulement.
Rapport : `transitions/moteur-prive-c62312eb-fenetre-1/LIRE-MOTEUR.md`.
Cette seule fenêtre ne remplace ni le GUI ni le contrat natif entier ; aucune
interface WebKit, notarisation, voix facultative ou mise à jour N vers N+1
n'est qualifiée par elle.

**Deux exécutions ne sont pas deux rondes acceptées.** Tant que toutes les
preuves requises et leurs lectures ne sont pas établies, le CLI reste en
ZERO_CHECK, plateau 0/2. GAP_SCAN, clôture et nouvelle publication ne sont pas
ouverts. Le compteur historique de forçages reste 23.
Le cycle est mis en pause normale en ZERO_CHECK le 2 octobre à 16:54:58 UTC pour
ces blocages et l'attente du GO push. Il n'est ni clôturé ni redémarré. L'usage
consigné est 32 appels de travail et 1 545 000 tokens GPT estimés, sans mesure
API ; le budget séparé reste dans ses limites. La recherche des manques en
GAP_SCAN et son arbitrage humain restent derrière les deux rondes acceptées.

## Limites et prochaines portes

La reproduction HTTP complète de restauration entre profils a été refusée par
la revue automatique pour un risque de cybersécurité signalé. Elle n'a pas été
exécutée. Le témoin conservé exécute la source extraite par AST et SQLCipher
réel, avec archive ancienne `.tar.gz`, probe d'init_db et dépendances annexes
factices. Il n'atteste pas une restauration TestClient entre profils, une archive
chiffrée par passphrase ni un trousseau réel. Les contrôles unitaires mémoire
et les tests voisins restent distincts de ce témoin.

À cette étape : cinq défauts produit et un oracle de test corrigés, portes
complètes et recalibrationv3 réussies ; qualification des deux rondes encore
incomplète pour les raisons explicites ci-dessus. Aucun plateau du
cycle 15 n'est recyclé. Les dettes différées historiques restent documentées.
Le profil réel et le port 17293 ne sont pas utilisés par le cycle 16 ; l'incident
natif du cycle 15 reste conservé, sans affirmer l'intégrité globale de ce profil.
La 0.77.1 est signée ad hoc ; aucune notarisation attestée, updater N vers N+1
non exercé. Toute nouvelle publication ou annonce Discord exige un GO propre
au cycle 16.

Le push de `codex/cycle-16` vers `origin`
(`git@github.com:ludovicsanchez38-creator/Synoptia-THERESE.git`) est **bloqué par
la revue automatique** : elle considère l'autorisation15 documentaire seulement
et ne reconnaît pas la confiance de la destination GitHub pour ce lot16.
La tentative normale a échoué en résolution DNS ; la tentative escaladée a
été rejetée avant exécution. Aucun push16, aucun contournement ni nouvelle
tentative après ce refus. Reçu : `push-cycle16-refuse-root/receipt.json`.
Une demande explicite de GO pour pousser cette branche a été transmise à Ludo
dans la tâche principale ; sa réponse reste attendue. Ce GO ne couvre ni merge,
tag, release, installation ou annonce Discord.
Le blocage WebKit demeure technique, distinct de cette autorisation manquante.

## Décision de Ludo du 3 octobre 2026 : abandon de la VM macOS

Ludo demande dans la conversation de suivi : « On laisse beton le similateur
mac os c'est innutile. » La piste UTM/macOS invité est abandonnée pour le cycle
16. Ne plus poursuivre sa configuration, son écran noir, une nouvelle
installation ou les gestes de réveil demandés précédemment. Cette décision
remplace l'attente du geste physique décrite dans
`.app-loop/cycles/16/reprise/reprise-demandee-20261003T1743/TRANSMISSION-RESULTAT.md`.
Les reçus et captures antérieurs restent historiques.

La tentative d'accès à UTM dans cette conversation a répondu « Computer Use
was not approved to use UTM ». Aucun arrêt de VM n'est donc attesté ici. Le
contrôle de cette application n'a pas été réessayé après ce retour ; ses disques
et fichiers n'ont pas été supprimés.

La prochaine qualification doit rechercher une voie directe sur l'application,
avec données et profils de test isolés, sans réintroduire de VM. L'abandon de
cette piste ne valide aucune ronde et ne dispense pas de vérifier les écritures
WebKit avant un lancement natif. Le cycle conserve ZERO_CHECK, 0/2 rondes
acceptées et 23 transitions forcées historiques. La pause technique reste
en place pendant ce changement de méthode.

Au contrôle de cette conversation, la branche est `codex/cycle-16`, le HEAD
produit `1905aa19206d5a1764da48bf56e481a5fd2b89fb` et les CI générale, Windows et
E2E sont enregistrées réussies dans
`.app-loop/cycles/16/suivi-ci-20261003-root/index-final.json`. Le refus de push
raconté plus haut est historique : ce HEAD est déjà suivi sur origin. Le présent
lot ne modifie que le suivi et le motif de pause ; aucune nouvelle recette,
fusion, installation, release ou annonce Discord n'est exécutée.
