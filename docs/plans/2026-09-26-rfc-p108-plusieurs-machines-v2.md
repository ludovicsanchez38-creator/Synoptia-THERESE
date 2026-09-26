# RFC P-108, version 2 : reprendre son travail sur une autre machine

Rédigé le 26/09/2026. Remplace la V1 (`docs/plans/2026-09-25-rfc-p108-plusieurs-machines.md`), jugée NO-GO par la revue adverse (`docs/plans/revues/2026-09-25-revue-rfc-p105-p108.md`, section P-108 : quatre P2, cinq P3). Intègre les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 14 à 17). Aucun code avant la validation de ce document.

Toutes les lignes citées ont été relues au commit `ca9f44d1` (26/09/2026, 01 h 30). Chemins relatifs à `src/backend/app/` et à `src/frontend/src/`, sauf mention contraire.

## 0. Ce qui change par rapport à la V1

- **L'alerte « dossier synchronisé » passe en premier** (décision 17) : c'est le lot le moins cher, et il protège dès aujourd'hui ceux qui copient `~/.therese` avec sa clé.
- **Même version exigée des deux côtés** (décision 14), lue dans le manifeste **interne** de l'archive, jamais dans le `.json` voisin. En plus, le démarrage refuse désormais une base d'une révision Alembic inconnue au lieu de la ré-estampiller à une tête plus ancienne.
- **L'identité d'installation et la génération vivent dans un fichier à part**, hors de la base et hors de l'archive, et une extraction en liste blanche empêche une archive de l'écraser.
- **La garde contre l'écrasement a un mécanisme** : génération du relais, signature par table métier, et un refus sans appel quand une facture émise serait perdue ou en doublon.
- **Les connecteurs importés arrivent désactivés** (décision 15) et listés « à réactiver ».
- **Trois états d'avant relais** sont gardés (décision 16), et l'archive de sécurité est chiffrée **avant** toute étape destructive.
- **Le fichier arrive par un chemin local** choisi dans la boîte de dialogue native, validé et plafonné avant d'être lu.
- **« Ce qui ne voyage pas » est dérivé** de la liste de ce que l'archive contient, et tenu par une sentinelle.
- **Aucune migration Alembic.**

## 1. Le besoin

Dr_logic-3D, sur Discord (fil du 25/09, 03:35 à 04:29), travaille sur plusieurs machines, duplique THÉRÈSE sur chacune et bute sur la synchronisation des données. Il veut reprendre le même travail d'une instance à l'autre : conversations, contacts, projets, documents.

## 2. Décisions tranchées

### Décisions du 25/09/2026 (faits acquis)

| N° | Décision | Où elle vit dans cette V2 |
|---|---|---|
| 14 | Même version de THÉRÈSE exigée des deux côtés ; une archive d'une autre version est refusée (« mets cette machine à jour d'abord »). | §4.2, §4.3, lots 2 et 3 |
| 15 | Les connecteurs (MCP) importés arrivent désactivés et listés « à réactiver » avec leur commande. | §4.7, lot 4 |
| 16 | Trois états « d'avant relais » gardés sur chaque machine. | §4.7, lot 4 |
| 17 | L'alerte « tes données sont dans un dossier synchronisé » part avant le reste. | §4.9, lot 1 |

### Questions de la V1 tranchées par cette V2

1. **Usage alterné ou simultané.** La conception vise l'usage alterné (bureau le jour, portable le soir). L'usage simultané n'est pas pris en charge : la garde du §4.6 le détecte au moment du relais et le refuse ou le fait confirmer. L'option C (journal chiffré et fusion) ne sera étudiée que sur preuve d'un besoin simultané.
2. **Phrase de passe du relais.** 16 caractères au moins à l'émission d'un relais (12 restent la règle des sauvegardes, `routers/data.py:74`), avec une phrase générée proposée par l'écran : 25 caractères tirés par `crypto.getRandomValues` dans l'alphabet de Crockford, en cinq groupes (environ 125 bits). Motif : un fichier de relais est fait pour quitter la machine, donc pour subir une attaque hors ligne sans limite d'essais. L'import accepte toute archive valide, quelle que soit la longueur choisie à l'époque.
3. **Consentements.** Ils ne voyagent pas : ils vivent dans le stockage de la webview (`lib/consent.ts:46`, `:66`) et sont redemandés sur l'autre machine. C'est le sens prudent.
4. **Qdrant.** Il voyage, comme aujourd'hui (`routers/data.py:1077`). Le reconstruire à l'arrivée n'aurait d'intérêt que pour alléger l'archive, question du lot B.
5. **Redémarrage.** Il reste exigé après application, comme pour toute restauration (`routers/data.py:1698-1699`), et l'écran le dit.
6. **Vocabulaire.** « Relais », jamais « synchronisation », tant que la fusion n'existe pas. La formulation publique reste à Ludo (§10).

## 3. Ce qui existe, relu dans le code

### Points d'appui

