# Reprise du cycle 15 THÉRÈSE

## GO de release et reprise après audit

Le GO de Ludo du 01/10 autorise le workflow complet avec changelog. La version
calculée est `0.77.0-alpha`, selon la règle MINOR pour P160 et P162. Le pré-vol
vérifie main `887669c3`, la branche `b690ca7b`, le tag libre et les accès GitHub
et VPS. Le passage normal HUMAN_GATE vers RELEASE est suivi d'un retour
REPRODUCE puis REPAIR après le rouge produit B1760, sans transition forcée.

La conversion au 01/10 puis émission au 08/10 donne deux échéances dans un
PDF réel : 07/11 en en-tête, 31/10 dans les conditions. Les cinq HTTP rendent
200 ; le témoin JUnit donne un échec d'assertion, aucune erreur ni skip. La
preuve est conservée dans
`.app-loop/cycles/15/reprise/release-go/echeance-conversion/rouge-corrige-20261001T103905.120517Z/manifest.json`.
La première tentative, avec erreur de harnais, reste distincte et exclue.

Le correctif B1760 est vérifié et commité ; le bump prépare 0.77.0-alpha.
L'audit frais ajoute des cartes longues débordantes (B1762), des oracles
d'interface à corriger (B1763/B1764), l'audit de dépendances (B1765) et les
transactions DDL des fixtures (B1766). Leurs ciblés et limites sont centralisés
dans le rapport de release. La boucle courante est en REPAIR, en attente des
deux rondes sur la nouvelle source figée. Le compteur plateau est à zéro.
Les sections et preuves d4 ci-dessous sont historiques ; elles ne qualifient
pas le nouveau code. L'état courant des portes de release est porté par le
[rapport v0.77.0-alpha](releases/v0.77.0-alpha.md).

## État historique d4 après les décisions déléguées

La source finale des lots P160/P162 est `d4f19d7478dabb58ce640e701725367df92037bc`, poussée sur `origin/codex/cycle-15`. Les **25 corrections ciblées couvrent 18 défauts produit et sept défauts de contrôle**. P160 et P162 sont implémentées ; P161 est livrée comme cadrage documentaire, avec le parcours financier encore à développer. Le CLI canonique accepte **deux nouvelles rondes indépendantes : 2/2**, après B1759. La phase courante est `HUMAN_GATE`, sans nouvelle proposition en attente de décision. La publication d’une nouvelle version reste soumise au périmètre du skill `release-therese`. Les anciennes rondes restent historiques et le passage préliminaire ayant révélé B1759 est exclu du plateau.

### Portes fraîches et parcours

Les portes sont rejouées dans chacune des deux nouvelles rondes sur la même source figée. Le [backend R2](../.app-loop/cycles/15/reprise/portes-preservees-backend-20261001T074420.842446Z/backend-manifest.json) donne 4 300 cas : **4 295 réussis, cinq skips, zéro échec/erreur**, Ruff 0. Le [frontend R2](../.app-loop/cycles/15/reprise/portes-preservees-frontend-20261001T074426.088293Z/frontend-manifest.json) donne **3 430 réussis**, zéro échec/erreur/skip, TypeScript/ESLint/build 0 et 26 avertissements ESLint préexistants. [TAP R2](../.app-loop/cycles/15/reprise/runtime/tap-20261001T074518.065728Z/couverture-ecran.tap) : 20/20. [Mypy R2](../.app-loop/cycles/15/reprise/portes-preservees-mypy-20261001T074430.509088Z/mypy-manifest.json) sort réellement avec le code 1 : 937 erreurs, baseline respectée **par nombre**, sans attester l’identité de chaque erreur. Les copies Git exactes vérifient 3 560 fichiers inchangés et un index isolé égal à l’arbre du commit ; [qualification indépendante des trois portes R2](../.app-loop/cycles/15/reprise/runtime/qualification-gates-clean-r2-factures-indice-20261001T075253.185162Z/qualification-portes-git-v2.json).

La [carte courante](../.app-loop/cycles/15/reprise/carte-final-d4f19d74.json) est PASS, **2 109/2 109** dans le périmètre `src/tests/scripts/.github`, avec les 111 arbitrages historiques conservés. Les documents générés portent les agrégats historiques ; ils ne comptent pas les bugs actuels. Un commit ultérieur limité aux documents ne constitue pas un rejeu des tests : les preuves gardent leur véritable HEAD de code `d4f19d74`.

La [recalibration finale](../.app-loop/cycles/15/reprise/runtime/all-20261001T061527.801483Z/calibration-summary.json) passe sur cette source, avec sept captures inspectées. Les six instruments sont enregistrés à 06:20:02 UTC le 01/10, validité jusqu’au 03/10 à 06:20:02 UTC.

