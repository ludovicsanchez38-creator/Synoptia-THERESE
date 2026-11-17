# Cycle 20 : lot backend-donnees

Les douze défauts ont été repris séparément : reproduction rouge, contrôle du
chemin de production, correction, puis test vert. Tout reste non commité ; aucun
ajout à l’index, commit ou dépôt annexe n’a été tenté pendant cette reprise.
Les anciens verdicts B-1804 et B-1809 sont conservés comme historique du lot,
sans nouvelle vérification dans cette reprise.

Pour mémoire, B-1804 avait été écarté après un test historique vert sur une
copie temporaire du commit `1f31c26a` : l’écriture du coût précédait le refus
budgétaire. B-1809 avait été écarté après contrôle du filtre des documents sans
périmètre et du périmètre transmis par le chat. Ces observations antérieures ne
remplacent pas une nouvelle vérification de l’état courant.

| ID | Verdict | Test (`chemin::nom`) | Rouge : ligne d’échec | Correctif |
| --- | --- | --- | --- | --- |
| B-1804 | rejeté pour la perte de coût ; test historique absent | `tests/test_c19_usage_refus_budget.py::test_usage_comptabilise_avant_erreur_de_budget` (copie temporaire de `1f31c26a`) | Sans objet | Sans objet |
| B-1809 | rejeté | `tests/test_backfill_perimetre.py::TestLaBrancheLegacyEstRestreinte::test_les_documents_sans_perimetre_sont_exclus` ; `tests/test_scope_chat.py::TestLeContexteDuChatEstCloisonne::test_une_conversation_de_projet_ne_voit_que_son_projet` | Sans objet | Sans objet |
| B-1810 | confirme | `tests/test_c20_b1810_blocage_compte.py::test_blocage_refuse_le_compte_etranger` | `:23` | non commité |
| B-1811 | confirme | `tests/test_c20_b1811_spawn_mission.py::test_spawn_en_cours_bloque_une_seconde_mission` | `:41` | non commité |
| B-1812 | confirme | `tests/test_c20_b1812_export_config.py::test_export_config_inclut_les_activites_et_livrables` | `:36` (observé `:27` avant ajout d’imports) | non commité |
| B-1813 | confirme | `tests/test_c20_b1813_preference_recherche.py::test_preference_generique_ne_laisse_pas_la_recherche_autorisee` | `:17` | non commité |
| B-1814 | confirme | `tests/test_c20_b1814_sheets_lignes.py::test_ligne_sans_identifiant_signalee_en_import_et_synchronisation` | `:30` | non commité |
| B-1815 | confirme | `tests/test_c20_b1815_anonymisation_disque.py::test_anonymisation_signale_un_depot_restant` | `:39` (observé `:33` avant ajout d’imports) | non commité |
| B-1816 | confirme | `tests/test_c20_b1816_fil_comptes.py::test_contexte_fil_limite_au_compte_du_message` | `:40` | non commité |
| B-1817 | confirme | `tests/test_c20_b1817_reouverture_restauration.py::test_restauration_signale_la_reouverture_impossible` | `:34` (observé `:31` avant ajout d’imports) | non commité |
| B-1899 | confirme | `tests/test_c20_b1899_horodatage_notifications.py::test_notifications_renvoient_des_instants_dates_en_utc` | `:23` | non commité |
| B-1900 | confirme | `tests/test_c20_b1900_avis_piece_absente.py::test_piece_absente_signalee_dans_les_avis` | `:23` | non commité |
| B-1901 | confirme | `tests/test_c20_b1901_brave_illisible.py::test_recherche_n_annonce_pas_brave_quand_la_cle_est_illisible` | `:25` | non commité |
| B-1902 | confirme | `tests/test_c20_b1902_message_identifiants.py::test_mise_a_jour_sans_renouvellement_ne_l_annonce_pas` | `:30` | non commité |

## Corrections et limites

- B-1810 : contrôle du compte pour la modification et la lecture ; un calendrier
  absent ou externe sans compte est refusé. Les calendriers locaux sans compte
  restent utilisables. Les deux cas de lecture ont été reproduits rouges avant
  correction puis vérifiés verts.
