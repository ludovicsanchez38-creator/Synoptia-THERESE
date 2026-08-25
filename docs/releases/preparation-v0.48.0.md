# Préparation v0.48.0 - état au 25/08/2026 (soir)

> Branche `feat/0.48-etabli`, 19 commits. **PAS releasé** : la passe Soso
> finale attend la recharge des crédits Codex, et la release attend le GO
> explicite de Ludo.

## Périmètre livré (arbitrage Ludo : lot A + P1 + P3, le reste en backlog)

- **A1 - Board frontier + effort max** : catalogue neutre
  (`modeles_catalogue.py`, source unique, tête de liste = frontier
  éditorial, politique d'effort à 3 états), effort résolu PAR CONSTRUCTION
  de `LLMConfig` (`__post_init__`), les 4 tables de llm.py dérivées du
  catalogue, providers sans table locale d'effort, transport du content
  BRUT Mistral reasoning de bout en bout (BUG-108 préservé), repli Grok
  400 (`_stream_request` extrait), conseillers cloud en
  frontier + effort max + max_tokens (recommandé ou plancher 16000),
  `bascule_circuit=False` (repli EXPLICITE seulement).
- **B0 - manifeste au tiroir** : binding `{registre: "tiroir", carte}`,
  6 capacités nouvelles, registre canonique des cartes
  (`lib/capacites/cartes.ts`), `/aide` annonce « Plus d'outils → X »,
  gate de parité étendu.
- **C - lexique + frontière d'erreurs** : test de lexique sur les
  registres EXPORTÉS (interdits : sidecar, fencing, Qdrant,
  generation_id, tools, BYOK, LLM, MCP, provider), nommages imposés
  (Travaux, Décision, Contacts, Pipeline, Agenda, Devis et factures,
  Rédiger un document, Améliorer THÉRÈSE, Connecteurs, Service d'IA,
  Paramètres), `message_pour_ecran`/`ErreurPourEcran`
  (error_handler.py étendu), table dans `docs/rules/RULES-DESIGN.md`.
- **B1 - établi/tiroir** : `lib/etabli.ts` (Écrire, Retrouver, Préparer,
  Facturer - suivie par palette ⌘K et « Essayer un autre parcours »),
  porte « Plus d'outils », bouton « Capacités » du composeur retiré,
  état vide honnête du brief (`has_email`), placeholder partagé.
- **A2 - sonde de dérive** : 1×/jour Europe/Paris, mode CLOUD seulement,
  parallèle timeout 6 s, pages larges (limit/pageSize 1000), dérive =
  frontier absent, chunk `catalogue_status`, `modele_deprecie` par
  AdvisorInfo, JAMAIS de bascule de modèle.

## Revue (le rituel, état à ce soir)

| Passe | Verdict | Findings | État |
|---|---|---|---|
| Soso 1 | NO-GO | 6 (1 bloquant Infomaniak, trim, circuit breaker, frontière, ErreurPourEcran, lexique parseur) | tous contre-vérifiés puis fermés |
| Soso 2 | NO-GO | 4 (str(e) à la source des providers, avis Board vide validé, trim début+fin, affordances chat) | tous fermés |
| Soso 3 | **interrompue** - crédits du workspace Codex épuisés | - | à relancer après recharge |
| Auto-contrôle | - | 1 (circuit breaker aveugle aux pannes réseau converties) | fermé (forme classée réseau/interne) |
| Panel interne (remplacement p3, AVANT la consigne 5 agents) | - | 21 confirmés / 12 réfutés / 48 invariants sains | tous fermés |

Points marquants du panel : `record_failure` compté AVANT le raise de
`raise_on_error` (le repli Board ne s'enclenchait jamais), ollama rejoint
la frontière des providers, sonde coupée en souverain, plancher
max_tokens des conseillers (effort max : le raisonnement décompte du
plafond), prix des 5 frontiers relevés aux sources officielles le 25/08
(opus-5 5/25, gpt-5.6-sol 4/20, gemini-3.7-flash 0.75/3.75 en vigueur,
mistral-medium-3-5 1.5/7.5, grok-4.6 2/6 - le Board n'affiche plus
0,00 €), lexique appliqué aux surfaces restantes (⌘/, onboarding,
ToolsPanel, BoardPanel, images).

> NB : la dimension « chemins d'erreur Board de bout en bout » du panel a
> été bloquée par un garde-fou du modèle ; elle est couverte
> indirectement (2 findings majeurs providers-consommateurs + les tests
> raise_on_error). À re-balayer dans la passe Soso finale.

## Gates au dernier commit

| Gate | Résultat |
|---|---|
| pytest (hors e2e) | 2246 verts, 0 échec |
| vitest | 872 verts |
| mypy fresh | 1001 (main 1002, baseline CI 1004) |
| ruff / tsc / eslint | propres (eslint 27/27) |

## Reste avant release

1. Recharger les crédits Codex (Ludo) → passe Soso finale sur le diff.
   Le prompt de cette passe DOIT nommer : (a) les chemins d'erreur du
   Board de bout en bout (dimension jamais balayée - sceptique du panel
   bloqué par un garde-fou) ; (b) les deux findings ui-etabli-sonde
   (plancher max_tokens conseillers, sonde coupée en souverain) fermés
   sans vérification adversariale (leurs réfuteurs ont sauté avec la
   limite de session) ; (c) les remédiations du panel elles-mêmes comme
   cibles de régression (motif confirmé trois fois dans la session).
2. GO explicite de Ludo → `/release-therese` (le « go dès le GO de Soso »
   valait pour la 0.47 seulement).

## Dette actée en cours de route

- Chemin chat stream : le `return` post-annulation saute la comptabilité
  du circuit breaker (trou jumeau PRÉEXISTANT du point corrigé, noté par
  le panel).
- Bascule cloud du circuit breaker chez un utilisateur souverain à clé
  cloud stockée : comportement préexistant (US-006), question de
  souveraineté à trancher un jour.
- Backlog audit Grok : `docs/revue-produit/02-backlog-audit-grok.md`.
- Validation réelle Mistral reasoning (pattern BUG-108) : conditions
  réelles nécessaires.
- Consigne durable posée ce jour : **5 agents max** par workflow
  multi-agents (le panel à 72 agents a épuisé la limite de session).
