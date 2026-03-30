# Orchestrateur QA Pipeline

Lance le pipeline QA complet THERESE. Simule une equipe de 6 testeurs QA + 1 testeur exploratoire.

## Arguments

- Sans argument : pipeline complet (6 agents + Quinn)
- `--quick` : Analyste + Guerisseur P0 seulement (~10 min)
- `--domain US-100` : ne traite qu'un domaine (ex: email)
- `--no-quinn` : saute le testeur exploratoire
- `--generate-only` : Analyste + Architecte + Ingenieur (pas d'execution)
- `--heal-only` : lance seulement le Guerisseur sur les tests existants
- `--quinn-only` : lance seulement Quinn

## Prerequis

Verifier avant de lancer :
1. Backend : `curl -s http://localhost:17293/health | grep healthy`
2. Frontend : `curl -s -o /dev/null -w "%{http_code}" http://localhost:1420` doit retourner 200
3. Chrome ouvert (si Quinn est inclus)

Si un prerequis echoue, STOPPER et informer.

## Pipeline complet

### Phase 1 : Analyse (Agent Analyste)

Lancer un Agent avec le prompt de `/qa/analyze` sur les fichiers stories.
Si `--domain` est specifie, ne traiter que le fichier correspondant.

**Input** : `docs/stories/US-*.md`
**Output** : `/tmp/qa-analysis.json`
**Duree estimee** : 2-5 min

### Phase 2 : Planification (Agent Architecte)

Lancer un Agent avec le prompt de `/qa/plan`.

**Input** : `/tmp/qa-analysis.json`
**Output** : `/tmp/qa-plan.json`
**Duree estimee** : 2-3 min

### Phase 3 : Generation (Agent Ingenieur)

Lancer un Agent avec le prompt de `/qa/generate`.

**Input** : `/tmp/qa-plan.json`
**Output** : `tests/e2e/stories/*.spec.ts`
**Duree estimee** : 5-10 min

### Phase 4 : Audit (Agent Sentinelle)

Lancer un Agent avec le prompt de `/qa/audit`.

**Input** : `tests/e2e/stories/*.spec.ts`
**Output** : Rapport audit + corrections
**Duree estimee** : 3-5 min

### Phase 5 : Execution + Guerison (Agent Guerisseur)

Lancer un Agent avec le prompt de `/qa/heal`.

**Input** : Tests audites
**Output** : `/tmp/qa-results.json` + rapport
**Duree estimee** : 10-20 min (selon nombre de tests)

### Phase 6 : Exploration (Agent Quinn)

Lancer un Agent avec le prompt de `/qa/quinn`.
Utilise Chrome MCP pour explorer l'app en direct.

**Input** : App running sur localhost:1420
**Output** : Rapport bugs + screenshots
**Duree estimee** : 15-30 min

### Phase 7 : Rapport (Agent Scribe)

Lancer un Agent avec le prompt de `/qa/report`.

**Input** : Tous les outputs precedents
**Output** : `docs/stories/COVERAGE.md` + `docs/qa-reports/YYYY-MM-DD-report.md`
**Duree estimee** : 2-3 min

## Mode --quick

Pipeline reduit pour validation rapide avant release :

1. Analyste (scope P0 uniquement)
2. Guerisseur (lance seulement les tests P0 existants)
3. Scribe (rapport reduit)

Duree estimee : ~10 min

## Parallelisation

Les Phases 1-4 (Analyste → Sentinelle) peuvent etre parallelisees par domaine :
- Agent 1 : Chat + Onboarding
- Agent 2 : Email + Calendar
- Agent 3 : CRM + Invoices + Memory
- Agent 4 : Settings + Board + Skills
- Agent 5 : Security + Navigation + Desktop

Chaque agent produit ses fichiers, puis le Guerisseur lance tout, et le Scribe compile.

## Sortie finale

Afficher le verdict en gros :

```
╔══════════════════════════════════════════╗
║  QA PIPELINE THERESE - VERDICT          ║
║                                          ║
║  Couverture : XX% (XXX/305 stories)      ║
║  Tests : XXX PASS / XX FAIL / XX SKIP   ║
║  Quinn : X bugs trouves                 ║
║                                          ║
║  ✅ RELEASE OK   ou   ❌ BLOQUANT       ║
╚══════════════════════════════════════════╝
```
