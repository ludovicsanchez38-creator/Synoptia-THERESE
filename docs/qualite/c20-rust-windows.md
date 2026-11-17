# Cycle 20 : lot rust-windows

Périmètre : arbre `gpt/c20-rust-windows`. Aucun commit ni push : l'orchestrateur rejouera les tests rouges sur la base, puis créera les commits. Les tests Windows exécutent le bloc Rust de production dans un harnais de commandes simulées, sur ce Mac ; ils ne remplacent pas un essai sur Windows.

Écart à la consigne : `.app-loop` était absent au contrôle effectué en début de suites et présent après leur exécution. La suite backend comprend des tests du cycle 15, notamment dans `tests/test_c15_emission_concurrente.py`, qui créent et écrivent leurs preuves sous `.app-loop/cycles/15/reprise/lot-c`. Je n'ai pas inspecté ni déplacé ce répertoire après ce constat.

| ID | Verdict | Test (chemin::nom) | Rouge observé | Correctif |
| --- | --- | --- | --- | --- |
| B-1835 | confirme | `tests/test_c20_windows_zombies.py::test_b1835_wmic_vide_ne_tue_pas_un_backend_non_identifie` | `AssertionError: assert ['414'] == []` | non commité |
| B-1836 | confirme | `tests/test_c20_windows_zombies.py::test_b1836_seul_le_port_exact_designe_un_moteur` | `AssertionError: assert ['4242'] == []` | non commité |
| B-1912 | confirme | `src/frontend/src/components/SplashScreen.relanceDemarrage.b1912.test.tsx::B-1912 : reprise après une erreur de démarrage` | `TestingLibraryElementError: Unable to find an accessible element with the role "button" and name "Relancer le moteur local"` | non commité |
| B-1913 | confirme | `src/frontend/src/components/board/BoardPanel.interactionsHistorique.b1913.test.tsx::B-1913 : la décision et ses commandes de suppression sont des interactions distinctes` | `Error: expect(element).not.toContainElement(element)` | non commité |
| B-1914 | confirme | `src/frontend/src/components/board/BoardPanel.visibiliteSuppression.b1914.test.tsx::B-1914 : la suppression est visible sans survol et identifie la décision` | `AssertionError: expected +0 to be 1` | non commité |
| B-1915 | confirme | `src/frontend/src/App.lienEvitement.b1915.test.tsx::B-1915 : le lien focalisé est au-dessus du chrome avec le CSS produit par Tailwind` | `AssertionError: expected 0 to be greater than or equal to 50` | non commité |
| B-1916 | rejete : doublon déjà corrigé | Tests de B-1913 et B-1914 ci-dessus | Sans nouvel essai rouge : ces deux tests ont reproduit ses défauts avant leurs correctifs | Sans objet |

Le `title` initial de B-1914 constituait déjà un nom accessible : la partie « pas de nom accessible » est donc rejetée. L'invisibilité sans survol est confirmée. L'action a reçu un nom explicite et une indication sur la décision visée.

Chemins de production vérifiés avant correction : `main.tsx` monte `App`, qui charge `SplashScreen` au démarrage ; `PanelContainer.tsx` charge `BoardPanel` ; la fonction Rust de démarrage release `spawn_backend_sidecar` appelle `kill_zombie_backends`.

Quand WMIC est absent, `tasklist` ne fournit que des candidats : leur ligne de commande est vérifiée par CIM avant tout arrêt. Si cette vérification échoue, aucun PID non identifié n'est arrêté. Le filtre WMIC est également contrôlé à partir de la ligne de commande et du port exact, avec prise en charge des chemins entre guillemets et des sorties UTF-16LE. Le test existant `tests/test_sentinelles_structure.py::TestCoqueRust::test_le_repli_tasklist_vient_apres_wmic` est conservé, sans affaiblissement. Le nouveau témoin vérifie aussi qu'un moteur identifié reste nettoyé sans WMIC : le retrait initial du repli a produit `AssertionError: assert [] == ['4242']` avant rétablissement sécurisé.