- **Une sauvegarde chiffrée autosuffisante.** Elle contient la base, Qdrant, les images, les fichiers produits, `mcp_servers.json`, le profil d'export, la clé maîtresse et son sel, les projets, les factures, les commandes et `THERESE.md` (`routers/data.py:1075-1091`), plus un manifeste interne `{"version": 1, "couverts": [...]}` (`:1116`). Le tout est chiffré par passphrase : en-tête `THBK1`, PBKDF2 à 480 000 itérations, sel frais (`services/encryption.py:520-550`).
- **Une restauration qui prévoit déjà l'autre machine** : la base restaurée est ouverte avec la clé de l'archive avant que le succès soit déclaré (`routers/data.py:1130-1179`), et au démarrage suivant le fichier de clé l'emporte sur le trousseau (`services/encryption.py:150-178`, BUG-050).
- **Une restauration prudente** : déchiffrement vers un temporaire avant toute destruction, clair effacé sur toute interruption (`routers/data.py:1507-1524`, B-1290) ; mode maintenance, suspension des créations du chat, arrêt des travaux de fond, fermeture de la base et de Qdrant (`:1560-1595`) ; archive de sécurité complète (`:1598`) et retour arrière intégral (`:1542-1557`).
- **Des identifiants UUID** sur les tables métier : pas de collision d'identifiants entre deux machines.
- **Des tests d'aller-retour** : `tests/test_backup_complete.py`, `tests/test_backup_encryption.py`, `tests/test_b1290_dechiffrement_interrompu.py`, `tests/test_alembic_stamp.py`.

### Manques

- **Aucune route pour une archive venue d'ailleurs** : la restauration cherche par nom dans `backups/` (`routers/data.py:1496-1502`). Rien ne s'appelle `installation_id`, `THBK2` ni `backups/import` dans le code (recherche du 26/09 : zéro occurrence).
- **La liste des sauvegardes se fie à un chemin absolu** : le `.json` porte `archive_path` en absolu (`routers/data.py:1295`), et la liste déclare l'archive absente si ce chemin n'existe pas (`:1338-1343`). Un `.json` venu d'une autre machine rend donc une archive « absente ».
- **Aucun contrôle de version** : le manifeste interne ne porte que sa propre version (`routers/data.py:1116`) ; `app_version` n'est que dans le `.json` voisin (`:1294`).
- **Une base d'une révision inconnue est ré-estampillée à la tête locale** : dès que la révision diffère de la tête (`models/database.py:677`) et que la preuve de schéma passe, ce qui arrive puisqu'une base plus récente contient toutes les colonnes anciennes, la table `alembic_version` est réécrite (`:762-766`). Et toute exception y est avalée (`:784-785`).
- **L'extraction prend tout** : `_safe_extractall(tar, data_dir)` (`routers/data.py:1615`) extrait chaque membre sûr au sens des chemins, mais pas seulement les noms que l'archive est censée contenir. Une archive fabriquée peut déposer n'importe quel fichier dans le dossier de données.
- **Une seule archive de sécurité, chiffrée après coup** : `_prune_pre_restore_backups` n'en garde qu'une (`routers/data.py:1380-1391`, appelée à `:1437`) ; le chiffrement n'a lieu qu'après la restauration (`:1682-1684`), et s'il échoue l'archive est supprimée (`:1428-1432`).
- **Les connecteurs repartent seuls** : chaque serveur `enabled` est lancé à l'initialisation (`services/mcp_service.py:293-295`), en tâche de fond au démarrage (`main.py:301-315`).
- **L'archive est chiffrée et déchiffrée entière en mémoire** (`services/encryption.py:544`, `:559`, `:568`).
- **Les chemins sont absolus** : `FileMetadata.path` unique (`models/entities.py:225`), racines de synchronisation avec l'identité du volume (`models/entities_sync.py:71-74`), dossier de travail en préférence (`routers/config.py:1252-1340`), `{WORKING_DIRECTORY}` figé à l'installation d'un connecteur (`routers/mcp.py:638-668`).
- **La numérotation des factures est séquentielle et unique** (`routers/invoices.py:82`, `:128-160` ; `models/entities.py:798`) : deux machines hors ligne émettraient le même numéro.
- **La pratique probable aujourd'hui est le pire cas** : synchroniser `~/.therese` par un service de fichiers. La clé maîtresse est un fichier voisin de la base (`services/encryption.py:40`, `SECURITY.md:31`, `:35`) et part chez l'hébergeur avec elle ; SQLite en WAL et Qdrant local se corrompent sous une copie concurrente.

### Écarts de la V1 et de la revue relevés par cette V2

| Affirmation | Réalité |
|---|---|
| V1 : « neuf magasins Zustand » ; revue : « dix fichiers de `stores/` appellent `persist(` » | Neuf magasins réels : `accessibilityStore`, `calendarStore`, `chatStore`, `crmStore`, `demoStore`, `emailStore`, `invoiceStore`, `personalisationStore`, `taskStore`. Le dixième fichier est un test, `stores/invoiceStore.filtresRelus.test.ts:4`, dont un commentaire cite `persist()`. D'autres clés locales existent hors des magasins (`lib/consent.ts`, `lib/variateurDuBrief.ts`, `lib/profileStorageIsolation.ts`) : la V2 ne compte plus, elle déclare (§4.8). |
| V1 : `run_instance_id` ne vit que le temps d'un lancement (`models/processing.py:73`) | Exact. Il ne peut pas servir d'identité d'installation. |
| Revue : l'archive porte `mcp_servers.json` (`routers/data.py:1069`) | La ligne est aujourd'hui `:1082`. Constat inchangé. |
| Commentaire de `models/database.py:616-618` : la tête est épinglée « pour que l'app PACKAGÉE puisse estampiller sans embarquer le dossier alembic/ » | `backend.spec` embarque pourtant le dossier `alembic` (`src/backend/backend.spec:96`). La V2 épingle quand même la liste des révisions connues, pour ne pas faire dépendre le démarrage d'une lecture de fichiers. |

## 4. Conception

### 4.1 L'identité d'installation

Un fichier `.installation.json` dans le dossier de données, écrit de façon atomique (fichier temporaire puis substitution, comme `services/mcp_service.py:349-372`), permissions 0600 :

