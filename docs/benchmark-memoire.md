# Benchmark Systèmes de Mémoire IA

> Document généré pour THÉRÈSE v2
> Date : 21 janvier 2026

## Statut

En cours

---

## 1. Vue d'ensemble

### Le problème fondamental

Les LLMs souffrent d'une limitation majeure : **l'absence de mémoire persistante**. Chaque conversation repart de zéro. L'utilisateur doit réexpliquer son contexte, ses préférences, ses projets à chaque session.

> "Agentic systems fail without context and memory. Model quality fails without context."
> — Emil Eifrem, CEO Neo4j

### L'enjeu pour THÉRÈSE

THÉRÈSE se positionne comme une assistante qui **connaît** son utilisateur :
- Ses clients et contacts
- Ses projets en cours
- Ses préférences de travail
- Son historique d'interactions

C'est **LE** différenciateur majeur vs Cowork (qui n'a pas de mémoire persistante).

---

## 2. Taxonomie des mémoires IA

### 2.1 Modèle cognitif (inspiré neuroscience)

| Type | Description | Équivalent humain | Usage IA |
|------|-------------|-------------------|----------|
| **Working Memory** | Contexte de la conversation active | Mémoire de travail | Context window LLM |
| **Episodic Memory** | Souvenirs d'événements spécifiques | "La réunion avec Jean mardi" | Historique conversations |
| **Semantic Memory** | Faits et connaissances | "Paris est la capitale" | Base de connaissances |
| **Procedural Memory** | Savoir-faire, compétences | "Comment faire du vélo" | Skills, workflows appris |

