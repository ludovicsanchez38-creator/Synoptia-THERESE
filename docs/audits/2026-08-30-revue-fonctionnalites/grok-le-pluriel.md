# Revue Grok — le pluriel (30/08/2026, passe 6)

> Angle : tout a été pensé pour UN. Deux comptes e-mail, deux agendas, deux
> devises, deux fournisseurs, deux projets du même nom, deux dossiers de
> données.

### 1. Le chat e-mail parle au premier compte de la table, pas à celui de l’écran

`workspace_tools.py` 878-909 : `select(EmailAccount).limit(1)`, ni `order_by`, ni défaut (le champ n’existe pas). `ToolConfirmationCard.tsx` 65-73 : À, Objet, Message, **pas l’expéditeur**.

**Tu crois** que le sélecteur du panneau (dès deux comptes) est l’expéditeur, y compris depuis le chat.

**Tu obtiens** le premier compte créé. Si son jeton est mort, 401, le second (sain, sélectionné) n’est jamais essayé.

**Repro.** Gmail A créé en premier, IMAP B sélectionné. « Envoie un mail à x@y.fr. » Ça part de A.

---

### 2. L’agenda du chat n’est pas l’agenda de l’écran, et un Gmail cache les autres

`workspace_tools.py` 912-960 : premier Gmail + `"primary"`. CalDAV n’existe pas sur ce chemin. `calendar.py` 154-162 : si `currentAccountId` est Gmail, le panneau ne rend **que** les agendas Google. `dashboard.py` 270-326 : tous les événements, sans nom d’agenda.

Trois bouches. Choisir Gmail pour lire son courrier fait disparaître iCloud et le local du menu Agenda. Le chat peut dire « aucun événement » pendant que l’accueil en montre.

La carte de RDV, elle, **dit** la destination (Google principal). La carte mail, non.

**Repro.** Agenda local plein + Gmail pour l’e-mail. Ouvrir Agenda : plus de local. « Qu’est-ce que j’ai cette semaine ? » : uniquement Google.

---

### 3. Le deuxième agenda Google écrase le premier

`calendar.py` 250-275 : `Calendar.id` = id Google, PK unique. Les fériés (`fr.french#holiday@group.v.calendar.google.com`), le carnet, un agenda d’équipe partagé ont **le même id** sur les deux comptes. Le second sync met à jour summary, **laisse `account_id` du premier**. Même schéma pour `CalendarEvent.id` (670-698) : le second sync écrase, `calendar_id` inchangé.

**Repro.** Deux Gmail, sync A puis B, déconnecter A. L’agenda férié de B 401.

---

### 4. Changer de compte e-mail ne vide pas ce qui appartenait à l’autre

`EmailPanel.tsx` 162-166 : pose l’id, recharge les labels. Rien d’autre. Persist : messages + labels + compte (`emailStore.ts` 196-202).

Label Gmail `Label_xxx` collé sur B → liste vide (BUG-122). Cache-first : la liste de A reste sous le nom de B. UID IMAP : le commentaire d’`EmailDetail` sait déjà qu’ils se recoupent (`accountId:messageId` pour les images) ; `messages.find(m => m.id === messageId)` n’a pas de filtre compte. Brouillon A, bascule B, Envoyer : part de B. La confirmation affiche l’UUID, pas l’adresse.

---

### 5. Deux fournisseurs : la réponse vient de l’autre, le badge et le coût disent le premier

`llm.py` 698-737, 848-918. Chat : `bascule_circuit=True` (le Board refuse). Circuit Anthropic ouvert → OpenAI, sans changer le sélecteur. `GET /api/config/llm/status` : zéro appelant frontend.

Le singleton est muté puis **restauré dans le `finally`**. `chat.py` 2513-2540 lit alors le fournisseur **sélectionné** : pastille, `Message.provider`, tarif. `delete_api_key` n’invalide ni le cache ni le singleton (`config.py` 316-364 vs 300-306). Une clé « effacée » peut encore servir de repli.

Couvre la dette « bascule cloud chez souverain à clé stockée », plus l’attribution fausse.

---

### 6. Deux contacts, la même adresse : le CRM en prend une au hasard, hors cloison

`Contact.email` indexé, pas unique. Création UI sans contrôle. `get_crm_contact_by_email` (`email.py` 129-144) : `.limit(1)` **global**. « Générer une réponse » injecte notes, score, téléphone de cette ligne (1527-1537). Le dashboard : le dernier gagne dans un dict. Le chat déduplique dans la cloison. Trois bouches.

**Repro.** Deux fiches `jean@x.fr`. Ouvrir un mail de cette adresse → Générer une réponse. Les notes de l’un partent dans le brouillon de l’autre.

---

### 7. Deux projets du même nom : le chat fusionne, le sélecteur confond

`POST /projects` sans unicité. `_find_existing_project` : `.first()` parmi les globaux. « existe déjà, je le réutilise » peut renvoyer l’id de l’autre client. Le picker affiche le nom seul. `EntitySuggestion` : `key={`project-${project.name}`}` : ignorer l’un retire les deux.

La cloison fichiers tient par UUID **une fois le bon id posé**. Le trou est en amont.

---

### 8. Les agents d’action étiquettent toute facture en euros

`action_agents.py` 383-389 : `{amount} EUR` en dur, plus `number` / `client_name` qui n’existent pas sur `Invoice`. Une facture USD sort « ? | ? | 1000 EUR ». L’encours du chat a le garde-fou ; cette surface non.

---

### 9. Deux dossiers de données : le trousseau et les PDF ne suivent pas

`session_token` Python suit `THERESE_DATA_DIR` (dette atelier caduque). Le Keychain, lui, reste `therese-app` / `encryption-key` (`encryption.py` 43-44) : BUG-050 écrase l’entrée, l’autre profil devient indéchiffrable. Les PDF facture sans `working_directory` s’écrivent dans `~/.therese/invoices` (`invoices.py` 49-51), pas dans le data dir.

---

Si tu n’en corriges qu’un : **les outils chat e-mail et agenda doivent parler au compte / calendrier de l’écran, ou refuser**. C’est un envoi et un RDV chez le mauvais destinataire interne, avec une carte qui ne le dit pas pour le mail.
