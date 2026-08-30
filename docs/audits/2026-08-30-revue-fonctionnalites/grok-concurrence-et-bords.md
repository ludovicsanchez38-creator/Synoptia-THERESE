# Revue Grok — concurrence, ordre et bords (30/08/2026, passe 3)

> Angle repris de Soso, à court de crédits. Deux choses en même temps, les
> étapes faites à l'envers, une écriture interrompue, et les limites.
>
> **Rapport partiel.** Le processus s'est figé après 48 Ko (0 % de CPU pendant
> 68 minutes) et a été arrêté. La sortie en flux entrelaçait le raisonnement
> et le rapport ; seules les sections bien formées sont conservées ici.

---

## 5. Upload : pas de plafond avant la copie, nom de fichier brut

**Fichier** : `files.py` `upload_file` 430-526, surtout 476-486.  
La limite 50 Mo n’existe que plus tard dans `file_parser.py` (`MAX_FILE_SIZE_BYTES`), **après** écriture disque.

**L’utilisateur croit** qu’un gros fichier sera refusé proprement, et que le nom (arabe, emoji, `..`) reste dans le dossier du projet.  
**Il obtient** :  
- copie intégrale d’un binaire énorme (pas de `max` Starlette trouvé), puis éventuellement 413 à l’extraction ; le fichier reste.  
- `dest_path = therese_dir / file.filename` : `../` sort du dossier projet (`os.replace` avant `validate_indexable_file`). Un nom avec `/` crée des sous-dossiers. Unicode/emoji passent en général sur APFS ; le danger est le séparateur et `..`, pas l’alphabet.

**Reproduction**  
Upload 800 Mo vers un projet : disque saturé, UI « ça indexe ». Upload nom `..\..\backups\x.pdf`.

**Pourquoi l’isolé ne le voit pas**  
Les tests envoient des petits `.txt` au nom simple.

**Mécanisme** : absence de limite en bordure + conversion chemin.

Fichier 0 octet : index « réussi » à `chunk_count=0` (hors scope, déjà interdit à rapporter).

---

## 6. Deux sauvegardes la même seconde

**Fichier** : `data.py` `create_backup` 872-928.  
Nom : `therese_backup_{YYYYMMDD_HHMMSS}` (précision **seconde**). Pas de `maintenance_mode` sur le backup (le restore l’a, 1166). Le restore refuse un second restore ; un backup, non.

**L’utilisateur croit** avoir deux archives distinctes.  
**Il obtient** le même chemin `.tar.gz` / `.enc`, courses `encrypt` + `unlink` : une archive incomplète, ou l’une qui efface l’autre.

Backup **pendant** restore : si le restore a déjà `begin()`, le backup est `REJECTED`. L’ordre inverse (backup TRACKED puis restore) : le restore attend la fin du backup. Ça tient. Le trou, c’est deux backups, ou double-clic.

**Reproduction**  
Deux POST `/api/data/backup` dans la même seconde.

**Pourquoi l’isolé ne le voit pas**  
Un backup à la fois dans les tests.

**Mécanisme** : collision d’identité + absence de mutex d’écriture.

---

## 7. Rattachement projet **pendant** le premier envoi (reste réel)

La dette documentée couvre « envoi pendant `setConversationProject` » (id serveur déjà posé). Il reste l’autre moitié.

**Fichiers**  
- `rattachementConversation.ts` : `persistanceEnVol` ne vit que le temps de `createConversation` (59-67), **pas** `setConversationProject`  
- `ChatInput.tsx` 605-627 : `attendrePersistance()` puis envoi **sans** `conversation_id` si `!synced`  
- `identiteConversation.ts` 17-24 : si déjà synced, on **refuse** l’id du stream

**L’utilisateur croit** que le message est dans la conversation rattachée au dossier.  
**Il obtient** : le POST part sans id → le backend crée la conversation A ; le rattachement crée B + projet ; le SSE A est rejeté ; les bulles locales sont sur B ; en base le texte est sur A, sans périmètre. Reload : B vide (ou sans le message), A orpheline. `search_files` sur B ne voit pas le dossier client.

**Reproduction**  
Nouvelle conversation, Entrée, et dans la seconde rattacher un projet (avant le chunk `conversation_id`).

**Pourquoi l’isolé ne le voit pas**  
Send seul, ou rattache seul, passent. Il faut les deux en vol, dans cet ordre.

**Mécanisme** : course d’identité / fenêtre après `persistanceEnVol = null`.

