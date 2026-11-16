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