- B-1811 : la mission lancée est enregistrée, visible comme active et annulable,
  puis son état final est consigné et son inscription retirée. La garde compte
  les missions avant leur création ; la sérialisation de deux départs
  strictement simultanés n’a pas été démontrée.
- B-1812 : l’export de configuration emprunte l’export RGPD commun, qui contient
  notamment activités, livrables et périmètre des conversations. Les secrets de
  connexion structurés restent masqués ; l’ordre des messages est préservé.
  Limite préexistante : cet export JSON ne contient pas les fichiers physiques,
  seulement leurs métadonnées. La sauvegarde chiffrée est un mécanisme distinct ;
  l’exhaustivité des autres données non représentées n’a pas été établie. La
  promesse d’un export de « toutes les données » reste donc partiellement
  satisfaite malgré le test C20 devenu vert.
- B-1813 : création, modification et suppression génériques de
  `web_search_enabled` sont refusées ; la route dédiée met à jour le garde.
- B-1814 : chaque ligne non vide invalide est signalée, avec son type et son
  numéro ; les bilans partiels disent qu’ils sont incomplets.
- B-1815 : le retrait du dépôt vérifie le résultat ; l’échec vectoriel est
  distinct de zéro élément. Les purges manuelle et automatique signalent ce qui
  reste, y compris après une interruption avant vérification. Point distinct
  constaté hors anonymisation : les routes de suppression ordinaires d’un
  contact ou d’un dossier ignorent encore le résultat de cette purge disque et
  peuvent donc annoncer `deleted: true` si elle échoue. Elles n’ont pas été
  modifiées dans ce lot.
- B-1816 : le contexte du fil est filtré par le compte du message ; un compte
  étranger ou absent est refusé et un fil vide ne regroupe pas d’autres messages.
- B-1817 : la restauration vérifie les deux moteurs, la fabrique de sessions et
  une requête asynchrone avant de déclarer le succès ; une panne déclenche le
  retour arrière et indique que la base doit être vérifiée.
- B-1899 : les dates de création et de lecture des notifications sont rendues
  comme instants UTC explicites.
- B-1900 : toutes les erreurs de pièces non transmises alimentent les avis en
  mode normal comme en flux, et le contexte destiné au modèle est assaini.
  Un essai complémentaire a d’abord révélé une fuite de détail technique :
  l’avis de lecture est désormais générique et ne reprend plus l’exception.
- B-1901 : l’écran de recherche applique la même vérification de déchiffrement
  de la clé Brave que la configuration générale.
- B-1902 : le message de mise à jour des identifiants ne prétend plus qu’un
  renouvellement a eu lieu ; le message d’échec est en français.

## Tests existants et changement de comportement

Aucune assertion existante n’a été supprimée pour faire passer une régression.
`test_seance_et_echeances.py` utilisait des événements orphelins et une écriture
sans compte : ses données sont désormais rattachées à un calendrier et ses
requêtes portent le compte, sans changer ses assertions métier. La lecture
historique acceptait elle aussi les événements orphelins ; elle les refuse
maintenant par précaution.

`test_mode_cabinet.py` traitait `web_search_enabled` comme une préférence
ordinaire supprimable : ce comportement ancien contournait le garde. Le test
continue de vérifier la suppression générique avec une autre préférence ; de
nouveaux tests exigent explicitement le refus pour la recherche. Dans
`test_regression.py`, une panne de purge vectorielle ne renvoie plus zéro,
indistinguable d’une purge vide : elle renvoie `None` et l’assertion a été
adaptée. `test_b1772_cache_cle_restauree.py` fournit une session factice utilisable
et vérifie sa sonde ; `test_backup_complete.py` fournit une réouverture factice
pour sa base volontairement non SQL et continue de vérifier l’ordre des étapes.

## Portes et contrôles

- Les douze tests initiaux ont été vus rouges individuellement puis verts. Le lot
  complet de tests C20 et ses cas supplémentaires : **26 réussis, 0 échec,
  0 erreur, 0 exclu** (`/tmp/c20-backend-douze-definitif.xml`). Les 91 tests
  d’agenda, de séances et d’erreurs exécutés après le renfort de lecture
  sont verts ; 19 tests ciblant les pièces et l’injection de contexte le sont
  également après le dernier correctif.