Le test de B-1912 vérifie également qu'une nouvelle erreur survenue pendant la relance reste affichée : avant le correctif complémentaire, il échouait avec `TestingLibraryElementError: Unable to find an accessible element with the role "alert"`.

## Remédiation de la relecture, passe 1

Les résultats ci-dessous concernent la remédiation ; les portes qui suivent décrivent l'état de la première passe.

1. **Nettoyage Windows Python.** `tests/test_c20_windows_zombies.py::test_les_deux_nettoyages_epargnent_un_backend_tiers` a d'abord échoué avec `AssertionError: assert ['414'] == []` : le processus tiers épargné par Rust était arrêté par Python. Python utilise désormais `tasklist` pour les candidats et vérifie chaque ligne de commande par CIM, avec le port exact, avant `taskkill`. Les tests couvrent aussi un vrai moteur simulé, les PID courant et parent, un port préfixe, l'indisponibilité ou l'échec de CIM et la poursuite après un candidat en échec.
2. **Ancienne relance automatique.** `tests/test_c20_relance_sidecar.py::test_ancienne_relance_automatique_ne_remplace_pas_la_reprise_manuelle` a d'abord échoué avec `AssertionError: assert ['2', '3'] == ['1', '2']`. Une génération invalide les anciens délais ; un verrou sérialise leur lancement avec la relance manuelle. Le test couvre aussi une terminaison tardive, une nouvelle relance automatique valable et une relance manuelle demandée pendant un lancement automatique déjà engagé.
3. **Double clic sur la relance.** `SplashScreen.relanceDemarrage.b1912.test.tsx`, test « ignore un double clic », a d'abord échoué avec `Error: expect(element).toBeDisabled()`. Un verrou immédiat empêche les appels simultanés ; le bouton est désactivé pendant la commande et redevient utilisable après son échec.

Vérifications de cette passe :

- `tests/test_c20_windows_zombies.py`, `tests/test_c20_relance_sidecar.py` et tests voisins du démarrage et de la coque : **62 réussis, 0 échec, 0 erreur, 0 ignoré**, décomptés dans `/tmp/rust-windows-r1.xml`.
- `ruff check --no-fix src/backend tests` : **0 erreur**.
- Quatre fichiers Vitest autour de `SplashScreen` : **43 tests réussis, 0 échec** ; `npx tsc --noEmit` : **0 erreur** ; `npm run lint` : **0 erreur, 27 avertissements hors fichiers modifiés**.

Les commandes Windows, processus et réponses réseau des scénarios sont simulés. Le harnais compile et exécute les blocs Rust concernés sur macOS, y compris la contrainte `Send` du traitement asynchrone ; il ne remplace ni une compilation Windows ni une recette sur cette plateforme. La suite complète n'a pas été relancée.

## Remédiation de la relecture, passe 2

Les deux constats sont confirmés. Les modifications restent non commitées pour permettre le rejeu des tests sans les correctifs.

| Constat | Test isolé avant correction | Ligne d'échec observée | Correctif et couverture |
| --- | --- | --- | --- |
| 1. Options ambiguës | `tests/test_c20_windows_zombies.py::test_les_nettoyages_refusent_les_options_ambigues[rust_wmic-port_repete]` | `AssertionError: assert ['4242'] == []` | Les nettoyages Python et Rust n'acceptent que les deux couples d'arguments émis par le lanceur. Les ports et hôtes répétés, ainsi que les formes `--port=...` et `--por ...` supplémentaires, sont refusés pour WMIC, CIM et Python. |
| 2. Ancienne erreur de relance | `SplashScreen.relanceDemarrage.b1912.test.tsx`, test « reprend après une erreur de l’ancienne génération reçue pendant la relance » | `AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times` | La commande et les événements Rust portent leur génération. Le splash ignore les événements plus anciens tout en conservant les échecs de la nouvelle tentative, avant ou après le retour de la commande. |

