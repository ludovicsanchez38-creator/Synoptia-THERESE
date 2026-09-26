# RFC P-105 (V4) : alerte quand un mail touche une tâche ou un livrable, et un créneau pour le traiter

Rédigé le 26/09/2026. Remplace la V3 (`docs/plans/2026-09-26-rfc-p105-alerte-mail-tache-v3.md`), refusée (NO-GO) par la revue adverse du 26/09 (constats 1 à 13 ; rapport de travail « revue-v3-p105-p106.md » de l'orchestrateur, hors dépôt). Les décisions du 25/09/2026 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, points 1 à 6 de P-105) restent des faits. Les réponses aux revues de la V1 (V2, section 7) et de la V2 (V3, section 0) restent valables ; la section 0 bis ci-dessous dit seulement où en est chacune au code.

**Base de vérification.** Toutes les lignes citées ont été relues à `2d49d8d5` (HEAD du 26/09/2026 au début de la rédaction), avec `git show 2d49d8d5:<fichier>`, jamais dans l'arbre de travail, où l'orchestrateur corrige en parallèle. Cinq commits sont arrivés pendant la rédaction (`62639261` à `06607577` : B-1506, B-1522, B-1523, B-1524 et un réglage de CI). Seuls B-1522 à B-1524 touchent un fichier cité, `routers/data.py`, après sa ligne 1257 : à `06607577`, la réouverture de la base citée en 6.11 est à `:1512-1523` (`init_db` à `:1520`) ; toutes les autres lignes citées de ce fichier sont inchangées. Depuis la base de la V3 (`6f927313`), B-1500, B-1503, B-1504, B-1505, B-1507 et B-1516 ont déplacé des lignes de `services/workspace_tools.py`, `routers/memory.py`, `routers/data.py` et `main.py` : toutes les citations ont été rebasées. Chemins relatifs à `src/backend/app/` (fichiers `.py`) et à `src/frontend/src/` (fichiers `.ts` et `.tsx`) ; les tests, `docs/`, `uv.lock` et `pyproject.toml` partent de la racine du dépôt. Les lignes de `imap_tools` et `dateutil` ont été relues dans l'environnement installé (`.venv`, imap_tools 1.11.1, python-dateutil 2.9.0.post0), qui n'est pas versionné. `tests/test_veille_courrier_rapprochement.py`, `tests/test_veille_courrier_releve.py` et `tests/test_creneaux.py` sont à créer ; aucune autre citation ne vise un fichier absent. Vérification mécanique : chaque citation a été imprimée à la base par un script et relue (209 citations).

Aucun code avant la validation de ce document.

## 0. Constats de la revue V3 et leur traitement

« Fermé au code » veut dire : un commit est sur main et un test nommé le prouve à la base relue. « Design, lot N » veut dire : la réponse est écrite ici, et son test est à écrire en premier au lot N ; elle n'est pas vérifiable au code avant.

| # | Grav. | Constat de la revue V3 | Traitement | État | Où |
|---|---|---|---|---|---|
| 1 | P2 | `a_reconnecter` posé sur « le 400 », qui couvre aussi 429, 408, redirection ; une réponse illisible sort en 401 | **Accepté.** Relu : `services/oauth.py:337-343` lève 400 pour toute réponse ni 200 ni 5xx ; un corps HTML fait lever `response.json()` hors du seul `except httpx.HTTPError` (`:354`), et le client suit les redirections (`services/http_client.py:59`), si bien qu'un portail captif rend une page en 200 dont la lecture lève aussi ; l'exception sort en 401 générique (`routers/email.py:319-324`). La relève ne classe plus sur les codes : `a_reconnecter` seulement sur un refus **typé** (corps JSON `error` parmi `invalid_grant`, `invalid_client`, `unauthorized_client`) ou sur des identifiants OAuth absents, eux aussi typés ; tout le reste est `illisible`. Tests en doublure HTTP, comme `tests/test_b1488_jeton_mail_panne_passagere.py`. Le même classement touche déjà l'écran E-mail : candidat A-3 (section 2) | design, lot 5 | 6.5 ; lot 5 |
| 2 | P2 | Les séries en journée entière ne sont ni lues ni dépliées | **Accepté.** Relu : l'import garde la RRULE quel que soit `all_day` (`services/import_service.py:78-82`) et range la série sur `start_date` (`routers/calendar.py:1971`, `:1974-1976`). La requête des séries porte désormais sur `start_datetime` **ou** `start_date` ; une série en journée entière se déplie en dates civiles. Mesuré dans l'environnement : un début naïf à minuit avec `UNTIL=20261012` se déplie ; `UNTIL=20261012T215959Z` lève `ValueError` ; la normalisation couvre ce cas | design, lot 4 | 6.7 ; lot 4 |
| 3 | P2 | A-1 livré pour l'heure datée seulement ; l'heure naïve du modèle reste prise pour Paris, fausse hors de Paris | **Accepté.** B-1500 (`ce5bc57f`) ramène à Paris une heure datée (`services/workspace_tools.py:1677-1686`) et garde une heure naïve telle quelle, par dessein (`tests/test_b1500_outil_agenda_heure_de_paris.py`, `test_une_heure_sans_fuseau_reste_celle_de_paris`) ; `ChatRequest` ne porte aucun fuseau (`models/schemas.py:105-119`) et le modèle reçoit l'heure en UTC (`services/llm.py:526-529`). Ouvert comme prérequis distinct **A-2**, qui ne relève pas de C-1 (il touche les écritures à venir, pas les anciennes). La phrase « trois prérequis rendent la convention vraie » est retirée | A-1 heure datée : fermé au code (`ce5bc57f`, `tests/test_b1500_outil_agenda_heure_de_paris.py`) ; A-2 : à corriger hors RFC, test au lot 4 | 1 ; 2 ; lot 4 |
| 4 | P2 | L'effacement par cascade repose sur un invariant `projet_id` vrai seulement à l'écriture ; une tâche change de projet | **Accepté, et plus large que la revue.** Relu : une tâche change de projet par `routers/tasks.py:252-253`, et **un livrable aussi**, bien que `Deliverable.project_id` soit obligatoire (`models/entities.py:885`) : l'import CRM (`services/crm_import.py:1214`), la synchronisation du tableur (`services/crm_sync.py:278`) et la mise à jour d'un livrable par ligne importée (`services/crm_utils.py:714`) le réaffectent. La V4 retire la colonne `projet_id` des rapprochements : le projet d'une cible se lit par jointure, au moment de la lecture. La cascade passe les identifiants réellement supprimés, que `_nettoyer_et_supprimer_projet` tient déjà (`routers/memory.py:457-464`), avant `session.delete(project)` (`:466`) | design, lot 2 | 6.4 ; 6.11 ; lot 2 |
| 5 | P3 | L'ancre vise un « groupe de la source » qui n'existe pas ; les lignes peuvent être derrière le repli | **Accepté.** Relu : liste plate tronquée au seuil (`components/prototype/TodayDashboardCard.tsx:144`, `:302`, repli `:326-336`), une seule liste (`components/prototype/prototypeReadModels.ts:180-205`), et `Ligne` ne porte ni `id` ni second interactif (`components/ui/Ligne.tsx:8`, `:26-45`). L'ancre vit sur la première ligne courrier, rendue par un composant dédié ; le clic de « Cette semaine » lève le repli avant de défiler, par une propriété de l'Accueil | design, lot 3 | 6.6 ; lot 3 |
| 6 | P3 | « Aucune écriture en base » faux pour Gmail : lire renouvelle le jeton et le commite | **Accepté.** `routers/email.py:304`, `:312` ; la classification des outils le dit déjà (`services/contexte_execution.py:22-25`). Formulation corrigée : aucune écriture métier, seul le jeton renouvelé, comme l'écran E-mail. Le motif « ne dépend pas de P0 » tient : c'est le régime de l'écran E-mail, qui n'est pas client de P0 non plus | design, lot 3 | 6.6 ; lot 3 |
| 7 | P3 | Première relève : le reste de la fenêtre est sauté, et on ne sait pas s'il est compté | **Accepté, tranché.** Le reste de la fenêtre de 14 jours n'est ni examiné ni compté ; `non_examines` ne compte que les messages au-dessus du filigrane. Le brief dit « rapprochement commencé le 26/09 avec tes 50 mails les plus récents ». L'alternative (filigrane bas, « Relever la suite » qui remonte) est écartée, motif en 6.5 | design, lot 5 | 6.5 ; lot 5 |
| 8 | P3 | La branche « occupé sur toutes les lectures » suppose un critère qui n'existe pas | **Accepté, branche retirée.** Aucun critère à la base relue : `synced_at` est réécrit par toute modification locale, même d'un seul titre (`services/calendar/local_provider.py:364`), et aucune date d'installation n'est enregistrée (`config.py:25` ne porte que la version en cours). Appliquée à toutes les lignes, la branche bloquerait deux ou trois créneaux par rendez-vous pour toujours, sans pouvoir énumérer les fuseaux d'origine des ICS importés. Seule reste la phrase de réserve ; le critère éventuel appartient au ticket C-1 | design, lot 4 | 2 ; 8 |
| 9 | P3 | Rien n'empêche le lot 4 d'être visible avant C-1 | **Accepté.** Seconde garde `CRENEAU_LIVRE = False`, testée comme la première : tant qu'elle est fausse, la route des créneaux répond 404 et le bouton n'est pas rendu | design, lots 3 et 4 | 6.6 ; 6.7 ; lot 4 |
| 10 | P3 | `lib/etabli.ts:27` ne nomme pas la source « E-mails » | **Accepté.** Ancre retirée : le libellé « E-mails » est neuf ; il entre au lexique au lot 3 | fermé au document | 6.1 |
| 11 | P3 | `tests/test_variables.py:213` passe à vide | **Accepté.** Seul `tests/test_routers_data.py:152` est cité | design, lot 2 | lot 2 |
| 12 | P3 | Citations décalées | **Accepté, et rebasé plus loin que la revue** : ses propres numéros étaient déjà dépassés à `2d49d8d5` (`delete_contact` est à `routers/memory.py:1079`, ses appels de la cascade à `:1138` et `:1436` ; la réouverture de la base à `routers/data.py:1505-1516`, `init_db` à `:1513`) | fermé au document | partout |
| 13 | P3 | La table ne distingue pas le code du design | **Accepté.** Colonne « État » ci-dessus et en 0 bis | fermé au document | 0 ; 0 bis |

## 0 bis. Constats de la revue V2 : où en est chacun au code

| # | Constat de la revue V2 | État à `2d49d8d5` |
|---|---|---|
| 1 | Heure murale de Paris non tenue par les écritures | **Fermé au code** pour l'écran (B-1487, `30aa8b33`, `tests/test_b1487_evenement_local_fuseau_du_poste.py`), l'import ICS (B-1486, `66b78788`, `tests/test_b1486_import_ics_heure_de_paris.py`) et l'heure datée de l'outil du chat (B-1500, `ce5bc57f`, `tests/test_b1500_outil_agenda_heure_de_paris.py`). **Ouvert** pour l'heure naïve de l'outil hors de Paris (A-2) et pour les lignes anciennes (C-1). Test du créneau par les vraies écritures : lot 4 |
| 2 | Dépliage des récurrences | Design, lot 4 (complété pour les journées entières, constat 2 ci-dessus) |
| 3 | CalDAV partiel, STATUS et TRANSP | Design, lot 4 |
| 4 | Coupure réseau lue comme un refus | **Fermé au code** côté client OAuth pour le transport et les 5xx (B-1488, `2c8a4489`, `tests/test_b1488_jeton_mail_panne_passagere.py`). Classement de la relève : design, lot 5 (refait, constat 1 ci-dessus) |
| 5 | UIDVALIDITY changée | Design, lot 5 (précisé, constat 7) |
| 6 | Déduplication et concurrence | Design, lot 5 |
| 7 | Lots et dépendance à P0 | Design ; garde de livraison testée au lot 3, seconde garde au lot 4 (constat 9) |
| 8 | Anonymisation par adresse, export de la fiche | Design, lot 2 |
| 9 | `routers/actions.py:164` ne supprime rien | Fermé au document (chemin retiré) |
| 10 | Base témoin de l'estampillage | Design, lot 2 |
| 11 | Date IMAP écrite par l'expéditeur | Design, lots 2 et 5 |
| 12 | Garde en liste blanche | Design, lot 5 |
| 13 | Règle de l'échéance | Design, lot 4 |
| 14 | Remise à `jamais` à la reconnexion | Design, lot 5 |
| 15 | `Message-ID` dupliqué ou absent | Design, lot 1 |
| 16 | « Cette semaine » et ancre | Design, lot 3 (refait, constat 5) |
| 17 | Cache Google | Design, lot 4 |

## 1. Ce que la V4 change

- Le créneau ne suppose plus que chaque ligne de l'agenda est en heure de Paris. B-1486, B-1487 et B-1500 tiennent la convention pour l'écran, l'import et l'heure datée du chat ; A-2 reste à corriger pour l'heure naïve du chat hors de Paris ; C-1 traite les lignes déjà en base. Le lot 4 n'est visible qu'après A-2 et C-1, par une garde testée.
- Les séries en journée entière sont lues et dépliées.
- La relève ne déduit plus un refus d'un code HTTP : elle attend un refus typé, et range tout le reste en « illisible », retenté au geste suivant.
- Les rapprochements ne portent plus de `projet_id` : une tâche qui change de projet emporte ses rapprochements, et la suppression d'un projet efface ceux des tâches et livrables qu'elle supprime réellement.
- L'ancre du brief est posée sur une vraie ligne, et le clic lève le repli.
- La première relève dit ce qu'elle a examiné, sans compteur qu'aucun geste ne ferait baisser.

## 2. Prérequis

| Nom | Nature | État à la base relue | Bloque |
|---|---|---|---|
| **P0** | Pièce « mise au repos » du chantier du 25/09 (`docs/plans/2026-09-25-chantier-mise-au-repos-ecritures-de-fond.md`), validée par la décision 1 | Non livrée : aucun symbole `mise_au_repos` dans `src/backend/app/` ; la purge n'attend encore que trois familles de travaux nommées une par une (`routers/data.py:602-629`) | lots 5 et 6 |
| **B-1486** | L'import ICS rangeait l'heure Z comme heure de Paris | **Fermé au code** (`66b78788`, `tests/test_b1486_import_ics_heure_de_paris.py`) : un instant daté est ramené à Paris avant stockage (`services/import_service.py:56-65`). Les lignes déjà importées gardent leur décalage | lot 4 |
| **B-1487** | La création et la modification d'un événement local ignoraient le fuseau de l'écran | **Fermé au code** (`30aa8b33`, `tests/test_b1487_evenement_local_fuseau_du_poste.py`) : l'heure saisie et le fuseau du poste (`components/calendar/EventForm.tsx:276-280`, `components/prototype/MeetingConversationCard.tsx:270`) sont ramenés en heure de Paris (`routers/calendar.py:100-110`) à la création (`:1194-1195`) comme à la modification (`:1366`, `:1372`) ; une heure de Paris rendue à l'écran porte son fuseau (`routers/calendar.py:113-120`) | lot 4 |
| **B-1488** | Une coupure réseau au renouvellement du jeton demandait de reconnecter le compte | **Fermé au code** (`2c8a4489`, `tests/test_b1488_jeton_mail_panne_passagere.py`) : transport et 5xx en 503 (`services/oauth.py:331-335`, `:354-357`) | lecture Google du lot 4 ; lot 5 |
| **A-1** | L'outil agenda du chat rangeait une heure datée sans la ramener à Paris | **Fermé au code** (B-1500, `ce5bc57f`, `tests/test_b1500_outil_agenda_heure_de_paris.py`) : `services/workspace_tools.py:1677-1686` | lot 4 |
| **A-2** (nouveau, à corriger hors RFC) | L'outil agenda du chat prend une heure naïve du modèle pour l'heure de Paris, fausse sur un poste hors de Paris | Preuves ci-dessous | **visibilité** du lot 4 (garde `CRENEAU_LIVRE`) |
| **A-3** (nouveau, candidat à reproduire, hors RFC) | L'écran E-mail demande de reconnecter un compte sain quand le point de jeton répond 429, 408 ou une page HTML | Preuves ci-dessous | rien dans P-105 : la relève ne lit pas ces codes (6.5) |
| **C-1** (candidat, à trancher) | Conversion unique des anciennes lignes hors Paris | Aucune migration posée ; décision à écrire dans son propre ticket | **visibilité** du lot 4 (garde `CRENEAU_LIVRE`) |

**A-2, preuves et forme recommandée.** L'outil ne convertit que l'heure datée (`services/workspace_tools.py:1683-1686`) ; une heure sans fuseau est rangée telle quelle, prise pour l'heure de Paris, et `CreateEventRequest` reçoit `timezone=args.get("timezone") or "Europe/Paris"` (`:1705`) alors que le schéma de l'outil n'offre aucun fuseau. `ChatRequest` ne transmet pas le fuseau du poste (`models/schemas.py:105-119`), et l'heure donnée au modèle est en UTC (`services/llm.py:526-529`, « … UTC ») : un modèle qui calcule « dans deux heures » à partir d'elle écrit une heure naïve en UTC. Sur un poste à Toronto, « rendez-vous demain à 10 h » devient 10 h de Paris, affiché 4 h. Forme recommandée pour le ticket : `ChatRequest` gagne `timezone`, envoyé par `ChatInput` comme le fait `EventForm` (`components/calendar/EventForm.tsx:280`), validé par `_validate_timezone` (`routers/calendar.py:87-97`, repli Paris) ; l'outil ramène une heure naïve de ce fuseau à Paris, comme `_heure_murale_paris` (`routers/calendar.py:100-110`) ; l'heure donnée au modèle est dite dans ce fuseau. Le test `test_une_heure_sans_fuseau_reste_celle_de_paris` reste vrai sans champ et sur un poste à Paris ; il gagne un jumeau « poste America/Toronto : 10 h de Toronto ».

**A-3, preuves.** Toute réponse ni 200 ni 5xx sort en 400 « Token refresh failed: … » (`services/oauth.py:337-343`) ; une page HTML (portail captif, redirection suivie par `services/http_client.py:59`) fait lever la lecture JSON, qui sort en 401 « Please reconnect your account » (`routers/email.py:319-324`) ; l'écran lit « Token » et « 401 » comme une session expirée (`components/email/EmailList.tsx:298-299`). Même famille que B-1488, pour les autres causes passagères. P-105 ne dépend pas de sa correction : la relève classe sur un refus typé (6.5).

**C-1, ce que P-105 en attend.** Les lignes écrites avant B-1486 (import ICS en Z ou avec TZID) et avant B-1487 (créées ou modifiées sur un poste hors de Paris) ne sont pas converties. P-105 ne tranche pas C-1 et ne propose plus de tenir ces lignes pour occupées « sur toutes leurs lectures » (constat 8 : aucun critère ne les distingue, et les fuseaux d'origine des ICS ne sont pas conservés). Il s'engage à ceci : **le créneau ne suppose pas que chaque ligne est en heure de Paris**, et la garde `CRENEAU_LIVRE` reste fausse tant que C-1 n'est pas tranché. Si C-1 conclut à une conversion, rien n'est à ajouter ici. S'il conclut à l'absence de conversion, la carte des créneaux porte une phrase de réserve : « Les rendez-vous créés ou importés avant la version 0.xx peuvent être décalés d'une ou plusieurs heures : vérifie ton agenda avant de réserver » (numéro de version posé à la release). Si C-1 veut un critère pour cibler ces lignes, c'est à lui de le créer ; P-105 le lira alors.

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

## 5. État du code à la base relue

Les points d'appui de la V2 (section 4) et de la V3 (section 5) restent justes, lignes rebasées ; seuls ceux qui changent ou s'ajoutent sont repris ici.

- **Agendas, convention.** `CalendarEvent.start_datetime` est une heure murale de Paris, naïve (`services/calendar/local_provider.py:28-41`, B-275). B-1486, B-1487 et B-1500 la tiennent pour l'import, l'écran et l'heure datée du chat ; A-2 reste ouvert pour l'heure naïve du chat ; les lignes déjà écrites relèvent de C-1. Le fournisseur local filtre sa fenêtre sur le seul début (`services/calendar/local_provider.py:215-226`), ce qui convient à l'écran de l'agenda mais pas à un calcul d'occupation. Toute modification locale réécrit `synced_at` (`services/calendar/local_provider.py:364`).
- **Récurrences locales.** Seule la RRULE est gardée à l'import (`services/import_service.py:78-82`), **pour un événement horaire comme pour une journée entière** ; la série est rangée sur `start_datetime` ou sur `start_date` selon `all_day` (`routers/calendar.py:1974-1979`). L'écran n'écrit aucune récurrence. EXDATE, RDATE et les occurrences déplacées n'existent pas en base.
- **CalDAV.** Lecture dépliée (`services/calendar/caldav_provider.py:227-231`), tronquée à `max_results` et tolérante aux événements illisibles (`:235-242`), statut écrit en dur (`:664`), heure sans TZID rendue naïve (`:620-623`).
- **Google.** `services/calendar/google_provider.py:130-150` convertit sans rien écrire ; seule la route de liste écrit le cache (`routers/calendar.py:913-1019`). Le statut est lu (`services/calendar/google_provider.py:306`), la transparence ne l'est pas.
- **Jeton OAuth.** Transport coupé, délai dépassé ou 5xx : 503 (`services/oauth.py:331-335`, `:354-357`). Toute autre réponse que 200 : 400, quel que soit le motif (`:337-343`). Corps illisible (page HTML, en 200 comme en 4xx) : l'exception sort du client OAuth sans être une `HTTPException`, puis en 401 générique (`routers/email.py:319-324`). Identifiants OAuth absents : 401 aussi (`routers/email.py:288-292`). Deux 401 de sens opposé, donc, et un 400 qui mêle refus et limitation de débit.
- **Lecture IMAP.** `imap_tools` sélectionne un dossier en lecture seule (`folder.set(folder, readonly=True)`, `.venv/.../imap_tools/folder.py:40-42`) ; la connexion du fournisseur sélectionne en écriture (`services/email/imap_smtp_provider.py:249-264`, `initial_folder="INBOX"`). En en-têtes seuls, `imap_tools` ne lit ni `INTERNALDATE` ni le corps (`.venv/.../imap_tools/mailbox.py:190-191`).
- **Verrous par clé.** Patron existant : `_verrous_projet.setdefault(project_id, asyncio.Lock())` (`services/project_sync_service.py:79`). Aucun `on_conflict_do_nothing` dans le code.
- **Échéances.** Une tâche porte `due_date` à minuit Z (`components/tasks/TaskForm.tsx:172`, `:188`), relu naïf après SQLite ; un livrable reçoit la date saisie telle quelle (`components/prototype/DeliverablesWorkspaceCanvas.tsx:82`). Dans les deux cas, l'information utile est un jour civil.
- **Projet d'une cible.** Une tâche change de projet par `routers/tasks.py:252-253` ; un livrable par l'import CRM et la synchronisation du tableur (`services/crm_import.py:1214`, `services/crm_sync.py:278`, `services/crm_utils.py:714`). La cascade d'un projet énumère ses tâches et livrables avant de le supprimer (`routers/memory.py:457-466`) ; elle est appelée par la suppression d'une fiche (`routers/memory.py:1138`), celle d'un projet (`:1436`) et l'anonymisation (`routers/rgpd.py:266`).
- **Brief et « Cette semaine ».** Le brief se relit toutes les 5 minutes, au focus et au retour de visibilité (`components/prototype/usePrototypeReadData.ts:5`, `:48-50`) ; « Cette semaine » ne lit qu'au montage (`components/prototype/CetteSemaine.tsx:56-62`). Le brief rend une liste plate (`components/prototype/prototypeReadModels.ts:180-205`), coupée au seuil du réglage par un état interne (`components/prototype/TodayDashboardCard.tsx:123`, `:144`) ; aucune ancre de source n'existe.
- **Portabilité d'une fiche.** `GET /api/rgpd/export/{contact_id}` (`routers/rgpd.py:47`) rend ce que l'anonymisation efface (B-590, `routers/rgpd.py:135-136`) ; son schéma a des listes par défaut vides (`models/schemas.py:457-467`).

## 6. Conception V4

La conception de la V3 est gardée ; chaque sous-section la reprend en entier, avec les changements de la V4 intégrés.

### 6.1 Vocabulaire

À l'écran, « travaux » désigne les traitements longs (`docs/rules/RULES-DESIGN.md`, section 13) : le mot « travail en cours » ne paraît jamais. On dit **la tâche** ou **le livrable**, et **la cible** dans ce document. La source du brief s'appelle **« E-mails »**, la marque sur une cible **« Mail récent »**. Les deux libellés sont neufs (aucun registre ne les porte à la base relue) ; ils entrent au lexique au lot 3.

### 6.2 Le rapprochement, un moteur pur

Inchangé : module de fonctions pures `rapprocher(entete, index, reglages) -> list[Proposition]`, index construit une fois par relève (adresses des fiches non archivées, projets `active`, cibles ouvertes avec leur projet **courant**, rapprochements retenus par fil), règles 1 à 6 dans l'ordre de la V2 (fil confirmé ; contact d'une tâche ouverte ; contact d'un projet à une seule cible ; contact d'un projet à plusieurs cibles ; objet qui cite un projet ou un livrable ; même domaine hors domaines grand public), mêmes garde-fous (écart retenu 90 jours, silences, mention d'objet avec `_fold` de `services/memory_tools.py:902-908`, frontière de mot, liste de mots courants, liste fermée de domaines grand public), mêmes écartements préalables (adresse du compte, en-têtes de masse `List-Id`, `List-Unsubscribe`, `Precedence`, `Auto-Submitted`, puis le classeur `services/email_classifier_v2.py:194`), mêmes choix tranchés (« ouvert » couvre tout ce qui n'est pas terminé d'un projet actif ; règle du domaine au niveau « à confirmer »). Un rapprochement reste une proposition : il ne modifie ni la fiche, ni la cible, ni le mail.

### 6.3 Identité d'un message et fils

**Identité.**

- Clé principale : l'en-tête `Message-ID` normalisé (chevrons et espaces retirés, minuscules).
- **Sans `Message-ID`**, la clé ne dépend jamais de l'UID, qui change avec UIDVALIDITY :
  - Gmail : `gmail:` suivi de l'identifiant Gmail, stable pour la vie du message ;
  - IMAP : `empreinte:` suivi du SHA-256 de (compte, expéditeur normalisé, en-tête `Date` brut, objet, `RFC822.SIZE`). La taille est rendue par la lecture d'en-têtes (`.venv/.../imap_tools/mailbox.py:190-191`) et ne change pas quand le message change de dossier.
- **`Message-ID` partagé par deux messages distincts** : chaque ligne porte une `empreinte` (SHA-256 de l'expéditeur normalisé, de l'en-tête `Date` brut et de l'objet). Quand un `Message-ID` déjà connu arrive avec une autre empreinte, la clé devient `<Message-ID>#<12 premiers caractères de l'empreinte>` : le second message est traité comme neuf.
- On garde aussi l'identifiant du fournisseur pour ouvrir le mail (identifiant Gmail, ou UIDVALIDITY et UID). « Ouvrir le mail » essaie cet identifiant, puis recherche le `Message-ID` dans la boîte, et à défaut le dit (« ce mail a été déplacé ou supprimé »).

**Pourquoi la relève n'écrit jamais `EmailMessage`.** Inchangé : clé primaire sur l'identifiant seul (`models/entities.py:391`), collisions entre comptes IMAP (`routers/email.py:1233-1243`, `:1276`), clé étrangère `email_follow_ups.email_message_id` (`models/entities.py:938`). La table des rapprochements porte elle-même ce qu'elle affiche.

**Fils.** Gmail : `gmail:` suivi du `threadId`. IMAP (décision 3), dans cet ordre : l'ancêtre déjà connu (un identifiant de `References` ou `In-Reply-To` présent dans un rapprochement retenu du même compte) ; sinon le premier identifiant de `References` ; sinon `In-Reply-To` ; sinon la clé du message lui-même. Un message sans `Message-ID` ni ancêtre a pour fil sa propre clé : « Pas lié » ne vaut alors que pour lui. Aucun regroupement par objet.

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
| `recu_le` | date de l'en-tête `Date`, **pour l'affichage seulement** |
| `expediteur_adresse`, `expediteur_nom` | normalisée ; nom tel quel ; adresse indexée (effacement par adresse, section 6.11) |
| `objet` | tronqué à 200 caractères |
| `contact_id` | fiche (nullable, indexée) |
| `cible_type`, `cible_id` | `tache`, `livrable` ou `projet` ; paire indexée |
| `regle`, `niveau` | 1 à 6 ; `sur`, `probable`, `a_confirmer` |
| `statut` | `nouveau`, `vu`, `confirme`, `ecarte` |
| `cree_le`, `maj_le` | horloge locale, UTC naïve comme les autres colonnes |

**Pas de `projet_id`** (constat 4). La V3 le portait avec un invariant tenu à l'écriture seulement. Le projet d'une cible se lit au moment de la lecture : `Task.project_id` pour une tâche, `Deliverable.project_id` pour un livrable, la cible elle-même pour un projet. Le brief, les pastilles et l'effacement suivent donc la cible là où elle est. Coût : une jointure sur deux tables dans les lectures, bornées à cinq lignes pour le brief et à un projet pour les pastilles.

Unicité sur (`account_id`, `message_cle`, `cible_type`, `cible_id`). Objet, adresse et nom de l'expéditeur sont des données personnelles : export, purge, anonymisation et rétention les couvrent (section 6.11).

**`silences_courrier`.** `id`, `account_id` (nullable), `type` (`projet`, `expediteur`, `fil`), `valeur`, `jusqu_au` (jamais nul, jamais au-delà de 90 jours), `cree_le`.

**`releves_courrier`**, une ligne par compte : `account_id` (clé primaire et étrangère), `uidvalidity` et `dernier_uid` (IMAP), `filigrane_date` (Gmail), `premiere_releve_le`, `premiere_releve_plafonnee` (booléen), `derniere_tentative_le`, `derniere_reussite_le`, `etat` (`jamais`, `ok`, `illisible`, `a_reconnecter`), `code_erreur` (un code, jamais le texte d'une exception), `non_examines`.

Motif de la troisième table plutôt qu'une colonne sur `EmailAccount` : `create_all` n'ajoute aucune colonne à une table existante (`models/database.py:320-325`).

**Préférence serveur** `veille_courrier` : relève de fond seulement.

### 6.5 La relève au geste

**Un seul chemin** : `POST /api/veille-courrier/relever?account_id=...&forcer=...`. Il lit des en-têtes, applique les règles, écrit des propositions et l'état du compte. Il ne lit jamais un corps et ne modifie rien chez le fournisseur.

**Qui l'appelle.** L'ouverture de l'écran E-mail (vue complète `components/email/EmailList.tsx` et carte `components/prototype/EmailConversationCard.tsx`), une fois par compte et par ouverture, sans attendre la réponse ; le bouton « Relever » de la source E-mails (`forcer=true`). Sans `forcer`, un compte relevé il y a moins de deux minutes n'est pas relu.

**Sérialisation par compte.** Un verrou `asyncio.Lock` par compte, sur le patron de `services/project_sync_service.py:79`. Une relève qui trouve le verrou pris attend sa libération, puis rend l'état que la première vient d'écrire, sans relire, même avec `forcer`. Le serveur tourne en un seul processus : un verrou en mémoire suffit.

**Écriture sans doublon.** `sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_nothing(index_elements=[account_id, message_cle, cible_type, cible_id])` : un message déjà traité, relu après une remise à zéro du filigrane, ne lève aucune erreur.

**Filigrane monotone.** Mise à jour conditionnelle (`dernier_uid` n'est remplacé que par une valeur plus grande, dans la même UIDVALIDITY ; `filigrane_date` que par une date plus tardive), seulement après l'écriture réussie des propositions du message.

**Lecture IMAP.** Une méthode nouvelle du fournisseur, distincte de `list_messages` :

- connexion sans dossier initial, puis `folder.set("INBOX", readonly=True)`, soit un `EXAMINE` : le serveur refuse tout changement d'indicateur pendant la session ;
- `headers_only=True`, `mark_seen=False`, sous `_run_imap_operation` et ses délais (`services/email/imap_smtp_provider.py:282`) ;
- statut du dossier lu d'abord (UIDVALIDITY) ;
- **première relève, ou UIDVALIDITY changée** (constat 7) : critère `SINCE` à J-14 (date interne du serveur, pas l'en-tête `Date:`) ; parmi les UID rendus, **les 50 plus élevés** sont examinés, le filigrane est posé sur le plus élevé. Le reste de la fenêtre n'est **ni examiné ni compté** : `non_examines` vaut 0, et `premiere_releve_plafonnee` dit si la fenêtre dépassait 50. Le brief dit « rapprochement commencé le 26/09 avec tes 50 mails les plus récents » (ou « commencé le 26/09 » si la fenêtre tenait). Les rapprochements existants restent, identifiés par `Message-ID` ;
- relèves suivantes : critère UID « dernier + 1 à la fin », ordre croissant, UID inférieurs ou égaux au filigrane filtrés (le serveur rend toujours le dernier message pour une plage ouverte).

Alternative écartée pour la première relève : un filigrane posé bas, que « Relever la suite » ferait remonter. La première relève montrerait alors les mails les plus anciens d'abord, et le compteur « 30 mails pas encore examinés » renverrait à des mails de deux semaines, qu'on n'attend plus de voir rapprochés.

**Lecture Gmail.** Première relève : `in:inbox newer_than:14d`, les 50 plus récents, même règle (reste non compté, `premiere_releve_plafonnee`). Ensuite : `after:` suivi du filigrane en secondes (date interne de Gmail). Identifiants listés, puis `format='metadata'` des plus anciens aux plus récents, comme la liste existante (`routers/email.py:958-963`).

**Plafond.** Relèves suivantes : au plus 50 messages examinés, du plus ancien au plus récent après le filigrane. Le reste, **au-dessus du filigrane**, est compté dans `non_examines` ; le brief le dit (« 34 mails pas encore examinés ») avec « Relever la suite » (doctrine B-425), qui le fait baisser.

**États de compte** (constat 1).

- `a_reconnecter` **seulement sur un refus typé** :
  1. `RefusDeJeton`, sous-classe nouvelle de `HTTPException` levée par `refresh_access_token` quand la réponse n'est ni 200 ni 5xx **et** que son corps JSON porte `error` parmi `invalid_grant`, `invalid_client`, `unauthorized_client` ; code 400 et texte inchangés ;
  2. `IdentifiantsOAuthAbsents`, sous-classe de `HTTPException` levée à la place de l'actuelle (`routers/email.py:288-292`) ; code 401 et texte inchangés.
  Les deux sous-classes gardent code et texte : l'écran E-mail, qui lit le texte (`components/email/EmailList.tsx:298-299`), et `tests/test_b1488_jeton_mail_panne_passagere.py` ne voient aucune différence.
- `illisible` pour **tout le reste** : le 503 de B-1488 ; un 400 non typé (429, 408, tout autre 4xx, corps non JSON) ; le 401 générique de `routers/email.py:319-324` (déchiffrement, page HTML en 200 derrière une redirection suivie, échec d'écriture du jeton) ; un 401 de l'API Gmail avec un jeton encore valide localement ; serveur IMAP injoignable ; identifiants IMAP refusés (code `identifiants_refuses`) ; toute autre exception. Retenté au geste suivant.
- **Pourquoi la relève diverge de l'écran E-mail** sur le 401 générique. L'écran retente à chaque geste : son « reconnecte-toi » est un message, pas un état. `a_reconnecter` arrête la relève jusqu'à une reconnexion : un mauvais classement coûterait une source d'alerte muette pour de bon, alors que « illisible depuis 9 h 10 » reste vrai et se corrige seul. Un jeton révoqué côté Google sans refus typé (401 de l'API Gmail) finit en refus typé au plus tard au rafraîchissement suivant, dans l'heure (`routers/email.py:305`).
- Un compte `a_reconnecter` n'est plus tenté jusqu'à sa remise à `jamais`, faite en quatre points, chacun testé :
  1. rappel OAuth `POST /auth/callback`, branche « compte existant » (après `routers/email.py:423`) ;
  2. rappel `GET /auth/callback-redirect`, même branche (après `routers/email.py:542`) ;
  3. `POST /auth/imap-setup`, même branche (après `routers/email.py:815`) ;
  4. `POST /auth/update-credentials/{account_id}` (`routers/email.py:681-717`), après l'enregistrement des identifiants, quel que soit le résultat du rafraîchissement.
- Dans tous les cas, aucune exception ne remonte à l'écran : la réponse porte l'état, et le brief le nomme.

**Mise au repos** (décision 1). La relève écrit en base : elle est cliente de P0. Pendant une purge ou une restauration, elle refuse d'entrer (503 « relève suspendue ») et celle en vol est attendue. P0 est livrée avant le lot 5.

### 6.6 Ce que l'utilisateur voit

**La source « E-mails » du brief.**

- Elle lit seulement `rapprochements_courrier` et `releves_courrier`, jamais le fournisseur ; le rafraîchissement du brief reste une lecture locale.
- `GET /api/dashboard/today` gagne un bloc `courrier` : lignes groupées par cible (cinq au plus), total pour le compteur, état et fraîcheur par compte, et `creneau` (valeur de la garde `CRENEAU_LIVRE`). Une lecture en échec ajoute `email` à `indisponibles`.
- Une ligne par cible : « 2 mails de Mme Durand sur Refonte du site · livrable Maquettes, échéance jeudi », avec le motif. Le projet nommé est celui de la cible **à la lecture** (6.4).
- La fraîcheur est toujours dite : « relevé à 10 h 42 », « jamais relevé : ouvre tes e-mails ou appuie sur Relever », « compte pro@ à reconnecter », « compte perso@ illisible depuis 9 h 10 », « rapprochement commencé le 26/09 avec tes 50 mails les plus récents ».
- Place : dans la liste plate, après les factures échues, avant les rendez-vous (`components/prototype/prototypeReadModels.ts:199-200`). Domaine visuel `taches` (`components/ui/Etiquette.tsx:17`).
- Aucune source quand aucun compte n'est branché.

**Rendu et ancre** (constat 5). Une ligne courrier porte deux interactifs (le dépliage et « Vu »), ce que `Ligne` exclut par contrat (« un seul interactif pour la rangée », `components/ui/Ligne.tsx:8`) : elle est rendue par un composant dédié, `LigneCourrier`, dans le même `visibleItems.map` (`components/prototype/TodayDashboardCard.tsx:302`). La **première** ligne courrier porte `id="brief-source-email"`. L'Accueil tient un état `sourceDemandee: { cle: 'email', jeton: number } | null` et le passe à `TodayDashboardCard`. À chaque nouveau jeton, la carte appelle `setToutAfficher(true)` (le repli de `:326-336` est levé), puis, après le rendu, fait défiler jusqu'à `#brief-source-email` et pose le focus sur son bouton de dépliage. Sans ligne courrier (lue entre-temps, ou source indisponible), le focus va au titre du brief (`tabIndex={-1}`).

**Garde de livraison de la relève.** Le lot 3 livre l'écran avant que la relève existe. Le module de la veille porte `RELEVE_COURRIER_LIVREE = False` ; tant qu'elle est fausse, `/today` ne rend pas le bloc `courrier` et la source n'apparaît pas. Le lot 5 la passe à vrai dans le même commit que la relève, avec le test de bout en bout qui la prouve. Les pastilles, la ligne de « Cette semaine » et la liste des silences n'ont pas besoin de garde : sans relève, aucune ligne n'existe à afficher.

**Garde de livraison du créneau** (constat 9). Le module porte aussi `CRENEAU_LIVRE = False`. Tant qu'elle est fausse, `POST /api/veille-courrier/creneaux` répond 404 et « Proposer un créneau » n'est pas rendu (le bloc `courrier` porte `creneau: false`). Elle ne passe à vrai qu'après A-2 livré et C-1 tranché ; une sentinelle le tient (lot 4 : `DECISION_C1` et le champ `timezone` de `ChatRequest`). Ainsi le lot 4 peut être sur main sans être visible, et le lot 5, qui passe la première garde, n'expose pas le créneau.

**Actions sur une ligne.** Libellé bouton de dépliage (`aria-expanded`) ; à droite, « Vu » seul ; dans le dépliage, par mail, « Ouvrir le mail », « Oui, c'est lié », « Pas lié », « Taire », et « Proposer un créneau » si `creneau` est vrai. « Vu » sort la cible du brief et garde la pastille ; « Oui, c'est lié » demande la cible pour les règles 4 et 6 ; « Pas lié » écarte le fil pour cette cible 90 jours ; « Taire » 7 jours ou jusqu'à réactivation, 90 jours au plus, levée depuis Paramètres, rubrique Services. « Relever » et « Relever la suite » apparaissent avec le lot 5.

**« Ouvrir le mail »** (constat 6). Route de résolution `GET /api/veille-courrier/messages/{id}/ouvrir` : elle rend l'identifiant du fournisseur, ou le retrouve par `Message-ID` (IMAP : recherche sur l'en-tête dans la boîte de réception sélectionnée en lecture seule ; Gmail : `rfc822msgid:`). **Aucune écriture métier** : les tables de la veille et `email_messages` ne changent pas ; seul le jeton Gmail expiré est renouvelé et enregistré, comme à chaque lecture de l'écran E-mail (`routers/email.py:304`, `:312`, et `services/contexte_execution.py:22-25`, qui classe déjà cet effet comme technique). C'est le régime de l'écran E-mail, qui n'est pas client de P0 : la route vit au lot 3. L'écran ouvre ensuite le mail par l'identifiant rendu (`services/api/email.ts:294-295`).

**« Cette semaine »** (décision 6). `GET /api/dashboard/semaine` gagne un champ `courrier` distinct de `a_venir` : le nombre de cibles dont l'échéance tombe de demain à J+7 et qui ont un rapprochement `nouveau`. Une seule ligne quand il est positif : « Mail récent sur 2 tâches ou livrables de la semaine ». `components/prototype/CetteSemaine.tsx` se relit au focus et au retour de visibilité, sur le patron du brief (`components/prototype/usePrototypeReadData.ts:48-50`). Le clic appelle une nouvelle propriété `onOpenBriefSource('email')`, qui pose un nouveau jeton dans `sourceDemandee`. Une lecture en échec ajoute `email` aux `indisponibles` de la route, et la ligne dit « Les mails rapprochés n'ont pas pu être lus ».

**Pastille « Mail récent ».** `Etiquette` avec texte, sur `components/memory/ProjectDeliverablesSection.tsx`, `components/crm/DeliverablesList.tsx` et la carte d'une tâche, tant qu'un rapprochement `nouveau` ou `vu` de moins de 90 jours vise la cible. Données : `GET /api/veille-courrier/pastilles?projet_id=`, qui joint les cibles **actuelles** du projet (6.4).

**Accessibilité et mode démo.** Boutons nommés d'après la cible, dépliage dans l'ordre de tabulation, test vitest par rôle et par nom ; `maskText` sur expéditeurs, objets, cibles et titre prérempli.

### 6.7 Le créneau libre

**Déclenchement.** Au geste « Proposer un créneau », jamais en fond. `POST /api/veille-courrier/creneaux` avec la cible, la durée et le fuseau du poste ; 404 tant que `CRENEAU_LIVRE` est faux.

**Horizon.** Le plus proche entre l'échéance de la cible et le prochain rendez-vous avec ce contact. Sans échéance ni rendez-vous, aucun créneau. Lecture bornée à 30 jours.

- **Règle de l'échéance.** Une échéance est un **jour civil** : la partie date de la valeur stockée, sans conversion de fuseau (minuit Z pour une tâche, relu naïf ; date brute pour un livrable). L'horizon est la **fin des heures ouvrées de ce jour, dans le fuseau du poste** (18 h). Une tâche due le jeudi 01/10 donne « avant jeudi 18 h » à Paris comme à Fort-de-France.
- **Règle du rendez-vous.** Son début, converti en instant depuis la convention de son agenda.

**Lecture des agendas, au moment du geste.** Chaque agenda est lu par une fonction qui rend `(occupations, complet)`. Un agenda dont `complet` est faux est **illisible** : aucun créneau n'est proposé, et l'écran le nomme (« l'agenda Travail n'a pas pu être lu : aucun créneau proposé, pour ne pas t'en suggérer un déjà pris »), avec « Réessayer ».

- **Agendas locaux.** Requête dédiée, jamais `list_events` du fournisseur local (filtre sur le seul début, `services/calendar/local_provider.py:215-226`, et plafond de 100) :
  - seulement les agendas `provider == "local"` : le cache Google n'est jamais lu pour un créneau ;
  - événements ponctuels avec heure : chevauchement, `start_datetime < fin` et `end_datetime > debut`, bornes ramenées en heure murale de Paris ;
  - journées entières ponctuelles : `start_date <= dernier jour` et `end_date >= premier jour` (fin inclusive, BUG-144) ;
  - **séries** (constat 2) : toutes les lignes dont `recurrence` n'est pas nul et dont **`start_datetime` précède la fin de fenêtre, ou `start_date` précède ou égale son dernier jour**, sans borne basse, pour qu'une série commencée trois mois plus tôt soit lue, qu'elle soit horaire ou en journée entière.
- **Dépliage d'une série horaire.** `dateutil` refuse toute différence de conscience du fuseau entre DTSTART et UNTIL, dans les deux sens (mesuré). Le dépliage :
  1. rend le début conscient en heure de Paris (convention de la colonne) ;
  2. normalise UNTIL avant `rrulestr` : en Z, gardé ; date seule, remplacée par 23:59:59 de ce jour à Paris, convertie en Z ; date-heure sans fuseau, lue en heure de Paris, convertie en Z ;
  3. déplie sur la fenêtre (les occurrences gardent l'heure murale de Paris à travers les changements d'heure) ;
  4. toute exception rend l'agenda local illisible.
- **Dépliage d'une série en journée entière** (constat 2, mesuré). Le début est `start_date` à minuit, **naïf** ; UNTIL est normalisé en naïf : date seule, gardée (le dépliage l'inclut, mesuré : `UNTIL=20261012` rend le 12/10) ; en Z, ramené au jour de Paris de cet instant, à 23:59:59 naïf (sans quoi `rrulestr` lève `ValueError`, mesuré) ; date-heure sans fuseau, gardée. Chaque occurrence occupe les jours civils de sa date à sa date plus (`end_date` moins `start_date`), fin inclusive. Toute exception rend l'agenda local illisible.
- Les exceptions d'une série n'existent pas en base : une occurrence annulée chez l'organisateur apparaît occupée. C'est une erreur dans le sens prudent.
- **Google.** Lecture par le fournisseur (`services/calendar/google_provider.py:130-150`), occurrences dépliées (`singleEvents`, `services/calendar_service.py:162`), **sans écriture du cache**. Toutes les pages sont suivies ; au-delà de dix pages de 250, l'agenda est incomplet. `status == "cancelled"` ignoré. `CalendarEventDTO` gagne `transparent: bool = False`, rempli depuis `transparency` : un événement transparent ne bloque rien. Le jeton passe par `ensure_valid_access_token` : une erreur rend l'agenda illisible, quel que soit son code.
- **CalDAV.** Lecture stricte dédiée : tous les événements de la fenêtre, sans tranche ; au-delà de 500, incomplet ; **un seul VEVENT illisible rend l'agenda incomplet**. `_caldav_event_to_dto` lit `STATUS` (au lieu du statut en dur, `services/calendar/caldav_provider.py:664`) et `TRANSP` : `CANCELLED` ignoré, `TENTATIVE` occupé, `TRANSPARENT` libre. **Heure flottante** (`services/calendar/caldav_provider.py:620-623`) : lue en heure de Paris, la convention que l'import ICS applique déjà (`services/import_service.py:56-59`) et celle de l'écran pour une heure sans fuseau (`routers/calendar.py:113-120`).
- Événements annulés ignorés ; provisoires occupés ; journées entières occupées, ponctuelles ou en série.

**Heures et jours** (décision 5). Fuseau du poste envoyé par l'écran et validé comme `_validate_timezone` (`routers/calendar.py:87-97`), repli sur Europe/Paris dit à l'écran ; heures stockées converties en instants depuis leur convention ; heures ouvrées de `WorkCalendar` (`services/planning.py:168-172`), sans réglage nouveau ; onze jours fériés légaux de métropole par une fonction pure, Pâques calculé, moteur PERT inchangé (`services/planning.py:20`) ; fin inclusive des journées entières.

**Ce que le créneau ne suppose pas.** Qu'une ligne locale écrite avant B-1486 ou B-1487, ou par l'outil du chat avant A-2, soit en heure de Paris (section 2). La garde `CRENEAU_LIVRE` le tient.

**Résultat.** Une heure par défaut (30 min, 1 h, 2 h), trois créneaux au plus, un par demi-journée au plus, fraîcheur dite, « Aucun créneau d'une heure avant jeudi 18 h » plutôt qu'un créneau après l'horizon ; phrase de réserve de C-1 si C-1 l'impose.

**Réservation.** « Réserver ce créneau » ouvre `NewEventForm` prérempli (propriété de valeurs initiales à ajouter, `components/prototype/MeetingConversationCard.tsx:212-229`) et passe par son étape de confirmation (`:229`). La création envoie le fuseau du poste (`components/prototype/MeetingConversationCard.tsx:270`), que le serveur convertit en heure de Paris (`routers/calendar.py:1194-1195`).

### 6.8 La relève de fond, facultative

Inchangée : désactivée par défaut, gouvernée par le seul interrupteur de Paramètres, rubrique Services (décision 2), planificateur calqué sur celui des notifications (`main.py:363-382`), absent sous `THERESE_SKIP_SERVICES` (`main.py:262`), annulé à l'arrêt ; même chemin que la relève au geste (même verrou, même insertion sans doublon, même filigrane, même classement des états) ; compte `a_reconnecter` sauté ; client de P0 ; coupée par « Effacer toutes mes données », qui efface `preferences` (`routers/data.py:697`).

### 6.9 Ce qui ne part jamais sans confirmation

Automatique, et seulement cela : lire des en-têtes sans les marquer lus, calculer, écrire une proposition locale et l'état d'un compte (plus le jeton renouvelé, effet technique déjà présent à l'écran E-mail). Tout le reste reste au clic (répondre, brouillon, transfert, indicateurs, classement, rattachement, statut ou échéance d'une cible, relance, réservation, envoi à un modèle en ligne).

**Garde en liste blanche.** Deux mécanismes, testés séparément :

- côté serveur IMAP : la boîte est sélectionnée par `EXAMINE` ; le test vérifie l'appel `folder.set("INBOX", readonly=True)` et l'absence de `select` en écriture ;
- côté code : les doublures du fournisseur IMAP et du client Gmail **échouent sur tout appel hors de la liste permise**. IMAP : connexion, `folder.status`, `folder.set` en lecture seule, recherche d'UID, `fetch` en en-têtes seuls sans marquage. Gmail : liste des messages et lecture en `metadata`. Toute autre méthode, présente ou future (`create_folder`, `delete_folder` à `services/email/imap_smtp_provider.py:813` et `:834`, `trash_message`, `create_label`, `update_label`, `delete_label`, `batch_modify_messages` à `services/gmail_service.py:414`, `:431`, `:445`, `:449`, `:465`), fait échouer le test.

### 6.10 Confidentialité et modèle

Inchangée : V1 sans modèle ; phase 2 sur modèle Ollama local non « cloud » seulement (`services/ollama_capabilites.py:86-90`), sans repli en ligne (B-1071, `services/llm.py:832-841`), corps lu seulement pour un mail rapproché et enveloppé par `sanitize_for_context` ; en ligne, jamais en fond.

### 6.11 Effacement, portabilité et rétention

Une seule fonction de service, `oublier_courrier(session, *, comptes=(), fiches=(), adresses=(), projets=(), taches=(), livrables=())`, oublie les rapprochements et les silences qui les visent. Elle est appelée depuis :

| Chemin | Lieu à la base | Ce qui part |
|---|---|---|
| Purge totale | `routers/data.py:632-700` (tâches `:671`, livrables `:675`) | les trois tables, avant `EmailMessage` et `EmailAccount` (`:662-663`) |
| Déconnexion d'un compte | `routers/email.py:758-767` | les trois tables pour ce compte |
| Anonymisation manuelle | `routers/rgpd.py:184`, l'adresse lue avant `effacer_l_identite` (`:209`) | rapprochements de la fiche (`contact_id`) **et ceux dont `expediteur_adresse` vaut l'adresse de la fiche** ; silences `expediteur` à cette adresse |
| Anonymisation automatique | `services/rgpd_auto.py:196-208`, l'adresse lue avant `effacer_l_identite` (`:199`) | idem |
| Suppression d'une fiche | `routers/memory.py:1079` | idem |
| Cascade d'un projet | `_nettoyer_et_supprimer_projet` (`routers/memory.py:361`), entre l'énumération des tâches et livrables (`:457-464`) et `session.delete(project)` (`:466`) ; appelée par `routers/memory.py:1138`, `:1436` et `routers/rgpd.py:266` | rapprochements visant le projet, et ceux des **identifiants de tâches et livrables que la cascade supprime réellement** ; silences `projet` de ce projet |
| Suppression d'une tâche | `routers/tasks.py:293` ; tâches d'une fiche anonymisée, `routers/rgpd.py:271-273` | rapprochements de la tâche |
| Suppression d'un livrable | `routers/crm.py:378` | rapprochements du livrable |

Aucun `PRAGMA foreign_keys` : chaque chemin est explicite et testé. Une tâche ou un livrable déplacé d'un projet A vers B n'est plus dans l'énumération de A : ses rapprochements restent ; arrivé dans A, il y est : ils partent (constat 4).

**Portabilité d'une fiche.** `GET /api/rgpd/export/{contact_id}` (`routers/rgpd.py:47`) rend, avant tout effacement possible, `rapprochements_courrier` (lignes dont `contact_id` vaut la fiche ou dont `expediteur_adresse` vaut son adresse) et `silences_courrier` (silences `expediteur` à son adresse). `RGPDExportResponse` (`models/schemas.py:457-467`) gagne deux listes par défaut vides, comme `prestations` et `email_messages` (B-590).

**Rétention** (décision 4). Tout court depuis `cree_le` ou `maj_le`, horloge locale, jamais depuis l'en-tête `Date:` :

- rapprochements `ecarte` : 90 jours après `maj_le` ;
- silences : `jusqu_au`, jamais nul, jamais au-delà de 90 jours ;
- rapprochements `nouveau` et `vu` : 90 jours après `cree_le` ;
- rapprochements `confirme` : tant que la cible, la fiche et le compte existent.

L'expiration s'applique au démarrage, avant la première requête, puis au début de chaque relève ; les lectures filtrent de toute façon les lignes expirées.

**Export complet, sauvegarde et restauration.** Les trois tables entrent dans l'export RGPD complet (`routers/data.py:172-428`) ; `data_format_version` passe à la valeur suivante de celle en vigueur (« 1.4 » à la base, `routers/data.py:262`), en coordination avec toute autre RFC qui l'incrémenterait dans la même release ; l'archive porte la base entière (`routers/data.py:1108-1109`) ; une sauvegarde d'avant P-105 restaurée recrée les tables vides, puisque la base est rouverte par `init_db` (`routers/data.py:1505-1516`, `:1513`).

## 7. Mise en œuvre, lot par lot

Chaque lot fait l'objet d'un commit, tests rouges d'abord, sabotage ciblé par fonction et revue adverse du diff.

**Dépendances.**

| Lot | Dépend de | Ne dépend pas de |
|---|---|---|
| 1. Moteur | rien | P0, prérequis d'agenda |
| 2. Données | lot 1 | P0 |
| 3. Écran, sans relève | lots 1 et 2 | P0 (aucune écriture métier de fond ; la résolution d'un mail a le régime de l'écran E-mail) |
| 4. Créneau libre | lots 1 à 3 ; B-1486, B-1487, B-1488 et A-1 (fermés au code) ; **A-2 et C-1 pour passer `CRENEAU_LIVRE` à vrai** | P0 (aucune écriture) |
| 5. Relève au geste | P0, B-1488, lots 1 à 3 ; passe `RELEVE_COURRIER_LIVREE` à vrai | lot 4 (sa garde reste fausse) ; A-3 |
| 6. Relève de fond | P0, lot 5 | lot 4 |
| 7. Recette | lots 1 à 6, les deux gardes à vrai | |

### Lot 1 : le moteur de rapprochement

- **Moteur.** Module pur : normalisation d'adresse, index (cibles avec leur projet courant), règles 1 à 6, garde-fous, écartements par en-têtes puis classeur, clé de message avec repli et empreinte, clé de fil. Retrait, dans un commit à part, de `services/email_contact_matcher.py` (`:16`, sans appelant).
- **Écran, données.** Rien.
- **Tests à écrire en premier** (`tests/test_veille_courrier_rapprochement.py`, un test par règle, chacun saboté) : ceux de la V2 et de la V3 (adresses, statuts ignorés, projet à plusieurs cibles, mentions d'objet, domaines, fil confirmé, fil écarté, silences, fils IMAP, en-têtes de masse, classeur sans extrait ; message IMAP sans `Message-ID` : clé stable après un changement d'UID ; deux messages au même `Message-ID` : deux clés ; message sans `Message-ID` ni ancêtre : « Pas lié » n'écarte pas un autre message du même expéditeur), plus : **tâche déplacée de A vers B dans l'index : la règle du contact de projet la rattache à B**.
- **Critères observables.** Sur un jeu d'en-têtes témoin, le moteur rend les propositions attendues, identiques d'une exécution à l'autre.

### Lot 2 : les données

- **Moteur.** `oublier_courrier` (section 6.11), expiration.
- **Écran.** Rien.
- **Données.**
  - Trois modèles dans `models/entities.py`, créés par `create_all` ; révision Alembic de `down_revision = "b8c9d0e1f2a3"` qui crée les tables si elles manquent ; `ALEMBIC_HEAD_REVISION` (`models/database.py:619`) passe à cette révision.
  - Preuve d'estampillage : `tables_de_veille_courrier()` dérivée des modèles, sur le patron de `tables_de_planning()` (`models/database.py:632`).
  - **Base témoin des tests** : `_creer_tables_veille_reelles(db_path)` dans `tests/test_alembic_stamp.py`, appelée par `_make_patched_tracked_db` (`:98`) après `_creer_tables_sync_reelles` et `_creer_tables_planning_reelles` (`:135-136`).
  - Export RGPD complet (trois blocs, version suivante) et export de la fiche (deux listes).
  - Appel de `oublier_courrier` sur chaque chemin du tableau de la section 6.11.
- **Tests à écrire en premier.**
  - `tests/test_alembic_stamp.py` : constante égale à la vraie tête (`:139`) ; jumeaux de `:307` et `:330` pour les tables de veille ; `make db-migrate` sur base neuve et ancienne ; les tests de ré-estampillage existants verts avec la base témoin étendue.
  - Export complet : trois clés, version suivante ; `tests/test_routers_data.py:152` passe à cette version (constat 11 : `tests/test_variables.py:213` n'est pas une garde d'incrément).
  - Export de la fiche : rapprochements par `contact_id` et par adresse présents, silences à son adresse présents, ceux d'une autre fiche absents.
  - Purge totale : zéro ligne dans les trois tables après le 200.
  - Déconnexion : les lignes du compte partent, celles d'un autre restent.
  - Anonymisation manuelle puis automatique : rapprochements de la fiche effacés ; rapprochement de règle 5 dont l'expéditeur est la fiche anonymisée, sans `contact_id`, effacé ; silence à son adresse effacé ; silence à une autre adresse gardé ; **tâche de la fiche supprimée par `routers/rgpd.py:271-273` : ses rapprochements partent**.
  - Suppression d'une tâche, d'un livrable, d'une fiche, d'un projet : lignes correspondantes effacées.
  - **Cascade** (constat 4) : « tâche déplacée de A vers B, suppression de A : ses rapprochements restent » ; « tâche arrivée dans A, suppression de A : ses rapprochements partent » ; « livrable réaffecté de A vers B par un import CRM, suppression de A : ses rapprochements restent » ; « livrable de A, suppression de A : ses rapprochements partent » ; la même cascade appelée par la suppression d'une fiche (`routers/memory.py:1138`) et par l'anonymisation (`routers/rgpd.py:266`) oublie les mêmes lignes.
  - Expiration : écarté de 91 jours parti, de 89 jours gardé ; `nouveau` de 91 jours parti ; un `nouveau` dont `recu_le` est vieux de deux ans mais `cree_le` d'hier est gardé ; `confirme` ancien gardé.
  - Restauration d'une sauvegarde d'avant P-105 : tables présentes et vides.
- **Critères observables.** Une base 0.75 mise à jour démarre, s'estampille à la nouvelle tête, et `make db-migrate` n'échoue pas.

### Lot 3 : ce que l'utilisateur voit, sans relève

- **Moteur.** Bloc `courrier` de `/api/dashboard/today` (sous la garde `RELEVE_COURRIER_LIVREE`, avec `creneau`) et champ `courrier` de `/api/dashboard/semaine`, lecture locale seule, projet de la cible par jointure ; routes des actions (`PATCH` d'un rapprochement, création et levée d'un silence), des pastilles, et route de résolution « Ouvrir le mail ».
- **Écran.**
  - Sixième entrée de `SOURCES_DU_BRIEF` (`components/prototype/prototypeReadModels.ts:223-235`, clé `email`, nom « E-mails »), type `TodayDashboard` étendu (`services/api/dashboard.ts:85`), `LigneCourrier`, ancre sur la première ligne courrier.
  - Propriété `sourceDemandee` de `TodayDashboardCard`, levée du repli, défilement, focus.
  - `components/prototype/CetteSemaine.tsx` : ligne unique, relecture au focus et à la visibilité, clic qui pose le jeton.
  - Liste des silences actifs avec « Réactiver », dans Paramètres, rubrique Services.
  - Pastille « Mail récent ».
  - Masque démo ; libellés « E-mails » et « Mail récent » au lexique (`docs/rules/RULES-DESIGN.md`, section 13, et `lib/lexique.test.ts`).
- **Données.** Écriture des statuts et des silences, au clic.
- **Tests à écrire en premier** (vitest, puis pytest) : ceux du lot 4 de la V2 sauf « Relever » et « Relever la suite », plus :
  - garde fausse : `/today` sans bloc `courrier`, aucune source « E-mails » même avec un compte branché ; garde vraie (forcée en test) : la source et ses phrases de fraîcheur ;
  - « Cette semaine » se relit au focus et au retour de visibilité ;
  - **« lignes courrier au-delà du seuil : le clic de « Cette semaine » lève le repli, `#brief-source-email` est rendu et le focus est sur son bouton de dépliage »** (constat 5) ; **« aucune ligne courrier : focus sur le titre du brief »** ;
  - `creneau: false` : aucun bouton « Proposer un créneau » dans le dépliage ;
  - « Ouvrir le mail » d'un message déplacé : la route le retrouve par `Message-ID` ; message introuvable : phrase dédiée ; **jeton Gmail expiré doublé : la résolution aboutit, les tables de la veille et `email_messages` sont inchangées, seul `access_token` du compte a changé** (constat 6) ;
  - **pastilles d'une tâche déplacée de A vers B : visibles sous B, plus sous A** ;
  - route `/today` : aucun appel réseau (fournisseurs doublés qui échouent si on les appelle).
- **Critères observables.** Garde forcée à vrai, sur des propositions semées en base de démonstration : le brief affiche la ligne, son motif et sa fraîcheur ; « Pas lié » la retire ; « Ouvrir le mail » ouvre le bon message dans l'écran E-mail. Garde à faux : l'Accueil est inchangé.

### Lot 4 : le créneau libre (garde `CRENEAU_LIVRE` fausse jusqu'à A-2 et C-1)

- **Moteur.** Fonction pure `creneaux_libres` ; fonction pure des jours fériés ; règle de l'échéance ; requête locale dédiée (séries horaires et en journée entière) et dépliage normalisé ; lecture stricte CalDAV ; lecture Google paginée sans écriture, `transparent` dans le DTO ; route `POST /api/veille-courrier/creneaux` sous la garde. `python-dateutil` déclaré dans `pyproject.toml` (déjà verrouillé, `uv.lock:2484`).
- **Écran.** Carte des créneaux dans le dépliage (rendue seulement si `creneau`) ; valeurs initiales de `NewEventForm` ; « Réserver ce créneau » ; phrase de réserve si C-1 l'impose.
- **Données.** Rien. Aucune écriture de cache.
- **Tests à écrire en premier** (`tests/test_creneaux.py`, puis vitest) :
  - **garde** (constat 9) : `CRENEAU_LIVRE` faux : la route répond 404 et le bloc porte `creneau: false` ; forcée à vrai : 200. Le module porte aussi `DECISION_C1`, qui vaut `"a_trancher"` jusqu'au ticket C-1, puis `"conversion"` ou `"reserve"`. Une sentinelle rougit si `CRENEAU_LIVRE` est vrai alors que `DECISION_C1` vaut `"a_trancher"` ou que `ChatRequest` ne porte pas le champ `timezone` d'A-2 ; avec `"reserve"`, la carte des créneaux porte la phrase de réserve ;
  - semaine type ; week-end ; journée entière ; événement de plusieurs jours à fin inclusive ; annulé ignoré ; provisoire bloquant ; transparent libre (Google et CalDAV) ;
  - **par les vraies écritures** : un rendez-vous créé par `POST /api/calendar/events` à 10 h avec `timezone=America/Martinique` bloque 10 h en Martinique (B-1487) ; un ICS à `DTSTART:...T080000Z` importé bloque 10 h à Paris en été (B-1486) ; un événement créé par l'outil du chat avec un décalage bloque son heure réelle (B-1500) ; **un rendez-vous créé par le chat à 10 h sans fuseau sur un poste America/Toronto bloque 10 h de Toronto** (exige A-2 : marqué `xfail(strict=True)` jusqu'à sa livraison, pour que sa réussite oblige à retirer la marque) ;
  - **séries** : série hebdomadaire commencée trois mois avant la fenêtre, chaque occurrence bloque ; UNTIL en Z ; UNTIL en date seule ; UNTIL flottant ; COUNT ; événement qui chevauche le début de fenêtre ; règle malformée : agenda local illisible ; **série hebdomadaire en journée entière commencée trois mois avant la fenêtre : chaque jour concerné occupé** ; **même série avec `UNTIL` en date seule, puis en Z : dernière occurrence incluse, aucune exception** (constat 2) ;
  - CalDAV : 501 événements : incomplet, aucun créneau, agenda nommé ; un VEVENT malformé parmi dix : idem ; `STATUS:CANCELLED` ignoré ; heure flottante lue en heure de Paris ;
  - Google : deux pages suivies ; aucune ligne écrite dans `calendar_events` pendant la lecture ; erreur de jeton : agenda illisible ;
  - échéance : tâche due le 01/10 (stockée `2026-10-01T00:00:00Z`) donne l'horizon 01/10 à 18 h à Paris et à Fort-de-France ; livrable dû le 01/10, idem ;
  - fériés : 11/11/2026, 25/12/2026, 29/03/2027, 06/05/2027 exclus ; passage à l'heure d'hiver du 25/10/2026 ; fuseau invalide : repli signalé ;
  - échéance passée ou absente : aucun créneau ; horizon ramené au prochain rendez-vous ; un créneau par demi-journée ; phrase dédiée si aucun ;
  - « Réserver ce créneau » ouvre le formulaire prérempli sans rien créer, et la création envoie le fuseau du poste.
- **Critères observables.** Garde forcée à vrai, sur les données de démonstration : trois créneaux avant l'échéance d'un livrable, aucun sur un férié, ni sur une occurrence d'une réunion récurrente commencée avant la fenêtre, ni sur un lundi d'une série « Chantier Martin, tous les lundis, journée entière ».
- **Visibilité.** Le commit qui passe `CRENEAU_LIVRE` à vrai vient après A-2 livré et C-1 tranché, et applique ce que C-1 impose (section 2).

### Lot 5 : la relève au geste (après P0)

- **Moteur.** Méthode de lecture d'en-têtes IMAP (connexion sans dossier, `EXAMINE`, `SINCE`, filigrane), lecture Gmail (première relève, `after:`), route `POST /api/veille-courrier/relever`, verrou par compte, insertion `ON CONFLICT DO NOTHING`, filigrane monotone, garde de deux minutes, états de compte sur refus typés, **`RefusDeJeton` dans `services/oauth.py` et `IdentifiantsOAuthAbsents` dans `routers/email.py`**, remise à `jamais` aux quatre points, plafond et compteur, client de P0. La liste de l'écran E-mail n'est pas modifiée.
- **Écran.** Appel de la relève à l'ouverture de l'écran E-mail ; « Relever » et « Relever la suite » ; « N mails pas encore examinés » ; phrase de première relève. `RELEVE_COURRIER_LIVREE` passe à vrai.
- **Données.** Écriture des propositions et de `releves_courrier`.
- **Tests à écrire en premier** (`tests/test_veille_courrier_releve.py`, fournisseurs doublés en liste blanche, **point de jeton doublé au niveau du client HTTP** comme `tests/test_b1488_jeton_mail_panne_passagere.py`, jamais le service OAuth) :
  - doublures en liste blanche : tout appel hors liste échoue ; `folder.set("INBOX", readonly=True)` appelé, aucune sélection en écriture ; Gmail en `metadata` seulement ;
  - plafond de 50, du plus ancien au plus récent ; `non_examines` exact ; filigrane après écriture ; reprise où la relève précédente s'est arrêtée ; UID inférieur ou égal au filigrane filtré ;
  - **première relève sur 80 messages dans la fenêtre** (constat 7) : les 50 plus récents examinés, `non_examines` = 0, `premiere_releve_plafonnee` vrai, phrase « avec tes 50 mails les plus récents » ; relève suivante avec 3 nouveaux : 3 examinés, `non_examines` = 0 ; même test sur Gmail ;
  - UIDVALIDITY changée sur une boîte de 5 000 messages : au plus 50 examinés, aucun de plus de 14 jours (date interne), aucun doublon ;
  - même message relu après remise à zéro du filigrane : aucune erreur, aucune ligne en double ;
  - deux relèves simultanées du même compte : une seule lecture chez le fournisseur ;
  - filigrane monotone : une écriture plus basse est ignorée ;
  - deux comptes IMAP, même UID : deux lignes distinctes ;
  - **états de compte** (constat 1) : 400 `invalid_grant` : `a_reconnecter`, aucune tentative au geste suivant ; 400 `invalid_client` : `a_reconnecter` ; **429 du point de jeton : `illisible`, retenté** ; **400 à corps HTML : `illisible`** ; **page HTML en 200 : `illisible`** ; 503 : `illisible` ; `httpx.ConnectError` : `illisible` ; identifiants OAuth absents : `a_reconnecter` ; **déchiffrement qui lève dans `ensure_valid_access_token` (401 générique) : `illisible`** ; les sous-classes gardent code et texte (`tests/test_b1488_jeton_mail_panne_passagere.py` vert sans modification) ;
  - remise à `jamais` : un test par point ;
  - serveur IMAP injoignable : `illisible`, aucune exception à l'écran ;
  - deuxième appel sous deux minutes sans `forcer` : aucune connexion ;
  - pendant une purge : 503 « relève suspendue », aucune ligne écrite après le 200 de la purge ;
  - garde du créneau fausse : le passage de `RELEVE_COURRIER_LIVREE` à vrai ne rend pas « Proposer un créneau ».
- **Critères observables.** Bout en bout (Playwright, serveur jetable 17393) : un compte doublé reçoit le mail d'un contact de projet ; ouvrir l'écran E-mail le relève ; le brief affiche la ligne, son motif et sa fraîcheur ; « Pas lié » la retire, et une réponse dans le même fil ne la ramène pas ; le client de messagerie montre toujours le mail comme non lu.

### Lot 6 : la relève de fond, facultative (après P0 et le lot 5)

Inchangé (planificateur, suspension par P0, arrêt propre, interrupteur et texte d'activation, préférence `veille_courrier`), plus : une relève de fond et une relève au geste simultanées sur le même compte ne font qu'une lecture ; un compte `illisible` est retenté au passage suivant, un compte `a_reconnecter` jamais.

### Lot 7 : recette réelle

Sur les données de démonstration, puis sur un compte Gmail et un compte IMAP réels : après relève, le client de messagerie montre les nouveaux mails comme non lus ; une réponse IMAP dans un fil écarté n'est pas reproposée ; un créneau n'est jamais posé sur une réunion récurrente locale ni sur un jour d'une série en journée entière ; sur un poste réglé sur `America/Toronto`, un rendez-vous créé à l'écran et un autre créé par le chat bloquent leur heure réelle ; un point d'accès Wi-Fi à portail captif rend le compte « illisible », pas « à reconnecter ».

### Phase 2, après usage réel

Inchangée : modèle local non « cloud » pour départager et résumer, derrière une préférence serveur ; tests « modèle `:cloud` refusé » et « Ollama arrêté : étape sautée, aucun repli ».

## 8. Ce que la V4 retire ou reporte, et pourquoi

Aucune décision de Ludo n'est réduite : les six décisions du 25/09 sont tenues telles quelles. Ce que la V3 faisait bien est gardé : moteur pur, identité et fils, tables et rétention, relève sérialisée en lecture seule, gardes en liste blanche, dépliage mesuré, lecture stricte des agendas, effacements explicites.

| Retiré ou reporté | Pourquoi |
|---|---|
| Colonne `projet_id` et son invariant (V3, 6.4) | Vrai à l'écriture seulement : une tâche change de projet (`routers/tasks.py:252-253`), un livrable aussi, par l'import CRM (`services/crm_import.py:1214`). Remplacée par une jointure à la lecture et par les identifiants que la cascade supprime réellement |
| Branche « tenir les anciennes lignes pour occupées sur toutes leurs lectures » (V3, section 2) | Aucun critère ne distingue ces lignes (`services/calendar/local_provider.py:364`, `config.py:25`), les fuseaux d'origine des ICS ne sont pas conservés, et appliquée à tout l'agenda elle bloquerait deux ou trois créneaux par rendez-vous pour toujours. Seule la phrase de réserve reste |
| Classement `a_reconnecter` sur les codes 400 et 401 (V3, 6.5) | Le 400 mêle refus et limitation de débit, le 401 mêle identifiants absents et réponse illisible. Remplacé par deux refus typés |
| Phrase « trois prérequis rendent la convention vraie pour les nouvelles écritures » (V3, section 1) | Fausse sur un poste hors de Paris tant que A-2 n'est pas corrigé |
| « Aucune écriture en base » pour « Ouvrir le mail » (V3, 6.6) | Faux pour Gmail : le jeton est renouvelé et enregistré. Remplacé par « aucune écriture métier » |
| Ancre sur « le groupe de la source » (V3, 6.6) | Ce groupe n'existe pas. Remplacée par la première ligne courrier et la levée du repli |
| Citation de `tests/test_variables.py:213` comme garde d'incrément | Vraie sur toute version autre que « 1.0 » |
| Citation de `lib/etabli.ts:27` pour le nom « E-mails » | Ce fichier nomme le verbe « Écrire un e-mail » |
| « Livraison du lot 4 après C-1 » sans mécanisme (V3, lot 4) | Remplacé par la garde `CRENEAU_LIVRE`, qui attend aussi A-2 |
| Test « une EXDATE libère son jour », test « 5 h en Martinique », phrase sur le cache Google, `routers/actions.py:164`, rétention depuis `recu_le`, lecture CalDAV par `list_events` (retraits de la V3) | Motifs de la V3, section 8, toujours valables |
| Occurrences déplacées d'une série importée | Reportées hors P-105 (section 9) |

## 9. Risques restants

- **A-2 et C-1 retardent le créneau.** Tant que l'un manque, la garde reste fausse : l'alerte existe (lot 5), le créneau non. C'est voulu : un créneau faux sur un poste hors de Paris proposerait un moment déjà pris.
- **Phrase de réserve permanente** si C-1 conclut à l'absence de conversion : elle ne disparaît jamais, faute de critère pour savoir qu'il ne reste plus d'anciennes lignes.
- **Occurrence déplacée d'une série importée** (candidat à reproduire, hors P-105). `parse_ics` rend chaque VEVENT, exceptions à RECURRENCE-ID comprises (`services/import_service.py:30-32`) ; la route d'import saute toute ligne dont l'UID existe déjà dans l'agenda (`routers/calendar.py:1940-1953`). La réunion déplacée n'est pas en base. Le même défaut touche l'écran de l'agenda.
- **Série importée d'un autre fuseau.** Dépliée à heure murale de Paris ; une réunion hebdomadaire à 10 h en Martinique décale d'une heure les semaines où Paris est à l'heure d'hiver. Le TZID d'origine n'est pas conservé.
- **Journées entières toujours bloquantes.** Un « Anniversaire de Paul » en journée entière bloque sa journée. Erreur dans le sens prudent ; un événement transparent (Google, CalDAV) n'est pas concerné.
- **Classement typé des refus.** Un fournisseur qui refuserait un jeton avec un autre code `error` que les trois retenus laisserait le compte `illisible` (retenté, jamais muet) au lieu de `a_reconnecter`. Le brief dit alors « illisible depuis … », sans dire de reconnecter ; la recette réelle (lot 7) le vérifie sur Google.
- **Divergence passagère avec l'écran E-mail** tant que A-3 n'est pas corrigé : derrière un portail captif, l'écran dit « reconnecte-toi » et le brief « illisible ». Le brief a raison.
- **Dépendance à P0.** Sans elle, pas de relève, donc pas d'alerte réelle ; les lots 1 à 4 avancent sous leurs gardes.
- **Verrou en mémoire.** Il suppose un seul processus serveur, ce qui est le cas de l'application de bureau.
- **Fatigue d'alerte, faux négatifs, fils IMAP imparfaits, fériés de métropole seulement, lecture au geste plus lente qu'un cache, charge chez les fournisseurs, sentiment de surveillance, recouvrement avec P-104** : inchangés par rapport à la V2 (section 9), mêmes parades.

## 10. Questions réservées à Ludo

Aucune. P-105 n'efface que les lignes qu'elle crée elle-même, selon la décision 4, n'annonce rien publiquement et ne touche pas à la marque.

C-1 (conversion des anciennes lignes d'agenda) modifie des données de l'utilisateur sans en effacer : elle relève de la délégation, avec une recommandation, dans son propre ticket. Si la décision prise devait effacer des événements, elle reviendrait à Ludo. A-2 et A-3 sont des défauts ordinaires, corrigés hors RFC.

## Amendements de la revue unique V4 (26/09/2026)

Verdict GO. Pas de V5 : les constats P2 de `docs/plans/revues/2026-09-26-revue-rfc-v4-p105-p106.md` s'imposent aux lots concernés, avec leurs tests, et seront vérifiés à la revue de conception de chaque lot.
