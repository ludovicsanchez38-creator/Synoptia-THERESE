# Chantier 4 - Variables V1 - Design V4 (11/07/2026, après NO-GO Codex)

> V3 challengée par Codex (verdict NO-GO, 12 findings dont 4 critiques,
> `scratchpad codex_variables_out2.log`). Findings lourds (1-5, 8) VÉRIFIÉS
> empiriquement le 11/07 : ReDoS mesuré 5,6 s sur 3000 espaces, directive
> inline exécutée depuis un sujet `produire` (préexistant), asymétries
> stream/non-stream et trou de ré-estampillage lus dans le code. La V4 ferme
> les findings 1-12. Apports Dr_logic (nuit 10-11/07) inchangés : scalaire ou
> liste, créer/remplacer/ajouter/supprimer, manipulation chat zéro-LLM,
> mémoire de travail.

## Décision d'architecture (finding 10)

Fonction pure **`prepare_chat_plan(raw, variables_snapshot) -> ChatPlan`**
(nouveau service `chat_plan.py`) : TOUTE la classification déterministe
(message-action, slash, directives inline, commandes /fichier /analyse,
skill forcé {{action:}}), puis résolution des variables, en UN SEUL point.
Retourne : type de chemin (action locale / slash / produire / llm), texte
LLM final résolu, commandes classifiées, inconnues, erreurs de borne,
`variables_revision` (hash). send_message EXÉCUTE le plan (effets séparés) ;
`POST /api/variables/preview` APPELLE la même fonction sans effets. Aucun
parseur ne retouche JAMAIS un texte dérivé ou résolu.

## Tranche 0 - Durcissement préexistant (AVANT toute variable ; bugs réels dès aujourd'hui)

- **0a ReDoS (finding 5)** : garde de longueur dans `parse_action_message`
  (enveloppe `{action:` + longueur > 2000 -> réponse locale « syntaxe
  invalide », pas de regex) + réécriture `_ACTION_MESSAGE`/`_PRODUIRE` sans
  quantificateurs de blancs concurrents (alternance exacte, IGNORECASE limité
  au mot-clé). Sujet blanc `"   "` -> rejet explicite. Enveloppe reconnue
  mais corps invalide -> réponse locale, jamais le LLM (fin du fallback
  silencieux `kind=unknown` -> LLM pour une enveloppe malformée).
- **0b produire immuable (finding 1, VÉRIFIÉ)** : le prompt de rédaction vit
  dans une variable dédiée du plan, `request.message` n'est PLUS muté ; la
  branche produire saute slash/inline/skill-detect (skill déjà forcé). Test :
  sujet contenant `[contact: X]`, `/contact`, `/fichier` -> AUCUN effet.
- **0c skill figé (finding 3, VÉRIFIÉ)** : `resolve_skill_from_message` reçoit
  le message BRUT (jamais le résolu) ; parité stream/non-stream documentée.
- **0d safety sur le bon payload (finding 4, VÉRIFIÉ)** : `check_prompt_safety`
  contrôle LE texte final envoyé au LLM (résolu), sur les DEUX chemins.
- **0e /fichier /analyse sur le brut (finding 2, VÉRIFIÉ)** :
  `_parse_file_commands` tourne UNE fois sur le brut dans le plan, résultats
  passés explicitement au streaming - plus aucune redétection sur texte dérivé.
- **0f historique (finding 4)** : les échanges déterministes sont EXCLUS du
  contexte LLM - tag `extra_data.deterministic` posé sur le message user à la
  classification + filtre history sur ce tag et sur
  `model in (action-deterministe, commande-deterministe)` (les legacy user
  restent : bruit sans risque, documenté).

## Tranche 1 - Modèle (findings 7, 8, 11)

Entité SQLModel `Variable` : **`id` UUID PK + `name` UNIQUE** (renommage
possible plus tard), `kind` (`text`|`list`, CHECK), `value` TEXT = JSON
(`str` si text, `list[str]` si list - invariant kind/value validé par UNE
fonction partagée API/chat), `description`, `created_at`/`updated_at`.
Limites : 100 variables, scalaire 4000 c., liste 100 x 500 c., description
200, nom `[a-z0-9_]{1,32}`, réservés `action|aide|variable|variables`.
- Migration : CREATE TABLE ad-hoc idempotent (`apply_adhoc_migrations`) +
  révision Alembic + bump `ALEMBIC_HEAD_REVISION`. **Fermeture finding 8** :
  la preuve de schéma du ré-estampillage exige AUSSI la table `variables`
  (pas seulement `invoices.validite_jours`). Tests : ancienne tête -> nouvelle
  (la migration tourne), boot desktop (ad-hoc seule), base neuve (create_all),
  restauration d'un backup pré-Variables.
