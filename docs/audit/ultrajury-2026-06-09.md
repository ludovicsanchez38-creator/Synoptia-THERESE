# UltraJury - Rapport d'Audit THÉRÈSE Desktop v0.21.0-alpha

**Projet** : THÉRÈSE v2 (app desktop Tauri 2.0 - React/TS + FastAPI Python sidecar)
**Type** : Fullstack desktop (SEO skippé, 11 axes)
**Date** : 9 juin 2026
**Score global** : 70.5/100
**Delta** : -2.9 vs 73.4 (27 mars 2026, v0.7.2)
**Prisme** : Solopreneur/indépendant français, local-first
**Auditeur** : Claude Fable 5 (UltraJury 6 phases : 11 agents + 8 cross-reviews)

> **Lecture du delta** : la baisse de 2.9 points ne signifie pas une régression du produit. Entre v0.7.2 et v0.21.0, le code a quasiment doublé (~105K LOC), 14 versions sont sorties, et cette édition de l'audit a vérifié chaque affirmation par cross-review (8 binômes, tous les ajustements à la baisse sauf Produit). Le score mesure un produit plus grand audité plus durement. Variance LLM intrinsèque : ±5 points.

## Tableau des scores

| # | Axe | Brute | Ajustée | Poids | Pondéré | Delta vs 27/03 |
|---|-----|-------|---------|-------|---------|-------|
| 1 | Performance | 79 | 77.0 | 10.9% | 8.39 | +4 |
| 2 | Sécurité | 74 | 71.5 | 10.9% | 7.79 | -7.5 |
| 3 | Accessibilité | 68 | 66.0 | 8.7% | 5.74 | -6 |
| 4 | Architecture | 70 | 68.7 | 13.0% | 8.93 | -4.3 |
| 5 | Frontend | 78 | 76.0 | 10.9% | 8.28 | -2 |
| 6 | DevOps | 63 | 63.0 | 8.7% | 5.48 | -5 |
| 7 | Qualité Code | 73 | 72.0 | 10.9% | 7.85 | +6 |
| 8 | Résilience | 68 | 66.0 | 7.6% | 5.02 | -6 |
| 9 | Conformité | 82 | 77.0 | 7.6% | 5.85 | -1 |
| 10 | Produit | 63 | 66.0 | 5.4% | 3.56 | -12 |
| 11 | Contenu | 69 | 66.5 | 5.4% | 3.59 | -5.5 |
| | **TOTAL** | | | **100%** | **70.5** | **-2.9** |

## Radar

```
Performance   : ████████░░ 77
Conformité    : ████████░░ 77
Frontend      : ████████░░ 76
Qualité Code  : ███████░░░ 72
Sécurité      : ███████░░░ 71.5
Architecture  : ███████░░░ 68.7
Contenu       : ███████░░░ 66.5
Accessibilité : ███████░░░ 66
Résilience    : ███████░░░ 66
Produit       : ███████░░░ 66
DevOps        : ██████░░░░ 63
```

## Problèmes critiques (action immédiate)

1. **RCE in-process via le sandbox d'exécution de code** : `code_executor.py` bloque par regex mais pas l'introspection dunder (`().__class__.__base__.__subclasses__()`), et `exec()` tourne dans le même interpréteur que le `session_token` et la clé Fernet. Déclenchable par prompt injection (email/page lus par le LLM). `code_executor.py:43,703-704`.
2. **Aucune confirmation humaine dans la boucle d'outils** : `send_email` s'exécute en autonomie totale (dispatch if/elif sans registre de permissions, `chat.py:1136-1251`) → exfiltration possible par injection.
3. **Graceful shutdown jamais exécuté** : `/api/shutdown` exige le token d'auth mais ses 2 appelants (Tauri TCP brut, UpdateBanner fetch nu) ne l'envoient pas → 401 systématique, force-kill à chaque fermeture, BUG-099 (verrou backend.exe pendant update Windows) réactivé. `main.py:535-540`, `lib.rs:404-423`.
4. **README mensonger sur l'argument n°1** : « contexte stocké et chiffré » (README.md:34) alors que le SOVEREIGNTY_BLOCK de `llm.py` interdit ce claim à l'app elle-même. Plus badge 0.7.0-alpha, lien `anthropics/openclaw` en 404, cible « mairies » incohérente.
5. **Effacement RGPD art. 17 incomplet** : les `EmailMessage` du contact anonymisé restent intacts avec FK ; la purge Qdrant post-commit sans retry peut laisser un vecteur fantôme définitif. `rgpd.py:155-255`, `rgpd_auto.py:110,212-218`. Plus « Ne mentionne jamais que tu es une IA » dans le générateur d'emails.
6. **Updater auto structurellement mort + binaires non signés** : pubkey vide, aucun `.sig`/`latest.json`, endpoint `releases/latest` = 404 (toutes les releases sont prerelease) → aucun canal de patch sécurité vers le parc installé. `tauri.conf.json:73`.

## Découvertes des cross-reviews (au-delà des agents)