Le refus des options supplémentaires est volontairement prudent : même une option additionnelle bénigne empêche l'identification et donc l'arrêt automatique de ce processus. Le prédicat Rust est aussi appelé sur Unix ; les deux tests Rust existants B-1261 ont été exécutés avec le prédicat de production extrait. Le test de génération exécute les émetteurs, la commande et l'ordonnancement Rust de production dans un harnais de fenêtre et de sidecar simulés. Le double clic et les erreurs sans génération restent couverts par les tests préexistants.

Pour rejouer les deux rouges isolément :

```sh
OLLAMA_BASE_URL=http://127.0.0.1:9 THERESE_DATA_DIR=/tmp/rust-windows-r2-profil-fictif PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest 'tests/test_c20_windows_zombies.py::test_les_nettoyages_refusent_les_options_ambigues[rust_wmic-port_repete]' -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/rust-windows-r2-rouge1.xml
cd src/frontend
VITE_THERESE_BACKEND_PORT=9 npm_config_offline=true npx --no-install vitest run src/components/SplashScreen.relanceDemarrage.b1912.test.tsx -t 'reprend après une erreur de l’ancienne génération' --configLoader runner --maxWorkers=1
```

Portes de cette passe, sans suite complète :

- Pytest et harnais Rust : **46 réussis, 0 échec, 0 erreur, 0 ignoré**, après lecture de `/tmp/rust-windows-r2.xml` ; le compte inclut l'exécution des deux tests Rust B-1261 dans un cas pytest.
- Ruff sur `src/backend tests` : **0 erreur**.
- Frontend : **74 tests réussis dans 7 fichiers** autour du splash, de la reprise, du bandeau et de l'installation ; TypeScript : **0 erreur** ; ESLint : **0 erreur, 27 avertissements hors fichiers modifiés**.

Les commandes Windows, les événements, le sidecar et les réponses aux sondes frontend étaient simulés. Les harnais Rust ont été compilés sur macOS : aucune compilation Windows ni recette sur cette plateforme n'a été effectuée.

## Remédiation de la relecture, passe 3

Les deux réserves de la relecture sur les chemins contenant `--` et le délai CIM sont acceptées par l'orchestrateur et restent hors de cette passe. Seul le harnais du test de génération est modifié ; le code de production et les assertions existantes sont inchangés.

Le test `tests/test_c20_relance_sidecar.py::test_generations_des_evenements_et_de_la_commande` a d'abord été lancé seul sur Linux et a échoué à la compilation avec ``AssertionError: error[E0599]: no method named `path` found for reference `&AppHandle` in the current scope``. Après extension du test aux trois configurations simulées, le cas `linux` a reproduit la même ligne d'échec. Le faux `AppHandle` fournit maintenant le résolveur de ressources demandé par la branche Linux et la fausse commande accepte une valeur d'environnement `String`. Les branches `cfg(target_os)` de l'extrait sont sélectionnées dans le harnais pour exécuter les scénarios Linux, macOS et Windows sur le même banc ; l'extrait actuel ne contient pas de branche propre à Windows. Les trois cas conservent les assertions sur les événements et les générations.

L'autre test de relance extrait les fonctions de relance et de terminaison sans branche `target_os`. Le harnais de nettoyage Windows extrait déjà son bloc simulé indépendamment du système, et les tests qui lisent `lib.rs` ont aussi été vérifiés. Ces simulations ont été compilées et exécutées avec `rustc` sous Linux ; elles ne constituent pas une compilation ni une recette natives sur macOS ou Windows.

Portes de cette passe, sans suite complète :

