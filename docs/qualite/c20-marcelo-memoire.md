# Cycle 20 : lot marcelo-mémoire

## Candidats

| ID | Verdict | Test de comportement | Commit du rouge | Commit du correctif |
| --- | --- | --- | --- | --- |
| B-1798 | confirmé | `tests/test_recherche_fichiers_par_contenu.py::test_un_mot_du_contenu_retrouve_le_fichier` | Aucun commit séparé : test et correctif déjà réunis dans le cherry-pick demandé | `6fa3100b` |
| B-1799 | confirmé | `tests/test_c20_b1799_recherche_vide.py::test_recherche_vide_ne_devient_pas_un_contenu_invente` et `::test_recherche_web_confirmee_vide_ne_devient_pas_un_contenu_invente` | `23aed949` | `f56dfb69` |
| B-1800 | rejeté sur ce banc | `/private/tmp/c20-b1800-rejeu.py::test_route_memoire_avec_jeton_lu_sur_disque` ; voir aussi `tests/test_r3_5_recherche_fichiers.py::test_indexation_filtre_qdrant_et_http_reels_sans_modele_en_ligne` | Aucun | Aucun |
| B-1827 | confirmé | `tests/test_c20_b1827_cloison_recherche.py::test_index_restreint_les_fragments_au_dossier_et_a_la_conversation` et `::test_route_ferme_tous_les_chemins_sans_perimetre` | `2208745b` | `9951a0f2` |
| B-1828 | confirmé | `tests/test_c20_b1828_confirmations_distinctes.py::test_envois_distincts_gardent_deux_cartes` | `8cfd8143` | `d0eb3f39` |
| B-1909 | confirmé | `tests/test_c20_b1909_repli_pptx.py::test_repli_pptx_convertit_les_puces_markdown` | `55732e9a` | `1c654161` |
| B-1910 | confirmé | `tests/test_c20_b1910_creation_non_confirmee.py::test_confirmation_ne_pretend_pas_creer_sans_succes` et `::test_message_de_succes_contredit_par_le_json_n_est_pas_annonce` | `a7a2dfd1` | `2fb947c1` |

Le commit `89545e9e` a été intégré sous `6fa3100b`, avec ajout du co-auteur demandé. Ses 19 tests passent. Pour B-1798, le test du mot dans le contenu a aussi été rejoué sur le fichier de production précédent, puis le fichier corrigé a été restauré. Le test et la correction du cherry-pick étaient déjà dans un seul commit ; ils n'ont pas été réécrits.

Pour B-1800, un fichier texte a été réellement indexé dans une base et un index jetables. La route HTTP, appelée avec le jeton lu dans un fichier `.session_token` jetable, renvoie 200 et retrouve le contenu « DRAC ». Sans l'en-tête, elle renvoie 401 ; un script qui ignore le statut HTTP et interprète l'absence de `results` comme une liste vide peut afficher zéro. La garde est dans `src/backend/app/main.py:860` et la route dans `src/backend/app/routers/memory.py:497`. Ce rejeu a eu lieu sur ce Mac, pas sur le Manjaro de Marcelo. Sa boîte de réception n'a pas été consultée : l'accès à SYN et aux services en ligne est hors mandat. Son incident reste donc inexpliqué.

Pour B-1799, la réponse déterministe couvre les formats vides connus des recherches natives de fichiers, e-mails, factures et web confirmées. Elle ne prétend pas interpréter les formats arbitraires d'un connecteur MCP. Pour B-1827, les anciens tests du contenu vectoriel fabriquaient des fragments sans périmètre : leurs assertions sont conservées et leurs fixtures déclarent maintenant des fragments généraux. Pour B-1828, l'ancien test qui fusionnait l'outil natif et son homonyme MCP exige désormais deux cartes ; les répétitions identiques de l'outil natif gardent leur test de déduplication.

## Écarts d'environnement et incident de test

Le worktree utilise des métadonnées Git situées hors de l'arbre autorisé. Le cherry-pick ordinaire a été refusé à la création du verrou Git. Les commits de ce rapport sont donc dans les métadonnées isolées `.c20-git`, sur une branche portant le nom demandé ; la référence Git d'origine n'a pas pu être mise à jour. Un bundle incrémental est fourni à la racine de l'arbre pour transférer les commits sans réseau.

