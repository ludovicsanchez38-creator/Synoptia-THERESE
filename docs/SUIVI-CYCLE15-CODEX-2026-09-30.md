# Reprise du cycle 15 THÉRÈSE

## État vérifié

Mise à jour le 1er octobre 2026. La reprise demandée par Ludo a récupéré les lots commencés dans Claude Code puis interrompus faute de budget. Les **22 fiches ciblées sont corrigées : 17 sur le produit et 5 sur les contrôles**. L’évaluateur canonique a accepté **deux rondes indépendantes successives : 2/2**, sur la source figée `fbfa29f1`. La revue des propositions est terminée ; la boucle est en `HUMAN_GATE`, avec trois décisions en attente. Les transitions de cette reprise sont normales ; les 23 anciennes transitions forcées restent historiques.

Source figée : `fbfa29f1b8fd69ab7bf7af0652aa0775d71798cd`, branche `codex/cycle-15`, dans `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex`. Le push sur `origin` est vérifié par `ls-remote`. Le dépôt d’origine est propre et `main` local/distant reste à `887669c37f1488034512cab846c04d257a2e45f2`, version `0.76.1`.

Le lot final de documentation porte uniquement le suivi, le changelog et la carte générée. Les portes et captures gardent leur vrai HEAD de code `fbfa29f1` ; un commit de documentation ultérieur ne vaut pas un rejeu des tests.

La [matrice canonique des corrections](../.app-loop/cycles/15/reprise/matrice-corrections.json) indexe les rouges, verts et sabotages. Son [audit](../.app-loop/cycles/15/reprise/audit-matrice-22-fbfa29f1.json) vérifie 69 références uniques sans erreur d’empreinte. Les suites ciblées se recouvrent ; leurs nombres ne s’additionnent pas.

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

Les preuves détaillées sont rangées sous `../.app-loop/cycles/15/reprise/` dans `lot-a`, `lot-b`, `lot-c`, `instrument`, `home-symbolique`, `chat-suppression`, `crm-focus`, `accueil-collision`, `backend-races`, `date-poste-b1754`, `garde-generer-b1755` et `pipeline-vertical-scroll`. Les index ciblés et la matrice font foi ; les premiers essais invalidés sont conservés et explicitement exclus.

### Dernier défaut du Pipeline

À 800 × 900, les indices placés sous une grille dense de 1436 px entraînaient le panneau CRM à `scrollTop=886` dès leur focus. Titres et premières cartes devenaient invisibles. Le correctif `fbfa29f1` déplace uniquement le bloc des indices avant la grille. Les gestionnaires, les huit étapes, les fondus, le glisser-déposer et le transfert conditionnel du focus restent vérifiés.

Le rouge et le sabotage source ont chacun une assertion attendue sur 14 cas, sans erreur ; le vert passe les 30 voisins. Le sabotage DOM retrouve le déplacement à 886. Le [vert natif courant](../.app-loop/cycles/15/reprise/pipeline-vertical-scroll/native-vert-af1nf5_d/mesures.json) conserve titres et premières cartes dans la zone affichée, `scrollTop=0` au focus des indices et aux Entrées. Tab peut aligner la région à 62 px sans masquer le contenu. La colonne partiellement présente au bord horizontal peut garder son titre coupé : `headerVisible` mesure une intersection après clipping, pas une lecture intégrale ; l’indice gauche permet de la rejoindre. Ce cas reste distinct de la disparition verticale corrigée. Ses 54 contacts synthétiques sont strictement identiques avant/après, en nombre et en empreinte. Les assertions trop strictes de Tab à zéro et du nombre historique 45 sont exclues et conservées.

## Portes complètes et carte

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

La pile de test est [arrêtée après validation](../.app-loop/cycles/15/reprise/runtime/arret-final-20261001.json) : ses deux PID sont absents et aucune écoute ne reste sur 1420/17393. Les profils, bases et preuves sont conservés.

Les six instruments passent témoins positifs, négatifs et restauration dans le [bilan de calibration](../.app-loop/cycles/15/reprise/runtime/all-20260930T230311.012678Z/calibration-summary.json). Ils ont été enregistrés à 23:10:03 UTC le 30/09, validité jusqu’au 02/10 à 23:10:03 UTC. Cette calibration garde son vrai HEAD `5f291d40` : B1756 modifie le Pipeline et son test, aucun instrument. Son statut canonique est encore PASS lors du début de la validation finale.

Outils constatés : Node 22.19.0, Playwright 1.58.2, Chromium 145.0.7632.6, pytest 9.0.2 et Vitest 4.0.17. Les recettes UI utilisent Chromium ; elles ne valident pas le packaging natif.

## Rondes finales

