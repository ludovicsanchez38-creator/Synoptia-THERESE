# Chantier A — « La vérité »

> **NO-GO des deux relecteurs sur la version initiale (28/08).** Grok et Soso ont
> convergé : le design cassait quatre choses invisibles depuis le plan. Le
> chantier est **scindé** en conséquence.
>
> ## Ce qui a fait tomber la V1
>
> **A2 (gate sur la recherche web) casse quatre choses :**
>
> 1. `/confirm-tool` route tout outil intégré vers `execute_workspace_tool`, qui
>    **ne connaît pas** `web_search` — démontré à l'exécution :
>    `Outil inconnu : web_search`. La recherche ne fonctionnerait plus du tout.
> 2. `ToolConfirmationCard.tsx:67` présente tout outil non-calendrier comme un
>    **e-mail**, avec un bouton « Envoyer ».
> 3. Après confirmation, le résultat **n'est pas réinjecté au modèle** :
>    l'utilisateur recevrait des résultats bruts, sans reprise de génération.
> 4. Board, Deep Research et les agents appellent le service de recherche
>    **directement** (`board.py:284`, `deep_research.py:113`) : ils contourneraient
>    le gate. Une promesse de confirmation qui ne couvre pas ces chemins serait un
>    mensonge de plus.
>
> Soso corrige aussi le cadrage : « `web_search` n'est pas une mutation externe :
> c'est une **lecture avec exfiltration de la requête**. Ta taxonomie mélange deux
> risques. » Il propose un registre unique `ToolPolicy(effect, data_egress,
> confirmation, executor, continuation)`.
>
> **A6 (retry 401) est mal cadré :** je voulais exclure le SSE ; Soso démontre que
> le 401 du middleware arrive **avant** l'entrée dans la route (`main.py:700`),
> donc aucune génération n'a démarré et le rejeu est sûr. En revanche il ne faut
> **pas** rejouer « tout 401 » (Gmail, Groq, Sheets en renvoient aussi) : il faut
> un marqueur propre au middleware. Et `sidecar-status: running` est émis dès le
> `spawn`, avant que FastAPI soit prêt (`lib.rs:303`).
>
> **A5 (score) :** ni `min(100)` ni clamp d'affichage. Le maximum théorique est
> 170, `entities.py:37` documente déjà `0-100+`, et des overrides manuels existent
> sans champ de provenance — une migration par recalcul effacerait une intention
> utilisateur. Reste le libellé, qui est faux.
>
> ## Le chantier est scindé
>
> | Lot | Contenu | État |
> |---|---|---|
> | **A-texte** | Les affirmations fausses qui se corrigent par du texte et un test : bloc souveraineté, trois phrases de `PrivacyTab`, les libellés du score, « Connecté » | **en cours** |
> | **A-mécanique** | Le gate de confirmation web (A2) et le rejeu du 401 (A6) | **à redessiner**, design séparé |
>
> A-texte ne prétend rien corriger d'autre que ce qu'il dit. En particulier, tant
> que A-mécanique n'est pas livré, **la phrase corrigée devra avouer que la
> recherche web part sans confirmation** — dire vrai avant de réparer, c'est
> l'objet même du chantier.
>
> Le document ci-dessous est la V1, conservée pour mémoire.

---

# V1 (NO-GO) — design soumis à relecture AVANT code

Issu de la campagne dix personas du 28/08. Sept endroits où l'écran ou le prompt
système affirment quelque chose de faux. Trois personas sur dix sont partis
là-dessus, sur une ligne rouge professionnelle.

**Rien n'est codé. Ce document est là pour être démoli avant, pas après.**

---

## A1 — Le prompt ordonne de nier le chiffrement

### Le fait

`services/llm.py`, `SOVEREIGNTY_BLOCK` :

> « IMPORTANT (honnêteté sécurité) : la base SQLite n'est PAS chiffrée au repos.
> Ne prétends JAMAIS qu'elle est « chiffrée », « AES-256 » ou équivalent : ce
> serait faux. »

La base **est** chiffrée : SQLCipher AES-256, US-014 (`database.py:460-505`),
vérifié sur une base réelle (en-tête ≠ `SQLite format 3`).

`tests/test_regression.py::TestSovereigntyHonesty` **exige** cette phrase. Les
deux tests contradictoires sont verts simultanément.

### Ce que je propose d'écrire

Le message doit rester honnête sur ce qui **n'est pas** chiffré, sinon on
remplace un mensonge par un autre :

- `therese.db` : chiffrée (SQLCipher AES-256, clé dérivée du trousseau système).
- Échappatoire `THERESE_DB_PLAINTEXT=1` : si elle est posée, la base est en
  clair. Le prompt doit-il en parler ? **À trancher** (je penche pour non : c'est
  un drapeau de débogage, et le mentionner brouille le message).
- **Qdrant** : l'index vectoriel contient coordonnées et notes **en clair**
  (relevé par la contre-expertise).
- **`localStorage`** : les conversations non éphémères y sont sérialisées sans
  chiffrement applicatif (`chatStore.ts:426`).
