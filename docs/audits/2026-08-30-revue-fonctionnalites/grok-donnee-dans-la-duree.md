# Revue Grok — la donnée dans la durée (30/08/2026, seconde passe)

> Angle : migrations, persistance, accumulation, références mortes, dates et
> fuseaux, aller-retour export/import. Orthogonal à la première passe, qui ne
> regardait qu un appel isolé à un instant.

Je vais d’abord recaler le périmètre : rapports de la première passe, historique git récent, puis les jonctions de schéma (migrations, persistance, liens morts) que ces deux angles ne pouvaient pas voir.Le mois est chargé côté métier (relances, prestations, traces, cloison agenda). Je vais croiser ça avec les migrations et les suppressions, là où un schéma qui a bougé laisse des données orphelines.Deux systèmes de schéma coexistent : Alembic et des `ALTER TABLE` ad hoc dans `database.py`. C’est exactement le genre de jonction que la première passe ne voyait pas.Je commence par le schéma actuel, les ALTER ad-hoc et lesJe commence par cart migrations Alembic pour voirographier l où ils’état processus divergent, les fichiers. qui s’accumulent, l’import/export et le traitement des dates.Je lis le reste des ALTER ad-hoc et je sors les champs desJe modèles pour les commence comparer. par cartographier les suppressions, les FK et les lectures qui restent après un delete.Je lis le modèle d'entités et les handlers de suppression des objets métier.Je compare les colonnes du modèle aux ALTER réellement appliqués au démarrage, et je vérifie le stamp Alembic.Les FK SQLite ne sont pas activées : je vérifie le ménage applicatif et les lectures qui restent après.Voici ce qui tient vraiment, en durée. Le reste (circuit breaker, confirmations d’outils, MCP en vol, embeddings en RAM) est du processus : perdu au redémarrage, et c’est voulu.

---

## Finding 1 (grave) — Les prestations n’existent ni pour l’export JSON, ni pour l’oubli, ni pour « tout effacer »

La table `prestations` (29/08 : intitulé, montant HT, financeur, `fin_le`, suivi J+N) est du métier. Le commentaire d’export dit « couverture de toutes les tables utilisateur ». Le code ne la mentionne nulle part.

**Attendu** : Art. 20 exporte l’engagement ; Art. 17 et « toutes mes données » l’effacent, comme la suppression d’un contact.

**Obtenu** :

- `GET /api/data/export` (`data.py` ~191-343) n’a pas de clé `prestations`. `data_format_version: "1.2"` est déjà un mensonge.
- `DELETE /api/data/all` (`data.py` ~456-490) ne `delete` pas `Prestation`. SQLite n’a pas `PRAGMA foreign_keys` : les lignes restent, `contact_id` orphelin, montants et financeurs encore en base.
- `POST /api/rgpd/anonymize/{id}` (`rgpd.py` ~185-245) anonymise la fiche, casse projets / mails / activités, **laisse les prestations**. La suppression de contact, elle, les efface (`memory.py` 720-727). Deux bouches.

**Chemin** : fiche client → prestation avec montant et OPCO → Paramètres → exporter / anonymiser / tout supprimer.

**Reproduction** : créer une prestation, `GET /api/data/export`, chercher `"prestations"` : absent. Anonymiser le contact, `GET /api/prestations?contact_id=…` : encore là, collée à `[ANONYMISÉ]`. `DELETE /api/data/all?confirm=true` : idem.

La sauvegarde chiffrée (`therese.db` entière) **les emporte**. C’est le JSON RGPD et les deux chemins d’oubli qui mentent.

---

## Finding 2 (grave) — Restore = conversations qui promettent un fichier que le disque n’a plus

`_create_archive` (`data.py` 736-744) prend DB, Qdrant, `images/`, MCP, profil d’export, clé. **Pas `outputs/`.**

Les skills écrivent dans `~/.therese/outputs/` (`registry.py` 32-33). Le message persiste `extra_data.skill_files` (`chat.py` 2648-2656). Au redémarrage, le téléchargement **retombe sur le disque** (`skills.py` 241-247, glob `*_{8 premiers chars}.*`). Donc :

| Événement | Fichier skill |
|---|---|
| Redémarrage simple | Survît (disque + glob) |
| Restore depuis backup | Perdu. Le bouton de la bulle reste. 404. |
| Usage long | `outputs/` **sans aucune purge** (seul `delete-all` le vide) |

Les backups utilisateur n’ont **aucune rétention** (seulement `pre_restore_*`, garder 1, `data.py` 1019-1028). Chaque sauvegarde = DB + Qdrant + images, qui grossit, jamais ramassée.