Les recettes fraîches R2 vérifient séparément [Pipeline/contexte/titres](../.app-loop/cycles/15/reprise/runtime/recette-2026-10-01T07-45-56-083Z/recette.json), [facture FACT-2026-014 et avoir FACT-2026-015](../.app-loop/cycles/15/reprise/runtime/facturation-p160-2026-10-01T07-46-03-415Z/recette.json) et [focus CRM](../.app-loop/cycles/15/reprise/runtime/crm-focus-2026-10-01T07-46-07-921Z/recette.json). Le [Pipeline dense](../.app-loop/cycles/15/reprise/pipeline-vertical-scroll/native-vert-_23byt4c/mesures.json) conserve ses 99 contacts et leur empreinte, sans écriture ; ses sept mesures couvrent focus et Entrée. La visibilité horizontale d’un titre au bord reste une intersection après clipping. Le [clavier Accueil](../.app-loop/cycles/15/reprise/accueil-collision/clavier-2026-10-01T07-48-20-958Z/recette.json) observe BODY après disparition de l’indice puis Tab au composeur avec focus visible ; il ne démontre pas un maintien automatique du focus.

La [recette P162 fraîche R2](../.app-loop/cycles/15/reprise/p162-indice/native-3hxf48gt/recette.json) passe **312 assertions, quatre configurations et 24 images relues indépendamment**. Les 33 pièces sont strictement conservées. Molette et bords sont exercés à 800 px dans les deux thèmes ; à 1440 px le tableau tient. Tab peut aligner le cadre sous les filtres et sortir le paragraphe du cadrage ; titres et premières valeurs restent visibles. Aucun indice flottant ni validation de lecteur d’écran n’est revendiqué.

### Deux nouvelles rondes propres

| Ronde et acteur | Lecture indépendante | Couverture et limites des gestes | Manifeste / évaluation réelle |
| --- | --- | --- | --- |
| R1 : `cycle15_lots_review` | [Tri `cycle15_inventory`](../.app-loop/cycles/15/reprise/runtime/tri-clean113-review-r1-cycle15_inventory/final-20261001T074121.438652Z/tri-independant-clean-r1.json) : 84 originaux et 44 compléments ; 27 IDs / 461 occurrences, 26 diagnostics ou limites conservés, un faux positif, aucun nouveau défaut établi | 848 entrées : 198 changements, 454 refus, 195 non exercés (dont 30 contrôles PDF), un inchangé | [113/113](../.app-loop/cycles/15/reprise/transitions/final-clean-round1-d4f19d74-20261001T070946.029690Z/manifeste-critique-c15.json) ; [CLI PASS 1/2](../.app-loop/cycles/15/reprise/plateau-c15-clean113-review-r1-d4f19d74/evaluation-cli-root.json) |
| R2 : root | [Tri `cycle15_inventory` corrigé](../.app-loop/cycles/15/reprise/runtime/tri-clean113-root-r2-cycle15_inventory/final-corrige-20261001T082831.366280Z/tri-independant-clean-r2.json) : 84 originaux et 44 compléments ; 27 IDs / 510 occurrences, 26 diagnostics ou limites conservés, un faux positif, aucun nouveau défaut établi | 913 entrées : 199 changements, 503 refus, 210 non exercés (dont 33 contrôles PDF), un inchangé | [113/113](../.app-loop/cycles/15/reprise/transitions/final-clean-round2-d4f19d74-20261001T080005.557529Z/manifeste-critique-c15.json) ; [CLI PASS 2/2](../.app-loop/cycles/15/reprise/plateau-c15-clean113-root-r2-d4f19d74/evaluation-cli-root.json) |

Chaque ronde ouvre 21 écrans dans deux thèmes à 800 et 1440 px. Les gestes automatiques concernent seulement 1440 px en clair ; les trois autres contextes sont des observations visuelles. Les listes dépendent des fixtures et ne représentent pas autant de boutons uniques. Les refus et exclusions ne sont pas convertis en gestes réussis. R1 : 11 déjà sélectionnés, 16 inactifs, 164 sortants/confirmations et quatre natifs constituent les 195 non exercés ; R2 : 11, 16, 179 et quatre constituent les 210. Les 30/33 contrôles de génération PDF sont inclus dans ces non-exercés et exclus avant clic ; ils ne s’ajoutent pas aux totaux. Les recettes ciblées sont distinctes des 84 captures globales.

