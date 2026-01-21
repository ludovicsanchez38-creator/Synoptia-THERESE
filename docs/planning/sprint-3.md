# Sprint 3 : Système de Mémoire

## Informations

- **Durée** : 2 semaines
- **Points** : 39 pts
- **Objectif** : Mémoire persistante complète - différenciateur clé vs Cowork

## Stories incluses

### Epic 3 - Mémoire (39 pts)

| ID | Story | Points | Priorité |
|----|-------|--------|----------|
| E3-01 | CRUD mémoire backend | 5 | P0 |
| E3-02 | Embeddings nomic-embed-text | 3 | P0 |
| E3-03 | Recherche hybride (BM25 + semantic) | 8 | P0 |
| E3-04 | Injection contexte automatique | 5 | P0 |
| E3-05 | Scope mémoire (global/projet/conversation) | 5 | P1 |
| E3-06 | Oubli sélectif | 3 | P2 |
| E3-07 | Interface CRUD mémoire | 5 | P1 |
| E3-08 | Extraction automatique d'entités | 5 | P1 |

## Dépendances critiques

```
(Sprint 1) E1-05 (Qdrant) ──► E3-02 (Embeddings)

E3-01 (CRUD) ──┬──► E3-03 (Recherche)
               │
E3-02 (Embed) ─┘

E3-03 ──► E3-04 (Injection contexte)

E3-01 ──► E3-05 (Scopes) ──► E3-06 (Oubli)

E3-01 ──► E3-07 (UI CRUD)

E3-01, E3-02 ──► E3-08 (Extraction auto)
```

## Definition of Done Sprint

- [ ] CRUD mémoire (fact, preference, note, entity) fonctionnel
- [ ] Embeddings générés et stockés dans Qdrant
- [ ] Recherche hybride avec RRF fusion
- [ ] Contexte mémoire injecté automatiquement dans prompts
- [ ] Scopes global/projet/conversation opérationnels
- [ ] UI de gestion mémoire accessible
- [ ] Extraction automatique des contacts/projets/faits
- [ ] Oubli sélectif avec cascade

## Répartition suggérée

### Semaine 1

| Jour | Focus | Stories |
|------|-------|---------|
| L | Modèles + CRUD backend | E3-01 |
| M | Pipeline embeddings | E3-02 |
| M-J | Recherche hybride BM25+semantic | E3-03 |
| V | Tests recherche + tuning | E3-03 |

### Semaine 2

| Jour | Focus | Stories |
|------|-------|---------|
| L | Injection contexte LLM | E3-04 |
| M | Scopes mémoire | E3-05 |
| M | Oubli sélectif | E3-06 |
| J | UI panneau mémoire | E3-07 |
| V | Extraction auto entités | E3-08 |

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Recherche hybride lente | Élevé | Indexer BM25 en SQLite FTS5 |
| Extraction entités imprécise | Moyen | Seuil confiance élevé (0.7) |
| Contexte trop long | Moyen | Limiter à 5 items pertinents |
| Qdrant disk space | Faible | Monitoring + cleanup old vectors |

## Métriques de succès

- Recherche mémoire < 100ms
- Précision extraction entités > 80%
- Recall recherche hybride > 90%
- UI mémoire fluide (virtualisation)

## Livrables

1. **Backend** : `services/memory.py`, `services/embedding.py`
2. **Search** : Algorithme RRF fusion documenté
3. **UI** : Panneau mémoire complet
4. **Tests** : Tests unitaires + benchmarks recherche

## Notes techniques importantes

### Architecture mémoire cognitive

```
┌─────────────────────────────────────────────────┐
│                   USER INPUT                     │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│            MEMORY RETRIEVAL                      │
│  ┌─────────────┐    ┌─────────────────────────┐ │
│  │   BM25      │    │  Semantic (Qdrant)      │ │
│  │  (SQLite)   │    │  nomic-embed-text       │ │
│  └──────┬──────┘    └────────────┬────────────┘ │
│         │                        │              │
│         └────────┬───────────────┘              │
│                  ▼                              │
│         ┌───────────────┐                       │
│         │  RRF Fusion   │                       │
│         │  k=60         │                       │
│         └───────┬───────┘                       │
└─────────────────┼───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│           CONTEXT INJECTION                      │
│  System prompt + Top-k memories + User input    │
└─────────────────────────────────────────────────┘
```

### Types de mémoire

| Type | Extraction | Exemple |
|------|------------|---------|
| `fact` | Manuelle/Auto | "Ludo habite à Manosque" |
| `preference` | Manuelle | "Préfère Python à JavaScript" |
| `entity` | Auto | Contact, Projet, Organisation |
| `note` | Manuelle | Annotations utilisateur |

---

*Sprint 3 / 4 - THÉRÈSE v2*
