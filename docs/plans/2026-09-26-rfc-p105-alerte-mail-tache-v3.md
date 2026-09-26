# RFC P-105 (V3) : alerte quand un mail touche une tâche ou un livrable, et un créneau pour le traiter

Rédigé le 26/09/2026. Remplace la V2 (`docs/plans/2026-09-26-rfc-p105-alerte-mail-tache-v2.md`), refusée (NO-GO) par la revue adverse du 26/09 (constats 1 à 17, rapport de travail `revue-v2-p105-p106.md` de l'orchestrateur). Les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 1 à 6 de P-105) restent des faits. La réponse à la revue de la V1 (V2, section 7) reste valable et n'est pas recopiée ici.

**Base de vérification.** Toutes les lignes citées ont été relues à `6f927313` (HEAD du 26/09/2026), avec `git show HEAD:<fichier>` et non l'arbre de travail, où l'orchestrateur corrige des défauts en parallèle. B-1486 (`66b78788`), B-1487 (`30aa8b33`) et B-1488 (`2c8a4489`) ont été livrés pendant la rédaction : les constats qui les concernent décrivent le code d'avant, et les lignes citées sont celles d'après. Chemins relatifs à `src/backend/app/` (fichiers `.py`) et à `src/frontend/src/` (fichiers `.ts` et `.tsx`) ; les tests, `docs/`, `uv.lock` et `pyproject.toml` partent de la racine du dépôt. Les lignes de `imap_tools` et `dateutil` ont été relues dans l'environnement installé (`.venv`, imap_tools 1.11.1, python-dateutil 2.9.0.post0), qui n'est pas versionné.

Aucun code avant la validation de ce document.

## 0. Constats de la revue V2 et leur traitement

| # | Constat de la revue V2 | Traitement | Où |
|---|---|---|---|
| 1 | « Heure murale de Paris » est une convention déclarée, pas tenue par les écritures | **Accepté.** Relu avant correctifs : la création et la modification d'un événement local jetaient `request.timezone`, l'import ICS jetait le décalage. Les deux sont corrigés depuis (B-1487, `routers/calendar.py:100-110` et `:1194-1195`, `:1366`, `:1372` ; B-1486, `services/import_service.py:56-63`). Reste l'outil du chat, qui range l'heure du modèle sans conversion (`services/workspace_tools.py:1672-1673`). Traité par trois prérequis (B-1486, B-1487, A-1) et un candidat (C-1) pour les lignes déjà en base. Le test de la V2 (« bloque 5 h en Martinique ») est remplacé par des tests qui passent par les vraies écritures. La migration demandée par la revue est **réfutée** sous sa forme simple : le décalage a été jeté à l'écriture et aucune colonne ne dit d'où vient une ligne (`models/entities.py:508-545`) ; c'est l'objet de C-1, que P-105 ne tranche pas | 2 ; 6.7 ; lot 4 |
| 2 | Le dépliage des récurrences ne tient pas sur les données réelles | **Accepté, et le remède de la revue est insuffisant.** Mesuré dans l'environnement : `rrulestr` lève `ValueError` dès que DTSTART et UNTIL n'ont pas la même conscience du fuseau, **dans les deux sens** (UNTIL en Z avec un début naïf, UNTIL naïf ou en date seule avec un début conscient). Rendre le début conscient ne suffit donc pas : UNTIL est normalisé aussi. Requête dédiée sans borne basse pour les séries, chevauchement pour le reste ; toute erreur de dépliage rend l'agenda illisible. Le test EXDATE est retiré (donnée impossible : `services/import_service.py:79-82` ne garde que la RRULE) | 6.7 ; lot 4 |
| 3 | Lecture CalDAV partielle invisible ; STATUS et TRANSP jamais lus | **Accepté.** `services/calendar/caldav_provider.py:235-242` tronque et saute en silence, `services/calendar/caldav_provider.py:664` écrit `status="confirmed"` en dur. Lecture stricte dédiée au créneau (plafond atteint ou événement illisible : agenda illisible), STATUS et TRANSP lus, heure flottante tranchée (heure de Paris) | 6.7 ; lot 4 |
| 4 | Une coupure réseau au rafraîchissement du jeton pose `a_reconnecter` pour de bon | **Accepté, avec une précision.** Avant B-1488, une erreur de transport sortait du client OAuth en 500 « Token refresh failed » et un 5xx de Google en 400, comme un refus explicite : le code ne permettait pas de distinguer une panne d'un refus. B-1488 (livré, `2c8a4489`) sort le transport et les 5xx en 503 (`services/oauth.py:331-335`, `:354-357`) et garde le 400 pour un refus (`services/oauth.py:337-341`) ; `ensure_valid_access_token` les relance tels quels (`routers/email.py:317-318`). La relève classe sur ces codes, et ses tests doublent le service OAuth | 2 ; 6.5 ; lot 5 |
| 5 | Un changement d'UIDVALIDITY relit toute la boîte | **Accepté.** Traité comme une première relève (14 jours, 50 messages au plus parmi les plus récents) | 6.5 ; lot 5 |
| 6 | Déduplication et concurrence non décrites | **Accepté.** `INSERT ... ON CONFLICT DO NOTHING`, verrou par compte sur le patron existant (`services/project_sync_service.py:79`), filigrane monotone | 6.5 ; lot 5 |
| 7 | Le lot 4 consomme des routes du lot 3, bloqué par P0 | **Accepté.** Lots réordonnés : ce que l'utilisateur voit (lot 3) ne dépend plus de P0 ; la route de résolution (lecture chez le fournisseur, sans écriture) y passe ; « Relever » et « Relever la suite » arrivent avec la relève (lot 5). Une garde de livraison empêche la source « E-mails » de promettre une relève qui n'existe pas encore | 6.6 ; section 7 |
| 8 | Anonymisation par `contact_id` seulement ; export de la fiche oublié | **Accepté.** Effacement aussi par adresse d'expéditeur (lue avant `effacer_l_identite`), et export de portabilité de la fiche étendu (`routers/rgpd.py:47`, `models/schemas.py:457-467`) | 6.11 ; lot 2 |
| 9 | `routers/actions.py:164` ne supprime aucune tâche | **Accepté** (`routers/actions.py:164-166` annule un traitement long). Chemins réels relevés : `routers/tasks.py:293`, `routers/rgpd.py:273`, `routers/crm.py:378`, purge `routers/data.py:671` et `:675`, cascade du projet par `routers/memory.py:361` | 6.11 ; lot 2 |
| 10 | Base témoin de l'estampillage non mise à jour | **Accepté.** `_creer_tables_veille_reelles` appelée par `_make_patched_tracked_db` (`tests/test_alembic_stamp.py:98`, `:135-136`) | lot 2 |
| 11 | La date de réception IMAP vient de l'en-tête `Date:` de l'expéditeur | **Accepté.** Rétention comptée depuis `cree_le` ; fenêtre de 14 jours par le critère IMAP `SINCE` (date interne du serveur) | 6.4 ; 6.5 ; 6.11 |
| 12 | Test de garde en liste noire incomplète | **Accepté, et renforcé.** Doublures en liste blanche, plus sélection de la boîte en lecture seule (`folder.set(..., readonly=True)`, soit `EXAMINE`), que le serveur IMAP fait respecter | 6.9 ; lot 5 |
| 13 | L'horizon « échéance » n'a pas de règle de conversion | **Accepté.** Deux écritures différentes relevées (tâche `components/tasks/TaskForm.tsx:172` et `:188`, livrable `components/prototype/DeliverablesWorkspaceCanvas.tsx:82`) ; règle du jour civil, fin des heures ouvrées dans le fuseau du poste | 6.7 ; lot 4 |
| 14 | La remise à `jamais` à la reconnexion n'a pas de point d'appel | **Accepté et élargi** : quatre points, pas trois. Les trois branches « compte existant » (`routers/email.py:423`, `:542`, `:815`), plus `update-credentials` (`routers/email.py:681-707`), qui enregistre des identifiants OAuth et retente le rafraîchissement. `reauthorize` (`:594`) ne fait qu'ouvrir le flux ; les jetons arrivent par les deux rappels | 6.5 ; lot 5 |
| 15 | `Message-ID` dupliqué ou absent : cas non tranchés | **Accepté.** Clé de repli indépendante de l'UID, empreinte stockée pour distinguer deux messages au même `Message-ID`, clé de fil d'un message sans identifiant | 6.3 ; 6.4 ; lot 1 |
| 16 | « Cette semaine » lue une seule fois, clic sans cible | **Accepté.** Relecture au focus et au retour de visibilité ; ancre nouvelle `brief-source-email`, défilement et focus | 6.6 ; lot 3 |
| 17 | Contradiction sur le cache Google | **Accepté.** Lecture par le fournisseur, sans écriture du cache ; la phrase de la V2 est retirée | 6.7 ; lot 4 |

## 1. Ce que la V3 change

- Le créneau libre ne suppose plus que chaque ligne de l'agenda est en heure de Paris : trois prérequis rendent la convention vraie pour les nouvelles écritures, et un candidat à trancher traite les lignes déjà en base (section 2).
- Le dépliage des récurrences est défini jusqu'à la normalisation de UNTIL, mesurée sur la bibliothèque installée.
- La relève est sérialisée par compte, absorbe les doublons en base, n'efface jamais son filigrane, et sélectionne la boîte en lecture seule.
- Les états de compte ne confondent plus une coupure réseau avec un refus.
- Les lots sont réordonnés : l'écran et le créneau avancent sans la pièce « mise au repos » ; seule la relève l'attend.
- Les effacements suivent l'adresse de l'expéditeur, et la portabilité d'une fiche rend ses rapprochements.

## 2. Prérequis

| Nom | Nature | État à la base relue | Bloque |
|---|---|---|---|
| **P0** | Pièce « mise au repos » du chantier du 25/09 (`docs/plans/2026-09-25-chantier-mise-au-repos-ecritures-de-fond.md`), validée par la décision 1 | Non livrée : aucun symbole `mise_au_repos` dans `src/backend/app/` | lots 5 et 6 |
| **B-1486** | L'import ICS rangeait l'heure Z comme heure de Paris | **Livré** (`66b78788`) : un instant daté est ramené à Paris avant stockage (`services/import_service.py:56-63`). Les lignes déjà importées gardent leur décalage (message du commit) | lot 4 (garantie de la convention) |
| **B-1487** | La création et la modification d'un événement local ignoraient le fuseau de l'écran | **Livré** (`30aa8b33`) : l'heure saisie et le fuseau du poste (`components/calendar/EventForm.tsx:276-280`, `components/prototype/MeetingConversationCard.tsx:267-270`) sont ramenés en heure de Paris (`routers/calendar.py:100-110`), à la création (`:1194-1195`) comme à la modification (`:1366`, `:1372`) ; une heure de Paris rendue à l'écran porte son fuseau (`routers/calendar.py:113-121`). Les lignes déjà écrites ne sont pas converties | lot 4 |
| **B-1488** | Une coupure réseau au renouvellement du jeton demandait de reconnecter le compte | **Livré** (`2c8a4489`) : transport et 5xx en 503, refus explicite en 400 (`services/oauth.py:331-341`, `:354-357`). La section 6.5 s'appuie sur ces codes | lot 5 ; lecture Google du lot 4 |
| **A-1** (à reproduire) | L'outil agenda du chat range l'heure donnée par le modèle sans la ramener à Paris | Preuves ci-dessous ; reste à reproduire le parcours complet dans le chat | lot 4 |
| **C-1** (candidat, à trancher) | Conversion unique des anciennes lignes hors Paris | Aucune migration posée ; décision à écrire dans son propre ticket | livraison du lot 4 |

**A-1, preuves.** `services/workspace_tools.py:1672-1673` lit `datetime.fromisoformat(start_str)` sans conversion ; le schéma de l'outil n'offre aucun champ de fuseau (`services/workspace_tools.py:190-226`, exemple naïf « 2026-03-26T14:00:00 »), si bien que `timezone=args.get("timezone") or "Europe/Paris"` (`:1694`) vaut toujours Paris ; le fournisseur local range `request.start` tel quel (`services/calendar/local_provider.py:285`) et ne lit jamais `request.timezone`. Deux cas :

- le modèle écrit un décalage ou un « Z » : SQLite garde la valeur faciale et jette le décalage (mesuré avec une colonne `DateTime` SQLAlchemy : `2026-10-05T12:00:00Z` relu `12:00`, soit 12 h de Paris au lieu de 14 h). Le modèle y est poussé : l'heure qu'on lui donne est en UTC (`services/llm.py:526-529`, « … UTC ») ;
- le modèle écrit une heure naïve : elle est prise pour l'heure de Paris, fausse sur un poste hors de Paris (même défaut que B-1487, sans le fuseau de l'écran pour le corriger).

