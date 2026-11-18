# Cycle 20 : lot marcelo-agenda

## Périmètre et livraison Git

Base : `cd287fb3`, branche demandée `gpt/c20-marcelo-agenda`. Le correctif partiel `3b70de50` a été intégré par cherry-pick sous `ba2c11ea` avec la signature demandée. Ses 12 tests ciblés passent.

Lors du travail initial, les métadonnées Git du worktree n'étaient pas accessibles en écriture. L'orchestrateur a depuis repris les 26 commits sur la branche réelle et les a rebasés sur `c20/integration`. Cette remédiation laisse ses modifications non commitées dans l'arbre demandé, pour reprise par l'orchestrateur.

## Troisième passe : changement de voie

La réponse du modèle reste diffusée et enregistrée avant comme après les outils. Après une lecture, le modèle reçoit le résultat de `list_calendar_events` et poursuit sa réponse ; le routeur ne substitue plus ce résultat à sa continuation et ne l'écarte plus. Le repli préexistant sur le résultat d'outil reste disponible si aucun texte n'est produit. Le texte transmis au skill de fichier comprend également la continuation. La mention finale sans lecture est conservée dans les deux voies, uniquement pour les motifs étroits existants et si l'outil n'a pas été appelé pendant la réponse. La conversion F-11 des tableaux Markdown en listes est rétablie hors flux.

Le commit de Syn conserve la consigne de présenter les événements lus avec leurs dates et heures. Cela ne garantit pas la fidélité du modèle : un modèle qui déforme le résultat de l'outil n'est plus corrigé par le routeur ; le comportement attendu est seulement mieux consigné dans son contexte. La détection sans outil reste limitée à certains libellés et horaires. Aucun modèle réel n'a été appelé.

La route de suppression du profil s'en remet au service pour vider le cache sous son contrôle de génération. Une sauvegarde concurrente conserve ainsi sa fiche, son vecteur et son cache ; une suppression sans fiche efface aussi un éventuel cache obsolète, si la génération est inchangée. SQL et Qdrant ne forment toujours pas une transaction atomique.

Au démarrage, `c20/integration` pointait sur `1b715850` : le diff de `src/backend/app/routers/chat.py` comptait **181 lignes modifiées** (156 ajouts, 25 suppressions). À cette même référence, il en compte désormais **78** (74 ajouts, 4 suppressions). Le partage du contexte du flux reste nécessaire à B-1795 ; les protections générales de persistance du préambule et de la mention interrompus, ainsi que la mesure du premier morceau après outil, restent couvertes par les tests. Les gardes d'annulation ajoutées dans les boucles du producteur ont été retirées pour revenir au comportement de la branche d'intégration de départ.

Pendant la porte complète, `c20/integration` a avancé sur `a3323cd7` avec le lot marcelo-mémoire, qui modifie aussi `chat.py` et d'autres fichiers. Sur cette référence actualisée, le diff de `chat.py` compte **211 lignes modifiées** (81 ajouts, 130 suppressions) : il comprend les changements du lot mémoire absents de cette branche. Ils n'ont pas été importés partiellement dans le lot agenda. La conciliation des deux lots reste à vérifier lors de l'intégration ; la porte de cette troisième passe ne teste pas leur combinaison.

Les nouveaux tests ont été exécutés avant correction. Lignes d'échec reproduites :

```text
test_lecture_puis_mail_preserve_le_flux_et_le_message_enregistre[conversation]
E   AssertionError: assert 'Je consulte ...ien avec Paul' == 'Je consulte ...n\nÀ bientôt.'
test_apres_lecture_la_presentation_du_second_outil_est_conservee
E   AssertionError: assert 'Aucun événem...ndrier local.' == 'Je cherche m...rrier trouvé.'
test_sans_flux_le_tableau_markdown_est_converti_et_enregistre
E   AssertionError: assert 'Récapitulati...ple | Texte |' == 'Récapitulati...aleur : Texte'
test_route_suppression_preserve_le_cache_d_une_sauvegarde_concurrente
E   assert None is not None
```

Les vérifications ciblées ont couvert les réponses en flux et hors flux, les faux positifs, le cas Qwen, la diffusion progressive, les deux outils, le skill de fichier et la course par la route. Les données et vecteurs sont fictifs ; les connexions réseau et les chemins interdits ont été bloqués par la garde locale. Les preuves produites par les deux fichiers historiques du cycle 15 ont été redirigées vers `/private/tmp`.

La passe ciblée comprenant les tests B-1797, B-1829 et les deux fichiers historiques dont les preuves sont redirigées donne **92 réussites**, code 0. La passe précédente vérifiant aussi B-1795, B-1796, B-1830, B-1831, B-1911 et les générations de profil donne **94 réussites**, code 0.

