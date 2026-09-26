# RFC P-105 (V2) : alerte quand un mail touche une tâche ou un livrable, et un créneau pour le traiter

Rédigé le 26/09/2026. Remplace la V1 (`docs/plans/2026-09-25-rfc-p105-alerte-mail-tache.md`), jugée NO-GO par la revue adverse (`docs/plans/revues/2026-09-25-revue-rfc-p105-p108.md`, section P-105). Intègre les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, section « Décisions du 25/09/2026 », points 1 à 6 de P-105), qui sont traitées ici comme des faits.

**Base de vérification.** Toutes les lignes citées ont été relues au commit `900765fb` (26/09/2026). Un autre agent commite pendant la rédaction : une ligne peut avoir glissé de quelques rangs, jamais changé de sens. Chemins relatifs à `src/backend/app/` (fichiers `.py`) et à `src/frontend/src/` (fichiers `.ts` et `.tsx`) ; les tests et la documentation partent de la racine du dépôt.

Aucun code avant la validation de ce document.

## 1. Ce que la V2 change

- Les six questions de la revue sont tranchées par les décisions du 25/09 et deviennent des règles de conception.
- Un message est identifié par son en-tête `Message-ID`, et un fil IMAP est reconstitué à partir de `References` et `In-Reply-To`. La relève n'écrit plus jamais dans le cache `EmailMessage`.
- La sixième source du brief ne lit que la base locale et dit sa fraîcheur. Elle ne déclenche aucune lecture chez le fournisseur.
- Le créneau libre lit les agendas au moment du geste, déplie les récurrences locales, exclut les jours fériés et travaille dans le fuseau du système.
- Le découpage en lots nomme, pour chacun, la part moteur, écran et données, ainsi que les tests à écrire en premier.
- Les erreurs de la V1 trouvées en relisant le code sont corrigées (section 8), dont deux qui auraient faussé les créneaux.

## 2. Le besoin

Dr_logic-3D, testeur alpha, sur Discord (fil du 25/09, 03:35 à 04:29) :

- Un client écrit au sujet d'un travail en cours. THÉRÈSE doit faire le rapprochement avec la tâche ou le livrable concerné et prévenir.
- Il veut **suivre sans forcément agir** : être prévenu, pas qu'on réponde à sa place.
- Second volet : proposer un **créneau libre** pour traiter ce mail avant l'échéance, ou avant le prochain rendez-vous avec ce client.

Périmètre accepté par Ludo le 25/09 : lecture seule, aucune action automatique, design challengé avant le code.

## 3. Décisions du 25/09/2026 (tranchées)

1. **Mise au repos des écritures de fond : validée.** Le rapprochement au geste est livré d'abord ; la relève de fond vient après.
2. **L'interrupteur « désactivé par défaut » ne gouverne que la relève de fond.** Le rapprochement au geste est local, visible, et toujours actif.
3. **Les fils IMAP sont reconstitués avant la livraison.** « Pas lié » vaut pour tout le fil, sur Gmail comme sur IMAP.
4. **Rétention : 90 jours** pour les rapprochements écartés et les silences, qui sont aussi effacés avec la fiche à l'anonymisation.
5. **Fuseau du système, jours fériés français exclus** pour le calcul des créneaux.
6. **Une ligne dans « Cette semaine »**, sans relève supplémentaire.

Les questions de la V1 qui n'ont pas été reposées le 25/09 sont tranchées ici (section 5), chacune avec son motif.

## 4. État du code à HEAD

### 4.1 Points d'appui

- **Lecture des mails, au geste seulement.**
  - Gmail : liste enrichie en `format='metadata'`, cinq appels en parallèle (`routers/email.py:935-999`, sémaphore l.958, lecture l.963).
  - IMAP : `imap_tools`, liste depuis le plus récent (`services/email/imap_smtp_provider.py:322-389`). Depuis B-1409 (commit `974c0cb1`), toutes les lectures passent `mark_seen=False` (l.355-359, 437, 693, 750, 862).
  - La liste IMAP télécharge encore les corps complets (aucun `headers_only`), puisqu'elle en tire l'extrait (`imap_smtp_provider.py:994`, `snippet=msg.text[:200]`).
  - `imap_tools` 1.11.1 accepte `headers_only` (`.venv/.../imap_tools/mailbox.py:170-182`).
