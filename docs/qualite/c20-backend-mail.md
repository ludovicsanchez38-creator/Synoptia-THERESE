# Cycle 20 : lot backend-mail

Branche de travail `gpt/c20-backend-mail`. Les corrections et les tests sont laissés non commités, conformément au mandat d'exécution. Les rouges ont été exécutés individuellement avant chaque correction ; les messages ci-dessous reprennent la ligne d'échec observée. Les tests utilisent des serveurs et modèles fictifs.

| ID | Verdict | Test ou preuve | Rouge observé | Correctif |
| --- | --- | --- | --- | --- |
| B-1802 | confirme | `tests/test_b1802_date_message_id.py::test_envoi_et_copie_envoyes_portent_date_et_identifiant` | `AssertionError: en-tête Date absent` | non commité |
| B-1803 | rejete | `src/frontend/src/components/email/EmailList.tsx:133` et `src/frontend/src/components/prototype/emailReadModels.ts:45` | sans objet | sans objet |
| B-1820 | confirme | `tests/test_b1820_contrat_connexion.py::test_echec_et_succes_de_connexion_sont_des_booleens` | `AssertionError: un échec IMAP doit renvoyer False` | non commité |
| B-1821 | confirme | `tests/test_b1821_reindexation_extraction.py::test_reindexation_apres_extraction_none_preserve_anciens_vecteurs` | `Failed: DID NOT RAISE <class 'fastapi.exceptions.HTTPException'>` | non commité |
| B-1822 | confirme | `tests/test_b1822_brouillon_mime.py::test_brouillon_enregistre_conserve_fil_et_piece[False-create]` | `AssertionError: assert None == '<origine@example.test>'` | non commité |
| B-1823 | confirme | `tests/test_b1823_extraction_demandes.py::test_demande_aide_n_ecarte_pas_contact_ni_projet[peux-tu]` | `AssertionError: assert [] == ['Marie Martin']` | non commité |
| B-1905 | confirme | `tests/test_b1905_piece_gmail.py::test_piece_jointe_gmail_retrouve_nom_et_type` | `AssertionError: assert 'attachment' == 'devis.pdf'` | non commité |
| B-1906 | rejete | `tests/test_c22b_pdf_sans_texte.py::test_scan_avertit_le_chat` et `tests/test_c22b_pdf_sans_texte.py::test_indexation_vide_ne_repond_pas_pret` | sans objet | sans objet |
| B-1907 | confirme | `tests/test_b1907_profil_inconnu.py::test_sans_profil_brouillon_ne_fabrique_pas_identite_ni_signature` | `assert 'Ludo' not in "Tu es l'ass... ta réponse."` | non commité |
| B-1908 | confirme | `tests/test_b1908_taille_image.py::test_depassement_minimal_affiche_une_taille_superieure_a_la_limite` | `AssertionError: assert '5,01 Mo' in 'image.png (5 Mo, limite 5 Mo)'` | non commité |

## Portée et limites

- Chemins de production vérifiés : `routers/email.py::send_email` appelle le fournisseur IMAP pour B-1802 ; `routers/files.py::index_file` passe par le service d'indexation pour B-1821 ; `routers/email.py::create_draft` appelle le fournisseur IMAP pour B-1822 ; `routers/chat.py::_extract_entities_background` appelle l'extracteur pour B-1823 ; `routers/email.py::generate_email_response` utilise le générateur pour B-1907 ; `routers/chat.py::_attacher_images` charge les images pour B-1908.
- B-1803 : la liste IMAP ou Gmail est relue auprès du fournisseur, puis la liste affichée est remplacée par les résultats reçus ; les messages absents ne sont pas ajoutés depuis le cache du navigateur. Cela ne prouve pas la purge de la fiche éventuellement conservée dans la base locale ni le cas d'une requête de rafraîchissement en échec.
- B-1820 : `test_connection` respecte désormais le contrat booléen commun ; `test_connection_details` conserve le diagnostic IMAP/SMTP utilisé par les deux routes. La fixture commune et les tests existants ont été adaptés au nouveau nom de la méthode détaillée, sans retirer leurs assertions sur le refus de configuration, l'enregistrement réussi, les détails d'échec ou les délais.
- B-1821 : seule la valeur `None`, qui désigne une extraction impossible, est traitée comme un échec ; une chaîne vide garde son traitement existant. Les anciens vecteurs et leur compteur restent intacts lors de l'échec.
- B-1822 : la création et le remplacement d'un brouillon IMAP conservent les pièces, les références du fil et la copie cachée fournies au contrat du fournisseur. La route HTTP actuelle ne transmet pas encore de pièces jointes ni de références au fournisseur : le parcours d'interface complet ne les expose donc pas.
- B-1905 : les métadonnées sont récupérées dans le message avant le téléchargement, y compris dans les parties MIME imbriquées. Le fournisseur est utilisé par le code de production, mais aucun appelant de `get_attachment` n'a été trouvé dans le parcours applicatif : aucun téléchargement d'interface de bout en bout n'est démontré.
- B-1906 : `extract_text` renvoie délibérément une chaîne vide, que les appelants du chat et de la route d'indexation convertissent en avis adapté. L'index interne conserve un compteur à zéro ; cela ne signifie pas que la route annonce une réussite.
- B-1907 : sans nom connu, le brouillon ne reçoit plus d'identité ou de signature ajoutée par défaut. Quand un nom de profil est disponible, la règle de signature déjà présente est conservée.

