# RFC P-108, version 4 : reprendre son travail sur une autre machine

Rédigé le 26/09/2026. Remplace la V3 (`docs/plans/2026-09-26-rfc-p108-plusieurs-machines-v3.md`), refusée (NO-GO sans P1) par la revue adverse du 26/09 (14 constats : quatre P2, dix P3 ; rapport de travail `revue-v3-p107-p108.md` de l'orchestrateur, hors dépôt). Les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 14 à 17) restent des faits. **C'est la dernière version avant l'implémentation** : il n'y aura pas de nouvelle revue de ce document, chaque lot aura sa revue de conception au moment du code, puis la revue de son diff. Le document se lit donc seul : ce que la V2 et la V3 faisaient bien y est repris en clair, sans renvoi.

**Base de vérification.** Toutes les lignes citées ont été relues à `d0f7ab26` (HEAD du 26/09/2026, 04 h 16), dans un arbre extrait par `git archive`, jamais dans l'arbre de travail. Depuis la base de la V3 (`d80d4406`), `routers/data.py` a été modifié par B-1497, B-1498, B-1504, B-1505, B-1507, B-1522 à B-1524 et B-1536, `routers/invoices.py` par B-1493 et B-1506, `main.py` par B-1507 et B-1516, `models/database.py` et `models/entities.py` par P-132 (nouvelle tête Alembic `c9d0e1f2a3b4`) : aucun numéro de ces fichiers n'est recopié de la V3. Chemins relatifs à `src/backend/app/` (fichiers `.py` du moteur), à `src/frontend/src/` (fichiers `.ts` et `.tsx`) et à `src/frontend/src-tauri/src/` (fichiers `.rs`) ; `src/backend/main.py` (point d'entrée du moteur packagé, `src/backend/backend.spec:144`), `tests/`, `docs/`, `.github/` et `README.md` partent de la racine du dépôt.

**Prérequis fermés au code, cités et jamais recodés ici :**

- **B-1497** (`bb2e5919`) : la restauration n'extrait que les entrées d'une sauvegarde, `NOMS_D_ARCHIVE` (`routers/data.py:1062-1067`) comparée exactement (`tests/test_b1497_extraction_sauvegarde.py`).
- **B-1498** (`55c051b5`) : `recharger_la_configuration` (`services/mcp_service.py:297`) remplace la liste des connecteurs en mémoire par le fichier, sans rien démarrer, à la fin de toute restauration (`routers/data.py:1777-1783`).
- **B-1504** (`b9c3666c`) : un lien dans une sauvegarde n'empêche plus sa restauration ; il est ignoré à l'extraction et compté au journal (`routers/data.py:1265-1266`, `:1287-1288`).
- **B-1506** (`62639261`) : une facture ou un avoir émis ne se supprime plus et ne repasse plus en brouillon (409 « émets un avoir », `routers/invoices.py:568`, `:678`, critère `_facture_emise` `:701-711`, `tests/test_b1506_facture_emise_intouchable.py`). Un devis reste libre.
- **B-1507** (`124e8bcc`) : au démarrage, la copie déchiffrée d'une restauration interrompue (`.<nom>.restore.tar.gz`) est effacée (`routers/data.py:947-964`, appelée `main.py:196-203`).
- **B-1522** (`eb820c50`) : après une restauration, l'interrupteur web suit la base restaurée (`routers/data.py:1797-1806`).
- **B-1523** (`b7eebc90`) et **B-1536** (`7baf1793`) : le retour arrière écarte `therese.db-wal` et `therese.db-shm` avant de remettre l'état d'avant, et sous Windows vide le WAL qu'il ne peut supprimer (`_ecarter_les_compagnons_de_la_base`, `routers/data.py:1514`, appelée `:1656-1660` ; `tests/test_b1523_retour_arriere_sans_wal_etranger.py`, `tests/test_b1536_retour_arriere_compagnon_ouvert.py`). Il ne relit pas encore la base remise : la V4 n'en dépend pas (§4.7).
- **B-1524** (`06607577`) : l'archive est examinée par `_membres_a_extraire` (`routers/data.py:1259`) juste après le déchiffrement, avant toute destruction (`:1621-1634`, `tests/test_b1524_archive_refusee_avant_effacement.py`).

**Prérequis encore ouvert** : le chantier « mise au repos des écritures de fond » (décision 1 de P-105). Le lot 4 part après lui.

## 0. Constats de la revue V3 et leur traitement

« Fermé au code » : un commit est sur main et un test nommé le prouve à la base relue. « Design, lot N » : la réponse est écrite ici, et son test est à écrire en premier au lot N.

| # | Gravité | Constat | Traitement | Où | Fermé au code, ou design |
|---|---|---|---|---|---|
| 1 | P2 | Le blocage revient dès que les deux machines ont émis sous des numéros différents ; les seules issues étaient la suppression ou le retour au brouillon | **Accepté, et B-1506 le rend plus aigu** : ces deux issues n'existent plus pour une facture ou un avoir émis, le refus de la V3 serait donc un blocage sans sortie. La V4 retire le refus. **Une facture ou un avoir émis ne disparaît jamais par un relais ni par une restauration** : la machine qui reçoit reprend, dans les données reçues, chaque facture ou avoir émis ici (critère `_facture_emise` de B-1506) qui y manque ou n'y est qu'en brouillon ; numéro libre, elle est reprise telle quelle ; numéro pris par une autre pièce, elle est reprise marquée « en double ». La clé étrangère `contact_id` (`models/entities.py:815`) se résout par la fiche reçue, par l'adresse, ou par une fiche recréée depuis la copie figée du client (`:818-822`). Un devis, que B-1506 laisse libre, suit la garde (listé, confirmé) | §4.6 | design, lot 4 (`test_reprise_pieces_de_series_differentes`, `test_devis_absent_du_relais_liste_et_confirme`) |
| 2 | P2 | La mise de côté fausse les comptes et perd le PDF envoyé | **Accepté, et dissous** : plus rien n'est mis de côté hors du registre. La pièce reprise reste dans la base, avec son statut et son montant : l'avoir qui l'annule s'y relie (`routers/invoices.py:424-435` exige une facture présente), l'encours reste juste (`services/workspace_tools.py:530-532`, `:757-766`). Son PDF est lu octet pour octet avant toute destruction et réécrit à côté des autres | §4.6 | design, lot 4 (`test_reprise_pdf_identique_octet_pour_octet`, `test_encours_juste_apres_avoir_lie_a_la_piece_en_double`) |
| 3 | P2 | Le retour arrière rejoue un WAL étranger ; l'archive d'un échec était supprimée sur la foi d'un retour arrière non vérifié | **Moitié fermée au code** (B-1523). Pour le reste, la V4 ne supprime plus jamais l'archive d'un échec : elle est gardée, chiffrée, listée, hors du compte des trois | §4.7 | fermé au code : `b7eebc90`, `tests/test_b1523_retour_arriere_sans_wal_etranger.py` ; design, lot 4 (`test_archive_d_un_echec_gardee_hors_du_compte`) |
| 4 | P2 | L'exclusion vise la mauvaise préférence CRM | **Accepté.** Relu : `routers/crm.py:1029-1041` range `google_client_id` et `google_client_secret`, des réglages ressaisis ; le rafraîchissement réécrit `crm_sheets_access_token` (`services/crm_sync.py:37`, `:652-664`) et la synchronisation `crm_last_sync` (`services/crm_utils.py:769-778`, `services/crm_sync.py:674-692`). Exclues : ces deux clés ; comptées : `google_client_*` et `crm_sheets_refresh_token` (réécrit seulement par une reconnexion, `:415-433`). Sentinelle sur les préférences écrites par un service | §4.6 | design, lot 4 (`test_garde_rafraichissement_jeton_crm_muet`) |
| 5 | P3 | `sys.exit(78)` dans le cycle de vie devient le code 3 d'uvicorn | **Accepté.** Vérifié : uvicorn 0.40.0 appelle `sys.exit(STARTUP_FAILURE)`, soit 3, quand le démarrage échoue. Le cycle de vie écrit le fichier d'état puis lève ; le point d'entrée `src/backend/main.py` attrape le `SystemExit` autour de `uvicorn.run` (`:286`) et sort en 78 quand le fichier d'état est celui de ce processus. L'`atexit` de nettoyage (`:267-276`) reste joué | §4.3 | design, lot 2 (`test_point_d_entree_sort_en_78_et_ecrit_le_refus`) |
| 6 | P3 | L'écran dépend d'un événement émis une seule fois | **Accepté.** Le motif est gardé dans `SidecarState` (`lib.rs:219-232`) et exposé par une commande Tauri que `SplashScreen` lit au montage et à l'expiration (`components/SplashScreen.tsx:149-151`), en plus de l'événement | §4.3 | design, lot 2 (`SplashScreen.refus.test.tsx`) |
| 7 | P3 | La liste blanche était vérifiée après l'effacement | **Fermé au code** (B-1524). Le relais réutilise `_membres_a_extraire` à l'examen et avant toute destruction | §4.5, §4.7 | fermé au code : `06607577`, `tests/test_b1524_archive_refusee_avant_effacement.py` |
| 8 | P3 | Deux relevés périmés ; les liens sont perdus en silence | **Accepté.** Le §4.12 ne recode plus le ménage de B-1507, il l'étend. Les liens sont écartés **à l'archivage** et nommés dans la réponse (sauvegarde et relais) ; B-1504 reste le filet pour les archives anciennes ; « ce qui reste » les mentionne | §4.4, §4.9, §4.12 | fermé au code pour la restauration (B-1504, B-1507) ; design, lot 3 (`test_liens_ecartes_a_l_archivage_et_nommes`) |
| 9 | P3 | Numéros faux à HEAD | **Accepté.** Tout est rebasé à `d0f7ab26` | tout | sans objet |
| 10 | P3 | L'alerte promet « chiffre-le » sans geste | **Accepté, réduit au geste qui existe.** Une archive d'avant restauration restée en clair sans jumeau chiffré reçoit au démarrage un `.json` (par `_register_pre_restore_backup`, `routers/data.py:1428`) : elle apparaît dans la liste, où « Restaurer » et « Supprimer » existent déjà. Plus aucune promesse de chiffrement | §4.12 | design, lot 3 (`test_archive_interrompue_enregistree_restaurable_et_supprimable`) |
| 11 | P3 | Le clair temporaire d'une émission échappe au balayage | **Accepté.** Tous les clairs intermédiaires de création, sauvegarde comme relais, s'écrivent dans `backups/` sous `.<nom>.creation.tar.gz` ; le balayage les voit tous | §4.4, §4.12 | design, lot 3 (`test_balayage_au_demarrage`, cas émission) |
| 12 | P3 | Une règle commune évince les états d'avant relais et passe la rétention locale de un à trois | **Accepté.** Les archives du relais s'appellent `pre_relais_*` ; trois sont gardées (décision 16) ; la restauration locale garde la sienne, `pre_restore_*` (`routers/data.py:1452-1463`), inchangée | §4.7 | design, lot 4 (`test_retention_trois_pre_relais_une_pre_restore`) |
| 13 | P3 | `pieces-ecartees/` range en clair, survit à la purge | **Dissous** avec le constat 2 : plus de dossier à part. Les pièces reprises vivent dans la base chiffrée, leurs PDF à côté des autres PDF de facture, sous la même règle (effacés par la purge, `routers/data.py:775`) | §4.6 | design, lot 4 |
| 14 | P3 | La machine qui reçoit perd son journal des validations sans le savoir | **Accepté.** Le journal d'activité, validations de P-107 comprises, est classé « voyage » : il est remplacé par celui de l'autre machine et gardé dans l'état d'avant relais ; l'écran le dit avant « Appliquer » | §4.9, §4.11 | design, lots 4 et 5 |

### Défauts du code actuel relevés en relisant

Les défauts nouveaux trouvés en relisant la restauration pour cette V4 sont listés par P-107 V4 (§0) parce que sa fonction `resynchroniser_les_preferences_en_memoire()` les ferme, et le relais l'appelle : après une restauration, le profil, `THERESE.md` et le mode cabinet d'avant restent servis jusqu'au redémarrage (jumeaux de B-1522), et les PDF de facture produits dans l'intervalle portent l'émetteur d'avant (`routers/invoices.py:856`, `:906`). Aucun autre défaut nouveau.

## 1. Ce que la V4 change

- **Une facture ou un avoir émis ne disparaît jamais par un relais ni par une restauration** : il est repris, au besoin marqué « en double ». Plus de refus sans sortie, plus de dossier de pièces à part. Un devis suit la garde.
- **Le refus d'une base plus récente atteint l'écran à coup sûr** : code de sortie traduit au point d'entrée, motif gardé côté Rust et relu par l'écran.
- **Les archives d'un échec sont toujours gardées**, et le relais a sa propre rétention.
- **La signature ignore le jeton CRM rafraîchi**, pas les identifiants que tu ressaisis.
- **Les liens sont écartés à l'archivage et nommés**, tous les clairs intermédiaires sont balayés, l'archive d'une restauration interrompue devient visible.
- **Le journal d'activité est déclaré dans « ce qui voyage »**.
- **Les tests sont nommés** (fichier et fonction).

## 2. Décisions

Les décisions du 25/09 restent des faits : **14** même version exigée des deux côtés, refus sinon ; **15** connecteurs importés désactivés et listés « à réactiver » ; **16** trois états d'avant relais ; **17** l'alerte « dossier synchronisé » part en premier.

Tranchées par la V2 et gardées : usage **alterné** (le simultané n'est pas pris en charge, la garde le détecte au relais) ; phrase de passe de **16 caractères** au moins à l'émission (12 restent la règle des sauvegardes, `routers/data.py:74`), avec une phrase proposée par l'écran (25 caractères de l'alphabet de Crockford tirés par `crypto.getRandomValues`, en cinq groupes) ; les **accords** ne voyagent pas (ils vivent dans la webview, `lib/consent.ts`) ; **Qdrant** voyage ; **redémarrage** exigé après application ; vocabulaire « **relais** », jamais « synchronisation ».

Tranchées par cette V4, sur délégation (choix de conception avec recommandation) : la reprise des factures et avoirs émis, alignée sur B-1506, et le marquage « en double » (§4.6) ; l'archive d'un échec toujours gardée (§4.7) ; le préfixe `pre_relais_` et la rétention séparée (§4.7) ; l'archive interrompue rendue visible plutôt que chiffrée (§4.12). Seules les questions du §10 restent à Ludo.

## 3. Ce qui existe

**Points d'appui.** Une sauvegarde chiffrée autosuffisante : `_create_archive` (`routers/data.py:1093-1162`) range la base, Qdrant, les images, les fichiers produits, `mcp_servers.json`, le profil d'export, la clé maîtresse et son sel, les projets, les factures, les commandes et `THERESE.md` (cibles `:1108-1124`), les compagnons WAL quand le point de contrôle est incomplet (`:1126-1140`), et un manifeste interne version 1 (`:1149`) ; le tout est chiffré par phrase de passe (en-tête `THBK1`, PBKDF2 à 480 000 itérations, `services/encryption.py:520-568`). La restauration (`routers/data.py:1546-1837`) déchiffre vers un temporaire avant toute destruction (`:1598-1615`), examine les entrées (`:1621-1634`, B-1524), passe en mode maintenance, arrête les travaux de fond, ferme la base et Qdrant (`:1670-1706`), crée une archive de sécurité (`:1709`), vide et extrait (`:1723-1727`), vérifie la base avec la clé de l'archive (`_verify_restored_db`, `:1165`, appel `:1730`), fait un retour arrière sur échec (`:1648-1668`, `:1733-1770`), rouvre la base (`:1533-1544`), relit les connecteurs (`:1777-1783`), puis chiffre l'archive de sécurité avec la phrase saisie (`_finalize_safety_archive`, `:1475-1510`) en n'en gardant qu'une (`:1452-1463`). Les identifiants des tables métier sont des UUID.

**Manques.** Aucune route pour une archive venue d'ailleurs : la restauration cherche par nom dans `backups/` (`:1544`, `:1566-1572`). Aucun contrôle de version : `app_version` n'est que dans le `.json` voisin (`:1364`). Une base d'une révision inconnue est ré-estampillée à la tête locale (`models/database.py:773`, `:863`) et l'erreur est avalée (`:884`) ; et comme `_rouvrir_la_base_apres_restauration` appelle `init_db` sur la base restaurée (`routers/data.py:1541`), c'est vrai aussi juste après une restauration. L'archive de sécurité n'est chiffrée qu'à la fin (`:1811`) : pendant toute la restauration, elle est en clair. La liste des sauvegardes se fie à un chemin absolu (`archive_path`, `:1367`, lu `:1410`). Les connecteurs repartent seuls au démarrage (`services/mcp_service.py:311-330`). L'archive est chiffrée et déchiffrée entière en mémoire. Les chemins sont absolus (fichiers indexés, racines de synchronisation, dossier de travail). La numérotation des pièces est séquentielle et unique (`routers/invoices.py:82-125`, `models/entities.py:814`) : deux machines hors ligne émettent le même numéro. La pratique probable aujourd'hui est le pire cas : synchroniser `~/.therese` par un service de fichiers, clé maîtresse comprise.

## 4. Conception

### 4.1 L'identité d'installation

`.installation.json` dans le dossier de données, écrit de façon atomique (fichier temporaire puis substitution), permissions 0600, **hors de la base** (la restauration remplace toute la table `preferences`) et **hors de l'archive** (`NOMS_D_ARCHIVE` ne le contient pas, aucune archive ne peut donc l'écrire) :

```json
{"schema": 1, "installation_id": "uuid4", "machine": "hex", "empreinte": "forte",
 "generation": 0, "dernier_relais": null}
```

- **`machine`** = SHA-256 de l'identifiant stable de la machine et du dossier de données résolu. L'identifiant : `IOPlatformUUID` sous macOS (`ioreg -rd1 -c IOPlatformExpertDevice`), `MachineGuid` sous Windows (`HKLM\SOFTWARE\Microsoft\Cryptography`), `/etc/machine-id` sous Linux. Le nom d'hôte ne sert plus, sauf repli quand l'identifiant est illisible (`"empreinte": "faible"`).
- **Empreinte étrangère, dossier non synchronisé** : l'identité est régénérée une fois (nouvel `installation_id`, `dernier_relais` vidé), et l'alerte du lot 1 le mentionne.
- **Empreinte étrangère, dossier synchronisé** (diagnostic du lot 1) : le fichier n'est **pas** réécrit ; l'identité est « figée » en mémoire, l'émission comme l'application d'un relais sont refusées avec le texte de l'alerte, qui ajoute « Deux machines utilisent le même dossier THÉRÈSE. » Sans cela, chaque machine réécrirait le fichier à son tour et le service le renverrait à l'autre, sans fin.
- `dernier_relais` : `{"sens": "emis" | "recu", "le": date, "generation": n, "autre_installation": id, "signature": {...}}`.

### 4.2 Le manifeste interne, version 2

Chaque archive, sauvegarde comme relais, porte dans `.manifeste-sauvegarde.json` (`routers/data.py:1057`) :

```json
{"version": 2, "couverts": ["projects", "invoices", "commands", "THERESE.md"],
 "app_version": "0.76.0-alpha", "revision_alembic": "c9d0e1f2a3b4",
 "installation_emettrice": "uuid", "generation": 7, "relais": true,
 "cree_le": "2026-09-26T18:00:00Z", "signature": {"contacts": {"lignes": 212, "empreinte": "hex"}},
 "liens_non_transmis": ["projects/devis/raccourci.pdf"]}
```

`elements_couverts` (`routers/data.py:1070-1079`) lit toujours `couverts`, en version 1 comme en version 2. Le manifeste est dans l'archive chiffrée : il ne se lit qu'avec la phrase de passe.

### 4.3 Les révisions connues, et un refus qui arrive à l'écran

**`REVISIONS_CONNUES`** : tuple épinglé des 18 révisions de `src/backend/alembic/versions/` (P-132 vient d'ajouter `c9d0e1f2a3b4`), à côté de `ALEMBIC_HEAD_REVISION` (`models/database.py:715`), tenu par `tests/test_alembic_stamp.py` (`test_constante_epinglee_suit_la_vraie_tete`, `:139`, étendu).

**Le contrôle, en tête.** `verifier_revision_connue(db_path)` est appelé par `init_db` (`models/database.py:1075`) juste après la création du dossier parent (`:1082`), avant la migration de chiffrement (`:1084-1134`), avant `create_all` (`:1213`), les ajouts de colonnes (`:1216`, `:1231-1241`), les migrations ad hoc qui réparent des totaux de factures (`apply_adhoc_migrations`, `:1267`, dont `reparer_totaux_tva_non_applicable`, `:210`) et l'estampille (`:1273`). Il ouvre la base en lecture seule (avec la clé dérivée quand elle est chiffrée), lit `alembic_version` et lève `RevisionInconnue` si la révision n'est pas connue. Une base sans table `alembic_version` passe ; une base illisible passe aussi, pour laisser l'erreur de clé actuelle (`:1125-1134`) dire la vraie cause. `ensure_alembic_stamp` (`:738`) garde en second filet un refus avant tout ré-estampillage (`:773`), relancé hors du `except` qui avale tout (`:884`). Ce contrôle protège aussi la réouverture après restauration (`routers/data.py:1541`).

**La sortie.** Le cycle de vie (`main.py:183-193`) attrape `RevisionInconnue` autour de `init_db`, écrit `.demarrage_refuse.json` dans le dossier de données (`{"motif": "donnees_plus_recentes", "revision": "…", "version_app": "…", "pid": n}`), puis relance l'exception. Starlette la change en échec de démarrage et uvicorn sort par `sys.exit(3)`. Le point d'entrée `src/backend/main.py` entoure `uvicorn.run` (`:286-292`) d'un `try` : sur `SystemExit`, s'il existe un fichier d'état dont le `pid` est celui du processus, il sort par `sys.exit(78)` (`CODE_DONNEES_PLUS_RECENTES`) ; sinon il relance. Un `os._exit` dans le cycle de vie est écarté : il sauterait l'`atexit` de nettoyage des processus enfants (`:267-276`). Le fichier d'état est effacé au démarrage réussi suivant. **Attention au rechargement** : hors gel, le point d'entrée passe `reload=True` avec un objet d'application (`:284`, `:290`), combinaison qu'uvicorn refuse aussitôt par `sys.exit(1)` (« You must pass the application as an import string », `uvicorn/main.py:581-584` en 0.40.0), avant tout démarrage. Le rechargement est donc coupé aussi quand `THERESE_ENV=production`, la variable que le sidecar pose déjà (`lib.rs:294`) : `reload = not is_frozen and os.environ.get("THERESE_ENV") != "production"`. Le test du lot 2 passe par cette branche, la seule que l'application packagée emprunte.

**La couche Rust.** Une fonction pure `reaction_a_la_sortie(code: Option<i32>) -> Reaction` (`ArretVoulu` pour 0, `Refus("donnees_plus_recentes")` pour 78, `Relance` sinon, signal compris), hors du bloc `#[cfg(not(debug_assertions))]` pour être testable. `handle_sidecar_termination` (`lib.rs:436-459`) s'en sert : sur `Refus`, il range le motif dans un nouveau champ `refus: Mutex<Option<String>>` de `SidecarState` (`lib.rs:219-232`), émet `sidecar-refus` avec `{"motif": …}` et ne relance pas, comme pour le code 0 (`:451-454`). Une commande `commands::lire_refus_du_moteur` rend le motif ; elle est ajoutée à `generate_handler!` (`lib.rs:557-563`). La CI gagne une étape `cargo test --lib` dans le job qui passe déjà `cargo clippy --all-targets` avec un sidecar factice (`.github/workflows/ci.yml:430-442`).

**L'écran.** `SplashScreen` écoute `sidecar-refus` (à côté de `sidecar-error`, `components/SplashScreen.tsx:113`) **et** appelle `lire_refus_du_moteur` au montage et à l'expiration (`:149-151`) : un événement parti avant l'écoute n'est pas perdu. Le texte vient d'une table par motif, jamais de la charge reçue. Motif `donnees_plus_recentes` : « Tes données ont été enregistrées par une version plus récente de THÉRÈSE. Installe la dernière version, puis relance. Si tu viens de revenir à une version plus ancienne, réinstalle la plus récente, ou restaure une sauvegarde faite avec la version installée. Rien n'a été modifié. » Pas de « xattr » (`:119` ne vaut que pour `sidecar-error`). Motif inconnu : un texte générique qui ne recopie rien de la charge. La documentation utilisateur reçoit le même paragraphe.

### 4.4 Émettre un relais

`POST /api/data/relais/preparer` avec `{passphrase}` (16 caractères au moins), refusé tant que l'identité est figée :

1. calcule la signature métier (§4.6) ;
2. écrit l'archive **en clair sous `backups/.<nom>.creation.tar.gz`**, par le chemin des sauvegardes, manifeste version 2 (`relais: true`, `generation` locale plus un), **en écartant les liens** (§4.9) ;
3. la chiffre vers `backups/relais/emis/<nom>.tar.gz.enc`, supprime le clair, dans un `finally` ;
4. enregistre dans `.installation.json` la nouvelle génération et `dernier_relais` (`sens: "emis"`) ;
5. rend le nom, le chemin complet, la taille et `liens_non_transmis`.

L'archive émise n'apparaît pas parmi les sauvegardes : `list_backups` ne lit que `backups/*.json` sans descendre (`routers/data.py:1404`). `create_backup` suit la même règle pour son clair (aujourd'hui `<nom>.tar.gz`, `:1316`) : tous les clairs intermédiaires de création vivent dans `backups/` sous un nom qui commence par un point et finit par `.creation.tar.gz`. L'écran propose « Afficher le fichier » ; tu copies toi-même le fichier sur ta clé ou dans ton dossier partagé : le serveur n'écrit jamais hors de `backups/`.

### 4.5 Recevoir : arrivée du fichier et examen, sans rien détruire

**Arrivée.** L'écran ouvre la boîte native (`open` de `@tauri-apps/plugin-dialog`) et envoie le **chemin**, pas le contenu (qui doublerait la charge mémoire). Contrôles avant toute lecture : chemin absolu ; `lstat` d'un fichier régulier (ni lien ni dossier) ; taille sous le plafond `min(2 Gio, mémoire totale / 4)` (`detect_system_memory`, `services/system_resources.py:76`), 1 Gio si la mémoire est inconnue ; cinq premiers octets égaux à `THBK1`. Chemins traités par `Path`, pour valoir sous Windows. Copie par blocs de 1 Mio vers `backups/relais/recus/<nom>.tar.gz.enc`, en exclusif et en 0600. Une copie reçue n'est pas restaurable par « Restaurer » : son nom contient une barre, que la validation refuse (`routers/data.py:1565`).

**Examen** : `POST /api/data/relais/examiner` avec `{nom, passphrase}`. Déchiffrement vers `backups/.<nom>.restore.tar.gz` (le motif que B-1507 balaie, effacé dans un `finally`) ; `_membres_a_extraire` (B-1524) ; lecture du manifeste ; extraction de `therese.db`, `therese.db-wal` et `therese.db-shm` dans `backups/relais/.examen-<horodatage>/`, effacé dans un `finally`, et ouverture là avec la clé dérivée du `.encryption_key` de l'archive : SQLite rejoue le WAL, révision, pièces et signature se lisent sur l'état complet. Réponse :

```json
{"compatible": true, "motif": null,
 "archive": {"emise_le": "…", "app_version": "0.76.0-alpha", "installation": "…"},
 "cette_machine": {"app_version": "0.76.0-alpha"},
 "garde": {"plus_ancienne": false, "modifications": [{"table": "Contacts", "lignes": "+3"}]},
 "pieces_reprises": [{"numero": "FACT-2026-012", "client": "…", "ttc": 480.0, "cas": "reprise"}],
 "pieces_en_double": [{"numero": "FACT-2026-012", "ici": {…}, "relais": {…}}],
 "pieces_modifiees_ici": [{"numero": "FACT-2026-010", "ce_qui_change": "statut payée"}],
 "connecteurs_a_reactiver": [{"nom": "Slack", "commande": "npx", "arguments": ["…"]}],
 "a_rebrancher": {"fichiers_hors_therese": 42, "racines_synchronisees": 2, "dossier_de_travail": "…"},
 "liens_non_transmis": ["…"], "ne_voyage_pas": ["…"], "identite_figee": false}
```

L'examen ne modifie rien, hors la copie reçue. Refus (décision 14) : autre `app_version` (l'écran dit laquelle mettre à jour) ; manifeste version 1 sur la route du relais (« refais le relais depuis l'autre machine, à jour ») ; révision inconnue ; membre hors liste.

### 4.6 La garde, et la reprise des pièces

Tout est refait à l'application, jamais repris de l'examen.

**Contrôle 1, génération.** Une archive d'une autre installation dont la génération est inférieure ou égale à la génération locale est plus ancienne que le dernier relais connu ici.

**Contrôle 2, signature métier.** Pour chaque table métier, le nombre de lignes et un SHA-256 des lignes triées par clé primaire (valeurs en JSON à clés triées, dates ISO), comparés à la signature de `dernier_relais`. Sans relais antérieur, toute table métier non vide compte, **sauf `preferences`** : un portable neuf qui vient de faire sa mise en route ne doit pas demander de confirmation. Ce qui ne compte pas :

- **tables techniques** : `notifications`, `activity_logs`, `processing_tasks`, `email_messages`, `email_labels` (cache de la boîte distante), `project_sync_entries`, `sync_plans`, `sync_operations` ; chaque table de `SQLModel.metadata` (quarante à la base) est classée métier ou technique, avec un motif ;
- **colonnes volatiles**, dans toutes les tables : `updated_at`, `synced_at`, `last_sync`, `last_sync_error`, `access_token`, `refresh_token`, `token_expiry`. Relevé : le rafraîchissement d'un jeton Gmail réécrit `access_token`, `token_expiry` et `updated_at` (`routers/email.py:304-306`) ; la lecture d'un agenda Google réécrit `synced_at` (`routers/calendar.py:412`, `:1014`) ;
- **copies d'un service distant** : les lignes de `calendars` dont `provider` n'est pas `local` (`models/entities.py:503`) et leurs événements ;
- **préférences écrites en arrière-plan**, par clé : `crm_sheets_access_token` (`services/crm_sync.py:37`, réécrite `:661`) et `crm_last_sync` (`:41`, `services/crm_utils.py:778`). Restent comptées : `google_client_id` et `google_client_secret` (`routers/crm.py:1029-1041`, ressaisis à la main), `crm_sheets_refresh_token` (réécrit par une reconnexion seulement), le profil, les clés, les réglages.

Les contrôles 1 et 2 refusent l'application **sauf confirmation explicite** (`confirme_ecrasement: true`), avec un texte qui dit ce qui sera perdu.

**Contrôle 3, remplacé par la reprise des pièces.** La reprise suit exactement la ligne de B-1506 : elle concerne les pièces pour lesquelles `_facture_emise` (`routers/invoices.py:701-711`) est vraie, c'est-à-dire une facture ou un avoir dont `sent_at` est posé ou dont le statut n'est plus `draft` (`models/entities.py:828`, `:841`). Ce sont les seules qu'aucun geste ne peut supprimer ni ramener au brouillon : leur absence dans l'archive, ou leur état de brouillon là-bas, ne peut donc pas venir d'un geste voulu sur l'autre machine. Un devis reste hors de la séquence (B-1506 le laisse libre) : l'autre machine a pu le supprimer ou le remettre en brouillon exprès, et le reprendre annulerait ce geste en silence. Un devis créé ou modifié ici depuis le dernier relais suit donc la garde : il est listé dans `pieces_modifiees_ici` (« DEV-2026-004 de cette machine sera perdu »), entre dans la confirmation du contrôle 2, et reste dans l'état d'avant relais. En comparant la base locale et celle de l'archive, pour chaque facture ou avoir émis ici :

| Cas | Ce qui se passe |
|---|---|
| son identifiant manque à l'archive, son numéro y est libre | **reprise** telle quelle |
| son identifiant manque, son numéro est porté par une autre pièce de l'archive | **reprise marquée « en double »** : `invoice_number = "<numéro>~<identifiant>"` |
| son identifiant est dans l'archive, mais en brouillon | **reprise par-dessus** : la version d'ici remplace la ligne et les lignes de détail reçues (le brouillon de l'archive est antérieur : B-1506 interdit de ramener au brouillon une facture ou un avoir émis) |
| son identifiant est dans l'archive, émise aussi, avec d'autres valeurs | la version du relais est gardée ; la pièce est listée dans `pieces_modifiees_ici` et entre dans la confirmation du contrôle 2 |

**La reprise elle-même**, dans le cœur partagé (§4.7), après l'extraction et `_verify_restored_db`, sur la base extraite ouverte avec la clé de l'archive, en **une transaction** :

- la pièce et ses lignes (`InvoiceLine`, `models/entities.py:850-865`) avec leurs identifiants ;
- son client : la fiche reçue si `contact_id` y existe ; sinon une fiche reçue de même adresse électronique (non vide, casse ignorée), à laquelle la pièce est rattachée ; sinon une fiche recréée avec le même identifiant depuis la copie figée (`client_name`, `client_company`, `client_email`, `client_phone`, `client_address`, `models/entities.py:818-822`), `rgpd_base_legale = "obligation_legale"` ; l'examen le dit (« Le client de FACT-2026-012 manque au relais : sa fiche sera recréée depuis la pièce ») ;
- `converted_from_id` recopié tel quel ; s'il désigne une pièce absente du résultat, il ne mène nulle part, et le PDF d'un avoir omet alors la ligne d'origine (`routers/invoices.py:878-885`) ;
- son PDF : les octets de `<dossier des factures>/<numéro>.pdf` (dossier résolu par `resolve_invoice_output_dir`, `services/invoice_pdf.py:90`) sont lus **avant toute destruction**. Si ce dossier est `invoices/` du dossier de données (élément couvert, vidé à l'application), ils sont réécrits après l'extraction sous le nom de la pièce reprise (`<numéro>~<identifiant>.pdf` pour une pièce en double), jamais par-dessus un fichier différent (qui garde son nom ; la copie prend alors le nom suffixé). Si c'est le dossier de travail (hors du dossier de données, que le relais ne touche pas), le fichier d'une pièce en double y est renommé au nom suffixé, après contrôle du SHA-256, puisque le numéro nu appartient désormais à l'autre pièce.

Un échec de la reprise, ou un nombre de pièces relu différent de celui attendu, déclenche le retour arrière complet.

**Le marquage « en double ».** Le suffixe `~<identifiant>` rend le numéro unique en base (`models/entities.py:814`). Il est ignoré par le calcul du numéro suivant, qui écarte déjà tout suffixe non numérique (`routers/invoices.py:116-123`). Une fonction `numero_affiche(numero)` rend la partie avant `~` : elle sert au numéro imprimé sur le PDF (`services/invoice_pdf.py:318`, `:435`, `:815`), à la citation de la facture d'origine d'un avoir (`routers/invoices.py:885`), et aux champs `numero_affiche` et `numero_en_double` de la réponse des pièces. Le nom du fichier PDF garde le numéro complet (`services/invoice_pdf.py:782`), pour que les deux PDF ne s'écrasent pas. **Règle générale** : toute surface qui montre un numéro à une personne, au modèle ou dans un document sortant passe par `numero_affiche` et signale « numéro en double » à part ; les usages internes (clé d'unicité, nom de fichier, recherche exacte) gardent le numéro complet. Lecteurs relevés à la base : côté moteur, `routers/invoices.py`, `services/invoice_pdf.py`, `routers/dashboard.py`, `services/notification_service.py`, `services/workspace_tools.py` (`search_invoices`, `invoice_totals`, cartes du chat) et `services/action_agents.py` (bloc des pièces de la source `crm`, bloc des factures) ; côté écran, `components/invoices/InvoiceForm.tsx`, `components/invoices/InvoicesPanel.tsx`, `components/prototype/DeliverablesWorkspaceCanvas.tsx`, `components/prototype/InvoiceConversationCard.tsx`, `components/prototype/prototypeReadModels.ts`, `services/api/dashboard.ts`, `services/api/invoices.ts`. Deux sentinelles les tiennent (lot 4). `_facture_emise` n'est pas touchée : la pièce reste émise, intouchable, et **l'avoir qui l'annule se relie à elle**, si bien que l'encours reste juste.

Motif : deux pièces différentes ont réellement été envoyées sous le même numéro ; la numérotation est rompue chez les clients, le relais ne peut pas la réparer. Il peut ne rien perdre et ne rien fausser : les deux pièces restent au registre, avec leur PDF, et la correction légale (un avoir sur celle qui a été émise en second, puis une réémission sous un numéro neuf) se fait dans THÉRÈSE, avec des totaux justes. Après succès, l'écran le dit en ces termes.

**Prévention.** `GET /api/data/relais/etat` rend `dernier_relais`. Tant que le dernier relais connu est « émis » et qu'aucun n'a été reçu depuis, le formulaire de pièce affiche au passage à « envoyé » ou « payé » un avertissement non bloquant : « Tu as passé le relais à une autre machine le 26/09. Émettre ici risque un numéro en double avec l'autre machine. »

**Sentinelles** (`tests/test_sentinelles_structure.py`) : `test_chaque_table_classee_metier_ou_technique` ; `test_colonnes_volatiles_classees` (toute colonne métier qui finit par `_token`, `_expiry`, `_at` hors `created_at`, ou contient `sync`, est volatile ou « métier malgré le nom » avec un motif, par exemple `sent_at`) ; `test_preferences_ecrites_par_un_service_classees` (toute clé de `Preference` écrite hors d'une route de réglage, relevée par l'AST dans `services/` et dans les tâches de fond, est volatile ou métier avec un motif).

### 4.7 Appliquer

`POST /api/data/relais/appliquer` avec `{nom, passphrase, confirme_ecrasement, confirme_doubles}`. Le corps de `restore_backup` (`routers/data.py:1546-1837`) devient un **cœur partagé** par les deux routes, dans cet ordre :

1. déchiffrement vers `backups/.<nom>.restore.tar.gz` et examen des entrées (B-1524) ;
2. manifeste, révision connue, contrôles 1 et 2, plan de reprise (§4.6), lecture des PDF à reprendre : **avant toute destruction** ;
3. mode maintenance, arrêt des travaux de fond, fermeture de la base et de Qdrant (inchangés) ;
4. **archive de sécurité chiffrée d'abord** : créée en clair (`pre_relais_<horodatage>` pour un relais, `pre_restore_<horodatage>` pour une restauration locale), aussitôt chiffrée avec la phrase saisie et enregistrée avec son `.json` (`kind`, `issue: "en_cours"`). Si ce chiffrement échoue, tout s'arrête avec « rien n'a été modifié ». Le clair ne sert qu'au retour arrière et disparaît dans le `finally`. Sans phrase de passe (anciennes sauvegardes en clair, route locale seulement), le comportement actuel est gardé ;
5. vidage et extraction (inchangés, avec B-1523 pour le retour arrière) ;
6. **connecteurs** : quand l'installation émettrice diffère de la locale ou manque, chaque serveur du `mcp_servers.json` extrait passe à `"enabled": false` avant la vérification de la base ; la relecture de B-1498 remplace ensuite la liste en mémoire, sans rien démarrer ;
7. `_verify_restored_db` (inchangé), puis la **reprise des pièces** ;
8. finalisation : réouverture de la base, relecture des connecteurs, `resynchroniser_les_preferences_en_memoire()` (P-107 V4, §4.8.6 : clés, profil, `THERESE.md`, interrupteur web, mode cabinet, retraits), mise à jour de `.installation.json` (`generation = max(locale, archive)`, `dernier_relais` en `sens: "recu"` ; l'`installation_id` ne change pas), `issue: "reussie"` sur l'archive de sécurité.

**Rétention** (décision 16). `pre_relais_*` : les trois plus récentes d'issue `reussie` sont gardées, par une nouvelle fonction qui ne touche qu'à ce préfixe. `pre_restore_*` : une seule, comme aujourd'hui (`_prune_pre_restore_backups`, `routers/data.py:1452-1463`), mais sans toucher les archives d'issue `echec` ou `interrompue`. **Une archive d'issue `echec` est toujours gardée**, chiffrée, listée, hors du compte : elle porte l'état d'avant la tentative, et rien ne prouve aujourd'hui que le retour arrière l'a remis à l'identique (`_rollback`, `:1648-1668`, rend vrai sans relire la base). Tu la supprimes par « Supprimer », qui existe. Une archive ancienne sans `issue` compte comme réussie.

**Copie reçue** : supprimée après une application réussie (son contenu est devenu la base en service, l'état d'avant est dans l'archive de sécurité, et l'original reste où tu l'as choisi). **Copies émises** : jamais élaguées d'office, listées avec leur date et leur taille, supprimables d'un geste ; leur élagage automatique est posé à Ludo (§10).

### 4.8 La route locale « Restaurer »

`restore_backup` lit le manifeste de l'archive déchiffrée **avant** l'archive de sécurité et toute destruction :

| Archive | Conduite |
|---|---|
| Version 2, d'une autre installation | refus 409 : « Cette sauvegarde vient d'une autre machine : ouvre-la par « Recevoir d'une autre machine ». » |
| Version 2, de cette installation | comportement actuel, plus révision connue et reprise des factures et avoirs émis depuis la sauvegarde |
| Version 1 (avant ce chantier) | comportement actuel, plus révision connue, connecteurs désactivés (origine inconnue, listés « à réactiver ») et reprise des pièces |
| `.db` ancienne (`routers/data.py:1589`, `:1732`) | révision connue vérifiée avant la copie |

La reprise vaut aussi ici : restaurer une sauvegarde d'avant une facture émise ne doit pas effacer cette facture, que B-1506 rend intouchable. La réponse liste les pièces reprises. Désactiver les connecteurs d'une archive version 1 est un changement de comportement, dit dans la réponse.

### 4.9 Ce qui voyage, ce qui reste, ce qui est à rebrancher

La liste est **générée** par le serveur :

- **Voyage** : les cibles de l'archive (`routers/data.py:1110-1126`), donc toute la base, **journal d'activité compris** : sur la machine qui reçoit, il est remplacé par celui de l'autre machine, validations de P-107 comprises ; le sien reste dans l'état d'avant relais.
- **Reste sur chaque machine** : les autres entrées du dossier de données, chacune avec un libellé (âmes des agents, outils installés, voix et modèles de dictée, compteur de consommation, journaux techniques, sauvegardes, copies de relais, jeton de session, identité d'installation), et **les liens posés à la main** dans les dossiers transmis, écartés à l'archivage et nommés par `liens_non_transmis` (le filtre de `tar.add` à `routers/data.py:1149` ; B-1504 reste le filet pour les archives anciennes).
- **Reste dans l'interface**, déclaré par l'écran : accords pour les services en ligne, réglages d'affichage, état des écrans.
- **À rebrancher**, calculé depuis la base de l'archive : fichiers indexés hors du dossier de données, racines de synchronisation, dossier de travail, connecteurs.

**Sentinelle** (`test_chaque_nom_sous_le_dossier_de_donnees_est_classe`) : chaque nom de premier niveau construit sous `settings.data_dir` dans le code du moteur est classé « voyage » ou « reste », avec son libellé.

### 4.10 L'alerte du dossier synchronisé

Service `services/emplacement_donnees.py`, fonction pure `diagnostiquer(dossier, maison, environnement)` :

1. **dossier résolu** (liens suivis) sous une racine connue : iCloud Drive (`~/Library/Mobile Documents/com~apple~CloudDocs`), fournisseurs de fichiers macOS (`~/Library/CloudStorage/<Fournisseur>-…`, le nom du service vient du préfixe), `~/Dropbox`, `~/Nextcloud`, `~/Google Drive`, `~/OneDrive*` ; sous Windows, les dossiers désignés par `OneDrive`, `OneDriveConsumer`, `OneDriveCommercial`, puis `%USERPROFILE%\Dropbox`, `%USERPROFILE%\iCloudDrive`, `%USERPROFILE%\Nextcloud` ;
2. **marqueur** dans le dossier ou un parent jusqu'au dossier personnel : `.stfolder`, `.dropbox`, `.sync` ;
3. **copies en conflit** déjà présentes : `therese 2.db`, `conflicted copy`, `.sync-conflict-`, `therese-<NOM-DU-PC>.db`.

Route `GET /api/data/emplacement`. Au démarrage, si le dossier est synchronisé, une notification « attention » (`create_notification`), sauf si la même existe depuis moins de 30 jours. À l'écran : une `Alerte` (rôle `alert`) dans Confidentialité, et la ligne « Données » du Centre de confiance (`components/prototype/CapabilityCenter.tsx:587`), qui dit la vérité. Texte : « Ton dossier THÉRÈSE est synchronisé par iCloud Drive. La clé qui ouvre ta base est dans le même dossier : elle part chez iCloud avec elle. Et si deux machines ouvrent THÉRÈSE en même temps, la base peut s'abîmer. Sors ce dossier de la synchronisation, et n'ouvre THÉRÈSE que sur une machine à la fois. » ; avec la phrase du §4.1 quand deux machines partagent le dossier ; après le lot 5 : « Pour changer de machine, passe le relais (Confidentialité). »

### 4.11 L'écran « Passer le relais »

Dans Confidentialité (`components/settings/PrivacyTab.tsx`, à côté de la section des sauvegardes, `:307-423`), deux blocs.

- **Envoyer vers une autre machine** : phrase de passe (16 caractères au moins, « Proposer une phrase »), puis, **avant** la création, ce que contient le fichier : ta base, la clé qui l'ouvre, tes clés d'API, les accès à tes boîtes mail, la configuration de tes connecteurs ; « Qui a ce fichier et sa phrase de passe a tout. » Puis le chemin, « Afficher le fichier », et les liens non transmis. Plus bas, les **copies émises** : date, taille, « Supprimer ».
- **Recevoir d'une autre machine** : fichier, phrase de passe, « Examiner ». L'état des lieux en phrases (« Cette machine a 3 contacts de plus qu'au dernier relais : ils seront perdus »), **les pièces reprises**, **les pièces en double** avec leur case propre, **les pièces modifiées ici**, ce qui ne voyage pas (dont : « Ton journal d'activité sera remplacé par celui de l'autre machine ; il reste dans l'état d'avant relais »), les connecteurs à réactiver. Avant « Appliquer » : « L'état de cette machine d'avant le relais sera gardé, chiffré avec la phrase de passe de ce relais. Garde cette phrase : sans elle, cet état ne se rouvre pas. » « Appliquer » exige la case de la garde quand elle parle, et la case des doubles quand il y en a ; il est absent pour une version incompatible. Après succès : « Redémarre THÉRÈSE. » et, s'il y a des doubles : « FACT-2026-012 de cette machine est reprise, marquée « en double ». Annule par un avoir celle des deux qui a été émise en second, puis réémets-la : l'avoir se relie à elle et tes totaux restent justes. »
- **Identité figée** : le bloc est remplacé par le texte de l'alerte du lot 1.

Le mot « synchronisation » n'apparaît nulle part. La liste des pièces montre « numéro en double » à côté d'une pièce marquée (`components/invoices/InvoicesPanel.tsx`).

### 4.12 Le balayage au démarrage

`effacer_les_dechiffrements_interrompus` (`routers/data.py:947-964`, appelée `main.py:196-203`) est étendue, et ne regarde que des noms connus :

| Nom | Conduite | Motif |
|---|---|---|
| `backups/.<nom>.restore.tar.gz` | supprimé (B-1507, inchangé) | double en clair d'une archive chiffrée |
| `backups/.<nom>.creation.tar.gz` | supprimé | la création d'une sauvegarde ou d'un relais ne modifie pas les données ; le clair n'est qu'un intermédiaire |
| `backups/relais/.examen-*` | supprimé | l'examen ne modifie rien |
| `backups/pre_restore_*.tar.gz`, `backups/pre_relais_*.tar.gz` en clair, avec un jumeau `.tar.gz.enc` et son `.json` | le clair est supprimé | le jumeau chiffré, écrit avant toute destruction (§4.7), porte le même état |
| les mêmes, sans jumeau | **gardé**, et enregistré avec un `.json` (`encrypted: false`, `issue: "interrompue"`) par `_register_pre_restore_backup` (`routers/data.py:1428`) | c'est peut-être la seule copie de l'état d'avant une restauration interrompue |

Dans le dernier cas, l'archive apparaît dans la liste des sauvegardes, où « Restaurer » (une archive `.tar.gz` en clair se restaure déjà, `routers/data.py:1587`, `:1718`) et « Supprimer » existent, et une `Alerte` de Confidentialité dit : « Une restauration a été interrompue. L'état d'avant est gardé, en clair, dans tes sauvegardes : restaure-le si tes données te semblent incomplètes, sinon supprime-le. » Aucune ancienne sauvegarde en clair accompagnée de son `.json` n'est touchée.

### 4.13 Hors périmètre, et lot B conditionnel

- **Journal chiffré et fusion**, **instance jointe à distance** : hors périmètre.
- **Lot B**, seulement si le relais manuel lasse : dossier de relais choisi (archive déposée à la fermeture, proposée à l'ouverture, jamais appliquée sans geste) ; format chiffré par morceaux pour ne plus tenir l'archive en mémoire ; remappage des préfixes de chemins. Il touche la promesse publique (§10).

## 5. Lots

Chaîne de chaque lot : revue de conception du lot, tests écrits d'abord et vus rouges, code, sabotage ciblé par fonction, revue adverse du diff, recette dans l'application lancée.

### Lot 1 : l'alerte du dossier synchronisé (moteur, écran)

Livre §4.10. Fichier `tests/test_p108_lot1_dossier_synchronise.py` :

- `test_diagnostiquer_racines_connues` (paramétré : chaque racine, nom du service rendu) ;
- `test_diagnostiquer_dossier_ordinaire` ;
- `test_diagnostiquer_lien_vers_icloud` ;
- `test_diagnostiquer_marqueur_dans_un_parent` (paramétré : `.stfolder`, `.dropbox`, `.sync`) ;
- `test_diagnostiquer_copies_en_conflit` (paramétré sur les quatre motifs) ;
- `test_diagnostiquer_variables_windows` (environnement simulé ; le même test tourne sur le runner Windows avec de vrais chemins) ;
- `test_notification_une_seule_fois_en_trente_jours` ;
- `test_route_emplacement`.

Vitest : `components/settings/PrivacyTab.dossierSynchronise.test.tsx` (l'`Alerte` nomme le service, n'existe pas sinon) et `components/prototype/CapabilityCenter.donnees.test.tsx` (la ligne « Données » change).

Critère observable : un `THERESE_DATA_DIR` placé dans iCloud Drive affiche l'alerte au lancement et dans Confidentialité. Ce lot peut partir seul.

### Lot 2 : identité, manifeste version 2, révisions connues, refus à l'écran (moteur, Rust, écran)

Livre §4.1 à §4.3. Fichier `tests/test_p108_lot2_identite_revision.py` :

- `test_installation_creee_une_fois_et_stable`, `test_empreinte_ignore_le_nom_d_hote`, `test_empreinte_faible_sans_identifiant_de_machine` ;
- `test_empreinte_etrangere_dossier_ordinaire_regenere_une_fois` et `test_empreinte_etrangere_dossier_synchronise_fige_sans_ecrire` ;
- `test_installation_absente_de_toute_archive` ;
- `test_manifeste_version_2_complet` et `test_elements_couverts_lit_une_archive_version_1` ;
- `test_revision_inconnue_refusee_avant_toute_ecriture` (paramétré : base en clair, base chiffrée ; SHA-256 identique avant et après, aucune table créée) ;
- `test_base_sans_alembic_version_passe` et `test_base_illisible_laisse_l_erreur_de_cle` ;
- `test_ensure_alembic_stamp_ne_reestampille_plus_une_revision_inconnue` ;
- `test_point_d_entree_sort_en_78_et_ecrit_le_refus` : sous-processus sur `src/backend/main.py` avec `THERESE_ENV=production` (sans quoi uvicorn sort en 1 avant de démarrer), port libre, `THERESE_DATA_DIR` jetable, base estampillée `revision_du_futur` ; code de retour 78, fichier d'état présent avec le bon `pid` ;
- `test_point_d_entree_sans_refus_garde_son_code` : même sous-processus, démarrage qui échoue pour une autre cause ; le code n'est pas 78 ;
- `test_refus_efface_au_demarrage_reussi_suivant`.

Dans `tests/test_alembic_stamp.py` : `test_constante_epinglee_suit_la_vraie_tete` (`:139`) vérifie aussi que `REVISIONS_CONNUES` égale l'ensemble des révisions du dossier et contient la tête. Dans `tests/test_variables.py` : `_base_legacy` (`:248`) pose une révision connue ancienne au lieu de `ancienne_tete` (`:270`) ; `test_pas_de_restamp_sans_table_variables` (`:293`) et `test_restamp_avec_schema_complet` (`:308`) gardent leur intention.

Rust, `#[cfg(test)] mod tests` dans `lib.rs` : `reaction_a_la_sortie_zero_est_un_arret_voulu`, `reaction_a_la_sortie_78_est_un_refus_sans_relance`, `reaction_a_la_sortie_un_relance`, `reaction_a_la_sortie_signal_relance`. CI : étape `cargo test --lib` après clippy.

Vitest, `components/SplashScreen.refus.test.tsx` : l'événement affiche le texte de la table, sans « xattr » ; un refus déjà rangé avant le montage est lu par la commande au montage ; il l'est aussi à l'expiration ; un motif inconnu affiche le texte générique sans rien de la charge.

Critère observable : une base d'une version future dans un dossier de test ; l'application packagée affiche le texte de la table, sans relance ni « xattr ».

### Lot 3 : émettre, examiner, balayer (moteur)

Livre §4.4, §4.5, §4.9 et §4.12. Fichier `tests/test_p108_lot3_emettre_examiner.py` :

- `test_aller_examen_sans_modification` : deux `THERESE_DATA_DIR` aux clés différentes ; B examine le relais de A ; la base, les fichiers et `.installation.json` de B sont identiques avant et après (SHA-256) ;
- `test_examen_refus_sans_rien_modifier` (paramétré : mauvais en-tête, archive tronquée, mauvaise phrase, taille au-delà du plafond, lien symbolique, dossier, chemin inexistant, chemin relatif, autre `app_version`, manifeste version 1, révision inconnue, membre hors liste) ;
- `test_aucun_clair_apres_une_exception_a_chaque_etape` ;
- `test_examen_voit_une_facture_presente_seulement_dans_le_wal` ;
- `test_emission_phrase_de_15_refusee_de_16_acceptee` et `test_emission_avance_la_generation` ;
- `test_emission_hors_de_la_liste_des_sauvegardes` et `test_emission_refusee_quand_l_identite_est_figee` ;
- `test_liens_ecartes_a_l_archivage_et_nommes` (paramétré : sauvegarde, relais) ;
- `test_list_backups_voit_une_archive_au_chemin_d_une_autre_machine` ;
- `test_balayage_au_demarrage` (paramétré : `.x.creation.tar.gz` venu d'une sauvegarde puis d'une émission, `relais/.examen-x/`, `pre_relais_*` clair avec jumeau, `pre_restore_*` clair sans jumeau gardé et enregistré ; une ancienne sauvegarde en clair avec son `.json` intacte ; `.x.restore.tar.gz` toujours effacé) ;
- `test_archive_interrompue_enregistree_restaurable_et_supprimable` ;
- `test_purge_note_compte_les_copies_de_relais` (la note de la purge, `routers/data.py:798-810`, compte aussi `backups/relais/`).

Dans `tests/test_sentinelles_structure.py` : `test_chaque_nom_sous_le_dossier_de_donnees_est_classe`, vue rouge sur un nom fabriqué.

Critère observable : sur une machine, deux profils ; le relais de l'un s'examine dans l'autre et décrit ce qui arriverait.

### Lot 4 : appliquer, avec la garde et la reprise des pièces (moteur)

Livre §4.6 à §4.8. Part après le chantier « mise au repos ». Fichier `tests/test_p108_lot4_appliquer.py` :

- **aller-retour** : `test_aller_retour_entre_deux_profils` (A vers B, B relit une conversation, un contact et une clé d'API ; B vers A, A relit le travail fait sur B) ;
- **garde** : `test_garde_contact_cree_apres_relais` (refus sans confirmation, succès avec), `test_garde_contact_modifie_sans_creation`, `test_garde_muette_pour_une_notification`, `test_garde_muette_pour_le_jeton_gmail_rafraichi`, `test_garde_muette_pour_la_lecture_d_un_agenda_google`, `test_garde_rafraichissement_jeton_crm_muet` (par le vrai chemin de rafraîchissement, `services/crm_sync.py:652-664`, OAuth simulé), `test_garde_parle_pour_les_identifiants_google_client`, `test_garde_parle_pour_un_evenement_d_agenda_local`, `test_garde_parle_pour_une_cle_d_api_ajoutee`, `test_generation_depassee_refusee_sans_confirmation` ;
- **reprise** : `test_reprise_pieces_de_series_differentes` (A émet DEV-2026-004, B émet FACT-2026-012 ; A vers B puis B vers A aboutissent ; les deux pièces existent des deux côtés ; aucune suppression), `test_reprise_numero_libre_contact_present`, `test_reprise_contact_rattache_par_adresse`, `test_reprise_contact_recree_depuis_la_copie_figee`, `test_reprise_numero_pris_marquee_en_double`, `test_reprise_par_dessus_un_brouillon`, `test_piece_modifiee_ici_listee_et_version_du_relais_gardee`, `test_devis_absent_du_relais_liste_et_confirme` (B vers A d'abord : le devis d'A est listé perdu, la confirmation est exigée, il reste dans l'état d'avant relais), `test_devis_envoye_ici_brouillon_dans_le_relais_version_du_relais_gardee`, `test_reprise_pdf_identique_octet_pour_octet` (paramétré : dossier `invoices/` du dossier de données, dossier de travail), `test_reprise_en_echec_fait_un_retour_arriere_complet` ;
- **en double** : `test_numero_suivant_ignore_un_numero_marque`, `test_pdf_d_une_piece_en_double_imprime_le_numero_sans_suffixe`, `test_surfaces_affichees_sans_suffixe` (paramétré : tableau de bord, notification, `search_invoices`, contexte d'un agent), `test_avoir_cite_le_numero_sans_suffixe`, `test_encours_juste_apres_avoir_lie_a_la_piece_en_double`, `test_piece_en_double_reste_intouchable` (B-1506 : ni suppression ni brouillon) ;
- **archive de sécurité et rétention** : `test_archive_de_securite_chiffree_avant_destruction` (chiffrement simulé en échec : 500 « rien n'a été modifié », base identique octet pour octet), `test_retention_trois_pre_relais_une_pre_restore`, `test_archive_d_un_echec_gardee_hors_du_compte`, `test_copie_recue_supprimee_apres_succes_copies_emises_intactes` ;
- **connecteurs** : `test_connecteurs_desactives_liste_en_memoire_egale_le_fichier` (et `MCPService().initialize()` n'en lance aucun), `test_restauration_locale_meme_installation_garde_ses_connecteurs` ;
- **route locale** : `test_route_locale_refuse_une_archive_d_une_autre_installation_avant_destruction` (409, base identique), `test_route_locale_archive_version_1_connecteurs_desactives`, `test_route_locale_reprend_les_pieces_emises_depuis_la_sauvegarde`, `test_copie_recue_introuvable_par_restaurer`, `test_revision_inconnue_refusee_avant_destruction` (paramétré : relais, restauration locale, `.db` ancienne) ;
- **mémoire du processus et journal** : `test_resynchronisation_apres_le_relais` et `test_journal_remplace_par_celui_de_l_autre_machine`.

Dans `routers/invoices.py` et `services/invoice_pdf.py` : `numero_affiche` et les champs de réponse, testés par les trois tests « en double » ci-dessus. Dans `tests/test_sentinelles_structure.py` : `test_chaque_table_classee_metier_ou_technique`, `test_colonnes_volatiles_classees` (vue rouge sur une colonne fabriquée `derniere_sync_at`), `test_preferences_ecrites_par_un_service_classees`, `test_lecteurs_du_numero_de_piece_classes` (chaque lecture de `invoice_number` hors des modèles, relevée par l'AST, est classée « affichée », et passe alors par `numero_affiche`, ou « interne » ; vue rouge sur un lecteur fabriqué). Côté écran, `lib/numeroDePiece.sentinelle.test.ts` fait de même sur les sources (`import.meta.glob` en texte brut) : un fichier qui affiche un numéro lit `numero_affiche`.

Critère observable : deux profils sur une machine, relais dans les deux sens, un contact et une facture créés de chaque côté pour voir la garde parler, puis un même numéro émis des deux côtés pour voir la pièce reprise « en double », l'avoir relié et les totaux.

### Lot 5 : l'écran (écran)

Livre §4.11 et l'avertissement du §4.6. Fichier `components/settings/PasserLeRelais.test.tsx`, par rôle et par nom :

- « Proposer une phrase » remplit un champ de 29 caractères (25 plus quatre séparateurs), différent à chaque clic ;
- ce que contient le fichier est affiché avant la création ; les liens non transmis sont nommés ;
- l'état des lieux d'une réponse simulée : version incompatible (pas de bouton « Appliquer ») ; garde (case obligatoire) ; pièces reprises listées ; pièces en double (case propre obligatoire) ; pièces modifiées ici ; phrase du journal remplacé ;
- la phrase sur l'état d'avant relais est présente avant « Appliquer » ;
- la phrase de succès des doubles ;
- les copies émises avec date, taille et « Supprimer » ;
- identité figée : le texte de l'alerte remplace le bloc ;
- aucun texte ne contient « synchronis » ;
- l'alerte du lot 1 gagne « passe le relais ».

Et : `components/invoices/InvoiceForm.relais.test.tsx` (avertissement après un relais émis, absent après un relais reçu), `components/invoices/InvoicesPanel.enDouble.test.tsx` (mention « numéro en double »), `components/settings/PrivacyTab.restaurationInterrompue.test.tsx` (l'alerte du §4.12).

Critère observable : parcours complet au clavier seul.

### Lot 6 : recette réelle sur deux machines

macOS vers Windows 10, puis retour, avec de vraies données (Dr_logic travaille sous Windows 10, et le sel binaire comme `O_BINARY` ont déjà piégé les tests), un numéro émis des deux côtés exprès, et sa correction par un avoir.

## 6. Données et migrations

- **Aucune révision Alembic.** La tête reste celle que P-132 vient de poser, `c9d0e1f2a3b4` (`models/database.py:715`). La preuve d'estampillage change de nature, pas de contenu : elle ne ré-estampille plus une révision inconnue et son erreur n'est plus avalée ; toute révision future entre dans `ALEMBIC_HEAD_REVISION`, dans `REVISIONS_CONNUES` et dans la preuve de schéma.
- **Numéro marqué** : une valeur nouvelle de `invoices.invoice_number` (`<numéro>~<identifiant>`), sans changement de schéma.
- **Fichiers nouveaux** : `.installation.json` ; `.demarrage_refuse.json` (effacé au démarrage réussi suivant) ; `backups/relais/emis/`, `backups/relais/recus/`, `backups/relais/.examen-*` (temporaire).
- **Métadonnées des archives de sécurité** : `kind` (`pre_restore`, `pre_relais`) et `issue` (`en_cours`, `reussie`, `echec`, `interrompue`).
- **Purge totale** : `.installation.json` garde son identifiant, `dernier_relais` est vidé ; `backups/relais/` n'est pas touché, comme les sauvegardes (tout y est chiffré), et la note le compte.
- **Export RGPD** : inchangé.

## 7. Risques restants

- **Perte de données** : le relais remplace tout, sauf les factures et avoirs émis. La garde, les trois états d'avant relais, les archives d'échec gardées et la reprise des pièces sont les protections ; aucune ne suffit seule.
- **Numérotation rompue en usage simultané** : le relais ne la répare pas ; il garde les deux pièces, les montre et oriente vers l'avoir. La prévention réduit le risque sans l'annuler.
- **Pièce modifiée des deux côtés** (par exemple payée ici, relancée là-bas) : la version du relais gagne, après confirmation.
- **Fiche de client recréée** : si tu avais effacé ce client sur l'autre machine, sa fiche revient, réduite à la copie que la pièce porte déjà ; l'examen le dit.
- **Brouillon dont le PDF a circulé, devis** : ni l'un ni l'autre n'est repris ; la garde les liste, la confirmation les couvre, ils restent dans l'état d'avant relais.
- **Signature** : une colonne volatile mal classée ferait parler la garde à tort ; une préférence rechiffrée à l'identique (sel aléatoire) la fait parler aussi, dans le sens prudent.
- **Empreinte faible** : sans identifiant de machine lisible, le nom d'hôte revient, avec ses changements.
- **Sécurité** : l'archive contient la clé maîtresse, les clés d'API, les jetons Gmail, les mots de passe IMAP et la configuration des connecteurs ; qui a le fichier et la phrase a tout. Une archive fabriquée par un tiers qui connaît la phrase peut déposer des consignes dans `THERESE.md` ou le profil ; connecteurs désactivés et liste blanche ferment les deux voies d'exécution relevées.
- **Mémoire** : l'archive est tenue entière en mémoire ; au-delà du plafond, le relais est impossible avant le lot B, et l'écran le dit.
- **Clair transitoire** : réduit par le balayage, jamais nul entre l'écriture et le chiffrement.
- **Usage simultané** non pris en charge ; détecté seulement au relais.

## 8. Ce que la V4 retire ou reporte, et pourquoi

| Élément de la V3 | Sort | Motif |
|---|---|---|
| Contrôle 3 « factures » avec refus, mise de côté et acquittement numéro par numéro | remplacé par la reprise des pièces | B-1506 a fermé les deux seules sorties ; le refus deviendrait un blocage sans issue, et la mise de côté faussait l'encours |
| Dossier `backups/relais/pieces-ecartees/` | retiré | plus rien ne sort du registre ; il gardait en clair des pièces hors de la purge |
| Critère « émise » (`sent_at` ou statut), tous types | remplacé par `_facture_emise` de B-1506 (facture et avoir) | seules ces pièces ne peuvent disparaître par un geste voulu ; reprendre un devis annulerait peut-être une suppression faite exprès sur l'autre machine |
| Suppression de l'archive d'un échec quand le retour arrière « a réussi » | retirée : l'archive d'un échec est toujours gardée | `_rollback` ne relit pas la base qu'il remet |
| Trois archives de sécurité communes aux deux routes | séparées : `pre_relais_*` (trois), `pre_restore_*` (une) | la règle commune réduisait la décision 16 et changeait la rétention locale sans décision |
| Exclusion des « jetons OAuth du CRM, catégorie `oauth` » | remplacée par `crm_sheets_access_token` et `crm_last_sync` | la V3 visait les identifiants que tu ressaisis |
| « Quitte avec un code dédié » depuis le cycle de vie | code traduit au point d'entrée | uvicorn change toute sortie du cycle de vie en code 3 |
| Écran fondé sur un seul événement | motif gardé côté Rust et relu | un événement parti avant l'écoute était perdu |
| Balayage conditionnel de `.restore.tar.gz` | retiré | B-1507 le fait déjà, sans condition, et c'est juste (le `.enc` d'origine reste) |
| « Chiffre-le avec une phrase de passe » pour l'archive interrompue | remplacé par son enregistrement dans la liste | aucun geste ne chiffrait une archive existante |
| Clair d'émission dans `backups/relais/emis/` | déplacé dans `backups/` | le balayage ne le voyait pas |
| « Tous les membres sont contrôlés avant la première écriture » | cité comme fait de B-1524 | c'était vrai de l'extraction seulement, jusqu'à B-1524 |

Ce que la V2 et la V3 faisaient bien est gardé : l'identité hors base et hors archive, le manifeste interne version 2, la signature par table plutôt qu'un compteur, l'archive de sécurité chiffrée avant toute destruction, l'arrivée par un chemin local validé, l'examen qui ne détruit rien, la liste blanche unique de B-1497, « ce qui ne voyage pas » dérivé et tenu par sentinelle, les copies de relais hors de la liste des sauvegardes, l'alerte du dossier synchronisé en premier.

## 9. Livraison

Ordre : lot 1, lot 2, lot 3, lot 4 (après la « mise au repos »), lot 5, lot 6. Le lot 1 peut partir seul. `resynchroniser_les_preferences_en_memoire()` est créée par le premier livré du lot 5 de P-107, des correctifs des jumeaux de B-1522 ou du lot 4 de P-108 ; les autres y ajoutent leurs caches. Revue de conception à chaque lot, sécurité d'abord ; revue du diff à chaque lot. Aucune release sans le GO de Ludo.

## 10. Questions réservées à Ludo

1. **Le lot B et la promesse publique.** Le README promet « Ton contexte reste sur ta machine, jamais envoyé à un serveur Synoptïa » (`README.md:34`). Le relais manuel n'y change rien : tu déplaces toi-même un fichier chiffré. Le lot B déposerait ce fichier de lui-même dans un dossier synchronisé par un tiers. **Option A**, lancer le lot B après le lot 6 et réécrire la phrase (« tes données restent sur tes machines ; le relais, chiffré, passe par le dossier que tu choisis ») : moins de gestes pour les utilisateurs à deux machines, une promesse publique à changer. **Option B**, ne le lancer que sur une demande exprimée : la promesse reste telle quelle. **Recommandation** : B.
2. **Les mots publics** (notes de version, réponse à Dr_logic sur Discord). **Option A**, « relais » et « une machine à la fois », avec une réponse à Dr_logic dès le lot 1 lui disant de sortir `~/.therese` de sa synchronisation actuelle : il est protégé tout de suite, et le mot « synchronisation » n'est jamais promis. **Option B**, attendre le lot 5 pour annoncer d'un coup : une seule annonce, mais Dr_logic reste exposé d'ici là. **Recommandation** : A.
3. **Élaguer d'office les relais émis.** Chaque relais émis est une archive complète dans `backups/relais/emis/` ; la V4 ne les supprime jamais sans ton geste, puisque ce serait effacer d'office des états passés des données. **Option A**, garder les deux plus récents et supprimer les plus anciens en le disant à l'émission (« le relais du 12/09 a été supprimé ; il en reste deux ») : le disque ne se remplit pas, un état passé disparaît sans geste. **Option B**, ne jamais élaguer : rien ne se perd, la liste et la place grandissent jusqu'à ce que tu supprimes. **Recommandation** : A, ce sont des copies de passage dont tu as emporté la tienne.

## Annexe : appuis dans le code (à `d0f7ab26`)

- Sauvegarde : `routers/data.py:947-964` (balayage), `:1051-1091` (manifeste, liste blanche, éléments couverts), `:1093-1162` (archive), `:1259-1292` (entrées et extraction), `:1296-1391` (création), `:1394-1425` (liste), `:1428-1510` (archive de sécurité, rétention), `:1841` (suppression).
- Restauration : `routers/data.py:1533-1837` ; retour arrière `:1648-1668`.
- Purge : `routers/data.py:634-823`.
- Estampille et démarrage : `models/database.py:709-885`, `:1075-1275` ; `main.py:183-215` ; `src/backend/main.py:262-292`.
- Moteur et écran de démarrage : `lib.rs:219-232`, `:399-470`, `:557-563` ; `components/SplashScreen.tsx:103-160` ; `.github/workflows/ci.yml:425-442`.
- Connecteurs : `services/mcp_service.py:297-330`.
- Factures : `routers/invoices.py:60-68`, `:82-168`, `:424-435`, `:568`, `:664-711`, `:878-949` ; `services/invoice_pdf.py:90`, `:318`, `:435`, `:781-782`, `:815` ; `models/entities.py:808-865` ; encours `services/workspace_tools.py:522-560`, `:754-767`.
- Écritures de fond : `routers/email.py:304-306` ; `routers/calendar.py:412`, `:1014` ; `services/crm_sync.py:36-41`, `:395-433`, `:652-692` ; `services/crm_utils.py:769-778` ; `routers/crm.py:1029-1041`.
- Chiffrement des archives : `services/encryption.py:520-568`.
- Écran des sauvegardes : `components/settings/PrivacyTab.tsx:307-423` ; appels `services/api/data.ts:88-137`.