Les [preuves plateau R1](../.app-loop/cycles/15/reprise/plateau-c15-clean113-review-r1-d4f19d74/evidence.json) et [R2](../.app-loop/cycles/15/reprise/plateau-c15-clean113-root-r2-d4f19d74/evidence.json) gardent leurs sources, lecteurs, audits et limites. Chaque manifeste critique vérifie 283 fichiers SHA, 564 cas JUnit précis, 101 pointeurs JSON et 20 TAP. Le [dernier index indépendant](../.app-loop/cycles/15/reprise/runtime/tri-clean113-root-r2-cycle15_inventory/final-corrige-20261001T082831.366280Z/index-assemblage-r2.json) relie la matrice des 25 corrections, les portes et les audits ; l’audit d’assemblage R2 vérifie 684 références, 53 chemins SHA uniques et 540 pointeurs, sans erreur. Le premier tri R2 et sa correction de détail « score » restent conservés ; le plateau utilise exclusivement la version corrigée.

Le premier passage global sur cette source conserve [84 captures et 27 alertes](../.app-loop/cycles/15/reprise/runtime/couverture-c15-final113-root-r1-d4f19d74-20261001T062207.930198Z/qualification-ronde-preliminaire-b1759.json) comme découverte uniquement. B1759 est confirmé dans le nouveau contrôle d’assemblage : une variable masque sa fonction de clé JUnit. Le refus est conservé ; une copie corrigée, une copie sabotée byte-exacte de l’original et une restauration vérifient le mécanisme. Le sabotage retrouve le TypeError avant écriture, la restauration assemble 113/113 et passe son validateur. [Exécution réelle](../.app-loop/cycles/15/reprise/b1759-sabotage-restaure-20261001T064827.690989Z/execution.json). Le produit et les six instruments calibrés ne changent pas. Ce passage préliminaire n’entre dans aucune des deux rondes propres.

Le laboratoire final est [arrêté et vérifié](../.app-loop/cycles/15/reprise/runtime/arret-clean113-final-20261001T083316.084372Z/arret.json) : PID 90069/90070 absents, aucune écoute sur 1420/17393. Les profils, bases, anciennes preuves et l’application existante sont conservés.

### Relecture finale des besoins après les deux rondes

Le [rapport final indépendant](../.app-loop/cycles/15/reprise/gap-scan/preuve-etat-gap-scan-fige-factures-indice-20261001T084914.157354Z/rapport-final-borne-factures-indice-etat-archive.json) relit les parcours métier/facturation, chat et petit écran/clavier, puis les déduplique avec les 162 propositions et les fiches pertinentes. Aucun besoin nouveau hors des éléments déjà enregistrés n’est établi dans ce périmètre. P160/P162 restent des implémentations vérifiées ; P161 reste un cadrage. B1558/B1635 restent différés. Les 454/503 refus et les 195/210 gestes non exercés conservent leurs limites ; aucune exhaustivité métier ou conformité comptable globale n’est annoncée.

L’audit vérifie 38 fichiers directs et 193 pointeurs, puis les 227 empreintes distinctes et 1 034 pointeurs incorporés aux deux tris, sans erreur. Les huit sources relues correspondent au HEAD. Le [premier rapport](../.app-loop/cycles/15/reprise/gap-scan/rapport-final-borne-factures-indice-d4f19d74-20261001T084233.657021Z.json) reste intact ; le rapport dérivé ne remplace que deux références vers une copie byte-exacte de l’état GAP_SCAN, avant sa transition normale vers HUMAN_GATE.

L’[état final archivé](../.app-loop/cycles/15/reprise/etat-final-root-20261001T085118.449735Z/etat-final.json) confirme les 25 fiches ciblées corrigées, les deux rondes acceptées et les registres copiés à l’octet près. Les 162 propositions ont déjà une décision : 137 acceptées, 15 différées et 10 rejetées. La délégation P160/P161/P162 n’est pas redemandée. Le nouveau portail concerne le prochain périmètre de release : `release-therese` exige un accord explicite sur la version et sa publication. Aucun nouveau GO n’est inféré de la stabilisation.

## États antérieurs conservés

Les états intermédiaires ci-dessous conservent leurs HEAD et leurs dates. L’état courant et ses limites sont indiqués en tête ; les anciennes rondes ne comptent pas pour les évolutions suivantes.

Mise à jour le 1er octobre 2026. La reprise demandée par Ludo a récupéré les lots commencés dans Claude Code puis interrompus faute de budget. Les **22 fiches ciblées sont corrigées : 17 sur le produit et 5 sur les contrôles**. L’évaluateur canonique a accepté **deux rondes indépendantes successives : 2/2**, sur la source `fbfa29f1`, avant les nouvelles évolutions. Ludo a ensuite délégué les trois décisions selon la logique et la législation ; P160, P161 et P162 sont acceptées. La boucle est en `IMPLEMENT` : P160 est stabilisée, P161 livrée comme cadrage et P162 codée, revue sans blocage, en attente du vert natif sur commit. B-1757, confirmé puis corrigé, reliait un numéro 2026 à une date d’émission 2027 sur deux routes. Le plateau courant est à 0 ; les deux rondes antérieures restent des preuves historiques. Les transitions de cette reprise sont normales ; les 23 anciennes transitions forcées restent historiques.