## Comparaison avec la branche historique

Le commit local `de839790` n'est ancêtre ni de cette branche ni de la référence locale `origin/main`. Les commits du 2 novembre `4dab31b4`, `38de3070` et `2e6a2a76` ne sont pas non plus leurs ancêtres. Les quatre fichiers du périmètre agenda et messagerie comparés sont identiques entre `HEAD` et cette référence locale ; aucune actualisation distante n'a été faite.

- Le délai IMAP reste fixé par des constantes dans `imap_smtp_provider.py:38` ; la configuration et sa borne du correctif historique ne sont pas présentes sous cette forme. L'échec de la copie dans Envoyés est journalisé, mais aucun avertissement équivalent au reçu historique n'est renvoyé par ce fournisseur.
- La résolution d'un dossier IMAP absent produit déjà un avertissement et une liste vide, mais les distinctions d'erreurs et le refus proposés dans la réserve historique ne sont pas repris à l'identique.
- La purge CalDAV sur fenêtre bornée existe dans `calendar.py:903`. En revanche, le contrôle du jeton de pagination répété et l'attestation explicite de lecture complète du correctif historique ne figurent pas dans les fichiers comparés. La présence de cette purge seule ne prouve donc pas l'équivalence complète des réserves #104.

## Portes de vérification

### Incident d'isolement de la première exécution

La première exécution complète a lancé huit cas de `test_c15_emission_concurrente.py` et `test_c15_courses_suppression_conversion.py` qui enregistrent leurs observations sous `.app-loop/cycles/15/reprise/lot-c`. Les huit cas ont réussi et leur code écrit ces fichiers : `concurrence-observation-provisoire-deux-envois.txt`, `concurrence-observation-provisoire-envoi-paiement.txt`, `concurrence-observation-provisoire-deux-paiements.txt`, `concurrence-observation-historique-emise.txt`, `concurrence-pieces-distinctes.txt`, `concurrence-base-occupee.txt`, `concurrence-course-suppression-emission.txt` et `concurrence-course-double-conversion.txt`. Ces écritures, possiblement des remplacements, contreviennent à la consigne de ne pas toucher à `.app-loop`. Le dossier n'a pas été ouvert ni modifié de nouveau pour tenter une restauration ; son état antérieur est inconnu.

Pour la seconde exécution, les preuves de ces tests sont redirigées vers `/tmp/c20-backend-mail-preuves`, sans changer leurs assertions ; un garde interdit l'accès au dossier `.app-loop` de cet arbre et au profil réel. Deux tests ont vérifié la redirection. Le bac autorise les seuls essais réseau locaux hors ports interdits et refuse les résolutions externes ; le dossier personnel des tests est temporaire.

La seconde exécution a été interrompue après deux échecs du harnais autonome : les `pytest` qu'il lance héritaient du nom du plugin d'isolation alors que leur chemin d'import est volontairement épuré. Le plugin retire désormais son propre nom de l'environnement une fois chargé. Les quinze tests du harnais passent isolément avec cette correction ; une nouvelle porte complète a été lancée.

### Résultats finaux

- Backend, XML `/tmp/backend-mail-pytest.xml` lu après exécution : **6 622 cas, 6 556 réussis, 15 échoués, 0 erreur, 51 ignorés**. Les huit nouveaux fichiers de test sont verts : 16 cas réussis ; les trois cas du test existant sur les PDF sans texte sont également verts.
- Ruff, commande demandée sur `src/backend tests` : **réussi, 0 erreur**.
- Frontend : portes non exécutées, aucun fichier frontend modifié.
- La première passe complète donnait 6 554 réussis, 17 échecs et 51 ignorés. Elle avait révélé deux régressions corrigées avant la passe finale : la forme de l'ouverture binaire dans le test B-1908 et l'ancien appel au diagnostic détaillé dans le test SMTP. Les assertions correspondantes sont conservées et les deux tests passent dans le XML final.