- Test de génération étendu : **3 réussis, 0 échec, 0 erreur, 0 ignoré**, après lecture de `/tmp/rust-windows-r3-cible.xml`.
- Cinq fichiers de tests autour des harnais, de la coque et du sidecar : **58 réussis, 0 échec, 0 erreur, 0 ignoré**, après lecture de `/tmp/rust-windows-r3-rust.xml`.
- Porte élargie aux tests de démarrage : **73 réussis, 0 échec, 1 erreur, 0 ignoré**, après lecture de `/tmp/rust-windows-r3.xml`. `tests/test_main_startup.py::TestStartupKeychainSafety::test_startup_profile_preload_skips_decrypt` expire à 120 s dans la fixture `db_session`. Relancé seul avec un profil neuf, puis avec une base neuve en clair, il expire aussi. Une sonde Python indépendante de l'application reproduit le blocage : un `Future` résolu par `call_soon_threadsafe` depuis un thread différé expire. En mode debug, `asyncio` signale `PermissionError: [Errno 1] Operation not permitted` lors de l'écriture dans son socket interne de réveil. La porte élargie reste donc rouge dans cet environnement.
- `ruff check --no-fix src/backend tests` : **0 erreur**. Aucun fichier frontend n'a été modifié.

## Portes

- Frontend, `npm run test -- --run --configLoader runner` : **967 fichiers, 4 107 tests réussis, 0 échec**. Le chargeur `runner` évite une écriture dans `node_modules`, qui est un lien vers le dépôt principal. La commande sans cette option échoue avant les tests avec `EPERM` sur `.vite-temp`.
- Frontend, `npx tsc --noEmit` : réussi, 0 erreur.
- Frontend, `npm run lint` : réussi, 0 erreur.
- Backend, `ruff check --no-fix src/backend tests` : réussi, 0 erreur.
- Rust, deux tests B-1261 existants compilés avec le prédicat de production extrait de `lib.rs` : **2 réussis, 0 échec**. Ce contrôle local ne compile pas la cible Windows.
- Backend, commande pytest demandée : **6 755 réussis, 15 échoués, 51 ignorés, 0 erreur**, sur 6 821 cas. Le XML lu est `/tmp/rust-windows-pytest.xml`. Cinq échecs correspondent à la référence fournie, dix autres restent hors référence.

Les cinq échecs de référence sont :

- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[True-True]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[True-False]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[False-True]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[False-False]`
- `tests/test_securite_f2_recette_deb.py::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document`

Les dix autres échecs sont :

- `tests/test_b1153_bac_a_sable_commandes.py::test_le_cas_de_l_audit_ne_vide_plus_un_dossier_hors_du_depot`
- `tests/test_b1153_bac_a_sable_commandes.py::test_le_code_de_l_agent_n_ecrit_ni_dans_le_dossier_personnel_ni_dans_tmp`
- `tests/test_b1153_bac_a_sable_commandes.py::test_le_depot_et_le_dossier_temporaire_restent_ecrivables`
- `tests/test_b1153_bac_a_sable_commandes.py::test_l_environnement_du_moteur_ne_passe_pas`
- `tests/test_b1153_bac_a_sable_commandes.py::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[False]`
- `tests/test_b1153_bac_a_sable_commandes.py::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[True]`
- `tests/test_b1153_bac_a_sable_commandes.py::test_aucune_connexion_locale_pas_meme_vers_un_port_ouvert`
- `tests/test_b1153_bac_a_sable_commandes.py::test_un_processus_exterieur_ne_recoit_aucun_signal`
- `tests/test_b1191_commande_introuvable_nommee.py::test_pytest_absent_du_path_n_est_pas_un_confinement_en_panne`
- `tests/test_b1191_commande_introuvable_nommee.py::test_temoin_commande_presente_s_execute_confinee`

Neuf de ces dix cas nécessitent d'exécuter des commandes dans un confinement imbriqué. Leur sonde échoue ici : une exécution directe de `sandbox-exec` avec un profil minimal retourne `sandbox_apply: Operation not permitted` (code 71). Le dixième, `test_aucune_connexion_locale_pas_meme_vers_un_port_ouvert`, échoue dès `serveur.bind(...)` avec `PermissionError: [Errno 1] Operation not permitted`. Les deux tests représentatifs ont été relancés isolément et reproduisent l'échec. Les modules backend qu'ils exercent n'ont pas été modifiés dans ce lot ; ces dix échecs ne figurent pas dans la référence et empêchent de déclarer la porte backend verte dans cet environnement.