- **Aucune relève de fond.** Le serveur lance trois boucles : nettoyage OAuth (`main.py:343`), notifications horaires (`main.py:348-364`), purge RGPD quotidienne (`main.py:369-383`). Toutes sont absentes sous `THERESE_SKIP_SERVICES` (`main.py:244`). Règle écrite : « Jamais de sync automatique sans consentement » (`docs/rules/RULES-DONNEES.md:227`).
- **Du mail à la fiche.** `get_crm_contact_by_email` compare sans la casse et refuse l'ambiguïté : deux fiches pour une adresse, aucune (`routers/email.py:192-214`). Elle n'exclut pas les fiches `archive`. `services/email_contact_matcher.py:16` fait la même recherche sans ce garde-fou et n'a aucun appelant dans `src/` ni dans `tests/`.
- **De la fiche à la tâche ou au livrable.**
  - Contact : `stage` vaut `archive` pour le tombeau RGPD (`models/entities.py:37`, et `services/relances.py:42-46` l'exclut déjà).
  - Projet : `contact_id`, `status` (active, completed, on_hold) (`models/entities.py:89-90`).
  - Tâche : `status` (todo, in_progress, done, cancelled), `due_date`, `project_id`, `contact_id` (`models/entities.py:560-566`).
  - Livrable : `project_id`, `status` (a_faire, en_cours, en_revision, valide), `due_date` (`models/entities.py:885-889`). Un livrable n'a pas de contact : le chemin passe par le projet.
- **Le fil Gmail est natif** (`threadId`, `routers/email.py:969`). **Le fil IMAP n'existe pas** : `supports_threads` rend `False` (`imap_smtp_provider.py:179-180`), `_imap_to_dto` ne pose pas `thread_id` (`imap_smtp_provider.py:991-1011`, alors que le DTO a le champ, `services/email/base_provider.py:31`), et la route écrit `msg.thread_id or msg.id` (`routers/email.py:1108`).
- **Brief du jour.** Cinq sources (`components/prototype/prototypeReadModels.ts:223-235`), chacune nommée dans `indisponibles` quand sa lecture échoue (`routers/dashboard.py:291`, doctrine B-051). La route se veut locale : « SQLite local, pas d'appel réseau » (`routers/dashboard.py:278`). Plafond serveur `PLAFOND_BRIEF = 50` (`routers/dashboard.py:264`), compteur de ce qui n'est pas affiché (`prototypeReadModels.ts:208`). Le brief se relit toutes les 5 minutes, au focus et au retour de visibilité (`components/prototype/usePrototypeReadData.ts:5`, `:48-50`).
- **« Cette semaine » (P-135).** Route `GET /api/dashboard/semaine` (`routers/dashboard.py:546-660`), liste `a_venir` triée et plafonnée à 20 (`:543`, `:612-613`), clé `semaine` dans ses `indisponibles` (`:616`). Écran : `components/prototype/CetteSemaine.tsx`, lecture unique au montage (l.58), routage du clic par `kind` (l.94-97).
- **Horaires ouvrés.** `WorkCalendar` du planning : lundi à vendredi, 9 h à 12 h et 14 h à 18 h (`services/planning.py:168-172`), fuseau paramétrable (`:195-199`), aucun jour férié.
- **Fuseau.** L'écran connaît le fuseau du système (`components/calendar/EventForm.tsx:249`, `components/prototype/MeetingConversationCard.tsx:270`). Le serveur sait valider un nom IANA (`routers/calendar.py:87-97`, `_validate_timezone`).
- **Agendas.**
  - `CalendarEvent.start_datetime` est une **heure murale de Paris, naïve** (`services/calendar/local_provider.py:28-40`) ; le cache Google y est ramené aussi (`routers/calendar.py:123-133`).
  - Le cache Google est rempli à chaque liste (`routers/calendar.py:925-993`), avec les occurrences déjà dépliées (`services/calendar_service.py:162`, `singleEvents`).
  - CalDAV est lu en direct et déplié (`services/calendar/caldav_provider.py:226-231`), mais **n'est pas mis en cache** : `_list_events_provider` convertit les DTO sans rien écrire (`routers/calendar.py:812-889`).
  - L'agenda local garde la règle brute (`models/entities.py:529`, tableau JSON de chaînes `RRULE:...`), et aucun code ne la déplie : aucun import de `dateutil` ni de `rrule` dans `src/backend/app/` (seuls l'export ICS et l'import la manipulent, `routers/calendar.py:2036-2039`, `services/import_service.py:76-79`).
  - `python-dateutil` est dans le verrou (`uv.lock:2484`) mais pas dans `pyproject.toml` ; `icalendar` y est déclaré (`pyproject.toml:53`).
- **Création d'un rendez-vous.** Le formulaire `NewEventForm` (`components/prototype/MeetingConversationCard.tsx:212-229`) a sa propre étape de confirmation (état `confirming`, l.229), mais n'accepte aucune valeur initiale.
- **Confirmation des outils.** Seule la lecture classée passe sans carte (`services/tool_confirmations.py:33-49`, classes `services/contexte_execution.py:26-60`).
- **Contenu non fiable.** `sanitize_for_context` (`services/prompt_security.py:216`).
- **Mode maintenance.** Toute requête `/api/` est admise ou refusée par `maintenance_mode.admit` (`main.py:718-734`) ; la restauration attend les requêtes admises (`services/maintenance.py:51-66`). La purge totale ne passe pas par ce verrou : elle suspend les seules créations du chat (`routers/data.py:586-589`, `services/memory_tools.py:1256-1266`) et attend quelques travaux (`routers/data.py:602-629`).
- **Schéma.** Tête Alembic épinglée `ALEMBIC_HEAD_REVISION = "b8c9d0e1f2a3"` (`models/database.py:619`). L'application packagée ne lance pas `alembic upgrade head` : `create_all` crée les tables manquantes mais n'ajoute aucune colonne (`models/database.py:320-324`, `:1113`), et la preuve d'estampillage doit couvrir chaque élément nouveau (`models/database.py:688-770`, modèle `tables_de_planning()` l.632-640). Tests du motif : `tests/test_alembic_stamp.py:307` et `:330`.
- **Export, purge, sauvegarde.** Export RGPD table par table, `data_format_version` à « 1.4 » (`routers/data.py:172-430`, l.262 ; test `tests/test_routers_data.py:152` ; `tests/test_variables.py:213` exige l'incrément). Purge totale table par table (`routers/data.py:632-697`). L'archive de sauvegarde porte `therese.db` entier (`routers/data.py:1076`) et la réouverture après restauration relance `init_db` (`routers/data.py:1442-1452`).
- **Effacements existants.** Déconnexion d'un compte (`routers/email.py:758-766`, effacement à la main, sans cascade). Anonymisation manuelle (`routers/rgpd.py:184`, projets l.256-265, tâches l.271-273, mails l.276-281). Anonymisation automatique (`services/rgpd_auto.py:199-208`, identité et mails seulement). Suppression d'une fiche (`routers/memory.py:1053`), d'un projet (`routers/memory.py:361`, `:1389`), d'une tâche (`routers/tasks.py:283`, `routers/actions.py:164`), d'un livrable (`routers/crm.py:365-378`).
- **Mode démo.** `useDemoMask` et `maskText` (`hooks/useDemoMask.ts:19`), déjà appliqués au brief (`components/prototype/TodayDashboardCard.tsx:309-310`).
- **Lignes du brief.** Primitive `Ligne` : libellé bouton qui couvre la ligne, emplacement `droite` où les boutons restent cliquables (`components/ui/Ligne.tsx:64-105`).

### 4.2 Manques

- Aucun rapprochement entre un mail et un projet, une tâche ou un livrable.
- Aucun calcul de créneau libre, aucune liste de jours fériés (recherche de « férié » et « holiday » sans résultat utile dans `src/backend/app/`).
- `EmailAccount` n'a aucun état de compte, et `last_sync` n'est jamais écrit (`models/entities.py:336-378`, l.375).
- Le consentement cloud vit dans l'interface seule (`lib/consent.ts:44-67`).
- La pièce « mise au repos » du chantier du 25/09 n'existe pas encore dans le code : `services/maintenance.py` ne porte que le verrou de restauration, et aucun symbole `mise_au_repos` n'existe.

## 5. Conception V2

### 5.1 Vocabulaire

À l'écran, le mot « travaux » désigne les traitements longs (`docs/rules/RULES-DESIGN.md`, section 13, ligne « processing-tasks »). La V1 parlait de « travail en cours » : ce mot ne paraîtra jamais à l'écran. On dit **la tâche** ou **le livrable**, et **la cible** dans ce document. La source du brief s'appelle **« E-mails »**, comme l'entrée « Écrire un e-mail » de l'établi (`lib/etabli.ts:27`). La marque sur une tâche ou un livrable s'appelle **« Mail récent »**. Les deux libellés entrent dans la table du lexique (section 13) au lot 4.

### 5.2 Le rapprochement, un moteur pur

Nouveau module de fonctions pures, sans réseau ni base : `rapprocher(entete, index, reglages) -> list[Proposition]`. L'index est construit une fois par relève.

**L'index.**

- Adresses des fiches non archivées, normalisées (minuscules, espaces retirés). Une adresse portée par deux fiches est marquée ambiguë et ne rapproche rien, comme `get_crm_contact_by_email` (`routers/email.py:208-212`).
- Projets `active` avec leur contact.
- Cibles ouvertes : tâches `todo` ou `in_progress` sans projet ou d'un projet actif ; livrables `a_faire`, `en_cours` ou `en_revision` d'un projet actif. Les `in_progress` et `en_cours` passent devant.
- Cette définition de « ouvert » est un paramètre du moteur, pour suivre P-104 (fil de travail) le jour venu.
- Rapprochements confirmés et écartés encore retenus, par fil.

**Les règles, dans cet ordre.**

| Rang | Règle | Niveau | Cible | Motif affiché |
|---|---|---|---|---|
| 1 | Le fil porte un rapprochement confirmé | sûr | la cible confirmée | « suite du fil rattaché à Maquettes » |
| 2 | Expéditeur = contact d'une tâche ouverte | sûr | la tâche | « Mme Durand, contact de la tâche Relecture » |
| 3 | Expéditeur = contact d'un projet actif qui n'a qu'une cible ouverte | sûr | cette cible | « contact du projet Refonte, livrable Maquettes en cours » |
| 4 | Expéditeur = contact d'un projet actif qui a plusieurs cibles ouvertes | probable | le projet | « contact du projet Refonte : lequel ? » et les trois premières cibles |
| 5 | L'objet cite le nom d'un projet actif ou d'un livrable ouvert | probable | la cible citée | « l'objet cite Refonte du site » |
| 6 | Même domaine que le contact d'un projet actif, hors domaines grand public | à confirmer | le projet | « même société que Mme Durand » |

**Garde-fous.**

- Un fil écarté pour une cible n'est plus jamais proposé pour cette cible tant que l'écart est retenu (90 jours, décision 4).
- Un silence actif (projet, expéditeur ou fil) supprime la proposition.
- Mention dans l'objet : accents repliés par la même méthode que `_fold` (`services/memory_tools.py:902-908`), frontière de mot (« Site » ne trouve pas « Situation »), nom de quatre lettres au moins, liste fermée de mots trop courants (« site », « devis », « projet », « facture », « contrat », « réunion », « rendez-vous »). L'objet seulement : le corps n'est jamais lu en V1.
- Domaine : une liste fermée de domaines grand public (gmail.com, googlemail.com, outlook.fr, outlook.com, hotmail.fr, hotmail.com, live.fr, live.com, msn.com, yahoo.fr, yahoo.com, icloud.com, me.com, orange.fr, wanadoo.fr, free.fr, sfr.fr, neuf.fr, laposte.net, bbox.fr, gmx.fr, gmx.com, proton.me, protonmail.com, aol.com) ne sert jamais à la règle 6.
- **Un rapprochement est une proposition.** Il ne modifie ni la fiche, ni la cible, ni le mail.

**Messages écartés avant toute règle.**

1. Les mails dont l'expéditeur est l'adresse du compte lui-même.
2. Les messages de masse, reconnus aux seuls en-têtes : `List-Id`, `List-Unsubscribe`, `Precedence` (bulk, list, junk), `Auto-Submitted` différent de `no`.
3. Puis le classeur existant, appelé avec l'objet et l'expéditeur. Il lit aussi l'extrait (`services/email_classifier_v2.py:194`), vide en lecture d'en-têtes : c'est pourquoi les en-têtes passent en premier.

**Choix tranchés ici** (questions 2 et 3 de la V1, non reposées le 25/09) :

- « Ouvert » couvre tout ce qui n'est pas terminé dans un projet actif, les cibles déjà commencées en tête. Motif : un client écrit aussi sur ce qui n'a pas démarré, et l'ordre suffit à hiérarchiser.
- La règle du domaine est gardée au niveau « à confirmer ». Motif : le cas du collègue qui écrit à la place du contact est le premier faux négatif de la V1, et le niveau le plus bas n'affirme rien.

### 5.3 Identité d'un message et fils

**Identité.** La clé d'un message est son en-tête `Message-ID` normalisé (chevrons et espaces retirés, minuscules). À défaut d'en-tête, la clé est l'identifiant du fournisseur préfixé par le compte. On garde aussi l'identifiant du fournisseur pour ouvrir le mail : identifiant Gmail, ou, pour IMAP, le couple UIDVALIDITY et UID de la boîte de réception.

Motif : un UID IMAP change quand le message change de dossier (identifiant « Dossier::uid », `imap_smtp_provider.py:214-232`) et redevient ambigu quand UIDVALIDITY est remise à zéro. Le `Message-ID` survit aux deux. « Ouvrir le mail » essaie l'identifiant du fournisseur ; s'il ne répond plus, il recherche le `Message-ID` dans la boîte, et à défaut le dit (« ce mail a été déplacé ou supprimé »).

**Pourquoi la relève n'écrit jamais `EmailMessage`.** La clé primaire du cache est l'identifiant seul (`models/entities.py:391`), un petit entier pour IMAP. Deux comptes IMAP produisent vite le même « 42 » : la branche IMAP de `get_message` saute alors la ligne sans rien dire (`routers/email.py:1233-1243`), la branche Gmail insérerait un doublon (`:1276`). Passer à une clé composite exigerait de reconstruire la table sous SQLite et de reprendre la clé étrangère `email_follow_ups.email_message_id` (`models/entities.py:938`) : un chantier à lui seul, sans bénéfice pour P-105. La table des rapprochements porte donc elle-même le peu qu'elle affiche (section 5.4).

**Fils.**

- Gmail : la clé de fil est `gmail:` suivi du `threadId`.
- IMAP (décision 3) : la relève lit `Message-ID`, `In-Reply-To` et `References`, que la lecture d'en-têtes fournit. La clé de fil est, dans cet ordre :
  1. celle d'un ancêtre déjà connu : si l'un des identifiants de `References` ou `In-Reply-To` figure dans un rapprochement retenu du même compte, le message hérite de son fil ;
  2. sinon, le premier identifiant de `References` (la racine, que la RFC 5322 demande de conserver) ;
  3. sinon, `In-Reply-To` ;
  4. sinon, son propre `Message-ID`.
- Aucun regroupement par objet (« Re: ») : deux conversations distinctes au même objet seraient fondues.

### 5.4 Données

Trois tables nouvelles, créées par `create_all` au démarrage et par une révision Alembic. Aucune colonne n'est ajoutée à une table existante.

**`rapprochements_courrier`.**

| Champ | Contenu |
|---|---|
| `id` | identifiant |
| `account_id` | compte (clé étrangère `email_accounts.id`, indexée) |
| `message_cle` | `Message-ID` normalisé, ou identifiant fournisseur préfixé |
| `message_fournisseur_id` | identifiant Gmail, ou UIDVALIDITY et UID IMAP |
| `fil_cle` | clé de fil (section 5.3), indexée |
| `ancetres` | identifiants `References` et `In-Reply-To`, tableau JSON borné à 20 |
| `recu_le` | date de réception, UTC naïve comme les autres colonnes DateTime (`routers/email.py:81-87`) |
| `expediteur_adresse`, `expediteur_nom` | normalisée ; nom tel quel |
| `objet` | tronqué à 200 caractères |
| `contact_id`, `projet_id` | fiche et projet rapprochés (nullables, indexés) |
| `cible_type`, `cible_id` | `tache`, `livrable` ou `projet` (règles 4 et 6) |
| `regle`, `niveau` | 1 à 6 ; `sur`, `probable`, `a_confirmer` |
| `statut` | `nouveau`, `vu`, `confirme`, `ecarte` |
| `cree_le`, `maj_le` | dates |

Unicité sur (`account_id`, `message_cle`, `cible_type`, `cible_id`). La V1 refusait d'y ranger objet et expéditeur ; la revue a montré que la relecture du cache ne tient pas (section 5.3). Ces trois champs sont désormais des données personnelles de la table : elles entrent dans l'export, la purge, l'anonymisation et la rétention (section 5.11).

**`silences_courrier`.** `id`, `account_id` (nullable), `type` (`projet`, `expediteur`, `fil`), `valeur` (identifiant de projet, adresse normalisée ou clé de fil), `jusqu_au` (jamais nul), `cree_le`.

**`releves_courrier`**, une ligne par compte. `account_id` (clé primaire et étrangère), `uidvalidity` et `dernier_uid` (IMAP), `filigrane_date` (Gmail), `premiere_releve_le`, `derniere_tentative_le`, `derniere_reussite_le`, `etat` (`jamais`, `ok`, `illisible`, `a_reconnecter`), `code_erreur` (un code, jamais le texte d'une exception, doctrine `message_pour_ecran`), `non_examines` (entier).

Motif de la troisième table plutôt qu'une colonne sur `EmailAccount` (constat 9) : une colonne nouvelle exige une migration ad hoc au démarrage, puisque `create_all` n'ajoute aucune colonne à une table existante (`models/database.py:320-324`), plus une ligne dans la preuve. Une table neuve est créée par `create_all` et se prouve comme les tables de planning. `EmailAccount.last_sync` reste tel quel, jamais écrit.

**Préférence serveur** `veille_courrier` (table `preferences`) : `{"active": false, "intervalle_min": 30, "comptes": [...]}`. Elle ne sert qu'à la relève de fond (section 5.8).

### 5.5 La relève au geste

**Un seul chemin** : `POST /api/veille-courrier/relever?account_id=...&forcer=...`. Il lit des en-têtes, applique les règles, écrit des propositions et l'état du compte. Il ne lit jamais un corps et ne modifie rien chez le fournisseur.

**Qui l'appelle.**

- L'ouverture de l'écran E-mail (vue complète `components/email/EmailList.tsx` et carte `components/prototype/EmailConversationCard.tsx`), une fois par compte et par ouverture, sans attendre la réponse pour afficher la liste.
- Le bouton « Relever » de la source E-mails du brief (`forcer=true`).
- Sans `forcer`, le serveur ne relit pas un compte relevé il y a moins de deux minutes : il rend l'état connu. Motif : basculer d'écran en écran ne doit pas multiplier les connexions IMAP.

**Lecture IMAP.** Une méthode nouvelle du fournisseur, distincte de la liste :

- `headers_only=True`, `mark_seen=False`, boîte de réception seulement ;
- statut du dossier lu d'abord (UIDVALIDITY) ; si elle a changé, le filigrane repart de zéro (les rapprochements existants restent valides, puisqu'ils sont identifiés par `Message-ID`) ;
- critère UID « dernier + 1 à la fin », ordre croissant ; les UID inférieurs ou égaux au filigrane sont filtrés, puisque le serveur rend toujours le dernier message pour une plage ouverte au-delà du maximum.

**Lecture Gmail.** Liste de la boîte de réception postérieure au filigrane (`after:` en secondes), puis `format='metadata'` message par message, comme la liste existante. Les identifiants sont tous listés (ils sont légers), puis les métadonnées lues des plus anciens aux plus récents.

**Plafond et filigrane** (constat 8).

- Au plus 50 messages examinés par relève, **du plus ancien au plus récent** après le filigrane. Le filigrane avance sur le dernier message traité, et seulement après l'écriture réussie de ses propositions.
- Ce qui reste est compté dans `non_examines`. Le brief le dit (« 34 mails pas encore examinés ») avec un bouton « Relever la suite », selon la doctrine B-425.
- **Première relève d'un compte** : les 14 derniers jours, 50 messages au plus parmi les plus récents ; le filigrane est posé sur le plus récent. Le brief dit « rapprochement commencé le 26/09 ». Motif : parcourir tout l'historique d'une boîte n'apporte rien à une alerte, et coûterait des minutes sur une machine modeste.
- Deux relèves du même message n'écrivent aucune ligne en double (contrainte d'unicité).

**États de compte** (constat 9).

- Jeton OAuth non rafraîchissable (401 de `ensure_valid_access_token`, `routers/email.py:289-292` et `:321-324`) : `a_reconnecter`, posé une fois. Les relèves suivantes de ce compte ne tentent plus rien jusqu'à la reconnexion, qui remet l'état à `jamais`.
- Serveur injoignable, délai dépassé, identifiants refusés : `illisible`, retenté au geste suivant.
- Dans les deux cas, aucune exception ne remonte à l'écran : la réponse porte l'état, et le brief le nomme.

**Mise au repos** (décision 1). La relève écrit en base. Elle est donc cliente de la pièce « mise au repos » du chantier du 25/09 (`docs/plans/2026-09-25-chantier-mise-au-repos-ecritures-de-fond.md`) : pendant une purge ou une restauration, elle refuse d'entrer (réponse 503 « relève suspendue ») et celle en vol est attendue. Sans cela, une relève commencée avant une purge pourrait écrire après son 200, et la promesse I1 tomberait : la purge totale n'attend aujourd'hui que les créations du chat et quelques indexations (`routers/data.py:586-629`). **La livraison de cette pièce est un prérequis du lot 3**, pas seulement sa validation.

### 5.6 Ce que l'utilisateur voit

**La source « E-mails » du brief** (constat 4).

- Elle lit **seulement** `rapprochements_courrier` et `releves_courrier`. Elle ne déclenche jamais de relève, et le rafraîchissement de 5 minutes du brief (`usePrototypeReadData.ts:48`) reste une lecture locale.
- `GET /api/dashboard/today` gagne un bloc `courrier` : lignes groupées par cible (cinq au plus), total pour le compteur, et par compte son état et sa fraîcheur. Une lecture en échec ajoute la clé `email` à `indisponibles`, la même clé que `get_setup_status` (`routers/dashboard.py:174`).
- Une ligne par cible, pas par mail : « 2 mails de Mme Durand sur Refonte du site · livrable Maquettes, échéance jeudi », avec le motif du rapprochement.
- La fraîcheur est toujours dite : « relevé à 10 h 42 », « jamais relevé : ouvre tes e-mails ou appuie sur Relever », « compte pro@ à reconnecter », « compte perso@ illisible depuis 9 h 10 ». Une boîte jamais relevée n'est pas une boîte vide (doctrine B-051).
- Place dans le brief : après les factures échues, avant les rendez-vous. Motif : un client qui écrit sur une tâche en cours pèse plus qu'un rendez-vous déjà posé, moins qu'un retard.
- Domaine visuel : `taches` (`components/ui/Etiquette.tsx:17`). Motif : l'alerte porte sur une tâche ou un livrable, et un cinquième domaine demanderait deux jetons de couleur de plus pour rien.
- Aucune ligne quand aucun compte n'est branché : la source n'apparaît pas du tout.

**Actions sur une ligne.**

- Le libellé de la ligne est un bouton de dépliage (`aria-expanded`) : il ouvre, sous la ligne, la liste des mails rapprochés (expéditeur, objet, date, motif).
- À droite de la ligne, un seul bouton : « Vu ».
- Dans le dépliage, pour chaque mail : « Ouvrir le mail », « Oui, c'est lié », « Pas lié », « Taire », « Proposer un créneau ».
- « Vu » : les propositions de cette cible passent à `vu` et sortent du brief ; elles restent visibles sur la cible (pastille) jusqu'à expiration.
- « Oui, c'est lié » (constat 12) : statut `confirme`. Pour une cible `projet` (règles 4 et 6), il demande d'abord laquelle, parmi les cibles ouvertes du projet. C'est ce statut qui rend la règle 1 sûre pour la suite du fil.
- « Pas lié » : statut `ecarte` ; ce fil n'est plus proposé pour cette cible pendant 90 jours.
- « Taire » : ce projet, cet expéditeur ou ce fil, « pendant 7 jours » ou « jusqu'à réactivation (90 jours au plus) ». Les silences actifs se lèvent depuis Paramètres, rubrique Services.
- Motif du dépliage : six boutons par ligne recréeraient la surcharge relevée le 27/08 (« trop d'interfaces »), et la plupart des lignes n'appellent qu'un « Vu ».

**« Cette semaine »** (décision 6). `GET /api/dashboard/semaine` gagne un champ `courrier` distinct de `a_venir` (le tri et le plafond de 20 de `a_venir` ne changent pas) : le nombre de cibles dont l'échéance tombe de demain à J+7 et qui ont un rapprochement `nouveau`. L'écran ajoute une seule ligne quand ce nombre est positif : « Mail récent sur 2 tâches ou livrables de la semaine ». Le clic ouvre l'Accueil sur la source E-mails. Aucune relève supplémentaire : lecture de la table seule. Une lecture en échec ajoute `email` aux `indisponibles` de la route, et la ligne dit « Les mails rapprochés n'ont pas pu être lus ».

**Pastille « Mail récent ».** Sur la section Livrables de la fenêtre du projet (`components/memory/ProjectDeliverablesSection.tsx`, livrée par P-153), sur la liste des livrables (`components/crm/DeliverablesList.tsx`) et sur la carte d'une tâche. C'est une `Etiquette` avec son texte, jamais une couleur seule (constat 16). Elle apparaît tant qu'un rapprochement `nouveau` ou `vu` de moins de 90 jours vise la cible. Données : `GET /api/veille-courrier/pastilles?projet_id=` (lecture locale).

**Accessibilité** (constat 16). Boutons nommés d'après la cible (« Vu : Maquettes », « Pas lié à Maquettes », « Taire Refonte du site »). Le dépliage suit l'ordre de tabulation de la ligne. Un test vitest par rôle et par nom pour chaque action.

**Mode démo.** Expéditeurs, objets et noms de cibles passent par `maskText`, dans le brief, « Cette semaine », le dépliage et le titre prérempli d'un créneau.

### 5.7 Le créneau libre

**Déclenchement.** Au geste « Proposer un créneau », jamais en fond. Route `POST /api/veille-courrier/creneaux` avec la cible, la durée et le fuseau.

**Horizon.** Le plus proche entre l'échéance de la cible et le prochain rendez-vous avec ce contact (un événement dont les participants contiennent son adresse). Sans échéance ni rendez-vous, aucun créneau : une date inventée est pire qu'une date absente (`services/echeances.py:22-35`). La lecture s'arrête à 30 jours devant : au-delà, les créneaux les plus proches sont de toute façon trouvés avant. *Choix tranché ici (question 4 de la V1)* : couvrir les deux formulations du besoin, l'échéance et le rendez-vous.

**Lecture des agendas, au moment du geste** (constat 3 et correction de la V1).

- Agendas locaux : table `CalendarEvent`, récurrences **dépliées** sur la fenêtre (`dateutil.rrule.rrulestr` sur les lignes `RRULE`, `EXDATE` et `RDATE` stockées). `python-dateutil` devient une dépendance directe dans `pyproject.toml` (il est déjà dans le verrou, `uv.lock:2484`).
- Google : lecture par le fournisseur sur la fenêtre, occurrences déjà dépliées (`singleEvents`), ce qui rafraîchit au passage le cache.
- CalDAV : lecture par le fournisseur, dépliée (`expand=True`). La V1 supposait tout dans `CalendarEvent`, ce qui ignorait CalDAV.
- Un agenda illisible : **aucun créneau proposé**, et l'écran le nomme (« l'agenda Travail n'a pas pu être lu : aucun créneau proposé, pour ne pas t'en suggérer un déjà pris »), avec « Réessayer ». Un créneau calculé sans un agenda serait une affirmation fausse.
- Événements annulés ignorés ; « provisoires » tenus pour occupés ; journées entières tenues pour occupées.

**Heures et jours** (décision 5).

- Fuseau : celui du système, envoyé par l'écran (`Intl.DateTimeFormat().resolvedOptions().timeZone`) et validé côté serveur comme `_validate_timezone` (`routers/calendar.py:87-97`). Nom invalide ou absent : Europe/Paris, dit à l'écran.
- Les heures stockées sont converties d'abord en instants depuis leur convention (heure murale de Paris pour `CalendarEvent`, `local_provider.py:28-40` ; instant pour les DTO Google et CalDAV), puis comparées aux heures ouvrées du fuseau du système.
- Heures ouvrées : celles du planning, lundi à vendredi, 9 h à 12 h et 14 h à 18 h. *Choix tranché ici (question 5 de la V1)* : pas de réglage nouveau en V1, pour ne pas ajouter d'écran avant l'usage ; les intervalles viennent de `WorkCalendar` (`services/planning.py:171`) pour qu'une future préférence les change aux deux endroits.
- Jours fériés : une fonction pure nouvelle rend les onze jours fériés légaux de métropole (1er janvier, lundi de Pâques, 1er mai, 8 mai, Ascension, lundi de Pentecôte, 14 juillet, 15 août, 1er novembre, 11 novembre, 25 décembre), Pâques calculé. Aucune bibliothèque de fériés n'est dans l'environnement ; onze dates ne justifient pas d'en ajouter une. Le moteur PERT reste inchangé : y exclure les fériés changerait ses résultats et sa `ENGINE_VERSION` (`services/planning.py:20`), hors périmètre.
- Fin inclusive des journées entières (BUG-144).

**Résultat.**

- Durée d'une heure par défaut, modifiable dans la carte (30 min, 1 h, 2 h).
- Trois créneaux au plus, le plus tôt d'abord, **un par demi-journée au plus**. Motif : trois heures consécutives d'un même matin ne laissent pas de choix réel.
- Fraîcheur dite : « d'après tes agendas lus à 10 h 42 ».
- Aucun créneau avant l'horizon : « Aucun créneau d'une heure avant jeudi 18 h. » Jamais un créneau après l'échéance présenté comme une solution.

**Réservation.** « Réserver ce créneau » ouvre `NewEventForm` prérempli (titre « Traiter le mail de Mme Durand (Maquettes) », début, fin). Une propriété optionnelle de valeurs initiales est à ajouter au formulaire, qui n'en accepte aucune aujourd'hui (`MeetingConversationCard.tsx:212-229`). La création passe par son étape de confirmation existante (l.229) ; rien n'est créé sans le clic de l'utilisateur.

### 5.8 La relève de fond, facultative

- Désactivée par défaut, gouvernée par le seul interrupteur de Paramètres, rubrique Services (décision 2). Texte d'activation : « Thérèse lit les en-têtes de tes nouveaux mails toutes les 30 minutes, tant que l'application est ouverte. Rien n'est marqué lu, rien n'est envoyé, le contenu des mails n'est pas lu. » Poser la préférence vaut consentement, et le serveur peut la lire (ce qu'il ne peut pas faire du consentement cloud, `lib/consent.ts:44-67`).
- Planificateur calqué sur celui des notifications (`main.py:348-364`) : absent sous `THERESE_SKIP_SERVICES`, annulé et attendu à l'arrêt comme `notification_task` (`main.py:453-458`).
- Même chemin que la relève au geste, avec le même plafond et les mêmes états. Un compte `a_reconnecter` est sauté sans tentative.
- **Client de la mise au repos** : suspendu pendant une purge ou une restauration, repris à la sortie.
- Jetons OAuth rafraîchis en fond : un effet technique d'infrastructure, que `services/contexte_execution.py:22-25` sépare déjà des effets métier.
- La purge totale efface `preferences` entière (`routers/data.py:697`) : après « Effacer toutes mes données », la relève de fond est coupée. C'est voulu.