Source figée : `fbfa29f1b8fd69ab7bf7af0652aa0775d71798cd`, branche `codex/cycle-15`, dans `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex`. Le push sur `origin` est vérifié par `ls-remote`. Le dépôt d’origine est propre et `main` local/distant reste à `887669c37f1488034512cab846c04d257a2e45f2`, version `0.76.1`.

Le lot final de documentation porte uniquement le suivi, le changelog et la carte générée. Les portes et captures gardent leur vrai HEAD de code `fbfa29f1` ; un commit de documentation ultérieur ne vaut pas un rejeu des tests.

La [matrice canonique des corrections](../.app-loop/cycles/15/reprise/matrice-corrections.json) indexe les rouges, verts et sabotages. Son [audit](../.app-loop/cycles/15/reprise/audit-matrice-22-fbfa29f1.json) vérifie 69 références uniques sans erreur d’empreinte. Les suites ciblées se recouvrent ; leurs nombres ne s’additionnent pas.

## P160 et P161 après délégation

P160 est implémentée dans un lot distinct. Les 12 nouveaux cas et 177 voisins passent, sans échec, erreur ou skip, sous SQLCipher et garde avant imports : [vert ciblé](../.app-loop/cycles/15/reprise/p160-serie-commune/vert-final-et-voisins-20261001T052958.432084Z/manifest.json). Les sabotages en copies exactes produisent 4 échecs pour les séries, 5 pour l’héritage et 2 pour la frontière annuelle, sans erreur ni skip. La comparaison naïve/UTC invalide du premier vert est conservée et exclue. Le lot conserve les pièces émises et traite les brouillons AV, anciens, importés, rang zéro ou alias de rang. La recette Chromium P160 sur `1991c13c` passe, avec quatre captures inspectées : FACT-2026-008 puis avoir FACT-2026-009, type et origine conservés. Mypy reste à 937. La première porte complète donne 4 300 cas avec deux échecs du harnais B-1758 : les sentinelles attendent un index Git dans la copie. L’index isolé est ajouté, les deux sentinelles passent et leur désactivation reproduit les deux échecs. La porte complète corrigée passe 4 300 cas, zéro échec/erreur, cinq skips et Ruff 0 : [preuve](../.app-loop/cycles/15/reprise/portes-preservees-backend-20261001T054758.736479Z/backend-manifest.json). Les fichiers copiés et les 69 preuves historiques sont contrôlés avant/après. P160 est stable ; P162 est traitée comme second lot, avec la qualification finale indiquée en tête.

Le total corrigé ciblé devient 24 fiches (18 produit, 6 contrôles), dont B-1757 et B-1758. P160 est une évolution acceptée distincte de ce comptage. P161 est livré comme [cadrage](plans/2026-10-01-decisions-et-cadrage-cycle15.md), avec une relecture documentaire indépendante sans blocage ; le futur parcours financier reste à développer.

## P162 : indice de colonnes

L’indice est placé avant le tableau et suit le débordement réel, le défilement et les changements de largeur. La région se rejoint avec Tab ; les flèches et la molette restent natives. Les 18 nouveaux cas et les 55 voisins passent (73 au total), TypeScript et ESLint passent avec un avertissement préexistant. Trois copies sabotées échouent comme attendu sur 15, 1 et 14 assertions, sans erreur ni skip. La source et le test restent identiques après les sabotages ; la relecture indépendante ne trouve aucun blocage. [Gel et preuves](../.app-loop/cycles/15/reprise/p162-indice/gel-code-23833dc7.json). La qualification Chromium finale est indiquée en tête du suivi.

## Correctifs vérifiés