La commande complète demandée rend le code **1**. Lecture du XML `/tmp/agenda-r3.xml` : **6 710 cas, 6 644 réussites, 15 échecs, 0 erreur et 51 ignorés**, en 593,244 secondes. Les 15 échecs font tous partie des cas annoncés : huit B-1153, deux B-1191, quatre `test_refus_a_lecran_meme_sans_fiches` et un `test_securite_f2_recette_deb`. **Aucun nouvel échec** selon cette liste ; la porte brute ne passe donc pas intégralement.

La commande `.venv/bin/python -m ruff check --no-fix src/backend tests` réussit : **0 erreur**.

## Candidats

| ID | Verdict | Test de comportement (`chemin::nom`) | Commit du rouge | Commit du correctif |
| --- | --- | --- | --- | --- |
| B-1795 | `confirme` | `tests/test_b1795_agenda_selection_stream.py::test_le_chat_lit_l_agenda_choisi_parmi_plusieurs` | `4d927eb0` | `29b1810d` |
| B-1797 | `confirme` | `tests/test_b1797_agenda_sans_outil.py::test_qwen_sans_outil_preserve_les_horaires_et_ajoute_la_mention` ; `test_faux_positifs_reponse_intacte_sans_mention` ; `test_lecture_puis_mail_preserve_le_flux_et_le_message_enregistre` ; `test_apres_lecture_la_presentation_du_second_outil_est_conservee` ; `test_apres_appel_de_lecture_aucune_mention` ; `test_sans_flux_le_tableau_markdown_est_converti_et_enregistre` | `50bee5b2`, `04b75576`, `8285f21b`, `b08a7019`, `59677c7b` | Historique : `6eeecfa9`, `b7a5744c`, `260ded0a`, `32da4f6c`, `c8c50914` ; troisième passe non commitée |
| B-1796 | `confirme` | `tests/test_b1796_etat_synchronisation_agenda.py::test_etat_caldav_sain_transmis_avec_les_evenements` | `74576bb2` | `b38e3358` |
| B-1829 | `confirme` | `tests/test_b1829_suppression_profil_durable.py::test_echec_qdrant_ne_signale_pas_une_suppression_reussie` ; `tests/test_b1829_suppression_profil_durable.py::test_annulation_avant_le_verrou_ne_supprime_rien` ; `tests/test_b1829_suppression_profil_durable.py::test_annulation_pendant_qdrant_attend_la_fin_du_fil` ; `tests/test_b1829_suppression_profil_durable.py::test_une_nouvelle_demande_repare_un_vecteur_orphelin` | `f90a933a` | `00ad1daa` |
| B-1830 | `confirme` | `tests/test_b1830_erreurs_lecture_agenda.py::test_l_outil_restitue_la_cause_sans_affirmer_une_absence_de_calendrier` | `34bc1443` | `960f2da7`, `b7be1e66` |
| B-1831 | `confirme` | `tests/test_b1831_lecture_agenda_sans_commit.py::test_echec_lecture_distante_ne_valide_pas_les_modifications_en_attente` | `9181de52` | `7e0beb19` |
| B-1832 | `rejete` après B-1830 | `tests/test_b1830_erreurs_lecture_agenda.py::test_l_outil_restitue_la_cause_sans_affirmer_une_absence_de_calendrier` : cas `introuvable` et `plusieurs_comptes` | — | — |
| B-1911 | `confirme` | `tests/test_b1911_refus_courrier_accentue.py::test_sans_compte_le_message_est_accentue_et_tutoie` | `39d3b217` | `43b95bd4` |

B-1832 décrit le même défaut que B-1830 : au moment de son examen, les tests de B-1830 sont verts et `src/backend/app/services/workspace_tools.py` ne formule l'absence d'agenda que dans le cas correspondant. Aucun commit distinct n'a été créé pour ce doublon.

Le cherry-pick adapte les attentes de `tests/test_b1110_agenda_local_recurrent.py` à l'année et aux accents désormais affichés. Il corrige aussi `tests/test_regression_fournisseurs.py` : l'ancienne assertion interdisait la date UTC partout dans le prompt, alors que le nouveau repère de demain peut légitimement la contenir ; le test vérifie toujours la date et le décalage du poste sur la ligne du jour, ainsi que sa date ISO. Cette raison figure aussi dans le commentaire du test importé.

