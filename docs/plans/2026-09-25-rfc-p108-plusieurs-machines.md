# RFC P-108 : reprendre son travail sur une autre machine

Rédigé le 25/09/2026. Proposition S8 de Dr_logic-3D, acceptée par Ludo le 25/09 avec la recommandation du triage : « à cadrer : synchronisation chiffrée de bout en bout, sujet de sécurité avant tout ». Aucun code avant la validation de ce document.

Chemins relatifs à `src/backend/app/` et à `src/frontend/src/`, sauf mention contraire.

## 1. Le besoin

Dr_logic-3D, sur Discord (fil du 25/09, 03:35 à 04:29) :

- Il travaille sur plusieurs machines, duplique THÉRÈSE sur chacune et bute sur la synchronisation des données.
- Il veut reprendre le même travail d'une instance à l'autre : conversations, contacts, projets, documents.
- Ce qui n'est pas dit et change tout : usage **alterné** (bureau le jour, portable le soir) ou **simultané** (deux machines ouvertes qui écrivent en même temps) ?

## 2. Ce qui existe déjà

**Points d'appui :**

- **Une sauvegarde chiffrée autosuffisante.** Elle contient la base SQLCipher, Qdrant, les images, les fichiers produits, les projets, les factures, les commandes, `mcp_servers.json` et la clé maîtresse (`routers/data.py:1063-1080`). Le tout est chiffré par une passphrase d'au moins 12 caractères : PBKDF2 à 480 000 itérations, sel frais (`services/encryption.py:512-568`, `routers/data.py:74`).
- **Une restauration déjà prévue d'une machine à l'autre** :
  - la base restaurée est ouverte avec la clé de l'archive avant que le succès soit déclaré (`routers/data.py:1117-1167`) ;
  - au démarrage suivant, le fichier de clé l'emporte sur le trousseau (`services/encryption.py:138-190`, BUG-050) ;
  - l'état précédent est gardé en archive de sécurité chiffrée.
- **Des identifiants UUID** sur les tables métier (`models/entities.py`) : pas de collision d'identifiants entre deux machines.
- **Un export RGPD en JSON**, tables de planning comprises (`routers/data.py:172-428`). Il n'est pas restaurable : seuls les conversations et les contacts se réimportent (`:1723`, `:1893`).

**Manques :**

- **Pas d'import d'une archive venue d'ailleurs.** La restauration ne cherche que dans `~/.therese/backups/`, par nom (`routers/data.py:1462-1475`). Il faut y copier à la main le `.tar.gz.enc` et son `.json`. Or ce `.json` porte en `archive_path` un chemin absolu de l'autre machine (`:1279-1286`) : la liste déclare alors l'archive absente (`:1325-1330`).
- **Un redémarrage est exigé** après restauration (`routers/data.py:1659`).
- **L'archive est chiffrée entière en mémoire** (`services/encryption.py:537-568`) : une grosse base d'images et de vecteurs peut ne pas tenir.
- **Les chemins sont absolus** : `FileMetadata.path` (unique, `models/entities.py:225`), les racines de synchronisation avec leur identité de volume (`models/entities_sync.py:71-75`), le dossier de travail, et `{WORKING_DIRECTORY}` figé à l'installation d'un préréglage MCP (`routers/mcp.py:630-661`). Sur l'autre machine, les documents indexés pointent dans le vide, et project.sync refuse, à raison, de scanner un autre volume.
- **L'état de l'interface ne voyage pas** : les consentements (`lib/consent.ts`) et neuf magasins Zustand restent dans le stockage de la webview (`stores/chatStore.ts:451` et suivants).
- **Rien pour fusionner** :
  - aucune suppression logique sur la quarantaine de tables (seules les racines de synchronisation ont un tombeau, `models/entities_sync.py:59-78`) ;
  - `updated_at` absent de nombreuses tables ;
  - un journal d'activité à identifiant entier.
