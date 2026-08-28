# Chantier B — Les ruptures d'usage

> **NO-GO sur la V1. Le périmètre change sur les quatre points.**
>
> ## B1 — NE PAS implémenter l'envoi. Retirer la promesse
>
> Je proposais d'implémenter l'envoi de devis par e-mail (« ~1 j, le service
> existe »). Faux : il faut attacher le PDF (chemin à écrire côté Gmail), vérifier
> que le contact a un e-mail, et ne poser `sent` **qu'après acceptation du
> fournisseur**. « Un échec Gmail sans PJ enverrait un devis **sans le devis**.
> Pire que le 501. » Deux jours minimum, et ce n'est pas la rupture vécue.
>
> Ce que B fait : **retirer la promesse restante**. Le chat ment encore — il
> oriente vers « la vue Facturation » alors que cette vue n'envoie pas
> (`chat.py:2333` et le guidage de `search_invoices`). `InvoiceForm` sait déjà
> poser *Envoyé* à la main : c'est le vrai repli (WhatsApp, courrier).
>
> ## B3 — Un outil d'agrégat, pas un `search_invoices` surchargé
>
> `search_invoices` est un **lookup** : `query` obligatoire, ILIKE, **limite 10**.
> Y ajouter un total serait un mensonge — « un total sur 10 lignes est un
> mensonge ».
>
> Donc `invoice_totals` : lecture seule, pas de `query`, un `SUM` SQL, **borné
> aux factures** (`document_type='facture'`) — sinon un devis `sent` entre dans
> l'encours, et l'artisan voulait 1 218 € (Garcia + SCI), pas son devis Moreau.
> Plus un total affiché sur `InvoicesPanel`, sans LLM.
>
> Coût du schéma supplémentaire : ~150 jetons par tour. Moins cher qu'un lookup
> qui additionne faux.
>
> ## B2 — Cinq couches, pas une ligne
>
> Je disais « `POST /memory/contacts` la jette ». Il faut honorer **toutes** les
> couches, sinon elles redivergent :
>
> 1. `POST /memory/contacts` (`memory.py:389`)
> 2. l'outil `create_contact` (schéma + écriture)
> 3. `ContactModal`
> 4. **le formulaire du premier devis** (`InvoiceConversationCard.tsx:410-450`) —
>    le chemin exact de l'artisan, qui n'a **ni adresse ni téléphone**
> 5. le type `Contact` du frontend, qui n'a pas `address`
>
> **Lieu d'exécution : dette nommée.** `Invoice` n'a pas le champ, le PDF lit
> `contact.address` comme destinataire. Pour un particulier maison = chantier ;
> pour une SCI, non. C'est un autre chantier.
>
> ## B4 — Un join, et le même trou sur le brief
>
> `Invoice.contact` existe, `list_invoices` fait déjà `selectinload` sur les
> lignes. Ajouter `selectinload(Invoice.contact)` et un `contact_name` optionnel.
> Pas de dénormalisation, pagination inchangée.
>
> **Même trou sur le brief du jour** : `overdue_invoices` n'a pas le nom
> (`dashboard.py:368`). L'artisan a lu « Facture FACT-2026-001 », pas Garcia.
>
> ## Cinquième rupture, sortie du périmètre et nommée
>
> **Les notifications arrivent après l'échéance.** L'avocat avait des délais les
> 11 et 12 septembre, une audience le 18 : une seule notification, « Tâche en
> retard », le lendemain. Le générateur ne connaît que les factures de plus de
> 30 jours, les prospects inactifs, les tâches déjà tardives et les rendez-vous
> du lendemain.
>
> Pour un avocat, un délai manqué est une faute professionnelle. **C'est un
> chantier à part**, pas une ligne à glisser ici.
>
> De même, la **TVA à 20 % par défaut** sur un devis de rénovation à 10 % :
> rupture réelle, hors B (un apprenti enverrait 5 040 € au lieu de 4 620 €).
>
> ## L'ordre retenu
>
> **B2** (les cinq couches) → **B4** (join + brief) → **B3** (`invoice_totals`)
> → **B1** (retirer la promesse, 2 h).
>
> B2 d'abord parce que sans adresse, le PDF sort avec un destinataire vide :
> l'artisan s'arrête là.
>
> ---
>
> La V1 est conservée ci-dessous.

