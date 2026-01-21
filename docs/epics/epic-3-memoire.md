# Epic 3 : Mémoire Persistante

> LE différenciateur de THÉRÈSE - mémoire qui apprend et retient

## Vision

Créer un système de mémoire qui :
- Retient automatiquement les informations importantes des conversations
- Permet une recherche rapide (< 200ms) dans le contexte
- Affiche le contexte actif de manière transparente
- Donne le contrôle total à l'utilisateur sur ses données

**C'est la feature que Cowork n'a pas.**

## Stories incluses

| ID | Titre | Points | Priorité |
|----|-------|--------|----------|
| E3-01 | Définir le schéma mémoire (entités, relations) | 3 | P0 |
| E3-02 | Créer le service d'embedding (texte → vecteur) | 5 | P0 |
| E3-03 | Implémenter l'indexation dans Qdrant | 5 | P0 |
| E3-04 | Créer la recherche hybride (keyword + semantic) | 5 | P0 |
| E3-05 | Injecter le contexte mémoire dans les prompts LLM | 3 | P0 |
| E3-06 | Créer le panneau "Contexte actif" (UI) | 5 | P1 |
| E3-07 | Implémenter CRUD mémoire (voir, éditer, supprimer) | 5 | P1 |
| E3-08 | Ajouter l'extraction auto d'entités depuis conversations | 8 | P2 |

**Total : 39 points**

## Critères de succès de l'Epic

- [ ] THÉRÈSE se souvient d'une info donnée dans une conversation précédente
- [ ] La recherche mémoire retourne des résultats en < 200ms
- [ ] Le panneau contexte affiche les éléments pertinents
- [ ] L'utilisateur peut voir/éditer/supprimer n'importe quelle mémoire
- [ ] L'extraction automatique identifie contacts et projets
- [ ] Export mémoire possible (JSON/CSV)

## Architecture mémoire

```
┌─────────────────────────────────────────────────────────┐
│                    Module Mémoire                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │  Extracteur │───▶│  Embedder    │───▶│  Qdrant   │  │
│  │  (LLM)      │    │(nomic-embed) │    │ (vectors) │  │
│  └─────────────┘    └──────────────┘    └───────────┘  │
│         │                                      │        │
│         ▼                                      ▼        │
│  ┌─────────────────────────────────────────────────┐   │
│  │                    SQLite                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │   │
│  │  │ contacts │  │ projects │  │ preferences  │  │   │
│  │  └──────────┘  └──────────┘  └──────────────┘  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │   │
│  │  │ memories │  │ entities │  │conversations │  │   │
│  │  └──────────┘  └──────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Schéma des entités

### Contact
```yaml
contact:
  id: UUID
  first_name: string
  last_name: string
  company: string?
  email: string?
  phone: string?
  notes: text
  tags: string[]
  created_at: timestamp
  updated_at: timestamp
```

### Project
```yaml
project:
  id: UUID
  name: string
  description: text
  status: enum (active, done, archived)
  client_id: UUID? (ref contact)
  tags: string[]
  created_at: timestamp
  updated_at: timestamp
```

### Memory (entité générique)
```yaml
memory:
  id: UUID
  type: enum (fact, preference, note)
  content: text
  source: enum (extracted, manual)
  conversation_id: UUID?
  embedding_id: string (Qdrant)
  created_at: timestamp
```

## Design du panneau contexte

```
┌───────────────────────────────┐
│ 📚 Contexte actif             │
├───────────────────────────────┤
│                               │
│ 🏢 Projet en cours            │
│ ┌───────────────────────────┐ │
│ │ THÉRÈSE v2                │ │
│ │ Alternative Cowork        │ │
│ │ #IA #Desktop #MVP         │ │
│ └───────────────────────────┘ │
│                               │
│ 👤 Contacts récents           │
│ ┌───────────────────────────┐ │
│ │ Pierre H. - DAF           │ │
│ │ Célia G. - Consultant     │ │
│ └───────────────────────────┘ │
│                               │
│ 💡 Préférences                │
│ • Aime les réponses concises  │
│ • Stack : Python + React      │
│ • Timezone : Europe/Paris     │
│                               │
│ [Voir toute la mémoire →]     │
└───────────────────────────────┘
```

## Flux de recherche hybride

```
Query utilisateur
        │
        ▼
┌───────────────────┐
│ 1. Keyword search │  ← SQLite FTS5
│    (exactitude)   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 2. Semantic search│  ← Qdrant cosine
│    (similarité)   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 3. Fusion + Rank  │  ← RRF algorithm
│    (top-k = 5)    │
└─────────┬─────────┘
          │
          ▼
    Résultats triés
```

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Extraction entités bruitée | Mauvaise mémoire | Validation manuelle + confidence threshold |
| Latence Qdrant | UX dégradée | Cache en mémoire + batch async |
| Mémoire qui grossit trop | Perf | Politique de rétention + archivage |
| Conflit info contradictoire | Confusion | Versioning + timestamp + source |

## Dépendances

- E1-03 (SQLite) obligatoire
- E1-04 (Qdrant) obligatoire
- E2-02 (API Claude) pour extraction

## Définition of Done

- Mémoire fonctionnelle end-to-end
- Recherche < 200ms
- CRUD complet avec UI
- Tests unitaires extracteur
- Export JSON fonctionnel

---

*Epic owner : Agent Dev Backend*
*Sprint cible : Sprint 3*
