# Sprint 1 : Infrastructure & Chat Base

## Informations

- **Durée** : 2 semaines
- **Points** : 34 pts
- **Objectif** : Fondations techniques complètes + chat fonctionnel basique

## Stories incluses

### Epic 1 - Infrastructure (23 pts)

| ID | Story | Points | Priorité |
|----|-------|--------|----------|
| E1-01 | Setup Tauri 2.0 + React 19 | 5 | P0 |
| E1-02 | Structure backend FastAPI | 5 | P0 |
| E1-03 | SQLite + Alembic migrations | 3 | P0 |
| E1-04 | Communication Tauri-Python IPC | 5 | P0 |
| E1-05 | Configuration Qdrant embedded | 3 | P0 |
| E1-06 | Health check & logging | 2 | P1 |

### Epic 2 - Chat Core partiel (11 pts)

| ID | Story | Points | Priorité |
|----|-------|--------|----------|
| E2-01 | Input chat avec raccourcis | 3 | P0 |
| E2-02 | Affichage messages avec Markdown | 3 | P0 |
| E2-03 | Intégration streaming LLM | 5 | P0 |

## Dépendances critiques

```
E1-01 (Tauri) ──┬──► E1-04 (IPC)
                │
E1-02 (FastAPI) ┘

E1-03 (SQLite) ──► E2-01, E2-02

E1-05 (Qdrant) ──► (Sprint 3)

E2-01, E2-02 ──► E2-03 (Streaming)
```

## Definition of Done Sprint

- [ ] Application Tauri démarre sans erreur
- [ ] Backend FastAPI accessible via IPC
- [ ] Base SQLite créée avec migrations
- [ ] Qdrant embedded opérationnel
- [ ] Chat fonctionnel : envoi message → réponse streamed
- [ ] Logs structurés actifs
- [ ] CI/CD basique configuré

## Répartition suggérée

### Semaine 1

| Jour | Focus | Stories |
|------|-------|---------|
| L-M | Setup Tauri + React | E1-01 |
| M-J | Backend FastAPI | E1-02 |
| V | SQLite + Qdrant | E1-03, E1-05 |

### Semaine 2

| Jour | Focus | Stories |
|------|-------|---------|
| L | IPC Tauri-Python | E1-04 |
| M | Health check + Logging | E1-06 |
| M-J | UI Chat (Input + Messages) | E2-01, E2-02 |
| V | Streaming LLM | E2-03 |

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| IPC Tauri-Python complexe | Élevé | Utiliser spawn process, pas sidecar |
| Qdrant embedded mode instable | Moyen | Fallback SQLite FTS5 |
| Rate limiting Claude API | Faible | Mistral en fallback |

## Métriques de succès

- Temps de démarrage app < 3s
- Latence IPC < 50ms
- Premier token streaming < 500ms
- Zéro crash au lancement

## Livrables

1. **Code** : `src/frontend/`, `src/backend/` fonctionnels
2. **Config** : `.env.example`, `pyproject.toml`, `package.json`
3. **Tests** : Tests unitaires backend (>80% couverture)
4. **Docs** : README installation mise à jour

---

*Sprint 1 / 4 - THÉRÈSE v2*
