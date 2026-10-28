# Lot 2 : fonctions quotidiennes de THÉRÈSE 0.82

Rapport du 28 octobre 2026. Branche `boucle/c22b-fonctions`, base `45be2f16`.
Travail réalisé dans l’arbre courant `run-dq/wt-c22b` uniquement.
Aucun chemin de sortie `-o` ne figurait dans la demande reçue ; ce rapport est donc enregistré à la racine de cet arbre.

Sources initiales lues : synthèse de l’audit du 27 octobre et rapports A3, A4, A7 dans `~/staging/therese-audit-beta-2026-10-27/`.

## État des cinq points

### 1. Recherche web : fait

Commit `7bea9031` : `fix(chat): répondre après la recherche web confirmée (B-1319)`.

Après confirmation, les résultats sont transmis au modèle pour rédiger une réponse à la question d’origine, avec des liens vers les sources. La question est conservée avec la confirmation pour éviter de répondre à une question arrivée entre-temps. Les résultats restent des données d’outil, avec une consigne explicite de ne pas suivre leurs instructions éventuelles. Cette continuation n’autorise aucune nouvelle action.

La réponse est enregistrée dans la conversation, les jetons sont comptabilisés et le contrôle de budget est appliqué. Un échec de rédaction produit un message explicite. L’annulation ne lance ni recherche ni modèle.

Régression : les cas « réponse après confirmation » et « question conservée » échouaient avant le correctif. Les trois tests de `test_c22b_recherche_confirmee.py` passent. Avec `test_chat_tool_confirmation.py` et `test_tool_confirmations.py`, le passage ciblé comptait 25 réussites.

Non vérifié : qualité de la synthèse et des citations avec un fournisseur réel. Les résultats web et le modèle sont simulés dans les tests ; aucun modèle payant ni moteur de recherche de l’application n’a été appelé.

### 2. PDF scanné joint au chat : fait par message explicite

Commit `1aade809` : `fix(documents): signaler les PDF sans texte dans le chat (B-1213)`.

Un PDF sans texte exploitable ne devient plus « Prêt » après une indexation vide. Le serveur et l’écran signalent l’absence de texte. Le contexte du chat conserve également un avis de lecture explicite, y compris pour une pièce déjà jointe. Le message propose une version avec texte sélectionnable ou OCR, ou des images JPG/PNG avec un modèle capable de les lire.

Les pages faites de blancs sont ignorées ; la limite de pages d’un PDF vide ne crée plus à elle seule un faux contenu lisible. Aucun moteur OCR n’est ajouté ou installé dans ce lot. La solution retenue est la seconde possibilité autorisée dans la demande.

Régression : les trois nouveaux tests échouaient avant correction. Passage ciblé de `test_c22b_pdf_sans_texte.py`, `test_chat_contexte_fichier_non_bloquant.py` et `test_files_indexation_remediation.py` : 10 réussites. `ChatInput.indexation.test.tsx` : 9 réussites.

Non vérifié : OCR local et recette manuelle dans l’application de bureau avec un document scanné réel. Les tests produisent des PDF sans couche texte exploitable.

### 3. Adresse de réponse des courriels : fait

Commit `dc5b776a` : `fix(messagerie): répondre aux adresses Reply-To et les montrer (B-1296)`.

Les fournisseurs IMAP et Gmail lisent les adresses `Reply-To`, y compris plusieurs destinataires et les noms contenant une virgule. Elles traversent le cache, l’API et le formulaire de réponse. Une ancienne entrée de cache sans information sur cet en-tête est relue avant d’autoriser « Répondre ».

« Répondre », « Répondre à tous » et l’utilisation d’une réponse générée privilégient ces adresses. Le repli vers l’expéditeur s’applique quand l’absence de `Reply-To` a été vérifiée. « Répondre à tous » conserve les copies, déduplique les destinataires et exclut le compte courant.

