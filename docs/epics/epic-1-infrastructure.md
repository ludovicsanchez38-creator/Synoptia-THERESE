# Epic 1 : Infrastructure & Setup

> Mise en place de la stack technique de base THÉRÈSE v2

## Vision

Créer les fondations solides permettant le développement itératif de THÉRÈSE :
- Application desktop cross-platform fonctionnelle
- Communication fluide entre frontend React et backend Python
- Bases de données locales opérationnelles
- Pipeline de build reproductible

## Stories incluses

| ID | Titre | Points | Priorité |
|----|-------|--------|----------|
| E1-01 | Initialiser le projet Tauri + React | 5 | P0 |
| E1-02 | Configurer le backend Python FastAPI | 3 | P0 |
| E1-03 | Mettre en place SQLite avec schéma initial | 3 | P0 |
| E1-04 | Intégrer Qdrant en mode embedded | 5 | P0 |
| E1-05 | Créer la communication IPC Tauri ↔ Backend | 5 | P0 |
| E1-06 | Configurer le build cross-platform | 3 | P1 |

**Total : 24 points**

## Critères de succès de l'Epic

- [ ] `make dev` lance l'application complète (frontend + backend)
- [ ] Le frontend affiche une page de test avec health check backend
- [ ] SQLite stocke et restitue des données de test
- [ ] Qdrant indexe et recherche un vecteur de test
- [ ] `make build` génère un exécutable pour macOS
- [ ] Les logs unifiés sont visibles dans la console dev

## Architecture cible

```
┌─────────────────────────────────────────────┐
│           THÉRÈSE Desktop App               │
├─────────────────────────────────────────────┤
│  Tauri Shell (Rust)                         │
│  ├── Window management                      │
│  ├── File system access                     │
│  └── IPC bridge                             │
├─────────────────────────────────────────────┤
│  React Frontend (WebView)                   │
│  ├── Zustand store                          │
│  ├── TailwindCSS                            │
│  └── Tauri API calls                        │
├─────────────────────────────────────────────┤
│  Python Backend (Sidecar)                   │
│  ├── FastAPI server                         │
│  ├── SQLite (SQLModel)                      │
│  └── Qdrant (embedded)                      │
└─────────────────────────────────────────────┘
```

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Complexité IPC Tauri ↔ Python | Délai | Prototype early, documentation Tauri sidecar |
| Qdrant embedded instable | Blocage | Fallback SQLite FTS5 si nécessaire |
| Build cross-platform Windows | Délai | Focus macOS d'abord, Windows en stretch |

## Dépendances externes

- Rust toolchain (rustup)
- Node.js 20+
- Python 3.12+ via UV
- Qdrant binary ou lib Rust

## Définition of Done

- Tests unitaires backend passent
- Application démarre sans erreur
- Documentation setup dans README
- Commit atomique par story

---

*Epic owner : Agent Architect*
*Sprint cible : Sprint 1*