**Reproduction** : générer un DOCX dans le chat, backup, restore, recliquer « Télécharger » sur l’ancien message.

Les images, elles, sont dans l’archive et survivent. Incohérence skills / images.

---

## Finding 3 (grave) — Après redémarrage, la sidebar n’a plus que 50 conversations

`useConversationSync` appelle `listConversations(50, 0)` (`useConversationSync.ts` 98). Le store persisté (`therese-chat`) avait potentiellement tout. Le merge jette les conversations **déjà synced** qui ne sont pas dans ces 50 (`116-123` : `localOnly` = `!local.synced`).

**Attendu** : l’historique SQLite est la source ; la liste UI le reflète.

**Obtenu** : SQLite garde tout. L’UI, au boot, n’affiche que les 50 plus récentes. Pas de second `offset`. La 51e est injoignable depuis la sidebar.

**Reproduction** : 51 conversations, redémarrer, compter le rail. La plus ancienne est encore en `GET /api/chat/conversations?limit=1&offset=50`, pas à l’écran.

Zustand persist **n’est pas** un filet : le sync du boot l’écrase.

---

## Finding 4 (sérieux) — Round-trip import/export : ce qui sort ne rentre pas

### Conversations

`GET /api/data/export/conversations` (`data.py` 396-418) sort `id, title, created_at, messages.{role, content, created_at}`.

`POST /api/data/import/conversations` (`data.py` 1335-1361) :

- ignore `created_at` (nouveaux timestamps) ;
- ignore `extra_data` (plus de bouton skill) ;
- ignore `provider`, tokens, `project_id`, `memory_scope` ;
- skip si l’id existe déjà (pas de fusion) ;
- régénère les ids de messages.

L’export **complet** RGPD a `extra_data` via `_export_row`. Il n’existe **aucun** import de ce JSON. Le restore, c’est l’archive `.tar.gz.enc`, pas le JSON.

### CRM

`CONTACT_COLUMNS` (`crm_export.py` 43-58) : pas de `next_follow_up`, pas d’adresse, pas d’`extra_data`, pas de RGPD. L’import (`crm_import.py` 612-625) ne les pose pas non plus.

**Reproduction** : poser une relance au 15/01, exporter CSV, réimporter sur base vide. `next_follow_up` est `null`. L’accueil ne propose plus de relancer.

VCard/ICS : import existe (`import_service.py`, `/import-ics`). Export ICS all-day convertit bien inclusive → exclusive (`calendar.py` 1553). Round-trip ICS all-day : OK (BUG-144). CSV CRM : pas OK.

---

## Finding 5 (sérieux) — « Aujourd’hui » n’est pas la même horloge partout

`GET /api/dashboard/today` (`dashboard.py` 259-263) :

```python
today = date.today()                    # civil local
today_dt = datetime.combine(today, datetime.min.time())  # minuit NAIF local
thirty_days_ago = datetime.now()        # naif local, pas UTC
```

Les relances (`relances.py` 32-37) : `Contact.next_follow_up <= datetime.now(UTC)`.

Les all-day du brief (`dashboard.py` 280-286) :

```python
CalendarEvent.all_day == True,
CalendarEvent.start_date == today_str,   # égalité sur le SEUL jour de début
```

**Attendu** : un événement « 29-31 août, toute la journée » apparaît le 30. Une relance « le 30 » est due le 30 civil, pas à 00:00 UTC.

**Obtenu** :

- All-day multi-jours : invisible dès le 2e jour. `end_date` n’est pas lu.
- Relance stockée `2026-08-30T00:00:00Z` : due dès minuit UTC (2h du matin à Paris). Le badge « en retard » du brief coupe `isoformat().slice(0, 10)` (`prototypeReadModels.ts` 35-36) contre `date.today()` local : un `…T22:00:00Z` (minuit Paris du lendemain) passe « en retard d’un jour ».
- RDV horés Google : sync `fromisoformat(dateTime.replace("Z", ""))` (`calendar.py` 685-716) **garde un offset `+02:00`**. Comparaison avec `today_dt` naif. SQLite peut renvoyer naif (ça passe, l’heure est celle de l’offset sans conversion) ou aware (TypeError avalé par le `except` L327-328 : **journée vide**).

**Reproduction all-day** : événement local toute la journée du 29 au 31. Ouvrir l’accueil le 30. Absent.