La fiche du message et la confirmation d’envoi montrent l’adresse de réponse ; la confirmation continue de montrer les destinataires effectifs. Aucun envoi réel n’a été effectué.

Régression : les trois cas initiaux de lecture et de cache échouaient avant correction ; un quatrième cas vérifie la migration idempotente du cache. Les quatre passent. Les tests ciblés des fournisseurs IMAP/SMTP, Gmail et du marquage Alembic passent également. Côté interface, 24 tests passent dans les cinq fichiers de messagerie et de carte de confirmation listés plus bas.

Non vérifié : connexion à une boîte réelle et livraison d’un message. Migration ajoutée : `c22b01replyto`.

### 4. CalDAV et iCloud : écritures simples et lecture des récurrences faites

Commits :

- `0c2c576f` : `fix(agenda): écrire dans les calendriers CalDAV et iCloud (B-1307)`.
- `ec958ed4` : `fix(agenda): conserver les occurrences dans la lecture et les rappels (B-1308, B-1309)`.

Création, modification et suppression utilisent désormais l’identifiant distant du calendrier CalDAV. L’écran conserve l’identifiant local. Les confirmations existantes sont conservées et exercées par les tests d’interface ; la protection contre une modification concurrente reste en place.

À la lecture, tous les composants `VEVENT` renvoyés par une ressource développée sont conservés. Chaque occurrence possède un identifiant distinct. La pagination ne tronque plus silencieusement les résultats après le premier lot. Le statut annulé et les journées entières sont conservés. Le cache est réconcilié dans la fenêtre effectivement relue et les occurrences participent aux rappels du lendemain.

Les séries locales anciennes sont aussi développées pour la lecture bornée et les rappels. Les contrôles de fuseau de Paris et de dédoublement des rappels ont été rejoués. Aucun code de l’accueil n’a été modifié.

Régression : le test d’écriture avec identifiant local échouait avant correction ; les trois premiers cas de lecture des séries et de rappel échouaient aussi. Les cinq tests C22b actuels passent. Les régressions voisines de CalDAV, des récurrences locales et des notifications passent. Les tests d’interface vérifient la confirmation avant création, modification et suppression.

Simulation utilisée : calendrier DAV et ressources iCalendar en mémoire, avec le vrai `CalDAVProvider` appelé par les routes FastAPI. Les tests couvrent l’enchaînement création, modification avec `If-Match`, suppression, lecture de plusieurs occurrences, pagination et cache. Le transport HTTP DAV, l’authentification et un compte iCloud réel restent à vérifier.

**Question produit, sans réponse reçue :** lors de l’édition ou de la suppression d’une occurrence, faut-il agir sur cette occurrence, sur toute la série ou proposer les deux ? Les occurrences sont lisibles, mais leur modification et leur suppression sont explicitement bloquées dans l’écran et l’API. L’écriture des événements simples fonctionne. L’édition des séries n’est pas implémentée dans ce lot.

Autres limites : les rappels CalDAV utilisent le cache des fenêtres déjà synchronisées. La modification du contenu de l’accueil, réservée à l’autre lot, n’a pas été entreprise.

### 5. Identité des parties et mentions des factures directes : fait, avec limites historiques

Commit `53e699b2` : `fix(factures): compléter l’identité des parties et les mentions de livraison`.

