# Plan : Pipeline QA Autonome THERESE

**Objectif** : Passer de 25% a 95%+ de couverture sur 305 user stories avec zero bug en prod
**Architecture** : 6 agents Claude Code specialises en pipeline + visual regression + testeur exploratoire Quinn. Chaque agent est un skill `.claude/commands/qa/`. Le pipeline lit les stories, genere des tests Playwright, les audite, les execute et auto-corrige.
**Stack** : Claude Code (orchestration), Playwright (E2E frontend), Vitest (unitaire), Chrome MCP (exploratoire)
**Fichiers impactes** : 10 skills, 1 config Playwright, 12+ fichiers tests, 1 COVERAGE.md
**Estimation** : 10 taches, ~3-4h

---

## Tache 1 : Structure du pipeline QA

**Fichiers** :
- Creer : `.claude/commands/qa/` (dossier)
- Creer : `docs/stories/COVERAGE.md`

**Instructions** :
1. Creer le dossier `.claude/commands/qa/`
2. Creer le fichier COVERAGE.md avec la structure de tracking

**Verification** :
- [ ] Dossier `.claude/commands/qa/` existe
- [ ] `docs/stories/COVERAGE.md` existe avec header

**Commit** : `feat(qa): init pipeline QA - structure`

---

## Tache 2 : Agent Analyste (qa-analyze.md)

**Fichiers** :
- Creer : `.claude/commands/qa/analyze.md`

**Instructions** :
1. Cree le skill qui lit un fichier US-*.md
2. Parse chaque story : titre, criteres `- [ ]`, composants, data-testid
3. Scanne le code source pour verifier les selecteurs reels
4. Produit une cartographie JSON des elements testables

**Verification** :
- [ ] `/qa/analyze docs/stories/US-001-chat-onboarding.md` produit la cartographie
- [ ] Les data-testid listes sont verifies dans le code source

**Commit** : `feat(qa): agent Analyste - cartographie stories`

---

## Tache 3 : Agent Architecte (qa-plan.md)

**Fichiers** :
- Creer : `.claude/commands/qa/plan.md`

**Instructions** :
1. Cree le skill qui recoit la cartographie de l'Analyste
2. Classe chaque critere : BROWSER / API / CODE
3. Priorise P0 / P1 / P2 selon l'impact utilisateur
4. Genere un plan de test structure avec scenarios happy path + negatif + edge

**Verification** :
- [ ] `/qa/plan` produit un plan avec P0/P1/P2
- [ ] Chaque critere a au moins un scenario

**Commit** : `feat(qa): agent Architecte - priorisation`

---

## Tache 4 : Agent Ingenieur (qa-generate.md)

**Fichiers** :
- Creer : `.claude/commands/qa/generate.md`
- Creer : `tests/e2e/stories/` (dossier)

**Instructions** :
1. Cree le skill qui genere des tests Playwright TypeScript
2. Utilise les data-testid de la cartographie
3. Pattern : Page Object Model leger
4. Genere happy path + test negatif + edge case par critere
5. Chaque test reference l'US et le critere dans le nom

**Verification** :
- [ ] Tests generes dans `tests/e2e/stories/`
- [ ] Chaque test a un describe/it avec reference US-XXX

**Commit** : `feat(qa): agent Ingenieur - generation tests Playwright`

---

## Tache 5 : Agent Sentinelle (qa-audit.md)

**Fichiers** :
- Creer : `.claude/commands/qa/audit.md`

**Instructions** :
1. Cree le skill qui audite les tests generes
2. Verifie : data-testid existent dans le code, pas de selecteurs fragiles, patterns anti-regression respectes
3. Verifie les 4 patterns obligatoires (negatif, interaction z-index, semantique, multi-contexte)
4. Bloque si un test P0 a un selecteur invalide

**Verification** :
- [ ] `/qa/audit` signale les tests avec selecteurs invalides
- [ ] Les 4 patterns sont verifies

**Commit** : `feat(qa): agent Sentinelle - audit qualite`

---

## Tache 6 : Agent Guerisseur (qa-heal.md)

**Fichiers** :
- Creer : `.claude/commands/qa/heal.md`

**Instructions** :
1. Cree le skill qui lance les tests et auto-corrige
2. Execute `npx playwright test` sur les fichiers generes
3. Analyse les erreurs : selecteur introuvable, timeout, assertion
4. Corrige et relance (max 5 iterations)
5. Produit un rapport pass/fail/healed

**Verification** :
- [ ] `/qa/heal` lance les tests et tente la correction
- [ ] Rapport final avec pass/fail/healed

**Commit** : `feat(qa): agent Guerisseur - self-healing`

---

## Tache 7 : Agent Quinn - Testeur exploratoire (qa-quinn.md)

**Fichiers** :
- Creer : `.claude/commands/qa/quinn.md`

**Instructions** :
1. Cree le skill persona "Quinn, testeur QA veteran"
2. Quinn explore l'app via Chrome MCP en black-box
3. Teste les parcours complets (onboarding → chat → memory → board)
4. Essaie les cas limites : inputs vides, XSS, viewport mobile, double-click
5. Prend des screenshots des bugs trouves
6. Produit un rapport markdown detaille

**Verification** :
- [ ] `/qa/quinn` explore l'app et produit un rapport de bugs
- [ ] Screenshots dans /tmp/therese-tests/

**Commit** : `feat(qa): agent Quinn - testeur exploratoire IA`

---

## Tache 8 : Agent Scribe (qa-report.md)

**Fichiers** :
- Creer : `.claude/commands/qa/report.md`

**Instructions** :
1. Cree le skill qui compile les resultats de tous les agents
2. Met a jour `docs/stories/COVERAGE.md` avec la matrice story → critere → test → statut
3. Genere le rapport final avec verdict RELEASE OK / BLOQUANT
4. Calcule le taux de couverture global

**Verification** :
- [ ] COVERAGE.md mis a jour avec les resultats
- [ ] Rapport final avec verdict

**Commit** : `feat(qa): agent Scribe - reporting couverture`

---

## Tache 9 : Orchestrateur (qa-full.md)

**Fichiers** :
- Creer : `.claude/commands/qa/full.md`

**Instructions** :
1. Cree le skill maitre qui lance le pipeline complet
2. Ordre : Analyste → Architecte → Ingenieur → Sentinelle → Guerisseur → Quinn → Scribe
3. Chaque agent s'execute en sous-agent
4. Option `--quick` : saute Quinn et ne teste que les P0
5. Option `--domain US-100` : ne teste qu'un domaine

**Verification** :
- [ ] `/qa/full` lance le pipeline complet
- [ ] `/qa/full --quick` ne lance que P0

**Commit** : `feat(qa): orchestrateur pipeline complet`

---

## Tache 10 : Config Playwright Frontend

**Fichiers** :
- Creer : `src/frontend/playwright.config.ts`
- Modifier : `src/frontend/package.json` (ajout deps)

**Instructions** :
1. Creer la config Playwright pour le frontend
2. baseURL = http://localhost:1420
3. Activer visual regression (toHaveScreenshot)
4. Configurer les projets : desktop (1280x800) + mobile (375x667)
5. Ajouter les deps dans package.json

**Verification** :
- [ ] `npx playwright test --list` fonctionne
- [ ] Config accepte les screenshots de reference

**Commit** : `feat(qa): config Playwright frontend + visual regression`