- Les secrets (clés API, mots de passe) : Fernet + trousseau.

### Le test

`TestSovereigntyHonesty` est **retourné** : il doit désormais échouer si le bloc
affirme que la base n'est pas chiffrée, et exiger la mention de SQLCipher. Le
nom de la classe et son docstring (« NO-GO Syn 0.20.0 ») doivent être réécrits :
la raison d'être a changé.

**Question au relecteur** : faut-il garder une trace de l'ancien NO-GO dans le
commentaire, ou est-ce un poids mort qui fera croire à un retour en arrière ?

---

## A2 — La recherche web part sans confirmation

### Le fait

`web_search` et `browser_navigate` sont classés `MUTATION_EXTERNE`
(`contexte_execution.py:49-50`) mais absents de
`SENSITIVE_TOOL_NAMES = {"send_email", "create_calendar_event"}`.
Aucune confirmation. DuckDuckGo est le repli gratuit : rien à configurer pour
que ça parte. Le prompt système **pousse** activement à s'en servir
(`chat.py:2300` : « Ne dis JAMAIS que tu ne peux pas accéder à internet »).

### Le piège que j'ai trouvé et que je ne veux pas déclencher

Ma recommandation initiale disait « brancher le gate sur `MUTATION_EXTERNE`
plutôt que sur une liste tenue à la main ». **C'est dangereux** :

```python
def classe_de(nom: str) -> str:
    """Un outil MCP inconnu est externe par nature : dans le doute,
    la classe la plus prudente."""
    return CLASSIFICATION_DES_OUTILS.get(nom, MUTATION_EXTERNE)
```

Tout outil MCP est inconnu de la table, donc `MUTATION_EXTERNE`. Brancher le
gate dessus soumettrait **chaque appel d'outil MCP** à une carte de
confirmation. Un serveur MCP qui lit un fichier demanderait une validation à
chaque lecture. L'usage MCP deviendrait inutilisable.

### Les deux options

