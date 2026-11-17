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

## Remédiation des relectures 4 à 7 (écrite par l'orchestrateur)

Constats successifs sur le masquage des URL exportées : un port pris pour le
début d'un identifiant quand une adresse e-mail suivait (relecture 4), y
compris derrière une ponctuation, des clés confondues une fois masquées et des
nombres altérés par la réécriture d'un JSON (relecture 5), puis du HTML
tronqué quand une adresse e-mail suit un lien, une URL imbriquée qui absorbait
les paramètres suivants et un point-virgule qui coupait une valeur secrète
(relecture 6), enfin un mot de passe commençant par des chiffres suivis
d'une virgule resté en clair dans un champ qui n'est qu'une URL, et une
espace avant l'URL d'un attribut HTML (relecture 7). Entre-temps la revue de
sécurité automatique des commits a
relevé une clé JSON en double rendue telle quelle, une récursion non bornée,
un paramètre de connexion laissé en clair après une URL imbriquée et une
préférence trop imbriquée rendue brute. Deux passes de Codex ayant échoué sur
cette fonction, elle a été réécrite à la main.

Principe retenu après la relecture 6 : **ne jamais altérer un texte sans un
indice d'identifiant**. L'autorité d'une URL est lue au plus étroit ; on ne
lit au-delà que sur un indice précis.

Règles (`_masquer_urls_export`, `src/backend/app/routers/data.py`) :

1. Une chaîne qui est un JSON (objet ou liste) est lue fidèlement : nombres
   gardés en texte, paires dans l'ordre, clés en double conservées. Sans rien
   à masquer elle ressort telle quelle, à l'octet près. Sinon elle est réécrite
   depuis ce qui a été lu : seul l'espacement peut changer. La valeur d'une
   préférence suit la même voie.
2. Un champ qui est une URL entière (aucune espace : adresse d'agenda, hôte de
   messagerie, valeur d'un champ JSON) est lu comme une bibliothèque d'URL le
   lit : son autorité va jusqu'au premier `/`, `?` ou `#`, et tout ce qui y
   précède le dernier `@` est un identifiant, quels que soient ses caractères.
3. Dans un texte, l'autorité d'une URL s'arrête à tout ce qui ne peut pas
   appartenir à un nom d'hôte : `/`, `?`, `#`, espace, guillemet, apostrophe,
   chevron, barre oblique inverse, virgule, point-virgule, parenthèse,
   accolade. Ce qui y précède le dernier `@` est un identifiant et part. Sans
   autre indice l'URL s'arrête là, quoi qu'il y ait derrière : lien HTML,
   Markdown, JSON ou dictionnaire dans un texte restent intacts.
4. Dans un texte, on ne lit au-delà du séparateur que sur deux indices : ce
   qui précède ne peut pas être un hôte suivi de son port (`nom:secret` ; un
   port suivi d'un point reste un port), ou bien l'URL s'arrête sur un
   guillemet que rien n'a ouvert et qu'une lettre ou un chiffre suit aussitôt
   (un attribut HTML ou un champ JSON se ferment sur `>`, une virgule ou une
   espace). Le `@` doit alors se trouver dans le mot qui suit.
5. Une URL passée en paramètre d'une autre est lue de la même façon, par la
   même boucle et sans récursion ; son autorité s'arrête en plus au séparateur
   de paramètres (`&`, `;`) : elle n'absorbe pas la suite de l'URL principale.
6. Les paramètres de connexion (`password=`, `access_token=`…) sont masqués
   dans une seconde passe, sur toute l'étendue de l'URL après son premier `?`
   ou `#` ; un nom de paramètre est reconnu après `?`, `&`, `#` ou `;`, et
   la valeur d'un secret va jusqu'au `&` ou au `#` suivant, point-virgule
   compris. Hors identifiants et valeurs masquées, le texte sort caractère
   pour caractère.
6 bis. Dans un texte, l'URL dont on masque les paramètres s'arrête où elle
   s'arrête vraiment : avant la ponctuation finale de la phrase, et avant un
   fermant qu'elle n'a pas ouvert (`[texte](https://…)`, mais pas
   `Page_(test)`), un accent grave ou une barre verticale, à condition que la
   suite ait la forme d'un texte (plus que de la ponctuation derrière les
   fermants, un accent grave qui termine un code, une barre dans une ligne de
   tableau qui se termine par une barre) et qu'elle ne porte aucun paramètre
   de connexion. Sinon ces caractères font
   partie de l'URL et tout est masqué : ce qui suit la fin retenue n'étant
   plus masqué, on ne raccourcit jamais dans le doute. Dans un attribut HTML, `&amp;` sépare les paramètres
   et une entité numérique (`&#45;`) fait partie de la valeur. Le guillemet
   ouvrant d'un attribut est reconnu même séparé de l'URL par une espace.
7. Les clés sont masquées comme les valeurs. Deux clés distinctes qui se
   confondent une fois masquées restent deux entrées : la seconde reçoit un
   suffixe ` (2)`.
8. Un JSON trop imbriqué pour être parcouru est masqué comme un texte ; s'il
   s'agit de la valeur d'une préférence, elle sort `[REDACTED]` en entier.
9. Le coût est linéaire : les bornes d'une suite de caractères sans espace ne
   sont calculées qu'une fois, même si elle contient vingt mille URL (une
   première version, quadratique, mettait plus de deux minutes sur 640 000
   caractères ; mesuré ensuite à 0,05 s).