- Porte backend complète et lecture de `/tmp/backend-donnees-pytest.xml` :
  **6 632 cas : 6 481 réussis, 11 échecs, 0 erreur et 140 exclus**. Les
  11 échecs appartiennent aux références annoncées : 7 cas de
  `tests.test_b1153_bac_a_sable_commandes` et 4 cas de
  `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches`. Aucun autre
  échec n’a été relevé dans ce rapport.
- Les 140 exclusions se répartissent ainsi : 79 sous-processus refusés par la
  garde, 47 cas demandant `RLIMIT_AS` sous Linux, 9 créations de dépôts Git
  interdites, 1 vérification Git réelle interdite, 2 générations d’image
  réelles, 1 construction de bundles PyInstaller et 1 test réseau. Les cas de
  référence `tests.test_b1191_commande_introuvable_nommee` et
  `tests.test_securite_f2_recette_deb` ont été exclus par la garde et ne sont
  donc pas mesurés ici.
- Porte Ruff : **réussie, 0 erreur**, avec
  `.venv/bin/python -m ruff check --no-fix src/backend tests`.
- Pendant la porte protégée, une garde Python refuse les connexions réseau et
  les sous-processus. Elle ne démontre pas l’absence d’un éventuel appel natif
  contournant Python. Les tests qui fabriquent un dépôt Git annexe sont exclus ;
  les tests qui exigent un vrai sous-processus sont signalés comme exclus. Les
  preuves de deux tests du cycle
  15 sont redirigées vers `/private/tmp/c20-backend-preuves/`, jamais dans
  `.app-loop/`. La garde et le plugin temporaires se trouvent dans
  `/private/tmp/c20-backend-garde/` ; le bac temporaire propre à la porte finale
  est `/private/tmp/c20-bac-porte-integrale`.
- Avant la mise en place de cette garde, les deux exécutions ciblées de B-1901
  ont atteint `GET /api/config/`, qui tente une sonde HTTP locale vers
  `127.0.0.1:9`. Aucune réponse de fournisseur n’a été observée. Les exécutions
  suivantes ont bloqué les connexions par une garde Python.
- Les tests bloqués par ces restrictions ne constituent pas une validation
  complète de leur comportement.

Pour une prochaine campagne, une commande de recette réutilisable pourrait
installer la garde, isoler les preuves et relever automatiquement chaque rouge
et son vert. Elle n’a pas été ajoutée au projet pendant ce lot.

## Remédiation de la relecture, passe 2

- **Agenda CalDAV sans compte.** La lecture et le blocage acceptent les
  calendriers locaux et CalDAV quand les deux comptes sont vides, y compris
  lorsque le client envoie `account_id=`. Un compte étranger et un calendrier
  Google sans compte restent refusés. Le test paramétré couvre les deux routes,
  les comptes vides et les refus croisés ; un fournisseur CalDAV simulé vérifie
  aussi la modification et la suppression sans compte. Rouges isolés observés
  avant correction : `E   assert 404 == 200`, à la ligne 104 en lecture et à la
  ligne 114 au blocage dans `tests/test_c20_b1810_blocage_compte.py`. Après
  correction, 82 tests d’agenda et de séances réussis.
  Limite distincte observée en relisant le parcours : une liste CalDAV renvoie
  l’identifiant distant alors que sa copie en base porte une clé dérivée. Un
  essai en mémoire avec fournisseur simulé renvoie encore 404 en lecture et au
  blocage quand on transmet l’identifiant de la liste ; les tests de cloison
  ci-dessus utilisent l’identifiant de la ligne en base. Ce décalage d’identité,
  préexistant et distinct du contrôle de compte demandé, n’a pas été corrigé.
