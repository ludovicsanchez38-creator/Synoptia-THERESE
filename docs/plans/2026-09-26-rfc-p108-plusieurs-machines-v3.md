# RFC P-108, version 3 : reprendre son travail sur une autre machine

Rédigé le 26/09/2026. Remplace la V2 (`docs/plans/2026-09-26-rfc-p108-plusieurs-machines-v2.md`), refusée (NO-GO) par la revue adverse du 26/09 (15 constats : un P1, cinq P2, neuf P3 ; rapport de travail `revue-v2-p107-p108.md` de l'orchestrateur). Les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 14 à 17) restent des faits. Aucun code avant la validation de ce document.

**Base de vérification.** Toutes les lignes citées ont été relues au commit `d80d4406` (26/09/2026, 02 h 37), par `git show d80d4406:<fichier>`, jamais dans l'arbre de travail. Les numéros de `routers/data.py` ont glissé depuis la base de la V2 (`ca9f44d1`) : de dix rangs à partir de la ligne 1037, de vingt-sept à partir de 1214, de trente-quatre à partir de 1693 (B-1497, B-1498), et au-delà encore après l'import des conversations (B-1483). Ceux de `routers/calendar.py` aussi (B-1487). Aucun numéro de ces deux fichiers n'est recopié de la V2. Chemins relatifs à `src/backend/app/` (fichiers `.py`), à `src/frontend/src/` (fichiers `.ts` et `.tsx`) et à `src/frontend/src-tauri/src/` (fichiers `.rs`) ; les tests et `docs/` partent de la racine du dépôt.

**Prérequis corrigés à part par l'orchestrateur**, cités par leur numéro et jamais recodés ici :

- **B-1497** (corrigé, `bb2e5919`) : la restauration n'extrait que les entrées d'une sauvegarde. `NOMS_D_ARCHIVE` (`routers/data.py:1037-1043`) et `_membre_attendu` (`:1214-1231`) refusent l'archive entière, avant toute écriture, dès qu'un membre n'est ni un fichier ni un dossier, contient `..`, commence par `/`, porte une barre oblique inverse ou sort de la liste. `tests/test_b1497_extraction_sauvegarde.py` reprend les deux sondes de la revue.
- **B-1498** (corrigé, `55c051b5`) : `recharger_la_configuration` (`services/mcp_service.py:297-309`) arrête les connecteurs, vide la liste en mémoire, relit `mcp_servers.json` et ne démarre rien ; elle est appelée à la fin de toute restauration (`routers/data.py:1693-1699`).
- **Chantier « mise au repos des écritures de fond »** (décision 1 de P-105) : le lot 4 part après lui, comme en V2.

## 0. Constats de la revue V2 et leur traitement

| # | Gravité | Constat | Traitement | Où |
|---|---|---|---|---|
| 1 | P1 | La liste blanche par premier segment se contourne par `outputs/../x` et par un lien interne | **Corrigé à part (B-1497).** Les deux suggestions restantes tombent : la casse repliée est inutile parce que la liste est comparée exactement et que tout le reste est refusé (une variante de casse est refusée, jamais confondue avec un nom attendu) ; l'extraction dans un dossier vide est inutile parce que tous les membres sont contrôlés avant la première écriture (`routers/data.py:1239-1244`). P-108 réutilise `NOMS_D_ARCHIVE` comme seule liste blanche : `.installation.json` n'y figure pas, aucune archive ne peut donc l'écrire. **Conséquence relevée** : une sauvegarde d'un dossier qui contient un lien est désormais irrestaurable, reproduit (défauts ci-dessous) | §4.7, lot 4 |
| 2 | P2 | La copie de relais devient une sauvegarde ordinaire que « Restaurer » applique sans garde | **Accepté.** Les copies de relais vivent dans `backups/relais/`, hors de la liste des sauvegardes : `list_backups` ne lit que `backups/*.json`, sans descendre (`routers/data.py:1359`), et `restore_backup` refuse tout nom qui contient `/` (`:1501`). La route locale lit le manifeste avant toute destruction et refuse une archive d'une autre installation ; une archive d'avant ce chantier y garde un chemin, avec révision contrôlée, connecteurs désactivés et garde des factures | §4.8, lot 4 |
| 3 | P2 | Le refus d'une révision inconnue arrive après les écritures d'`init_db` | **Accepté.** Le contrôle passe en tête d'`init_db`, avant la migration de chiffrement (`models/database.py:996`) et avant `create_all` (`:1113`), en lecture seule. Test : la base refusée reste identique octet pour octet | §4.3, lot 2 |
| 4 | P2 | Le message n'atteint pas l'écran : `sidecar-error` n'est émis qu'à l'échec du lancement, et le moteur est relancé trois fois | **Accepté.** Code de sortie dédié, fichier d'état, branche sans relance à côté de celle du code 0 (`lib.rs:451-454`), événement à charge structurée, écran qui choisit son texte par le motif et jamais par le texte reçu, sans « xattr » | §4.3, lot 2 |
| 5 | P2 | Des tables métier sont réécrites en arrière-plan ; la garde parlerait à chaque relais | **Accepté.** La signature exclut les colonnes volatiles, les agendas distants et leurs événements (copies d'un service), et les préférences techniques, sous sentinelle. Les lignes que la revue cite pour l'agenda sont périmées : les écritures de `synced_at` sont à `routers/calendar.py:399`, `:705`, `:982` | §4.6, lot 4 |
| 6 | P2 | Le conflit de numéros bloque les deux sens pour toujours | **Accepté.** Une sortie sans perte : les pièces en conflit sont mises de côté (fichier permanent, jamais élagué), puis acquittées une par une. Et une prévention : émettre une facture après avoir passé le relais déclenche un avertissement. Au passage, un défaut existant : une facture émise se supprime ou repasse en brouillon, relevé à reproduire | §4.6, lots 4 et 5 |
| 7 | P3 | Une facture envoyée puis repassée en brouillon échappe au critère `status` | **Accepté.** Critère : `sent_at IS NOT NULL OR status <> 'draft'` | §4.6, lot 4 |
| 8 | P3 | L'examen lit une base en retard quand le point de contrôle WAL a échoué | **Accepté.** La base, `therese.db-wal` et `therese.db-shm` sont extraits ensemble dans le temporaire, à l'examen comme à l'application | §4.5, lots 3 et 4 |
| 9 | P3 | Deux tests existants posent une révision inconnue | **Accepté.** `tests/test_variables.py` : l'aide `_base_legacy` (`:248`, révision `ancienne_tete` à `:270`) et ses deux tests d'estampille (`:293`, `:308-317`) passent à une révision connue. `tests/test_alembic_stamp.py` n'utilise que des révisions du dossier et ne change pas | lot 2 |
| 10 | P3 | Après une rétrogradation, l'application ne démarre plus, sans issue décrite | **Accepté.** Le message et la documentation disent la conduite : réinstaller la dernière version, ou restaurer une sauvegarde faite avec la version installée | §4.3, lot 2 |
| 11 | P3 | L'état d'avant relais est chiffré avec la phrase du relais, sans que l'utilisateur le sache | **Accepté.** L'écran le dit avant « Appliquer » | §4.11, lot 5 |
| 12 | P3 | Les applications en échec occupent les trois places ; les copies de relais ne sont jamais élaguées | **Accepté.** Seules les applications réussies comptent ; l'archive d'un échec n'est gardée que si le retour arrière a échoué ; la copie reçue est retirée après succès ; les copies émises sont listées avec leur taille et supprimables, et leur élagage automatique est posé à Ludo | §4.7, §10 |
| 13 | P3 | Les clairs transitoires se multiplient, et rien ne balaie ceux qu'un arrêt brutal laisse | **Accepté, avec une réserve de prudence** : au démarrage, seuls les doubles en clair d'un contenu qui existe ailleurs sont supprimés ; une archive de sécurité en clair, qui peut être la seule copie de l'état d'avant une restauration interrompue, n'est jamais supprimée d'office. Défaut existant, relevé à reproduire | §4.12, lot 3 |
| 14 | P3 | Sur un dossier synchronisé, l'empreinte fait réécrire `.installation.json` sans fin | **Accepté.** Empreinte fondée sur l'identifiant stable de la machine ; identité figée, relais refusé, quand le dossier est détecté comme synchronisé | §4.1, lots 1 et 2 |
| 15 | P3 | `_load_config` ne vide pas la liste en mémoire | **Corrigé à part (B-1498).** P-108 désactive les connecteurs dans le fichier extrait, puis s'appuie sur la relecture de B-1498. Test : la liste en mémoire égale celle du fichier, tous désactivés | §4.7, lot 4 |

### Défauts du code actuel relevés en relisant, hors de toute RFC

- **Reproduit : une sauvegarde qui contient un lien est irrestaurable depuis B-1497.** `_create_archive` ajoute chaque dossier par `tar.add` récursif (`routers/data.py:1122-1125`), qui range un lien symbolique tel quel ; `_membre_attendu` refuse tout membre qui n'est ni fichier ni dossier (`:1226`). Recette de la sonde : un dossier `outputs/` qui contient `devis.pdf` et un lien symbolique `raccourci.pdf -> devis.pdf` ; `tar.add(str(src), arcname="outputs")` comme à `routers/data.py:1124` ; puis `_safe_extractall` du dépôt, qui répond « Archive de sauvegarde non sûre : elle contient un chemin ou un lien inattendu » (sonde de travail : `/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-6213c477b4c6/scratchpad/sonde_lien_sauvegarde/sonde.py`, lancée à `d80d4406`). À ficher. Recommandation : écarter les liens à l'archivage et les nommer dans la réponse, pour que l'erreur apparaisse à la sauvegarde et non à la restauration. **Prérequis du lot 3.**
- **À reproduire : une facture émise se supprime, ou repasse en brouillon.** `delete_invoice` ne lit aucun statut (`routers/invoices.py:655-681`) ; `PATCH` accepte le retour à `draft` (`:586-588`) ; l'écran montre « Supprimer » sur toute ligne (`components/invoices/InvoicesPanel.tsx:525-538`). Une facture émise ne se supprime pas : elle s'annule par un avoir.
- **À reproduire : un arrêt brutal pendant une restauration laisse l'archive en clair**, clé comprise : la copie déchiffrée `.<nom>.restore.tar.gz` (`routers/data.py:1541`) et l'archive de sécurité `pre_restore_*.tar.gz` (`:1557-1558`, `:1625`). B-1269 n'a fermé que l'annulation pendant `begin()`.

## 1. Ce que la V3 change

- **Les copies de relais ne sont plus des sauvegardes** : dossier à part, jamais restaurables par « Restaurer ».
- **La route locale a ses contrôles** : révision, origine, connecteurs, factures.
- **Le refus d'une base plus récente se fait avant toute écriture**, et il arrive à l'écran avec son propre texte.
- **La signature ignore ce que THÉRÈSE réécrit toute seule.**
- **Un conflit de numéros a une sortie**, sans perte de pièce, et une prévention.
- **L'identité d'installation tient sur un dossier synchronisé.**
- **Les archives en clair sont balayées au démarrage**, sauf celle qui peut être la dernière copie d'un état.
- **B-1497 et B-1498 sont des prérequis corrigés** ; la V3 s'appuie dessus au lieu de les recoder.

## 2. Décisions

Inchangées (V2, §2) : décisions 14 à 17, usage alterné, phrase de passe de 16 caractères avec proposition générée, consentements qui ne voyagent pas, Qdrant qui voyage, redémarrage exigé, vocabulaire « relais ».

## 3. Ce qui existe

Les points d'appui et les manques de la V2 (V2, §3) restent vrais, relus à la base, avec deux changements :

- **L'extraction est fermée par B-1497** : il n'est plus exact que « l'extraction prend tout ».
- **La liste des connecteurs en mémoire suit la restauration** (B-1498), sans démarrage.

Numéros à jour pour ce qui sert à la conception : cibles de l'archive `routers/data.py:1085-1101` ; compagnons WAL `:1103-1117` ; manifeste version 1 `:1126` ; création chiffrée `:1250-1330` (archive en clair `:1296`, chiffrement `:1306`, suppression du clair `:1314-1315`) ; liste `:1349-1380` ; archive de sécurité `:1383-1465` ; restauration `:1482-1735` (validation du nom `:1501`, clair déchiffré `:1541`, archive de sécurité `:1557-1558` et `:1625`, extraction `:1639-1646`, échecs `:1649-1686`, relecture des connecteurs `:1693-1699`, finalisation `:1716`).

## 4. Conception

### 4.1 L'identité d'installation

`.installation.json` dans le dossier de données, écrit de façon atomique, permissions 0600, hors de la base et hors de l'archive (inchangé, V2 §4.1), avec une empreinte `machine` refaite :

- **`machine` = SHA-256 de l'identifiant stable de la machine et du dossier de données résolu.** L'identifiant : `IOPlatformUUID` sous macOS (`ioreg -rd1 -c IOPlatformExpertDevice`), `MachineGuid` sous Windows (registre `HKLM\SOFTWARE\Microsoft\Cryptography`), `/etc/machine-id` sous Linux. Le nom d'hôte ne sert plus : il peut changer avec le réseau ou recevoir un suffixe en cas de conflit de nom. Si l'identifiant est illisible, repli sur le nom d'hôte, noté `"empreinte": "faible"`.
- **Empreinte étrangère, dossier non synchronisé** : l'identité est régénérée une fois (nouvel `installation_id`, `dernier_relais` vidé), comme en V2.
- **Empreinte étrangère, dossier synchronisé** (diagnostic du lot 1) : le fichier n'est **pas** réécrit. L'identité est marquée « figée » en mémoire, le relais (émission et application) est refusé avec le texte de l'alerte du lot 1, et l'alerte ajoute : « Deux machines utilisent le même dossier THÉRÈSE. » Sans cela, chaque machine réécrirait le fichier à son tour et le service de synchronisation le renverrait à l'autre, sans fin, avec des copies en conflit du fichier qui porte la garde.

### 4.2 Le manifeste interne, version 2

Inchangé (V2, §4.2).

### 4.3 Les révisions connues, et un refus qui arrive à l'écran

**`REVISIONS_CONNUES`** : tuple épinglé des 17 révisions de `src/backend/alembic/versions/`, à côté de `ALEMBIC_HEAD_REVISION` (`models/database.py:619`), tenu par `tests/test_alembic_stamp.py` (inchangé, V2 §4.3).

**Le contrôle, en tête.** `verifier_revision_connue(db_path)` est appelé par `init_db` (`models/database.py:975`) juste après la création du dossier parent (`:982`), avant la migration de chiffrement (`:996-1034`), avant `create_all` (`:1113`), les `ALTER TABLE` (`:1131-1141`), les migrations ad hoc qui réparent des totaux de factures (`:1167`, `reparer_totaux_tva_non_applicable` `:210`) et l'estampille (`:1173`). Il ouvre la base en lecture seule, lit `alembic_version`, et lève `RevisionInconnue` si la révision n'est pas dans `REVISIONS_CONNUES`. Une base sans table `alembic_version` (ancienne) passe ; une base illisible (clé d'une autre machine) passe aussi, pour laisser l'erreur actuelle de clé (`:1025-1034`) dire la vraie cause. `ensure_alembic_stamp` garde en plus le refus de la V2 (`:677`), relancé hors du `except` qui avale tout (`:784-785`), comme second filet.

**La sortie.** Le cycle de vie (`main.py:193`) attrape `RevisionInconnue`, écrit `.demarrage_refuse.json` dans le dossier de données (`{"motif": "donnees_plus_recentes", "revision": "…", "version": "…"}`), puis quitte avec un code dédié, `CODE_DONNEES_PLUS_RECENTES = 78`. Un simple `raise` ne suffirait pas : uvicorn sort alors avec un code générique, que la couche Rust prend pour un plantage et relance trois fois (`lib.rs:404-418`), ce qui rejouerait l'ouverture à chaque fois.

**La couche Rust.** `handle_sidecar_termination` (`lib.rs:436-459`) traite déjà le code 0 comme un arrêt voulu, sans relance (`:451-454`). Le code 78 suit la même branche et émet un événement `sidecar-refus` à charge structurée (`{"motif": "donnees_plus_recentes"}`). La décision est une fonction pure, `reaction_a_la_sortie(code)`, hors du bloc `#[cfg(not(debug_assertions))]`, pour être testable. Il n'existe aujourd'hui aucun test Rust ni aucun `cargo test` dans la CI : le lot 2 ajoute le module de test et l'étape de CI, ou, si l'étape est refusée, la recette de l'application packagée vérifie le cas.

**L'écran.** `SplashScreen` écoute `sidecar-refus` et choisit son texte dans une table par motif, jamais par le texte reçu (doctrine D4). Texte du motif `donnees_plus_recentes` : « Tes données ont été enregistrées par une version plus récente de THÉRÈSE. Installe la dernière version, puis relance. Si tu viens de revenir à une version plus ancienne, réinstalle la plus récente, ou restaure une sauvegarde faite avec la version installée. Rien n'a été modifié. » Pas de « xattr », qui ne concerne que l'écran de `sidecar-error` (`components/SplashScreen.tsx:113-120`). La documentation utilisateur reçoit le même paragraphe sur la rétrogradation.

### 4.4 Émettre un relais

Inchangé (V2, §4.4), avec trois précisions :

- l'archive est écrite dans `backups/relais/emis/`, jamais dans `backups/` : elle n'apparaît pas parmi les sauvegardes ;
- elle est d'abord écrite sous un nom temporaire en clair `.relais_<horodatage>.creation.tar.gz`, puis chiffrée ; le balayage du §4.12 reconnaît ce nom ;
- l'émission est refusée tant que l'identité est figée (§4.1).

### 4.5 Recevoir : arrivée du fichier et examen

Inchangé (V2, §4.5), avec ces changements :

- **La copie arrive dans `backups/relais/recus/`**, avec son `.json` à côté, hors de la liste des sauvegardes (constat 2).
- **L'examen extrait la base et ses deux compagnons** (`therese.db`, `therese.db-wal`, `therese.db-shm`) dans un dossier temporaire `backups/relais/.examen-<horodatage>/`, et l'ouvre là, avec la clé de l'archive. SQLite rejoue le WAL à l'ouverture : révision, factures et signature se lisent sur l'état complet. L'archive range ces compagnons à part quand le point de contrôle était incomplet (`routers/data.py:1103-1117`). Le dossier temporaire est effacé dans un `finally`.
- **La réponse** gagne `pieces_en_conflit` (§4.6) et `identite_figee`.

### 4.6 La garde contre l'écrasement

Trois contrôles, refaits à l'application et jamais repris de l'examen (V2, §4.6), avec ces changements.

**Contrôle 2, signature métier : ce qu'elle ne compte pas.**

- **Colonnes volatiles**, exclues de toutes les tables : `updated_at`, `synced_at`, `last_sync`, `last_sync_error`, `access_token`, `refresh_token`, `token_expiry`. Relevé : le rafraîchissement d'un jeton Gmail réécrit `access_token`, `token_expiry` et `updated_at` d'`email_accounts` (`routers/email.py:304-311`) ; la synchronisation d'un agenda réécrit `synced_at` (`routers/calendar.py:399`, `:705`, `:982`).
- **Copies d'un service distant**, exclues : les lignes de `calendars` dont `provider` n'est pas `local` (`models/entities.py:487`) et les événements de ces agendas. Les agendas locaux et leurs événements restent métier.
- **Préférences techniques**, exclues par clé : `crm_last_sync` (`services/crm_utils.py:753`), les jetons OAuth du CRM (catégorie `oauth`, `routers/crm.py:1036`). Les autres préférences (profil, clés d'API, réglages) restent comptées.
- **Sentinelle** : toute colonne d'une table métier dont le nom se termine par `_token`, `_expiry`, `_at` hors `created_at`, ou contient `sync`, figure soit dans la liste des colonnes volatiles, soit dans une liste « métier malgré le nom » avec un motif (par exemple `sent_at`, qui date un envoi et doit compter). Une colonne nouvelle non classée fait échouer la suite. Toute clé de préférence écrite par un service en arrière-plan est classée de même.

**Contrôle 3, factures : le critère.** Une pièce est **émise** quand `sent_at IS NOT NULL OR status <> 'draft'` (`models/entities.py:812`, `:825`). Une facture envoyée puis repassée en brouillon garde son `sent_at` (`routers/invoices.py:684-688`) et reste protégée.

**Contrôle 3, deux cas et deux sorties.**

- **Pièce émise ici, absente de l'archive, sans autre pièce sous ce numéro** : refus. « Cette machine a émis FACT-2026-012, absente de ce relais. Passe d'abord le relais de cette machine vers l'autre. » Ce chemin aboutit tant que l'autre machine n'a pas elle-même émis sous les mêmes numéros.
- **Même numéro, pièce différente** : les deux machines ont émis, chacune de son côté, une pièce différente sous le même numéro. La numérotation est déjà rompue chez les clients : le relais ne peut pas la réparer, seulement ne rien perdre et ne pas bloquer pour toujours. La sortie :
  1. l'examen liste chaque conflit : la pièce d'ici (numéro, client, montant TTC, date d'envoi) et celle du relais sous le même numéro ;
  2. « Mettre de côté ces pièces » (`POST /api/data/relais/mettre-de-cote`) écrit, pour chaque pièce d'ici en conflit, son contenu complet (pièce, lignes, client) en JSON et son PDF quand le profil d'émetteur le permet, dans `backups/relais/pieces-ecartees/<date>/`. Ce dossier n'est jamais élagué ; il est listé à l'écran et ne se vide que par ton geste ;
  3. l'application accepte `pieces_acquittees`, la liste des numéros que tu as retapés un par un. Elle refuse si un conflit n'est pas acquitté, ou si sa pièce n'a pas été mise de côté (fichier absent ou d'un autre identifiant) ;
  4. après succès, l'écran dit : « Les pièces mises de côté ne sont plus dans THÉRÈSE. Si elles ont été envoyées, leur numéro est aussi porté par une autre pièce : fais-les annuler par un avoir et réémettre sous un numéro neuf. THÉRÈSE peut émettre cet avoir, sans lien vers la pièce absente (le lien d'un avoir exige une facture présente, `routers/invoices.py:424-435`) : cite son numéro dans les notes. »

  Motif : la V2 refusait sans appel des deux côtés, ce qui interdisait tout relais ultérieur ; accepter sur une simple case perdrait une pièce légale. La mise de côté permanente garde tout, et l'acquittement numéro par numéro fait porter le geste par la personne qui sait ce qu'elle a envoyé.
- **Prévention.** `GET /api/data/relais/etat` rend `dernier_relais`. Tant que le dernier relais connu est « émis » et qu'aucun relais n'a été reçu depuis, le formulaire de facture affiche, au passage à « envoyé » ou à « payé », un avertissement non bloquant : « Tu as passé le relais à une autre machine le 26/09. Émettre ici risque un numéro en double avec l'autre machine. » C'est la cause du conflit, prise à sa source.

Les contrôles 1 et 2 refusent l'application sauf confirmation explicite (inchangé).

### 4.7 Appliquer

Inchangé (V2, §4.7) sur le cœur partagé avec `restore_backup` et l'archive de sécurité chiffrée avant toute destruction, avec ces changements :

- **Liste blanche** : `NOMS_D_ARCHIVE` (B-1497), seule liste, pour les deux routes. Le relais n'en ajoute aucune.
- **Base et compagnons WAL** extraits ensemble pour les contrôles refaits (§4.5).
- **Connecteurs** : quand l'installation émettrice diffère de la locale, ou manque, chaque serveur du `mcp_servers.json` extrait passe à `"enabled": false` avant la vérification de la base ; puis la relecture de B-1498 (`routers/data.py:1693-1699`) remplace la liste en mémoire par celle du fichier, sans rien démarrer.
- **Rétention** (décision 16) : les métadonnées de l'archive de sécurité portent `kind` (`pre_restore` ou `pre_relais`) et `issue` (`reussie`, `echec`). `_prune_pre_restore_backups` (`routers/data.py:1407`) garde les trois plus récentes d'issue `reussie` ; une archive d'issue `echec` n'est gardée que si le retour arrière a échoué, car elle porte alors le seul état d'avant, sinon elle est supprimée puisque le retour arrière a remis ce même état. Une archive ancienne sans `issue` compte comme réussie.
- **Copie reçue** : supprimée après une application réussie. Son contenu est devenu la base en service, l'état d'avant est dans l'archive de sécurité, et le fichier d'origine reste où tu l'as choisi.
- **Copies émises** : jamais élaguées d'office ; listées avec leur date et leur taille, et supprimables d'un geste. L'élagage automatique est posé à Ludo (§10).

### 4.8 La route locale « Restaurer »

`restore_backup` lit le manifeste de l'archive déchiffrée **avant** l'archive de sécurité et toute destruction (`routers/data.py:1625`) :

| Archive | Conduite |
|---|---|
| Version 2, d'une autre installation | refus 409 : « Cette sauvegarde vient d'une autre machine : ouvre-la par « Recevoir d'une autre machine ». » Tous les contrôles du relais s'y appliqueront |
| Version 2, de cette installation | comportement actuel, plus révision connue et garde des factures en confirmation |
| Version 1 (avant ce chantier) | comportement actuel, plus révision connue, connecteurs désactivés (origine inconnue) et garde des factures en confirmation |

**Pourquoi une confirmation, et non un refus, sur la route locale.** Une sauvegarde locale sert à se relever d'une panne ; la refuser parce qu'une facture a été émise depuis laisserait quelqu'un sans issue. La garde liste donc les pièces émises absentes de la sauvegarde, propose la même mise de côté qu'au §4.6, et demande une case cochée. Une archive d'avant ce chantier venue d'une autre machine et posée à la main dans `backups/` passe par ce chemin : c'est la situation d'aujourd'hui, désormais avec la liste des pièces et leur mise de côté.

**Pourquoi les connecteurs d'une archive version 1 arrivent désactivés.** Rien ne prouve son origine ; une restauration de sa propre sauvegarde ancienne demande de réactiver ses connecteurs, listés « à réactiver ». C'est un changement de comportement, dit dans la réponse de la restauration.

### 4.9 Ce qui voyage, ce qui reste, ce qui est à rebrancher

Inchangé (V2, §4.8), avec `backups/relais/` classé « reste ».

### 4.10 L'alerte du dossier synchronisé

Inchangée (V2, §4.9), avec la phrase du §4.1 quand deux machines partagent le dossier.

### 4.11 L'écran « Passer le relais »

Inchangé (V2, §4.10), avec :

- **avant « Appliquer »**, la phrase : « L'état de cette machine d'avant le relais sera gardé, chiffré avec la phrase de passe de ce relais. Garde cette phrase : sans elle, cet état ne se rouvre pas. » Quand la phrase a été proposée par l'écran, la même phrase est rappelée à l'émission ;
- **les conflits de numéros** : la liste du §4.6, le bouton « Mettre de côté ces pièces », puis un champ par numéro à retaper ;
- **les copies émises** : liste avec date, taille et « Supprimer » ;
- **l'identité figée** : le bloc est remplacé par le texte de l'alerte du lot 1.

### 4.12 Le balayage au démarrage

Au démarrage, après `init_db` et avant de servir, un balayage de `backups/` ne regarde que des noms temporaires connus :

| Nom | Conduite | Motif |
|---|---|---|
| `.<nom>.restore.tar.gz` | supprimé si `<nom>.tar.gz.enc` existe | double en clair d'une archive chiffrée (`routers/data.py:1541`) |
| `.<nom>.creation.tar.gz` | supprimé | la création d'une sauvegarde ou d'un relais ne modifie pas les données ; le clair n'est qu'un intermédiaire |
| `relais/.examen-*` | supprimé | l'examen ne modifie rien |
| `pre_restore_*.tar.gz` sans `.enc` | **gardé**, et une alerte dans Confidentialité : « Une restauration a été interrompue. L'état d'avant est gardé en clair : chiffre-le avec une phrase de passe, ou supprime-le. » | après un arrêt brutal au milieu d'une restauration, cette archive peut être la seule copie de l'état d'avant |

Aucune ancienne sauvegarde en clair (`<nom>.tar.gz` avec son `.json`) n'est touchée. Pour que le nom temporaire de création existe, `create_backup` écrit son clair sous `.<nom>.creation.tar.gz` au lieu de `<nom>.tar.gz` (`routers/data.py:1296`).

### 4.13 Hors périmètre

Inchangé (V2, §4.11).

## 5. Lots

Chaîne de chaque lot : tests écrits d'abord et vus rouges, code, sabotage ciblé par fonction, revue adverse du diff, recette dans l'application lancée.

### Lot 1 : l'alerte du dossier synchronisé (moteur, écran)

Inchangé (V2, lot 1). `diagnostiquer` sert aussi au §4.1.

### Lot 2 : identité, manifeste version 2, révisions connues, refus à l'écran (moteur, Rust, écran)

Tests de la V2 (lot 2), plus :

- **refus en tête** : une base estampillée `revision_du_futur`, en clair puis chiffrée, fait lever `RevisionInconnue` par `init_db` ; son SHA-256 est identique avant et après, et aucune table n'a été créée ;
- **sortie** : le cycle de vie écrit `.demarrage_refuse.json` et sort avec le code 78 (sous-processus de test) ;
- **Rust** : `reaction_a_la_sortie(0)` et `(78)` ne relancent pas, `(1)` relance ;
- **vitest** : `sidecar-refus` avec le motif affiche le texte de la table, ne contient pas « xattr », et un motif inconnu affiche un texte générique sans rien recopier de la charge ;
- **empreinte** : identifiant de machine simulé ; empreinte stable d'un démarrage à l'autre ; nom d'hôte changé sans effet ; empreinte étrangère sur dossier non synchronisé : une régénération ; sur dossier synchronisé : aucune écriture, identité figée ;
- **tests existants réécrits** : `_base_legacy` de `tests/test_variables.py:248` pose une révision connue ancienne ; `test_pas_de_restamp_sans_table_variables` (`:293`) et `test_restamp_avec_schema_complet` (`:308-317`) gardent leur intention.

Critère observable : une base d'une version future dans un dossier de test ; l'application packagée affiche le texte de la table, sans relance ni « xattr ».

### Lot 3 : émettre et examiner (moteur)

Prérequis : le défaut du lien dans une sauvegarde est corrigé. Tests de la V2 (lot 3), plus :

- une émission écrit dans `backups/relais/emis/`, et `GET /api/data/backups` ne la liste pas ;
- une archive dont le point de contrôle WAL était incomplet, avec une facture présente seulement dans le WAL : l'examen la voit ;
- **balayage** : chacun des quatre noms du §4.12 fabriqué dans `backups/` ; après le démarrage, les trois doubles ont disparu, le `pre_restore_*.tar.gz` est gardé et l'alerte existe ; une ancienne sauvegarde en clair avec son `.json` est intacte.

### Lot 4 : appliquer, avec la garde (moteur)

Part après le chantier « mise au repos ». Tests de la V2 (lot 4), plus :

- **route locale** : `POST /api/data/restore/relais` rend 400 ; une copie reçue n'est pas listée ; une archive version 2 d'une autre installation posée dans `backups/` rend 409 avant toute destruction (base identique octet pour octet) ; une archive version 1 se restaure, connecteurs désactivés et listés ;
- **signature** : un rafraîchissement de jeton Gmail, une synchronisation d'agenda Google et une synchronisation du CRM ne déclenchent pas la garde ; un événement ajouté à un agenda local la déclenche ; sentinelle vue rouge sur une colonne fabriquée `derniere_sync_at` non classée ;
- **factures** : une facture envoyée puis repassée en brouillon reste protégée ; même numéro sous deux identifiants : refus sans mise de côté, refus sans acquittement, succès avec les deux, et le dossier `pieces-ecartees` contient la pièce ; pièce absente sans conflit : refus avec le message « passe d'abord le relais » ;
- **connecteurs** : après application d'une archive étrangère, la liste en mémoire égale celle du fichier extrait et chaque serveur est désactivé ; `MCPService().initialize()` n'en lance aucun ;
- **rétention** : trois applications réussies, puis une en échec dont le retour arrière réussit : trois archives, celle de l'échec supprimée ; retour arrière simulé en échec : l'archive de l'échec est gardée en plus ; après succès, la copie reçue a disparu et les copies émises sont intactes.

### Lot 5 : l'écran (écran)

Tests de la V2 (lot 5), plus :

- la phrase sur l'état d'avant relais est présente avant « Appliquer » ;
- conflit de numéros : « Mettre de côté ces pièces », puis un champ par numéro ; « Appliquer » reste désactivé tant qu'un numéro n'est pas retapé à l'identique ;
- l'avertissement du formulaire de facture après un relais émis, absent après un relais reçu ;
- liste des copies émises avec taille et « Supprimer ».

### Lot 6 : recette réelle sur deux machines

Inchangé (V2, lot 6), avec un conflit de numéros provoqué exprès et sa sortie.

## 6. Données et migrations

- **Aucune révision Alembic.** La tête reste `b8c9d0e1f2a3` (`models/database.py:619`).
- **Fichiers nouveaux** : `.installation.json`, `.demarrage_refuse.json` (effacé au démarrage réussi suivant), `backups/relais/` et ses sous-dossiers.
- **Métadonnées d'archive de sécurité** : `kind` gagne `pre_relais`, et `issue` apparaît.
- **Purge totale** : inchangée (V2, §6). `backups/relais/pieces-ecartees/` n'est pas touché par la purge, comme les sauvegardes, et la note de la purge le compte avec elles.

## 7. Risques restants

- **Perte de données** : le relais remplace tout. La garde, les trois archives de sécurité, la mise de côté des pièces et le refus sur les factures sont les protections ; aucune ne suffit seule.
- **Numérotation rompue en usage simultané** : le relais ne la répare pas ; il la montre, garde les pièces et oriente vers l'avoir. La prévention du §4.6 réduit le risque sans l'annuler.
- **Brouillon dont le PDF a circulé** : un brouillon n'est pas protégé par le contrôle 3, même si son PDF a été produit et envoyé hors de THÉRÈSE.
- **Signature** : une colonne volatile mal classée ferait parler la garde à tort ; la sentinelle par nom le rend visible, sans garantir un nom trompeur.
- **Empreinte faible** : sans identifiant de machine lisible, le nom d'hôte revient, avec ses changements.
- **Sécurité, archive fabriquée, mémoire, usage simultané** : inchangés (V2, §7).
- **Clair transitoire** : réduit par le balayage, jamais nul entre l'écriture et le chiffrement.

## 8. Ce que la V3 retire ou reporte, et pourquoi

| Élément de la V2 | Sort | Motif |
|---|---|---|
| Liste blanche propre au relais (« cibles plus WAL plus manifeste ») | remplacée par `NOMS_D_ARCHIVE` | B-1497 l'a posée pour toutes les restaurations ; deux listes divergeraient |
| Copie d'arrivée dans `backups/` avec un `.json` | déplacée dans `backups/relais/recus/` | elle devenait restaurable sans garde |
| Refus « sans appel » dans les deux sens | remplacé par mise de côté et acquittement | il interdisait tout relais ultérieur |
| Critère `status` seul | remplacé | `sent_at` survit à un retour au brouillon |
| Empreinte par nom d'hôte | remplacée | instable, et réécriture sans fin sur dossier synchronisé |
| Refus de révision dans `ensure_alembic_stamp` seulement | gardé comme second filet | trop tard pour être le premier |
| Message par l'écran d'erreur fatale existant | remplacé par un événement dédié | `sidecar-error` n'est pas émis dans ce cas |
| Recharger le service MCP dans le lot 4 | retiré | fait par B-1498 |

Ce que la V2 faisait bien est gardé : l'identité hors base et hors archive, le manifeste interne version 2, la signature par table plutôt qu'un compteur, l'archive de sécurité chiffrée avant toute destruction, l'arrivée par un chemin local validé, « ce qui ne voyage pas » dérivé et tenu par sentinelle, l'alerte du dossier synchronisé en premier.

## 9. Livraison

Ordre : lot 1, lot 2, lot 3 (après la correction du lien dans une sauvegarde), lot 4 (après la « mise au repos »), lot 5, lot 6. Le lot 1 peut partir seul. Revue adverse du design de ce document avant le lot 1, sécurité d'abord ; revue du diff à chaque lot. Aucune release sans le GO de Ludo.

## 10. Questions réservées à Ludo

1. **Le lot B et la promesse publique** : inchangée (V2, §10, question 1). **Recommandation** : ne lancer le lot B que sur une demande exprimée.
2. **Les mots publics** : inchangée (V2, §10, question 2). **Recommandation** : « relais », « une machine à la fois », et répondre à Dr_logic dès le lot 1.
3. **Élaguer d'office les relais émis.** Chaque relais émis est une archive complète gardée dans `backups/relais/emis/`. La V3 ne les supprime jamais sans ton geste, puisque ce serait effacer d'office des états passés de tes données. **Recommandation** : garder les deux plus récents et supprimer les plus anciens, en le disant à l'émission (« le relais du 12/09 a été supprimé ; il en reste deux ») ; ce sont des copies de passage, dont tu as emporté la tienne.

## Annexe : appuis dans le code

- Sauvegarde : `routers/data.py:1032-1043` (manifeste, liste blanche), `:1068-1137` (archive), `:1250-1330` (création), `:1349-1380` (liste).
- Extraction : `routers/data.py:1193-1248`.
- Restauration : `routers/data.py:1482-1735` ; archive de sécurité `:1383-1465`.
- Estampille et démarrage : `models/database.py:613-785`, `:975-1175` ; `main.py:182-194`.
- Moteur et écran de démarrage : `lib.rs:351-365`, `:372-395`, `:399-459` ; `components/SplashScreen.tsx:107-125`.
- Connecteurs : `services/mcp_service.py:288-330`.
- Factures : `routers/invoices.py:82-125`, `:424-435`, `:586-588`, `:655-688` ; `models/entities.py:798`, `:812`, `:825`.
- Écritures de fond : `routers/email.py:304-311` ; `routers/calendar.py:399`, `:705`, `:982` ; `services/crm_utils.py:753` ; `routers/crm.py:1036`.
- Écran des sauvegardes : `components/settings/PrivacyTab.tsx:306-406`.
