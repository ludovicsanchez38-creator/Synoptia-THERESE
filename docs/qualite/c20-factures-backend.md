# Cycle 20 : factures et backend

Branche `gpt/c20-factures-backend`, sans commit ni push : l'index Git n'est pas accessible dans ce bac à sable. Chaque ligne rouge ci-dessous provient d'un lancement isolé avant correction ; l'orchestrateur pourra rejouer les tests sur la base avant d'enregistrer les lots.

| ID | Verdict | Test de comportement | Rouge observé avant correction | Correctif |
| --- | --- | --- | --- | --- |
| B-1859 | confirme | `tests/test_b1859_snapshot_migration.py::test_migration_partielle_preserve_les_snapshots_existants` | `At index 0 diff: 'Nouveau Nom' != 'Ancien Nom'` | non commité |
| B-1860 | confirme | `tests/test_b1860_adresse_emission.py::test_refuse_emission_sans_adresse_sans_numero` | `assert 200 == 409` pour `[sent-facture]` ; 8 cas rouges | non commité |
| B-1861 | confirme | `tests/test_b1861_pdf_emis.py::test_pdf_emis_deja_genere_ne_change_pas_apres_modification_du_profil` | `At index 993 diff: b'4' != b'2'` | non commité |
| B-1862 | confirme | `tests/test_b1862_penalites_conversion.py::test_conversion_utilise_la_meme_penalite_par_defaut_que_la_facture_directe` | `assert False` pour la présence de la même règle sur les deux PDF | non commité |
| B-1863 | confirme | `tests/test_b1863_stamp_incomplet.py::test_schema_incomplet_ne_saute_pas_les_migrations` | `AssertionError: assert 't4memoire03' == None` pour `[False]` | non commité |
| B-1973 | confirme | `tests/test_b1973_pied_pdf_lisible.py::test_pied_du_pdf_a_un_contraste_et_un_corps_lisibles` | `AssertionError: Contraste du pied : 2.54:1` | non commité |
| B-1974 | confirme | `tests/test_b1974_regime_tva.py::test_sans_tva_le_regime_normal_ne_devient_pas_une_franchise` | `AssertionError: assert '293 B' not in 'Claire Exem... des impôts.'` | non commité |
| B-1975 | confirme | `tests/test_b1975_messages_factures.py::test_messages_visibles_de_facturation_sont_en_francais` | `[absente]` : `assert 'Pièce introuvable.' in '{"code":"HTTP_ERROR","message":"Invoice not found"}'` ; 3 cas rouges | non commité |
| B-1976 | confirme | `tests/test_b1976_budget_devise.py::test_les_reponses_de_budget_precisent_la_devise` | `KeyError: 'currency'` pour `[limits]` ; 3 cas rouges | non commité |

## Précisions et limites

Aucun candidat n'est classé `regle_a_trancher`.

- B-1859 : la migration appelée par `apply_adhoc_migrations`, elle-même appelée par `init_db`, préserve les colonnes déjà figées, y compris leurs valeurs vides. Les colonnes absentes restent reconstruites à partir du contact courant quand il existe ; elles ne prouvent donc pas une valeur historique.
- B-1860 : les deux routes de première émission contrôlent l'adresse avant l'attribution d'un numéro ; une adresse peut être fournie dans la même requête de mise à jour. Les pièces déjà émises ne sont pas réécrites. Les scénarios préexistants d'émission reçoivent une adresse fictive ; le test C22b qui émettait volontairement sans adresse crée désormais directement une pièce historique pour conserver le contrôle du message de réparation.
- B-1861 : le PDF existant d'une pièce émise est réutilisé et sa première création est publiée sans écrasement. Un deuxième test rouge (`tests/test_b1861_pdf_emis.py::test_brouillon_ancien_ne_fait_pas_passer_son_pdf_pour_la_piece_emise`, `assert 200 == 409`) a montré qu'un brouillon historique déjà numéroté pouvait laisser un aperçu sous le numéro définitif : l'émission est maintenant refusée tant que ce fichier n'a pas été déplacé. Le fichier d'origine n'est pas retrouvé si son dossier change ou s'il est supprimé ; l'identité de l'émetteur à l'émission n'est pas conservée séparément. La publication utilise un lien physique et exige un système de fichiers qui le permet.
- B-1862 : la règle par défaut suit celle documentée pour B-1338 dans `docs/releases/v0.81.1-alpha.md`. Un second test rouge (`tests/test_b1862_penalites_conversion.py::test_pdf_sans_mentions_conserve_le_taux_particulier_enregistre`) a montré qu'un taux particulier enregistré était ignoré si les mentions étaient vides ; le PDF reprend maintenant ce taux. Les mentions et taux particuliers déjà enregistrés restent inchangés. Aucune vérification juridique en ligne n'a été effectuée dans ce lot. Les tests B-1357 vérifient toujours la typographie d'un taux particulier fourni explicitement ; B-1760 vérifie la nouvelle règle par défaut et ses autres assertions de conservation restent actives.
  Rouge exact du cas supplémentaire B-1862 : `assert '11,62 %' in "SIRET 12345678900010\nDocument généré par THÉRÈSE - 16/11/2026\nPage 1\nFACTURE\nN° Brouillon, numéro à l'émission\nÉ...vrement : 40 €.\nEscompte pour paiement anticipé : néant.\nMentions légales : TVA incluse selon les taux en vigueur.\n"`.
