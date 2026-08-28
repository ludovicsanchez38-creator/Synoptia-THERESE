# O1 - Les journaux ignorent THERESE_DATA_DIR

**Trouvé par l'orchestration** (pas par un persona), pendant le contrôle
d'intégrité de la base réelle au milieu de la campagne.

- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : `src/backend/app/core/logging_config.py:161`

## Ce qui se passe

Le backend lancé avec `THERESE_DATA_DIR=/un/dossier/jetable` range bien ses
données métier dans ce dossier : `therese.db` (chiffrée SQLCipher), l'index
Qdrant, les sorties. Mais :

```python
log_dir = Path.home() / ".therese" / "logs"   # ligne 161
```

Le chemin des journaux est codé en dur sur le dossier de l'installation
réelle. `lsof` sur le processus de campagne le confirme :
`/Users/synoptia/.therese/logs/therese.log` reste ouvert en écriture pendant
que tout le reste écrit dans le dossier jetable.

Même motif, en lecture, pour les instructions personnalisées :
`src/backend/app/services/llm.py:206` cherche `~/.therese/THERESE.md`, jamais
`<data_dir>/THERESE.md`.

## Pourquoi ça compte

L'intention d'isolation existe déjà dans le produit (revue 0.40.1, F11 : « le
token suit `THERESE_DATA_DIR` — une instance de test ne doit pas parler à
l'installation réelle »). Elle est appliquée à moitié.

Conséquences concrètes :

1. Une instance de test écrit dans l'installation de production. C'est
   exactement le motif de l'incident de campagne du 14/06, par une autre route.
2. Deux instances lancées en parallèle écrivent dans le même fichier de log.
3. Pour un utilisateur soumis au secret professionnel (l'avocat et le médecin
   de cette campagne le testent explicitement), un journal qui échappe au
   dossier de données déclaré est un écart entre ce que l'application promet et
   ce qu'elle fait. Le `SecretMaskingFilter` masque les secrets, pas les noms
   ni les objets de messages.

## Correctif attendu

`log_dir` et le chemin de `THERESE.md` doivent dériver de `settings.data_dir`,
qui honore déjà `THERESE_DATA_DIR` (`config.py:68-73`).

**Correction après contre-expertise Soso** : j'avais supposé un problème d'ordre
d'initialisation (« le logging est configuré avant les settings »). C'est faux :
`settings` est importé avant `setup_logging()` (`main.py:16`). Il n'y a donc pas
d'obstacle technique — juste un chemin écrit en dur.

**Ce que j'avais manqué**, et qui élargit le constat à trois cas au lieu d'un :

| Cas | Fichier | Nature |
|---|---|---|
| Journaux | `logging_config.py:161` | **écriture** hors instance — et les journaux contiennent les **arguments complets des outils** (`logging_config.py:148`, `chat.py:2882`) |
| PDF de factures | `invoices.py:33` | fallback d'**écriture** vers `~/.therese/invoices` |
| `THERESE.md` | écrit dans `data_dir` (`config.py:829`), lu dans `~/.therese` (`llm.py:198`), puis **mis en cache** | **split-brain** : on écrit à un endroit, on lit l'autre, et la valeur périmée reste en mémoire |

Le troisième est le plus vicieux : un utilisateur qui modifie ses instructions
personnalisées les écrit dans un fichier que l'application ne relira jamais.

À traiter comme **deux défauts distincts** : les écritures hors instance, et les
lectures croisées / périmées.

## Vérification

```bash
THERESE_DATA_DIR=/tmp/jetable .venv/bin/python -m uvicorn app.main:app \
  --app-dir src/backend --port 17931
lsof -p <pid> | grep therese.log     # doit pointer /tmp/jetable/logs, pas ~/.therese
```

---

# Preuve empirique : la fuite s'est produite pendant la campagne

Ce constat n'est plus théorique. Le contrôle d'intégrité de fin de campagne a
trouvé **trois fichiers écrits dans l'installation réelle** par des personas
qui tournaient pourtant sur un `THERESE_DATA_DIR` jetable :

```
28/08 11:41  ~/.therese/invoices/DEV-2026-001.pdf     ← devis chaudière du persona 02
28/08 13:12  ~/.therese/invoices/FACT-2026-001.pdf    ← facture impayée du persona 02
28/08 13:12  ~/.therese/invoices/FACT-2026-002.pdf    ← idem
```

Plus, en continu, l'écriture des journaux (`~/.therese/logs/therese.log`, 8 Mo
sur la durée de la campagne).

C'est exactement le fallback signalé par la contre-expertise : `invoices.py:33`
range les PDF sous `~/.therese/invoices` sans passer par `settings.data_dir`.

## Ce qui a tenu, et ce qui n'a pas tenu

| Couche | Isolée par `THERESE_DATA_DIR` ? |
|---|---|
| Base SQLite (`therese.db`) | **oui** — datée du 28/08 09:08, avant le début de la campagne (11:09) |
| Index Qdrant | **oui** |
| Sorties, commandes, outils | **oui** |
| **PDF de factures** | **NON** — trois fichiers écrits dans l'installation réelle |
| **Journaux** | **NON** — écriture continue, avec les arguments complets des outils |

Vérification finale de la base réelle : `contacts: 2`, `invoices: 0`,
`conversations: 8`, `calendar_events: 429` — les données de l'utilisateur, aucune
de la campagne. Les trois PDF ont été mis à la corbeille
(`~/.Trash/therese-invoices-campagne-20260828/`) ; ils n'avaient écrasé aucun
document, la table `invoices` réelle étant vide.

## Pourquoi cette preuve compte

Un utilisateur n'a aucune raison de lancer deux instances. Mais le produit, lui,
en a : les E2E isolés, les tests, une future importation, un mode « bac à
sable ». Le mécanisme d'isolation existe et il est **partiel** — ce qui est plus
dangereux qu'une absence d'isolation, parce qu'on lui fait confiance.

Cette campagne l'a cru aussi : le protocole affirmait aux personas qu'ils
travaillaient sur une instance jetable. C'était vrai pour leurs données, faux
pour leurs documents.
