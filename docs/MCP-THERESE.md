# Piloter THÉRÈSE depuis un agent

> État au 29/08/2026. **THÉRÈSE se lit, elle ne s'écrit pas** depuis l'extérieur.

## Ce que la porte fait, et ce qu'elle ne fait pas

THÉRÈSE embarque un serveur MCP (JSON-RPC, protocole `2024-11-05`) qui expose
**huit outils, tous en lecture** :

| Outil | Ce qu'il rend |
|---|---|
| `list_contacts` | les contacts, **liste bornée** (voir plus bas) |
| `get_contact` | une fiche selon le contrat de lecture (état, traces, consigne) |
| `list_emails` | les messages |
| `list_invoices` | les devis et factures |
| `list_tasks` | les tâches |
| `list_events` | les événements d'agenda |
| `search_memory` | la recherche |
| `get_project` | un dossier |

Six outils d'écriture existent dans le code (`create_activity`, `draft_email`,
`send_email`, `create_invoice`, `create_task`, `create_event`) et sont
**refusés** avec un motif explicite. Ce n'est pas un oubli.

### Pourquoi l'écriture est fermée

Un agent qui écrit dans THÉRÈSE pendant qu'un autre écrit dans le CRM d'origine
fabrique deux vérités qui divergent. La règle de la maison est « un fait, un
endroit ».

**Ouvrir l'écriture n'est pas une route à écrire, c'est une décision à
prendre** : qui, de THÉRÈSE ou du CRM, fait foi. Tant que la réponse n'est pas
tranchée, un agent peut préparer, citer, lister. Il ne peut pas envoyer le
mail, poser la tâche ni créer l'événement. Ce n'est pas « piloter », et il faut
le dire plutôt que d'habiller la porte en pont.

## Le contrat de lecture d'une fiche

`get_contact` lit `GET /api/memory/contacts/{id}/fiche`, la **même** route que
le chat. Elle rend trois choses distinctes :

```json
{
  "display_name": "…", "email": "…", "company": "…",
  "etat_courant": null,
  "traces": [
    { "origine": "resume manuscrit de la fiche", "date": null, "texte": "FORGER 490 EUR" },
    { "origine": "activite (note)", "date": "2026-08-27T16:00:00Z",
      "titre": "CORRECTION : c'est PROPULSER", "statut": "en_vigueur" }
  ],
  "consigne": "n'affirme que etat_courant…"
}
```

- **Les coordonnées sont des faits.**
- **`etat_courant`** est ce que l'application a réellement enregistré : il
  dérive des prestations ouvertes. **Il est souvent `null`**, et c'est normal.
- **`traces`** est ce qui a été écrit, daté, sans hiérarchie de vérité. Le
  résumé manuscrit de la fiche y descend : il n'est pas un état. Une trace de
  statut `annulee` a été retirée par son auteur.
- **`consigne`** part avec la donnée, parce qu'un modèle qui ne la reçoit pas
  tranche quand même.

Ne pas utiliser `GET /api/memory/contacts/{id}` pour alimenter un modèle : cette
route sert l'interface et rend le bloc `notes` comme un champ ordinaire.

## Le piège de la pagination

`list_contacts` est bornée (50 par défaut, 200 au maximum) et répond `200`
même tronquée. **Ne jamais annoncer un total** à partir de sa réponse : dire
« j'en vois N », pas « il y en a N ». Le même piège avait masqué 78
opportunités lors d'un import CRM.

## Comment le serveur est lancé

En `stdio`, par le processus qui l'utilise :

```bash
python -m app.services.mcp_therese_server
```

Il parle au backend local en HTTP, avec le jeton de session de l'application
(`~/.therese/.session_token`, en-tête `X-Therese-Token`). Il n'ouvre aucun port
et ne s'expose pas au réseau.

## Ce qui reste à faire avant d'ouvrir davantage

1. Décider qui fait foi, de THÉRÈSE ou du CRM d'origine.
2. Une confirmation humaine pour toute écriture (le motif déjà inscrit dans le
   filtre actuel).
3. Alors seulement, une porte authentifiée pour un agent externe.