- B-1863 : une base sans estampille est désormais soumise à la même preuve de schéma qu'une base suivie. La sous-assertion signalée pour `activities.contact_id` était déjà couverte par la comparaison des colonnes au modèle ; `test_colonne_contact_absente_des_activites_bloque_le_reestampillage` le confirme. Les anciens tests d'estampille directe ont été adaptés : un schéma incomplet est refusé, le test chiffré utilise un schéma complet.
- B-1973 : mesure issue des opérateurs du PDF généré et référence de contraste de `docs/stories/US-700-navigation-ux.md` ; rendu de la page inspecté avec le moteur Apple. Pas de contrôle sur papier physique.
- B-1974 : le test P-119 qui assimilait une absence de régime déclaré à la franchise vérifie désormais une mention neutre et l'absence de référence 293 B. La franchise et l'exonération déclarées gardent leurs tests.
- B-1975 : le test de suppression vérifie désormais le message français exact, au lieu d'exiger les mots anglais de l'ancien comportement.
- B-1976 : les clés historiques en `eur` restent disponibles en lecture et en écriture pour compatibilité. Les réponses exposent `currency: USD` et des alias en `usd` ; le renommage complet du contrat et des données persistées reste une dette.
- Les preuves des tests de concurrence cycle 15 sont écrites dans `tmp_path`, afin de ne pas toucher à `.app-loop/`. Aucun test n'a été supprimé ni rendu moins exigeant pour cette isolation.

## Remédiation de la relecture, passe 1

Chaque rouge ci-dessous a été obtenu en lançant seul le cas indiqué, avant son correctif. Les fichiers de tests voisins ont été relancés après chaque correction.

1. **Origine du PDF.** `tests/test_b1861_pdf_emis.py::test_pdf_historique_non_atteste_est_refuse_sans_modifier_le_fichier` : `E   assert 200 == 409`. Une archive est maintenant liée à l'identifiant, au numéro, à la date et au type de la pièce, ainsi qu'à l'empreinte du PDF. Un fichier historique sans preuve, ou un PDF modifié, est refusé en génération et à l'ouverture sans être écrasé. Une collision lors de la publication n'est pas certifiée.
2. **Statut du PDF.** `tests/test_b1861_pdf_emis.py::test_pdf_actualise_le_statut_sans_reecrire_l_original[paiement-Pay\xe9e]` : `E       AssertionError: assert 'Payée' in 'SIRET 12345678900010\nDocument généré par THÉRÈSE - 16/11/2026\nPage 1\nFACTURE\nN° FACT-2026-001\nÉMETTEUR\nDESTINAT...vrement : 40 €.\nEscompte pour paiement anticipé : néant.\nMentions légales : TVA incluse selon les taux en vigueur.\n'`. Pour un changement de statut ou le passage de l'échéance, une édition distincte reprend les données de l'archive et l'état courant ; l'original reste inchangé et la route d'ouverture choisit cette édition. Les deux transitions sont testées avec changement du profil entre les générations.
3. **Snapshot client.** `tests/test_b1859_snapshot_migration.py::test_chaque_colonne_absente_preserve_toutes_les_valeurs_existantes[client_name]` : `E     At index 1 diff: 'Société actuelle' != None`. Seules les colonnes ajoutées sont remplies. Les cinq colonnes manquantes sont testées séparément, avec conservation des `NULL`, des chaînes vides et des autres valeurs existantes, puis nouvelle exécution de la migration.
4. **Estampillage.** `tests/test_b1863_stamp_incomplet.py::test_factures_au_schema_incomplet_ne_peuvent_pas_etre_estampillees[tva_applicable-True]` : `E   AssertionError: assert 't4memoire03' == 'c3d4e5f6a7b8'`. L'estampillage exige toutes les colonnes du modèle `Invoice`. Sept colonnes absentes sont testées sur des bases suivies et non suivies ; le témoin positif est construit depuis les modèles réels.