- **Anonymisation incomplète.** L’écran lit `success` et affiche durablement le
  `message` du moteur en cas de purge incomplète. Il recharge les contacts car
  les données en base ont déjà été modifiées. Les tests couvrent dépôt restant,
  index non purgé et succès complet, avec rendu réel de la notification. Rouge
  isolé avant correction :
  `AssertionError: expected [] to deeply equal ArrayContaining{…}` dans
  `MemoryPanel.confirmations.c10.test.tsx` (deux cas). Vérification des autres
  chemins : la purge automatique B-1815 enregistre une notification distincte
  et compte les anonymisations incomplètes ; en B-1817, l’échec de réouverture
  produit une erreur HTTP 503, propagée par `request` et affichée par
  `PrivacyTab`. Un test d’écran vérifie ce dernier chemin. Les contrôles voisins
  RGPD et restauration ont réussi : 23 tests backend, 54 tests frontend et le
  test d’écran de restauration ajouté ensuite.
- **Pièce absente.** L’avis porte uniquement le nom du fichier, dans les deux
  modes du chat et dans le contexte transmis au modèle. Rouge isolé avant
  correction, pour les deux modes :
  `AssertionError: Le chemin du dossier est exposé à l'écran` dans
  `tests/test_c20_b1900_avis_piece_absente.py:50`. Les nouveaux tests contrôlent
  l’écran et le contexte du faux modèle ; 23 tests voisins ont réussi.

Porte backend, rapport `/tmp/backend-donnees-r2.xml` lu : **6 644 cas,
6 493 réussis, 11 échecs, 0 erreur et 140 exclus**. Les seuls échecs sont les
7 cas connus de `tests.test_b1153_bac_a_sable_commandes` et les 4 cas connus de
`tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches` ; aucun autre
rouge. Les exclusions comprennent 79 sous-processus interdits, 47 tests
réservés à `RLIMIT_AS` sous Linux, 9 créations de dépôt Git et une vérification
Git interdites, 2 générations d’image réelles, 1 construction de bundles et
1 test réseau. Les tests exclus ne sont pas validés. La garde et le plugin de
la campagne précédente ont été réutilisés pour bloquer les connexions et les
sous-processus, interdire les chemins protégés et isoler les preuves.
Ruff backend : **réussi, 0 erreur**.

Porte frontend complète : **949 fichiers et 4 081 tests réussis**, puis
TypeScript sans erreur et lint réussi avec **0 erreur et 27 avertissements**
sur des lignes non modifiées. Les tests ont utilisé `--configLoader runner
--no-cache --maxWorkers=3` : le `node_modules` de cet arbre est un lien vers un
autre dossier, où le mode de chargement par défaut aurait voulu écrire. Une
garde Node bloquait le réseau dans Vitest et ses workers ; le test Vite des
variables lance un fils à environnement épuré, qui ne l’hérite pas. Son code
examiné ne construit qu’un module virtuel en mémoire et ne contient pas d’appel
réseau. Cette garde ne couvre pas les appels natifs. `npx --no-install` et le
mode npm hors ligne ont empêché toute installation.

## Remédiation de la relecture, passe 3

Les six tests ont été exécutés isolément avant leur correctif. Les lignes
ci-dessous sont celles observées dans leurs rapports XML rouges ; les numéros
de ligne ont pu évoluer depuis l'ajout des autres cas. Les tests existants
n'ont pas été affaiblis.

1. **Identité CalDAV.** Le cache résout l'UID distant dans le calendrier
   concerné ; sans calendrier explicite, une correspondance ambiguë est
   refusée. Lecture, blocage, modification et suppression réutilisent l'UID de
   la liste ; le blocage reste visible après resynchronisation et modification.
   Test : `tests/test_c20_b1810_blocage_compte.py::test_parcours_caldav_depuis_la_liste_garde_le_blocage_et_le_bon_agenda`.
   Rouge initial : `E   assert 404 == 200`. Un contrôle supplémentaire a d'abord
   révélé `E   AssertionError: assert None == 'Attestation manquante'` après
   modification ; il est désormais couvert aussi.