`fin_le` / `suivi_apres_jours` (`echeances.py`) : arithmétique sur `date`, pas de fuseau. Ça, c’est propre. Le trou, c’est que cette échéance n’écrit pas `next_follow_up` toute seule : sans geste, le brief ne la montre pas. Cohérent avec « une relance est une date posée », mais l’échéance Qualiopi calculée peut exister sans jamais entrer dans « à relancer ».

---

## Ce qui survit / meurt, sans étirer

**Survit au redémarrage (disque / SQLite)**  
DB `~/.therese/`, Qdrant, `mcp_servers.json`, images, `outputs/` (fichiers, pas le cache), logs rotatifs (10 Mo × 5, `logging_config.py` 214-218), préférences, brouillons d’atelier flushés (~2 s, `documents.py` 332-343 + `finally` 400-402). Traitements orphelins → `interrupted` au boot (`task_registry.py` 162-187). Terminés purgés à 30 jours (`traitements.py` 332, appelé depuis `main.py` 241-243).

**Meurt avec le process (attendu)**  
`_file_cache` (le glob disque rattrape). Circuit breaker. Confirmations d’outils (`tool_confirmations.py` 8-10, fail-safe). Générations SSE (`_active_generations`). MCP stdio. Modèle d’embeddings. Verrous d’indexation. Streaming en cours : le **texte partiel** est quand même écrit (`_persister_message_partiel`, `chat.py` 1961).

**S’accumule sans ramasse-miettes**  
`outputs/`, `images/` (sauf delete manuel / delete-all), backups `.tar.gz.enc` (sauf pre_restore), conversations/messages, mails synchronisés, `ActivityLog` (purge **manuelle** `DELETE /api/data/logs?days=90`, jamais planifiée), notifications.

**Zustand vs serveur**  
Seul le chat (et quelques prefs) persisté. Le chat persisté n’est pas la vérité : le boot le recouvre avec 50 lignes serveur. Voix locale : `localStorage` (`voice.ts`), survit, n’est pas dans le backup.

---

Si on ne corrige qu’une chose : **les prestations dans export / anonymize / delete-all**. C’est de l’argent et des financeurs qui survivent à l’oubli alors que le contact, lui, est tombé.Les FK SQLite ne sont **pas activées** (aucun `PRAGMA foreign_keys`, aucun `ondelete` dans le schéma). Tout le ménage est applicatif. Plusieurs chemins de `delete` ne passent pas par le ménage déjà écrit ailleurs. Après redémarrage, les identifiants morts restent, et plusieurs lectures mentent ou 404.

---

### 1. Suppression d’un contact en cascade contourne `delete_project` (le plus grave)

**Fichiers.** [`memory.py:687-761`](src/backend/app/routers/memory.py) vs [`memory.py:1016-1063`](src/backend/app/routers/memory.py). UI : [`MemoryPanel.tsx:202`](src/frontend/src/components/memory/MemoryPanel.tsx) appelle `deleteContactWithCascade(..., true)`.

**Attendu.** Le commentaire de `delete_project` (l. 1045-1060) : détacher les conversations, remettre `memory_scope` à `global`, appeler `retirer_racine` sinon « une racine orpheline bloquerait ce dossier pour toujours ».

**Obtenu.** `cascade=true` fait `session.delete(project)` **sans** ce ménage :

- conversations encore en `memory_scope=project` + `project_id` mort
- racine `project_sync_roots` encore active (`detachee=0`)
- fichiers `scope=project`, documents, événements agenda encore collés à l’id mort
- Qdrant : `_delete_embedding(project.id)` seulement, pas les fragments des fichiers du dossier

Le sélecteur [`ConversationProjectPicker.tsx:68-71`](src/frontend/src/components/chat/ConversationProjectPicker.tsx) ne trouve plus le projet dans `listProjects()` : il affiche l’état vide (documents généraux / toute la mémoire) pendant que le backend cloisonne encore sur l’id fantôme. C’est **exactement** le mensonge que `delete_project` avait fermé, rouvert par un autre bouton.

Même trou dans l’anonymisation RGPD : [`rgpd.py:205-226`](src/backend/app/routers/rgpd.py) détruit les projets sans `retirer_racine` ni détachement des conversations.

**Reproduction.** Contact + projet + racine sync + conversation rattachée. Vue Contacts, supprimer le contact (cascade). Redémarrer. Rouvrir la conversation : l’écran dit « généraux », le RAG ne sert plus les fichiers du dossier. Tenter de rattacher le **même** dossier à un nouveau projet : l’index unique partiel `uq_sync_root_racine_active` refuse.

