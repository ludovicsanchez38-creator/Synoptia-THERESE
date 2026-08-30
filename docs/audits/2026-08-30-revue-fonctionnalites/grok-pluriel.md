# Revue Grok — le pluriel (30/08/2026)

> Angle : tout a été pensé pour UN. Le deuxième compte, le deuxième agenda,
> le deuxième nom, le deuxième fournisseur. Ce que les passes « un appel isolé »
> ne pouvaient pas voir.
>
> **NO-GO**

Les totaux d'encours tiennent : EUR + USD ne s'additionnent plus. La cloison
fichiers tient par UUID. Les contacts généraux fail-open et les fichiers
fail-closed sans périmètre restent la dette du 27/08 (une ligne, pas un finding).

Le trou de cette passe : **le sélecteur de l'écran n'est pas celui des outils**.
Deux bouches, deux vérités.

---

### 1. Le chat e-mail parle au premier compte de la table, pas à celui de l'écran

**Fichiers.** `workspace_tools.py` 878-909 ; `entities.py` 321-360 ; `ToolConfirmationCard.tsx` 65-73 ; `EmailPanel.tsx` 269-288.

**Tu crois** que le sélecteur du panneau Email (affiché dès qu'il y a deux comptes) est l'expéditeur, y compris depuis le chat.

**Tu obtiens** `select(EmailAccount).limit(1)` : pas de `order_by`, pas de `is_default` (le champ n'existe pas). Les outils `read_emails` / `send_email` / `search_emails` n'ont aucun paramètre de compte. La carte de confirmation montre À, Objet, Message : **pas l'expéditeur**.

Si ce premier compte a un jeton mort, `ensure_valid_access_token` lève un 401 (`email.py` 219-255). `_get_email_provider` ne l'attrape pas et **ne tente pas le second**, même sain.

**Reproduire.** Compte A (Gmail, créé en premier) + compte B (IMAP, sélectionné à l'écran). « Envoie un mail à x@y.fr. » La carte n'indique pas From. L'envoi part de A. Variante : révoquer A, garder B : le chat échoue, B n'est jamais essayé.

---

### 2. L'agenda du chat n'est pas l'agenda de l'écran, et un Gmail cache les autres

**Fichiers.** `workspace_tools.py` 912-960 et 963-1000 ; `calendar.py` 154-162 ; `CalendarPanel.tsx` 111 ; `dashboard.py` 270-326.

**Tu crois** que le menu de l'agenda (et CalDAV, et le local) est celui que le chat consulte et où il crée.

**Tu obtiens** trois bouches :

| Surface | Ce qu'elle voit |
|---|---|
| Chat | Premier Gmail + `"primary"`. CalDAV n'existe pas sur ce chemin. Local seulement s'il n'y a **aucune** ligne Gmail (même à jeton mort, BUG-133 ne s'applique pas). |
| Panneau Agenda | `listCalendars(currentAccountId)`. Si le compte e-mail courant est Gmail : **return immédiat** des seuls agendas Google. Local et CalDAV disparaissent du menu. |
| Accueil | Tous les `CalendarEvent` SQLite, **sans nom d'agenda**. |

`currentAccountId` est celui du store **e-mail**. Choisir Gmail pour lire son courrier masque iCloud / le local dans l'agenda. Le chat peut dire « aucun événement » pendant que l'accueil en montre (ils sont sur le local).

La carte de RDV, elle, **dit** la destination (`get_calendar_confirmation_destination`). Elle dit Google principal du premier Gmail, pas le calendrier du menu.

**Reproduire.** Agenda local plein + Gmail connecté pour l'e-mail. Ouvrir Agenda : plus de local. « Qu'est-ce que j'ai cette semaine ? » : uniquement Google primary. Accueil : les deux, sans provenance.

---

### 3. Le deuxième agenda Google écrase le premier (identifiants globaux)

**Fichiers.** `calendar.py` 250-275 et 670-698 ; `entities.py` 493-499.

**Tu crois** que deux comptes Gmail ont deux listes d'agendas, et qu'un RDV copié sur deux agendas reste deux lignes.

**Tu obtiens** `Calendar.id =` l'id Google, PK unique. Les agendas système ont le **même** id sur tous les comptes français (`fr.french#holiday@group.v.calendar.google.com`, carnet d'adresses, agenda partagé d'équipe). Le second sync trouve la ligne, met à jour summary/timezone, **ne réécrit pas `account_id`**. L'agenda « férié » de B reste collé au jeton de A. Déconnecter A le casse pour B.

Même schéma pour les événements : `CalendarEvent.id =` l'id Google, pas `(calendar_id, id)`. Le second sync `session.get` par id seul, écrase le contenu, **laisse `calendar_id` du premier**. Dashboard et notifications lisent cette table plate.

**Reproduire.** Deux Gmail. Synchroniser A, puis B. L'agenda Jours fériés n'existe qu'une fois, `account_id` = A. Déconnecter A. Sur B, le férié 401.

---

### 4. Changer de compte e-mail ne vide pas ce qui appartenait à l'autre

**Fichiers.** `EmailPanel.tsx` 162-166 ; `emailStore.ts` 94 et 196-202 ; `EmailList.tsx` 77-93 ; `emailReadModels.ts` 45-52 ; `EmailDetail.tsx` 45-61 ; `EmailCompose.tsx` 93-111.

**Tu crois** que le sélecteur bascule la boîte.

**Tu obtiens** `switchAccount` pose l'id et recharge les labels. Rien d'autre. Survivent : messages, `currentLabelId`, `currentMessageId`, brouillon, `needsReauth`. Le persist localStorage emporte messages + labels + compte.

Conséquences tracées :

- Un label Gmail `Label_xxx` (ou un dossier IMAP) reste collé. Sur B, dossier introuvable → liste vide + warning, pas l'INBOX (contrat BUG-122).
- Cache-first : tant que le fetch de B n'a pas répondu, la liste de A reste sous le nom de B. Fetch en échec : l'erreur s'efface, A reste.
- `mapEmailList` réinjecte corps et priorité **par id**. Le commentaire d'`EmailDetail` admet déjà que les UID IMAP se recoupent (`accountId:messageId` pour les images) ; `messages.find(m => m.id === messageId)` n'a pas de filtre compte.
- Brouillon rédigé sur A, bascule vers B, Envoyer : part de B. La confirmation affiche l'`UUID` du compte, pas l'adresse.

Même persist côté agenda (`calendarStore.ts` 167-174 : `events` + `currentCalendarId`). `setCurrentCalendar` ne vide pas les événements.

**Reproduire.** Deux IMAP. Ouvrir un mail du compte A (UID 42). Passer sur B. Le volet droit refetch l'UID 42 **chez B**. Rédiger un brouillon, changer de compte, confirmer : l'UUID a changé, l'adresse n'est pas écrite.

---

### 5. Deux fournisseurs configurés : la réponse vient de l'autre, le badge et le coût disent le premier

**Fichiers.** `llm.py` 698-737, 848-918, 920-931 ; `chat.py` 2513-2540 et 2666-2672 ; `config.py` 300-306 vs 316-364.

**Tu crois** parler au modèle du sélecteur. Si tu as retiré la deuxième clé, elle n'est plus là.

**Tu obtiens** `bascule_circuit=True` sur le chat (le Board la refuse). Circuit Anthropic ouvert → OpenAI (ou le premier fallback encore fermé) **sans** changer `llm_provider` en base. `GET /api/config/llm/status` existe, **zéro appelant frontend**.

Pendant le stream, `self.config` est muté vers le fallback, puis **restauré dans le `finally`**. `continue_with_tool_results` ne re-résout pas : tant que le premier générateur n'est pas fini, les outils tournent sur le fallback (ça tient pour un message). Ensuite `chat.py` lit `llm_service.config` **déjà restauré** : badge, `Message.provider`, `token_tracker` (donc le tarif) = le fournisseur **sélectionné**, pas celui qui a répondu.

`set_api_key` invalide cache + singleton. `delete_api_key` ne fait **ni l'un ni l'autre**. `_get_api_key_from_db` sert le cache. Le circuit breaker peut encore basculer sur une clé que tu viens d'effacer.

Couvre la dette « bascule cloud chez souverain à clé stockée » : c'est le même mécanisme, plus l'attribution fausse.

**Reproduire.** Clés Anthropic + OpenAI. Ouvrir le circuit Anthropic (3 pannes). Envoyer un message. La pastille dit Anthropic. Le coût est au tarif Anthropic. Effacer la clé OpenAI dans Réglages, renvoyer : le cache peut encore s'en servir.

---

### 6. Deux contacts, la même adresse : le CRM en prend une au hasard, hors cloison

**Fichiers.** `entities.py` 29 (index, **pas** unique) ; `memory.py` 384-410 (création sans contrôle) ; `email.py` 129-144 et 1527-1537 ; `dashboard.py` 304-308 ; `memory_tools.py` 387-398.

**Tu crois** qu'une adresse désigne une fiche, et que « Générer une réponse » part de *cette* fiche.

**Tu obtiens** deux créations silencieuses. `get_crm_contact_by_email` : `.limit(1)` global, pas de `order_by`, **ignore** le périmètre projet. Injecte nom, téléphone, score, **notes** dans le brouillon. Le dashboard, lui, construit un dict : le **dernier** gagne. Le chat `create_contact` déduplique dans la cloison (`.first()`). Trois bouches.

**Reproduire.** Jean Dupont `jean@x.fr` (notes internes, score 90), puis Jean Martin `jean@x.fr` (score 20). Ouvrir un mail de `jean@x.fr` → Générer une réponse. Les notes de l'un partent dans le brouillon destiné à l'autre.

---

### 7. Deux projets du même nom : le chat fusionne, le sélecteur confond, ignorer l'un ignore les deux

**Fichiers.** `memory.py` 838-863 ; `memory_tools.py` 294-313 et 620-627 ; `ConversationProjectPicker.tsx` 156-159 ; `EntitySuggestion.tsx` 152, 160-162, 210-217.

**Tu crois** qu'un nom de dossier désigne *ce* dossier, et que la cloison fichiers suit.

**Tu obtiens** `POST /projects` sans unicité. Les projets nés de l'UI sont `scope=global`. `_find_existing_project` prend `.first()` parmi les globaux visibles : « existe déjà, je le réutilise » peut renvoyer l'id de l'autre client. Le picker affiche le nom seul (deux options identiques). `EntitySuggestion` a `key={`project-${project.name}`}` : ignorer l'un retire les deux ; le budget est étiqueté `EUR` en dur.

La cloison **fichiers** reste par UUID une fois le bon id posé. Le trou est en amont : on pose le mauvais id.

**Reproduire.** Deux projets « Audit Dupont » (clients A et B) depuis Mémoire. Dans le chat : « crée le projet Audit Dupont » réutilise le premier. Le sélecteur de cloison : deux libellés identiques. Choisir le mauvais ouvre les fichiers de l'autre.

---

### 8. Les agents d'action étiquettent toute facture en euros

**Fichier.** `action_agents.py` 383-389.

**Tu crois** que le contexte « factures » d'un rapport hebdo parle des vrais documents.

**Tu obtiens** `{amount} EUR` en dur. `Invoice` n'a ni `number` ni `client_name` (c'est `invoice_number` + `contact`). Une facture USD 1 000 sort « ? | ? | 1000 EUR ».

L'encours du chat, lui, refuse d'additionner (volontaire, tests verts). Cette surface-là n'a pas reçu le garde-fou.

**Reproduire.** Facture USD `sent` 1 000 + devis EUR 500. Lancer un rapport métier qui charge le contexte invoices.

---

### 9. Deux dossiers de données : le trousseau et les PDF ne suivent pas

**Fichiers.** `encryption.py` 43-44 (Keychain `therese-app` / `encryption-key`, global) vs 29 (fichier `.encryption_key` dans le data dir) ; `invoices.py` 49-51 (repli `~/.therese/invoices`, pas `resolve_invoice_output_dir`).

**Confirme** : le `session_token` Python suit `THERESE_DATA_DIR` (`main.py` 411). Ce n'est plus la dette atelier.

**Tu crois** qu'un second profil (`THERESE_DATA_DIR` ailleurs) est une installation à part.

**Tu obtiens** la même entrée Keychain. BUG-050 écrase le trousseau avec le `.encryption_key` du dossier **courant** : l'autre profil devient indéchiffrable. Les PDF facture, si aucun `working_directory`, s'écrivent dans `~/.therese/invoices` (génération **et** suppression). Persona de test → fichiers dans l'installation réelle.

**Reproduire.** Deux `THERESE_DATA_DIR`. Lancer B. La clé Keychain est celle de B. Rouvrir A : InvalidToken. Générer une facture sans dossier de travail configuré : le PDF est dans `~/.therese/invoices`, pas dans le data dir.

---

## Confirmations (une ligne)

- Encours mixte EUR+USD : **tient** (`encours_ttc` null, `encours_par_devise`). Ne pas rouvrir.
- Cloison fichiers fail-closed / contacts généraux fail-open : **dette 27/08**. Confirme.
- `GET /api/files/` sans filtre : dette assumée. Confirme.
- `session_token` suit le data dir. La dette atelier sur ce point est caduque.
- Board : `bascule_circuit=False`. Volontaire 0.48.
- Thème clair/sombre : pas d'état métier collé.

## Pas élevé (tracé, pas un finding)

- Prestations : pas de champ devise, `€ HT` en dur. Produit FR (Qualiopi), pas un mélange de deux devises stockées.
- Variables `{nom}` : table unique globale. Contrat V1, pas une cloison projet.
- MCP `{server_id}__outil` : le modèle ne collisionne pas. L'API HTTP sans `server_id` prend le premier serveur du nom : landmine, pas le chemin UI.
- Conversion devis USD : recopie la devise (pas de taux inventé). `late_penalty_rate = 11.62` est toutefois **écrit** sur la facture dollars ; seules les mentions PDF sont gated EUR.

---

Si on ne corrige qu'une chose : **les outils chat e-mail et agenda doivent parler au compte / calendrier de l'écran, ou refuser**. C'est le deuxième objet le plus dangereux : un envoi, un RDV, chez le mauvais destinataire interne, avec une carte qui ne le dit pas pour le mail.