2. **Compte d'agenda.** Modification et suppression contrôlent le compte avant
   d'appeler le fournisseur. L'écran utilise le compte du calendrier choisi,
   y compris quand un autre compte mail est sélectionné. Test :
   `tests/test_c20_b1810_blocage_compte.py::test_compte_etranger_refuse_toutes_les_operations_avant_le_fournisseur`.
   Rouge : `E   assert [404, 404, 200, 200] == [404, 404, 404, 404]`.
   Les tests d'écran dans `EventForm.test.tsx`, `EventDetail.cycle6.test.tsx`
   et `CalendarPanel.reconciliationAvantEvenements.test.tsx` ont également
   échoué avant l'adaptation de leurs appels.
3. **Chemins des pièces jointes.** Les erreurs ne transmettent que le nom du
   fichier, sans reprendre une exception contenant un chemin. Le test
   `tests/test_c20_b1900_avis_piece_absente.py::test_avis_de_fichier_ne_contient_aucun_chemin_absolu`
   parcourt les messages produits et le contexte modèle, en flux et hors flux :
   fichier lisible, fichier absent, dossier, liens, accès, contrôle de type,
   lecture, taille et fichier vide. Rouge initial :
   `E   assert (not "Ce n'est pas un fichier : /private/tmp/c20-r3-pytest-36240/test_avis_de_fichier_ne_contie2/dossier-personnel-fictif/piece.txt" or '/private/tm...r_ne_contie2' not in "Ce n'est pa...if/piece.txt"`.
   Le cas d'un accès refusé au contrôle du type a également été vu rouge avant
   d'être corrigé.
4. **Suppressions partielles.** La suppression d'un projet ou d'un contact en
   cascade rend `deleted: false` et nomme les dépôts restants si leur purge
   échoue après le commit. Les trois écrans retirent la fiche déjà supprimée
   en base et affichent durablement le message. Test backend :
   `tests/test_c20_b1815_anonymisation_disque.py::test_suppression_signale_le_depot_restant_apres_commit`.
   Rouge : `E   assert True is False`. Les tests des trois écrans et celui du
   transport API `memory.suppressionPartielle.c20.test.ts` couvrent la suite.
5. **Secrets dans l'export.** Les identifiants de connexion CalDAV et IMAP sont
   exclus ; les identifiants intégrés aux URL et paramètres sensibles sont
   masqués, y compris dans les préférences proxy structurées. Les deux routes
   sont couvertes par
   `tests/test_c20_b1812_export_config.py::test_export_masque_identifiants_des_urls_et_configurations_de_connexion`.
   Rouge : `E   assert 'identifiant-fictif' not in '{"exported_...port\\"}"}]}'`. Ce masquage vise les
   champs de connexion, préférences structurées et URL reconnues : un secret
   inscrit librement dans un texte ne peut pas être identifié de façon fiable.
6. **Mission interrompue.** Seul un événement terminal `done` consigne une fin
   réussie. Une fermeture anticipée consigne une interruption ; un générateur
   épuisé sans événement terminal émet une erreur. Test :
   `tests/test_c20_b1811_spawn_mission.py::test_spawn_interrompu_n_est_pas_consigne_comme_termine`.
   Rouge : `E   AssertionError: assert 'done' == 'cancelled'`. Une simulation
   ASGI de déconnexion pendant l'envoi et la fermeture après `done` ou `error`
   vérifient aussi les appelants.

La porte demandée est **ciblée**, sans suite complète. Rapport
`/tmp/backend-donnees-r3.xml` lu : **126 cas, 125 réussis, 0 échec, 0 erreur,
1 exclu**. L'exclusion est `tests.test_agents_depot_autorise::test_spawn_laisse_passer_le_depot_autorise` : elle exige une vérification Git réelle interdite ici et ne constitue donc pas une validation.
Ruff backend et tests : **0 erreur**. Frontend : **9 fichiers, 84 tests
réussis**, TypeScript sans erreur, lint **0 erreur et 27 avertissements** sur
des lignes préexistantes.

La recette a utilisé une base jetable et les gardes Python et Node qui bloquent
les connexions réseau ; la garde Python interdit aussi les sous-processus et
les chemins protégés. Ces gardes ne prouvent pas qu'un appel natif pourrait être
intercepté. Le chargement Vitest `runner`, sans cache et avec trois workers,
évite une écriture dans le `node_modules` partagé. Les dépendances étaient
déjà présentes et npm a été exécuté hors ligne.