Un test supplémentaire a révélé une régression dans la première remédiation : `tests/test_b1861_pdf_emis.py::test_donnees_archive_alterees_ne_produisent_pas_une_nouvelle_identite` échouait avec `E   assert 200 == 409`. Les données nécessaires à une édition sont maintenant liées au PDF original par une empreinte inscrite dans ses métadonnées ; leur altération est refusée. Les tests voisins relancés après cette correction comptent **56 réussis, 0 échoué, 0 ignoré**.

Le fichier compagnon `.pdf.therese.json`, créé avec les permissions `0600`, contient les données de la pièce et du profil nécessaires aux éditions. Il doit être conservé et déplacé avec le PDF. Les empreintes contrôlent leur cohérence locale ; elles ne constituent pas une signature électronique. Un PDF historique déjà présent sans fichier compagnon est refusé, même s'il s'agit du bon document. Une première génération après émission utilise toujours le profil disponible à cette génération : l'identité de l'émetteur au moment exact de l'émission n'est pas enregistrée séparément. Si le dossier configuré change et que ni le PDF ni son compagnon ne s'y trouvent, cette première génération peut être refaite depuis le profil courant. Une base déjà estampillée à tort avant ce correctif n'est pas désestampillée automatiquement.

**Porte ciblée finale : 295 réussis, 0 échoué, 0 ignoré**, résultats lus dans `/tmp/factures-backend-r1.xml`. Ruff sur `src/backend tests` : **0 erreur**. Les données de test sont jetables et une garde interdit les connexions réseau ainsi que les chemins exclus. La suite complète n'a pas été lancée et aucun changement n'a été commité.

## Remédiation de la relecture, passe 2

Chaque constat a d'abord été reproduit par un test lancé seul ; les lignes ci-dessous sont recopiées de ses résultats avant correction.

1. **Collision entre profils.** `tests/test_b1861_pdf_emis.py::test_brouillons_historiques_isoles_preservent_archive_partagee` : `E   AssertionError: Archive émise modifiée par un brouillon`. Chaque aperçu reçoit un nom propre à l'identifiant et au numéro de la pièce ainsi qu'à sa génération, et sa publication ne remplace aucun fichier. L'ouverture retrouve l'aperçu de la pièce ; sa suppression ne cible pas l'archive d'un autre profil. Le test vérifie deux brouillons de même numéro, la régénération, la suppression d'un devis et l'intégrité du PDF et du compagnon émis.
2. **Compagnon interrompu.** `tests/test_b1861_pdf_emis.py::test_preuve_intermittente_ne_bloque_pas_la_reprise_du_pdf` : `E   assert 409 == 200`. Le PDF et son compagnon sont préparés et vérifiés avant la publication. Si l'interruption survient entre la publication du PDF et celle du compagnon, une génération ou une ouverture ultérieure finalise la paire seulement si le PDF publié est le même fichier que le PDF provisoire vérifié. La reprise couvre l'archive et ses éditions ; une preuve altérée ou un fichier étranger est refusé, même si ses octets sont identiques.

La vérification des appelants a fait apparaître trois régressions introduites pendant cette passe, chacune reproduite isolément avant sa correction :