**Source** : [Cognitive Memory in Large Language Models](https://arxiv.org/html/2504.02441v1)

### 2.2 Architecture technique typique

```
┌─────────────────────────────────────────────────────────────┐
│                    Context Window (LLM)                      │
│                   Working Memory ~128K-1M tokens             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Vector    │  │  Knowledge  │  │  Key-Value  │          │
│  │  Database   │  │    Graph    │  │    Store    │          │
│  │  (Qdrant)   │  │  (Neo4j)    │  │  (SQLite)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│       ↓                 ↓                 ↓                  │
│  Semantic Search   Relations        Fast Facts              │
│  Embeddings        Entités          Préférences             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Solutions de mémoire analysées

### 3.1 Mem0

| Champ | Valeur |
|-------|--------|
| **Nom** | Mem0 ("mem-zero") |
| **Type** | Memory layer open source + managed |
| **GitHub** | [mem0ai/mem0](https://github.com/mem0ai/mem0) - 45K+ stars |
| **Licence** | Apache 2.0 |
| **Funding** | $24M (octobre 2025) |
| **Adoption** | Netflix, Lemonade, Rocket Money |

**Architecture** :
- Hybrid data store : vector DB + graph DB + key-value store
- 24+ vector databases supportés (Qdrant, Chroma, Pinecone, pgvector, MongoDB)
- 16+ providers LLM (OpenAI, Anthropic, Ollama, Groq, local)

**Performance** :
- 26% meilleure accuracy vs OpenAI Memory (benchmark LOCOMO)
- 91% lower latency vs full-context
- 90% token cost savings

**Points forts** :
- Open source mature et bien maintenu
- Intégration AWS officielle (ElastiCache + Neptune)
- Graph Memory pour relations complexes
- Compatible 100% local avec Ollama

**Points faibles** :
- Complexité de setup multi-store
- Documentation parfois incomplète
- Pas de UI native

**Source** : [Mem0 Official](https://mem0.ai/), [GitHub](https://github.com/mem0ai/mem0)

---

### 3.2 Letta (ex-MemGPT)

| Champ | Valeur |
|-------|--------|
| **Nom** | Letta (anciennement MemGPT) |
| **Type** | LLM Operating System |
| **Origine** | UC Berkeley research |
| **Approche** | Self-editing memory via tool calls |
| **Funding** | $10M (stealth exit) |

**Concept clé : LLM OS**

L'approche MemGPT traite le context window comme de la RAM :
- **In-context memory** : ce qui est dans le context window
- **Out-of-context memory** : archival memory (vector DB) + recall memory (historique)

L'agent **décide lui-même** quoi mettre en mémoire et quoi récupérer.

**Architecture mémoire** :
```
Core Memory (in-context)
├── Persona : personnalité de l'agent
└── User Info : informations sur l'utilisateur

External Memory (out-of-context)
├── Archival Memory : vector DB (long-term facts)
└── Recall Memory : conversation history
```

**Points forts** :
- Agent autonome pour la gestion mémoire
- Self-improvement via Skill Learning
- Letta Code : #1 sur Terminal-Bench (coding benchmark)
- Model-agnostic (recommande Opus 4.5 et GPT-5.2)

**Points faibles** :
- Plus complexe à comprendre que RAG classique
- Overhead computationnel (l'agent fait des tool calls pour mémoire)
- Moins mature que Mem0 en production

**Source** : [Letta Docs](https://docs.letta.com/), [GitHub](https://github.com/letta-ai/letta)

---

### 3.3 Claude Memory (Anthropic)

| Champ | Valeur |
|-------|--------|
| **Nom** | Claude Memory |
| **Type** | Feature native Claude |
| **Launch** | Septembre 2025 |
| **Disponibilité** | Pro, Max, Team, Enterprise |

**Timeline** :
- Sept 2025 : Launch initial (Team/Enterprise)
- Oct 2025 : Automatic memory (Pro/Max)
- Jan 2026 : Memory tool pour agents (beta)

**Architecture** :
- **Approche fichier** : stockage en Markdown (CLAUDE.md)
- **Pas de RAG complexe** : transparence et simplicité
- Structure hiérarchique claire

**Catégories mémoire** :
- Role & Work
- Current Projects
- Personal Content
- Preferences

**Points forts** :
- Intégration native (zero setup)
- Transparence (fichiers lisibles)
- Automatic memory synthesis

**Points faibles** :
- Cloud only (pas de souveraineté)
- Limité à l'écosystème Claude
- Pas de graph memory
- Cowork n'utilise PAS cette feature !

**Source** : [Claude Memory Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)

---

### 3.4 LangGraph + MongoDB

| Champ | Valeur |
|-------|--------|
| **Nom** | LangGraph Memory Store |
| **Type** | Framework + Database |
| **Approche** | Long-term memory pour agents LangChain |

**Architecture** :
- LangGraph pour orchestration agent
- MongoDB comme persistent store
- Checkpointing automatique

**Points forts** :
- Intégration écosystème LangChain
- Sessions cross-device
- Bonne documentation

**Points faibles** :
- Lock-in LangChain
- MongoDB overhead pour petits projets

**Source** : [MongoDB Blog](https://www.mongodb.com/company/blog/product-release-announcements/powering-long-term-memory-for-agents-langgraph)

---

## 4. Vector Databases comparées

### 4.1 Tableau comparatif

| Critère | Qdrant | Chroma | Pinecone | pgvector |
|---------|--------|--------|----------|----------|
| **Type** | Open source | Open source | Managed | Extension PG |
| **Langage** | Rust | Python→Rust | Cloud | SQL |
| **Performance** | Excellent | Bon (MVP) | Excellent | Bon |
| **Scale** | Billions | <10M | Billions | Millions |
| **Self-hosted** | Docker/K8s | In-process | Non | PostgreSQL |
| **Hybrid search** | Oui | Basique | Oui | Via extensions |
| **GPU** | Oui | Non | N/A | Non |
| **Prix** | Free/Managed | Free | $$ | Free |

### 4.2 Recommandations par use case

| Cas d'usage | Recommandation |
|-------------|----------------|
| **Prototypage rapide** | Chroma (zero config) |
| **Production self-hosted** | **Qdrant** (performance + features) |
| **Enterprise SaaS** | Pinecone (managed) |
| **Stack existante PostgreSQL** | pgvector |
| **Budget serré, mid-scale** | Qdrant |

### 4.3 Qdrant en détail (recommandé pour THÉRÈSE)

**Pourquoi Qdrant** :
- **Rust** : performance native, sécurité mémoire
- **Hybrid search** : dense + sparse vectors
- **Quantization** : 97% RAM reduction possible
- **Filtering** : metadata filtering avancé
- **Self-hosted** : 100% souveraineté
- **Compliance** : features pour environnements régulés

**Benchmarks** :
- 12K QPS avec scalar quantization + on-disk
- 4x memory cut avec tuning approprié
- Latency comparable à Pinecone

**Source** : [Qdrant vs Pinecone](https://qdrant.tech/blog/comparing-qdrant-vs-pinecone-vector-databases/)

---

## 5. Knowledge Graphs pour mémoire

### 5.1 Neo4j comme couche mémoire

Neo4j se positionne comme "the default knowledge layer for agentic systems".

**Avantages des graphs** :
- **Relations explicites** : Client → Projet → Tâche
- **Traversal** : "Tous les projets de ce client depuis 2024"
- **Temporal** : évolution des relations dans le temps
- **Explicabilité** : on voit pourquoi l'IA se souvient

**MCP Integration** :
- Neo4j MCP Memory Server : stocke les conversations en graph
- Neo4j MCP Cypher Server : queries directes

**Graphiti** :
- Library Python pour construire des Knowledge Graphs
- Raw text → AI Knowledge Graph
- Hybrid search (semantic + keyword)

**Source** : [Neo4j Agentic Memory](https://neo4j.com/nodes-2025/agenda/building-evolving-ai-agents-via-dynamic-memory-representations-using-temporal-knowledge-graphs/)

### 5.2 Architecture hybride Vector + Graph

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│         Semantic Search             │
│   Vector DB (Qdrant) → Embeddings   │
│   "Trouve infos similaires"         │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│         Relationship Query          │
│   Graph DB (Neo4j/SQLite) → Links   │
│   "Explore les connexions"          │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│         Context Assembly            │
│   Fusion des résultats → Prompt     │
└─────────────────────────────────────┘
```

---

## 6. Solutions locales / souveraines

### 6.1 Stack 100% local

Pour une souveraineté totale (RGPD, data sensitivity) :

| Composant | Solution |
|-----------|----------|
| **LLM** | Ollama (Mistral, Llama, Qwen) |
| **Embeddings** | nomic-embed-text, mxbai-embed-large |
| **Vector DB** | Qdrant (Docker) |
| **Graph** | SQLite (relations simples) ou Neo4j Community |
| **Memory Layer** | Mem0 (mode local) |

**Mem0 100% local** :
```python
from mem0 import Memory

config = {
    "llm": {
        "provider": "ollama",
        "config": {"model": "mistral:latest"}
    },
    "embedder": {
        "provider": "ollama",
        "config": {"model": "nomic-embed-text"}
    }
}

memory = Memory.from_config(config)
```

**Source** : [Mem0 Local Companion](https://docs.mem0.ai/cookbooks/companions/local-companion-ollama)

### 6.2 Avantages souveraineté

- **RGPD** : données ne quittent jamais l'infra
- **Sécurité** : zero data leaks via API tiers
- **Coûts** : pas de fees API (après hardware)
- **Contrôle** : mise à jour, backup, audit complet
- **Offline** : fonctionne sans internet

### 6.3 Ollama embeddings

Modèles recommandés (2026) :
- **nomic-embed-text** : 768 dims, bon ratio perf/taille
- **mxbai-embed-large** : 1024 dims, meilleure quality
- **all-minilm** : 384 dims, ultra léger

**Source** : [Ollama Embeddings Guide](https://collabnix.com/ollama-embedded-models-the-complete-technical-guide-to-local-ai-embeddings-in-2025/)

---

## 7. Patterns d'architecture mémoire

### 7.1 RAG classique

```
User → Query → Embed → Vector Search → Top-K docs → LLM → Response
```

**Limites** :
- Stateless (pas d'apprentissage)
- Pas de distinction semantic/episodic
- Retrieval peut être bruitée

### 7.2 MemGPT / LLM OS

```
User → Agent → [Decide what to remember]
                    ↓
            Memory Tools (read/write)
                    ↓
            Vector DB + Archival
```

**Avantages** :
- Agent autonome
- Memory curation intelligente
- Self-improvement possible

### 7.3 Cognitive Architecture (recommandé)

```
┌─────────────────────────────────────────────────────────────┐
│                   THÉRÈSE Memory System                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Working Memory (in-context)                                 │
│  └── Conversation courante, tâche active                     │
│                                                              │
│  Episodic Memory (vector DB)                                 │
│  └── Historique conversations, événements datés             │
│                                                              │
│  Semantic Memory (SQLite + vector)                           │
│  └── Contacts, projets, faits business                       │
│                                                              │
│  Procedural Memory (skills)                                  │
│  └── Workflows appris, préférences de travail                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Recherche académique récente

### 8.1 Papers clés (2025-2026)

| Paper | Date | Contribution |
|-------|------|--------------|
| Memory in the Age of AI Agents | Dec 2025 | Survey complet, taxonomie |
| Mem0: Scalable Long-Term Memory | Apr 2025 | Architecture production-ready |
| MemOS: Memory OS for AI System | Jul 2025 | Memory as system resource |
| MIRIX: Multi-Agent Memory System | Jul 2025 | Memory pour multi-agents |
| Memory-R1: Memory via RL | Aug 2025 | Reinforcement learning pour memory |
| ComoRAG: Cognitive Memory RAG | Sep 2025 | RAG avec cognitive modeling |

**Source** : [Agent Memory Paper List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List)

### 8.2 Tendances 2026

1. **Memory as OS resource** : traiter la mémoire comme CPU/RAM
2. **Graph-structured memory** : au-delà des embeddings plats
3. **Self-evolving memory** : agents qui apprennent de leur mémoire
4. **Multi-agent memory sharing** : mémoire partagée entre agents
5. **Temporal knowledge graphs** : évolution dans le temps

---

## 9. Comparatif solutions pour THÉRÈSE

| Critère | Mem0 | Letta | Claude Memory | LangGraph |
|---------|------|-------|---------------|-----------|
| **Open source** | Apache 2.0 | Open | Propriétaire | MIT |
| **Self-hosted** | Oui | Oui | Non | Oui |
| **Local (Ollama)** | Oui | Oui | Non | Oui |
| **Graph memory** | Oui | Partiel | Non | Via MongoDB |
| **Maturité** | Production | Production | GA | Production |
| **Complexité** | Moyenne | Haute | Basse | Moyenne |
| **Documentation** | Bonne | Bonne | Excellente | Excellente |
| **Communauté** | 45K stars | 40K stars | N/A | LangChain |

---

## 10. Recommandations pour THÉRÈSE

### 10.1 Architecture cible

```
┌───────────────────────────────────────────────────────────────┐
│                    THÉRÈSE Memory Architecture                 │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│   Frontend (Tauri/React)                                       │
│        ↓                                                       │
│   FastAPI Backend                                              │
│        ↓                                                       │
│   ┌─────────────────────────────────────────────────────────┐ │
│   │              Memory Manager (Mem0-based)                 │ │
│   │                                                          │ │
│   │  ┌───────────┐  ┌───────────┐  ┌───────────┐            │ │
│   │  │  Qdrant   │  │  SQLite   │  │  CLAUDE   │            │ │
│   │  │ (vectors) │  │ (facts)   │  │   .md     │            │ │
│   │  └───────────┘  └───────────┘  └───────────┘            │ │
│   │       ↓              ↓              ↓                    │ │
│   │   Episodic      Semantic       Working                  │ │
│   │   Memory        Memory         Context                  │ │
│   └─────────────────────────────────────────────────────────┘ │
│        ↓                                                       │
│   LLM (Claude API → Mistral API → Ollama local)               │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### 10.2 Stack recommandée

| Composant | Choix | Raison |
|-----------|-------|--------|
| **Memory Layer** | Mem0 (customisé) | Mature, flexible, local possible |
| **Vector DB** | Qdrant | Performance, self-hosted, souveraineté |
| **Relational** | SQLite | Léger, embarqué, backup facile |
| **Context** | CLAUDE.md pattern | Transparent, simple, efficace |
| **Embeddings** | nomic-embed-text (Ollama) | Local, bon rapport perf/taille |

### 10.3 Différenciateurs vs concurrence

| Feature | Cowork | Claude Pro | THÉRÈSE (cible) |
|---------|--------|------------|-----------------|
| **Mémoire persistante** | Non | Oui (cloud) | Oui (local) |
| **Souveraineté données** | Non | Non | Oui |
| **Graph relations** | Non | Non | Oui |
| **Contacts/CRM intégré** | Non | Non | Oui |
| **Mode offline** | Non | Non | Oui |
| **Export/portabilité** | Limité | Limité | Total |

### 10.4 Priorités d'implémentation

1. **MVP** : SQLite + embeddings basiques (mémoire simple)
2. **V1** : Qdrant + Mem0 pattern (mémoire riche)
3. **V2** : Graph relations (contacts/projets liés)
4. **V3** : Self-evolving memory (apprentissage)

---

## 11. Risques et mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| **Memory bloat** | Performance dégradée | Utility-based deletion, TTL |
| **Hallucinations** | Faux souvenirs | Validation sources, confidence scores |
| **Privacy leaks** | RGPD issues | Encryption, access control |
| **Stale memory** | Infos obsolètes | Temporal tracking, refresh |
| **Complexity** | Maintenance difficile | Start simple, iterate |

---

## 12. Sources

### Documentation officielle
- [Mem0 Documentation](https://docs.mem0.ai/)
- [Letta (MemGPT) Documentation](https://docs.letta.com/)
- [Claude Memory Tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

### Articles et guides
- [How Does LLM Memory Work - DataCamp](https://www.datacamp.com/blog/how-does-llm-memory-work)
- [Design Patterns for Long-Term Memory - Serokell](https://serokell.io/blog/design-patterns-for-long-term-memory-in-llm-powered-architectures)
- [Ollama Embeddings Guide - Collabnix](https://collabnix.com/ollama-embedded-models-the-complete-technical-guide-to-local-ai-embeddings-in-2025/)
- [Neo4j Agentic Memory](https://neo4j.com/nodes-2025/agenda/building-evolving-ai-agents-via-dynamic-memory-representations-using-temporal-knowledge-graphs/)

### Recherche académique
- [Memory in the Age of AI Agents](https://arxiv.org/abs/2512.13564)
- [Mem0: Building Production-Ready AI Agents](https://arxiv.org/abs/2504.19413)
- [Cognitive Memory in LLMs](https://arxiv.org/html/2504.02441v1)
- [Agent Memory Paper List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List)

### Comparatifs vector databases
- [Vector Database Comparison 2025 - LiquidMetal AI](https://liquidmetal.ai/casesAndBlogs/vector-comparison/)
- [Best Vector Databases 2025 - Firecrawl](https://www.firecrawl.dev/blog/best-vector-databases-2025)
- [Qdrant vs Pinecone - Qdrant Blog](https://qdrant.tech/blog/comparing-qdrant-vs-pinecone-vector-databases/)

---

## 13. Conclusion

La mémoire persistante est le **différenciateur #1** de THÉRÈSE vs Cowork. L'écosystème 2025-2026 offre des solutions matures (Mem0, Letta) et des bases de données performantes (Qdrant) pour implémenter une mémoire souveraine.

**Recommandation** : Adopter une architecture cognitive (working/episodic/semantic/procedural) basée sur Mem0 + Qdrant + SQLite, avec possibilité de fonctionnement 100% local via Ollama.

**Tagline mémoire** : "THÉRÈSE te connaît. Elle se souvient de tes clients, tes projets, tes préférences - même hors ligne."

---

*Document généré le 21 janvier 2026*
*THÉRÈSE v2 - Synoptïa*
