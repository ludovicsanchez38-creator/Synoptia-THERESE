# Sprint 4 : Fichiers & Polish

## Informations

- **Durée** : 2 semaines
- **Points** : 38 pts
- **Objectif** : Gestion fichiers complète + finalisation UX

## Stories incluses

### Epic 4 - Fichiers (28 pts)

| ID | Story | Points | Priorité |
|----|-------|--------|----------|
| E4-01 | File browser natif | 5 | P0 |
| E4-02 | Lecture PDF (PyMuPDF) | 5 | P0 |
| E4-03 | Lecture DOCX (python-docx) | 3 | P0 |
| E4-04 | Lecture TXT/Markdown | 2 | P0 |
| E4-05 | Drag & drop fichiers | 3 | P1 |
| E4-06 | Indexation fichiers (embeddings) | 5 | P1 |
| E4-07 | Analyse fichiers via chat | 5 | P1 |

### Epic 5 - UX/UI fin (10 pts)

| ID | Story | Points | Priorité |
|----|-------|--------|----------|
| E5-06 | Panneau latéral multifonction | 5 | P1 |
| E5-07 | Paramètres utilisateur | 5 | P1 |
| E5-08 | Onboarding wizard | 5 | P2 |

## Dépendances critiques

```
(Tauri) fs permissions ──► E4-01 (File browser)

E4-01 ──┬──► E4-02 (PDF)
        ├──► E4-03 (DOCX)
        └──► E4-04 (TXT/MD)

E4-02, E4-03, E4-04 ──► E4-05 (Drag & drop)

E4-02, E4-03, E4-04 ──► E4-06 (Indexation)

E4-06 ──► E4-07 (Analyse chat)

(Sprint 2) E5-01 ──► E5-06, E5-07, E5-08
```

## Definition of Done Sprint

- [ ] File browser avec navigation dossiers
- [ ] Parsing PDF, DOCX, TXT, Markdown
- [ ] Drag & drop fonctionnel
- [ ] Fichiers indexés dans Qdrant
- [ ] Commandes /analyse, /extrait, /demande
- [ ] Panneau latéral 3 onglets (Historique, Mémoire, Fichiers)
- [ ] Page Settings complète (API, LLM, Mémoire, Interface, Données)
- [ ] Onboarding 5 étapes au premier lancement

## Répartition suggérée

### Semaine 1

| Jour | Focus | Stories |
|------|-------|---------|
| L | File browser Tauri | E4-01 |
| M | Parser PDF | E4-02 |
| M | Parser DOCX | E4-03 |
| J | Parser TXT/MD | E4-04 |
| V | Drag & drop | E4-05 |

### Semaine 2

| Jour | Focus | Stories |
|------|-------|---------|
| L | Indexation fichiers | E4-06 |
| M | Analyse fichiers chat | E4-07 |
| M | Panneau latéral | E5-06 |
| J | Page Settings | E5-07 |
| V | Onboarding wizard | E5-08 |

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| PDF complexes (scans, images) | Élevé | Détection + message utilisateur |
| Fichiers volumineux | Moyen | Chunking intelligent |
| Settings non persistés | Faible | Zustand persist + localStorage |

## Métriques de succès

- Parsing PDF < 2s pour 50 pages
- Indexation fichier < 5s
- Sidebar resize fluide
- Onboarding completion rate > 90%

## Livrables

1. **Parsers** : `services/parsers/` (pdf, docx, text)
2. **Indexation** : `services/file_indexer.py`
3. **UI** : Sidebar, Settings, Onboarding
4. **Tests** : Tests E2E parcours complet

## Notes techniques importantes

### Pipeline fichiers

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   File Drop     │────►│    Parser       │────►│   Chunking      │
│  (.pdf/.docx)   │     │  (PyMuPDF/docx) │     │  (1000 tokens)  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Chat Query    │◄────│  Qdrant Search  │◄────│   Embeddings    │
│  /analyse file  │     │  (top-k chunks) │     │  (nomic-embed)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Formats supportés

| Format | Parser | Extraction |
|--------|--------|------------|
| `.pdf` | PyMuPDF | Texte + métadonnées |
| `.docx` | python-docx | Texte + styles + tableaux |
| `.txt` | chardet | Texte (détection encoding) |
| `.md` | Custom | Texte + front matter YAML |

### Structure Settings

```typescript
interface Settings {
  // API
  apiProvider: 'claude' | 'mistral' | 'ollama';
  apiKey: string;
  apiModel: string;

  // LLM
  systemPrompt: string;
  temperature: number;
  maxTokens: number;

  // Mémoire
  autoExtractEntities: boolean;
  memoryContextSize: number;
  confidenceThreshold: number;

  // Interface
  fontSize: 'small' | 'medium' | 'large';
  enableAnimations: boolean;
  compactMode: boolean;
  sidebarDefaultTab: 'history' | 'memory' | 'files';

  // Données
  dataPath: string;
}
```

---

*Sprint 4 / 4 - THÉRÈSE v2*