- **Le numéro de facture est séquentiel et unique** (`routers/invoices.py:81-160`, `models/entities.py:798`) : deux machines hors ligne émettraient le même numéro, ce que la numérotation continue interdit.
- **Aucun identifiant d'installation** : `run_instance_id` ne vit que le temps d'un lancement (`models/processing.py:73`).
- **La pratique probable aujourd'hui est le pire cas** : synchroniser `~/.therese` par un service de fichiers. La clé maîtresse est un fichier voisin de la base (`services/encryption.py:40`, `SECURITY.md:31-36`) : elle part en clair chez l'hébergeur avec elle. Et SQLite en WAL comme Qdrant local se corrompent sous une copie concurrente.

## 3. Quatre options

| | A. Passage de relais | B. Relais par un dossier synchronisé | C. Journal chiffré et fusion | D. Instance unique jointe à distance |
|---|---|---|---|---|
| Idée | Exporter une archive « relais » sur A, l'importer sur B ; une seule machine active à la fois | A, mais l'archive est déposée et relevée dans un dossier que l'utilisateur synchronise déjà (Nextcloud, iCloud, clé USB) | Chaque instance écrit un journal d'opérations chiffré de bout en bout ; les instances fusionnent | Une machine sert, les autres s'y connectent par le réseau |
| Pour | Réutilise la sauvegarde éprouvée ; aucun serveur ; chiffré | Moins de gestes ; aucun serveur Synoptïa | Usage simultané possible | Une seule base, rien à fusionner |
| Contre | Remplacement complet, pas de fusion ; gestes manuels | Détection de conflit indispensable ; un fichier chiffré chez un tiers | Tombeaux, `updated_at` partout, règles de fusion par table, numérotation des factures, appairage des clés : un chantier de sécurité et de perte de données | Le moteur n'écoute que 127.0.0.1 et rend son jeton à tout appel sans `Origin` (`main.py:686-701`, relevé par B-1153). Thérèse Server est arrêté depuis le 24/08 (`../Synoptia-THERESE-Server/README.md`) |
| Effort | Petit à moyen | Moyen | Large | Large |

## 4. Recommandation : A d'abord, B si l'usage le demande, C seulement sur preuve

### Premier lot : le relais explicite

- **Import d'une archive venue d'ailleurs** : `POST /api/data/backups/import`, sur un fichier choisi par l'utilisateur.
  - Contrôle de l'en-tête `THBK1` et plafond de taille.
  - Écriture sous `backups/` avec un `.json` régénéré.
  - `list_backups` résout l'archive par son nom, et non plus par un chemin absolu.