---

### 2. Factures orphelines : l’écran les montre, le PDF 404, le chat les nie

**Fichiers.** [`Invoice.contact_id` NOT NULL](src/backend/app/models/entities.py) (l. 568). `delete_contact` ne touche **jamais** aux factures (l. 687-761). `Contact.invoices` est déclaré `cascade_delete=True` (l. 60) puis **écrasé** sans cascade (l. 663).

**Attendu.** Un document de facturation survit au contact, ou il est refusé à la suppression. Dans tous les cas, une lecture ultérieure ne doit pas inventer l’absence.

**Obtenu, après redémarrage :**

| Lecture | Comportement |
|---|---|
| `GET /api/invoices/` + `selectinload(Invoice.contact)` | facture encore là, `contact_name=None` |
| Vue Facturation [`InvoicesPanel.tsx:292`](src/frontend/src/components/invoices/InvoicesPanel.tsx) | titre = numéro, plus de client |
| Formulaire, `<select value={contactId}>` mort | option introuvable, champ Client vide |
| `GET /{id}/pdf` [`invoices.py:635-637`](src/backend/app/routers/invoices.py) | **404 « Contact not found »** (la facture existe) |
| `search_invoices` [`workspace_tools.py:722-723`](src/backend/app/services/workspace_tools.py) | `JOIN Contact` interne : « Aucune facture ni devis » |
| `invoice_totals` [`workspace_tools.py:697-705`](src/backend/app/services/workspace_tools.py) | **pas** de join : l’encours **compte encore** la créance |

Deux outils se contredisent. L’artisan demande « FACT-2026-001 » : le chat dit qu’elle n’existe pas, l’encours l’inclut, le PDF dit que le contact n’existe pas.

**Reproduction.** Facture `sent` sur Dupont. Supprimer Dupont depuis la **modale** ([`ContactModal.tsx:133`](src/frontend/src/components/memory/ContactModal.tsx), `cascade=false`). Redémarrer. Liste factures, PDF, « retrouve FACT-… » dans le chat.

Chemin Contacts (cascade) : les factures ne sont toujours pas ménagées dans le handler. Si le `cascade_delete` du mapper (l. 60) est encore vivant, `session.delete(contact)` **détruit** les pièces comptables en silence. Les deux issues sont inacceptables, le test de cascade ([`test_routers_memory.py:193`](tests/test_routers_memory.py)) ne crée aucune facture.

---

### 3. Suppression d’un projet (l’UI n’envoie jamais `cascade`)

**Fichiers.** [`ProjectsPanel.tsx:109`](src/frontend/src/components/memory/ProjectsPanel.tsx) et [`ProjectModal.tsx:237`](src/frontend/src/components/memory/ProjectModal.tsx) : `deleteProject(id)` sans cascade. Backend : fichiers seulement si `cascade=true` ([`memory.py:1030-1041`](src/backend/app/routers/memory.py)).

**Attendu.** Après suppression du dossier, plus rien n’y pointe. Les conversations, elles, sont bien détachées.

**Obtenu, durable :**

- `files.scope_id` = id mort (pas une FK). Vecteurs Qdrant encore servis.
- Recherche `scope=all` ([`qdrant.py:275-284`](src/backend/app/services/qdrant.py)) inclut **tous** les `scope=project`, y compris les dossiers effacés. « Tous les projets » réinjecte le contenu d’un projet supprimé.
- `Document.project_id` / `contact_id` : dette confirmée, toujours aucune `ON DELETE SET NULL`, aucun `UPDATE ... SET NULL` dans `delete_project` / `delete_contact`. L’atelier reliste le document avec un id mort ([`documents.py:192-193, 874-875`](src/backend/app/routers/documents.py)). Création : **aucune** vérif que le projet/contact existe encore.
- `CalendarEvent.project_id` : posé à la création ([`local_provider.py:251`](src/backend/app/services/calendar/local_provider.py)), jamais nulled. Cloison 0.56 : `project_id == X OR IS NULL` ([`local_provider.py:189-193`](src/backend/app/services/calendar/local_provider.py)). Un rdv du dossier mort n’est plus `NULL` : invisible depuis tout autre dossier, encore visible dans l’agenda sans filtre.
- Tâches / livrables : `cascade_delete=True` côté ORM, probablement effacés avec le `session.delete(project)`. Pas un trou si le mapper fire. `create_task` ([`tasks.py:142-143`](src/backend/app/routers/tasks.py)) n’exige pas que le projet/contact existe : on peut coller un id déjà mort par l’API.

