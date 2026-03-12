# UltraJury - Rapport d'Audit THERESE v2

**Projet** : THERESE v2 - L'assistante souveraine des entrepreneurs francais
**Date** : 12 mars 2026
**Stack** : Tauri 2.0 + React 19 + TailwindCSS 4 + FastAPI Python + SQLite + Qdrant
**Taille** : 406 fichiers source, 163K lignes (62K Python, 39K TS/React, 499 Rust)
**Version** : v0.6.1-alpha

---

## Score global : 64.1/100

## Tableau des scores

| # | Axe | Note /100 | Poids | Pondere | Tendance |
|---|-----|-----------|-------|---------|----------|
| 1 | Architecture | 65 | 12% | 7.80 | - |
| 2 | Securite | 70 | 10% | 7.00 | - |
| 3 | Frontend | 71 | 10% | 7.10 | + |
| 4 | Performance | 67 | 10% | 6.70 | - |
| 5 | Qualite Code | 59 | 10% | 5.90 | - |
| 6 | SEO/Discoverability | 59 | 8% | 4.72 | - |
| 7 | Accessibilite | 62 | 8% | 4.96 | - |
| 8 | DevOps | 55 | 8% | 4.40 | - |
| 9 | Resilience | 58 | 7% | 4.06 | - |
| 10 | Conformite | 68 | 7% | 4.76 | + |
| 11 | Contenu | 68 | 5% | 3.40 | - |
| 12 | Produit | 65 | 5% | 3.25 | + |
| | **TOTAL** | | **100%** | **64.1** | |

## Radar

```
Architecture   : ██████▓░░░ 65
Securite       : ███████░░░ 70
Frontend       : ███████░░░ 71
Performance    : ██████▓░░░ 67
Qualite Code   : █████▓░░░░ 59
SEO            : █████▓░░░░ 59
Accessibilite  : ██████░░░░ 62
DevOps         : █████▓░░░░ 55
Resilience     : █████▓░░░░ 58
Conformite     : ██████▓░░░ 68
Contenu        : ██████▓░░░ 68
Produit        : ██████▓░░░ 65
```

---

## Plan d'action complet

### Matrice Impact x Effort

```
              Effort faible       Effort moyen        Effort eleve
Impact   [QUICK WINS]         [PLANIFIER]          [LONG TERME]
haut     #1,#2,#3,#4,#5      #9,#10,#12,#14       #15 tour guide
         #6,#7,#8,#11

Impact   [FAIRE]              [POSSIBLE]           [EVITER]
moyen    #13 CI fix           Refactor ChatInput    Signature code
                              Refactor ChatLayout   Auto-update Tauri

Impact   [SI TEMPS]           [BACKLOG]            [NON]
faible   Badges FR/EN         i18n complet         -
```

---

## P0 - Quick Wins (Semaine 1)

Objectif : +10 points (64 -> ~74/100)

| # | Recommandation | Impact | Effort | Axes | PR | Statut |
|---|---------------|--------|--------|------|-----|--------|
| 1 | Accents manquants `actionData.ts` + `CommandPalette.tsx` + `chat.py` | Haut | Faible | Contenu, A11y | #40 | FAIT |
| 2 | `React.lazy` panneaux + `react-syntax-highlighter/light` | Haut | Faible | Perf (-266KB), Archi | #41 | FAIT |
| 3 | Corriger `delete_backup` path traversal (copier validation de `restore_backup`) | Haut | Faible | Secu, Conformite | #39 | FAIT |
| 4 | Retirer `/api/shutdown` de `exempt_paths` | Haut | Faible | Securite | #39 | FAIT |
| 5 | Creer `<DialogShell>` avec `role="dialog"` + focus trap (8 modales) | Haut | Faible | A11y | - | TODO |
| 6 | ErrorBoundary global dans `App.tsx` | Haut | Faible | Frontend, Resilience | #43 | FAIT |
| 7 | Landmarks ARIA (`<main>`, `<nav>`) + skip link | Haut | Faible | Accessibilite | #43 | FAIT |
| 8 | Licence MIT -> AGPL dans `package.json` + `Cargo.toml` + URL repo | Haut | Faible | SEO, Conformite | #38 | FAIT |
| 11 | Supprimer `old_name` du log d'anonymisation RGPD | Haut | Faible | Conformite | #39 | FAIT |
| 13 | Remplacer `exit 0` sur timeout CI par warning + fail | Moyen | Faible | DevOps, Secu | #42 | FAIT |

