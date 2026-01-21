# CLAUDE.md - THÉRÈSE V2

> Contexte projet pour Claude Code - Ne pas supprimer

## Projet

**THÉRÈSE v2** - Alternative souveraine à Cowork (Anthropic)
- **Créateur** : Ludo Sanchez (Synoptïa)
- **Tagline** : "Ta mémoire, tes données, ton business."
- **Cible** : Solopreneurs et TPE français

### Différenciateurs vs Cowork
1. **Mémoire persistante** (Cowork n'en a pas)
2. **UX/UI premium** dark mode
3. **Souveraineté** des données (100% local)
4. **Marché français**

### Stack technique
- Frontend : Tauri 2.0 + React + TailwindCSS
- Backend : Python FastAPI + UV
- Database : SQLite + Qdrant (embeddings)
- LLM : Claude API → Mistral → local (évolution)

### Identité visuelle
```yaml
palette:
  background: "#0B1226"
  surface: "#131B35"
  text_primary: "#E6EDF7"
  text_muted: "#B6C7DA"
  accent_cyan: "#22D3EE"
  accent_magenta: "#E11D8D"
```

---

## BMAD Method

BMAD (Breakthrough Method for Agile AI-Driven Development) est installé dans ce projet.

### Installation faite
- **Modules** : BMB + BMM + CIS
- **IDE** : Claude Code
- **TTS** : macOS Say
- **Langue** : French
- **Dossier** : `_bmad/`

### Commandes BMAD principales
```bash
*help              # Liste toutes les commandes
*workflow-init     # Analyse projet et recommande un track
*analyst           # Agent Analyst (benchmarks, recherche)
*pm                # Agent Product Manager (PRD)
*ux                # Agent UX Designer (design, wireframes)
*architect         # Agent Architect (architecture technique)
*sm                # Agent Scrum Master (stories, sprints)
*dev               # Agent Developer (implémentation)
*qa                # Agent QA (tests, validation)
```

### Workflow BMAD pour THÉRÈSE
```
Prompt 0 : Setup initial ✅ FAIT
Prompt 1 : Benchmark Cowork (*analyst) → docs/benchmark-cowork.md
Prompt 2 : Benchmark Mémoire (*analyst) → docs/benchmark-memoire.md
Prompt 3 : Benchmark UX (*ux) → docs/benchmark-ux.md
Prompt 4 : PRD (*pm) → docs/prd-therese.md
Prompt 5 : Architecture (*architect) → docs/architecture.md
Prompt 6 : Stories (*sm) → docs/stories/*.md
```

---

## Avancement

### Fait
- [x] Structure projet créée
- [x] Git initialisé + premier commit
- [x] README.md, Makefile, pyproject.toml, package.json
- [x] Placeholders docs/ créés
- [x] Backend FastAPI minimal (health check)
- [x] BMAD installé (BMB + BMM + CIS + TTS)
- [x] Prompt 1 : Benchmark Cowork (docs/benchmark-cowork.md - 380 lignes)
- [x] Prompt 2 : Benchmark Mémoire (docs/benchmark-memoire.md - 567 lignes)

### En cours
- [ ] Prompt 3 : Benchmark UX

### À faire
- [ ] Prompt 4 : PRD
- [ ] Prompt 5 : Architecture
- [ ] Prompt 6 : Stories
- [ ] Développement MVP

---

## Fichier prompts

Les prompts BMAD sont dans : `prompts-bmad-therese-v2.md`

Chaque prompt correspond à un agent BMAD et génère un document dans `docs/`.

---

## Notes importantes

- **Cowork** = produit desktop d'Anthropic lancé 12 janvier 2026
- **Vulnérabilité connue** : prompt injection via fichiers (PromptArmor)
- **Limitation majeure Cowork** : PAS de mémoire persistante entre sessions
- **Cowork dispo** : macOS only, Max ($100-200/mois) puis Pro ($20/mois)

---

*Dernière mise à jour : 21 janvier 2026*