---

## Tracé, pas un finding

| Sujet | Verdict |
|---|---|
| Indexation vs suppression | Même `_verrou_de_chemin` (`retrait_index.py` 68, `indexation.py` 236). Sérialisé. |
| Qdrant orphelins à la suppression | `delete` par filtre serveur, plus le cap 1000. |
| Échec d’écriture d’index | `chunk_count=0` consigné (hors rapport demandé). |
| Double-clic composeur une fois `isStreaming` posé | File d’un prompt, bouton Stop. Pas de double POST évident après le premier `await`. |
| Keyring / Fernet concurrent | Pas de course d’écriture de clé tracée sur ces chemins. |
| Pagination catalogue fichiers | `total` + `affiches` (plafond 25), pas silencieux. `read_file` pose `tronque`. |
| Replay d’outils à 4000 car. | Marqué `[...tronqué]` pour le modèle. |

---

Trois endroits où l’utilisateur peut **prendre un livrable faux pour un livrable vrai** : historique coupé (1), réponse partielle (2), outils MCP « en erreur » alors qu’ils tournent encore (3). L’argent via outils chat n’est pas passé par une troncature de totaux : `invoice_totals` n’a pas montré de coupe silencieuse sur ce passage.Les agents ont remonté des courses que je n’avais pas encore ouvertes. Je vérifie dans le code celles qui touchent l’argent et les envois chez un tiers.**NO-GO**

La première passe regardait un appel isolé, bien formé. Ici le livrable faux n’apparaît que si deux choses se croisent, si l’étape 3 précède l’étape 1, si on coupe au milieu, ou si on touche le plafond. Rien de ce qui suit n’est un bouton qui ment tout seul.

Ce qui tient, pour ne pas noyer le reste : l’indexation sérialise par chemin, `pop_pending` empêche un second `confirm-tool` sur la même carte, l’empreinte `send_email` déduplique les cartes d’un même tour, et `invoice_number` unique empêche deux factures au même numéro (ça ne sauve pas la double conversion).

---

### 1. Concurrence : un devis converti deux fois, deux factures

**Mécanisme :** TOCTOU. Lecture du statut, puis écriture, sans verrou et sans unicité sur `converted_from_id`.

**Fichiers :** `InvoiceForm.tsx` L359-381 et L921-930 ; `invoices.py` L797-869 ; `entities.py` L583.

**L’utilisateur croit** qu’un clic « Convertir » crée une facture et verrouille le devis.

**Il obtient** deux `FACT-YYYY-NNN` distincts, le devis marqué `converted` à la fin. Le client peut être facturé deux fois.

**Chemin :** le bouton du dialogue n’a ni `disabled` ni garde `isConverting`. `handleConvertToInvoice` pose `setIsConverting(true)` (asynchrone React) puis POST. Côté serveur : `if devis.status == "converted"` (L797) lit l’objet déjà chargé, génère un numéro (L811), insert la facture, pose `converted` seulement au `commit` (L864-869). Deux sessions voient encore `accepted`/`sent`. `converted_from_id` est indexé, pas unique.

**Repro :** devis accepté, ouvrir « Convertir en facture », double-clic rapide sur Convertir. Ou le même devis ouvert dans deux onglets.

**Pourquoi la première passe ne pouvait pas le voir :** un seul POST bien formé réussit et laisse le devis converti. Le trou est entre les deux lectures du statut.

---

### 2. Interruption : timeout d’envoi, puis renvoyer = deux mails chez le destinataire

**Mécanisme :** le client abandonne l’attente, le serveur n’abandonne pas l’effet de bord. Aucune clé d’idempotence.

**Fichiers :** `EmailCompose.tsx` L104-126 ; `core.ts` L119 et L203-251 (`API_TIMEOUT_MS = 30_000`) ; `email.py` L1125-1186 (aucun `is_disconnected`) ; `workspace_tools.py` L1155-1163 (`wait_for(..., 30)`).

**L’utilisateur croit** « L'envoi a expiré » : rien n’est parti.

**Il obtient** le premier mail qui arrive quand même, puis un second s’il renvoie.

**Chemin :** confirmation -> `api.sendEmail` (timeout fetch 30 s) *et* `Promise.race` 35 s qui n’aborde rien. FastAPI continue jusqu’à `gmail.send_message` / `aiosmtplib.send`. `wait_for` côté chat annule la coroutine locale, pas l’acceptation SMTP/Gmail. `POST /api/email/messages` n’a pas d’idempotency key.