### 5.9 Ce qui ne part jamais sans confirmation

Automatique, et seulement cela : lire des en-têtes sans les marquer lus, calculer, écrire une proposition locale et l'état d'un compte.

Toujours au clic de l'utilisateur : répondre, créer un brouillon, transférer ; marquer lu ou non lu, étoiler, classer, déplacer, supprimer ; rattacher un mail à une fiche ; changer le statut ou l'échéance d'une tâche ou d'un livrable ; créer une relance ; réserver un créneau ; envoyer quoi que ce soit à un modèle en ligne.

Un test de garde vérifie que la relève n'appelle jamais `send_message`, `create_draft`, `update_draft`, `modify_message`, `move_message` ni `delete_message` (méthodes du fournisseur IMAP, `imap_smtp_provider.py:447`, `:604`, `:626`, `:668`, `:740`, `:704`).

### 5.10 Confidentialité et modèle

- **V1 sans modèle.** Les règles suffisent au cas du testeur et s'expliquent en une ligne. L'écran dit que Thérèse lit les en-têtes, pas le mail.
- **Phase 2, modèle local seulement** (constat 14 et question 6 de la V1). La V1 prenait `auto_extract_entities` pour exemple d'un traitement local ; c'était faux : l'extraction tourne sur le service de la conversation, en ligne compris (`routers/chat.py:970-975`, B-1139). La phase 2 exige un modèle Ollama installé qui ne soit pas un modèle « cloud » (`services/ollama_capabilites.py:86-90`), sans aucun repli en ligne (B-1071, `services/llm.py:832-840`). Rôle : départager plusieurs cibles et résumer « ce qui est demandé ». Le corps n'est lu que pour un mail déjà rapproché, et passe par `sanitize_for_context`. Réponse en JSON dont les identifiants doivent appartenir à la liste fournie.
- **En ligne : jamais en fond.** « Analyser dans le chat » ouvre une conversation, qui demande l'accord du fournisseur comme aujourd'hui.