La [première ronde finale](../.app-loop/cycles/15/reprise/plateau-c15-r1-fbfa29f1-v2/evidence.json), exécutée par root et arbitrée par `cycle15_lots_review`, puis la [seconde](../.app-loop/cycles/15/reprise/plateau-c15-r2-fbfa29f1/evidence.json), exécutée par `cycle15_lots_review` et arbitrée par `cycle15_inventory`, sont acceptées : **2/2**. Les journaux d’évaluation sont conservés dans les mêmes dossiers. Aucune couverture précédente n’est assimilée à une ronde propre : celle sur `6bf4f66d` a révélé B1755 ; celle sur `5f291d40` a révélé B1756. La source `fbfa29f1` est restée figée pendant les deux rondes.

| Ronde | Couverture réelle | Arbitrage indépendant | Transitions |
| --- | --- | --- | --- |
| R1 | 84 captures ; 588 entrées de gestes : 223 changements, 229 non localisés, 104 exclus, 16 inactifs, 11 déjà sélectionnés, 4 natifs, 1 inchangé | [26 IDs : 23 limites acceptées, 3 faux positifs, zéro nouveau défaut établi](../.app-loop/cycles/15/reprise/runtime/couverture-c15-root-round1-fbfa29f1-20260930T234217.438211Z/tri-independant-cycle15-lots-review-fbfa29f1.json) | [110/110](../.app-loop/cycles/15/reprise/transitions/final-ronde1-fbfa29f1/manifeste-critique-c15.json) |
| R2 | 84 captures ; 653 entrées de gestes : 181 changements, 321 non localisés, 150 non exercés, 1 inchangé | [26 IDs : 25 diagnostics/limites acceptés, 1 faux positif, zéro nouveau défaut établi](../.app-loop/cycles/15/reprise/runtime/couverture-c15-review-round2-fbfa29f1-20261001T001453.850100Z/tri-independant-cycle15_inventory.json) | [110/110](../.app-loop/cycles/15/reprise/transitions/final-ronde2-fbfa29f1/manifeste-critique-c15.json) |

Chaque ronde ouvre 21 écrans à deux largeurs et dans deux thèmes ; les gestes automatiques concernent seulement 1440 px en clair. Les listes de gestes diffèrent selon les fixtures, ne représentent pas autant de boutons uniques et ne prouvent pas les gestes non exercés. Chaque manifeste critique vérifie 235 fichiers SHA, 534 cas JUnit précis, 95 pointeurs JSON et 20 TAP. L’[audit du tri R2](../.app-loop/cycles/15/reprise/runtime/couverture-c15-review-round2-fbfa29f1-20261001T001453.850100Z/validation-tri-cycle15_inventory.json) vérifie 161 fichiers SHA et 65 pointeurs sans erreur ; son lecteur a inspecté 84 originaux et 29 compléments.

Les portes sont rejouées indépendamment en R2 : [backend 4 288 cas, zéro échec/erreur, cinq skips et Ruff 0](../.app-loop/cycles/15/reprise/portes-backend-20261001T000723.729439Z/backend-manifest.json), [frontend 3 412 cas verts, TypeScript/ESLint/build 0](../.app-loop/cycles/15/reprise/portes-frontend-20261001T000712.643571Z/frontend-manifest.json), [TAP 20/20](../.app-loop/cycles/15/reprise/runtime/tap-20261001T000801.654288Z/couverture-ecran.tap). Les [trois recettes fraîches R2](../.app-loop/cycles/15/reprise/runtime/couverture-c15-review-round2-fbfa29f1-20261001T001453.850100Z/actor-r2-manifest.json) passent neuf contrôles. La recette Pipeline GET seule conserve 63 contacts et leur empreinte avant/après ; le clavier Accueil observe BODY après disparition de l’indice puis Tab au composeur avec focus visible, sans démontrer un maintien explicite du focus ni un lecteur d’écran.

La [recette complémentaire Factures R2](../.app-loop/cycles/15/reprise/runtime/factures-defilement-2026-10-01T00-37-23-413Z/qualification-r2.json) passe trois contrôles à 800 × 900 en clair : molette réelle de 0 à 392 px, titres et première ligne d’Envoi/Paiement/Échéance lisibles au bord. Six images sont inspectées, aucune écriture ; les 84 captures et six rapports bruts antérieurs restent identiques. Ce geste n’est pas attribué aux captures initiales du tableau ni au thème sombre.

## Décisions et limites

P-157 (indices Pipeline) et P-159 (historique/contexte transmis) sont acceptées et implémentées. P-158 a été rejetée et remplacée par B-1738 ; aucun tiroir redimensionnable n’est ajouté. P-160 reste en attente : choisir la règle des prochaines séries factures/avoirs. Aucun numéro historique n’est modifié.

