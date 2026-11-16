# Cycle 20, lot diff-2

Travail limité à `gpt/c20-diff-2`. Aucun commit ni push : l'index Git est inaccessible dans ce bac à sable, conformément au mandat (aucune tentative de `git add`). Les changements restent dans l'arbre pour reprise par l'orchestrateur. Aucun appel à un fournisseur LLM ni à un service en ligne.

Résultat : 4 candidats confirmés pour 3 défauts distincts, 4 rejetés et 2 soumis au même arbitrage de date. Trois nouveaux fichiers de tests couvrent 10 cas, tous observés rouges avant correction puis verts. Aucun test existant modifié.

## Verdicts et preuves

| Id | Verdict | Test (chemin::nom) ou preuve | Rouge observé (à la place du commit) | Correctif |
| --- | --- | --- | --- | --- |
| B-1874 | rejete | `tests/test_b1219_outil_projet_valeurs_controlees.py::test_un_budget_illisible_ou_infini_n_est_pas_enregistre` ; `src/backend/app/services/memory_tools.py:263-271,766-777` | Aucun rouge : le convertisseur renvoie déjà `None` pour les valeurs citées, puis le stocke tel quel. | Aucun changement |
| B-1875 | confirme | `tests/test_b1875_anonymisation_transactionnelle.py::test_un_echec_annule_aussi_le_detachement` (4 cas : identité/commit, manuel/automatique) | `AssertionError: l'anonymisation annulée a détaché la racine` (4 échecs, `/tmp/diff-2-b1875-rouge.xml`) | non commité |
| B-1876 | regle_a_trancher | `src/frontend/src/components/invoices/InvoiceForm.datePaiement.p155.test.tsx::B-1147 reprise après correctif : %s %s %s` ; la route `mark_invoice_paid` accepte aussi des horodatages | Aucun test rouge sans choisir une convention absente du contrat | Aucun changement |
| B-1877 | confirme | `src/frontend/src/components/memory/ProjectDeliverablesSection.changementProjet.b1877.test.tsx::un ajout de A ne rejoint jamais B, même après la fusion` (2 ordres), puis 3 cas voisins | `Error: expect(element).not.toBeInTheDocument()` ; élément trouvé : `Livrable A` dans B (`/tmp/diff-2-b1877-rouge.xml`, 5 échecs) | non commité |
| B-1878 | confirme | `src/frontend/src/components/memory/ProjectDeliverablesSection.changementProjet.b1877.test.tsx::un ajout de A ne rejoint jamais B, même après la fusion` ; doublon de B-1877 | Même rouge observé avant correction : `Error: expect(element).not.toBeInTheDocument()` ; `Livrable A` affiché dans B | non commité |
| B-1879 | rejete | `tests/test_p160_serie_commune.py::test_frontiere_annee_garde_numero_et_date_dans_la_meme_annee` ; `src/backend/app/routers/invoices.py:364-383` | Aucun : `issue_date` est une date civile à minuit, pas un instant UTC | Aucun changement |
| B-1880 | rejete | `src/frontend/src/components/email/ResponseGeneratorModal.tsx:80-105,130-143` ; `src/frontend/src/components/email/ResponseGeneratorModal.obsolete.test.tsx::compte changé sans fermer et même UID : le vieux résultat ne remplace pas la réponse du nouveau compte` | Aucun défaut de production reproduit ; assertion de session effectivement incomplète | Aucun changement |
| B-2002 | regle_a_trancher | `src/frontend/src/components/invoices/InvoiceForm.datePaiement.p155.test.tsx::B-1147 reprise après correctif : %s %s %s` ; même convention que B-1876 | Aucun sans arbitrage du sens des horodatages anciens | Aucun changement |
| B-2003 | confirme | `src/frontend/src/components/crm/ExplicationDuScore.cible.b2003.test.tsx::B-2003 : la cible de l’aide respecte les 36 px des boutons Contacts` | `AssertionError: hauteur de la cible en pixels: expected 24 to be greater than or equal to 36` (`/tmp/diff-2-b2003-rouge.xml`) | non commité |
| B-2006 | rejete | `src/frontend/src/components/email/ResponseGeneratorModal.tsx:80-105,130-143` ; même test voisin que B-1880 | Même lacune d'assertion, aucun défaut de production reproduit | Aucun changement |