```json
{
  "schema": 1,
  "installation_id": "uuid4",
  "machine": "sha256(nom d'hôte, dossier personnel, dossier de données résolu)",
  "generation": 0,
  "dernier_relais": null
}
```

- Créé au premier démarrage s'il manque. **Hors de la base** : la restauration remplace la table `preferences` entière (`routers/data.py:1672-1673`), un identifiant rangé là voyagerait. **Hors de l'archive** : `_create_archive` n'ajoute que des cibles nommées (`:1075-1091`), et l'extraction en liste blanche (§4.7) refuse un membre de ce nom.
- **Dossier copié** : si l'empreinte `machine` ne correspond plus, le fichier vient d'une autre machine (copie à la main, dossier synchronisé). Un nouvel `installation_id` est tiré, `dernier_relais` est vidé, et l'alerte du lot 1 le mentionne. Un changement de nom d'hôte produit le même effet ; c'est sans danger (§8).
- `dernier_relais` : `{"sens": "emis" | "recu", "le": date, "generation": n, "autre_installation": id, "signature": {...}}`.

### 4.2 Le manifeste interne, version 2

Chaque archive (sauvegarde ordinaire comme relais) porte, dans `.manifeste-sauvegarde.json` (`routers/data.py:1032`) :

```json
{
  "version": 2,
  "couverts": ["projects", "invoices", "commands", "THERESE.md"],
  "app_version": "0.76.0-alpha",
  "revision_alembic": "b8c9d0e1f2a3",
  "installation_emettrice": "uuid",
  "generation": 7,
  "relais": true,
  "cree_le": "2026-09-26T18:00:00Z",
  "signature": {"contacts": {"lignes": 212, "empreinte": "hex"}}
}
```

`elements_couverts` (`routers/data.py:1035-1044`) lit toujours `couverts`, en version 1 comme en version 2. Le manifeste est dans l'archive chiffrée : on ne le lit qu'avec la phrase de passe, ce qui est voulu.

### 4.3 Les révisions connues

- `REVISIONS_CONNUES` : tuple épinglé des 17 révisions de `src/backend/alembic/versions/`, à côté de `ALEMBIC_HEAD_REVISION` (`models/database.py:619`). `tests/test_alembic_stamp.py` étend `test_constante_epinglee_suit_la_vraie_tete` (`:139`) : le tuple égale l'ensemble des révisions du dossier et contient la tête.
- **`ensure_alembic_stamp`** : avant tout ré-estampillage (`models/database.py:677`), une révision absente de `REVISIONS_CONNUES` lève `RevisionInconnue`, relancée **hors** du `except Exception` qui avale tout (`:784-785`). `init_db` (`:1173`) la propage ; le démarrage échoue avec « Ces données viennent d'une version plus récente de THÉRÈSE : mets l'application à jour », affiché par l'écran d'erreur fatale existant (`components/SplashScreen.tsx:114`, B-757). Ce garde protège aussi ceux qui synchronisent `~/.therese` entre deux versions.
- **Au relais**, la révision est lue dans la base de l'archive elle-même (extraite vers un temporaire, ouverte avec la clé dérivée du `.encryption_key` de l'archive par `derive_db_key_from_master`, `services/encryption.py:470-485`) ; la valeur du manifeste ne sert qu'à l'affichage. Une révision inconnue est refusée avant toute destruction, sur la route du relais comme sur la restauration locale.

### 4.4 Émettre un relais

`POST /api/data/relais/preparer` avec `{passphrase}` (16 caractères au moins) :

1. calcule la signature métier (§4.6) ;
2. crée l'archive par le chemin des sauvegardes, manifeste version 2 avec `relais: true` et `generation = generation locale + 1` ;
3. enregistre dans `.installation.json` la nouvelle génération et `dernier_relais` (`sens: "emis"`) ;
4. rend le nom, le chemin complet du `.tar.gz.enc` et sa taille.

L'écran propose « Afficher le fichier », par `open` de `@tauri-apps/plugin-shell` avec repli sur l'affichage du chemin, le motif déjà utilisé pour les PDF de facture (`components/invoices/InvoicesPanel.tsx:148-160`). L'utilisateur copie lui-même le fichier sur sa clé ou dans son dossier partagé : le serveur n'écrit jamais hors de `backups/`.

### 4.5 Recevoir : arrivée du fichier et examen, sans rien détruire

**Arrivée.** L'écran ouvre la boîte de dialogue native (`open` de `@tauri-apps/plugin-dialog`, déjà utilisée par `components/settings/SettingsModal.tsx:7` et `components/chat/ChatInput.tsx:13`) et envoie le **chemin** au serveur. Envoyer le contenu dans la requête doublerait la charge mémoire d'une archive déjà lue entière au déchiffrement ; le délai n'est pas l'obstacle, les routes de sauvegarde passent déjà `timeoutMs: null` (`services/api/data.ts:115`).

**Contrôles, dans cet ordre, avant de lire le contenu** : chemin absolu ; `lstat` d'un fichier régulier (ni lien ni dossier) ; taille sous le plafond ; cinq premiers octets égaux à `THBK1`. Plafond : `min(2 Gio, mémoire totale / 4)` par `detect_system_memory` (`services/system_resources.py:76`), 1 Gio si la mémoire est inconnue, puisque le déchiffrement tient l'archive et son clair en mémoire (`services/encryption.py:559-568`). Les chemins sont traités par `Path`, jamais par motif sur `/`, pour valoir sous Windows.