### Revue des propositions après plateau

Le scan borné couvre les personas métier/comptable, chat et petit écran/clavier, à partir des parcours R2 et des 160 propositions lues. Les [preuves et déduplication](../.app-loop/cycles/15/reprise/gap-scan/synthese-canonique-c15.json) réunissent deux rapports : métier/chat (27 références, 16 pointeurs et 14 ancres vérifiés) et petit écran/clavier (130 fichiers SHA et 49 pointeurs vérifiés), sans erreur. Aucun test ou appel supplémentaire n’est lancé pour ce scan. Le besoin d’indice dans Factures, observé par deux lecteurs, devient une seule proposition ; le chat n’en ajoute aucune. Les copies exactes des registres au moment de la lecture sont conservées avant l’ajout canonique.

| Proposition en attente | Observation et choix demandé | Impact / effort / recommandation |
| --- | --- | --- |
| P-160 | Choisir une série commune pour les prochaines factures/avoirs, ou conserver FACT/AV distinctes après justification comptable. | Impact métier ; lot isolé avec migration/concurrence après décision. Recommandation : série commune pour les prochaines émissions. |
| P-161 | Cadrer un parcours pour rectifier un avoir déjà émis : l’écran renvoie actuellement vers un avis comptable, sans pièce rectificative liée dans le formulaire. Distinct de P154 (avoir lié à une facture). | Impact moyen ; cadrage avant estimation/code. Recommandation : décider d’abord du cadrage comptable. |
| P-162 | Signaler les colonnes hors cadre dans Devis et factures : à 800 px elles sont accessibles par défilement, mais aucun indice ne les annonce. Distinct des étapes du Pipeline P157. | Impact moyen ; petit effort estimé à confirmer par maquette. Recommandation : indice discret. |

Le skill `boucle-amelioration-app` attend une réponse humaine sur ces propositions : oui, non ou plus tard ; P160 demande aussi le choix de série. Les propositions restent `pending`, sans décision supposée. La boucle reste active au portail humain. Une éventuelle implémentation devra reprendre la stabilisation et les contrôles de la zone modifiée.

La disponibilité des modèles est déclarée : Claude `quota_exhausted`, Grok `unavailable`, GPT disponible, diversité dégradée. Aucun fallback payant ni appel de fournisseur réel n’est utilisé. Les anciens compteurs estimatifs ne constituent pas une mesure actuelle des jetons de la reprise.

Limites conservées : 295 fiches différées antérieures, dont B-1558 (suffixe null d’une fiche) ; B-1737 décrit un autre mécanisme que le témoin B-1753. Cinq skips backend : bundle Linux opt-in, updater réseau réel opt-in, cas d’indisponibilité Whisper non testable car faster-whisper est installé, deux fournisseurs d’images réels. Dette mypy : 937 erreurs, baseline préexistante sans augmentation ; 26 avertissements ESLint. Tests Windows natifs, lecteurs d’écran, packaging et fournisseurs payants non validés. Pour P159, l’écran est vérifié sur métadonnées synthétiques ; le calcul/persistance HTTP est exercé sous fournisseur factice. La mise en statut Envoyée de la fixture facture n’envoie aucun courriel.

Le [changelog](CHANGELOG.md) porte une section « Non publié ». Aucune nouvelle version, publication, release, PR ou intégration à main n’est réalisée par cette reprise.

## Rejouer les contrôles locaux

Le harnais est conservé dans `../.app-loop/cycles/15/reprise/`, ignoré par Git, avec ses sources, profils et journaux. Le [guide runtime](../.app-loop/cycles/15/reprise/runtime/README.md) contient les commandes. Les registres sont modifiés uniquement par `app_loop.py`, les scripts de preuve ne les mutent pas.

La section « Commandes de validation finale » de ce guide porte les procédures de portes, TAP, fixtures, couverture, témoins complémentaires, assemblage et arrêt. Le refus initial du journal TypeScript vide reste archivé ; aucun test n’a été rejoué pour corriger ce format de preuve. Les corrections B1755 et B1756 ne réécrivent aucune preuve de leurs anciennes couvertures.

Les scripts exacts de deux anciens témoins Pipeline précommit n’avaient ni copie ni hash ; leur replay exact reste non attesté. Les mesures, captures et SHA produit sont conservés. Le helper min10/5 du vert courant est archivé avec sa vraie empreinte, voir [audit de conservation](../.app-loop/cycles/15/reprise/pipeline-vertical-scroll/conservation-helpers-597643c45bdb40a39e7251203eba02fe.json).

Les WIP, preuves d’origine et ancienne application sont conservés. Le verrou `.agents-sync-paused` évite une synchronisation automatique pendant la reprise. Aucun nettoyage définitif n’est effectué.