**Repro :** SMTP ou Gmail > 30 s. Confirmer. Attendre l’erreur. Renvoyer le même brouillon.

Même famille CalDAV : `caldav_provider.py` L286-336 construit un `VEVENT` sans `uid`. Timeout 30 s puis recréer = deux événements chez le serveur.

**Pourquoi la première passe ne pouvait pas le voir :** un POST qui rentre en 200 n’exerce ni l’abort, ni le retry. Les mocks répondent tout de suite.

---

### 3. Ordre : une facture payée reste entièrement réinscriptible, le PDF est écrasé

**Mécanisme :** l’étape « payer » ne fige rien. L’étape suivante (éditer, régénérer) écrit par-dessus.

**Fichiers :** `InvoiceForm.tsx` L501-507 (sélecteur de statut toujours actif), L866-878 (Enregistrer jamais bloqué si `paid`) ; `invoices.py` L346-454 (`update_invoice` sans garde de statut métier) ; `invoice_pdf.py` L645-646 (`filename = f"{invoice_number}.pdf"`).

**L’utilisateur croit** qu’une facture payée est close (un avoir pour corriger).

**Il obtient** des lignes, un montant, une devise, un client et un statut `sent`/`cancelled` encore posables. Régénérer le PDF remplace le fichier du numéro. L’encours ne la voit plus (`paid`), le document opposable a changé.

**Chemin :** Marquer comme payée -> rouvrir -> modifier une ligne -> Mettre à jour -> PDF. Le PUT recalcule `total_ttc` (L445-449) et garde `paid`.

**Repro :** facture `sent` à 1 200 EUR, marquer payée, passer une ligne à 1 EUR, enregistrer, régénérer le PDF.

**Pourquoi la première passe ne pouvait pas le voir :** un PUT isolé sur un brouillon est le chemin nominal. Il faut enchaîner payer *puis* modifier.

La suppression a le même trou d’ordre : `delete_invoice` L464-486 n’interdit aucun statut, le bouton Supprimer est sur toutes les cartes (`InvoicesPanel.tsx` L347-358). Effacer le dernier `FACT-2026-005` puis recréer réassigne `005` (`MAX()` L88-103).

---

### 4. Limite : le panneau Facturation tronque à 50 et affiche ça comme le total

**Mécanisme :** pagination sans page suivante, compteur = longueur de la page.

**Fichiers :** `invoices.py` L201-226 (`limit` défaut 50, plafond 100, pas de `total`) ; `invoices.ts` L84-101 ; `InvoicesPanel.tsx` L81 (`listInvoices()` sans `skip`/`limit`) et L169 (`{filteredInvoices.length} document(s)`).

**L’utilisateur croit** voir toutes ses pièces. Le sous-titre dit « 50 documents ».

**Il obtient** les 50 plus récentes. Les plus anciennes sont invisibles, non éditables, non supprimables depuis l’écran. `invoice_totals` (`workspace_tools.py` L697-706) lit **tout** l’encours : le chat peut citer une créance absente du panneau.

Même famille côté outil : `_search_invoices` L731-754 coupe à 10 et répond « 10 document(s) trouvé(s) » sans dire qu’il en reste.

**Repro :** 51 factures, ouvrir Devis et factures. La plus ancienne n’y est pas. Demander à THÉRÈSE « combien on me doit » : l’encours inclut la 51e.

**Pourquoi la première passe ne pouvait pas le voir :** un GET de 10 factures, `limit` largement suffisant, a l’air complet.

---

### 5. Limite : la suite `FACT-YYYY-NNN` casse à 1000 et le commentaire ment

**Mécanisme :** `MAX()` lexicographique sur une chaîne paddée à 3 chiffres. Unique ensuite = 500, pas un retry.

**Fichiers :** `invoices.py` L65-103 (commentaire L74 : « MAX() pour éviter les race conditions ») ; `entities.py` L567 `unique=True`.

**L’utilisateur croit** que les numéros continuent (001, 002, … 1000, 1001) et qu’un document = un numéro.

**Il obtient :**
- au 1001e document de l’année : `max("FACT-2026-999", "FACT-2026-1000")` = `"FACT-2026-999"` (`'9' > '1'`). `next` recalcule 1000, contrainte unique, **500** sur toute création suivante ;
- deux créations parallèles : même `MAX` lu sans `BEGIN IMMEDIATE`. L’unique évite le doublon de numéro, le second commit lève `IntegrityError` non géré, ou, si le second `MAX` voit déjà le commit, **deux documents**. Le bouton Créer (`InvoiceForm.tsx` L259, `isSaving` posé trop tard) n’aide pas un double-clic.