### 5.11 Effacement et rétention

Une seule fonction de service oublie les rapprochements et les silences d'une fiche, d'un projet, d'une cible ou d'un compte. Elle est appelée depuis :

| Chemin | Lieu | Ce qui part |
|---|---|---|
| Purge totale | `routers/data.py:632-697` | les trois tables, avant `EmailMessage` et `EmailAccount` |
| Déconnexion d'un compte (constat 7) | `routers/email.py:758-766` | les trois tables pour ce compte |
| Anonymisation manuelle | `routers/rgpd.py:184` | rapprochements de la fiche ; silences dont la valeur est son adresse, lue **avant** l'effacement de l'identité |
| Anonymisation automatique | `services/rgpd_auto.py:199-208` | idem ; ce chemin n'efface aujourd'hui que l'identité et les mails, il faut donc l'y ajouter |
| Suppression d'une fiche | `routers/memory.py:1053` | idem |
| Suppression d'un projet | `routers/memory.py:361` (appelée par l'anonymisation et `:1389`) | rapprochements et silences du projet |
| Suppression d'une tâche | `routers/tasks.py:283`, `routers/actions.py:164` | rapprochements de la tâche |
| Suppression d'un livrable | `routers/crm.py:365-378` | rapprochements du livrable |

Aucun `PRAGMA foreign_keys` n'est posé (`models/database.py`), et la purge supprime table par table : chaque chemin est donc explicite et testé.

