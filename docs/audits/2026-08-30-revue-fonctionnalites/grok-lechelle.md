# Revue Grok — l'échelle (30/08/2026, passe 8)

> Angle : l'application est testée avec trois contacts et dix messages. Ce qui
> casse au millier. Huit plafonds atteints en silence.

### 1. Une conversation de 200 messages : l'écran montre le début, le modèle voit la fin

`chat.py` 3467-3481 (`GET .../messages`, `order_by(created_at)` ASC + `limit=100`, pas d'offset) ; `useConversationSync.ts` 135-143 (`setConversationMessages` **remplace**) ; `chat.py` 1148-1153 (historique LLM : DESC + `limit=50`, BUG-031).

**Tu crois** rouvrir la conversation. Tout y est. Le modèle a lu la même chose.

**Tu obtiens** deux fenêtres disjointes. L'UI prend les 100 plus anciens. Le modèle reçoit les 50 plus récents. Au 151e message, plus aucun recouvrement. Changer de conversation et y revenir écrase le store : les messages 101+ existent en base, l'écran les a oubliés. Rien ne dit que c'est tronqué.

**Reproduire.** Fil de 110 messages. En changer, y revenir. Les 10 derniers ont disparu de l'écran. Demander « qu'est-ce que je viens de dire ? » : le modèle peut répondre juste, la bulle n'est plus là.

---

### 2. Contacts : 200 (souvent 50), et la recherche jette ce qui n'est pas déjà chargé

`memory.py` 348-378 (`le=200`, pas de `total`) ; `contactsStore.ts` 63-67 et 91-113 (filtre local sur ces 200, hits `searchMemory` résolus par `byId` du store : un hit hors des 200 est jeté) ; `InvoiceForm.tsx` 133-136 (`listContacts()` = **50**) ; `CRMPanel.tsx` 147-148 (« N contacts » = `contacts.length`). `GET /api/crm/pipeline/stats` totalise en SQL, aucun écran ne l'appelle.

**Tu crois** que Contacts, le pipeline et le formulaire de facture voient le carnet.

**Tu obtiens** les 200 derniers `updated_at`. Le 201e n'est ni dans la liste, ni dans le kanban, ni dans la recherche, même par nom exact : le backend le trouve, le store le jette. Un devis n'offre que 50 contacts.

**Reproduire.** 250 contacts. Le 201e s'appelle Dupont. Chercher « Dupont » : rien. Ouvrir un devis : Dupont n'est pas dans la liste.

---

### 3. Factures : 50, le compteur dit que c'est le total, les filtres tournent dans ce seau

`invoices.py` 201-226 (défaut 50, `le=100`, pas de `total`) ; `InvoicesPanel.tsx` 78-82 et 170 ; `invoiceStore.ts` 96-116 (filtre **en local**).

**Tu crois** la liste complète. « 50 documents ». Un filtre Payée vide veut dire qu'il n'y en a pas.

**Tu obtiens** les 50 plus récentes. Filtrer « Payée » sur ce seau peut afficher vide alors que mille factures payées sont en base. Ce n'est pas le finding Soso 16 : ici le GET réussit et tronque. L'encours du chat, lui, totalise tout.

**Reproduire.** 80 factures, dont 30 payées toutes plus anciennes que les 50 dernières. Ouvrir Facturation : « 50 documents ». Filtre Payée : « Aucune facture ».

---

### 4. La barre des conversations s'arrête à 50

`chat.py` 3261-3284 ; `useConversationSync.ts` 98 (`listConversations(50, 0)`).

**Tu crois** l'historique. La 51e n'a plus de porte. Pas de « charger plus », pas de compteur.

**Reproduire.** 60 conversations. Nouvelle machine (ou persist vidé) : 50. Les 10 plus anciennes sont injoignables.

---

### 5. La boîte mail s'arrête à 50, et IMAP ignore le jeton de page

`EmailList.tsx` 88-93 (`maxResults: 50`, jamais `pageToken`) ; `emailStore.ts` 74-78 (`pageToken` / `hasMore` existent, zéro appelant UI) ; `email.py` 948-955 (IMAP n'envoie pas `page_token`) ; `imap_smtp_provider.py` 284-309 (si le jeton arrivait : `fetch` de `offset + max_results` en mémoire, puis slice).

**Tu crois** ta boîte. Au pire, un bouton pour la suite.

**Tu obtiens** les 50 plus récents du label. Pas de page 2. Côté IMAP, même un `page_token` collé à la main est jeté : toujours la première page.

**Reproduire.** INBOX de 200 mails. Scroller : fin à 50. Aucun contrôle.

---

### 6. L'agenda d'un mois chargé coupe aux 250 premiers événements

`CalendarPanel.tsx` 157-174 (`max_results: 250`) ; `calendar.py` 566 et 642-665 (`nextPageToken` ignoré) ; `calendar_service.py` 160-164 (`orderBy=startTime`) ; `local_provider.py` 208-215 (ASC + `limit`).

**Tu crois** le mois. Un mardi vide est un mardi sans rendez-vous.

**Tu obtiens** les 250 **premiers** du mois. Le 251e et la fin du mois disparaissent. Un mois d'agence (10 RDV/jour) rend les derniers jours blancs.

**Reproduire.** 260 événements en mars, répartis. Ouvrir mars : le début est plein, la fin du mois est vide.

---

### 7. La recherche mémoire fait un aller-retour SQL par hit, puis charge tout ce qui matche un ILIKE

`memory.py` 174-212 (un `select` par hit Qdrant) et 232-242 (`ILIKE %query%` **sans LIMIT**, scoring Python, coupe après coup).

**Tu crois** une recherche. « e » au millier de contacts charge l'annuaire, le note en Python, n'en garde que 10. La route est `async` : ces `await` en série et le `.all()` restent sur la boucle. Le chat attend.

**Reproduire.** 2000 contacts. Chercher « e » dans Contacts. Observer le gel.

---

### 8. L'export RGPD et la liste des fichiers d'un projet chargent la base entière

`data.py` 97-188 (`GET /api/data/export` : tous les messages, toutes les tables, JSON, sur la route async) ; `memory.py` 925-936 (`list_project_files` sans `limit`) ; `ProjectModal.tsx` 85.

**Tu crois** un export, ou la liste du dossier synchronisé.

**Tu obtiens** tout en mémoire d'un coup. 300 conversations × 200 messages : plus aucune autre requête n'est servie. Un projet crawlé au millier de pages envoie le millier de lignes au modal.

**Reproduire.** Base déjà grosse. Déclencher l'export RGPD : l'app ne répond plus jusqu'à la fin du JSON.

---

Rapport aussi dans `docs/audits/2026-08-30-revue-fonctionnalites/grok-lechelle.md`. Je n'ai pas refilé les findings des passes 1 : Soso 16 est un échec déguisé, ici le GET réussit et tronque.