Vérifié : `max(['FACT-2026-999','FACT-2026-1000'])` vaut `FACT-2026-999`.

**Repro :** 1000 factures 2026, puis encore une. Ou deux POST `/api/invoices` au même instant.

**Pourquoi la première passe ne pouvait pas le voir :** un create isolé avant 999 réussit. Le test `test_invoice_number_uses_max_for_sequence` vérifie la présence de `MAX`, pas le lexique ni la course.

---

### 6. Conversion : date civile via `toISOString` (factures, édition d’un RDV, dernier jour du mois)

**Mécanisme :** mélange UTC et jour local. Le calendrier a déjà `localDateKey` (BUG-144). Trois surfaces l’ignorent encore.

**a) Facture, défaut d’émission / échéance**

`InvoiceForm.tsx` L89-98 : `new Date().toISOString().split('T')[0]` et `date.setDate(+30)` puis `toISOString()`. `civilDate.ts` L1-9 dit explicitement de ne jamais faire ça.

À 00:30 en France, la facture neuve est datée de la veille. Le numéro, lui, prend `datetime.now(UTC).year` (`invoices.py` L84) : autour du 1er janvier, date 2025 et numéro `FACT-2026-…`.

**b) Édition d’un événement horodaté, ça part chez Google**

`EventForm.tsx` L70-75 : en édition, `start.toISOString().split('T')[0]` (UTC) + `toTimeString()` (local). La création du même fichier (L90-96) utilise déjà `localDateKey`. Un RDV le 20 à 00:30 Paris s’affiche le 19 à 00:30. Enregistrer sans rien toucher envoie `2026-07-19T00:30:00` + fuseau du poste. Google déplace le RDV, les invitations partent à nouveau.

**c) Vue mois : le 31 (et le 29 février) n’existent pas pour Google**

`CalendarPanel.tsx` L158-171 : `endOfMonth = new Date(y, m+1, 0)` (dernier jour à minuit **local**) puis `toISOString()`. `timeMax` Google est exclusif. En UTC+2, juillet s’arrête au 30 vers 22:00Z : tout événement du 31 est hors fenêtre. La grille affiche quand même la case du 31, vide.

**Pourquoi la première passe ne pouvait pas le voir :** un create à midi UTC, ou un RDV à 15 h en milieu de mois, est cohérent. Il faut le bord de journée, l’édition (pas la création), ou le dernier jour du mois.

---

### 7. Concurrence : deux refresh OAuth, puis « reconnecte ton compte »

**Mécanisme :** check-then-act sans mutex, plus un champ de rotation jeté.

**Fichiers :** `email.py` L147-243 (`ensure_valid_access_token`, marge 120 s L66, aucun `Lock`) ; `oauth.py` L342-346 (le dict renvoyé **omet** `refresh_token` même si Google en envoie un).

**L’utilisateur croit** que Mails + Agenda au démarrage rafraîchissent le jeton, compte sain.

**Il obtient** deux `refresh_token` grant en parallèle (liste mails et liste events, ou chat `send_email` + calendrier). Dernier `commit` gagne. Si Google a tourné le refresh token, le second grant avec l’ancien peut révoquer la famille. L’écran dit 401 « reconnecte ton compte » (`email.py` L252-254) alors que le compte l’était. Même un refresh *seul* qui recevrait un nouveau refresh token le perd : `new_tokens.get('refresh_token')` dans `email.py` L239 est mort, `oauth.py` ne le recopie pas.

**Repro :** jeton à moins de 120 s. Ouvrir Mails et Agenda en même temps.

**Pourquoi la première passe ne pouvait pas le voir :** un seul `await ensure_valid_access_token` réussit. Il faut deux coroutines sur le même `EmailAccount`.

---

### 8. Interruption : Arrêter persiste un moignon comme réponse finie

**Mécanisme :** écriture partielle sans drapeau. Le tour suivant la rejoue comme un assistant achevé.

**Fichiers :** `chat.py` `_persister_message_partiel` L1961-1990, appelé L2462-2468 ; `ChatInput.tsx` L746-750 (`*(interrompu)*` **local seulement**).