- **Identité et génération** : un `installation_id` créé au premier lancement. Le manifeste de l'archive (`routers/data.py:1012-1015`) porte l'installation émettrice, la date et un compteur de génération.
- **Garde contre l'écrasement** : si la machine qui importe a été modifiée après le dernier relais émis ou reçu, l'écran le dit en clair avant toute étape destructive. L'archive de sécurité existante reste le filet.
- **Ce qui ne voyage pas est dit à l'écran** :
  - les consentements, redemandés (c'est le sens prudent) ;
  - les réglages d'affichage et les modèles Ollama ;
  - les fichiers indexés hors de `~/.therese` et les racines de synchronisation, listés « à rebrancher », jamais réécrits en silence.
- **Alerte** si le dossier de données est sous un dossier synchronisé connu (iCloud Drive, Dropbox, OneDrive, Nextcloud) : le risque est expliqué, et l'écran renvoie vers le relais.
- **Factures** : la règle « une seule machine émet » est documentée ; le relais transporte la séquence.

### Deuxième lot (B), si le relais manuel lasse

- Dossier de relais choisi par l'utilisateur : l'archive y est déposée à la fermeture et proposée à l'ouverture sur l'autre machine, jamais appliquée sans un geste.
- Chiffrement par morceaux (format `THBK2`), pour ne plus charger l'archive en mémoire.
- Remappage des préfixes de chemins (de `/Users/a/Documents` vers `C:\Users\a\Documents`), avec aperçu.

### Hors périmètre

- C, tant que l'usage simultané n'est pas avéré.
- D, qui relève de Thérèse Console, en conception.

## 5. Décisions attendues de Ludo

1. **L'usage** : alterné ou simultané chez Dr_logic ? Toute la suite en dépend.
2. **La passphrase du relais** : garder 12 caractères minimum, ou exiger plus pour un fichier qui vivra chez un tiers ? Recommandation : 16, avec une phrase de passe générée proposée.
3. **Les consentements** voyagent-ils ? Recommandation : non, ils sont redemandés.
4. **Le lot 2** est-il compatible avec la promesse « données locales » ? Le fichier est chiffré, mais il quitte la machine.
5. **Qdrant** : il voyage (plus lourd) ou se reconstruit à l'arrivée (plus long) ?

## 6. Livraison proposée

1. Design court et revue adverse, sécurité d'abord, selon le triage.
2. Identifiant d'installation et manifeste enrichi (TDD).
3. Route d'import et garde contre l'écrasement.
4. Écran « Passer le relais » dans Confidentialité (`components/settings/PrivacyTab.tsx`), avec la liste de ce qui ne voyage pas.
5. Alerte de dossier synchronisé.
6. Recette réelle sur deux machines, macOS et Windows.

## 7. Plan de tests

- **Aller-retour** sur deux `THERESE_DATA_DIR` distincts, avec des clés différentes. A exporte, B importe. B relit une conversation, un contact chiffré et une clé d'API. Puis B exporte et A réimporte.
- **Archives défectueuses** : archive tronquée, mauvaise passphrase, mauvais en-tête, taille au-delà du plafond. Chaque cas est refusé avant toute étape destructive ; les données de B restent intactes (empreinte de la base avant et après).
- **Garde** : si B a été modifié après le dernier relais, un import sans confirmation explicite est refusé.
- **Noms forgés** : un nom d'archive en `../` ou un `.json` qui pointe hors de `backups/` est refusé.
- **Aucun clair sur disque**, y compris après interruption (même exigence que B-1290).
- **Recette Windows réelle** : Dr_logic travaille sous Windows 10, et le sel binaire comme `O_BINARY` ont déjà piégé les tests (`services/encryption.py:29-37`).
- **Sabotage** ciblé par fonction (contrôle d'en-tête, garde), puis revue adverse du diff.

## 8. Risques

- **Perte de données** : le relais remplace tout, et importer une archive plus ancienne efface le travail récent. La garde de génération et l'archive de sécurité sont les deux protections ; aucune ne suffit seule. L'état écrasé est gardé, chiffré avec la passphrase du relais (dette connue depuis la 0.40.1).
- **Sécurité** : l'archive contient la clé maîtresse. Qui a le fichier et la passphrase a tout. Une passphrase faible sur un fichier déposé chez un tiers ouvre la voie à une attaque hors ligne, sans limite d'essais.
- **Souveraineté** : aucun serveur Synoptïa ; le transport reste le choix de l'utilisateur. Le lot 2 fait sortir un fichier chiffré de la machine : à dire dans le Centre de confiance.
- **Faux sentiment de synchronisation** : parler de « relais », jamais de « synchronisation », tant que la fusion n'existe pas.
- **Facturation** : deux machines qui émettraient chacune casseraient la numérotation continue ; le relais doit rester exclusif.

## Annexe : appuis dans le code

- Origine : `.app-loop/proposals.json`, P-108.
- Sauvegarde : `routers/data.py:1210-1307` (création, passphrase exigée `:1233-1255`), `:1428-1665` (restauration), `:1971` (état).
- Clé : `services/encryption.py:47-61` (un compte de trousseau par dossier de données), `:446-485` (clé SQLCipher dérivée par HKDF).
- Tests existants : `tests/test_backup_complete.py` (aller-retour, archive de sécurité, absence de clair).