- `test_changement_du_pdf_pendant_la_finalisation_ne_la_certifie_pas[deplacement]` : `E   assert 500 == 409`. Un PDF déplacé ou remplacé pendant la finalisation ne laisse pas de compagnon publié pour un autre fichier.
- `test_ouverture_retrouve_le_dernier_apercu_sur_un_disque_aux_dates_identiques` : `E   AssertionError: assert '/tmp/pytest-...fffffffff.pdf' == '/tmp/pytest-...000000000.pdf'`. L'ordre des générations est porté par les noms des aperçus et ne dépend pas de la précision des dates du système de fichiers.
- `tests/test_facture_pdf_ouverture.py::test_apercu_remplace_par_un_lien_apres_la_recherche_ne_sort_pas_du_dossier` : `E   Failed: DID NOT RAISE <class 'fastapi.exceptions.HTTPException'>`. L'ouverture revalide le chemin après la recherche pour refuser un lien sortant substitué entre-temps.

Les aperçus successifs sont conservés jusqu'à la suppression de leur pièce. Pour une pièce historique portant déjà son numéro définitif, les aperçus correspondants doivent être déplacés avant émission. Les anciens aperçus enregistrés sous le seul numéro ne sont plus résolus comme aperçus : il faut les régénérer ; les fichiers existants sont conservés. Les fichiers provisoires `.therese-publication-*` permettent une reprise après interruption et doivent rester avec le PDF tant que celle-ci n'a pas abouti ; un arrêt brutal avant publication peut laisser des fichiers provisoires orphelins. Comme en passe 1, la publication nécessite un système de fichiers acceptant les liens physiques.

Après le premier correctif, **75 tests voisins ont réussi** ; après le second, **84**. La porte ciblée finale compte **183 réussis, 0 échec, 0 erreur, 0 ignoré**, chiffres lus dans `/tmp/factures-backend-r2.xml`. Ruff sur `src/backend tests` : **0 erreur**. Une garde locale interdit les connexions et les chemins exclus ; un tube anonyme remplace le réveil par socketpair que ce bac à sable refuse. La suite complète et les portes frontend n'ont pas été lancées. Les changements restent non commités.

## Remédiation de la relecture, passe 3

Chaque constat a été reproduit par le test indiqué lancé seul avant correction ; les lignes d'échec sont recopiées ci-dessous.

1. **Reprise après sauvegarde et restauration.** `tests/test_b1861_pdf_emis.py::test_restauration_reprend_la_publication_interrompue[pdf-False]` : `E   AssertionError: Le PDF publié a disparu après restauration`. La restauration conserve le lien physique de publication si sa source provisoire, sa destination et un compagnon régulier unique sont dans le même dossier et que les chemins et noms attendus sont vérifiés. La reprise vérifie toujours la preuve du PDF avant de l'accepter. Le test effectue une interruption, une sauvegarde chiffrée et une restauration réelles, puis une reprise depuis la génération ou l'ouverture, sur l'archive et une édition, après changement de profil. Les tests d'extraction couvrent aussi les liens étrangers, les chemins vers un autre dossier, les sources dupliquées, les compagnons absents et la publication dont les deux liens sont présents dans l'archive. Les liens sans compagnon régulier admissible restent ignorés ; les dossiers de factures extérieurs aux éléments couverts par la sauvegarde ne sont pas inclus automatiquement.
2. **Compagnon seul avant émission.** `tests/test_b1861_pdf_emis.py::test_compagnon_sans_pdf_bloque_la_premiere_emission[fichier-envoi]` : `E   assert 200 == 409`. Les deux voies de première émission refusent un compagnon présent, y compris un lien cassé. Le brouillon et son numéro provisoire sont conservés ; après déplacement du compagnon, l'émission et la génération réussissent avec le numéro attendu. Les quatre combinaisons envoi/paiement et fichier/lien cassé sont testées.