## B-1874 : portée de la lecture statique

L'assertion existante est effectivement plus large que le nom du test. Le code exécuté, lui, écarte les budgets illisibles, infinis ou négatifs avec `None`, et passe directement cette valeur au modèle `Project`. Cette faiblesse d'assertion ne prouve donc pas un défaut de production. Aucun test ni code modifié pour ce candidat. Contrôle voisin : 16 tests passés, 0 échec, 0 erreur, 0 ignoré (`/tmp/diff-2-b1874.xml`).

## B-1875 : reproduction avant correction

Les quatre cas échouent sur l'état durable de la racine, relu dans une nouvelle session après l'erreur. La fiche et le projet sont conservés, mais la racine est détachée. Le test vérifie aussi la génération, le plan et le référentiel de synchronisation lors du passage au vert. Une première version du test attendait une exception HTTP ; elle a été rectifiée avant toute modification de production, car le gestionnaire d'erreurs transforme cette exception en réponse 500.

Chemins de production vérifiés avant correction : `app.routers.rgpd.anonymize_contact` et `app.services.rgpd_auto.auto_purge_expired_contacts` appellent `anonymiser_la_personne`, qui détache les racines puis utilise `app.routers.memory._nettoyer_et_supprimer_projet`.

Correction B-1875 : session SQL appelante transmise à `retirer_racine`, sans commit interne dans ce cas ; verrou du projet conservé jusqu'à la fin de la transaction, y compris sur erreur. Les appels autonomes conservent leur propre transaction. Les 4 régressions et les voisins B-1685 / synchronisation passent : 37 tests, 0 échec, 0 erreur, 0 ignoré (`/tmp/diff-2-b1875-vert.xml`).

## B-1876 : convention des dates de paiement à trancher

