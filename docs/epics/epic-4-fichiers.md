# Epic 4 : Gestion des Fichiers

> Accès, lecture et indexation des fichiers locaux

## Vision

Permettre à THÉRÈSE d'interagir avec les documents de l'utilisateur :
- Navigation fluide dans l'arborescence locale
- Lecture intelligente des formats courants (PDF, DOCX, TXT, MD)
- Indexation dans la mémoire pour recherche ultérieure
- Analyse via chat ("résume ce PDF")

## Stories incluses

| ID | Titre | Points | Priorité |
|----|-------|--------|----------|
| E4-01 | Créer le file browser (navigation dossiers) | 5 | P1 |
| E4-02 | Implémenter la lecture PDF | 3 | P1 |
| E4-03 | Implémenter la lecture DOCX | 3 | P1 |
| E4-04 | Implémenter la lecture TXT/MD | 2 | P1 |
| E4-05 | Ajouter le drag & drop de fichiers | 3 | P1 |
| E4-06 | Indexer les fichiers dans la mémoire | 5 | P2 |
| E4-07 | Permettre l'analyse de fichier via chat | 5 | P1 |

**Total : 26 points**

## Critères de succès de l'Epic

- [ ] L'utilisateur peut naviguer dans ses dossiers depuis THÉRÈSE
- [ ] Les fichiers PDF, DOCX, TXT, MD s'ouvrent et affichent leur contenu
- [ ] Le drag & drop d'un fichier déclenche son analyse
- [ ] "Résume ce fichier" fonctionne dans le chat
- [ ] Les fichiers indexés apparaissent dans la mémoire
- [ ] Recherche "mon contrat avec Pierre" retrouve le bon fichier

## Design du file browser

```
┌─────────────────────────────────────────────────────────┐
│ 📁 Fichiers                                   [⚙️] [X]  │
├─────────────────────────────────────────────────────────┤
│ 📂 /Users/ludo/Documents                                │
│ ├── 📂 Clients                                          │
│ │   ├── 📂 Pierre Heninger                              │
│ │   │   ├── 📄 contrat-forger.pdf          12 Ko       │
│ │   │   └── 📄 notes-session.md            2 Ko        │
│ │   └── 📂 Célia Galas                                  │
│ ├── 📂 Projets                                          │
│ │   └── 📂 THERESE-v2                                   │
│ └── 📄 roadmap-2026.docx                   45 Ko       │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ 🔍 Rechercher dans les fichiers...                      │
├─────────────────────────────────────────────────────────┤
│ Fichiers récents                                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 📄 benchmark-cowork.md        il y a 2h    [📤]    │ │
│ │ 📄 prd-therese.md            hier          [📤]    │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Formats supportés

| Format | Extension | Parser | Limite |
|--------|-----------|--------|--------|
| PDF | .pdf | PyMuPDF | 50 Mo / 500 pages |
| Word | .docx | python-docx | 20 Mo |
| Texte | .txt | natif | 10 Mo |
| Markdown | .md | natif | 10 Mo |
| Images | .png, .jpg | PIL + Vision API | 10 Mo |

## Architecture extraction

```
┌──────────────┐
│   Fichier    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│           File Parser                 │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌─────┐ │
│  │ PDF  │ │ DOCX │ │ TXT  │ │ IMG │ │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬──┘ │
│     └────────┴────────┴────────┘     │
│                  │                    │
│                  ▼                    │
│            Texte brut                 │
└──────────────────┬───────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌──────────────┐       ┌──────────────┐
│   SQLite     │       │   Qdrant     │
│  (metadata)  │       │ (embeddings) │
└──────────────┘       └──────────────┘
```

## Flux drag & drop

```
1. User drops file
        │
        ▼
2. Tauri intercepts (FileDropEvent)
        │
        ▼
3. Frontend affiche preview
        │
        ▼
4. User confirme "Analyser ce fichier"
        │
        ▼
5. Backend parse le fichier
        │
        ▼
6. Texte extrait → LLM pour résumé
        │
        ▼
7. Résumé affiché dans le chat
        │
        ▼
8. Option : "Ajouter à la mémoire ?"
```

## Sécurité fichiers

### Permissions Tauri

```json
{
  "tauri": {
    "allowlist": {
      "fs": {
        "scope": ["$HOME/Documents/**", "$HOME/Desktop/**"],
        "readFile": true,
        "writeFile": false
      }
    }
  }
}
```

### Limitations

- Pas d'accès aux dossiers système
- Pas d'écriture par défaut
- Confirmation utilisateur pour chaque nouveau dossier
- Logs des accès fichiers

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| PDF corrompu | Crash | Try/catch + message erreur gracieux |
| Fichier trop gros | Perf/coût | Limite taille + chunking |
| Contenu sensible | Sécurité | Tout reste local + logs opt-in |
| Formats exotiques | Frustration | Liste claire formats supportés |

## Dépendances

- E1-05 (IPC) obligatoire
- E3-03 (Indexation Qdrant) pour mémoire fichiers
- E2-02 (API Claude) pour analyse

## Définition of Done

- File browser fonctionnel
- 4 formats lus sans erreur
- Drag & drop opérationnel
- Indexation mémoire active
- "Résume ce fichier" fonctionne
- Tests avec fichiers de test

---

*Epic owner : Agent Dev Backend*
*Sprint cible : Sprint 4*