Le défaut de stockage est prouvé ; ce qui reste à reproduire, c'est la fréquence réelle du premier cas dans une conversation.

**C-1, ce que P-105 en attend.** Les lignes écrites avant B-1486 (import ICS en Z ou avec TZID, rangées à l'heure UTC ou du TZID) et avant B-1487 (créées ou modifiées sur un poste hors de Paris, rangées à l'heure du poste) ne sont pas converties. Sur un poste à Paris, seuls les imports ICS antérieurs sont décalés ; sur un poste hors de Paris (un testeur est à Toronto), les deux familles le sont. P-105 ne tranche pas C-1. Il s'engage seulement à ceci : **le créneau ne suppose pas que chaque ligne est en heure de Paris**, et le lot 4 n'est pas livré tant que C-1 n'est pas tranché. Si C-1 conclut à une conversion, rien n'est à ajouter ici. S'il conclut à l'absence de conversion, le lot 4 devra, avant livraison, soit tenir ces lignes pour occupées sur toutes leurs lectures possibles (heure de Paris, heure du poste, UTC), soit dire sur la carte des créneaux que les rendez-vous antérieurs à la mise à jour peuvent être décalés. Aucune de ces deux branches n'efface de donnée.

## 3. Le besoin

Dr_logic-3D, testeur alpha, sur Discord (fil du 25/09, 03:35 à 04:29) :

- Un client écrit au sujet d'un travail en cours. THÉRÈSE doit faire le rapprochement avec la tâche ou le livrable concerné et prévenir.
- Il veut **suivre sans forcément agir** : être prévenu, pas qu'on réponde à sa place.
- Second volet : proposer un **créneau libre** pour traiter ce mail avant l'échéance, ou avant le prochain rendez-vous avec ce client.

Périmètre accepté par Ludo le 25/09 : lecture seule, aucune action automatique, design challengé avant le code.

## 4. Décisions du 25/09/2026 (tranchées)

1. **Mise au repos des écritures de fond : validée.** Le rapprochement au geste est livré d'abord ; la relève de fond vient après.
2. **L'interrupteur « désactivé par défaut » ne gouverne que la relève de fond.** Le rapprochement au geste est local, visible, et toujours actif.
3. **Les fils IMAP sont reconstitués avant la livraison.** « Pas lié » vaut pour tout le fil, sur Gmail comme sur IMAP.
4. **Rétention : 90 jours** pour les rapprochements écartés et les silences, qui sont aussi effacés avec la fiche à l'anonymisation.
5. **Fuseau du système, jours fériés français exclus** pour le calcul des créneaux.
6. **Une ligne dans « Cette semaine »**, sans relève supplémentaire.

## 5. État du code à HEAD

Les points d'appui de la V2 (section 4) restent justes, lignes relues ; seuls ceux qui changent ou s'ajoutent sont repris ici.

