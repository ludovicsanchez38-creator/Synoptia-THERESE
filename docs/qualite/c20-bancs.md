# Cycle 20 : lot bancs

Arbre `gpt/c20-bancs`, base observée `4dfc79d1`. Aucun commit ni push : les rouges et les correctifs restent dans l'arbre pour que l'orchestrateur rejoue les tests sur la base, puis constitue les commits. Les lignes de rouge ci-dessous sont les sorties réellement observées ; le mot « non commité » indique un correctif présent dans l'arbre.

| ID | Verdict | Test ou preuve | Rouge observé | Correctif |
| --- | --- | --- | --- | --- |
| B-2029 | confirmé | `tests/test_b2029_couverture.py::test_garde_autorise_uniquement_la_migration_locale_du_chat` | `At index 0 diff: 'bloquee' != 'continue'` | non commité |
| B-1806 | confirmé | `tests/test_b1806_banc_ollama.py::test_refus_existant_avec_grande_fenetre`, quatre variantes | `assert not fournisseur[2]` | non commité |
| B-1808 | confirmé | `src/frontend/src/lib/chatPersistence.fin.test.ts::aucune sauvegarde du test précédent ne part après son démontage` ; `::une requête déjà partie peut échouer après disparition de la fenêtre` | `expected "vi.fn()" to not be called at all, but actually been called 1 times` ; `TypeError: Cannot read properties of undefined (reading 'dispatchEvent')` | non commité |
| B-1807 | confirmé | `tests/test_b1807_recette_deb.py::test_amorcage_avec_interpreteur_dans_un_chemin_a_espaces` | `AssertionError: assert '' == 'document-factice'` | non commité |
| B-2030 | confirmé | `src/frontend/src/components/calendar/CalendarPanel.reconnexion.chargement.test.tsx::ni une liste vide ni un agenda local n’éteignent la bannière ; un agenda Google l’éteint et arrête le sondage` | `AssertionError: expected 1 to be greater than 1` | non commité |
| B-2033 | confirmé partiellement | `tests/test_b2033_charges.py::test_scenario_action_attend_le_commit_durable` | `AssertionError: assert 'running' == 'done'` | non commité pour le scénario Actions ; les deux autres restent ouverts |
| B-1850 | rejeté | `tests/test_alembic_stamp.py::test_stamp_db_legacy` et `::test_make_db_migrate_sur_db_legacy` ; `src/backend/alembic/env.py:142`, `:150` et `:156` | aucun : les deux tests passent | aucun changement |
| B-1851 | confirmé | `tests/test_b1851_preuve_frontiere.py::test_preuve_refuse_les_evenements_manquants_ou_non_surs`, six variantes | `Failed: DID NOT RAISE <class 'AssertionError'>` | non commité |
| B-1852 | confirmé : lacune de preuve | `tests/test_b1852_preuve_attribution.py::test_preuve_echoue_si_le_chat_annonce_le_fournisseur_choisi` ; `::test_reponse_chat_annonce_le_fournisseur_effectif` | `Failed: DID NOT RAISE <class 'AssertionError'>` | non commité |
| B-1853 | rejeté sur la contradiction de règles | `tests/test_scope_contacts.py::TestUneCreationNEstJamaisPublieeSansLeVouloir::test_un_contact_ajoute_au_carnet_est_partage_en_mode_transversal` et `::test_un_projet_cree_en_mode_transversal_reste_dans_sa_conversation` ; `docs/recette/2026-10-20-r1.md:8` | aucun : les deux tests passent | aucun changement |
| B-1854 | confirmé | `src/frontend/src/test/b1854-garde-parcours.test.ts::refuse les mutations sur les routes bouchonnées` et `::laisse le calcul pur rejoindre le moteur` | `AssertionError: expected { status: 200, …(2) } to match object { status: 405 }` ; `AssertionError: expected { status: 200, …(2) } to be 'moteur'` | non commité |
| B-1970 | confirmé : même lacune que B-1852 | Rouge commun : `tests/test_b1852_preuve_attribution.py::test_preuve_echoue_si_le_chat_annonce_le_fournisseur_choisi` ; affichage : `src/frontend/src/components/chat/MessageBubble.b1970.test.tsx::le badge de la réponse affiche le fournisseur effectif après une bascule` | même rouge que B-1852 : `Failed: DID NOT RAISE <class 'AssertionError'>` ; pas de rouge distinct pour le composant, déjà correct avec les données transmises | non commité, preuve complétée par le test du badge |