La première exécution de la suite complète a été interrompue après découverte d'un effet de bord : les tests de concurrence du cycle 15 ont écrit leurs preuves dans `.app-loop/cycles/15/reprise/lot-c`, malgré l'interdiction. Ce dossier n'a pas été inspecté ni nettoyé. Avant la relance, une garde locale a été vérifiée sur ces tests : elle redirige leurs preuves vers `/private/tmp/c20-marcelo-preuves` et bloque l'accès à l'installation personnelle de THÉRÈSE. Une garde réseau bloque les services externes et les ports interdits. L'environnement refuse par ailleurs l'ouverture d'une écoute locale temporaire, nécessaire aux tests du bac à sable des commandes.

Pour reprendre les commits sur la branche Git d'origine, depuis cet arbre et après vérification de son état :

```sh
git fetch --no-tags ./c20-marcelo-memoire.bundle gpt/c20-marcelo-memoire
git reset --mixed FETCH_HEAD
```

Ces commandes mettent à jour la branche et l'index sans pousser et sans modifier les fichiers de travail. Elles restent à exécuter hors du sandbox actuel.

## Portes

- Backend : **6 601 passés, 15 échoués, 51 ignorés**, sur 6 667 cas. Rapport JUnit : `/tmp/marcelo-memoire-pytest.xml`.
- Ruff sur `src/backend tests` : **0 erreur**.
- Frontend : non exécuté, aucun fichier frontend modifié.

Échecs de référence communiqués avant le lot :

- `tests/test_r3_4_ollama.py::test_refus_a_lecran_meme_sans_fiches` : 4 cas paramétrés.
- `tests/test_securite_f2_recette_deb.py::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document` : 1 cas.

Dix échecs supplémentaires dans cet environnement de travail :

- `tests/test_b1153_bac_a_sable_commandes.py::test_le_cas_de_l_audit_ne_vide_plus_un_dossier_hors_du_depot`.
- `tests/test_b1153_bac_a_sable_commandes.py::test_le_code_de_l_agent_n_ecrit_ni_dans_le_dossier_personnel_ni_dans_tmp`.
- `tests/test_b1153_bac_a_sable_commandes.py::test_le_depot_et_le_dossier_temporaire_restent_ecrivables`.
- `tests/test_b1153_bac_a_sable_commandes.py::test_l_environnement_du_moteur_ne_passe_pas`.
- `tests/test_b1153_bac_a_sable_commandes.py::test_la_cle_maitresse_du_dossier_de_donnees_est_illisible` : 2 cas paramétrés.
- `tests/test_b1153_bac_a_sable_commandes.py::test_aucune_connexion_locale_pas_meme_vers_un_port_ouvert`.
- `tests/test_b1153_bac_a_sable_commandes.py::test_un_processus_exterieur_ne_recoit_aucun_signal`.
- `tests/test_b1191_commande_introuvable_nommee.py::test_pytest_absent_du_path_n_est_pas_un_confinement_en_panne`.
- `tests/test_b1191_commande_introuvable_nommee.py::test_temoin_commande_presente_s_execute_confinee`.

Le confinement des commandes exige une sonde utilisant une écoute locale temporaire. Celle-ci lève `PermissionError` dans le sandbox de cette session, même sans la garde réseau ajoutée pour le lot ; la commande est alors refusée et les tests qui l'attendent échouent. Le code du bac à sable et ces tests sont inchangés depuis la base. Les identifiants des paramètres sont conservés dans le XML, sans être recopiés ici.

## Remédiation de la relecture

