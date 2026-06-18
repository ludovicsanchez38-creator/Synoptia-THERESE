# Mail + Calendrier THÉRÈSE - quick-wins priorisés

> Audit du 18/06/2026 par panel de 3 concepteurs experts (messagerie type Superhuman/Gmail, agenda type Fantastical/Cron, interop IMAP/CalDAV + IA-natif), avec inventaire du code et vérification de faisabilité sur le code réel. Repo : `Synoptia-THERESE`.

## 1. Cadrage

Le Mail repose sur un socle solide (lecture/envoi multi-providers Gmail+IMAP, threading, cache local des corps, infra notifications in-app, support complet des pièces jointes au niveau provider). Ce qui manque, c'est surtout la couche HTTP qui expose ces capacités déjà construites (pièces jointes en envoi, résumé de fil) et les automatismes de productivité (snooze, send-later, triage en lot).

Le Calendrier a une vue semaine/jour fonctionnelle, le PUT /events et @dnd-kit déjà présents, et une infra de rappels in-app, mais il souffre de manques structurels qui trahissent la confiance dans l'agenda (plage horaire codée en dur qui masque des RDV, occurrences récurrentes non dépliées) et de l'absence de gestes natifs (RSVP, notifications OS, création depuis un mail).

## 2. Top quick-wins (à faire d'abord)

Tri par rapport valeur/effort (impact H et effort le plus faible en tête).

| # | Fonctionnalité | Zone | Valeur pour l'utilisateur | Effort | Impact | Fichiers clés |
|---|---|---|---|---|---|---|
| 1 | Résumer ce fil / mes mails (IA locale) | Mail | Comprendre un long échange en 3 lignes avant de répondre, 100% local | M (vrai quick-win) | H | `services/workspace_tools.py`, `routers/email.py`, `tests/test_routers_email.py` |
| 2 | Plage horaire agenda adaptative | Calendrier | Plus aucun RDV ne disparaît hors 8h-20h ; confiance restaurée | S (option dynamique) | M | `components/calendar/CalendarView.tsx` |
| 3 | Envoi de pièces jointes (câblage HTTP) | Mail | Envoyer devis/facture/contrat en PJ sans repasser par Gmail | M (~4-6h) | H | `models/schemas_email.py`, `routers/email.py`, `services/gmail_service.py`, `frontend .../email.ts` + `EmailCompose.tsx` |
| 4 | Notif OS email (Tauri, périmètre réduit) | Mail | Être prévenu d'un nouveau mail app fermée | S (email seul) | H | `src-tauri/Cargo.toml`, `frontend package.json`, `EmailPanel.tsx`, `notification_service.py` |
| 5 | Créer un événement depuis un email | Both | RDV négocié par mail devient un clic au lieu d'une double saisie | M (bouton+.ics S, extraction NL ~1-2h) | H | `components/email/EmailDetail.tsx`, `routers/email.py`, `routers/calendar.py`, `services/workspace_tools.py` |
| 6 | RSVP invitation (accepter/refuser/peut-être) | Calendrier | Gérer ses RDV clients de bout en bout sans rouvrir Gmail/Outlook | M | `routers/calendar.py`, `services/calendar/*_provider.py`, `EventDetail.tsx` |
| 7 | Templates / snippets de réponse | Mail | Réutiliser ses formulations récurrentes (devis, prise de contact) | S (à confirmer) | M | inventaire, non encore chiffré |
| 8 | Quick-add langage naturel (compléter) | Calendrier | "RDV Dupont jeudi 14h" crée l'événement | M (à confirmer) | M | `routers/calendar.py`, `EventForm` |

Note honnête : seul le #1 est un vrai quick-win confirmé par l'audit code. Les #2 et #4 sont des quick-wins partiels (variante réduite). Les autres sont des "petits chantiers" courts (M), pas des items d'une heure.

## 3. Mail (top 5)

1. **Résumer ce fil / mes mails (IA locale)** - Le manque : aucun résumé de fil n'existe. La solution : ajouter `SUMMARIZE_THREAD_TOOL` à `WORKSPACE_TOOLS`, récupérer les messages du thread (déjà en cache `body_plain`/`body_html`), les envoyer au LLM déjà branché (`generate_content`). Geste : un seul appel async supplémentaire via `_get_email_provider` (le pattern existe déjà dans `_read_emails`), 100% local-first. C'est le meilleur ratio du lot.