---

# V1 (NO-GO) — design soumis à relecture AVANT code

Ce qui empêche de **finir un travail commencé**. Contrairement à A (la vérité)
et C (le secret), B ne touche pas à la confiance : il touche à l'utilité.

## Les quatre ruptures, par ordre de gravité vécue

### B1 — L'artisan fait son devis et ne peut pas l'envoyer

`POST /invoices/{id}/send` répond **501 en toutes circonstances**
(`invoices.py:880-884`) : « L'envoi de factures par email n'est pas encore
disponible. Télécharge le PDF et envoie-le manuellement. »

Trouvé par la contre-expertise, pas par les personas — l'artisan avait
abandonné avant.

**Deux options :**

| | Implémenter l'envoi | Retirer la promesse |
|---|---|---|
| Coût | ~1 j (le service e-mail existe, `send_email` fonctionne) | 2 h |
| Risque | envoi réel de document commercial : le geste doit être confirmé, et le statut ne doit changer QUE si l'envoi a réussi (le code le dit déjà en commentaire) | aucun |
| Pour l'artisan | il finit son travail | il sait au moins où il en est |

Je penche pour **implémenter**, en réutilisant le chemin `send_email` déjà
gardé par une confirmation. **Question au relecteur** : le PDF en pièce jointe
passe-t-il par un chemin existant, ou faut-il l'écrire ?

### B2 — L'adresse du client est jetée à la création

Sept couches déclarent `address`, trois l'honorent (base, `PATCH`, import VCF).
`POST /memory/contacts` la **jette** (`memory.py:383`), l'outil `create_contact`
ne l'expose pas, le formulaire ne l'a pas.

Pour un devis du bâtiment, le **lieu d'exécution** est exigé — et le modèle de
données ne le distingue pas de l'adresse du contact.

Petit, mécanique, sans risque.

### B3 — « Combien me reste-t-il à encaisser ? » n'a aucun chemin

`search_invoices` exige une `query`, ne filtre aucun statut, n'agrège rien
(`workspace_tools.py:256`, `:359`). La question la plus fréquente d'un artisan
est hors de portée, quel que soit le modèle.

Proposition : un outil de lecture financière (encours, retards, par statut), et
`query` devenue optionnelle.

**Question au relecteur** : ajouter un outil au chat coûte du contexte à chaque
tour. Vaut-il mieux étendre `search_invoices` (filtres + agrégat) que d'en
ajouter un second ?

### B4 — La liste des devis n'affiche pas le nom du client

`InvoicesPanel` montre `DEV-2026-001`, le statut, deux dates, le montant. Pas le
client. « Je ne retiens pas les numéros, je retiens Moreau. »

Le `contact_id` est là, le nom ne l'est pas dans la réponse.

## Ce que ce chantier ne fait pas

- Il ne touche pas au PDF (accents, statut anglais) : c'est E.
- Il ne touche pas à l'accueil : c'est D, et D attend un arbitrage de cap.

## Questions générales

1. **L'ordre.** B2 et B4 sont mécaniques. B1 et B3 sont des fonctionnalités.
   Par quoi commencer ?
2. **Y a-t-il une cinquième rupture** dans les rapports que je n'ai pas
   retenue ?
3. **B1 : le statut.** Le code refuse aujourd'hui de changer le statut tant que
   l'envoi n'est pas réel. Si j'implémente l'envoi, quel est le contrat exact —
   statut `sent` seulement après un succès SMTP confirmé ?
