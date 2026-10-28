# Lot 1 C22A : premier usage, aide et reprise des données

Rapport du 28 octobre 2026. Branche `boucle/c22a-premier-usage`, base `45be2f16`. Travail effectué uniquement dans cet arbre. Aucun push, tag, déploiement, redémarrage de service existant ou envoi de message. Les serveurs de recette étaient des processus locaux dédiés, arrêtés après les tests.

Le chemin annoncé par `-o` n’était pas présent dans la demande reçue. Ce fichier est le chemin de repli annoncé pendant le travail.

Sources lues : synthèse de l’audit du 27 octobre, rapports A2, A5 et A6, source du guide bêta et PDF fourni, risque B-1344 dans `docs/application-map/risques.md`.

## Résultat et commits

| Point | État | Commit |
| --- | --- | --- |
| 1. Reprise des copies automatiques | Fait | `05b30832` fix(données): proposer la reprise des copies au démarrage (B-1341) |
| 2. Refus des blocs thinking | Hypothèse confirmée, corrigé | `d111b826` fix(anthropic): conserver le système pendant les appels d’outils |
| 3. Aide et ouverture des PDF | Fait ; recette native installée à compléter | `6c683279` fix(aide): embarquer le guide et ouvrir les PDF avec une portée limitée |
| 4. Première IA utilisable | Fait ; essais avec compte réel et Ollama à compléter | `5b782719` feat(accueil): guider la connexion à Claude et l’installation d’Ollama |
| 5. Sécurité, dépliage hors cadre | Reproduit dans Chromium, corrigé | `2bdd04b3` fix(accueil): attendre la fin du dépliage des risques (B-1344) |

## 1. Reprise des copies automatiques

Le démarrage vérifie la base avec `quick_check`. Une base illisible, une erreur d’initialisation ou une migration qui lève ouvre un mode de récupération : le moteur reste joignable, les routes métier sont bloquées et les routes de reprise exigent le jeton de session. Le splash reconnaît immédiatement l’état `recovery`.

L’écran présente les dates et versions, demande confirmation, annonce ce qui revient à l’état ancien et permet de redémarrer après restauration. La version affichée est celle du moteur qui a pris la copie avant migration ; le texte le précise.

La copie choisie est préparée et vérifiée avant déplacement des originaux. La base courante, son WAL, son SHM, son éventuel journal et le fichier de clé sont mis de côté dans un dossier unique sous `backups/reprises`. Ces abris ne sont pas élagués automatiquement. Un témoin interdit le démarrage normal après une interruption au milieu des déplacements. L’effacement explicite des données emporte aussi ces abris.

Une base illisible ne fait plus tourner la rétention des trois copies. Une base vide valide peut encore s’initialiser ; elle n’est pas acceptée comme copie à restaurer. Les liens symboliques dans les copies et les identifiants de copie étrangers sont refusés.

Limites : ces copies couvrent la base et sa clé, pas les documents ni l’index vectoriel, ce que la confirmation dit. Il n’y a pas de nouvelle interface de restauration des archives manuelles quand aucune copie automatique n’existe. Pas d’essai de panne électrique réelle ni de restauration d’un profil utilisateur réel.

Tests moteur : 26 réussis, dans `test_reprise_copies_auto.py`, `test_b1341_copie_automatique_avant_demarrage.py` et `test_migration_errors.py`. Cas couverts : confirmation et authentification, migration en échec, copie illisible, conservation des originaux, interruption pendant le déplacement, SQLCipher avec WAL, chemins refusés, effacement et base vide valide. Les nouveaux tests de reprise échouaient avant l’ajout ; le cas de base vide a également été vérifié rouge puis vert.

Tests interface : 40 réussis au total, dans `RepriseDonnees.test.tsx`, `SplashScreen.reprise.test.tsx`, `SplashScreen.b1262.test.tsx` et `SplashScreen.sidecarFatal.test.tsx`.

## 2. Système stable pour Anthropic

