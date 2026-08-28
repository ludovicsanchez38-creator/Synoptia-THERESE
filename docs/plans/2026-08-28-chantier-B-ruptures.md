# Chantier B — Les ruptures d'usage

Design soumis à relecture AVANT code. **Rien n'est codé.**

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