| Fiches | Périmètre | Résultat |
| --- | --- | --- |
| B-1615, B-1671, B-1743 à B-1745 | Facturation | Numéro définitif à la première émission ; contenu, numéros et dates des pièces déjà émises conservés ; brouillon annulé modifiable ; avoir ordinaire lié à une facture émise. |
| B-1746, B-1747 | Facturation simultanée | Réservation d’écriture avant lecture, numéro unique et premières dates conservées ; contention SQLCipher réelle signalée en HTTP 409. |
| B-1750, B-1751 | Suppression et devis | Une émission concurrente ne laisse plus supprimer la pièce ; une double conversion d’un devis ne crée qu’un brouillon. |
| B-1738 | Conversations | Titre long intégral accessible au focus et au survol, avec le tiroir de largeur existante. |
| B-1739 | Contexte | Préférence d’historique consommée, bilan après filtre/coupe, texte courant retiré distingué, persistance au rechargement et tours d’outils sous fournisseur factice. |
| B-1742, B-1756 | Pipeline | Indices avant la grille dense, titres et premières cartes visibles au focus et après Entrée ; focus rendu à la région lorsque l’indice disparaît au bord. |
| B-1748 | Fichiers | Dossiers sensibles synthétiques refusés même avec un HOME symbolique ; note ordinaire autorisée. |
| B-1749 | Chat | Une réponse non diffusée ne laisse plus de message orphelin si sa conversation est supprimée pendant sa génération. |
| B-1752 | CRM | Ouverture au clavier transmet le focus au montage réel de la fiche, sans voler un focus déplacé pendant l’attente. |
| B-1713 | Accueil | Hauteur du composeur et de l’indice réservée hors du viewport défilant ; derniers textes atteignables aux quatre tailles vérifiées. |
| B-1740, B-1741 | Instrument hors ligne | Garde avant imports produit, destinations Unix nommées et proxies refusés, chemins de données explicites et profils jetables. |
| B-1753 | Témoins d’annulation | Entrée réelle du faux flux attendue ; seules les tâches propres au témoin sont terminées, même après une assertion en échec. |
| B-1754 | Témoins de date | Six cas : trois instants figés dans trois décalages, chacun avec et sans profil, distinguent date locale et UTC. |
| B-1755 | Instrument écran | « Générer » accentué et ses variantes sont exclus avant clic ; trois générations factices restent à zéro clic, avec un clic sur le contrôle sûr. |
| B-1757 | Première émission | Le numéro annuel et les premières dates utilisent le même instant, vérifié sur PUT et paiement initial au changement d’année. |
| B-1758 | Copies des portes | Un index Git isolé conserve le contexte requis par les sentinelles ; sabotage et restauration reproduisent puis ferment leurs deux échecs. |
| B-1759 | Assemblage des preuves | La fonction de clé JUnit ne peut plus être masquée par la variable de boucle ; l’original saboté échoue avant écriture, la restauration assemble 113/113. |

Les preuves détaillées sont rangées sous `../.app-loop/cycles/15/reprise/` dans `lot-a`, `lot-b`, `lot-c`, `instrument`, `home-symbolique`, `chat-suppression`, `crm-focus`, `accueil-collision`, `backend-races`, `date-poste-b1754`, `garde-generer-b1755` et `pipeline-vertical-scroll`. Les index ciblés et la matrice font foi ; les premiers essais invalidés sont conservés et explicitement exclus.

### Dernier défaut du Pipeline

À 800 × 900, les indices placés sous une grille dense de 1436 px entraînaient le panneau CRM à `scrollTop=886` dès leur focus. Titres et premières cartes devenaient invisibles. Le correctif `fbfa29f1` déplace uniquement le bloc des indices avant la grille. Les gestionnaires, les huit étapes, les fondus, le glisser-déposer et le transfert conditionnel du focus restent vérifiés.

Le rouge et le sabotage source ont chacun une assertion attendue sur 14 cas, sans erreur ; le vert passe les 30 voisins. Le sabotage DOM retrouve le déplacement à 886. Le [vert natif courant](../.app-loop/cycles/15/reprise/pipeline-vertical-scroll/native-vert-af1nf5_d/mesures.json) conserve titres et premières cartes dans la zone affichée, `scrollTop=0` au focus des indices et aux Entrées. Tab peut aligner la région à 62 px sans masquer le contenu. La colonne partiellement présente au bord horizontal peut garder son titre coupé : `headerVisible` mesure une intersection après clipping, pas une lecture intégrale ; l’indice gauche permet de la rejoindre. Ce cas reste distinct de la disparition verticale corrigée. Ses 54 contacts synthétiques sont strictement identiques avant/après, en nombre et en empreinte. Les assertions trop strictes de Tab à zéro et du nombre historique 45 sont exclues et conservées.

## Portes complètes et carte avant les décisions déléguées