La documentation officielle confirme précisément l’hypothèse : les modèles récents vérifient la liaison des blocs thinking au système, aux outils et aux messages précédents. Le contrôle concerne notamment les comptes créés depuis le 31 août 2026. Un changement du préfixe peut entraîner un refus 400. Sources consultées le 28 octobre : [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) et [Troubleshooting thinking](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#a-400-error-says-a-thinking-block-signature-is-invalid).

La continuation Anthropic ne relit plus les fiches pour reconstruire le système au milieu d’une boucle d’outils. Elle conserve le contrôle de taille sans retailler le préfixe. Le prochain tour utilisateur relit les fiches. Les résultats des outils restent transmis immédiatement.

Tests : 34 réussis, dans `test_anthropic_systeme_stable.py`, `test_anthropic_blocs_de_reflexion.py`, `test_b1502_suite_des_outils_meme_fournisseur.py`, `test_c19e_fiche_ecrite_au_tour.py` et `test_r6_prefixe_cache.py`. Le vrai adaptateur reçoit les réponses d’un serveur simulé : avant correction, les deux cas renvoyaient le refus 400 ; après, les signatures sont conservées et les nouvelles fiches apparaissent au tour suivant. Aucun appel à Anthropic avec une clé réelle.

Détail : `docs/notes-techniques/c22a-thinking-anthropic.md`.

## 3. Aide et PDF locaux

L’entrée Aide existe dans les paramètres, dans le rail de l’accueil et dans la première étape de configuration. Elle propose le PDF local et le lien sécurité de B-1349.

Le PDF fourni est copié sans modification dans `src/frontend/src-tauri/resources/guide-therese-0.82.pdf`, déclaré dans les ressources communes et dans la surcharge Linux. La couverture porte 0.82.0. Taille : 2 371 838 octets. SHA-256 identique à l’original : `3c6b7de9045bb5cecdf073c4f2f608b053979689f205947e5b9d1f77b71e4ffe`.

Le greffon Tauri Opener 2.5.0 remplace l’usage de Shell pour les fichiers. Sa permission côté interface est limitée au seul fichier du guide sous `$RESOURCE`. Pour une facture, la commande native reçoit uniquement son identifiant et le jeton de session. Elle demande au moteur le PDF de cette facture, dans le dossier de factures configuré, puis l’ouvre avec Opener. L’écran ne peut fournir ni chemin arbitraire ni programme d’ouverture. Les liens sortant du dossier des factures sont refusés. [Documentation officielle du greffon](https://v2.tauri.app/plugin/opener/).

Tests : 7 réussis côté moteur dans `test_facture_pdf_ouverture.py`. Côté interface, 15 réussis dans `Aide.test.tsx`, `pdfLocaux.test.ts`, `InvoicesPanel.test.tsx` et `InvoicesPanel.causePdf.test.tsx`. Le test du panneau échouait avec l’ancien appel Shell et passe avec le nouveau mécanisme. La portée du guide et les deux déclarations de ressource sont contrôlées. Un scénario Chromium vérifie aussi le clic jusqu’à l’appel Opener, avec IPC simulé.

Vérification Rust Linux réussie : `cargo check --lib --no-default-features -j 1`, avec une surcharge temporaire `TAURI_CONFIG` retirant `externalBin` et ne gardant que la ressource du guide. Les premiers essais sans cette surcharge ont rencontré le moteur embarqué absent, puis le frontend de production non construit. Ce contrôle valide les commandes et l’intégration du greffon ; il ne constitue pas une recette d’un paquet installé.

À vérifier sur Linux installé, Mac et Windows : résolution réelle de la ressource dans le paquet, ouverture par le lecteur PDF par défaut, ouverture d’une facture dans le dossier par défaut puis dans un dossier choisi, comportement sans lecteur associé. Sur Windows, vérifier aussi un PDF déjà ouvert dans un lecteur qui verrouille le fichier. Aucun paquet de distribution n’a été construit ou installé.

## 4. Première connexion à une IA

Un même panneau d’aide est présent dans l’assistant et les paramètres, avant le choix du fournisseur. Le parcours Claude explique ce qu’est une clé, le compte Console, les crédits, le plafond, l’espace de travail et le retour dans THÉRÈSE pour enregistrer et vérifier la clé. Les liens vont directement à la Console, à Billing, aux clés et à la page des tarifs. Aucun montant n’est inscrit dans l’application. Le catalogue Anthropic conserve Opus par défaut, vérifié dans le test d’accueil.

Le parcours local reste dépliable même quand Ollama est indisponible. Il donne le téléchargement officiel, la commande `ollama run qwen3.5:4b`, l’indication d’environ 3,3 Go et un bouton pour vérifier la disponibilité après installation. La vérification de mémoire existante reste appliquée lors du choix du modèle.

Sources vérifiées : [tarifs Claude](https://claude.com/pricing#api), [paiement de l’API Claude](https://support.claude.com/en/articles/8977456-how-do-i-pay-for-my-claude-api-usage), [téléchargement Ollama](https://ollama.com/download), [Qwen 3.5 4b](https://ollama.com/library/qwen3.5:4b).

Tests : le dernier groupe de 8 fichiers Vitest compte 74 réussites, dont 71 pour ce point et 3 pour les liens et le dépliage Sécurité. Il inclut le guide de connexion, la sélection locale, la vérification de clé, les paramètres et le catalogue. Après ajout de l’assertion d’intégration « aide locale accessible malgré la carte grisée, Opus conservé », le fichier de sélection locale a été rejoué : 4 réussites. Son assertion de visibilité attend désormais la fin de l’animation d’entrée du composant.

Pas d’achat de crédits, de création de compte, de clé réelle, d’installation d’Ollama ni de téléchargement de modèle. Les étapes décrites sont documentées ; une première réponse réelle reste à jouer pendant la recette utilisateur.

## 5. Dépliage Sécurité

Le composant réel a été testé dans une zone défilante, avec Chromium sous Linux, aux tailles 1100 × 640 et 1100 × 800. Avant correction, le dernier risque dépassait de 52 pixels après animation dans les deux cas. Le défilement est maintenant ajusté à la fin de l’animation, seulement si ce risque est encore ouvert.

Après correction : 3 scénarios Chromium réussis, soit les deux hauteurs et l’aide PDF ; 2 tests unitaires B-1344 et 1 test du lien B-1349 réussis. Les scénarios de rendu utilisent un serveur Vite dédié au port 14383 et n’appellent aucun moteur réel. Aucun E2E complet lancé.

## Vérifications et questions restantes

Toutes les commandes lourdes ont été lancées avec `nice -n 10`, Vitest et Playwright avec un seul worker, Cargo avec un seul job. Les tests se limitent aux fichiers concernés. Les étapes finales sont vertes ; les échecs intermédiaires et leurs causes sont indiqués ci-dessus.

Commandes de recette reproductibles :

- Moteur : `nice -n 10 .venv/bin/pytest <fichiers cités> -q`. Pour obtenir le résumé malgré le hook local `os._exit` de `tests/conftest.py`, les dernières exécutions utilisaient une couverture ciblée avec `--cov=app.services.reprise_auto`, `--cov=app.services.llm` ou `--cov=app.services.invoice_pdf`, et `--cov-report=`.
- Interface : `nice -n 10 npm --prefix src/frontend test -- --maxWorkers=1 <fichiers cités>`.
- Rendu : `nice -n 10 npx playwright test --config tests/rendering/playwright.c22a.config.ts` : 3 réussites.
- TypeScript : `tsc --noEmit -p src/frontend/tsconfig.json` : réussi.
- Ruff sur les fichiers Python modifiés et ESLint sur les nouveaux composants/helpers : réussis. `git diff --check` : réussi.

Points à reprendre à l’intégration :

1. Le numéro global de l’application est encore 0.81.1 dans cette branche ; le guide embarqué est bien celui de la 0.82 demandée. La montée de version globale reste à faire pour la livraison 0.82.
2. Le guide fourni contient encore, au chapitre 4, l’affirmation que la clé enregistrée n’est pas testée. B-1348 a depuis ajouté cette vérification. Le PDF a été embarqué tel que demandé, sans réécriture du document public ; cette phrase est à synchroniser dans sa source avant livraison.
3. Mac, Windows, lecteurs PDF natifs et vrais fournisseurs restent à recetter. Les portes complètes pytest, Vitest et E2E restent à Syn, conformément à la consigne.