- B-1799, tour mixte : la réponse déterministe de recherche vide ne coupe le tour que si tous ses outils ont rendu une recherche vide reconnue. Sinon, tous les résultats sont transmis à la continuation. Un avertissement de recherche partielle ne neutralise pas le repli sur un autre résultat utile quand le modèle reste silencieux.
- B-1799, recherche partielle : le refus ou l'impossibilité de vérifier l'accord « documents » est transmis dans le résultat de recherche. Les fichiers hors périmètre et le contenu non consulté sont annoncés explicitement dans la bulle ; le sélecteur de dossier est indiqué. Ces situations ne sont pas classées comme des recherches vides.
- B-1910 : en cas d'échec d'une création, `error`, puis `message`, sont affichés lorsqu'ils ne contredisent pas le statut. Une affirmation de création conserve le message générique de non-confirmation.

Chaque nouveau test a été lancé seul avant la correction du comportement qu'il vérifie. Les cinq premières lignes ci-dessous sont les échecs constatés sur le code initial. Les cinq suivantes proviennent de contrôles ajoutés pendant la correction : le premier met en évidence un repli masqué par la première version de l'avertissement ; les quatre derniers, des formulations mal classées par le filtre des confirmations en cours de correction. Le témoin de deux recherches vides et celui d'une erreur affirmant « Contact créé » étaient déjà verts avant correction.

```text
FAILED tests/test_c20_b1799_recherche_vide.py::test_recherche_vide_et_emails_trouves_repondent_avec_les_deux_resultats - assert ('Rapport Alpha' in "Je n'ai trouvé aucun fichier pour cette recherche. Les autres résultats sont disponibles dans le détail des outils.")
FAILED tests/test_c20_b1799_recherche_vide.py::test_fichiers_hors_perimetre_annonces_avec_le_selecteur - assert 'hors périmètre' in "je n'ai trouvé aucun fichier pour cette recherche."  +  where "je n'ai trouvé aucun fichier pour cette recherche." = <built-in method lower of str object at 0x111a196f0>()  +    where <built-in method lower of str object at 0x111a196f0> = "Je n'ai trouvé aucun fichier pour cette recherche.".lower
FAILED tests/test_c20_b1799_recherche_vide.py::test_sans_accord_documents_la_bulle_dit_que_le_contenu_n_est_pas_consulte - assert ('contenu' in "je n'ai trouvé aucun fichier pour cette recherche.")  +  where "je n'ai trouvé aucun fichier pour cette recherche." = <built-in method lower of str object at 0x111b1d140>()  +    where <built-in method lower of str object at 0x111b1d140> = "Je n'ai trouvé aucun fichier pour cette recherche.".lower
FAILED tests/test_c20_b1910_creation_non_confirmee.py::test_erreur_de_validation_du_contact_est_affichee - assert "L'adresse e-mail n'a pas la forme attendue" in "La création n'est pas confirmée. Vérifie dans l'application avant de réessayer."
FAILED tests/test_c20_b1910_creation_non_confirmee.py::test_motif_d_interruption_de_creation_est_affiche - AssertionError: assert 'La création ...de réessayer.' == 'Création du ...a génération.'      - Création du contact interrompue avant écriture : l'utilisateur a arrêté la génération.   + La création n'est pas confirmée. Vérifie dans l'application avant de réessayer.
FAILED tests/test_c20_b1799_recherche_vide.py::test_avertissement_partiel_ne_masque_pas_le_repli_des_emails - AssertionError: assert ('Rapport Alpha' in 'Des fichiers indexés existent dans des dossiers hors périmètre de cette conversation. Pour les consulter, rattache la conversation à un dossier avec le sélecteur en haut du chat.\n\n')
FAILED tests/test_c20_b1910_creation_non_confirmee.py::test_negation_puis_affirmation_de_creation_reste_masquee - AssertionError: assert 'le contact a été créé' not in 'La création... a été créé.'      'le contact a été créé' is contained here:     La création n'a pas été confirmée mais le contact a été créé.   ?                                        +++++++++++++++++++++
FAILED tests/test_c20_b1910_creation_non_confirmee.py::test_cause_evoquant_une_adresse_deja_enregistree_est_preservee - AssertionError: assert 'La création ...de réessayer.' == 'Cet e-mail e...r un contact.'      - Cet e-mail est déjà enregistré pour un contact.   + La création n'est pas confirmée. Vérifie dans l'application avant de réessayer.
FAILED tests/test_c20_b1910_creation_non_confirmee.py::test_creation_dite_effectuee_malgre_l_echec_reste_masquee - AssertionError: assert 'a été effectuée' not in 'La création...é effectuée.'      'a été effectuée' is contained here:     La création du contact a été effectuée.   ?                        +++++++++++++++
FAILED tests/test_c20_b1910_creation_non_confirmee.py::test_affirmation_sans_accents_malgre_l_echec_reste_masquee - AssertionError: assert 'Contact cree' not in 'Contact cree avec succes.'      'Contact cree' is contained here:     Contact cree avec succes.
```