**Copie** par blocs de 1 Mio vers `backups/relais_<horodatage>.tar.gz.enc`, créé en exclusif et en 0600, avec un `.json` régénéré. `list_backups` résout désormais chaque archive par son nom dans `backups/`, et non plus par `archive_path` (`routers/data.py:1338`) : les `.json` existants restent lisibles.

**Examen** : `POST /api/data/relais/examiner` avec `{chemin, passphrase}`. Déchiffrement vers un temporaire (motif B-1290, clair effacé dans un `finally`), lecture du manifeste, liste des membres, extraction de la seule base vers un temporaire pour lire sa révision, ses factures et ses fichiers indexés, puis réponse :

```json
{
  "compatible": false,
  "motif": "version",
  "archive": {"emise_le": "...", "app_version": "0.77.0-alpha", "installation": "portable"},
  "cette_machine": {"app_version": "0.76.2-alpha"},
  "garde": {"plus_ancienne": false, "modifications": [{"table": "Contacts", "lignes": "+3"}], "factures_bloquantes": []},
  "connecteurs_a_reactiver": [{"nom": "Slack", "commande": "npx", "arguments": ["..."]}],
  "a_rebrancher": {"fichiers_hors_therese": 42, "racines_synchronisees": 2, "dossier_de_travail": "/Users/a/Documents"},
  "ne_voyage_pas": ["..."]
}
```

L'examen ne modifie rien sur la machine, hors la copie dans `backups/`. Les refus de version (décision 14) : une archive d'une autre `app_version` est incompatible et l'écran dit laquelle mettre à jour ; une archive au manifeste version 1 (faite avant ce chantier) est refusée sur la route du relais (« refais le relais depuis l'autre machine, à jour »).

### 4.6 La garde contre l'écrasement

Trois contrôles, refaits à l'application et jamais repris de l'examen :