- RGPD (finding 11) : ajout explicite à l'export `/api/data/all` (+ bump
  `data_format_version`) ET à la purge ; valeurs REJETÉES si
  `check_prompt_safety` les bloque (fermeture du vecteur « valeur stockée puis
  rejouée ») ; jamais de valeur dans les logs (test V2 rétabli). Backups :
  couverts via therese.db, rétention inchangée - dit honnêtement dans l'UI
  (une purge ne réécrit ni les backups ni l'historique passé). Dette notée :
  `/api/config/export` (4 modèles) n'est PAS l'export canonique.

## Tranche 2 - Verbes chat (finding 6, 12)

```text
{action: variable creer courses liste}       -> refus si existe (« existe déjà, utilise remplacer »)
{action: variable creer titre "Mon rapport"}
{action: variable remplacer titre "Autre"}   -> verbe explicite, écrasement assumé
{action: variable ajouter courses "tomates"} -> append liste / concat + espace scalaire
{action: variable supprimer courses}         -> confirmation dans la réponse (valeur perdue)
{action: variable afficher courses}
{action: variables}
```

- `creer` sur existant = REFUS explicite (jamais d'écrasement silencieux -
  aligné sur la sémantique /contact). API : POST 409, PUT remplace.
- Valeurs de mutation : texte Unicode arbitraire borné, guillemets droits ou
  français, SANS `{` `}` ni retour ligne (rejet explicite - tue récursion et
  ambiguïtés d'échappement à la source). Chaîne vide interdite. AUCUNE
  substitution dans les commandes de mutation (testé).
- `check_prompt_safety` sur toute valeur entrante (chat ET API).
- EXCLUS V1 (documenté dans `{action: aide}`) : retirer un élément, renommer,
  conversion de type, fusion, tri/SQL, alimentation externe.

## Tranche 3 - Substitution + preview (findings 9, 10)

- Substitution `{nom}` par `prepare_chat_plan` : chat principal (texte LLM
  final) + sujet `produire` UNIQUEMENT (jamais verbe/format/cible - le corps
  d'action n'accepte que des tokens `\{[a-z0-9_]{1,32}\}` par alternance
  exacte). Single-pass : valeurs jamais re-scannées (ni actions, ni slash,
  ni /fichier, ni tokens - testé avec valeurs simulant CHAQUE syntaxe).
  Inconnue -> token laissé tel quel. `{{nom}}` -> littéral `{nom}` (sans
  collision `{{action:`, testé). Listes : `- élément` par ligne dans un
  prompt produire, `, ` inline sinon.
- **Bornes d'expansion (finding 9)** : ≤ 20 tokens par message, texte résolu
  ≤ 60 000 c. - dépassement = réponse locale explicite, AUCUN appel LLM,
  même erreur dans preview et send.
- **Persistance : le BRUT est l'historique** (décision explicite finding 10) :
  la bulle et la base gardent ce que l'utilisateur a tapé ; le résolu ne vit
  que dans le payload LLM du tour courant ; JAMAIS de re-résolution
  rétroactive ; l'historique rejoué reste brut (limitation documentée :
  l'assistant voit la valeur dans le tour où elle est utilisée).
- Preview : `{resolved, unknown[], errors[], variables_revision}` - le
  frontend renvoie `variables_revision` à l'envoi ; s'il a changé, le backend
  résout avec l'état courant (pas d'erreur, mais le chip se rafraîchit).

## Tranche 4 - Frontend

- Réglages > Services > « Variables » : CRUD complet, bandeau honnêteté
  (« les valeurs sont envoyées au modèle à l'usage, vivent dans la base et
  l'historique - pas un coffre à secrets »).
- ChatInput : token `{nom}` détecté -> preview debounced, chip « N résolues,
  M inconnues » ; confirmation d'envoi UNIQUEMENT si inconnues.
- Menu `/` : entrées variable ; `{action: aide}` liste les verbes.
- Périmètre V1 : chat principal + sujet produire. Deep Research, Board,
  agents, Atelier : AUCUNE substitution (testé pour au moins un).

## Ordre TDD

0a -> 0b -> 0c/0d/0e -> 0f (chaque étape = RED d'abord, gates après le lot)
puis 1 -> 2 -> 3 -> 4. La tranche 0 est commitable seule (fix sécurité
autonome, releasable même sans variables).