`delete_by_scope` existe ([`qdrant.py:517`](src/backend/app/services/qdrant.py)) et **n’a aucun appelant**.

**Reproduction.** Projet + fichiers indexés + rdv créé depuis une conversation rattachée + document d’atelier. Supprimer le projet dans la vue Dossiers. Redémarrer. Conversation en « Tous les projets » : les fragments du dossier mort remontent. Agenda d’un autre dossier : le rdv a disparu sans avoir été annulé.

---

### 4. Qdrant : le contrat fail-closed de `retrait_index` n’est pas celui des contacts/projets

[`retrait_index.py`](src/backend/app/services/retrait_index.py) : Qdrant d’abord, erreur = 500, la ligne SQLite reste.

Suppression contact/projet :

```136:144:src/backend/app/routers/memory.py
async def _delete_embedding(entity_id: str) -> None:
    try:
        ...
        await qdrant.async_delete_by_entity(entity_id)
    except Exception as e:
        logger.warning(...)
```

Et l’ordre contact (l. 762-766) : **SQLite d’abord**, Qdrant ensuite, warning avalé. Crash Qdrant = vecteur contact encore servi, plus de fiche.

Cascade fichiers (l. 756-758 / 1038-1040) : Qdrant avalé, **puis** `session.delete(file)`. C’est le bug 0.45 que `retirer_de_lindex` avait fermé, recopié ici. Après redémarrage, la recherche sémantique cite un `entity_id` dont `read_file` répond 404 (même message que hors périmètre).

---

### 5. Relances e-mail et déconnexion de compte

`EmailFollowUp.email_message_id` est une FK ([`entities.py:702`](src/backend/app/models/entities.py)). Aucun ménage :

- `DELETE /messages/{id}` ([`email.py:1297-1300`](src/backend/app/routers/email.py))
- `DELETE /auth/disconnect/{account_id}` ([`email.py:671-679`](src/backend/app/routers/email.py)) : messages puis compte, **pas** les follow-ups, **pas** les calendriers (`calendars.account_id`)
- purge RGPD e-mails ([`rgpd.py:230-234`](src/backend/app/routers/rgpd.py), [`rgpd_auto.py:205-209`](src/backend/app/services/rgpd_auto.py))
- `delete_contact` ne null pas `EmailFollowUp.contact_id`

Les listes ([`follow_ups.py:114-118`](src/backend/app/routers/follow_ups.py), [`dashboard.py:387-402`](src/backend/app/routers/dashboard.py)) font `.get()` : pas de plantage. `email_subject` / `contact_name` à `None`, `email_message_id` encore là. Un clic du brief ouvre un id 404. Relance « due » encore pending pour un mail qui n’existe plus.

Disconnect laisse aussi les `calendars` + `calendar_events`. Le delete calendrier **Google** du routeur ([`calendar.py:438-440`](src/backend/app/routers/calendar.py)) fait `session.delete(calendar)` sans boucler les events, alors que le provider local le fait ([`local_provider.py:152-157`](src/backend/app/services/calendar/local_provider.py)). `Calendar.events` n’a **pas** de cascade ORM. Events orphelins après suppression d’un agenda Google.

---

### 6. Traces qui se remplacent, devis convertis (moins brutal, liens morts)

- `Activity.remplace_id` → `activities.id` ([`entities.py:631`](src/backend/app/models/entities.py)). `DELETE /activities/{id}` ([`crm.py:212-227`](src/backend/app/routers/crm.py)) ne null pas les pointeurs. `PATCH` statut n’exige pas que `remplace_par_id` existe (l. 206). `read_contact` renvoie `remplacee_par` vers un id introuvable ([`memory_tools.py:991`](src/backend/app/services/memory_tools.py)).
- `Invoice.converted_from_id` : pas une FK, pas de ménage à la suppression du devis. Lien « devis source » 404.
- `DocumentPiste.section_origine_id` : pas une FK. Régénération de trame vide ([`documents.py:585-586`](src/backend/app/routers/documents.py)) détruit les sections, les pistes gardent l’ancien id.

Pas de crash SQL (FK off). Lectures qui mentent sur « ce qui remplace quoi ».

---

### Index graphe (arêtes)

C’est l’index des **noms d’IHM** ([`tests/test_index_des_noms.py`](tests/test_index_des_noms.py), Mermaid des cartes → vues). Aucun identifiant métier, aucun graphe de contacts/projets. Rien à signaler de ce côté.

---