**L’utilisateur croit** (après Arrêter) que la réponse est coupée. Au tour suivant, ou sur un autre poste, THÉRÈSE « se souvient » d’avoir fini.

**Il obtient** un `Message` assistant en base, contenu = le texte déjà produit, **sans** `extra_data` d’interruption. Le `*(interrompu)*` ne vit que dans le store. L’historique chargé pour le prochain `send` (`chat.py` L1148-1162) envoie ce moignon au modèle comme un tour complet.

**Repro :** question longue, Arrêter au milieu, envoyer « continue ». Ou quitter et rouvrir la conversation depuis un store vide (l’API n’a pas le marqueur).

**Pourquoi la première passe ne pouvait pas le voir :** le SSE `cancelled` est propre. Le faux livrable n’apparaît qu’au round-trip base + tour suivant.

---

### 9. Concurrence : deux cartes calendrier, deux événements chez Google

**Mécanisme :** `empreinte_action` ne sait dédupliquer que `send_email`. Fail-open pour le reste.

**Fichiers :** `tool_confirmations.py` L102-111 ; `chat.py` L2848-2870.

**L’utilisateur croit** confirmer *le* rendez-vous.

**Il obtient** deux `events.insert` (Google / CalDAV), deux invitations, si le modèle émet deux `create_calendar_event` dans le même tour. D1 a fermé ce trou pour l’e-mail. Le calendrier est laissé en « une carte par appel » par commentaire explicite.

**Repro :** « Prends RDV mardi 14 h avec Marie » avec un modèle qui double l’outil. Valider les deux cartes.

**Pourquoi la première passe ne pouvait pas le voir :** un seul `create_calendar_event` bien formé crée un événement. Les tests D1 ne couvrent que `send_email`.

Complément d’ordre, même surface : vider les participants à l’édition (`EventForm.tsx` L173 : `attendees.length > 0 ? attendees : undefined`). Le PUT Google (`calendar_service.py` ~295-312) ne touche `attendees` que si la clé est présente. `undefined` conserve l’ancienne liste. Les invitations restent, et reçoivent la mise à jour.

---

### 10. Limite : l’historique de conversation est amputé en silence

**Mécanisme :** deux plafonds, aucune marque utilisateur.

**Fichiers :** `chat.py` L1148-1154 (`limit(50)` derniers messages, sans dire qu’il en reste) ; `context.py` L36-41 (`pop(0)` tant qu’il reste plus d’un message, **sans** marque ; la marque L34 n’existe que s’il ne reste **plus qu’un** message, cas Board).

**L’utilisateur croit** que le modèle a toute la conversation (et les fichiers déjà « lus »).

**Il obtient** une réponse sur un passé coupé. L’écran montre encore les vieux messages. Ils ont borné les pièces jointes *justement* pour éviter ce sacrifice (`chat.py` L435-452). Le trim multi-messages n’a pas reçu le même traitement. Ensuite on gonfle encore le prompt système (skill, outils, `BLOC_PIECES_JOINTES`, L2259+) *après* le budget.

**Repro :** 60 messages, ou 20 messages + gros collage + Ollama. Poser une question qui s’appuie sur le début.

**Pourquoi la première passe ne pouvait pas le voir :** 2-3 messages courts tiennent. Il faut le volume réel.

Complément MCP, deux horloges : `mcp_service.py` L538 (`REQUEST_TIMEOUT = 60` du balayeur) contre L719 (`timeout=120` de `call_tool`) et L638 (init 90 s). Un outil à 70 s meurt à 60 s alors que l’appelant croit avoir deux minutes. La réponse tardive est jetée.

Complément Gmail, quota : `_list_messages_gmail` L864-870 pose `{error}` sur un GET 429. `mapEmailListItem` (`emailReadModels.ts` L16) rend `null`. La liste est plus courte, `console.warn` seulement (`EmailList.tsx` L111-123). Boîte « à jour », mails absents.

---

Ce que je n’ai **pas** promu en finding, alors que c’est réel : le PDF imprime « net a 30 jours » en dur (`invoice_pdf.py` L611) même après une conversion à 60 jours (visible sur un PDF isolé, trop proche d’un appel unique) ; le panneau qui n’insère pas la facture après conversion (câblage `onSave`, famille « le bouton n’affiche pas ce qu’il promet ») ; le rattachement projet pendant le premier envoi (résiduel déjà accepté). L’indexation concurrente avec une suppression est verrouillée.