Les **cinq échecs de référence** communiqués avant le lot sont :

```text
tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-True]
tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-False]
tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-True]
tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-False]
tests.test_securite_f2_recette_deb::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document
```

Les **dix échecs supplémentaires**, non inclus dans cette référence, concernent le bac à sable des commandes :

```text
tests.test_b1153_bac_a_sable_commandes::test_le_cas_de_l_audit_ne_vide_plus_un_dossier_hors_du_depot
tests.test_b1153_bac_a_sable_commandes::test_le_code_de_l_agent_n_ecrit_ni_dans_le_dossier_personnel_ni_dans_tmp
tests.test_b1153_bac_a_sable_commandes::test_le_depot_et_le_dossier_temporaire_restent_ecrivables
tests.test_b1153_bac_a_sable_commandes::test_l_environnement_du_moteur_ne_passe_pas
tests.test_b1153_bac_a_sable_commandes::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[False]
tests.test_b1153_bac_a_sable_commandes::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible[True]
tests.test_b1153_bac_a_sable_commandes::test_aucune_connexion_locale_pas_meme_vers_un_port_ouvert
tests.test_b1153_bac_a_sable_commandes::test_un_processus_exterieur_ne_recoit_aucun_signal
tests.test_b1191_commande_introuvable_nommee::test_pytest_absent_du_path_n_est_pas_un_confinement_en_panne
tests.test_b1191_commande_introuvable_nommee::test_temoin_commande_presente_s_execute_confinee
```

Le bac d'exécution refuse `bind` sur une adresse locale avec `PermissionError`. Le test B-1153 de l'écriture autorisée a aussi été relancé sans le garde réseau ajouté pour cette recette : il échoue de la même façon, la sonde du confinement étant refusée. Les autres cas ne peuvent donc pas établir leurs assertions de confinement dans cet environnement. Ces dix rouges restent ouverts ; ils ne doivent pas être comptés comme une porte verte.

## Remédiation de la relecture, passe 1

Le constat est confirmé : lorsque l'extracteur rendait `None`, la synchronisation recevait une exception HTTP 422, consignait l'opération en échec et la réessayait à la reprise. Le cœur d'indexation émet maintenant `ExtractionImpossible` avant l'écriture vectorielle et sans appeler `_ecrire_et_consigner`. Les routes d'indexation et de dépôt traduisent ce signal en HTTP 422 ; la synchronisation le consigne `obsolete`, avec son motif. Les anciens vecteurs, les compteurs et la référence de la dernière version indexée restent en place. Les autres erreurs restent réessayables selon le contrat existant.

Le test d'intégration ajouté a été exécuté seul avant le correctif. Sa ligne d'échec, relue dans `/tmp/backend-mail-r1-rouge.xml`, était :

```text
E       AssertionError: assert 'echec' == 'obsolete'
```

Les cinq nouveaux cas couvrent l'indexation initiale et la réindexation illisibles, l'absence d'écriture, la conservation des données précédentes, la poursuite des autres opérations, la reprise sans nouvel essai et la réponse 422 des deux routes. Le test B-1821 vérifie désormais le 422 par la route HTTP réelle, en conservant ses assertions sur les vecteurs et les métadonnées. Les appelants du cœur, du suivi HTTP, du dépôt et du chat ont été relus.

La première passe des tests voisins a rendu 103 réussites et deux échecs dans les nouvelles assertions HTTP : elles cherchaient `detail`, alors que le gestionnaire d'erreurs de l'application renvoie `message`. Après correction de ces assertions et ajout du cas de premier fichier, la passe relue dans `/tmp/backend-mail-r1-voisins.xml` donne **106 réussites sur 106**.

La porte backend demandée, relue dans `/tmp/backend-mail-r1.xml`, donne **6 627 cas : 6 561 réussites, 15 échecs, 0 erreur et 51 ignorés**. Les 15 échecs correspondent tous aux références fournies : huit cas B-1153, deux B-1191, quatre cas `test_refus_a_lecran_meme_sans_fiches` et le cas `test_securite_f2_recette_deb`. Aucun autre rouge n'a été relevé. La suite a été lancée avec un environnement jetable, une garde Python interdisant les opérations réseau et l'accès aux deux chemins protégés, et une redirection des preuves C15 vers `/tmp`.

Ruff, sur `src/backend tests` avec `--no-fix`, est **réussi sans erreur**. Une première invocation avait été refusée avant analyse parce que la variable temporaire de désactivation du cache valait `1` ; elle a été relancée avec la valeur reconnue `true`. Les portes frontend ne s'appliquent pas : aucun fichier frontend modifié. Les changements restent non commités.