### Ce qui est déjà propre (pour ne pas les recompter)

- Tâches au delete contact : `contact_id = None` (l. 708-718), volontaire.
- Prestations au delete contact : supprimées (l. 720-727).
- Activités au delete contact : supprimées.
- Conversations au **delete projet** (pas contact) : détachées + `memory_scope=global`.
- `retirer_racine` au **delete projet** (pas contact / pas RGPD).
- Delete fichier isolé : `retirer_de_lindex` fail-closed.
- Follow-up list : tolère un contact/mail manquant (None, pas 500).
- PDF facture : 404 explicite si contact absent (mais le libellé ment sur l’objet).

---

**Priorité si on corrige.** (1) un seul `supprimer_projet()` utilisé par delete projet, cascade contact, et RGPD : `retirer_racine` + détacher conversations + SET NULL agenda/documents + `retirer_de_lindex` des fichiers. (2) politique facture/contact : refuser la suppression tant qu’il reste une pièce, ou figer le nom/adresse **dans** la facture. (3) aligner `_delete_embedding` sur `retrait_index` (Qdrant d’abord, pas d’avalement) et brancher `delete_by_scope`.# NO-GO

La première passe regardait un appel isolé. Ici, le défaut tient **entre deux sessions** : un geste d’hier laisse un identifiant, un fichier ou une date que le prochain démarrage lit comme s’ils étaient encore vrais.

Les jonctions de fin août sont le cœur du problème. `delete_project` (0.43) a appris à détacher les conversations. La cascade contact, l’anonymisation RGPD et les prestations (29/08) n’empruntent pas ce chemin. Une facture n’a toujours qu’un pointeur vers le client vivant.

Rien de ce qui suit n’est un finding déjà rendu (faux livrable, panne déguisée en succès, repli Office).

---

## 1. Supprimer un contact en cascade contourne le ménage de `delete_project`

**Fichiers.** `src/backend/app/routers/memory.py` lignes 738-746 (cascade contact) contre 1016-1063 (`delete_project`). UI : `MemoryPanel.tsx` ligne 202 (`deleteContactWithCascade(..., true)`). Même trou dans `rgpd.py` lignes 205-226.

**Ce que Ludo croit.** Effacer la fiche (Contacts, confirmation cascade) emporte le dossier, comme le bouton Dossiers. Le commentaire de `delete_project` dit explicitement : sans détachement, le sélecteur afficherait « Toute la mémoire » pendant que le backend cloisonne encore sur l’id mort.

**Ce qu’il obtient, après redémarrage.** `session.delete(project)` tout seul :

- les conversations gardent `project_id` + `memory_scope=project` ;
- `_perimetre_de_conversation` (`chat.py` 618-623) cloisonne dès que `project_id` est posé, que le projet existe ou non ;
- `ConversationProjectPicker.tsx` 68-71 ne trouve plus le projet dans `listProjects()` : l’écran ne peut plus nommer le dossier ;
- `retirer_racine` n’est pas appelé : la racine `project_sync_roots` reste `detachee=0`. L’index unique `uq_sync_root_racine_active` (`database.py` 820-823) refuse de recoller **le même dossier** à un nouveau projet.

**Reproduction.** Contact + projet + racine de sync + conversation rattachée. Vue Contacts, supprimer le contact (cascade). Redémarrer. Rouvrir la conversation : le sélecteur ne montre plus le dossier, le RAG filtre encore sur l’id fantôme. Tenter de rattacher le même dossier ailleurs : collision sur la racine encore active.

---

## 2. Une facture n’a pas de copie du client. La supprimer la personne, ou l’anonymiser, réécrit le document légal (ou le rend injouable)

**Fichiers.** `entities.py` 561-591 (`Invoice` : `contact_id` uniquement, pas de nom/adresse figés). `Contact.invoices` déclaré `cascade_delete=True` ligne 60, **écrasé** sans cascade ligne 663. `delete_contact` (`memory.py` 687-761) ne touche jamais aux factures. PDF : `invoices.py` 635-637. Chat : `workspace_tools.py` 697-705 (`invoice_totals`, pas de join) contre 721-723 (`search_invoices`, `JOIN Contact`). Anonymisation : `rgpd.py` 186-195 (l’`address` n’est pas vidée).

**Ce que Ludo croit.** Une facture émise reste un document. Effacer ou anonymiser Dupont n’efface pas FACT-2026-001, et le PDF d’hier imprime encore Dupont à l’adresse d’hier.

**Ce qu’il obtient, après redémarrage.**