La relecture de la première correction a révélé une régression lorsque l'arrêt survient pendant le nettoyage, après suppression du compagnon provisoire mais avant celle du PDF provisoire : `tests/test_b1497_extraction_sauvegarde.py::test_restauration_apres_nettoyage_interrompu_du_compagnon_provisoire` : `E   AssertionError: Le PDF publié a disparu pendant le nettoyage interrompu`. La restauration accepte aussi le compagnon final régulier dans ce cas. Les tests voisins comptaient **53 réussites** après le premier correctif et **85** après le second ; la porte finale couvre également la correction du nettoyage.

**Porte ciblée finale : 169 réussis, 0 échec, 0 erreur, 0 ignoré**, nombres lus dans `/tmp/factures-backend-r3.xml`. Ruff sur `src/backend tests` : **0 erreur**. Le lanceur temporaire interdit les connexions et les chemins exclus ; un tube anonyme réveille la boucle et la sortie forcée de pytest est neutralisée pour permettre l'écriture du bilan. La suite complète et les portes frontend n'ont pas été lancées. Les changements restent non commités.

## Portes

- **Backend, porte finale : 6 556 réussis, 14 échoués, 62 ignorés, 0 erreur de collecte**, sur 6 632 cas, XML `/tmp/factures-backend-pytest.xml`. La commande demandée a été exécutée avec une garde locale pour interdire les connexions et opérations hors périmètre. Onze cas ont été ignorés par cette garde : ils créent un dépôt Git, exécutent un ensemble contenant de telles créations, ou touchent le dossier personnel. Les 51 autres ignorés le sont par la suite elle-même. Il s'agit donc d'une porte partielle et non verte.
- Les **26 cas des nouveaux tests B-1859 à B-1976** sont tous passés dans cette porte, sans cas ignoré.
- **Échecs supplémentaires : 9** dans les tests de confinement B-1153/B-1191. La sonde du confinement échoue avec `PermissionError` et une ouverture de socket locale est refusée. Deux cas représentatifs ont aussi été rejoués sans la garde ajoutée et ont échoué de la même façon. Ce constat ne prouve pas leur état avant le lot.
- **Échecs de référence annoncés : 5** : les quatre cas R3.4 et la recette `.deb` ci-dessous.
- **Passe intermédiaire, avant le dernier correctif B-1862 : 6 555 réussis, 14 échoués, 62 ignorés**, sur 6 631 cas, XML `/tmp/factures-backend-pytest-avant-taux.xml`. Ses 14 échecs sont exactement ceux de la porte finale.
- **Première passe, avant correction de la garde : 6 540 réussis, 30 échoués, 61 ignorés, 0 erreur**, sur 6 631 cas, XML `/tmp/factures-backend-pytest-premier.xml`. Treize collectes enfant échouaient car la garde était introuvable dans leur sous-processus ; elles passent dans la porte finale. Le test qui exécute le dossier enfant est désormais ignoré car il créerait des dépôts Git. Deux autres échecs intermittents, sur les traitements et la restauration, passent seuls puis dans la porte finale.
- **Pénalités et tests voisins : 41 réussis, 0 échoué, 0 ignoré**, XML `/private/tmp/b1862-taux-vert.xml`.
- **Sous-ensemble facturation : 539 réussis, 0 échoué, 1 ignoré**, sur 540 cas, XML `/tmp/c20-facturation2.xml`.
- **Diagnostic de la garde : 16 réussis, 0 échoué, 1 ignoré**, sur 17 cas, XML `/private/tmp/c20-diagnostic.xml`.
- **Ruff : 0 erreur** avec `ruff check --no-fix src/backend tests`. `git diff --check` ne signale aucune erreur.
- **Frontend : non requis**, aucun fichier frontend n'a été modifié.

Une commande locale pourrait automatiser la capture des rouges isolés et leur report dans le bilan, sans intervenir sur Git.

### Échecs de la porte finale

