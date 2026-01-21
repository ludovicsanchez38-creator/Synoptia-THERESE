# Sprint 2 : Chat Avancé & UX Base

## Informations

- **Durée** : 2 semaines
- **Points** : 32 pts
- **Objectif** : Chat complet avec persistance + fondations UX premium

## Stories incluses

### Epic 2 - Chat Core fin (13 pts)

| ID | Story | Points | Priorité |
|----|-------|--------|----------|
| E2-04 | Persistance des conversations | 5 | P0 |
| E2-05 | Gestion du contexte LLM | 5 | P0 |
| E2-06 | Commandes slash | 3 | P1 |

### Epic 5 - UX/UI partiel (19 pts)

| ID | Story | Points | Priorité |
|----|-------|--------|----------|
| E5-01 | Thème sombre premium | 3 | P0 |
| E5-02 | Command palette (⌘K) | 5 | P1 |
| E5-03 | Raccourcis clavier globaux | 3 | P1 |
| E5-04 | Animations et transitions | 3 | P2 |
| E5-05 | Indicateurs d'état | 2 | P1 |

## Dépendances critiques

```
(Sprint 1) E2-03 ──► E2-04 (Persistance)
                 │
                 └──► E2-05 (Contexte)

E2-04 ──► E2-06 (Commandes slash)

E5-01 (Thème) ──► E5-02, E5-03, E5-04, E5-05
```

## Definition of Done Sprint

- [ ] Conversations sauvegardées et restaurées
- [ ] Contexte LLM géré avec sliding window
- [ ] Commandes /help, /clear, /new fonctionnelles
- [ ] Design system TailwindCSS complet
- [ ] Command palette (⌘K) opérationnelle
- [ ] Raccourcis clavier documentés
- [ ] Animations fluides 60fps
- [ ] Indicateurs connexion/activité visibles

## Répartition suggérée

### Semaine 1

| Jour | Focus | Stories |
|------|-------|---------|
| L-M | Persistance conversations | E2-04 |
| M-J | Gestion contexte LLM | E2-05 |
| V | Commandes slash | E2-06 |

### Semaine 2

| Jour | Focus | Stories |
|------|-------|---------|
| L | Design system + Thème | E5-01 |
| M | Command palette | E5-02 |
| M | Raccourcis clavier | E5-03 |
| J | Animations Framer Motion | E5-04 |
| V | Indicateurs d'état | E5-05 |

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Gestion contexte complexe | Élevé | Implémenter token counting précis |
| Performance animations | Moyen | Utiliser will-change, GPU layers |
| Conflits raccourcis OS | Faible | Vérifier sur macOS |

## Métriques de succès

- Restauration conversation < 200ms
- Command palette ouverture < 100ms
- Animations constantes à 60fps
- prefers-reduced-motion respecté

## Livrables

1. **Chat** : CRUD conversations complet
2. **Design System** : `lib/theme.ts`, composants UI
3. **Accessibilité** : Raccourcis, focus management
4. **Tests** : Tests E2E chat workflow

---

*Sprint 2 / 4 - THÉRÈSE v2*