- **Agendas, convention.** `CalendarEvent.start_datetime` est une heure murale de Paris, naïve (`services/calendar/local_provider.py:28-41`, B-275). La revue a montré qu'elle n'était pas tenue par toutes les écritures ; B-1486 et B-1487 la rétablissent pour l'import ICS et l'écran, A-1 reste ouvert pour l'outil du chat, et les lignes déjà écrites relèvent de C-1 (section 2). À l'écran, une heure sans fuseau est désormais rendue comme heure de Paris (`routers/calendar.py:113-121`). Le fournisseur local filtre sa fenêtre sur le seul début (`services/calendar/local_provider.py:215-226`), ce qui convient à l'écran de l'agenda mais pas à un calcul d'occupation.
- **Récurrences locales.** Seule la RRULE est gardée à l'import (`services/import_service.py:79-82`) ; l'écran n'en écrit aucune (ni `EventForm` ni `NewEventForm` ne portent de champ de récurrence). EXDATE, RDATE et les occurrences déplacées (RECURRENCE-ID) n'existent donc pas en base.
- **CalDAV.** Lecture dépliée (`services/calendar/caldav_provider.py:227-231`), tronquée à `max_results` et tolérante aux événements illisibles (`services/calendar/caldav_provider.py:235-242`), statut écrit en dur (`services/calendar/caldav_provider.py:664`), heure sans TZID rendue naïve (`services/calendar/caldav_provider.py:620-623`).
- **Google.** `services/calendar/google_provider.py:130-150` convertit sans rien écrire ; seule la route de liste écrit le cache (`routers/calendar.py:913-1019`). Le statut est lu (`services/calendar/google_provider.py:306`), la transparence ne l'est pas.
- **Jeton OAuth, depuis B-1488.** Transport coupé, délai dépassé ou 5xx de Google : 503 (`services/oauth.py:331-335`, `:354-357`) ; refus explicite (`invalid_grant`) : 400 (`services/oauth.py:337-341`) ; tous deux relancés tels quels par `ensure_valid_access_token` (`routers/email.py:317-318`). Des identifiants OAuth absents donnent 401 (`routers/email.py:289-292`), et une erreur inattendue hors HTTP (déchiffrement, réponse mal formée) aussi (`routers/email.py:319-324`).
- **Lecture IMAP.** `imap_tools` sélectionne un dossier en lecture seule (`folder.set(folder, readonly=True)`, `.venv/.../imap_tools/folder.py:40-42`) ; la connexion du fournisseur, elle, sélectionne en écriture (`services/email/imap_smtp_provider.py:249-264`, `initial_folder="INBOX"`). En en-têtes seuls, `imap_tools` ne lit ni `INTERNALDATE` ni le corps (`.venv/.../imap_tools/mailbox.py:190-191`).
- **Verrous par clé.** Patron existant : `_verrous_projet.setdefault(project_id, asyncio.Lock())` (`services/project_sync_service.py:79`). Aucun `on_conflict_do_nothing` dans le code à ce jour.
- **Échéances.** Une tâche porte `due_date` à minuit Z (`components/tasks/TaskForm.tsx:172`, `:188`), relu naïf après SQLite ; un livrable reçoit la date saisie telle quelle (`components/prototype/DeliverablesWorkspaceCanvas.tsx:82`). Dans les deux cas, l'information utile est un jour civil.
- **Brief et « Cette semaine ».** Le brief se relit toutes les 5 minutes, au focus et au retour de visibilité (`components/prototype/usePrototypeReadData.ts:5`, `:48-50`) ; « Cette semaine » ne lit qu'au montage (`components/prototype/CetteSemaine.tsx:56-62`). Aucune ancre de source n'existe dans le brief (`components/prototype/TodayDashboardCard.tsx` ne pose que des `data-testid`).
- **Portabilité d'une fiche.** `GET /api/rgpd/export/{contact_id}` (`routers/rgpd.py:47`) rend ce que l'anonymisation efface (B-590, `routers/rgpd.py:135-136`) ; son schéma a des listes par défaut vides (`models/schemas.py:457-467`).

## 6. Conception V3

La conception de la V2 (section 5) est gardée ; chaque sous-section ci-dessous la reprend en entier, avec les changements de la V3 intégrés.

### 6.1 Vocabulaire

Inchangé. À l'écran, « travaux » désigne les traitements longs (`docs/rules/RULES-DESIGN.md`, section 13) : le mot « travail en cours » ne paraît jamais. On dit **la tâche** ou **le livrable**, et **la cible** dans ce document. La source du brief s'appelle **« E-mails »** (`lib/etabli.ts:27`), la marque sur une cible **« Mail récent »**. Les deux libellés entrent au lexique au lot 3.

### 6.2 Le rapprochement, un moteur pur