## Remédiation de la relecture, passe 4

La passe est limitée aux trois constats transmis par l'orchestrateur. Les
tests des deux correctifs ont été exécutés isolément avant modification ; les
tests existants n'ont pas été affaiblis.

| Constat | Bilan | Test et rouge initial | Correctif et contrôle |
| --- | --- | --- | --- |
| B-1812, URL CalDAV | confirmé | `tests/test_c20_b1812_export_config.py::test_export_masque_url_dont_le_mot_de_passe_contient_un_delimiteur` : `E       assert False` pour l'apostrophe, avant correction. | L'autorité est analysée jusqu'à l'hôte avant de masquer les identifiants ; les préférences structurées sont traitées avant leur sérialisation JSON. Les deux exports couvrent apostrophe, guillemet, chevrons, barre oblique inverse et espace, ainsi qu'une URL dans un texte. |
| B-1811, `/spawn` interrompu | confirmé | `tests/test_c20_b1811_spawn_mission.py::test_deconnexion_avant_le_flux_libere_la_mission_et_autorise_un_nouveau_depart` : `E           fastapi.exceptions.HTTPException: 409: Une mission Atelier est déjà en cours. Attends sa fin ou annule-la avant de lancer un agent.` | La réponse ASGI ferme le flux et finalise la mission même si le générateur n'a jamais démarré. La finalisation est partagée et idempotente. Les tests couvrent ASGI 2.3 et 2.4, puis une nouvelle mission ; ils vérifient aussi qu'une déconnexion pendant l'envoi d'un événement terminal conserve son résultat. |

Le premier correctif de l'export tronquait une phrase contenant une URL puis
une adresse mail. Le test `test_export_conserve_le_texte_entre_une_url_et_une_adresse_mail`
l'a d'abord reproduit : `E       AssertionError: assert 'Voir https://example.invalid' == 'Voir https:/...ample.invalid'`.
L'analyse a été resserrée et les deux routes passent ce test.

### Résidu renvoyé au portail (nouvelle tentative d'anonymisation)

Le test isolé `test_nouvelle_tentative_conserve_le_depot_non_purge` a reproduit
le faux succès au second appel : `E       assert True is False`
(`tests/test_c20_r4_residu_anonymisation.py:27`). La conservation durable des
dépôts reste une décision du propriétaire du produit ; `rgpd.py` n'a pas été
modifié. Le test rouge a été déplacé hors de l'arbre vers
`/private/tmp/c20-r4-residu-anonymisation-87401.py` : la Corbeille demandée
était hors des droits d'écriture de cette session.

Le même diagnostic ASGI sur la mission d'écran `/api/agents/request` montre
qu'elle reste `in_progress` après une déconnexion pendant `http.response.start` :
`E           AssertionError: assert 'in_progress' == 'cancelled'`. Elle n'a pas
été corrigée dans cette passe. Le test de diagnostic a été déplacé hors de
l'arbre vers `/private/tmp/c20-r4-diagnostic-mission-ecran-87901.py`.

La porte ciblée, rapport `/tmp/backend-donnees-r4.xml` lu, compte **109 cas :
104 réussis, 0 échec, 0 erreur et 5 exclus**. Un test exige une vérification
Git réelle et quatre nécessitent un dépôt Git annexe : ils n'ont pas été
validés. Ruff sur `src/backend tests` : **0 erreur**. La recette utilise une
base jetable et une garde Python contre les connexions réseau, les
sous-processus et les chemins protégés ; elle ne prouve pas l'interception
d'éventuels appels natifs. Aucune suite complète ni modification frontend n'a
été lancée. Les changements restent non commités.

## Remédiation des relectures 4 et 5 (écrite par l'orchestrateur)

Constats : le masquage des URL prenait un port (`:443`) pour le début d'un
identifiant dès qu'une adresse e-mail suivait sur la même ligne (relecture 4),
puis encore quand une ponctuation suivait le port ; deux clés distinctes
devenaient identiques une fois masquées et une entrée disparaissait ; un JSON
réécrit perdait la précision de ses nombres (relecture 5). Entre les deux, la
revue de sécurité automatique des commits a relevé une clé JSON en double
rendue telle quelle, une récursion non bornée et un paramètre de connexion
laissé en clair après une URL imbriquée. Deux passes de Codex ayant échoué sur
cette fonction, elle a été réécrite à la main.