**Rétention** (décision 4, constat 11).

- Rapprochements `ecarte` : 90 jours après leur dernière mise à jour.
- Silences : `jusqu_au` jamais nul et jamais au-delà de 90 jours.
- Rapprochements `nouveau` et `vu` : 90 jours après la réception, par analogie avec la décision 4 (au-delà, l'alerte n'a plus d'objet).
- Rapprochements `confirme` : tant que la cible, la fiche et le compte existent. C'est un lien voulu par l'utilisateur, comme `EmailMessage.contact_id` aujourd'hui.
- L'expiration s'applique au démarrage, avant que le serveur accepte une requête (aucun conflit possible avec une purge), puis au début de chaque relève. Aucune boucle de fond de plus. Les lectures filtrent de toute façon les lignes expirées.

**Export** (constat 11). Les trois tables entrent dans l'export RGPD (`routers/data.py:172`), silences compris ; `data_format_version` passe de « 1.4 » à « 1.5 » (`routers/data.py:262`).

**Sauvegarde et restauration.** Rien à changer : l'archive porte la base entière (`routers/data.py:1076`). Une sauvegarde d'avant P-105 restaurée recrée les tables vides au `init_db` de réouverture (`routers/data.py:1442-1452`), et la relève repart de sa première fois.

## 6. Mise en œuvre, lot par lot

Chaque lot fait l'objet d'un commit, tests rouges d'abord, sabotage ciblé par fonction (jamais par chaîne globale) et revue adverse du diff. Le design de ce document passe par sa propre revue adverse avant le lot 1.

### Prérequis hors P-105

- **P0. Pièce « mise au repos »** (chantier du 25/09, validé). Bloque les lots 3 et 6, pas les lots 1, 2, 4 et 5.

### Lot 1 : le moteur de rapprochement

- **Moteur.** Module pur : normalisation d'adresse, index, règles 1 à 6, garde-fous, écartements par en-têtes puis classeur, clé de message, clé de fil (section 5.3). Retrait, dans un commit à part, de `services/email_contact_matcher.py`, sans appelant et sans le garde-fou d'ambiguïté : sa présence invite à réutiliser la mauvaise version.
- **Écran.** Rien.
- **Données.** Rien.
- **Tests à écrire en premier** (`tests/test_veille_courrier_rapprochement.py`, un test par règle, chacun saboté) :
  - expéditeur exact, casse et espaces ; deux fiches pour une adresse, aucun rapprochement ; fiche `archive`, aucun ;
  - projet `completed` ou `on_hold` ignoré ; tâche `done` ou `cancelled` ignorée ; livrable `valide` ignoré ;
  - projet à plusieurs cibles ouvertes : niveau probable, cible `projet`, trois candidates au plus, commencées en tête ;
  - « Réfection » trouve « refection » ; « Site » ne trouve pas « Situation » ; un nom de trois lettres ou un mot courant ne déclenche rien ;
  - `gmail.com` jamais utilisé comme domaine ; domaine de société : « à confirmer » ;
  - fil confirmé hérité (règle 1) ; fil écarté jamais reproposé pour la même cible, mais proposé pour une autre ; silence respecté, puis levé à sa date ;
  - **fil IMAP** : une réponse dont `References` cite un message écarté n'est pas reproposée ; une réponse qui n'a que `In-Reply-To` vers un message connu hérite de son fil ; deux conversations au même objet restent deux fils ;
  - mail de l'adresse du compte, `List-Id`, `List-Unsubscribe`, `Precedence: bulk`, `Auto-Submitted: auto-replied` écartés ; `Auto-Submitted: no` gardé ; newsletter reconnue par le classeur sans extrait.
- **Critères observables.** Sur les données de démonstration, le moteur rend les propositions attendues d'un jeu d'en-têtes témoin, identiques d'une exécution à l'autre.

### Lot 2 : les données

- **Moteur.** Fonction d'oubli (section 5.11), expiration des lignes (section 5.11).
- **Écran.** Rien.
- **Données.**
  - Trois modèles dans `models/entities.py`, créés par `create_all`.
  - Révision Alembic générée par `alembic revision`, `down_revision = "b8c9d0e1f2a3"`, qui crée les trois tables si elles manquent (même prudence que `b8c9d0e1f2a3`, qui teste l'existence avant d'ajouter).
  - `ALEMBIC_HEAD_REVISION` passe à cette nouvelle révision (`models/database.py:619`).
  - Preuve d'estampillage étendue : une fonction `tables_de_veille_courrier()` dérivée des modèles, sur le patron de `tables_de_planning()` (`models/database.py:632-640`), ajoutée à la conjonction de `models/database.py:747-757` avec la même exigence « toutes les colonnes ».
  - Export RGPD : trois blocs, `data_format_version` « 1.5 ».
  - Purge totale, déconnexion, anonymisations manuelle et automatique, suppressions de fiche, projet, tâche et livrable : appel de la fonction d'oubli.
- **Tests à écrire en premier.**
  - `tests/test_alembic_stamp.py` : la constante suit la vraie tête (test existant, l.139) ; « une base à `b8c9d0e1f2a3` sans les tables de veille n'est pas ré-estampillée » et « des tables de veille malformées ne passent pas la preuve », jumeaux de l.307 et l.330 ; `make db-migrate` sur une base neuve et sur une base ancienne.
  - Export : les trois clés présentes, version « 1.5 » (mise à jour de `tests/test_routers_data.py:152`).
  - Purge totale : zéro ligne dans les trois tables après le 200.
  - Déconnexion d'un compte : ses lignes partent, celles d'un autre compte restent.
  - Anonymisation manuelle, puis automatique : rapprochements de la fiche et silences à son adresse effacés ; un silence sur une autre adresse reste.
  - Suppression d'une tâche, d'un livrable, d'un projet, d'une fiche : lignes correspondantes effacées.
  - Expiration : un écarté de 91 jours disparaît au démarrage, un de 89 jours reste ; un `confirme` ancien reste.
  - Restauration d'une sauvegarde d'avant P-105 : tables présentes et vides après réouverture.
- **Critères observables.** Une base 0.75 mise à jour démarre, s'estampille à la nouvelle tête, et `make db-migrate` n'échoue pas.

### Lot 3 : la relève au geste (après P0)

- **Moteur.**
  - Méthode de lecture d'en-têtes du fournisseur IMAP (section 5.5), distincte de `list_messages`, sous `_run_imap_operation` et ses délais.
  - Lecture Gmail postérieure au filigrane.
  - Recherche d'un message par `Message-ID` chez le fournisseur (IMAP : recherche sur l'en-tête dans la boîte de réception ; Gmail : `rfc822msgid:`), et route de résolution que le bouton « Ouvrir le mail » appellera. L'écran ne sait aujourd'hui ouvrir un mail que par l'identifiant du fournisseur (`services/api/email.ts:294-295`).
  - Route `POST /api/veille-courrier/relever`, garde de deux minutes, états de compte, plafond et compteur, client de la mise au repos.
  - La liste de l'écran E-mail n'est pas modifiée : elle continue de lire les corps pour ses extraits. Passer la liste en en-têtes seuls est un sujet distinct, hors P-105.