- `tests/test_b1153_bac_a_sable_commandes.py::test_le_cas_de_l_audit_ne_vide_plus_un_dossier_hors_du_depot`
- `tests/test_b1153_bac_a_sable_commandes.py::test_le_depot_et_le_dossier_temporaire_restent_ecrivables`
- `tests/test_b1153_bac_a_sable_commandes.py::test_l_environnement_du_moteur_ne_passe_pas`
- `tests/test_b1153_bac_a_sable_commandes.py::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[False]`
- `tests/test_b1153_bac_a_sable_commandes.py::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[True]`
- `tests/test_b1153_bac_a_sable_commandes.py::test_aucune_connexion_locale_pas_meme_vers_un_port_ouvert`
- `tests/test_b1153_bac_a_sable_commandes.py::test_un_processus_exterieur_ne_recoit_aucun_signal`
- `tests/test_b1191_commande_introuvable_nommee.py::test_pytest_absent_du_path_n_est_pas_un_confinement_en_panne`
- `tests/test_b1191_commande_introuvable_nommee.py::test_temoin_commande_presente_s_execute_confinee`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[True-True]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[True-False]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[False-True]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[False-False]`
- `tests/test_securite_f2_recette_deb.py::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document`

### Tests ignorés par la garde du lot

- `tests/test_agents_v040.py::test_git_worktree_keeps_user_checkout_untouched_and_diff_uses_task_branch`
- `tests/test_b1153_bac_a_sable_commandes.py::test_le_code_de_l_agent_n_ecrit_ni_dans_le_dossier_personnel_ni_dans_tmp`
- `tests/test_b1153_git_de_mission_durci.py::test_le_commit_de_mission_n_execute_ni_hook_ni_pilote_ni_faux_depot`
- `tests/test_git_service_commit_merge_c9.py::test_un_chemin_introuvable_fait_echouer_le_commit`
- `tests/test_git_service_commit_merge_c9.py::test_un_merge_en_conflit_revient_sur_la_branche_de_depart`
- `tests/test_harnais_backend_autonome.py::test_le_dossier_src_backend_tests_tient_seul`
- `tests/test_identite_git_des_agents.py::test_un_commit_reussit_sans_identite_globale`
- `tests/test_identite_git_des_agents.py::test_l_identite_est_locale_au_depot`
- `tests/test_spawn_gardes_atelier.py::test_spawn_refuse_hors_de_main`
- `tests/test_spawn_gardes_atelier.py::test_spawn_refuse_un_arbre_sale`
- `tests/test_spawn_gardes_atelier.py::test_spawn_refuse_pendant_une_mission_atelier`

### Échecs de la première passe, avant correction de la garde

- `tests/test_actions_traitement.py::TestLeRunEstUnTraitement::test_nominal_running_pendant_done_apres`
- `tests/test_b1153_bac_a_sable_commandes.py::test_le_cas_de_l_audit_ne_vide_plus_un_dossier_hors_du_depot`
- `tests/test_b1153_bac_a_sable_commandes.py::test_le_depot_et_le_dossier_temporaire_restent_ecrivables`
- `tests/test_b1153_bac_a_sable_commandes.py::test_l_environnement_du_moteur_ne_passe_pas`
- `tests/test_b1153_bac_a_sable_commandes.py::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[False]`
- `tests/test_b1153_bac_a_sable_commandes.py::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[True]`
- `tests/test_b1153_bac_a_sable_commandes.py::test_aucune_connexion_locale_pas_meme_vers_un_port_ouvert`
- `tests/test_b1153_bac_a_sable_commandes.py::test_un_processus_exterieur_ne_recoit_aucun_signal`
- `tests/test_b1191_commande_introuvable_nommee.py::test_pytest_absent_du_path_n_est_pas_un_confinement_en_panne`
- `tests/test_b1191_commande_introuvable_nommee.py::test_temoin_commande_presente_s_execute_confinee`
- `tests/test_backup_complete.py::test_restore_ferme_les_engines_avant_extraction`
- `tests/test_harnais_backend_autonome.py::test_le_dossier_src_backend_tests_tient_seul`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_agents.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_backup.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_command_registry.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_crm_sync_message.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_error_handling.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_escalation.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_follow_ups.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_performance.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_personalisation.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_planning_api.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_services_security.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_t4_3_fermeture_harnais_autonome.py]`
- `tests/test_harnais_backend_autonome.py::test_chaque_fichier_de_src_backend_tests_se_collecte_seul[test_workspace_summarize.py]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[True-True]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[True-False]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[False-True]`
- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches[False-False]`
- `tests/test_securite_f2_recette_deb.py::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document`