Règles retenues (`_masquer_urls_export`, `src/backend/app/routers/data.py`) :

1. Une chaîne qui est un JSON (objet ou liste) est lue fidèlement : nombres
   gardés en texte, paires dans l'ordre, clés en double conservées. Sans rien
   à masquer elle ressort telle quelle, à l'octet près. Sinon elle est réécrite
   depuis ce qui a été lu : seul l'espacement peut changer, les nombres
   ressortent au caractère près. La valeur d'une préférence suit la même voie.
2. Dans un texte, l'autorité d'une URL s'arrête au premier `/`, `?`, `#` ou à
   la première espace ; tout ce qui y précède le dernier `@` est un
   identifiant et part, quels que soient ses caractères (lecture de la
   RFC 3986).
3. Une espace ne prolonge l'identifiant que dans un cas étroit : ce qui la
   précède ne peut pas être un hôte suivi de son port (`nom:secret` ; un port
   suivi d'une ponctuation reste un port), et le mot qui la suit porte
   lui-même le `@`.
4. Une URL passée en paramètre d'une autre est lue de la même façon, par la
   même boucle et sans récursion (cinq mille niveaux testés).
5. Les paramètres de connexion (`password=`, `access_token=`…) sont masqués
   dans une seconde passe, sur toute l'étendue de l'URL après son premier `?`
   ou `#`. Hors identifiants et valeurs masquées, le texte sort caractère pour
   caractère (casse du schéma, `?` final).
6. Les clés sont masquées comme les valeurs. Deux clés distinctes qui se
   confondent une fois masquées restent deux entrées : la seconde reçoit un
   suffixe ` (2)`. Une clé que le masquage ne change pas garde son nom.
7. Un JSON trop imbriqué pour être parcouru est masqué comme un texte ; s'il
   s'agit de la valeur d'une préférence, elle sort `[REDACTED]` en entier (un
   secret rangé sous une clé de connexion n'aurait pas été atteint).

Tests : `tests/test_c20_b1812_export_config.py`, 74 tests dont 56 ajoutés par
ces passes, sur les deux routes d'export pour chaque reproduction des
relecteurs. Rouges constatés avant chaque correctif, dans l'ordre des commits :
5, 3, 4, 21, 2, puis 2. 265 tests voisins de l'export verts ; ruff propre ; mypy
du fichier inchangé (23).

Limites connues, non couvertes :

- un mot de passe saisi tel quel avec PLUSIEURS espaces, ou avec une espace
  et qui commence par des chiffres (`nom:12 34@hôte`). Choix assumé entre
  deux risques opposés, relevés l'un par la relecture (un texte légitime
  tronqué jusqu'à l'adresse e-mail suivante), l'autre par la revue de sécurité
  (ce mot de passe laissé en clair) : les deux demandent une URL invalide, la
  règle étroite garde le texte ;
- un mot de passe contenant `/`, `?` ou `#` non encodés : aucune bibliothèque
  ne lit une telle URL comme l'utilisateur l'entend ;
- une URL encodée en pourcentage passée en paramètre d'une autre ;
- la valeur d'un paramètre de connexion qui contient un guillemet, une
  apostrophe, un chevron ou une barre oblique inverse : l'URL s'arrête là dans
  un texte, la fin de la valeur reste ;
- la règle 2 lit `https://site.invalid;a@b.invalid` (sans espace) comme une
  URL à identifiants, ce qu'elle est selon la RFC : le texte avant le `@`
  part ;
- la règle 3 lit `https://hôte:mot suite@domaine` comme un identifiant coupé
  par une espace (`mot` n'étant pas un port) ;
- les colonnes JSON que l'export décode avant de les masquer (`extra_data`…)
  passent par le lecteur JSON ordinaire, antérieur à ce lot : leurs nombres
  décimaux très longs y sont arrondis comme avant.
