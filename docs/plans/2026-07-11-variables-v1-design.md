# Chantier 4 - Variables V1 - Design V3 (11/07/2026)

> Évolution du design V2 (`2026-07-10-chantiers-3-4-5-designs.md`, chantier 4)
> enrichie de la session de co-design spontanée Dr_logic x Katia dans #bugs la
> nuit du 10 au 11/07 (messages 1525216457..1525379188). Statut : à challenger
> par Codex puis TDD (GO Ludo donné le 11/07 : « go enchaine »).

## Ce que Dr_logic a apporté (et qu'on intègre)

1. **Variables = mémoire de travail**, pas seulement des raccourcis de
   substitution : on compose des blocs au fil de la conversation, puis on les
   utilise (use case liste de courses : moins d'oublis, moins de tokens).
2. **Modèle borné par lui-même** : une variable est SOIT une valeur
   alphanumérique (scalaire, enrichie par concaténation), SOIT une liste de
   valeurs (enrichie par ajout d'élément). Rien d'autre en V1.
3. **Opérations** : créer/remplacer, ajouter, supprimer. (« fusionner »
   explicitement écarté par lui : sous-entend un format, reporté.)
4. **Manipulation depuis le chat en zéro-LLM** via la grammaire d'actions
   existante (cohérence chantier 2).

## Reporté explicitement (V2+)

- Triplet `action/cible/acte` + paramètres JSON par variable (refonte de la
  grammaire = chantier à part, quand les actions typées arriveront).
- Variables JSON arbitraires, fusion, SQL/tri SQLite exposé au LLM.
- Alimentation externe (cron, command.txt), formulaire web distant.
- Nom de fichier stable dans la carte « Fichier généré » : c'est BUG-136/137,
  traité dans le lot bugs, pas ici.

## Modèle de données

Table SQLite `variables` (migration Alembic) :
- `name` UNIQUE, `[a-z0-9_]{1,32}`, mots réservés interdits (`action`,
  `aide`, `variable`, `variables`)
- `kind` : `text` | `list`
- `value` : JSON (`str` pour text, `list[str]` pour list)
- `description` optionnelle, `created_at` / `updated_at`
- Limites V1 : 100 variables max, valeur scalaire 4000 caractères max,
  liste 100 éléments max de 500 caractères max, description 200.
- RGPD : les valeurs partent au LLM à l'usage, vivent en SQLite et dans
  l'historique -> rubrique présentée honnêtement (PAS un coffre à secrets),
  incluses dans l'export RGPD existant, purge avec le reste.

## Grammaire chat (zéro LLM, allowlist stricte, extension de chat_actions.py)

```text
{action: variable creer courses liste}          -> liste vide
{action: variable creer titre "Mon rapport"}    -> scalaire
{action: variable ajouter courses "tomates"}    -> +1 élément (ou concat si scalaire)
{action: variable supprimer courses}
{action: variable afficher courses}             -> contenu formaté, local
{action: variables}                             -> liste nom/type/taille, local
```

- Réponses locales (`kind="variable"`, même chemin que navigate/help : réponse
  + `done`, aucune bulle LLM).
- `creer` sur un nom existant = remplacer (le verbe affiché le dit).
- `ajouter` : concaténation avec espace sur un scalaire, append sur une liste.

## Substitution `{nom}`

- **Ordre STRICT dans send_message** (inchangé vs V2) : classification de
  TOUTES les syntaxes déterministes sur le message BRUT (message-action,
  slash, directives inline) PUIS substitution `{nom}` UNIQUEMENT dans la
  partie destinée au LLM, PUIS check_prompt_safety. Une valeur ne peut JAMAIS
  fabriquer une action/slash/directive (single-pass, valeurs jamais
  re-scannées, testé avec des valeurs simulant chaque syntaxe).
- **Dans les messages-actions** : le corps de `_ACTION_MESSAGE` exclut `{}`
  aujourd'hui -> extension contrôlée : le corps accepte UNIQUEMENT des tokens
  `\{[a-z0-9_]{1,32}\}` (pas d'imbrication, lookahead `{{` conservé).
  La substitution s'applique au SUJET d'un `produire` APRÈS classification
  (la valeur est une donnée, le skill/format sont déjà fixés) :
  `{action: produire docx "liste de courses depuis {courses}"}`.
  Une liste substituée se rend `- élément` par ligne dans le prompt de
  rédaction, `, ` inline ailleurs.
- Variable inconnue : token laissé TEL QUEL (visible), signalé par l'aperçu.
- `{action: ...}` reste NON substituable en tant que tel : seul le sujet
  passe par la substitution, jamais le verbe/format/cible.

## API

- `GET/POST/PUT/DELETE /api/variables` (CRUD, validations = limites du
  modèle, 422 sinon).
- `POST /api/variables/preview` `{text}` -> `{resolved, unknown: [...]}` :
  MÊME fonction de résolution que send_message, zéro effet de bord - c'est
  l'aperçu exact du payload.

## Frontend

- Réglages > Services > « Variables » (même emplacement qu'Exports Word) :
  liste, création (nom/type/valeur/description), édition, suppression,
  bandeau honnêteté (« les valeurs sont envoyées au modèle à l'usage »).
- ChatInput : quand l'input contient un token `{nom}`, appel debounced de
  /preview et affichage discret (chip) : « 2 variables résolues, 1 inconnue :
  {client} » - l'envoi reste possible (confirmation UNIQUEMENT si inconnues).
- Périmètre V1 : chat principal + sujet des actions produire. Deep Research,
  Board, agents, Atelier : EXCLUS explicitement (aucune substitution).
- Menu `/` : entrée `variable` insérant la syntaxe ; `{action: aide}` liste
  les nouveaux verbes.

## Tests (TDD, par tranche)

1. Service + migration : CRUD, limites, unicité, mots réservés, kinds.
2. Grammaire : chaque verbe, casse/accents, corps avec tokens `{nom}`,
   `{{action` toujours écarté, action inconnue -> aide.
3. Substitution : ordre strict (valeur simulant action/slash/directive =
   zéro effet de bord), single-pass (valeur contenant `{autre}` non
   re-résolue), inconnue laissée telle quelle, listes (rendu ligne/inline),
   sujet produire substitué, verbe/format jamais substitués.
4. Endpoints : CRUD + preview sans effet de bord (aucune écriture, aucun LLM).
5. Frontend : section Réglages (CRUD), chip d'aperçu (résolues/inconnues),
   confirmation si inconnues, menu /.
