# Plan : Onglet Agents locaux dans l'Atelier

**Date** : 30 mars 2026
**Objectif** : Ajouter un onglet "Agents" dans l'Atelier avec 6 agents metier preconfigures, sans dependance OpenClaw
**Cible** : Testeurs alpha (semi-techniques)
**Estimation** : 3-4h, 4 fichiers a creer + 2 a modifier

## Architecture

Reutilise le `AgentRuntime` existant (meme moteur que le chat Katia/Zezette) mais avec des profils d'agents configurables.

```
AtelierPanel.tsx (modifier)
├── Tab "Chat"   → SwarmOrchestrator (Katia+Zezette, flow fixe)
├── Tab "Agents" → AgentSpawner (nouveau)
│   ├── AgentCatalog.tsx     → grille 2x3 des 6 agents
│   ├── AgentSession.tsx     → chat avec un agent spawne
│   └── AgentSessionList.tsx → sidebar sessions actives (optionnel v1)

Backend (modifier agents.py):
├── POST /api/agents/spawn       → lance AgentRuntime avec un profil
├── GET  /api/agents/profiles    → liste les profils disponibles
├── GET  /api/agents/sessions    → reutilise les sessions existantes
└── services/agents/profiles.py  → definitions des 6 agents
```

## 6 agents preconfigures

| ID | Nom | Icone | Outils | Couleur |
|----|-----|-------|--------|---------|
| researcher | Chercheur Web | 🔍 | web_search, read_file, write_file | cyan |
| writer | Redacteur | ✍️ | read_file, write_file | magenta |
| analyst | Analyste | 📊 | read_file, search_codebase, run_command | blue |
| planner | Planificateur | 📅 | read_file, write_file | green |
| coder | Codeur | 💻 | read_file, write_file, search_codebase, run_command, git_status | purple |
| creative | Creatif | 🎨 | web_search, write_file | amber |

Chaque agent :
- System prompt specifique (role, ton, contraintes)
- Liste d'outils autorises (sous-ensemble de THERESE_TOOLS)
- Streaming SSE comme le chat local
- Pas de flow Katia→Zezette (agent autonome, pas de handoff)

## UX

### Ecran catalogue (pas de session active)
```
┌─────────────────────────────────────┐
│ Atelier    [Chat] [Agents]          │
├─────────────────────────────────────┤
│                                     │
│  Choisis un agent pour commencer    │
│                                     │
│  ┌──────────┐  ┌──────────┐        │
│  │ 🔍       │  │ ✍️       │        │
│  │ Chercheur│  │ Redacteur│        │
│  │ Web      │  │          │        │
│  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐        │
│  │ 📊       │  │ 📅       │        │
│  │ Analyste │  │ Planif.  │        │
│  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐        │
│  │ 💻       │  │ 🎨       │        │
│  │ Codeur   │  │ Creatif  │        │
│  └──────────┘  └──────────┘        │
│                                     │
└─────────────────────────────────────┘
```

### Ecran session (agent selectionne)
```
┌─────────────────────────────────────┐
│ ← 🔍 Chercheur Web  [claude-sonnet]│
├─────────────────────────────────────┤
│                                     │
│ [Messages agent en streaming]       │
│ [Tool calls visibles]              │
│ [Resultats inline]                 │
│                                     │
├─────────────────────────────────────┤
│ [Textarea input]           [Send]  │
└─────────────────────────────────────┘
```

## Taches d'implementation

### Tache 1 : Profils d'agents (backend)
- Creer `src/backend/app/services/agents/profiles.py`
- 6 profils avec system_prompt + tools
- Endpoint GET /api/agents/profiles

### Tache 2 : Endpoint spawn (backend)
- POST /api/agents/spawn dans agents.py
- Prend profile_id + instruction
- Lance AgentRuntime avec le profil
- Stream SSE (meme pattern que /api/agents/request)

### Tache 3 : Catalogue UI (frontend)
- Creer AgentCatalog.tsx (grille 2x3)
- Clic sur agent → demande l'instruction → spawn
- Design glass/dark theme coherent

### Tache 4 : Session chat UI (frontend)
- Creer AgentSession.tsx (chat streaming)
- Reutiliser le pattern de AtelierPanel chat view
- Header avec nom agent + modele + bouton retour

### Tache 5 : Integration AtelierPanel
- Ajouter tab "Agents" dans la nav
- Router entre catalogue et session
- Store minimal (agentSessionMessages, activeProfile)

## Non-scope (v2)

- Multi-sessions paralleles (un seul agent a la fois pour v1)
- Custom agents (l'utilisateur cree ses propres agents)
- Integration OpenClaw (si besoin plus tard, hybride)
- Historique des sessions agents
- MCP tools dans les agents