## Résultats et limites

- B-2029 : la garde admet uniquement le POST de migration du chat vers le backend jetable, sans paramètre d'URL. Le service appelé écrit dans la base jetable et ne contacte pas de fournisseur. Le test exerce la route Playwright simulée et les refus voisins. Les ports du parcours étant interdits dans ce mandat, aucun parcours navigateur complet n'a été lancé et la production de `rapport.json` n'est pas vérifiée ici.
- B-1806 : l'identité initiale tenait dans une fenêtre de 128 000 jetons. Elle est augmentée pour dépasser cette fenêtre ; les quatre assertions et leurs variantes restent en place. Aucun transport réel n'est utilisé.
- B-1808 : le démontage du test annule les écritures différées enregistrées ; une réponse déjà en vol ne tente plus de signaler son échec à une fenêtre absente. Les tests voisins de persistance restent actifs. Une suite complète reste nécessaire pour valider l'effet du nettoyage commun sur tous les tests.
- B-1807 : le faux exécutable utilisait un interpréteur dans un shebang contenant des espaces. Un lanceur shell transmet maintenant le chemin cité à Python ; le test continue à exécuter l'amorçage réel de la recette avec curl simulé.
- B-2030 : le test attend le premier sondage réellement observé au lieu de confondre l'état « En attente » avec l'armement de l'intervalle. Les vérifications successives sur liste vide, agenda local, agenda Google et arrêt restent présentes.
- B-2033 : le scénario Actions attend désormais la fin du producteur et de son commit durable avant de lire la base. Le test de restauration et le test de planning sont passés isolément ici, sans rouge permettant d'identifier la cause de leur échec intermittent. Le seuil du planning reste strictement d'une seconde en temps réel : le remplacer par du temps CPU ou le retirer affaiblirait l'assertion existante. Recommandation technique : conserver ce seuil et le mesurer sur un banc dédié ou caractérisé ; ne pas prétendre avoir corrigé ces deux cas sans les reproduire. Les journaux indiqués dans la demande sont sous `.app-loop/`, dont l'accès était interdit.
- B-1850 : le prévol Alembic crée les tables manquantes et applique les migrations ad hoc avant l'estampille. Les deux scénarios ne suivent donc pas le même chemin que l'appel direct à `ensure_alembic_stamp`.
- B-1851 : les contre-épreuves couvrent pour chacun des deux fournisseurs l'absence d'événement, une fuite dans un texte et une fuite dans les arguments d'un outil. Le test exige une erreur et inspecte tous les champs de chaque événement.
- B-1852 et B-1970 : la contre-épreuve montre que l'ancien test ne détectait pas une attribution de chat incorrecte. Les réponses HTTP avec et sans flux, puis la pastille du composant, sont vérifiées avec un fournisseur factice. La bascule est simulée : le résolveur actuel retourne le fournisseur choisi (`src/backend/app/services/llm.py:827-834`) et ne change pas de destinataire sur panne. Ces tests ne prouvent donc pas une bascule automatique réelle.
- B-1853 : la règle R1-2 distingue explicitement le carnet de contacts partagé des projets non promus. Le docstring de la classe de test, antérieur à cette distinction, reste trompeur ; aucun comportement n'a été modifié sans rouge.
- B-1854 : les écritures rencontrent la garde avant les bouchons de lecture. Le calcul ROI pur rejoint le moteur ; son scénario vérifie deux résultats distincts. La réponse factice de génération d'image est limitée au seul scénario de confirmation. Les scénarios Playwright complets ne sont pas exécutables sans la pile sur les ports interdits ; seul le comportement de la garde a été exercé ici.

Aucune règle métier non documentée n'a été identifiée comme devant être tranchée dans ce lot.

## Portes et comptes

