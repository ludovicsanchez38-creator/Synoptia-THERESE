# Cycle 20 : lot migrations

Branche `gpt/c20-migrations`, base `6959f803`. Les tests et correctifs sont laissés non commités conformément au mandat. Les lignes de la colonne « Rouge » proviennent des exécutions isolées avant correction ; elles permettent leur rejeu sur la base initiale.

| ID | Verdict | Test ou preuve | Rouge observé | Correctif |
| --- | --- | --- | --- | --- |
| B-1888 | confirme | `tests/test_c20_b1888_transaction_activites.py::test_reconstruction_preserve_la_transaction_appelante` | `AssertionError: La transaction de l’appelant a été validée.` | non commité |
| B-1889 | confirme | `tests/test_c20_b1889_notes_heritees.py::test_note_rattachee_preservee_si_evenement_sans_projet` | `AssertionError: assert None == 'projet-existant'` | non commité |
| B-1890 | confirme | `tests/test_c20_b1890_activites_sans_contact.py::test_migration_ajoute_contact_absent_sans_perte` | `KeyError: 'contact_id'` (schémas standard et enrichi) | non commité |
| B-1891 | confirme | `tests/test_c20_b1891_reparation_transaction.py::test_reparation_preserve_la_transaction_appelante` | `AssertionError: La réparation a validé la transaction de l’appelant.` | non commité |
| B-1892 | rejete | `docs/plans/2026-10-21-r2-memoire-fiches.md:59-61` ; `tests/test_c19d_b1088_securite_memoire.py::test_faux_positifs_differes_et_contre_exemples_v5` | Sans objet : refus prudent documenté | Sans objet |
| B-1893 | confirme | `tests/test_c20_b1893_provenance_sans_marque.py::test_reponse_sans_information_documentaire_reste_prudente` | `AssertionError: assert 'sans_document' == 'documents'` | non commité |
| B-1894 | rejete | `src/backend/app/routers/reprise.py:36-38` ; essai concurrent isolé décrit ci-dessous | Sans objet : aucune deuxième restauration observée | Sans objet |
| B-2009 | confirme | `tests/test_c20_b2009_motifs_ambigus.py::test_refus_ambigu_sans_attribution_inexacte` | `AssertionError: assert 'opinion politique' not in 'Cette donné...n politique.'` ; `AssertionError: assert 'appartenance syndicale' not in 'Cette donné...e syndicale.'` | non commité |
| B-2010 | confirme | `tests/test_c20_b2010_limite_cle.py::test_limite_ne_presente_pas_la_cle_comme_acceptee` | `AssertionError: assert 'acceptée' not in 'Clé accepté...de requêtes.'` | non commité |
| B-2011 | confirme | `tests/test_c20_b2011_cle_sans_espace.py::test_cle_sans_espace_ne_cite_pas_un_autre_fournisseur` | `assert 'OpenAI' in "Ta clé Claude n'est rattachée à aucun espace de travail. Dans la Console Claude, crée une clé rattachée à un espace (par exemple « Default Workspace »)."` | non commité |
| B-2012 | confirme | `src/frontend/src/components/atelier/AgentSession.profilChange.b2012.test.tsx::explique un changement de profil pendant la vérification de destination` | `Error: expect(element).toHaveTextContent()` ; reçu : `Vérifie la connexion au moteur` | non commité |
| B-2013 | confirme | `src/frontend/src/components/atelier/AgentSession.refusDestination.b2013.test.tsx::affiche le refus du moteur pendant la vérification de destination` | `Error: expect(element).toHaveTextContent()` ; reçu : `Vérifie la connexion au moteur` | non commité |
| B-2014 | confirme | `src/frontend/src/components/invoices/InvoiceForm.abandonPaiement.b2014.test.tsx::écarte le paiement pendant la question d’abandon et le rétablit ensuite` | `Error: expect(element).not.toBeInTheDocument()` : bouton « Marquer comme payée » encore présent dans l'arbre accessible | non commité |

## Précisions

- **B-1892.** Un UUID ou un condensat hexadécimal peut aussi être une valeur secrète. La règle existante impose le refus en cas de doute : le faux positif signalé est réel, mais l'assouplissement demandé implicitement contredirait cette règle. Aucun filtre n'a été affaibli.
- **B-1894.** Dans la boucle asynchrone unique de l'application desktop, aucun `await` ne sépare le contrôle du verrou de son acquisition ; une acquisition non contestée ne suspend pas la tâche. Un essai en mémoire avec restauration fictive bloquée a obtenu un refus 409 pendant la première restauration, puis un autre après celle-ci, avec un seul appel à `restaurer_copie`. Cela ne prétend pas couvrir un déploiement multiprocessus, qui n'est pas le mode de lancement vérifié ici.
- **B-2013.** Le test existant `AgentSession.accordMoteur.test.tsx` imposait l'ancien message de connexion et interdisait explicitement le motif utile : ses assertions ont été inversées pour vérifier le refus réel, et le test des coupures réseau conserve son exigence distincte.
- **B-2014.** Les tests existants `InvoiceForm.pied.c19d.test.tsx` supposaient les commandes accessibles pendant la question. Les vérifications de disposition sont conservées après « Continuer la saisie » ; le nouveau test vérifie que les actions incompatibles sont masquées pendant la question et reviennent ensuite. Une soumission clavier pendant la question est également arrêtée. Un contrôle supplémentaire du focus a d'abord échoué avec `Error: expect(element).toHaveFocus()` ; le focus entre désormais sur « Continuer la saisie » puis revient sur « Annuler ».
- Les chemins corrigés sont appelés par le code de production : migrations depuis `app.models.database`, garde depuis `memory_cards`, provenance depuis le routeur de chat, messages de clé depuis le routeur de configuration, et composants React dans les parcours concernés.

