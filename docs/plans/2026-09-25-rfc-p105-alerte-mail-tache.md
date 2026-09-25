# RFC P-105 : alerte proactive, un mail client rapproché du travail en cours et un créneau pour le traiter

Rédigé le 25/09/2026. Proposition S5 de Dr_logic-3D, acceptée par Ludo le 25/09 dans un périmètre précis : **V1 en lecture seule** (rapprochement d'un mail entrant avec un livrable ou une tâche en cours, alerte avec son contexte, aucune action automatique), design challengé avant le code. Aucun code avant la validation de ce document.

Chemins relatifs à `src/backend/app/` (serveur) et `src/frontend/src/` (interface), sauf mention contraire.

## 1. Le besoin

Dr_logic-3D, testeur alpha, sur Discord (fil du 25/09, 03:35 à 04:29) :

- Un client écrit au sujet d'un travail en cours. Le testeur résume ce qu'il attend : « Thérèse le reçoit, le lit, fait le rapprochement avec la tâche en cours et t'alerte ».
- Il veut **suivre le déroulement sans forcément agir** : être prévenu, pas qu'on réponde à sa place.
- Second volet : proposer un **créneau libre** pour traiter ce mail avant l'échéance. Le portail formule le même besoin « avant un rendez-vous ». La conception couvre les deux lectures (section 4.4).

## 2. Ce qui existe déjà

### Points d'appui

- **Lecture des e-mails, au geste seulement.** La liste est lue chez le fournisseur à l'ouverture de la vue Courrier : Gmail en `format='metadata'`, cinq appels en parallèle (`routers/email.py:935-999`), IMAP par `imap_tools` (`routers/email.py:1002-1122`). Le cache local `EmailMessage` ne reçoit que les messages ouverts ou classés (`routers/email.py:1186-1281` et `1733-1835`).
- **Aucune relève de fond.** Le serveur ne lance que trois tâches de fond : nettoyage OAuth, notifications horaires, purge RGPD quotidienne (`main.py:341-383`). La règle écrite la plus proche est « Jamais de sync automatique sans consentement » (`docs/rules/RULES-DONNEES.md:227`). Aucune décision plus précise n'a été trouvée.
- **Du mail à la fiche.** `get_crm_contact_by_email` compare sans tenir compte de la casse et refuse l'ambiguïté : deux fiches pour une adresse, aucun rattachement (`routers/email.py:192-214`). `EmailMessage.contact_id` existe (`models/entities.py:430`) et se pose à la main par `PUT /messages/{id}/link-contact` (`routers/email.py:2043`). `services/email_contact_matcher.py:16` fait la même recherche sans ce garde-fou et n'a aucun appelant.
- **De la fiche au travail.**
  - Projet : `Project.contact_id` et `Project.status` (active, completed, on_hold) (`models/entities.py:89-90`).
  - Tâche : `Task.status`, `due_date`, `project_id`, `contact_id` (l.560 à 566).
  - Livrable : `Deliverable.project_id`, `status` (a_faire, en_cours, en_revision, valide) et `due_date` (l.883 à 887). Un livrable n'a pas de contact : le chemin passe toujours par le projet.
- **Notions voisines.**
  - La relance est une date posée, contacts archivés exclus (`services/relances.py:27-51`, l.46).
  - Le suivi d'un mail est `EmailFollowUp` (`models/entities.py:930`, `routers/follow_ups.py:49-80`).
  - Le classement de priorité est déterministe et reconnaît les newsletters et les promotions (`services/email_classifier_v2.py:163`).
- **Brief du jour, seule surface d'attention vivante.** Il a cinq sources (`components/prototype/prototypeReadModels.ts:215-228`). Chacune est nommée dans `indisponibles` quand sa lecture échoue (`routers/dashboard.py:383`, `421`, `465`, `504`, `512`). Un plafond serveur (`routers/dashboard.py:264`) complète un compteur de ce qui n'est pas affiché (B-425, `prototypeReadModels.ts:200`). Décision de Ludo du 16/07 : le brief se limite aux vrais points d'attention (`prototypeReadModels.ts:179-184`).
- **Horaires ouvrés.** `WorkCalendar` du planning PERT : lundi à vendredi, 9 h à 12 h et 14 h à 18 h, fuseau de Paris (`services/planning.py:168-216`). Les événements sont en cache dans `CalendarEvent` (`models/entities.py:508`), avec leurs participants (l.528), et se relisent par `POST /api/calendar/sync` (`routers/calendar.py:1751`).
- **Confirmation.** Tout outil hors lecture passe par une carte (`services/tool_confirmations.py:33-49`, classes d'effet `services/contexte_execution.py:26-60`).
- **Contenu non fiable.** `sanitize_for_context` neutralise les marqueurs forgés (`services/prompt_security.py:216`, doctrine BUG-148).

### Manques

- **Aucun rapprochement** entre un mail et un projet, une tâche ou un livrable. **Aucune notion de « travail en cours »** : seuls les statuts `in_progress` et `en_cours` s'en approchent. P-104 (fil de travail) portera plus tard cette notion.
- **Aucun calcul de créneau libre** dans le dépôt.
- **La table `notifications` n'a plus de surface.** Le générateur horaire l'alimente toujours (`services/notification_service.py:293-316`, lancé par `main.py:345-364`). L'interface n'appelle plus jamais `listNotifications` (`services/api/notifications.ts:26`) depuis le retrait de la cloche le 16/07 (commits `628d672f` puis `31ec0a3f`).
- **Le consentement cloud vit dans l'interface seule** (`lib/consent.ts:44-67`, stockage local du navigateur). Le serveur n'en voit rien : une tâche de fond ne peut pas savoir si un envoi en ligne est permis.
- `EmailAccount.last_sync` existe mais n'est jamais écrit (`models/entities.py:375`).

### Préalable découvert en lisant le code

**Lister une boîte IMAP marquerait les messages comme lus sur le serveur.**

- `services/email/imap_smtp_provider.py:355` appelle `mailbox.fetch(criteria, reverse=True, limit=…)` sans `mark_seen`.
- Dans `imap_tools` 1.11.1, `mark_seen` vaut `True` par défaut et produit une lecture `BODY[]` au lieu de `BODY.PEEK[]` (`imap_tools/mailbox.py:171` et `191`).
- Ouvrir la vue Courrier marquerait donc lus jusqu'à 51 messages chez le fournisseur, corps complets téléchargés.

À reproduire sur un vrai compte, puis à ficher. Pour P-105, c'est bloquant : une relève qui ferait disparaître les « non lus » du client de messagerie trahirait la promesse de lecture seule.

## 3. Trois options

| | A. Au geste, règles déterministes | B. A, plus une relève périodique facultative | C. Tout confier au modèle |
|---|---|---|---|
| Idée | Le rapprochement tourne quand on ouvre le Courrier ou qu'on appuie sur « Relever » dans le brief | Même moteur, lancé aussi toutes les 30 min quand l'utilisateur l'a activé | Chaque mail entrant est lu par le modèle, qui décide s'il concerne un travail |
| Pour | Aucune activité de fond, aucune donnée ne sort, chaque alerte s'explique en une ligne | Répond au « t'alerte » du testeur avec le même code que A | Rattrape les formulations indirectes |
| Contre | Pas proactif : rien n'arrive si l'on n'ouvre rien | Nouvel écrivain de fond (purge, restauration), jetons OAuth rafraîchis en fond, charge réseau | Consentement cloud illisible côté serveur, coût et latence sur une machine modeste, injection de prompt, faux positifs inexplicables |
| Effort | Moyen | Moyen, plus un lot | Moyen, risque élevé |

## 4. Recommandation : A puis B dans la V1, le modèle en phase 2 et en local

### 4.1 Le rapprochement : des règles d'abord, dans cet ordre

Le moteur est une fonction pure `rapprocher(entete, index)`, sans réseau ni base. L'index (adresses connues, projets actifs, tâches et livrables ouverts) est construit une fois par relève.

| Rang | Règle | Niveau | Motif affiché |
|---|---|---|---|
| 1 | Le fil est déjà rattaché (même `thread_id`, rattachement confirmé) | sûr | « suite du fil rattaché à Refonte du site » |
| 2 | Expéditeur = contact d'une tâche ouverte (`Task.contact_id`) | sûr | « Mme Durand, contact de la tâche Maquettes » |
| 3 | Expéditeur = contact d'un projet actif qui n'a qu'un travail en cours | sûr | « contact du projet Refonte, livrable Maquettes en cours » |
| 4 | Expéditeur = contact d'un projet actif qui a plusieurs travaux en cours | probable | les trois premiers, « lequel ? » |
| 5 | Nom d'un projet actif ou d'un livrable en cours cité dans l'objet | probable | « l'objet cite Refonte du site » |
| 6 | Même domaine que le contact d'un projet actif, hors domaines grand public | à confirmer | « même société que Mme Durand » |

Garde-fous :

- **Adresse.** Elle est normalisée (minuscules, espaces retirés). Deux fiches pour une même adresse : aucun rattachement. Contacts `archive` exclus, comme pour les relances.
- **Mention de projet.**
  - Accents repliés (`services/memory_tools.py:902`) et frontière de mot : « Site » ne trouve pas « Situation ».
  - Nom de quatre lettres au moins ; les mots trop courants (« site », « devis », « projet ») ne déclenchent rien.
  - L'objet seulement : le corps n'est pas lu en V1.
- **Domaine.** Une liste fermée de domaines grand public (gmail.com, outlook.fr, orange.fr, etc.) n'est jamais utilisée pour la règle 6.
- **« En cours » en V1.** Tâches `todo` ou `in_progress`, livrables `a_faire`, `en_cours` ou `en_revision`, d'un projet `active`. Les `in_progress` et `en_cours` passent devant (question 2). Le moteur reçoit cette définition en paramètre, pour suivre P-104 plus tard.
- **Messages écartés.** Les mails de l'utilisateur lui-même, les messages portant `List-Id` ou `Auto-Submitted`, et les newsletters et promotions du classeur existant.
- **Un rapprochement est une proposition.** Il ne pose jamais `EmailMessage.contact_id` : c'est le bouton « Oui, c'est lié » qui le fait.

### 4.2 L'alerte : où elle s'affiche, comment la faire taire

**Où elle s'affiche.**

- **Dans le brief du jour**, comme sixième source « Courrier », avec la clé `courrier` dans `indisponibles`. Même doctrine que B-051 : un compte illisible n'est pas une boîte vide.
  - Une ligne par travail, pas par mail : « 2 mails de Mme Durand sur Refonte du site · livrable Maquettes, échéance jeudi ».
  - Le motif du rapprochement (tableau 4.1) s'affiche toujours.
- **Sur la vue du projet et la liste des livrables** : une pastille « mail récent » sur l'objet rapproché.
- **Ni cloche ressuscitée, ni notification système en V1.** Aucun greffon de notification n'est installé (`src/frontend/src-tauri/Cargo.toml:20-31`). Voir la question 6.

**Actions sur l'alerte.**

- « Ouvrir le mail ».
- « Vu » : la ligne sort du brief et reste dans l'historique du projet.
- « Pas lié » : la ligne est écartée, et ce fil n'est plus jamais proposé pour ce travail.
- « Taire » : ce projet ou cet expéditeur, pour 7 jours ou jusqu'à réactivation.
- Un interrupteur général dans Paramètres, désactivé par défaut.

**Plafond et mode démo.** Cinq lignes « Courrier » au plus dans le brief, le reste en compteur. En mode démo, expéditeurs et objets passent par `useDemoMask`.

**Pourquoi des tables dédiées plutôt que `notifications`.** La table existante n'a ni lien structuré (un `action_url` texte), ni vraie clé de dédoublonnage (une fenêtre de temps sur `action_url`, `services/notification_service.py:133-142`), ni surface. Deux nouvelles tables :

- `rapprochements_courrier`.
  - Contenu : compte, identifiant et fil du message, date de réception, contact, projet, cible (tâche ou livrable) et son identifiant, règle, niveau, statut (nouveau, vu, confirmé, écarté), dates.
  - Unicité sur le triplet compte, message, cible.
  - **Ni objet ni extrait** : l'affichage relit le cache `EmailMessage`, rempli pour les seuls messages rapprochés.
- `silences_courrier` : type (projet, expéditeur, fil), valeur, date de fin.

### 4.3 La charge : au geste d'abord, la relève périodique en option

- **Un seul chemin** : `POST /api/veille-courrier/relever?account_id=`. Il lit les en-têtes de la boîte de réception depuis le filigrane (`EmailAccount.last_sync`, enfin écrit), 50 messages au plus. Il applique les règles et écrit les propositions.
- **Au geste** : à l'ouverture de la vue Courrier, et par le bouton « Relever » du brief.
- **Périodique (lot 6), désactivée par défaut.**
  - Une préférence serveur `veille_courrier` (active, intervalle de 30 min, comptes concernés).
  - L'écran d'activation la pose après un texte clair : « Thérèse lit les en-têtes de tes nouveaux mails toutes les 30 minutes, tant que l'application est ouverte. Rien n'est marqué lu, rien n'est envoyé. »
  - Cette préférence vaut consentement, et le serveur peut la lire.
- **Lecture sans effet chez le fournisseur** : Gmail en `metadata` ; IMAP en `headers_only=True` et `mark_seen=False`.
- **Planificateur.** Il est calqué sur celui des notifications (`main.py:345-364`), absent sous `THERESE_SKIP_SERVICES` et annulé à l'arrêt. Il est **suspendu pendant une purge ou une restauration** (chantier « mise au repos des écritures de fond » du 25/09). Sans cela, la promesse I1 de la purge tombe.
- **Jeton OAuth qui ne se rafraîchit plus.** Le compte est marqué « à reconnecter » une seule fois, sa relève s'arrête, et le brief le nomme dans `indisponibles`. Pas de nouvelle tentative à chaque cycle.

### 4.4 Le créneau libre

- **Calcul.** Une fonction pure `creneaux_libres(evenements, de, jusqua, duree, calendrier)` travaille sur le cache `CalendarEvent` (tous les agendas, hors événements annulés) et sur les horaires de `WorkCalendar`.
- **Horizon.** C'est l'échéance de la tâche ou du livrable, ou le prochain rendez-vous avec ce contact s'il est plus proche. Les deux formulations du besoin sont couvertes.
- **Sans échéance ni rendez-vous, aucun créneau n'est proposé.** Une date inventée est pire qu'une date absente (`services/echeances.py:26-31`).
- **Durée et nombre.** Une heure par défaut, modifiable dans la carte (30 min, 1 h, 2 h). Trois créneaux au plus, le plus tôt d'abord.
- **Journées entières considérées comme occupées.** Mieux vaut un créneau de moins qu'un créneau posé un jour de congé.
- **Dates.** Fin inclusive (BUG-144) ; dates naïves ramenées en UTC (BUG-126, `services/notification_service.py:25-32`).
- **Fraîcheur dite** : « d'après ton agenda relu à 10 h 42 », avec un bouton « Relire l'agenda ».
- **Aucun créneau libre avant l'horizon** : « Aucun créneau d'une heure avant jeudi 18 h. » Jamais un créneau après l'échéance présenté comme une solution.
- **Réservation.** « Réserver ce créneau » ouvre la création d'événement préremplie (titre, projet), qui passe par la confirmation existante.

### 4.5 Ce qui ne part jamais sans confirmation

Automatique, et seulement cela : lire des en-têtes sans les marquer lus, calculer, écrire une proposition locale.

Toujours au clic de l'utilisateur :

- répondre, créer un brouillon, transférer ;
- marquer lu ou non lu, étoiler, classer, déplacer, supprimer ;
- rattacher le mail à une fiche ;
- changer le statut ou l'échéance d'une tâche ou d'un livrable ;
- créer une relance ;
- réserver un créneau ;
- envoyer quoi que ce soit à un modèle en ligne.

Un test de garde (section 6) vérifie que la relève n'appelle jamais les méthodes d'écriture des fournisseurs.

### 4.6 Confidentialité et modèle

- **V1 sans modèle.** Les règles suffisent au cas du testeur et s'expliquent en une ligne.
- **Phase 2 : modèle local seulement**, derrière une préférence serveur, sur le modèle de `auto_extract_entities` (`routers/chat.py:964`).
  - Rôle : départager plusieurs travaux candidats, et résumer en une ligne « ce qui est demandé ».
  - Le corps n'est lu que pour les mails déjà rapprochés, et passe par `sanitize_for_context`.
  - Aucun outil. La réponse est un JSON dont les identifiants doivent appartenir à la liste fournie : tout autre identifiant est rejeté.
  - Ollama arrêté : l'étape est sautée, jamais de repli en ligne (B-1071, `services/llm.py:832-840`).
- **En ligne : jamais en fond.** Le serveur ne voit pas le consentement v2. L'analyse en ligne reste un geste : « Analyser dans le chat » ouvre une conversation, qui applique l'accord `llm` du fournisseur comme aujourd'hui. Une analyse en ligne en fond exigerait une nouvelle finalité (« veille du courrier ») recopiée côté serveur : hors V1.
- **Honnêteté du discours.** En V1, Thérèse lit les en-têtes, pas le mail, et l'écran le dit. « Thérèse le lit » ne devient vrai qu'en phase 2.

## 5. Livraison proposée (après validation), en TDD

0. Design court et revue adverse du design. Correctif IMAP : lecture `BODY.PEEK` en liste, `headers_only` pour la relève, test rouge d'abord.
1. Moteur de rapprochement (fonction pure) : une règle, un test.
2. Tables, migration Alembic, export, import, purge RGPD, restauration, suppression et anonymisation d'une fiche. Tout cela dès ce lot, pas après (leçon de P-104).
3. Route de relève au geste, filigrane, cache minimal des messages rapprochés, clé `indisponibles`.
4. Brief (sixième source), actions « Vu », « Pas lié » et « Taire », pastille sur le projet, masque démo, lexique.
5. Créneau libre : fonction pure, carte, réservation par la confirmation existante.
6. Relève périodique facultative : préférence, écran d'activation, planificateur, mise au repos, jetons.
7. Recette sur les données de démonstration, puis sur un compte Gmail et un compte IMAP réels.

Phase 2, après usage réel : modèle local et ligne « ce qui est demandé ».

Chaque lot fait l'objet d'un commit, avec sabotage des tests (ciblé par fonction, jamais par chaîne globale) et revue adverse du diff.

## 6. Plan de tests

**Moteur (pytest, fonction pure).** Un test par règle, chacun saboté :

- expéditeur exact, casse et espaces ; deux fiches pour une adresse, aucun rattachement ; contact `archive`, aucun ;
- projet `completed` ou `on_hold` ignoré ; tâche `done` ou `cancelled` ignorée ; livrable `valide` ignoré ;
- plusieurs travaux en cours : niveau « probable » et liste bornée à trois ;
- « Réfection » trouve « refection » ; « Site » ne trouve pas « Situation » ; un nom de trois lettres ou un mot courant ne déclenche rien ;
- `gmail.com` jamais utilisé comme domaine ; un domaine de société donne « à confirmer » ;
- fil déjà rattaché hérité ; fil écarté jamais reproposé ; silence respecté, puis levé à sa date ;
- mails de l'utilisateur, `List-Id`, `Auto-Submitted` et newsletters écartés.

**Relève (pytest, fournisseurs doublés).**

- Zéro appel à `send_message`, `create_draft`, `modify_message`, `move_message`, `delete_message` (espions).
- IMAP appelé avec `mark_seen=False` et `headers_only=True` ; Gmail en `metadata`.
- Plafond de 50. Le filigrane n'avance qu'après succès. Deux relèves ne créent aucune ligne en double.
- Compte en panne : `courrier` apparaît dans `indisponibles`, aucune exception ne remonte. Jeton non rafraîchissable : compte marqué une fois, relève arrêtée.
- Planificateur absent sous `THERESE_SKIP_SERVICES`, et suspendu pendant une purge : aucune ligne écrite après le 200.

**Créneaux (pytest, fonction pure).**

- Semaine type ; week-end ; journée entière bloquante ; événement de plusieurs jours à fin inclusive ; dates naïves ; événement annulé ignoré.
- Échéance passée ou absente : aucun créneau. Horizon ramené au prochain rendez-vous du contact.
- Passage à l'heure d'hiver du 25/10/2026.
- Aucun créneau disponible : phrase dédiée, jamais un créneau après l'échéance.

**Données.** Export, import, purge et restauration contiennent les deux tables. Supprimer ou anonymiser une fiche retire ses rapprochements.

**Interface (vitest).**

- Sixième source du brief et son état indisponible.
- Actions « Vu », « Pas lié » et « Taire » ; plafond et compteur.
- Masque démo ; lexique vérifié (`lexiqueTitres.test.ts`).
- « Réserver ce créneau » ouvre la confirmation sans rien créer.

**Bout en bout (Playwright, serveur jetable 17393).** Un compte doublé reçoit le mail d'un contact de projet. Le brief affiche la ligne et son motif. « Pas lié » la retire pour de bon.

**Recette humaine.** Sur un compte Gmail et un compte IMAP réels, après une relève, le client de messagerie montre toujours les nouveaux mails comme non lus.

## 7. Risques

- **Fatigue d'alerte.** Trop de lignes, et l'utilisateur coupe tout. Parades : une ligne par travail, plafond, « Pas lié » définitif, V1 sans modèle.
- **Faux négatifs.** Un client qui écrit depuis une adresse personnelle ou celle d'un collègue passe inaperçu. L'écran dit que le rapprochement repose sur les adresses connues.
- **Homonymes et noms courts.** La règle 5 ne dépasse jamais le niveau « probable ».
- **Écriture de fond.** La relève périodique est un nouvel écrivain de fond. Sans la mise au repos, la purge RGPD perd sa promesse I1.
- **Jetons et charge.** Rafraîchissements OAuth en fond, quotas Gmail, serveurs IMAP lents, machines modestes. Parades : plafond, délais bornés, règles seulement en V1.
- **Agenda périmé.** Un créneau calculé sur un cache ancien peut être déjà pris. Parades : fraîcheur affichée, réservation repassée par la confirmation.
- **Sentiment de surveillance** (« Thérèse lit mes mails en douce »). Parades : désactivé par défaut, texte d'activation explicite, en-têtes seulement.
- **Recouvrement avec P-104.** Quand le fil de travail existera, « en cours » devra le suivre. La définition est un paramètre du moteur.

## 8. Décisions attendues de Ludo

1. **Relève périodique** facultative dès la V1 (lot 6), désactivée par défaut ? Recommandation : oui.
2. **« En cours »** : tout ce qui est ouvert dans un projet actif, les `in_progress` et `en_cours` en tête ? Recommandation : oui.
3. **Rattachement par domaine** de société, au niveau « à confirmer » ? Recommandation : oui, hors domaines grand public.
4. **Horizon du créneau** : le plus proche entre l'échéance et le prochain rendez-vous du client ? Recommandation : oui.
5. **Heures de disponibilité** : celles du planning (9 h à 12 h, 14 h à 18 h, en semaine), ou un réglage ?
6. **Phase 2** : modèle local seulement, l'analyse en ligne restant un geste dans le chat ? Recommandation : oui.
7. **Table `notifications`**, alimentée chaque heure sans surface depuis le 16/07 : la laisser, la retirer ou la rebrancher (hors P-105) ?