- **Écran.** Appel de la relève à l'ouverture de l'écran E-mail, sans bloquer la liste.
- **Données.** Écriture des propositions et de `releves_courrier`.
- **Tests à écrire en premier** (`tests/test_veille_courrier_releve.py`, fournisseurs doublés) :
  - zéro appel aux méthodes d'écriture du fournisseur (espions, section 5.9) ;
  - IMAP appelé avec `headers_only=True` et `mark_seen=False`, boîte de réception seule ; Gmail en `metadata` ;
  - plafond de 50, du plus ancien au plus récent ; `non_examines` exact ; le filigrane n'avance qu'après écriture ; une deuxième relève reprend où la première s'est arrêtée ;
  - UID inférieur ou égal au filigrane rendu par le serveur : filtré ;
  - UIDVALIDITY changée : filigrane remis à zéro, aucun doublon ;
  - **deux comptes IMAP, même UID** : deux lignes distinctes, chacune avec son expéditeur et son objet ;
  - **message déplacé** : « Ouvrir le mail » le retrouve par `Message-ID` ;
  - jeton non rafraîchissable : `a_reconnecter` posé une fois, aucune nouvelle tentative au geste suivant ; reconnexion : état remis à `jamais` ;
  - serveur injoignable : `illisible`, aucune exception à l'écran ;
  - deuxième appel sous deux minutes sans `forcer` : aucune connexion ;
  - pendant une purge : 503 « relève suspendue », aucune ligne écrite après le 200 de la purge.