La fiche officielle [Service Public, Mentions obligatoires sur une facture](https://www.service-public.gouv.fr/entreprendre/vosdroits/F31808), vérifiée le 11 août 2026 et consultée le 28 octobre, a servi à vérifier les mentions d’identité : nom des parties, adresses, adresse de facturation distincte, forme juridique et capital d’une société, mention EI et référence du bon de commande lorsqu’il existe. Les accès directs aux versions de L441-9 et au lien Légifrance fourni par cette fiche ont échoué avec un refus d’accès. Je ne prétends donc pas avoir obtenu le texte consolidé intégral de L441-9 à cette date.

Le [BOFiP, BOI-TVA-DECLA-30-20-20-10, paragraphe 160](https://bofip.impots.gouv.fr/bofip/140-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-10-20131018) précise que la date d’opération doit figurer lorsqu’elle diffère de l’émission et qu’elle est déterminée. Le champ de date est donc proposé sans date déduite automatiquement, conformément au correctif demandé par l’audit.

Changements réalisés :

- Profil émetteur : forme juridique, capital déclaré en euros et adresse de facturation distincte, conservés lors de la sauvegarde et de la relecture.
- PDF : mention EI accolée au nom ; forme juridique et capital ; deux adresses si nécessaire.
- Brouillon : adresse du destinataire modifiable, adresse de facturation distincte, date de livraison ou de prestation et numéro de bon de commande.
- Conservation de ces champs lors des conversions ; protection contre leur modification, y compris par `null`, après émission.
- Refus de générer le PDF si l’identité de l’émetteur est incomplète ou si l’adresse du destinataire manque. Le capital est contrôlé pour les formes usuelles de société couvertes par le code.
- Migration `c22b02facture` : nouveaux champs facultatifs, sans inventer de valeurs pour les anciennes pièces.

Les pénalités et l’escompte de B-1338 sont inchangés. Leurs tests ont été rejoués.

Régression : les trois tests initiaux échouaient avant correction. Ils lisent notamment le vrai PDF produit, vérifient EI, capital, adresses, date et bon de commande, puis la conservation et l’immuabilité des données. Un quatrième test, également rouge avant sa correction, vérifie le message destiné aux anciennes pièces émises sans adresse. Les quatre passent.

Les tests existants dont les jeux de données se disaient complets ont reçu les mentions désormais requises. Un passage ciblé de 75 tests a vérifié les avoirs, montants établis, dates parisiennes d’émission, échéances et autres comportements des PDF. Les tests de migration, du profil, du routeur factures, des régimes de TVA et du générateur passent. Les 29 tests ciblés du formulaire et du profil passent, ainsi que le typage TypeScript.

**Question sur les anciennes pièces :** comment traiter une facture déjà émise dont l’adresse client manque ? Le nouveau contrôle refuse sa régénération ; l’interface explique qu’elle est figée et invite à consulter le PDF d’origine s’il a été conservé. Aucune ancienne pièce n’est réécrite. La procédure de rectification ou de reprise historique reste à décider. Le contrôle ajouté porte sur la génération du PDF ; le changement de statut d’une pièce ne constitue pas un contrôle juridique complet.

Non vérifié ou hors de ce correctif : cas particuliers d’identité juridique autres que les formes usuelles, opposition d’un client particulier à l’adresse, mentions sectorielles et réforme de la facture électronique. Ce travail corrige les lacunes d’identité relevées par l’audit ; il ne constitue pas une certification de conformité de toute facture.

## Commandes et vérifications ciblées

Toutes les commandes lourdes ont été lancées avec `nice -n 10`. Les chemins Python ci-dessous sont relatifs à la racine ; Vitest et TypeScript sont lancés depuis `src/frontend`. Aucun ensemble complet de tests ni e2e complet n’a été exécuté.

Passage final des nouveaux tests :

```text
nice -n 10 .venv/bin/pytest -q
  tests/test_c22b_recherche_confirmee.py
  tests/test_c22b_pdf_sans_texte.py
  tests/test_c22b_reply_to.py
  tests/test_c22b_caldav_ecriture.py
  tests/test_c22b_recurrences.py
  tests/test_c22b_identite_facture.py
```

Résultat : **19 réussites, code 0**. Pour obtenir le détail des échecs et ce compteur malgré la sortie immédiate du `conftest.py`, certains passages ont utilisé un petit lanceur `pytest.main` avec un greffon d’affichage, sans modifier les fixtures communes.

Autres fichiers ou sélections Python exécutés, tous réussis après correction :

| Domaine | Fichiers ou sélections |
| --- | --- |
| Recherche | `test_chat_tool_confirmation.py`, `test_tool_confirmations.py` |
| Documents | `test_chat_contexte_fichier_non_bloquant.py`, `test_files_indexation_remediation.py` |
| Courriel | `test_services_imap_smtp_provider.py`, `test_services_gmail_service.py`, `test_alembic_stamp.py` |
| Agenda | `test_caldav_jeton_de_version.py`, `test_caldav_rappels_participants_statut.py`, `test_r4_3_caldav.py`, `test_b1110_agenda_local_recurrent.py`, `test_c20f_notifications_paris.py` |
| Factures | `test_routers_invoices.py`, `test_invoice_pdf_francais.py`, `test_b1338_penalites_legales.py`, `test_invoice_currency_migration.py`, `test_billing_profile_cache.py`, `test_b1445_regime_tva_par_la_route.py`, `test_b1616_pdf_relit_le_profil_si_cache_vide.py` |
| PDF et pièces établies | `test_p154_avoir_et_sa_facture.py`, `test_c20e_montants_etablis.py`, `test_b1164_emission_paris.py`, `test_frontiere_facturation_agenda.py`, `test_b1760_echeance_mentions.py` |
| Sélections PDF dans des fichiers plus larges | `test_regression_facturation_agenda.py::TestPdfDeFacture` ; `test_f1_coherence_des_couches.py::TestUnSeulMontantATraversLesCouches::test_le_pdf_imprime_le_meme_montant` ; `test_f1_coherence_des_couches.py::TestUnSeulSeparateurDecimalDansLeDocument` ; `test_lot5_frontiere_et_bornes.py::TestB468LePdfPorteLeStatutEffectif` |

Interface : commande `nice -n 10 ./node_modules/.bin/vitest run <fichiers ciblés> --maxWorkers=1`, avec les fichiers suivants sous `src/components/` :

| Domaine | Fichiers | Résultat |
| --- | --- | --- |
| Documents | `chat/ChatInput.indexation.test.tsx` | 9 réussites |
| Courriel | `email/EmailDetail.replyTo.test.tsx`, `email/EmailDetail.test.tsx`, `email/EmailDetail.transfertHtml.test.tsx`, `email/EmailCompose.test.tsx`, `chat/ToolConfirmationCard.cc.b1293.test.tsx` | 24 réussites |
| Agenda | `calendar/EventForm.test.tsx`, `calendar/EventDetail.da.test.tsx` | 7 et 8 réussites au dernier passage de chaque fichier |
| Factures et profil | `invoices/InvoiceForm.test.tsx`, `settings/ProfileTab.da.test.tsx`, `settings/SettingsModal.confirmationProfil.test.tsx` | 29 réussites |

Contrôles finaux :

- `nice -n 10 ./node_modules/.bin/tsc --noEmit --incremental false` : réussi.
- Ruff sur les fichiers Python modifiés depuis `45be2f16` : réussi après rangement des imports.
- `git diff --check` : réussi.

Les échecs intermédiaires ont servi à reproduire les défauts ou à ajuster les données des tests à la nouvelle identité requise. Une invocation Python avec un nom de fichier B-1338 erroné n’a collecté aucun test ; elle a été corrigée avec `test_b1338_penalites_legales.py`. Aucun résultat de cette invocation n’est compté comme réussi.

Commit complémentaire `b2121feb` : `style(lot2): ordonner les imports des correctifs`. Il ne change que les imports ; les 19 régressions ont été rejouées après ce rangement.

## Limites de la livraison locale

Les portes complètes restent à rejouer par Syn, ainsi que la recette bureau et les connexions réelles. Aucun push, tag, publication, déploiement, redémarrage de service, envoi de mail ou de message n’a été effectué. Les fonctionnalités de l’autre lot, notamment accueil, aide, ouverture des fichiers locaux et reprise des copies, n’ont pas été modifiées.