| Contrôle sur la source figée | Résultat | Preuve |
| --- | --- | --- |
| Backend | 4 288 cas, zéro échec/erreur, cinq skips ; Ruff 0 | [Manifeste backend](../.app-loop/cycles/15/reprise/portes-backend-20260930T233501.395429Z/backend-manifest.json) |
| Frontend | 3 412 cas, zéro échec/erreur/skip ; TypeScript, ESLint et build 0 | [Manifeste frontend](../.app-loop/cycles/15/reprise/portes-frontend-20260930T233454.319642Z/frontend-manifest.json) |
| Couverture sémantique | PASS, 2 107/2 107 fichiers, aucune preuve ou seconde lecture manquante | [Carte immuable](../.app-loop/cycles/15/reprise/carte-final-fbfa29f1.json) |
| Garde de couverture | 20/20 TAP | [TAP courant](../.app-loop/cycles/15/reprise/runtime/tap-20260930T233617.121803Z/couverture-ecran.tap) |
| Pipeline, contexte et titres | Parcours Chromium passé sur la source courante | [Recette](../.app-loop/cycles/15/reprise/runtime/recette-2026-09-30T23-36-19-236Z/recette.json) |
| Factures et avoirs | Brouillon modifiable, pièce émise figée, origine chargée et consigne adaptée | [Recette](../.app-loop/cycles/15/reprise/runtime/facturation-2026-09-30T23-36-34-276Z/recette.json) |
| Focus CRM | Entrée, Tab Étape/Score et respect du focus déplacé | [Recette](../.app-loop/cycles/15/reprise/runtime/crm-focus-2026-09-30T23-36-39-374Z/recette.json) |
| Clavier Accueil | Deux contextes : Entrée termine le défilement, Tab rejoint le composeur avec focus visible | [Qualification](../.app-loop/cycles/15/reprise/accueil-collision/clavier-2026-09-30T23-37-09-030Z/qualification.json) |

Les lectures primaires et secondaires portent sur les fichiers complets et leurs empreintes actuelles. Les 111 signaux historiques d’invariants divergents restent arbitrés par l’humain ; aucun nouvel arbitrage n’est ajouté. La carte générée distingue les risques agrégés historiques des fiches actuellement actives.

## Pile jetable et calibration

Frontend canonique sur `1420`, backend sur `17393`. HOME et données sont sous `/private/tmp/therese-c15-codex-runtime-h8n2vaxw`. Environnement explicitement construit, sans clé ni proxy hérité ; répertoires courants et `envDir` vides ; garde hors ligne avant imports. Les chemins de base sont vérifiés par l’attestation et l’API. Le port réel `17293`, `~/.therese` et les comptes ne sont pas utilisés.

La pile du plateau précédent a été [arrêtée après validation](../.app-loop/cycles/15/reprise/runtime/arret-final-20261001.json) : ses deux PID sont absents et aucune écoute ne reste sur 1420/17393. Les profils, bases et preuves sont conservés.

Les six instruments passent témoins positifs, négatifs et restauration dans le [bilan de calibration](../.app-loop/cycles/15/reprise/runtime/all-20260930T230311.012678Z/calibration-summary.json). Ils ont été enregistrés à 23:10:03 UTC le 30/09, validité jusqu’au 02/10 à 23:10:03 UTC. Cette calibration garde son vrai HEAD `5f291d40` : B1756 modifie le Pipeline et son test, aucun instrument. Son statut canonique est encore PASS lors du début de la validation finale.

Outils constatés : Node 22.19.0, Playwright 1.58.2, Chromium 145.0.7632.6, pytest 9.0.2 et Vitest 4.0.17. Les recettes UI utilisent Chromium ; elles ne valident pas le packaging natif.

## Rondes finales avant les décisions déléguées

La [première ronde finale](../.app-loop/cycles/15/reprise/plateau-c15-r1-fbfa29f1-v2/evidence.json), exécutée par root et arbitrée par `cycle15_lots_review`, puis la [seconde](../.app-loop/cycles/15/reprise/plateau-c15-r2-fbfa29f1/evidence.json), exécutée par `cycle15_lots_review` et arbitrée par `cycle15_inventory`, sont acceptées : **2/2**. Les journaux d’évaluation sont conservés dans les mêmes dossiers. Aucune couverture précédente n’est assimilée à une ronde propre : celle sur `6bf4f66d` a révélé B1755 ; celle sur `5f291d40` a révélé B1756. La source `fbfa29f1` est restée figée pendant les deux rondes.

| Ronde | Couverture réelle | Arbitrage indépendant | Transitions |
| --- | --- | --- | --- |
| R1 | 84 captures ; 588 entrées de gestes : 223 changements, 229 non localisés, 104 exclus, 16 inactifs, 11 déjà sélectionnés, 4 natifs, 1 inchangé | [26 IDs : 23 limites acceptées, 3 faux positifs, zéro nouveau défaut établi](../.app-loop/cycles/15/reprise/runtime/couverture-c15-root-round1-fbfa29f1-20260930T234217.438211Z/tri-independant-cycle15-lots-review-fbfa29f1.json) | [110/110](../.app-loop/cycles/15/reprise/transitions/final-ronde1-fbfa29f1/manifeste-critique-c15.json) |
| R2 | 84 captures ; 653 entrées de gestes : 181 changements, 321 non localisés, 150 non exercés, 1 inchangé | [26 IDs : 25 diagnostics/limites acceptés, 1 faux positif, zéro nouveau défaut établi](../.app-loop/cycles/15/reprise/runtime/couverture-c15-review-round2-fbfa29f1-20261001T001453.850100Z/tri-independant-cycle15_inventory.json) | [110/110](../.app-loop/cycles/15/reprise/transitions/final-ronde2-fbfa29f1/manifeste-critique-c15.json) |