1. **Génération.** Si l'archive vient d'une autre installation et que sa génération est inférieure ou égale à la génération locale, elle est plus ancienne que le dernier relais connu ici.
2. **Signature métier.** Pour chaque table métier, le nombre de lignes et un SHA-256 des lignes triées par clé primaire (valeurs sérialisées en JSON à clés triées, dates ISO). La signature courante de la machine est comparée à celle de `dernier_relais`. Sans relais antérieur, toute table métier non vide compte comme une modification, **sauf `preferences`** : une installation neuve qui vient de faire sa mise en route (service d'IA, clé) n'a rien à perdre, et le cas le plus courant, un portable neuf, ne doit pas demander de confirmation d'écrasement.
   - **Pourquoi pas un compteur incrémenté par les routes d'écriture**, comme le proposait la revue : une route oubliée rendrait la garde muette sans que rien ne rougisse, et la V1 elle-même relève l'absence d'`updated_at` sur de nombreuses tables. La signature voit aussi une modification sans création. Elle coûte une lecture complète, deux fois par relais seulement, en tâche de thread.
   - **Tables exclues**, parce qu'écrites en arrière-plan ou recopiées d'un service distant : `notifications` (générées toutes les heures, `main.py:348-364`), `activity_logs`, `processing_tasks`, `email_messages` et `email_labels` (cache de la boîte distante), les résultats et plans de synchronisation de dossiers (`project_sync_entries`, `sync_plans`, `sync_operations`, dérivés d'un scan local). Les racines rattachées (`project_sync_roots`) restent métier : ce sont des choix de l'utilisateur. `preferences` est **incluse** : un profil ou une clé d'API modifiés doivent déclencher la garde.
   - **Sentinelle** : chaque table de `SQLModel.metadata` est classée « métier » ou « technique », avec un motif pour chaque technique. Une table nouvelle non classée fait échouer la suite.
3. **Factures, sans appel.** Si cette machine porte une pièce hors brouillon (`status`, `models/entities.py:812`) dont le numéro manque à l'archive, ou un même numéro sous un autre identifiant, l'application est **refusée**, confirmation ou non. Message : « Cette machine a émis FACT-2026-012, absent du relais. Passe d'abord le relais de cette machine vers l'autre. » Motif : réattribuer un numéro émis casse la numérotation continue, et aucune confirmation ne rend ce geste légal.

Les contrôles 1 et 2 refusent l'application **sauf confirmation explicite** (`confirme_ecrasement: true`), avec un texte qui dit ce qui sera perdu. Le contrôle 3 ne se contourne pas.

### 4.7 Appliquer

`POST /api/data/relais/appliquer` avec `{nom, passphrase, confirme_ecrasement}`.

- **Cœur partagé.** Le corps de `restore_backup` (`routers/data.py:1455-1708`) devient une fonction commune aux deux routes. Le chantier « mise au repos des écritures de fond », validé le 25/09 (décision 1 de P-105), profitera ainsi aux deux sans être recodé ; ce lot part après lui.
- **Avant toute destruction** : refaire les contrôles de version, de révision (§4.3) et de garde (§4.6) ; vérifier que chaque membre de l'archive appartient à la liste blanche des noms de cibles (`routers/data.py:1075-1091`, plus `therese.db-wal`, `therese.db-shm` et le manifeste). Un membre hors liste refuse l'archive entière. La même vérification s'applique à la restauration locale.
- **Archive de sécurité chiffrée d'abord.** Juste après `_create_archive(safety_archive)` (`routers/data.py:1598`), elle est chiffrée avec la phrase de passe saisie. Si ce chiffrement échoue, tout s'arrête avant `_wipe_volatile_dirs` (`:1612`) avec « rien n'a été modifié ». Le clair ne sert qu'au retour arrière (`:1550`) et disparaît dans le `finally`. Sans phrase de passe (anciennes sauvegardes en clair, restauration locale seulement), le comportement actuel est conservé.
- **Trois états gardés** (décision 16) : `_prune_pre_restore_backups` conserve les trois archives de sécurité les plus récentes par `created_at`, qu'elles viennent d'une restauration ou d'un relais (métadonnée `kind: "pre_relais"` pour les distinguer à l'écran).
- **Connecteurs désactivés** (décision 15) quand l'installation émettrice diffère de la locale (ou manque, sur la route du relais) : après l'extraction et avant la vérification de la base (`routers/data.py:1619`), chaque serveur du `mcp_servers.json` extrait passe à `"enabled": false`. Seul ce champ change ; les variables restent chiffrées par la clé maîtresse de l'archive (`services/mcp_service.py:316`) et se déchiffreront après le redémarrage, puisque la clé voyage. Le service MCP en mémoire arrête ses serveurs et recharge la liste depuis le fichier sans en démarrer aucun : sinon une modification de connecteur avant le redémarrage réécrirait l'ancienne liste (`services/mcp_service.py:349-372`). Une restauration locale d'une archive de la même installation garde ses connecteurs actifs.
- **Après succès** : `.installation.json` reçoit `generation = max(locale, archive)` et `dernier_relais` (`sens: "recu"`, signature du manifeste). L'`installation_id` ne change pas.

### 4.8 Ce qui voyage, ce qui reste, ce qui est à rebrancher

La liste est **générée** par le serveur, jamais écrite à la main :

- **Voyage** : les cibles de l'archive (`routers/data.py:1075-1091`).
- **Reste sur chaque machine** : les autres entrées du dossier de données, chacune avec un libellé : âmes des agents (`agents/<id>/SOUL.md`, `services/agents/config.py:101`), outils installés (`tools/`, `services/skills/tool_installer.py:55`), voix et modèles de dictée locale (`voices/`, `models/whisper`, `services/voice_local.py:60`, `:72`), compteur de consommation (`token_usage.json`, `services/token_tracker.py:508`), journaux techniques (`logs/`, `core/logging_config.py:164`), sauvegardes, jeton de session, identité d'installation.
- **Reste dans l'interface**, déclaré par l'écran : accords pour les services en ligne, réglages d'affichage et état des écrans.
- **À rebrancher**, calculé depuis la base de l'archive : fichiers indexés hors du dossier de données, racines de synchronisation, dossier de travail, connecteurs.

**Sentinelle** : un test relève chaque nom de premier niveau construit sous `settings.data_dir` dans le code du moteur et exige qu'il soit classé « voyage » ou « reste », avec son libellé. Un nouveau dossier non classé fait échouer la suite.

### 4.9 L'alerte du dossier synchronisé

Service `services/emplacement_donnees.py`, fonction pure `diagnostiquer(dossier, maison, environnement)` :

1. **Dossier résolu** (liens suivis par `Path.resolve()`) sous une racine connue : iCloud Drive (`~/Library/Mobile Documents/com~apple~CloudDocs`), fournisseurs de fichiers macOS (`~/Library/CloudStorage/<Fournisseur>-…`, le nom du service vient du préfixe), `~/Dropbox`, `~/Nextcloud`, `~/Google Drive`, `~/OneDrive*` ; sous Windows, les dossiers désignés par `OneDrive`, `OneDriveConsumer`, `OneDriveCommercial`, puis `%USERPROFILE%\Dropbox`, `%USERPROFILE%\iCloudDrive`, `%USERPROFILE%\Nextcloud`.
2. **Marqueur** dans le dossier ou un parent jusqu'au dossier personnel : `.stfolder` (Syncthing), `.dropbox`, `.sync` (Resilio).
3. **Copies en conflit déjà présentes** : `therese 2.db` (suffixe d'iCloud), `conflicted copy` (Dropbox, Nextcloud), `.sync-conflict-` (Syncthing), `therese-<NOM-DU-PC>.db` (OneDrive).

Route `GET /api/data/emplacement`. Au démarrage, si le dossier est synchronisé, une notification « attention » par `create_notification` (`services/notification_service.py:35`), sauf si la même existe depuis moins de 30 jours. À l'écran : une `Alerte` (`components/ui/Alerte.tsx:38`, rôle `alert`) dans Confidentialité, et la ligne « Données » du Centre de confiance, qui affirme aujourd'hui « conservés sur ta machine » (`components/prototype/CapabilityCenter.tsx:587`), dit la vérité quand ce n'est plus le cas.

Texte : « Ton dossier THÉRÈSE est synchronisé par iCloud Drive. La clé qui ouvre ta base est dans le même dossier : elle part chez iCloud avec elle. Et si deux machines ouvrent THÉRÈSE en même temps, la base peut s'abîmer. Sors ce dossier de la synchronisation, et n'ouvre THÉRÈSE que sur une machine à la fois. » Après le lot 5, il ajoute : « Pour changer de machine, passe le relais (Confidentialité). »

### 4.10 L'écran « Passer le relais »

Dans Confidentialité (`components/settings/PrivacyTab.tsx`, à côté de la section des sauvegardes, `:306-400`), deux blocs :

- **Envoyer vers une autre machine** : phrase de passe (16 caractères au moins, bouton « Proposer une phrase »), puis la liste de ce que contient le fichier, dite en clair **avant** la création : ta base, la clé qui l'ouvre, tes clés d'API, les accès à tes boîtes mail (jetons Gmail, mots de passe IMAP, `models/entities.py:354-355`, `:363`) et la configuration de tes connecteurs. « Qui a ce fichier et sa phrase de passe a tout. » Puis le chemin du fichier et « Afficher le fichier ».
- **Recevoir d'une autre machine** : choix du fichier, phrase de passe, « Examiner ». L'écran montre l'état des lieux (§4.5), les avertissements de garde en phrases (« Cette machine a 3 contacts de plus qu'au dernier relais : ils seront perdus »), ce qui ne voyage pas, les connecteurs à réactiver. « Appliquer » exige une case cochée quand la garde parle ; il est absent quand une facture bloque. Après succès : « Redémarre THÉRÈSE. L'état d'avant relais est gardé, chiffré avec la phrase de passe du relais. »

Le mot « synchronisation » n'apparaît nulle part.

### 4.11 Hors périmètre, et lot B conditionnel

- **C** (journal chiffré et fusion) et **D** (instance jointe à distance) : hors périmètre, comme en V1. Pour D, le moteur n'écoute que 127.0.0.1 et rend son jeton à tout appel sans `Origin` (`main.py:694-708`).
- **Lot B, seulement si le relais manuel lasse** : dossier de relais choisi par l'utilisateur (archive déposée à la fermeture, proposée à l'ouverture, jamais appliquée sans geste) ; format `THBK2` chiffré par morceaux pour ne plus tenir l'archive en mémoire ; remappage des préfixes de chemins avec aperçu. Il touche la promesse publique (§10).