Inchangé par rapport à la V2 : module de fonctions pures `rapprocher(entete, index, reglages) -> list[Proposition]`, index construit une fois par relève (adresses des fiches non archivées, projets `active`, cibles ouvertes, rapprochements retenus par fil), règles 1 à 6 dans l'ordre de la V2 (fil confirmé ; contact d'une tâche ouverte ; contact d'un projet à une seule cible ; contact d'un projet à plusieurs cibles ; objet qui cite un projet ou un livrable ; même domaine hors domaines grand public), mêmes garde-fous (écart retenu 90 jours, silences, mention d'objet avec `_fold` de `services/memory_tools.py:902-908`, frontière de mot, liste de mots courants, liste fermée de domaines grand public), mêmes écartements préalables (adresse du compte, en-têtes de masse `List-Id`, `List-Unsubscribe`, `Precedence`, `Auto-Submitted`, puis le classeur `services/email_classifier_v2.py:194`), mêmes choix tranchés (« ouvert » couvre tout ce qui n'est pas terminé d'un projet actif ; règle du domaine au niveau « à confirmer »). Un rapprochement reste une proposition : il ne modifie ni la fiche, ni la cible, ni le mail.

### 6.3 Identité d'un message et fils

**Identité** (constat 15).

- Clé principale : l'en-tête `Message-ID` normalisé (chevrons et espaces retirés, minuscules).
- **Sans `Message-ID`**, la clé ne dépend jamais de l'UID, qui change avec UIDVALIDITY :
  - Gmail : `gmail:` suivi de l'identifiant Gmail, stable pour la vie du message ;
  - IMAP : `empreinte:` suivi du SHA-256 de (compte, expéditeur normalisé, en-tête `Date` brut, objet, `RFC822.SIZE`). La taille est rendue par la lecture d'en-têtes (`.venv/.../imap_tools/mailbox.py:190-191`) et ne change pas quand le message change de dossier.
- **`Message-ID` partagé par deux messages distincts** (outil d'envoi défectueux) : chaque ligne porte une `empreinte` (SHA-256 de l'expéditeur normalisé, de l'en-tête `Date` brut et de l'objet). Quand un `Message-ID` déjà connu arrive avec une autre empreinte, la clé devient `<Message-ID>#<12 premiers caractères de l'empreinte>` : le second message est traité comme neuf, pas comme un doublon.
- On garde aussi l'identifiant du fournisseur pour ouvrir le mail (identifiant Gmail, ou UIDVALIDITY et UID). « Ouvrir le mail » essaie cet identifiant, puis recherche le `Message-ID` dans la boîte, et à défaut le dit (« ce mail a été déplacé ou supprimé »).

**Pourquoi la relève n'écrit jamais `EmailMessage`.** Inchangé : clé primaire sur l'identifiant seul (`models/entities.py:391`), collisions entre comptes IMAP (`routers/email.py:1233-1243`, `:1276`), clé étrangère `email_follow_ups.email_message_id` (`models/entities.py:938`). La table des rapprochements porte elle-même ce qu'elle affiche.

**Fils.**

- Gmail : `gmail:` suivi du `threadId`.
- IMAP (décision 3), dans cet ordre : l'ancêtre déjà connu (un identifiant de `References` ou `In-Reply-To` présent dans un rapprochement retenu du même compte) ; sinon le premier identifiant de `References` ; sinon `In-Reply-To` ; sinon la clé du message lui-même.
- **Un message sans `Message-ID` ni ancêtre** a pour fil sa propre clé de repli : « Pas lié » ne vaut alors que pour lui. Une réponse qui le cite ne peut pas le citer (il n'a pas d'identifiant) : c'est une limite du courrier, pas du moteur.
- Aucun regroupement par objet.

### 6.4 Données

Trois tables nouvelles, créées par `create_all` au démarrage et par une révision Alembic. Aucune colonne n'est ajoutée à une table existante.

**`rapprochements_courrier`.**

| Champ | Contenu |
|---|---|
| `id` | identifiant |
| `account_id` | compte (clé étrangère `email_accounts.id`, indexée) |
| `message_cle` | clé du message (section 6.3) |
| `empreinte` | SHA-256 de l'expéditeur, de l'en-tête `Date` brut et de l'objet |
| `message_fournisseur_id` | identifiant Gmail, ou UIDVALIDITY et UID IMAP |
| `fil_cle` | clé de fil, indexée |
| `ancetres` | identifiants `References` et `In-Reply-To`, tableau JSON borné à 20 |
| `recu_le` | date de l'en-tête `Date`, **pour l'affichage seulement** (écrite par l'expéditeur, constat 11) |
| `expediteur_adresse`, `expediteur_nom` | normalisée ; nom tel quel ; adresse indexée (effacement par adresse, section 6.11) |
| `objet` | tronqué à 200 caractères |
| `contact_id`, `projet_id` | fiche et projet (nullables, indexés). **Invariant** : `projet_id` est renseigné dès que la cible appartient à un projet |
| `cible_type`, `cible_id` | `tache`, `livrable` ou `projet` |
| `regle`, `niveau` | 1 à 6 ; `sur`, `probable`, `a_confirmer` |
| `statut` | `nouveau`, `vu`, `confirme`, `ecarte` |
| `cree_le`, `maj_le` | horloge locale, UTC naïve comme les autres colonnes |

Unicité sur (`account_id`, `message_cle`, `cible_type`, `cible_id`). Objet, adresse et nom de l'expéditeur sont des données personnelles de la table : export, purge, anonymisation et rétention les couvrent (section 6.11).

**`silences_courrier`.** `id`, `account_id` (nullable), `type` (`projet`, `expediteur`, `fil`), `valeur`, `jusqu_au` (jamais nul, jamais au-delà de 90 jours), `cree_le`.

**`releves_courrier`**, une ligne par compte : `account_id` (clé primaire et étrangère), `uidvalidity` et `dernier_uid` (IMAP), `filigrane_date` (Gmail), `premiere_releve_le`, `derniere_tentative_le`, `derniere_reussite_le`, `etat` (`jamais`, `ok`, `illisible`, `a_reconnecter`), `code_erreur` (un code, jamais le texte d'une exception), `non_examines`.

Motif de la troisième table plutôt qu'une colonne sur `EmailAccount` : inchangé (`models/database.py:320-324`).

**Préférence serveur** `veille_courrier` : inchangée, relève de fond seulement.

### 6.5 La relève au geste

**Un seul chemin** : `POST /api/veille-courrier/relever?account_id=...&forcer=...`. Il lit des en-têtes, applique les règles, écrit des propositions et l'état du compte. Il ne lit jamais un corps et ne modifie rien chez le fournisseur.

**Qui l'appelle.** L'ouverture de l'écran E-mail (vue complète `components/email/EmailList.tsx` et carte `components/prototype/EmailConversationCard.tsx`), une fois par compte et par ouverture, sans attendre la réponse ; le bouton « Relever » de la source E-mails (`forcer=true`). Sans `forcer`, un compte relevé il y a moins de deux minutes n'est pas relu.

**Sérialisation par compte** (constat 6). Un verrou `asyncio.Lock` par compte, sur le patron de `services/project_sync_service.py:79`. Une relève qui trouve le verrou pris attend sa libération, puis rend l'état que la première vient d'écrire, sans relire, même avec `forcer`. Deux déclencheurs à l'ouverture et un clic sur « Relever » ne font donc jamais deux lectures concurrentes. Le serveur tourne en un seul processus : un verrou en mémoire suffit.

**Écriture sans doublon** (constat 6). Les propositions sont écrites par `sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_nothing(index_elements=[account_id, message_cle, cible_type, cible_id])` : un message déjà traité, relu après une remise à zéro du filigrane, ne lève aucune erreur et ne bloque rien.

**Filigrane monotone** (constat 6). Le filigrane n'avance que par une mise à jour conditionnelle (`dernier_uid` n'est remplacé que par une valeur plus grande, dans la même UIDVALIDITY ; `filigrane_date` que par une date plus tardive), et seulement après l'écriture réussie des propositions du message.

**Lecture IMAP.** Une méthode nouvelle du fournisseur, distincte de `list_messages` :

- connexion sans dossier initial, puis `folder.set("INBOX", readonly=True)`, soit un `EXAMINE` : le serveur lui-même refuse tout changement d'indicateur pendant la session (constat 12) ;
- `headers_only=True`, `mark_seen=False` en plus, sous `_run_imap_operation` et ses délais (`services/email/imap_smtp_provider.py:282`) ;
- statut du dossier lu d'abord (UIDVALIDITY) ;
- **première relève, ou UIDVALIDITY changée** (constat 5) : critère `SINCE` à J-14, qui porte sur la date interne du serveur et non sur l'en-tête `Date:` (constat 11) ; les 50 UID les plus élevés sont examinés, le filigrane est posé sur le plus élevé, et le brief dit « rapprochement commencé le 26/09 ». Les rapprochements existants restent, puisqu'ils sont identifiés par `Message-ID` et que l'insertion absorbe les doublons ;
- relèves suivantes : critère UID « dernier + 1 à la fin », ordre croissant, UID inférieurs ou égaux au filigrane filtrés (le serveur rend toujours le dernier message pour une plage ouverte).

**Lecture Gmail.** Première relève : `in:inbox newer_than:14d`, les 50 plus récents. Ensuite : `after:` suivi du filigrane en secondes, qui porte sur la date interne de Gmail. Identifiants listés, puis `format='metadata'` des plus anciens aux plus récents, comme la liste existante (`routers/email.py:958-963`).

**Plafond.** Au plus 50 messages examinés par relève, du plus ancien au plus récent après le filigrane (hors première relève). Le reste est compté dans `non_examines` ; le brief le dit (« 34 mails pas encore examinés ») avec « Relever la suite » (doctrine B-425).

**États de compte** (constats 4 et 14).

- `a_reconnecter` **seulement sur un refus** : le 400 d'un rafraîchissement refusé (`invalid_grant`, `services/oauth.py:337-341`) et le 401 de `ensure_valid_access_token` (identifiants OAuth absents, `routers/email.py:289-292`, ou erreur inattendue hors HTTP, `:319-324`). Motif du 401 inattendu : le reste de l'application le présente déjà comme « reconnecte ton compte », et le brief ne doit pas contredire l'écran E-mail. Ce classement par code n'est possible que depuis B-1488 : avant, un refus et une panne sortaient tous deux en 400 ou 500.
- `illisible` pour tout le reste : le 503 de B-1488 (transport, délai, 5xx), serveur IMAP injoignable, identifiants IMAP refusés (code `identifiants_refuses`), toute autre exception. Retenté au geste suivant.
- Un compte `a_reconnecter` n'est plus tenté jusqu'à sa remise à `jamais`, faite en quatre points, chacun testé :
  1. rappel OAuth `POST /auth/callback`, branche « compte existant » (après `routers/email.py:423`) ;
  2. rappel `GET /auth/callback-redirect`, même branche (après `routers/email.py:542`) ;
  3. `POST /auth/imap-setup`, même branche (après `routers/email.py:815`) ;
  4. `POST /auth/update-credentials/{account_id}` (`routers/email.py:681-707`), après l'enregistrement des identifiants, quel que soit le résultat du rafraîchissement : la relève suivante reclasse le compte.
- Dans tous les cas, aucune exception ne remonte à l'écran : la réponse porte l'état, et le brief le nomme.

**Mise au repos** (décision 1). La relève écrit en base : elle est cliente de P0. Pendant une purge ou une restauration, elle refuse d'entrer (503 « relève suspendue ») et celle en vol est attendue. P0 est livrée avant le lot 5.

### 6.6 Ce que l'utilisateur voit

**La source « E-mails » du brief.**

- Elle lit seulement `rapprochements_courrier` et `releves_courrier`, jamais le fournisseur ; le rafraîchissement du brief reste une lecture locale.
- `GET /api/dashboard/today` gagne un bloc `courrier` : lignes groupées par cible (cinq au plus), total pour le compteur, état et fraîcheur par compte. Une lecture en échec ajoute `email` à `indisponibles`.
- Une ligne par cible : « 2 mails de Mme Durand sur Refonte du site · livrable Maquettes, échéance jeudi », avec le motif.
- La fraîcheur est toujours dite : « relevé à 10 h 42 », « jamais relevé : ouvre tes e-mails ou appuie sur Relever », « compte pro@ à reconnecter », « compte perso@ illisible depuis 9 h 10 ».
- Place : après les factures échues, avant les rendez-vous. Domaine visuel `taches` (`components/ui/Etiquette.tsx:17`).
- Aucune source quand aucun compte n'est branché.
- **Ancre** (constat 16) : le groupe de la source porte `id="brief-source-email"`, et son titre `tabIndex={-1}` pour recevoir le focus.

**Garde de livraison** (constat 7). Le lot 3 livre l'écran avant que la relève existe ; sans garde, un compte branché afficherait « jamais relevé : ouvre tes e-mails » alors qu'ouvrir ses e-mails ne relèverait rien. Le module de la veille porte une constante `RELEVE_COURRIER_LIVREE = False`. Tant qu'elle est fausse, `/today` ne rend pas le bloc `courrier` et la source n'apparaît pas. Le lot 5, qui livre la relève, la passe à vrai dans le même commit, avec le test de bout en bout qui la prouve. Aucune release intermédiaire ne peut donc exposer une promesse sans chemin. Les pastilles, la ligne de « Cette semaine » et la liste des silences n'ont pas besoin de garde : sans relève, aucune ligne n'existe à afficher.

**Actions sur une ligne.** Inchangées : libellé bouton de dépliage (`aria-expanded`) ; à droite, « Vu » seul ; dans le dépliage, par mail, « Ouvrir le mail », « Oui, c'est lié », « Pas lié », « Taire », « Proposer un créneau ». Mêmes effets que la V2 (« Vu » sort la cible du brief et garde la pastille ; « Oui, c'est lié » demande la cible pour les règles 4 et 6 ; « Pas lié » écarte le fil pour cette cible 90 jours ; « Taire » 7 jours ou jusqu'à réactivation, 90 jours au plus, levée depuis Paramètres, rubrique Services). « Relever » et « Relever la suite » apparaissent avec le lot 5.

**« Ouvrir le mail ».** Route de résolution `GET /api/veille-courrier/messages/{id}/ouvrir` : elle rend l'identifiant du fournisseur, ou le retrouve par `Message-ID` (IMAP : recherche sur l'en-tête dans la boîte de réception sélectionnée en lecture seule ; Gmail : `rfc822msgid:`). Lecture chez le fournisseur, **aucune écriture en base** : elle ne dépend donc pas de P0 et vit au lot 3. L'écran ouvre ensuite le mail par l'identifiant rendu (`services/api/email.ts:294-295`).

**« Cette semaine »** (décision 6, constat 16). `GET /api/dashboard/semaine` gagne un champ `courrier` distinct de `a_venir` : le nombre de cibles dont l'échéance tombe de demain à J+7 et qui ont un rapprochement `nouveau`. Une seule ligne quand il est positif : « Mail récent sur 2 tâches ou livrables de la semaine ». `components/prototype/CetteSemaine.tsx` se relit au focus et au retour de visibilité, sur le patron du brief (`components/prototype/usePrototypeReadData.ts:48-50`), au lieu d'une lecture unique au montage. Le clic appelle une nouvelle propriété `onOpenBriefSource('email')` : l'Accueil fait défiler jusqu'à `#brief-source-email` et y pose le focus. Une lecture en échec ajoute `email` aux `indisponibles` de la route, et la ligne dit « Les mails rapprochés n'ont pas pu être lus ».

**Pastille « Mail récent ».** Inchangée : `Etiquette` avec texte, sur `components/memory/ProjectDeliverablesSection.tsx`, `components/crm/DeliverablesList.tsx` et la carte d'une tâche, tant qu'un rapprochement `nouveau` ou `vu` de moins de 90 jours vise la cible. Données : `GET /api/veille-courrier/pastilles?projet_id=`.

**Accessibilité et mode démo.** Inchangés : boutons nommés d'après la cible, dépliage dans l'ordre de tabulation, test vitest par rôle et par nom ; `maskText` sur expéditeurs, objets, cibles et titre prérempli.

### 6.7 Le créneau libre

**Déclenchement.** Au geste « Proposer un créneau », jamais en fond. `POST /api/veille-courrier/creneaux` avec la cible, la durée et le fuseau du poste.

**Horizon** (constat 13). Le plus proche entre l'échéance de la cible et le prochain rendez-vous avec ce contact. Sans échéance ni rendez-vous, aucun créneau. Lecture bornée à 30 jours.

- **Règle de l'échéance.** Une échéance est un **jour civil** : la partie date de la valeur stockée, sans conversion de fuseau (minuit Z pour une tâche, relu naïf ; date brute pour un livrable). L'horizon est la **fin des heures ouvrées de ce jour, dans le fuseau du poste** (18 h, section « Heures et jours »). Une tâche due le jeudi 01/10 donne « avant jeudi 18 h » à Paris comme à Fort-de-France. Lire l'échéance comme un instant la ferait tomber à 2 h le jour même à Paris et à 20 h la veille en Martinique.
- **Règle du rendez-vous.** Son début, converti en instant depuis la convention de son agenda.

**Lecture des agendas, au moment du geste.** Chaque agenda est lu par une fonction qui rend `(occupations, complet)`. Un agenda dont `complet` est faux est **illisible** : aucun créneau n'est proposé, et l'écran le nomme (« l'agenda Travail n'a pas pu être lu : aucun créneau proposé, pour ne pas t'en suggérer un déjà pris »), avec « Réessayer ».

- **Agendas locaux** (constat 2). Requête dédiée, jamais `list_events` du fournisseur local (filtre sur le seul début, `services/calendar/local_provider.py:215-226`, et plafond de 100) :
  - seulement les agendas `provider == "local"` : le cache Google n'est jamais lu pour un créneau, il peut être périmé ;
  - événements ponctuels avec heure : chevauchement, `start_datetime < fin` et `end_datetime > debut`, bornes ramenées en heure murale de Paris ;
  - journées entières : `start_date <= dernier jour` et `end_date >= premier jour` (fin inclusive, BUG-144) ;
  - séries : **toutes** les lignes dont `recurrence` n'est pas nul et dont le début précède la fin de fenêtre, sans borne basse, pour qu'une série commencée trois mois plus tôt soit lue.
- **Dépliage d'une série** (constat 2, mesuré dans l'environnement). `dateutil` refuse toute différence de conscience du fuseau entre DTSTART et UNTIL, dans les deux sens. Le dépliage :
  1. rend le début conscient en heure de Paris (convention de la colonne) ;
  2. normalise UNTIL avant `rrulestr` : en Z, gardé ; date seule, remplacée par 23:59:59 de ce jour à Paris, convertie en Z ; date-heure sans fuseau, lue en heure de Paris, convertie en Z ;
  3. déplie sur la fenêtre (les occurrences gardent l'heure murale de Paris à travers les changements d'heure, vérifié : 10 h le 01/09 en +02:00, 10 h le 29/12 en +01:00) ;
  4. toute exception, à la normalisation comme au dépliage, rend l'agenda local illisible.
  Les exceptions d'une série n'existent pas en base (section 5) : une occurrence annulée chez l'organisateur apparaît occupée. C'est une erreur dans le sens prudent.
- **Google** (constat 17). Lecture par le fournisseur (`services/calendar/google_provider.py:130-150`), occurrences dépliées (`singleEvents`, `services/calendar_service.py:162`), **sans écriture du cache**. Toutes les pages sont suivies jusqu'à épuisement du jeton de page ; au-delà de dix pages de 250, l'agenda est incomplet. `status == "cancelled"` ignoré. `CalendarEventDTO` gagne `transparent: bool = False`, rempli depuis `transparency` dans `_gevent_to_dto` : un événement transparent ne bloque rien. Le jeton passe par `ensure_valid_access_token` : une erreur rend l'agenda illisible, quel que soit son code.
- **CalDAV** (constat 3). Lecture stricte dédiée, distincte de `list_events` : tous les événements de la fenêtre, sans tranche ; au-delà de 500, incomplet ; **un seul VEVENT illisible rend l'agenda incomplet** au lieu d'être sauté. `_caldav_event_to_dto` lit `STATUS` (au lieu du statut écrit en dur, `services/calendar/caldav_provider.py:664`) et `TRANSP` : `CANCELLED` ignoré, `TENTATIVE` occupé, `TRANSPARENT` libre. **Heure flottante** (DTSTART sans TZID, rendue naïve, `services/calendar/caldav_provider.py:620-623`) : lue en heure de Paris, la convention que l'import ICS applique déjà à une heure flottante (`services/import_service.py:56-59`) et celle de l'écran de l'agenda pour une heure sans fuseau (`routers/calendar.py:113-121`) : le créneau et l'agenda affiché disent la même heure.
- Événements annulés ignorés ; provisoires occupés ; journées entières occupées.

**Heures et jours** (décision 5). Inchangés : fuseau du poste envoyé par l'écran et validé comme `_validate_timezone` (`routers/calendar.py:87-97`), repli sur Europe/Paris dit à l'écran ; heures stockées converties en instants depuis leur convention (heure murale de Paris pour `CalendarEvent`, instant pour les DTO Google et CalDAV, heure de Paris pour une heure flottante) ; heures ouvrées de `WorkCalendar` (`services/planning.py:168-172`), sans réglage nouveau ; onze jours fériés légaux de métropole par une fonction pure, Pâques calculé, moteur PERT inchangé (`services/planning.py:20`) ; fin inclusive des journées entières.

**Ce que le créneau ne suppose pas.** Qu'une ligne locale écrite avant B-1486 ou B-1487 soit en heure de Paris (section 2, C-1). Le lot 4 n'est pas livré avant la décision C-1.

**Résultat.** Inchangé : une heure par défaut (30 min, 1 h, 2 h), trois créneaux au plus, un par demi-journée au plus, fraîcheur dite, « Aucun créneau d'une heure avant jeudi 18 h » plutôt qu'un créneau après l'horizon.

**Réservation.** Inchangée : « Réserver ce créneau » ouvre `NewEventForm` prérempli (propriété de valeurs initiales à ajouter, `components/prototype/MeetingConversationCard.tsx:212-229`) et passe par son étape de confirmation (`:229`). La création suit le chemin corrigé par B-1487 : elle envoie le fuseau du poste (`components/prototype/MeetingConversationCard.tsx:270`), que le serveur convertit en heure de Paris (`routers/calendar.py:1194-1195`).

### 6.8 La relève de fond, facultative

Inchangée : désactivée par défaut, gouvernée par le seul interrupteur de Paramètres, rubrique Services (décision 2), texte d'activation de la V2, planificateur calqué sur les notifications (`main.py:348-364`), absent sous `THERESE_SKIP_SERVICES`, annulé à l'arrêt ; même chemin que la relève au geste, donc même verrou par compte, même insertion sans doublon, même filigrane monotone ; compte `a_reconnecter` sauté ; client de P0 ; coupée par « Effacer toutes mes données », qui efface `preferences`.

### 6.9 Ce qui ne part jamais sans confirmation

Automatique, et seulement cela : lire des en-têtes sans les marquer lus, calculer, écrire une proposition locale et l'état d'un compte. Tout le reste reste au clic, comme dans la V2 (répondre, brouillon, transfert, indicateurs, classement, rattachement, statut ou échéance d'une cible, relance, réservation, envoi à un modèle en ligne).

**Garde en liste blanche** (constat 12). Deux mécanismes, testés séparément :

- côté serveur IMAP : la boîte est sélectionnée par `EXAMINE` ; le test vérifie l'appel `folder.set("INBOX", readonly=True)` et l'absence de `select` en écriture ;
- côté code : les doublures du fournisseur IMAP et du client Gmail **échouent sur tout appel qui n'est pas dans la liste permise**. IMAP : connexion, `folder.status`, `folder.set` en lecture seule, recherche d'UID, `fetch` en en-têtes seuls sans marquage. Gmail : liste des messages et lecture en `metadata`. Toute autre méthode, présente ou future (`create_folder`, `delete_folder` à `services/email/imap_smtp_provider.py:813` et `:834`, `trash_message`, `create_label`, `update_label`, `delete_label`, `batch_modify_messages` à `services/gmail_service.py:414`, `:431`, `:445`, `:449`, `:465`, ou une méthode ajoutée demain), fait échouer le test.

### 6.10 Confidentialité et modèle

Inchangée : V1 sans modèle ; phase 2 sur modèle Ollama local non « cloud » seulement (`services/ollama_capabilites.py:86-90`), sans repli en ligne (B-1071, `services/llm.py:832-840`), corps lu seulement pour un mail rapproché et enveloppé par `sanitize_for_context` ; en ligne, jamais en fond.

### 6.11 Effacement, portabilité et rétention

Une seule fonction de service oublie les rapprochements et les silences d'une fiche, d'une adresse, d'un projet, d'une cible ou d'un compte. Elle est appelée depuis :

| Chemin | Lieu à HEAD | Ce qui part |
|---|---|---|
| Purge totale | `routers/data.py:632-697` (tâches `:671`, livrables `:675`) | les trois tables, avant `EmailMessage` et `EmailAccount` |
| Déconnexion d'un compte | `routers/email.py:758-766` | les trois tables pour ce compte |
| Anonymisation manuelle | `routers/rgpd.py:184`, avant `effacer_l_identite` | rapprochements de la fiche (`contact_id`) **et ceux dont `expediteur_adresse` vaut l'adresse de la fiche** ; silences `expediteur` à cette adresse. L'adresse est lue avant l'effacement de l'identité |
| Anonymisation automatique | `services/rgpd_auto.py:199-208`, avant `effacer_l_identite` (`:199`) | idem |
| Suppression d'une fiche | `routers/memory.py:1053` | idem |
| Suppression d'un projet, et la cascade de ses tâches et livrables | `routers/memory.py:361` (appelée par `:1113`, `:1411` et l'anonymisation) | rapprochements et silences du projet ; ceux de ses tâches et livrables partent avec, par l'invariant `projet_id` (section 6.4) |
| Suppression d'une tâche | `routers/tasks.py:293` ; tâches d'une fiche anonymisée, `routers/rgpd.py:273` | rapprochements de la tâche |
| Suppression d'un livrable | `routers/crm.py:378` | rapprochements du livrable |

Aucun `PRAGMA foreign_keys` : chaque chemin est explicite et testé.

**Portabilité d'une fiche** (constat 8). `GET /api/rgpd/export/{contact_id}` (`routers/rgpd.py:47`) rend, avant tout effacement possible, `rapprochements_courrier` (lignes dont `contact_id` vaut la fiche ou dont `expediteur_adresse` vaut son adresse) et `silences_courrier` (silences `expediteur` à son adresse). `RGPDExportResponse` (`models/schemas.py:457-467`) gagne deux listes par défaut vides, comme `prestations` et `email_messages` (B-590).

**Rétention** (décision 4, constat 11). Tout court depuis `cree_le` ou `maj_le`, horloge locale, jamais depuis l'en-tête `Date:` :

- rapprochements `ecarte` : 90 jours après `maj_le` ;
- silences : `jusqu_au`, jamais nul, jamais au-delà de 90 jours ;
- rapprochements `nouveau` et `vu` : 90 jours après `cree_le` ;
- rapprochements `confirme` : tant que la cible, la fiche et le compte existent.

L'expiration s'applique au démarrage, avant la première requête, puis au début de chaque relève ; les lectures filtrent de toute façon les lignes expirées.

**Export complet, sauvegarde et restauration.** Inchangés : les trois tables entrent dans l'export RGPD complet (`routers/data.py:172-430`), `data_format_version` passe de « 1.4 » à « 1.5 » (`routers/data.py:262`) ; l'archive porte la base entière (`routers/data.py:1086`) ; une sauvegarde d'avant P-105 restaurée recrée les tables vides, puisque la base est rouverte par `init_db` (`routers/data.py:1470-1479`).

## 7. Mise en œuvre, lot par lot

Chaque lot fait l'objet d'un commit, tests rouges d'abord, sabotage ciblé par fonction et revue adverse du diff. Les lots 3 et 4 de la V3 correspondent aux lots 4 et 5 de la V2 ; la relève au geste, lot 3 de la V2, devient le lot 5.

**Dépendances.**

| Lot | Dépend de | Ne dépend pas de |
|---|---|---|
| 1. Moteur | rien | P0, prérequis d'agenda |
| 2. Données | lot 1 (types des propositions) | P0 |
| 3. Écran, sans relève | lots 1 et 2 | P0 (aucune écriture de fond ; la résolution d'un mail ne fait que lire chez le fournisseur) |
| 4. Créneau libre | lots 1 à 3 (le geste vit dans le dépliage) ; B-1486 et B-1487 (livrés) et A-1 pour la convention ; **décision C-1 avant livraison** ; B-1488 (livré) pour lire Google proprement | P0 (aucune écriture) |
| 5. Relève au geste | P0, B-1488 (livré), lots 1 à 3 ; passe la garde de livraison à vrai | lot 4 |
| 6. Relève de fond | P0, lot 5 | lot 4 |
| 7. Recette | lots 1 à 6 | |

### Lot 1 : le moteur de rapprochement

- **Moteur.** Module pur : normalisation d'adresse, index, règles 1 à 6, garde-fous, écartements par en-têtes puis classeur, clé de message avec repli et empreinte, clé de fil (section 6.3). Retrait, dans un commit à part, de `services/email_contact_matcher.py` (`:16`, sans appelant ni garde-fou d'ambiguïté).
- **Écran, données.** Rien.
- **Tests à écrire en premier** (`tests/test_veille_courrier_rapprochement.py`, un test par règle, chacun saboté) : tous ceux de la V2 (adresses, statuts ignorés, projet à plusieurs cibles, mentions d'objet, domaines, fil confirmé, fil écarté, silences, fils IMAP, en-têtes de masse, classeur sans extrait), plus :
  - message IMAP sans `Message-ID` : clé `empreinte:` identique d'une relecture à l'autre, **y compris après un changement d'UID** ;
  - deux messages distincts au même `Message-ID` : deux clés distinctes, le second n'est pas « déjà traité » ;
  - message sans `Message-ID` ni ancêtre : fil égal à sa clé ; « Pas lié » sur lui n'écarte pas un autre message du même expéditeur.
- **Critères observables.** Sur un jeu d'en-têtes témoin, le moteur rend les propositions attendues, identiques d'une exécution à l'autre.

### Lot 2 : les données

- **Moteur.** Fonction d'oubli (section 6.11), expiration.
- **Écran.** Rien.
- **Données.**
  - Trois modèles dans `models/entities.py`, créés par `create_all` ; révision Alembic de `down_revision = "b8c9d0e1f2a3"` qui crée les tables si elles manquent ; `ALEMBIC_HEAD_REVISION` (`models/database.py:619`) passe à cette révision.
  - Preuve d'estampillage : `tables_de_veille_courrier()` dérivée des modèles, sur le patron de `tables_de_planning()` (`models/database.py:632`), ajoutée à la preuve avec l'exigence « toutes les colonnes ».
  - **Base témoin des tests** (constat 10) : `_creer_tables_veille_reelles(db_path)` dans `tests/test_alembic_stamp.py`, appelée par `_make_patched_tracked_db` (`:98`) après `_creer_tables_sync_reelles` et `_creer_tables_planning_reelles` (`:135-136`), pour que les tests existants qui attendent le ré-estampillage restent verts pour la bonne raison.
  - Export RGPD complet (trois blocs, « 1.5 ») et **export de la fiche** (deux listes, section 6.11).
  - Appel de la fonction d'oubli sur chaque chemin du tableau de la section 6.11.
- **Tests à écrire en premier.**
  - `tests/test_alembic_stamp.py` : constante égale à la vraie tête (`:139`) ; jumeaux de `:307` et `:330` pour les tables de veille ; `make db-migrate` sur base neuve et ancienne ; les tests de ré-estampillage existants verts avec la base témoin étendue.
  - Export complet : trois clés, version « 1.5 » (`tests/test_routers_data.py:152`, et `tests/test_variables.py:213` qui exige l'incrément).
  - **Export de la fiche** : ses rapprochements par `contact_id` et par adresse d'expéditeur présents, silences à son adresse présents, ceux d'une autre fiche absents.
  - Purge totale : zéro ligne dans les trois tables après le 200.
  - Déconnexion : les lignes du compte partent, celles d'un autre restent.
  - Anonymisation manuelle puis automatique : rapprochements de la fiche effacés ; **rapprochement de règle 5 dont l'expéditeur est la fiche anonymisée, sans `contact_id`, effacé** ; silence à son adresse effacé ; silence à une autre adresse gardé.
  - Suppression d'une tâche (`routers/tasks.py:293`), d'un livrable (`routers/crm.py:378`), d'une fiche, d'un projet : lignes correspondantes effacées ; **suppression d'un projet : les rapprochements de ses tâches et livrables partent par la cascade**.
  - Expiration : écarté de 91 jours parti, de 89 jours gardé ; `nouveau` de 91 jours parti ; **un `nouveau` dont `recu_le` est vieux de deux ans mais `cree_le` d'hier est gardé** ; `confirme` ancien gardé.
  - Restauration d'une sauvegarde d'avant P-105 : tables présentes et vides.
- **Critères observables.** Une base 0.75 mise à jour démarre, s'estampille à la nouvelle tête, et `make db-migrate` n'échoue pas.

### Lot 3 : ce que l'utilisateur voit, sans relève

- **Moteur.** Bloc `courrier` de `/api/dashboard/today` (sous la garde `RELEVE_COURRIER_LIVREE`) et champ `courrier` de `/api/dashboard/semaine`, lecture locale seule ; routes des actions (`PATCH` d'un rapprochement, création et levée d'un silence), des pastilles, et **route de résolution « Ouvrir le mail »** avec la recherche par `Message-ID` chez le fournisseur (lecture seule, section 6.6).
- **Écran.**
  - Sixième entrée de `SOURCES_DU_BRIEF` (`components/prototype/prototypeReadModels.ts:223-235`, clé `email`, nom « E-mails »), type `TodayDashboard` étendu (`services/api/dashboard.ts:85`), ancre `brief-source-email`.
  - Lignes groupées, dépliage, « Ouvrir le mail », « Vu », « Oui, c'est lié », « Pas lié », « Taire », fraîcheur et états de compte lus dans `releves_courrier`.
  - `components/prototype/CetteSemaine.tsx` : ligne unique, relecture au focus et à la visibilité, clic vers l'ancre.
  - Liste des silences actifs avec « Réactiver », dans Paramètres, rubrique Services.
  - Pastille « Mail récent ».
  - Masque démo ; libellés au lexique (`docs/rules/RULES-DESIGN.md`, section 13, et `lib/lexique.test.ts`).
- **Données.** Écriture des statuts et des silences, au clic.
- **Tests à écrire en premier** (vitest, puis pytest) : tous ceux du lot 4 de la V2 sauf « Relever » et « Relever la suite », plus :
  - garde fausse : `/today` sans bloc `courrier`, aucune source « E-mails » même avec un compte branché ; garde vraie (forcée en test) : la source et ses phrases de fraîcheur ;
  - « Cette semaine » se relit au focus et au retour de visibilité ;
  - clic sur la ligne de « Cette semaine » : `#brief-source-email` défile et reçoit le focus ;
  - « Ouvrir le mail » d'un message déplacé : la route le retrouve par `Message-ID` ; message introuvable : phrase dédiée ; aucune écriture en base pendant la résolution ;
  - route `/today` : aucun appel réseau (fournisseurs doublés qui échouent si on les appelle).
- **Critères observables.** Garde forcée à vrai, sur des propositions semées en base de démonstration : le brief affiche la ligne, son motif et sa fraîcheur ; « Pas lié » la retire ; « Ouvrir le mail » ouvre le bon message dans l'écran E-mail. Garde à faux : l'Accueil est inchangé.

### Lot 4 : le créneau libre

- **Moteur.** Fonction pure `creneaux_libres` ; fonction pure des jours fériés ; règle de l'échéance ; requête locale dédiée et dépliage normalisé ; lecture stricte CalDAV (STATUS, TRANSP, plafond, erreur fatale) ; lecture Google paginée sans écriture, `transparent` dans le DTO ; route `POST /api/veille-courrier/creneaux`. `python-dateutil` déclaré dans `pyproject.toml` (déjà verrouillé, `uv.lock:2484`).
- **Écran.** Carte des créneaux dans le dépliage ; valeurs initiales de `NewEventForm` ; « Réserver ce créneau ».
- **Données.** Rien. Aucune écriture de cache.
- **Tests à écrire en premier** (`tests/test_creneaux.py`, puis vitest) :
  - semaine type ; week-end ; journée entière ; événement de plusieurs jours à fin inclusive ; annulé ignoré ; provisoire bloquant ; **transparent libre (Google et CalDAV)** ;
  - **par les vraies écritures** (constat 1) : un rendez-vous créé par `POST /api/calendar/events` à 10 h avec `timezone=America/Martinique` bloque 10 h en Martinique (exige B-1487) ; un ICS à `DTSTART:...T080000Z` importé bloque 10 h à Paris en été (B-1486) ; un événement créé par l'outil du chat avec un décalage bloque son heure réelle (exige A-1) ;
  - **séries** (constat 2) : série hebdomadaire commencée trois mois avant la fenêtre, chaque occurrence de la fenêtre bloque ; UNTIL en Z ; UNTIL en date seule ; UNTIL flottant ; COUNT ; événement qui chevauche le début de fenêtre (9 h à 11 h, fenêtre ouverte à 10 h) ; règle malformée : agenda local illisible, aucun créneau ;
  - **CalDAV** (constat 3) : 501 événements : incomplet, aucun créneau, agenda nommé ; un VEVENT malformé parmi dix : idem ; `STATUS:CANCELLED` ignoré ; heure flottante lue en heure de Paris ;
  - **Google** : deux pages suivies ; aucune ligne écrite dans `calendar_events` pendant la lecture ; erreur de jeton : agenda illisible ;
  - **échéance** (constat 13) : tâche due le 01/10 (stockée `2026-10-01T00:00:00Z`) donne l'horizon 01/10 à 18 h à Paris et à Fort-de-France ; livrable dû le 01/10 (date brute), idem ;
  - fériés : 11/11/2026, 25/12/2026, 29/03/2027, 06/05/2027 exclus ; passage à l'heure d'hiver du 25/10/2026 ; fuseau invalide : repli signalé ;
  - échéance passée ou absente : aucun créneau ; horizon ramené au prochain rendez-vous ; un créneau par demi-journée ; phrase dédiée si aucun ;
  - « Réserver ce créneau » ouvre le formulaire prérempli sans rien créer, et la création envoie le fuseau du poste.
- **Critères observables.** Sur les données de démonstration, trois créneaux avant l'échéance d'un livrable, aucun sur un férié ni sur une occurrence d'une réunion récurrente commencée avant la fenêtre.
- **Livraison.** Après la décision C-1, et avec ce qu'elle impose (section 2).

### Lot 5 : la relève au geste (après P0)

- **Moteur.** Méthode de lecture d'en-têtes IMAP (connexion sans dossier, `EXAMINE`, `SINCE`, filigrane), lecture Gmail (première relève, `after:`), route `POST /api/veille-courrier/relever`, verrou par compte, insertion `ON CONFLICT DO NOTHING`, filigrane monotone, garde de deux minutes, états de compte, remise à `jamais` aux quatre points, plafond et compteur, client de P0. La liste de l'écran E-mail n'est pas modifiée.
- **Écran.** Appel de la relève à l'ouverture de l'écran E-mail ; « Relever » et « Relever la suite » ; « N mails pas encore examinés ». `RELEVE_COURRIER_LIVREE` passe à vrai.
- **Données.** Écriture des propositions et de `releves_courrier`.
- **Tests à écrire en premier** (`tests/test_veille_courrier_releve.py`, fournisseurs doublés en liste blanche) :
  - doublures en liste blanche : tout appel hors liste échoue ; `folder.set("INBOX", readonly=True)` appelé, aucune sélection en écriture ; Gmail en `metadata` seulement ;
  - plafond de 50, du plus ancien au plus récent ; `non_examines` exact ; filigrane après écriture ; reprise où la relève précédente s'est arrêtée ; UID inférieur ou égal au filigrane filtré ;
  - **UIDVALIDITY changée sur une boîte de 5 000 messages** : au plus 50 examinés, aucun de plus de 14 jours (date interne), aucun doublon ;
  - **même message relu après remise à zéro du filigrane** : aucune erreur, aucune ligne en double, le filigrane avance ;
  - **deux relèves simultanées du même compte** : une seule lecture chez le fournisseur, les deux réponses portent le même état ;
  - **filigrane monotone** : une écriture plus basse que la valeur en base est ignorée ;
  - deux comptes IMAP, même UID : deux lignes distinctes ;
  - **refus explicite du fournisseur** (réponse 400 `invalid_grant` du point de jeton doublé) : `a_reconnecter`, aucune tentative au geste suivant ; **identifiants OAuth absents** : `a_reconnecter` ;
  - **rafraîchissement en échec réseau** (doublure du client HTTP qui lève `httpx.ConnectError`, pour exercer le vrai classement de B-1488) : `illisible`, retenté au geste suivant ; **réponse 503 de Google** : `illisible` ; **erreur inattendue hors HTTP** (401 de `routers/email.py:319-324`) : `a_reconnecter`, comme l'écran E-mail ;
  - **remise à `jamais`** : un test par point (rappel OAuth, rappel par redirection, configuration IMAP, mise à jour des identifiants) ;
  - serveur IMAP injoignable : `illisible`, aucune exception à l'écran ;
  - deuxième appel sous deux minutes sans `forcer` : aucune connexion ;
  - pendant une purge : 503 « relève suspendue », aucune ligne écrite après le 200 de la purge.
- **Critères observables.** Bout en bout (Playwright, serveur jetable 17393) : un compte doublé reçoit le mail d'un contact de projet ; ouvrir l'écran E-mail le relève ; le brief affiche la ligne, son motif et sa fraîcheur ; « Pas lié » la retire, et une réponse dans le même fil ne la ramène pas ; le client de messagerie montre toujours le mail comme non lu.

### Lot 6 : la relève de fond, facultative (après P0 et le lot 5)

Inchangé par rapport au lot 6 de la V2 (planificateur, suspension par P0, arrêt propre, interrupteur et texte d'activation, préférence `veille_courrier`, mêmes tests), plus : une relève de fond et une relève au geste simultanées sur le même compte ne font qu'une lecture (même verrou).

### Lot 7 : recette réelle

Sur les données de démonstration, puis sur un compte Gmail et un compte IMAP réels : après relève, le client de messagerie montre les nouveaux mails comme non lus ; une réponse IMAP dans un fil écarté n'est pas reproposée ; un créneau n'est jamais posé sur une réunion récurrente locale ; sur un poste réglé sur `America/Toronto`, un rendez-vous créé après B-1487 bloque son heure réelle.

### Phase 2, après usage réel

Inchangée : modèle local non « cloud » pour départager et résumer, derrière une préférence serveur ; tests « modèle `:cloud` refusé » et « Ollama arrêté : étape sautée, aucun repli ».

## 8. Ce que la V3 retire ou reporte, et pourquoi

Aucune décision de Ludo n'est réduite : les six décisions du 25/09 sont tenues telles quelles.

| Retiré ou reporté | Pourquoi |
|---|---|
| Test « une EXDATE libère son jour » (V2, lot 5) | Donnée impossible : aucune EXDATE n'est stockée (`services/import_service.py:79-82`), l'écran n'écrit aucune récurrence. Remplacé par l'annonce d'un faux occupé, dans le sens prudent |
| Test « un rendez-vous local à 10 h (Paris) bloque 5 h en Martinique » (V2, lot 5) | Il passait avec le code défectueux. Remplacé par des tests qui passent par les vraies écritures |
| Phrase « ce qui rafraîchit au passage le cache » (V2, 5.7) | Fausse : le fournisseur Google ne l'écrit pas. Le créneau ne l'écrit pas non plus |
| `routers/actions.py:164` dans les chemins d'effacement | Ne supprime aucune tâche |
| Rétention depuis `recu_le` | L'en-tête `Date:` est écrit par l'expéditeur. Rétention depuis `cree_le` |
| « Relever » et « Relever la suite » au lot de l'écran | Reportés au lot 5 : sans relève livrée, ils seraient des boutons sans chemin |
| Lecture CalDAV par `list_events` pour le créneau | Troncature et omissions silencieuses ; remplacée par une lecture stricte |
| Occurrences déplacées d'une série importée | Reportées hors P-105 : elles ne sont pas en base (section 9, candidat à reproduire) |

## 9. Risques restants

- **Lignes d'agenda antérieures aux correctifs** (C-1). Tant que C-1 n'est pas tranché, le créneau ne part pas ; si la décision est de ne rien convertir, la mitigation retenue alors aura son propre coût (moins de créneaux, ou une phrase de réserve).
- **Occurrence déplacée d'une série importée** (candidat à reproduire, hors P-105). `parse_ics` rend chaque VEVENT, exceptions à RECURRENCE-ID comprises (`services/import_service.py:30`) ; la route d'import saute toute ligne dont l'UID existe déjà dans l'agenda (`routers/calendar.py:1940-1953`). La réunion déplacée n'est donc pas en base, et son créneau réel peut être proposé. Le même défaut touche l'écran de l'agenda.
- **Série importée d'un autre fuseau.** Elle est dépliée à heure murale de Paris ; une réunion hebdomadaire à 10 h en Martinique décale d'une heure les semaines où Paris est à l'heure d'hiver. Le TZID d'origine n'est pas conservé.
- **Dépendance à P0.** Sans elle, pas de relève, donc pas d'alerte réelle ; les lots 1 à 4 avancent, sous la garde de livraison.
- **Dépendance au sens des codes de B-1488.** La section 6.5 classe les états sur les codes que B-1488 a rendus distincts (503, 400, 401). Un changement de ces codes casserait le classement : les tests du lot 5 passent par le vrai client OAuth, doublé au niveau HTTP, pour le voir tout de suite.
- **Fatigue d'alerte, faux négatifs, fils IMAP imparfaits, rétention, fériés de métropole seulement, lecture au geste plus lente qu'un cache, charge chez les fournisseurs, sentiment de surveillance, recouvrement avec P-104** : inchangés par rapport à la V2 (section 9), mêmes parades.
- **Verrou en mémoire.** Il suppose un seul processus serveur, ce qui est le cas de l'application de bureau ; un déploiement à plusieurs processus devrait le remplacer.

## 10. Questions réservées à Ludo

Aucune. P-105 n'efface que les lignes qu'elle crée elle-même, selon la décision 4, n'annonce rien publiquement et ne touche pas à la marque.

C-1 (conversion des anciennes lignes d'agenda) modifie des données de l'utilisateur sans en effacer : elle relève de la délégation, avec une recommandation, dans son propre ticket. Si la décision prise devait effacer des événements, elle reviendrait à Ludo.