Chaque ronde ouvre 21 écrans à deux largeurs et dans deux thèmes ; les gestes automatiques concernent seulement 1440 px en clair. Les listes de gestes diffèrent selon les fixtures, ne représentent pas autant de boutons uniques et ne prouvent pas les gestes non exercés. Chaque manifeste critique vérifie 235 fichiers SHA, 534 cas JUnit précis, 95 pointeurs JSON et 20 TAP. L’[audit du tri R2](../.app-loop/cycles/15/reprise/runtime/couverture-c15-review-round2-fbfa29f1-20261001T001453.850100Z/validation-tri-cycle15_inventory.json) vérifie 161 fichiers SHA et 65 pointeurs sans erreur ; son lecteur a inspecté 84 originaux et 29 compléments.

Les portes sont rejouées indépendamment en R2 : [backend 4 288 cas, zéro échec/erreur, cinq skips et Ruff 0](../.app-loop/cycles/15/reprise/portes-backend-20261001T000723.729439Z/backend-manifest.json), [frontend 3 412 cas verts, TypeScript/ESLint/build 0](../.app-loop/cycles/15/reprise/portes-frontend-20261001T000712.643571Z/frontend-manifest.json), [TAP 20/20](../.app-loop/cycles/15/reprise/runtime/tap-20261001T000801.654288Z/couverture-ecran.tap). Les [trois recettes fraîches R2](../.app-loop/cycles/15/reprise/runtime/couverture-c15-review-round2-fbfa29f1-20261001T001453.850100Z/actor-r2-manifest.json) passent neuf contrôles. La recette Pipeline GET seule conserve 63 contacts et leur empreinte avant/après ; le clavier Accueil observe BODY après disparition de l’indice puis Tab au composeur avec focus visible, sans démontrer un maintien explicite du focus ni un lecteur d’écran.

La [recette complémentaire Factures R2](../.app-loop/cycles/15/reprise/runtime/factures-defilement-2026-10-01T00-37-23-413Z/qualification-r2.json) passe trois contrôles à 800 × 900 en clair : molette réelle de 0 à 392 px, titres et première ligne d’Envoi/Paiement/Échéance lisibles au bord. Six images sont inspectées, aucune écriture ; les 84 captures et six rapports bruts antérieurs restent identiques. Ce geste n’est pas attribué aux captures initiales du tableau ni au thème sombre.

## Décisions et limites

P-157 (indices Pipeline) et P-159 (historique/contexte transmis) sont acceptées et implémentées. P-158 a été rejetée et remplacée par B-1738 ; aucun tiroir redimensionnable n’est ajouté. La [décision déléguée du 01/10 et le cadrage](plans/2026-10-01-decisions-et-cadrage-cycle15.md) retiennent la série FACT commune pour les prochaines émissions, le cadrage de rectification d’un avoir et un indice avant le tableau Factures. Aucun numéro historique n’est modifié. Les résultats courants des lots P160 et P162 sont indiqués en tête de ce suivi.

### Revue initiale des propositions avant la délégation

Le scan borné couvre les personas métier/comptable, chat et petit écran/clavier, à partir des parcours R2 et des 160 propositions lues. Les [preuves et déduplication](../.app-loop/cycles/15/reprise/gap-scan/synthese-canonique-c15.json) réunissent deux rapports : métier/chat (27 références, 16 pointeurs et 14 ancres vérifiés) et petit écran/clavier (130 fichiers SHA et 49 pointeurs vérifiés), sans erreur. Aucun test ou appel supplémentaire n’est lancé pour ce scan. Le besoin d’indice dans Factures, observé par deux lecteurs, devient une seule proposition ; le chat n’en ajoute aucune. Les copies exactes des registres au moment de la lecture sont conservées avant l’ajout canonique.

| Proposition au portail initial | Observation et choix demandé | Impact / effort / recommandation |
| --- | --- | --- |
| P-160 | Choisir une série commune pour les prochaines factures/avoirs, ou conserver FACT/AV distinctes après justification comptable. | Impact métier ; lot isolé avec migration/concurrence après décision. Recommandation : série commune pour les prochaines émissions. |
| P-161 | Cadrer un parcours pour rectifier un avoir déjà émis : l’écran renvoie actuellement vers un avis comptable, sans pièce rectificative liée dans le formulaire. Distinct de P154 (avoir lié à une facture). | Impact moyen ; cadrage avant estimation/code. Recommandation : décider d’abord du cadrage comptable. |
| P-162 | Signaler les colonnes hors cadre dans Devis et factures : à 800 px elles sont accessibles par défilement, mais aucun indice ne les annonce. Distinct des étapes du Pipeline P157. | Impact moyen ; petit effort estimé à confirmer par maquette. Recommandation : indice discret. |