2. **Envoi de pièces jointes** - Le manque vérifié : tout le lourd est fait côté provider (IMAP complet, DTO, champs DB), mais `SendEmailRequest` (schemas_email.py:97) n'a aucun champ `attachments` et `gmail_service.send_message()` n'assemble pas de MIME multipart pour des PJ. La solution : ajouter `attachments` au schéma, passer l'endpoint POST en multipart/form-data, câbler `request.attachments` aux deux providers. Geste : re-signature de l'endpoint + assemblage MIME, compter ~4-6h avec tests pour Gmail et IMAP.

3. **Notification OS d'un nouveau mail** - Le manque : il y a des notifications in-app + SQLite avec polling, mais zéro notification OS native (aucune dépendance Tauri, aucun code Rust/frontend). La solution version réduite : ajouter `tauri-plugin-notification` et ne brancher d'abord que le mail entrant (S). Geste : déclarer la lib (Cargo.toml + package.json), brancher l'événement nouveau mail. La version complète email+agenda avec permissions et tests 3 OS reste un M.

4. **Templates / snippets** - Le manque (inventaire, status missing, à confirmer) : pas de réponses préenregistrées. La solution probable : une petite table `EmailTemplate` + un sélecteur dans `EmailCompose.tsx`. Geste : CRUD simple, pas de provider à toucher, estimation S (à confirmer après lecture du store email).

5. **Snooze (reporter un email)** - Le manque : inexistant. La solution : labels `SNOOZED` custom + un job qui remet en INBOX à l'échéance. Honnêtement ce n'est pas un quick-win (effort L, voir chantiers) : Gmail n'a pas de snooze natif, il faut un scheduler, la gestion timezone et l'UI date. Je le cite ici comme la fonctionnalité Mail à plus forte valeur (impact H) à planifier juste après les quick-wins.

## 4. Calendrier (top 5)

1. **Plage horaire adaptative** - Le manque vérifié : `WEEK_START_HOUR=8`/`WEEK_END_HOUR=20` et `DAY_START_HOUR=6`/`DAY_END_HOUR=22` sont codés en dur dans CalendarView.tsx, donc tout RDV hors plage disparaît. La solution rapide (S) : calculer dynamiquement min/max des événements de la semaine affichée, avec défaut 8h-20h. Geste : remplacer les constantes par un calcul sur les events rendus. La version "réglage utilisateur dans les préférences" est plus flexible mais bute sur un bug réel (voir ci-dessous), donc à reporter.

2. **RSVP à une invitation** - Le manque : zéro existant, et `base_provider.py` n'expose pas `respond_event()`, les attendees n'ont pas de champ statut. La solution : route POST `/events/{id}/respond` (Google via `attendees[].responseStatus`, CalDAV via PARTSTAT + .ics METHOD:REPLY) + 3 boutons dans `EventDetail.tsx`. Geste : enrichir le DTO attendees, implémenter par provider, migration DB. Effort M, fort impact métier (gestion RDV clients sans rouvrir Gmail).

3. **Créer un événement depuis un email** (synergie mail+calendrier, différenciateur) - Le manque : pas de pont mail vers agenda. La solution : bouton "Ajouter à l'agenda" dans `EmailDetail.tsx` qui pré-remplit `EventForm`. Geste : bouton + détection PJ .ics = 15 min ; l'extraction NL (titre/date/participant depuis le corps) via dateparser+regex ou appel LLM = 1-2h. Point de vigilance : pas d'endpoint GET attachment Gmail, ce qui bloque le flow .ics intégré tant qu'on ne l'ajoute pas.

4. **Notification OS pour les rappels d'événement** - Le manque : l'infra in-app existe (NotificationCenter, store, service) mais les reminders ne sont jamais persistés côté `CalendarEvent` et aucun plugin Tauri OS n'est configuré. La solution : persister les reminders (migration Alembic), scheduler léger qui lève une notif X minutes avant `start`. Geste : migration DB + Cargo.toml + init Rust + scheduler. Effort M, pas quick.

5. **Quick-add langage naturel (compléter)** - Le manque (inventaire, status partial, à confirmer) : un quick-add existe partiellement (Google quick-add) mais limité et pas viable local/CalDAV. La solution : réutiliser le parser NL de l'item 3 pour une saisie texte unique. Geste : factoriser l'extracteur NL, estimation M (à confirmer).

