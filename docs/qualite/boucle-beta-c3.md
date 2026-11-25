# Boucle bêta, cycle 3

La candidate reste en 0.85.0. Le cycle 3 a relu les changements de `bf636e65e` à `51e4908f0` avant de confronter ses constats aux conclusions du cycle 2. Les huit contrôles ciblés ont rougi au retrait. Le libellé du README est vérifié par un oracle documentaire indépendant. Le test versionné MCP ne réagissait pas au retrait de la protection contre l’annulation. La garde ajoutée au cycle 3 détecte cet écart. Le test Board rougit aussi si la barrière de persistance est levée avant le premier événement du flux.

## Correctifs et essais

| Sujet | Comportement éprouvé | Preuve |
|---|---|---|
| `bc2-B-027` | Deux envois avec outils reproduisent un refus 400 sur la 0.84 publiée et sur le cycle 2, avec `deepseek-v4-pro`. Le chat préserve l’historique et les outils en demandant une réponse sans réflexion quand un ancien message ne porte pas de raisonnement rejouable. Un avis explique ce choix. | `test_deepseek_historique_outils.py`, les deux modèles testés jusqu’au retour d’outil. Le retrait rétablit les deux refus. Onze charges utiles supplémentaires. [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/) · [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/) |
| `bc2-B-024` | Le Board réserve un seul essai par fournisseur en récupération au départ d’une requête. L’annulation libère la place. | `test_board_sonde_circuit.py` suspend la première requête de deux délibérations préparées. Dix variantes vérifient les états du circuit. |
| `bc2-B-028` | Le guide d’installation nomme la bêta et conserve les trois formats et le lien de téléchargement. | Oracle Markdown et dix variantes. |
| `bc2-B-029` | Une lecture publique qui échoue rend 503. Le remplacement d’une fiche illisible est refusé. Une absence valide rend toujours 200 avec `null`. | `test_routers_config.py`, lignes contrôlées avant et après. Une base créée par `fed73a97b` est relue avec une empreinte, un identifiant et un horodatage de profil identiques. Onze variantes de lecture. |
| `bc3-B-031` | La requête d’arrêt MCP peut être annulée pendant que le processus finit. Le second appel constate la terminaison. | `test_b1825_mcp_echec_initialisation.py`, rouge au retrait de `shield`. |
| `bc3-B-032` à `bc3-B-035` | Six sauts levés. Les deux tests de sélection d’image passent par la route et le répartiteur réels, avec des adaptateurs simulés. Les sauvegardes autonomes éprouvent une archive chiffrée sur SQLite WAL. Les tarifs sont testés en USD. La personnalisation vérifie les valeurs par défaut et l’absence du réglage de langue retiré par BUG-164. | Rejeu des 19 cas historiques. Sabotages des deux sélections, de la phrase de chiffrement, de la devise et du champ retiré. |

Le repli DeepSeek ne demande aucun changement de stockage. La préférence d’effort sert encore aux requêtes qui permettent la réflexion. La conservation du raisonnement et du protocole complet des outils reste un choix de conception distinct, notamment pour l’exposition et la purge des nouvelles données. L’essai HTTP utilise uniquement un transport simulé.

## Ronde Linux et plateau

La ronde complète a porté sur `3fd71f6dd`. Le banc a rendu VERT à 04 h 13. Le JUnit principal compte 7 370 cas et 13 sauts. Les suites autonome, Vitest et Playwright desktop comptent respectivement 187, 4 380 et 112 cas, sans saut. Aucun JUnit ne signale d’échec et Playwright ne signale aucun rejeu instable. Mypy compte les 922 diagnostics du cliquet.

Les onze tests Seatbelt ont été collectés sur Linux et sont réservés à macOS. Le test réseau du manifeste est passé sur le point public historique, HTTP 200, version 0.84.0 et six plateformes. La contre-épreuve PyInstaller est passée dans son cadre dédié, avec le délai de la CI. Le plateau reste à 0/2 avec les sauts maintenus, trois arbitrages d’invariants et les exigences de rondes indépendantes. Les instruments du cycle 3 ne portent pas d’étalonnage formel dans le registre.

La boucle entre dans la préparation locale de la candidate par transition documentée. Les preuves et l’arbitrage accompagnent le bundle sous `c3/`. Le résultat de la porte de release sur le commit de rapport figure dans le rendu de ce même banc. Clippy, le build Tauri, les essais natifs Windows et macOS, la mise à jour native et les signatures sont hors du banc Linux.