Question : `payment_date` représente-t-il le jour saisi, un instant à convertir systématiquement à Paris, ou un instant à afficher dans le fuseau du poste ? P-155 accepte la date réelle du paiement (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:140-142,197-199`) sans préciser cette convention. Le schéma stocke un `datetime`, le formulaire envoie un jour sans heure, et la route retire le suffixe `Z` avant enregistrement (`src/backend/app/routers/invoices.py:1099,1117`). Les tests de reprise exigent le jour écrit. La convention Paris explicite de `_date_demission` concerne l'émission ; elle ne fixe pas celle du paiement.

Options : conserver le jour littéral pour toutes les valeurs ; convertir les instants zonés en jour de Paris ; convertir dans le fuseau du poste. Recommandation : définir le paiement comme une date civile `YYYY-MM-DD`, préserver les jours déjà saisis, convertir à Paris les valeurs dont la provenance prouve qu'elles sont des instants. Les anciennes valeurs sans fuseau nécessitent une règle de reprise explicite : une conversion automatique inventerait une information perdue. Aucun changement avant cet arbitrage.

## B-1877 et B-1878 : création tardive après changement de projet

Les deux descriptions désignent la même course. Reproduction avant correction dans les deux ordres lecture/création, avec un aller-retour A/B/A et une nouvelle création dans B. Les cinq cas échouent : trois sur un livrable étranger affiché et deux sur la saisie de A conservée dans B. Le test contrôle ensuite aussi les erreurs tardives, le bouton pendant la création de B et la conservation de sa saisie.

Chemin de production vérifié : `ProjectModal.tsx:501` monte `ProjectDeliverablesSection` sans clé par projet ; `ProjectsPanel.tsx:267` et `PanelContainer.tsx:164` utilisent cette modale. La correction doit invalider la génération à chaque départ de projet, remettre à zéro la version des écritures et ignorer les succès, erreurs et finalisations d'une ancienne ouverture.

Vitest : le chargement par défaut a tenté d'écrire son module temporaire dans le `node_modules` partagé et a été refusé par le bac à sable, avant tout test. Les exécutions utilisent `--configLoader=runner --no-cache`, sans modifier la configuration ni écrire dans les dépendances partagées.

Les 5 nouveaux tests et les 29 voisins P-153 passent (`/tmp/diff-2-b1877-vert.xml`). Aucun test existant affaibli ou réécrit.

## B-1879 : date civile d'émission

Le candidat suppose à tort que `issue_date` est un instant UTC. `_date_demission` convertit l'instant capturé en jour de Paris, puis le stocke sans fuseau à minuit. Les chemins envoyé/payé capturent l'instant avant l'allocation et le transmettent à `_poser_dates_demission`. Recalculer via ce même chemin après le passage à minuit donnerait le 1er janvier et ferait échouer l'assertion existante. Les 12 tests P-160 passent (`/tmp/diff-2-b1879.xml`). L'assertion ne couvre pas toute mutation imaginable, mais le défaut de production décrit n'est pas reproduit.

## B-1880 : couverture de réouverture incomplète

Le test cité ne compare effectivement pas le brouillon final. Cela ne démontre pas une réponse périmée dans l'application : `estCourante` vérifie génération, ouverture, message et compte avant succès, erreur et finalisation ; l'effet invalide la génération au changement de contexte et à la fermeture. Le voisin `ResponseGeneratorModal.obsolete.test.tsx` vérifie explicitement la réponse fraîche, son bouton et le texte transmis après une réponse périmée. Les 6 tests existants passent (`/tmp/diff-2-b1880.xml`). Le scénario exact de réouverture reste moins couvert que son intitulé ne le promet ; les journaux ne sont pas présentés ici comme des assertions.

## B-2002 : même arbitrage que B-1876

Question, options et recommandation : voir B-1876. Le mot « aujourd'hui » borne la saisie ; il ne tranche pas le fuseau des anciennes valeurs stockées. Les 32 tests de paiement existants passent avec leur convention actuelle (`/tmp/diff-2-b2002-b2003.xml`).

## B-2003 : taille de la cible

La règle locale fixe les boutons des écrans Contacts à 36 px, avec une exception pour les puces de filtre uniquement (`docs/plans/2026-09-11-da-lot4-contacts-design.md:44-46`). Le bouton d'aide n'est pas une puce de filtre. Le test rend le vrai composant puis applique les utilitaires dimensionnels avec le compilateur Tailwind réel, au pas standard de 0,25 rem et à la taille de texte de référence de 16 px. Il mesure 24 px au rouge. Aucun examen textuel du source du composant.

Chemins de production vérifiés avant correction : `PipelineView.tsx:482` monte `ExplicationDuScore` dans la carte du contact ; `CRMPanel.tsx:361` le monte dans la fiche. Seule la taille est confirmée, au regard de la règle locale de design. Le bouton natif, `aria-expanded`, `aria-controls` et l'anneau de focus ne prouvent pas les autres défauts suggérés ; aucun rôle supplémentaire n'est imposé au texte déplié. Correction limitée à une cible de 36 × 36 px qui ne rétrécit pas dans un conteneur flex. Les 4 tests du composant passent (`/tmp/diff-2-b2003-vert.xml`).

Une tentative de mesure dans Chromium local a échoué au lancement : `bootstrap_check_in ... Permission denied (1100)` dans le bac à sable. Chromium s'est arrêté avant toute page ; aucun service réseau n'a été démarré. La vérification des dimensions reste celle du DOM et des CSS compilés, pas une recette visuelle dans un navigateur.

## B-2006 : doublon de B-1880

Même constat de couverture et même verdict. Aucun changement : les règles du lot exigent un défaut de comportement reproduit avant de modifier le code. Il reste possible de renforcer séparément le test de réouverture ; cela ne constitue pas ici une réparation rouge/verte démontrée.

## Portes finales

Exécutées le 16 novembre 2026, dans cet arbre uniquement. Aucune suite complète lancée. Les comptes de pytest et Vitest ci-dessous sont lus dans leurs XML, pas déduits de la console tronquée.

| Porte | Périmètre | Passés | Échoués | Erreurs | Ignorés | Preuve |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Pytest | 25 fichiers ciblés | 174 | 0 | 0 | 0 | `/tmp/diff-2-pytest.xml`, sortie 0 |
| Vitest | 10 fichiers ciblés, 3 workers maximum | 87 | 0 | 0 | 0 | `/tmp/diff-2-vitest.xml`, sortie 0 |
| Ruff | `src/backend tests`, sans correction automatique | Sans objet | 0 | 0 | Sans objet | `All checks passed!`, sortie 0 |
| TypeScript | `tsc --noEmit` | Sans objet | 0 | 0 | Sans objet | Sortie 0, aucun diagnostic |
| ESLint | `npm run lint` | Sans objet | 0 | 0 | Sans objet | Sortie 0, 27 avertissements dans 22 fichiers non modifiés, `/tmp/diff-2-eslint.log` |
| Contrôle de diff | `git diff --check` | Sans objet | 0 | 0 | Sans objet | Sortie 0 |

Total des tests aux portes finales : **261 passés, 0 échoué, 0 erreur, 0 ignoré**. Noms des échecs finaux : **aucun**. Les trois fichiers de régression représentent 4 cas pytest et 6 cas Vitest. Des tests voisins émettent des avertissements React `act(...)` et les erreurs simulées prévues par leurs scénarios ; ils restent verts et n'ont pas été modifiés. Aucun avertissement ESLint ne vise un fichier modifié dans ce lot.

### Rejeu backend

```sh
PYTHONDONTWRITEBYTECODE=1 OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest \
  tests/test_b1875_anonymisation_transactionnelle.py \
  tests/test_b1685_anonymiser_un_dossier_synchronise.py \
  tests/test_project_sync_service.py tests/test_project_sync_idempotence.py \
  tests/test_project_sync_api.py tests/test_project_sync_boucle.py \
  tests/test_routers_rgpd.py tests/test_rgpd_erasure.py tests/test_anonymisation_brouillons.py \
  tests/test_b1438_rgpd_adresse_fiche.py tests/test_b1640_preavis_efface_a_l_anonymisation.py \
  tests/test_b1688_relance_echue_effacee_a_l_anonymisation.py \
  tests/test_b1651_purge_auto_alignee_sur_la_manuelle.py tests/test_rgpd_purge_commit_echoue_c9.py \
  tests/test_r5_10_rgpd.py tests/test_r5_9_notes.py tests/test_routers_memory.py \
  tests/test_p148_trois_chemins_de_suppression.py tests/test_p148_ensemble_du_projet.py \
  tests/test_memory_purge_disque_du_dossier.py tests/test_b1178_cascade_contact_purge_le_depot.py \
  tests/test_b1503_suppression_projet_rend_ses_contacts.py \
  tests/test_b1219_outil_projet_valeurs_controlees.py tests/test_p160_serie_commune.py \
  tests/test_p155_date_de_paiement.py \
  -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-2-pytest.xml
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m ruff check --no-fix --no-cache src/backend tests
```

### Rejeu frontend

Depuis `src/frontend` :

```sh
npx --no-install vitest run \
  src/components/memory/ProjectDeliverablesSection.changementProjet.b1877.test.tsx \
  src/components/memory/ProjectDeliverablesSection.p153.test.tsx \
  src/components/memory/ProjectModal.livrables.p153.test.tsx \
  src/components/crm/ExplicationDuScore.cible.b2003.test.tsx \
  src/components/crm/ExplicationDuScore.p152.test.tsx \
  src/components/crm/PipelineView.da.test.tsx src/components/crm/PipelineView.clavier.test.tsx \
  src/components/email/ResponseGeneratorModal.session.test.tsx \
  src/components/email/ResponseGeneratorModal.obsolete.test.tsx \
  src/components/invoices/InvoiceForm.datePaiement.p155.test.tsx \
  --maxWorkers=3 --no-cache --configLoader=runner \
  --reporter=default --reporter=junit --outputFile.junit=/tmp/diff-2-vitest.xml
npx --no-install tsc --noEmit
npm run lint
```

Les répétitions rouge/vert de ce lot peuvent être regroupées dans une commande de l'orchestrateur reprenant ces listes ; aucune automatisation persistante n'a été ajoutée ici.

## Remédiation de la relecture, passe 1

Les six constats sont confirmés et corrigés dans cet arbre. L'arbre était propre au départ. Cette passe ne fait ni `git add`, ni commit, ni push : l'orchestrateur dispose des tests et des correctifs non commités pour son rejeu contradictoire. Aucun appel réseau, fournisseur LLM ou lancement de serveur ; les données des tests sont jetables. Les preuves d'exécution sont sous `/tmp`.

Chaque régression ci-dessous a été lancée seule, avant son correctif de production. Les sélections Vitest `-t` ignorent les autres cas du fichier uniquement pendant le rouge. Aucun test existant n'a perdu d'assertion.

### Rouges constatés et corrections

Les tests backend ajoutés vivent dans `tests/test_c20_diff2_relecture.py`.

| Constat | Test lancé avant correction | Ligne d'échec recopiée | Correction |
| --- | --- | --- | --- |
| 1, P1 | `test_cascade_refusee_conserve_les_racines_et_les_plans` : deux dossiers, panne de l'index | `AssertionError: la cascade refusée a détaché une racine` | Le premier détachement de `delete_contact` reçoit désormais la session métier. Le contact, les deux projets, leurs racines, générations, plans et références survivent au refus. |
| 2, P1 | `test_purge_ne_detache_que_les_contacts_de_l_episode_a_traiter`, cas `courant` et `ancien` | `AssertionError: un contact ignoré a perdu sa racine` ; `AssertionError: une ancienne notification bloque le nouvel épisode` | Suppression du pré-détachement de toute la campagne. Le contrôle `rgpd_purge_done` utilise le début de l'épisode déjà défini pour les préavis, avant de sélectionner les personnes à anonymiser. Le détachement reste dans `anonymiser_la_personne`. |
| 3, P1 | `ProjectDeliverablesSection.changementProjet.b1877.test.tsx`, `le premier DOM de B ne contient ni les livrables ni la saisie de A` | `AssertionError: le premier DOM de B montre encore A: expected { projet: 'B', livrableA: true, …(1) } to deeply equal { projet: 'B', livrableA: false, …(1) }` | L'état porte le projet auquel il appartient et se réinitialise pendant le rendu. Un observateur dans le `useLayoutEffect` parent ne voit plus le livrable ni la saisie de A dans le DOM de B. |
| 4, P1 | `test_un_rollback_restitue_les_fragments_et_un_plan_fidele`, cinq cas initiaux : manuel, automatique, projet, cascade, fermeture | `AssertionError: le rollback SQL a perdu les fragments de recherche` | Copie paginée des points concernés avant tout effacement, avec identifiants, payloads et vecteurs. Le rollback ou la fermeture restitue ces points avant de libérer les verrous ; un commit réussi abandonne la copie. |
| 5, P1 | `ProjectDeliverablesSection.changementProjet.b1877.test.tsx`, sélection `une création ancienne`, trois cas | `Error: expect(received).toBeInTheDocument()` ; diagnostic : `Received has value: null` | Si une création d'une ancienne ouverture réussit après le retour dans le même projet, elle déclenche une nouvelle lecture. La réponse ancienne ne modifie ni la nouvelle saisie, ni l'état d'une création plus récente. |
| 6, P2 | `ExplicationDuScore.cible.b2003.test.tsx`, trois tailles, rouge sur `small` | `AssertionError: hauteur de la cible en pixels: expected 31.5 to be greater than or equal to 36` | Ajout des minima CSS de 36 px sur les deux dimensions. Le test applique les vraies préférences de police et convertit les rem avec la taille de la racine, puis prend en compte les minima. |

Les XML rouges sont `/tmp/diff-2-r1-c1-rouge.xml` à `/tmp/diff-2-r1-c6-rouge.xml` : respectivement **1, 2, 1, 5, 3 et 1 échecs**, sans erreur de collecte. Pour les reproduire sur la production sans correctifs, sélectionner les noms ci-dessus avec `pytest fichier::test` ou `vitest fichier -t 'nom du test'`.

### Appelants et risques de régression vérifiés

Après chaque correctif, les appelants ont été relus et les voisins lancés. La cascade et la suppression directe passent par `_nettoyer_et_supprimer_projet` ; les anonymisations manuelle et automatique passent par `anonymiser_la_personne`, puis ce même nettoyage. Le détachement autonome de la route de synchronisation garde son contrat. La campagne reste appelée par le démarrage et la tâche quotidienne. Côté interface, `ProjectModal` monte toujours la section des livrables, et les deux montages de l'aide au score restent dans `PipelineView` et `CRMPanel`.

Pour le constat 4, les nouveaux tests utilisent le vrai moteur Qdrant en mémoire avec des vecteurs fixes, sans encodeur. Ils relisent SQLite après l'échec, comparent exactement les points restitués et construisent le plan suivant : le fichier n'est « inchangé » que parce que ses fragments sont à nouveau présents. Trois cas complémentaires couvrent une panne après effacement partiel, un commit réussi et un rollback de deux dossiers. Ce dernier restitue **1 003 points**, dont une copie dépassant la page de 1 000 points, conserve le voisin et refuse un nouveau plan pendant la restitution. Le commit réussi ne ressuscite aucun point à la fermeture de la session.

La restitution est attendue dans l'événement de fin de transaction d'`AsyncSession`, via son pont greenlet `await_only`. Le travail Qdrant reste dans un thread ; les verrous sont rendus ensuite, même si la restitution lève. Les copies sont en mémoire et couvrent le rollback et la fermeture de session, pas un arrêt brutal du processus au milieu de l'effacement.

Les simulacres Qdrant de `tests/conftest.py`, `tests/test_routers_memory.py` et `tests/test_r5_10_rgpd.py` ont seulement reçu la méthode de copie retournant une liste vide. Leurs assertions sont conservées. Les nouvelles vérifications de restitution exercent les vraies méthodes sur le moteur en mémoire.

Pour les livrables, les lectures lentes et les créations concurrentes restent couvertes. Le test historique A/B/A conserve son assertion : aucune ancienne réponse n'est directement injectée. Les nouveaux cas font retourner l'ajout enregistré par la relecture et vérifient qu'il apparaît une seule fois, que la saisie reste intacte et que le nouvel ajout reste en cours. Les erreurs tardives de A ne contaminent toujours pas B. Pour la cible d'aide, la vérification repose sur le DOM et les CSS Tailwind compilés avec les préférences 14, 16 et 18 px ; aucune recette graphique dans un navigateur n'est revendiquée.

Les voisins immédiatement après correction passent : 38 tests backend pour le constat 1, 15 pour le constat 2, 37 tests frontend pour le constat 3, 73 tests backend pour le constat 4 avant ses compléments, 40 tests frontend pour le constat 5 et 15 pour le constat 6. Les 11 cas du nouveau fichier backend passent également après ajout des compléments. Ces exécutions se recouvrent ; elles ne sont pas additionnées au total final.

### Portes de cette passe

Exécutées le 16 novembre 2026. Les comptes sont lus dans les XML. Aucune suite complète lancée, aucun des rouges connus exclus n'a été sélectionné.

| Porte | Périmètre | Résultat vérifié | Preuve |
| --- | --- | --- | --- |
| Pytest | 24 fichiers ciblés | **152 passés, 0 échec, 0 erreur, 0 ignoré** | `/tmp/diff-2-r1.xml`, sortie 0 |
| Vitest | 7 fichiers, 3 workers maximum | **55 passés, 0 échec, 0 erreur, 0 ignoré** | `/tmp/diff-2-r1-vitest.xml`, sortie 0 |
| Ruff | `src/backend tests`, sans correction automatique | `All checks passed!`, sortie 0 | Commande ci-dessous |
| TypeScript | `tsc --noEmit` | Sortie 0, aucun diagnostic | Commande ci-dessous |
| ESLint | `npm run lint` | Sortie 0, 0 erreur, 27 avertissements dans des fichiers non modifiés | `/tmp/diff-2-r1-eslint.log` |
| Diff | `git diff --check` | Sortie 0 | Arbre de travail |

Total final : **207 tests passés**. Les avertissements React `act(...)` des voisins `ExplicationDuScore.p152.test.tsx` et `PipelineView.clavier.test.tsx` restent présents. Aucun correctif de lint extérieur aux constats.

### Commandes de rejeu

Depuis la racine de cet arbre :

```sh
PYTHONDONTWRITEBYTECODE=1 OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest \
  tests/test_c20_diff2_relecture.py tests/test_b1875_anonymisation_transactionnelle.py \
  tests/test_b1685_anonymiser_un_dossier_synchronise.py \
  tests/test_project_sync_service.py tests/test_project_sync_idempotence.py \
  tests/test_project_sync_api.py tests/test_project_sync_boucle.py \
  tests/test_retrait_complet_qdrant.py tests/test_retrait_index_service.py \
  tests/test_routers_memory.py tests/test_routers_rgpd.py tests/test_rgpd_erasure.py \
  tests/test_rgpd_purge_commit_echoue_c9.py tests/test_rgpd_purge_notifications_multiples_c9.py \
  tests/test_b1641_purge_rgpd_preavis_obligatoire.py \
  tests/test_b1651_purge_auto_alignee_sur_la_manuelle.py \
  tests/test_b1667_purge_respecte_le_consentement_renouvele.py \
  tests/test_b1670_preavis_d_un_episode_passe.py \
  tests/test_p148_trois_chemins_de_suppression.py tests/test_p148_ensemble_du_projet.py \
  tests/test_memory_purge_disque_du_dossier.py tests/test_b1178_cascade_contact_purge_le_depot.py \
  tests/test_b1503_suppression_projet_rend_ses_contacts.py tests/test_r5_10_rgpd.py \
  -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-2-r1.xml
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m ruff check --no-fix --no-cache src/backend tests
git diff --check
```

Depuis `src/frontend` :

```sh
npm_config_offline=true npx --no-install vitest run \
  src/components/memory/ProjectDeliverablesSection.changementProjet.b1877.test.tsx \
  src/components/memory/ProjectDeliverablesSection.p153.test.tsx \
  src/components/memory/ProjectModal.livrables.p153.test.tsx \
  src/components/crm/ExplicationDuScore.cible.b2003.test.tsx \
  src/components/crm/ExplicationDuScore.p152.test.tsx \
  src/components/crm/PipelineView.da.test.tsx src/components/crm/PipelineView.clavier.test.tsx \
  --maxWorkers=3 --no-cache --configLoader=runner \
  --reporter=default --reporter=junit --outputFile.junit=/tmp/diff-2-r1-vitest.xml
npm_config_offline=true npx --no-install tsc --noEmit
npm_config_offline=true npm run lint
```

Le chargement `runner` et l'absence de cache évitent toute écriture dans les dépendances partagées. Ces listes peuvent être reprises dans la commande de validation de l'orchestrateur ; aucune automatisation persistante n'est ajoutée dans cette passe.