- Le rate limiter fallback est un **no-op total** (bug `del`+`return` avant `append`) et slowapi sans `default_limits` ne limite rien ; le log « rate limiting active » est faux.
- `/health/services` plante en permanence (`execute("SELECT 1")` sans `text()` sous SQLAlchemy 2.x, **prouvé par exécution**) → `database: false` constant ; `/health` global ne teste pas la DB.
- `remark-gfm` absent → **les tableaux markdown du LLM ne se rendent pas** alors que les renderers `table/th/td` sont déjà codés (`MessageBubble.tsx:341-363`).
- Le chemin Alembic est **incompatible** avec les DB existantes (pas de stamp `alembic_version` sur les bases `create_all`).
- Dès le 1er flush de streaming, `isStreaming` passe à `false` → re-parse ReactMarkdown complet à chaque flush + curseur de streaming mort.
- Le finding « dictée vocale indisponible en desktop » était **inversé** : le plugin natif existe depuis le 05/02 (`tauri-plugin-mic-recorder`), c'est le guide qui est faux — défaut de relecture doc, pas de produit.
- `lib.rs:277-288` supprime la quarantaine macOS au runtime (contournement Gatekeeper automatisé) — angle mort de l'agent Sécurité.
- MCP : `validate_mcp_command` whiteliste `npx/uvx/bun/docker/deno` qui exécutent du code distant arbitraire sans pinning.

## Top 10 Recommandations

| # | Recommandation | Impact | Effort | Axes | Priorité |
|---|---------------|--------|--------|------|----------|
| 1 | Sandbox réelle : exec() en sous-process isolé + blocage dunder | Haut | Élevé | Sécu | P0 |
| 2 | Confirmation humaine avant send_email et actions sortantes | Haut | Moyen | Sécu, UX | P0 |
| 3 | RGPD : effacement emails du contact anonymisé + purge Qdrant fiable + retirer « jamais une IA » | Haut | Moyen | Conformité | P0 |
| 4 | README véridique (chiffrement, badge, lien 404, cible) | Haut | Faible | Contenu | P0 |
| 5 | Réparer /api/shutdown (exempt ou token) + test de régression | Haut | Faible | Résilience | P0 |
| 6 | Signer les binaires + réactiver l'updater (pubkey, latest.json, canal prerelease) | Haut | Élevé | DevOps | P1 |
| 7 | Brancher la résilience : text("SELECT 1"), circuit breaker sur 429/5xx streaming, retry câblé, timeout CalDAV | Haut | Moyen | Résilience | P1 |
| 8 | Streaming chat : memo réparé, persist débouncé, virtualisation (react-virtuoso déjà installé), remark-gfm | Haut | Moyen | Perf, Frontend | P1 |
| 9 | Capacité tools par provider (supports_tools) + avertissement UI Grok/Gemini/Ollama | Moyen | Moyen | Archi, Produit | P1 |
| 10 | A11y AA : DialogShell généralisé, text-yellow-400 du thème clair, MotionConfig global | Moyen | Élevé | A11y | P1 |

### Matrice Impact x Effort

```
             Effort faible          Effort moyen              Effort élevé
Impact haut  README (4),            Confirmation outils (2),  Sandbox (1),
             shutdown (5),          RGPD (3), résilience (7), signature+updater (6)
             health SELECT 1        streaming chat (8)
Impact moyen rate limit réel,       tools par provider (9),   a11y AA (10),
             accents erreurs        guide utilisateur         migrations unifiées
Impact bas   fichier { parasite,    architecture.md           refactor routers obèses
             tu/vous Accueil
```

## Plan d'action

### Semaine 1 (Quick Wins + P0)
- README véridique (US-004, 1h), /api/shutdown (US-005), text("SELECT 1") (1 ligne), rate limiting réel
- Démarrer sandbox (US-001) et confirmation humaine (US-002)

### Semaines 2-3 (Structurel)
- RGPD complet (US-003), résilience branchée (US-008), streaming chat (US-010), backup complet (US-011)
- Signature binaires + updater (US-007, chantier certificats)

### Mois 2+ (Évolutions)
- Chiffrement DB au repos (US-014, tenir la promesse), migrations Alembic unifiées (US-015)
- A11y AA (US-013), contenu/docs (US-017), CI bloquante (US-018), perf démarrage (US-016)

## Forces confirmées (à préserver)

- **Conformité RGPD outillée** rare pour une alpha : router dédié 9 endpoints, purge auto planifiée, zéro télémétrie, licences 100 % compatibles AGPL.
- **Cycle de vie sidecar exemplaire** : kill zombies, locks Qdrant, splash robuste, logs JSON rotatifs avec masquage de secrets.
- **SQLite finement réglé** (WAL, 34+10 index, N+1 traités) et **streaming SSE instrumenté** (first-token, p95, /api/perf).
- **Persona et garde-fous system prompts** (SOVEREIGNTY_BLOCK anti-hallucination) + changelog vulgarisé exemplaire.
- **CI 4 jobs réelle** (ruff vert, tsc, vitest, build) et versioning industrialisé (bump 7 fichiers synchronisés).

## Résumé exécutif

THÉRÈSE 0.21.0-alpha est un produit étonnamment large et soigné pour une alpha, avec des fondations réelles (RGPD, sidecar, DB, CI) mais une couche de « défenses déclarées non branchées » : rate limiting inerte, retry mort, circuit breaker aveugle, shutdown en 401, updater incapable de livrer une mise à jour. Les deux urgences sont la fermeture du vecteur prompt injection → exec()/send_email, et l'alignement de la promesse publique (chiffrement) sur la réalité technique. Le backlog de 18 stories (5 P0) est prêt dans `backlog-2026-06-09.md`.