## Portes

- Frontend Vitest : **4 102 réussis, 0 échec, 0 ignoré**, dans 966 fichiers. Le mode `--configLoader runner` évite l'écriture du fichier temporaire Vite dans le `node_modules` partagé et en lecture seule ; la suite a aussi été limitée à deux workers et confinée hors réseau.
- TypeScript : **0 erreur** (`npx tsc --noEmit`).
- ESLint : **0 erreur, 27 avertissements**, tous dans des fichiers non modifiés (`npm run lint`).
- Ruff : **0 erreur** (`.venv/bin/python -m ruff check --no-fix src/backend tests`).
- Backend pytest : **6 639 réussis, 15 échoués, 51 ignorés, 0 erreur**, soit 6 705 cas, d'après `/tmp/migrations-pytest.xml`. Cinq échecs correspondent à la référence fournie. Les dix autres ne sont pas couverts par cette référence et restent non résolus : les relancer isolément donne les mêmes résultats, avec une sonde de confinement rejetée par `PermissionError` ou un confinement qui ne démarre pas. L'ouverture d'un port local éphémère renvoie aussi `PermissionError` à l'appel système. Ces indices attribuent les dix échecs aux restrictions du bac à sable imbriqué, sans constituer une validation de ces tests en dehors de cette session.

Échecs connus de la référence :

- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-True]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-False]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-True]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-False]`
- `tests.test_securite_f2_recette_deb::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document`

Échecs supplémentaires observés dans ce bac à sable :

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

Une première exécution backend, interrompue avant les tests qui écrivent dans `.app-loop`, avait produit un échec intermittent de `tests/test_actions_traitement.py::TestLeRunEstUnTraitement::test_nominal_running_pendant_done_apres` : le statut en mémoire était terminé alors que le traitement durable était encore en cours. Ce test est passé en rejeu isolé. Cette observation reste à distinguer du résultat final de la suite.

Les deux tests historiques qui écrivent leurs preuves sous `.app-loop` ont été lancés avec une redirection limitée à ces écritures vers `/tmp/c20-migrations-preuves` : leurs huit cas sont passés et aucun dossier `.app-loop` n'a été créé. La garde temporaire interdit aussi les connexions externes et les trois ports exclus. La commande Vitest brute avait d'abord échoué au démarrage avec `EPERM` sur son fichier temporaire dans `node_modules` ; aucun test n'avait alors été exécuté.

Pour les prochains lots, une commande de rejeu de chaque nouveau test sur la base initiale pourrait automatiser cette vérification répétée avant les commits de l'orchestrateur.

## Remédiation de la relecture, passe 1

Les deux constats sont confirmés. Les changements restent non commités pour permettre le rejeu des tests sans les correctifs de production.

| Constat | Test isolé avant correction | Rouge observé | Correction et vérification |
| --- | --- | --- | --- |
| 1. B-2013 | `src/components/atelier/AgentSession.refusHttp.b2013.test.tsx` | `Error: expect(element).toHaveTextContent()` dans les deux callbacks. Attendu : « Ce profil d’agent est introuvable. Reviens au catalogue. » ; reçu : le message demandant de vérifier la connexion au moteur. | Le vrai `getAgentConsent` et `request` reçoivent un HTTP 404 simulé. Les deux callbacks affichent désormais le refus métier HTTP 4xx ; une coupure conserve son message distinct. Les tests vérifient aussi l'absence de mission et les deux coupures. |
| 2. B-2014 | `src/components/invoices/InvoiceForm.focusAbandon.b2014.test.tsx` | `Error: expect(element).toHaveFocus()` pour Tab et Maj+Tab. Le focus restait sur « Abandonner » dans un sens et visait le bouton masqué « Créer » dans l'autre. | Le piège clavier exclut les descendants d'un élément `hidden`. Les deux extrémités sont vérifiées dans le formulaire réel ; les tests voisins couvrent notamment la reprise de saisie et la conversion. |

Les chemins des tests ci-dessus sont relatifs à `src/frontend`. Pour rejouer chaque rouge isolément depuis ce répertoire, lancer respectivement :

```sh
VITE_THERESE_BACKEND_PORT=9 npm_config_offline=true npx --no-install vitest run src/components/atelier/AgentSession.refusHttp.b2013.test.tsx --configLoader runner --maxWorkers=1
VITE_THERESE_BACKEND_PORT=9 npm_config_offline=true npx --no-install vitest run src/components/invoices/InvoiceForm.focusAbandon.b2014.test.tsx --configLoader runner --maxWorkers=1
```

Portes de cette passe, sans suite complète :

- Backend ciblé : **6 réussis, 0 échec, 0 erreur, 0 ignoré**, vérifiés dans `/tmp/migrations-r1.xml` : `tests/test_t4_3_accord_atelier.py` et les deux tests `test_mark_invoice_paid` et `test_mark_invoice_paid_default_date` de `tests/test_routers_invoices.py`.
- Ruff sur `src/backend tests` : **0 erreur**.
- Frontend : **207 tests réussis dans 60 fichiers** : tests `AgentSession`, `InvoiceForm` et `useDialogFocusTrap`. Les appels HTTP du test frontend sont simulés ; les connexions et écoutes réseau étaient interdites pendant les exécutions.
- TypeScript : **0 erreur**. ESLint : **0 erreur, 27 avertissements**, dans des fichiers non modifiés.