- **Critères observables.** Sur un compte de démonstration doublé, ouvrir l'écran E-mail fait apparaître des lignes dans `rapprochements_courrier`, et le client de messagerie montre toujours les nouveaux mails comme non lus.

### Lot 4 : ce que l'utilisateur voit

- **Moteur.** Bloc `courrier` de `/api/dashboard/today` et champ `courrier` de `/api/dashboard/semaine`, lecture locale seule ; routes des actions (`PATCH` d'un rapprochement, création et levée d'un silence) et des pastilles.
- **Écran.**
  - Sixième entrée de `SOURCES_DU_BRIEF` (clé `email`, nom « E-mails ») et type `TodayDashboard` étendu (`services/api/dashboard.ts:85`).
  - Lignes groupées, dépliage, « Ouvrir le mail » (par la route de résolution du lot 3), « Vu », « Oui, c'est lié », « Pas lié », « Taire », « Relever », « Relever la suite », fraîcheur et états de compte.
  - Ligne unique dans `CetteSemaine.tsx`, avec une branche de clic nouvelle (l.94-97).
  - Liste des silences actifs, chacun avec « Réactiver », dans Paramètres, rubrique Services.
  - Pastille « Mail récent » sur la fenêtre du projet, la liste des livrables et la carte d'une tâche.
  - Masque démo partout ; ajout des deux libellés à la table du lexique (`docs/rules/RULES-DESIGN.md`, section 13) et à `lib/lexique.test.ts`.
- **Données.** Écriture des statuts et des silences.
- **Tests à écrire en premier** (vitest, puis pytest pour les routes) :
  - le rafraîchissement du brief (intervalle, focus, visibilité) n'appelle jamais `/api/veille-courrier/relever` ;
  - source indisponible (`email` dans `indisponibles`) : phrase dédiée, jamais « rien » ; compte jamais relevé : phrase dédiée ; compte à reconnecter nommé ;
  - cinq lignes au plus, le reste dans le compteur ; « N mails pas encore examinés » ;
  - un bouton par action, trouvé par son rôle et son nom (« Pas lié à Maquettes ») ; dépliage avec `aria-expanded` ; pastille lisible par son texte ;
  - « Oui, c'est lié » sur une cible `projet` demande laquelle ; « Pas lié » retire la ligne ;
  - « Taire » pose un silence d'au plus 90 jours ; « Réactiver » dans Paramètres le lève et les propositions suivantes reviennent ;
  - masque démo sur expéditeur, objet et cible ;
  - « Cette semaine » : une seule ligne, absente à zéro, phrase dédiée en cas d'échec de lecture ;
  - `lexiqueTitres.test.ts` et `lexique.test.ts` verts avec les nouveaux libellés ;
  - route `/today` : aucun appel réseau (fournisseurs doublés qui échouent si on les appelle).
- **Critères observables.** Bout en bout (Playwright, serveur jetable 17393) : un compte doublé reçoit le mail d'un contact de projet ; le brief affiche la ligne, son motif et sa fraîcheur ; « Pas lié » la retire, et une réponse dans le même fil ne la ramène pas.

### Lot 5 : le créneau libre