**Bilan P0** : 9/10 faits (PRs #38-#43). Reste : #5 DialogShell.

---

## P1 - Structurel (Semaines 2-3)

Objectif : +8 points supplementaires (~74 -> ~82/100)

| # | Recommandation | Impact | Effort | Axes | Statut |
|---|---------------|--------|--------|------|--------|
| 9 | Job CI `security-audit` (npm audit + pip-audit + gitleaks) | Haut | Moyen | Secu, DevOps | FAIT (PR #42) |
| 10 | Completer `DELETE /api/data/all` (9 tables manquantes + purge Qdrant) | Haut | Moyen | Conformite RGPD, Resilience | TODO |
| 12 | Activer Ruff `B`+`C90`+`SIM` (bugbear, complexite, simplification) | Haut | Moyen | Qualite Code, Archi | TODO |
| 14 | Singleton SQLite sync dans `llm.py` (remplacer 4 `create_engine`) | Haut | Moyen | Perf, Archi | TODO |
| 16 | Script sync versions (backend `__init__.py`, `Cargo.toml`, `package.json`, `tauri.conf.json`) | Moyen | Faible | DevOps, Qualite Code | TODO |
| 17 | Refactorer `_do_stream_response` (295L -> 5 sous-fonctions) | Moyen | Moyen | Archi, Qualite Code | TODO |
| 18 | Refactorer ChatInput.tsx (864L -> sous-composants) | Moyen | Moyen | Frontend, Archi | TODO |
| 19 | Brancher `useReducedMotion` dans `animations.ts` | Moyen | Faible | A11y | TODO |
| 20 | Refactorer ChatLayout.tsx (17 useState -> store/useReducer) | Moyen | Moyen | Frontend, Archi | TODO |

---

## P2 - Evolutions (Mois 2+)

Objectif : 82 -> 90/100

| # | Recommandation | Impact | Effort | Axes | Statut |
|---|---------------|--------|--------|------|--------|
| 15 | Tour guide post-onboarding (time-to-first-value) | Haut | Eleve | Produit | TODO |
| 21 | Package `services/crm/` (2793L flat -> package avec sous-modules) | Moyen | Moyen | Archi | TODO |
| 22 | Circuit breaker + retry sur providers LLM | Haut | Moyen | Resilience | TODO |
| 23 | Detection offline frontend (Service Worker ou navigator.onLine) | Moyen | Moyen | Resilience | TODO |
| 24 | Politique de confidentialite (PRIVACY.md) | Moyen | Faible | Conformite | TODO |
| 25 | Monitoring erreurs (Sentry ou equivalent self-hosted) | Haut | Moyen | DevOps, Resilience | TODO |
| 26 | Tests E2E Playwright (parcours critique : onboarding -> chat -> export) | Haut | Eleve | Qualite Code, DevOps | TODO |

---

## P3 - Backlog long terme

Objectif : 90+/100 (production-ready)

| # | Recommandation | Impact | Effort | Axes | Statut |
|---|---------------|--------|--------|------|--------|
| 27 | Signature code Apple (Developer ID + notarization) | Haut | Eleve | Securite, Produit | TODO |
| 28 | Signature code Windows (Authenticode) | Haut | Eleve | Securite, Produit | TODO |
| 29 | Auto-update Tauri (tauri-plugin-updater) | Haut | Eleve | DevOps, Produit | TODO |
| 30 | i18n complet (fr/en) | Moyen | Eleve | Contenu, SEO | TODO |
| 31 | Healthcheck endpoint + monitoring infra | Moyen | Moyen | DevOps | TODO |
| 32 | Badges README (CI, version, licence, downloads) | Faible | Faible | SEO | TODO |
| 33 | SEO app stores (description, screenshots, categories) | Moyen | Moyen | SEO, Produit | TODO |

---

## Problemes critiques identifies (resolus)

1. `/api/shutdown` sans auth -> PR #39
2. `delete_backup` path traversal -> PR #39
3. Licence AGPL vs MIT -> PR #38
4. Ancien nom dans log anonymisation RGPD -> PR #39
5. Pas d'ErrorBoundary racine -> PR #43
6. CI masque les echecs (exit 0) -> PR #42
7. Zero lazy loading -> PR #41
8. 80+ accents manquants -> PR #40

---

## Resume executif

THERESE v2 est un projet alpha ambitieux et remarquablement riche (14+ modules, 9 providers LLM,
multi-plateforme) avec des fondations solides : architecture provider pattern, chiffrement Fernet/Keychain,
design system premium, suite de regression originale (354 tests BUG-XXX), et un positionnement souverainete
coherent.

Le score de **64.1/100** reflete un projet en alpha active qui a priorise les fonctionnalites sur la finition.

- **P0 Quick Wins** (9/10 faits) : objectif ~74/100
- **P1 Structurel** : objectif ~82/100
- **P2 Evolutions** : objectif ~90/100
- **P3 Production-ready** : objectif 90+/100