## 5. Plus gros chantiers (à planifier, pas quick-win)

- **Send-later (programmer un envoi)** - effort M-L : table `ScheduledEmail`, endpoint dédié, et surtout un mécanisme de flush qui n'existe pas en archi (ni APScheduler ni Celery). Bloqué par l'absence de scheduler.
- **Snooze email** - effort L (3-5 jours) : émulation par labels, scheduler, modal date, gestion timezone, croisement avec l'INBOX.
- **Triage clavier en lot** - effort L : zéro infra batch (pas de `selectedIds` en store, pas d'endpoint batch, pas d'abstraction Gmail/IMAP lot). Piège quota Gmail batchModify (1/msg) et boucle IMAP.
- **Expansion des occurrences récurrentes** - effort L (impact H pourtant) : `GET /events` renvoie la RRULE brute, il faut déplier les occurrences (dateutil.rrule) avec tous les edge cases (UNTIL, COUNT, exceptions, fuseaux) + tests.
- **Clic créneau vide + glisser-déposer** - effort L : PUT /events et @dnd-kit existent mais WeekView/DayView utilisent du positionnement absolu sans DndContext, refactor requis, zéro test drag-drop actuel.
- **Notifications OS complètes 3 OS** (email + agenda, permissions, tests) - infra Tauri à poser proprement.
- **Liens de prise de RDV / disponibilités** - inventaire status missing (à confirmer), chantier infra côté serveur (génération de créneaux, page publique).
- **Infra transverse prérequise** : un scheduler/background-task (APScheduler ou équivalent). Il débloque d'un coup send-later, snooze ET les rappels OS. C'est le vrai investissement structurant.

## 6. Reco de séquence

1. **Résumer ce fil (IA local)** d'abord. Meilleur ratio valeur/effort de tout le lot, vrai quick-win confirmé sur le code, et c'est exactement le différenciateur "IA souveraine" de THÉRÈSE pour un solopreneur. Tu livres une fonctionnalité visible sans toucher à l'architecture.

2. **Plage horaire adaptative (version dynamique)** ensuite. Effort S, mais corrige un défaut de confiance grave : aujourd'hui un RDV à 7h ou 21h est invisible. Un agenda qui cache des RDV, c'est un agenda qu'on n'ose plus utiliser. À faire vite parce que c'est un bug perçu, pas juste un manque.

3. **Envoi de pièces jointes**. C'est le manque Mail le plus demandé en usage réel (devis, facture, contrat) et le gros du travail est déjà fait côté provider. Avant de le lancer, corrige le petit bug adjacent : le frontend appelle POST /preferences mais seuls GET, PUT/{key} et DELETE/{key} existent (vérifié dans config.py). Ça t'évitera de buter dessus quand tu voudras exposer le réglage de plage horaire en préférence.

4. **Créer un événement depuis un email**. Une fois résumé + PJ en place, c'est la synergie qui rend THÉRÈSE différente d'un client mail et d'un agenda côte à côte. Commence par la version simple (bouton + détection .ics), ajoute l'extraction NL dans un second temps.

5. **En parallèle, pose la décision d'infra scheduler**. Tant qu'il n'existe pas, send-later, snooze et rappels OS resteront bloqués. Choisir APScheduler maintenant (léger, local, sans dépendance cloud, cohérent avec le local-first) débloque trois fonctionnalités à forte valeur d'un seul investissement. C'est le point de bascule entre "quick-wins cosmétiques" et "vraie productivité".

---

### Bugs réels confirmés au passage (vérifiés sur le code)
- `POST /preferences` appelé par le frontend mais absent du backend (config.py : seuls GET, PUT/{key}, DELETE/{key}).
- `SendEmailRequest` sans champ `attachments` (schemas_email.py:97-105) -> envoi de PJ impossible via HTTP.
- Plages horaires codées en dur (CalendarView.tsx:261-263 et 495-497) -> événements hors 8h-20h (semaine) / 6h-22h (jour) invisibles.

### Méthode
Panel 3 experts + inventaire code + vérification faisabilité par agent adversarial sur chaque proposition (déjà présent ? effort réel ? fichiers ?). 23 propositions -> 22 uniques -> 12 non déjà présentes (7 quick-wins S/M + 5 chantiers L).