## 5. Lots, livrables un par un

Chaque lot suit la chaîne : tests écrits d'abord et vus rouges, code, sabotage ciblé par fonction, revue adverse du diff, recette dans l'application lancée.

### Lot 1 : l'alerte du dossier synchronisé (moteur, écran)

Livre §4.9. Aucune migration.

Tests à écrire en premier :

- `diagnostiquer`, tableau paramétré : chaque racine connue détectée avec le nom de son service ; un `~/.therese` ordinaire non détecté ; un `~/.therese` qui est un lien vers une racine iCloud détecté ; un `.stfolder` dans un parent détecté ; chaque motif de copie en conflit relevé ;
- variables d'environnement Windows (`OneDrive` et consorts) simulées ; le même test tourne sur le runner Windows de la CI avec de vrais chemins ;
- la notification est créée au premier démarrage et pas au second ;
- vitest : l'`Alerte` nomme le service quand le dossier est synchronisé et n'existe pas sinon ; la ligne « Données » du Centre de confiance change.

Critère observable : un `THERESE_DATA_DIR` placé dans un dossier iCloud Drive affiche l'alerte au lancement et dans Confidentialité.

### Lot 2 : identité, manifeste version 2, révisions connues (moteur, données)

Livre §4.1 à §4.3.

Tests à écrire en premier :

- `.installation.json` créé une fois, stable d'un démarrage à l'autre, absent de toute archive produite, régénéré avec un nouvel identifiant quand l'empreinte `machine` diffère ;
- chaque archive porte le manifeste version 2 complet ; `elements_couverts` lit encore une archive version 1 ;
- `REVISIONS_CONNUES` égale l'ensemble des révisions du dossier `alembic/versions` et contient la tête ;
- une base estampillée d'une révision inconnue, au schéma complet, n'est **pas** ré-estampillée et lève `RevisionInconnue` jusqu'à `init_db` ; le test existant `test_realignement_db_trackee_ancienne_schema_patche` (`tests/test_alembic_stamp.py:248`) reste vert.

Critère observable : copier la base d'une version future dans un dossier de test et lancer l'application affiche le message « mets l'application à jour » au lieu de démarrer.

### Lot 3 : émettre et examiner (moteur)

Livre §4.4, §4.5 et §4.8.

Tests à écrire en premier :

- **aller** entre deux `THERESE_DATA_DIR` aux clés différentes : A prépare un relais, B l'examine ; l'examen rend l'état des lieux ; la base, les fichiers et `.installation.json` de B sont identiques avant et après (empreintes comparées) ;
- **refus à l'examen**, sans rien modifier : mauvais en-tête, archive tronquée, mauvaise phrase de passe, taille au-delà du plafond, lien symbolique, dossier, chemin inexistant, chemin relatif ; autre `app_version` ; manifeste version 1 ; révision inconnue dans la base de l'archive ;
- **aucun clair sur disque** : une exception simulée à chaque étape de l'examen ne laisse aucun `.tar.gz` ni base temporaire dans `backups/` ;
- **émission** : phrase de passe de 15 caractères refusée, 16 acceptée ; la génération locale avance de un ;
- `list_backups` voit une archive dont le `.json` porte le chemin absolu d'une autre machine ;
- **sentinelle** « voyage ou reste » : un nom de dossier fabriqué et non classé la fait échouer.

Critère observable : sur une seule machine, deux profils `THERESE_DATA_DIR` ; le relais de l'un s'examine dans l'autre et décrit correctement ce qui arriverait.

### Lot 4 : appliquer, avec la garde (moteur)

Livre §4.6 et §4.7. Part **après** le chantier « mise au repos des écritures de fond ».

Tests à écrire en premier :