| Lecture | Résultat |
|---|---|
| Liste Facturation | la pièce est là, plus de nom de client |
| `GET /{id}/pdf` | **404 « Contact not found »** (la facture existe) |
| `search_invoices` | « Aucune facture ni devis » (le JOIN interne échoue) |
| `invoice_totals` | l’encours **compte encore** la créance |
| Anonymiser puis régénérer le PDF | destinataire `[ANONYMISÉ]`, **adresse réelle encore là** |
| Changer l’adresse du contact | le prochain PDF réécrit rétroactivement toutes les pièces |

Deux boutons, deux issues, aucune n’est tenable : `ContactModal.tsx` 133 (`cascade=false`) laisse des factures orphelines ; `MemoryPanel` cascade ne les ménage pas non plus. Le test de cascade contact ne crée aucune facture.

**Reproduction.** Facture `sent` sur Dupont. La supprimer depuis la fiche (pas la vue Mémoire). Redémarrer. Liste, PDF, « retrouve FACT-… » dans le chat, « combien on me doit ».

---

## 3. Les prestations (29/08) n’existent ni pour l’export, ni pour l’oubli, ni pour « tout effacer »

**Fichiers.** Table posée par `apply_adhoc_migrations` (`database.py` 156-194). Export : `data.py` 191-194 (`data_format_version: "1.2"` / « toutes les tables utilisateur ») et l’import du haut de fichier, **sans** `Prestation`. `DELETE /api/data/all` : `data.py` 456-490, pas de `delete(Prestation)`. Anonymisation : `rgpd.py` 185-245, pas de prestations. La suppression de contact, elle, les efface (`memory.py` 720-727).

**Ce que Ludo croit.** Exporter, anonymiser ou tout effacer emporte l’engagement (intitulé, montant HT, financeur, `fin_le`).

**Ce qu’il obtient.** Le JSON RGPD n’a pas de clé `prestations`. Après anonymisation, `GET /api/prestations?contact_id=…` rend encore la ligne, collée à `[ANONYMISÉ]`. Après « toutes mes données », les montants et l’OPCO restent en base (`PRAGMA foreign_keys` jamais posé). La sauvegarde chiffrée (`therese.db` entière) les emporte ; le JSON et les deux chemins d’oubli, non.

**Reproduction.** Créer une prestation, `GET /api/data/export`, chercher `"prestations"`. Anonymiser le contact, relire les prestations. `DELETE /api/data/all?confirm=true`, relire.

---

## 4. Supprimer un dossier (le geste UI réel) laisse fichiers, rendez-vous et documents sur un id mort

**Fichiers.** `ProjectsPanel.tsx` 109 et `ProjectModal.tsx` 237 : `deleteProject(id)` **sans** `cascade`. Backend : fichiers seulement si `cascade=true` (`memory.py` 1030-1041). Conversations : bien détachées (1045-1063). Agenda 0.56 : `local_provider.py` 189-193 (`project_id == X OR IS NULL`). Documents : `entities.py` 724-725, aucun `SET NULL`. `delete_by_scope` existe (`qdrant.py`) et **n’a aucun appelant**.

**Ce que Ludo croit.** Le dossier Ruiz n’existe plus. Plus de fragments, plus de séances, plus de documents d’atelier rattachés.

**Ce qu’il obtient, après redémarrage.**

- Fichiers `scope=project` / `scope_id` mort. Une conversation en « Tous les projets » (`scope=all`) **réinjecte** le contenu du dossier effacé.
- Rendez-vous locaux encore étiquetés Ruiz : invisibles depuis tout autre dossier (ils ne sont plus `NULL`), encore visibles dans l’agenda sans filtre. Ils n’ont pas été annulés.
- Documents d’atelier encore listés (`documents.py` 208, aucun filtre), `project_id` mort. Création : aucune vérif que le projet existe encore.

C’est la jonction 0.43 (conversations) / 0.56 (agenda) / atelier : le ménage a été écrit pour un seul pointeur.

**Reproduction.** Projet + fichiers indexés + RDV créé depuis une conversation rattachée + document d’atelier. Supprimer le dossier dans Dossiers. Redémarrer. Conversation « Tous les projets » : les fragments reviennent. Agenda d’un autre dossier : la séance a disparu sans avoir été annulée.

---

## 5. Une sauvegarde restaurée promet des fichiers Office que le disque n’a plus