Le test existant `tests/test_profil_generation.py::TestUneSuppressionTient::test_la_suppression_attend_l_indexation_en_cours` imposait une génération avancée avant la prise du verrou. Il a été remplacé par un test concurrent vérifiant que le vecteur ne réapparaît pas après la suppression. Cette évolution est expliquée dans `00ad1daa`. Le test `tests/test_enveloppe_agenda_et_navigation.py` vérifie la même absence d’événement, avec le mot désormais accentué, comme expliqué dans `c8c50914`. Le test existant sur le refus en l'absence de calendrier a été conservé ; sa régression a été corrigée dans `b7be1e66`.

Les chemins de production ont été vérifiés : le sélecteur `CalendarPanel` écrit dans le même store lu par `ChatInput` avant l'envoi ; la route `/api/chat/send` exécute le flux puis `execute_workspace_tool` ; la route de suppression du profil appelle `delete_user_profile`. Les nouveaux tests traversent le chat HTTP, le répartiteur d'outils ou le service de profil appelé par sa route, avec fournisseurs et données fictifs.

## Limites et règles à trancher

Aucun candidat n'a été classé `regle_a_trancher` : la règle de B-1797 était fournie dans le mandat.

Le correctif de B-1795 transmet la sélection du panneau, mais ne résout pas un nom d'agenda énoncé dans le chat. La promesse P-163 reste à implémenter dans un autre lot.

Le test de B-1795 vérifie la sélection et la lecture d'un événement avec un fournisseur fictif. Il ne démontre pas qu'un modèle réel interprète correctement « jusqu'à la fin de l'année » ; l'outil limite par ailleurs une lecture à 90 jours.

B-1797 laisse le modèle utiliser le résultat de `list_calendar_events` lorsque cet outil est appelé. Sans cet appel, une mention n'est ajoutée qu'en présence d'une demande personnelle explicite et datée et d'au moins deux lignes contenant chacune un horaire. Les motifs sont volontairement étroits et n'héritent pas du tour précédent. Aucun modèle réel n'a été appelé.

B-1796 démontre l'absence antérieure d'état dans le résultat d'outil et transmet l'état enregistré. Les fournisseurs CalDAV et Google ont été simulés : la cause exacte de la phrase observée par Marcelo et l'état d'un serveur réel n'ont pas été vérifiés.

## Remédiation précédente de la relecture : historique

Les constats et résultats de cette section décrivent l'état de la deuxième passe. La troisième passe ci-dessus remplace notamment le traitement du résultat d'agenda et la suppression du cache par la route.

- **B-1797** : suppression du remplacement de la réponse sans lecture. La mention est ajoutée après le texte uniquement si les deux conditions de la décision sont réunies. Les onze faux positifs sont couverts en flux et hors flux, dont les deux relances après une vraie lecture fictive ; le test Qwen couvre les horaires inventés, et les réponses sans deux lignes horaires restent intactes, tableau Markdown compris. Le skill de fichier reçoit le texte du modèle. Quand l'outil est appelé, ses résultats font foi même si le message initial n'a pas la forme d'une demande d'agenda.
- **B-1829** : la suppression SQL est validée avant le retrait du vecteur ; l'annulation attend la fin des deux opérations, puis se propage. Une erreur Qdrant provoque la restauration de la ligne sauvegardée, sauf si une nouvelle ligne existe déjà. Au niveau du service, le cache du profil est vidé après une suppression achevée, sauf si une nouvelle fiche a été enregistrée entre-temps. Sa génération peut alors réindexer la nouvelle fiche après le retrait. Les tests contrôlent le vecteur, l'annulation pendant le commit et l'absence de retrait du vecteur lorsque le commit SQL échoue.
- **Relecture du flux** : l'offre de l'outil d'agenda ne retient plus les morceaux du modèle. Ils sont émis immédiatement et le premier token est enregistré au premier morceau, y compris après un autre outil. Le texte diffusé avant un appel d'agenda est conservé. Chaque lecture effective produit aussitôt son résultat déterministe ; le modèle peut poursuivre ses appels d'outils, mais son texte après cette lecture n'est pas affiché pour éviter une liste réécrite. La mention sans lecture garde ses deux conditions étroites.
- **Flux interrompu** : seul le texte effectivement diffusé est sauvegardé, y compris si l'arrêt survient après un préambule, un résultat d'agenda ou la mention finale ; un morceau reçu après l'annulation est écarté.

Chaque test ci-dessous a été lancé isolément avant son correctif. Pour les tests paramétrés, la ligne recopiée est la première ligne d'échec et le nombre indique les variantes en échec :