Portes après correction : **109 tests passés**, aucun échec ni cas ignoré sur les six fichiers demandés ; `ruff check --no-fix src/backend tests` : **0 erreur**. Les données et la garde de test étaient dans un dossier temporaire ignoré de cet arbre. Une garde d'audit Python bloquait les événements de connexion et d'accès aux chemins interdits surveillés par Python ; l'activation supplémentaire de `sandbox-exec` a été refusée par le sandbox de la session. Les modèles étaient fictifs ; SQLite et Qdrant utilisés par les tests étaient isolés.

Restent incertains : le comportement d'un modèle réel face aux résultats et aux avertissements n'a pas été évalué ; le filtrage des messages de création est fondé sur des formulations reconnues et ne peut pas interpréter toutes les phrases libres. Les formats arbitraires d'outils non natifs ne sont pas reconnus comme recherches vides. La suite complète et son rejeu sur les deux machines restent à la charge de l'orchestrateur. La section historique sur un dépôt Git annexe et un bundle décrit le lot précédent, pas l'état de cette remédiation.

## Seconde remédiation

- Une recherche partielle sans document ni autre résultat exploitable affiche sa limite et s'arrête sans rappeler le modèle, même si un autre outil a échoué. L'avertissement de périmètre n'est posé que si le périmètre courant n'a rendu aucun document. Un résultat utile laisse la continuation possible.
- Une panne de l'index est distinguée d'un refus d'accord : la réponse précise que le contenu n'a pas pu être consulté, tout en conservant les éventuels résultats par nom.
- Les recherches vides reconnues ne masquent plus un autre résultat dans le repli. Un résultat exploitable obtenu à un tour précédent empêche la phrase déterministe du tour vide suivant ; les tests vérifient la bulle et le message enregistré.
- Le filtre des créations distingue les participes passés affirmatifs des instructions à l'impératif ou à l'infinitif et des formulations envisagées au futur. L'échec réel du brouillon sans ligne restitue « Ajoute au moins une ligne au brouillon. »

Avant la première modification applicative, le rejeu ciblé comptait 12 échecs et un témoin passant sur 13 cas (`/private/tmp/marcelo-r2.Leym6j/rouge.xml`). Les lignes suivantes sont recopiées des échecs XML, dans l'ordre des quatre réserves :

```text
E       AssertionError: assert 'comité imaginaire' not in 'Des fichier... imaginaire.'
E       AssertionError: assert 'La création ...de réessayer.' == 'Ajoute au mo...au brouillon.'
E       assert ('Rapport Alpha' in "Je n'ai trouvé aucun fichier pour cette recherche.")
E       KeyError: 'contenu_non_consulte'
```

Le cas de repli avec les e-mails et la recherche vide dans le même tour échouait aussi : seul le JSON de la recherche vide était affiché. Les contrôles supplémentaires de formulation ont été lancés avant leur correction ; les deux contrôles complémentaires sur le périmètre et le format booléen de la limite ont d'abord échoué sur la première version de la remédiation.

Porte demandée : **124 tests passés, zéro échec, erreur ou cas ignoré**, d'après `/tmp/memoire-r2.xml` ; `ruff check --no-fix src/backend tests` : **0 erreur**. Les données et le profil de test sont jetables sous `/private/tmp`. Une garde Python interdisait les connexions, les écoutes et les chemins exclus ; pytest ignorait explicitement `.app-loop`. Deux sondes IPv6 et quatre tentatives vers le port 9, dont la découverte de la configuration Ollama, ont été interceptées avant ouverture de port, résolution DNS ou connexion. Aucun fournisseur réel n'a été contacté.