**Fichiers.** Archive : `data.py` 736-744 (DB, Qdrant, `images/`, MCP, clé ; **pas** `outputs/`). Écriture : `registry.py` 32-33. Persistance du bouton : `extra_data.skill_files` sur le message. Téléchargement après cache vide : `skills.py` 241-247, glob `*_{8 premiers caractères}.*`. Purge de `outputs/` : uniquement `delete-all` (513). Rétention des backups utilisateur : aucune (seulement `pre_restore_*`, garder 1).

**Ce que Ludo croit.** Restaurer une sauvegarde ramène les documents générés dans le chat, comme les images.

**Ce qu’il obtient.** Redémarrage simple : le glob disque rattrape. Restore : le bouton de la bulle est toujours là (`extra_data` est dans la DB), le clic fait 404. Les images, elles, sont dans l’archive. `outputs/` et les `.tar.gz.enc` grossissent sans ramasse-miettes.

**Reproduction.** Produire un DOCX dans le chat, backup, restore, recliquer « Télécharger » sur l’ancien message.

Complément round-trip JSON (même famille) : `POST /api/data/import/conversations` (`data.py` 1344-1361) ignore `extra_data`, `provider`, `project_id`, `memory_scope`, `created_at`. L’export CRM CSV n’a pas `next_follow_up` (`crm_export.py` 43-58) : une relance posée, exportée, réimportée, disparaît de l’accueil.

---

## 6. Deux relances persistées, deux horloges. Le brief du 30 n’est pas celui du 29

**Fichiers.** Relance CRM : `relances.py` 32-37 (`next_follow_up <= datetime.now(UTC)`), notifications `notification_service.py` 169-177. Relance e-mail : `EmailDetail.tsx` 212-217 (`due_date: `${followUpDate}T09:00:00``, **sans** `contact_id`), table `email_follow_ups` (`due_date` en `VARCHAR`). Brief : `dashboard.py` 259-264 (`date.today()` local, `today_dt` naïf, `thirty_days_ago = datetime.now()` naïf) et 365-373 (EmailFollowUp jusqu’à J+2). All-day : 280-286, égalité sur `start_date` seul. Google : `calendar.py` 685-716, `dateTime.replace("Z", "")`.

**Ce que Ludo croit.** « Relance créée. Elle apparaît dans Relances et alertes. » Une seule définition depuis le 29/08. Un événement « 29-31 août, toute la journée » est là le 30.

**Ce qu’il obtient.**

- La cloche ne lit que `next_follow_up`. La relance née d’un mail alimente `due_follow_ups` du brief, **pas** les notifications. Deux tables, deux bouches, alors que le chantier relances visait exactement ça.
- Relance CRM stockée `…T00:00:00Z` : due à minuit UTC (02h à Paris). Le badge « en retard » du brief coupe `isoformat().slice(0, 10)` contre la date civile locale (`prototypeReadModels.ts` 35-36).
- All-day multi-jours : invisible dès le deuxième jour (`end_date` n’est pas lu).
- RDV Google avec offset : comparaison au minuit naïf du brief. Une exception aware/naïf est avalée (`dashboard.py` 327-328) : **journée vide**.

**Reproduction.** Créer une relance depuis un mail, regarder la cloche. Poser un all-day du 29 au 31, ouvrir l’accueil le 30.

---

## Vu, pas refilé, pas étiré

- Traitements orphelins marqués `interrupted` au boot (`task_registry.py` 162-187) : ça tient.
- `mode_cabinet` relu depuis les préférences au démarrage.
- Tâches au delete contact : `contact_id` dénoué, volontaire.
- Prestations au delete contact (le chemin dédié) : bien détruites. C’est le **reste** des portes qui les oublie.
- Delete fichier isolé : `retrait_index` fail-closed. La cascade contact/projet **recopie** l’ancien avalement Qdrant (`memory.py` 136-144, 756-758) : vecteurs orphelins après crash, cousin du contrat 0.45, pas un finding séparé.
- Sidebar au boot : `listConversations(50, 0)` (`useConversationSync.ts` 98) écrase le persist Zustand. La 51e conversation survit en SQLite, disparaît du rail. Réel, secondaire à côté des six ci-dessus.
- `PRAGMA foreign_keys` jamais posé : c’est le mécanisme des findings 1 à 4, pas un finding à part.

**Si on n’en ferme qu’un :** un seul `supprimer_projet()` appelé par delete projet, cascade contact et RGPD (`retirer_racine` + détacher les conversations + SET NULL agenda/documents + `retirer_de_lindex` des fichiers). Juste derrière : figer nom et adresse **dans** la facture, et brancher `Prestation` sur export / anonymize / delete-all.