```text
test_qwen_sans_outil_preserve_les_horaires_et_ajoute_la_mention (10 variantes)
E       assert "Je n'ai pas ...isse le lire." == 'Voici tes re...t pas de lui.'
test_faux_positifs_reponse_intacte_sans_mention (22 variantes)
E       assert "Je n'ai pas ...isse le lire." == 'Réponse du m...0 : Exemple B'
test_sans_deux_lignes_horaires_aucune_mention (6 variantes)
E       assert "Je n'ai pas ...isse le lire." == 'Je ne peux p...e ton agenda.'
test_sans_lecture_explicite_et_repere_aucune_mention (8 variantes)
E       assert "Je n'ai pas ...isse le lire." == '- 14h : Exem...0 : Exemple B'
test_sans_lecture_explicite_et_repere_aucune_mention, cas d'utilisation et modification (8 variantes)
E       AssertionError: assert '- 14h : Exem...t pas de lui.' == '- 14h : Exem...0 : Exemple B'
test_reperes_temporels_explicites_declenchent_la_mention (4 variantes sur 6)
E       AssertionError: assert '- 14h : Exem...0 : Exemple B' == '- 14h : Exem...t pas de lui.'
test_skill_fichier_explicite_recoit_le_texte_du_modele
E       assert "Je n'ai pas ...isse le lire." == '# Document\n... le document.'
test_lecture_effective_prevaut_meme_sans_motif_agenda
E       AssertionError: assert 'Événement vérifié' in 'Événement inventé avant outil. Événement inventé après outil.'
test_annulation_pendant_qdrant_attend_la_fin_du_fil, avec la ligne SQL initialement conservée
E       AssertionError: assert [] == ['owner_profile']
test_echec_commit_sql_ne_retire_pas_le_vecteur
E       AssertionError: assert [] == ['owner_profile']
test_annulation_pendant_commit_sql_termine_la_suppression
E       AssertionError: assert [] == ['owner_profile']
test_nouvelle_fiche_pendant_retrait_retrouve_son_vecteur
E       AssertionError: assert [] == ['Nouveau profil fictif']
test_l_annulation_persiste_le_message_partiel, contrôle de régression du flux
E       AssertionError: le partiel doit survivre au rechargement
```

La nouvelle relecture a d'abord été testée en rouge, avant modification du producteur. Les trois tests ont échoué ainsi :

```text
test_agenda_offert_le_texte_et_le_premier_token_arrivent_au_fil_de_l_eau
E   AssertionError: assert ['premier', 'deuxième', 'fin'] == ['premier']
test_annonce_avant_lecture_puis_rendez_vous_du_resultat
E   assert (None is not None)
test_annulation_en_flux_enregistre_exactement_le_texte_diffuse
E   AssertionError: assert ['Premier mor...non diffusé.'] == ['Premier morceau. ']
```

Après cette première correction, un contrôle supplémentaire de l'arrêt après la mention a lui aussi échoué avant son correctif :

```text
test_annulation_apres_mention_enregistre_tout_le_texte_diffuse
E   assert [] == ['- 14h : Exe... pas de lui.']
```

Un autre contrôle, lancé avant la correction du préambule, a échoué ainsi :

```text
test_annulation_apres_preambule_enregistre_le_texte_diffuse
E   AssertionError: assert [] == ['Préambule affiché.']
```

Limites : la détection de la mention est fondée sur des formes et horaires précis ; elle ne couvre pas toutes les façons de demander ou de présenter un agenda. Après une lecture effective, tout le texte de la continuation du modèle est écarté, même s'il ne réécrit pas les rendez-vous : la diffusion de tout texte du modèle n'est donc pas satisfaite sur ce chemin. Les tests utilisent une base jetable, un index simulé et des fournisseurs fictifs ; ils ne démontrent pas le comportement de Qdrant ou d'un modèle réel. Si Qdrant échoue après avoir effectué une suppression, ou si la restauration SQL échoue à son tour, les deux stockages ne constituent pas une transaction atomique. La route de suppression vide elle aussi le cache après retour du service ; son interaction avec une sauvegarde concurrente n'a pas été testée.

Portes de la nouvelle relecture :

- La commande pytest demandée : **143 réussis**, 4 avertissements, code 0. Elle comprend huit variantes nouvelles : flux progressif, annonce avant lecture, quatre moments d'annulation et continuation après un autre outil avec ou sans lecture d'agenda.
- Recherche dans `tests/` des assertions sur l'ordre et le nombre des morceaux : **295 réussis**, 4 avertissements, code 0, sur 16 fichiers ou classes ciblant le flux, les fournisseurs, les outils, les fichiers et l'annulation.
- `.venv/bin/python -m ruff check --no-fix src/backend tests` : **0 erreur**, code 0.
- La garde de test existante bloque les connexions réseau, les ports IP et les chemins interdits ; données et fichiers temporaires sont sous `.pytest_cache/c20-flux-relecture/` dans cet arbre. Aucun fournisseur réel n'a été appelé.