- **aller-retour** : A vers B, B relit une conversation, un contact chiffré et une clé d'API ; B vers A, A relit le travail fait sur B ;
- **garde** : B crée un contact après le relais, puis applique un relais plus ancien : refusé sans `confirme_ecrasement`, accepté avec ; B modifie un contact sans en créer : refusé de même ; une notification générée seule ne déclenche pas la garde ; une clé d'API ajoutée la déclenche ;
- **génération** : réappliquer sur A un relais qu'A a déjà dépassé est refusé sans confirmation ;
- **factures** : B a émis FACT-2026-012 absent de l'archive : refusé même avec confirmation ; un même numéro sous deux identifiants : refusé ;
- **archive de sécurité** : chiffrement simulé en échec, réponse 500 « rien n'a été modifié » et base de B identique octet pour octet ; trois relais successifs laissent trois archives de sécurité, le quatrième supprime la plus ancienne ;
- **connecteurs** : après application d'une archive étrangère, `MCPService().initialize()` sur le dossier ne lance aucun serveur, et une modification de connecteur avant redémarrage ne ressuscite pas l'ancienne liste ; une restauration locale de la même installation garde ses serveurs actifs ;
- **liste blanche** : une archive fabriquée qui contient `.installation.json`, `tools/x.py` ou `.session_token` est refusée avant toute destruction ;
- **révision inconnue** refusée avant toute destruction, sur la route du relais comme sur la restauration locale.

Critère observable : deux profils sur une machine, relais dans les deux sens, avec un contact et une facture créés de chaque côté pour voir la garde parler.

### Lot 5 : l'écran (écran)

Livre §4.10.

Tests vitest à écrire en premier, par rôle et par nom :

- le bouton « Proposer une phrase » remplit un champ de 29 caractères (25 plus quatre séparateurs), différent à chaque clic ;
- la liste de ce que contient le fichier est affichée avant la création ;
- l'état des lieux d'une réponse simulée : version incompatible (le bouton « Appliquer » n'existe pas), garde (case à cocher obligatoire), facture bloquante (pas de bouton, message) ;
- aucun texte ne contient « synchroniser » ni « synchronisation » ;
- l'alerte du lot 1 gagne la phrase « passe le relais ».

Critère observable : parcours complet au clavier seul.

### Lot 6 : recette réelle sur deux machines

macOS vers Windows 10, puis retour, avec de vraies données. Dr_logic travaille sous Windows 10, et le sel binaire comme `O_BINARY` ont déjà piégé les tests (`services/encryption.py:31-38`).

## 6. Données et migrations

- **Aucune révision Alembic.** La tête reste `b8c9d0e1f2a3` (`models/database.py:619`).
- **La preuve d'estampillage change de nature**, pas de contenu : elle ne ré-estampille plus une révision hors de `REVISIONS_CONNUES`, et son erreur ne sera plus avalée. Toute révision future (celle de P-105, par exemple) devra entrer dans `ALEMBIC_HEAD_REVISION`, dans `REVISIONS_CONNUES` et dans la preuve de schéma ; `tests/test_alembic_stamp.py` y veille.
- **Un fichier nouveau**, `.installation.json`, hors base et hors archive.
- **Purge totale** : `.installation.json` garde son identifiant, mais `dernier_relais` est vidé, puisque sa signature dérive de données effacées.
- **Export RGPD** : inchangé.

## 7. Risques restants

- **Perte de données.** Le relais remplace tout. La garde, les trois archives de sécurité et le refus sur les factures sont les protections ; aucune ne suffit seule. Les tables exclues de la signature ne sont pas protégées : le journal d'activité de B depuis le dernier relais, par exemple, est remplacé par celui de A (il reste dans l'archive de sécurité).
- **Sécurité.** L'archive contient la clé maîtresse, les clés d'API, les jetons Gmail, les mots de passe IMAP et la configuration des connecteurs. Qui a le fichier et la phrase de passe a tout. PBKDF2 à 480 000 itérations et 16 caractères au moins limitent l'attaque hors ligne sans la rendre impossible.
- **Archive fabriquée par un tiers qui connaît la phrase de passe.** Connecteurs désactivés et liste blanche ferment les deux voies d'exécution relevées. Elle peut encore déposer des consignes dans `THERESE.md` ou le profil ; le portillon des outils reste fail-closed, rien ne part sans carte.
- **Mémoire.** L'archive est tenue entière en mémoire ; au-delà du plafond, le relais est impossible avant le lot B, et l'écran le dit.
- **Clair transitoire à la création.** L'archive est d'abord écrite en clair dans `backups/`, puis chiffrée (`routers/data.py:1268-1288`) ; un arrêt brutal entre les deux laisse un clair à côté de la base. C'est antérieur à cette RFC, et l'exposition est celle du dossier de données lui-même, sauf si ce dossier est synchronisé : l'alerte du lot 1 couvre ce cas.
- **Identité de machine** fondée sur le nom d'hôte : un changement de nom régénère l'identité. Effet sans danger : une confirmation de plus au prochain relais, des connecteurs à réactiver à la main.
- **Faux positifs de la garde** : une réparation de données faite au démarrage, ou une purge RGPD automatique des contacts (`main.py:369-383`), change la signature. La garde demande alors une confirmation de trop ; c'est le sens prudent.
- **Usage simultané** non pris en charge ; détecté seulement au moment du relais.
- **Liste blanche sur la restauration locale.** Une ancienne archive qui porterait un nom hors de la liste des cibles serait refusée. Aucune n'est connue, mais les archives d'avant 0.40 n'ont pas été relues pour cette RFC : les archives témoins de `tests/test_backup_complete.py` le diront au lot 4, et un nom légitime trouvé là entrera dans la liste.
- **Chantier « mise au repos »** : tant qu'il n'a pas livré, les cas B-1291, B-1293 et B-1265 s'appliquent à toute restauration ; c'est pourquoi le lot 4 part après lui.

## 8. Réponse à la revue