- Backend ciblé, XML `/tmp/bancs-pytest.xml` relu : **78 tests passés, 0 échoué, 0 erreur, 0 ignoré**. Échecs : aucun. Le plugin `tests/bancs_sans_reseau.py` a compté **0 tentative de connexion** dans le processus pytest ; il interdit les connexions sortantes durant ce banc.
- Vérifications isolées supplémentaires : Alembic **2/2**, portée contact/projet **2/2**, restauration **1/1**, planning **1/1** ; soit **6 passés, 0 échoué, 0 ignoré**. Échecs : aucun. Ces résultats isolés ne prouvent pas l'absence des intermittences B-2033.
- Frontend ciblé : **12 fichiers, 37 tests passés, 0 échoué, 0 ignoré, 0 erreur non gérée**. Échecs : aucun. Le chargeur `--configLoader runner` est nécessaire ici : le chargeur standard tente d'écrire dans le `node_modules` partagé et reçoit `EPERM` avant de lancer les tests.
- Garde Node existante de couverture écran : **1 test passé, 0 échoué**.
- Ruff : **0 erreur**. TypeScript `tsc --noEmit` : **0 erreur**. ESLint : **0 erreur, 27 avertissements** dans des fichiers source non modifiés ; sortie 0 avec le seuil existant.
- Aucune suite complète, aucun lancement sur les ports interdits, aucun commit, aucun push et aucun accès à `.app-loop/`.

## Remédiation de la relecture, passe 1

- P2, banc Actions : l'attente du producteur et de son commit est limitée à cinq secondes. Un `finally` annule et attend les tâches créées par le scénario, y compris si leur nombre est inattendu. Les vérifications de l'état et du commit durable restent en place.
- Contre-épreuve ajoutée dans `tests/test_b2033_charges.py`, lancée seule pour chaque variante avant le correctif :
  - `producteur-bloque` : `E   AssertionError: le scénario n'a pas borné l'attente du producteur`
  - `nombre-inattendu` : `E   AssertionError: des producteurs du scénario restent actifs`
- Les appelants relus comprennent le scénario au commit retardé et l'enregistrement des tâches par `ActionRunner.run`. Les deux variantes ajoutées et les tests voisins passent : **59 tests, 0 échec, 0 erreur, 0 ignoré**, d'après `/tmp/bancs-r1.xml` relu. La garde hors réseau a compté **0 tentative de connexion**.
- `ruff check --no-fix --no-cache src/backend tests` : **0 erreur**. Aucune suite complète ni modification frontend ; aucun commit ni push.

## Remédiation de la relecture, passe 2

- P2 confirmé : le scénario Actions attend le producteur sans laisser `wait_for` suspendre son propre dépassement de délai. Il suit l'écriture terminale protégée et les fermetures protégées qu'elle lance, puis annule et attend les tâches du scénario avec un nettoyage borné ; une seconde annulation traite une première annulation retardée. Les tâches d'un autre traitement ne sont pas annulées.
- Contre-épreuves lancées seules dans `tests/test_b2033_charges.py` avant leur correctif respectif, avec les véritables `ActionRunner._execute` et `TraitementHandle.terminer` et une écriture retenue :
  - avant la correction, `pendant-commit` : `E           AssertionError: une écriture de clôture reste active` ;
  - avant la correction, `avant-cloture` : `E           AssertionError: le scénario reste suspendu pendant la clôture` ;
  - après la première correction, `annulation-retardee` : `E           AssertionError: une écriture de clôture reste active` ;
  - après la deuxième correction, `fermeture-protegee` : `E               AssertionError: une fermeture protégée reste active`.
- Les quatre variantes vérifient également qu'une clôture concurrente extérieure au scénario reste active. Les appelants relus comprennent `ActionRunner.run`, `_execute`, `TraitementHandle.terminer` et la fermeture de session de `get_session_context`.
- Limite : si une coroutine ignore toutes les demandes d'annulation au-delà des délais de nettoyage, le scénario échoue explicitement mais Python ne permet pas de la terminer de force ; elle peut alors rester active. Les contre-épreuves couvrent une annulation retardée et une fermeture protégée imbriquée qui finissent par accepter l'annulation.
- Porte backend ciblée et fichiers voisins : **72 tests passés, 0 échec, 0 erreur, 0 ignoré**, d'après `/tmp/bancs-r2.xml` relu ; **0 tentative de connexion** selon la garde hors réseau. Le bac refuse aussi l'envoi sur les sockets locales de réveil d'asyncio : un tube local temporaire a servi à réveiller la boucle du client de test, sans autoriser de connexion réseau.
- `ruff check --no-fix src/backend tests` : **0 erreur**. Aucune suite complète, modification frontend, ni opération Git d'écriture.