Portes de la remédiation précédente :

- La commande pytest demandée : **124 réussis**, 4 avertissements, code 0.
- Les cinq fichiers complémentaires ciblant le flux, son annulation, les skills et la sélection d'agenda : **22 réussis**, 4 avertissements, code 0.
- `.venv/bin/python -m ruff check --no-fix src/backend tests` : **0 erreur**, code 0. Les premières passes ont signalé un espacement d'import puis un ordre d'opérandes, corrigés avant la passe verte.
- Exécution avec données jetables dans cet arbre, fournisseur et index simulés, et garde locale contre les accès réseau et les chemins interdits. La suite complète reste à la charge de l'orchestrateur.
- Le harnais, ses journaux et sa base fictive sont conservés dans `.pytest_cache/c20-marcelo-essais/`, ignoré par Git. La mise à la Corbeille a été refusée par le confinement de ce runtime.

## Portes du lot initial

- Suite backend demandée : **6576 réussis, 15 échoués, 0 erreurs de test, 51 ignorés**, sur 6642 cas. Durée : 393.144 s. Résultat de la commande : code 1. Source des comptes : `/tmp/marcelo-agenda-pytest.xml`.
- Les tests importés de `3b70de50` : **12 réussis, 0 échoué** dans cette suite. Les nouveaux tests du lot : B-1795 1/1, B-1796 1/1, B-1797 12/12, B-1829 4/4, B-1830 4/4, B-1831 1/1 et B-1911 1/1.
- Ruff : `.venv/bin/python -m ruff check --no-fix src/backend tests` : **0 erreur**, code 0.
- Frontend : aucune modification de fichiers frontend ; portes frontend non requises et non exécutées.

La porte n'est pas verte. Cinq échecs correspondent à la référence fournie : les quatre paramètres de `test_refus_a_lecran_meme_sans_fiches` et le test `test_securite_f2_recette_deb`. Les dix autres sont hors de cette référence : huit tests B-1153 et deux B-1191 nécessitent les capacités de confinement macOS ; dans ce runtime déjà restreint, le sous-confinement échoue avec `PermissionError`, et un test ne peut pas ouvrir sa socket locale jetable. Un cas de chacun de ces deux fichiers a été relancé sans la garde de test et échoue aussi ; leurs fichiers et le code de confinement sont identiques à la base `cd287fb3`. Cela ne remplace pas une porte verte dans un environnement autorisant ces tests.

Pour respecter l'interdiction d'accès à `.app-loop/`, les fichiers de preuve produits par deux tests historiques ont été redirigés vers `/private/tmp`. Les autres assertions restent exécutées. Une garde bloque les sorties réseau et les ports interdits ; les données sont jetables. Une première passe complète a donné 6 553 réussites, 30 échecs et 51 ignorés : quatorze échecs provenaient de la transmission involontaire du plugin aux sous-tests autonomes, et un de ma régression B-1830. Le harnais et cette régression ont été corrigés avant la porte ci-dessus.

Noms exacts des 15 échecs relevés dans le XML :

- `tests.test_b1153_bac_a_sable_commandes::test_le_cas_de_l_audit_ne_vide_plus_un_dossier_hors_du_depot`
- `tests.test_b1153_bac_a_sable_commandes::test_le_code_de_l_agent_n_ecrit_ni_dans_le_dossier_personnel_ni_dans_tmp`
- `tests.test_b1153_bac_a_sable_commandes::test_le_depot_et_le_dossier_temporaire_restent_ecrivables`
- `tests.test_b1153_bac_a_sable_commandes::test_l_environnement_du_moteur_ne_passe_pas`
- `tests.test_b1153_bac_a_sable_commandes::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[False]`
- `tests.test_b1153_bac_a_sable_commandes::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[True]`
- `tests.test_b1153_bac_a_sable_commandes::test_aucune_connexion_locale_pas_meme_vers_un_port_ouvert`
- `tests.test_b1153_bac_a_sable_commandes::test_un_processus_exterieur_ne_recoit_aucun_signal`
- `tests.test_b1191_commande_introuvable_nommee::test_pytest_absent_du_path_n_est_pas_un_confinement_en_panne`
- `tests.test_b1191_commande_introuvable_nommee::test_temoin_commande_presente_s_execute_confinee`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-True]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-False]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-True]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-False]`
- `tests.test_securite_f2_recette_deb::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document`