| Gravité | Constat de la revue | Réponse | Où dans la V2 |
|---|---|---|---|
| P2 | Aucun contrôle de version : une archive plus récente s'importe dans une application plus ancienne, et la base est ré-estampillée à la tête locale. | **Accepté.** Manifeste interne version 2 (`app_version`, révision, installation, génération) ; égalité stricte des versions sur le relais (décision 14) ; révision lue dans la base de l'archive et refusée si inconnue, avant toute destruction ; au démarrage, plus de ré-estampillage d'une révision inconnue (`models/database.py:677`, `:762-766`) et plus d'erreur avalée (`:784-785`). Test : « archive d'une version plus récente refusée avant toute étape destructive ». | §4.2, §4.3, §4.5, lots 2 à 4 |
| P2 | Importer une archive revient à importer des commandes lancées au démarrage suivant. | **Accepté.** Connecteurs d'une autre installation désactivés à l'extraction, listés « à réactiver » avec leur commande (décision 15) ; service MCP en mémoire rechargé sans démarrage. Test : « serveur importé non lancé ». | §4.7, lot 4 |
| P2 | Une seule archive de sécurité, effacée à chaque import. | **Accepté.** Trois gardées (décision 16) ; chiffrées avant toute destruction, et l'application refusée si ce chiffrement échoue. | §4.7, lot 4 |
| P2 | La garde contre l'écrasement n'a pas de mécanisme ; un identifiant rangé en base voyagerait. | **Accepté, avec une variante motivée.** Identité et génération dans `.installation.json`, hors base et hors archive, protégé par l'extraction en liste blanche. À la place d'un compteur incrémenté par les routes d'écriture, une signature par table métier comparée au dernier relais : elle voit aussi les modifications, et une route oubliée ne peut pas la rendre muette. Comparaison décrite ; les tests demandés par la revue y figurent, plus un refus sans appel sur les factures. | §4.1, §4.6, lots 2 et 4 |
| P3 | La liste de « ce qui ne voyage pas » est incomplète ; il faut la dériver des cibles. | **Accepté.** Liste générée depuis les cibles de l'archive, avec les éléments relevés par la revue ; sentinelle sur chaque nom construit sous le dossier de données. | §4.8, lots 3 et 5 |
| P3 | La RFC ne cite que la clé maîtresse ; l'archive porte aussi les accès aux boîtes mail et aux connecteurs. | **Accepté.** L'écran les nomme au choix de la phrase de passe, avant la création du fichier. | §4.10, lot 5 |
| P3 | La RFC ne dit pas comment le fichier arrive au serveur. | **Tranché** : chemin local choisi par la boîte native, validé (fichier régulier, taille, en-tête) avant toute lecture, puis copié par blocs. Pas d'envoi dans la requête, qui doublerait la mémoire. | §4.5, lot 3 |
| P3 | L'alerte « dossier synchronisé » est le lot le moins cher et le plus urgent. | **Accepté** (décision 17) : lot 1. | §4.9, lot 1 |
| P3 | « Neuf magasins Zustand » : dix fichiers appellent `persist(`. | **Réfuté.** Le dixième fichier est un test, `stores/invoiceStore.filtresRelus.test.ts:4`, dont un commentaire cite `persist()` ; les neuf magasins réels sont listés au §3. La V2 ne compte plus : ce qui reste dans l'interface est déclaré par l'écran. | §3, §4.8 |

## 9. Livraison

Ordre : lot 1, lot 2, lot 3, puis lot 4 après le chantier « mise au repos », lot 5, lot 6. Le lot 1 ne dépend de rien et peut partir seul dans la prochaine version. Revue adverse du design de ce document avant le lot 1, sécurité d'abord ; revue du diff à chaque lot. Aucune release sans le GO de Ludo.

## 10. Questions réservées à Ludo

1. **Le lot B et la promesse publique.** Le README promet « Ton contexte reste sur ta machine, jamais envoyé à un serveur Synoptïa » (`README.md:34`). Le relais manuel ne change rien à cette phrase, puisque l'utilisateur déplace lui-même un fichier chiffré. Le lot B, lui, déposerait ce fichier de façon automatique dans un dossier synchronisé par un tiers. **Recommandation** : ne lancer le lot B que sur une demande exprimée, et le jour venu écrire « tes données restent sur tes machines ; le relais, chiffré, passe par le dossier que tu choisis ».
2. **Les mots publics.** Notes de version et réponse à Dr_logic sur Discord : dire « relais », jamais « synchronisation », et « une machine à la fois ». **Recommandation** : oui, et répondre à Dr_logic dès la livraison du lot 1, en lui disant de sortir `~/.therese` de sa synchronisation actuelle en attendant le relais.

## Annexe : appuis dans le code

- Origine : `.app-loop/proposals.json`, P-108.
- Sauvegarde : `routers/data.py:1058-1127` (archive, cibles `:1075-1091`, manifeste `:1116`), `:1223-1319` (création, phrase de passe `:1249-1266`), `:1322-1353` (liste).
- Restauration : `routers/data.py:1455-1708` ; archive de sécurité `:1356-1438` ; retour arrière `:1542-1557`.
- Chiffrement : `services/encryption.py:40-61` (fichier de clé, compte de trousseau par dossier), `:470-485` (clé de base par HKDF), `:520-568` (format `THBK1`).
- Estampillage : `models/database.py:613-785`.
- Connecteurs : `services/mcp_service.py:288-372` ; démarrage `main.py:301-315`.
- Notifications : `services/notification_service.py:35` ; planificateurs `main.py:341-383`.
- Écran des sauvegardes : `components/settings/PrivacyTab.tsx:306-400` ; appels `services/api/data.ts:88-116`.