Ce portail initial a reçu la délégation explicite de Ludo le 01/10 : les trois propositions sont désormais `accepted`, avec leurs raisons enregistrées par `app_loop.py`. Le document de décision porte les critères et les sources officielles relues. P161 est un livrable de cadrage documentaire ; une proposition de code est traitée à la fois, avec stabilisation et contrôles de la zone modifiée.

La disponibilité des modèles est déclarée : Claude `quota_exhausted`, Grok `unavailable`, GPT disponible, diversité dégradée. Aucun fallback payant ni appel de fournisseur réel n’est utilisé. Les anciens compteurs estimatifs ne constituent pas une mesure actuelle des jetons de la reprise.

Limites conservées : 295 fiches différées antérieures, dont B-1558 (suffixe null d’une fiche) et B-1635 (bouton Supprimer encore visible sur une pièce émise, puis refus HTTP 409). Le [complément de lecture](../.app-loop/cycles/15/reprise/gap-scan/complement-affordance-suppression-emis-factures-indice-20261001T081432.205068Z.json) confirme la dette de présentation ; la protection backend corrigée ne la supprime pas. Aucun effacement de pièce émise n’est exercé par cette lecture ; B-1737 décrit un autre mécanisme que le témoin B-1753. Cinq skips backend : bundle Linux opt-in, updater réseau réel opt-in, cas d’indisponibilité Whisper non testable car faster-whisper est installé, deux fournisseurs d’images réels. Dette mypy : 937 erreurs, baseline préexistante respectée par nombre, sans contrôle d’identité de chaque erreur ; 26 avertissements ESLint. Tests Windows natifs, lecteurs d’écran, packaging et fournisseurs payants non validés. Pour P159, l’écran est vérifié sur métadonnées synthétiques ; le calcul/persistance HTTP est exercé sous fournisseur factice. La mise en statut Envoyée de la fixture facture n’envoie aucun courriel.

Le [changelog](CHANGELOG.md) porte une section « Non publié ». Aucune nouvelle version, publication, release, PR ou intégration à main n’est réalisée par cette reprise.

### Périmètre de release

Le skill `release-therese` classe cette reprise en correctifs et évolutions acceptées. Il exige un accord explicite sur la version et sa publication avant la publication complète ; les accords antérieurs du cycle 14 ne sont pas étendus à une nouvelle release. Les décisions P160/P161/P162 déléguées sont exécutées dans leur périmètre, sans nouvelle décision métier en attente.

| Porte | État de cette reprise |
| --- | --- |
| Code et contrôles | Source `d4f19d74`, deux rondes propres acceptées, limites ci-dessus. |
| Version | 0.76.1 inchangée ; aucun bump. |
| Changelog | Section « Non publié » mise à jour ; suivi et carte actualisés. |
| Merge, tag, build/CI de release, assets et release GitHub | Non autorisés pour une nouvelle publication dans cette reprise. Le build frontend de contrôle ne constitue pas un binaire de release. |
| Landing, updater, rapport versionné, Discord, installation et agents | Non autorisés pour une nouvelle release ; aucun résultat antérieur n’est attribué au cycle 15. |
| Contrôles post-release | Non applicables tant qu’aucune nouvelle version n’est publiée. |


## Rejouer les contrôles locaux

Le harnais est conservé dans `../.app-loop/cycles/15/reprise/`, ignoré par Git, avec ses sources, profils et journaux. Le [guide runtime](../.app-loop/cycles/15/reprise/runtime/README.md) contient les commandes. Les registres sont modifiés uniquement par `app_loop.py`, les scripts de preuve ne les mutent pas.

La section « Commandes de validation finale » de ce guide porte les procédures de portes, TAP, fixtures, couverture, témoins complémentaires, assemblage et arrêt. Le refus initial du journal TypeScript vide reste archivé ; aucun test n’a été rejoué pour corriger ce format de preuve. Les corrections B1755 et B1756 ne réécrivent aucune preuve de leurs anciennes couvertures.

Les scripts exacts de deux anciens témoins Pipeline précommit n’avaient ni copie ni hash ; leur replay exact reste non attesté. Les mesures, captures et SHA produit sont conservés. Le helper min10/5 du vert courant est archivé avec sa vraie empreinte, voir [audit de conservation](../.app-loop/cycles/15/reprise/pipeline-vertical-scroll/conservation-helpers-597643c45bdb40a39e7251203eba02fe.json).

Les WIP, preuves d’origine et ancienne application sont conservés. Le verrou `.agents-sync-paused` évite une synchronisation automatique pendant la reprise. Aucun nettoyage définitif n’est effectué.