Tests : `tests/test_c20_b1812_export_config.py`, 150 tests dont 132 ajoutés par
ces passes ; chaque reproduction des relecteurs est rejouée sur les deux
routes d'export. Rouges constatés avant chaque correctif, dans l'ordre des
commits : 5, 3, 4, 21, 2, 2, 14, 4, 9, 3, puis 8 (ces huit derniers tirés des sondes d'une huitième relecture interrompue faute de crédits Codex). Six cas de HTML et de texte et quatre
cas de charge ajoutés par contre-épreuve de l'orchestrateur. 341 tests voisins
de l'export verts ; ruff propre ; mypy du fichier inchangé (23).

Limites connues, non couvertes (chacune demande une URL que les lecteurs
d'URL ne lisent pas comme l'utilisateur l'entend) :

- DANS UN TEXTE seulement (un champ qui est une URL entière n'est pas
  concerné) : un mot de passe saisi tel quel qui contient un séparateur de
  texte autre qu'un guillemet (virgule, parenthèse, espace…) et dont ce qui le précède a
  la forme d'un hôte, c'est-à-dire un nom d'utilisateur seul ou un début tout
  en chiffres (`nom:12 34@hôte`, `nom:42,secret@hôte`) ; ou plusieurs espaces.
  Choix assumé entre deux risques opposés : lire au-delà d'un séparateur sans
  indice tronquait tout lien HTML suivi d'une adresse e-mail (relectures 6
  et 7) ;
- dans un texte, un mot de passe qui contient à la fois un `@` et un
  séparateur de texte (`nom:secret@2026,suite@hôte`) : seule la partie avant
  le premier `@` part ;
- un secret passé en paramètre dont le dernier caractère est une ponctuation
  de phrase (`?token=abc!` dans une phrase) : ce dernier caractère reste ;
  de même un secret qui se termine par un fermant ou un accent grave suivi
  de ponctuation, ou qui contient une barre verticale dans une ligne de
  tableau : ce qui suit est pris pour du texte ;
- dans un texte, une URL collée à une adresse e-mail par un caractère de nom
  d'hôte (`https://site.invalid.contact@site.invalid`, espace oubliée) est lue
  comme la RFC la lit : ce qui précède le `@` part ;
- un champ entier de la forme `https://hôte,contact@domaine` (sans espace) est
  lu comme une URL à identifiants, ce qu'il est pour toute bibliothèque ;
- un mot de passe contenant `/`, `?` ou `#` non encodés, ou, dans une URL
  passée en paramètre d'une autre, `&` ou `;` ;
- une URL encodée en pourcentage passée en paramètre d'une autre ;
- la valeur d'un paramètre de connexion qui contient un guillemet, une
  apostrophe, un chevron ou une barre oblique inverse : l'URL s'arrête là dans
  un texte ;
- `https://hôte:mot suite@domaine` hors guillemets (`mot` n'étant pas un
  port) est lu comme un identifiant coupé par une espace ;
- les colonnes JSON que l'export décode avant de les masquer (`extra_data`…)
  passent par le lecteur JSON ordinaire, antérieur à ce lot : leurs nombres
  décimaux très longs y sont arrondis comme avant.

## Remédiation de la relecture, passe 6

Les corrections restent limitées aux trois constats transmis et aux règles
retenues en P-173. Seuls `src/backend/app/routers/data.py`, le nouveau fichier
`tests/test_c20_r6_export_config.py` et ce bilan sont modifiés. Les 150 tests
de `tests/test_c20_b1812_export_config.py` sont inchangés. Aucun ajout à
l'index, commit, rebase, dépôt annexe ou bundle ; aucun fichier de référence
n'a été réintégré dans l'arbre.

1. **P1, paramètres d'un champ URL entier.** Après le retrait des identifiants,
   le masquage des paramètres porte sur toute l'URL, même lorsqu'un autre
   paramètre contient une apostrophe, un guillemet, un chevron ou une barre
   oblique inverse. Les espaces extérieurs au champ restent présents.
   `test_export_masque_les_parametres_sur_tout_le_champ_url` ajoute 20 cas :
   les deux routes, cinq délimiteurs, avant et après le paramètre secret ;
   champs agenda, messagerie et préférence JSON. Rouge isolé avant correction :
   **10 échecs et 10 réussites**, dont
   `E       AssertionError: assert 'https://agen..._token=FICTIF' == 'https://agen...en=[REDACTED]'`
   (`/tmp/backend-donnees-r6-url-rouge.xml`). Une contre-épreuve a révélé que
   mon premier correctif absorbait les espaces finaux :
   `test_masquage_d_une_url_entiere_conserve_les_espaces_autour` a échoué seul
   avec `E       AssertionError: assert ' \thttps://a...en=[REDACTED]' == ' \thttps://a...REDACTED]\n  '`.
   La borne du champ exclut maintenant ces espaces, comme auparavant.
2. **P1, recherche quadratique.** Les deux passes partagent un parcours des
   suites de caractères autorisés dans un schéma. Chaque suite n'est lue
   qu'une fois ; sa fin doit porter `://` avant de rechercher une initiale
   à une frontière de mot. Les règles de fin d'autorité et d'URL restent
   identiques. `test_recherche_des_urls_reste_lineaire_sur_des_suffixes_a_points`
   reproduit les tailles 64 000 et 128 000, avec l'URL du relecteur et sans
   URL pour exercer également la seconde passe. Il borne le temps CPU à
   `3 * temps_petit + 0,02 s` et à 5 s, pour isoler la mesure de la charge
   partagée. Les deux rouges isolés ont donné
   `E       AssertionError: Coût non linéaire : 4.285s puis 17.218s` et
   `E       AssertionError: Coût non linéaire : 8.788s puis 34.870s`
   (`/tmp/backend-donnees-r6-charge-rouge.xml`). Ils passent après correction,
   ainsi que les quatre charges existantes. Une comparaison temporaire de
   10 000 chaînes a aussi retrouvé les mêmes bornes de schéma que l'ancienne
   expression régulière.
3. **P2, les trois expressions de typage signalées.** `morceaux` est une
   `list[str]`, le tri emploie `col(Message.created_at)` et `col(Message.id)`,
   et le résultat masqué de l'assembleur est annoté `dict[str, Any]`.
   Aucun `cast` ni `type: ignore`. Le test isolé
   `test_mypy_n_ajoute_aucune_erreur_dans_les_trois_expressions_corrigees`
   charge les modules de cet arbre avec mypy 1.19.1, sans cache. Il a d'abord
   relevé les trois diagnostics, puis passe :
   `E       AssertionError: src/backend/app/routers/data.py:169: error: Need type annotation for "morceaux" (hint: "morceaux: list[<type>] = ...")  [var-annotated]` ;
   `E         src/backend/app/routers/data.py:563: error: Argument 1 to "order_by" of "GenerativeSelect" has incompatible type "datetime"` ;
   `E         src/backend/app/routers/data.py:800: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]`
   (`/tmp/backend-donnees-r6-typage-rouge.xml`).

**La porte mypy globale reste non conforme : 927 erreurs, contre 923 à
l'intégration.** La commande de CI, avec `--no-incremental --cache-dir=/dev/null`,
mesurait 929 erreurs avant cette passe et en mesure 927 après. La comparaison
à froid avec les sources de référence lues uniquement en mémoire confirme
923 contre 927, sans réécriture de fichier de référence dans l'arbre. Les
quatre diagnostics nets restants étaient déjà présents avant cette passe :
`crm.py:81` (`_signaler_ligne_invalide`, `type-arg`), `calendar.py:1131`
(`_evenement_en_cache`, `union-attr`), `agents.py:787` (`__call__`,
`no-untyped-def`) et `_valeur_de_preference_exportable` dans `data.py`
(`no-any-return`, ligne 499 lors de la mesure, 500 après le dernier ajustement).
Le diagnostic de `rgpd_auto.py:45` change de libellé (`int` vers `int | None`)
sans changer le nombre. Ces expressions sortent des trois constats autorisés
et n'ont pas été modifiées. Les journaux sont dans
`/tmp/backend-donnees-r6-mypy-{avant,apres,integration,memoire}.log`.

Les appelants ont été relus : chaînes et clés de JSON, préférences
structurées, assembleur commun, délégation de `/api/config/export` et tri des
messages. Après chaque correctif, les tests ajoutés, les 150 cas existants
et les premiers voisins de l'export ont été rejoués.

Porte finale ciblée, **rapport `/tmp/backend-donnees-r6.xml` lu : 249 tests
réussis, 0 échec, 0 erreur, 0 exclu**, dont 24 nouveaux cas. Fichiers :
`test_c20_r6_export_config.py`, `test_c20_b1812_export_config.py`,
`test_routers_data.py`, `test_routers_config.py`,
`test_export_config_par_conversation.py` et `test_data_export_profil_rgpd.py`.
Options : `OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest
<fichiers> -q -p no:cacheprovider --timeout=120
--junitxml=/tmp/backend-donnees-r6.xml`. Ruff sur `src/backend tests` :
**0 erreur** avec `--no-fix`. Aucune suite complète ni porte frontend.

La recette utilise uniquement une base jetable dans `/tmp`, une garde Python
contre les connexions réseau et les chemins interdits, et aucun fournisseur
LLM. Le sandbox refuse aussi l'écriture dans les sockets Unix : le réveil
interne de la boucle asyncio du lanceur temporaire utilise donc un tube local.

## Remédiation de la relecture, passe 7

Seuls les deux écarts transmis par l'orchestrateur sont traités. Les réserves
acceptées restent intactes. Aucun fichier n'a été repris depuis une autre
branche ou un autre lot. Les seules modifications hors des cinq modules
signalés, de leurs tests et de ce bilan sont le recalage du cliquet aux deux
endroits explicitement autorisés. Aucun ajout à l'index ni commit.

1. **Typage global.** `ReponseMission.__call__` porte les types ASGI
   `Scope`, `Receive`, `Send` et le retour `None`. Les deux dictionnaires de
   `_signaler_ligne_invalide` sont des `dict[str, Any]`. La préférence rendue
   passe par une valeur annotée `str`, conforme à `Preference.value`
   (`src/backend/app/models/entities.py:341`). Le résultat de la purge est
   annoté `int`, conforme à `QdrantService.async_delete_by_entity`
   (`src/backend/app/services/qdrant.py:763`) ; le retour `None` en cas
   d'échec reste inchangé. Le cache d'agenda écarte le calendrier `None`
   dans une vraie branche avant de lire `provider`, sans `assert`.
   Aucun `cast`, `type: ignore` ni changement de comportement.

   Cinq cas AST dans `tests/test_c20_r7_typage.py` ont chacun été lancés seuls
   et vus rouges avant le correctif. Les cinq rapports
   `/tmp/backend-donnees-r7-rouge-{1,2,3,4,5}.xml` ont été lus : un échec,
   aucune erreur de recette dans chacun. Lignes d'échec recopiées des XML,
   dans l'ordre ASGI, CRM, export, purge puis agenda :

   ```text
   AssertionError: assert {'receive': N... 'send': None} == {'receive': '...send': 'Send'}
   AssertionError: assert {'row': 'dict...tats': 'dict'} == {'row': 'dict...ct[str, Any]'}
   AssertionError: _valeur_de_preference_exportable retourne une valeur externe sans annotation str
   AssertionError: purge_contact_vector retourne une valeur externe sans annotation int
   AssertionError: Le cache doit écarter explicitement le calendrier None avant de lire provider
   ```

   La mesure globale à froid donne **927 avant, 922 après** :
   `.venv/bin/python -m mypy src/backend/app --ignore-missing-imports
   --no-error-summary --cache-dir=/dev/null`, puis comptage de ` error:`.
   Journaux : `/tmp/backend-donnees-r7-mypy-avant.log` et
   `/tmp/backend-donnees-r7-mypy-apres.log`. La comparaison des diagnostics,
   après neutralisation des numéros de ligne, retire exactement les cinq
   diagnostics signalés et n'en ajoute aucun. Le diagnostic de la purge
   existait déjà sous une autre forme : sa correction descend donc d'une
   unité sous les 923 de référence. **Le cliquet est abaissé à 922 dans
   `.github/workflows/ci.yml` et `tests/test_cliquet_mypy_ci.py`.** Le test
   d'égalité a d'abord été recalé et lancé seul contre l'ancien workflow :
   `AssertionError: assert '923' == '922'`
   (`/tmp/backend-donnees-r7-cliquet-rouge.xml`, lu).

   Les appelants ont été relus après correction : réponse ASGI et finalisation
   de mission, lecture/blocage/modification d'événement, import et synchronisation
   CRM, assembleur partagé des exports, anonymisations manuelle et automatique.
   Les tests voisins couvrent notamment les déconnexions ASGI 2.3/2.4, la
   cloison entre comptes, le masquage des préférences et les purges partielles.

2. **Test instable.**
   `test_mypy_n_ajoute_aucune_erreur_dans_les_trois_expressions_corrigees`
   est retiré, ainsi que ses trois imports devenus inutiles. Aucun saut,
   allongement de délai ou nouvel essai. **La garde des trois expressions de
   la passe 6 est le cliquet global.** Un sixième cas AST vérifie que ce
   fichier de tests ne réimporte pas mypy ; il ne lance aucun analyseur.
   Lancé seul avant le retrait, il donne :
   `AssertionError: Un test d'export relance mypy : ['mypy']`
   (`/tmp/backend-donnees-r7-rouge-6.xml`, lu). Après retrait, cette garde et
   les 23 cas d'export restants passent : **24 réussis**, XML
   `/tmp/backend-donnees-r7-instabilite-vert.xml` lu.

Portes finales ciblées, rapports XML lus :

- `/tmp/backend-donnees-r7.xml` : **431 réussis, 0 échec, 0 erreur,
  0 exclu**, dont les six nouveaux cas statiques. Les 22 fichiers exécutés
  couvrent les routes agents, agenda, CRM, données, configuration et RGPD,
  les régressions C20 B-1810/1811/1812/1814/1815, l'export par conversation et
  du profil, les préavis et les quatre régressions de purge du cycle 9.
- `/tmp/backend-donnees-r7-cliquet.xml` : **7 réussis, 0 échec, 0 erreur,
  0 exclu**, après modification du workflow ; les deux branches de comparaison
  stricte restent vérifiées. Total des portes finales : **438 réussis**.
- Ruff : `.venv/bin/python -m ruff check --no-fix src/backend tests`,
  **0 erreur**. `git diff --check` est propre.

Les lancements pytest utilisent `OLLAMA_BASE_URL=http://127.0.0.1:9`,
`-q -p no:cacheprovider --timeout=120` et les chemins XML ci-dessus.
La garde temporaire de la recette est adaptée à une base jetable dans
`/tmp/backend-donnees-r7-data` et bloque les connexions réseau ainsi que les
chemins protégés ; elle conserve le tube local de réveil asyncio de la passe 6.
Aucun fournisseur LLM, service réel, port interdit, suite complète ou porte
frontend n'a été sollicité. Aucun test existant n'a été affaibli.
Cette adaptation reste dans `/tmp/backend-donnees-r6-garde/sitecustomize.py`
et ne modifie ni l'application ni ses assertions.