- **Moteur.** Fonction pure `creneaux_libres` (occupations, fenêtre, durée, heures ouvrées, fériés, fuseau) ; fonction pure des jours fériés ; dépliage des récurrences locales ; lecture des agendas au geste ; route `POST /api/veille-courrier/creneaux`. `python-dateutil` déclaré dans `pyproject.toml`.
- **Écran.** Carte des créneaux dans le dépliage ; valeurs initiales de `NewEventForm` ; « Réserver ce créneau » ouvre le formulaire prérempli.
- **Données.** Rien de nouveau (le cache Google se rafraîchit comme aujourd'hui).
- **Tests à écrire en premier** (`tests/test_creneaux.py`, puis vitest) :
  - semaine type ; week-end ; journée entière bloquante ; événement de plusieurs jours à fin inclusive ; événement annulé ignoré ; provisoire bloquant ;
  - **réunion hebdomadaire locale** : chaque occurrence de la fenêtre bloque, pas seulement la première ; une `EXDATE` libère son jour ;
  - 11/11/2026 et 25/12/2026 exclus (tous deux en semaine) ; lundi de Pâques 2027 (29/03/2027) et Ascension 2027 (06/05/2027) exclus ;
  - heure murale de Paris convertie : un rendez-vous local à 10 h (Paris) bloque 5 h pour un système en `America/Martinique` (UTC-4 ; Paris en UTC+1 le 1er décembre) ;
  - fuseau invalide : repli sur Europe/Paris, signalé ;
  - passage à l'heure d'hiver du 25/10/2026 ;
  - échéance passée ou absente : aucun créneau ; horizon ramené au prochain rendez-vous du contact ;
  - un créneau par demi-journée au plus ; aucun après l'horizon ; phrase dédiée si aucun ;
  - un agenda CalDAV doublé en échec : aucun créneau, agenda nommé ;
  - « Réserver ce créneau » ouvre le formulaire prérempli sans rien créer.
- **Critères observables.** Sur les données de démonstration, trois créneaux proposés avant l'échéance d'un livrable, aucun sur un jour férié ni sur une occurrence d'une réunion récurrente.

### Lot 6 : la relève de fond, facultative (après P0 et le lot 3)

- **Moteur.** Planificateur, suspension par la mise au repos, arrêt propre.
- **Écran.** Interrupteur dans Paramètres, rubrique Services (à côté de la liste des silences du lot 4), texte d'activation, liste des comptes concernés.
- **Données.** Préférence `veille_courrier`.
- **Tests à écrire en premier.** Planificateur absent sous `THERESE_SKIP_SERVICES` ; préférence absente ou `active: false` : aucune relève de fond, relève au geste intacte ; suspendu pendant une purge, aucune ligne après le 200 ; annulé à l'arrêt ; compte `a_reconnecter` sauté ; après la purge totale, la préférence a disparu et plus rien ne tourne.
- **Critères observables.** Activée, la relève tourne toutes les 30 minutes tant que l'application est ouverte ; désactivée, le journal ne montre plus aucune relève de fond.

### Lot 7 : recette réelle

Sur les données de démonstration, puis sur un compte Gmail et un compte IMAP réels : après relève, le client de messagerie montre toujours les nouveaux mails comme non lus ; une réponse IMAP dans un fil écarté n'est pas reproposée ; un créneau n'est jamais posé sur une réunion récurrente locale.

### Phase 2, après usage réel

Modèle local non « cloud » pour départager et résumer, derrière une préférence serveur ; test « modèle `:cloud` refusé » et « Ollama arrêté : étape sautée, aucun repli ».

## 7. Réponse à la revue

### Constats

| # | Gravité | Constat | Réponse | Où, dans la V2 |
|---|---|---|---|---|
| 1 | P2 | Règle 1 et « Pas lié » inopérants sur IMAP, faute de fil | Accepté. Décision 3 : fil reconstitué par `References`, `In-Reply-To` et ancêtres connus ; aucun regroupement par objet. Le DTO a déjà le champ `thread_id` (`services/email/base_provider.py:31`), mais la relève ne s'en sert pas : elle calcule sa propre clé de fil | 5.3 ; lot 1 (tests fil IMAP) ; lot 4 (bout en bout) |
| 2 | P2 | Cache `EmailMessage` indexé sur l'UID seul | Accepté. La relève n'écrit plus jamais ce cache ; la table porte expéditeur, objet et `Message-ID`. Clé composite écartée (reconstruction de table et clé étrangère `email_follow_ups.email_message_id`, `models/entities.py:938`) | 5.3, 5.4 ; lot 3 (deux comptes, même UID ; message déplacé) |
| 3 | P2 | Récurrences locales ignorées | Accepté, et élargi : CalDAV n'était pas couvert non plus (pas de cache, `routers/calendar.py:812-889`). Agendas lus au geste, RRULE locales dépliées par `dateutil`, déclaré en dépendance directe | 5.7 ; lot 5 (réunion hebdomadaire locale, `EXDATE`) |
| 4 | P2 | Ce que lit la sixième source du brief | Accepté. Lecture de la base locale seule, fraîcheur dite, jamais de relève au rafraîchissement | 5.6 ; lot 4 (test du rafraîchissement) |
| 5 | P3 | Préalable IMAP périmé | Accepté. B-1409 est livré (`imap_smtp_provider.py:355-359`) ; il reste `headers_only`, porté par une méthode de relève distincte | 4.1, 5.5 ; lot 3 |
| 6 | P3 | Étapes Alembic absentes du lot 2 | Accepté. La constante est désormais `b8c9d0e1f2a3` à `models/database.py:619` (la revue citait `a7b8c9d0e1f2` à la l.617, antérieure à P-139) ; révision, constante, preuve dérivée des modèles, purge et test de base partiellement patchée sont inscrits | 5.4 ; lot 2 |
| 7 | P3 | Déconnexion d'un compte oubliée | Accepté | 5.11 ; lot 2 |
| 8 | P3 | Plafond de 50 et filigrane mal articulés | Accepté. Filigrane par UID (IMAP) ou date (Gmail), traitement du plus ancien au plus récent, compteur `non_examines` et « Relever la suite » | 5.5 ; lot 3 |
| 9 | P3 | Aucun support pour « à reconnecter » | Accepté. Table `releves_courrier` plutôt qu'une colonne, parce que `create_all` n'ajoute aucune colonne (`models/database.py:320-324`) | 5.4, 5.5 ; lots 2 et 3 |
| 10 | P3 | Interrupteur et relève au geste contradictoires | Tranché par la décision 2 : l'interrupteur ne gouverne que la relève de fond | 3, 5.8 ; lot 6 |
| 11 | P3 | Silences et écartés sans limite, hors anonymisation | Accepté. Décision 4 : 90 jours ; silences par adresse effacés à l'anonymisation (adresse lue avant l'effacement de l'identité), silences dans l'export | 5.11 ; lot 2 |
| 12 | P3 | « Oui, c'est lié » absent des actions et des tests | Accepté. Action, statut `confirme`, choix de la cible pour les règles 4 et 6, tests | 5.6 ; lot 4 |
| 13 | P3 | Fuseau de Paris, pas de jours fériés | Tranché par la décision 5 : fuseau du système, onze fériés légaux exclus | 5.7 ; lot 5 |
| 14 | P3 | « Modèle local seulement » ne tient pas (`:cloud`) | Accepté, et la référence de la V1 est corrigée : `auto_extract_entities` tourne sur le service de la conversation (`routers/chat.py:970-975`). Refus des modèles « cloud » | 5.10 ; phase 2 |
| 15 | P3 | Filtre des newsletters aveugle sans extrait | Accepté. En-têtes de masse d'abord, classeur ensuite | 5.2 ; lot 1 |
| 16 | P3 | Aucune exigence d'accessibilité | Accepté. Pastille textuelle, boutons nommés d'après la cible, dépliage `aria-expanded`, tests par rôle et par nom | 5.6 ; lot 4 |

### Questions de la revue

| Question | Réponse | Où |
|---|---|---|
| Valider le chantier « mise au repos » ? | Décision 1 : validé. Sa livraison est le prérequis P0 des lots 3 et 6 | 3, 5.5 ; section 6 |
| L'interrupteur coupe-t-il le rapprochement au geste ? | Décision 2 : non | 3, 5.8 |
| IMAP : « Pas lié » pour un message ou pour le fil ? | Décision 3 : pour le fil, reconstitué avant livraison | 5.3 |
| Durée de conservation des écartés et des silences ? | Décision 4 : 90 jours, effacés avec la fiche à l'anonymisation | 5.11 |
| Fuseau hors métropole, jours fériés ? | Décision 5 : fuseau du système, fériés français exclus | 5.7 |
| Une ligne dans « Cette semaine » ? | Décision 6 : oui, une ligne, sans relève | 5.6 |

## 8. Corrections de la V1 trouvées en relisant le code

- **Les dates naïves de l'agenda ne sont pas de l'UTC.** La V1 voulait les « ramener en UTC (BUG-126) ». `CalendarEvent.start_datetime` est une heure murale de Paris (`services/calendar/local_provider.py:28-40`, `routers/calendar.py:123-133`) ; la ramener en UTC aurait décalé chaque créneau d'une ou deux heures. `_as_aware_utc` de `services/notification_service.py:25-32` vaut pour d'autres colonnes, pas pour celle-ci.
- **CalDAV n'est pas dans le cache.** La V1 calculait les créneaux « sur le cache `CalendarEvent` (tous les agendas) ». Un agenda CalDAV n'y est jamais écrit (`routers/calendar.py:812-889`).
- **« Travail » est un mot réservé à l'écran** (section 5.1).
- **`get_crm_contact_by_email` n'exclut pas les fiches archivées** (`routers/email.py:192-214`) : l'index du moteur les exclut lui-même, plutôt que de réutiliser cette fonction.
- **L'anonymisation automatique ne suit pas le même chemin que la manuelle** (`services/rgpd_auto.py:199-208` contre `routers/rgpd.py:245-281`) : la fonction d'oubli doit être appelée aux deux endroits.
- Lignes décalées depuis la V1 : `EmailFollowUp` est à `models/entities.py:932` ; toutes les références de ce document ont été relues au commit `900765fb`. `src/frontend/src-tauri/Cargo.toml:18-31` ne déclare toujours aucun greffon de notification : la V2 n'en demande pas.

## 9. Risques restants

- **Dépendance au chantier « mise au repos ».** Tant qu'il n'est pas livré, les lots 3 et 6 attendent, et avec eux toute alerte réelle. Les lots 1, 2, 4 et 5 avancent sans lui, mais le lot 4 n'aura que des données de démonstration.
- **Fatigue d'alerte.** Parades : une ligne par cible, cinq lignes au plus, « Pas lié » sur tout le fil, « Taire », pas de modèle en V1. Aucun interrupteur ne coupe le rapprochement au geste (décision 2) : si l'usage montre qu'il en faut un, il se posera après la recette.
- **Faux négatifs.** Un client qui écrit d'une adresse inconnue, ou dont l'outil d'envoi ajoute `List-Unsubscribe` à un mail personnel, passe inaperçu. L'écran dit que le rapprochement repose sur les adresses connues.
- **Fils IMAP imparfaits.** Un client de messagerie qui ne pose ni `References` ni `In-Reply-To` casse le fil ; « Pas lié » ne vaut alors que pour ce message. Aucun regroupement par objet n'est tenté, par choix.
- **Rétention.** Un fil écarté peut revenir après 90 jours ; c'est le prix de la décision 4.
- **Jours fériés.** Métropole seulement : Alsace-Moselle (Vendredi saint, 26 décembre) et outre-mer (abolition de l'esclavage) ne sont pas exclus. Un utilisateur de Martinique aura le bon fuseau, pas ses fériés locaux.
- **Agendas lus au geste.** Plus lent qu'une lecture de cache sur une machine modeste ou un serveur CalDAV lent ; un agenda illisible bloque toute proposition, par prudence.
- **Charge.** Quotas Gmail, serveurs IMAP lents : plafond de 50, délais bornés de `_run_imap_operation`, garde de deux minutes.
- **Sentiment de surveillance.** Parades : relève de fond désactivée par défaut, texte d'activation explicite, en-têtes seulement, fraîcheur toujours affichée.
- **Recouvrement avec P-104.** Quand le fil de travail existera, la définition de « ouvert » devra le suivre ; elle est un paramètre du moteur.

## 10. Questions réservées à Ludo

Aucune. Rien dans cette RFC n'efface de données de l'utilisateur au-delà de ce que la décision 4 a fixé (les lignes que P-105 crée elle-même), n'annonce rien publiquement et ne touche à la marque.

Hors périmètre : la table `notifications`, alimentée chaque heure sans surface depuis le retrait de la cloche (commits `628d672f` et `31ec0a3f`), n'est ni lue ni modifiée par P-105. Si quelqu'un propose un jour de la retirer, cela effacerait des lignes sur la machine des utilisateurs : la question ira alors à Ludo, dans son propre ticket.