| | Option 1 — liste explicite | Option 2 — gate sur la classification, sauf inconnus |
|---|---|---|
| Geste | ajouter `web_search`, `browser_navigate` à `SENSITIVE_TOOL_NAMES` | `requires_confirmation` renvoie True si `CLASSIFICATION_DES_OUTILS.get(nom) == MUTATION_EXTERNE` (**`.get` sans défaut**, donc un inconnu ne déclenche rien) |
| Ferme la famille ? | non : le prochain outil externe repartira sans garde | oui, pour tout outil **déclaré** |
| Risque MCP | nul | nul (le défaut prudent de `classe_de` n'est pas utilisé ici) |
| Effet de bord | aucun | `send_email` est déjà `MUTATION_EXTERNE` → cohérent. `create_calendar_event` est `MUTATION_LOCALE` → **il faudrait le garder en dur**, sinon on lui retire sa confirmation |

**Je penche pour l'option 2**, avec `SENSITIVE_TOOL_NAMES` conservé comme
complément pour `create_calendar_event`. Mais l'asymétrie me gêne : deux
mécanismes pour une même décision, ce qui est exactement le vice que le chantier F
dénonce.

**Question au relecteur** : y a-t-il une troisième forme, où une seule table
porte à la fois la classe d'effet et l'exigence de confirmation ?

### Ce qui ne doit PAS changer

- Le fail-open sur empreinte incalculable (D1, v0.50.0).
- La déduplication par empreinte dans le tour courant.
- L'exemption des outils de lecture (`read_emails`, `search_files`…).

### Le test de complétude

Un test qui échoue si un outil déclaré `MUTATION_EXTERNE` n'est couvert par
aucun gate. C'est lui qui empêche les deux tables de diverger à nouveau.

---

## A3 — « Aucune donnée n'est envoyée à un serveur externe »

`PrivacyTab.tsx:253-256`. L'exception énoncée ne couvre que les modèles cloud.
La recherche web n'y est pas.

Après A2, une confirmation sera demandée — mais la phrase reste fausse telle
quelle, puisque la donnée **part** une fois confirmée. Proposition : énoncer les
deux sorties possibles (modèle cloud, recherche web) et dire que la seconde
demande une confirmation.

### Inventaire des sorties réseau, fait avant d'écrire la phrase

Je posais la question aux relecteurs. Je l'ai cherchée moi-même, et **il y en a
trois que je n'avais pas listées**. Sans elles, je réécrivais une phrase encore
fausse.

| Sortie | Vers | Choisie par l'utilisateur ? |
|---|---|---|
| Modèle cloud (Anthropic, OpenAI, Mistral, xAI, Google, OpenRouter, Perplexity, MiniMax…) | le fournisseur | oui, il le configure |
| `web_search` / `browser_navigate` | DuckDuckGo ou Brave | **non** — allumé par défaut, aucune confirmation (A2) |
| **Vérification de mise à jour** | `https://synoptia.fr/therese/alpha/latest.json` (`tauri.conf.json:72`) | **non** — automatique. Sortie vers **Synoptïa** |
| **Modèle d'embeddings** | `huggingface.co` (`nomic-ai/nomic-embed-text-v1.5`) | **non** — téléchargé au premier usage |
| **Modèles de voix locale** | `huggingface.co` (Whisper / Piper) | à l'activation, ~145 Mo |
| OAuth messagerie / agenda | Google | oui |

**Aucune télémétrie, aucun analytics** : recherche `telemetry|analytics|sentry|posthog|matomo` → zéro résultat. C'est un point à dire, il est bon.

La phrase corrigée doit donc distinguer trois choses : ce qui **reste** sur la
machine (les données métier), ce qui **sort sur décision** de l'utilisateur
(modèle cloud, messagerie), et ce qui **sort sans qu'il l'ait demandé**
(vérification de mise à jour, téléchargement des modèles) — ces dernières étant
des sorties techniques qui n'emportent pas de données métier, ce qu'il faut dire
plutôt que taire.

**Question qui reste au relecteur** : la vérification de mise à jour emporte-t-elle
autre chose que l'IP et la version courante ? Et faut-il un réglage pour la
couper ?

---

## A4 — « Pas de données personnelles tierces »

`PrivacyTab.tsx:50`, justification de la conservation illimitée des
conversations. Faux dès qu'un utilisateur tape un nom dans le chat — ce que le
médecin a fait en trente secondes.

Correctif : dire ce qui est vrai (les conversations peuvent contenir tout ce que
l'utilisateur y écrit, y compris des données personnelles de tiers) et, si une
justification RGPD est nécessaire, la rattacher à l'intérêt légitime de
l'utilisateur qui reste maître de ses effacements.

**Je ne suis pas juriste.** Cette ligne est dans une table de durées de
conservation qui a une portée réglementaire. Je propose de corriger l'assertion
factuelle et de **signaler** que le fond RGPD demande un avis.

---

## A5 — Le score « de 0 à 100 » monte à 145

`scoring.py:88` : `return max(0, score)`, borné en bas seulement.
`PipelineView.tsx:274` et `:281` (infobulle **et** `aria-label`) annoncent
« de 0 à 100 ». Preuve : 4 contacts sur 8 au-dessus de 100 pendant la campagne,
trois à 145, sans aucune activité.

Deux réponses possibles : borner (`min(100, ...)`) ou corriger le libellé.

**Je penche pour borner**, parce qu'un score non borné n'est pas comparable
entre contacts. Mais cela change des valeurs existantes en base.

**Question au relecteur** : borner à l'affichage ou au calcul ? Le calcul est
persisté (`score` en base, `scoring.py` écrit) ; borner au calcul ne rétroagit
pas sur les scores déjà stockés, ce qui laisserait des 145 en base et des 100 à
l'écran. Faut-il une migration, ou borner à l'affichage suffit-il ?

---

## A6 — Le 401 muet après une relance du moteur

`core.ts:93-110` charge le token **une fois**. Aucune ligne ne traite un 401.
Tauri relance pourtant le sidecar (jusqu'à 3 tentatives, `lib.rs:375`), et
chaque démarrage génère un **nouveau** token. Après relance, tout retourne 401
et le bandeau annonce que le moteur est reparti.

Vécu par l'écrivaine, qui a arrêté d'essayer.

### Proposition

1. Dans `apiFetch` : sur 401, vider `_sessionToken`, rappeler `initializeAuth()`,
   **rejouer la requête une seule fois**. Un second 401 remonte.
2. Écouter `sidecar-status: running` et recharger le token à ce moment.

### Les pièges que je vois

- **Le flux SSE** : `POST /api/chat/send` est un flux. Rejouer une requête de
  chat après un 401 relancerait une génération — donc potentiellement un
  **second appel d'outil**. Le retry doit-il exclure les requêtes de streaming ?
  Je pense que oui, mais je veux un avis.
- **Les requêtes concurrentes** : dix appels partent, tous prennent un 401, tous
  rappellent `initializeAuth()`. Il faut une promesse partagée (le fichier a déjà
  ce motif avec `_initPromise` pour `initApiBase`).
- **Boucle** : si le backend renvoie 401 en permanence (token jamais prêt), le
  retry unique évite la boucle, mais il faut vérifier que `initializeAuth()`
  échoue proprement.

**Question au relecteur** : le retry doit-il porter sur `apiFetch` (tout) ou
seulement sur les appels non-streaming ? Et faut-il un test qui simule un
changement de token côté serveur ?

---

## Ce que ce chantier ne fait PAS

- Il ne touche pas au cloisonnement (chantier C).
- Il ne touche pas à l'accueil (chantier D).
- Il n'implémente pas l'envoi de facture (chantier B).
- Il ne réécrit pas le prompt système au-delà du bloc souveraineté.

## Vérification prévue

TDD strict : test rouge d'abord, vérifié rouge pour la bonne raison, puis
**preuve par sabotage** (copie du fichier, pas remplacement inverse). Gates
complets dans l'ordre : ruff, pytest hors e2e (lire le XML), vitest, tsc,
eslint 27, mypy fresh (baseline 1001). Puis relecture du diff.
