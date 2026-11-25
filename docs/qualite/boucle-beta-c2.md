# Boucle bêta, cycle 2

La seconde session a audité les 14 commits du cycle 1 depuis `fed73a97b`. Ses notes de première lecture du diff précèdent l'ouverture du rendu, des preuves et des corps de commit. Elle a ensuite rejoué les gardes dans une copie de travail. La candidate porte le numéro 0.85.0.

## Correctifs et preuves

| Défaut | Correction | Test de régression |
|---|---|---|
| `bc2-B-020` | Conserver l'effort enregistré quand l'utilisateur passe par GPT-6.2, qui choisit son propre niveau sur la requête. | L'aller-retour du sélecteur dans `SettingsModal.da.test.tsx` fait réapparaître Très élevé sur GPT-6.1. |
| `bc2-B-021` | Envoyer la limite Qwen4-Max via `max_completion_tokens`, plafonnée à 262 144 en réflexion. | Le corps simulé dans `tests/test_modeles_catalogue.py` exige le champ et la valeur. [Qwen4-Max](https://www.alibabacloud.com/help/en/model-studio/qwen4-max) |
| `bc2-B-022` | Partager un arrêt jusqu'à la terminaison du processus et des lecteurs, puis démarrer le processus suivant. | `test_b1825_mcp_echec_initialisation.py` observe deux arrêts et un démarrage entrelacés. |
| `bc2-B-023` | Conserver les données légales hors formulaire. Une lecture HTTP échouée laisse la saisie disponible et bloque l'écriture jusqu'à une relecture. | `ProfileStep.recharge.b1840.test.tsx` couvre les champs absents de l'écran et la reprise après échec. |
| `bc2-B-025` | Garder l'affichage bêta en attente, en erreur et après l'abandon du moteur. | `SplashScreen.b1262.test.tsx` échoue trois fois sous le suffixe Alpha. Les 47 cas antérieurs restaient verts. |
| `bc2-B-026` | Traduire Très élevé en `high` chez DeepSeek, conformément au contrat du service. | `tests/test_modeles_catalogue.py` vérifie les deux modèles courants et l'ancien identifiant Flash. [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/) |
| `B-2069` | Attendre la prise en charge du flux Board avant son écriture protégée. | `test_board_traitement.py` suspend la liaison du suivi et vérifie le premier événement, puis la sauvegarde et la clôture. |
| `bc2-B-030` | Donner au lien public du guide un libellé lisible en bêta en conservant sa cible. | Le contrôle de documentation rougit quand le nom historique redevient visible et vérifie les deux liens après restauration. |

Les sabotages du cycle 2 ont été réalisés dans une copie sans dépôt Git et consignés dans le registre. Des matrices indépendantes couvrent 10 à 15 combinaisons par correctif. Les tests hérités ont également rougi sous les retraits ciblés du catalogue, de Synthetic, de la phase À propos, des versions et du badge, des défauts B-2065 à B-2068 et de l'effort Auto de GPT-6.2. Le démarrage était l'angle mort de la garde héritée de phase.

Les deux schémas et le frontend acceptent Synthetic. La route de configuration reçoit une clé fictive, relit la préférence, affiche la liste et parcourt le chat et le retour d'outil avec un transport HTTP simulé. Un accord portant sur un autre fournisseur ne permet pas le transfert. La politique affichée reste attribuée à Synthetic. [Politique de confidentialité](https://synthetic.new/policies/privacy)

Le contrôle À propos a passé les cinq couples demandés et dix nouveaux couples avec suffixes, métadonnées et entrées illisibles. Le point de mise à jour Tauri conserve son adresse historique. Les quatre verrous et la version restent identiques au cycle 1. Clippy, la compilation Tauri, les installs natives et leurs signatures sont hors banc Linux.

## Carte, Board et ronde

La carte bornée compte 165 fichiers sur 165 et 74 rapports valides. Les 19 doubles lectures manquantes ont été complétées et le contrôle des ancres ne signale aucune preuve invalide. Trois couples d'invariants complémentaires attendent un arbitrage humain. Neuf fichiers ont une preuve actualisée en plus des lectures antérieures conservées pour l'historique.

P24 a passé 46 réexécutions sur 50 avant correction et 50 sur 50 après, avec quatre processus `nice`, les mêmes cœurs et les délais du test d'origine. Avant, les quatre échecs ont atteint 5,443 à 5,582 secondes. Après, les mesures JUnit vont de 0,226 à 0,329 seconde et la médiane est 0,300 seconde. Dix combinaisons inédites entre le début du suivi, la liaison de l'adaptateur et de nouvelles questions passent après la réparation.

La porte complète locale est verte sur `278fec740` et de nouveau sur `1e92f63c3` après le libellé du README. Sur cette dernière tête, Pytest compte 7 361 cas, l’autonome 187, Vitest 4 380 et Playwright 112. Aucun échec ni rejeu Playwright instable. Les 15 sauts Pytest et les 4 sauts autonomes sont hérités. Les trois personas rejoués sur des données jetables vérifient 38 étapes dans la pile navigateur. À l’amorçage, trois requêtes aux accords ont été annulées, puis le même point d’accès a rendu 200 sur les trois profils. Les captures À propos affichent la version 0.85.0 et la phase Bêta.

Le plateau formel reste à 0/2. Le registre refuse les sauts hérités et les trois invariants en attente d’arbitrage. La transition vers la préparation locale a été forcée avec une note au registre, conformément au périmètre demandé.

## Reports

`bc2-B-027` a été reproduit sur deux appels publics de chat, avec un fournisseur simulé qui applique le contrat DeepSeek. La seconde question avec outils reçoit une erreur 400 parce que le message assistant de la première réponse est fourni avec `content` et `role` seuls. Le cycle 1 avait couvert le rejeu pendant la même exécution d'un outil. Le défaut de conservation entre messages concerne le stockage d'historique hérité et demande une conception qui précise le traitement du raisonnement fournisseur. [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)

Les écarts hérités de concurrence du circuit de reprise (`bc2-B-024`), de lecture du profil (`bc2-B-029`, constat statique) et de vocabulaire dans le guide de démarrage des testeurs (`bc2-B-028`) sont consignés pour la suite. Les quatre préférences éprouvées sous rotation de catalogue sont conservées par la route, qui réinsère l'identifiant actif.

La porte de la candidate et les traces sont indexées dans `RENDU-C2.md` à la racine du dossier de travail du 25 novembre.
